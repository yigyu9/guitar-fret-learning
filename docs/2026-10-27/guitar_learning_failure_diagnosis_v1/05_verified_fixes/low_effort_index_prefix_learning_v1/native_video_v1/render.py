"""Own-schema three-note renderer; native graphics/strict PPO helpers are reused."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('prefix_video_producer',HERE.parent/'probe.py')
producer=importlib.util.module_from_spec(spec);sys.modules[spec.name]=producer;spec.loader.exec_module(producer)
grid,cap=producer.grid,producer.cap


def header(payload,update,settings,schema):
    metadata=payload.get('metadata',{})
    if (metadata.get('schema')!=schema or not metadata.get('input_pins') or metadata.get('settings')!=settings or
        payload.get('updates')!=update or settings['num_envs']!=128 or settings['song']['short_learning']['schema']!=schema):
        raise ValueError('Own3note schema/settings/update128 and sealed source required')
    return metadata


def completed_training():
    value=grid.read(producer.HERE/'02_train_eval_launcher.json')
    assert value['completed'] and value['returncode']==0
    assert [c['job'] for c in value['children']]==['train']+['evaluate_%06d'%u for u in producer.UPDATES]
    assert all(c['returncode']==0 for c in value['children'])


def evidence():
    completed_training();_,paths=producer.gate('evaluate')
    root=producer.HERE/'learning_analysis/results_v1';paths.update(producer.base.reviewed(root/'review.json'))
    assert str(root/'selection.json') in grid.read(root/'review.json')['reviewed_sha256']
    selection=grid.read(root/'selection.json')
    assert selection['latest_update']==300 and selection['video_updates']==sorted({selection['best_update'],300})
    return selection,paths|{producer.HERE/'02_train_eval_launcher.json',root/'selection.json'}


def gate(update,require_review=True):
    cap.reject_existing(HERE/'runs'/('update_%06d'%update))
    seal=grid.read(HERE/'preparation_seal.json')
    assert all(grid.sha(p)==h for p,h in seal['input_pins'].items())
    if require_review:
        review=grid.read(HERE/'review.json')
        assert seal['independent_review']=='passed_no_findings' and review['verdict']=='PASS' and not review['findings']
        assert seal['input_pins'][str(HERE/'review.json')]==grid.sha(HERE/'review.json')
        assert all(grid.sha(p)==h for p,h in review['reviewed_sha256'].items())
    selection,paths=evidence();assert update in selection['video_updates']
    checkpoint=producer.checkpoint(update);assert seal['input_pins'][str(checkpoint)]==grid.sha(checkpoint)
    return checkpoint,seal,paths|{HERE/'preparation_seal.json',*map(Path,seal['input_pins'])}


def capture_episode(pool,policy,capture,np,torch,fields):
    observation=pool.observation;indices=[4,7,8]
    with torch.no_grad():
        for tick in range(pool.spec['view']['duration_ticks']):
            action=policy.act(*(observation[k] for k in fields),deterministic=True)['action']
            observation,reward,cost,terminated,truncated,episodes=pool.step(action)
            before=len(capture.samples)
            try:capture.record(tick,reward,cost,terminated,truncated,episodes)
            finally:
                # Original capture appends its row before writing encoder bytes.
                if len(capture.samples)>before:
                    env=pool.environment;row=capture.samples[-1]
                    row.update(policy_action=pool.last_policy_action[0].cpu().numpy().copy(),executed_action=pool.last_executed_action[0].cpu().numpy().copy(),
                        source_time_s=np.asarray(float(env._score_time()[0])),candidate=env.candidate[0,indices].cpu().numpy().copy(),wrong=env.wrong[0,indices].cpu().numpy().copy(),
                        surface_distance_m=env.surface_distance[0,indices].cpu().numpy().copy(),surface_height_m=env.surface_height[0,indices].cpu().numpy().copy(),
                        released=env.note['released'][0,indices].cpu().numpy().copy(),release_s=env.note['release_s'][0,indices].cpu().numpy().copy(),
                        guard_current_goal=pool.pending['current_goal'][0].cpu().numpy().copy(),reward=np.asarray(float(reward[0])),cost=np.asarray(float(cost[0])))
                    for name,value in pool.last_wrist_feedback.items():row['wrist_'+name]=value[0].cpu().numpy().copy()
            if capture.episode is not None:break
            ids=(terminated|truncated).nonzero().flatten()
            if ids.numel():observation=pool.reset(ids)[0]
    if capture.episode is None:raise RuntimeError('env0 first episode incomplete within original3note duration')


def save_raw(out,capture,pool,np,failed):
    result=dict(trace_finite=False,clock_contiguous=False)
    if capture and capture.samples:
        arrays={k:np.stack([r[k] for r in capture.samples]) for k in capture.samples[0]}
        result.update(trace_finite=all(bool(np.isfinite(v).all()) for v in arrays.values()),clock_contiguous=bool(np.array_equal(arrays['physics_step'],4*np.arange(1,len(capture.samples)+1))))
        with (out/('partial_poses_env0000.npz' if failed else 'poses_env0000.npz')).open('xb') as f:np.savez_compressed(f,**arrays)
    if pool and pool.guard_rows:
        with (out/'current_goal_DIP60.npz').open('xb') as f:np.savez_compressed(f,**{k:np.stack([r[k] for r in pool.guard_rows]) for k in pool.guard_rows[0]})
    return result


def render_native(checkpoint,out,update,seal,paths):
    import isaacgym  # Import order identical to the native renderer, after full gate.
    from isaacgym import gymapi
    import numpy as np
    import torch
    from guitar_learning.training.decision_ppo import DecisionPPOTrainer
    from guitar_learning.training.ppo import PPOConfig
    from guitar_learning.training.gpu_pool import FIELDS
    from guitar_learning.training.finger_skill_runner import _validate_pins
    from guitar_learning.training.recording import project_source_paths
    from guitar_learning.tool.validation.hand_contact_probe import GraphicsGym,finish_video
    from guitar_learning.tool.demonstration import render_finger_skill as native
    extra=producer.support();settings=producer.settings();payload=torch.load(checkpoint,map_location='cpu',weights_only=False)
    metadata=header(payload,update,settings,extra.SCHEMA);_validate_pins(metadata)
    torch.set_num_threads(1);torch.backends.cuda.matmul.allow_tf32=False
    original_gym=gymapi.acquire_gym;original_cameras=copy.deepcopy(native.CAMERAS);cameras_config=copy.deepcopy(original_cameras)
    cameras_config['fullbody']=((-.10,3.4,1.1),(-.15,-.10,.65))
    observed={};state=dict(out=out,cleanup_errors=[],pool=None,scene=None);pool=capture=policy=model_before=None
    videos={};codes={};cleanup=[];failure=None;pins={};summary=None;raw={};started=time.monotonic()
    try:
        with producer.execution_scope('evaluate',seal,paths,observed):
            with producer.base.effort_scope(paths,state) as runner:
                out.mkdir(parents=True,exist_ok=False);grid.write(out/'settings.json',settings)
                pins=runner._pins(settings,out,[checkpoint,Path(__file__).resolve(),*map(Path,metadata['input_pins'])]);grid.write(out/'inputs_before.json',pins)
                gymapi.acquire_gym=lambda:GraphicsGym(original_gym())
                try:pool=runner.ShortPool(settings,out/'scene')
                finally:gymapi.acquire_gym=original_gym
                grid.write(out/'training_contract.json',pool.contract)
                policy=runner.ShortPolicy(contract=pool.contract,size=settings['size']).to(settings['device'])
                trainer=DecisionPPOTrainer(policy,PPOConfig(**settings['ppo']))
                if pool.environment.approach_gamma!=trainer.config.gamma:raise ValueError('Original PBRS/PPO gamma mismatch')
                trainer.load(checkpoint)  # Original complete identity/model/optimizer/RNG loader.
                model_before={k:v.detach().clone() for k,v in policy.state_dict().items()};policy.eval()
                pool.environment.set_evaluation(True,full_song=False);pool.observation=pool.reset()[0]
                native.CAMERAS=cameras_config;cameras=native._create_cameras(pool.scene,gymapi)
                for name in cameras:videos[name]=native._encoder(out/(name+'.mp4'))
                capture=native._EnvZeroCapture(pool,gymapi,np,cameras,videos);capture_episode(pool,policy,capture,np,torch,FIELDS)
                summary=extra.compact_episode(capture.episode,pool.spec)
                grid.write(out/'episode_env0000.json',capture.episode);grid.write(out/'episode_summary.json',summary)
                view=pool.spec['view'];grid.write(out/'capture_metadata.json',dict(schema='diagnostic.index_prefix_video.v1',checkpoint=str(checkpoint),checkpoint_sha256=grid.sha(checkpoint),
                    policy_schema=policy.schema,checkpoint_training_updates=trainer.updates,training_updates=0,fresh=False,control='deterministic policy',reference_N_injected=False,
                    environment=0,actual_num_envs=128,selection='predeclared env0 first episode; actual best/latest selected outside renderer',selected_target_count=3,
                    source_indices=[4,7,8],source_targets=view['source_targets'],score_offset_s=view['score_offset_s'],duration_ticks=view['duration_ticks'],
                    wrist_control=pool.spec['wrist_control'],current_goal_guard=pool.spec['candidate_dip_guard'],joint_names=pool.scene.names,body_names=pool.scene.body_names,
                    native_pixels=True,width=1280,height=720,video_fps=30,capture_hz=60,source_physics_hz=240,frames=len(capture.frame_times_s),frame_times_s=capture.frame_times_s,
                    camera_settings=cameras_config,camera_scope='original hand camera and existing short-renderer fullbody head/feet framing',
                    frame_mapping='frame n maps to control endpoint2*(n+1); no t0; odd final endpoint has no frame',
                    vector_scope='candidate/wrong/released/release_s/distance columns source4/7/8 at poststep; guard_current_goal is precontrol',
                    policy_performance_scope='conditional3note F4/stagedwrist/currentgoalguard; not freeguitar J33, naturalness or whole128 video',
                    evaluator_fingerprint_callback_used=False,episode_summary=summary))
    except BaseException as error:failure=dict(type=type(error).__name__,message=str(error));raise
    finally:
        gymapi.acquire_gym=original_gym;native.CAMERAS=original_cameras
        for name,process in videos.items():
            try:
                code,errors=finish_video(process);codes[name]=code;cleanup.extend(dict(component=name,message=e) for e in errors)
            except BaseException as error:cleanup.append(dict(component=name,message=str(error)))
        if pool:
            try:pool.close()
            except BaseException as error:cleanup.append(dict(component='scene_close',message=str(error)))
        try:raw=save_raw(out,capture,pool,np,failure is not None)
        except BaseException as error:cleanup.append(dict(component='raw_capture',message=str(error)))
        unchanged=bool(model_before is not None and all(torch.equal(v,model_before[k]) for k,v in policy.state_dict().items()))
        changed=[p for p,h in pins.items() if not Path(p).is_file() or grid.sha(p)!=h]
        missing=sorted(project_source_paths(list(sys.modules.items()))-set(pins));audit=state['scene'].diagnostics if state.get('scene') is not None else {}
        lifecycle=bool(audit.get('closed') and audit.get('environment_count')==128 and audit.get('physx_use_gpu') and audit.get('use_gpu_pipeline') and
            audit.get('diagnostic_guitar_mode')=='fixed' and audit.get('hand_collision',{}).get('enabled_distinct_finger_pairs')==90 and audit.get('hand_collision_native_readback_environments')==128)
        files={name:dict(path=str(out/(name+'.mp4')),bytes=(out/(name+'.mp4')).stat().st_size if (out/(name+'.mp4')).is_file() else 0) for name in codes}
        good=bool(failure is None and unchanged and lifecycle and not cleanup and not state['cleanup_errors'] and not changed and not missing and raw.get('trace_finite') and raw.get('clock_contiguous') and
            capture and capture.episode and capture.frame_times_s and len(codes)==2 and all(c==0 for c in codes.values()) and all(v['bytes']>0 for v in files.values()) and
            observed.get('aliases_restored') and observed.get('NN_constructors')==1 and state.get('prefix_task_verified') and state.get('aliases_restored') and state.get('loader_restored'))
        if out.is_dir():
            grid.write(out/'inputs_after.json',dict(verified=not changed and not missing,input_pins=pins,changed_paths=changed,unpinned_project_sources=missing))
            grid.write(out/'report.json',dict(schema='diagnostic.index_prefix_video.v1',completed=good,failure=failure,cleanup_errors=cleanup+state['cleanup_errors'],
                native_pixels=True,checkpoint=str(checkpoint),checkpoint_sha256=grid.sha(checkpoint),checkpoint_unchanged=str(checkpoint) not in changed,
                checkpoint_pins_validated=True,policy_unchanged=unchanged,training_updates=0,checkpoint_training_updates=update,fresh=False,reference_N_injected=False,
                recorded_environment=0,first_episode_only=True,selected_target_count=3,episode_summary=summary,frames=len(capture.frame_times_s) if capture else 0,
                encoding_exit_codes=codes,video_files=files,changed_inputs=changed,unpinned_project_sources=missing,scene_closed=audit.get('closed',False),lifecycle_verified=lifecycle,
                wrapper_aliases_restored=observed.get('aliases_restored',False),cap_aliases_restored=state.get('aliases_restored',False),loader_restored=state.get('loader_restored',False),
                prefix_task_verified=state.get('prefix_task_verified',False),NN_constructors=observed.get('NN_constructors',0),evaluator_fingerprint_callback_used=False,gpu_scene=audit,wall_s=time.monotonic()-started,**raw))
        if failure is None and not good:raise RuntimeError('Native3note render/source/model/clock/scene audit failed; outputs retained')


def commands(updates):
    return dict(video_updates=updates,render=[[grid.PYTHON,'-B',str(Path(__file__).resolve()),'--execute','--update',str(u)] for u in updates])


def prepare():
    assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));selection,paths=evidence()
    cap.reject_existing(HERE/'cpu_inputs');cap.reject_existing(HERE/'preparation_seal.json')
    tests=producer.module('prefix_video_cpu_checks',HERE/'cpu_checks.py');checks=tests.check(sys.modules[__name__]);models=tests.actual_models(sys.modules[__name__],selection['video_updates'])
    inputs=HERE/'cpu_inputs';inputs.mkdir()
    grid.write(inputs/'settings.json',producer.settings());grid.write(inputs/'commands.json',commands(selection['video_updates']));grid.write(inputs/'selection.json',selection)
    grid.write(HERE/'cpu_verification_final.json',dict(synthetic=checks,actual_models=models))
    paths.update(inputs.glob('*.json'));paths.update(producer.checkpoint(u) for u in selection['video_updates'])
    paths.update((Path(__file__),HERE/'cpu_checks.py',HERE/'PLAN.md',HERE/'README.md',HERE/'cpu_verification_final.json'))
    from guitar_learning.tool.experiments.short_finger_learning import runner
    grid.write(HERE/'preparation_seal.json',dict(independent_review='pending',input_pins=runner._pins(producer.settings(),inputs,paths)))
    result=subprocess.run([grid.PYTHON,'-B',str(Path(__file__).resolve()),'--gate-check'],text=True,capture_output=True,check=True)
    grid.write(HERE/'fresh_process_gate.json',json.loads(result.stdout));seal=grid.read(HERE/'preparation_seal.json')
    seal['input_pins'][str(HERE/'fresh_process_gate.json')]=grid.sha(HERE/'fresh_process_gate.json')
    (HERE/'preparation_seal.json').write_text(json.dumps(seal,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(CPU_only=True,GPU_executed=False,video_updates=selection['video_updates'],pins=len(seal['input_pins']))))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    for name in ('self-test','execute','prepare','gate-check'):g.add_argument('--'+name,action='store_true')
    p.add_argument('--update',type=int,choices=producer.UPDATES);a=p.parse_args();sys.path.insert(0,str(grid.ROOT))
    if a.self_test:
        checks=producer.module('prefix_video_cpu_checks',HERE/'cpu_checks.py').check(sys.modules[__name__]);print(json.dumps(checks,indent=2))
    elif a.prepare:prepare()
    elif a.gate_check:
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));selection,_=evidence()
        for update in selection['video_updates']:
            _,seal,_=gate(update,require_review=False)
            if seal['independent_review']=='pending':
                try:gate(update)
                except (FileNotFoundError,AssertionError):pass
                else:raise AssertionError('Pending video admitted')
            else:gate(update)
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));print(json.dumps(dict(stdlib_only=True,GPU_executed=False,video_updates=selection['video_updates'])))
    else:
        if a.update is None:p.error('--update required for execution')
        checkpoint,seal,paths=gate(a.update);render_native(checkpoint,HERE/'runs'/('update_%06d'%a.update),a.update,seal,paths)
