"""Dimension contract for the Action Residual Coordinator."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ActionResidualConfig:
    """Fixed-shape context encoders used by the coordinator.

    Action dimensions are intentionally absent here.  They are derived from
    the ordered joint-name manifest, then validated against the current
    30D Fret + 30D Strike + 15D body profile.
    """

    goal_context_dim: int = 128
    readiness_context_dim: int = 64
    joint_context_dim: int = 600
    guitar_context_dim: int = 128

    action_feature_dim: int = 64
    goal_feature_dim: int = 64
    readiness_feature_dim: int = 64
    joint_feature_dim: int = 128
    guitar_feature_dim: int = 64

    small_encoder_hidden_dim: int = 128
    joint_encoder_hidden_dim: int = 256
    fusion_hidden_dims: tuple[int, int] = (512, 256)
    residual_head_hidden_dim: int = 128
    initial_new_action_std: float = 0.02

    def __post_init__(self) -> None:
        integer_fields = (
            "goal_context_dim",
            "readiness_context_dim",
            "joint_context_dim",
            "guitar_context_dim",
            "action_feature_dim",
            "goal_feature_dim",
            "readiness_feature_dim",
            "joint_feature_dim",
            "guitar_feature_dim",
            "small_encoder_hidden_dim",
            "joint_encoder_hidden_dim",
            "residual_head_hidden_dim",
        )
        for name in integer_fields:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if (len(self.fusion_hidden_dims) != 2
                or any(isinstance(v, bool) or not isinstance(v, int) or v <= 0
                       for v in self.fusion_hidden_dims)):
            raise ValueError("fusion_hidden_dims must contain two positive integers")
        if not 0.0 < float(self.initial_new_action_std) <= 1.0:
            raise ValueError("initial_new_action_std must be in (0, 1]")

        # These widths define ``full.action_residual.pre_tanh.v1``.  Allowing
        # a same-ID shape variant would break the structured Goal encoder,
        # context packers, and checkpoint semantics even when some Linear
        # tensor shapes happened to remain loadable.
        expected = {
            "goal_context_dim": 128,
            "readiness_context_dim": 64,
            "joint_context_dim": 600,
            "guitar_context_dim": 128,
            "action_feature_dim": 64,
            "goal_feature_dim": 64,
            "readiness_feature_dim": 64,
            "joint_feature_dim": 128,
            "guitar_feature_dim": 64,
            "small_encoder_hidden_dim": 128,
            "joint_encoder_hidden_dim": 256,
            "fusion_hidden_dims": (512, 256),
            "residual_head_hidden_dim": 128,
        }
        mismatches = [
            f"{name}={getattr(self, name)!r}, expected {value!r}"
            for name, value in expected.items()
            if getattr(self, name) != value
        ]
        if mismatches:
            raise ValueError(
                "Action Residual v1 network widths are fixed; use a new "
                "architecture ID for shape changes: " + "; ".join(mismatches))

    @property
    def fusion_input_dim(self) -> int:
        return (
            self.action_feature_dim
            + self.goal_feature_dim
            + self.readiness_feature_dim
            + self.joint_feature_dim
            + self.guitar_feature_dim
        )
