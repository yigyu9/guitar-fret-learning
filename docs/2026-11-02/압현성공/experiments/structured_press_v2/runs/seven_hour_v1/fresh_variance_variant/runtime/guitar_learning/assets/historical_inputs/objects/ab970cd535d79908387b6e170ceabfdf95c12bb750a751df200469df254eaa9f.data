"""Pure tensor rules for ready, timing and post-event episode completion.

These helpers intentionally avoid Isaac Gym so the two easy-to-regress
contracts can be tested on CPU:

* A1 ready success is latched once while its episode keeps a fixed horizon;
* timing statistics observe a physical target crossing before the tolerance
  gate filters successful hits;
* only a real release waits for recovery, while a miss can finish immediately.
"""
from __future__ import annotations

import math

import torch


def strike_rational_timing_quality(
        error_s: torch.Tensor, core_s: float) -> torch.Tensor:
    if not isinstance(error_s, torch.Tensor) or not error_s.is_floating_point():
        raise TypeError("timing error must be a floating tensor")
    if not torch.isfinite(error_s).all():
        raise ValueError("timing error must be finite")
    if isinstance(core_s, bool):
        raise TypeError("timing core must be numeric")
    core_s = float(core_s)
    if not math.isfinite(core_s) or core_s <= 0.0:
        raise ValueError("timing core must be finite and positive")
    return 1.0 / (1.0 + (error_s / core_s).square())


def strike_timed_approach_open(
        episode_time_s: torch.Tensor,
        target_time_s: torch.Tensor,
        first_offset_s: torch.Tensor,
        approach_lead_s: float) -> dict[str, torch.Tensor]:
    values = (episode_time_s, target_time_s, first_offset_s)
    if any(not isinstance(value, torch.Tensor) for value in values):
        raise TypeError("timed approach inputs must be tensors")
    if any(value.shape != episode_time_s.shape for value in values[1:]):
        raise ValueError("timed approach inputs must share shape [N]")
    if any(not value.is_floating_point() for value in values):
        raise TypeError("timed approach inputs must use floating tensors")
    if any(value.device != episode_time_s.device for value in values[1:]):
        raise ValueError("timed approach inputs must share a device")
    if any(not torch.isfinite(value).all() for value in values):
        raise ValueError("timed approach inputs must be finite")
    if isinstance(approach_lead_s, bool):
        raise TypeError("approach lead must be numeric")
    approach_lead_s = float(approach_lead_s)
    if not math.isfinite(approach_lead_s) or approach_lead_s <= 0.0:
        raise ValueError("approach lead must be finite and positive")
    approach_start_s = target_time_s + first_offset_s - approach_lead_s
    time_to_approach_s = approach_start_s - episode_time_s
    return {
        "approach_start_s": approach_start_s,
        "time_to_approach_s": time_to_approach_s,
        "approach_open": time_to_approach_s <= 0.0,
    }


def strike_early_timing_cost(
        accepted_release: torch.Tensor,
        signed_error_s: torch.Tensor,
        *,
        grace_s: float,
        scale_s: float) -> torch.Tensor:
    if (not isinstance(accepted_release, torch.Tensor)
            or accepted_release.dtype != torch.bool
            or accepted_release.ndim != 2):
        raise TypeError("accepted_release must be bool [N,S]")
    if (not isinstance(signed_error_s, torch.Tensor)
            or signed_error_s.shape != accepted_release.shape
            or not signed_error_s.is_floating_point()):
        raise TypeError("signed_error_s must be floating [N,S]")
    if signed_error_s.device != accepted_release.device:
        raise ValueError("early timing inputs must share a device")
    if not torch.isfinite(signed_error_s[accepted_release]).all():
        raise ValueError("accepted signed timing errors must be finite")
    if isinstance(grace_s, bool) or isinstance(scale_s, bool):
        raise TypeError("early timing grace and scale must be numeric")
    grace_s = float(grace_s)
    scale_s = float(scale_s)
    if (not math.isfinite(grace_s) or grace_s < 0.0
            or not math.isfinite(scale_s) or scale_s <= 0.0):
        raise ValueError("early timing grace/scale must be finite and valid")
    excess = (-signed_error_s - grace_s).clamp(min=0.0)
    return torch.where(
        accepted_release,
        (excess / scale_s).square().clamp(max=1.0),
        torch.zeros_like(signed_error_s))


def strike_premature_release(
        accepted_release: torch.Tensor,
        release_time_s: torch.Tensor,
        target_time_s: torch.Tensor,
        target_offset_s: torch.Tensor,
        left_tolerance_s: torch.Tensor) -> dict[str, torch.Tensor]:
    if (accepted_release.ndim != 2
            or accepted_release.dtype != torch.bool):
        raise TypeError("accepted_release must be bool [N,S]")
    if (release_time_s.shape != accepted_release.shape
            or target_offset_s.shape != accepted_release.shape):
        raise ValueError("release times/offsets must match accepted releases")
    if (target_time_s.shape != accepted_release.shape[:1]
            or left_tolerance_s.shape != accepted_release.shape[:1]):
        raise ValueError("target time/tolerance must have shape [N]")
    values = (release_time_s, target_time_s, target_offset_s,
              left_tolerance_s)
    if any(not value.is_floating_point() for value in values):
        raise TypeError("timing evidence must use floating tensors")
    if any(value.device != accepted_release.device for value in values):
        raise ValueError("premature-release inputs must share a device")
    if (not torch.isfinite(target_time_s).all()
            or not torch.isfinite(target_offset_s).all()
            or not torch.isfinite(left_tolerance_s).all()
            or not torch.isfinite(release_time_s[accepted_release]).all()
            or torch.any(left_tolerance_s <= 0.0)):
        raise ValueError("premature-release timing inputs are invalid")
    expected = target_time_s[:, None] + target_offset_s
    signed_error = torch.where(
        accepted_release, release_time_s - expected,
        torch.zeros_like(release_time_s))
    return {
        "signed_error_s": signed_error,
        "premature": (
            accepted_release
            & (signed_error < -left_tolerance_s[:, None])).any(dim=1),
    }


def strike_balanced_practice_direction(
        env_ids: torch.Tensor,
        reset_generation: torch.Tensor) -> torch.Tensor:
    if env_ids.ndim != 1 or reset_generation.shape != env_ids.shape:
        raise ValueError("practice direction inputs must share shape [N]")
    if env_ids.is_floating_point() or reset_generation.is_floating_point():
        raise TypeError("practice direction inputs must use integer tensors")
    if env_ids.device != reset_generation.device:
        raise ValueError("practice direction inputs must share a device")
    if torch.any(env_ids < 0) or torch.any(reset_generation < 0):
        raise ValueError("practice direction inputs must be non-negative")
    return torch.where(
        ((env_ids + reset_generation) % 2) == 0,
        torch.ones_like(env_ids),
        -torch.ones_like(env_ids))


