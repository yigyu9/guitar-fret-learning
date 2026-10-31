"""New preparation reward on the immutable500-state native environment."""
import copy
from unittest.mock import patch

import numpy as np

from guitar_learning.runtime.persistent_environment import _CONSTRUCTION_LOCK
from guitar_learning.song import environment as original
from guitar_learning.tool.experiments.transition.environment import TransitionEnvironment, SONG
from guitar_learning.tool.experiments.transition.task import make_task
from guitar_learning.tool.experiments.transition_refinement.reward import RewardLedger, RIGHT_TERMS


class RefinementEnvironment(TransitionEnvironment):
    def reset(self):
        self.refinement_ledger = None
        try:
            observation, info = super().reset()
            self.refinement_ledger = RewardLedger(self.task, self.last_measured, self.transition_config)
            self.contract['reward']['refinement'] = self.refinement_ledger.metadata()
            info['training_contract'] = self.contract
            self._refinement_info(info, False)
            return observation, info
        except BaseException:
            self.close()
            raise

    def _refinement_info(self, info, completed):
        report = self.refinement_ledger.summary(completed)
        report['successful'] = info['transition']['successful']
        report['stage_success'] = report['successful']
        report['role'] = self.role
        info['refinement'] = report
        if 'episode' in info:
            info['episode']['refinement'] = copy.deepcopy(report)

    def step(self, action):
        if self.finished:
            raise RuntimeError('reset required before stepping a finished/uninitialized episode')
        try:
            observation, previous_reward, terminated, truncated, info = super().step(action)
            rows = info['physics_measurements']
            for row in rows:
                row['refinement_reward_terms'] = self.refinement_ledger.update(row['music'])
            reasons = info['failure_reasons']
            if reasons:
                self.refinement_ledger.invalidate(reasons)
                for row in rows:
                    row['refinement_reward_terms'] = {name:min(0., value)
                        for name, value in row['refinement_reward_terms'].items()}
            info['legacy_reward_terms'] = copy.deepcopy(info['reward_terms'])
            keep = {'action_change', 'terminal_failure'} | (set(RIGHT_TERMS) if self.role == 'joint' else set())
            terms = {name:value for name,value in info['reward_terms'].items() if name in keep}
            for row in rows:
                for name, value in row['refinement_reward_terms'].items():
                    terms[name] = terms.get(name, 0.)+value
            reward = float(sum(terms.values()))
            if not np.isfinite(reward):
                raise ValueError('finite refinement reward required')
            self.total_reward += reward-previous_reward
            info['reward_terms'] = terms
            if 'episode' in info:
                info['episode']['reward'] = self.total_reward
            completed = bool(terminated and info['termination_reason'] == 'timeline_complete')
            self._refinement_info(info, completed)
            return observation, reward, terminated, truncated, info
        except BaseException:
            self.finished = True
            raise


def build_environment(config, out, *, bundle, transition, song=None, **kwargs):
    task = make_task(bundle, transition)
    with _CONSTRUCTION_LOCK, patch.object(original.training_environment, 'ContactEnvironment', original.PersistentContactEnvironment):
        return RefinementEnvironment(config, out, task=task, transition=transition,
            song=SONG if song is None else song, **kwargs)
