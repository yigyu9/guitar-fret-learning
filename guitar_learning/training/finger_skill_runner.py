"""Explicit R/F/J execution, actor-only phase transfers and fixed evaluation."""
import copy
import json
import math
import os
from pathlib import Path
import random
import sys
import time
import traceback

from guitar_learning.training import json_io
from guitar_learning.training.recording import write, digest, project_source_paths, active_source_paths
from guitar_learning.training.gpu_log_records import EpisodeWriter, CheckpointRecorder, episode_summary, TRANSITION_SCHEMA, METRICS_SCHEMA


SCHEMA = 'guitar_learning.finger_skill_run.v1'
RESUME_SCHEMA = 'guitar_learning.finger_skill_resume.v1'
RESUME_SCHEMA_V2 = 'guitar_learning.finger_skill_resume.v2'


def resume_schema(settings):
    return (RESUME_SCHEMA_V2 if settings.get('finger_skill', {}).get('schema') ==
            'guitar_learning.finger_skill.v2' else RESUME_SCHEMA)


def _validate_joint_settings(settings):
    spec = settings.get('finger_skill', {})
    if spec.get('schema') != 'guitar_learning.finger_skill.v2':
        return
    if (spec.get('phase') != 'J' or spec.get('exploration') != 'independent' or
            spec.get('hold_ticks') != 1 or spec.get('scope') != 'scheduled'):
        raise ValueError('Joint finger-skill v25 requires J, independent K1 and scheduled scope')
    ppo = settings['ppo']
    if (ppo.get('advantage_normalization') != 'joint' or ppo.get('cost_weight') != 1. or
            ppo.get('episode_cost_budget') is not None or ppo.get('lambda_lr') != 0.):
        raise ValueError('Joint finger-skill v25 requires joint advantages and fixed cost weight one')


def _planned_budget(curriculum):
    if curriculum.schema == 'guitar_learning.finger_skill_exposure.v1':
        return curriculum.config['planned_transitions']
    return curriculum.config['budgets'][curriculum.phase]


def _apply_progress(pool, curriculum):
    if curriculum.schema == 'guitar_learning.finger_skill_exposure.v1':
        pool.set_training_progress(curriculum.committed_transitions)


def phase_settings(settings, phase):
    if phase not in ('R', 'F', 'J'):
        raise ValueError('R/F/J phase required')
    value = copy.deepcopy(settings)
    value['finger_skill']['phase'] = phase
    if settings['finger_skill']['phase'] == 'auto':
        value['seed'] += {'R': 0, 'F': 1000, 'J': 2000}[phase]
        value['finger_skill']['scope'] = 'full_song' if phase == 'J' else 'phrases'
    return value


def phase_budgets(settings):
    unit = settings['horizon']*settings['num_envs']
    spec = settings['finger_skill']
    budgets = dict(R=spec['preparation_updates']*unit, F=spec['finger_updates']*unit,
                   J=settings['updates']*unit)
    if spec['phase'] != 'auto':
        budgets[spec['phase']] = settings['updates']*unit
    return budgets


def checkpoint_metadata(settings, curriculum, pool, *, input_pins=None, **extra):
    return dict(schema=resume_schema(settings), settings=copy.deepcopy(settings),
        curriculum=curriculum.state_dict(), sampler=pool.environment.sampler.state_dict(),
        input_pins=copy.deepcopy(input_pins or {}),
        resume_scope='same-phase model/Adam/RNG/curriculum/sampler; fresh prepared episodes', **extra)


def restore_checkpoint(trainer, pool, curriculum, checkpoint):
    metadata = trainer.load(checkpoint)
    expected = (RESUME_SCHEMA_V2 if curriculum.schema == 'guitar_learning.finger_skill_exposure.v1'
                else RESUME_SCHEMA)
    if not isinstance(metadata, dict) or metadata.get('schema') != expected:
        raise ValueError('finger-skill checkpoint metadata required')
    _validate_pins(metadata)
    curriculum.load_state_dict(metadata['curriculum'])
    phase = trainer.policy.phase
    if curriculum.phase != phase or metadata['settings']['finger_skill']['phase'] != phase:
        raise ValueError('same-phase strict resume required')
    pool.environment.sampler.load_state_dict(metadata['sampler'])
    _apply_progress(pool, curriculum)
    pool.observation = pool.reset()[0]
    return metadata


