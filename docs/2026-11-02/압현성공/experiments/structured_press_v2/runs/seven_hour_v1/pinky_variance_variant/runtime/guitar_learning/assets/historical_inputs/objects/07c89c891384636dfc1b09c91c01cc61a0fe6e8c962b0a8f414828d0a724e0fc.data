"""Native inference of the new 81D policy with real coupled music measurements."""
import argparse
import hashlib
import json
from pathlib import Path
import traceback


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path,value):
    with Path(path).open('x') as stream:
        json.dump(value,stream,indent=2,ensure_ascii=False,allow_nan=False);stream.write('\n')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--checkpoint',type=Path)
    parser.add_argument('--stochastic',action='store_true')
    parser.add_argument('--train',action='store_true')
    args=parser.parse_args()
    if args.train:
        from .joint_learning_observation_v1 import require_native_training_ready
        require_native_training_ready()  # Before native imports or output creation.
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    # Isaac Gym must import before Torch.
    from .dual_music_scene_v1 import DualMusicScene,preload_targets,BASE
    from .joint_learning_observation_v1 import JointMusicMeasurement,TRAINING_BLOCKERS,ROOT,BUNDLE
    from .joint_policy_v1 import AbsoluteTargetCodec,JointActorCritic,digest
    from .joint_ppo_v1 import JointPPO,PPOConfig
    from .gym_trial_recording import GymTrialRecording
    from .run_joint_hold import native_state
    from .build_fixed_lower_asset import LOWER_BODIES,MANIFEST,REFERENCE
    from .environment_contract_v1 import EnvironmentContract
    import numpy as np
    import torch
    paths=set(str(p) for folder in ('stability_adapter_2','tab2body') for p in (ROOT/folder).rglob('*')
              if p.is_file() and p.suffix in ('.py','.json','.xml','.md','.obj','.stl','.mtl','.png','.urdf'))
    paths.update(json.loads(MANIFEST.read_text())['input_sha256'])
    paths.update(str(REFERENCE/n) for n in ('report.json','states.json'))
    paths.update(str(p) for p in BUNDLE.rglob('*.json'))
    paths.update(EnvironmentContract().inputs);paths.add(str(BASE))
    paths.update(str(ROOT/p) for p in (
        'fret/training/runs/20260911_1710_02_Jazz1-200-B_solo/checkpoints/fret_035000.pt',
        'strike/training/runs/20260920_Jazz1_sync_baseline/checkpoints/strike_010000.pt',
        'strike/02_physical_control/pick-grip-reference.json'))
    if args.checkpoint: paths.add(str(args.checkpoint.resolve()))
    inputs={p:sha(p) for p in sorted(paths)}
    save(out/'attempt.json',{'input_sha256':inputs,'stochastic':args.stochastic,'seed':101})
    scene=recorder=measurement=None;controls=[];trace=[];failure=None;videos={};unchanged=False
    try:
        torch.manual_seed(101);np.random.seed(101)
        scene=DualMusicScene(5.)
        initial=native_state(scene)
        if initial!=scene.contract.reference['native_initial_state']: raise AssertionError('initial state changed')
        anchor,preload=preload_targets(scene.contract,1.)
        codec=AbsoluteTargetCodec(scene.contract,anchor)
        measurement=JointMusicMeasurement(scene)
        obs,manifest=measurement.observe(scene.observe())
        source_paths=[Path(p) for p in paths if Path(p).suffix != '.md']
        abi={'schema':'upper81_joint_v1','observation':manifest,'action_dimension':81,'codec':codec.manifest(),
             'actor_hidden':[512,256],'critic_hidden':[512,256],'value_dimension':1,
             'policy_distribution':'tanh_diagonal_gaussian_latent_stored_v1','control_hz':60,'physics_hz':240,
             'canonical_music_sha256':measurement.music.timeline.content_sha256,
             'input_sha256':dict(scene.contract.inputs,**measurement.inputs,**{str(BASE):sha(BASE)}),
             'source_sha256':{str(p):sha(p) for p in source_paths},
             'reward_contract_status':list(TRAINING_BLOCKERS),'teacher_weights_loaded':False}
        save(out/'learning_abi.json',{'payload':abi,'sha256':digest(abi)})
        model=JointActorCritic(739,scene.contract.groups)
        trainer=JointPPO(model,abi,PPOConfig())
        if args.checkpoint: trainer.load(args.checkpoint)
        model.eval()
        trainer.save(out/'initial_policy.pt')
        save(out/'initial_values.json',{'native_initial_state':initial,'preload':preload,
                                      'codec':codec.manifest(),'checkpoint':str(args.checkpoint) if args.checkpoint else None,
                                      'training_ready':False,'training_blockers':list(TRAINING_BLOCKERS),
                                      'preparation_seconds':2,'physics_horizon_seconds':5,
                                      'strap_enabled':False,'source_actors_called':0,
                                      'PD_properties':{k:scene.pd_properties[k].tolist() for k in scene.pd_properties.dtype.names}})
        fixed=[scene.human_bodies.index(n) for n in ('Pelvis',)+LOWER_BODIES]
        recorder=GymTrialRecording(scene,out/'media')
        def record_state():
            state=native_state(scene)
            if any(state['human_body_states'][i]!=initial['human_body_states'][i] for i in fixed):
                raise AssertionError('fixed lower/root body moved')
            if not np.isfinite([[s['pos'],s['vel']] for s in state['human_dof_states']]).all():
                raise ValueError('non-finite native joint state')
            if max(abs(s['vel']) for s in state['human_dof_states'])>50:
                raise ValueError('unsafe native joint velocity')
            guitar=state['guitar_body_states'][0]['pose']
            trace.append({'physics_step':scene.steps,'position_W_m':[guitar['p'][k] for k in 'xyz'],
                          'quaternion_xyzw':[guitar['r'][k] for k in 'xyzw'],
                          'q_rad':[s['pos'] for s in state['human_dof_states']]})
        record_state();recorder.capture()
        for tick in range(300):
            sample=model.sample(torch.tensor(obs)[None],deterministic=not args.stochastic)
            action=sample['action'][0].numpy()
            physical,info=scene.step(codec.owner_action(action))
            next_obs,_=measurement.observe(physical)
            controls.append({'physics_step':scene.steps,'observation_before':obs.tolist(),
                             'action81':action.tolist(),'latent81':sample['latent'][0].tolist(),
                             'sample_log_prob':float(sample['log_prob'][0]),'value':float(sample['value'][0]),
                             'requested_rad':codec.requested(action).tolist(),'owner_info':info,
                             'joint_event_count':len(measurement.music.results)})
            obs=next_obs;record_state()
            if scene.steps%8==0: recorder.capture()
            if scene.steps%240==0: print('recorded',scene.steps/240,'seconds',flush=True)
        save(out/'final_observation.json',obs.tolist())
        save(out/'joint_crossings.json',measurement.music.crossings)
        save(out/'joint_events.json',measurement.music.results)
        save(out/'music_physics_samples.json',measurement.samples)
    except BaseException as error:
        failure={'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()}
        print(failure['traceback'],flush=True)
    finally:
        steps=scene.steps if scene else 0
        forbidden=list(scene.forbidden_calls) if scene else []
        if recorder and (not recorder.frames or recorder.frames[-1]['physics_step']!=steps):
            try: recorder.capture()
            except BaseException as error:
                if failure is None: failure={'type':type(error).__name__,'message':str(error)}
        if scene: scene.close()
        if recorder:
            try: videos=recorder.encode()
            except BaseException as error:
                if failure is None: failure={'type':type(error).__name__,'message':str(error)}
        save(out/'controls.json',controls);save(out/'trace.json',trace)
        unchanged=all(sha(p)==h for p,h in inputs.items())
        if measurement: unchanged=unchanged and all(sha(p)==h for p,h in measurement.inputs.items())
        save(out/'report.json',{'completed':failure is None and unchanged and not forbidden,
             'failure':failure,'physics_steps':steps,'physics_seconds':steps/240,'control_steps':len(controls),
             'policy_dimension':739,'policy_action_dimension':81,'inputs_unchanged':unchanged,
             'forbidden_calls':forbidden,'videos':videos,'source_actor_calls':0,'native_training_updates':0,
             'training_ready':False,'stop_reason':'five_second_policy_diagnostic' if failure is None else 'error',
             'scope':'new policy inference and measured music; not music/reward certification'})
    if failure or not unchanged or forbidden: raise RuntimeError(failure or 'input/ownership changed')


if __name__=='__main__': main()
