"""500-state, 39-channel transition specialists; inactive hand stays at zero."""
from guitar_learning.skills.specialist_policy import SpecialistPolicy as BaseSpecialist

INITIALIZATION = 'transition_selected_actor_std_only_fresh_critic_Adam'


class SpecialistPolicy(BaseSpecialist):
    schema = 'guitar_learning_transition39_v1'

    def __init__(self, state_dim=500, event_dim=24, size='medium', contract=None):
        config = (contract or {}).get('task', {}).get('transition', {})
        role = config.get('role')
        if (state_dim != 500 or event_dim != 24 or role not in ('left', 'joint')
                or config.get('schema') != 'guitar_learning.transition.v1'
                or (contract or {}).get('observation', {}).get('dimension') != 500):
            raise ValueError('explicit 500-state left/joint transition contract required')
        super().__init__(state_dim, event_dim, size, contract, role=role, frozen_partner=False)
        self.architecture['initialization'] = INITIALIZATION
        self.architecture['inactive_action'] = 'zero_residual_no_partner'

    def transfer_actor(self, *args, **kwargs):
        raise ValueError('transition initialization requires transition.transfer')