def strike_focused_practice_direction(
        balanced_direction: torch.Tensor,
        focus_draw: torch.Tensor,
        *,
        focus_direction: int,
        target_focus_fraction: float) -> dict[str, torch.Tensor]:
    if (not isinstance(balanced_direction, torch.Tensor)
            or balanced_direction.ndim != 1
            or balanced_direction.dtype == torch.bool
            or balanced_direction.is_floating_point()):
        raise TypeError("balanced_direction must be an integer tensor [N]")
    if (not isinstance(focus_draw, torch.Tensor)
            or focus_draw.shape != balanced_direction.shape
            or not focus_draw.is_floating_point()
            or focus_draw.device != balanced_direction.device):
        raise TypeError("focus_draw must be a matching floating tensor")
    if torch.any((balanced_direction != -1) & (balanced_direction != 1)):
        raise ValueError("balanced directions must contain only -1 or +1")
    if not torch.isfinite(focus_draw).all() \
            or torch.any(focus_draw < 0.0) or torch.any(focus_draw >= 1.0):
        raise ValueError("focus draws must be finite in [0, 1)")
    if isinstance(focus_direction, bool) or focus_direction not in (-1, 1):
        raise ValueError("focus_direction must be -1 or +1")
    if isinstance(target_focus_fraction, bool):
        raise TypeError("target_focus_fraction must be numeric")
    target_focus_fraction = float(target_focus_fraction)
    if (not math.isfinite(target_focus_fraction)
            or not 0.5 <= target_focus_fraction <= 0.7):
        raise ValueError("target focus fraction must be in [0.5, 0.7]")
    focused_subset_fraction = 2.0 * (target_focus_fraction - 0.5)
    focused_subset = focus_draw < focused_subset_fraction
    direction = torch.where(
        focused_subset,
        torch.full_like(balanced_direction, focus_direction),
        balanced_direction)
    return {
        "direction": direction,
        "focused_subset": focused_subset,
    }


def strike_uniform_traversal_offsets(
        traversal: torch.Tensor,
        direction: torch.Tensor,
        interval_s: torch.Tensor) -> torch.Tensor:
    if traversal.ndim != 2 or traversal.dtype != torch.bool:
        raise TypeError("traversal must be a bool tensor with shape [N,S]")
    if direction.shape != traversal.shape[:1] or direction.is_floating_point():
        raise TypeError("direction must be an integer tensor with shape [N]")
    if interval_s.shape != traversal.shape[:1] \
            or not interval_s.is_floating_point():
        raise TypeError("interval_s must be a floating tensor with shape [N]")
    if (direction.device != traversal.device
            or interval_s.device != traversal.device):
        raise ValueError("traversal offset inputs must share a device")
    if torch.any((direction != -1) & (direction != 1)):
        raise ValueError("direction must contain only -1 or +1")
    if not torch.isfinite(interval_s).all() or torch.any(interval_s <= 0.0):
        raise ValueError("interval_s must be finite and positive")
    if not traversal.any(dim=1).all():
        raise ValueError("every traversal row must contain a string")
    indices = torch.arange(
        traversal.shape[1], device=traversal.device,
        dtype=interval_s.dtype)[None]
    center = (
        (indices * traversal).sum(dim=1)
        / traversal.sum(dim=1).to(interval_s.dtype))
    offsets = (
        -direction.to(interval_s.dtype)[:, None]
        * (indices - center[:, None])
        * interval_s[:, None])
    return torch.where(traversal, offsets, torch.zeros_like(offsets))


def strike_limit_traversal_span(
        traversal: torch.Tensor,
        target_direction: torch.Tensor,
        max_strings: int) -> torch.Tensor:
    if traversal.ndim != 2 or traversal.dtype != torch.bool:
        raise TypeError("traversal must be a bool tensor with shape [N,S]")
    if target_direction.shape != traversal.shape[:1] \
            or target_direction.is_floating_point():
        raise TypeError("target_direction must be an integer tensor with shape [N]")
    if target_direction.device != traversal.device:
        raise ValueError("traversal and direction must share a device")
    if isinstance(max_strings, bool) or not isinstance(max_strings, int) \
            or max_strings < 1:
        raise ValueError("max_strings must be a positive integer")
    if torch.any((target_direction != -1) & (target_direction != 1)):
        raise ValueError("target_direction must contain only -1 or +1")

    forward_rank = traversal.long().cumsum(dim=1)
    reverse_rank = torch.flip(
        torch.flip(traversal, dims=(1,)).long().cumsum(dim=1), dims=(1,))
    rank = torch.where(
        (target_direction == 1)[:, None], reverse_rank, forward_rank)
    return traversal & (rank <= max_strings)


def strike_next_traversal_string(
        traversal: torch.Tensor,
        completed: torch.Tensor,
        target_direction: torch.Tensor,
        fallback: torch.Tensor) -> torch.Tensor:
    if traversal.ndim != 2 or completed.shape != traversal.shape:
        raise ValueError("traversal and completed must share shape [N,S]")
    if traversal.dtype != torch.bool or completed.dtype != torch.bool:
        raise TypeError("traversal and completed must use torch.bool")
    if target_direction.shape != traversal.shape[:1] \
            or fallback.shape != traversal.shape[:1]:
        raise ValueError("direction and fallback must have shape [N]")
    if target_direction.is_floating_point() or fallback.is_floating_point():
        raise TypeError("direction and fallback must use integer tensors")
    if (completed.device != traversal.device
            or target_direction.device != traversal.device
            or fallback.device != traversal.device):
        raise ValueError("traversal target tensors must share a device")
    if torch.any((target_direction != -1) & (target_direction != 1)):
        raise ValueError("target_direction must contain only -1 or +1")

    remaining = traversal & ~completed
    indices = torch.arange(
        traversal.shape[1], device=traversal.device,
        dtype=fallback.dtype)[None]
    down = torch.where(
        remaining, indices, torch.full_like(indices, -1)).amax(dim=1)
    up = torch.where(
        remaining, indices,
        torch.full_like(indices, traversal.shape[1])).amin(dim=1)
    selected = torch.where(target_direction == 1, down, up)
    return torch.where(remaining.any(dim=1), selected, fallback)


def strike_strum_terminal_progress(
        tip_g: torch.Tensor,
        final_string_point_g: torch.Tensor,
        exit_point_g: torch.Tensor,
        previous_best: torch.Tensor,
        active: torch.Tensor) -> dict[str, torch.Tensor]:
    """Measure monotone progress from the final string to the sweep exit.

    The segment itself defines the positive direction, so this contract is
    identical for down- and up-strums.  Only increases in the best clamped
    projection are returned; reversing or cycling therefore cannot create
    additional positive reward.
    """
    values = (
        ("final_string_point_g", final_string_point_g),
        ("exit_point_g", exit_point_g),
    )
    if not isinstance(tip_g, torch.Tensor):
        raise TypeError("tip_g must be a torch.Tensor")
    if tip_g.ndim != 2 or tip_g.shape[1] != 3:
        raise ValueError("tip_g must have shape [N,3]")
    for name, value in values:
        if not isinstance(value, torch.Tensor):
            raise TypeError(f"{name} must be a torch.Tensor")
        if value.shape != tip_g.shape:
            raise ValueError(f"{name} must match tip_g shape [N,3]")
        if value.dtype != tip_g.dtype or value.device != tip_g.device:
            raise TypeError(f"{name} must match tip_g dtype/device")
    if (not isinstance(previous_best, torch.Tensor)
            or previous_best.shape != tip_g.shape[:1]
            or previous_best.dtype != tip_g.dtype
            or previous_best.device != tip_g.device):
        raise TypeError(
            "previous_best must match the tip batch floating dtype/device")
    if (not isinstance(active, torch.Tensor)
            or active.shape != tip_g.shape[:1]
            or active.dtype != torch.bool
            or active.device != tip_g.device):
        raise TypeError("active must be a matching bool tensor")
    if not tip_g.is_floating_point():
        raise TypeError("terminal progress geometry must be floating tensors")
    if (not torch.isfinite(tip_g).all()
            or not torch.isfinite(final_string_point_g).all()
            or not torch.isfinite(exit_point_g).all()
            or not torch.isfinite(previous_best).all()
            or torch.any(previous_best < 0.0)
            or torch.any(previous_best > 1.0)):
        raise ValueError("terminal progress inputs must be finite and bounded")

    segment = exit_point_g - final_string_point_g
    length_squared = segment.square().sum(dim=1)
    if torch.any(active & (length_squared <= 1e-12)):
        raise ValueError("active strum exit segments must be non-degenerate")
    safe_length_squared = length_squared.clamp_min(1e-12)
    projection = (
        ((tip_g - final_string_point_g) * segment).sum(dim=1)
        / safe_length_squared).clamp(0.0, 1.0)
    current = torch.where(active, projection, torch.zeros_like(projection))
    next_best = torch.where(
        active, torch.maximum(previous_best, current), previous_best)
    increment = (next_best - previous_best).clamp(0.0, 1.0)
    exit_distance = torch.linalg.vector_norm(tip_g - exit_point_g, dim=1)
    return {
        "current": current,
        "best": next_best,
        "increment": increment,
        "exit_distance_m": exit_distance,
    }


