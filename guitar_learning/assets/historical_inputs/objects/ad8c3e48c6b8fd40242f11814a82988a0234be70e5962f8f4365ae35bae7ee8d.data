"""Block-encoded feed-forward actor/critic for Fret-v2."""
from __future__ import annotations

from collections import OrderedDict

import torch
from torch import nn

from .models import ActorCritic, _atanh_clamped, mlp
from ..fret_v2_contract import (
    FRET_V1_OBSERVATION_CONTRACT,
    FRET_V2_BLOCK_SIZES,
    FRET_V2_BLOCK_SLICES,
    FRET_V2_OBSERVATION_CONTRACT,
    FRET_V2_OBSERVATION_DIM,
)


FRET_V2_MODEL_ARCHITECTURE = "fret.block_encoder_mlp.v1"

FRET_V2_ENCODER_WIDTHS = OrderedDict((
    ("O_proprio", 96),
    ("O_arm_anchor", 48),
    ("O_hand_geometry", 96),
    ("O_current_event", 64),
    ("O_target_geometry", 48),
    ("O_finger_transition", 64),
    ("O_lookahead", 72),
    ("O_readiness_contact", 64),
    ("O_phase", 32),
    ("O_synchronizer", 8),
    ("O_history", 48),
))


class FretV2BlockNetwork(nn.Module):
    def __init__(self, output_dim: int, *, output_gain: float):
        super().__init__()
        if set(FRET_V2_ENCODER_WIDTHS) != set(FRET_V2_BLOCK_SIZES):
            raise RuntimeError("Fret-v2 encoder widths do not match ABI blocks")
        self.encoders = nn.ModuleDict({
            name: nn.Sequential(
                nn.Linear(size, FRET_V2_ENCODER_WIDTHS[name]), nn.ELU())
            for name, size in FRET_V2_BLOCK_SIZES.items()
        })
        for encoder in self.encoders.values():
            nn.init.orthogonal_(encoder[0].weight, gain=2 ** 0.5)
            nn.init.zeros_(encoder[0].bias)
        self.fusion = mlp(
            sum(FRET_V2_ENCODER_WIDTHS.values()), (512, 256),
            int(output_dim), output_gain=output_gain)

    @property
    def output_layer(self) -> nn.Linear:
        return self.fusion[-1]

    def __getitem__(self, index):
        if index == -1:
            return self.output_layer
        raise IndexError("FretV2BlockNetwork only exposes its final layer at -1")

    def forward(self, observation: torch.Tensor) -> torch.Tensor:
        if observation.ndim != 2 or observation.shape[1] != FRET_V2_OBSERVATION_DIM:
            raise ValueError("Fret-v2 network requires observations shaped [N,420]")
        encoded = [
            self.encoders[name](observation[:, FRET_V2_BLOCK_SLICES[name]])
            for name in FRET_V2_BLOCK_SIZES
        ]
        return self.fusion(torch.cat(encoded, dim=-1))


class FretV2ActorCritic(ActorCritic):
    MODEL_ARCHITECTURE_VERSION = FRET_V2_MODEL_ARCHITECTURE

    def __init__(self, obs_dim, action_dim, value_dim=6,
                 actor_hidden=(512, 256), critic_hidden=(512, 256),
                 init_std=0.02, init_mean=None):
        if int(obs_dim) != FRET_V2_OBSERVATION_DIM:
            raise ValueError("FretV2ActorCritic requires obs_dim=420")
        if int(action_dim) != 30:
            raise ValueError("FretV2ActorCritic requires action_dim=30")
        super().__init__(
            obs_dim, action_dim, value_dim=value_dim,
            actor_hidden=actor_hidden, critic_hidden=critic_hidden,
            init_std=init_std, init_mean=None)
        self.actor = FretV2BlockNetwork(action_dim, output_gain=0.01)
        self.critic = FretV2BlockNetwork(value_dim, output_gain=1.0)
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


def fret_actor_critic_class(observation_contract: str):
    if observation_contract == FRET_V1_OBSERVATION_CONTRACT:
        return ActorCritic
    if observation_contract == FRET_V2_OBSERVATION_CONTRACT:
        return FretV2ActorCritic
    raise ValueError(f"unsupported Fret observation contract: {observation_contract!r}")


__all__ = [
    "FRET_V2_ENCODER_WIDTHS",
    "FRET_V2_MODEL_ARCHITECTURE",
    "FretV2ActorCritic",
    "FretV2BlockNetwork",
    "fret_actor_critic_class",
]
