"""Explicit frozen-current-physics adapter evaluation of the v19 checkpoint500.

This is not v19 training resume: exact old policy identity and legacy temporal
idle4 observations run on audited unchanged physics/success logic. Current v20
rewards and new diagnostics are reported separately from musical success.
Archive source is only hashed and parsed as data, never imported or executed.
"""
import argparse
import ast
import copy
import faulthandler
import json
from pathlib import Path
import sys
import time
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluate as current
ROOT, PHASE = current.ROOT, current.PHASE
NUM_ENVS, CAPTURE_ENVS = 1024, tuple(range(8))
BASELINE = ROOT/'docs/2026-10-25/guitar_learning_long_training_v19_3000'
ARCHIVE = ROOT/'guitar_learning/archive/20261025_before_finger_recovery_v20'
CHAIN_SCHEMA = 'guitar_learning.v19_checkpoint500_current_physics_adapter.v1'
CHECKPOINT_UPDATES = (500,)
require, sha, write, json_io = current.require, current.sha, current.write, current.json_io
validate_capture, select_video_env = current.validate_capture, current.select_video_env
per_note_summary, posture_metadata = current.per_note_summary, current.posture_metadata
verify_trainer_restoration = current.verify_trainer_restoration


def checkpoint_path(run, updates):
    require(updates == 500, 'Only original v19 checkpoint500 is the predefined baseline')
    return run/'checkpoint_000499.pt'


CONTRACT_DIFFERENCES = frozenset(
    ['/observation/fields/'+str(i) for i in range(540,544)] + [
    '/observation/finger_posture/encoding', '/observation/finger_posture/role',
    '/observation/finger_posture/schema', '/reward/schema', '/reward/finger_recovery',
    '/reward/finger_shape', '/task/song/finger_recovery'] +
    ['/reward/finger_posture/'+name for name in ('allowed_standby_rates_per_s', 'gate',
        'quality', 'rate', 'rate_bounds_per_s/1', 'schema', 'shape_rate_per_s', 'standby_rate_per_s')])


def differences(left, right, prefix=''):
    result = set()
    if type(left) is not type(right):
        return {prefix}
    if isinstance(left, dict):
        for key in set(left) | set(right):
            path = prefix+'/'+key
            result.update({path} if key not in left or key not in right else
                differences(left[key], right[key], path))
    elif isinstance(left, list):
        if len(left) != len(right):
            return {prefix}
        for i, pair in enumerate(zip(left,right)):
            result.update(differences(*pair, prefix+'/'+str(i)))
    elif left != right:
        result.add(prefix)
    return result


def validate_old_contract(contract):
    observation, reward = contract.get('observation',{}), contract.get('reward',{})
    require(contract.get('schema') == 'guitar_learning.training.v1' and
        observation.get('dimension') == 544 and observation.get('event_dim') == 24 and
        observation.get('priority_slots') == 8 and
        observation.get('fields',[])[-4:] == ['finger_posture.'+finger+'.idle_weight'
            for finger in ('index','middle','ring','pinky')] and
        reward.get('schema') == 'guitar_learning.gpu_tensor_song_reward.v19' and
        reward.get('finger_posture',{}).get('schema') == 'guitar_learning.gpu_finger_preparation_rate.v3' and
        'finger_recovery' not in reward and 'finger_shape' not in reward,
        'Expected original v19 policy contract with temporal idle4')


def validate_contract_bridge(policy_contract, simulator_contract):
    validate_old_contract(policy_contract)
    current.validate_input_contract(simulator_contract)
    actual = differences(policy_contract, simulator_contract)
    require(actual == CONTRACT_DIFFERENCES,
        'Unexpected policy/simulator contract difference: '+str(sorted(actual ^ CONTRACT_DIFFERENCES)))
    return actual


def ast_definition(path, name):
    tree = ast.parse(Path(path).read_text())
    found = [node for node in ast.walk(tree) if
        isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name == name]
    require(len(found) == 1, 'One source definition required: '+name)
    return ast.dump(found[0],include_attributes=False)


