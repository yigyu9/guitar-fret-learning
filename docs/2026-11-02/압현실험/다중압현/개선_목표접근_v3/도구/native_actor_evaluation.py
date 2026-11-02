"""Guarded native closed-loop evaluation of a fresh actor-only B1 artifact."""
import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

STUDY = Path(__file__).resolve().parents[1]
TRAIN = STUDY.parent/'학습_인접2지_v1'
sys.path.insert(0, str(TRAIN/'도구'))
from native_goal_press import readiness, _state, impact, stop_own_group, expansion_allowed
from study_queue_v2 import ROOT, GPU_UUID, gpu_query

SCHEMA = 'multi_press.native_actor_evaluation.v1'
FIELDS = ('state', 'events', 'mask', 'priority_events', 'priority_mask')
PRIOR = STUDY/'로그/goal_nominal_v1/guard_report.json'
NOMINAL = STUDY/'입력/goal_nominal_v1.json'
PILOT = TRAIN/'로그/parallel_v1/pilot_env2/J/final.pt'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def validate_bootstrap_links(manifest):
    report_path, plan_path = Path(manifest['bootstrap_report']), Path(manifest['bootstrap_plan'])
    for path in (report_path, plan_path):
        path.resolve().relative_to(STUDY)
        if manifest['pins'].get(str(path)) != sha(path):
            raise ValueError('Pinned bootstrap report and plan required')
    report = read(report_path)
    if (not all(report.get(k) is True for k in ('completed', 'cpu_only', 'std_critic_buffers_unchanged')) or
            report.get('optimizer_rng_transferred') is not False or
            report.get('artifact') != manifest['actor_artifact'] or
            report.get('artifact_sha256') != manifest['actor_sha256'] or
            report.get('plan') != str(plan_path) or report.get('plan_sha256') != sha(plan_path) or
            any(manifest['pins'].get(k) != value for k, value in report['source_sha256'].items())):
        raise ValueError('Bootstrap artifact/report/plan/source SHA linkage differs')
    return report


def verify_manifest(path, expected_sha=None):
    path = Path(path).resolve()
    path.relative_to(STUDY/'입력')
    if expected_sha is not None and sha(path) != expected_sha:
        raise ValueError('Actor evaluation manifest changed')
    manifest = read(path)
    if (manifest.get('schema') != SCHEMA or manifest.get('sealed') is not True or
            manifest.get('num_envs') != 1 or manifest.get('controls') != 330 or
            manifest.get('training_updates') != 0 or
            manifest.get('policy_control') != 'deterministic_actor_only' or
            manifest.get('source_checkpoint') != str(PILOT) or
            manifest.get('prior_guard_report') != str(PRIOR)):
        raise ValueError('Sealed single-env deterministic actor evaluation required')
    Path(manifest['out']).resolve().relative_to(STUDY/'로그')
    Path(manifest['actor_artifact']).resolve().relative_to(STUDY/'로그')
    required = (Path(__file__).resolve(), STUDY/'도구/teacher_bootstrap.py',
        Path(manifest['actor_artifact']), Path(manifest['bootstrap_report']),
        Path(manifest['bootstrap_plan']), PRIOR, NOMINAL, PILOT,
        TRAIN/'도구/prepare.py', TRAIN/'도구/pair_environment.py')
    pins = manifest.get('pins', {})
    if any(str(item) not in pins for item in required):
        raise ValueError('All evaluation, lineage and guard sources must be pinned')
    if (pins[str(Path(manifest['actor_artifact']))] != manifest['actor_sha256'] or
            any(pins.get(k) != value for k, value in read(NOMINAL)['pins'].items())):
        raise ValueError('Original nominal pins and exact new actor SHA required')
    for name, value in pins.items():
        source = Path(name).resolve()
        source.relative_to(ROOT)
        if sha(source) != value:
            raise ValueError('Actor evaluation pinned input changed: '+name)
    validate_bootstrap_links(manifest)
    if not expansion_allowed(read(PRIOR)):
        raise ValueError('Prior nominal capture and verified delay below25% required')
    return manifest


