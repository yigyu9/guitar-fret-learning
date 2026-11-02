"""Diagnostic angle requests in the unchanged native task, not a learned policy."""
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

MANIFEST = STUDY/'입력/native_response_v1.json'
OUT = STUDY/'로그/native_response_v1'
BASE = TRAIN/'로그/parallel_v1/pilot_env2'
CAPTURE = OUT/'capture'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(expected=None):
    if expected is not None and sha(MANIFEST) != expected:
        raise ValueError('Diagnostic manifest identity changed')
    m = json.loads(MANIFEST.read_text())
    if (m.get('schema') != 'multi_press.native_finger_response.v1' or
            m.get('num_envs') != 1 or m.get('controls') != 330 or
            m.get('degrees') != 15 or m.get('training_updates') != 0):
        raise ValueError('Unexpected diagnostic protocol')
    for path, expected in m['pins'].items():
        if sha(path) != expected:
            raise ValueError('Diagnostic input changed: '+path)
    return m


def smooth(value):
    value = min(1., max(0., value))
    return value**3*(10-15*value+6*value**2)


def fractions(time_s):
    """15deg: index rise/hold, middle rise/hold, both return. No state writes."""
    if not math.isfinite(time_s) or not 0 <= time_s <= 5.5+1e-9:
        raise ValueError('Finite bounded episode time required')
    returning = 1-smooth((time_s-4.25)/1.)
    return smooth((time_s-.5)/1.)*returning, smooth((time_s-2.25)/1.)*returning


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
        groups = [[pool.scene.names.index('LH:'+finger+suffix) for suffix in ('1_x', '2', '3')]
                  for finger in ('index', 'middle')]
        action_groups = [[int((controller.active == joint).nonzero().item()) for joint in joints] for joints in groups]
        for group in action_groups:
            if bool((ref[group]+math.radians(15) > controller.action_high[group]).any()):
                raise ValueError('15deg request exceeds unchanged action bounds')
        cameras = _create_cameras(pool.scene, gymapi)
        for name in cameras:
            videos[name] = _encoder(CAPTURE/(name+'.mp4'))
        capture = _EnvZeroCapture(pool, gymapi, np, cameras, videos)
        for tick in range(330):
            desired = ref[None].clone()
            portion = fractions((tick+1)/60.)
            for group, value in zip(action_groups, portion):
                desired[:, group] += math.radians(15)*value
            action = trajectory_actions(desired, ref, controller.action_low, controller.action_high)
            observation, reward, cost, terminated, truncated, episodes = pool.step(action)
            requested.append(desired[0].detach().cpu().numpy().copy())
            capture.record(tick, reward, cost, terminated, truncated, episodes)
            if bool(terminated[0] or truncated[0]):
                break
        if capture.episode is None:
            raise RuntimeError('Diagnostic did not end at original task boundary')
        (CAPTURE/'episode_env0000.json').write_text(json.dumps(capture.episode, ensure_ascii=False, indent=2))
        (CAPTURE/'metadata.json').write_text(json.dumps(dict(joint_names=pool.scene.names,
            body_names=pool.scene.body_names, action_names=pool.contract['action']['names'],
            reference=controller.reference.detach().cpu().tolist(),
            requested_joint_groups=groups, requested_action_groups=action_groups,
            frames=len(capture.frame_times_s), frame_times_s=capture.frame_times_s,
            source_manifest_sha256=sha(MANIFEST), resource_before=resource,
            control='Diagnostic +15deg MCP/PIP/DIP ramp/hold/return; no learned actions',
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
            all(code == 0 for code in codes.values()) and capture and capture.episode)
        episode = capture.episode if capture else None
        protocol_completed = bool(episode and len(capture.samples) == 330 and episode['reason'] == 'timeline_complete')
        outcome = 'protocol_completed' if protocol_completed else (
            'physical_failure' if episode and episode['termination']['physical_failure'] else
            'wrist_failure' if episode and episode['termination']['wrist_failure'] else 'incomplete_or_error')
        (CAPTURE/'report.json').write_text(json.dumps(dict(completed=captured and protocol_completed,
            capture_completed=captured, protocol_completed=protocol_completed, outcome=outcome, failure=failure,
            cleanup_errors=errors, encoding_exit_codes=codes, lifecycle_verified=lifecycle, gpu_scene=audit,
            native_pixels=bool(capture and capture.frame_times_s), frames=len(capture.frame_times_s) if capture else 0,
            training_updates=0, policy_evaluation=False, actual_actuator_diagnostic=True,
            episode=episode), ensure_ascii=False, indent=2))
        if failure is None and not captured:
            raise RuntimeError('Diagnostic capture cleanup/lifecycle failed')


def parent():
    expected = sha(MANIFEST)
    manifest = verify(expected)
    ready, reason, resource = readiness()
    if not ready:
        raise RuntimeError('Diagnostic resource gate: '+reason)
    OUT.mkdir(exist_ok=False)
    baseline = _state(); final = None; process = None; failure = None; capture_report = None
    (OUT/'single_before.json').write_text(json.dumps(baseline, ensure_ascii=False, indent=2))
    command = [manifest['python'], '-B', str(ROOT/'scripts/tab2body.py'), '--cache-root',
               str(ROOT/'.runtime/cache'), 'run', str(Path(__file__).resolve()), '--child']
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
    args = parser.parse_args()
    child() if args.child else parent()
