"""Fail-closed, name-based action layout for Full control."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Iterable


ACTION_RESIDUAL_ARCHITECTURE_ID = "full.action_residual.pre_tanh.v1"
CURRENT_PROFILE_JOINT_DIM = 75
CURRENT_PROFILE_FRET_DIM = 30
CURRENT_PROFILE_STRIKE_DIM = 30
CURRENT_PROFILE_ARM_RESIDUAL_DIM = 18
CURRENT_PROFILE_BODY_RESIDUAL_DIM = 15
CURRENT_PROFILE_PROTECTED_FINGER_DIM = 42
CURRENT_PROFILE_JOINT_FEATURES = 8


def _names(label: str, values: Iterable[str]) -> tuple[str, ...]:
    result = tuple(str(value) for value in values)
    if not result:
        raise ValueError(f"{label} must not be empty")
    if any(not value for value in result):
        raise ValueError(f"{label} must contain non-empty names")
    if len(set(result)) != len(result):
        raise ValueError(f"{label} must contain unique names")
    return result


@dataclass(frozen=True)
class ActionResidualManifest:
    """Immutable action ABI and residual authority.

    ``neutral_logits`` are pre-tanh values.  They must be calculated from the
    seated hold action; numeric zero is not assumed to be a valid hold target.
    Caps correspond to ``arm_residual_names + body_residual_names``.
    """

    joint_action_names: tuple[str, ...]
    fret_action_names: tuple[str, ...]
    strike_action_names: tuple[str, ...]
    arm_residual_names: tuple[str, ...]
    body_residual_names: tuple[str, ...]
    neutral_logits: tuple[float, ...]
    residual_caps: tuple[float, ...]
    fret_checkpoint_sha256: str = ""
    strike_checkpoint_sha256: str = ""
    architecture_id: str = ACTION_RESIDUAL_ARCHITECTURE_ID

    def __post_init__(self) -> None:
        groups = {
            "joint_action_names": _names(
                "joint_action_names", self.joint_action_names),
            "fret_action_names": _names(
                "fret_action_names", self.fret_action_names),
            "strike_action_names": _names(
                "strike_action_names", self.strike_action_names),
            "arm_residual_names": _names(
                "arm_residual_names", self.arm_residual_names),
            "body_residual_names": _names(
                "body_residual_names", self.body_residual_names),
        }
        for key, value in groups.items():
            object.__setattr__(self, key, value)

        joint = set(self.joint_action_names)
        fret = set(self.fret_action_names)
        strike = set(self.strike_action_names)
        arms = set(self.arm_residual_names)
        body = set(self.body_residual_names)
        if not fret.isdisjoint(strike):
            raise ValueError("Fret and Strike source actions must be disjoint")
        for label, subset in (
                ("Fret", fret), ("Strike", strike),
                ("arm residual", arms), ("body residual", body)):
            missing = subset - joint
            if missing:
                raise ValueError(
                    f"{label} names are absent from the joint manifest: "
                    f"{sorted(missing)}")
        if not arms.issubset(fret | strike):
            raise ValueError("arm residual authority must belong to a source action")
        if not arms.isdisjoint(body):
            raise ValueError("arm and body residual names must be disjoint")

        neutral = tuple(float(value) for value in self.neutral_logits)
        caps = tuple(float(value) for value in self.residual_caps)
        if len(neutral) != len(self.joint_action_names):
            raise ValueError("neutral_logits must match joint_action_names")
        if len(caps) != self.residual_dim:
            raise ValueError("residual_caps must match residual action names")
        if not all(math.isfinite(value) for value in neutral):
            raise ValueError("neutral_logits must be finite")
        if not all(math.isfinite(value) and value >= 0.0 for value in caps):
            raise ValueError("residual_caps must be finite and non-negative")
        object.__setattr__(self, "neutral_logits", neutral)
        object.__setattr__(self, "residual_caps", caps)

        if self.architecture_id != ACTION_RESIDUAL_ARCHITECTURE_ID:
            raise ValueError(
                "Action Residual manifest has the wrong architecture_id")
        for label, digest in (
                ("fret_checkpoint_sha256", self.fret_checkpoint_sha256),
                ("strike_checkpoint_sha256", self.strike_checkpoint_sha256)):
            if digest and (len(digest) != 64
                           or any(c not in "0123456789abcdef" for c in digest)):
                raise ValueError(f"{label} must be an empty string or lowercase SHA-256")

    @property
    def joint_action_dim(self) -> int:
        return len(self.joint_action_names)

    @property
    def fret_action_dim(self) -> int:
        return len(self.fret_action_names)

    @property
    def strike_action_dim(self) -> int:
        return len(self.strike_action_names)

    @property
    def residual_action_names(self) -> tuple[str, ...]:
        return self.arm_residual_names + self.body_residual_names

    @property
    def residual_dim(self) -> int:
        return len(self.arm_residual_names) + len(self.body_residual_names)

    @property
    def new_action_names(self) -> tuple[str, ...]:
        sources = set(self.fret_action_names) | set(self.strike_action_names)
        return tuple(name for name in self.joint_action_names if name not in sources)

    @property
    def protected_action_names(self) -> tuple[str, ...]:
        residual = set(self.residual_action_names)
        return tuple(name for name in self.joint_action_names if name not in residual)

    def indices(self, names: Iterable[str]) -> tuple[int, ...]:
        lookup = {name: index for index, name in enumerate(self.joint_action_names)}
        return tuple(lookup[name] for name in names)

    def validate_current_75d_profile(self, joint_context_dim: int) -> None:
        """Fail closed on the no-gaze 75D profile implemented by v1.

        ``ActionResidualManifest`` remains a serializable name container, but
        the v1 coordinator is intentionally not a generic arbitrary-width
        policy.  A future 81D gaze model must use another architecture ID.
        """
        expected = {
            "joint action": (self.joint_action_dim, CURRENT_PROFILE_JOINT_DIM),
            "Fret action": (self.fret_action_dim, CURRENT_PROFILE_FRET_DIM),
            "Strike action": (
                self.strike_action_dim, CURRENT_PROFILE_STRIKE_DIM),
            "arm residual": (
                len(self.arm_residual_names),
                CURRENT_PROFILE_ARM_RESIDUAL_DIM),
            "body residual": (
                len(self.body_residual_names),
                CURRENT_PROFILE_BODY_RESIDUAL_DIM),
            "protected finger": (
                len(self.protected_action_names),
                CURRENT_PROFILE_PROTECTED_FINGER_DIM),
        }
        wrong = [
            f"{label}={actual}, expected {target}"
            for label, (actual, target) in expected.items()
            if actual != target
        ]
        if wrong:
            raise ValueError(
                "Action Residual v1 requires the current 75D profile: "
                + "; ".join(wrong))

        if set(self.new_action_names) != set(self.body_residual_names):
            raise ValueError(
                "every non-source action must be owned by the 15D body "
                "residual, with no orphan action")
        expected_joint_context = (
            self.joint_action_dim * CURRENT_PROFILE_JOINT_FEATURES)
        if int(joint_context_dim) != expected_joint_context:
            raise ValueError(
                "joint_context_dim must equal 75 actions × 8 features "
                f"({expected_joint_context})")

        arm_prefixes = (
            "L_Shoulder", "L_Elbow", "L_Wrist",
            "R_Shoulder", "R_Elbow", "R_Wrist",
        )
        for prefix in arm_prefixes:
            count = sum(
                name.startswith(prefix) for name in self.arm_residual_names)
            if count != 3:
                raise ValueError(
                    f"arm residual requires exactly three {prefix} axes")
        body_prefixes = (
            "L_Thorax", "R_Thorax", "Torso", "Spine", "Chest",
        )
        for prefix in body_prefixes:
            count = sum(
                name.startswith(prefix) for name in self.body_residual_names)
            if count != 3:
                raise ValueError(
                    f"body residual requires exactly three {prefix} axes")

        for label, digest in (
                ("Fret", self.fret_checkpoint_sha256),
                ("Strike", self.strike_checkpoint_sha256)):
            if not digest:
                raise ValueError(
                    f"{label} checkpoint SHA-256 is required by the 75D "
                    "runtime profile")

    def payload(self) -> dict[str, object]:
        return {
            "architecture_id": self.architecture_id,
            "joint_action_names": list(self.joint_action_names),
            "fret_action_names": list(self.fret_action_names),
            "strike_action_names": list(self.strike_action_names),
            "arm_residual_names": list(self.arm_residual_names),
            "body_residual_names": list(self.body_residual_names),
            "neutral_logits": list(self.neutral_logits),
            "residual_caps": list(self.residual_caps),
            "fret_checkpoint_sha256": self.fret_checkpoint_sha256,
            "strike_checkpoint_sha256": self.strike_checkpoint_sha256,
        }

    def sha256(self) -> str:
        canonical = json.dumps(
            self.payload(), ensure_ascii=False, sort_keys=True,
            separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()