def validate_settings(settings):
    expected = dict(updates=100, num_envs=64, horizon=32, seed=7, size='medium')
    if any(settings.get(key) != value for key, value in expected.items()):
        raise ValueError('Full100/64/H32/seed7 medium settings required before capture')
    spec = settings['finger_skill']
    if (spec['planned_transitions'] != 204800 or spec['full_song_after'] != 51200 or
            settings['song_training']['control_ticks'] != 330 or
            settings['song_training']['episode_duration_s'] != 5.5 or
            settings['song_training']['target_count'] != 2 or
            settings['experiment']['case_id'] != 'index_middle_same' or
            settings['experiment']['common_window_s'] != [3.3, 4.8] or
            settings['experiment'].get('improvement') is not None):
        raise ValueError('Original E0 pair task and full exposure contract required')
    result = copy.deepcopy(settings)
    result['num_envs'] = 1
    return result


def capture_contract(actual, expected):
    from guitar_learning.portability import portable
    if portable(actual) != portable(expected):
        raise ValueError('Actual native pool differs from the complete projected E0 actor contract')


def evaluation_outcome(episode, captured, protocol):
    if not captured:
        return 'inspection_error'
    termination = (episode or {}).get('termination', {})
    if termination.get('physical_failure'):
        return 'physical_failure'
    if termination.get('wrist_failure'):
        return 'wrist_failure'
    if not protocol:
        return 'incomplete_episode'
    return 'policy_simultaneous_clean_success' if episode.get('simultaneous_press', {}).get('success') else 'policy_hold_failed'


def policy_control_step(policy, pool, tick, capture, observations):
    """Observe before action; capture the same action at its actual native endpoint."""
    import torch
    before = {key: pool.observation[key].detach().clone() for key in FIELDS}
    with torch.no_grad():
        decision = policy.act(**before, deterministic=True)
    action = decision['action']
    if (action.shape != (1, 39) or not bool(torch.isfinite(action).all()) or
            bool((action.abs() > 1).any()) or bool((action[:, 33:] != 0).any())):
        raise ValueError('Finite bounded original J33 policy action required')
    expected_step = 4*(tick+1)
    observation, reward, cost, terminated, truncated, episodes = pool.step(action)
    if (int(pool.scene.snapshot()['physics_step'][0]) != expected_step or
            not torch.equal(pool.environment.action, action)):
        raise ValueError('Policy action and consecutive native endpoint mismatch')
    for key in FIELDS:
        observations[key].append(before[key][0].cpu().numpy().copy())
    observations['action'].append(action[0].detach().cpu().numpy().copy())
    capture.record(tick, reward, cost, terminated, truncated, episodes)
    return bool(terminated[0] or truncated[0])


