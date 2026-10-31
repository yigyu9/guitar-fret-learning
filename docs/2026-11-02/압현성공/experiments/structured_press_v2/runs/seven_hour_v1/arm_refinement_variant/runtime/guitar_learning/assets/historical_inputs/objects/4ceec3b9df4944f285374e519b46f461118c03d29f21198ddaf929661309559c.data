"""Unchanged physical pilot with a bounded81 baseline residual."""
import copy
from unittest.mock import patch

from . import deadline_native_v1 as old
from . import deadline_native_v4 as previous
from .deadline_bounded_residual_v1 import CAPS_RAD, bounded_target

PROFILE = copy.deepcopy(previous.PROFILE)
PROFILE['name'] = 'stability_guarded_update_pilot_v1'


class NativeDeadlineEnvironment(previous.NativeDeadlineEnvironment):
    def reset(self):
        with patch.object(previous, 'PROFILE', PROFILE):
            observation = super().reset()
        self.metadata['residual_caps_rad'] = CAPS_RAD.copy()
        return observation

    def previous_update_abi(self):
        return super().abi()

    def abi(self):
        with patch.object(previous, 'PROFILE', PROFILE):
            abi = super().abi()
        abi.update(version='stability_guarded825_v1',
                   action_codec='bounded radian residual around dynamic baseline; single rate owner',
                   residual_caps_rad=CAPS_RAD.copy(),
                   policy_update={'version': 'post_step_analytic_kl_v3',
                       'RMS': 'pinned frozen', 'learning_rate': 3e-5,
                       'KL': 'mean old-to-new Gaussian sum81 over complete rollout <=0.02',
                       'rollback': 'model and Adam; 8 half-LR candidates'})
        return abi

    def require_training_ready(self):
        if self._finished or not self._ready or self.metadata['profile']['name'] != PROFILE['name']:
            raise RuntimeError('guarded pilot reset required; finished episode must reset')

    def step(self, action):
        def requested(a, nominal, lower, upper):
            return bounded_target(a, nominal, lower, upper, self.scene.contract.groups)
        with patch.object(old, 'anchored_target', requested), patch.object(previous, 'PROFILE', PROFILE):
            return super().step(action)

    def close(self):
        with patch.object(previous, 'PROFILE', PROFILE):
            return super().close()
