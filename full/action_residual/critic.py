"""Central multi-head critic for Action Residual PPO training."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Optional

import torch
from torch import nn

from .config import ActionResidualConfig
from .checkpoint_utils import validate_finite_state_dict
from .context_encoding import (
    GUITAR_SUPPORT_MANIFEST,
    PRIVILEGED_MANIFEST,
    READINESS_MANIFEST,
)
from .goal_encoder import GoalScoreBatch, GoalScoreEncoder
from .manifest import ActionResidualManifest
from .source_adapter import SourceProposal
from .source_intent import SourceIntentCalibration, SourceIntentNormalizer


DEFAULT_VALUE_HEAD_NAMES = (
    "fret_high_e",
    "fret_B",
    "fret_G",
    "fret_D",
    "fret_A",
    "fret_low_E",
    "strike",
    "joint_event_sync",
    "guitar_pose_twist",
    "support_slip_force",
    "assist_recovery_safety",
)


def _encoder(input_dim: int, hidden_dim: int, output_dim: int) -> nn.Sequential:
    module = nn.Sequential(
        nn.Linear(input_dim, hidden_dim),
        nn.ELU(),
        nn.Linear(hidden_dim, output_dim),
        nn.ELU(),
    )
    for layer in module.modules():
        if isinstance(layer, nn.Linear):
            nn.init.orthogonal_(layer.weight, gain=2 ** 0.5)
            nn.init.zeros_(layer.bias)
    return module


@dataclass(frozen=True)
class CentralCriticConfig:
    """Dimensions that are private to the centralized training critic."""

    privileged_context_dim: int = 128
    privileged_feature_dim: int = 64
    hidden_dims: tuple[int, int] = (512, 256)
    value_head_names: tuple[str, ...] = DEFAULT_VALUE_HEAD_NAMES

    def __post_init__(self) -> None:
        for name in ("privileged_context_dim", "privileged_feature_dim"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if (len(self.hidden_dims) != 2
                or any(isinstance(value, bool)
                       or not isinstance(value, int)
                       or value <= 0 for value in self.hidden_dims)):
            raise ValueError("hidden_dims must contain two positive integers")
        names = tuple(str(name) for name in self.value_head_names)
        if not names or any(not name for name in names):
            raise ValueError("value_head_names must be non-empty")
        if len(set(names)) != len(names):
            raise ValueError("value_head_names must be unique")
        object.__setattr__(self, "value_head_names", names)


class CentralMultiHeadCritic(nn.Module):
    """Value estimator that may use training-only physical information.

    The actor never receives ``privileged_context``.  It is reserved for values
    such as exact tether wrench, randomized mass/inertia, and simulator-only
    contact attribution.  This keeps deployment observations honest while PPO
    can still estimate the eleven separately-auditable reward channels.
    """

    def __init__(
            self, manifest: ActionResidualManifest,
            actor_config: Optional[ActionResidualConfig] = None,
            critic_config: Optional[CentralCriticConfig] = None,
            source_intent_calibration: Optional[
                SourceIntentCalibration] = None) -> None:
        super().__init__()
        self.manifest = manifest
        self.actor_config = actor_config or ActionResidualConfig()
        self.config = critic_config or CentralCriticConfig()
        self.manifest.validate_current_75d_profile(
            self.actor_config.joint_context_dim)

        source_dim = manifest.fret_action_dim + manifest.strike_action_dim
        self.source_intent_normalizer = SourceIntentNormalizer(
            manifest, source_intent_calibration)
        # Separate parameters are intentional: privileged critic training must
        # not mutate the actor's categorical score representation.
        self.goal_score_encoder = GoalScoreEncoder()
        self.action_encoder = _encoder(
            source_dim,
            self.actor_config.small_encoder_hidden_dim,
            self.actor_config.action_feature_dim)
        self.goal_encoder = _encoder(
            self.actor_config.goal_context_dim,
            self.actor_config.small_encoder_hidden_dim,
            self.actor_config.goal_feature_dim)
        self.readiness_encoder = _encoder(
            self.actor_config.readiness_context_dim,
            self.actor_config.small_encoder_hidden_dim,
            self.actor_config.readiness_feature_dim)
        self.joint_encoder = _encoder(
            self.actor_config.joint_context_dim,
            self.actor_config.joint_encoder_hidden_dim,
            self.actor_config.joint_feature_dim)
        self.guitar_encoder = _encoder(
            self.actor_config.guitar_context_dim,
            self.actor_config.small_encoder_hidden_dim,
            self.actor_config.guitar_feature_dim)
        self.privileged_encoder = _encoder(
            self.config.privileged_context_dim,
            self.actor_config.small_encoder_hidden_dim,
            self.config.privileged_feature_dim)

        first, second = self.config.hidden_dims
        input_dim = (
            self.actor_config.fusion_input_dim
            + self.config.privileged_feature_dim)
        self.value_network = nn.Sequential(
            nn.Linear(input_dim, first),
            nn.ELU(),
            nn.Linear(first, second),
            nn.ELU(),
            nn.Linear(second, len(self.config.value_head_names)),
        )
        for layer in self.value_network.modules():
            if isinstance(layer, nn.Linear):
                gain = 1.0 if layer is self.value_network[-1] else 2 ** 0.5
                nn.init.orthogonal_(layer.weight, gain=gain)
                nn.init.zeros_(layer.bias)

    @property
    def value_dim(self) -> int:
        return len(self.config.value_head_names)

    def _apply(self, fn, recurse: bool = True):
        reference = next(self.parameters(), None)
        if reference is not None:
            probe = torch.empty(
                0, dtype=torch.float32, device=reference.device)
            if fn(probe).dtype != torch.float32:
                raise TypeError(
                    "Action Residual critic must remain torch.float32")
        return super()._apply(fn, recurse=recurse)

    @staticmethod
    def _require_matrix(
            name: str, value: torch.Tensor, batch: int, width: int) -> None:
        if value.ndim != 2 or value.shape != (batch, width):
            raise ValueError(
                f"{name} must have shape {(batch, width)}, got "
                f"{tuple(value.shape)}")
        if not torch.isfinite(value).all():
            raise ValueError(f"{name} must be finite")
        if value.dtype != torch.float32:
            raise TypeError(f"{name} must use torch.float32")

    def _validate_source_proposal(
            self, label: str, proposal: SourceProposal,
            expected_names: tuple[str, ...], expected_sha256: str) -> None:
        if not isinstance(proposal, SourceProposal):
            raise TypeError(f"{label}_proposal must be a SourceProposal")
        if proposal.action_names != expected_names:
            raise ValueError(
                f"{label} source action names/order do not match the manifest")
        if proposal.checkpoint_sha256 != expected_sha256:
            raise ValueError(
                f"{label} source checkpoint SHA-256 does not match the manifest")

    def forward(
            self, *, fret_proposal: SourceProposal,
            strike_proposal: SourceProposal,
            goal_context: torch.Tensor, readiness_context: torch.Tensor,
            joint_context: torch.Tensor, guitar_context: torch.Tensor,
            privileged_context: torch.Tensor) -> torch.Tensor:
        self._validate_source_proposal(
            "fret", fret_proposal,
            self.manifest.fret_action_names,
            self.manifest.fret_checkpoint_sha256)
        self._validate_source_proposal(
            "strike", strike_proposal,
            self.manifest.strike_action_names,
            self.manifest.strike_checkpoint_sha256)
        fret_mean = fret_proposal.mean
        strike_mean = strike_proposal.mean
        if fret_mean.ndim != 2:
            raise ValueError("fret_mean must have shape [batch, action]")
        batch = fret_mean.shape[0]
        widths = (
            ("fret_mean", fret_mean, self.manifest.fret_action_dim),
            ("strike_mean", strike_mean, self.manifest.strike_action_dim),
            ("goal_context", goal_context,
             self.actor_config.goal_context_dim),
            ("readiness_context", readiness_context,
             self.actor_config.readiness_context_dim),
            ("joint_context", joint_context,
             self.actor_config.joint_context_dim),
            ("guitar_context", guitar_context,
             self.actor_config.guitar_context_dim),
            ("privileged_context", privileged_context,
             self.config.privileged_context_dim),
        )
        for name, value, width in widths:
            self._require_matrix(name, value, batch, width)
        all_inputs = tuple(value for _, value, _ in widths)
        if any(value.device != fret_mean.device for value in all_inputs[1:]):
            raise ValueError("all critic inputs must share one device")
        parameter = next(self.parameters(), None)
        if parameter is not None and parameter.device != fret_mean.device:
            raise ValueError("critic inputs and parameters must share a device")
        if parameter is not None and parameter.dtype != torch.float32:
            raise RuntimeError("critic parameters left their FP32 contract")

        features = (
            self.action_encoder(self.source_intent_normalizer(
                fret_mean, strike_mean)),
            self.goal_encoder(goal_context),
            self.readiness_encoder(readiness_context),
            self.joint_encoder(joint_context),
            self.guitar_encoder(guitar_context),
            self.privileged_encoder(privileged_context),
        )
        return self.value_network(torch.cat(features, dim=-1))

    def forward_structured_goal(
            self, *, fret_proposal: SourceProposal,
            strike_proposal: SourceProposal,
            goal_score: GoalScoreBatch, readiness_context: torch.Tensor,
            joint_context: torch.Tensor, guitar_context: torch.Tensor,
            privileged_context: torch.Tensor) -> torch.Tensor:
        """Critic path with its own checkpointed GoalScoreEncoder."""

        return self.forward(
            fret_proposal=fret_proposal,
            strike_proposal=strike_proposal,
            goal_context=self.goal_score_encoder(goal_score),
            readiness_context=readiness_context,
            joint_context=joint_context,
            guitar_context=guitar_context,
            privileged_context=privileged_context,
        )

    def checkpoint_manifest(self) -> dict[str, object]:
        return {
            "architecture_id": self.manifest.architecture_id,
            "action_manifest_sha256": self.manifest.sha256(),
            "action_manifest": self.manifest.payload(),
            "actor_config": asdict(self.actor_config),
            "critic_config": asdict(self.config),
            "value_head_names": list(self.config.value_head_names),
            "privileged_context_dim": self.config.privileged_context_dim,
            "hidden_dims": list(self.config.hidden_dims),
            "goal_score_schema": self.goal_score_encoder.schema_metadata(),
            "static_context_schema": {
                "readiness_sha256": READINESS_MANIFEST.sha256(),
                "guitar_support_sha256": GUITAR_SUPPORT_MANIFEST.sha256(),
                "privileged_sha256": PRIVILEGED_MANIFEST.sha256(),
            },
            "source_intent_calibration":
                self.source_intent_normalizer.checkpoint_manifest(),
        }

    def get_extra_state(self) -> dict[str, object]:
        """Persist value-head meanings and the complete action ABI."""

        return deepcopy(self.checkpoint_manifest())

    def set_extra_state(self, state: dict[str, object]) -> None:
        if not isinstance(state, dict) or state != self.checkpoint_manifest():
            raise RuntimeError(
                "Action Residual critic checkpoint manifest mismatch")

    def _validate_semantic_state_dict(self, state_dict, prefix: str = "") -> None:
        expected = {
            f"{prefix}_extra_state": self.get_extra_state(),
            f"{prefix}goal_score_encoder._extra_state":
                self.goal_score_encoder.get_extra_state(),
            f"{prefix}source_intent_normalizer._extra_state":
                self.source_intent_normalizer.get_extra_state(),
        }
        for key, value in expected.items():
            if state_dict.get(key) != value:
                raise RuntimeError(
                    "Action Residual critic checkpoint manifest mismatch")

    def _load_from_state_dict(
            self, state_dict, prefix, local_metadata, strict,
            missing_keys, unexpected_keys, error_msgs):
        validate_finite_state_dict(state_dict, label="critic")
        self._validate_semantic_state_dict(state_dict, prefix)
        return super()._load_from_state_dict(
            state_dict, prefix, local_metadata, strict,
            missing_keys, unexpected_keys, error_msgs)

    def load_state_dict(self, state_dict, strict: bool = True, assign: bool = False):
        """Validate semantic metadata before mutating any parameter tensor."""

        validate_finite_state_dict(state_dict, label="critic")
        self._validate_semantic_state_dict(state_dict)
        return super().load_state_dict(
            state_dict, strict=strict, assign=assign)