def child(manifest_path):
    manifest_path = Path(manifest_path).resolve()
    expected_sha = sha(manifest_path)
    manifest = verify_manifest(manifest_path, expected_sha)
    ready, reason, resource = readiness()
    if not ready or os.environ.get('CUDA_VISIBLE_DEVICES') != GPU_UUID:
        raise RuntimeError('Actor evaluation refused before Gym import: '+reason)
    import isaacgym
    from isaacgym import gymapi
    import numpy as np
    import torch
    from guitar_learning.portability import portable
    from guitar_learning.training import finger_skill_runner as runner
    from guitar_learning.training.rollout import GpuPool
    from guitar_learning.tool.demonstration.render_finger_skill import _create_cameras, _encoder, _EnvZeroCapture
    from guitar_learning.tool.validation.hand_contact_probe import GraphicsGym, finish_video
    from pair_environment import PairEnvironment
    from prepare import load_cases, make_settings
    from teacher_bootstrap import new_policy, load_actor_artifact, target_contract, actor_parameters
    source = torch.load(PILOT, map_location='cpu', weights_only=False)
    runner._validate_metadata_schema(source['metadata'])
    runner._validate_pins(source['metadata'])
    expected_contract = target_contract(source['identity']['architecture']['contract'])
    case = next(case for case in load_cases() if case['case_id'] == 'index_middle_same')
    bundle = TRAIN/'입력/song_bundles/index_middle_same'
    full_settings = make_settings(case, bundle, updates=100, num_envs=64, horizon=32, size='medium', seed=7)
    settings = validate_settings(full_settings)
    out = Path(manifest['out'])/'capture'
    out.mkdir(exist_ok=False)
    write(out/'full_training_settings.json', portable(full_settings))
    write(out/'settings.json', portable(settings))
    pins = dict(manifest['pins']); pins[str(manifest_path)] = expected_sha
    write(out/'inputs_before.json', pins)
    torch.set_num_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    original = gymapi.acquire_gym
    pool = capture = policy = None
    videos, codes, cleanup = {}, {}, []
    failure = None
    unchanged = fresh_unchanged = False
    observations = {key: [] for key in FIELDS+('action',)}
    class PairPool(GpuPool):
        environment_class_override = PairEnvironment
    try:
        gymapi.acquire_gym = lambda: GraphicsGym(original())
        try:
            pool = PairPool(settings, out/'scene')
        finally:
            gymapi.acquire_gym = original
        capture_contract(pool.contract, expected_contract)
        write(out/'training_contract.json', portable(pool.contract))
        policy = new_policy(expected_contract)
        actor_names = set(actor_parameters(policy))
        fresh = {name: value.detach().clone() for name, value in policy.state_dict().items()
                 if name not in actor_names}
        load_actor_artifact(policy, manifest['actor_artifact'], expected_contract, manifest['actor_sha256'])
        fresh_unchanged = all(torch.equal(policy.state_dict()[name], value) for name, value in fresh.items())
        if not fresh_unchanged:
            raise ValueError('Actor loader changed fresh std, critic or buffers')
        policy = policy.to(settings['device']).eval()
        initial_model = {key: value.detach().clone() for key, value in policy.state_dict().items()}
        pool.environment.set_evaluation(enabled=True, full_song=True)
        pool.observation = pool.reset()[0]
        cameras = _create_cameras(pool.scene, gymapi)
        for name in cameras:
            videos[name] = _encoder(out/(name+'.mp4'))
        capture = _EnvZeroCapture(pool, gymapi, np, cameras, videos)
        for tick in range(330):
            if policy_control_step(policy, pool, tick, capture, observations):
                break
        if capture.episode is None:
            raise RuntimeError('No completed first native policy episode')
        unchanged = all(torch.equal(policy.state_dict()[name], value) for name, value in initial_model.items())
        if not unchanged:
            raise ValueError('Evaluation mutated policy weights or buffers')
        write(out/'episode_env0000.json', capture.episode)
        verify_manifest(manifest_path, expected_sha)
    except BaseException as error:
        failure = repr(error)
        raise
    finally:
        gymapi.acquire_gym = original
        for name, process in videos.items():
            code, errors = finish_video(process); codes[name] = code
            cleanup.extend(errors)
        if capture and capture.samples:
            try:
                np.savez_compressed(out/'poses_env0000.npz',
                    **{key: np.stack([row[key] for row in capture.samples]) for key in capture.samples[0]})
                np.savez_compressed(out/'policy_observations.npz',
                    **{key: np.stack(value) for key, value in observations.items()})
            except BaseException as error:
                cleanup.append('raw_capture: '+repr(error))
        if pool:
            try:
                pool.close()
            except BaseException as error:
                cleanup.append('scene_close: '+repr(error))
        diagnostic = pool.scene.diagnostics if pool and pool.scene else None
        lifecycle = bool(diagnostic and diagnostic.get('closed') and diagnostic.get('physx_use_gpu') and
            diagnostic.get('use_gpu_pipeline') and diagnostic.get('simulator_count') == 1 and
            diagnostic.get('environment_count') == 1)
        changed = [name for name, value in pins.items() if not Path(name).is_file() or sha(name) != value]
        captured = bool(failure is None and not cleanup and lifecycle and unchanged and fresh_unchanged and
            not changed and len(codes) == 2 and all(value == 0 for value in codes.values()) and capture and capture.samples)
        episode = capture.episode if capture else None
        protocol = bool(episode and len(capture.samples) == 330 and len(capture.frame_times_s) == 165 and
                        episode.get('reason') == 'timeline_complete')
        metadata = dict(schema=SCHEMA, actor_artifact=manifest['actor_artifact'], actor_sha256=manifest['actor_sha256'],
            source_manifest_sha256=expected_sha, resource_before=resource, training_updates=0,
            policy_evaluation=True, deterministic=True, actual_target_approach_diagnostic=False,
            no_mid_episode_state_injection=True, observation_alignment='row i before action i; poses row i after4 physics substeps',
            frames=len(capture.frame_times_s) if capture else 0,
            frame_times_s=capture.frame_times_s if capture else [],
            joint_names=pool.scene.names if pool else [], body_names=pool.scene.body_names if pool else [],
            source_physics_hz=240, capture_hz=60, video_fps=30)
        write(out/'metadata.json', metadata)
        write(out/'inputs_after.json', pins)
        write(out/'report.json', dict(schema=SCHEMA, completed=captured and protocol,
            capture_completed=captured, protocol_completed=protocol,
            outcome=evaluation_outcome(episode, captured, protocol), failure=failure,
            cleanup_errors=cleanup, encoding_exit_codes=codes, lifecycle_verified=lifecycle,
            policy_unchanged=unchanged, fresh_std_critic_buffers_unchanged=fresh_unchanged,
            source_pins_unchanged=not changed, changed_sources=changed,
            native_pixels=bool(capture and capture.frame_times_s), frames=metadata['frames'],
            policy_evaluation=True, training_updates=0, episode=episode, gpu_scene=diagnostic))
        if failure is None and not captured:
            raise RuntimeError('Policy evaluation capture/lifecycle/source verification failed')


