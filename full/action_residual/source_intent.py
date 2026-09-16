"""Frozen calibration for source pre-tanh means used as actor features."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any

import torch
from torch import nn

from .manifest import ActionResidualManifest


SOURCE_INTENT_ENCODING_ID = "full.action_residual.source_intent.v1"
CALIBRATED = "CALIBRATED"
CALIBRATION_REQUIRED = "CALIBRATION_REQUIRED"


def _finite_tuple(label: str, values: tuple[float, ...], size: int, *,
                  positive: bool = False) -> tuple[float, ...]:
    result = tuple(float(value) for value in values)
    if len(result) != size:
        raise ValueError(f"{label} must contain {size} values")
    if not all(math.isfinite(value) for value in result):
        raise ValueError(f"{label} must be finite")
    if positive and not all(value > 0.0 for value in result):
        raise ValueError(f"{label} must be strictly positive")
    return result


@dataclass(frozen=True)
class SourceIntentCalibration:
    """Immutable per-source robust center/scale contract."""

    fret_action_names: tuple[str, ...]
    strike_action_names: tuple[str, ...]
    fret_checkpoint_sha256: str
    strike_checkpoint_sha256: str
    fret_center: tuple[float, ...]
    fret_scale: tuple[float, ...]
    strike_center: tuple[float, ...]
    strike_scale: tuple[float, ...]
    status: str
    z_clip: float = 5.0
    encoding_id: str = SOURCE_INTENT_ENCODING_ID

    def __post_init__(self) -> None:
        fret_names = tuple(str(name) for name in self.fret_action_names)
        strike_names = tuple(str(name) for name in self.strike_action_names)
        for label, names in (
                ("fret_action_names", fret_names),
                ("strike_action_names", strike_names)):
            if not names or any(not name for name in names):
                raise ValueError(f"{label} must contain non-empty names")
            if len(set(names)) != len(names):
                raise ValueError(f"{label} must contain unique names")
        if not set(fret_names).isdisjoint(strike_names):
            raise ValueError("Fret and Strike calibration names must be disjoint")
        object.__setattr__(self, "fret_action_names", fret_names)
        object.__setattr__(self, "strike_action_names", strike_names)

        for label, digest in (
                ("fret_checkpoint_sha256", self.fret_checkpoint_sha256),
                ("strike_checkpoint_sha256", self.strike_checkpoint_sha256)):
            if (len(digest) != 64
                    or any(char not in "0123456789abcdef" for char in digest)):
                raise ValueError(f"{label} must be a lowercase SHA-256")
        object.__setattr__(self, "fret_center", _finite_tuple(
            "fret_center", self.fret_center, len(fret_names)))
        object.__setattr__(self, "fret_scale", _finite_tuple(
            "fret_scale", self.fret_scale, len(fret_names), positive=True))
        object.__setattr__(self, "strike_center", _finite_tuple(
            "strike_center", self.strike_center, len(strike_names)))
        object.__setattr__(self, "strike_scale", _finite_tuple(
            "strike_scale", self.strike_scale, len(strike_names), positive=True))
        if self.status not in (CALIBRATED, CALIBRATION_REQUIRED):
            raise ValueError("unsupported source-intent calibration status")
        if (not math.isfinite(float(self.z_clip))
                or float(self.z_clip) <= 0.0):
            raise ValueError("z_clip must be finite and positive")
        object.__setattr__(self, "z_clip", float(self.z_clip))
        if self.encoding_id != SOURCE_INTENT_ENCODING_ID:
            raise ValueError("unsupported source-intent encoding_id")

    @classmethod
    def fallback(
            cls, manifest: ActionResidualManifest, *,
            z_clip: float = 5.0) -> "SourceIntentCalibration":
        """Create the explicit ``clip(mu,-z,z)/z`` provisional contract."""

        return cls(
            fret_action_names=manifest.fret_action_names,
            strike_action_names=manifest.strike_action_names,
            fret_checkpoint_sha256=manifest.fret_checkpoint_sha256,
            strike_checkpoint_sha256=manifest.strike_checkpoint_sha256,
            fret_center=(0.0,) * manifest.fret_action_dim,
            fret_scale=(1.0,) * manifest.fret_action_dim,
            strike_center=(0.0,) * manifest.strike_action_dim,
            strike_scale=(1.0,) * manifest.strike_action_dim,
            status=CALIBRATION_REQUIRED,
            z_clip=z_clip,
        )

    def validate_manifest(self, manifest: ActionResidualManifest) -> None:
        expected = (
            (self.fret_action_names, manifest.fret_action_names, "Fret names"),
            (self.strike_action_names, manifest.strike_action_names,
             "Strike names"),
            (self.fret_checkpoint_sha256,
             manifest.fret_checkpoint_sha256, "Fret SHA"),
            (self.strike_checkpoint_sha256,
             manifest.strike_checkpoint_sha256, "Strike SHA"),
        )
        for actual, target, label in expected:
            if actual != target:
                raise ValueError(
                    f"source-intent calibration {label} does not match manifest")

    def payload(self) -> dict[str, Any]:
        return {
            "encoding_id": self.encoding_id,
            "status": self.status,
            "z_clip": self.z_clip,
            "fret_action_names": list(self.fret_action_names),
            "strike_action_names": list(self.strike_action_names),
            "fret_checkpoint_sha256": self.fret_checkpoint_sha256,
            "strike_checkpoint_sha256": self.strike_checkpoint_sha256,
            "fret_center": list(self.fret_center),
            "fret_scale": list(self.fret_scale),
            "strike_center": list(self.strike_center),
            "strike_scale": list(self.strike_scale),
        }

    def sha256(self) -> str:
        encoded = json.dumps(
            self.payload(), ensure_ascii=True, sort_keys=True,
            separators=(",", ":"), allow_nan=False).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


def calibrate_source_intent(
        manifest: ActionResidualManifest, *,
        fret_mean_samples: torch.Tensor,
        strike_mean_samples: torch.Tensor, quantile: float = 0.95,
        minimum_scale: float = 1e-3,
        z_clip: float = 5.0) -> SourceIntentCalibration:
    """Fit a deterministic median/absolute-quantile calibration offline."""

    if not 0.5 <= float(quantile) < 1.0:
        raise ValueError("quantile must be in [0.5, 1.0)")
    if not math.isfinite(float(minimum_scale)) or minimum_scale <= 0.0:
        raise ValueError("minimum_scale must be finite and positive")

    def fit(label: str, samples: torch.Tensor,
            width: int) -> tuple[tuple[float, ...], tuple[float, ...]]:
        if (not isinstance(samples, torch.Tensor)
                or samples.ndim != 2 or samples.shape[1] != width
                or samples.shape[0] < 2):
            raise ValueError(
                f"{label} samples must have shape [at least 2, {width}]")
        if not samples.is_floating_point() or not torch.isfinite(samples).all():
            raise ValueError(f"{label} samples must be finite floating point")
        values = samples.detach().to(dtype=torch.float64, device="cpu")
        center = values.median(dim=0).values
        scale = torch.quantile(
            (values - center).abs(), float(quantile), dim=0
        ).clamp_min(float(minimum_scale))
        return (
            tuple(float(value) for value in center.tolist()),
            tuple(float(value) for value in scale.tolist()),
        )

    fret_center, fret_scale = fit(
        "Fret", fret_mean_samples, manifest.fret_action_dim)
    strike_center, strike_scale = fit(
        "Strike", strike_mean_samples, manifest.strike_action_dim)
    return SourceIntentCalibration(
        fret_action_names=manifest.fret_action_names,
        strike_action_names=manifest.strike_action_names,
        fret_checkpoint_sha256=manifest.fret_checkpoint_sha256,
        strike_checkpoint_sha256=manifest.strike_checkpoint_sha256,
        fret_center=fret_center,
        fret_scale=fret_scale,
        strike_center=strike_center,
        strike_scale=strike_scale,
        status=CALIBRATED,
        z_clip=z_clip,
    )


class SourceIntentNormalizer(nn.Module):
    """Normalize only the encoder copy; source base means remain untouched."""

    def __init__(
            self, manifest: ActionResidualManifest,
            calibration: SourceIntentCalibration | None = None) -> None:
        super().__init__()
        calibration = calibration or SourceIntentCalibration.fallback(manifest)
        calibration.validate_manifest(manifest)
        self.calibration = calibration
        self.register_buffer(
            "fret_center", torch.tensor(calibration.fret_center))
        self.register_buffer(
            "fret_scale", torch.tensor(calibration.fret_scale))
        self.register_buffer(
            "strike_center", torch.tensor(calibration.strike_center))
        self.register_buffer(
            "strike_scale", torch.tensor(calibration.strike_scale))

    @property
    def calibration_required(self) -> bool:
        return self.calibration.status == CALIBRATION_REQUIRED

    def _normalize(
            self, name: str, value: torch.Tensor,
            center: torch.Tensor, scale: torch.Tensor) -> torch.Tensor:
        if (not isinstance(value, torch.Tensor) or value.ndim != 2
                or value.shape[1] != center.numel()):
            raise ValueError(
                f"{name} must have shape [batch, {center.numel()}]")
        if not value.is_floating_point() or not torch.isfinite(value).all():
            raise ValueError(f"{name} must be finite floating point")
        center = center.to(dtype=value.dtype, device=value.device)
        scale = scale.to(dtype=value.dtype, device=value.device)
        z = ((value - center) / scale).clamp(
            -self.calibration.z_clip, self.calibration.z_clip)
        return z / self.calibration.z_clip

    def forward(
            self, fret_mean: torch.Tensor,
            strike_mean: torch.Tensor) -> torch.Tensor:
        if fret_mean.shape[0] != strike_mean.shape[0]:
            raise ValueError("Fret and Strike source batches must match")
        fret = self._normalize(
            "fret_mean", fret_mean, self.fret_center, self.fret_scale)
        strike = self._normalize(
            "strike_mean", strike_mean,
            self.strike_center, self.strike_scale)
        result = torch.cat((fret, strike), dim=-1)
        if not torch.isfinite(result).all():
            raise RuntimeError("source-intent normalization produced nonfinite")
        return result

    def get_extra_state(self) -> dict[str, Any]:
        return {
            "calibration": deepcopy(self.calibration.payload()),
            "calibration_sha256": self.calibration.sha256(),
        }

    def set_extra_state(self, state: dict[str, Any]) -> None:
        if not isinstance(state, dict) or state != self.get_extra_state():
            raise RuntimeError("source-intent checkpoint calibration mismatch")

    def checkpoint_manifest(self) -> dict[str, Any]:
        return self.get_extra_state()


__all__ = [
    "CALIBRATED",
    "CALIBRATION_REQUIRED",
    "SOURCE_INTENT_ENCODING_ID",
    "SourceIntentCalibration",
    "SourceIntentNormalizer",
    "calibrate_source_intent",
]