def strike_ordered_release_progress(
        previous: torch.Tensor,
        release: torch.Tensor,
        subframe_t: torch.Tensor,
        release_direction: torch.Tensor,
        traversal: torch.Tensor,
        target_direction: torch.Tensor) -> dict[str, torch.Tensor]:
    tensors = (previous, release, subframe_t, release_direction, traversal)
    if any(value.ndim != 2 for value in tensors):
        raise ValueError("ordered strike tensors must have shape [N,S]")
    if any(value.shape != previous.shape for value in tensors[1:]):
        raise ValueError("ordered strike tensors must share shape [N,S]")
    if target_direction.shape != previous.shape[:1]:
        raise ValueError("target_direction must have shape [N]")
    if previous.dtype != torch.bool or release.dtype != torch.bool \
            or traversal.dtype != torch.bool:
        raise TypeError("previous, release and traversal must use torch.bool")
    if not subframe_t.is_floating_point():
        raise TypeError("subframe_t must use a floating dtype")
    if release_direction.is_floating_point() \
            or target_direction.is_floating_point():
        raise TypeError("strike directions must use integer tensors")
    if any(value.device != previous.device for value in tensors[1:]) \
            or target_direction.device != previous.device:
        raise ValueError("ordered strike tensors must share a device")
    if not torch.isfinite(subframe_t).all():
        raise ValueError("subframe_t must be finite")
    if torch.any((target_direction != -1) & (target_direction != 1)):
        raise ValueError("target_direction must contain only -1 or +1")

    accepted = previous.clone()
    accepted_now = torch.zeros_like(previous)
    unplanned = torch.zeros(previous.shape[0], device=previous.device)
    wrong_direction = torch.zeros_like(unplanned)
    order_violation = torch.zeros_like(unplanned)
    duplicate = torch.zeros_like(unplanned)
    active_time = torch.where(
        release, subframe_t,
        torch.full_like(subframe_t, float("inf")))
    ordered_strings = torch.argsort(active_time, dim=1)
    rows = torch.arange(previous.shape[0], device=previous.device)

    for slot in range(previous.shape[1]):
        string_index = ordered_strings[:, slot]
        active = release[rows, string_index]
        target = traversal[rows, string_index]
        direction_ok = (
            release_direction[rows, string_index] == target_direction)
        already = accepted[rows, string_index]
        remaining = traversal & ~accepted
        down_expected = torch.where(
            remaining,
            torch.arange(previous.shape[1], device=previous.device)[None],
            torch.full(previous.shape, -1, device=previous.device,
                       dtype=torch.long)).amax(dim=1)
        up_expected = torch.where(
            remaining,
            torch.arange(previous.shape[1], device=previous.device)[None],
            torch.full(previous.shape, previous.shape[1],
                       device=previous.device, dtype=torch.long)).amin(dim=1)
        expected = torch.where(
            target_direction == 1, down_expected, up_expected)
        expected_now = string_index == expected
        can_accept = active & target & direction_ok & ~already & expected_now
        unplanned += (active & ~target).to(unplanned.dtype)
        wrong_direction += (active & target & ~direction_ok).to(unplanned.dtype)
        duplicate += (active & target & direction_ok & already).to(
            unplanned.dtype)
        order_violation += (
            active & target & direction_ok & ~already & ~expected_now
        ).to(unplanned.dtype)
        accepted[rows, string_index] |= can_accept
        accepted_now[rows, string_index] |= can_accept

    complete = ((accepted & traversal) == traversal).all(dim=1)
    return {
        "accepted_release": accepted_now,
        "accumulated_release": accepted,
        "complete": complete,
        "unplanned_crossing_count": unplanned,
        "wrong_direction_count": wrong_direction,
        "order_violation_count": order_violation,
        "duplicate_crossing_count": duplicate,
    }


def _matching_bool_masks(
        first_name: str,
        first: torch.Tensor,
        second_name: str,
        second: torch.Tensor) -> None:
    for name, value in ((first_name, first), (second_name, second)):
        if not isinstance(value, torch.Tensor):
            raise TypeError(f"{name} must be a torch.Tensor")
        if value.dtype != torch.bool:
            raise TypeError(f"{name} must use torch.bool")
    if first.shape != second.shape:
        raise ValueError(f"{first_name} and {second_name} must share a shape")
    if first.device != second.device:
        raise ValueError(f"{first_name} and {second_name} must share a device")


def _matching_shape_device(reference_name, reference, values):
    if not isinstance(reference, torch.Tensor):
        raise TypeError(f"{reference_name} must be a torch.Tensor")
    for name, value in values:
        if not isinstance(value, torch.Tensor):
            raise TypeError(f"{name} must be a torch.Tensor")
        if value.shape != reference.shape:
            raise ValueError(f"{name} must match {reference_name} shape")
        if value.device != reference.device:
            raise ValueError(f"{name} must share {reference_name} device")


def _require_integer_tensor(name, value):
    if value.dtype == torch.bool or value.is_floating_point():
        raise TypeError(f"{name} must use an integer dtype")


def strike_motion_target_context(
        event_string: torch.Tensor,
        event_lane_y: torch.Tensor,
        event_direction: torch.Tensor,
        recovery_string: torch.Tensor,
        recovery_lane_y: torch.Tensor,
        recovery_direction: torch.Tensor,
        recovery_context_valid: torch.Tensor,
        motor_phase: torch.Tensor,
        *,
        release_recover_phase: int) -> dict[str, torch.Tensor]:
    """Keep released geometry and direction while the motor follows through."""
    values = (
        ("event_lane_y", event_lane_y),
        ("event_direction", event_direction),
        ("recovery_string", recovery_string),
        ("recovery_lane_y", recovery_lane_y),
        ("recovery_direction", recovery_direction),
        ("recovery_context_valid", recovery_context_valid),
        ("motor_phase", motor_phase),
    )
    _matching_shape_device("event_string", event_string, values)
    _require_integer_tensor("event_string", event_string)
    _require_integer_tensor("event_direction", event_direction)
    _require_integer_tensor("recovery_string", recovery_string)
    _require_integer_tensor("recovery_direction", recovery_direction)
    _require_integer_tensor("motor_phase", motor_phase)
    if not event_lane_y.is_floating_point():
        raise TypeError("event_lane_y must use a floating dtype")
    if recovery_lane_y.dtype != event_lane_y.dtype:
        raise TypeError("recovery_lane_y must match event_lane_y dtype")
    if recovery_context_valid.dtype != torch.bool:
        raise TypeError("recovery_context_valid must use torch.bool")
    if torch.any(
            recovery_context_valid
            & (recovery_direction != -1)
            & (recovery_direction != 1)):
        raise ValueError("valid recovery direction must be -1 or +1")
    if torch.any((event_direction != -1) & (event_direction != 1)):
        raise ValueError("event direction must be -1 or +1")
    if not torch.isfinite(event_lane_y).all() or not torch.isfinite(
            recovery_lane_y).all():
        raise ValueError("strike lane context must be finite")
    if (isinstance(release_recover_phase, bool)
            or not isinstance(release_recover_phase, int)):
        raise TypeError("release_recover_phase must be an integer")

    recovering = (
        (motor_phase == release_recover_phase)
        & recovery_context_valid)
    return {
        "target_string": torch.where(
            recovering, recovery_string, event_string),
        "target_lane_y": torch.where(
            recovering, recovery_lane_y, event_lane_y),
        "target_direction": torch.where(
            recovering, recovery_direction,
            event_direction),
        "recovering": recovering,
    }