def parent(manifest_path):
    manifest_path = Path(manifest_path).resolve()
    expected_sha = sha(manifest_path)
    manifest = verify_manifest(manifest_path, expected_sha)
    ready, reason, resource = readiness()
    if not ready:
        raise RuntimeError('Actor evaluation resource gate: '+reason)
    out = Path(manifest['out']); out.mkdir(exist_ok=False)
    baseline = _state(); final = None; process = None; failure = None; captured = None
    write(out/'single_before.json', baseline)
    command = [manifest['python'], '-B', str(ROOT/'scripts/tab2body.py'), '--cache-root',
        str(ROOT/'.runtime/cache'), 'run', str(Path(__file__).resolve()), '--manifest', str(manifest_path), '--child']
    env = dict(os.environ, CUDA_VISIBLE_DEVICES=GPU_UUID, PYTHONDONTWRITEBYTECODE='1',
               OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    started = time.monotonic()
    try:
        with (out/'native.stdout.log').open('xb') as stream, (out/'resources.jsonl').open('x') as samples:
            process = subprocess.Popen(command, cwd=str(ROOT), env=env, stdout=stream,
                stderr=subprocess.STDOUT, start_new_session=True)
            while process.poll() is None:
                verify_manifest(manifest_path, expected_sha)
                current = _state(); measured = impact(baseline, current)
                if measured['severe']:
                    raise RuntimeError('Existing sweep delay/error guard: '+repr(measured))
                if time.monotonic()-started > 240:
                    raise TimeoutError('Actor evaluation wall-time exceeded240s')
                rows = [row for row in gpu_query('uuid,memory.free,utilization.gpu', 'gpu') if row['uuid'] == GPU_UUID]
                if len(rows) != 1:
                    raise RuntimeError('GPU identity monitoring failed')
                free = float(rows[0]['memory.free [MiB]'].split()[0])
                if not math.isfinite(free) or free < 2048:
                    raise MemoryError('Actor evaluation free GPU memory below2GiB')
                samples.write(json.dumps(dict(epoch=time.time(), gpu=rows[0], impact=measured,
                    single_finished=current['finished']))+'\n'); samples.flush()
                time.sleep(3)
        if process.wait() != 0:
            raise RuntimeError('Actor evaluation child failed; see native.stdout.log')
        captured = read(out/'capture/report.json')
        if not captured.get('capture_completed'):
            raise RuntimeError('Actor evaluation capture incomplete')
        verify_manifest(manifest_path, expected_sha)
        final = _state()
        if impact(baseline, final)['severe']:
            raise RuntimeError('Final existing sweep guard failed')
    except BaseException as error:
        failure = repr(error)
        if process:
            stop_own_group(process)
        raise
    finally:
        verified = final is not None
        final_error = None
        if final is None:
            try:
                final = _state(); verified = True
            except BaseException as error:
                final_error = repr(error)
                if failure is None:
                    failure = 'final_state: '+final_error
        write(out/'single_after.json', final)
        measured = impact(baseline, final) if verified else dict(
            available=False, severe=True, expansion_allowed=False,
            maximum_elapsed_ratio=None, compared_completed_jobs=None,
            inspection_errors=['final_state_unavailable'], error=final_error)
        protocol = bool(captured and captured.get('protocol_completed'))
        result = dict(schema=SCHEMA, completed=failure is None and protocol,
            failure=failure, wall_s=time.monotonic()-started, command=command, resource_before=resource,
            impact=measured, capture_completed=bool(captured and captured.get('capture_completed')),
            protocol_completed=protocol, outcome=captured.get('outcome') if captured else 'inspection_error',
            source_manifest_sha256=expected_sha, final_state_verified=verified,
            final_state_error=final_error, training_updates=0,
            policy_evaluation=True)
        write(out/'guard_report.json', result)
        print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--child', action='store_true')
    args = parser.parse_args()
    child(args.manifest) if args.child else parent(args.manifest)
