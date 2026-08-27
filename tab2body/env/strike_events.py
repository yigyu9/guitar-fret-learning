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
    protected = torch.zeros(previous.shape[0], device=previous.device)
    wrong_direction = torch.zeros_like(protected)
    order_violation = torch.zeros_like(protected)
    duplicate = torch.zeros_like(protected)
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
        protected += (active & ~target).to(protected.dtype)
        wrong_direction += (active & target & ~direction_ok).to(protected.dtype)
        duplicate += (active & target & direction_ok & already).to(
            protected.dtype)
        order_violation += (
            active & target & direction_ok & ~already & ~expected_now
        ).to(protected.dtype)
        accepted[rows, string_index] |= can_accept
        accepted_now[rows, string_index] |= can_accept

    complete = ((accepted & traversal) == traversal).all(dim=1)
    return {
        "accepted_release": accepted_now,
        "accumulated_release": accepted,
        "complete": complete,
        "protected_crossing_count": protected,
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
        ("recovery_string", recovery_string),
        ("recovery_lane_y", recovery_lane_y),
        ("recovery_direction", recovery_direction),
        ("recovery_context_valid", recovery_context_valid),
        ("motor_phase", motor_phase),
    )
    _matching_shape_device("event_string", event_string, values)
    _require_integer_tensor("event_string", event_string)
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
            torch.ones_like(recovery_direction)),
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


def strike_a4_continuing_phase(
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
        release_recover_phase: int) -> torch.Tensor:
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
    return torch.where(
        action_phase == release_recover_phase,
        recovery_count + 1,
        torch.zeros_like(recovery_count))


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
    "strike_a4_continuing_phase",
    "strike_completed_recovery_frames",
    "strike_false_positive_count",
    "strike_release_recovery_context",
    "strike_recovery_incomplete_timeout",
    "strike_motion_target_context",
    "strike_physical_target_candidate",
    "strike_ready_latch",
    "strike_ready_episode_resolution",
    "strike_recovery_to_approach",
    "strike_timing_gate",
    "strike_resolved_episode_done",
]
