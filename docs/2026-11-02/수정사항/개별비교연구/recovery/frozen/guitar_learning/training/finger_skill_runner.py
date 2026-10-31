import copy
import math
import os
from pathlib import Path
import random
import sys
import time
import traceback
from guitar_learning.training import training_log_io as json_io
from guitar_learning.training.training_log_io import write, digest, project_source_paths, active_source_paths
from guitar_learning.training.training_log_io import EpisodeWriter, CheckpointRecorder, episode_summary, TRANSITION_SCHEMA, METRICS_SCHEMA


def _count(value, name):
    if type(value) is not int or value < 0:
        raise ValueError(name+' must be a nonnegative integer')
    return value


class ExposureSchedule:
    """최초 학습에서 정한 노출 전환 문턱을 유지하며, 추가 학습으로 옮기지 않는다."""
    schema = 'guitar_learning.finger_skill_exposure.v1'
    phase = 'J'

    def __init__(self, planned_transitions, full_song_after=None):
        if _count(planned_transitions, 'planned_transitions') < 1:
            raise ValueError('positive planned transitions required')
        threshold = planned_transitions//4 if full_song_after is None else full_song_after
        if _count(threshold, 'full_song_after') != planned_transitions//4:
            raise ValueError('fixed quarter of original planned transitions required')
        self.config = dict(planned_transitions=planned_transitions, full_song_after=threshold)
        self.committed_transitions = 0

    @property
    def training_transitions(self):
        return dict(J=self.committed_transitions)

    @property
    def evaluation_transitions(self):
        return {}

    def status(self):
        planned, committed = self.config['planned_transitions'], self.committed_transitions
        return dict(phase='J', planned_transitions=planned,
            full_song_after=self.config['full_song_after'], committed_transitions=committed,
            remaining_transitions=max(0, planned-committed),
            next_reset_scope='full_song' if committed >= self.config['full_song_after'] else 'phrases',
            changes_only_on_episode_reset=True, mastery_gate=False)

    def commit(self, transitions):
        self.committed_transitions += _count(transitions, 'committed transitions')
        return self.status()

    def state_dict(self):
        return dict(schema=self.schema, config=copy.deepcopy(self.config),
                    committed_transitions=self.committed_transitions)

    def load_state_dict(self, state):
        if (not isinstance(state, dict) or state.keys() != self.state_dict().keys() or
                state.get('schema') != self.schema or state.get('config') != self.config):
            raise ValueError('strict exposure schedule schema/config mismatch')
        committed = _count(state['committed_transitions'], 'committed transitions')
        self.committed_transitions = committed


SCHEMA = 'guitar_learning.finger_skill_run.v2'
RESUME_SCHEMA = 'guitar_learning.finger_skill_resume.v3'


def resume_schema(settings):
    if settings.get('finger_skill', {}).get('schema') != 'guitar_learning.finger_skill.v3':
        raise ValueError('J-only finger-skill v3 checkpoint metadata required')
    return RESUME_SCHEMA


def _validate_joint_settings(settings):
    spec = settings.get('finger_skill', {})
    if (spec.get('schema') != 'guitar_learning.finger_skill.v3' or spec.get('phase') != 'J'
            or spec.get('exploration') != 'independent' or spec.get('hold_ticks') != 1
            or spec.get('scope') != 'scheduled'):
        raise ValueError('J-only finger skill requires independent K1 and scheduled scope')
    ppo = settings['ppo']
    if (ppo.get('advantage_normalization') != 'joint' or ppo.get('cost_weight') != 1.
            or ppo.get('episode_cost_budget') is not None or ppo.get('lambda_lr') != 0.):
        raise ValueError('J-only finger skill requires joint advantages and fixed cost weight one')


def _planned_budget(schedule):
    return schedule.config['planned_transitions']


def _apply_progress(pool, schedule):
    pool.set_training_progress(schedule.committed_transitions)


def checkpoint_metadata(settings, schedule, pool, *, input_pins=None, **extra):
    return dict(schema=resume_schema(settings), settings=copy.deepcopy(settings),
        curriculum=schedule.state_dict(), sampler=pool.environment.sampler.state_dict(),
        input_pins=copy.deepcopy(input_pins or {}),
        resume_scope='J model/Adam/RNG/exposure/sampler; fresh prepared episodes', **extra)


