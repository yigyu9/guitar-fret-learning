"""두 타현 목표를 공유 인코딩하고 오른손27축만 표본화하는 별도 정책."""
import copy
import math

import torch
from torch import nn

from guitar_learning.training.policy import CompactEncoder, mlp, Policy
from guitar_learning.tool.experiments.right27.control import ACTION_NAMES
from guitar_learning.tool.experiments.right27.policy import Right27Policy


POLICY_SCHEMA = 'guitar_learning.compact_strike_policy.v1'
OBSERVATION_SCHEMA = 'guitar_learning.compact_strike_observation.v1'


class CompactStrikeEncoder(CompactEncoder):
    """state256와 현재/다음 목표64씩을 결합하며 빈 목표는 정확히0이다."""
    def __init__(self, state_dim, event_dim, fusion_hidden=256):
        nn.Module.__init__(self)
        self.state = mlp(state_dim, 256, 256)
        self.goal = mlp(event_dim, 64, 64)
        self.fusion = mlp(384, fusion_hidden, 256)


class CompactStrikePolicy(nn.Module):
    schema = POLICY_SCHEMA
    role_sizes = (12, 27)

    def __init__(self, state_dim, event_dim=None, size='medium', contract=None, *,
                 role='right', frozen_partner=False):
        super().__init__()
        from guitar_learning.gpu.compact_strike import (STATE_DIM, GOAL_DIM, STATE_FIELDS,
            STATE_SCALES, GOAL_FIELDS, GOAL_SCALES)
        if role != 'right' or frozen_partner or size not in ('small', 'medium', 'large'):
            raise ValueError('Compact strike requires right27, no frozen partner and a recorded size')
        if not isinstance(contract, dict) or contract.get('schema') != 'guitar_learning.training.v1':
            raise ValueError('Explicit compact strike training contract required')
        observation, action = contract.get('observation', {}), contract.get('action', {})
        spec = contract.get('compact_strike', {})
        event_dim = observation.get('event_dim') if event_dim is None else event_dim
        fields, scales = observation.get('fields', []), observation.get('scales', [])
        if (spec.get('schema') != OBSERVATION_SCHEMA or type(state_dim) is not int or state_dim != STATE_DIM or
                type(event_dim) is not int or event_dim != GOAL_DIM or
                observation.get('dimension') != state_dim or observation.get('event_dim') != event_dim or
                observation.get('priority_slots') != 2 or len(fields) != state_dim or
                fields != list(STATE_FIELDS) or scales != list(STATE_SCALES) or
                observation.get('goal_fields') != list(GOAL_FIELDS) or
                observation.get('goal_scales') != list(GOAL_SCALES) or
                any(not isinstance(name, str) for name in fields) or len(set(fields)) != state_dim or
                len(scales) != state_dim or any(isinstance(value, bool) or not isinstance(value, (int, float)) or
                    not math.isfinite(value) or value <= 0 for value in scales) or
                action.get('dimension') != 39 or action.get('names') != list(ACTION_NAMES) or
                action.get('active_indices') != list(range(12, 39)) or
                action.get('inactive_indices') != list(range(12))):
            raise ValueError('Compact strike observation and right27 transport contract mismatch')
        self.architecture = dict(schema=self.schema, state_dim=state_dim, event_dim=event_dim,
            priority_slots=['current', 'next'], state_encoder=[256, 256], goal_encoder=[64, 64],
            fusion_input=384, fusion=[512, 256], value_fusion=[256, 256],
            learned_action_dim=27, transport_action_dim=39, attention=False,
            shared_goal_encoder=True, separate_actor_value_encoders=True,
            active_action_indices=list(range(12, 39)), inert_action_indices=list(range(12)),
            action_layout=dict(inert=[0, 12], right_hand21=[12, 33], right_elbow_wrist6=[33, 39]),
            requested_size=size, width_selection='fixed; requested_size does not change layer widths',
            distribution='tanh Gaussian over active27 only; inert latent/action/mean/log_std zero',
            contract=copy.deepcopy(contract))
        self.actor_encoder = CompactStrikeEncoder(state_dim, event_dim, fusion_hidden=512)
        self.value_encoder = CompactStrikeEncoder(state_dim, event_dim)
        self.actor_head = nn.Linear(256, 27)
        nn.init.zeros_(self.actor_head.weight)
        nn.init.zeros_(self.actor_head.bias)
        self.log_std = nn.Parameter(torch.full((27,), -3.))
        self.reward_critic = nn.Linear(256, 1)
        self.cost_critic = nn.Linear(256, 1)
        self.register_buffer('active_mask', torch.arange(39) >= 12)

    _active_mask = Right27Policy._active_mask
    act = Right27Policy.act
    evaluate = Right27Policy.evaluate
    log_probability = staticmethod(Right27Policy.log_probability)
    analytic_kl = staticmethod(Right27Policy.analytic_kl)

    def actor_parameters(self):
        return [*self.actor_encoder.parameters(), *self.actor_head.parameters(), self.log_std]

    def value_parameters(self):
        return [*self.value_encoder.parameters(), *self.reward_critic.parameters(),
                *self.cost_critic.parameters()]

    def forward(self, state, events, mask, priority_events, priority_mask):
        Policy._validate(self, state, events, mask, priority_events, priority_mask)
        if events.shape[1] != 0:
            raise ValueError('Compact strike uses exactly two priority goals and empty general events')
        actor = self.actor_encoder(state, priority_events, priority_mask)
        value = self.value_encoder(state, priority_events, priority_mask)
        active = self.actor_head(actor)
        inert = active.new_zeros((len(state), 12))
        return dict(mean=torch.cat((inert, active), -1),
            log_std=torch.cat((inert, self.log_std.clamp(-5, 2).expand_as(active)), -1),
            reward_value=self.reward_critic(value).squeeze(-1),
            cost_value=self.cost_critic(value).squeeze(-1))