def strike_recovery_to_approach(
        motor_phase: torch.Tensor,
        event_resolved: torch.Tensor,
        recovery_count: torch.Tensor,
        recovery_rearmed: torch.Tensor,
        time_to_target_s: torch.Tensor,
        *,
        release_recover_phase: int,
        minimum_follow_through_frames: int,
        approach_lead_s: float) -> torch.Tensor:
    """Allow next-event approach only after a minimum follow-through."""
    values = (
        ("event_resolved", event_resolved),
        ("recovery_count", recovery_count),
        ("recovery_rearmed", recovery_rearmed),
        ("time_to_target_s", time_to_target_s),
    )
    _matching_shape_device("motor_phase", motor_phase, values)
    _require_integer_tensor("motor_phase", motor_phase)
    _require_integer_tensor("recovery_count", recovery_count)
    if event_resolved.dtype != torch.bool:
        raise TypeError("event_resolved must use torch.bool")
    if recovery_rearmed.dtype != torch.bool:
        raise TypeError("recovery_rearmed must use torch.bool")
    if not time_to_target_s.is_floating_point():
        raise TypeError("time_to_target_s must use a floating dtype")
    if not torch.isfinite(time_to_target_s).all():
        raise ValueError("time_to_target_s must be finite")
    if (isinstance(release_recover_phase, bool)
            or not isinstance(release_recover_phase, int)):
        raise TypeError("release_recover_phase must be an integer")
    if (isinstance(minimum_follow_through_frames, bool)
            or not isinstance(minimum_follow_through_frames, int)
            or minimum_follow_through_frames < 1):
        raise ValueError(
            "minimum_follow_through_frames must be a positive integer")
    approach_lead_s = float(approach_lead_s)
    if not math.isfinite(approach_lead_s) or approach_lead_s < 0.0:
        raise ValueError("approach_lead_s must be finite and non-negative")
    return (
        (motor_phase == release_recover_phase)
        & ~event_resolved
        & (recovery_count >= minimum_follow_through_frames)
        & recovery_rearmed
        & (time_to_target_s <= approach_lead_s))


def strike_song_continuing_phase(
        motor_phase: torch.Tensor,
        physical_release: torch.Tensor,
        recovery_context_valid: torch.Tensor,
        *,
        release_recover_phase: int) -> dict[str, torch.Tensor]:
    """Advance the musical event without inventing a motor-phase transition.

    A miss keeps READY or APPROACH exactly as it was.  Only a fresh physical
    release, or an already active release context, owns RECOVER.
    """
    _matching_bool_masks(
        "physical_release", physical_release,
        "recovery_context_valid", recovery_context_valid)
    _matching_shape_device(
        "motor_phase", motor_phase,
        (("physical_release", physical_release),))
    _require_integer_tensor("motor_phase", motor_phase)
    if (isinstance(release_recover_phase, bool)
            or not isinstance(release_recover_phase, int)):
        raise TypeError("release_recover_phase must be an integer")
    preserve_recovery = (
        physical_release
        | ((motor_phase == release_recover_phase)
           & recovery_context_valid))
    next_phase = torch.where(
        preserve_recovery,
        torch.full_like(motor_phase, release_recover_phase),
        motor_phase)
    return {
        "motor_phase": next_phase,
        "preserve_recovery": preserve_recovery,
    }


def strike_completed_recovery_frames(
        action_phase: torch.Tensor,
        recovery_count: torch.Tensor,
        *,
        release_recover_phase: int,
        disruption: torch.Tensor | None = None) -> torch.Tensor:
    """Count intervals executed from a RELEASE_RECOVER observation.

    Entering recovery after a crossing does not count the hit frame itself;
    only a later action selected while recovery was already visible completes
    one follow-through frame.
    """
    _matching_shape_device(
        "action_phase", action_phase,
        (("recovery_count", recovery_count),))
    _require_integer_tensor("action_phase", action_phase)
    _require_integer_tensor("recovery_count", recovery_count)
    if (isinstance(release_recover_phase, bool)
            or not isinstance(release_recover_phase, int)):
        raise TypeError("release_recover_phase must be an integer")
    if torch.any(recovery_count < 0):
        raise ValueError("recovery_count must be non-negative")
    next_count = torch.where(
        action_phase == release_recover_phase,
        recovery_count + 1,
        torch.zeros_like(recovery_count))
    if disruption is None:
        return next_count
    if (not isinstance(disruption, torch.Tensor)
            or disruption.dtype != torch.bool
            or disruption.shape != recovery_count.shape
            or disruption.device != recovery_count.device):
        raise TypeError(
            "recovery disruption must be a matching bool tensor")
    return torch.where(disruption, torch.zeros_like(next_count), next_count)


def strike_clean_recovery_progress(
        recovery_count: torch.Tensor,
        best_count: torch.Tensor,
        recovery_rearmed: torch.Tensor,
        recovery_active: torch.Tensor,
        completion_recorded: torch.Tensor,
        *,
        recovery_frames: int) -> dict[str, torch.Tensor]:
    _matching_shape_device(
        "recovery_count", recovery_count,
        (("best_count", best_count),
         ("recovery_rearmed", recovery_rearmed),
         ("recovery_active", recovery_active),
         ("completion_recorded", completion_recorded)))
    _require_integer_tensor("recovery_count", recovery_count)
    _require_integer_tensor("best_count", best_count)
    if (recovery_rearmed.dtype != torch.bool
            or recovery_active.dtype != torch.bool
            or completion_recorded.dtype != torch.bool):
        raise TypeError("recovery progress masks must use torch.bool")
    if (isinstance(recovery_frames, bool)
            or not isinstance(recovery_frames, int)
            or recovery_frames < 1):
        raise ValueError("recovery_frames must be a positive integer")
    if torch.any(recovery_count < 0) or torch.any(best_count < 0):
        raise ValueError("recovery progress counts must be non-negative")
    eligible = torch.where(
        recovery_active & recovery_rearmed,
        recovery_count.clamp_max(recovery_frames),
        torch.zeros_like(recovery_count))
    next_best = torch.maximum(best_count, eligible)
    progress = (
        (next_best - best_count).to(torch.float32)
        / float(recovery_frames))
    complete_pulse = (
        ~completion_recorded
        & (best_count < recovery_frames)
        & (next_best >= recovery_frames))
    return {
        "best_count": next_best,
        "progress": progress,
        "complete_pulse": complete_pulse,
        "completion_recorded": completion_recorded | complete_pulse,
    }


def strike_recovery_clearance_target(
        recovery_active: torch.Tensor,
        clearance_required: torch.Tensor,
        clearance_lifted: torch.Tensor,
        clearance_reached: torch.Tensor,
        release_lift: torch.Tensor,
        next_entry_lift: torch.Tensor,
        next_ready: torch.Tensor) -> dict[str, torch.Tensor]:
    """Select and retain the recovery waypoint until APPROACH begins."""
    _matching_shape_device(
        "recovery_active", recovery_active,
        (("clearance_required", clearance_required),
         ("clearance_lifted", clearance_lifted),
         ("clearance_reached", clearance_reached)))
    for name, value in (
            ("recovery_active", recovery_active),
            ("clearance_required", clearance_required),
            ("clearance_lifted", clearance_lifted),
            ("clearance_reached", clearance_reached)):
        if value.dtype != torch.bool:
            raise TypeError(f"{name} must use torch.bool")
    if (release_lift.ndim != 2 or release_lift.shape[-1] != 3
            or next_entry_lift.shape != release_lift.shape
            or next_ready.shape != release_lift.shape
            or release_lift.shape[0] != recovery_active.shape[0]
            or release_lift.device != recovery_active.device
            or next_entry_lift.device != recovery_active.device
            or next_ready.device != recovery_active.device):
        raise ValueError("recovery clearance points must have shape [N, 3]")
    active = recovery_active & clearance_required
    lifted_target = torch.where(
        clearance_reached[:, None], next_ready, next_entry_lift)
    target = torch.where(
        clearance_lifted[:, None], lifted_target, release_lift)
    return {"active": active, "target": target}


