"""Frozen v20 A500 final evaluation and actual first-song pose capture.

Each repeat is a new native process and a new output directory; no historical files change.

No PPO updates/curriculum advancement; same prepared whole-song contract.
"""
import argparse
import copy
import faulthandler
import hashlib
import json
import random
from pathlib import Path
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[4]
PHASE = Path(__file__).resolve().parents[1]
NUM_ENVS = 1024
CAPTURE_ENVS = tuple(range(8))
CHECKPOINT_UPDATES = (500,)
CHAIN_SCHEMA = 'guitar_learning.fresh_v20_A500.v1'
sys.path.insert(0, str(ROOT))
from guitar_learning.training import json_io


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def write(path, value):
    with Path(path).open('x') as stream:
        json_io.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def select_video_env(episodes):
    """Predeclared selection: lowest safe ID, else longest; no score selection."""
    rows = {e['env_id']: e for e in episodes if e['env_id'] in CAPTURE_ENVS}
    require(set(rows) == set(CAPTURE_ENVS), 'All eight predeclared first episodes required')
    safe = [i for i, e in rows.items() if e['reason'] == 'timeline_complete' and e['left_curriculum']['full_safe']]
    return min(safe) if safe else min(rows, key=lambda i: (-rows[i]['task_time_s'], i))


def validate_capture(arrays, body_count, episode):
    import numpy as np
    frames = episode['steps']+1
    shapes = dict(body_state=(frames, body_count, 13), q=(frames, 105), qd=(frames, 105),
        target=(frames, 105), action=(frames, 39), clock=(frames,),
        left_count=(frames,), near_count=(frames,), contact_count=(frames,), candidate_count=(frames,))
    require(set(arrays) == set(shapes), 'Unexpected pose capture fields')
    for key, shape in shapes.items():
        require(arrays[key].shape == shape and np.isfinite(arrays[key]).all(), 'Invalid capture: '+key)
    require(np.array_equal(arrays['clock'], np.arange(frames)*4), 'First-song physics clock not continuous')
    require(abs(arrays['clock'][-1]/240.-episode['task_time_s']) < 1e-9, 'Capture endpoint differs from episode')
    require(int(arrays['left_count'][-1]) == episode['song']['left_success_count'], 'Capture/ledger success count differs')
    require(np.max(np.abs(np.linalg.norm(arrays['body_state'][..., 3:7], axis=-1)-1)) < 1e-3,
            'Recorded body quaternion not near unit length')


def per_note_summary(episodes, targets):
    result = []
    for j, target in enumerate(targets):
        row = copy.deepcopy(target)
        for group, selected in (('all_first', episodes), ('full_safe_first',
                [e for e in episodes if e['left_curriculum']['full_safe']])):
            n = len(selected)
            values = [e['left_note_ledger']['values'] for e in selected]
            row[group] = dict(episodes=n, left_success_count=sum(v['left'][j] for v in values))
            for field in ('left', 'near_done', 'contact_done'):
                row[group][field+'_fraction'] = sum(v[field][j] for v in values)/n if n else None
            for field in ('clean', 'best_clean_streak', 'wrong', 'missing', 'contact_time', 'near_time',
                          'wrong_supported_time', 'wrong_ambiguous_time', 'wrong_next_preparation_time'):
                row[group]['mean_'+field+'_s'] = sum(v[field][j] for v in values)/n if n else None
            row[group]['mean_best_required_fraction'] = (sum(min(v['best_clean_streak'][j]/
                target['required_clean_s'], 1.) for v in values)/n) if n else None
        result.append(row)
    return result


def checkpoint_path(run, updates):
    require(updates in CHECKPOINT_UPDATES, 'Expected final500 checkpoint')
    return run/('initial.pt' if updates == 0 else 'final.pt' if updates == 500 else 'checkpoint_%06d.pt'%(updates-1))


