"""Phase-specific support/finger actors and full-rank finger exploration.

Means are physical-joint latents. In correlated mode only the three flexion
standard deviations per finger live in an orthogonal bend/difference basis.
"""
import copy
import math

import torch
from torch import nn
from torch.distributions import Normal
import torch.nn.functional as F

from guitar_learning.core.control import ACTIVE_NAMES
from guitar_learning.training.policy import Encoder, Policy


FINGERS = ('index', 'middle', 'ring', 'pinky')
PHASE_FIELDS = ('finger_skill.phase_R', 'finger_skill.phase_F', 'finger_skill.phase_J',
                'finger_skill.planned_ticks', 'finger_skill.remaining_s')
WRIST_TERMINATION_FIELDS = ('wrist_termination.active', 'wrist_termination.elapsed_s',
                           'wrist_termination.preparation_remaining_s',
                           'wrist_termination.severe_elapsed_s')


class FingerSkillPolicy(nn.Module):
    schema = 'guitar_learning.finger_skill_policy.v1'

    def __init__(self, state_dim, event_dim=24, size='medium', contract=None,
                 phase='F', exploration='independent'):
        super().__init__()
        sizes = dict(small=(256, 256, 256), medium=(512, 512, 256), large=(1024, 1024, 512))
        if size not in sizes or phase not in ('R', 'F', 'J') or exploration not in ('independent', 'correlated'):
            raise ValueError('explicit size, R/F/J phase and independent/correlated exploration required')
        if event_dim != 24 or not isinstance(contract, dict) or contract.get('schema') != 'guitar_learning.training.v1':
            raise ValueError('explicit training contract and 24 event columns required')
        if any(not isinstance(contract.get(key), dict) for key in
               ('observation', 'action', 'task', 'reward', 'termination', 'native_backend')):
            raise ValueError('complete GPU training contract required')
        observation = contract['observation']
        fields = observation.get('fields')
        spec = contract['task'].get('finger_skill', {})
        simplified = isinstance(spec, dict) and spec.get('schema') == 'guitar_learning.finger_skill.v2'
        tail = PHASE_FIELDS+WRIST_TERMINATION_FIELDS if simplified else PHASE_FIELDS
        if simplified and (state_dim != 561 or phase != 'J' or exploration != 'independent'):
            raise ValueError('Simplified finger skill requires561 states, joint learning and independent exploration')
        slots = [finger+'_'+kind for finger in FINGERS for kind in ('tracking', 'next')]
        if (not isinstance(fields, list) or len(fields) != state_dim or
                any(not isinstance(field, str) for field in fields) or len(set(fields)) != state_dim or
                observation.get('dimension') != state_dim or tuple(fields[-len(tail):]) != tail or
                observation.get('priority_slots') != 8 or
                observation.get('finger_targets', {}).get('slots') != slots or
                observation.get('finger_targets', {}).get('schema') != 'guitar_learning.left_finger_targets.v1' or
                contract['action'].get('names') != list(ACTIVE_NAMES) or
                contract['native_backend'].get('pipeline') != 'gpu' or
                not isinstance(spec, dict) or spec.get('schema') not in (
                    'guitar_learning.finger_skill.v1', 'guitar_learning.finger_skill.v2') or
                spec.get('phase') != phase or spec.get('exploration') != exploration):
            raise ValueError('named finger-skill state, exact action order, GPU, phase and exploration contract required')
        local_fields = {}
        for finger in FINGERS:
            joints = ['LH:'+finger+suffix for suffix in ('1_x', '1_z', '2', '3')]
            local_fields[finger] = [block+'.'+joint for block in ('q_offset', 'q_velocity', 'target_error') for joint in joints]
            local_fields[finger] += ['finger_posture.'+finger+'.'+joint+'.'+trig
                                    for joint in ('MCP', 'PIP', 'DIP') for trig in ('sin', 'cos')]
            local_fields[finger] += ['finger_posture.'+finger+'.'+name for name in ('valid', 'standby_gate')]
        required = [name for names in local_fields.values() for name in names]
        required += [block+'.'+joint for block in ('q_offset', 'q_velocity', 'target_error', 'previous_action')
                     for joint in ACTIVE_NAMES[:17]]
        if any(name not in fields for name in required):
            raise ValueError('named support and local finger fields missing')

        # Explicit allowlist: no nonthumb state, pad errors, score outcomes or
        # phase/duration inputs can make a frozen support actor chase fingers.
        support_fields = [block+'.'+joint for block in ('q_offset', 'q_velocity', 'target_error', 'previous_action')
                          for joint in ACTIVE_NAMES[:17]]
        support_fields += [field for field in fields if field.startswith((
            'guitar_in_pelvis.', 'guitar_reset_delta.', 'feet_reset_delta.',
            'L_Wrist_in_guitar.', 'LH:thumb3_in_guitar.', 'thumb_support.',
            'contact_loss_s.', 'wrist_region.delta_')) or field in (
                'contact.chest', 'contact.right_upper_arm', 'contact.right_thigh',
                'contact.thumb', 'contact.left_foot', 'contact.right_foot')]
        if simplified:
            support_fields += list(WRIST_TERMINATION_FIELDS)
        self.phase, self.exploration = phase, exploration
        self.architecture = dict(schema=self.schema, state_dim=state_dim, event_dim=event_dim,
            size=size, fusion=sizes[size], priority_slots=tuple(slots), phase=phase,
            exploration=exploration, normalization='fixed_observation_scaling_no_running_updates',
            support_fields=support_fields, support_event_columns=tuple(range(9)),
            local_fields=local_fields,
            local_indices={finger: [fields.index(field) for field in names] for finger, names in local_fields.items()},
            likelihood='phase_active_physical_tanh_latent_with_orthogonal_basis_std_v1',
            contract=copy.deepcopy(contract))
        self.register_buffer('support_indices', torch.tensor([fields.index(field) for field in support_fields]))
        self.register_buffer('support_event_columns', torch.tensor(list(range(9))))
        basis = torch.tensor([[1/math.sqrt(3), 1/math.sqrt(2), 1/math.sqrt(6)],
                              [1/math.sqrt(3), -1/math.sqrt(2), 1/math.sqrt(6)],
                              [1/math.sqrt(3), 0., -2/math.sqrt(6)]])
        self.register_buffer('bend_basis', basis)
        self.register_buffer('bend_indices', torch.tensor([[17+4*i, 19+4*i, 20+4*i] for i in range(4)]))
        fusion = sizes[size]
        self.support_encoder = Encoder(len(support_fields), 9, fusion, priority_count=8)
        self.support_head = nn.Linear(fusion[-1], 17)
        self.finger_encoder = Encoder(state_dim, event_dim, fusion, priority_count=8)
        self.finger_heads = nn.ModuleDict({finger: nn.Sequential(
            nn.Linear(fusion[-1]+256+20, 128), nn.Tanh(), nn.Linear(128, 4)) for finger in FINGERS})
        for head in (self.support_head, *(head[-1] for head in self.finger_heads.values())):
            nn.init.zeros_(head.weight)
            nn.init.zeros_(head.bias)
        self.support_log_std = nn.Parameter(torch.full((17,), -3.))
        self.finger_log_std = nn.Parameter(torch.full((16,), -3.))
        if exploration == 'correlated':
            with torch.no_grad():
                self.finger_log_std[[0, 2, 3, 4, 6, 7, 8, 10, 11, 12, 14, 15]] += torch.tensor(
                    [math.log(2)/2, -math.log(2)/2, -math.log(2)/2]*4)
        self.value_encoder = Encoder(state_dim, event_dim, fusion, priority_count=8)
        self.reward_critic = nn.Linear(fusion[-1], 1)
        self.cost_critic = nn.Linear(fusion[-1], 1)
        for module in (self.support_encoder, self.support_head):
            module.requires_grad_(phase != 'F')
        self.support_log_std.requires_grad_(phase != 'F')
        for module in (self.finger_encoder, self.finger_heads):
            module.requires_grad_(phase != 'R')
        self.finger_log_std.requires_grad_(phase != 'R')

    _validate = Policy._validate

    def actor_parameters(self):
        groups = (self.support_encoder, self.support_head, self.finger_encoder, self.finger_heads)
        return [parameter for group in groups for parameter in group.parameters() if parameter.requires_grad] + [
            parameter for parameter in (self.support_log_std, self.finger_log_std) if parameter.requires_grad]

    def value_parameters(self):
        return [*self.value_encoder.parameters(), *self.reward_critic.parameters(), *self.cost_critic.parameters()]

    def _active_mask(self):
        mask = torch.zeros(39, dtype=torch.bool, device=self.support_log_std.device)
        if self.phase != 'F': mask[:17] = True
        if self.phase != 'R': mask[17:33] = True
        return mask

    def _to_basis(self, latent):
        if self.exploration == 'independent':
            return latent
        result = latent.clone()
        result[..., self.bend_indices] = latent[..., self.bend_indices] @ self.bend_basis.to(latent)
        return result

    def _from_basis(self, latent):
        if self.exploration == 'independent':
            return latent
        result = latent.clone()
        result[..., self.bend_indices] = latent[..., self.bend_indices] @ self.bend_basis.to(latent).T
        return result

    def forward(self, state, events, mask, priority_events, priority_mask):
        self._validate(state, events, mask, priority_events, priority_mask)
        support = self.support_encoder(state[:, self.support_indices],
            events[..., self.support_event_columns], mask,
            priority_events[..., self.support_event_columns], priority_mask)
        support_mean = self.support_head(support)
        if self.phase == 'R':
            finger_mean = state.new_zeros((state.shape[0], 16))
        else:
            context = self.finger_encoder(state, events, mask, priority_events, priority_mask)
            tokens = self.finger_encoder.event(torch.where(priority_mask[..., None], priority_events,
                                                           torch.zeros_like(priority_events)))
            tokens = tokens * priority_mask[..., None]
            finger_mean = torch.cat([self.finger_heads[finger](torch.cat((context,
                tokens[:, 2*i:2*i+2].flatten(1), state[:, self.architecture['local_indices'][finger]]), -1))
                for i, finger in enumerate(FINGERS)], -1)
        mean = torch.cat((support_mean, finger_mean, state.new_zeros((state.shape[0], 6))), -1)
        std = torch.cat((self.support_log_std, self.finger_log_std, self.support_log_std.new_full((6,), -3.))).clamp(-5, 2)
        log_std = torch.where(self._active_mask(), std, std.new_full((39,), -3.)).expand_as(mean)
        value = self.value_encoder(state, events, mask, priority_events, priority_mask)
        return dict(mean=mean, log_std=log_std, reward_value=self.reward_critic(value).squeeze(-1),
                    cost_value=self.cost_critic(value).squeeze(-1))

    def log_probability(self, mean, log_std, latent):
        active = self._active_mask()
        bm, bz = self._to_basis(mean)[..., active], self._to_basis(latent)[..., active]
        correction = 2*(math.log(2)-latent[..., active]-F.softplus(-2*latent[..., active]))
        return (Normal(bm, log_std[..., active].exp()).log_prob(bz)-correction).sum(-1)

    def analytic_kl(self, old_mean, old_log_std, mean, log_std):
        active = self._active_mask()
        difference = (self._to_basis(old_mean)-self._to_basis(mean))[..., active]
        old_std, std = old_log_std[..., active], log_std[..., active]
        return (std-old_std+(old_std.mul(2).exp()+difference.square())/(2*std.mul(2).exp())-.5).sum(-1)

    def act(self, state, events, mask, priority_events, priority_mask, deterministic=False):
        result = self(state, events, mask, priority_events, priority_mask)
        latent = result['mean'].clone()
        active = self._active_mask()
        if not deterministic:
            noise = torch.zeros_like(latent)
            noise[..., active] = Normal(torch.zeros_like(latent[..., active]),
                                         result['log_std'][..., active].exp()).sample()
            latent = latent+self._from_basis(noise)
        result.update(action=latent.tanh(), latent=latent,
                      logp=self.log_probability(result['mean'], result['log_std'], latent))
        return result

    def evaluate(self, state, events, mask, priority_events, priority_mask, latent):
        if latent.shape != (state.shape[0], 39) or not torch.isfinite(latent).all():
            raise ValueError('finite latent[B,39] required')
        result = self(state, events, mask, priority_events, priority_mask)
        active = self._active_mask()
        result.update(logp=self.log_probability(result['mean'], result['log_std'], latent),
                      entropy=Normal(torch.zeros_like(result['mean'][..., active]),
                                     result['log_std'][..., active].exp()).entropy().sum(-1))
        return result

    def transfer_from(self, other):
        """Explicit phase transfer: actor weights only, with no optimizer/value state.

        Exploration changes require a separate experiment and are rejected here:
        copying basis standard deviations as physical ones changes covariance.
        """
        if not isinstance(other, FingerSkillPolicy):
            raise ValueError('finger-skill actor source required; legacy checkpoints are incompatible')
        for key in ('state_dim', 'event_dim', 'size', 'exploration', 'support_fields', 'local_fields'):
            if self.architecture[key] != other.architecture[key]:
                raise ValueError('actor transfer architecture mismatch: '+key)
        target, source = self.architecture['contract'], other.architecture['contract']
        for key in ('observation', 'action', 'native_backend', 'termination'):
            if target[key] != source[key]:
                raise ValueError('actor transfer physics/control/base observation mismatch: '+key)
        keys = [key for key in self.state_dict() if key.startswith((
            'support_encoder.', 'support_head.', 'finger_encoder.', 'finger_heads.')) or
            key in ('support_log_std', 'finger_log_std')]
        source_state, target_state = other.state_dict(), self.state_dict()
        if any(not torch.isfinite(source_state[key]).all() for key in keys):
            raise ValueError('nonfinite actor transfer source')
        with torch.no_grad():
            for key in keys:
                target_state[key].copy_(source_state[key])
        return dict(schema='guitar_learning.finger_skill_phase_transfer.v1',
                    source_phase=other.phase, target_phase=self.phase, copied=keys,
                    critics='not_transferred', optimizers='not_transferred')