def strike_handoff_path_clearance(
        continuing: torch.Tensor,
        release_string: torch.Tensor,
        previous_direction: torch.Tensor,
        next_entry_string: torch.Tensor,
        next_direction: torch.Tensor,
        *,
        num_strings: int) -> dict[str, torch.Tensor]:
    _matching_shape_device(
        "continuing", continuing,
        (("release_string", release_string),
         ("previous_direction", previous_direction),
         ("next_entry_string", next_entry_string),
         ("next_direction", next_direction)))
    if continuing.dtype != torch.bool:
        raise TypeError("continuing must use torch.bool")
    for name, value in (
            ("release_string", release_string),
            ("previous_direction", previous_direction),
            ("next_entry_string", next_entry_string),
            ("next_direction", next_direction)):
        _require_integer_tensor(name, value)
    if (isinstance(num_strings, bool) or not isinstance(num_strings, int)
            or num_strings < 1):
        raise ValueError("num_strings must be a positive integer")
    for name, value in (
            ("release_string", release_string),
            ("next_entry_string", next_entry_string)):
        if torch.any((value < 0) | (value >= num_strings)):
            raise ValueError(f"{name} is outside the string range")
    for name, value in (
            ("previous_direction", previous_direction),
            ("next_direction", next_direction)):
        if torch.any((value != -1) & (value != 1)):
            raise ValueError(f"{name} must contain only -1 or +1")

    previous_exit_side = 2 * release_string - previous_direction
    next_entry_side = 2 * next_entry_string + next_direction
    lower = torch.minimum(previous_exit_side, next_entry_side)
    upper = torch.maximum(previous_exit_side, next_entry_side)
    string_positions = (
        2 * torch.arange(
            num_strings, dtype=release_string.dtype,
            device=release_string.device)[None])
    crossing_mask = (
        continuing[:, None]
        & (string_positions > lower[:, None])
        & (string_positions < upper[:, None]))
    rows = torch.arange(continuing.shape[0], device=continuing.device)
    release_index = release_string.to(torch.long)
    next_entry_index = next_entry_string.to(torch.long)
    return {
        "crossing_mask": crossing_mask,
        "clearance_required": crossing_mask.any(dim=1),
        "recent_string_crossed": crossing_mask[rows, release_index],
        "next_entry_string_crossed": crossing_mask[rows, next_entry_index],
        "same_string": continuing & (release_string == next_entry_string),
        "previous_exit_side": previous_exit_side,
        "next_entry_side": next_entry_side,
    }


def strike_clearance_waypoint_state(
        active: torch.Tensor,
        lifted: torch.Tensor,
        reached: torch.Tensor,
        target_distance: torch.Tensor,
        *,
        distance_threshold: float) -> dict[str, torch.Tensor]:
    _matching_shape_device(
        "active", active,
        (("lifted", lifted),
         ("reached", reached),
         ("target_distance", target_distance)))
    for name, value in (
            ("active", active),
            ("lifted", lifted),
            ("reached", reached)):
        if value.dtype != torch.bool:
            raise TypeError(f"{name} must use torch.bool")
    if not target_distance.is_floating_point():
        raise TypeError("target_distance must use a floating dtype")
    distance_threshold = float(distance_threshold)
    if not math.isfinite(distance_threshold) or distance_threshold <= 0.0:
        raise ValueError("distance_threshold must be finite and positive")
    arrived = (
        active
        & ~reached
        & (target_distance <= distance_threshold))
    target_changed = arrived & ~lifted
    reached_pulse = arrived & lifted
    return {
        "lifted": lifted | target_changed,
        "reached": reached | reached_pulse,
        "target_changed": target_changed,
        "reached_pulse": reached_pulse,
    }


def strike_dual_recovery_plan(
        current_time_s: torch.Tensor,
        next_target_time_s: torch.Tensor,
        continuing: torch.Tensor,
        release_string: torch.Tensor,
        previous_direction: torch.Tensor,
        next_entry_string: torch.Tensor,
        next_direction: torch.Tensor,
        *,
        num_strings: int,
        sim_hz: int,
        approach_lead_s: float,
        full_recovery_frames: int,
        minimum_handoff_frames: int) -> dict[str, torch.Tensor]:
    _matching_shape_device(
        "current_time_s", current_time_s,
        (("next_target_time_s", next_target_time_s),
         ("continuing", continuing),
         ("release_string", release_string),
         ("previous_direction", previous_direction),
         ("next_entry_string", next_entry_string),
         ("next_direction", next_direction)))
    if (not current_time_s.is_floating_point()
            or not next_target_time_s.is_floating_point()):
        raise TypeError("dual recovery times must use floating dtypes")
    if not torch.isfinite(current_time_s).all() \
            or not torch.isfinite(next_target_time_s).all():
        raise ValueError("dual recovery times must be finite")
    if continuing.dtype != torch.bool:
        raise TypeError("continuing must use torch.bool")
    _require_integer_tensor("release_string", release_string)
    _require_integer_tensor("previous_direction", previous_direction)
    _require_integer_tensor("next_entry_string", next_entry_string)
    _require_integer_tensor("next_direction", next_direction)
    for name, value in (
            ("sim_hz", sim_hz),
            ("full_recovery_frames", full_recovery_frames),
            ("minimum_handoff_frames", minimum_handoff_frames)):
        if (isinstance(value, bool) or not isinstance(value, int)
                or value < 1):
            raise ValueError(f"{name} must be a positive integer")
    if minimum_handoff_frames > full_recovery_frames:
        raise ValueError(
            "minimum_handoff_frames cannot exceed full_recovery_frames")
    approach_lead_s = float(approach_lead_s)
    if not math.isfinite(approach_lead_s) or approach_lead_s < 0.0:
        raise ValueError("approach_lead_s must be finite and non-negative")
    available_frames = torch.floor(
        (next_target_time_s - current_time_s - approach_lead_s)
        * float(sim_hz) + 1e-6).to(torch.long)
    handoff = continuing & (available_frames < full_recovery_frames)
    handoff_frames = available_frames.clamp(
        min=minimum_handoff_frames, max=full_recovery_frames)
    required_frames = torch.where(
        handoff,
        handoff_frames,
        torch.full_like(handoff_frames, full_recovery_frames))
    path = strike_handoff_path_clearance(
        continuing,
        release_string,
        previous_direction,
        next_entry_string,
        next_direction,
        num_strings=num_strings)
    same_string_handoff = handoff & path["same_string"]
    rearm_required = continuing & (
        ~handoff | path["same_string"] | path["clearance_required"])
    return {
        "available_frames": available_frames,
        "required_frames": required_frames,
        "handoff": handoff,
        "same_string_handoff": same_string_handoff,
        "path_crossing_mask": path["crossing_mask"],
        "clearance_required": path["clearance_required"],
        "rearm_required": rearm_required,
    }


