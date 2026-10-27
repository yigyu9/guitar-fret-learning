"""Actionable pre-roll and fixed-window hand timing over unchanged native physics."""
import copy
from dataclasses import asdict, replace
from unittest.mock import patch
import numpy as np
from guitar_learning.core import training_environment
from guitar_learning.core.training_environment import TrainingEnvironment
from guitar_learning.runtime.persistent_environment import PersistentContactEnvironment, _CONSTRUCTION_LOCK
from guitar_learning.music_task import ScoreTask
from guitar_learning.skills.skill_environment import SkillScoreTask, skill_pick_guide
from guitar_learning.skills.skill_environment_v2 import SkillTrainingEnvironmentV2, SkillObservationBuilder, HISTORY_FIELDS, TIME_FIELDS, COUNT_FIELDS
from guitar_learning.imitation.imitation_environment import profile_settings
from guitar_learning.timing.timing_curriculum import TimingConfig, TimingLedger, TIMING_HISTORY_FIELDS, history_scales

REFERENCE_HORIZON_S = 4.


def execution_task(original, timing):
    """Translate the clock origin, preserving source score times and provenance."""
    if not isinstance(original, ScoreTask) or len(original.targets) != 1 or not original.targets[0].fret:
        raise ValueError('one original fretted target required')
    targets = tuple(replace(t, press_s=t.press_s+timing.pre_roll_s,
        onset_s=t.onset_s+timing.pre_roll_s, end_s=t.end_s+timing.pre_roll_s)
        for t in original.targets)
    horizon = REFERENCE_HORIZON_S+timing.pre_roll_s
    if targets[0].onset_s+timing.window_s > horizon:
        raise ValueError('timing window must fit in the complete policy horizon')
    return SkillScoreTask(targets, original.lookahead_s, original.capacity,
        copy.deepcopy(original.provenance), horizon)


class TimingObservationBuilder(SkillObservationBuilder):
    """Preserve the old 505 field meanings/scales; append visible timing history."""
    def __init__(self, base, environment):
        for name in ('music.remaining_s', 'music.elapsed_s', 'music.held_total_s'):
            base.scales[base.fields.index(name)] = REFERENCE_HORIZON_S
        base.spec['scales'] = base.scales.tolist()
        super().__init__(base, environment)
        self.history_scales = np.array([REFERENCE_HORIZON_S if name in TIME_FIELDS
            else REFERENCE_HORIZON_S*240 if name in COUNT_FIELDS else 1.
            for name in HISTORY_FIELDS])
        self.timing_scales = np.asarray(history_scales(environment.task, environment.timing_config), dtype=float)
        self.scales = np.r_[base.scales, self.history_scales, self.timing_scales]
        self.fields = base.fields+['skill_history.'+name for name in HISTORY_FIELDS]+[
            'timing_history.'+name for name in TIMING_HISTORY_FIELDS]
        self.spec.update(dimension=len(self.fields), fields=self.fields,
            scales=self.scales.tolist(), timing_history=dict(
                schema='guitar_learning.timing_history.v1', fields=list(TIMING_HISTORY_FIELDS),
                clock='same tick end; policy time u >= 0, score time u - pre_roll_s',
                baseline_dimension=505, baseline_normalization_horizon_s=REFERENCE_HORIZON_S))

    def build(self, *args):
        observation = super().build(*args)
        ledger = getattr(self.environment, 'timing_ledger', None)
        values = np.zeros(len(TIMING_HISTORY_FIELDS)) if ledger is None else np.asarray(ledger.history())
        if values.shape != self.timing_scales.shape or not np.isfinite(values).all():
            raise ValueError('finite complete timing history required')
        observation['state'] = np.r_[observation['state'],
            np.clip(values/self.timing_scales, -10., 10.)].astype(np.float32)
        return observation


