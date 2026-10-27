"""Explicit-budget full GPU song training with a separate measurement contract."""
import copy
import json
import math
import os
from pathlib import Path
import random
import resource
import sys
import time
import traceback

from guitar_learning.training.recording import write, digest, project_source_paths


def run(settings, args):
    import isaacgym
    import numpy as np
    import torch
    from guitar_learning.training.gpu_pool import GpuPool, TensorCollector
    from guitar_learning.skills.specialist_policy import SpecialistPolicy
    from guitar_learning.training.ppo import PPOTrainer, PPOConfig
    from guitar_learning.training.monitoring import Monitor, available_memory_bytes, save_failure_checkpoint
    from guitar_learning.training.training_log_io import TransitionJournal
    from guitar_learning.runtime.prepared_reset_v1 import prepared_input_paths, BASELINE_CONFIG
    from guitar_learning.native.lower_body_release_v1.common import pin

    if settings['device'] != 'cuda:0' or not torch.cuda.is_available():
        raise RuntimeError('GPU physics training requires CUDA; CPU fallback is not permitted')
    settings = copy.deepcopy(settings)
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    write(out/'settings.json', settings)
    root = Path(__file__).resolve().parents[2]
    sources = {p for p in (root/'guitar_learning').rglob('*.py') if 'archive' not in p.parts}
    sources.update((root/'guitar_learning/assets').rglob('*.json'))
    sources.update((root/'guitar_learning/assets/gpu_rigid_guitar_v1').glob('*.xml'))
    sources.update(p for p in Path(settings['song_training']['bundle']).rglob('*') if p.is_file())
    sources.update(prepared_input_paths())
    sources.add(out/'settings.json')
    if args.resume:
        sources.add(args.resume.resolve())
    pins = pin(BASELINE_CONFIG, extra=sources)
    write(out/'inputs_before.json', pins)
    random.seed(settings['seed'])
    np.random.seed(settings['seed'])
    torch.manual_seed(settings['seed'])
    torch.set_num_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.cuda.reset_peak_memory_stats()
    monitor = Monitor(out, min_available_memory_gib=settings['min_available_memory_gib'])
    journal = TransitionJournal(out/'transitions.jsonl.gz', metadata=dict(
        schema='guitar_learning.gpu_transition.v1', physics_hz=240, control_hz=60,
        measurement='gpu_surface_loaded.v1',
        scope='GPU reward/cost and termination arrays; completed note summaries in episodes.jsonl'))
    episodes_stream = (out/'episodes.jsonl').open('x')
    metrics_stream = (out/'learning_metrics.jsonl').open('x')
    pool = trainer = None
    eligible = False
    failure = None
    recovery = None
    updates = []
    completed_episodes = 0
    episode_counts = dict(timeline_complete=0, physical_failure=0, stage_success=0)
    timers = dict(startup_s=0., collection_s=0., update_s=0., checkpoint_s=0.)
    started = time.perf_counter()
    current_update = 0
    cleanup_errors = []
    stopped = 'updates_complete'
    min_cuda_free = None
    min_cuda_guard_free = None
    cuda_cache_releases = 0

    def jsonline(stream, value):
        stream.write(json.dumps(value, allow_nan=False)+'\n')
        stream.flush()

    def check_resources(context=None, *, release_cache=False):
        nonlocal min_cuda_free, min_cuda_guard_free, cuda_cache_releases
        free, _ = torch.cuda.mem_get_info()
        min_cuda_free = free if min_cuda_free is None else min(min_cuda_free, free)
        if release_cache or free < 1024**3:
            before = dict(free_bytes=free, allocated_bytes=torch.cuda.memory_allocated(),
                          reserved_bytes=torch.cuda.memory_reserved())
            # Return unused allocator blocks before enforcing the physical free-memory floor.
            torch.cuda.empty_cache()
            cuda_cache_releases += 1
            free, _ = torch.cuda.mem_get_info()
            monitor.event('cuda_cache_release', before=before,
                reason='optimizer_boundary' if release_cache else 'low_free_memory',
                after=dict(free_bytes=free, allocated_bytes=torch.cuda.memory_allocated(),
                           reserved_bytes=torch.cuda.memory_reserved()))
        min_cuda_guard_free = free if min_cuda_guard_free is None else min(min_cuda_guard_free, free)
        if free < 1024**3:
            raise MemoryError('GPU free memory below1GiB resource floor')
        if context is not None:
            monitor.progress(context)
        else:
            monitor.check()

    def transition(tick, reward, cost, terminated, truncated, episodes):
        journal.write(dict(schema='guitar_learning.gpu_transition.v1', update_index=current_update,
            tick_in_update=tick, reward=reward.tolist(), cost=cost.tolist(),
            terminated=terminated.tolist(), truncated=truncated.tolist(), episodes=episodes))
        for episode in episodes:
            jsonline(episodes_stream, dict(update_index=current_update, episode=episode))

    try:
        monitor.start()
        check_resources()
        monitor.set_phase('gpu_scene_startup')
        begin = time.perf_counter()
        pool = GpuPool(settings, out)
        timers['startup_s'] = time.perf_counter()-begin
        write(out/'training_contract.json', pool.contract)
        policy = SpecialistPolicy(pool.observation['state'].shape[-1], size=settings['size'],
            contract=pool.contract, role=settings['specialist']['role'], frozen_partner=False).to(settings['device'])
        with torch.no_grad():
            policy.log_std.fill_(math.log(settings['initial_std']))
        curriculum = None
        if settings['specialist']['role'] == 'left':
            from guitar_learning.song.curriculum_runtime import CurriculumCoordinator
            curriculum = CurriculumCoordinator(policy, pool)
        trainer = PPOTrainer(policy, PPOConfig(**settings['ppo']))
        if settings['specialist']['role'] == 'left' and pool.environment.approach_gamma != trainer.config.gamma:
            raise ValueError('Surface approach discount must equal PPO reward gamma')
        if args.resume:
            trainer.load(args.resume.resolve())
        if curriculum is not None:
            pool.observation = curriculum.restore()
        eligible = True
        trainer.save(out/'initial.pt', metadata=dict(settings=settings,
            resume_scope='GPU model_optimizer_RNG_curriculum; new prepared physical episodes'))
        collector = TensorCollector(policy, pool)
        for index in range(settings['updates']):
            if settings['max_wall_seconds'] is not None and time.perf_counter()-started >= settings['max_wall_seconds']:
                stopped = 'wall_budget'
                break
            current_update = index
            monitor.set_phase('collecting', update_index=index, ticks=0, horizon=settings['horizon'])
            begin = time.perf_counter()
            pool.environment.reset_reward_window()
            buffer, completed = collector.collect(settings['horizon'],
                progress_callback=check_resources, transition_callback=transition)
            torch.cuda.synchronize()
            collection_s = time.perf_counter()-begin
            timers['collection_s'] += collection_s
            monitor.set_phase('optimizing')
            begin = time.perf_counter()
            eligible = False
            metrics = trainer.update(buffer, completed)
            if settings['specialist']['role'] == 'left':
                metrics['reward_component_means'] = pool.environment.reward_window_means(settings['horizon']*settings['num_envs'])
            journal.commit(settings['horizon']*settings['num_envs'])
            if curriculum is not None:
                metrics['left_curriculum'], collector.observation = curriculum.advance(completed, collector.observation)
            eligible = True
            torch.cuda.synchronize()
            update_s = time.perf_counter()-begin
            timers['update_s'] += update_s
            completed_episodes += len(completed)
            for episode in completed:
                episode_counts['timeline_complete'] += episode['reason'] == 'timeline_complete'
                episode_counts['physical_failure'] += episode['reason'] == 'terminal_failure'
                episode_counts['stage_success'] += bool(episode['song']['stage_success'])
            metrics.update(update_index=index, optimizer_updates=trainer.updates,
                collection_s=collection_s, update_s=update_s,
                transitions=settings['horizon']*settings['num_envs'], completed_episodes=completed,
                mean_reward=float(buffer['reward'].mean()), mean_cost=float(buffer['cost'].mean()),
                physics_steps=pool.scene.physics_steps, journal=journal.stats)
            del buffer
            write(out/('update_%06d.json'%index), metrics)
            jsonline(metrics_stream, metrics)
            updates.append(dict(update_index=index, optimizer_updates=trainer.updates,
                transitions=metrics['transitions'], collection_s=collection_s, update_s=update_s))
            if (index+1) % settings['checkpoint_every'] == 0 and index+1 < settings['updates']:
                trainer.save(out/('checkpoint_%06d.pt'%index), metadata=dict(settings=settings, update_in_run=index+1))
            print('[gpu training] update=%d transitions=%d collect=%.3fs PPO=%.3fs episodes=%d' % (
                index, metrics['transitions'], collection_s, update_s, len(completed)), flush=True)
            check_resources(release_cache=True)
        monitor.set_phase('saving_final')
        begin = time.perf_counter()
        trainer.save(out/'final.pt', metadata=dict(settings=settings, updates_in_run=len(updates), stopped=stopped))
        timers['checkpoint_s'] += time.perf_counter()-begin
    except BaseException as error:
        stopped = 'interrupted' if isinstance(error, KeyboardInterrupt) else 'error'
        failure = dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc())
        recovery = save_failure_checkpoint(trainer, out, dict(settings=settings,
            recovery_scope='last valid optimizer state; incomplete rollout discarded'), eligible=eligible)
        raise
    finally:
        for label, cleanup in (('GPU scene', pool.close if pool is not None else lambda: None),):
            try:
                cleanup()
            except BaseException as error:
                cleanup_errors.append(dict(component=label, type=type(error).__name__, message=str(error)))
        unresolved = journal.stats['unresolved_sampled']
        if unresolved:
            journal.discard(unresolved)
        try:
            journal.close()
        except BaseException as error:
            cleanup_errors.append(dict(component='journal', type=type(error).__name__, message=str(error)))
        for stream in (episodes_stream, metrics_stream):
            try:
                stream.flush()
                os.fsync(stream.fileno())
                stream.close()
            except BaseException as error:
                cleanup_errors.append(dict(component='metrics', type=type(error).__name__, message=str(error)))
        changed = [path for path, value in pins.items() if not Path(path).is_file() or digest(path) != value]
        imported = project_source_paths(list(sys.modules.items()))
        missing = sorted(imported-set(pins))
        try:
            monitor.close(stopped)
        except BaseException as error:
            cleanup_errors.append(dict(component='monitor', type=type(error).__name__, message=str(error)))
        scene_audit = pool.scene.diagnostics if pool is not None and pool.scene is not None else None
        lifecycle_ok = bool(scene_audit and scene_audit['closed'] and
            scene_audit['physx_use_gpu'] and scene_audit['use_gpu_pipeline'] and
            scene_audit['simulator_count'] == 1 and scene_audit['environment_count'] == settings['num_envs'])
        checks = not (changed or missing or cleanup_errors) and lifecycle_ok
        complete = failure is None and checks and (len(updates) == settings['updates'] or stopped == 'wall_budget')
        resources = dict(parent_rss_peak_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            min_available_memory_bytes=monitor.minimum_available or available_memory_bytes(),
            cuda_free_sample_min_bytes=min_cuda_free,
            cuda_free_guard_sample_min_bytes=min_cuda_guard_free,
            cuda_cache_releases=cuda_cache_releases,
            torch_cuda_allocated_peak_bytes=torch.cuda.max_memory_allocated(),
            torch_cuda_reserved_peak_bytes=torch.cuda.max_memory_reserved())
        report = dict(schema='guitar_learning.gpu_run.v1', completed=complete, settings=settings,
            failure=failure, stopped=stopped, recovery_checkpoint=recovery, cleanup_errors=cleanup_errors,
            changed_inputs=changed, missing_import_pins=missing, journal=journal.stats,
            transitions=journal.stats['committed'], optimizer_updates=trainer.updates if trainer else None,
            updates=updates, timers=timers, wall_s=time.perf_counter()-started, resources=resources,
            gpu_scene=scene_audit, lifecycle_verified=lifecycle_ok,
            completed_episodes=completed_episodes,
            scope='GPU PhysX and CUDA batched control/measurement/PPO; new surface-load contact criterion, not historical native witness or acoustic success')
        write(out/'report.json', report)
        write(out/'song_report.json', dict(schema='guitar_learning.gpu_song_run.v2', completed=complete,
            completed_episodes=completed_episodes, episode_counts=episode_counts,
            episodes_path='episodes.jsonl',
            partial_trajectories_are_successes=False, measurement='gpu_surface_loaded.v1'))
        if failure is None and not complete:
            raise RuntimeError('GPU run source or lifecycle checks failed; see report.json')
    return report