def restore_checkpoint(trainer, pool, schedule, checkpoint):
    metadata = trainer.load(checkpoint)
    if not isinstance(metadata, dict) or metadata.get('schema') != RESUME_SCHEMA:
        raise ValueError('J-only finger-skill checkpoint metadata required')
    _validate_joint_settings(metadata['settings'])
    _validate_pins(metadata)
    schedule.load_state_dict(metadata['curriculum'])
    pool.environment.sampler.load_state_dict(metadata['sampler'])
    _apply_progress(pool, schedule)
    pool.observation = pool.reset()[0]
    return metadata


def _validate_pins(metadata):
    changed = [path for path, value in metadata.get('input_pins', {}).items()
               if not Path(path).is_file() or digest(path) != value]
    if changed:
        raise ValueError('checkpoint input sources changed: '+str(changed[:8]))


def _pins(settings, out, extra=()):
    from guitar_learning.runtime.prepared_reset_v1 import prepared_input_paths, BASELINE_CONFIG
    from guitar_learning.native.paths import pin
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
    from guitar_learning.training.policy import FingerSkillPolicy
    return FingerSkillPolicy(pool.observation['state'].shape[-1], size=settings['size'],
        contract=pool.contract).to(settings['device'])


def _train_phase(settings, out, curriculum, *, resume=None, updates=None):
    """J 학습을 실행한다. curriculum은 단계 선택기가 아닌 고정 ExposureSchedule이다."""
    import numpy as np
    import torch
    from guitar_learning.training.rollout import GpuPool
    from guitar_learning.training.rollout import DecisionCollector
    from guitar_learning.training.ppo import DecisionPPOTrainer
    from guitar_learning.training.ppo import PPOConfig
    from guitar_learning.training.training_log_io import Monitor, save_failure_checkpoint
    from guitar_learning.training.training_log_io import TransitionJournal
    # 입력을 봉인하고 결과 파일을 만든 뒤, J 모델·환경을 생성한다.
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    write(out / 'settings.json', settings)
    pins = _pins(settings, out, [Path(value).resolve() for value in (resume,) if value])
    write(out / 'inputs_before.json', pins)
    random.seed(settings['seed'])
    np.random.seed(settings['seed'])
    torch.manual_seed(settings['seed'])
    torch.set_num_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    monitor = Monitor(out, min_available_memory_gib=settings['min_available_memory_gib'])
    journal = TransitionJournal(
        out / 'transitions.jsonl.gz',
        metadata=dict(
            schema=TRANSITION_SCHEMA,
            physics_hz=240,
            control_hz=60,
            family=settings['finger_skill']['schema'],
            scope='raw control transitions',
        ),
    )
    decisions = TransitionJournal(
        out / 'decisions.jsonl.gz',
        metadata=dict(
            schema='guitar_learning.finger_decision.v1',
            scope='one row per sampled decision; raw control references',
        ),
    )
    episodes = EpisodeWriter(out)
    checkpoints = CheckpointRecorder(out)
    metrics_stream = (out / 'learning_metrics.jsonl').open('x')
    pool = trainer = None
    failure, recovery, cleanup_errors = (None, None, [])
    recovery_eligible, current_update, used_updates = (False, 0, 0)
    stopped = 'updates_complete'
    started = time.monotonic()
    episode_ids = []
    min_cuda_free = None
    # 이번 PPO에 반영한 노출과 아직 반영하지 않은 수집분을 분리한다.
    committed_exposure = dict(phrases=0, full_song=0)
    update_exposure = dict(phrases=0, full_song=0)
    exposure_committed = False
    limit = updates

    def guard(context=None):
        nonlocal min_cuda_free
        free, _ = torch.cuda.mem_get_info()
        if free < 1024 ** 3:
            torch.cuda.empty_cache()
            free, _ = torch.cuda.mem_get_info()
        min_cuda_free = free if min_cuda_free is None else min(min_cuda_free, free)
        if free < 1024 ** 3:
            raise MemoryError('GPU free memory below 1 GiB resource floor')
        monitor.progress(context) if context is not None else monitor.check()

    def raw(tick, reward, cost, terminated, truncated, rows):
        # 호출 한 번은 한 60Hz tick의 N환경 묶음이다. 저널 한 행이 N개 전이를 참조한다.
        full = int(pool.environment.focus_mask.all(dim=-1).sum())
        update_exposure['full_song'] += full
        update_exposure['phrases'] += settings['num_envs'] - full
        refs = [episodes.append(row, current_update, tick) for row in rows]
        episode_ids.extend((ref['episode_id'] for ref in refs))
        if journal.stats['pending_rows'] == 59:
            # 다음 행이 60행 gzip 묶음을 확정하기 전에 참조 에피소드를 먼저 동기화한다.
            episodes.sync()
        journal.write(dict(
            schema=TRANSITION_SCHEMA,
            update_index=current_update,
            tick_in_update=tick,
            reward=reward.tolist(),
            cost=cost.tolist(),
            terminated=terminated.tolist(),
            truncated=truncated.tolist(),
            episode_refs=refs,
        ))

    def metadata(**extra):
        return checkpoint_metadata(
            settings,
            curriculum,
            pool,
            input_pins=pins,
            requested_run_budget_transitions=updates * settings['horizon'] * settings['num_envs'] if updates is not None else None,
            original_phase_budget=_planned_budget(curriculum),
            exposure_transitions=copy.deepcopy(committed_exposure),
            manual_budget_extension=resume is not None and updates is not None,
            **extra,
        )

    def save(name, kind, **extra):
        checkpoints.record(out / name, kind, trainer.updates, lambda: trainer.save(out / name, metadata=metadata(**extra)))
    try:
        monitor.start()
        guard()
        pool = GpuPool(settings, out)
        write(out / 'training_contract.json', pool.contract)
        policy = _policy(settings, pool)
        with torch.no_grad():
            shift = math.log(settings['initial_std']) + 3.0
            policy.support_log_std.add_(shift)
            policy.finger_log_std.add_(shift)
        trainer = DecisionPPOTrainer(policy, PPOConfig(**settings['ppo']))
        if pool.environment.approach_gamma != trainer.config.gamma:
            raise ValueError('surface potential and PPO reward discount must match')
        if resume:
            restored_metadata = restore_checkpoint(trainer, pool, curriculum, resume)
            saved_exposure = restored_metadata.get('exposure_transitions')
            if (not isinstance(saved_exposure, dict) or
                    saved_exposure.keys() != committed_exposure.keys() or
                    any((type(value) is not int or value < 0 for value in saved_exposure.values())) or
                    (sum(saved_exposure.values()) != curriculum.committed_transitions)):
                raise ValueError('strict committed exposure counters required')
            committed_exposure.update(saved_exposure)
        _apply_progress(pool, curriculum)
        if limit is None:
            limit = math.ceil(curriculum.status()['remaining_transitions'] / (settings['horizon'] * settings['num_envs']))
        recovery_eligible = True
        save('initial.pt', 'initial')
        collector = DecisionCollector(policy, pool, gamma=trainer.config.gamma, cost_gamma=trainer.config.cost_gamma)
        # 수집 → PPO → 저널 commit → 일정 commit → 환경 진행도 갱신 순서를 유지한다.
        for index in range(limit):
            if settings['max_wall_seconds'] is not None and time.monotonic() - started >= settings['max_wall_seconds']:
                stopped = 'wall_budget'
                break
            current_update = trainer.updates
            update_exposure.update(phrases=0, full_song=0)
            exposure_committed = False
            episode_ids.clear()
            monitor.set_phase('collecting', update_index=current_update, ticks=0, horizon=settings['horizon'])
            pool.environment.reset_reward_window()
            begin = time.monotonic()
            buffer, completed = collector.collect(
                settings['horizon'],
                progress_callback=guard,
                transition_callback=raw,
                decision_callback=lambda row: decisions.write(dict(
                    schema='guitar_learning.finger_decision.v1',
                    update_index=current_update,
                    **row,
                )),
                policy_version=trainer.updates,
            )
            torch.cuda.synchronize()
            collect_s = time.monotonic() - begin
            monitor.set_phase('optimizing')
            # optimizer 갱신부터 commit 완료까지는 복구 checkpoint를 만들 수 없다.
            recovery_eligible = False
            begin = time.monotonic()
            metrics = trainer.update(buffer, completed)
            transitions = settings['horizon'] * settings['num_envs']
            episodes.sync()
            journal.commit(transitions)
            decisions.commit(int(buffer['valid'].sum()))
            curriculum.commit(transitions)
            if sum(update_exposure.values()) != transitions:
                raise ValueError('actual exposure counts must equal raw committed transitions')
            for scope in committed_exposure:
                committed_exposure[scope] += update_exposure[scope]
            exposure_committed = True
            _apply_progress(pool, curriculum)
            recovery_eligible = True
            torch.cuda.synchronize()
            metrics.update(
                schema=METRICS_SCHEMA,
                update_index=current_update,
                optimizer_updates=trainer.updates,
                phase=policy.phase,
                transitions=transitions,
                decisions=int(buffer['valid'].sum()),
                collection_s=collect_s,
                update_s=time.monotonic() - begin,
                completed_episode_ids=list(episode_ids),
                episode_summary=episode_summary(completed),
                mean_reward=float(buffer['reward'][buffer['valid']].mean()),
                mean_cost=float(buffer['cost'][buffer['valid']].mean()),
                mean_reward_cost_scope='discounted decision sums; raw control values in transitions journal',
                reward_component_means=pool.environment.reward_window_means(transitions),
                curriculum=curriculum.status(),
                journal=journal.stats,
                decision_journal=decisions.stats,
                exposure_transitions=copy.deepcopy(update_exposure),
                cumulative_exposure_transitions=copy.deepcopy(committed_exposure),
            )
            metrics_stream.write(json_io.dumps(metrics, allow_nan=False) + '\n')
            metrics_stream.flush()
            del buffer
            used_updates += 1
            if (index + 1) % settings['checkpoint_every'] == 0 and index + 1 < limit:
                save('checkpoint_%06d.pt' % trainer.updates, 'periodic')
            guard()
        # 최종 저장 뒤에는 장면·로그 종료와 입력 무결성을 확인한다.
        save('final.pt', 'final', stopped=stopped, updates_in_run=used_updates)
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc())
        stopped = 'interrupted' if isinstance(error, KeyboardInterrupt) else 'error'
        if pool is not None:
            recovery = checkpoints.record(
                out / 'failure_last_valid.pt',
                'recovery',
                trainer.updates if trainer else None,
                lambda: save_failure_checkpoint(
                    trainer, out, metadata(recovery_scope='incomplete rollout discarded'),
                    eligible=recovery_eligible,
                ),
            )
        raise
    finally:
        # 저널을 닫기 전에 참조 에피소드를 동기화하고 미반영 수집분은 폐기 표시한다.
        for name, callback in [
            ('pool', pool.close if pool else lambda: None),
            ('episodes', episodes.sync),
            ('raw journal', journal.close),
            ('decision journal', decisions.close),
        ]:
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
        missing = sorted(project_source_paths(list(sys.modules.items())) - set(pins))
        audit = pool.scene.diagnostics if pool and pool.scene else None
        lifecycle = bool(
            audit and audit['closed'] and audit['physx_use_gpu'] and audit['use_gpu_pipeline']
            and (audit['simulator_count'] == 1)
            and (audit['environment_count'] == settings['num_envs'])
        )
        verified = not (changed or missing or cleanup_errors) and lifecycle
        report = dict(
            schema=SCHEMA,
            completed=failure is None and verified,
            stopped=stopped,
            phase=settings['finger_skill']['phase'],
            settings=settings,
            optimizer_updates=trainer.updates if trainer else 0,
            updates_in_run=used_updates,
            transitions=journal.stats['committed'],
            journal=journal.stats,
            decision_journal=decisions.stats,
            checkpoints=checkpoints.stats,
            failure=failure,
            recovery_checkpoint=recovery,
            changed_inputs=changed,
            missing_import_pins=missing,
            cleanup_errors=cleanup_errors,
            lifecycle_verified=lifecycle,
            gpu_scene=audit,
            min_cuda_free_bytes=min_cuda_free,
            wall_s=time.monotonic() - started,
            curriculum=curriculum.state_dict(),
            partial_episodes_are_successes=False,
            requested_run_updates=updates,
            original_phase_budget=_planned_budget(curriculum),
            exposure_transitions=committed_exposure,
            sampled_uncommitted_exposure_transitions=update_exposure if not exposure_committed else None,
            discarded_from_learning_exposure_transitions=update_exposure if not exposure_committed else None,
            manual_budget_extension=resume is not None and updates is not None,
        )
        write(out / 'report.json', report)
        if failure is None and (not verified):
            raise RuntimeError('finger-skill phase source/lifecycle check failed; see report.json')
    return dict(report=report, checkpoint=str(out / 'final.pt'))


