"""곡별 왼손 fret 정책용 MLP Actor + 6채널 Critic."""
from __future__ import annotations

import torch
from torch import nn
from torch.nn import functional as F


SQUASH_EPS = 1e-6
POLICY_DISTRIBUTION_VERSION = "tanh_squashed_masked_diagonal_gaussian.v2"


def _atanh_clamped(action):
    """Inverse tanh for an action that belongs to the closed policy interval."""
    return torch.atanh(action.clamp(-1.0 + SQUASH_EPS, 1.0 - SQUASH_EPS))


def _tanh_log_abs_det_jacobian(latent):
    """Stable ``log(1 - tanh(latent)^2)`` used by the bounded policy density."""
    return 2.0 * (torch.log(torch.as_tensor(
        2.0, dtype=latent.dtype, device=latent.device))
        - latent - F.softplus(-2.0 * latent))


class RunningMeanStd(nn.Module):
    def __init__(self, shape, eps=1e-4, clip=5.0):
        super().__init__()
        self.register_buffer("mean", torch.zeros(shape))
        self.register_buffer("var", torch.ones(shape))
        self.register_buffer("count", torch.tensor(float(eps)))
        self.clip = float(clip)

    @torch.no_grad()
    def update(self, x):
        x = x.reshape(-1, x.shape[-1])
        if x.numel() == 0:
            return
        if not torch.isfinite(x).all():
            raise FloatingPointError(
                "observation normalization received a non-finite sample")
        batch_mean = x.mean(0)
        batch_var = x.var(0, unbiased=False)
        batch_count = x.shape[0]
        delta = batch_mean - self.mean
        total = self.count + batch_count
        new_mean = self.mean + delta * batch_count / total
        m_a = self.var * self.count
        m_b = batch_var * batch_count
        m2 = m_a + m_b + delta.square() * self.count * batch_count / total
        self.mean.copy_(new_mean)
        self.var.copy_(m2 / total)
        self.count.copy_(total)

    def forward(self, x):
        return ((x - self.mean) / torch.sqrt(self.var + 1e-8)).clamp(-self.clip, self.clip)


def mlp(input_dim, hidden, output_dim, output_gain=1.0):
    layers = []
    last = input_dim
    for width in hidden:
        layer = nn.Linear(last, width)
        nn.init.orthogonal_(layer.weight, gain=2 ** 0.5)
        nn.init.zeros_(layer.bias)
        layers += [layer, nn.ELU()]
        last = width
    out = nn.Linear(last, output_dim)
    nn.init.orthogonal_(out.weight, gain=output_gain)
    nn.init.zeros_(out.bias)
    return nn.Sequential(*layers, out)


