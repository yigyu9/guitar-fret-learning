"""Make the former first2s native settling available to the policy and rewards."""
import copy
from unittest.mock import patch
import numpy as np
from .environment_v5 import FreeGuitarEnvironment
from .training_environment import ContactEnvironment as OriginalContactEnvironment
from .persistent_environment import (PersistentContactEnvironment as OriginalPersistentContactEnvironment,
    _CONSTRUCTION_LOCK)
from . import training_environment
from .music_task import ScoreTask
from .timing_environment import TimingEnvironment
from .timing_curriculum import TimingConfig


TASK_METADATA = dict(schema='guitar_learning.actionable_preparation.v1',
    native_preparation_seconds=0., policy_pre_roll_s=3., initial_policy_preparation_s=2.,
    replaced_native_preparation_s=2., physical_horizon_s=7.,
    scope='policy controls all39 allowed channels from first native step; original score+3 and absolute note timing retained')
REWARD_METADATA = dict(schema='guitar_learning.preparation_contact.v1', role='left',
    interval_policy_s=[0., 2.], weight_per_second=.2,
    measurement='original target candidate from measured native contact; unchanged candidate definition',
    integration='mean previous-and-current positive candidate interval duration clipped to policy[0,2] at actual240Hz; first isolated positive sample has no duration; positive terms suppressed for entire failed control tick',
    scope='shaping only; timing/music success unchanged')


class ContactEnvironment(FreeGuitarEnvironment, OriginalContactEnvironment):
    """Use v5 duration support and the exact original contact snapshot methods.

    The cooperative MRO places original contact reset/snapshot before the shared
    v4 physical methods. No native measurement or force API is replaced.
    """


class PersistentContactEnvironment(ContactEnvironment, OriginalPersistentContactEnvironment):
    """Retain original persistent session ownership/reset/error cleanup with v5."""


class ActionablePreparationEnvironment(TimingEnvironment):
    def __init__(self, *args, timing=TimingConfig(pre_roll_s=3.), preparation_seconds=0., **kwargs):
        if not isinstance(timing, TimingConfig) or timing.pre_roll_s != 3.:
            raise ValueError('actionable preparation requires fixed3s policy pre-roll')
        if isinstance(preparation_seconds, bool) or preparation_seconds != 0.:
            raise ValueError('actionable preparation requires native preparation_seconds0')
        super().__init__(*args, timing=timing, preparation_seconds=0., **kwargs)

    def reset(self):
        observation, info = super().reset()
        self.contract['task']['actionable_preparation'] = copy.deepcopy(TASK_METADATA)
        self.contract['reward']['actionable_preparation'] = copy.deepcopy(REWARD_METADATA)
        info['training_contract'] = self.contract
        return observation, info

    def step(self, action):
        try:
            previous = getattr(self, 'last_measured', None)
            observation, reward, terminated, truncated, info = super().step(action)
            extra = 0.
            for row in info['physics_measurements']:
                value = 0.
                measured = row['music']
                if self.role == 'left':
                    duration = max(0., min(measured['task_time_s'], 2.)-max(previous['task_time_s'], 0.))
                    both = [bool(previous['targets'][target.target_id]['candidate']) and
                            bool(measured['targets'][target.target_id]['candidate'])
                            for target in self.task.targets]
                    value = .2*duration*float(np.mean(both))
                if not np.isfinite(value):
                    raise ValueError('finite preparation contact reward required')
                row['preparation_contact_reward'] = value
                extra += value
                previous = measured
            if info['failure_reasons']:
                extra = 0.
                for row in info['physics_measurements']: row['preparation_contact_reward'] = 0.
            reward += extra
            self.total_reward += extra
            info['reward_terms']['preparation_contact'] = extra
            if 'episode' in info: info['episode']['reward'] = self.total_reward
            return observation, reward, terminated, truncated, info
        except BaseException:
            self.finished = True
            raise


def build_environment(config, out, *, role, bundle, timing=TimingConfig(pre_roll_s=3.), stage='B',
        start_event_index=0, phrase_events=8, tempo_scale=1., seed=7, worker_id=0, music=None, **kwargs):
    music = dict(music or {})
    if (role not in ('left', 'right') or stage != 'B' or start_event_index != 0 or tempo_scale != 1.
            or set(music)-{'reward_mode', 'goal_event_indices'}
            or music.get('reward_mode', 'legacy') != 'legacy' or music.get('goal_event_indices') is not None):
        raise ValueError('actionable timing requires fixed first original fretted note at tempo1')
    task = ScoreTask.from_bundle(bundle, stage=stage, start_event_index=start_event_index,
                                 phrase_events=phrase_events, tempo_scale=tempo_scale)
    with _CONSTRUCTION_LOCK:
        with patch.object(training_environment, 'ContactEnvironment', PersistentContactEnvironment):
            return ActionablePreparationEnvironment(config, out, role=role, task=task, timing=timing, **kwargs)