class _DeterministicPolicy:
    def __init__(self, policy):
        self.policy, self.phase = policy, policy.phase

    def __call__(self, *inputs):
        return self.policy(*inputs)

    def act(self, *inputs):
        return self.policy.act(*inputs, deterministic=True)


def evaluate_checkpoint(checkpoint, out, *, num_envs=None, scope='full_song', max_batches=1, max_episodes=512, deadline=None):
    """완결된 에피소드를 평가하며, 실패와 환경별 고정 분모를 유지한다.

    먼저 끝난 환경은 다른 환경이 끝날 때까지 정상적으로 초기화한다.
    해당 환경의 후속 에피소드는 이번 평가 묶음에서 제외하며, 반환 전에 장면을 닫는다.
    """
    import isaacgym
    import torch
    from guitar_learning.training.rollout import GpuPool
    from guitar_learning.training.rollout import DecisionCollector
    from guitar_learning.training.ppo import DecisionPPOTrainer
    from guitar_learning.training.ppo import PPOConfig
    from guitar_learning.training.training_log_io import Monitor
    if scope not in ('phrases', 'full_song'):
        raise ValueError('phrases/full_song evaluation scope required')
    if type(max_batches) is not int or max_batches < 1 or type(max_episodes) is not int or max_episodes < 1:
        raise ValueError('positive evaluation limits required')
    checkpoint, out = (Path(checkpoint).resolve(), Path(out).resolve())
    payload = torch.load(checkpoint, map_location='cpu', weights_only=False)
    metadata = payload.get('metadata')
    if not isinstance(metadata, dict) or metadata.get('schema') != resume_schema(metadata.get('settings', {})):
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
    write(out / 'settings.json', settings)
    pins = _pins(settings, out, [checkpoint])
    write(out / 'inputs_before.json', pins)
    monitor = Monitor(out, min_available_memory_gib=settings['min_available_memory_gib'])
    writer = EpisodeWriter(out)
    pool = None
    rows, failure, cleanup_errors = ([], None, [])
    actual_transitions, batches = (0, 0)
    started = time.monotonic()
    report = None
    try:
        monitor.start()
        pool = GpuPool(settings, out)
        policy = _policy(settings, pool)
        trainer = DecisionPPOTrainer(policy, PPOConfig(**settings['ppo']))
        trainer.load(checkpoint)
        pool.environment.set_evaluation(enabled=True, full_song=scope == 'full_song')
        pool.observation = pool.reset()[0]
        collector = DecisionCollector(
            _DeterministicPolicy(policy),
            pool,
            gamma=trainer.config.gamma,
            cost_gamma=trainer.config.cost_gamma,
        )
        opportunities = [0] * 4
        for batch in range(max_batches):
            count = min(settings['num_envs'], max_episodes - len(rows))
            if count <= 0:
                break
            seen = set()
            max_ticks = math.ceil(pool.environment.task.duration_s * 60) + settings['horizon']
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
                if free < 1024 ** 3:
                    torch.cuda.empty_cache()
                    free, _ = torch.cuda.mem_get_info()
                if free < 1024 ** 3:
                    raise MemoryError('GPU evaluation free memory below 1 GiB floor')
                monitor.progress(context)
            while len(seen) < count and elapsed_ticks < max_ticks:
                horizon = min(settings['horizon'], max_ticks - elapsed_ticks)
                buffer, _ = collector.collect(horizon, transition_callback=record, progress_callback=guard)
                del buffer
                elapsed_ticks += horizon
            if len(seen) != count:
                raise RuntimeError('fixed evaluation did not finish every scheduled first episode')
            batches += 1
        writer.sync()
        report = dict(
            schema='guitar_learning.finger_skill_evaluation.v1',
            checkpoint=str(checkpoint),
            checkpoint_sha256=digest(checkpoint),
            phase=policy.phase,
            scope=scope,
            episodes=len(rows),
            batches=batches,
            finger_opportunities=opportunities,
            limits=dict(
                max_batches=max_batches,
                max_episodes=max_episodes,
                requested_max_episodes=requested_max_episodes,
                all_envs_in_first_batch=True,
            ),
            actual_simulated_transitions=actual_transitions,
            selected_episode_transitions=sum((row['steps'] for row in rows)),
            first_episode_per_env_per_batch=True,
            failed_episodes_in_denominator=True,
            summary=episode_summary(rows),
            wall_s=time.monotonic() - started,
            settings=settings,
            training_contract=pool.contract,
        )
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc())
        raise
    finally:
        for name, callback in (
            ('pool', pool.close if pool else lambda: None),
            ('episodes', writer.close),
            ('monitor', lambda: monitor.close('error' if failure else 'evaluation_complete')),
        ):
            try:
                callback()
            except BaseException as error:
                cleanup_errors.append(dict(component=name, message=str(error)))
        changed = [path for path, value in pins.items() if not Path(path).is_file() or digest(path) != value]
        missing = sorted(project_source_paths(list(sys.modules.items())) - set(pins))
        audit = pool.scene.diagnostics if pool and pool.scene else None
        lifecycle = bool(
            audit and audit['closed'] and audit['physx_use_gpu'] and audit['use_gpu_pipeline']
            and (audit['simulator_count'] == 1)
            and (audit['environment_count'] == settings['num_envs'])
        )
        report = dict(
            report or {},
            actual_simulated_transitions=actual_transitions,
            selected_episode_transitions=sum((row['steps'] for row in rows)),
            episodes=len(rows),
            completed=failure is None and (not (changed or missing or cleanup_errors)) and lifecycle,
            failure=failure,
            changed_inputs=changed,
            missing_import_pins=missing,
            cleanup_errors=cleanup_errors,
            lifecycle_verified=lifecycle,
            gpu_scene=audit,
        )
        write(out / 'report.json', report)
        if failure is None and (not report['completed']):
            raise RuntimeError('finger-skill evaluation source/lifecycle check failed')
    return (report, rows)


