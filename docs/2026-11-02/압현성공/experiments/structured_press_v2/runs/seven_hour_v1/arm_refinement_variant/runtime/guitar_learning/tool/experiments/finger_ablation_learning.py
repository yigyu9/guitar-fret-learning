"""통제 실험 전용 정책·최적화기: 기본 경로를 유지하며 선택한 요인만 바꾼다."""
import copy
import math

import torch

from guitar_learning.training.policy import FingerSkillPolicy
from guitar_learning.training.ppo import DecisionPPOTrainer


FACTORS = ('adaptive_lr', 'exploration', 'preparation', 'geometry', 'separate')


def validate_research_config(value=None):
    """다섯 실험 요인을 생략 없이 기록해 체크포인트 간 혼용을 막는다."""
    if value is None:
        value = dict.fromkeys(FACTORS, False)
    if not isinstance(value, dict) or set(value) != set(FACTORS) or any(
            type(flag) is not bool for flag in value.values()):
        raise ValueError('research_config requires exactly five boolean factors')
    return copy.deepcopy(value)


class LearningPolicy(FingerSkillPolicy):
    """탐색 실험만 비엄지16축의 초기 표준편차와 분포 하한을 확대한다."""
    def __init__(self, state_dim, event_dim=24, size='medium', contract=None,
                 research_config=None):
        self.research_config = validate_research_config(research_config)
        super().__init__(state_dim, event_dim=event_dim, size=size, contract=contract)
        self.architecture['research_config'] = copy.deepcopy(self.research_config)
        if self.research_config['exploration']:
            with torch.no_grad():
                self.finger_log_std.fill_(math.log(.10))

    def forward(self, *inputs):
        result = super().forward(*inputs)
        if self.research_config['exploration']:
            # 실제 표본화·확률·KL·entropy가 같은 하한 적용 분포를 사용한다.
            log_std = result['log_std']
            result['log_std'] = torch.cat((log_std[:, :17],
                log_std[:, 17:33].clamp_min(math.log(.07)), log_std[:, 33:]), -1)
        return result


class LearningTrainer(DecisionPPOTrainer):
    """KL 안전 검사를 유지한 채 재시도 감소 폭과 안정 시 회복만 비교한다."""
    def __init__(self, policy, config=None, research_config=None):
        self.research_config = validate_research_config(research_config)
        if getattr(policy, 'research_config', self.research_config) != self.research_config:
            raise ValueError('policy and trainer research_config mismatch')
        super().__init__(policy, config)
        if self.research_config['adaptive_lr']:
            if self.config.actor_lr != 3e-5 or self.config.target_kl != .02:
                raise ValueError('adaptive experiment requires actor_lr=3e-5 and target_kl=.02')
            # Adam 상태와 함께 저장·복원되므로 실패한 갱신과 재개 시에도 횟수가 보존된다.
            self.actor_optimizer.param_groups[0]['research_stable_updates'] = 0

    def _identity(self):
        result = super()._identity()
        result['research_config'] = copy.deepcopy(self.research_config)
        return result

    def _retry_actor_lr(self, retry):
        if not self.research_config['adaptive_lr']:
            return super()._retry_actor_lr(retry)
        # 각 재시도 전 동일한 snapshot이 복원된다. 지수는 연속 시도마다 절반을 뜻한다.
        for group in self.actor_optimizer.param_groups:
            group['lr'] = max(3e-6, group['lr'] * .5**(retry+1))

    def _update(self, buffer, completed_episodes):
        result = super()._update(buffer, completed_episodes)
        if not self.research_config['adaptive_lr']:
            return result
        group = self.actor_optimizer.param_groups[0]
        before = group['lr']
        stable = (result['kl_retries'] == 0 and math.isfinite(result['analytic_kl'])
                  and result['analytic_kl'] < .005)
        count = group['research_stable_updates'] + 1 if stable else 0
        recovered = count >= 10
        if recovered:
            for item in self.actor_optimizer.param_groups:
                item['lr'] = min(3e-5, item['lr'] * 1.2)
            count = 0
        group['research_stable_updates'] = count
        result['actor_lr'] = group['lr']
        result['diagnostics']['research_learning_rate'] = dict(
            lr_before_recovery=before, lr_after_recovery=group['lr'],
            stable_updates=count, stable_this_update=stable,
            recovered=recovered and group['lr'] > before,
            reason='ten_stable_updates' if recovered else ('stable' if stable else 'reset'))
        return result
