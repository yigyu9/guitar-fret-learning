"""연주 목표 없이 상태를 받아 전신37축을 제어하는 독립 Actor–Critic.

기존 PPO의39칸 전달 규격을 유지하되 뒤2칸은 행동·확률·KL에 참여하지 않는다.
실제 제어용 actor_action()은 가치망 계산 없이37축만 반환한다.
"""
import copy
import math

import torch
from torch import nn
from torch.distributions import Normal

from guitar_learning.gpu.whole_body import STATE_DIM, STATE_FIELDS, STATE_SCALES
from guitar_learning.gpu.whole_body_control import ACTION_NAMES
from guitar_learning.training.policy import mlp
from guitar_learning.training.policy import Policy


POLICY_SCHEMA = 'guitar_learning.whole_body_policy.v1'
OBSERVATION_SCHEMA = 'guitar_learning.whole_body_observation.v1'
REWARD_SCHEMA = 'guitar_learning.whole_body_reward.v1'
ACTION_DIM = 37
TRANSPORT_DIM = 39


class WholeBodyEncoder(nn.Module):
    """상태 인코더 뒤에 행동 또는 가치 추정용 특징망을 둔다."""
    def __init__(self, state_dim, fusion_hidden):
        super().__init__()
        self.state = mlp(state_dim, 256, 256)
        self.fusion = mlp(256, fusion_hidden, 256)

    def forward(self, state):
        return self.fusion(self.state(state))


