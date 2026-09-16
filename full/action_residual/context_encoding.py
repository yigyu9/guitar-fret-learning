"""Field-level context contracts and fail-closed fixed-scale encoders.

This module is deliberately independent from :mod:`model`.  It turns raw,
physical context records into the four fixed-width tensors consumed by the
Action Residual actor/critic while preserving a checkpointable schema.

The important distinction is between required state and optional sensors:

* required state must always be finite;
* optional payload is checked wherever its validity bit is one;
* invalid optional payload is encoded as exactly zero, even if the caller
  supplied NaN as the unavailable raw value.

All normalization is by immutable physical scales.  There is no online RMS in
this module, so a rollout and a later PPO re-evaluation see the same encoding.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Mapping, Sequence

import torch


READINESS_DIM = 64
JOINT_COUNT = 75
JOINT_FEATURE_COUNT = 8
JOINT_HISTORY_DIM = JOINT_COUNT * JOINT_FEATURE_COUNT
GUITAR_SUPPORT_DIM = 128
PRIVILEGED_DIM = 128

STRING_KEYS = (
    "string_high_e", "string_B", "string_G",
    "string_D", "string_A", "string_low_E",
)
SUPPORT_SITE_KEYS = (
    "left_neck",
    "right_palm_wrist",
    "right_forearm",
    "chest",
    "right_thigh",
)
TETHER_KEYS = ("left", "right")


def _as_parameter(
        label: str, value: float | Sequence[float], size: int,
        *, positive: bool = False) -> tuple[float, ...]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        result = tuple(float(item) for item in value)
        if len(result) != size:
            raise ValueError(f"{label} must have {size} values")
    else:
        result = (float(value),) * size
    if not all(math.isfinite(item) for item in result):
        raise ValueError(f"{label} must be finite")
    if positive and not all(item > 0.0 for item in result):
        raise ValueError(f"{label} must be strictly positive")
    return result


_BASE_VALID_RULES = {
    "required",
    "value",
    "binary",
    "one_hot",
    "bounded_0_1",
    "bounded_minus1_1",
    "nonnegative",
    "positive",
}
_MASK_SEPARATORS = (
    "_masked_by_all:",
    "_masked_by_any:",
    "_masked_by:",
)


def _parse_valid_rule(rule: str) -> tuple[str, str | None, tuple[str, ...]]:
    for separator in _MASK_SEPARATORS:
        if separator in rule:
            base, references = rule.split(separator, maxsplit=1)
            refs = tuple(reference for reference in references.split("|")
                         if reference)
            mode = separator.removeprefix("_masked_by").removesuffix(":")
            mode = {"": "one", "_all": "all", "_any": "any"}.get(
                mode, mode)
            if base not in _BASE_VALID_RULES - {"required", "one_hot"}:
                raise ValueError(f"unsupported masked valid rule: {rule}")
            if not refs:
                raise ValueError(f"masked valid rule has no reference: {rule}")
            return base, mode, refs
    if rule not in _BASE_VALID_RULES:
        raise ValueError(f"unsupported valid rule: {rule}")
    return rule, None, ()


@dataclass(frozen=True)
class EncodingField:
    """One immutable, contiguous field in an encoded tensor ABI.

    ``center`` and ``scale`` are expressed in the raw unit.  ``clip`` applies
    after ``(raw - center) / scale``.  A masked field must reference one or
    more scalar binary fields in the same block.
    """

    name: str
    offset: int
    size: int
    unit: str
    coordinate_frame: str
    center: float | tuple[float, ...] = 0.0
    scale: float | tuple[float, ...] = 1.0
    clip: tuple[float, float] = (-1.0, 1.0)
    valid_rule: str = "required"
    invalid_fill_rule: str = "auto"
    dtype: str = "float32"
    components: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("field name must not be empty")
        if isinstance(self.offset, bool) or not isinstance(self.offset, int):
            raise ValueError("field offset must be an integer")
        if self.offset < 0:
            raise ValueError("field offset must be non-negative")
        if isinstance(self.size, bool) or not isinstance(self.size, int):
            raise ValueError("field size must be an integer")
        if self.size <= 0:
            raise ValueError("field size must be positive")
        if not self.unit or not self.coordinate_frame:
            raise ValueError("field unit and coordinate_frame are required")
        if self.dtype != "float32":
            raise ValueError("context encoding fields must use float32")
        components = tuple(str(value) for value in self.components)
        if self.size > 1:
            if (len(components) != self.size
                    or any(not value for value in components)
                    or len(set(components)) != len(components)):
                raise ValueError(
                    f"{self.name}.components must name all {self.size} "
                    "ordered elements")
        elif components and (len(components) != 1 or not components[0]):
            raise ValueError(
                f"{self.name}.components must be empty or contain one name")
        object.__setattr__(self, "components", components)
        center = _as_parameter(f"{self.name}.center", self.center, self.size)
        scale = _as_parameter(
            f"{self.name}.scale", self.scale, self.size, positive=True)
        object.__setattr__(self, "center", center)
        object.__setattr__(self, "scale", scale)

        if len(self.clip) != 2:
            raise ValueError(f"{self.name}.clip must be (low, high)")
        low, high = (float(self.clip[0]), float(self.clip[1]))
        if not math.isfinite(low) or not math.isfinite(high) or low >= high:
            raise ValueError(f"{self.name}.clip must be finite and increasing")
        object.__setattr__(self, "clip", (low, high))

        _, mask_mode, _ = _parse_valid_rule(self.valid_rule)
        expected_fill = "zero" if mask_mode is not None else "reject"
        if self.invalid_fill_rule == "auto":
            object.__setattr__(self, "invalid_fill_rule", expected_fill)
        elif self.invalid_fill_rule != expected_fill:
            raise ValueError(
                f"{self.name}.invalid_fill_rule must be {expected_fill!r}")

    @property
    def stop(self) -> int:
        return self.offset + self.size

    def payload(self) -> dict[str, object]:
        return {
            "name": self.name,
            "offset": self.offset,
            "size": self.size,
            "unit": self.unit,
            "coordinate_frame": self.coordinate_frame,
            "dtype": self.dtype,
            "normalization_center": list(self.center),
            "normalization_scale": list(self.scale),
            "clip": list(self.clip),
            "valid_rule": self.valid_rule,
            "invalid_fill_rule": self.invalid_fill_rule,
            "components": list(self.components),
        }


@dataclass(frozen=True)
class EncodingBlockManifest:
    """Immutable and hashable contiguous tensor layout."""

    name: str
    dimension: int
    fields: tuple[EncodingField, ...]
    schema_version: int = 1

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("block manifest name must not be empty")
        if self.schema_version != 1:
            raise ValueError("only encoding schema version 1 is supported")
        if isinstance(self.dimension, bool) or not isinstance(
                self.dimension, int) or self.dimension <= 0:
            raise ValueError("block dimension must be a positive integer")
        fields = tuple(self.fields)
        if not fields:
            raise ValueError("block manifest must contain fields")
        object.__setattr__(self, "fields", fields)

        cursor = 0
        names: set[str] = set()
        for field in fields:
            if field.name in names:
                raise ValueError(f"duplicate field name: {field.name}")
            names.add(field.name)
            if field.offset != cursor:
                raise ValueError(
                    f"{field.name} starts at {field.offset}; expected {cursor}")
            cursor = field.stop
        if cursor != self.dimension:
            raise ValueError(
                f"{self.name} fields end at {cursor}; expected {self.dimension}")

        lookup = {field.name: field for field in fields}
        for field in fields:
            _, mask_mode, references = _parse_valid_rule(field.valid_rule)
            if mask_mode is None:
                continue
            for reference in references:
                if reference not in lookup:
                    raise ValueError(
                        f"{field.name} references missing validity field "
                        f"{reference!r}")
                valid_field = lookup[reference]
                valid_base, valid_mask_mode, _ = _parse_valid_rule(
                    valid_field.valid_rule)
                if (valid_field.size != 1 or valid_base != "binary"
                        or valid_mask_mode is not None):
                    raise ValueError(
                        f"{field.name} validity reference {reference!r} must "
                        "be an unmasked scalar binary field")

    def field(self, name: str) -> EncodingField:
        for field in self.fields:
            if field.name == name:
                return field
        raise KeyError(name)

    def slice(self, name: str) -> slice:
        field = self.field(name)
        return slice(field.offset, field.stop)

    def payload(self) -> dict[str, object]:
        return {
            "name": self.name,
            "dimension": self.dimension,
            "schema_version": self.schema_version,
            "fields": [field.payload() for field in self.fields],
        }

    def sha256(self) -> str:
        canonical = json.dumps(
            self.payload(), sort_keys=True, separators=(",", ":"),
            ensure_ascii=True).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()


class _Layout:
    def __init__(self) -> None:
        self.offset = 0
        self.fields: list[EncodingField] = []

    def add(
            self, name: str, size: int, *, unit: str = "1",
            frame: str = "none", center: float = 0.0,
            scale: float = 1.0, clip: tuple[float, float] = (-1.0, 1.0),
            valid_rule: str = "required",
            components: Sequence[str] = ()) -> None:
        self.fields.append(EncodingField(
            name=name,
            offset=self.offset,
            size=size,
            unit=unit,
            coordinate_frame=frame,
            center=center,
            scale=scale,
            clip=clip,
            valid_rule=valid_rule,
            components=tuple(components),
        ))
        self.offset += size

    def finish(self, name: str, dimension: int) -> EncodingBlockManifest:
        return EncodingBlockManifest(name, dimension, tuple(self.fields))


def _readiness_manifest() -> EncodingBlockManifest:
    layout = _Layout()
    layout.add("phase", 5, unit="category", valid_rule="one_hot",
               clip=(0.0, 1.0), components=(
                   "PREPARE", "APPROACH", "STRIKE", "HOLD", "RECOVER"))
    for name in (
            "fret_global_ready", "strike_ready", "guitar_stable",
            "strike_permission", "deadline_missed", "recovery_active",
            "action_history_valid"):
        layout.add(name, 1, unit="bool", valid_rule="binary",
                   clip=(0.0, 1.0))
    for name in (
            "fret_ready_dwell_fraction", "strike_ready_dwell_fraction",
            "guitar_stable_dwell_fraction"):
        layout.add(name, 1, unit="fraction", valid_rule="bounded_0_1",
                   clip=(0.0, 1.0))

    for string in STRING_KEYS:
        valid = f"{string}.measurement_valid"
        layout.add(f"{string}.press_required", 1, unit="bool",
                   valid_rule="binary", clip=(0.0, 1.0))
        layout.add(valid, 1, unit="bool", valid_rule="binary",
                   clip=(0.0, 1.0))
        layout.add(
            f"{string}.press_quality", 1, unit="fraction",
            valid_rule=f"bounded_0_1_masked_by:{valid}", clip=(0.0, 1.0))
        layout.add(
            f"{string}.assigned_finger_correct", 1, unit="bool",
            valid_rule=f"binary_masked_by:{valid}", clip=(0.0, 1.0))
        layout.add(
            f"{string}.ready_dwell_fraction", 1, unit="fraction",
            valid_rule=f"bounded_0_1_masked_by:{valid}", clip=(0.0, 1.0))

    pick_valid = "pick_geometry_valid"
    layout.add(pick_valid, 1, unit="bool", valid_rule="binary",
               clip=(0.0, 1.0))
    layout.add(
        "pick_to_entry_G", 3, unit="m", frame="guitar_G", scale=0.20,
        valid_rule=f"value_masked_by:{pick_valid}",
        components=("x_G", "y_G", "z_G"))
    layout.add(
        "pick_to_exit_G", 3, unit="m", frame="guitar_G", scale=0.20,
        valid_rule=f"value_masked_by:{pick_valid}",
        components=("x_G", "y_G", "z_G"))
    layout.add(
        "pick_relative_velocity_G", 3, unit="m/s", frame="guitar_G",
        scale=2.0, valid_rule=f"value_masked_by:{pick_valid}",
        components=("vx_G", "vy_G", "vz_G"))
    layout.add(
        "target_lane_error", 1, unit="m", frame="guitar_G", scale=0.03,
        valid_rule=f"value_masked_by:{pick_valid}")
    layout.add(
        "traversal_direction_speed", 1, unit="m/s", frame="guitar_G",
        scale=2.0, valid_rule=f"value_masked_by:{pick_valid}")
    layout.add(
        "clearance_margin", 1, unit="m", frame="guitar_G", scale=0.05,
        valid_rule=f"value_masked_by:{pick_valid}")
    layout.add("detector_armed", 6, unit="bool", valid_rule="binary",
               clip=(0.0, 1.0), components=STRING_KEYS)
    return layout.finish("action_residual.readiness.v1", READINESS_DIM)


READINESS_MANIFEST = _readiness_manifest()


def _guitar_manifest() -> EncodingBlockManifest:
    layout = _Layout()
    layout.add("pose_valid", 1, unit="bool", valid_rule="binary",
               clip=(0.0, 1.0))
    layout.add("twist_valid", 1, unit="bool", valid_rule="binary",
               clip=(0.0, 1.0))
    layout.add(
        "position_error_B", 3, unit="m", frame="support_B", scale=0.20,
        valid_rule="value_masked_by:pose_valid",
        components=("x_B", "y_B", "z_B"))
    layout.add(
        "orientation_error_6d_B", 6, unit="1", frame="support_B",
        scale=2.0, valid_rule="value_masked_by:pose_valid",
        components=("r1x", "r1y", "r1z", "r2x", "r2y", "r2z"))
    layout.add(
        "linear_velocity_B", 3, unit="m/s", frame="support_B", scale=0.5,
        valid_rule="value_masked_by:twist_valid",
        components=("vx_B", "vy_B", "vz_B"))
    layout.add(
        "angular_velocity_B", 3, unit="rad/s", frame="support_B", scale=5.0,
        valid_rule="value_masked_by:twist_valid",
        components=("wx_B", "wy_B", "wz_B"))
    layout.add(
        "gravity_direction_G", 3, unit="unit_vector", frame="guitar_G",
        valid_rule="value_masked_by:pose_valid",
        components=("gx_G", "gy_G", "gz_G"))
    for name, valid in (
            ("position_drop_safety_margin", "pose_valid"),
            ("tilt_safety_margin", "pose_valid"),
            ("linear_speed_safety_margin", "twist_valid"),
            ("angular_speed_safety_margin", "twist_valid")):
        layout.add(
            name, 1, unit="fraction", clip=(0.0, 1.0),
            valid_rule=f"bounded_0_1_masked_by:{valid}")

    site_contact_valid_names = []
    for site in SUPPORT_SITE_KEYS:
        prefix = f"support.{site}"
        kinematics_valid = f"{prefix}.kinematics_valid"
        contact_valid = f"{prefix}.contact_valid"
        site_contact_valid_names.append(contact_valid)
        layout.add(kinematics_valid, 1, unit="bool", valid_rule="binary",
                   clip=(0.0, 1.0))
        layout.add(
            f"{prefix}.anchor_position_error_G", 3, unit="m",
            frame="guitar_G", scale=0.20,
            valid_rule=f"value_masked_by:{kinematics_valid}",
            components=("x_G", "y_G", "z_G"))
        layout.add(
            f"{prefix}.relative_velocity_G", 3, unit="m/s",
            frame="guitar_G", scale=0.5,
            valid_rule=f"value_masked_by:{kinematics_valid}",
            components=("vx_G", "vy_G", "vz_G"))
        layout.add(contact_valid, 1, unit="bool", valid_rule="binary",
                   clip=(0.0, 1.0))
        layout.add(
            f"{prefix}.normal_load_proxy", 1, unit="N", frame="support_normal",
            scale=100.0, clip=(-1.0, 2.0),
            valid_rule=f"nonnegative_masked_by:{contact_valid}")
        layout.add(
            f"{prefix}.tangential_load_proxy", 1, unit="N",
            frame="support_tangent", scale=100.0,
            valid_rule=f"value_masked_by:{contact_valid}")
        layout.add(
            f"{prefix}.slip_speed", 1, unit="m/s", frame="support_tangent",
            scale=0.5, clip=(0.0, 2.0),
            valid_rule=f"nonnegative_masked_by:{contact_valid}")
        layout.add(
            f"{prefix}.friction_reserve", 1, unit="N",
            frame="support_tangent", scale=100.0, clip=(-2.0, 2.0),
            valid_rule=f"value_masked_by:{contact_valid}")
        layout.add(
            f"{prefix}.contact_on", 1, unit="bool", clip=(0.0, 1.0),
            valid_rule=f"binary_masked_by:{contact_valid}")

    aggregate_valid = "aggregate.contact_valid"
    layout.add(aggregate_valid, 1, unit="bool", valid_rule="binary",
               clip=(0.0, 1.0))
    aggregate_mask = f"value_masked_by:{aggregate_valid}"
    aggregate_nonnegative = f"nonnegative_masked_by:{aggregate_valid}"
    layout.add("aggregate.total_normal_load", 1, unit="N", scale=100.0,
               clip=(0.0, 5.0), valid_rule=aggregate_nonnegative)
    layout.add("aggregate.net_tangential_force_G", 3, unit="N",
               frame="guitar_G", scale=100.0, valid_rule=aggregate_mask,
               components=("fx_G", "fy_G", "fz_G"))
    layout.add("aggregate.net_contact_torque_G", 3, unit="N*m",
               frame="guitar_G", scale=20.0, valid_rule=aggregate_mask,
               components=("tx_G", "ty_G", "tz_G"))
    layout.add("aggregate.center_of_pressure_xy_G", 2, unit="m",
               frame="guitar_G", scale=0.20, valid_rule=aggregate_mask,
               components=("x_G", "y_G"))
    layout.add("aggregate.support_polygon_margin", 1, unit="m",
               frame="guitar_G", scale=0.20, valid_rule=aggregate_mask)
    layout.add("aggregate.overforce_margin", 1, unit="N", scale=100.0,
               clip=(-2.0, 2.0), valid_rule=aggregate_mask)
    layout.add("aggregate.global_slip_margin", 1, unit="m/s", scale=0.5,
               clip=(-2.0, 2.0), valid_rule=aggregate_mask)
    layout.add("aggregate.guitar_stable_dwell_fraction", 1, unit="fraction",
               clip=(0.0, 1.0), valid_rule="bounded_0_1")
    layout.add("aggregate.post_impact_grace_fraction", 1, unit="fraction",
               clip=(0.0, 1.0), valid_rule="bounded_0_1")

    layout.add("guitar_mode", 3, unit="category", valid_rule="one_hot",
               clip=(0.0, 1.0),
               components=("FIXED", "HAND_ASSISTED", "FREE"))
    layout.add("assist_lambda", 1, unit="fraction", clip=(0.0, 1.0),
               valid_rule="bounded_0_1_masked_by:assist_state_valid")
    layout.add("assist_transition_blend", 1, unit="fraction",
               clip=(0.0, 1.0),
               valid_rule="bounded_0_1_masked_by:assist_state_valid")
    layout.add("assist_state_valid", 1, unit="bool", valid_rule="binary",
               clip=(0.0, 1.0))
    for tether in TETHER_KEYS:
        prefix = f"tether.{tether}"
        valid = f"{prefix}.valid"
        mask_refs = f"{valid}|assist_state_valid"
        layout.add(valid, 1, unit="bool", valid_rule="binary",
                   clip=(0.0, 1.0))
        layout.add(f"{prefix}.extension_G", 3, unit="m", frame="guitar_G",
                   scale=0.10,
                   valid_rule=f"value_masked_by_all:{mask_refs}",
                   components=("x_G", "y_G", "z_G"))
        layout.add(f"{prefix}.relative_velocity_G", 3, unit="m/s",
                   frame="guitar_G", scale=0.5,
                   valid_rule=f"value_masked_by_all:{mask_refs}",
                   components=("vx_G", "vy_G", "vz_G"))
        layout.add(f"{prefix}.tension_cap_fraction", 1, unit="fraction",
                   clip=(0.0, 1.0),
                   valid_rule=f"bounded_0_1_masked_by_all:{mask_refs}")
        layout.add(f"{prefix}.artificial_power_fraction", 1, unit="fraction",
                   valid_rule=f"bounded_minus1_1_masked_by_all:{mask_refs}")
    return layout.finish(
        "action_residual.guitar_support.v1", GUITAR_SUPPORT_DIM)


GUITAR_SUPPORT_MANIFEST = _guitar_manifest()


def _privileged_manifest() -> EncodingBlockManifest:
    layout = _Layout()
    layout.add("physics.log_guitar_mass_ratio", 1, unit="log_ratio",
               clip=(-5.0, 5.0))
    layout.add("physics.center_of_mass_G", 3, unit="m", frame="guitar_G",
               scale=0.20, components=("x_G", "y_G", "z_G"))
    layout.add("physics.inertia_symmetric", 6, unit="kg*m^2", frame="guitar_G",
               scale=0.10, clip=(-5.0, 5.0),
               components=("Ixx", "Iyy", "Izz", "Ixy", "Ixz", "Iyz"))
    layout.add("physics.linear_damping", 1, unit="1/s", scale=10.0,
               clip=(0.0, 5.0), valid_rule="nonnegative")
    layout.add("physics.angular_damping", 1, unit="1/s", scale=10.0,
               clip=(0.0, 5.0), valid_rule="nonnegative")
    layout.add("physics.support_friction", 5, unit="coefficient",
               clip=(0.0, 3.0), valid_rule="nonnegative",
               components=SUPPORT_SITE_KEYS)
    layout.add("physics.contact_stiffness", 1, unit="N/m", scale=100000.0,
               clip=(0.0, 5.0), valid_rule="nonnegative")
    layout.add("physics.contact_damping", 1, unit="N*s/m", scale=1000.0,
               clip=(0.0, 5.0), valid_rule="nonnegative")
    layout.add("physics.guitar_geometry_scale_xyz", 3, unit="ratio",
               center=1.0, scale=0.5, valid_rule="positive",
               components=("x", "y", "z"))
    layout.add("physics.gravity_magnitude_ratio", 1, unit="ratio", center=1.0,
               scale=0.25, valid_rule="positive")
    layout.add("physics.restitution", 1, unit="coefficient",
               valid_rule="bounded_0_1", clip=(0.0, 1.0))

    for site in SUPPORT_SITE_KEYS:
        prefix = f"contact.{site}"
        valid = f"{prefix}.pair_valid"
        layout.add(valid, 1, unit="bool", valid_rule="binary",
                   clip=(0.0, 1.0))
        layout.add(f"{prefix}.point_G", 3, unit="m", frame="guitar_G",
                   scale=0.50, valid_rule=f"value_masked_by:{valid}",
                   components=("x_G", "y_G", "z_G"))
        layout.add(f"{prefix}.force_G", 3, unit="N", frame="guitar_G",
                   scale=100.0, clip=(-5.0, 5.0),
                   valid_rule=f"value_masked_by:{valid}",
                   components=("fx_G", "fy_G", "fz_G"))
        layout.add(f"{prefix}.relative_tangent_velocity_G", 3, unit="m/s",
                   frame="guitar_G", scale=0.5, clip=(-2.0, 2.0),
                   valid_rule=f"value_masked_by:{valid}",
                   components=("vx_G", "vy_G", "vz_G"))
        layout.add(f"{prefix}.penetration_depth", 1, unit="m", scale=0.01,
                   clip=(0.0, 5.0),
                   valid_rule=f"nonnegative_masked_by:{valid}")
        layout.add(f"{prefix}.true_friction_utilization", 1, unit="ratio",
                   clip=(0.0, 3.0),
                   valid_rule=f"nonnegative_masked_by:{valid}")

    for tether in TETHER_KEYS:
        prefix = f"exact_tether.{tether}"
        valid = f"{prefix}.valid"
        layout.add(valid, 1, unit="bool", valid_rule="binary",
                   clip=(0.0, 1.0))
        layout.add(f"{prefix}.extension_G", 3, unit="m", frame="guitar_G",
                   scale=0.10, valid_rule=f"value_masked_by:{valid}",
                   components=("x_G", "y_G", "z_G"))
        layout.add(f"{prefix}.force_G", 3, unit="N", frame="guitar_G",
                   scale=100.0, clip=(-5.0, 5.0),
                   valid_rule=f"value_masked_by:{valid}",
                   components=("fx_G", "fy_G", "fz_G"))
        layout.add(f"{prefix}.torque_G", 3, unit="N*m", frame="guitar_G",
                   scale=20.0, clip=(-5.0, 5.0),
                   valid_rule=f"value_masked_by:{valid}",
                   components=("tx_G", "ty_G", "tz_G"))
        layout.add(f"{prefix}.mechanical_work_rate", 1, unit="W", scale=100.0,
                   clip=(-5.0, 5.0), valid_rule=f"value_masked_by:{valid}")
        layout.add(f"{prefix}.saturation_fraction", 1, unit="fraction",
                   clip=(0.0, 1.0),
                   valid_rule=f"bounded_0_1_masked_by:{valid}")

    layout.add("domain.external_disturbance_force", 3, unit="N",
               frame="world", scale=100.0, clip=(-5.0, 5.0),
               components=("fx_W", "fy_W", "fz_W"))
    layout.add("domain.external_disturbance_torque", 3, unit="N*m",
               frame="world", scale=20.0, clip=(-5.0, 5.0),
               components=("tx_W", "ty_W", "tz_W"))
    layout.add("domain.reset_position_offset", 3, unit="m", frame="support_B",
               scale=0.20, clip=(-2.0, 2.0),
               components=("x_B", "y_B", "z_B"))
    layout.add("domain.reset_rotation_log", 3, unit="rad", frame="support_B",
               scale=math.pi, components=("rx_B", "ry_B", "rz_B"))
    layout.add("domain.initial_linear_velocity", 3, unit="m/s",
               frame="support_B", scale=0.5, clip=(-2.0, 2.0),
               components=("vx_B", "vy_B", "vz_B"))
    layout.add("domain.initial_angular_velocity", 3, unit="rad/s",
               frame="support_B", scale=5.0, clip=(-2.0, 2.0),
               components=("wx_B", "wy_B", "wz_B"))
    layout.add("domain.curriculum_difficulty", 1, unit="fraction",
               valid_rule="bounded_0_1", clip=(0.0, 1.0))
    layout.add("domain.assist_randomization_severity", 1, unit="fraction",
               valid_rule="bounded_0_1", clip=(0.0, 1.0))
    return layout.finish("action_residual.privileged.v1", PRIVILEGED_DIM)


PRIVILEGED_MANIFEST = _privileged_manifest()


def _binary_mask(name: str, tensor: torch.Tensor) -> torch.Tensor:
    if not torch.isfinite(tensor).all():
        raise ValueError(f"{name} must be finite")
    close_zero = torch.isclose(tensor, torch.zeros_like(tensor), atol=1e-6,
                               rtol=0.0)
    close_one = torch.isclose(tensor, torch.ones_like(tensor), atol=1e-6,
                              rtol=0.0)
    if not bool((close_zero | close_one).all()):
        raise ValueError(f"{name} must contain only binary 0/1 values")
    return close_one


class FixedScaleTensorBuilder:
    """Pack an exact field mapping using an :class:`EncodingBlockManifest`."""

    def __init__(self, manifest: EncodingBlockManifest) -> None:
        self.manifest = manifest

    def pack(self, values: Mapping[str, torch.Tensor]) -> torch.Tensor:
        expected = {field.name for field in self.manifest.fields}
        actual = set(values)
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        if missing or extra:
            raise ValueError(
                f"{self.manifest.name} field mismatch; missing={missing}, "
                f"extra={extra}")

        first = next(iter(values.values()), None)
        if not isinstance(first, torch.Tensor):
            raise TypeError("encoded values must be torch.Tensor instances")
        if first.ndim not in (1, 2):
            raise ValueError("encoded fields must have a batch dimension")
        batch = first.shape[0]
        device = first.device
        raw: dict[str, torch.Tensor] = {}
        for field in self.manifest.fields:
            value = values[field.name]
            if not isinstance(value, torch.Tensor):
                raise TypeError(f"{field.name} must be a torch.Tensor")
            if value.device != device:
                raise ValueError("all encoded fields must be on the same device")
            if field.size == 1 and value.shape == (batch,):
                value = value.unsqueeze(-1)
            if value.shape != (batch, field.size):
                raise ValueError(
                    f"{field.name} must have shape {(batch, field.size)}, got "
                    f"{tuple(value.shape)}")
            raw[field.name] = value.to(dtype=torch.float32)

        binary_masks: dict[str, torch.Tensor] = {}
        for field in self.manifest.fields:
            base_rule, _, _ = _parse_valid_rule(field.valid_rule)
            if base_rule == "binary" and "_masked_by" not in field.valid_rule:
                binary_masks[field.name] = _binary_mask(
                    field.name, raw[field.name])

        encoded: list[torch.Tensor] = []
        for field in self.manifest.fields:
            base_rule, mask_mode, references = _parse_valid_rule(
                field.valid_rule)
            value = raw[field.name]
            if mask_mode is None:
                valid = torch.ones(
                    batch, 1, dtype=torch.bool, device=device)
            else:
                masks = [binary_masks[reference] for reference in references]
                valid = masks[0]
                for mask in masks[1:]:
                    if mask_mode == "all":
                        valid = valid & mask
                    elif mask_mode == "any":
                        valid = valid | mask
                    else:
                        raise AssertionError("single validity rule has >1 reference")
            valid = valid.expand(-1, field.size)

            if not bool(torch.isfinite(value[valid]).all()):
                raise ValueError(
                    f"{field.name} contains nonfinite values while valid")
            safe = torch.where(valid, value, torch.zeros_like(value))

            if base_rule == "binary":
                _binary_mask(field.name, safe[valid].reshape(-1, 1))
                safe = torch.where(
                    torch.isclose(safe, torch.ones_like(safe), atol=1e-6,
                                  rtol=0.0),
                    torch.ones_like(safe), torch.zeros_like(safe))
            elif base_rule == "one_hot":
                _binary_mask(field.name, safe)
                if not bool(torch.isclose(
                        safe.sum(dim=-1), torch.ones(batch, device=device),
                        atol=1e-6, rtol=0.0).all()):
                    raise ValueError(f"{field.name} must be exactly one-hot")
            elif base_rule in ("bounded_0_1", "bounded_minus1_1"):
                low, high = ((0.0, 1.0) if base_rule == "bounded_0_1"
                             else (-1.0, 1.0))
                if not bool(((safe[valid] >= low - 1e-6)
                             & (safe[valid] <= high + 1e-6)).all()):
                    raise ValueError(
                        f"{field.name} must be in [{low}, {high}] while valid")
                safe = safe.clamp(low, high)
            elif base_rule in ("nonnegative", "positive"):
                boundary = 0.0
                if base_rule == "nonnegative":
                    valid_range = safe[valid] >= boundary - 1e-6
                else:
                    valid_range = safe[valid] > boundary
                if not bool(valid_range.all()):
                    qualifier = (
                        "non-negative" if base_rule == "nonnegative"
                        else "strictly positive")
                    raise ValueError(
                        f"{field.name} must be {qualifier} while valid")
                if base_rule == "nonnegative":
                    safe = safe.clamp_min(0.0)
            elif base_rule not in ("required", "value"):
                raise AssertionError(base_rule)

            center = torch.tensor(
                field.center, dtype=torch.float32, device=device).unsqueeze(0)
            scale = torch.tensor(
                field.scale, dtype=torch.float32, device=device).unsqueeze(0)
            normalized = ((safe - center) / scale).clamp(*field.clip)
            if mask_mode is not None:
                normalized = torch.where(
                    valid, normalized, torch.zeros_like(normalized))
            if not bool(torch.isfinite(normalized).all()):
                raise ValueError(f"{field.name} produced nonfinite encoding")
            if not bool(((normalized >= field.clip[0] - 1e-6)
                         & (normalized <= field.clip[1] + 1e-6)).all()):
                raise ValueError(f"{field.name} escaped its encoded range")
            encoded.append(normalized)

        result = torch.cat(encoded, dim=-1).contiguous()
        if result.shape != (batch, self.manifest.dimension):
            raise AssertionError("encoded block dimension contract was violated")
        return result


@dataclass(frozen=True)
class ReadinessEncodingInput:
    phase: torch.Tensor
    fret_global_ready: torch.Tensor
    strike_ready: torch.Tensor
    guitar_stable: torch.Tensor
    strike_permission: torch.Tensor
    deadline_missed: torch.Tensor
    strike_window_open: torch.Tensor
    recovery_active: torch.Tensor
    action_history_valid: torch.Tensor
    dwell_fractions: torch.Tensor
    press_required: torch.Tensor
    measurement_valid: torch.Tensor
    press_quality: torch.Tensor
    assigned_finger_correct: torch.Tensor
    ready_dwell_fraction: torch.Tensor
    pick_geometry_valid: torch.Tensor
    pick_to_entry_g: torch.Tensor
    pick_to_exit_g: torch.Tensor
    pick_relative_velocity_g: torch.Tensor
    target_lane_error: torch.Tensor
    traversal_direction_speed: torch.Tensor
    clearance_margin: torch.Tensor
    detector_armed: torch.Tensor


def _matrix_width(name: str, value: torch.Tensor, width: int) -> torch.Tensor:
    if not isinstance(value, torch.Tensor):
        raise TypeError(f"{name} must be a torch.Tensor")
    if value.ndim != 2 or value.shape[1] != width:
        raise ValueError(f"{name} must have shape [batch, {width}]")
    return value


def _binary_column(
        name: str, value: torch.Tensor, batch: int) -> torch.Tensor:
    if not isinstance(value, torch.Tensor):
        raise TypeError(f"{name} must be a torch.Tensor")
    if value.shape == (batch,):
        value = value.unsqueeze(-1)
    if value.shape != (batch, 1):
        raise ValueError(f"{name} must have shape [batch] or [batch, 1]")
    return _binary_mask(name, value)


class ReadinessPacker:
    manifest = READINESS_MANIFEST

    def __init__(self) -> None:
        self._builder = FixedScaleTensorBuilder(self.manifest)

    def pack(self, data: ReadinessEncodingInput) -> torch.Tensor:
        _matrix_width("phase", data.phase, 5)
        _matrix_width("dwell_fractions", data.dwell_fractions, 3)
        for name in (
                "press_required", "measurement_valid", "press_quality",
                "assigned_finger_correct", "ready_dwell_fraction",
                "detector_armed"):
            _matrix_width(name, getattr(data, name), 6)
        for name in (
                "pick_to_entry_g", "pick_to_exit_g",
                "pick_relative_velocity_g"):
            _matrix_width(name, getattr(data, name), 3)

        values: dict[str, torch.Tensor] = {
            "phase": data.phase,
            "fret_global_ready": data.fret_global_ready,
            "strike_ready": data.strike_ready,
            "guitar_stable": data.guitar_stable,
            "strike_permission": data.strike_permission,
            "deadline_missed": data.deadline_missed,
            "recovery_active": data.recovery_active,
            "action_history_valid": data.action_history_valid,
            "fret_ready_dwell_fraction": data.dwell_fractions[:, 0],
            "strike_ready_dwell_fraction": data.dwell_fractions[:, 1],
            "guitar_stable_dwell_fraction": data.dwell_fractions[:, 2],
        }
        for index, string in enumerate(STRING_KEYS):
            values.update({
                f"{string}.press_required": data.press_required[:, index],
                f"{string}.measurement_valid": data.measurement_valid[:, index],
                f"{string}.press_quality": data.press_quality[:, index],
                f"{string}.assigned_finger_correct":
                    data.assigned_finger_correct[:, index],
                f"{string}.ready_dwell_fraction":
                    data.ready_dwell_fraction[:, index],
            })
        values.update({
            "pick_geometry_valid": data.pick_geometry_valid,
            "pick_to_entry_G": data.pick_to_entry_g,
            "pick_to_exit_G": data.pick_to_exit_g,
            "pick_relative_velocity_G": data.pick_relative_velocity_g,
            "target_lane_error": data.target_lane_error,
            "traversal_direction_speed": data.traversal_direction_speed,
            "clearance_margin": data.clearance_margin,
            "detector_armed": data.detector_armed,
        })
        result = self._builder.pack(values)

        fret_ready = result[:, self.manifest.slice("fret_global_ready")]
        strike_ready = result[:, self.manifest.slice("strike_ready")]
        guitar_stable = result[:, self.manifest.slice("guitar_stable")]
        permission = result[:, self.manifest.slice("strike_permission")]
        deadline = result[:, self.manifest.slice("deadline_missed")]
        recovery = result[:, self.manifest.slice("recovery_active")]
        window_open = _binary_column(
            "strike_window_open", data.strike_window_open,
            result.shape[0]).to(dtype=torch.float32)
        expected_permission = (
                fret_ready * strike_ready * guitar_stable * window_open
                * (1.0 - deadline) * (1.0 - recovery))
        if not torch.equal(permission, expected_permission):
            raise ValueError(
                "strike_permission must exactly equal the readiness/window/"
                "deadline/recovery gate")

        required = _binary_mask("press_required", data.press_required)
        measured = _binary_mask("measurement_valid", data.measurement_valid)
        fret_ready_bool = fret_ready.reshape(-1) > 0.5
        if bool(((required & ~measured).any(dim=-1)
                 & fret_ready_bool).any()):
            raise ValueError(
                "fret_global_ready cannot be true with an unmeasured "
                "required string")
        pick_valid = _binary_column(
            "pick_geometry_valid", data.pick_geometry_valid,
            result.shape[0]).reshape(-1)
        if bool(((strike_ready.reshape(-1) > 0.5) & ~pick_valid).any()):
            raise ValueError(
                "strike_ready cannot be true when pick geometry is invalid")
        fret_dwell = result[:, self.manifest.slice(
            "fret_ready_dwell_fraction")].reshape(-1)
        guitar_dwell = result[:, self.manifest.slice(
            "guitar_stable_dwell_fraction")].reshape(-1)
        if bool((fret_ready_bool & (fret_dwell < 1.0 - 1e-6)).any()):
            raise ValueError("fret_global_ready requires completed fret dwell")
        if bool(((guitar_stable.reshape(-1) > 0.5)
                 & (guitar_dwell < 1.0 - 1e-6)).any()):
            raise ValueError("guitar_stable requires completed stable dwell")
        return result


@dataclass(frozen=True)
class JointHistoryEncodingInput:
    q: torch.Tensor
    qdot: torch.Tensor
    previous_executed_action: torch.Tensor
    previous_residual_ratio: torch.Tensor
    residual_rate_ratio: torch.Tensor
    effective_authority: torch.Tensor


JOINT_FEATURE_NAMES = (
    "q",
    "qdot",
    "lower_limit_margin",
    "upper_limit_margin",
    "previous_executed_action",
    "previous_residual_ratio",
    "residual_rate_ratio",
    "effective_authority",
)


def build_joint_history_manifest(
        joint_names: Sequence[str], lower_limits: Sequence[float],
        upper_limits: Sequence[float],
        velocity_scales: Sequence[float]) -> EncodingBlockManifest:
    names = tuple(str(name) for name in joint_names)
    lower = tuple(float(value) for value in lower_limits)
    upper = tuple(float(value) for value in upper_limits)
    velocity = tuple(float(value) for value in velocity_scales)
    if len(names) != JOINT_COUNT or len(set(names)) != JOINT_COUNT:
        raise ValueError("joint_names must contain exactly 75 unique names")
    if not (len(lower) == len(upper) == len(velocity) == JOINT_COUNT):
        raise ValueError("joint limits and velocity scales must have 75 values")
    if not all(math.isfinite(lo) and math.isfinite(hi) and hi > lo
               for lo, hi in zip(lower, upper)):
        raise ValueError("every joint must have finite lower < upper limits")
    if not all(math.isfinite(value) and value > 0.0 for value in velocity):
        raise ValueError("every joint velocity scale must be finite and positive")

    layout = _Layout()
    for name, lo, hi, vmax in zip(names, lower, upper, velocity):
        midpoint = 0.5 * (lo + hi)
        half_range = 0.5 * (hi - lo)
        prefix = f"joint.{name}"
        layout.add(f"{prefix}.q", 1, unit="rad", frame="joint_local",
                   center=midpoint, scale=half_range)
        layout.add(f"{prefix}.qdot", 1, unit="rad/s", frame="joint_local",
                   scale=vmax)
        layout.add(f"{prefix}.lower_limit_margin", 1, unit="fraction",
                   valid_rule="bounded_0_1", clip=(0.0, 1.0))
        layout.add(f"{prefix}.upper_limit_margin", 1, unit="fraction",
                   valid_rule="bounded_0_1", clip=(0.0, 1.0))
        layout.add(f"{prefix}.previous_executed_action", 1,
                   unit="normalized_action", valid_rule="bounded_minus1_1")
        layout.add(f"{prefix}.previous_residual_ratio", 1,
                   unit="cap_fraction", valid_rule="bounded_minus1_1")
        layout.add(f"{prefix}.residual_rate_ratio", 1,
                   unit="rate_cap_fraction", valid_rule="bounded_minus1_1")
        layout.add(f"{prefix}.effective_authority", 1, unit="fraction",
                   valid_rule="bounded_0_1", clip=(0.0, 1.0))
    return layout.finish("action_residual.joint_history.v1", JOINT_HISTORY_DIM)


def _finite_matrix(name: str, value: torch.Tensor, width: int) -> torch.Tensor:
    value = _matrix_width(name, value, width)
    if not torch.isfinite(value).all():
        raise ValueError(f"{name} must be finite")
    return value.to(dtype=torch.float32)


def _bounded_matrix(
        name: str, value: torch.Tensor, low: float, high: float) -> torch.Tensor:
    value = _finite_matrix(name, value, JOINT_COUNT)
    if not bool(((value >= low - 1e-6) & (value <= high + 1e-6)).all()):
        raise ValueError(f"{name} must be in [{low}, {high}]")
    return value.clamp(low, high)


class JointHistoryPacker:
    """Vectorized 75 × 8 joint-major encoder."""

    def __init__(
            self, joint_names: Sequence[str], lower_limits: Sequence[float],
            upper_limits: Sequence[float],
            velocity_scales: Sequence[float]) -> None:
        self.joint_names = tuple(str(name) for name in joint_names)
        self.lower_limits = tuple(float(value) for value in lower_limits)
        self.upper_limits = tuple(float(value) for value in upper_limits)
        self.velocity_scales = tuple(float(value) for value in velocity_scales)
        self.manifest = build_joint_history_manifest(
            self.joint_names, self.lower_limits, self.upper_limits,
            self.velocity_scales)

    def pack(self, data: JointHistoryEncodingInput) -> torch.Tensor:
        q = _finite_matrix("q", data.q, JOINT_COUNT)
        tensors = (
            data.qdot, data.previous_executed_action,
            data.previous_residual_ratio, data.residual_rate_ratio,
            data.effective_authority,
        )
        if any(tensor.device != q.device for tensor in tensors):
            raise ValueError("all joint-history fields must be on the same device")
        qdot = _finite_matrix("qdot", data.qdot, JOINT_COUNT)
        previous_action = _bounded_matrix(
            "previous_executed_action", data.previous_executed_action, -1.0, 1.0)
        previous_residual = _bounded_matrix(
            "previous_residual_ratio", data.previous_residual_ratio, -1.0, 1.0)
        residual_rate = _bounded_matrix(
            "residual_rate_ratio", data.residual_rate_ratio, -1.0, 1.0)
        authority = _bounded_matrix(
            "effective_authority", data.effective_authority, 0.0, 1.0)

        lower = torch.tensor(
            self.lower_limits, dtype=torch.float32, device=q.device).unsqueeze(0)
        upper = torch.tensor(
            self.upper_limits, dtype=torch.float32, device=q.device).unsqueeze(0)
        velocity = torch.tensor(
            self.velocity_scales, dtype=torch.float32,
            device=q.device).unsqueeze(0)
        width = upper - lower
        q_normalized = (2.0 * (q - lower) / width - 1.0).clamp(-1.0, 1.0)
        qdot_normalized = (qdot / velocity).clamp(-1.0, 1.0)
        lower_margin = ((q - lower) / width).clamp(0.0, 1.0)
        upper_margin = ((upper - q) / width).clamp(0.0, 1.0)

        encoded = torch.stack((
            q_normalized,
            qdot_normalized,
            lower_margin,
            upper_margin,
            previous_action,
            previous_residual,
            residual_rate,
            authority,
        ), dim=-1).reshape(q.shape[0], JOINT_HISTORY_DIM).contiguous()
        if not torch.isfinite(encoded).all():
            raise AssertionError("joint-history encoding produced nonfinite values")
        return encoded


@dataclass(frozen=True)
class SupportSiteEncodingInput:
    anchor_position_error_g: torch.Tensor
    relative_velocity_g: torch.Tensor
    normal_load_proxy: torch.Tensor
    tangential_load_proxy: torch.Tensor
    slip_speed: torch.Tensor
    friction_reserve: torch.Tensor
    contact_on: torch.Tensor
    kinematics_valid: torch.Tensor
    contact_valid: torch.Tensor


@dataclass(frozen=True)
class AggregateSupportEncodingInput:
    contact_valid: torch.Tensor
    total_normal_load: torch.Tensor
    net_tangential_force_g: torch.Tensor
    net_contact_torque_g: torch.Tensor
    center_of_pressure_xy_g: torch.Tensor
    support_polygon_margin: torch.Tensor
    overforce_margin: torch.Tensor
    global_slip_margin: torch.Tensor
    guitar_stable_dwell_fraction: torch.Tensor
    post_impact_grace_fraction: torch.Tensor


@dataclass(frozen=True)
class TetherEncodingInput:
    valid: torch.Tensor
    extension_g: torch.Tensor
    relative_velocity_g: torch.Tensor
    tension_cap_fraction: torch.Tensor
    artificial_power_fraction: torch.Tensor


@dataclass(frozen=True)
class GuitarSupportEncodingInput:
    pose_valid: torch.Tensor
    twist_valid: torch.Tensor
    position_error_b: torch.Tensor
    orientation_error_6d_b: torch.Tensor
    linear_velocity_b: torch.Tensor
    angular_velocity_b: torch.Tensor
    gravity_direction_g: torch.Tensor
    safety_margins: torch.Tensor
    support_sites: Mapping[str, SupportSiteEncodingInput]
    aggregate: AggregateSupportEncodingInput
    guitar_mode: torch.Tensor
    assist_lambda: torch.Tensor
    assist_transition_blend: torch.Tensor
    assist_state_valid: torch.Tensor
    tethers: Mapping[str, TetherEncodingInput]


def _named_records(
        label: str, records: Mapping[str, object],
        expected: tuple[str, ...]) -> None:
    actual = set(records)
    target = set(expected)
    if actual != target:
        raise ValueError(
            f"{label} keys must be exactly {expected}; "
            f"missing={sorted(target - actual)}, extra={sorted(actual - target)}")


class GuitarSupportPacker:
    manifest = GUITAR_SUPPORT_MANIFEST

    def __init__(self) -> None:
        self._builder = FixedScaleTensorBuilder(self.manifest)

    def pack(self, data: GuitarSupportEncodingInput) -> torch.Tensor:
        _named_records("support_sites", data.support_sites, SUPPORT_SITE_KEYS)
        _named_records("tethers", data.tethers, TETHER_KEYS)
        _matrix_width("position_error_b", data.position_error_b, 3)
        _matrix_width("orientation_error_6d_b", data.orientation_error_6d_b, 6)
        _matrix_width("linear_velocity_b", data.linear_velocity_b, 3)
        _matrix_width("angular_velocity_b", data.angular_velocity_b, 3)
        _matrix_width("gravity_direction_g", data.gravity_direction_g, 3)
        _matrix_width("safety_margins", data.safety_margins, 4)
        _matrix_width("guitar_mode", data.guitar_mode, 3)

        values: dict[str, torch.Tensor] = {
            "pose_valid": data.pose_valid,
            "twist_valid": data.twist_valid,
            "position_error_B": data.position_error_b,
            "orientation_error_6d_B": data.orientation_error_6d_b,
            "linear_velocity_B": data.linear_velocity_b,
            "angular_velocity_B": data.angular_velocity_b,
            "gravity_direction_G": data.gravity_direction_g,
            "position_drop_safety_margin": data.safety_margins[:, 0],
            "tilt_safety_margin": data.safety_margins[:, 1],
            "linear_speed_safety_margin": data.safety_margins[:, 2],
            "angular_speed_safety_margin": data.safety_margins[:, 3],
        }
        for site_name in SUPPORT_SITE_KEYS:
            site = data.support_sites[site_name]
            _matrix_width(
                f"support_sites[{site_name}].anchor_position_error_g",
                site.anchor_position_error_g, 3)
            _matrix_width(
                f"support_sites[{site_name}].relative_velocity_g",
                site.relative_velocity_g, 3)
            prefix = f"support.{site_name}"
            values.update({
                f"{prefix}.kinematics_valid": site.kinematics_valid,
                f"{prefix}.anchor_position_error_G":
                    site.anchor_position_error_g,
                f"{prefix}.relative_velocity_G": site.relative_velocity_g,
                f"{prefix}.contact_valid": site.contact_valid,
                f"{prefix}.normal_load_proxy": site.normal_load_proxy,
                f"{prefix}.tangential_load_proxy": site.tangential_load_proxy,
                f"{prefix}.slip_speed": site.slip_speed,
                f"{prefix}.friction_reserve": site.friction_reserve,
                f"{prefix}.contact_on": site.contact_on,
            })

        aggregate = data.aggregate
        _matrix_width(
            "aggregate.net_tangential_force_g",
            aggregate.net_tangential_force_g, 3)
        _matrix_width(
            "aggregate.net_contact_torque_g",
            aggregate.net_contact_torque_g, 3)
        _matrix_width(
            "aggregate.center_of_pressure_xy_g",
            aggregate.center_of_pressure_xy_g, 2)
        values.update({
            "aggregate.contact_valid": aggregate.contact_valid,
            "aggregate.total_normal_load": aggregate.total_normal_load,
            "aggregate.net_tangential_force_G":
                aggregate.net_tangential_force_g,
            "aggregate.net_contact_torque_G": aggregate.net_contact_torque_g,
            "aggregate.center_of_pressure_xy_G":
                aggregate.center_of_pressure_xy_g,
            "aggregate.support_polygon_margin":
                aggregate.support_polygon_margin,
            "aggregate.overforce_margin": aggregate.overforce_margin,
            "aggregate.global_slip_margin": aggregate.global_slip_margin,
            "aggregate.guitar_stable_dwell_fraction":
                aggregate.guitar_stable_dwell_fraction,
            "aggregate.post_impact_grace_fraction":
                aggregate.post_impact_grace_fraction,
            "guitar_mode": data.guitar_mode,
            "assist_lambda": data.assist_lambda,
            "assist_transition_blend": data.assist_transition_blend,
            "assist_state_valid": data.assist_state_valid,
        })
        for tether_name in TETHER_KEYS:
            tether = data.tethers[tether_name]
            _matrix_width(
                f"tethers[{tether_name}].extension_g", tether.extension_g, 3)
            _matrix_width(
                f"tethers[{tether_name}].relative_velocity_g",
                tether.relative_velocity_g, 3)
            prefix = f"tether.{tether_name}"
            values.update({
                f"{prefix}.valid": tether.valid,
                f"{prefix}.extension_G": tether.extension_g,
                f"{prefix}.relative_velocity_G": tether.relative_velocity_g,
                f"{prefix}.tension_cap_fraction": tether.tension_cap_fraction,
                f"{prefix}.artificial_power_fraction":
                    tether.artificial_power_fraction,
            })
        return self._builder.pack(values)


@dataclass(frozen=True)
class ExactContactEncodingInput:
    pair_valid: torch.Tensor
    point_g: torch.Tensor
    force_g: torch.Tensor
    relative_tangent_velocity_g: torch.Tensor
    penetration_depth: torch.Tensor
    true_friction_utilization: torch.Tensor


@dataclass(frozen=True)
class ExactTetherEncodingInput:
    valid: torch.Tensor
    extension_g: torch.Tensor
    force_g: torch.Tensor
    torque_g: torch.Tensor
    mechanical_work_rate: torch.Tensor
    saturation_fraction: torch.Tensor


@dataclass(frozen=True)
class PrivilegedEncodingInput:
    log_guitar_mass_ratio: torch.Tensor
    center_of_mass_g: torch.Tensor
    inertia_symmetric: torch.Tensor
    linear_damping: torch.Tensor
    angular_damping: torch.Tensor
    support_friction: torch.Tensor
    contact_stiffness: torch.Tensor
    contact_damping: torch.Tensor
    guitar_geometry_scale_xyz: torch.Tensor
    gravity_magnitude_ratio: torch.Tensor
    restitution: torch.Tensor
    contacts: Mapping[str, ExactContactEncodingInput]
    tethers: Mapping[str, ExactTetherEncodingInput]
    external_disturbance_force: torch.Tensor
    external_disturbance_torque: torch.Tensor
    reset_position_offset: torch.Tensor
    reset_rotation_log: torch.Tensor
    initial_linear_velocity: torch.Tensor
    initial_angular_velocity: torch.Tensor
    curriculum_difficulty: torch.Tensor
    assist_randomization_severity: torch.Tensor


class PrivilegedPacker:
    manifest = PRIVILEGED_MANIFEST

    def __init__(self) -> None:
        self._builder = FixedScaleTensorBuilder(self.manifest)

    def pack(self, data: PrivilegedEncodingInput) -> torch.Tensor:
        _named_records("contacts", data.contacts, SUPPORT_SITE_KEYS)
        _named_records("tethers", data.tethers, TETHER_KEYS)
        for name, width in (
                ("center_of_mass_g", 3), ("inertia_symmetric", 6),
                ("support_friction", 5), ("guitar_geometry_scale_xyz", 3),
                ("external_disturbance_force", 3),
                ("external_disturbance_torque", 3),
                ("reset_position_offset", 3), ("reset_rotation_log", 3),
                ("initial_linear_velocity", 3),
                ("initial_angular_velocity", 3)):
            _matrix_width(name, getattr(data, name), width)

        values: dict[str, torch.Tensor] = {
            "physics.log_guitar_mass_ratio": data.log_guitar_mass_ratio,
            "physics.center_of_mass_G": data.center_of_mass_g,
            "physics.inertia_symmetric": data.inertia_symmetric,
            "physics.linear_damping": data.linear_damping,
            "physics.angular_damping": data.angular_damping,
            "physics.support_friction": data.support_friction,
            "physics.contact_stiffness": data.contact_stiffness,
            "physics.contact_damping": data.contact_damping,
            "physics.guitar_geometry_scale_xyz":
                data.guitar_geometry_scale_xyz,
            "physics.gravity_magnitude_ratio": data.gravity_magnitude_ratio,
            "physics.restitution": data.restitution,
        }
        for site_name in SUPPORT_SITE_KEYS:
            contact = data.contacts[site_name]
            _matrix_width(f"contacts[{site_name}].point_g", contact.point_g, 3)
            _matrix_width(f"contacts[{site_name}].force_g", contact.force_g, 3)
            _matrix_width(
                f"contacts[{site_name}].relative_tangent_velocity_g",
                contact.relative_tangent_velocity_g, 3)
            prefix = f"contact.{site_name}"
            values.update({
                f"{prefix}.pair_valid": contact.pair_valid,
                f"{prefix}.point_G": contact.point_g,
                f"{prefix}.force_G": contact.force_g,
                f"{prefix}.relative_tangent_velocity_G":
                    contact.relative_tangent_velocity_g,
                f"{prefix}.penetration_depth": contact.penetration_depth,
                f"{prefix}.true_friction_utilization":
                    contact.true_friction_utilization,
            })
        for tether_name in TETHER_KEYS:
            tether = data.tethers[tether_name]
            _matrix_width(
                f"tethers[{tether_name}].extension_g", tether.extension_g, 3)
            _matrix_width(f"tethers[{tether_name}].force_g", tether.force_g, 3)
            _matrix_width(f"tethers[{tether_name}].torque_g", tether.torque_g, 3)
            prefix = f"exact_tether.{tether_name}"
            values.update({
                f"{prefix}.valid": tether.valid,
                f"{prefix}.extension_G": tether.extension_g,
                f"{prefix}.force_G": tether.force_g,
                f"{prefix}.torque_G": tether.torque_g,
                f"{prefix}.mechanical_work_rate": tether.mechanical_work_rate,
                f"{prefix}.saturation_fraction": tether.saturation_fraction,
            })
        values.update({
            "domain.external_disturbance_force":
                data.external_disturbance_force,
            "domain.external_disturbance_torque":
                data.external_disturbance_torque,
            "domain.reset_position_offset": data.reset_position_offset,
            "domain.reset_rotation_log": data.reset_rotation_log,
            "domain.initial_linear_velocity": data.initial_linear_velocity,
            "domain.initial_angular_velocity": data.initial_angular_velocity,
            "domain.curriculum_difficulty": data.curriculum_difficulty,
            "domain.assist_randomization_severity":
                data.assist_randomization_severity,
        })
        return self._builder.pack(values)


__all__ = [
    "AggregateSupportEncodingInput",
    "EncodingBlockManifest",
    "EncodingField",
    "ExactContactEncodingInput",
    "ExactTetherEncodingInput",
    "FixedScaleTensorBuilder",
    "GUITAR_SUPPORT_DIM",
    "GUITAR_SUPPORT_MANIFEST",
    "GuitarSupportEncodingInput",
    "GuitarSupportPacker",
    "JOINT_COUNT",
    "JOINT_FEATURE_COUNT",
    "JOINT_HISTORY_DIM",
    "JointHistoryEncodingInput",
    "JointHistoryPacker",
    "PRIVILEGED_DIM",
    "PRIVILEGED_MANIFEST",
    "PrivilegedEncodingInput",
    "PrivilegedPacker",
    "READINESS_DIM",
    "READINESS_MANIFEST",
    "ReadinessEncodingInput",
    "ReadinessPacker",
    "STRING_KEYS",
    "SUPPORT_SITE_KEYS",
    "SupportSiteEncodingInput",
    "TETHER_KEYS",
    "TetherEncodingInput",
    "build_joint_history_manifest",
]