def exact_equal(left, right):
    """Exact nested checkpoint equality, allowing CPU/GPU tensor placement."""
    import numpy as np
    import torch
    if isinstance(left, torch.Tensor) or isinstance(right, torch.Tensor):
        return (isinstance(left, torch.Tensor) and isinstance(right, torch.Tensor) and
                left.dtype == right.dtype and left.shape == right.shape and
                torch.equal(left.detach().cpu(), right.detach().cpu()))
    if isinstance(left, np.ndarray) or isinstance(right, np.ndarray):
        return (isinstance(left, np.ndarray) and isinstance(right, np.ndarray) and
                left.dtype == right.dtype and np.array_equal(left, right))
    if isinstance(left, dict) or isinstance(right, dict):
        return (isinstance(left, dict) and isinstance(right, dict) and left.keys() == right.keys() and
                all(exact_equal(left[key], right[key]) for key in left))
    if isinstance(left, (list, tuple)) or isinstance(right, (list, tuple)):
        return type(left) is type(right) and len(left) == len(right) and all(
            exact_equal(a, b) for a, b in zip(left, right))
    return type(left) is type(right) and left == right


def verify_trainer_restoration(trainer, payload):
    """Called immediately after strict load and after deterministic evaluation."""
    import numpy as np
    import torch
    pairs = dict(model=(trainer.policy.state_dict(), payload['model']),
        actor_optimizer=(trainer.actor_optimizer.state_dict(), payload['actor_optimizer']),
        value_optimizer=(trainer.value_optimizer.state_dict(), payload['value_optimizer']),
        updates=(trainer.updates, payload['updates']),
        cost_weight=(trainer.cost_weight, payload['cost_weight']),
        torch_rng=(torch.get_rng_state(), payload['torch_rng']),
        numpy_rng=(np.random.get_state(), payload['numpy_rng']),
        python_rng=(random.getstate(), payload['python_rng']),
        cuda_rng=(torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None, payload['cuda_rng']))
    for name, pair in pairs.items():
        require(exact_equal(*pair), 'Strict checkpoint restoration/evaluation changed '+name)


def validate_recovery(value):
    require(value == dict(schema='guitar_learning.left_finger_recovery.v1',
        standby_rate_per_s=.02, shape_rate_per_s=0.), 'Expected default v20 A recovery rates .02/0')



def validate_input_contract(contract):
    observation = contract.get('observation', {})
    slots = [finger+'_'+kind for finger in ('index','middle','ring','pinky') for kind in ('tracking','next')]
    require(contract.get('schema')=='guitar_learning.training.v1' and
        observation.get('dimension')==544 and observation.get('event_dim')==24 and
        type(observation.get('priority_slots')) is int and observation['priority_slots']==8 and
        isinstance(observation.get('finger_targets'), dict) and
        observation['finger_targets'].get('schema')=='guitar_learning.left_finger_targets.v1' and
        observation['finger_targets'].get('slots')==slots and
        contract.get('action', {}).get('dimension')==39 and
        contract.get('task', {}).get('specialist', {}).get('role')=='left' and
        contract.get('native_backend', {}).get('pipeline')=='gpu' and
        contract.get('reward', {}).get('schema')=='guitar_learning.gpu_tensor_song_reward.v20' and
        contract['reward'].get('finger_tracking', {}).get('schema')=='guitar_learning.gpu_finger_tracking_rate.v7' and
        contract['reward'].get('surface_learning', {}).get('schema')=='guitar_learning.surface_fretting.v8' and
        contract['reward'].get('finger_posture', {}).get('schema')=='guitar_learning.gpu_finger_preparation_rate.v4' and
        contract['reward'].get('action_change', {}).get('schema')=='guitar_learning.gpu_action_change.v2' and
        observation.get('surface_geometry', {}).get('schema')=='guitar_learning.left_surface_events.v5' and
        observation.get('event_fields', [None]*14)[11:14]==['clean_streak_s', 'contact_streak_fraction', 'contact_progress'],
        'Expected explicit GPU left544/eight-priority/E24/rewardv20 A/surface8/event5 contract')
    validate_recovery(contract['reward'].get('finger_recovery'))
    require(observation.get('finger_posture', {}).get('schema') ==
        'guitar_learning.left_finger_posture_observation.v2' and
        observation.get('fields', [])[-4:] == ['finger_posture.'+finger+'.standby_gate'
            for finger in ('index','middle','ring','pinky')] and
        contract['reward']['finger_posture'].get('standby_rate_per_s') == .02 and
        contract['reward'].get('finger_shape', {}).get('rate_per_s') == 0. and
        contract['reward'].get('finger_shape', {}).get('enabled') is False,
        'Expected actual standby_gate4, default standby .02 and disabled shape')


