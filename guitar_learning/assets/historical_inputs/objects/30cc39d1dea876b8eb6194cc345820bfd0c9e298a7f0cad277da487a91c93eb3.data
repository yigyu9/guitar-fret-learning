"""Named 105D FullBody action contract and G0 source-action arbitration."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional
import xml.etree.ElementTree as ET

import torch

from tab2body.learning.checkpoint_contract import canonical_sha256


FULL_ACTION_SCHEMA = "tab2body.full_action.v1"
FULL_ACTION_DIM = 105


def humanoid_joint_names(mjcf_path: Path) -> tuple:
    """Return the authored MJCF joint order used as the Full action ABI."""
    path = Path(mjcf_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"humanoid MJCF not found: {path}")
    root = ET.parse(str(path)).getroot()
    names = tuple(
        joint.get("name") for joint in root.iter("joint")
        if joint.get("name"))
    if not names or len(names) != len(set(names)):
        raise ValueError("humanoid MJCF joint names must be non-empty and unique")
    return names


@dataclass(frozen=True)
class FullActionManifest:
    """Final 105D name/order plus ownership in fixed-guitar G0.

    G0 activates only the two frozen 30D source skills.  Every other authored
    joint remains a named ``reserved_hold`` slot; it is not silently dropped
    into a temporary 60D ABI.
    """

    joint_names: tuple
    fret_action_names: tuple
    strike_action_names: tuple
    reserved_hold_names: tuple
    schema: str = FULL_ACTION_SCHEMA

    def __post_init__(self):
        joint_names = tuple(str(name) for name in self.joint_names)
        fret = tuple(str(name) for name in self.fret_action_names)
        strike = tuple(str(name) for name in self.strike_action_names)
        reserved = tuple(str(name) for name in self.reserved_hold_names)
        if self.schema != FULL_ACTION_SCHEMA:
            raise ValueError("unsupported Full action schema")
        if len(joint_names) != FULL_ACTION_DIM:
            raise ValueError(
                f"Full action manifest must contain {FULL_ACTION_DIM} joints")
        if len(set(joint_names)) != len(joint_names):
            raise ValueError("Full action joint names must be unique")
        if len(fret) != 30 or len(strike) != 30:
            raise ValueError("G0 requires exact 30D Fret and 30D Strike sources")
        if set(fret) & set(strike):
            raise ValueError("Fret and Strike action ownership must be disjoint")
        if len(reserved) != 45:
            raise ValueError("G0 must retain exactly 45 reserved hold slots")
        partition = fret + strike + reserved
        if len(set(partition)) != FULL_ACTION_DIM or set(partition) != set(
                joint_names):
            raise ValueError(
                "Fret, Strike and reserved_hold must partition the 105D ABI")
        object.__setattr__(self, "joint_names", joint_names)
        object.__setattr__(self, "fret_action_names", fret)
        object.__setattr__(self, "strike_action_names", strike)
        object.__setattr__(self, "reserved_hold_names", reserved)

    @classmethod
    def from_joint_names(cls, joint_names: Iterable[str], *,
                         fret_action_names: Iterable[str],
                         strike_action_names: Iterable[str]):
        full = tuple(str(name) for name in joint_names)
        fret = tuple(str(name) for name in fret_action_names)
        strike = tuple(str(name) for name in strike_action_names)
        source = set(fret) | set(strike)
        missing = sorted(source - set(full))
        if missing:
            raise ValueError(
                f"source actions are absent from humanoid MJCF: {missing}")
        reserved = tuple(name for name in full if name not in source)
        return cls(full, fret, strike, reserved)

    @classmethod
    def from_mjcf(cls, mjcf_path: Path, *, fret_action_names,
                  strike_action_names):
        return cls.from_joint_names(
            humanoid_joint_names(mjcf_path),
            fret_action_names=fret_action_names,
            strike_action_names=strike_action_names)

    @property
    def fret_indices(self):
        index = {name: i for i, name in enumerate(self.joint_names)}
        return tuple(index[name] for name in self.fret_action_names)

    @property
    def strike_indices(self):
        index = {name: i for i, name in enumerate(self.joint_names)}
        return tuple(index[name] for name in self.strike_action_names)

    @property
    def reserved_hold_indices(self):
        index = {name: i for i, name in enumerate(self.joint_names)}
        return tuple(index[name] for name in self.reserved_hold_names)

    def to_document(self):
        return {
            "schema": self.schema,
            "dimension": FULL_ACTION_DIM,
            "joint_names": list(self.joint_names),
            "ownership": {
                "fret_source": list(self.fret_action_names),
                "strike_source": list(self.strike_action_names),
                "reserved_hold": list(self.reserved_hold_names),
            },
        }

    @property
    def sha256(self):
        return canonical_sha256(self.to_document())


@dataclass(frozen=True)
class ArbitratedAction:
    """Pre-EMA command after ownership and Synchronizer holds are applied.

    The two local actions are deliberately named ``commanded``.  The shared
    Full task still has to apply its single common EMA/PD update and report the
    resulting action back to :class:`G0SynchronizationRuntime`; only that
    post-EMA value is valid for each frozen policy's ``O_history`` block.
    """

    full_action: torch.Tensor
    commanded_fret_action: torch.Tensor
    commanded_strike_action: torch.Tensor
    source_active_mask: torch.Tensor
    reserved_hold_mask: torch.Tensor


class G0ActionArbiter:
    """Scatter frozen source actions into the stable 105D named ABI.

    ``hold_action`` is mandatory because normalized zero is a joint midpoint,
    not necessarily the seated pose.  The shared physics environment must
    compute this vector from its actual joint limits and initial PD targets.
    EMA/PD is intentionally *not* applied here; the Full task applies it once
    after this arbitration.
    """

    def __init__(self, manifest: FullActionManifest):
        self.manifest = manifest

    @staticmethod
    def _source(value, batch, width, name):
        if not isinstance(value, torch.Tensor):
            raise TypeError(f"{name} must be a torch.Tensor")
        if value.shape != (batch, width):
            raise ValueError(
                f"{name} must have shape {(batch, width)}, got {tuple(value.shape)}")
        if not value.is_floating_point() or not torch.isfinite(value).all():
            raise ValueError(f"{name} must be a finite floating tensor")
        tolerance = 1e-6
        if bool((value.abs() > 1.0 + tolerance).any().item()):
            raise ValueError(f"{name} must remain in normalized range [-1,1]")
        return value

    def merge(self, fret_action: torch.Tensor, strike_action: torch.Tensor,
              hold_action: torch.Tensor, *, hold_fret=None,
              hold_strike=None, previous_fret_action=None,
              previous_strike_action=None,
              strike_entry_hold_action=None) -> ArbitratedAction:
        if not isinstance(hold_action, torch.Tensor) or hold_action.ndim != 2:
            raise ValueError("hold_action must have shape [N,105]")
        batch = hold_action.shape[0]
        if hold_action.shape[1] != FULL_ACTION_DIM:
            raise ValueError("hold_action must have shape [N,105]")
        if not hold_action.is_floating_point() or not torch.isfinite(
                hold_action).all():
            raise ValueError("hold_action must be finite and floating")
        tolerance = 1e-6
        if bool((hold_action.abs() > 1.0 + tolerance).any().item()):
            raise ValueError("hold_action must remain in normalized range [-1,1]")
        fret = self._source(fret_action, batch, 30, "fret_action")
        strike = self._source(strike_action, batch, 30, "strike_action")
        if fret.device != hold_action.device or strike.device != hold_action.device:
            raise ValueError("all action tensors must share a device")
        if fret.dtype != hold_action.dtype or strike.dtype != hold_action.dtype:
            raise ValueError("all action tensors must share a dtype")

        def apply_hold(current, previous, mask, label, explicit=None):
            if mask is None:
                return current
            mask_value = torch.as_tensor(
                mask, dtype=torch.bool, device=current.device)
            if mask_value.shape != (batch,):
                raise ValueError(f"{label} must have shape [N]")
            hold_value = explicit if explicit is not None else previous
            if hold_value is None:
                raise ValueError(f"{label} requires a previous source action")
            previous_value = self._source(
                hold_value, batch, current.shape[1],
                (f"explicit_{label}" if explicit is not None
                 else f"previous_{label}"))
            if previous_value.dtype != current.dtype:
                raise ValueError("previous source action dtype mismatch")
            return torch.where(mask_value[:, None], previous_value, current)

        fret = apply_hold(fret, previous_fret_action, hold_fret, "hold_fret")
        strike = apply_hold(
            strike, previous_strike_action, hold_strike, "hold_strike",
            explicit=strike_entry_hold_action)
        full = hold_action.clone()
        fret_idx = torch.as_tensor(
            self.manifest.fret_indices, dtype=torch.long,
            device=hold_action.device)
        strike_idx = torch.as_tensor(
            self.manifest.strike_indices, dtype=torch.long,
            device=hold_action.device)
        full[:, fret_idx] = fret
        full[:, strike_idx] = strike
        source_mask = torch.zeros(
            FULL_ACTION_DIM, dtype=torch.bool, device=hold_action.device)
        source_mask[fret_idx] = True
        source_mask[strike_idx] = True
        return ArbitratedAction(
            full_action=full,
            commanded_fret_action=fret,
            commanded_strike_action=strike,
            source_active_mask=source_mask,
            reserved_hold_mask=~source_mask,
        )


__all__ = [
    "ArbitratedAction",
    "FULL_ACTION_DIM",
    "FULL_ACTION_SCHEMA",
    "FullActionManifest",
    "G0ActionArbiter",
    "humanoid_joint_names",
]
