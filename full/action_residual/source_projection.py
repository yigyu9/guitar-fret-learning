"""Fail-closed projected observation view for frozen source policies.

The Full environment owns one live physics state.  A frozen source policy may
still need a projected legacy observation so motion from the foreign hand and
new body joints does not create an uncontrolled observation-distribution
shift.  Projection happens in raw observation space, before the source's
frozen normalization.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import math
from typing import Iterable

import torch
from torch import nn

from .checkpoint_utils import validate_finite_state_dict


PROJECTED_SOURCE_VIEW_ID = "full.source_observation.projected_legacy.v1"


def _string_tuple(label: str, values: Iterable[str]) -> tuple[str, ...]:
    result = tuple(str(value) for value in values)
    if not result or any(not value for value in result):
        raise ValueError(f"{label} must contain non-empty names")
    if len(set(result)) != len(result):
        raise ValueError(f"{label} must contain unique names")
    return result


def _sha256(payload: object) -> str:
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class SourceProjectionManifest:
    """Names and identity required to reproduce a source observation view."""

    source_name: str
    observation_names: tuple[str, ...]
    replace_with_rms_mean_names: tuple[str, ...]
    checkpoint_sha256: str
    rms_sha256: str
    view_id: str = PROJECTED_SOURCE_VIEW_ID

    def __post_init__(self) -> None:
        source_name = str(self.source_name)
        if not source_name:
            raise ValueError("source_name must not be empty")
        object.__setattr__(self, "source_name", source_name)
        observations = _string_tuple(
            "observation_names", self.observation_names)
        replacements = tuple(
            str(value) for value in self.replace_with_rms_mean_names)
        if any(not value for value in replacements):
            raise ValueError(
                "replace_with_rms_mean_names must contain non-empty names")
        if len(set(replacements)) != len(replacements):
            raise ValueError(
                "replace_with_rms_mean_names must contain unique names")
        missing = set(replacements) - set(observations)
        if missing:
            raise ValueError(
                "replacement fields are absent from observation_names: "
                f"{sorted(missing)}")
        object.__setattr__(self, "observation_names", observations)
        object.__setattr__(
            self, "replace_with_rms_mean_names", replacements)

        if self.view_id != PROJECTED_SOURCE_VIEW_ID:
            raise ValueError("unsupported source projection view_id")
        for label, digest in (
                ("checkpoint_sha256", self.checkpoint_sha256),
                ("rms_sha256", self.rms_sha256)):
            digest = str(digest)
            if (len(digest) != 64
                    or any(char not in "0123456789abcdef" for char in digest)):
                raise ValueError(f"{label} must be a lowercase SHA-256")
            object.__setattr__(self, label, digest)

    @property
    def observation_dim(self) -> int:
        return len(self.observation_names)

    @property
    def replacement_indices(self) -> tuple[int, ...]:
        lookup = {
            name: index for index, name in enumerate(self.observation_names)
        }
        return tuple(
            lookup[name] for name in self.replace_with_rms_mean_names)

    def payload(self) -> dict[str, object]:
        return {
            "source_name": self.source_name,
            "observation_names": list(self.observation_names),
            "replace_with_rms_mean_names": list(
                self.replace_with_rms_mean_names),
            "checkpoint_sha256": self.checkpoint_sha256,
            "rms_sha256": self.rms_sha256,
            "view_id": self.view_id,
        }

    def sha256(self) -> str:
        return _sha256(self.payload())


@dataclass(frozen=True)
class ProjectedSourceObservation:
    """Raw actor input plus a normalization result used only for audits.

    Existing ``ActorCritic.distribution(raw_obs)`` applies ``obs_rms``
    internally.  Runtime adapters must therefore pass ``raw_projected`` to
    the policy.  ``normalized_audit`` exists only for S0 equivalence checks;
    feeding it to the normal policy API would normalize twice.
    """

    raw_projected: torch.Tensor
    normalized_audit: torch.Tensor
    source_name: str
    checkpoint_sha256: str
    projection_manifest_sha256: str
    observation_dim: int

    def __post_init__(self) -> None:
        if (not isinstance(self.raw_projected, torch.Tensor)
                or not isinstance(self.normalized_audit, torch.Tensor)):
            raise TypeError("projected source payloads must be tensors")
        if (self.raw_projected.ndim != 2
                or self.normalized_audit.shape != self.raw_projected.shape):
            raise ValueError(
                "projected raw/audit tensors must have one [batch, obs] shape")
        if (self.raw_projected.dtype != torch.float32
                or self.normalized_audit.dtype != torch.float32):
            raise TypeError("projected source observations must use torch.float32")
        if self.raw_projected.device != self.normalized_audit.device:
            raise ValueError("projected raw/audit tensors must share one device")
        if (not torch.isfinite(self.raw_projected).all()
                or not torch.isfinite(self.normalized_audit).all()):
            raise ValueError("projected source observations must be finite")
        if (isinstance(self.observation_dim, bool)
                or not isinstance(self.observation_dim, int)
                or self.observation_dim <= 0
                or self.raw_projected.shape[-1] != self.observation_dim):
            raise ValueError("observation_dim must match the tensor width")
        if not isinstance(self.source_name, str) or not self.source_name:
            raise ValueError("source_name must be non-empty")
        for label, digest in (
                ("checkpoint_sha256", self.checkpoint_sha256),
                ("projection_manifest_sha256",
                 self.projection_manifest_sha256)):
            if (not isinstance(digest, str) or len(digest) != 64
                    or any(char not in "0123456789abcdef" for char in digest)):
                raise ValueError(f"{label} must be a lowercase SHA-256")


class FrozenSourceObservationProjector(nn.Module):
    """Project raw fields, then apply the immutable source RMS."""

    def __init__(
            self, manifest: SourceProjectionManifest, *,
            rms_mean: torch.Tensor, rms_variance: torch.Tensor,
            epsilon: float = 1e-8, clip: float = 5.0) -> None:
        super().__init__()
        self.manifest = manifest
        mean = torch.as_tensor(rms_mean, dtype=torch.float32).detach().clone()
        variance = torch.as_tensor(
            rms_variance, dtype=torch.float32).detach().clone()
        expected = (manifest.observation_dim,)
        if mean.shape != expected or variance.shape != expected:
            raise ValueError(
                "source RMS mean and variance must match observation_names")
        if not torch.isfinite(mean).all():
            raise ValueError("source RMS mean must be finite")
        if (not torch.isfinite(variance).all()
                or not bool((variance >= 0.0).all())):
            raise ValueError("source RMS variance must be finite and nonnegative")
        if not math.isfinite(float(epsilon)) or float(epsilon) <= 0.0:
            raise ValueError("epsilon must be finite and positive")
        if not math.isfinite(float(clip)) or float(clip) <= 0.0:
            raise ValueError("clip must be finite and positive")

        actual_rms_sha = _sha256({
            "mean": [float(value) for value in mean.tolist()],
            "variance": [float(value) for value in variance.tolist()],
            "epsilon": float(epsilon),
            "clip": float(clip),
        })
        if actual_rms_sha != manifest.rms_sha256:
            raise ValueError("source RMS content does not match rms_sha256")

        self.epsilon = float(epsilon)
        self.clip = float(clip)
        self._rms_mean_values = tuple(float(value) for value in mean.tolist())
        self._rms_variance_values = tuple(
            float(value) for value in variance.tolist())
        # These values are constructor-bound source artifacts.  They are not
        # loadable state: a same-shape checkpoint must never replace them.
        self.register_buffer("rms_mean", mean, persistent=False)
        self.register_buffer("rms_variance", variance, persistent=False)
        self.register_buffer(
            "replacement_indices",
            torch.tensor(manifest.replacement_indices, dtype=torch.long),
            persistent=False,
        )

    def _apply(self, fn, recurse: bool = True):
        probe = torch.empty(
            0, dtype=torch.float32, device=self.rms_mean.device)
        if fn(probe).dtype != torch.float32:
            raise TypeError(
                "frozen source projection RMS must remain torch.float32")
        result = super()._apply(fn, recurse=recurse)
        if (self.rms_mean.dtype != torch.float32
                or self.rms_variance.dtype != torch.float32):
            device = self.rms_mean.device
            # Restore the exact constructor-bound FP32 artifacts before
            # failing, so a rejected ``half()/double()`` cannot poison later
            # source inference.
            self.rms_mean = torch.tensor(
                self._rms_mean_values, dtype=torch.float32, device=device)
            self.rms_variance = torch.tensor(
                self._rms_variance_values,
                dtype=torch.float32, device=device)
            raise TypeError(
                "frozen source projection RMS must remain torch.float32")
        return result

    @staticmethod
    def rms_sha256(
            rms_mean: torch.Tensor, rms_variance: torch.Tensor, *,
            epsilon: float = 1e-8, clip: float = 5.0) -> str:
        mean = torch.as_tensor(rms_mean, dtype=torch.float32).detach().cpu()
        variance = torch.as_tensor(
            rms_variance, dtype=torch.float32).detach().cpu()
        if mean.ndim != 1 or variance.shape != mean.shape:
            raise ValueError("RMS tensors must be same-shape vectors")
        if (not torch.isfinite(mean).all()
                or not torch.isfinite(variance).all()
                or not bool((variance >= 0.0).all())):
            raise ValueError("RMS tensors must be finite with nonnegative variance")
        if (not math.isfinite(float(epsilon)) or float(epsilon) <= 0.0
                or not math.isfinite(float(clip)) or float(clip) <= 0.0):
            raise ValueError("epsilon and clip must be finite and positive")
        return _sha256({
            "mean": [float(value) for value in mean.tolist()],
            "variance": [float(value) for value in variance.tolist()],
            "epsilon": float(epsilon),
            "clip": float(clip),
        })

    def forward(self, live_raw: torch.Tensor) -> ProjectedSourceObservation:
        if (self.rms_mean.dtype != torch.float32
                or self.rms_variance.dtype != torch.float32):
            raise RuntimeError("source projection RMS left its FP32 contract")
        if (live_raw.ndim != 2
                or live_raw.shape[-1] != self.manifest.observation_dim):
            raise ValueError(
                "live_raw must have shape [batch, observation_dim]")
        if not torch.is_floating_point(live_raw):
            raise TypeError("live_raw must be floating point")
        if live_raw.dtype != torch.float32:
            raise TypeError(
                "source projection and frozen RMS must run in torch.float32")
        if not torch.isfinite(live_raw).all():
            raise ValueError("live_raw must be finite")

        mean = self.rms_mean.to(
            dtype=live_raw.dtype, device=live_raw.device)
        variance = self.rms_variance.to(
            dtype=live_raw.dtype, device=live_raw.device)
        indices = self.replacement_indices.to(device=live_raw.device)
        raw_projected = live_raw.clone()
        if indices.numel():
            replacements = mean.index_select(0, indices).unsqueeze(0).expand(
                live_raw.shape[0], -1)
            raw_projected.index_copy_(1, indices, replacements)
        normalized = (raw_projected - mean) / torch.sqrt(
            variance + self.epsilon)
        normalized = normalized.clamp(-self.clip, self.clip)
        return ProjectedSourceObservation(
            raw_projected=raw_projected,
            normalized_audit=normalized,
            source_name=self.manifest.source_name,
            checkpoint_sha256=self.manifest.checkpoint_sha256,
            projection_manifest_sha256=self.manifest.sha256(),
            observation_dim=self.manifest.observation_dim,
        )

    def checkpoint_manifest(self) -> dict[str, object]:
        return {
            "projection_manifest": self.manifest.payload(),
            "projection_manifest_sha256": self.manifest.sha256(),
            "epsilon": self.epsilon,
            "clip": self.clip,
        }

    def get_extra_state(self) -> dict[str, object]:
        return deepcopy(self.checkpoint_manifest())

    def set_extra_state(self, state: dict[str, object]) -> None:
        if not isinstance(state, dict) or state != self.checkpoint_manifest():
            raise RuntimeError("source projection checkpoint manifest mismatch")

    def _load_from_state_dict(
            self, state_dict, prefix, local_metadata, strict,
            missing_keys, unexpected_keys, error_msgs):
        validate_finite_state_dict(state_dict, label="source projection")
        if state_dict.get(f"{prefix}_extra_state") != self.get_extra_state():
            raise RuntimeError("source projection checkpoint manifest mismatch")
        return super()._load_from_state_dict(
            state_dict, prefix, local_metadata, strict,
            missing_keys, unexpected_keys, error_msgs)

    def load_state_dict(self, state_dict, strict: bool = True, assign: bool = False):
        if state_dict.get("_extra_state") != self.get_extra_state():
            raise RuntimeError("source projection checkpoint manifest mismatch")
        return super().load_state_dict(
            state_dict, strict=strict, assign=assign)
