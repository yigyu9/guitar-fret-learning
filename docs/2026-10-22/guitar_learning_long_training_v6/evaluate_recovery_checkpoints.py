"""Strict global0/500/1000/1500/2000 evaluation across a1300+700 recovery chain.

Original interrupted run has no completion report; physical episodes reset at
resume. No PPO update, historical pin edits, pressure or acoustic claims.
"""
import argparse
import copy
import faulthandler
import json
from pathlib import Path
import sys
import time
import traceback

PHASE=Path(__file__).resolve().parent
ROOT=PHASE.parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(PHASE))
from evaluate_checkpoints import (require,sha,write,json_io,NUM_ENVS,CAPTURE_ENVS,
    CHECKPOINT_UPDATES,SOURCE_PHASE,SOURCE_SEAL_SHA,verify_cached_pins,
    checkpoint_selection,select_video_env,validate_capture,per_note_summary,
    validate_input_contract,posture_metadata)
CHAIN_SCHEMA='guitar_learning.segmented_long_training_v6.v1'


def checkpoint_path(prefix,resumed,updates):
    require(updates in CHECKPOINT_UPDATES,'Predefined global checkpoint required')
    if updates in (0,500,1000):
        return prefix/('initial.pt' if updates==0 else 'checkpoint_%06d.pt'%(updates-1))
    return resumed/('checkpoint_000199.pt' if updates==1500 else 'final.pt')


def verify_copy_manifest(manifest,prefix):
    require(manifest['schema']=='guitar_learning.relocated_run_copy.v1' and manifest['completed'] is True and
        isinstance(manifest['errors'],list) and Path(manifest['destination']).resolve()==prefix,'Completed exact relocated-run copy required')
    source=Path(manifest['source'])
    require(source.is_absolute() and '..' not in source.parts,'Absolute lexical historical root required; do not access failed external volume')
    for relative,row in manifest['files'].items():
        name=Path(relative)
        require(not name.is_absolute() and '..' not in name.parts and row['source']==str(source/name) and
            row['copy']==str(prefix/name),'Copy record escaped or mismatched declared roots')
        path=prefix/name
        require(path.is_file() and path.stat().st_size==row['bytes'] and sha(path)==row['sha256'],'Local copied bytes differ: '+str(path))


def relocate_pins(pins,manifest):
    source,destination=Path(manifest['source']),Path(manifest['destination']).resolve()
    require(source.is_absolute() and '..' not in source.parts,'Absolute lexical historical root required')
    result,records={},[]
    for original,digest in pins.items():
        try:
            relative=Path(original).relative_to(source)
        except ValueError:
            result[original]=digest
            continue
        record=manifest['files'].get(str(relative))
        require(record is not None and record['sha256']==digest and record['source']==original and
            record['copy']==str(destination/relative),'Historical pin has no exact copy proof: '+original)
        actual=str(destination/relative)
        require(Path(actual).is_file() and sha(actual)==digest,'Relocated historical pin changed')
        result[actual]=digest
        records.append(dict(original=original,actual=actual,sha256=digest))
    return result,records


def merge_pins(*groups):
    result={}
    for group in groups:
        for path,digest in group.items():
            require(path not in result or result[path]==digest,'Conflicting input SHA: '+path)
            result[path]=digest
    return result


def same_tree(left,right):
    import numpy as np
    import torch
    if isinstance(left,torch.Tensor):
        return isinstance(right,torch.Tensor) and left.dtype==right.dtype and left.shape==right.shape and torch.equal(left.cpu(),right.cpu())
    if isinstance(left,np.ndarray):
        return isinstance(right,np.ndarray) and left.dtype==right.dtype and np.array_equal(left,right)
    if isinstance(left,dict):
        return isinstance(right,dict) and left.keys()==right.keys() and all(same_tree(v,right[k]) for k,v in left.items())
    if isinstance(left,(list,tuple)):
        return type(left) is type(right) and len(left)==len(right) and all(same_tree(a,b) for a,b in zip(left,right))
    return type(left) is type(right) and left==right


