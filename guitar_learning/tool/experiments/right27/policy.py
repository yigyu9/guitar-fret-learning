"""기존 39칸 PPO 버퍼에서 오른손21축과 오른팔6축만 학습하는 정책이다.

앞12칸은 운반용 빈칸이며 행동·logp·entropy·KL에 참여하지 않는다.
기존 관측 인코더와 가치망을 재사용하고, 다른 행동 배치의 체크포인트는 거부한다.
"""
import torch
from torch import nn
from torch.distributions import Normal
from guitar_learning.training.policy import Policy


class Right27Policy(Policy):
    role_sizes = (12, 27)
    schema = 'guitar_attention_right27_v1'

    def __init__(self, state_dim, event_dim=24, size='medium', contract=None, *,
                 role='right', frozen_partner=False):
        if role != 'right' or frozen_partner:
            raise ValueError('오른손 전용·동결 파트너 없는 정책만 지원한다')
        super().__init__(state_dim, event_dim, size, contract)
        # 실제 확률 변수는 오른손27개뿐이다. 빈칸용 actor head는 학습하지 않는다.
        self.actor_heads[0].requires_grad_(False)
        self.log_std = nn.Parameter(torch.full((27,), -3.))
        self.register_buffer('active_mask', torch.arange(39) >= 12)
        self.architecture.update(schema=self.schema, role='right', frozen_partner=False,
            active_action_indices=list(range(12,39)), inert_action_indices=list(range(12)),
            action_layout=dict(inert=[0,12], right_hand21=[12,33], right_elbow_wrist6=[33,39]),
            distribution='tanh Gaussian over active27 only; inert latent/action/mean/log_std zero')

    def _active_mask(self):
        """공용 PPO 진단도 확률을 갖는27칸만 집계하게 한다."""
        return self.active_mask

    def actor_parameters(self):
        return [*self.actor_encoder.parameters(), *self.actor_heads[1].parameters(), self.log_std]

    def forward(self, state, events, mask, priority_events, priority_mask):
        self._validate(state, events, mask, priority_events, priority_mask)
        actor = self.actor_encoder(state, events, mask, priority_events, priority_mask)
        value = self.value_encoder(state, events, mask, priority_events, priority_mask)
        active_mean = self.actor_heads[1](actor)
        inert = active_mean.new_zeros((state.shape[0],12))
        mean = torch.cat((inert, active_mean), -1)
        log_std = torch.cat((inert, self.log_std.clamp(-5,2).expand_as(active_mean)), -1)
        return dict(mean=mean, log_std=log_std,
            reward_value=self.reward_critic(value).squeeze(-1),
            cost_value=self.cost_critic(value).squeeze(-1))

    @staticmethod
    def log_probability(mean, log_std, latent):
        return Policy.log_probability(mean[...,12:], log_std[...,12:], latent[...,12:])

    @staticmethod
    def analytic_kl(old_mean, old_log_std, mean, log_std):
        """결정 PPO용 표본별 KL이며 빈칸 값이 바뀌어도 영향을 받지 않는다."""
        old_mean, old_log_std, mean, log_std = (v[...,12:] for v in (old_mean,old_log_std,mean,log_std))
        return (log_std-old_log_std+(old_log_std.mul(2).exp()+(old_mean-mean).square())/
            (2*log_std.mul(2).exp())-.5).sum(-1)

    def act(self, state, events, mask, priority_events, priority_mask, deterministic=False):
        result = self(state, events, mask, priority_events, priority_mask)
        mean, log_std = result['mean'][...,12:], result['log_std'][...,12:]
        active = mean if deterministic else Normal(mean, log_std.exp()).sample()
        latent = torch.cat((active.new_zeros((state.shape[0],12)), active), -1)
        result.update(action=latent.tanh(), latent=latent,
            logp=self.log_probability(result['mean'],result['log_std'],latent))
        return result

    def evaluate(self, state, events, mask, priority_events, priority_mask, latent):
        if latent.shape != (state.shape[0],39) or not torch.isfinite(latent).all():
            raise ValueError('유한 latent[B,39]가 필요하다')
        result = self(state, events, mask, priority_events, priority_mask)
        result.update(logp=self.log_probability(result['mean'],result['log_std'],latent),
            entropy=Normal(result['mean'][...,12:],result['log_std'][...,12:].exp()).entropy().sum(-1))
        return result