def strike_dual_recovery_to_approach(
        motor_phase: torch.Tensor,
        event_resolved: torch.Tensor,
        recovery_count: torch.Tensor,
        recovery_rearmed: torch.Tensor,
        time_to_target_s: torch.Tensor,
        required_frames: torch.Tensor,
        handoff: torch.Tensor,
        same_string_handoff: torch.Tensor,
        clearance_required: torch.Tensor,
        clearance_reached: torch.Tensor,
        *,
        release_recover_phase: int,
        approach_lead_s: float) -> torch.Tensor:
    _matching_shape_device(
        "motor_phase", motor_phase,
        (("event_resolved", event_resolved),
         ("recovery_count", recovery_count),
         ("recovery_rearmed", recovery_rearmed),
         ("time_to_target_s", time_to_target_s),
         ("required_frames", required_frames),
         ("handoff", handoff),
         ("same_string_handoff", same_string_handoff),
         ("clearance_required", clearance_required),
         ("clearance_reached", clearance_reached)))
    _require_integer_tensor("motor_phase", motor_phase)
    _require_integer_tensor("recovery_count", recovery_count)
    _require_integer_tensor("required_frames", required_frames)
    for name, value in (
            ("event_resolved", event_resolved),
            ("recovery_rearmed", recovery_rearmed),
            ("handoff", handoff),
            ("same_string_handoff", same_string_handoff),
            ("clearance_required", clearance_required),
            ("clearance_reached", clearance_reached)):
        if value.dtype != torch.bool:
            raise TypeError(f"{name} must use torch.bool")
    if not time_to_target_s.is_floating_point() \
            or not torch.isfinite(time_to_target_s).all():
        raise ValueError("time_to_target_s must be a finite floating tensor")
    if torch.any(recovery_count < 0) or torch.any(required_frames < 1):
        raise ValueError("dual recovery frame counts are invalid")
    if torch.any(same_string_handoff & ~handoff):
        raise ValueError("same-string handoff must also be a handoff")
    if (isinstance(release_recover_phase, bool)
            or not isinstance(release_recover_phase, int)):
        raise TypeError("release_recover_phase must be an integer")
    approach_lead_s = float(approach_lead_s)
    if not math.isfinite(approach_lead_s) or approach_lead_s < 0.0:
        raise ValueError("approach_lead_s must be finite and non-negative")
    rearm_required = same_string_handoff | clearance_required
    rearm_ready = recovery_rearmed | (handoff & ~rearm_required)
    clearance_ready = ~clearance_required | clearance_reached
    return (
        (motor_phase == release_recover_phase)
        & ~event_resolved
        & (recovery_count >= required_frames)
        & rearm_ready
        & clearance_ready
        & (time_to_target_s <= approach_lead_s))


def strike_dual_recovery_progress(
        recovery_count: torch.Tensor,
        best_count: torch.Tensor,
        recovery_rearmed: torch.Tensor,
        recovery_active: torch.Tensor,
        required_frames: torch.Tensor,
        handoff: torch.Tensor,
        handoff_transition: torch.Tensor,
        clearance_required: torch.Tensor,
        clearance_reached: torch.Tensor,
        completion_recorded: torch.Tensor) -> dict[str, torch.Tensor]:
    _matching_shape_device(
        "recovery_count", recovery_count,
        (("best_count", best_count),
         ("recovery_rearmed", recovery_rearmed),
         ("recovery_active", recovery_active),
         ("required_frames", required_frames),
         ("handoff", handoff),
         ("handoff_transition", handoff_transition),
         ("clearance_required", clearance_required),
         ("clearance_reached", clearance_reached),
         ("completion_recorded", completion_recorded)))
    _require_integer_tensor("recovery_count", recovery_count)
    _require_integer_tensor("best_count", best_count)
    _require_integer_tensor("required_frames", required_frames)
    for name, value in (
            ("recovery_rearmed", recovery_rearmed),
            ("recovery_active", recovery_active),
            ("handoff", handoff),
            ("handoff_transition", handoff_transition),
            ("clearance_required", clearance_required),
            ("clearance_reached", clearance_reached),
            ("completion_recorded", completion_recorded)):
        if value.dtype != torch.bool:
            raise TypeError(f"{name} must use torch.bool")
    if (torch.any(recovery_count < 0) or torch.any(best_count < 0)
            or torch.any(required_frames < 1)):
        raise ValueError("dual recovery progress frame counts are invalid")
    eligible = torch.where(
        recovery_active & (handoff | recovery_rearmed),
        torch.minimum(recovery_count, required_frames),
        torch.zeros_like(recovery_count))
    next_best = torch.maximum(best_count, eligible)
    progress = (
        (next_best - best_count).to(torch.float32)
        / required_frames.to(torch.float32))
    completion_ready = torch.where(
        handoff, handoff_transition, recovery_rearmed)
    completion_ready &= ~clearance_required | clearance_reached
    complete_pulse = (
        recovery_active
        & ~completion_recorded
        & (next_best >= required_frames)
        & completion_ready)
    return {
        "best_count": next_best,
        "progress": progress,
        "complete_pulse": complete_pulse,
        "completion_recorded": completion_recorded | complete_pulse,
    }


def strike_timing_gate(
        physical_target_candidate: torch.Tensor,
        timing_ok: torch.Tensor,
        *,
        timing_required: bool,
) -> dict[str, torch.Tensor]:
    """Return independent timing-observation and success masks.

    When timing is active, every physical target candidate remains a timing
    sample, including attempts outside the current tolerance.  Only the
    success candidate is gated by ``timing_ok``.
    """
    _matching_bool_masks(
        "physical_target_candidate", physical_target_candidate,
        "timing_ok", timing_ok)
    if not isinstance(timing_required, bool):
        raise TypeError("timing_required must be bool")
    if timing_required:
        timing_sample = physical_target_candidate.clone()
        success_candidate = physical_target_candidate & timing_ok
    else:
        timing_sample = torch.zeros_like(physical_target_candidate)
        success_candidate = physical_target_candidate.clone()
    return {
        "timing_sample": timing_sample,
        "success_candidate": success_candidate,
    }


def strike_event_outcome_masks(
        physical_target_candidate: torch.Tensor,
        target_hit: torch.Tensor,
        miss_pulse: torch.Tensor) -> dict[str, torch.Tensor]:
    _matching_bool_masks(
        "physical_target_candidate", physical_target_candidate,
        "target_hit", target_hit)
    _matching_bool_masks(
        "physical_target_candidate", physical_target_candidate,
        "miss_pulse", miss_pulse)
    if torch.any(target_hit & ~physical_target_candidate):
        raise ValueError("target_hit must be a physical target candidate")
    newly_resolved = target_hit | miss_pulse
    physical_hit = physical_target_candidate & newly_resolved
    physical_miss = miss_pulse & ~physical_hit
    return {
        "newly_resolved": newly_resolved,
        "physical_hit": physical_hit,
        "physical_miss": physical_miss,
    }


def strike_directional_strum_outcomes(
        newly_resolved: torch.Tensor,
        physical_hit: torch.Tensor,
        is_strum: torch.Tensor,
        target_direction: torch.Tensor) -> dict[str, torch.Tensor]:
    _matching_bool_masks(
        "newly_resolved", newly_resolved,
        "physical_hit", physical_hit)
    _matching_bool_masks(
        "newly_resolved", newly_resolved,
        "is_strum", is_strum)
    if (not isinstance(target_direction, torch.Tensor)
            or target_direction.shape != newly_resolved.shape
            or target_direction.device != newly_resolved.device
            or target_direction.dtype == torch.bool
            or target_direction.is_floating_point()):
        raise TypeError(
            "target_direction must be a matching integer tensor")
    if torch.any(physical_hit & ~newly_resolved):
        raise ValueError("physical_hit must be a resolved event")
    if torch.any((target_direction != -1) & (target_direction != 1)):
        raise ValueError("target_direction must contain only -1 or +1")
    resolved_strum = newly_resolved & is_strum
    down_event = resolved_strum & (target_direction == 1)
    up_event = resolved_strum & (target_direction == -1)
    return {
        "down_event": down_event,
        "up_event": up_event,
        "down_completed": physical_hit & down_event,
        "up_completed": physical_hit & up_event,
    }


