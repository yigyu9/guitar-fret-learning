"""High-level typed context packer and combined checkpoint manifest."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Sequence

import torch

from .context_encoding import (
    GUITAR_SUPPORT_DIM,
    GUITAR_SUPPORT_MANIFEST,
    JOINT_HISTORY_DIM,
    PRIVILEGED_DIM,
    PRIVILEGED_MANIFEST,
    READINESS_DIM,
    READINESS_MANIFEST,
    GuitarSupportEncodingInput,
    GuitarSupportPacker,
    JointHistoryEncodingInput,
    JointHistoryPacker,
    PrivilegedEncodingInput,
    PrivilegedPacker,
    ReadinessEncodingInput,
    ReadinessPacker,
)
from .manifest import ActionResidualManifest


CONTEXT_PIPELINE_ID = "full.action_residual.context_pipeline.v1"


@dataclass(frozen=True)
class PackedActorContext:
    """The three non-Goal tensors consumed by the actor."""

    readiness_context: torch.Tensor
    joint_context: torch.Tensor
    guitar_context: torch.Tensor

    def __post_init__(self) -> None:
        tensors = (
            ("readiness_context", self.readiness_context, READINESS_DIM),
            ("joint_context", self.joint_context, JOINT_HISTORY_DIM),
            ("guitar_context", self.guitar_context, GUITAR_SUPPORT_DIM),
        )
        batch = None
        device = None
        for name, tensor, width in tensors:
            if (not isinstance(tensor, torch.Tensor)
                    or tensor.ndim != 2 or tensor.shape[1] != width):
                raise ValueError(f"{name} must have shape [batch, {width}]")
            if not tensor.is_floating_point() or not torch.isfinite(tensor).all():
                raise ValueError(f"{name} must be finite floating point")
            if tensor.dtype != torch.float32:
                raise TypeError(f"{name} must use torch.float32")
            batch = tensor.shape[0] if batch is None else batch
            device = tensor.device if device is None else device
            if tensor.shape[0] != batch:
                raise ValueError("packed actor contexts must share a batch")
            if tensor.device != device:
                raise ValueError("packed actor contexts must share a device")

    @property
    def batch_size(self) -> int:
        return self.readiness_context.shape[0]

    def as_kwargs(self) -> dict[str, torch.Tensor]:
        return {
            "readiness_context": self.readiness_context,
            "joint_context": self.joint_context,
            "guitar_context": self.guitar_context,
        }


@dataclass(frozen=True)
class PackedCriticContext:
    """Actor-observable tensors plus critic-only privileged context."""

    actor: PackedActorContext
    privileged_context: torch.Tensor

    def __post_init__(self) -> None:
        value = self.privileged_context
        if (not isinstance(value, torch.Tensor) or value.ndim != 2
                or value.shape != (self.actor.batch_size, PRIVILEGED_DIM)):
            raise ValueError(
                "privileged_context must have shape [actor batch, 128]")
        if value.device != self.actor.readiness_context.device:
            raise ValueError("actor and privileged contexts must share a device")
        if not value.is_floating_point() or not torch.isfinite(value).all():
            raise ValueError("privileged_context must be finite floating point")
        if value.dtype != torch.float32:
            raise TypeError("privileged_context must use torch.float32")

    def as_kwargs(self) -> dict[str, torch.Tensor]:
        return {
            **self.actor.as_kwargs(),
            "privileged_context": self.privileged_context,
        }


class ActionResidualContextPacker:
    """Own all fixed-scale packers for one immutable 75D joint layout."""

    def __init__(
            self, action_manifest: ActionResidualManifest, *,
            lower_limits: Sequence[float],
            upper_limits: Sequence[float],
            velocity_scales: Sequence[float]) -> None:
        action_manifest.validate_current_75d_profile(JOINT_HISTORY_DIM)
        self.action_manifest = action_manifest
        self.protected_joint_indices = action_manifest.indices(
            action_manifest.protected_action_names)
        self.readiness = ReadinessPacker()
        self.joint = JointHistoryPacker(
            action_manifest.joint_action_names,
            lower_limits, upper_limits, velocity_scales)
        self.guitar = GuitarSupportPacker()
        self.privileged = PrivilegedPacker()

    def pack_actor(
            self, *, readiness: ReadinessEncodingInput,
            joint: JointHistoryEncodingInput,
            guitar: GuitarSupportEncodingInput) -> PackedActorContext:
        protected = torch.tensor(
            self.protected_joint_indices, dtype=torch.long,
            device=joint.effective_authority.device)
        for name, value in (
                ("previous_residual_ratio", joint.previous_residual_ratio),
                ("residual_rate_ratio", joint.residual_rate_ratio),
                ("effective_authority", joint.effective_authority)):
            if (not isinstance(value, torch.Tensor) or value.ndim != 2
                    or value.shape[-1] != JOINT_HISTORY_DIM // 8):
                raise ValueError(f"{name} must have shape [batch, 75]")
            if bool((value.index_select(1, protected) != 0.0).any()):
                raise ValueError(
                    f"{name} must be exactly zero on protected source fingers")
        return PackedActorContext(
            readiness_context=self.readiness.pack(readiness),
            joint_context=self.joint.pack(joint),
            guitar_context=self.guitar.pack(guitar),
        )

    def pack_critic(
            self, *, actor: PackedActorContext,
            privileged: PrivilegedEncodingInput) -> PackedCriticContext:
        return PackedCriticContext(
            actor=actor,
            privileged_context=self.privileged.pack(privileged),
        )

    def _payload_without_hash(self) -> dict[str, Any]:
        return {
            "pipeline_id": CONTEXT_PIPELINE_ID,
            "schema_version": 1,
            "action_manifest_sha256": self.action_manifest.sha256(),
            "blocks": {
                "readiness": READINESS_MANIFEST.payload(),
                "joint_history": self.joint.manifest.payload(),
                "guitar_support": GUITAR_SUPPORT_MANIFEST.payload(),
                "privileged": PRIVILEGED_MANIFEST.payload(),
            },
        }

    def checkpoint_manifest(self) -> dict[str, Any]:
        payload = self._payload_without_hash()
        encoded = json.dumps(
            payload, ensure_ascii=True, sort_keys=True,
            separators=(",", ":"), allow_nan=False).encode("utf-8")
        payload["schema_sha256"] = hashlib.sha256(encoded).hexdigest()
        return payload


__all__ = [
    "CONTEXT_PIPELINE_ID",
    "ActionResidualContextPacker",
    "PackedActorContext",
    "PackedCriticContext",
]
