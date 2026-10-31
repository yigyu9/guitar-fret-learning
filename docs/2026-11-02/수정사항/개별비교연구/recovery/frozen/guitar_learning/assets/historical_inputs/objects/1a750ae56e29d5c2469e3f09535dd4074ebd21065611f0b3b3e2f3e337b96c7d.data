"""Original finite native control with explicit zero-duration reset settling.

The inherited stepping, target ownership and guard checks remain unchanged.
Zero means policy handoff immediately after the prepared state boundary reset.
"""
from numbers import Real
import numpy as np
from .environment_v4 import FreeGuitarEnvironment as PreviousEnvironment


class FreeGuitarEnvironment(PreviousEnvironment):
    def __init__(self, *args, preparation_seconds=2., **kwargs):
        if (isinstance(preparation_seconds, bool) or not isinstance(preparation_seconds, Real)
                or not np.isfinite(preparation_seconds)
                or not (preparation_seconds == 0. or 1. <= preparation_seconds <= 2.)):
            raise ValueError('preparation_seconds must be0 or within1..2 seconds')
        # Let the original constructor validate every other control argument.
        # Its supported1s branch performs no physics until reset; replace only
        # the requested reset duration before construction returns.
        super().__init__(*args, preparation_seconds=preparation_seconds or 1., **kwargs)
        self.preparation_seconds = float(preparation_seconds)
        self.preparation_steps = int(round(self.preparation_seconds*60))*4

    def reset(self):
        observation, info = super().reset()
        if self.preparation_seconds == 0.:
            info['preparation_mode'] = 'prepared_state_then_immediate_policy_handoff'
        return observation, info