def verify_boundary(checkpoint,initial):
    import torch
    left,right=(torch.load(p,map_location='cpu',weights_only=False) for p in (checkpoint,initial))
    require(left['updates']==right['updates']==1300,'Strict1300 boundary required')
    require(same_tree({k:v for k,v in left.items() if k!='metadata'},
        {k:v for k,v in right.items() if k!='metadata'}),'Resumed initial differs in model/Adam/curriculum/RNG/identity')


def validate_recovery_chain(chain):
    require(chain['schema']==CHAIN_SCHEMA and chain['fresh_policy'] is False and chain['origin_fresh_policy'] is True and
        chain['continuous_training'] is False and chain['run_completed'] is True and chain['source_optimizer_updates']==2000 and
        chain['valid_prefix_updates']==1300 and chain['resumed_updates']==700 and chain['physical_episode_reset_at_resume'] is True and
        chain['original_native_report_missing'] is True and
        type(chain['excluded_old_update_file_count']) is int and chain['excluded_old_update_file_count']==len(chain['excluded_old_update_indices']) and
        chain['excluded_old_update_indices']==sorted(set(chain['excluded_old_update_indices'])) and
        all(type(i) is int and i>=1300 for i in chain['excluded_old_update_indices']),
        'Explicit validated1300+700 recovery/reset/excluded-branch contract required')


def verify_segmented_proof(proof,prefix,resumed,manifest):
    segments=proof['segments'];excluded=proof['excluded_old_update_indices']
    require(proof['schema']=='guitar_learning.long_training_v6_recovery_verification.v1' and proof['completed'] is True and
        proof['old_run']==str(prefix) and proof['run']==str(resumed) and proof['committed_updates']==2000 and
        proof['committed_transitions']==65536000 and len(segments)==2 and
        segments[0]['committed_updates']==1300 and segments[1]['committed_updates']==700 and
        segments[1]['optimizer_offset']==1300 and segments[1]['checkpoint_updates']==2000 and
        proof['restore']['exact_nonmetadata'] is True and proof['restore']['optimizer_updates']==1300 and
        proof['copy_manifest_sha256']==sha(manifest) and
        proof['source_manifest_sha256']==sha(PHASE/'training_source_manifest.json') and
        proof['checked_checkpoint_path']==str(resumed/'final.pt') and proof['checked_checkpoint_sha256']==sha(resumed/'final.pt') and
        proof['excluded_old_update_file_count']==len(excluded) and
        excluded==sorted(set(excluded)) and all(type(i) is int and i>=1300 for i in excluded),
        'Completed independently verified1300+700 recovery evidence required')


