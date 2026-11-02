"""Re-fit both targets at the actual native arrival, then request angles only."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

STUDY = Path(__file__).resolve().parents[1]
MULTI = STUDY.parent
TRAIN = MULTI/'학습_인접2지_v1'
sys.path.insert(0, str(TRAIN/'도구'))
from study_queue_v2 import ROOT, GPU_UUID, gpu_query
from parallel_resources_v1 import readiness, _state, SINGLE_STATE
from parallel_queue_v1 import impact, stop_own_group

CONDITION = 'nominal'
MANIFEST = STUDY/'입력/goal_nominal_v1.json'
OUT = STUDY/'로그/goal_nominal_v1'
BASE = TRAIN/'로그/parallel_v1/pilot_env2'
CAPTURE = OUT/'capture'
SOURCE_MANIFEST = MULTI/'미동작_원인검증_v2/입력/native_response_v1.json'
SOURCE_SHA = 'd61038dcc612ee6ae331f8042e43dbaacda698ef3125d8debdcb627ffc303e36'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(expected=None):
    if expected is not None and sha(MANIFEST) != expected:
        raise ValueError('Diagnostic manifest identity changed')
    m = json.loads(MANIFEST.read_text())
    expected_height = dict(nominal=-.0005, deeper=-.0009, tracking=-.0005)[CONDITION]
    if (m.get('schema') != 'multi_press.native_goal_press.v1' or m.get('condition') != CONDITION or
            m.get('num_envs') != 1 or m.get('controls') != 330 or
            m.get('height_m') != expected_height or m.get('training_updates') != 0 or
            m.get('tracking_correction') is not (CONDITION == 'tracking')):
        raise ValueError('Unexpected diagnostic protocol')
    if sha(SOURCE_MANIFEST) != SOURCE_SHA:
        raise ValueError('Sealed parent diagnostic identity changed')
    parent = json.loads(SOURCE_MANIFEST.read_text())
    required = [Path(__file__).resolve(), STUDY/'도구/live_geometry.py', SOURCE_MANIFEST]
    if (any(str(path) not in m.get('pins', {}) for path in required) or
            any(m['pins'].get(name) != value for name, value in parent['pins'].items())):
        raise ValueError('Original pins and new diagnostic sources must be preserved')
    for path, expected in m['pins'].items():
        if sha(path) != expected:
            raise ValueError('Diagnostic input changed: '+path)
    return m


def smooth(value):
    value = min(1., max(0., value))
    return value**3*(10-15*value+6*value**2)


def fraction(time_s):
    """Approach before notes, hold the shared window, release after note end."""
    if not math.isfinite(time_s) or not 0 <= time_s <= 5.5+1e-9:
        raise ValueError('Finite bounded episode time required')
    return smooth((time_s-.5)/2.)*(1-smooth((time_s-4.85)/.65))


def expansion_allowed(report):
    measured = report.get('impact', {})
    ratio = measured.get('maximum_elapsed_ratio')
    return bool(report.get('capture_completed') and report.get('protocol_completed') and
        report.get('completed') and report.get('final_state_verified') and not report.get('failure') and
        not measured.get('inspection_errors') and not measured.get('severe') and
        not isinstance(ratio, bool) and isinstance(ratio, (int, float)) and
        math.isfinite(ratio) and 0 < ratio < 1.25)


def teacher_allowed(episode, captured, protocol_completed):
    if not episode or not captured or not protocol_completed:
        return False
    pair = episode.get('simultaneous_press', {})
    return bool(pair.get('success') and pair.get('full_safe') and
        pair.get('source_score_window_s') == [3.3, 4.8] and
        pair.get('observed_s', 0)+1e-9 >= 1.5 and pair.get('clean_s', 0)+1e-9 >= 1.5 and
        pair.get('longest_clean_s', 0)+1e-9 >= 1.5 and pair.get('wrong_union_s') == 0 and
        pair.get('unsafe_s') == 0 and pair.get('individual_achievements') == [True, True] and
        episode.get('reason') == 'timeline_complete')


def child():
    expected = sha(MANIFEST)
    manifest = verify(expected)
    ready, reason, resource = readiness()
    if not ready or os.environ.get('CUDA_VISIBLE_DEVICES') != GPU_UUID:
        raise RuntimeError('Diagnostic refused before Gym import: '+reason)
    import isaacgym
    from isaacgym import gymapi
    import numpy as np
    import torch
    from guitar_learning.portability import localize, portable
    from guitar_learning.training import finger_skill_runner as runner
    from guitar_learning.training.rollout import GpuPool
    from guitar_learning.tool.demonstration.render_finger_skill import _create_cameras, _encoder, _EnvZeroCapture
    from guitar_learning.tool.validation.hand_contact_probe import GraphicsGym, finish_video
    from guitar_learning.tool.validation.press_acquisition import trajectory_actions
    from guitar_learning.tool.validation.press_acquisition import integral_tracking_offset
    from pair_environment import PairEnvironment
    payload = torch.load(BASE/'J/final.pt', map_location='cpu', weights_only=False)
    runner._validate_metadata_schema(payload['metadata'])
    runner._validate_pins(payload['metadata'])
    settings = localize(payload['metadata']['settings'])
    if (settings['experiment']['case_id'] != 'index_middle_same' or
            settings['experiment']['common_window_s'] != [3.3, 4.8] or
            settings['song_training']['episode_duration_s'] != 5.5):
        raise ValueError('Diagnostic task differs from source model task')
    settings['num_envs'] = 1
    CAPTURE.mkdir(exist_ok=False)
    (CAPTURE/'settings.json').write_text(json.dumps(settings, ensure_ascii=False, indent=2))
    torch.set_num_threads(1)
    original = gymapi.acquire_gym
    pool = capture = None
    videos = {}; codes = {}; errors = []; failure = None; requested = []
    teacher = {key: [] for key in ('state', 'events', 'mask', 'priority_events', 'priority_mask')}
    fit_report = None; geometry_failure = None
    class PairPool(GpuPool):
        environment_class_override = PairEnvironment
    try:
        gymapi.acquire_gym = lambda: GraphicsGym(original())
        try:
            pool = PairPool(settings, CAPTURE/'scene')
        finally:
            gymapi.acquire_gym = original
        # Exact native task/control contract; no model identity conversion.
        if portable(pool.contract) != payload['identity']['architecture']['contract']:
            raise ValueError('Diagnostic environment/control differs from original model')
        pool.environment.set_evaluation(enabled=True, full_song=True)
        pool.observation = pool.reset()[0]
        controller = pool.controller
        ref = controller.reference[controller.active]
        groups = [[pool.scene.names.index('LH:'+finger+suffix) for suffix in ('1_x', '1_z', '2', '3')]
                  for finger in ('index', 'middle')]
        action_groups = [[int((controller.active == joint).nonzero().item()) for joint in joints] for joints in groups]
        assigned = [i for group in groups for i in group]
        assigned_actions = [i for group in action_groups for i in group]
        start_angles = goal_angles = None
        correction = torch.zeros(1, 39, device=pool.scene.device)
        correction_mask = torch.zeros(1, 39, dtype=torch.bool, device=pool.scene.device)
        correction_mask[:, assigned_actions] = True
        cameras = _create_cameras(pool.scene, gymapi)
        for name in cameras:
            videos[name] = _encoder(CAPTURE/(name+'.mp4'))
        capture = _EnvZeroCapture(pool, gymapi, np, cameras, videos)
        for tick in range(330):
            if tick == 30:
                snapshot = pool.scene.snapshot()
                if (bool(pool.environment._control_failures().any()) or
                        bool((pool.environment.guide['delta'].abs() > 1e-6).any())):
                    geometry_failure = 'preparation_failed'
                    break
                from live_geometry import fit_snapshot
                pins = dict(manifest['pins']); pins[str(MANIFEST)] = expected
                arrival, case, fit_report = fit_snapshot(
                    snapshot['q'][0].detach().cpu().numpy(), snapshot['qd'][0].detach().cpu().numpy(),
                    snapshot['body_state'][0].detach().cpu().numpy(), pool.scene.names,
                    pool.scene.body_names, pool.contract, int(snapshot['physics_step'][0]), pins,
                    height=manifest['height_m'], max_nfev=60)
                (CAPTURE/'actual_arrival.json').write_text(json.dumps(arrival, ensure_ascii=False, indent=2))
                (CAPTURE/'geometry_fit.json').write_text(json.dumps(fit_report, ensure_ascii=False, indent=2))
                if not fit_report['both_geometry']:
                    geometry_failure = 'no_geometry_candidate'
                    break
                start_angles = snapshot['q'][0, assigned].clone()
                goal_angles = torch.as_tensor(fit_report['q105'], device=pool.scene.device,
                                               dtype=ref.dtype)[assigned]
                if bool(((goal_angles < controller.action_low[assigned_actions]) |
                         (goal_angles > controller.action_high[assigned_actions])).any()):
                    raise ValueError('Actual-arrival target exceeds unchanged action bounds')
            desired = ref[None].clone()
            if goal_angles is not None:
                desired[:, assigned_actions] = start_angles+fraction((tick+1)/60.)*(goal_angles-start_angles)
                if manifest['tracking_correction']:
                    actual = pool.scene.snapshot()['q'][:, controller.active]
                    correction = integral_tracking_offset(correction, desired, actual,
                        controller.action_low, controller.action_high, correction_mask)
                    desired = torch.where(correction_mask, desired+correction, desired)
            for key in teacher:
                teacher[key].append(pool.observation[key][0].detach().cpu().numpy().copy())
            action = trajectory_actions(desired, ref, controller.action_low, controller.action_high)
            observation, reward, cost, terminated, truncated, episodes = pool.step(action)
            requested.append(desired[0].detach().cpu().numpy().copy())
            capture.record(tick, reward, cost, terminated, truncated, episodes)
            if bool(terminated[0] or truncated[0]):
                break
        if capture.episode is None and geometry_failure is None:
            raise RuntimeError('Diagnostic did not end at original task boundary')
        (CAPTURE/'episode_env0000.json').write_text(json.dumps(capture.episode, ensure_ascii=False, indent=2))
        (CAPTURE/'metadata.json').write_text(json.dumps(dict(joint_names=pool.scene.names,
            body_names=pool.scene.body_names, action_names=pool.contract['action']['names'],
            reference=controller.reference.detach().cpu().tolist(),
            requested_joint_groups=groups, requested_action_groups=action_groups,
            frames=len(capture.frame_times_s), frame_times_s=capture.frame_times_s,
            source_manifest_sha256=sha(MANIFEST), resource_before=resource,
            control='Diagnostic live-arrival finger8 FK goal ramp/hold/release; no learned policy',
            condition=CONDITION, geometry_failure=geometry_failure, geometric_height_m=manifest['height_m'],
            tracking_correction=manifest['tracking_correction'],
            teacher_observation_alignment='row i: observation before action i; poses row i is after4 physics substeps',
            training_updates=0, no_mid_episode_state_injection=True), ensure_ascii=False, indent=2))
        verify(expected)
    except BaseException as error:
        failure = repr(error)
        raise
    finally:
        gymapi.acquire_gym = original
        for name, process in videos.items():
            code, messages = finish_video(process); codes[name] = code
            errors.extend(messages)
        if capture and capture.samples:
            try:
                np.savez_compressed(CAPTURE/'poses_env0000.npz',
                    **{key: np.stack([row[key] for row in capture.samples]) for key in capture.samples[0]},
                    requested_active=np.stack(requested))
                np.savez_compressed(CAPTURE/'teacher_observations.npz',
                    **{key: np.stack(values) for key, values in teacher.items()},
                    action=np.stack([row['action'] for row in capture.samples]))
            except BaseException as error:
                errors.append('pose_save: '+repr(error))
        if pool:
            try:
                pool.close()
            except BaseException as error:
                errors.append('scene_close: '+repr(error))
        audit = pool.scene.diagnostics if pool and pool.scene else None
        lifecycle = bool(audit and audit.get('closed') and audit.get('physx_use_gpu') and
            audit.get('use_gpu_pipeline') and audit.get('simulator_count') == 1 and audit.get('environment_count') == 1)
        captured = bool(failure is None and not errors and lifecycle and len(codes) == 2 and
            all(code == 0 for code in codes.values()) and capture and capture.samples)
        episode = capture.episode if capture else None
        protocol_completed = bool(episode and len(capture.samples) == 330 and episode['reason'] == 'timeline_complete')
        eligible = teacher_allowed(episode, captured, protocol_completed)
        if geometry_failure:
            outcome = geometry_failure
        elif not captured:
            outcome = 'inspection_error'
        elif episode and episode['termination']['physical_failure']:
            outcome = 'physical_failure'
        elif episode and episode['termination']['wrist_failure']:
            outcome = 'wrist_failure'
        elif not protocol_completed:
            outcome = 'incomplete_episode'
        else:
            outcome = 'simultaneous_clean_success' if eligible else 'simultaneous_hold_failed'
        (CAPTURE/'report.json').write_text(json.dumps(dict(completed=captured and protocol_completed,
            capture_completed=captured, protocol_completed=protocol_completed, outcome=outcome, failure=failure,
            cleanup_errors=errors, encoding_exit_codes=codes, lifecycle_verified=lifecycle, gpu_scene=audit,
            native_pixels=bool(capture and capture.frame_times_s), frames=len(capture.frame_times_s) if capture else 0,
            training_updates=0, policy_evaluation=False, actual_target_approach_diagnostic=True,
            teacher_eligible=eligible, geometry_failure=geometry_failure,
            episode=episode), ensure_ascii=False, indent=2))
        if failure is None and not captured:
            raise RuntimeError('Diagnostic capture cleanup/lifecycle failed')


def parent():
    expected = sha(MANIFEST)
    manifest = verify(expected)
    if CONDITION != 'nominal':
        prior = Path(manifest['prior_guard_report']).resolve()
        prior.relative_to(STUDY/'로그')
        expected_prior = STUDY/'로그/goal_nominal_v1/guard_report.json'
        if CONDITION == 'tracking' and (STUDY/'로그/goal_deeper_v1').exists():
            expected_prior = STUDY/'로그/goal_deeper_v1/guard_report.json'
        if (prior != expected_prior or str(prior) not in manifest['pins'] or
                not expansion_allowed(json.loads(prior.read_text()))):
            raise RuntimeError('Additional target trial held: prior verified delay below25% required')
    ready, reason, resource = readiness()
    if not ready:
        raise RuntimeError('Diagnostic resource gate: '+reason)
    OUT.mkdir(exist_ok=False)
    baseline = _state(); final = None; process = None; failure = None; capture_report = None
    (OUT/'single_before.json').write_text(json.dumps(baseline, ensure_ascii=False, indent=2))
    command = [manifest['python'], '-B', str(ROOT/'scripts/tab2body.py'), '--cache-root',
               str(ROOT/'.runtime/cache'), 'run', str(Path(__file__).resolve()), '--child', '--condition', CONDITION]
    env = dict(os.environ, CUDA_VISIBLE_DEVICES=GPU_UUID, PYTHONDONTWRITEBYTECODE='1',
               OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    started = time.monotonic()
    try:
        with (OUT/'native.stdout.log').open('xb') as stream, (OUT/'resources.jsonl').open('x') as samples:
            process = subprocess.Popen(command, cwd=str(ROOT), env=env, stdout=stream,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            query_errors = 0
            while process.poll() is None:
                verify(expected); current = _state(); measured = impact(baseline, current)
                if measured['severe']:
                    raise RuntimeError('Existing sweep delay/error guard: '+repr(measured))
                if time.monotonic()-started > 240:
                    raise TimeoutError('Diagnostic wall-time limit exceeded')
                try:
                    row = next(r for r in gpu_query('uuid,memory.free,utilization.gpu', 'gpu') if r['uuid'] == GPU_UUID)
                    free = float(row['memory.free [MiB]'].split()[0])
                    if not math.isfinite(free) or free < 2048:
                        raise MemoryError('Diagnostic free GPU memory below2GiB')
                    query_errors = 0
                    samples.write(json.dumps(dict(epoch=time.time(), gpu=row, impact=measured,
                        single_finished=current['finished']))+'\n'); samples.flush()
                except (OSError, subprocess.TimeoutExpired, RuntimeError):
                    query_errors += 1
                    if query_errors >= 3:
                        raise RuntimeError('Repeated GPU monitoring failure')
                time.sleep(3)
        if process.wait() != 0:
            raise RuntimeError('Diagnostic child failed; see native.stdout.log')
        capture_report = json.loads((CAPTURE/'report.json').read_text())
        if not capture_report['capture_completed']:
            raise RuntimeError('Diagnostic capture incomplete')
        verify(expected); final = _state()
        if impact(baseline, final)['severe']:
            raise RuntimeError('Final existing sweep guard failed')
    except BaseException as error:
        failure = repr(error)
        if process:
            stop_own_group(process)
        raise
    finally:
        final = final if final is not None else json.loads(SINGLE_STATE.read_text())
        (OUT/'single_after.json').write_text(json.dumps(final, ensure_ascii=False, indent=2))
        protocol_completed = bool(capture_report and capture_report['protocol_completed'])
        report = dict(completed=failure is None and protocol_completed, failure=failure, wall_s=time.monotonic()-started,
            command=command, resource_before=resource, impact=impact(baseline, final),
            capture_completed=bool(capture_report and capture_report['capture_completed']),
            protocol_completed=protocol_completed, outcome=capture_report.get('outcome') if capture_report else 'inspection_error',
            source_manifest_sha256=expected, final_state_verified=failure is None, training_updates=0)
        (OUT/'guard_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
        print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--child', action='store_true')
    parser.add_argument('--condition', choices=('nominal', 'deeper', 'tracking'), default='nominal')
    args = parser.parse_args()
    CONDITION = args.condition
    MANIFEST = STUDY/('입력/goal_'+CONDITION+'_v1.json')
    OUT = STUDY/('로그/goal_'+CONDITION+'_v1')
    CAPTURE = OUT/'capture'
    child() if args.child else parent()