def configure_finger_flexion_policy(
        model, control_names, ctrl_mid, ctrl_half, action_scale,
        exploration_std, pip_degrees, dip_degrees, seed_mean=True,
        thumb_exploration_std=None,
        thumb_base_exploration_std=None,
        repair_saturated_thumb_base=False,
        thumb_base_action_limit=0.8):
    """손가락 탐색 floor와 선택적 기존 엄지 포화 복구를 적용한다."""
    names = [str(name) for name in control_names]
    if len(names) != model.action_dim:
        raise ValueError("control name count must match policy action dimension")
    ctrl_mid = torch.as_tensor(
        ctrl_mid, dtype=model.log_std.dtype, device=model.log_std.device).flatten()
    ctrl_half = torch.as_tensor(
        ctrl_half, dtype=model.log_std.dtype, device=model.log_std.device).flatten()
    if ctrl_mid.numel() != model.action_dim or ctrl_half.numel() != model.action_dim:
        raise ValueError("control bounds must match policy action dimension")
    action_scale = float(action_scale)
    exploration_std = float(exploration_std)
    if action_scale <= 0.0 or exploration_std <= 0.0:
        raise ValueError("action scale and flexion exploration std must be positive")

    fingers = ("index", "middle", "ring", "pinky")
    flexion_names = {
        name
        for finger in fingers
        for name in (f"LH:{finger}1_x", f"LH:{finger}2", f"LH:{finger}3")
    }
    flexion_indices = [
        index for index, name in enumerate(names) if name in flexion_names]
    if len(flexion_indices) != 12:
        raise ValueError(
            f"expected 12 MCP/PIP/DIP flexion actions, got {len(flexion_indices)}")
    thumb_base_indices = [
        index for index, name in enumerate(names)
        if name.startswith("LH:thumb1_")]

    with torch.no_grad():
        floor = model.log_std.new_tensor(exploration_std).log()
        model.log_std[flexion_indices] = torch.maximum(
            model.log_std[flexion_indices], floor)
        if thumb_exploration_std is not None:
            thumb_exploration_std = float(thumb_exploration_std)
            if (not torch.isfinite(
                    model.log_std.new_tensor(thumb_exploration_std))
                    or thumb_exploration_std <= 0.0):
                raise ValueError(
                    "thumb exploration std must be finite and positive")
            thumb_indices = [
                index for index, name in enumerate(names)
                if name.startswith("LH:thumb")]
            if not thumb_indices:
                raise ValueError("thumb exploration requested without thumb actions")
            thumb_floor = model.log_std.new_tensor(
                thumb_exploration_std).log()
            model.log_std[thumb_indices] = torch.maximum(
                model.log_std[thumb_indices], thumb_floor)
        if thumb_base_exploration_std is not None:
            thumb_base_exploration_std = float(
                thumb_base_exploration_std)
            if (not torch.isfinite(
                    model.log_std.new_tensor(
                        thumb_base_exploration_std))
                    or thumb_base_exploration_std <= 0.0):
                raise ValueError(
                    "thumb base exploration std must be finite and positive")
            if not thumb_base_indices:
                raise ValueError(
                    "thumb base exploration requested without "
                    "LH:thumb1_* actions")
            thumb_base_floor = model.log_std.new_tensor(
                thumb_base_exploration_std).log()
            model.log_std[thumb_base_indices] = torch.maximum(
                model.log_std[thumb_base_indices], thumb_base_floor)
        if seed_mean:
            output = model.actor[-1]
            for index, name in enumerate(names):
                if any(name == f"LH:{finger}2" for finger in fingers):
                    degrees = float(pip_degrees)
                elif any(name == f"LH:{finger}3" for finger in fingers):
                    degrees = float(dip_degrees)
                else:
                    continue
                desired = model.log_std.new_tensor(
                    degrees * torch.pi / 180.0)
                physical_action = (
                    (desired - ctrl_mid[index])
                    / (action_scale * ctrl_half[index]).clamp_min(1e-6)
                ).clamp(-0.999, 0.999)
                output.weight[index].zero_()
                output.bias[index] = torch.atanh(physical_action)
        if repair_saturated_thumb_base:
            limits = torch.as_tensor(
                thumb_base_action_limit,
                dtype=model.log_std.dtype,
                device=model.log_std.device,
            ).flatten()
            if limits.numel() == 1:
                limits = limits.repeat(len(thumb_base_indices))
            if limits.numel() != len(thumb_base_indices):
                raise ValueError(
                    "thumb base action limit must be a scalar or match "
                    "the LH:thumb1_* action count")
            if not torch.isfinite(limits).all():
                raise ValueError("thumb base action limits must be finite")
            if not ((limits > 0.0) & (limits < 1.0)).all():
                raise ValueError(
                    "thumb base action limits must be in (0, 1)")
            if not thumb_base_indices:
                raise ValueError(
                    "thumb base saturation repair requested without "
                    "LH:thumb1_* actions")
            output = model.actor[-1]
            neutral_input = output.weight.new_zeros(1, model.obs_dim)
            neutral_mean = model.actor(neutral_input)[0]
            neutral_action = torch.tanh(neutral_mean)
            if not torch.isfinite(
                    neutral_action[thumb_base_indices]).all():
                raise ValueError(
                    "thumb base mean action must be finite before repair")
            for index, limit in zip(thumb_base_indices, limits):
                action = neutral_action[index]
                if action.abs() <= limit:
                    continue
                target = action.sign() * limit
                output.bias[index] += (
                    _atanh_clamped(target) - neutral_mean[index])
    return flexion_indices


