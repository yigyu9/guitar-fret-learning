"""Restrict native commands to reset initialization and one target owner."""


class InitializationGuard:
    def __init__(self, gym, owner): self.gym, self.owner = gym, owner

    def __getattr__(self, name):
        if name in ('set_actor_dof_position_targets', 'set_actor_dof_properties'):
            def owned(*args, **kwargs):
                if self.owner.initialization_complete and (name == 'set_actor_dof_properties' or
                        not self.owner.target_submission_allowed):
                    self.owner.forbidden_calls.append(name)
                    raise RuntimeError('target/PD setter outside single-owner step: '+name)
                return getattr(self.gym, name)(*args, **kwargs)
            return owned
        if name.startswith(('apply_', 'set_')) and ('force' in name or 'effort' in name):
            def forbidden(*args, **kwargs):
                self.owner.forbidden_calls.append(name)
                raise RuntimeError('external force/effort prohibited: '+name)
            return forbidden
        if name.startswith('set_') and 'state' in name:
            def initialize(*args, **kwargs):
                if self.owner.initialization_complete:
                    self.owner.forbidden_calls.append(name)
                    raise RuntimeError('state writes only permitted inside reset initialization')
                self.owner.initial_state_write_calls.append(name)
                return getattr(self.gym, name)(*args, **kwargs)
            return initialize
        return getattr(self.gym, name)