def strike_traversal_timing(
        release_time_s: torch.Tensor,
        release_valid: torch.Tensor,
        traversal: torch.Tensor,
        target_center_s: torch.Tensor,
        target_offsets_s: torch.Tensor,
        left_tolerance_s: torch.Tensor,
        right_tolerance_s: torch.Tensor) -> dict[str, torch.Tensor]:
    if (release_time_s.ndim != 2
            or target_offsets_s.shape != release_time_s.shape
            or release_valid.shape != release_time_s.shape
            or traversal.shape != release_time_s.shape):
        raise ValueError("strike traversal timing tensors must have shape [N,S]")
    if release_valid.dtype != torch.bool or traversal.dtype != torch.bool:
        raise TypeError("release_valid and traversal must use torch.bool")
    if not release_time_s.is_floating_point() \
            or not target_offsets_s.is_floating_point():
        raise TypeError("strike traversal times must use floating tensors")
    vectors = (target_center_s, left_tolerance_s, right_tolerance_s)
    if any(value.shape != release_time_s.shape[:1] for value in vectors):
        raise ValueError("strike traversal timing vectors must have shape [N]")
    if any(value.device != release_time_s.device for value in (
            release_valid, traversal, target_offsets_s, *vectors)):
        raise ValueError("strike traversal timing tensors must share a device")
    if (not torch.isfinite(release_time_s).all()
            or not torch.isfinite(target_offsets_s).all()
            or any(not torch.isfinite(value).all() for value in vectors)):
        raise ValueError("strike traversal timing tensors must be finite")
    if torch.any(left_tolerance_s <= 0.0) or torch.any(right_tolerance_s <= 0.0):
        raise ValueError("strike timing tolerances must be positive")

    required_valid = release_valid & traversal
    complete = ((release_valid & traversal) == traversal).all(dim=1)
    target_time = target_center_s[:, None] + target_offsets_s
    error = release_time_s - target_time
    error = torch.where(required_valid, error, torch.zeros_like(error))
    timing_ok_by_string = (
        (error >= -left_tolerance_s[:, None])
        & (error <= right_tolerance_s[:, None])
        & required_valid)
    timing_ok = complete & ((~traversal) | timing_ok_by_string).all(dim=1)
    early = complete & (
        traversal & (error < -left_tolerance_s[:, None])).any(dim=1)
    late = complete & (
        traversal & (error > right_tolerance_s[:, None])).any(dim=1)
    count = traversal.sum(dim=1).clamp_min(1).to(error.dtype)
    rms = torch.sqrt((error.square() * traversal).sum(dim=1) / count)
    masked_abs = torch.where(
        traversal, error.abs(), torch.full_like(error, -1.0))
    worst_index = masked_abs.argmax(dim=1)
    worst_error = error.gather(1, worst_index[:, None])[:, 0]

    inf = torch.full_like(target_offsets_s, float("inf"))
    neg_inf = torch.full_like(target_offsets_s, float("-inf"))
    first_index = torch.where(traversal, target_offsets_s, inf).argmin(dim=1)
    last_index = torch.where(traversal, target_offsets_s, neg_inf).argmax(dim=1)
    rows = torch.arange(release_time_s.shape[0], device=release_time_s.device)
    actual_duration = (
        release_time_s[rows, last_index] - release_time_s[rows, first_index])
    planned_duration = (
        target_offsets_s[rows, last_index]
        - target_offsets_s[rows, first_index])
    duration_error = torch.where(
        complete, actual_duration - planned_duration,
        torch.zeros_like(actual_duration))
    return {
        "complete": complete,
        "timing_ok": timing_ok,
        "early": early,
        "late": late,
        "per_string_error_s": error,
        "worst_error_s": worst_error,
        "rms_error_s": rms,
        "actual_duration_s": actual_duration,
        "planned_duration_s": planned_duration,
        "duration_error_s": duration_error,
    }


def strike_physical_target_candidate(
        target_release: torch.Tensor,
        event_resolved: torch.Tensor,
        nonfinite: torch.Tensor) -> torch.Tensor:
    """Apply only matcher-contract gates to a physical target release.

    Motor phase and entry-point distance remain trajectory diagnostics and
    shaping signals.  They are deliberately absent here: a valid target
    crossing must not become a false positive solely because an internal
    planner phase or one hidden 6 mm waypoint disagreed with the physics.
    """
    _matching_bool_masks(
        "target_release", target_release,
        "event_resolved", event_resolved)
    _matching_bool_masks(
        "target_release", target_release,
        "nonfinite", nonfinite)
    return target_release & ~event_resolved & ~nonfinite


def strike_false_positive_count(
        release: torch.Tensor,
        target_hit: torch.Tensor,
        blocked_wait_rearm: torch.Tensor) -> torch.Tensor:
    """Classify wrong/extra releases and suppressed duplicate crossings.

    A successful target release is subtracted once.  Detector crossings that
    were blocked only because the string had not re-armed remain explicit
    duplicate false positives instead of disappearing from the objective.
    """
    if not all(isinstance(value, torch.Tensor) for value in (
            release, target_hit, blocked_wait_rearm)):
        raise TypeError("strike crossing classifications must be tensors")
    if release.dtype != torch.bool or blocked_wait_rearm.dtype != torch.bool:
        raise TypeError("release and blocked_wait_rearm must use torch.bool")
    if target_hit.dtype != torch.bool:
        raise TypeError("target_hit must use torch.bool")
    if release.ndim != 2 or blocked_wait_rearm.shape != release.shape:
        raise ValueError(
            "release and blocked_wait_rearm must share shape (N, strings)")
    if target_hit.shape != release.shape[:1]:
        raise ValueError("target_hit must have shape (N,)")
    if (release.device != target_hit.device
            or release.device != blocked_wait_rearm.device):
        raise ValueError("strike crossing classifications must share a device")
    classified_release = (
        release.sum(dim=1) - target_hit.to(torch.long)).clamp_min(0)
    duplicates = blocked_wait_rearm.sum(dim=1)
    return (classified_release + duplicates).to(torch.float32)


def strike_release_recovery_context(
        release: torch.Tensor,
        subframe_t: torch.Tensor,
        crossing_pos_g: torch.Tensor,
        direction: torch.Tensor) -> dict[str, torch.Tensor]:
    """Select the final physical RELEASE in each swept control frame.

    A bad policy may cross several strings in one frame.  Follow-through starts
    after the last such crossing, independently of which release the matcher
    marked correct.
    """
    if not all(isinstance(value, torch.Tensor) for value in (
            release, subframe_t, crossing_pos_g, direction)):
        raise TypeError("release recovery context inputs must be tensors")
    if release.dtype != torch.bool:
        raise TypeError("release must use torch.bool")
    if release.ndim != 2 or subframe_t.shape != release.shape:
        raise ValueError("release/subframe_t must share shape (N, strings)")
    if crossing_pos_g.shape != (*release.shape, 3):
        raise ValueError("crossing_pos_g must have shape (N, strings, 3)")
    if direction.shape != release.shape:
        raise ValueError("direction must match release shape")
    _require_integer_tensor("direction", direction)
    if (not subframe_t.is_floating_point()
            or not crossing_pos_g.is_floating_point()):
        raise TypeError("release recovery geometry must use floating dtypes")
    if (release.device != subframe_t.device
            or release.device != crossing_pos_g.device
            or release.device != direction.device):
        raise ValueError("release recovery context inputs must share a device")
    if (not torch.isfinite(subframe_t[release]).all()
            or not torch.isfinite(crossing_pos_g[release]).all()):
        raise ValueError("released crossing geometry must be finite")

    released = release.any(dim=1)
    latest_t = torch.where(
        release, subframe_t, torch.full_like(subframe_t, -1.0))
    string = latest_t.argmax(dim=1)
    rows = torch.arange(release.shape[0], device=release.device)
    lane_y = crossing_pos_g[rows, string, 1]
    release_direction = direction[rows, string].to(torch.long)
    if torch.any(
            released
            & (release_direction != -1)
            & (release_direction != 1)):
        raise ValueError("every released crossing must have direction -1 or +1")
    string = torch.where(released, string, torch.zeros_like(string))
    lane_y = torch.where(released, lane_y, torch.zeros_like(lane_y))
    release_direction = torch.where(
        released, release_direction, torch.ones_like(release_direction))
    return {
        "released": released,
        "release_string": string,
        "release_lane_y": lane_y,
        "release_direction": release_direction,
    }