def _validate_pins(metadata):
    changed = [path for path, value in metadata.get('input_pins', {}).items()
               if not Path(path).is_file() or digest(path) != value]
    if changed:
        raise ValueError('checkpoint input sources changed: '+str(changed[:8]))


def _pins(settings, out, extra=()):
    from guitar_learning.runtime.prepared_reset_v1 import prepared_input_paths, BASELINE_CONFIG
    from guitar_learning.native.lower_body_release_v1.common import pin
    root = Path(__file__).resolve().parents[2]
    sources = active_source_paths(root/'guitar_learning')
    sources.update((root/'guitar_learning/assets').rglob('*.json'))
    sources.update((root/'guitar_learning/assets/gpu_rigid_guitar_v1').glob('*.xml'))
    sources.update(path for path in Path(settings['song_training']['bundle']).rglob('*') if path.is_file())
    sources.update(prepared_input_paths())
    sources.update(extra)
    sources.add(out/'settings.json')
    return pin(BASELINE_CONFIG, extra=sources)


def _policy(settings, pool):
    from guitar_learning.skills.finger_skill_policy import FingerSkillPolicy
    spec = settings['finger_skill']
    return FingerSkillPolicy(pool.observation['state'].shape[-1], size=settings['size'],
        contract=pool.contract, phase=spec['phase'], exploration=spec['exploration']).to(settings['device'])


def _transfer(policy, checkpoint):
    import torch
    from guitar_learning.skills.finger_skill_policy import FingerSkillPolicy
    from guitar_learning.training.decision_ppo import DecisionPPOTrainer
    payload = torch.load(checkpoint, map_location='cpu', weights_only=False)
    identity = payload.get('identity', {})
    architecture = identity.get('architecture', {})
    if identity.get('schema') != DecisionPPOTrainer.schema or architecture.get('schema') != FingerSkillPolicy.schema:
        raise ValueError('own finger-skill phase transfer checkpoint required')
    _validate_pins(payload['metadata'])
    source = FingerSkillPolicy(architecture['state_dim'], size=architecture['size'],
        contract=architecture['contract'], phase=architecture['phase'], exploration=architecture['exploration'])
    source.load_state_dict(payload['model'], strict=True)
    return policy.transfer_from(source)


