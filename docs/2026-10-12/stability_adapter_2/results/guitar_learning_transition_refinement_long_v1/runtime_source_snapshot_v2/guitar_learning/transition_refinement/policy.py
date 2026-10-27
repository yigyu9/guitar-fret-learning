"""Left-hand transition policy with explicitly bounded, small exploration.

The mean is an ordinary trainable actor. There is no frozen-prior mean bound.
Physical action limits and the original inactive-hand behavior are unchanged.
"""
from dataclasses import asdict, dataclass
import math

import torch

from ..transition.policy import SpecialistPolicy as TransitionPolicy


@dataclass(frozen=True)
class ExplorationConfig:
    min_std: float = 1e-4
    max_std: float = .05
    initial_std: float = .003

    def __post_init__(self):
        values = asdict(self).values()
        if (any(isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) for value in values)
                or not 0 < self.min_std <= self.initial_std <= self.max_std):
            raise ValueError('finite 0 < min_std <= initial_std <= max_std required')


class SpecialistPolicy(TransitionPolicy):
    schema = 'guitar_learning_transition_refinement39_v1'

    def __init__(self, state_dim=500, event_dim=24, size='medium', contract=None,
                 *, exploration=None):
        self.exploration = (ExplorationConfig(**exploration) if isinstance(exploration, dict)
                            else exploration or ExplorationConfig())
        if not isinstance(self.exploration, ExplorationConfig):
            raise ValueError('explicit ExplorationConfig or dictionary required')
        if (contract or {}).get('task', {}).get('transition', {}).get('role') != 'left':
            raise ValueError('refinement currently supports the left-hand stage only')
        super().__init__(state_dim, event_dim, size, contract)
        self.architecture['exploration'] = dict(
            schema='guitar_learning.transition_refinement_exploration.v1',
            **asdict(self.exploration), inactive_std_placeholder=-3.)
        self.architecture['mean_constraint'] = 'none_trainable_actor'
        self.architecture['initialization'] = 'validated_BC_selected_actor_only_new_exploration_fresh_critic_Adam'
        self.reset_exploration()

    def reset_exploration(self):
        """Explicitly initialize active exploration after selected-Actor migration."""
        with torch.no_grad():
            self.log_std[:33].fill_(math.log(self.exploration.initial_std))

    def forward(self, state, events, mask, priority_events, priority_mask):
        result = super().forward(state, events, mask, priority_events, priority_mask)
        lower, upper = math.log(self.exploration.min_std), math.log(self.exploration.max_std)
        result['log_std'] = torch.where(
            self._active_mask(), self.log_std.clamp(lower, upper),
            torch.full_like(self.log_std, -3.)).expand_as(result['mean'])
        return result
