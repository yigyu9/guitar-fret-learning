"""Pure Fret-v2 observation ABI and named-block packing helpers.

The module deliberately has no Isaac Gym dependency.  Environment, model,
checkpoint tools and CPU tests therefore share one authoritative 420D layout.
"""
from __future__ import annotations

from collections import OrderedDict
from typing import TYPE_CHECKING, Mapping, Sequence

if TYPE_CHECKING:
    import torch


FRET_V1_OBSERVATION_CONTRACT = "fret.observation.v1"
FRET_V2_OBSERVATION_CONTRACT = "fret.observation.v2"
FRET_V2_OBSERVATION_DIM = 420

FRET_V2_BLOCK_SIZES = OrderedDict((
    ("O_proprio", 60),
    ("O_arm_anchor", 18),
    ("O_hand_geometry", 60),
    ("O_current_event", 45),
    ("O_target_geometry", 24),
    ("O_finger_transition", 52),
    ("O_lookahead", 72),
    ("O_readiness_contact", 45),
    ("O_phase", 12),
    ("O_synchronizer", 2),
    ("O_history", 30),
))


def _xyz(prefix: str) -> list[str]:
    return [f"{prefix}.{axis}" for axis in ("x", "y", "z")]


def _rotation6d(prefix: str) -> list[str]:
    return [
        f"{prefix}.column_{column}.{axis}"
        for column in (0, 1)
        for axis in ("x", "y", "z")
    ]


def _strings(prefix: str) -> list[str]:
    return [f"{prefix}.string_{index}" for index in range(6)]


def _fingers(prefix: str) -> list[str]:
    return [f"{prefix}.finger_{index}" for index in range(1, 5)]


def _finger_event_fields(prefix: str) -> list[str]:
    fields = _strings(f"{prefix}.next_string_mask")
    fields += [
        f"{prefix}.next_fret",
        f"{prefix}.time_to_next_goal",
        f"{prefix}.next_valid",
        f"{prefix}.time_to_current_change",
        f"{prefix}.relation.keep",
        f"{prefix}.relation.move",
        f"{prefix}.relation.rest",
    ]
    return fields


def _lookahead_event_fields(index: int) -> list[str]:
    prefix = f"fret_v2.lookahead_{index}"
    fields = [f"{prefix}.valid", f"{prefix}.delta_s"]
    for finger in range(1, 5):
        fields += _strings(f"{prefix}.finger_{finger}.string_mask")
    fields += _fingers(f"{prefix}.finger_fret_normalized")
    fields += _strings(f"{prefix}.no_press")
    return fields