def validate_source_pins(old_training_pins):
    old_manifest = BASELINE/'training_source_manifest.json'
    original = json.loads(old_manifest.read_text())
    archived = json.loads((ARCHIVE/'manifest.json').read_text())
    require(original['python_count'] == archived['python_count'] == 459 and
        len(original['source']) == 459, 'Expected original and archived459 sources')
    current_pins = json.loads((PHASE/'train500/inputs_before.json').read_text())
    current.validate_source_pins(current_pins)
    pins = dict(current_pins)
    for relative, value in original['source'].items():
        path = str(ROOT/relative)
        preserved = ARCHIVE/relative
        require(old_training_pins.get(path) == value and archived['source'].get(relative) == value and
            preserved.is_file() and sha(preserved) == value, 'Archived old source pin mismatch: '+relative)
        pins[str(preserved)] = value
    original_source_paths = {str(ROOT/relative) for relative in original['source']}
    for path, value in old_training_pins.items():
        if path not in original_source_paths:
            require(Path(path).is_file() and sha(path) == value, 'Non-source old input changed: '+path)
            require(path not in pins or pins[path] == value, 'Shared input mismatch: '+path)
            pins[path] = value
    changed_production = {'guitar_learning/'+name for name in ('gpu/environment.py',
        'gpu/episode_diagnostics.py','gpu/finger_reward.py','skills/specialist_policy.py',
        'song/curriculum_runtime.py','training/start.py')}
    for relative,value in original['source'].items():
        if relative not in changed_production and not relative.startswith('guitar_learning/tests/'):
            require(sha(ROOT/relative) == value, 'Common runtime source changed: '+relative)
    definitions = {}
    modules = {
        'guitar_learning/gpu/finger_reward.py': ['finger_posture_reward','finger_target_indices',
            'finger_tracking_reward','_verify_source_frames','source_finger_frame_contract'],
        'guitar_learning/gpu/environment.py': ['_snapshot','_contacts','_wrong_sources','_wrist_guide',
            'set_curriculum','_weights','_surface_potential','begin_control','invalidate_control',
            '_safety','end_control','_focus','_history','_events','_episode','_finger_metrics'],
        'guitar_learning/skills/specialist_policy.py': ['forward','act','evaluate','log_probability'],
        'guitar_learning/song/curriculum_runtime.py': ['restore','advance']}
    import hashlib
    for relative,names in modules.items():
        for name in names:
            old, active = ast_definition(ARCHIVE/relative,name), ast_definition(ROOT/relative,name)
            require(old == active, 'Shared policy/measurement/physics AST changed: '+relative+':'+name)
            definitions[relative+':'+name] = hashlib.sha256(active.encode()).hexdigest()
    audit_path = BASELINE/'log_inspection.json'
    audit = json.loads(audit_path.read_text())
    require(audit.get('verified') is True and audit.get('transitions') == 98_304_000 and
        audit.get('raw_crc',{}).get('complete') is True and
        audit['raw_crc'].get('completed_members') == 3000 and
        audit['raw_crc'].get('valid_prefix_rows') == 96000 and
        audit['raw_crc'].get('error') is None and audit['raw_crc'].get('discarded_unverified_bytes') == 0,
        'Completed original v19 fresh3000 full-log audit required')
    for path in (old_manifest, audit_path, ARCHIVE/'manifest.json', PHASE/'training_source_manifest.json',
            PHASE/'train500/inputs_before.json', PHASE/'log_inspection.json'):
        pins[str(path)] = sha(path)
    adapter = dict(schema='guitar_learning.explicit_v19_policy_current_physics_adapter.v1',
        policy_contract='Original checkpoint500 full v19 contract; trainer.load strict identity',
        simulator_contract='Current frozen462 source v20 A .02/shape0; never relabeled v19',
        source_training_optimizer_updates=3000, source_checkpoint_optimizer_updates=500,
        original_source_count=459, current_source_count=462,
        source_archive=str(ARCHIVE), shared_definition_ast_sha256=definitions,
        observation_adapter='Clone state544 and replace columns540:544 with unchanged legacy finger_posture_reward temporal idle_weight; preserve all other state, events, masks and priority tokens',
        diagnostics='Current v20 fixed score windows/B-reference/geometry diagnostics applied equally to both policies',
        reward_scope='Current v20 A reward totals/components, not original v19 rewards; compare music/safety/pose/recovery only',
        scope='Explicit adapter evaluation, not original-source v19 training resume; old source is read-only hashed/AST-parsed data, never imported')
    return pins, adapter


def adapt_observation(environment, observation):
    import torch
    from guitar_learning.gpu.finger_reward import finger_posture_reward
    now = environment.clock.to(torch.float64)/240.
    measured = finger_posture_reward(now, environment.onset, environment.end, environment.press,
        environment.finger, environment.body[:,environment.finger_palm_index,3:7],
        environment.body[:,environment.finger_segment_indices,3:7])
    result = dict(observation)
    result['state'] = observation['state'].clone()
    result['state'][:,540:544] = measured['idle_weight'].float()
    require(result['state'].shape == (NUM_ENVS,544), 'Expected1024 state544 for explicit old policy adapter')
    return result


