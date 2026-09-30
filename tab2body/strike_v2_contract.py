"""Pure Strike-v2 observation ABI and block packing helpers.

This module deliberately has no Isaac Gym dependency.  The simulator task,
policy network, checkpoint tooling and CPU tests all import the same block
layout so a field-order change cannot silently corrupt a policy.
"""
from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Mapping, Sequence

if TYPE_CHECKING:
    import torch


STRIKE_V1_OBSERVATION_CONTRACT = "strike.observation.v1"
STRIKE_V2_OBSERVATION_CONTRACT = "strike.observation.v2"
STRIKE_V2_OBSERVATION_DIM = 303

STRIKE_V2_BLOCK_SIZES = OrderedDict((
    ("O_proprio", 60),
    ("O_arm_anchor", 18),
    ("O_hand_geometry", 30),
    ("O_grip_safety", 7),
    ("O_current_event", 32),
    ("O_target_geometry", 25),
    ("O_lookahead", 52),
    ("O_phase_detector", 29),
    ("O_recovery", 18),
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


def _direction(prefix: str) -> list[str]:
    return [f"{prefix}.down", f"{prefix}.up"]


def _string_fields(prefix: str) -> list[str]:
    return [f"{prefix}.string_{index}" for index in range(6)]


def _lookahead_fields(index: int) -> list[str]:
    prefix = f"strike_v2.lookahead_{index}"
    names = [f"{prefix}.valid", f"{prefix}.delta_s"]
    names += [
        f"{prefix}.gesture.single_pick",
        f"{prefix}.gesture.strum",
        f"{prefix}.gesture.alternate_restrike",
    ]
    names += _string_fields(f"{prefix}.traversal")
    names += _string_fields(f"{prefix}.audible")
    names += _direction(f"{prefix}.direction")
    names += _string_fields(f"{prefix}.offset_s")
    names.append(f"{prefix}.sweep_duration_s")
    return names


def strike_v2_block_manifest(
        controlled_dof_names: Sequence[str]) -> OrderedDict[str, tuple[str, ...]]:
    """Build the canonical 303D manifest for one exact 30D action order."""
    controlled = tuple(str(name) for name in controlled_dof_names)
    if len(controlled) != 30 or len(set(controlled)) != 30:
        raise ValueError(
            "Strike-v2 requires exactly 30 unique controlled DOF names")

    blocks: OrderedDict[str, tuple[str, ...]] = OrderedDict()
    blocks["O_proprio"] = tuple(
        [f"strike_v2.proprio.position.{name}" for name in controlled]
        + [f"strike_v2.proprio.velocity.{name}" for name in controlled])

    anchor = []
    anchor += _xyz("strike_v2.arm_anchor.position_G")
    anchor += _rotation6d("strike_v2.arm_anchor.rotation_G")
    anchor += _xyz("strike_v2.arm_anchor.linear_velocity_G")
    anchor += _xyz("strike_v2.arm_anchor.angular_velocity_G")
    anchor += _xyz("strike_v2.arm_anchor.projected_gravity")
    blocks["O_arm_anchor"] = tuple(anchor)

    hand = []
    for body in ("palm", "pick"):
        hand += _xyz(f"strike_v2.hand.{body}.position_G")
        hand += _rotation6d(f"strike_v2.hand.{body}.rotation_G")
        hand += _xyz(f"strike_v2.hand.{body}.linear_velocity_G")
        hand += _xyz(f"strike_v2.hand.{body}.angular_velocity_G")
    blocks["O_hand_geometry"] = tuple(hand)

    blocks["O_grip_safety"] = (
        "strike_v2.grip.quality_total",
        "strike_v2.grip.quality_pinch",
        "strike_v2.grip.quality_free",
        "strike_v2.safety.margin_arm",
        "strike_v2.safety.margin_thumb",
        "strike_v2.safety.margin_index",
        "strike_v2.safety.margin_other_fingers",
    )

    event = ["strike_v2.event.valid"]
    event += [
        "strike_v2.event.gesture.single_pick",
        "strike_v2.event.gesture.strum",
        "strike_v2.event.gesture.alternate_restrike",
    ]
    event += _string_fields("strike_v2.event.traversal")
    event += _string_fields("strike_v2.event.audible")
    event += _string_fields("strike_v2.event.offset_s")
    event += _direction("strike_v2.event.musical_direction")
    event += _direction("strike_v2.event.motor_direction")
    event += [
        "strike_v2.event.sweep_duration_s",
        "strike_v2.event.time_to_target_s",
        "strike_v2.event.window_open_delta_s",
        "strike_v2.event.window_close_delta_s",
        "strike_v2.event.approach_lead_s",
        "strike_v2.event.tempo_lambda",
    ]
    blocks["O_current_event"] = tuple(event)

    target = []
    for point in ("ready", "entry", "exit", "active"):
        target += _xyz(f"strike_v2.target.{point}_vector_G")
    target.append("strike_v2.target.lane_offset_m")
    target += _string_fields("strike_v2.target.current_required")
    target += _string_fields("strike_v2.target.next_required")
    blocks["O_target_geometry"] = tuple(target)

    blocks["O_lookahead"] = tuple(
        _lookahead_fields(1) + _lookahead_fields(2))

    phase = [
        "strike_v2.phase.ready",
        "strike_v2.phase.approach",
        "strike_v2.phase.release_recover",
        "strike_v2.phase.ready_dwell_fraction",
        "strike_v2.phase.event_resolved",
    ]
    phase += _string_fields("strike_v2.phase.completed_traversal")
    phase += _string_fields("strike_v2.detector.armed")
    phase += _string_fields("strike_v2.detector.rearm_progress")
    phase += _string_fields("strike_v2.detector.last_release")
    blocks["O_phase_detector"] = tuple(phase)

    recovery = [
        "strike_v2.recovery.valid",
        "strike_v2.recovery.mode.full",
        "strike_v2.recovery.mode.handoff",
        "strike_v2.recovery.mode.same_string_handoff",
        "strike_v2.recovery.progress",
        "strike_v2.recovery.required_fraction",
        "strike_v2.recovery.available_fraction",
        "strike_v2.recovery.clearance_required",
        "strike_v2.recovery.clearance_lifted",
        "strike_v2.recovery.clearance_reached",
    ]
    recovery += _xyz("strike_v2.recovery.current_target_vector_G")
    recovery += _xyz("strike_v2.recovery.next_entry_vector_G")
    recovery += _direction("strike_v2.recovery.direction")
    blocks["O_recovery"] = tuple(recovery)

    blocks["O_synchronizer"] = (
        "strike_v2.synchronizer.release_enable",
        "strike_v2.synchronizer.timing_offset_s",
    )
    blocks["O_history"] = tuple(
        f"strike_v2.history.previous_executed_action.{name}"
        for name in controlled)

    for block_name, expected_size in STRIKE_V2_BLOCK_SIZES.items():
        actual_size = len(blocks[block_name])
        if actual_size != expected_size:
            raise RuntimeError(
                f"{block_name} manifest has {actual_size} fields; "
                f"expected {expected_size}")
    flattened = [field for fields in blocks.values() for field in fields]
    if len(flattened) != STRIKE_V2_OBSERVATION_DIM:
        raise RuntimeError("Strike-v2 observation manifest is not 303D")
    if len(set(flattened)) != len(flattened):
        raise RuntimeError("Strike-v2 observation manifest contains duplicates")
    return blocks


def strike_v2_block_slices() -> OrderedDict[str, slice]:
    result: OrderedDict[str, slice] = OrderedDict()
    start = 0
    for name, size in STRIKE_V2_BLOCK_SIZES.items():
        result[name] = slice(start, start + size)
        start += size
    if start != STRIKE_V2_OBSERVATION_DIM:
        raise RuntimeError("Strike-v2 block sizes are not 303D")
    return result


STRIKE_V2_BLOCK_SLICES = strike_v2_block_slices()


def pack_strike_v2_blocks(
        blocks: Mapping[str, "torch.Tensor"], *,
        validate_finite: bool = True) -> "torch.Tensor":
    """Validate and concatenate a complete batch of named observation blocks."""
    import torch
    missing = [name for name in STRIKE_V2_BLOCK_SIZES if name not in blocks]
    unknown = sorted(set(blocks) - set(STRIKE_V2_BLOCK_SIZES))
    if missing or unknown:
        raise ValueError(
            f"invalid Strike-v2 observation blocks: missing={missing}, "
            f"unknown={unknown}")
    batch_size = None
    ordered = []
    for name, size in STRIKE_V2_BLOCK_SIZES.items():
        value = blocks[name]
        if not isinstance(value, torch.Tensor) or value.ndim != 2:
            raise TypeError(f"{name} must be a rank-2 torch.Tensor")
        if value.shape[1] != size:
            raise ValueError(
                f"{name} must be [N,{size}], got {tuple(value.shape)}")
        if batch_size is None:
            batch_size = value.shape[0]
        elif value.shape[0] != batch_size:
            raise ValueError("Strike-v2 observation blocks disagree on batch size")
        if validate_finite and not torch.isfinite(value).all():
            raise FloatingPointError(f"{name} contains NaN or Inf")
        ordered.append(value)
    result = torch.cat(ordered, dim=-1)
    if result.shape[1] != STRIKE_V2_OBSERVATION_DIM:
        raise RuntimeError("packed Strike-v2 observation is not 303D")
    return result


@dataclass(frozen=True)
class StrikeV2ObservationABI:
    schema: str = STRIKE_V2_OBSERVATION_CONTRACT
    dimension: int = STRIKE_V2_OBSERVATION_DIM

    @property
    def block_sizes(self) -> Mapping[str, int]:
        return OrderedDict(STRIKE_V2_BLOCK_SIZES)

    @property
    def block_slices(self) -> Mapping[str, slice]:
        return OrderedDict(STRIKE_V2_BLOCK_SLICES)


__all__ = [
    "STRIKE_V1_OBSERVATION_CONTRACT",
    "STRIKE_V2_BLOCK_SIZES",
    "STRIKE_V2_BLOCK_SLICES",
    "STRIKE_V2_OBSERVATION_CONTRACT",
    "STRIKE_V2_OBSERVATION_DIM",
    "StrikeV2ObservationABI",
    "pack_strike_v2_blocks",
    "strike_v2_block_manifest",
    "strike_v2_block_slices",
]