def strike_recovery_incomplete_timeout(
        stage_timeout: torch.Tensor,
        recovery_context_valid: torch.Tensor,
        recovery_count: torch.Tensor,
        recovery_rearmed: torch.Tensor,
        *,
        recovery_frames: int) -> torch.Tensor:
    """Fail a horizon that cuts off either follow-through or detector re-arm."""
    _matching_bool_masks(
        "stage_timeout", stage_timeout,
        "recovery_context_valid", recovery_context_valid)
    _matching_bool_masks(
        "stage_timeout", stage_timeout,
        "recovery_rearmed", recovery_rearmed)
    if not isinstance(recovery_count, torch.Tensor):
        raise TypeError("recovery_count must be a torch.Tensor")
    if recovery_count.shape != stage_timeout.shape:
        raise ValueError("recovery_count must match stage_timeout shape")
    if recovery_count.device != stage_timeout.device:
        raise ValueError("recovery_count must share stage_timeout device")
    _require_integer_tensor("recovery_count", recovery_count)
    if torch.any(recovery_count < 0):
        raise ValueError("recovery_count must be non-negative")
    if (isinstance(recovery_frames, bool)
            or not isinstance(recovery_frames, int)
            or recovery_frames < 1):
        raise ValueError("recovery_frames must be a positive integer")
    recovery_complete = (
        (recovery_count >= recovery_frames) & recovery_rearmed)
    return (
        stage_timeout & recovery_context_valid & ~recovery_complete)


def strike_ready_latch(
        at_ready: torch.Tensor,
        grip_success: torch.Tensor,
        ready_streak: torch.Tensor,
        ready_success: torch.Tensor,
        *,
        hold_frames: int) -> dict[str, torch.Tensor]:
    """Latch the first valid ready hold without ending the A1 episode.

    A fixed-length A1 episode prevents the policy from increasing return by
    deliberately staying just outside the success boundary.  The returned
    ``ready_pulse`` is one-shot even if the hand leaves and later re-enters.
    """
    _matching_bool_masks(
        "at_ready", at_ready,
        "grip_success", grip_success)
    _matching_bool_masks(
        "at_ready", at_ready,
        "ready_success", ready_success)
    if not isinstance(ready_streak, torch.Tensor):
        raise TypeError("ready_streak must be a torch.Tensor")
    if ready_streak.dtype == torch.bool or ready_streak.is_floating_point():
        raise TypeError("ready_streak must use an integer dtype")
    if ready_streak.shape != at_ready.shape:
        raise ValueError("ready_streak must match at_ready shape")
    if ready_streak.device != at_ready.device:
        raise ValueError("ready_streak must share at_ready device")
    if (isinstance(hold_frames, bool)
            or not isinstance(hold_frames, int)
            or hold_frames < 1):
        raise ValueError("hold_frames must be a positive integer")

    next_streak = torch.where(
        at_ready & grip_success,
        ready_streak + 1,
        torch.zeros_like(ready_streak))
    ready_pulse = (
        (next_streak == hold_frames)
        & ~ready_success)
    return {
        "ready_streak": next_streak,
        "ready_pulse": ready_pulse,
        "ready_success": ready_success | ready_pulse,
    }


def strike_ready_episode_resolution(
        stage_timeout: torch.Tensor,
        ready_success: torch.Tensor) -> dict[str, torch.Tensor]:
    """Resolve A1 only at its fixed horizon and label success truthfully."""
    _matching_bool_masks(
        "stage_timeout", stage_timeout,
        "ready_success", ready_success)
    return {
        "done": stage_timeout.clone(),
        "success": stage_timeout & ready_success,
        "miss": stage_timeout & ~ready_success,
    }


def strike_resolved_episode_done(
        event_resolved: torch.Tensor,
        motor_phase: torch.Tensor,
        recovery_count: torch.Tensor,
        recovery_rearmed: torch.Tensor,
        stage_timeout: torch.Tensor,
        *,
        release_recover_phase: int,
        recovery_frames: int,
) -> dict[str, torch.Tensor]:
    """Finish a resolved event after recovery only when a release occurred."""
    _matching_bool_masks(
        "event_resolved", event_resolved,
        "stage_timeout", stage_timeout)
    _matching_bool_masks(
        "event_resolved", event_resolved,
        "recovery_rearmed", recovery_rearmed)
    for name, value in (
            ("motor_phase", motor_phase),
            ("recovery_count", recovery_count)):
        if not isinstance(value, torch.Tensor):
            raise TypeError(f"{name} must be a torch.Tensor")
        if value.dtype == torch.bool or value.is_floating_point():
            raise TypeError(f"{name} must use an integer dtype")
        if value.shape != event_resolved.shape:
            raise ValueError(f"{name} must match event_resolved shape")
        if value.device != event_resolved.device:
            raise ValueError(f"{name} must share event_resolved device")
    if isinstance(release_recover_phase, bool):
        raise TypeError("release_recover_phase must be an integer")
    try:
        release_phase = int(release_recover_phase)
    except (TypeError, ValueError) as exc:
        raise TypeError(
            "release_recover_phase must be an integer") from exc
    if release_phase != release_recover_phase:
        raise ValueError("release_recover_phase must be an integer")
    if (isinstance(recovery_frames, bool)
            or not isinstance(recovery_frames, int)
            or recovery_frames < 1):
        raise ValueError("recovery_frames must be a positive integer")

    recovery_finished = (
        (motor_phase != release_phase)
        | ((recovery_count >= recovery_frames) & recovery_rearmed))
    done = (
        (event_resolved & recovery_finished)
        | stage_timeout)
    return {
        "recovery_finished": recovery_finished,
        "done": done,
    }


__all__ = [
    "strike_rational_timing_quality",
    "strike_timed_approach_open",
    "strike_early_timing_cost",
    "strike_premature_release",
    "strike_balanced_practice_direction",
    "strike_focused_practice_direction",
    "strike_uniform_traversal_offsets",
    "strike_limit_traversal_span",
    "strike_next_traversal_string",
    "strike_strum_terminal_progress",
    "strike_song_continuing_phase",
    "strike_completed_recovery_frames",
    "strike_clean_recovery_progress",
    "strike_recovery_clearance_target",
    "strike_handoff_path_clearance",
    "strike_clearance_waypoint_state",
    "strike_dual_recovery_plan",
    "strike_dual_recovery_to_approach",
    "strike_dual_recovery_progress",
    "strike_false_positive_count",
    "strike_release_recovery_context",
    "strike_recovery_incomplete_timeout",
    "strike_motion_target_context",
    "strike_physical_target_candidate",
    "strike_ready_latch",
    "strike_ready_episode_resolution",
    "strike_recovery_to_approach",
    "strike_timing_gate",
    "strike_event_outcome_masks",
    "strike_directional_strum_outcomes",
    "strike_traversal_timing",
    "strike_resolved_episode_done",
]