def _train_phase(settings, out, curriculum, *, resume=None, transfer=None, updates=None):
    import numpy as np
    import torch
    from guitar_learning.training.gpu_pool import GpuPool
    from guitar_learning.training.finger_decisions import DecisionCollector
    from guitar_learning.training.decision_ppo import DecisionPPOTrainer
    from guitar_learning.training.ppo import PPOConfig
    from guitar_learning.training.monitoring import Monitor, save_failure_checkpoint
    from guitar_learning.training.training_log_io import TransitionJournal
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    write(out/'settings.json', settings)
    pins = _pins(settings, out, [Path(value).resolve() for value in (resume, transfer) if value])
    write(out/'inputs_before.json', pins)
    random.seed(settings['seed'])
    np.random.seed(settings['seed'])
    torch.manual_seed(settings['seed'])
    torch.set_num_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    monitor = Monitor(out, min_available_memory_gib=settings['min_available_memory_gib'])
    journal = TransitionJournal(out/'transitions.jsonl.gz', metadata=dict(schema=TRANSITION_SCHEMA,
        physics_hz=240, control_hz=60, family=settings['finger_skill']['schema'], scope='raw control transitions'))
    decisions = TransitionJournal(out/'decisions.jsonl.gz', metadata=dict(
        schema='guitar_learning.finger_decision.v1', scope='one row per sampled decision; raw control references'))
    episodes = EpisodeWriter(out)
    checkpoints = CheckpointRecorder(out)
    metrics_stream = (out/'learning_metrics.jsonl').open('x')
    pool = trainer = None
    failure, recovery, cleanup_errors = None, None, []
    eligible, current_update, used_updates = False, 0, 0
    stopped = 'updates_complete'
    started = time.monotonic()
    episode_ids = []
    min_cuda_free = None
    scheduled = settings['finger_skill']['schema'] == 'guitar_learning.finger_skill.v2'
    scope_total = dict(phrases=0, full_song=0)
    scope_window = dict(phrases=0, full_song=0)
    scope_committed = False
    limit = updates

    def guard(context=None):
        nonlocal min_cuda_free
        free, _ = torch.cuda.mem_get_info()
        if free < 1024**3:
            torch.cuda.empty_cache()
            free, _ = torch.cuda.mem_get_info()
        min_cuda_free = free if min_cuda_free is None else min(min_cuda_free, free)
        if free < 1024**3:
            raise MemoryError('GPU free memory below 1 GiB resource floor')
        monitor.progress(context) if context is not None else monitor.check()

    def raw(tick, reward, cost, terminated, truncated, rows):
        if scheduled:
            full = int(pool.environment.focus_mask.all(dim=-1).sum())
            scope_window['full_song'] += full
            scope_window['phrases'] += settings['num_envs']-full
        refs = [episodes.append(row, current_update, tick) for row in rows]
        episode_ids.extend(ref['episode_id'] for ref in refs)
        if journal.stats['pending_rows'] == 59:
            episodes.sync()
        journal.write(dict(schema=TRANSITION_SCHEMA, update_index=current_update,
            tick_in_update=tick, reward=reward.tolist(), cost=cost.tolist(), terminated=terminated.tolist(),
            truncated=truncated.tolist(), episode_refs=refs))

    def metadata(**extra):
        return checkpoint_metadata(settings, curriculum, pool, input_pins=pins,
            requested_run_budget_transitions=(updates*settings['horizon']*settings['num_envs'] if updates is not None else None),
            original_phase_budget=_planned_budget(curriculum),
            exposure_transitions=copy.deepcopy(scope_total) if scheduled else None,
            manual_budget_extension=resume is not None and updates is not None, **extra)

    def save(name, kind, **extra):
        checkpoints.record(out/name, kind, trainer.updates,
            lambda: trainer.save(out/name, metadata=metadata(**extra)))

    try:
        monitor.start()
        guard()
        pool = GpuPool(settings, out)
        write(out/'training_contract.json', pool.contract)
        policy = _policy(settings, pool)
        with torch.no_grad():
            shift = math.log(settings['initial_std'])+3.
            policy.support_log_std.add_(shift)
            policy.finger_log_std.add_(shift)
        trainer = DecisionPPOTrainer(policy, PPOConfig(**settings['ppo']))
        if pool.environment.approach_gamma != trainer.config.gamma:
            raise ValueError('surface potential and PPO reward discount must match')
        if resume:
            restored_metadata = restore_checkpoint(trainer, pool, curriculum, resume)
            if scheduled:
                saved_exposure = restored_metadata.get('exposure_transitions')
                if (not isinstance(saved_exposure, dict) or saved_exposure.keys() != scope_total.keys() or
                        any(type(value) is not int or value < 0 for value in saved_exposure.values()) or
                        sum(saved_exposure.values()) != curriculum.committed_transitions):
                    raise ValueError('strict committed exposure counters required')
                scope_total.update(saved_exposure)
        if transfer:
            if settings['finger_skill']['schema'] == 'guitar_learning.finger_skill.v2':
                raise ValueError('Joint finger skill starts directly without phase transfer')
            write(out/'phase_transfer.json', _transfer(policy, transfer))
        _apply_progress(pool, curriculum)
        if limit is None:
            limit = math.ceil(curriculum.status()['remaining_transitions']/(settings['horizon']*settings['num_envs']))
        eligible = True
        save('initial.pt', 'initial')
        collector = DecisionCollector(policy, pool, gamma=trainer.config.gamma, cost_gamma=trainer.config.cost_gamma)
        for index in range(limit):
            if settings['max_wall_seconds'] is not None and time.monotonic()-started >= settings['max_wall_seconds']:
                stopped = 'wall_budget'
                break
            current_update = trainer.updates
            scope_window.update(phrases=0, full_song=0)
            scope_committed = False
            episode_ids.clear()
            monitor.set_phase('collecting', update_index=current_update, ticks=0, horizon=settings['horizon'])
            pool.environment.reset_reward_window()
            begin = time.monotonic()
            buffer, completed = collector.collect(settings['horizon'], progress_callback=guard,
                transition_callback=raw, decision_callback=lambda row: decisions.write(dict(
                    schema='guitar_learning.finger_decision.v1', update_index=current_update, **row)),
                policy_version=trainer.updates)
            torch.cuda.synchronize()
            collect_s = time.monotonic()-begin
            monitor.set_phase('optimizing')
            eligible = False
            begin = time.monotonic()
            metrics = trainer.update(buffer, completed)
            transitions = settings['horizon']*settings['num_envs']
            episodes.sync()
            journal.commit(transitions)
            decisions.commit(int(buffer['valid'].sum()))
            curriculum.commit(transitions)
            if scheduled:
                if sum(scope_window.values()) != transitions:
                    raise ValueError('actual exposure counts must equal raw committed transitions')
                for scope in scope_total:
                    scope_total[scope] += scope_window[scope]
                scope_committed = True
            _apply_progress(pool, curriculum)
            eligible = True
            torch.cuda.synchronize()
            metrics.update(schema=METRICS_SCHEMA, update_index=current_update, optimizer_updates=trainer.updates,
                phase=policy.phase, transitions=transitions, decisions=int(buffer['valid'].sum()),
                collection_s=collect_s, update_s=time.monotonic()-begin,
                completed_episode_ids=list(episode_ids), episode_summary=episode_summary(completed),
                mean_reward=float(buffer['reward'][buffer['valid']].mean()),
                mean_cost=float(buffer['cost'][buffer['valid']].mean()),
                mean_reward_cost_scope='discounted decision sums; raw control values in transitions journal',
                reward_component_means=pool.environment.reward_window_means(transitions),
                curriculum=curriculum.status(), journal=journal.stats, decision_journal=decisions.stats,
                exposure_transitions=copy.deepcopy(scope_window) if scheduled else None,
                cumulative_exposure_transitions=copy.deepcopy(scope_total) if scheduled else None)
            metrics_stream.write(json_io.dumps(metrics, allow_nan=False)+'\n')
            metrics_stream.flush()
            del buffer
            used_updates += 1
            if (index+1) % settings['checkpoint_every'] == 0 and index+1 < limit:
                save('checkpoint_%06d.pt'%trainer.updates, 'periodic')
            guard()
        save('final.pt', 'final', stopped=stopped, updates_in_run=used_updates)
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc())
        stopped = 'interrupted' if isinstance(error, KeyboardInterrupt) else 'error'
        if pool is not None:
            recovery = checkpoints.record(out/'failure_last_valid.pt', 'recovery',
                trainer.updates if trainer else None,
                lambda: save_failure_checkpoint(trainer, out, metadata(recovery_scope='incomplete rollout discarded'), eligible=eligible))
        raise
    finally:
        for name, callback in [('pool', pool.close if pool else lambda: None),
                ('episodes', episodes.sync), ('raw journal', journal.close), ('decision journal', decisions.close)]:
            try:
                if name.endswith('journal'):
                    item = journal if name == 'raw journal' else decisions
                    if item.stats['unresolved_sampled']:
                        item.discard(item.stats['unresolved_sampled'])
                callback()
            except BaseException as error:
                cleanup_errors.append(dict(component=name, message=str(error)))
        for stream in (episodes.stream, metrics_stream, checkpoints.stream):
            try:
                stream.flush()
                os.fsync(stream.fileno())
                stream.close()
            except BaseException as error:
                cleanup_errors.append(dict(component='stream', message=str(error)))
        try:
            monitor.close(stopped)
        except BaseException as error:
            cleanup_errors.append(dict(component='monitor', message=str(error)))
        changed = [path for path, value in pins.items() if not Path(path).is_file() or digest(path) != value]
        missing = sorted(project_source_paths(list(sys.modules.items()))-set(pins))
        audit = pool.scene.diagnostics if pool and pool.scene else None
        lifecycle = bool(audit and audit['closed'] and audit['physx_use_gpu'] and audit['use_gpu_pipeline']
            and audit['simulator_count'] == 1 and audit['environment_count'] == settings['num_envs'])
        verified = not (changed or missing or cleanup_errors) and lifecycle
        report = dict(schema=SCHEMA, completed=failure is None and verified, stopped=stopped,
            phase=settings['finger_skill']['phase'], settings=settings, optimizer_updates=trainer.updates if trainer else 0,
            updates_in_run=used_updates, transitions=journal.stats['committed'], journal=journal.stats,
            decision_journal=decisions.stats, checkpoints=checkpoints.stats, failure=failure,
            recovery_checkpoint=recovery, changed_inputs=changed, missing_import_pins=missing,
            cleanup_errors=cleanup_errors, lifecycle_verified=lifecycle, gpu_scene=audit,
            min_cuda_free_bytes=min_cuda_free, wall_s=time.monotonic()-started,
            curriculum=curriculum.state_dict(), partial_episodes_are_successes=False,
            requested_run_updates=updates, original_phase_budget=_planned_budget(curriculum),
            exposure_transitions=scope_total if scheduled else None,
            sampled_uncommitted_exposure_transitions=(scope_window if scheduled and not scope_committed else None),
            discarded_from_learning_exposure_transitions=(scope_window if scheduled and not scope_committed else None),
            manual_budget_extension=resume is not None and updates is not None)
        write(out/'report.json', report)
        if failure is None and not verified:
            raise RuntimeError('finger-skill phase source/lifecycle check failed; see report.json')
    return dict(report=report, checkpoint=str(out/'final.pt'))