def validate_source_pins(training_pins):
    """Require the frozen462 v20 sources and completed whole-run audit."""
    source_path = PHASE/'training_source_manifest.json'
    audit_path = PHASE/'log_inspection.json'
    local = json.loads(source_path.read_text())
    require(local['python_count']==462 and len(local['source'])==462,
        'Expected frozen v20 source462')
    require(set(local['source']) == {str(p.relative_to(ROOT))
        for p in (ROOT/'guitar_learning').rglob('*.py') if 'archive' not in p.parts},
        'Active Python census differs from frozen462 source manifest')
    source = {str(ROOT/p): h for p, h in local['source'].items()}
    require(all(training_pins.get(p)==h and sha(p)==h for p,h in source.items()),
        'Training/current v20 source pins differ')
    audit = json.loads(audit_path.read_text())
    require(audit['verified'] and audit['transitions']==16_384_000,
        'Completed v20 A500 raw audit required')
    require(audit.get('raw_crc', {}).get('complete') is True and
        audit['raw_crc'].get('valid_prefix_rows') == 16000 and
        audit['raw_crc'].get('completed_members') == 500 and
        audit['raw_crc'].get('error') is None and
        audit['raw_crc'].get('discarded_unverified_bytes') == 0,
        'Complete500 gzip members/16000 raw rows without discarded bytes required')
    return audit_path, source_path


def posture_metadata(contract, body_names):
    """Small reconstruction contract; actual quaternions are already captured."""
    validate_input_contract(contract)
    posture = copy.deepcopy(contract['reward']['finger_posture'])
    frame = posture['frame_source']
    require(posture['schema']=='guitar_learning.gpu_finger_preparation_rate.v4' and
        frame['schema']=='guitar_learning.source_finger_flex_frames.v1', 'Actual source posture definition required')
    palm = body_names.index('human/'+frame['palm_body'])
    segments = [[body_names.index('human/'+name) for name in finger] for finger in frame['finger_body_names']]
    require(len(segments)==4 and all(len(row)==3 for row in segments), 'Four fingers by three actual source bodies required')
    return dict(schema='guitar_learning.saved_pose_posture_definition.v1', contract=posture,
        palm_body_index=palm, segment_body_indices=segments,
        source_function='guitar_learning.gpu.finger_reward.finger_posture_reward (geometry and temporal idle only)',
        source_function_sha256=sha(ROOT/'guitar_learning/gpu/finger_reward.py'),
        quaternion='body_state[...,3:7] xyzw; actual parent inverse times child, never q1_x/z as full rotation',
        clock='clock/240 seconds at saved60Hz endpoints; t0 included, not240Hz extrema',
        score_inputs='targets.json onset_s/end_s/press_s/finger; all67 notes at original prepared-song time',
        scope='MCP/PIP/DIP signed geometry, projection/quaternion validity and temporal idle_weight can be reconstructed from saved poses. Current v20 A shape rate is0; optional B standby additionally requires240Hz own-finger load/contact/proximity vetoes absent from this pose-only trace. Actual integrated posture reward cannot be reconstructed here; endpoint geometry does not certify pressure or sound.')



