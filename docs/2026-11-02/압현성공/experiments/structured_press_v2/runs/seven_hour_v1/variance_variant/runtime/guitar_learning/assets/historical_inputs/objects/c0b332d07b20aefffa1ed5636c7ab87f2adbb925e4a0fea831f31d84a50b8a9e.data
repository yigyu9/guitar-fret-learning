"""Block-encoded feed-forward actor/critic for Strike-v2."""
from __future__ import annotations

from collections import OrderedDict

import torch
from torch import nn

from .models import ActorCritic, _atanh_clamped, mlp
from ..strike_v2_contract import (
    STRIKE_V1_OBSERVATION_CONTRACT,
    STRIKE_V2_BLOCK_SIZES,
    STRIKE_V2_BLOCK_SLICES,
    STRIKE_V2_OBSERVATION_CONTRACT,
    STRIKE_V2_OBSERVATION_DIM,
)


STRIKE_V2_MODEL_ARCHITECTURE = "strike.block_encoder_mlp.v1"

STRIKE_V2_ENCODER_WIDTHS = OrderedDict((
    ("O_proprio", 96),
    ("O_arm_anchor", 48),
    ("O_hand_geometry", 64),
    ("O_grip_safety", 16),
    ("O_current_event", 64),
    ("O_target_geometry", 48),
    ("O_lookahead", 64),
    ("O_phase_detector", 48),
    ("O_recovery", 48),
    ("O_synchronizer", 8),
    ("O_history", 48),
))


class StrikeV2BlockNetwork(nn.Module):
    """Encode named semantic groups independently, then fuse them with an MLP."""

    def __init__(self, output_dim: int, *, output_gain: float):
        super().__init__()
        if set(STRIKE_V2_ENCODER_WIDTHS) != set(STRIKE_V2_BLOCK_SIZES):
            raise RuntimeError("Strike-v2 encoder widths do not match ABI blocks")
        self.encoders = nn.ModuleDict({
            name: nn.Sequential(
                nn.Linear(size, STRIKE_V2_ENCODER_WIDTHS[name]),
                nn.ELU(),
            )
            for name, size in STRIKE_V2_BLOCK_SIZES.items()
        })
        for encoder in self.encoders.values():
            nn.init.orthogonal_(encoder[0].weight, gain=2 ** 0.5)
            nn.init.zeros_(encoder[0].bias)
        fusion_dim = sum(STRIKE_V2_ENCODER_WIDTHS.values())
        self.fusion = mlp(
            fusion_dim, (512, 256), int(output_dim), output_gain=output_gain)

    @property
    def output_layer(self) -> nn.Linear:
        return self.fusion[-1]

    def __getitem__(self, index):
        # Compatibility with narrow initialization/audit utilities that expect
        # the final output layer at actor[-1].
        if index == -1:
            return self.output_layer
        raise IndexError("StrikeV2BlockNetwork only exposes its final layer at -1")

    def forward(self, observation: torch.Tensor) -> torch.Tensor:
        if observation.ndim != 2 \
                or observation.shape[1] != STRIKE_V2_OBSERVATION_DIM:
            raise ValueError(
                "Strike-v2 network requires observations shaped [N,303]")
        encoded = [
            self.encoders[name](observation[:, STRIKE_V2_BLOCK_SLICES[name]])
            for name in STRIKE_V2_BLOCK_SIZES
        ]
        return self.fusion(torch.cat(encoded, dim=-1))


class StrikeV2ActorCritic(ActorCritic):
    """PPO-compatible Strike actor/critic with semantic block encoders."""

    MODEL_ARCHITECTURE_VERSION = STRIKE_V2_MODEL_ARCHITECTURE

    def __init__(self, obs_dim, action_dim, value_dim=1,
                 actor_hidden=(512, 256), critic_hidden=(512, 256),
                 init_std=0.02, init_mean=None):
        if int(obs_dim) != STRIKE_V2_OBSERVATION_DIM:
            raise ValueError("StrikeV2ActorCritic requires obs_dim=303")
        if int(action_dim) != 30 or int(value_dim) != 1:
            raise ValueError(
                "StrikeV2ActorCritic requires action_dim=30 and value_dim=1")
        # ActorCritic owns the tested bounded Gaussian, RMS and PPO API.  Its
        # temporary monolithic networks are replaced immediately below.
        super().__init__(
            obs_dim, action_dim, value_dim=value_dim,
            actor_hidden=actor_hidden, critic_hidden=critic_hidden,
            init_std=init_std, init_mean=None)
        self.actor = StrikeV2BlockNetwork(action_dim, output_gain=0.01)
        self.critic = StrikeV2BlockNetwork(value_dim, output_gain=1.0)
        if init_mean is not None:
            initial = torch.as_tensor(
                init_mean, dtype=self.actor.output_layer.bias.dtype)
            if initial.shape != self.actor.output_layer.bias.shape:
                raise ValueError(
                    f"init_mean shape {tuple(initial.shape)} != "
                    f"{tuple(self.actor.output_layer.bias.shape)}")
            if not torch.isfinite(initial).all():
                raise ValueError("init_mean must be finite")
            with torch.no_grad():
                self.actor.output_layer.bias.copy_(_atanh_clamped(initial))


def strike_actor_critic_class(observation_contract: str):
    """Resolve the policy class for an explicit observation ABI."""
    if observation_contract == STRIKE_V1_OBSERVATION_CONTRACT:
        return ActorCritic
    if observation_contract == STRIKE_V2_OBSERVATION_CONTRACT:
        return StrikeV2ActorCritic
    raise ValueError(f"unsupported Strike observation contract: {observation_contract!r}")


__all__ = [
    "STRIKE_V2_ENCODER_WIDTHS",
    "STRIKE_V2_MODEL_ARCHITECTURE",
    "StrikeV2ActorCritic",
    "StrikeV2BlockNetwork",
    "strike_actor_critic_class",
]
