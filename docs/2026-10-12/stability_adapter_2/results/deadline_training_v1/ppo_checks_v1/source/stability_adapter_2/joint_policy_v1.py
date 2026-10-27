"""81-channel policy: absolute anchor codec and stable latent PPO likelihood."""
import hashlib
import json
import numpy as np
import torch
from tab2body.learning.models import ActorCritic


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


class AbsoluteTargetCodec:
    def __init__(self, contract, anchor):
        self.contract = contract
        self.anchor = np.asarray(anchor, dtype=float).copy()
        if self.anchor.shape != (81,) or not np.isfinite(self.anchor).all():
            raise ValueError('finite 81D anchor required')
        if np.any(self.anchor < contract.effective_lower) or np.any(self.anchor > contract.effective_upper):
            raise ValueError('anchor outside effective limits; no implicit repair')

    def requested(self, action):
        action = np.asarray(action, dtype=float)
        if action.shape != (81,) or not np.isfinite(action).all() or np.any(np.abs(action) > 1):
            raise ValueError('finite squashed action81 required')
        span = np.where(action >= 0, self.contract.effective_upper-self.anchor,
                        self.anchor-self.contract.effective_lower)
        return self.anchor + span*action

    def owner_action(self, action):
        requested = self.requested(action)
        # Roundoff only: owner uses its existing absolute mid/half codec.
        normalized = (requested-self.contract.mid)/self.contract.half
        if np.any(np.abs(normalized) > 1+1e-12):
            raise AssertionError('codec produced out-of-range target')
        return np.clip(normalized, -1., 1.)

    def manifest(self):
        return {'version': 'absolute_anchor_v1', 'joint_names': self.contract.names,
                'groups': self.contract.groups, 'anchor_rad': self.anchor.tolist(),
                'lower_rad': self.contract.effective_lower.tolist(),
                'upper_rad': self.contract.effective_upper.tolist(),
                'rates_rad_s': self.contract.rates.tolist(),
                'boundary_flat_channels': np.flatnonzero(
                    (self.anchor == self.contract.effective_lower) |
                    (self.anchor == self.contract.effective_upper)).tolist()}


class JointActorCritic(ActorCritic):
    def __init__(self, obs_dim, groups):
        if len(groups) != 81 or [groups.count(k) for k in ('body','head','arm','finger')] != [9,6,24,42]:
            raise ValueError('ordered upper81 groups required')
        super().__init__(obs_dim, 81, value_dim=1, actor_hidden=(512,256),
                         critic_hidden=(512,256))
        with torch.no_grad():
            self.actor[-1].weight.zero_()
            self.actor[-1].bias.zero_()
            self.log_std.copy_(torch.tensor([-5. if g in ('body','head') else -4. for g in groups]))

    @torch.no_grad()
    def sample(self, obs, deterministic=False):
        distribution = self.distribution(obs)
        latent = distribution.mean if deterministic else distribution.sample()
        return {'action': torch.tanh(latent), 'latent': latent,
                'log_prob': self._squashed_log_prob(distribution, latent),
                'value': self.value(obs).squeeze(-1)}

    def evaluate_latent(self, obs, latent):
        distribution = self.distribution(obs)
        log_prob = self._squashed_log_prob(distribution, latent)
        # Reparameterized transformed entropy; average per joint fixes the 81D scale.
        draw = distribution.rsample()
        entropy = -self._squashed_log_prob(distribution, draw)/81
        return log_prob, entropy, self.critic(self.normalized(obs)).squeeze(-1)