def main():
    faulthandler.enable(all_threads=True)
    global NUM_ENVS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, default=BASELINE/'train3000')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--repeat', type=int, choices=(1,2,3), required=True)
    args = parser.parse_args()
    run, output_root = args.run.resolve(), args.out.resolve()
    require(run == (BASELINE/'train3000').resolve(), 'Use the predefined preserved v19 training lineage')
    require(not output_root.exists(), 'Use a new evaluation output directory for every repeat')
    settings = json.loads((run/'settings.json').read_text())
    report = json.loads((run/'report.json').read_text())
    training_pins = json.loads((run/'inputs_before.json').read_text())
    require(report['completed'] is True and report['optimizer_updates'] == 3000 and
            report['failure'] is None and not report['cleanup_errors'] and
            not report['changed_inputs'] and not report['missing_import_pins'], 'Training incomplete/integrity failure')
    require(settings['num_envs'] == NUM_ENVS and settings['horizon'] == 32 and settings['updates'] == 3000 and
            settings['size'] == 'large' and settings['seed'] == 7 and
            settings['specialist']['role'] == 'left' and settings['song_training']['control_ticks'] == 1969 and
            settings['ppo']['advantage_normalization'] == 'separate' and settings['ppo']['gae_lambda'] == .98,
            'Expected large/H32/seed7 left whole-song and v19 source large/H32/seed7 separate/.98 PPO settings')
    require('finger_recovery' not in settings['song'], 'Original v19 settings required')
    settings = copy.deepcopy(settings)
    settings['song']['finger_recovery'] = dict(schema='guitar_learning.left_finger_recovery.v1', standby_rate_per_s=.02, shape_rate_per_s=0.)
    baseline_pins, adapter = validate_source_pins(training_pins)
    training_pins = baseline_pins
    contract = json.loads((run/'training_contract.json').read_text())
    validate_old_contract(contract)
    chain = dict(schema=CHAIN_SCHEMA, run=str(run),
        source_training_optimizer_updates=3000, source_optimizer_updates=500, repeat=args.repeat,
        evaluation_mode='explicit_v19_policy_on_frozen_v20_physics_adapter', adapter=adapter,
        run_completed=True, source_manifest=str(BASELINE/'training_source_manifest.json'),
        source_manifest_sha256=sha(BASELINE/'training_source_manifest.json'))
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
            BASELINE/'log_inspection.json', BASELINE/'training_source_manifest.json',
            Path(__file__).resolve(), Path(current.__file__).resolve())})
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
            policy = SpecialistPolicy(544, size='large', contract=contract, role='left').to(settings['device'])
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
            difference = validate_contract_bridge(contract, pool.contract)
            write(out/'current_evaluation_contract.json', pool.contract)
            write(out/'adapter_contract.json', dict(adapter, contract_differences=sorted(difference)))
            require(policy.architecture['priority_slots']==tuple(contract['observation']['finger_targets']['slots']) and
                policy.architecture['finger_actor']['schema']=='guitar_learning.targeted_finger_actor.v1',
                'Restored eight-slot targeted-finger architecture differs')
            observation = adapt_observation(pool.environment, coordinator.restore())
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
                adapter=adapter,
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
                    observation = adapt_observation(pool.environment, observation)
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
                        observation = adapt_observation(pool.environment, pool.reset(done)[0])
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
                deterministic=True, repeat=args.repeat, adapter=adapter, source_training_optimizer_updates=3000, restoration_verified=['model','actor_optimizer','value_optimizer','torch_rng','cuda_rng','numpy_rng','python_rng','3331_curriculum'], num_envs=NUM_ENVS, ticks=ticks, curriculum_progress=progress,
                first_episodes_path='first_episodes.jsonl', targets_path='targets.json',
                episodes=[{key: value for key, value in e.items() if key != 'left_note_ledger'} for e in episodes],
                per_note=per_note_summary(episodes, targets),
                capture_metadata_path='capture_metadata.json' if capture_metadata is not None else None,
                input_pins_verified=len(pins), wall_s=time.perf_counter()-started,
                scope='Explicit current-physics adapter evaluation of old exact v19 policy contract and temporal idle4. First ended episodes; no PPO or curriculum advance. This is not native v19-source strict resume.',
                limitations='Episode reward and recovery diagnostics use current v20 A semantics, not v19 reward totals. Same song/prepared pose and each checkpoint own saved curriculum/observations; not identical-observation weight isolation, independent seeds, generalization, calibrated pressure or sound.')
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
