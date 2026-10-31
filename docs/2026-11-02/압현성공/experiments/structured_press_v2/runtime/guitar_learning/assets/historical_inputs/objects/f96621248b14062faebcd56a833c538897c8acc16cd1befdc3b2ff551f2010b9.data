"""Skill curriculum with observable objective history; native physics is v1.

The added state is common across all seven stages. One-shot achievement and
continuous dwell are policy inputs rather than hidden reward bookkeeping.
"""
import copy
from unittest.mock import patch
import numpy as np
from . import training_environment
from .skill_environment import SkillTrainingEnvironment
from .music_task import ScoreTask
from .persistent_environment import PersistentContactEnvironment, _CONSTRUCTION_LOCK

HISTORY_FIELDS = (
    'reached', 'contact_acquired', 'held', 'ready', 'crossed',
    'previous_candidate', 'candidate_dwell_s', 'candidate_longest_dwell_s', 'candidate_valid_s',
    'ready_dwell_s', 'previous_ready', 'has_first_success', 'first_success_s',
    'provisional_success', 'safety_invalidated', 'timed_safety_invalidated',
    'timed_acquired', 'timed_dwelled', 'timed_left_missed',
    'timed_right_matched50', 'timed_right_matched100', 'timed_right_missed',
    'timed_candidate', 'timed_previous_candidate', 'timed_valid_s',
    'timed_dwell_s', 'timed_longest_dwell_s', 'timed_acquisitions',
    'timed_releases', 'timed_timely_releases',
    'geometric_crossings', 'matching_crossings', 'duplicate_crossings',
    'timed_geometric_crossings', 'timed_matching_crossings',
    'timed_wrong_crossings', 'timed_duplicate_crossings',
)
TIME_FIELDS = {name for name in HISTORY_FIELDS if name.endswith('_s')}
COUNT_FIELDS = {'timed_acquisitions', 'timed_releases', 'timed_timely_releases',
    'geometric_crossings', 'matching_crossings', 'duplicate_crossings',
    'timed_geometric_crossings', 'timed_matching_crossings',
    'timed_wrong_crossings', 'timed_duplicate_crossings'}


def history_values(ledger):
    if ledger is None:
        return np.zeros(len(HISTORY_FIELDS), dtype=float)
    identity = ledger.task.targets[0].target_id
    timed, state = ledger.timed, ledger.timed.left[identity]
    values = (
        identity in ledger.reached, identity in ledger.contacts, identity in ledger.held,
        identity in ledger.ready, identity in ledger.crossed,
        ledger.previous[identity], ledger.dwell[identity], ledger.longest[identity], ledger.valid_s[identity],
        ledger.ready_dwell, ledger.previous_ready, ledger.first_success_s is not None,
        ledger.first_success_s if ledger.first_success_s is not None else 0.,
        ledger.provisional() and not ledger.reasons, bool(ledger.reasons), bool(timed.safety_reasons),
        identity in timed.acquired, identity in timed.dwelled, identity in timed.left_missed,
        identity in timed.right_matches[.05], identity in timed.right_matches[.1], identity in timed.right_missed,
        state['candidate'], timed.previous_candidates[identity], state['valid_s'],
        state['dwell_s'], state['longest_dwell_s'], state['acquisitions'],
        state['releases'], state['timely_releases'],
        ledger.geometric, ledger.matching, ledger.duplicates,
        timed.geometric_crossings, timed.matching_crossings, timed.wrong_crossings, timed.duplicate_crossings,
    )
    result = np.asarray(values, dtype=float)
    if result.shape != (len(HISTORY_FIELDS),) or not np.isfinite(result).all():
        raise ValueError('finite complete single-target skill history required')
    return result


class SkillObservationBuilder:
    """Keep original body/music inputs and append normalized ledger history."""
    def __init__(self, base, environment):
        self.base, self.environment = base, environment
        horizon = environment.skill_config.horizon_s
        self.history_scales = np.array([
            horizon if name in TIME_FIELDS else horizon*240 if name in COUNT_FIELDS else 1.
            for name in HISTORY_FIELDS], dtype=float)
        self.fields = base.fields+['skill_history.'+name for name in HISTORY_FIELDS]
        self.scales = np.r_[base.scales, self.history_scales]
        self.spec = copy.deepcopy(base.spec)
        self.spec.update(dimension=len(self.fields), fields=self.fields,
            scales=self.scales.tolist(),
            skill_history=dict(schema='guitar_learning.skill_history.v2',
                fields=list(HISTORY_FIELDS), scope='single selected target; common order/scales for all seven skills',
                clock='history after the returned240Hz measurements, before the next action',
                duplicate_scope='native detector crossing IDs are unique monotonically advancing physics-step/string pairs'))

    def build(self, *args):
        observation = self.base.build(*args)
        history = history_values(getattr(self.environment, 'skill_ledger', None))
        observation['state'] = np.r_[observation['state'],
            np.clip(history/self.history_scales, -10., 10.)].astype(np.float32)
        return observation


class SkillTrainingEnvironmentV2(SkillTrainingEnvironment):
    def _observation(self):
        if not isinstance(self.builder, SkillObservationBuilder):
            self.builder = SkillObservationBuilder(self.builder, self)
        return super()._observation()

    def reset(self):
        # Base reset builds an observation before creating the new skill ledger.
        # Clear the previous episode first, then return a rebuilt fresh state.
        self.skill_ledger = None
        _, info = super().reset()
        visibility = self.contract['observation']['skill_token_visibility']
        self.contract['observation'] = copy.deepcopy(self.builder.spec)
        self.contract['observation']['skill_token_visibility'] = visibility
        self.contract['task']['specialist']['schema'] = 'guitar_learning.skill.v2'
        info['training_contract'] = self.contract
        return self._observation(), info

    def step(self, action):
        # v1 computes native observations before its reward ledger is updated.
        # Rebuild here to expose history through the end of this same tick.
        _, reward, terminated, truncated, info = super().step(action)
        return self._observation(), reward, terminated, truncated, info


def build_skill_environment(config, out, *, role, skill, bundle, stage='B',
        start_event_index=0, phrase_events=8, tempo_scale=1., seed=7,
        worker_id=0, music=None, **kwargs):
    music = dict(music or {})
    if (stage != 'B' or set(music)-{'reward_mode', 'goal_event_indices'} or
            music.get('reward_mode', 'legacy') != 'legacy' or music.get('goal_event_indices') is not None):
        raise ValueError('skill environment requires fixed stage B, legacy setting and no pool')
    task = ScoreTask.from_bundle(bundle, stage=stage, start_event_index=start_event_index,
                                 phrase_events=phrase_events, tempo_scale=tempo_scale)
    with _CONSTRUCTION_LOCK:
        with patch.object(training_environment, 'ContactEnvironment', PersistentContactEnvironment):
            return SkillTrainingEnvironmentV2(config, out, role=role, skill=skill, task=task, **kwargs)