class ActorCritic(nn.Module):
    """단일프레임 MLP 정책과 줄별 value head.

    룩어헤드와 곡 진행률이 goal observation에 명시돼 있으므로 현재는 GRU를 쓰지 않는다.
    """

    POLICY_DISTRIBUTION_VERSION = POLICY_DISTRIBUTION_VERSION

    def __init__(self, obs_dim, action_dim, value_dim=6,
                 actor_hidden=(512, 256), critic_hidden=(512, 256), init_std=0.02,
                 init_mean=None):
        super().__init__()
        init_std = float(init_std)
        if not torch.isfinite(torch.tensor(init_std)) or init_std <= 0.0:
            raise ValueError("init_std must be finite and positive")
        self.obs_dim = int(obs_dim)
        self.action_dim = int(action_dim)
        self.value_dim = int(value_dim)
        self.obs_rms = RunningMeanStd(self.obs_dim)
        self.actor = mlp(self.obs_dim, actor_hidden, self.action_dim, output_gain=0.01)
        self.critic = mlp(self.obs_dim, critic_hidden, self.value_dim, output_gain=1.0)
        self.log_std = nn.Parameter(torch.full((self.action_dim,), init_std).log())
        if init_mean is not None:
            init_mean = torch.as_tensor(init_mean, dtype=self.actor[-1].bias.dtype)
            if init_mean.shape != self.actor[-1].bias.shape:
                raise ValueError(f"init_mean shape {init_mean.shape} != {(self.action_dim,)}")
            if not torch.isfinite(init_mean).all():
                raise ValueError("init_mean must be finite")
            with torch.no_grad():
                # The actor predicts an unconstrained latent mean.  The public
                # init_mean contract remains the physical action in [-1, 1].
                self.actor[-1].bias.copy_(_atanh_clamped(init_mean))

    def normalized(self, obs):
        return self.obs_rms(obs)

    def distribution(self, obs):
        """Return the latent Normal; executed actions are its tanh transform."""
        x = self.normalized(obs)
        mu = self.actor(x)
        std = self.log_std.clamp(-5.0, 1.0).exp().expand_as(mu)
        return torch.distributions.Normal(mu, std)

    @staticmethod
    def _masked_sum(value, action_mask):
        if action_mask is None:
            return value.sum(-1)
        action_mask = torch.as_tensor(
            action_mask, dtype=torch.bool, device=value.device)
        if action_mask.shape != value.shape:
            raise ValueError(
                f"action mask shape {action_mask.shape} != {value.shape}")
        if not action_mask.any(dim=-1).all():
            raise ValueError("every policy row must control at least one action")
        return value.masked_fill(~action_mask, 0.0).sum(-1)

    @classmethod
    def _squashed_log_prob(cls, dist, latent, action_mask=None):
        per_action = (
            dist.log_prob(latent)
            - _tanh_log_abs_det_jacobian(latent))
        return cls._masked_sum(per_action, action_mask)

    @torch.no_grad()
    def act(self, obs, deterministic=False, action_mask=None):
        dist = self.distribution(obs)
        latent = dist.mean if deterministic else dist.sample()
        action = torch.tanh(latent)
        log_prob = self._squashed_log_prob(
            dist, latent, action_mask=action_mask)
        value = self.critic(self.normalized(obs))
        return action, log_prob, value

    @torch.no_grad()
    def value(self, obs):
        return self.critic(self.normalized(obs))

    def evaluate_actions(
            self, obs, actions, action_mask=None,
            return_mean_action=False):
        dist = self.distribution(obs)
        latent = _atanh_clamped(actions)
        log_prob = self._squashed_log_prob(
            dist, latent, action_mask=action_mask)
        # H[tanh(Z)] = H[Z] + E[log |d tanh(Z)/dZ|].  One
        # reparameterized sample is sufficient for the small PPO entropy bonus.
        entropy_latent = dist.rsample()
        entropy = self._masked_sum(
            dist.entropy()
            + _tanh_log_abs_det_jacobian(entropy_latent),
            action_mask)
        value = self.critic(self.normalized(obs))
        if return_mean_action:
            return log_prob, entropy, value, torch.tanh(dist.mean)
        return log_prob, entropy, value