class _DeterministicPolicy:
    def __init__(self, policy):
        self.policy, self.phase = policy, policy.phase

    def __call__(self, *inputs):
        return self.policy(*inputs)

    def act(self, *inputs):
        return self.policy.act(*inputs, deterministic=True)


def evaluate_checkpoint(checkpoint, out, *, num_envs=None, scope='full_song',
                        min_finger_opportunities=0, max_batches=8, max_episodes=512, curriculum=None, deadline=None):
    """Evaluate complete episodes, keeping failures and a fixed per-env denominator.

    Already completed rows reset normally while slower rows finish. Their later
    episodes are ignored for that batch. The scene is closed before returning.
    """
    import isaacgym
    import torch
    from guitar_learning.training.gpu_pool import GpuPool
    from guitar_learning.training.finger_decisions import DecisionCollector
    from guitar_learning.training.decision_ppo import DecisionPPOTrainer
    from guitar_learning.training.ppo import PPOConfig
    from guitar_learning.training.monitoring import Monitor
    if scope not in ('phrases', 'full_song'):
        raise ValueError('phrases/full_song evaluation scope required')
    if (type(max_batches) is not int or max_batches < 1 or type(max_episodes) is not int or max_episodes < 1
            or type(min_finger_opportunities) is not int or min_finger_opportunities < 0):
        raise ValueError('positive evaluation limits required')
    checkpoint, out = Path(checkpoint).resolve(), Path(out).resolve()
    payload = torch.load(checkpoint, map_location='cpu', weights_only=False)
    metadata = payload.get('metadata')
    if (not isinstance(metadata, dict) or
            metadata.get('schema') != resume_schema(metadata.get('settings', {}))):
        raise ValueError('own finger-skill checkpoint metadata required')
    _validate_pins(metadata)
    settings = copy.deepcopy(metadata['settings'])
    _validate_joint_settings(settings)
    if num_envs is not None:
        if type(num_envs) is not int or not 1 <= num_envs <= 1024:
            raise ValueError('num_envs must be 1..1024')
        settings['num_envs'] = num_envs
    requested_max_episodes = max_episodes
    max_episodes = max(max_episodes, settings['num_envs'])
    out.mkdir(parents=True, exist_ok=False)
    write(out/'settings.json', settings)
    pins = _pins(settings, out, [checkpoint])
    write(out/'inputs_before.json', pins)
    monitor = Monitor(out, min_available_memory_gib=settings['min_available_memory_gib'])
    writer = EpisodeWriter(out)
    pool = None
    rows, failure, cleanup_errors = [], None, []
    actual_transitions, batches = 0, 0
    started = time.monotonic()
    report = None
    try:
        monitor.start()
        pool = GpuPool(settings, out)
        policy = _policy(settings, pool)
        trainer = DecisionPPOTrainer(policy, PPOConfig(**settings['ppo']))
        loaded_metadata = trainer.load(checkpoint)  # Exact actual pool contract; no relaxed model load.
        pool.environment.set_evaluation(enabled=True, full_song=scope == 'full_song')
        pool.observation = pool.reset()[0]
        collector = DecisionCollector(_DeterministicPolicy(policy), pool,
            gamma=trainer.config.gamma, cost_gamma=trainer.config.cost_gamma)
        opportunities = [0]*4
        for batch in range(max_batches):
            count = min(settings['num_envs'], max_episodes-len(rows))
            if count <= 0:
                break
            seen = set()
            max_ticks = math.ceil(pool.environment.task.duration_s*60)+settings['horizon']
            elapsed_ticks = 0

            def record(tick, reward, cost, terminated, truncated, episodes):
                nonlocal actual_transitions
                actual_transitions += settings['num_envs']
                for episode in episodes:
                    identity = episode['env_id']
                    if identity < count and identity not in seen:
                        seen.add(identity)
                        rows.append(copy.deepcopy(episode))
                        writer.append(episode, batch, tick)
                        for finger, metric in enumerate(episode['left_curriculum']['finger_metrics']):
                            opportunities[finger] += metric['target_count']

            def guard(context):
                if deadline is not None and time.monotonic() >= deadline:
                    raise TimeoutError('finger-skill evaluation reached pipeline wall budget')
                free, _ = torch.cuda.mem_get_info()
                if free < 1024**3:
                    torch.cuda.empty_cache()
                    free, _ = torch.cuda.mem_get_info()
                if free < 1024**3:
                    raise MemoryError('GPU evaluation free memory below 1 GiB floor')
                monitor.progress(context)

            while len(seen) < count and elapsed_ticks < max_ticks:
                horizon = min(settings['horizon'], max_ticks-elapsed_ticks)
                buffer, _ = collector.collect(horizon, transition_callback=record, progress_callback=guard)
                del buffer
                elapsed_ticks += horizon
            if len(seen) != count:
                raise RuntimeError('fixed evaluation did not finish every scheduled first episode')
            batches += 1
            if not min_finger_opportunities or all(value >= min_finger_opportunities for value in opportunities):
                break
        writer.sync()
        readiness = curriculum.evaluate(rows) if curriculum is not None else None
        if curriculum is not None:
            evaluated_metadata = copy.deepcopy(loaded_metadata)
            evaluated_metadata['curriculum'] = curriculum.state_dict()
            evaluated_metadata['evaluation'] = dict(checkpoint_sha256=digest(checkpoint),
                episodes=len(rows), scope=scope, report=str(out/'report.json'))
            recorder = CheckpointRecorder(out)
            try:
                recorder.record(out/'evaluated.pt', 'evaluated_same_model', trainer.updates,
                    lambda: trainer.save(out/'evaluated.pt', metadata=evaluated_metadata))
            finally:
                recorder.close()
        report = dict(schema='guitar_learning.finger_skill_evaluation.v1', checkpoint=str(checkpoint),
            checkpoint_sha256=digest(checkpoint), phase=policy.phase, scope=scope, readiness=readiness,
            readiness_checkpoint=str(out/'evaluated.pt') if curriculum is not None else None,
            episodes=len(rows), batches=batches, finger_opportunities=opportunities,
            requested_finger_opportunities=min_finger_opportunities,
            opportunities_sufficient=all(value >= min_finger_opportunities for value in opportunities),
            limits=dict(max_batches=max_batches, max_episodes=max_episodes,
                        requested_max_episodes=requested_max_episodes, all_envs_in_first_batch=True),
            actual_simulated_transitions=actual_transitions,
            selected_episode_transitions=sum(row['steps'] for row in rows),
            first_episode_per_env_per_batch=True, failed_episodes_in_denominator=True,
            summary=episode_summary(rows), wall_s=time.monotonic()-started,
            settings=settings, training_contract=pool.contract)
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc())
        raise
    finally:
        for name, callback in (('pool', pool.close if pool else lambda: None), ('episodes', writer.close),
                               ('monitor', lambda: monitor.close('error' if failure else 'evaluation_complete'))):
            try:
                callback()
            except BaseException as error:
                cleanup_errors.append(dict(component=name, message=str(error)))
        changed = [path for path, value in pins.items() if not Path(path).is_file() or digest(path) != value]
        missing = sorted(project_source_paths(list(sys.modules.items()))-set(pins))
        audit = pool.scene.diagnostics if pool and pool.scene else None
        lifecycle = bool(audit and audit['closed'] and audit['physx_use_gpu'] and audit['use_gpu_pipeline']
            and audit['simulator_count'] == 1 and audit['environment_count'] == settings['num_envs'])
        report = dict(report or {}, actual_simulated_transitions=actual_transitions,
            selected_episode_transitions=sum(row['steps'] for row in rows), episodes=len(rows),
            completed=failure is None and not (changed or missing or cleanup_errors) and lifecycle,
            failure=failure, changed_inputs=changed, missing_import_pins=missing,
            cleanup_errors=cleanup_errors, lifecycle_verified=lifecycle, gpu_scene=audit)
        write(out/'report.json', report)
        if failure is None and not report['completed']:
            raise RuntimeError('finger-skill evaluation source/lifecycle check failed')
    return report, rows