def main():
    faulthandler.enable(all_threads=True)
    global NUM_ENVS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, default=PHASE/'train500')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--repeat', type=int, choices=(1,2,3), required=True)
    args = parser.parse_args()
    run, output_root = args.run.resolve(), args.out.resolve()
    require(not output_root.exists(), 'Use a new evaluation output directory for every repeat')
    settings = json.loads((run/'settings.json').read_text())
    report = json.loads((run/'report.json').read_text())
    training_pins = json.loads((run/'inputs_before.json').read_text())
    require(report['completed'] is True and report['optimizer_updates'] == 500 and
            report['failure'] is None and not report['cleanup_errors'] and
            not report['changed_inputs'] and not report['missing_import_pins'], 'Training incomplete/integrity failure')
    require(settings['num_envs'] == NUM_ENVS and settings['horizon'] == 32 and settings['updates'] == 500 and
            settings['size'] == 'large' and settings['seed'] == 7 and
            settings['specialist']['role'] == 'left' and settings['song_training']['control_ticks'] == 1969 and
            settings['ppo']['advantage_normalization'] == 'separate' and settings['ppo']['gae_lambda'] == .98,
            'Expected large/H32/seed7 left whole-song and v20 A separate/.98 PPO settings')
    validate_recovery(settings['song'].get('finger_recovery'))
    require(not [f for f,h in training_pins.items() if sha(f) != h], 'Training inputs changed')
    seal_path, source_path = validate_source_pins(training_pins)
    contract = json.loads((run/'training_contract.json').read_text())
    validate_input_contract(contract)
    chain = dict(schema=CHAIN_SCHEMA, run=str(run),
        fresh_policy=True, source_optimizer_updates=500, repeat=args.repeat,
        run_completed=True, source_manifest=str(PHASE/'training_source_manifest.json'),
        source_manifest_sha256=sha(PHASE/'training_source_manifest.json'))
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
    results = []
    for expected_updates in CHECKPOINT_UPDATES:
        out = output_root
        checkpoint = checkpoint_path(run, expected_updates)
        out.mkdir(parents=True, exist_ok=False)
        write(out/'settings.json', settings)
        pins = dict(training_pins)
        pins.update({str(f): sha(f) for f in (out/'settings.json', checkpoint, run/'initial.pt',
            run/'report.json', run/'training_contract.json', PHASE/'training_source_manifest.json', run/'inputs_before.json',
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
            payload = torch.load(checkpoint, map_location='cpu', weights_only=False)
            initial = torch.load(run/'initial.pt', map_location='cpu', weights_only=False)
            require(initial['updates'] == 0 and initial['identity'] == payload['identity'] and
                not initial['actor_optimizer']['state'] and not initial['value_optimizer']['state'],
                'Expected fresh update0 initial policy with empty Adam state and the final identity')
            del initial
            trainer.load(checkpoint)
            verify_trainer_restoration(trainer, payload)
            require(trainer.updates == expected_updates, 'Unexpected restored update count')
            require(pool.contract == contract, 'Evaluation training contract differs')
            validate_input_contract(pool.contract)
            require(policy.architecture['priority_slots']==tuple(contract['observation']['finger_targets']['slots']) and
                policy.architecture['finger_actor']['schema']=='guitar_learning.targeted_finger_actor.v1',
                'Restored eight-slot targeted-finger architecture differs')
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
                        require(ledger['schema']=='guitar_learning.surface_note_ledger.v7',
                            'Expected current v20 note ledger.v7')
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
            verify_trainer_restoration(trainer, payload)
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
                deterministic=True, repeat=args.repeat, restoration_verified=['model','actor_optimizer','value_optimizer','torch_rng','cuda_rng','numpy_rng','python_rng','3331_curriculum'], num_envs=NUM_ENVS, ticks=ticks, curriculum_progress=progress,
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
        require(not [f for f, h in pins.items() if sha(f) != h], 'Evaluation inputs changed during capture/close')
        write(out/'report.json', report)
        lifecycle('report_written')
        results.append(report)
    print(json_io.dumps(dict(completed=True, source_optimizer_updates=500, repeat=args.repeat, environments=NUM_ENVS, output=str(out))))


if __name__ == '__main__':
    main()
