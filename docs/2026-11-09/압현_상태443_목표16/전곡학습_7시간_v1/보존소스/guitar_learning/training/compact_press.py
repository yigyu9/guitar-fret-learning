"""상태443/452와 손가락별 목표8×16을 결합하는 독립 압현 정책.

기존 정책의 관측·가중치는 변환하지 않는다. 배우는 출력은 왼손33축이며,
공용 물리/PPO 전달 규격을 위해 오른손6축의 고정0을 뒤에 붙인다.
"""
import copy

import torch
from torch import nn

from guitar_learning.core.control import ACTIVE_NAMES
from guitar_learning.training.policy import FingerSkillPolicy, Policy


POLICY_SCHEMA = 'guitar_learning.compact_press_policy.v1'


def mlp(inputs, hidden, outputs):
    """각 층에 Tanh를 적용하는 고정 크기의 특징 인코더다."""
    return nn.Sequential(nn.Linear(inputs, hidden), nn.Tanh(),
                         nn.Linear(hidden, outputs), nn.Tanh())


class CompactEncoder(nn.Module):
    """목표 인코더 하나를8슬롯이 공유하며, 비어 있는 슬롯은 인코딩 후에도0이다."""
    def __init__(self, state_dim):
        super().__init__()
        self.state = mlp(state_dim, 256, 256)
        self.goal = mlp(16, 64, 64)
        self.fusion = mlp(768, 256, 256)

    def features(self, state, goals, mask):
        safe = torch.where(mask[..., None], goals, torch.zeros_like(goals))
        encoded = self.goal(safe)*mask[..., None]
        return torch.cat((self.state(state), encoded.flatten(1)), -1)

    def forward(self, state, goals, mask):
        return self.fusion(self.features(state, goals, mask))


class CompactPressPolicy(nn.Module):
    """별도 actor/critic 인코더와768특징 결합을 사용하는 J33 직접 목표각 정책."""
    schema = POLICY_SCHEMA
    phase = 'J'
    exploration = 'independent'

    def __init__(self, state_dim, event_dim=16, size='medium', contract=None):
        super().__init__()
        if size not in ('small', 'medium', 'large'):
            raise ValueError('small/medium/large 실행 설정 필요; compact 구조의 폭은 고정')
        if not isinstance(contract, dict):
            raise ValueError('compact 환경 계약 필요')
        observation = contract.get('observation', {})
        spec = contract.get('compact_press', {})
        fields, scales = observation.get('fields', []), observation.get('scales', [])
        include_pelvis = spec.get('include_pelvis')
        if (spec.get('schema') != 'guitar_learning.compact_press_observation.v1'
                or type(include_pelvis) is not bool
                or state_dim != (452 if include_pelvis else 443)
                or observation.get('dimension') != state_dim
                or event_dim != 16 or observation.get('event_dim') != 16
                or observation.get('priority_slots') != 8
                or len(fields) != state_dim or len(set(fields)) != state_dim
                or len(scales) != state_dim
                or contract.get('action', {}).get('names') != list(ACTIVE_NAMES)):
            raise ValueError('compact443/452 상태,16목표,8슬롯 계약 불일치')
        self.architecture = dict(schema=self.schema, state_dim=state_dim, event_dim=16,
            priority_slots=[finger+'_'+kind for finger in ('index', 'middle', 'ring', 'pinky')
                            for kind in ('tracking', 'next')],
            state_encoder=[256, 256], goal_encoder=[64, 64], fusion=[256, 256],
            fusion_input=768, learned_action_dim=33, transport_action_dim=39,
            attention=False, shared_goal_encoder=True, include_pelvis=include_pelvis,
            requested_size=size, contract=copy.deepcopy(contract))
        self.actor_encoder = CompactEncoder(state_dim)
        self.value_encoder = CompactEncoder(state_dim)
        self.actor_head = nn.Linear(256, 33)
        nn.init.zeros_(self.actor_head.weight)
        nn.init.zeros_(self.actor_head.bias)
        # 기존 J 정책의 초기 표준편차를 유지하며 탐색 방식은 바꾸지 않는다.
        self.log_std = nn.Parameter(torch.full((33,), -3.))
        self.reward_critic = nn.Linear(256, 1)
        self.cost_critic = nn.Linear(256, 1)

    _validate = Policy._validate
    act = FingerSkillPolicy.act
    evaluate = FingerSkillPolicy.evaluate
    log_probability = FingerSkillPolicy.log_probability
    analytic_kl = FingerSkillPolicy.analytic_kl

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
