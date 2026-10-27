"""Conditional recorded-action replay in one new four-environment GPU pool.

Root runs this after the fixed final100 evaluation closes. Failed captured rows
are selected by lowest ID, never score. First-episode outcomes are limited to
one recorded prefix; rows without an observed end are right-censored. An actual
timeline endpoint is reported separately and is not67-note musical success.
"""
import argparse
import copy
import faulthandler
import json
from pathlib import Path
import sys
import time
import traceback

PHASE = Path(__file__).resolve().parent
ROOT = PHASE.parents[2]
sys.path.insert(0, str(PHASE))
sys.path.insert(0, str(ROOT))
from evaluate_checkpoints import require, sha, write, json_io, validate_capture
from probe_fingers import mapping

CASES = ('all_recorded', 'thumb5_zero', 'fingers16_zero', 'left21_zero')


def select_failure(report):
    require(report['completed'] is True and report['source_optimizer_updates'] == 100 and
            report['num_envs'] == 1024 and report['deterministic'] is True and
            report['gpu_scene']['closed'] is True and report['gpu_scene']['physx_use_gpu'] is True and
            report['gpu_scene']['use_gpu_pipeline'] is True, 'Closed final100 GPU evaluation required')
    rows = {r['env_id']: r for r in report['episodes']}
    require(len(rows) == len(report['episodes']) == 1024 and set(rows) == set(range(1024)), 'Complete first-episode cohort required')
    require(all(rows[i]['reason'] in ('terminal_failure', 'timeline_complete') and
                rows[i]['left_curriculum']['full_safe'] is (rows[i]['reason'] == 'timeline_complete')
                for i in range(8)), 'Captured first-episode outcomes contradict safety')
    eligible = [i for i in range(8) if rows[i]['reason'] == 'terminal_failure']
    if not eligible:
        return None
    selected = rows[min(eligible)]
    require(selected['left_curriculum']['full_safe'] is False, 'Selected failure has contradictory safety flag')
    return selected


def case_actions(action, order, active):
    """Leave all other actions identical; padding rows receive zero39 after end."""
    import numpy as np
    source = np.asarray(action)
    require(source.shape == (39,) and np.isfinite(source).all() and (np.abs(source) <= 1).all(), 'Finite bounded recorded action39 required')
    require(len(order) == len(set(order)) == 39 and len(active) == 4, 'Named action39/four case flags required')
    thumb = [i for i, name in enumerate(order) if name.startswith('LH:thumb')]
    fingers = [i for i, name in enumerate(order) if name.startswith('LH:') and not name.startswith('LH:thumb')]
    require(len(thumb) == 5 and len(fingers) == 16, 'Expected thumb5 and other fingers16')
    result = np.repeat(source[None], 4, axis=0)
    result[1, thumb] = 0
    result[2, fingers] = 0
    result[3, thumb+fingers] = 0
    result[~np.asarray(active, dtype=bool)] = 0
    return result


def reference_errors(source, replay, finger_native, source_episode, replay_episode):
    """Compare the original1024 trace and case0 until either first episode ends."""
    import numpy as np
    count = min(len(source['clock']), len(replay['clock']))
    require(count >= 1 and np.array_equal(source['clock'][:count], replay['clock'][:count]), 'Common first-episode clocks differ')
    left, right = source['body_state'][:count].astype(np.float64), replay['body_state'][:count].astype(np.float64)
    displacement = np.linalg.norm(left[..., :3]-right[..., :3], axis=-1)
    qa, qb = left[..., 3:7], right[..., 3:7]
    qa = qa/np.linalg.norm(qa, axis=-1, keepdims=True)
    qb = qb/np.linalg.norm(qb, axis=-1, keepdims=True)
    rotation = 2*np.arccos(np.clip(np.abs((qa*qb).sum(-1)), 0, 1))
    difference = {key: source[key][:count].astype(np.float64)-replay[key][:count].astype(np.float64)
                  for key in ('q', 'qd', 'target')}
    failed = replay_episode is not None and replay_episode['reason'] == 'terminal_failure'
    return dict(common_endpoint_frames=count, common_control_steps=count-1,
        body_position_max_error_m=float(displacement.max()),
        body_rotation_max_error_rad=float(rotation.max()),
        q_max_abs_error_rad=float(np.abs(difference['q']).max()),
        qd_max_abs_error_rad_s=float(np.abs(difference['qd']).max()),
        target_max_abs_error_rad=float(np.abs(difference['target']).max()),
        left21_target_max_abs_error_rad=float(np.abs(difference['target'][:, finger_native]).max()),
        source_failure_time_s=source_episode['task_time_s'],
        replay_first_failure_time_s=replay_episode['task_time_s'] if failed else None,
        failure_time_delta_s=replay_episode['task_time_s']-source_episode['task_time_s'] if failed else None,
        replay_failure_observed=failed,
        scope='N1024 recorded rollout versus newN4 native replay; batch/contact solver differences may change trajectories. Pose/target errors are measured, not assumed negligible; no precise causal or policy-generalization claim.')