class TimingEnvironment(SkillTrainingEnvironmentV2):
    def __init__(self, *args, task, role, timing=TimingConfig(), **kwargs):
        if not isinstance(timing, TimingConfig):
            raise ValueError('explicit TimingConfig required')
        self.original_task, self.timing_config = task, timing
        self.timing_ledger = None
        skill = 'hold' if role == 'left' else 'cross'
        skill_config, guide_config, _ = profile_settings(role, skill)
        skill_config = replace(skill_config, horizon_s=REFERENCE_HORIZON_S+timing.pre_roll_s)
        super().__init__(*args, task=execution_task(task, timing), role=role, skill=skill,
            skill_config=skill_config, guide_config=guide_config, **kwargs)

    def _observation(self):
        if not isinstance(self.builder, TimingObservationBuilder):
            base = self.builder.base if isinstance(self.builder, SkillObservationBuilder) else self.builder
            self.builder = TimingObservationBuilder(base, self)
        return TrainingEnvironment._observation(self)

    def reset(self):
        self.timing_ledger = None
        _, info = super().reset()
        self.timing_ledger = TimingLedger(self.task, self.last_measured, self.role, self.timing_config)
        timing = dict(schema='guitar_learning.timing.v1', config=asdict(self.timing_config),
            window_s=self.timing_config.window_s,
            policy_clock='u >= 0 after native settling', score_clock='t = u - pre_roll_s',
            original_targets=[asdict(t) for t in self.original_task.targets],
            original_provenance=copy.deepcopy(self.original_task.provenance),
            baseline_normalization_horizon_s=REFERENCE_HORIZON_S,
            actionable_preparation='policy actions and all240Hz safety/measurement remain active',
            support='individual chest/arm/thigh contact sharing is diagnostic; original native safety unchanged')
        self.contract['task']['timing'] = timing
        self.contract['reward']['timing'] = dict(config=asdict(self.timing_config),
            scope='separate relaxed timing reward; baseline skill reward replaced; original music ledger unchanged',
            safety='positive timing terms suppressed on failed tick; original costs and termination unchanged')
        info['training_contract'] = self.contract
        self._timing_info(info, completed=False)
        return self._observation(), info

    def _timing_info(self, info, completed):
        timing = self.timing_ledger.summary(completed=completed)
        info['timing'] = timing
        info['score_time_s'] = self.last_measured['task_time_s']-self.timing_config.pre_roll_s
        # Retain baseline hand evidence while selecting the new timing objective.
        info['specialist'].update(stage_success=timing['stage_success'],
            provisional_success=timing['provisional_success'],
            safety_invalidated=timing['safety_invalidated'], safety_reasons=timing['safety_reasons'],
            success_criterion='explicit fixed-window timing stage; original joint music remains separate',
            timing=copy.deepcopy(timing))
        if 'episode' in info:
            info['episode']['specialist'] = copy.deepcopy(info['specialist'])
            info['episode']['timing'] = copy.deepcopy(timing)
            info['episode']['score_time_s'] = info['score_time_s']

    def step(self, action):
        try:
            _, base_reward, terminated, truncated, info = super().step(action)
            additions = {}
            for sample, row in zip(info['native_control']['physics_samples240'], info['physics_measurements']):
                guide = (skill_pick_guide(self.task, sample, row['music']['task_time_s'],
                    'timed', self.guide_config) if self.role == 'right' else None)
                terms = self.timing_ledger.update(row['music'], guide)
                if row['stability']['failure_reasons']:
                    self.timing_ledger.invalidate(row['stability']['failure_reasons'])
                row['timing'] = self.timing_ledger.summary(completed=False)
                row['score_time_s'] = row['music']['task_time_s']-self.timing_config.pre_roll_s
                for key, value in terms.items():
                    additions[key] = additions.get(key, 0.)+value
            if info['failure_reasons']:
                self.timing_ledger.invalidate(info['failure_reasons'])
                additions = {k: min(0., value) for k, value in additions.items()}
            terms = {key: info['reward_terms'][key] for key in ('action_change', 'terminal_failure')}
            terms.update(additions)
            reward = float(sum(terms.values()))
            if not np.isfinite(reward):
                raise ValueError('finite timing reward required')
            self.total_reward += reward-base_reward
            info['reward_terms'] = terms
            self._timing_info(info, completed=bool(terminated and info['termination_reason'] == 'timeline_complete'))
            if 'episode' in info:
                info['episode']['reward'] = self.total_reward
            return self._observation(), reward, terminated, truncated, info
        except BaseException:
            self.finished = True
            raise


def build_environment(config, out, *, role, bundle, timing=TimingConfig(), stage='B',
        start_event_index=0, phrase_events=8, tempo_scale=1., seed=7, worker_id=0, music=None, **kwargs):
    music = dict(music or {})
    if (role not in ('left', 'right') or stage != 'B' or start_event_index != 0 or tempo_scale != 1.
            or set(music)-{'reward_mode', 'goal_event_indices'}
            or music.get('reward_mode', 'legacy') != 'legacy' or music.get('goal_event_indices') is not None):
        raise ValueError('timing v1 requires fixed first original single-note hand task at tempo1')
    task = ScoreTask.from_bundle(bundle, stage=stage, start_event_index=start_event_index,
        phrase_events=phrase_events, tempo_scale=tempo_scale)
    with _CONSTRUCTION_LOCK:
        with patch.object(training_environment, 'ContactEnvironment', PersistentContactEnvironment):
            return TimingEnvironment(config, out, role=role, task=task, timing=timing, **kwargs)
