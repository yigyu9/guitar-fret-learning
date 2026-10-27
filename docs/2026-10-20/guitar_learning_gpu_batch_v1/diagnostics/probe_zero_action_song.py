"""Actual GPU zero-action whole-song diagnostic; no optimizer or state spoofing.

The source is deliberately outside the active package. Output must be fresh.
Physical failures reset only their finished environments; collection boundaries
never reset a live song. Curriculum updates are diagnostic observations, not PPO.
"""
import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import resource
import sys
import time
import traceback


ROOT = Path(__file__).resolve().parents[4]


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, allow_nan=False, indent=2)
        stream.write('\n')


def status(path, value):
    temporary = Path(str(path)+'.tmp')
    temporary.write_text(json.dumps(value, allow_nan=False, indent=2)+'\n')
    os.replace(str(temporary), str(path))


def digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            value.update(block)
    return value.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--max-controls', type=int, default=2500)
    parser.add_argument('--horizon', type=int, default=32)
    args = parser.parse_args()
    if min(args.max_controls, args.horizon) < 1:
        parser.error('positive diagnostic control limit and collection horizon required')
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[name] = '1'
    sys.path.insert(0, str(ROOT))
    import isaacgym  # Native module must be loaded before Torch.
    import torch
    from guitar_learning.training.start import settings_document
    from guitar_learning.training.gpu_pool import GpuPool
    from guitar_learning.skills.specialist_policy import SpecialistPolicy
    from guitar_learning.song.curriculum_runtime import CurriculumCoordinator
    from guitar_learning.training.monitoring import available_memory_bytes
    from guitar_learning.runtime.prepared_reset_v1 import prepared_input_paths, BASELINE_CONFIG
    from guitar_learning.native.lower_body_release_v1.common import pin

    if not torch.cuda.is_available():
        raise RuntimeError('CUDA is required; this probe has no CPU fallback')
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    settings = settings_document('left', updates=1, num_envs=2, physics='gpu',
        device='cuda:0', horizon=args.horizon, size='small', seed=7)
    write(out/'settings.json', settings)
    probe = dict(schema='guitar_learning.gpu_zero_action_song_probe.v1',
        helper_path=str(Path(__file__).resolve()), helper_sha256=digest(__file__),
        num_envs=2, hand='left', device='cuda:0', horizon=args.horizon,
        max_controls=args.max_controls, policy_action='exact zero residual on all39 channels',
        optimizer_created=False, policy_used_for_action=False,
        curriculum_scope='real completed episodes observed at diagnostic collection boundaries; no PPO or training',
        stop='first measured timeline_complete or control limit; physical failures retained and selectively reset',
        success_scope='native lifecycle and new candidate measurement; zero policy is not evidence of learned music')
    write(out/'probe.json', probe)
    sources = {p for p in (ROOT/'guitar_learning').rglob('*.py') if 'archive' not in p.parts}
    sources.update((ROOT/'guitar_learning/assets').rglob('*.json'))
    sources.update(p for p in Path(settings['song_training']['bundle']).rglob('*') if p.is_file())
    sources.update(prepared_input_paths())
    sources.update((Path(__file__).resolve(), out/'settings.json', out/'probe.json'))
    pins = pin(BASELINE_CONFIG, extra=sources)
    write(out/'inputs_before.json', pins)
    source_count = len([p for p in sources if p.suffix == '.py' and p.is_relative_to(ROOT/'guitar_learning')]) if sys.version_info >= (3, 9) else sum(
        p.suffix == '.py' and str(p).startswith(str(ROOT/'guitar_learning')+'/') for p in sources)
    torch.set_num_threads(1)
    torch.manual_seed(7)
    torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()
    pool = None
    failure = None
    cleanup_error = None
    clock_errors = []
    curriculum_clock_errors = []
    episodes = []
    chunk_episodes = []
    chunks = []
    controls = 0
    timeline = False
    pending_reset = []
    startup_s = collection_s = 0.
    minimum_ram = available_memory_bytes()
    minimum_cuda_free = torch.cuda.mem_get_info()[0]
    peak_allocated = peak_reserved = 0
    max_clock = [0, 0]
    before_curriculum = after_curriculum = None
    final_scene = None
    last_status = 0.
    transition_stream = (out/'transitions.jsonl').open('x')
    episode_stream = (out/'episodes.jsonl').open('x')

    def jsonline(stream, value):
        stream.write(json.dumps(value, allow_nan=False)+'\n')
        stream.flush()

    def resource_sample():
        nonlocal minimum_ram, minimum_cuda_free, peak_allocated, peak_reserved
        ram = available_memory_bytes()
        free, total = torch.cuda.mem_get_info()
        minimum_ram = min(minimum_ram, ram)
        minimum_cuda_free = min(minimum_cuda_free, free)
        peak_allocated = max(peak_allocated, torch.cuda.max_memory_allocated())
        peak_reserved = max(peak_reserved, torch.cuda.max_memory_reserved())
        if ram < 6*1024**3 or free < 1024**3:
            raise MemoryError('probe resource floor: RAM6GiB, CUDA free1GiB')
        return dict(ram_available_bytes=ram, cuda_free_bytes=free, cuda_total_bytes=total,
            torch_allocated_bytes=torch.cuda.memory_allocated(), torch_reserved_bytes=torch.cuda.memory_reserved(),
            parent_rss_lifetime_peak_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

    def update_status(phase):
        value = dict(schema=probe['schema'], phase=phase, controls=controls,
            horizon=args.horizon, completed_episodes=len(episodes), timeline_complete=timeline,
            elapsed_s=time.perf_counter()-started, max_episode_clock=max_clock,
            current_episode_clock=pool.environment.clock.cpu().tolist() if pool is not None else None,
            scene_physics_steps=pool.scene.physics_steps if pool is not None else None,
            resources=resource_sample())
        status(out/'status.json', value)
        print(json.dumps(value, allow_nan=False), flush=True)

    def observe_chunk(curriculum, partial=False):
        nonlocal chunk_episodes
        clock_before = pool.environment.clock.clone()
        scene_steps = pool.scene.physics_steps
        state_before = curriculum.policy.left_curriculum_state.detach().cpu().tolist()
        result, observation = curriculum.advance(chunk_episodes, pool.observation)
        # The shared coordinator describes its training caller. This caller is
        # explicitly a diagnostic and has not performed any optimizer update.
        result['boundary'] = 'diagnostic collection boundary; no PPO or optimizer update'
        pool.observation = observation
        unchanged = bool(torch.equal(clock_before, pool.environment.clock) and scene_steps == pool.scene.physics_steps)
        if not unchanged:
            curriculum_clock_errors.append(dict(controls=controls, scene_steps_before=scene_steps,
                scene_steps_after=pool.scene.physics_steps))
        row = dict(chunk_index=len(chunks), controls=controls, partial=partial,
            episode_count=len(chunk_episodes), state_before=state_before,
            state_after=curriculum.policy.left_curriculum_state.detach().cpu().tolist(),
            native_clock_unchanged=unchanged, result=result)
        chunks.append(row)
        write(out/('chunk_%04d.json'%row['chunk_index']), row)
        chunk_episodes = []

    try:
        update_status('starting')
        begin = time.perf_counter()
        pool = GpuPool(settings, out)
        startup_s = time.perf_counter()-begin
        write(out/'training_contract.json', pool.contract)
        write(out/'scene_initial_diagnostics.json', pool.scene.diagnostics)
        policy = SpecialistPolicy(pool.observation['state'].shape[-1], size='small',
            contract=pool.contract, role='left', frozen_partner=False).to('cuda:0')
        curriculum = CurriculumCoordinator(policy, pool)
        pool.observation = curriculum.restore()
        before_curriculum = dict(state=policy.left_curriculum_state.detach().cpu().tolist(),
            summary=curriculum.state.summary(), clock=pool.environment.clock.cpu().tolist())
        write(out/'curriculum_before.json', before_curriculum)
        action = torch.zeros(2, 39, device='cuda:0')
        update_status('collecting')
        for tick in range(args.max_controls):
            clock_before = pool.environment.clock.clone()
            scene_before = pool.scene.physics_steps
            begin = time.perf_counter()
            with torch.no_grad():
                observation, reward, cost, terminated, truncated, completed = pool.step(action)
            torch.cuda.synchronize()
            collection_s += time.perf_counter()-begin
            controls = tick+1
            clock_after = pool.environment.clock.clone()
            if not bool(torch.equal(clock_after, clock_before+4)) or pool.scene.physics_steps != scene_before+4:
                clock_errors.append(dict(control=controls, before=clock_before.cpu().tolist(),
                    after=clock_after.cpu().tolist(), scene_before=scene_before,
                    scene_after=pool.scene.physics_steps))
                raise RuntimeError('native episode clock did not advance four steps')
            now_clock = clock_after.cpu().tolist()
            max_clock = [max(previous, actual) for previous, actual in zip(max_clock, now_clock)]
            note_values = None
            if completed:
                note_values = {key: value.detach().cpu().tolist() for key, value in pool.environment.note.items()}
            for episode in completed:
                index = episode['worker_id']
                measured = dict(episode)
                measured['probe_control'] = controls
                measured['per_note'] = {target.target_id: dict(target=asdict(target),
                    **{key: value[index][position] for key, value in note_values.items()})
                    for position, target in enumerate(pool.environment.task.targets)}
                measured['per_note_count'] = len(measured['per_note'])
                measured['source_episode_index'] = sum(e['worker_id'] == index for e in episodes)
                episodes.append(measured)
                chunk_episodes.append(dict(episode))
                jsonline(episode_stream, measured)
            timeline = any(row['reason'] == 'timeline_complete' for row in completed)
            pending_reset = (terminated | truncated).nonzero().flatten().cpu().tolist()
            reset_before = clock_after.cpu().tolist()
            if pending_reset and not timeline:
                pool.reset(pending_reset)
                clock_reset = pool.environment.clock.cpu().tolist()
                expected = [0 if index in pending_reset else value for index, value in enumerate(reset_before)]
                if clock_reset != expected:
                    clock_errors.append(dict(control=controls, reset_indices=pending_reset,
                        clock_after=clock_reset, expected=expected))
                    raise RuntimeError('selective episode reset changed an unfinished song clock')
            else:
                clock_reset = reset_before
            jsonline(transition_stream, dict(schema='guitar_learning.gpu_zero_action_transition.v1',
                control=controls, chunk_index=tick//args.horizon, tick_in_chunk=tick % args.horizon,
                clock_before=clock_before.cpu().tolist(), clock_after=reset_before,
                reset_indices=pending_reset if not timeline else [], clock_after_reset=clock_reset,
                scene_physics_steps=pool.scene.physics_steps, reward=reward.cpu().tolist(),
                cost=cost.cpu().tolist(), terminated=terminated.cpu().tolist(),
                truncated=truncated.cpu().tolist(), completed_episode_count=len(completed)))
            boundary = controls % args.horizon == 0
            if boundary or timeline:
                observe_chunk(curriculum, partial=not boundary)
            if timeline or boundary or time.perf_counter()-last_status >= 10:
                update_status('timeline_complete' if timeline else 'collecting')
                last_status = time.perf_counter()
            if timeline:
                break
        if controls % args.horizon and not timeline:
            observe_chunk(curriculum, partial=True)
        after_curriculum = dict(state=policy.left_curriculum_state.detach().cpu().tolist(),
            summary=curriculum.state.summary(), clock=pool.environment.clock.cpu().tolist())
        write(out/'curriculum_after.json', after_curriculum)
        final_scene = dict(pool.scene.diagnostics)
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc())
        print(json.dumps(dict(probe_failure=failure), allow_nan=False), flush=True)
    finally:
        if pool is not None:
            try:
                final_scene = dict(pool.scene.diagnostics)
                pool.close()
                final_scene = dict(pool.scene.diagnostics)
            except BaseException as error:
                cleanup_error = dict(type=type(error).__name__, message=str(error))
        for stream in (transition_stream, episode_stream):
            try:
                stream.flush()
                os.fsync(stream.fileno())
            finally:
                stream.close()
        peak_allocated = max(peak_allocated, torch.cuda.max_memory_allocated())
        peak_reserved = max(peak_reserved, torch.cuda.max_memory_reserved())
        changed = [path for path, value in pins.items() if not Path(path).is_file() or digest(path) != value]
        reasons = {}
        for row in episodes:
            for reason in row.get('failure_reasons', []):
                reasons[reason] = reasons.get(reason, 0)+1
        report = dict(schema=probe['schema'], completed=failure is None and cleanup_error is None and not changed,
            timeline_complete_measured=timeline, stopped='error' if failure else 'timeline_complete' if timeline else 'control_limit',
            failure=failure, cleanup_error=cleanup_error, source_count=source_count, changed_inputs=changed,
            controls=controls, transitions=controls*2, full_song_control_ticks=settings['song_training']['control_ticks'],
            target_count=settings['song_training']['target_count'], max_episode_clock=max_clock,
            completed_episodes=len(episodes), timeline_complete_episodes=sum(e['reason']=='timeline_complete' for e in episodes),
            physical_failure_episodes=sum(e['reason']=='terminal_failure' for e in episodes),
            failure_reason_counts=reasons, clock_errors=clock_errors, curriculum_clock_errors=curriculum_clock_errors,
            chunks=len(chunks), curriculum_before=before_curriculum, curriculum_after=after_curriculum,
            scene=final_scene, timings=dict(startup_s=startup_s, collection_s=collection_s,
                wall_s=time.perf_counter()-started), resources=dict(minimum_ram_available_bytes=minimum_ram,
                minimum_cuda_free_bytes=minimum_cuda_free, torch_allocated_peak_bytes=peak_allocated,
                torch_reserved_peak_bytes=peak_reserved,
                parent_rss_lifetime_peak_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
            notes='No PPO, no policy inference, no state edits except the production selective reset. Physical failures remain failures.')
        report['checks'] = dict(inputs_unchanged=not changed, native_clock_continuity=not clock_errors,
            curriculum_keeps_native_clock=not curriculum_clock_errors,
            actual_cuda=bool(final_scene and final_scene.get('device') == 'cuda:0' and
                final_scene.get('physx_use_gpu') is True and final_scene.get('use_gpu_pipeline') is True and
                final_scene.get('tensor_devices') and all(value == 'cuda:0'
                    for value in final_scene['tensor_devices'].values()) and final_scene.get('physics_steps', 0) > 0),
            no_optimizer=True, shared_scene_closed=bool(final_scene and final_scene.get('closed')),
            all_episode_summaries_have67_notes=all(e['per_note_count'] == 67 for e in episodes))
        report['completed'] = bool(report['completed'] and all(report['checks'].values()))
        write(out/'report.json', report)
        status(out/'status.json', dict(phase='completed', **report))
        print(json.dumps(report, allow_nan=False), flush=True)
    return 0 if report['completed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