def main():
    faulthandler.enable(all_threads=True)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evaluation', type=Path, default=PHASE/'evaluation_smoke_final_1024')
    parser.add_argument('--out', type=Path, default=PHASE/'finger_ablation_smoke100')
    args = parser.parse_args()
    source, out = args.evaluation.resolve(), args.out.resolve()
    report = json.loads((source/'report.json').read_text())
    episode = select_failure(report)
    pins = json.loads((source/'inputs_before.json').read_text())
    require(not [name for name, value in pins.items() if not Path(name).is_file() or sha(name) != value], 'Source evaluation inputs changed')
    for path in (Path(__file__).resolve(), PHASE/'evaluate_checkpoints.py', PHASE/'probe_fingers.py',
                 source/'report.json', source/'inputs_before.json'):
        value = sha(path)
        require(str(path) not in pins or pins[str(path)] == value, 'Existing source pin differs: '+str(path))
        pins[str(path)] = value
    out.mkdir(parents=True, exist_ok=False)
    if episode is None:
        write(out/'inputs_before.json', pins)
        write(out/'report.json', dict(completed=False, applicable=False, status='not_applicable',
            source_evaluation=str(source), reason='No physical failure among captured first env0..7',
            GPU_simulators_created=0, scope='No fallback to uncaptured or best/worst-score environments; no native replay performed'))
        print(json_io.dumps(dict(status='not_applicable', applicable=False)))
        return 0
    metadata = json.loads((source/'capture_metadata.json').read_text())
    require(metadata['source_optimizer_updates'] == 100 and metadata['checkpoint'] == report['checkpoint'] and
            metadata['checkpoint_sha256'] == pins[report['checkpoint']] and metadata['capture_envs'] == list(range(8)),
            'Final100 capture identity differs')
    require(metadata['training_chain'] == report['training_chain'] and report['training_chain']['fresh_policy'] and
            report['training_chain']['run_completed'], 'Fresh completed source training required')
    captures = metadata['captures']
    require([r['env_id'] for r in captures] == list(range(8)), 'Complete captured cohort0..7 required')
    capture = next(r for r in captures if r['env_id'] == episode['env_id'])
    pose_path = (source/capture['path']).resolve()
    require(pose_path.parent == source and sha(pose_path) == capture['sha256'] and capture['reason'] == 'terminal_failure', 'Selected failure capture differs')
    settings = json.loads((source/'settings.json').read_text())
    require((settings['num_envs'], settings['horizon'], settings['updates'], settings['size'], settings['seed'], settings['device']) ==
            (1024, 32, 100, 'large', 7, 'cuda:0') and settings['specialist']['role'] == 'left', 'Source settings differ')
    source_run = Path(report['training_chain']['run'])
    source_contract = json.loads((source_run/'training_contract.json').read_text())
    source_control = source_contract['native_backend']['control']
    finger_native, _ = mapping(source_control)
    for path in (pose_path, source/'capture_metadata.json', source/'settings.json', source_run/'training_contract.json'):
        value = sha(path)
        require(str(path) not in pins or pins[str(path)] == value, 'Existing capture pin differs: '+str(path))
        pins[str(path)] = value
    # Keep the native SDK first on the applicable path. The no-failure path above
    # creates no simulator and imports neither NumPy/Torch nor Isaac Gym.
    import isaacgym
    import numpy as np
    import torch
    from guitar_learning.core.control import ACTIVE_NAMES, LEFT_HAND_NAMES
    from guitar_learning.training.gpu_pool import GpuPool
    from guitar_learning.training.recording import project_source_paths
    require(source_control['action_order'] == list(ACTIVE_NAMES) and
            source_control['action_codec']['incremental_joint_names'] == list(LEFT_HAND_NAMES), 'Canonical action ordering differs')
    with np.load(str(pose_path), allow_pickle=False) as archive:
        original = {key: archive[key] for key in archive.files}
    validate_capture(original, len(metadata['body_names']), episode)
    require(len(metadata['body_names']) == 106 and metadata['joint_names'] == source_control['joint_names'] and
            metadata['capture_hz'] == 60 and metadata['source_physics_hz'] == 240, 'Source capture layout differs')
    steps = len(original['clock'])-1
    require(steps == episode['steps'] and 0 < steps <= 1969 and bool((original['action'][0] == 0).all()), 'Source first-episode prefix/sentinel differs')
    settings = copy.deepcopy(settings); settings['num_envs'] = 4
    write(out/'settings.json', settings)
    pins[str(out/'settings.json')] = sha(out/'settings.json')
    write(out/'inputs_before.json', pins)
    torch.set_num_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    pool, failure, cleanup = None, None, []
    active, first_end, padding_resets = [True]*4, [None]*4, [0]*4
    frames = [{key: [] for key in original} for _ in CASES]
    for row in frames:
        row['global_physics_step'] = []
    ticks, pending = 0, []
    started = time.perf_counter()
    def lifecycle(stage):
        path = out/'lifecycle.json'
        path.with_suffix('.tmp').write_text(json_io.dumps(dict(stage=stage, control_ticks=ticks,
            source_prefix_steps=steps, wall_s=time.perf_counter()-started))+'\n')
        path.with_suffix('.tmp').replace(path)
    def capture_rows(ids, actions):
        env = pool.environment
        indices = torch.tensor(ids, device=env.device)
        values = {key: env.snapshot[key][indices].detach().cpu().numpy()
                  for key in ('body_state', 'q', 'qd', 'target')}
        values.update(action=actions[indices].detach().cpu().numpy(), clock=env.clock[indices].cpu().numpy())
        for key, note in (('left_count', 'left'), ('near_count', 'near_done'), ('contact_count', 'contact_done')):
            values[key] = env.note[note][indices].sum(-1).cpu().numpy()
        values['candidate_count'] = env.candidate[indices].sum(-1).cpu().numpy()
        for offset, index in enumerate(ids):
            for key, value in values.items():
                frames[index][key].append(value[offset].copy())
            frames[index]['global_physics_step'].append(pool.scene.physics_steps)
    lifecycle('creating_pool')
    try:
        pool = GpuPool(settings, out)
        require(pool.controller.contract == source_control and pool.scene.body_names == metadata['body_names'], 'Replay control/body contract differs')
        for key in ('reward', 'task', 'diagnostics'):
            require(pool.contract[key] == source_contract[key], 'Replay environment contract differs: '+key)
        pool.set_curriculum(report['curriculum_progress'])  # Static source weights; no coordinator or advancement.
        write(out/'control_contract.json', pool.controller.contract)
        write(out/'visual_initial.json', pool.scene.contract['initial'])
        capture_rows(list(range(4)), torch.zeros(4, 39, device=pool.scene.device))
        with torch.no_grad():
            for tick in range(1, steps+1):
                if pending:
                    pool.reset(pending)
                    for index in pending:
                        padding_resets[index] += 1
                requested = case_actions(original['action'][tick], source_control['action_order'], active)
                actions = torch.as_tensor(requested, device=pool.scene.device, dtype=pool.scene.q.dtype)
                live = [i for i, value in enumerate(active) if value]
                result = pool.step(actions)
                require(bool(torch.isfinite(result[1]).all()) and bool(torch.isfinite(result[2]).all()) and
                        not bool(result[4].any()), 'Nonfinite replay metrics or unexpected truncation')
                if live:
                    capture_rows(live, actions)
                ended = {e['env_id']: e for e in result[5]}
                pending = result[3].nonzero().flatten().cpu().tolist()
                require(set(ended) == set(pending), 'Replay first-end identity differs')
                for index in pending:
                    if active[index]:
                        first_end[index] = ended[index]
                        active[index] = False
                ticks = tick
                if tick % 60 == 0:
                    lifecycle('replaying')
        torch.cuda.synchronize(pool.scene.device)
        lifecycle('prefix_complete')
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc())
        traceback.print_exc()
    finally:
        if pool is not None:
            try:
                torch.cuda.synchronize(pool.scene.device)
            except BaseException as error:
                cleanup.append(dict(component='preclose_sync', message=repr(error)))
            try:
                pool.close()
            except BaseException as error:
                cleanup.append(dict(component='pool.close', message=repr(error)))
    scene = pool.scene.diagnostics if pool is not None and pool.scene is not None else None
    native_ok = bool(scene and scene['closed'] and scene['physx_use_gpu'] and scene['use_gpu_pipeline'] and
        scene['simulator_count'] == 1 and scene['environment_count'] == scene['num_envs'] == 4 and scene['physics_steps'] == 4*ticks and
        set(scene['tensor_devices']) == {'dof', 'roots', 'bodies', 'contact_force', 'jacobian'} and
        all(device == 'cuda:0' for device in scene['tensor_devices'].values()))
    changed = [name for name, value in pins.items() if not Path(name).is_file() or sha(name) != value]
    missing = sorted(project_source_paths(list(sys.modules.items()))-set(pins))
    complete = failure is None and not(cleanup or changed or missing) and native_ok and ticks == steps
    cases, saved = [], []
    for index, name in enumerate(CASES):
        if not frames[index]['clock']:
            continue
        arrays = {key: np.stack(value) for key, value in frames[index].items()}
        count = len(arrays['clock'])
        require(np.array_equal(arrays['clock'], np.arange(count)*4) and
                all(bool(np.isfinite(value).all()) for value in arrays.values()), 'Captured first-prefix clock/nonfinite data')
        require(np.max(np.abs(np.linalg.norm(arrays['body_state'][..., 3:7], axis=-1)-1)) < 1e-3,
                'Captured quaternion is not near unit length')
        expected_actions = np.zeros_like(arrays['action'])
        for frame in range(1, count):
            expected_actions[frame] = case_actions(original['action'][frame], source_control['action_order'], [True]*4)[index]
        require(np.array_equal(arrays['action'], expected_actions), 'Captured action differs from predeclared case')
        endpoint = first_end[index]
        if endpoint is not None:
            require(count == endpoint['steps']+1, 'First-end/capture frame mismatch')
        path = out/('case_%d_%s.npz' % (index, name))
        np.savez_compressed(str(path), **arrays)
        saved.append(arrays)
        failed = endpoint is not None and endpoint['reason'] == 'terminal_failure'
        cases.append(dict(case=name, env_id=index, path=path.name, sha256=sha(path), frames=count,
            first_episode=endpoint, observed_first_steps=count-1, padding_resets=padding_resets[index],
            outcome='physical_failure' if failed else 'timeline_complete' if endpoint is not None else 'right_censored',
            recorded_action_case_verified=True, full_song_success_claim=False, first_episode_only=True))
    comparison = reference_errors(original, saved[0], finger_native, episode, first_end[0]) if len(saved) == 4 else None
    write(out/'capture_metadata.json', dict(schema='guitar_learning.gpu_recorded_action_ablation_capture.v1',
        body_names=metadata['body_names'], joint_names=metadata['joint_names'], source_capture=str(pose_path),
        source_capture_sha256=capture['sha256'], source_env_id=episode['env_id'], source_prefix_steps=steps,
        source_physics_hz=240, capture_hz=60, body_frame=metadata['body_frame'], cases=cases,
        action_order=source_control['action_order'], source_curriculum_progress=report['curriculum_progress'],
        scope='Only first episode frames are retained. Dead rows are selectively reset before further stepping and receive zero39 padding commands. Rows without an observed end are right-censored at recorded prefix end. A native timeline endpoint, if observed at the final source tick, is reported separately; no67-note musical success or policy-generalization claim.'))
    write(out/'report.json', dict(completed=complete, applicable=True, status='completed' if complete else 'failed',
        source_evaluation=str(source), source_env_id=episode['env_id'], source_episode=episode,
        source_prefix_steps=steps, control_ticks=ticks, native_physics_steps=scene['physics_steps'] if scene else None,
        expected_physics_steps=4*steps, batched_environment_transitions=4*ticks,
        failure=failure, cleanup_errors=cleanup, changed_inputs=changed, missing_import_pins=missing,
        gpu_scene=scene, cases=cases, original_action_case_reproduction=comparison,
        source_policy_inference_steps=0, PPO_updates=0, wall_s=time.perf_counter()-started,
        scope='Four fixed recorded-action ablations in newN4 GPU physics. Arms/wrists/right actions match source while each first episode is alive; finished padding rows reset and use zero39. Batch/contact differences versus sourceN1024 prevent a precise causal or same-policy generalization interpretation. No gain, physics, reward, safety or source changes.'))
    lifecycle('report_written')
    print(json_io.dumps(dict(completed=complete, source_env_id=episode['env_id'], control_ticks=ticks,
        outcomes=[r['outcome'] for r in cases])))
    return 0 if complete else 1


if __name__ == '__main__':
    sys.exit(main())
