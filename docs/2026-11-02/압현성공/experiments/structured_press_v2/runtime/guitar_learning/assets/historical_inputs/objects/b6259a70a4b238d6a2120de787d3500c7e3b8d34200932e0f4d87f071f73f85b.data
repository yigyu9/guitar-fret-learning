"""Fresh 54-action policy; deliberately has no legacy policy dependencies."""
import math

import torch
from torch import nn
from torch.distributions import Normal
import torch.nn.functional as F


class Policy(nn.Module):
    role_sizes = (15, 33, 6)

    def __init__(self, obs_dim, hidden_dim=128):
        super().__init__()
        self.obs_dim = int(obs_dim)
        self.hidden_dim = int(hidden_dim)
        self.encoder = nn.Sequential(nn.Linear(obs_dim, hidden_dim), nn.Tanh(),
                                     nn.Linear(hidden_dim, hidden_dim), nn.Tanh())
        self.actor_heads = nn.ModuleList(nn.Linear(hidden_dim, n) for n in self.role_sizes)
        for head in self.actor_heads:
            nn.init.zeros_(head.weight)
            nn.init.zeros_(head.bias)
        self.log_std = nn.Parameter(torch.full((54,), -1.0))
        self.reward_critic = nn.Linear(hidden_dim, 1)
        self.cost_critic = nn.Linear(hidden_dim, 1)

    def _distribution(self, obs):
        features = self.encoder(obs)
        mean = torch.cat([head(features) for head in self.actor_heads], dim=-1)
        return (Normal(mean, self.log_std.clamp(-5, 2).exp()),
                self.reward_critic(features).squeeze(-1),
                self.cost_critic(features).squeeze(-1))

    @staticmethod
    def _logp(distribution, latent):
        correction = 2 * (math.log(2) - latent - F.softplus(-2 * latent))
        return (distribution.log_prob(latent) - correction).sum(-1)

    def act(self, obs, deterministic=False):
        distribution, reward_value, cost_value = self._distribution(obs)
        latent = distribution.mean if deterministic else distribution.sample()
        return dict(action=latent.tanh(), latent=latent,
                    logp=self._logp(distribution, latent),
                    reward_value=reward_value, cost_value=cost_value)

    def evaluate(self, obs, latent):
        distribution, reward_value, cost_value = self._distribution(obs)
        return dict(logp=self._logp(distribution, latent),
                    entropy=distribution.entropy().sum(-1),
                    reward_value=reward_value, cost_value=cost_value)