def run(settings, args):
    import isaacgym
    import torch
    if settings['device'] != 'cuda:0' or not torch.cuda.is_available():
        raise RuntimeError('J-only finger-skill requires CUDA GPU physics; no CPU fallback')
    settings = copy.deepcopy(settings)
    _validate_joint_settings(settings)
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    spec = settings['finger_skill']
    schedule = ExposureSchedule(spec['planned_transitions'], spec['full_song_after'])
    resume = Path(args.resume).resolve() if args.resume else None
    started = time.monotonic()
    stages, stopped, failure, current_checkpoint = [], 'updates_complete', None, None
    try:
        if resume:
            payload = torch.load(resume, map_location='cpu', weights_only=False)
            metadata = payload.get('metadata', {})
            if metadata.get('schema') != RESUME_SCHEMA:
                raise ValueError('J-only finger-skill resume metadata required')
            _validate_joint_settings(metadata['settings'])
            _validate_pins(metadata)
            saved = metadata['curriculum']['config']
            schedule = ExposureSchedule(saved['planned_transitions'], saved['full_song_after'])
            schedule.load_state_dict(metadata['curriculum'])
        spec.update(schedule.config)
        write(out/'settings.json', settings)
        result = _train_phase(settings, out/'J', schedule, resume=resume, updates=settings['updates'])
        stages.append(result)
        current_checkpoint = result['checkpoint']
        stopped = result['report']['stopped']
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc())
        stopped = 'interrupted' if isinstance(error, KeyboardInterrupt) else 'error'
        raise
    finally:
        if not (out/'settings.json').exists():
            write(out/'settings.json', settings)
        report = dict(schema=SCHEMA, completed=failure is None and stopped == 'updates_complete',
            stopped=stopped, settings=settings, final_phase='J', final_checkpoint=current_checkpoint,
            stages=stages, curriculum=schedule.state_dict(), failure=failure,
            budgets_are_raw_control_transitions=True, training_transitions=schedule.committed_transitions,
            exposure_transitions=stages[-1]['report'].get('exposure_transitions') if stages else None,
            manual_budget_extension=resume is not None, requested_run_updates=settings['updates'],
            wall_s=time.monotonic()-started)
        write(out/'report.json', report)
    return report
