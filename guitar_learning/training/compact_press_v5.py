"""회복 경계를 관측하고 역할별 초기 탐색을 명시하는 독립 압현 v5 정책."""
import copy
import math

import torch
from torch import nn

from guitar_learning.core.control import ACTIVE_NAMES
from guitar_learning.training.policy import CompactEncoder, mlp, Policy
from torch.distributions import Normal
import torch.nn.functional as F

POLICY_SCHEMA = 'guitar_learning.compact_press_policy.v5'
OBSERVATION_SCHEMA = 'guitar_learning.compact_press_observation.v5'


def initial_stds(support=.15, finger=.35):
    """tanh 이전 정규분포의 표준편차이며 support는 팔12축과 엄지5축이다."""
    for name, value in (('support', support), ('finger', finger)):
        if (isinstance(value, bool) or not isinstance(value, (int, float)) or
                not math.isfinite(value) or not math.exp(-5) <= value <= math.exp(2)):
            raise ValueError(name + ' 초기 std는 exp(-5)..exp(2)의 유한 수여야 함')
    return dict(support17=float(support), finger16=float(finger))


class CompactPressEncoder(CompactEncoder):
    """26필드 목표의 공유 인코더와 상태 결합 폭을 V5 규격으로 구성한다."""
    def __init__(self, state_dim, fusion_hidden=256):
        nn.Module.__init__(self)
        self.state = mlp(state_dim, 256, 256)
        self.goal = mlp(26, 64, 64)
        self.fusion = mlp(768, fusion_hidden, 256)


class CompactPressV5Policy(nn.Module):
    """v5 관측을 직접 검사하며 기존 인코더 폭·33축 우도·독립 가치망을 유지한다."""
    schema = POLICY_SCHEMA
    phase = 'J'
    exploration = 'independent'

    def __init__(self, state_dim, event_dim=26, size='medium', contract=None,
                 initial_support_std=.15, initial_finger_std=.35):
        nn.Module.__init__(self)
        std = initial_stds(initial_support_std, initial_finger_std)
        if size not in ('small', 'medium', 'large'):
            raise ValueError('지원하는 size 필요; 압현 v5의 신경망 폭은 고정')
        if not isinstance(contract, dict) or contract.get('schema') != 'guitar_learning.training.v1':
            raise ValueError('명시적 압현 v5 학습 계약 필요')
        if contract.get('reward', {}).get('schema') != 'guitar_learning.compact_press_reward.v5':
            raise ValueError('명시적 압현 v5 보상 계약 필요')
        observation = contract.get('observation', {})
        spec = contract.get('compact_press', {})
        fields, scales = observation.get('fields', []), observation.get('scales', [])
        pelvis = spec.get('include_pelvis')
        if (spec.get('schema') != OBSERVATION_SCHEMA or type(pelvis) is not bool or
                state_dim != (473 if pelvis else 464) or observation.get('dimension') != state_dim or
                event_dim != 26 or observation.get('event_dim') != 26 or
                observation.get('priority_slots') != 8 or len(fields) != state_dim or
                any(not isinstance(f, str) for f in fields) or len(set(fields)) != state_dim or
                len(scales) != state_dim or any(isinstance(s, bool) or not isinstance(s, (int, float)) or
                    not math.isfinite(s) or s <= 0 for s in scales) or
                contract.get('action', {}).get('names') != list(ACTIVE_NAMES)):
            raise ValueError('압현 v5 상태464/473·목표26·8슬롯 계약 불일치')
        self.architecture = dict(schema=self.schema, state_dim=state_dim, event_dim=26,
            priority_slots=[f + '_' + kind for f in ('index', 'middle', 'ring', 'pinky')
                            for kind in ('tracking', 'next')],
            state_encoder=[256, 256], goal_encoder=[64, 64], fusion=[512, 256],
            value_fusion=[256, 256], fusion_input=768, learned_action_dim=33, transport_action_dim=39,
            attention=False, shared_goal_encoder=True, include_pelvis=pelvis,
            requested_size=size, width_selection='fixed; requested_size does not change layer widths',
            initial_stds=std, contract=copy.deepcopy(contract))
        self.actor_encoder = CompactPressEncoder(state_dim, fusion_hidden=512)
        self.value_encoder = CompactPressEncoder(state_dim)
        self.actor_head = nn.Linear(256, 33)
        nn.init.zeros_(self.actor_head.weight)
        nn.init.zeros_(self.actor_head.bias)
        self.log_std = nn.Parameter(torch.cat((torch.full((17,), math.log(std['support17'])),
                                               torch.full((16,), math.log(std['finger16'])))))
        self.reward_critic = nn.Linear(256, 1)
        self.cost_critic = nn.Linear(256, 1)

    _validate = Policy._validate

    def _active_mask(self):
        return torch.arange(39, device=self.log_std.device) < 33

    @property
    def support_log_std(self):
        """공용 실행기의 탐색 초기화가17축 분산에 직접 반영되는 view다."""
        return self.log_std[:17]

    @property
    def finger_log_std(self):
        """검지~소지16축에 대한 공용 실행기 호환 view다."""
        return self.log_std[17:]

    def actor_parameters(self):
        return [*self.actor_encoder.parameters(), *self.actor_head.parameters(), self.log_std]

    def value_parameters(self):
        return [*self.value_encoder.parameters(), *self.reward_critic.parameters(),
                *self.cost_critic.parameters()]

    def forward(self, state, events, mask, priority_events, priority_mask):
        self._validate(state, events, mask, priority_events, priority_mask)
        # 일반 lookahead는 사용하지 않고, 명시적인 손가락별8슬롯만 인코딩한다.
        actor = self.actor_encoder(state, priority_events, priority_mask)
        mean = torch.cat((self.actor_head(actor), state.new_zeros(len(state), 6)), -1)
        std = torch.cat((self.log_std.clamp(-5, 2), self.log_std.new_full((6,), -3.)))
        value = self.value_encoder(state, priority_events, priority_mask)
        return dict(mean=mean, log_std=std.expand_as(mean),
                    reward_value=self.reward_critic(value).squeeze(-1),
                    cost_value=self.cost_critic(value).squeeze(-1))

    def log_probability(self, mean, log_std, latent):
        active = self._active_mask()
        bm, bz = mean[..., active], latent[..., active]
        correction = 2*(math.log(2)-latent[..., active]-F.softplus(-2*latent[..., active]))
        return (Normal(bm, log_std[..., active].exp()).log_prob(bz)-correction).sum(-1)

    def analytic_kl(self, old_mean, old_log_std, mean, log_std):
        active = self._active_mask()
        difference = (old_mean-mean)[..., active]
        previous_log_std, current_log_std = old_log_std[..., active], log_std[..., active]
        return (
            current_log_std-previous_log_std
            +(previous_log_std.mul(2).exp()+difference.square())/(2*current_log_std.mul(2).exp())
            -.5
        ).sum(-1)

    def act(self, state, events, mask, priority_events, priority_mask, deterministic=False):
        result = self(state, events, mask, priority_events, priority_mask)
        latent = result['mean'].clone()
        active = self._active_mask()
        if not deterministic:
            noise = torch.zeros_like(latent)
            noise[..., active] = Normal(torch.zeros_like(latent[..., active]),
                                         result['log_std'][..., active].exp()).sample()
            latent = latent+noise
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