class WholeBodyPolicy(nn.Module):
    schema = POLICY_SCHEMA
    role_sizes = (ACTION_DIM, TRANSPORT_DIM-ACTION_DIM)

    def __init__(self, state_dim=STATE_DIM, contract=None):
        super().__init__()
        if (not isinstance(contract, dict) or
                contract.get('schema') != 'guitar_learning.training.v1' or
                any(not isinstance(contract.get(key), dict)
                    for key in ('observation', 'action', 'reward'))):
            raise ValueError('Explicit whole-body training contract required')
        observation, action, reward = (contract[key] for key in ('observation', 'action', 'reward'))
        if (type(state_dim) is not int or state_dim != STATE_DIM or
                observation.get('schema') != OBSERVATION_SCHEMA or
                type(observation.get('dimension')) is not int or
                observation.get('dimension') != STATE_DIM or
                observation.get('fields') != list(STATE_FIELDS) or
                observation.get('scales') != list(STATE_SCALES) or
                any(type(value) not in (int, float) or not math.isfinite(value) or value <= 0
                    for value in observation['scales']) or
                type(observation.get('event_dim')) is not int or observation['event_dim'] != 0 or
                type(observation.get('priority_slots')) is not int or observation['priority_slots'] != 0 or
                type(action.get('dimension')) is not int or
                action.get('dimension') != ACTION_DIM or len(ACTION_NAMES) != ACTION_DIM or
                action.get('names') != list(ACTION_NAMES) or reward.get('schema') != REWARD_SCHEMA):
            raise ValueError('Whole-body state-only484, physical37 and reward contract mismatch')
        self.architecture = dict(
            schema=self.schema, state_dim=state_dim, event_dim=0, priority_slots=[],
            state_encoder=[256, 256], fusion_input=256, fusion=[512, 256],
            value_fusion=[256, 256], goal_encoder=None, attention=False,
            separate_actor_value_encoders=True, learned_action_dim=ACTION_DIM,
            transport_action_dim=TRANSPORT_DIM, active_action_indices=list(range(ACTION_DIM)),
            inert_action_indices=list(range(ACTION_DIM, TRANSPORT_DIM)),
            distribution='tanh Gaussian over active37 only; inert latent/action/mean/log_std zero',
            contract=copy.deepcopy(contract),
        )
        self.actor_encoder = WholeBodyEncoder(state_dim, 512)
        self.value_encoder = WholeBodyEncoder(state_dim, 256)
        self.actor_head = nn.Linear(256, ACTION_DIM)
        nn.init.zeros_(self.actor_head.weight)
        nn.init.zeros_(self.actor_head.bias)
        self.log_std = nn.Parameter(torch.full((ACTION_DIM,), -3.))
        self.reward_critic = nn.Linear(256, 1)
        self.cost_critic = nn.Linear(256, 1)
        self.register_buffer('active_mask', torch.arange(TRANSPORT_DIM) < ACTION_DIM)

    def actor_parameters(self):
        return [*self.actor_encoder.parameters(), *self.actor_head.parameters(), self.log_std]

    def value_parameters(self):
        return [*self.value_encoder.parameters(), *self.reward_critic.parameters(),
                *self.cost_critic.parameters()]

    def _active_mask(self):
        return self.active_mask

    def _validate_state(self, state):
        if (state.ndim != 2 or state.shape[1] != STATE_DIM or not state.is_floating_point() or
                not torch.isfinite(state).all()):
            raise ValueError('Finite floating-point state[B,484] required')

    def _validate(self, state, events, mask, priority_events, priority_mask):
        self._validate_state(state)
        batch = len(state)
        if (events.shape != (batch, 0, 0) or priority_events.shape != (batch, 0, 0) or
                mask.shape != (batch, 0) or priority_mask.shape != (batch, 0) or
                mask.dtype != torch.bool or priority_mask.dtype != torch.bool):
            raise ValueError('Whole-body policy requires empty goal tensors[B,0,0] and bool masks[B,0]')

    def _actor_distribution(self, state):
        mean = self.actor_head(self.actor_encoder(state))
        return mean, self.log_std.clamp(-5, 2).expand_as(mean)

    def actor_action(self, state, deterministic=True):
        """상태만 사용하는 추론 경로. 가치망을 호출하지 않고 실제37축을 반환한다."""
        self._validate_state(state)
        mean, log_std = self._actor_distribution(state)
        latent = mean if deterministic else Normal(mean, log_std.exp()).sample()
        return latent.tanh()

    def forward(self, state, events, mask, priority_events, priority_mask):
        self._validate(state, events, mask, priority_events, priority_mask)
        mean, log_std = self._actor_distribution(state)
        inert = mean.new_zeros((len(state), TRANSPORT_DIM-ACTION_DIM))
        value = self.value_encoder(state)
        return dict(mean=torch.cat((mean, inert), -1), log_std=torch.cat((log_std, inert), -1),
            reward_value=self.reward_critic(value).squeeze(-1),
            cost_value=self.cost_critic(value).squeeze(-1))

    @staticmethod
    def log_probability(mean, log_std, latent):
        return Policy.log_probability(mean[..., :ACTION_DIM], log_std[..., :ACTION_DIM],
                                      latent[..., :ACTION_DIM])

    @staticmethod
    def analytic_kl(old_mean, old_log_std, mean, log_std):
        old_mean, old_log_std, mean, log_std = (
            value[..., :ACTION_DIM] for value in (old_mean, old_log_std, mean, log_std))
        return (log_std-old_log_std+(old_log_std.mul(2).exp()+(old_mean-mean).square()) /
                (2*log_std.mul(2).exp())-.5).sum(-1)

    def act(self, state, events, mask, priority_events, priority_mask, deterministic=False):
        result = self(state, events, mask, priority_events, priority_mask)
        mean, log_std = result['mean'][..., :ACTION_DIM], result['log_std'][..., :ACTION_DIM]
        active = mean if deterministic else Normal(mean, log_std.exp()).sample()
        latent = torch.cat((active, active.new_zeros((len(state), TRANSPORT_DIM-ACTION_DIM))), -1)
        result.update(action=latent.tanh(), latent=latent,
            logp=self.log_probability(result['mean'], result['log_std'], latent))
        return result

    def evaluate(self, state, events, mask, priority_events, priority_mask, latent):
        if latent.shape != (len(state), TRANSPORT_DIM) or not torch.isfinite(latent).all():
            raise ValueError('Finite transport latent[B,39] required for active37 policy')
        result = self(state, events, mask, priority_events, priority_mask)
        result.update(logp=self.log_probability(result['mean'], result['log_std'], latent),
            entropy=Normal(result['mean'][..., :ACTION_DIM],
                           result['log_std'][..., :ACTION_DIM].exp()).entropy().sum(-1))
        return result