def fret_v2_block_manifest(
        controlled_dof_names: Sequence[str]) -> OrderedDict[str, tuple[str, ...]]:
    """Build the canonical 420D manifest for one exact 30D action order."""
    controlled = tuple(str(name) for name in controlled_dof_names)
    if len(controlled) != 30 or len(set(controlled)) != 30:
        raise ValueError("Fret-v2 requires exactly 30 unique controlled DOF names")

    blocks: OrderedDict[str, tuple[str, ...]] = OrderedDict()
    blocks["O_proprio"] = tuple(
        [f"fret_v2.proprio.position.{name}" for name in controlled]
        + [f"fret_v2.proprio.velocity.{name}" for name in controlled])

    anchor = []
    anchor += _xyz("fret_v2.arm_anchor.position_G")
    anchor += _rotation6d("fret_v2.arm_anchor.rotation_G")
    anchor += _xyz("fret_v2.arm_anchor.linear_velocity_G")
    anchor += _xyz("fret_v2.arm_anchor.angular_velocity_G")
    anchor += _xyz("fret_v2.arm_anchor.projected_gravity")
    blocks["O_arm_anchor"] = tuple(anchor)

    hand = []
    for body in ("wrist", "palm"):
        hand += _xyz(f"fret_v2.hand.{body}.position_G")
        hand += _rotation6d(f"fret_v2.hand.{body}.rotation_G")
        hand += _xyz(f"fret_v2.hand.{body}.linear_velocity_G")
        hand += _xyz(f"fret_v2.hand.{body}.angular_velocity_G")
    for finger in ("index", "middle", "ring", "pinky"):
        hand += _xyz(f"fret_v2.hand.{finger}_tip.position_G")
        hand += _xyz(f"fret_v2.hand.{finger}_tip.linear_velocity_G")
    hand += _xyz("fret_v2.hand.thumb_pad.position_G")
    hand += _xyz("fret_v2.hand.thumb_pad.linear_velocity_G")
    blocks["O_hand_geometry"] = tuple(hand)

    event = ["fret_v2.event.valid"]
    event += _fingers("fret_v2.event.finger_active")
    for finger in range(1, 5):
        event += _strings(f"fret_v2.event.finger_{finger}.string_mask")
    event += _fingers("fret_v2.event.finger_fret_normalized")
    event += _fingers("fret_v2.event.finger_barre")
    event += _strings("fret_v2.event.no_press")
    event += ["fret_v2.event.chord_size", "fret_v2.event.atomic_chord"]
    blocks["O_current_event"] = tuple(event)

    target = []
    for finger in range(1, 5):
        target += _xyz(f"fret_v2.target.finger_{finger}.vector_G")
    target += _fingers("fret_v2.target.signed_press_depth_m")
    target += _fingers("fret_v2.target.string_lateral_error_m")
    target += _xyz("fret_v2.target.wrist_vector_G")
    target += ["fret_v2.target.wrist_radius_margin"]
    blocks["O_target_geometry"] = tuple(target)

    transition = []
    for finger in range(1, 5):
        transition += _finger_event_fields(
            f"fret_v2.transition.finger_{finger}")
    blocks["O_finger_transition"] = tuple(transition)

    blocks["O_lookahead"] = tuple(
        _lookahead_event_fields(1) + _lookahead_event_fields(2))

    readiness = []
    for signal in (
            "press_quality", "ready", "wrong_press", "sustain_valid",
            "slip_speed_mps"):
        readiness += _strings(f"fret_v2.readiness.{signal}")
    readiness += _fingers("fret_v2.readiness.target_distance_m")
    readiness += [
        "fret_v2.readiness.thumb.dx_scaled",
        "fret_v2.readiness.thumb.dy_scaled",
        "fret_v2.readiness.thumb.gap_scaled",
        "fret_v2.readiness.thumb.distance_scaled",
        "fret_v2.readiness.thumb.in_region",
        "fret_v2.readiness.thumb.contact",
        "fret_v2.readiness.thumb.force_quality",
        "fret_v2.readiness.chord_ready",
        "fret_v2.readiness.confidence",
        "fret_v2.readiness.dwell_fraction",
        "fret_v2.readiness.minimum_safety_margin",
    ]
    blocks["O_readiness_contact"] = tuple(readiness)

    blocks["O_phase"] = (
        "fret_v2.phase.prepare",
        "fret_v2.phase.press",
        "fret_v2.phase.hold",
        "fret_v2.phase.release",
        "fret_v2.phase.transition",
        "fret_v2.phase.preparation_progress",
        "fret_v2.phase.event_progress",
        "fret_v2.phase.time_to_press_s",
        "fret_v2.phase.time_to_release_s",
        "fret_v2.phase.song_sin",
        "fret_v2.phase.song_cos",
        "fret_v2.phase.event_resolved",
    )
    blocks["O_synchronizer"] = (
        "fret_v2.synchronizer.release_enable",
        "fret_v2.synchronizer.timing_offset_s",
    )
    blocks["O_history"] = tuple(
        f"fret_v2.history.previous_executed_action.{name}"
        for name in controlled)

    for block_name, expected_size in FRET_V2_BLOCK_SIZES.items():
        actual_size = len(blocks[block_name])
        if actual_size != expected_size:
            raise RuntimeError(
                f"{block_name} manifest has {actual_size} fields; "
                f"expected {expected_size}")
    flattened = [field for fields in blocks.values() for field in fields]
    if len(flattened) != FRET_V2_OBSERVATION_DIM:
        raise RuntimeError("Fret-v2 observation manifest is not 420D")
    if len(set(flattened)) != len(flattened):
        raise RuntimeError("Fret-v2 observation manifest contains duplicates")
    return blocks


def fret_v2_block_slices() -> OrderedDict[str, slice]:
    result: OrderedDict[str, slice] = OrderedDict()
    start = 0
    for name, size in FRET_V2_BLOCK_SIZES.items():
        result[name] = slice(start, start + size)
        start += size
    if start != FRET_V2_OBSERVATION_DIM:
        raise RuntimeError("Fret-v2 block sizes are not 420D")
    return result


FRET_V2_BLOCK_SLICES = fret_v2_block_slices()


def pack_fret_v2_blocks(
        blocks: Mapping[str, "torch.Tensor"], *,
        validate_finite: bool = True) -> "torch.Tensor":
    """Validate and concatenate one complete batch of named blocks."""
    import torch
    missing = [name for name in FRET_V2_BLOCK_SIZES if name not in blocks]
    unknown = sorted(set(blocks) - set(FRET_V2_BLOCK_SIZES))
    if missing or unknown:
        raise ValueError(
            f"invalid Fret-v2 observation blocks: missing={missing}, "
            f"unknown={unknown}")
    batch_size = None
    ordered = []
    for name, size in FRET_V2_BLOCK_SIZES.items():
        value = blocks[name]
        if not isinstance(value, torch.Tensor) or value.ndim != 2:
            raise TypeError(f"{name} must be a rank-2 torch.Tensor")
        if value.shape[1] != size:
            raise ValueError(f"{name} must be [N,{size}], got {tuple(value.shape)}")
        if batch_size is None:
            batch_size = value.shape[0]
        elif value.shape[0] != batch_size:
            raise ValueError("Fret-v2 observation blocks disagree on batch size")
        if validate_finite and not torch.isfinite(value).all():
            raise FloatingPointError(f"{name} contains NaN or Inf")
        ordered.append(value)
    result = torch.cat(ordered, dim=-1)
    if result.shape[1] != FRET_V2_OBSERVATION_DIM:
        raise RuntimeError("packed Fret-v2 observation is not 420D")
    return result


__all__ = [
    "FRET_V1_OBSERVATION_CONTRACT",
    "FRET_V2_BLOCK_SIZES",
    "FRET_V2_BLOCK_SLICES",
    "FRET_V2_OBSERVATION_CONTRACT",
    "FRET_V2_OBSERVATION_DIM",
    "fret_v2_block_manifest",
    "pack_fret_v2_blocks",
]