def main():
    faulthandler.enable(all_threads=True)
    global NUM_ENVS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix', type=Path, default=PHASE/'recovered_train2000_restart1')
    parser.add_argument('--resumed', type=Path, default=PHASE/'train_resume700')
    parser.add_argument('--copy-manifest', type=Path, default=PHASE/'recovery_copy_manifest.json')
    parser.add_argument('--verification', type=Path, default=PHASE/'recovery_verification.json')
    parser.add_argument('--out', type=Path, default=PHASE)
    parser.add_argument('--tag', default='recovery')
    parser.add_argument('--checkpoints', nargs='+', type=int, default=[2000,0,500,1000,1500])
    args = parser.parse_args()
    prefix, run, output_root = args.prefix.resolve(), args.resumed.resolve(), args.out.resolve()
    require(not args.tag or (Path(args.tag).name==args.tag and args.tag not in ('.','..')), 'Tag must be one filename component')
    require(len(args.checkpoints)==len(set(args.checkpoints)) and set(args.checkpoints)<=set(CHECKPOINT_UPDATES), 'Unique predefined global checkpoints required')
    manifest_path, verification_path = args.copy_manifest.resolve(), args.verification.resolve()
    relocation = json.loads(manifest_path.read_text())
    verify_copy_manifest(relocation, prefix)
    old_pins = json.loads((prefix/'inputs_before.json').read_text())
    relocated, remapping = relocate_pins(old_pins, relocation)
    resumed_pins = json.loads((run/'inputs_before.json').read_text())
    training_pins = merge_pins(relocated, resumed_pins)
    require(all(Path(p).is_file() and sha(p)==h for p,h in training_pins.items()), 'Actual source/asset/song/relocated input changed')
    prefix_settings = json.loads((prefix/'settings.json').read_text())
    settings = json.loads((run/'settings.json').read_text())
    report = json.loads((run/'report.json').read_text())
    require(not (prefix/'report.json').exists(), 'Interrupted original run unexpectedly has a completed native report')
    require(report['completed'] is True and report['optimizer_updates']==2000 and report['failure'] is None and
        not report['cleanup_errors'] and not report['changed_inputs'] and not report['missing_import_pins'], 'Resumed700 run incomplete/integrity failure')
    for document, updates in ((prefix_settings,2000),(settings,700)):
        require(document['num_envs']==1024 and document['horizon']==32 and document['updates']==updates and
            document['size']=='large' and document['seed']==7 and document['specialist']['role']=='left' and
            document['song_training']['control_ticks']==1969, 'Expected unchanged large1024/H32/seed7 whole-song settings')
    comparable = copy.deepcopy(prefix_settings); comparable['updates']=700
    require(comparable==settings,'Recovery settings differ beyond requested local update count')
    source_path, seal_path = SOURCE_PHASE/'tested_source_manifest.json', SOURCE_PHASE/'result_manifest.json'
    require(sha(seal_path)==SOURCE_SEAL_SHA, 'Sealed finger-input baseline changed')
    seal, source = json.loads(seal_path.read_text()), json.loads(source_path.read_text())
    local_source = json.loads((PHASE/'training_source_manifest.json').read_text())
    require(sha(source_path)==seal['files']['tested_source_manifest.json']['sha256'] and
        source['active_python_count']==len(source['source'])==436 and local_source['source']==source['source'] and
        all(training_pins.get(p)==h and sha(p)==h for p,h in source['source'].items()), 'Expected frozen v6 source436')
    contract = json.loads((run/'training_contract.json').read_text()); validate_input_contract(contract)
    require(contract==json.loads((prefix/'training_contract.json').read_text()), 'Recovery task/control/input contract differs')
    verification = json.loads(verification_path.read_text())
    verify_segmented_proof(verification,prefix,run,manifest_path)
    evidence = (manifest_path,verification_path,prefix/'inputs_before.json',prefix/'settings.json',prefix/'training_contract.json',
        prefix/'checkpoint_001299.pt',run/'initial.pt',PHASE/'evaluate_checkpoints.py')
    old_checkpoint_pins={str(prefix/name):relocation['files'][name]['sha256'] for name in
        ('initial.pt','checkpoint_000499.pt','checkpoint_000999.pt','checkpoint_001299.pt')}
    training_pins=merge_pins(training_pins,old_checkpoint_pins,{str(p):sha(p) for p in evidence},
        {str(p):sha(p) for p in (run/'checkpoint_000199.pt',run/'final.pt')})
    chain = dict(schema=CHAIN_SCHEMA, run=str(run), original_run=str(prefix), fresh_policy=False,
        origin_fresh_policy=True, continuous_training=False, source_optimizer_updates=2000, run_completed=True,
        valid_prefix_updates=1300,resumed_updates=700,physical_episode_reset_at_resume=True,
        original_native_report_missing=True,excluded_old_update_indices=verification['excluded_old_update_indices'],
        excluded_old_update_file_count=verification['excluded_old_update_file_count'],excluded_old_update_scope=verification['excluded_scope'],
        prior_attempt_scope='Earlier13-update interrupted attempt is separate; not included in this1300+700 path',
        recovery_verification=str(verification_path),recovery_verification_sha256=sha(verification_path),
        copy_manifest=str(manifest_path),copy_manifest_sha256=sha(manifest_path),copy_error_history=relocation['errors'],
        historical_input_relocations=remapping,
        source_manifest=str(PHASE/'training_source_manifest.json'),baseline_phase=str(SOURCE_PHASE),baseline_seal_sha256=SOURCE_SEAL_SHA,
        scope='Validated fresh prefix1300 plus strict resumed700; original post1300 branch excluded. Physical episodes reset at resume; not uninterrupted fresh2000 or inherited completion of the interrupted run.')
    validate_recovery_chain(chain)
    output_root.mkdir(parents=True,exist_ok=True)
    sys.path.insert(0, str(ROOT))
    import isaacgym  # Must precede NumPy/Torch in the native entry point.
    import numpy as np
    import torch
    from guitar_learning.training.gpu_pool import GpuPool, FIELDS
    from guitar_learning.skills.specialist_policy import SpecialistPolicy
    from guitar_learning.training.ppo import PPOTrainer, PPOConfig
    from guitar_learning.song.curriculum_runtime import CurriculumCoordinator
    from guitar_learning.training.recording import project_source_paths
    torch.set_num_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    verify_boundary(prefix/'checkpoint_001299.pt',run/'initial.pt')
    results = []
    for expected_updates in args.checkpoints:
        name = 'initial' if expected_updates==0 else 'final' if expected_updates==2000 else 'update_%04d'%expected_updates
        out = output_root/('evaluation_'+(args.tag+'_' if args.tag else '')+name+'_'+str(NUM_ENVS))
        checkpoint = checkpoint_path(prefix, run, expected_updates)
        if (out/'report.json').is_file():
            cached = json.loads((out/'report.json').read_text())
            cached_pins = json.loads((out/'inputs_before.json').read_text())
            expected_pins = dict(training_pins)
            expected_pins.update({str(f):sha(f) for f in (out/'settings.json', checkpoint, run/'initial.pt',
                run/'report.json', run/'training_contract.json', PHASE/'training_source_manifest.json',
                seal_path, source_path, Path(__file__).resolve())})
            verify_cached_pins(cached_pins, expected_pins)
            scene = cached['gpu_scene']
            require(cached['completed'] and cached['checkpoint']==str(checkpoint) and
                cached['source_optimizer_updates']==expected_updates and cached['training_chain']==chain and
                cached['evaluation_directory']==str(out) and scene['closed'] and scene['physx_use_gpu'] and
                scene['use_gpu_pipeline'] and scene['environment_count']==NUM_ENVS and scene['physics_steps']==cached['ticks']*4,
                'Existing closed evaluation/pins differ; preserve it and use a new tag')
            results.append(cached)
            continue
        out.mkdir(exist_ok=False)
        write(out/'settings.json', settings)
        pins = dict(training_pins)
        pins.update({str(f): sha(f) for f in (out/'settings.json', checkpoint, run/'initial.pt',
            run/'report.json', run/'training_contract.json', PHASE/'training_source_manifest.json',
            seal_path, source_path, Path(__file__).resolve())})
        write(out/'inputs_before.json', pins)
        pool, completed, captures, ticks = None, {}, {}, 0
        started = time.perf_counter()
        def lifecycle(stage, **extra):
            status = dict(stage=stage, ticks=ticks, completed_first_episodes=len(completed),
                wall_s=time.perf_counter()-started, checkpoint=str(checkpoint), **extra)
            (out/'lifecycle.json.tmp').write_text(json_io.dumps(status, allow_nan=False)+'\n')
            (out/'lifecycle.json.tmp').replace(out/'lifecycle.json')
        lifecycle('creating_pool')
        try:
            pool = GpuPool(settings, out)
            lifecycle('pool_created')
            policy = SpecialistPolicy(544, size='large', contract=pool.contract, role='left').to(settings['device'])
            coordinator = CurriculumCoordinator(policy, pool)
            trainer = PPOTrainer(policy, PPOConfig(**settings['ppo']))
            trainer.load(checkpoint)
            require(trainer.updates == expected_updates, 'Unexpected restored update count')
            require(pool.contract == contract, 'Evaluation training contract differs')
            validate_input_contract(pool.contract)
            require(policy.architecture['priority_slots']==tuple(contract['observation']['finger_targets']['slots']), 'Restored eight-slot architecture differs')
            observation = coordinator.restore()
            policy.eval()
            restored_state = policy.left_curriculum_state.clone()
            require(restored_state.numel()==3331, 'Expected strict3331-value saved curriculum')
            progress = coordinator.state.progress
            lifecycle('checkpoint_restored')
            targets = copy.deepcopy(pool.environment.task.provenance['song']['schedule'])
            require(len(targets) == pool.environment.M == 67, 'Expected actual67 target schedule')
            ids = [t.target_id for t in pool.environment.task.targets]
            require([t['target_id'] for t in targets] == ids, 'Target schedule/order mismatch')
            for j, target in enumerate(targets):
                target.update(target_index=j, canonical_string_1based=target['string']+1,
                    required_clean_s=float(pool.environment.required[j].item()))
            write(out/'targets.json', targets)
            write(out/'visual_initial.json', pool.scene.contract['initial'])
            capture_metadata = dict(schema='guitar_learning.gpu_first_song_pose_capture.v1',
                checkpoint=str(checkpoint), checkpoint_sha256=pins[str(checkpoint)], source_optimizer_updates=expected_updates,
                training_chain=chain,
                posture_reconstruction=posture_metadata(pool.contract, pool.scene.body_names),
                body_names=pool.scene.body_names, joint_names=pool.scene.names,
                body_frame='Native environment-local world; no environment-origin addition/subtraction',
                state_layout='body_state[x,y,z,qx,qy,qz,qw,COM_vx,COM_vy,COM_vz,wx,wy,wz]',
                logical_guitar='39 source markers from the actual GPU one-body rigid-guitar transform',
                source_physics_hz=240, capture_hz=60, capture_envs=list(CAPTURE_ENVS),
                initial_frame='Prepared reset t0; action0 is sentinel, not an applied policy decision',
                action='Frame k>0 stores the policy action applied over preceding four native physics steps',
                selection='Lowest envID among predeclared0..7 safe whole first songs; if none, longest first episode, then lowest ID',
                scope='Real evaluated-checkpoint first-episode observations before reset; no synthetic motion or pose interpolation')
            def capture(env_ids, actions):
                env = pool.environment
                indices = torch.tensor(env_ids, device=env.device)
                values = {key: env.snapshot[key][indices].detach().cpu().numpy()
                          for key in ('body_state', 'q', 'qd', 'target')}
                values.update(action=actions[indices].detach().cpu().numpy(), clock=env.clock[indices].cpu().numpy())
                for key, field in (('left_count', 'left'), ('near_count', 'near_done'), ('contact_count', 'contact_done')):
                    values[key] = env.note[field][indices].sum(-1).cpu().numpy()
                values['candidate_count'] = env.candidate[indices].sum(-1).cpu().numpy()
                for offset, index in enumerate(env_ids):
                    frames = captures.setdefault(index, {key: [] for key in values})
                    for key, value in values.items():
                        frames[key].append(value[offset].copy())
            capture(CAPTURE_ENVS, torch.zeros(NUM_ENVS, 39, device=pool.scene.device))
            with (out/'first_episodes.jsonl').open('x') as episode_stream, torch.no_grad():
                while len(completed) < NUM_ENVS and ticks < 1969:
                    capture_ids = [i for i in CAPTURE_ENVS if i not in completed] if capture_metadata is not None else []
                    action = policy.act(*(observation[k] for k in FIELDS), deterministic=True)['action']
                    observation, reward, cost, terminated, truncated, episodes = pool.step(action)
                    require(bool(torch.isfinite(reward).all()) and bool(torch.isfinite(cost).all()), 'Nonfinite evaluation metrics')
                    require(not bool(truncated.any()), 'Unexpected truncation in whole-song evaluation')
                    if capture_ids:
                        capture(capture_ids, action)
                    for episode in episodes:
                        index = episode['env_id']
                        if index in completed:
                            continue
                        ledger = episode['left_note_ledger']
                        require(ledger['target_ids'] == ids and len(ledger['values']['left']) == 67, 'Native ledger order mismatch')
                        require(sum(ledger['values']['left']) == episode['song']['left_success_count'], 'Native ledger/count mismatch')
                        completed[index] = episode
                        episode_stream.write(json_io.dumps(episode, allow_nan=False)+'\n')
                    episode_stream.flush()
                    ticks += 1
                    if ticks % 60 == 0:
                        lifecycle('stepping')
                    done = (terminated | truncated).nonzero().flatten()
                    if done.numel() and len(completed) < NUM_ENVS and ticks < 1969:
                        observation = pool.reset(done)[0]
            lifecycle('stepping_complete')
            require(set(completed) == set(range(NUM_ENVS)), 'Not all first episodes ended')
            torch.cuda.synchronize(pool.scene.device)
            require(trainer.updates == expected_updates and coordinator.state.progress == progress and
                    torch.equal(policy.left_curriculum_state, restored_state), 'Evaluation changed learning/curriculum state')
            changed = [f for f, h in pins.items() if sha(f) != h]
            lifecycle('input_pins_checked', changed_inputs=changed)
            require(not changed, 'Evaluation inputs/checkpoint changed')
            require(not (project_source_paths(list(sys.modules.items()))-set(pins)), 'Unpinned evaluation source imports')
            episodes = [completed[i] for i in range(NUM_ENVS)]
            if capture_metadata is not None:
                capture_metadata['selected_env_id'] = select_video_env(episodes)
                capture_metadata['captures'] = []
                for index in CAPTURE_ENVS:
                    arrays = {key: np.stack(value) for key, value in captures[index].items()}
                    validate_capture(arrays, len(pool.scene.body_names), completed[index])
                    path = out/('poses_env%04d.npz' % index)
                    np.savez_compressed(str(path), **arrays)
                    capture_metadata['captures'].append(dict(env_id=index, path=path.name, sha256=sha(path),
                        frames=len(arrays['clock']), reason=completed[index]['reason'],
                        full_safe=completed[index]['left_curriculum']['full_safe'], duration_s=completed[index]['task_time_s']))
                write(out/'capture_metadata.json', capture_metadata)
                lifecycle('pose_captures_written')
            report = dict(completed=True, checkpoint=str(checkpoint), source_optimizer_updates=expected_updates,
                evaluation_directory=str(out),
                training_chain=chain,
                deterministic=True, num_envs=NUM_ENVS, ticks=ticks, curriculum_progress=progress,
                first_episodes_path='first_episodes.jsonl', targets_path='targets.json',
                episodes=[{key: value for key, value in e.items() if key != 'left_note_ledger'} for e in episodes],
                per_note=per_note_summary(episodes, targets),
                capture_metadata_path='capture_metadata.json' if capture_metadata is not None else None,
                input_pins_verified=len(pins), wall_s=time.perf_counter()-started,
                scope='All first ended episodes only; reset other ended environments only to keep the original batch stepping. No PPO update or curriculum advance.',
                limitations='Same song/prepared pose and each checkpoint own saved curriculum/observations; not identical-observation weight isolation, independent seeds, generalization, calibrated pressure or sound.')
            lifecycle('result_prepared')
        except BaseException as error:
            write(out/'python_exception.json', dict(error=repr(error), traceback=traceback.format_exc()))
            traceback.print_exc()
            sys.stderr.flush()
            raise
        finally:
            if pool is not None:
                lifecycle('synchronizing_before_close')
                try:
                    torch.cuda.synchronize(pool.scene.device)
                finally:
                    lifecycle('destroying_simulator')
                    pool.close()
                    lifecycle('pool_closed')
        report['gpu_scene'] = pool.scene.diagnostics
        require(report['gpu_scene']['closed'] and report['gpu_scene']['physx_use_gpu'] and
                report['gpu_scene']['use_gpu_pipeline'] and report['gpu_scene']['environment_count'] == NUM_ENVS and
                report['gpu_scene']['physics_steps'] == ticks*4, 'Closed nativeGPU batch audit failed')
        write(out/'report.json', report)
        lifecycle('report_written')
        results.append(report)
    selection = checkpoint_selection(results)
    complete = set(args.checkpoints)==set(CHECKPOINT_UPDATES)
    combined = dict(completed=complete, requested_evaluations_completed=True, training_chain=chain,
        evaluated_updates=[r['source_optimizer_updates'] for r in results], results=results, selection=selection)
    summary_path = output_root/((args.tag+'_' if args.tag else '')+'checkpoint_evaluation.json')
    temporary = summary_path.with_suffix('.tmp')
    temporary.write_text(json_io.dumps(combined, indent=2, allow_nan=False)+'\n'); temporary.replace(summary_path)
    print(json_io.dumps(dict(completed=complete, checkpoint_updates=combined['evaluated_updates'], environments=NUM_ENVS)))


if __name__ == '__main__':
    main()
