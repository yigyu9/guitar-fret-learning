"""Independent hand actors with one central reward/cost value network.

The collector keeps its 39-channel action contract. Only the selected actor's
channels participate in PPO likelihood, entropy and exploration. A partner is
either the zero residual target or an explicitly imported deterministic actor.
"""
import copy
import math
from pathlib import Path

import torch
from torch import nn
from torch.distributions import Normal
import torch.nn.functional as F

from guitar_learning.training.policy import Encoder, Policy


class SpecialistPolicy(nn.Module):
    role_sizes = (33, 6)
    role_slices = {'left': slice(0, 33), 'right': slice(33, 39)}
    schema = 'guitar_specialists39_v1'

    def __init__(self, state_dim, event_dim=24, size='medium', contract=None,
                 role='left', frozen_partner=False):
        super().__init__()
        if min(state_dim, event_dim) < 1 or event_dim != 24:
            raise ValueError('positive explicit dimensions and event_dim=24 required')
        sizes = dict(small=(256, 256, 256), medium=(512, 512, 256), large=(1024, 1024, 512))
        if size not in sizes or role not in ('left', 'right', 'joint'):
            raise ValueError('small/medium/large size and left/right/joint role required')
        if not isinstance(frozen_partner, bool) or (role == 'joint' and frozen_partner):
            raise ValueError('frozen partner is only available for single-hand stages')
        if not isinstance(contract, dict) or contract.get('schema') != 'guitar_learning.training.v1' or any(
                not isinstance(contract.get(key), dict)
                for key in ('observation', 'action', 'task', 'reward', 'termination')):
            raise ValueError('explicit training observation/action/task/reward/termination contract required')
        fusion = sizes[size]
        self.role = role
        self.frozen_partner = frozen_partner
        self.trainable_roles = ('left', 'right') if role == 'joint' else (role,)
        self.architecture = dict(schema=self.schema, state_dim=state_dim, event_dim=event_dim,
                                 size=size, state_layers=(256, 256), event_layers=(128, 128),
                                 fusion=fusion, normalization='fixed_observation_scaling_no_running_updates',
                                 roles=self.role_sizes, priority_slots=('current', 'nearest_strict_deadline'),
                                 role=role, frozen_partner=frozen_partner,
                                 likelihood='trainable_channels_only_v1',
                                 inactive_action='deterministic_partner_or_zero_residual',
                                 contract=copy.deepcopy(contract))
        self.actor_encoders = nn.ModuleDict({name: Encoder(state_dim, event_dim, fusion)
                                            for name in self.role_slices})
        self.actor_heads = nn.ModuleDict({name: nn.Linear(fusion[-1], count)
                                         for name, count in zip(self.role_slices, self.role_sizes)})
        for name, head in self.actor_heads.items():
            nn.init.zeros_(head.weight)
            nn.init.zeros_(head.bias)
            if name not in self.trainable_roles:
                self.actor_encoders[name].requires_grad_(False)
                head.requires_grad_(False)
        self.value_encoder = Encoder(state_dim, event_dim, fusion)
        self.reward_critic = nn.Linear(fusion[-1], 1)
        self.cost_critic = nn.Linear(fusion[-1], 1)
        self.log_std = nn.Parameter(torch.full((39,), -3.))
        # This is checkpoint state: resuming a frozen partner must retain the
        # fact that a complete actor was imported, not silently use zero heads.
        self.register_buffer('partner_initialized', torch.zeros(2, dtype=torch.bool))

    def actor_parameters(self):
        parameters = []
        for name in self.trainable_roles:
            parameters.extend(self.actor_encoders[name].parameters())
            parameters.extend(self.actor_heads[name].parameters())
        return [*parameters, self.log_std]

    def value_parameters(self):
        return [*self.value_encoder.parameters(), *self.reward_critic.parameters(), *self.cost_critic.parameters()]

    _validate = Policy._validate

    def _active_mask(self):
        if self.role == 'joint':
            return torch.ones(39, dtype=torch.bool, device=self.log_std.device)
        mask = torch.zeros(39, dtype=torch.bool, device=self.log_std.device)
        mask[self.role_slices[self.role]] = True
        return mask

    def forward(self, state, events, mask, priority_events, priority_mask):
        self._validate(state, events, mask, priority_events, priority_mask)
        inputs = (state, events, mask, priority_events, priority_mask)
        means = []
        for index, name in enumerate(self.role_slices):
            if name in self.trainable_roles:
                means.append(self.actor_heads[name](self.actor_encoders[name](*inputs)))
            elif self.frozen_partner:
                if not bool(self.partner_initialized[index]):
                    raise ValueError('frozen partner requires a transferred actor or strict checkpoint resume')
                with torch.no_grad():
                    means.append(self.actor_heads[name](self.actor_encoders[name](*inputs)))
            else:
                means.append(state.new_zeros((state.shape[0], self.role_sizes[index])))
        mean = torch.cat(means, -1)
        # Fixed placeholders make the existing 39D analytic KL exactly zero on
        # inactive channels. They are not distributions sampled for those joints.
        log_std = torch.where(self._active_mask(), self.log_std.clamp(-5, 2),
                              torch.full_like(self.log_std, -3.)).expand_as(mean)
        value = self.value_encoder(*inputs)
        return dict(mean=mean, log_std=log_std,
                    reward_value=self.reward_critic(value).squeeze(-1),
                    cost_value=self.cost_critic(value).squeeze(-1))

    def log_probability(self, mean, log_std, latent):
        active = self._active_mask()
        mean, log_std, latent = mean[..., active], log_std[..., active], latent[..., active]
        correction = 2 * (math.log(2) - latent - F.softplus(-2 * latent))
        return (Normal(mean, log_std.exp()).log_prob(latent) - correction).sum(-1)

    def act(self, state, events, mask, priority_events, priority_mask, deterministic=False):
        result = self(state, events, mask, priority_events, priority_mask)
        latent = result['mean'].clone()
        active = self._active_mask()
        if not deterministic:
            latent[..., active] = Normal(result['mean'][..., active], result['log_std'][..., active].exp()).sample()
        result.update(action=latent.tanh(), latent=latent,
                      logp=self.log_probability(result['mean'], result['log_std'], latent))
        return result

    def evaluate(self, state, events, mask, priority_events, priority_mask, latent):
        if latent.shape != (state.shape[0], 39) or not torch.isfinite(latent).all():
            raise ValueError('finite latent[B,39] required')
        result = self(state, events, mask, priority_events, priority_mask)
        active = self._active_mask()
        result.update(logp=self.log_probability(result['mean'], result['log_std'], latent),
                      entropy=Normal(result['mean'][..., active], result['log_std'][..., active].exp()).entropy().sum(-1))
        return result

    def transfer_actor(self, checkpoint, role):
        """Warm-start a full specialist actor; never import critic/optimizer/RNG.

        Task stage metadata belongs under task.specialist. All other task,
        observation, action and termination semantics must match exactly. The
        source must have completed an update of the requested single-hand stage.
        """
        if role not in self.role_slices:
            raise ValueError('left/right source role required')
        payload = (torch.load(Path(checkpoint), map_location='cpu', weights_only=False)
                   if isinstance(checkpoint, (str, Path)) else checkpoint)
        if not isinstance(payload, dict):
            raise ValueError('PPO specialist checkpoint dictionary required')
        identity = payload.get('identity', {})
        if not isinstance(identity, dict):
            raise ValueError('own PPO checkpoint identity required')
        source = identity.get('architecture', {})
        if identity.get('schema') != 'guitar_learning_ppo_v1' or not isinstance(identity.get('config'), dict):
            raise ValueError('own PPO checkpoint identity required')
        if not isinstance(source, dict) or source.get('schema') != self.schema or source.get('role') != role:
            raise ValueError('requested single-hand specialist source required; shared/joint actors cannot be spliced')
        updates = payload.get('updates')
        if isinstance(updates, bool) or not isinstance(updates, int) or updates < 1:
            raise ValueError('source specialist must have completed a PPO update')
        for key in ('state_dim', 'event_dim', 'size', 'state_layers', 'event_layers', 'fusion',
                    'normalization', 'roles', 'priority_slots', 'likelihood', 'inactive_action'):
            if source.get(key) != self.architecture[key]:
                raise ValueError('source specialist architecture mismatch: ' + key)
        source_contract = source.get('contract', {})
        target_contract = self.architecture['contract']
        if not isinstance(source_contract, dict) or any(
                not isinstance(source_contract.get(key), dict)
                for key in ('observation', 'action', 'task', 'reward', 'termination')):
            raise ValueError('source specialist training contract required')
        for key in ('schema', 'observation', 'action', 'termination'):
            if source_contract.get(key) != target_contract[key]:
                raise ValueError('source specialist contract mismatch: ' + key)
        source_task = copy.deepcopy(source_contract.get('task', {}))
        target_task = copy.deepcopy(target_contract['task'])
        source_task.pop('specialist', None)
        target_task.pop('specialist', None)
        if source_task != target_task:
            raise ValueError('source specialist task mismatch')
        model = payload.get('model')
        expected = self.state_dict()
        if not isinstance(model, dict) or model.keys() != expected.keys() or any(
                not isinstance(value, torch.Tensor) or value.shape != expected[key].shape
                or value.dtype != expected[key].dtype or not torch.isfinite(value).all()
                for key, value in model.items()):
            raise ValueError('source specialist finite model/shape/dtype mismatch')
        # Validation is complete before mutating any target tensor.
        with torch.no_grad():
            for prefix in ('actor_encoders.' + role + '.', 'actor_heads.' + role + '.'):
                for key, value in model.items():
                    if key.startswith(prefix):
                        expected[key].copy_(value)
            selection = self.role_slices[role]
            self.log_std[selection].copy_(model['log_std'][selection])
            self.partner_initialized[tuple(self.role_slices).index(role)] = True
        return dict(role=role, source_updates=updates, source_architecture=copy.deepcopy(source),
                    source_config=copy.deepcopy(identity['config']), source_metadata=copy.deepcopy(payload.get('metadata')))