def run(settings, args):
    import isaacgym
    import torch
    from guitar_learning.training.finger_skill_curriculum import FingerSkillCurriculum, ExposureSchedule
    if settings['device'] != 'cuda:0' or not torch.cuda.is_available():
        raise RuntimeError('finger-skill requires CUDA GPU physics; no CPU fallback')
    settings = copy.deepcopy(settings)
    _validate_joint_settings(settings)
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    spec = settings['finger_skill']
    scheduled = spec['schema'] == 'guitar_learning.finger_skill.v2'
    automatic = spec['phase'] == 'auto'
    phase = 'R' if automatic else spec['phase']
    curriculum = (ExposureSchedule(spec['planned_transitions'], spec['full_song_after']) if scheduled
                  else FingerSkillCurriculum(phase, budgets=phase_budgets(settings)))
    resume = Path(args.resume).resolve() if args.resume else None
    manual_extension = resume is not None and not automatic
    pipeline_started = time.monotonic()
    wall_seconds = settings.get('max_wall_seconds')
    deadline = pipeline_started+wall_seconds if wall_seconds is not None else None
    evaluation_path = None

    def active_settings(phase):
        active = phase_settings(settings, phase)
        if deadline is not None:
            active['max_wall_seconds'] = max(0., deadline-time.monotonic())
        return active

    stages, evaluations = [], []
    stopped, failure, transfer = 'updates_complete', None, None
    current_checkpoint = None
    try:
        if resume:
            payload = torch.load(resume, map_location='cpu', weights_only=False)
            metadata = payload.get('metadata', {})
            if metadata.get('schema') != resume_schema(settings):
                raise ValueError('own finger-skill resume metadata required')
            _validate_pins(metadata)
            state = metadata['curriculum']
            if scheduled:
                saved = state['config']
                curriculum = ExposureSchedule(saved['planned_transitions'], saved['full_song_after'])
            elif not automatic:
                saved = state['config']
                curriculum = FingerSkillCurriculum(saved['initial_phase'], budgets=saved['budgets'],
                                                   thresholds=saved['thresholds'])
            curriculum.load_state_dict(state)
            phase = curriculum.phase
            if not automatic and phase != spec['phase']:
                raise ValueError('requested phase and checkpoint differ')
        if scheduled:
            spec.update(curriculum.config)
        write(out/'settings.json', settings)
        if automatic and phase == 'R' and resume is None and (deadline is None or time.monotonic() < deadline):
            candidate = _train_phase(active_settings('R'), out/'R_initial', curriculum, updates=0)
            stages.append(candidate)
            current_checkpoint = candidate['checkpoint']
            evaluation_path = out/'R_initial_evaluation'
            report, rows = evaluate_checkpoint(current_checkpoint, evaluation_path, scope='phrases',
                curriculum=curriculum, deadline=deadline)
            readiness = report['readiness']
            current_checkpoint = report['readiness_checkpoint']
            evaluations.append(dict(path='R_initial_evaluation', report=report, readiness=readiness))
            if readiness['ready']:
                phase = curriculum.next_phase()
                transfer, resume = current_checkpoint, None
            else:
                resume = current_checkpoint
        while True:
            if deadline is not None and time.monotonic() >= deadline:
                stopped = 'wall_budget'
                break
            active = active_settings(phase)
            result = _train_phase(active, out/phase, curriculum, resume=resume, transfer=transfer,
                updates=None if automatic else settings['updates'])
            stages.append(result)
            current_checkpoint = result['checkpoint']
            resume, transfer = None, None
            if result['report']['stopped'] == 'wall_budget':
                stopped = 'wall_budget'
                break
            if not automatic or phase == 'J':
                break
            evaluation_path = out/(phase+'_evaluation')
            report, rows = evaluate_checkpoint(current_checkpoint, evaluation_path, scope='phrases',
                min_finger_opportunities=64 if phase == 'F' else 0, curriculum=curriculum, deadline=deadline)
            readiness = report['readiness']
            current_checkpoint = report['readiness_checkpoint']
            evaluations.append(dict(path=phase+'_evaluation', report=report, readiness=readiness))
            if not readiness['ready']:
                stopped = phase+'_stalled'
                break
            transfer = current_checkpoint
            phase = curriculum.next_phase()
    except TimeoutError as error:
        if deadline is None or time.monotonic() < deadline:
            failure = dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc())
            stopped = 'error'
            raise
        stopped = 'wall_budget'
        if evaluation_path is not None and (evaluation_path/'report.json').is_file():
            evaluations.append(dict(path=evaluation_path.name,
                report=json.loads((evaluation_path/'report.json').read_text()), readiness=None))
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc())
        stopped = 'error'
        raise
    finally:
        if not (out/'settings.json').exists():
            write(out/'settings.json', settings)
        report = dict(schema=SCHEMA,
            completed=failure is None and stopped == 'updates_complete', stopped=stopped,
            settings=settings, final_phase=phase, final_checkpoint=current_checkpoint,
            stages=stages, evaluations=evaluations, curriculum=curriculum.state_dict(), failure=failure,
            budgets_are_raw_control_transitions=True,
            training_transitions=sum(curriculum.training_transitions.values()),
            exposure_transitions=(stages[-1]['report'].get('exposure_transitions') if scheduled and stages else None),
            evaluation_selected_episode_transitions=sum(curriculum.evaluation_transitions.values()),
            evaluation_actual_simulated_transitions=sum(row['report']['actual_simulated_transitions'] for row in evaluations),
            stalled_is_mastery=False, phase_transfer_is_strict_resume=False,
            manual_budget_extension=manual_extension, requested_run_updates=settings['updates'],
            wall_budget_scope='entire pipeline including phase startup and independent evaluation',
            wall_s=time.monotonic()-pipeline_started)
        write(out/'report.json', report)
    return report
