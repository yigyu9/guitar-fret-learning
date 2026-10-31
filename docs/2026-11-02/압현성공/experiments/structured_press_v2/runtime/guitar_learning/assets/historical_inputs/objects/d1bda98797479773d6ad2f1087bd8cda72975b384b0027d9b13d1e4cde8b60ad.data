"""Dual-critic PPO with a fixed, explicit pilot cost penalty."""
from dataclasses import asdict, dataclass
import os
from pathlib import Path
import random
import tempfile

import numpy as np
import torch


@dataclass(frozen=True)
class PPOConfig:
    learning_rate: float = 3e-4
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_ratio: float = 0.2
    cost_coefficient: float = 1.0
    value_coefficient: float = 0.5
    entropy_coefficient: float = 0.0
    max_grad_norm: float = 0.5
    epochs: int = 4
    minibatch_size: int = 256
    target_kl: float = 0.03


def compute_gae(reward, value, next_value, terminated, truncated, gamma, gae_lambda):
    """Next values must describe final observations, before any reset.

    Terminal transitions have zero bootstrap. Time limits bootstrap their final
    observation but do not propagate advantages from the following episode.
    """
    advantage = torch.zeros_like(reward)
    carry = torch.zeros_like(reward[0])
    for t in reversed(range(len(reward))):
        delta = reward[t] + gamma * (~terminated[t]).to(value.dtype) * next_value[t] - value[t]
        continuation = (~(terminated[t] | truncated[t])).to(value.dtype)
        carry = delta + gamma * gae_lambda * continuation * carry
        advantage[t] = carry
    return advantage, advantage + value


class PPOTrainer:
    schema = "fresh54_dualcritic_ppo_v1"

    def __init__(self, policy, config=None):
        self.policy = policy
        self.config = config or PPOConfig()
        if self.config.epochs < 1 or self.config.minibatch_size < 1:
            raise ValueError("epochs and minibatch_size must be positive")
        self.optimizer = torch.optim.Adam(policy.parameters(), lr=self.config.learning_rate)
        self.updates = 0

    def update(self, buffer):
        c = self.config
        b = {key: value.detach() for key, value in buffer.items()}
        ar, rr = compute_gae(b['reward'], b['reward_value'], b['next_reward_value'],
                             b['terminated'].bool(), b['truncated'].bool(), c.gamma, c.gae_lambda)
        ac, rc = compute_gae(b['cost'], b['cost_value'], b['next_cost_value'],
                             b['terminated'].bool(), b['truncated'].bool(), c.gamma, c.gae_lambda)
        advantage = (ar - c.cost_coefficient * ac).flatten()
        advantage = (advantage - advantage.mean()) / advantage.std(unbiased=False).clamp_min(1e-8)
        obs = b['obs'].reshape(-1, self.policy.obs_dim)
        latent = b['latent'].reshape(-1, 54)
        old_logp = b['logp'].flatten()
        rr, rc = rr.flatten(), rc.flatten()
        totals = dict(loss=0., policy_loss=0., reward_value_loss=0., cost_value_loss=0., grad_norm=0.)
        batches = 0
        for _ in range(c.epochs):
            order = torch.randperm(len(obs), device=obs.device)
            for index in order.split(c.minibatch_size):
                result = self.policy.evaluate(obs[index], latent[index])
                ratio = (result['logp'] - old_logp[index]).exp()
                actor_loss = -torch.minimum(ratio * advantage[index],
                    ratio.clamp(1-c.clip_ratio, 1+c.clip_ratio) * advantage[index]).mean()
                reward_loss = (result['reward_value'] - rr[index]).square().mean()
                cost_loss = (result['cost_value'] - rc[index]).square().mean()
                loss = actor_loss + c.value_coefficient * (reward_loss + cost_loss) - c.entropy_coefficient * result['entropy'].mean()
                if not torch.isfinite(loss):
                    raise FloatingPointError('nonfinite PPO loss')
                self.optimizer.zero_grad()
                loss.backward()
                grad_norm = torch.nn.utils.clip_grad_norm_(self.policy.parameters(), c.max_grad_norm, error_if_nonfinite=True)
                self.optimizer.step()
                if not all(torch.isfinite(parameter).all() for parameter in self.policy.parameters()):
                    raise FloatingPointError('nonfinite PPO parameters')
                for key, value in zip(totals, (loss, actor_loss, reward_loss, cost_loss, grad_norm)):
                    totals[key] += float(value.detach())
                batches += 1
            with torch.no_grad():
                log_ratio = self.policy.evaluate(obs, latent)['logp'] - old_logp
                approx_kl = float((log_ratio.exp() - 1 - log_ratio).mean())
                clip_fraction = float(((log_ratio.exp() - 1).abs() > c.clip_ratio).float().mean())
            if approx_kl > c.target_kl:
                break
        self.updates += 1
        metrics = {key: value / batches for key, value in totals.items()}
        metrics.update(approx_kl=approx_kl, clip_fraction=clip_fraction)
        return metrics

    def _identity(self):
        return dict(schema=self.schema, obs_dim=self.policy.obs_dim,
                    hidden_dim=self.policy.hidden_dim, role_sizes=self.policy.role_sizes,
                    config=asdict(self.config))

    def save(self, path, metadata=None):
        """Publish atomically without replacing any existing checkpoint."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = dict(identity=self._identity(), model=self.policy.state_dict(),
            optimizer=self.optimizer.state_dict(), updates=self.updates, metadata=metadata,
            torch_rng=torch.get_rng_state(), numpy_rng=np.random.get_state(),
            python_rng=random.getstate(),
            cuda_rng=torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None)
        descriptor, temporary = tempfile.mkstemp(prefix='checkpoint-', suffix='.pt', dir=str(path.parent))
        os.close(descriptor)
        try:
            torch.save(payload, temporary)
            os.link(temporary, path)
        finally:
            os.unlink(temporary)

    def load(self, path):
        # Checkpoints are trusted local artifacts, never legacy policy weights.
        payload = torch.load(path, map_location=next(self.policy.parameters()).device, weights_only=False)
        if not isinstance(payload, dict) or payload.get('identity') != self._identity():
            raise ValueError('checkpoint schema, architecture, or PPO config mismatch')
        cuda_rng = payload['cuda_rng']
        if cuda_rng is not None and (not torch.cuda.is_available() or len(cuda_rng) != torch.cuda.device_count()):
            raise ValueError('CUDA RNG topology mismatch')
        self.policy.load_state_dict(payload['model'], strict=True)
        self.optimizer.load_state_dict(payload['optimizer'])
        self.updates = payload['updates']
        torch.set_rng_state(payload['torch_rng'].cpu())
        np.random.set_state(payload['numpy_rng'])
        random.setstate(payload['python_rng'])
        if cuda_rng is not None:
            torch.cuda.set_rng_state_all([state.cpu() for state in cuda_rng])
        return payload['metadata']
