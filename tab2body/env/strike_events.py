"""Pure tensor rules for ready, timing and post-event episode completion.

These helpers intentionally avoid Isaac Gym so the two easy-to-regress
contracts can be tested on CPU:

* A1 ready success is latched once while its episode keeps a fixed horizon;
* timing statistics observe a physical target crossing before the tolerance
  gate filters successful hits;
* only a real release waits for recovery, while a miss can finish immediately.
"""
from __future__ import annotations

import torch


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
        stage_timeout: torch.Tensor,
        *,
        release_recover_phase: int,
        recovery_frames: int,
) -> dict[str, torch.Tensor]:
    """Finish a resolved event after recovery only when a release occurred."""
    _matching_bool_masks(
        "event_resolved", event_resolved,
        "stage_timeout", stage_timeout)
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
        | (recovery_count >= recovery_frames))
    done = (
        (event_resolved & recovery_finished)
        | stage_timeout)
    return {
        "recovery_finished": recovery_finished,
        "done": done,
    }


__all__ = [
    "strike_ready_latch",
    "strike_ready_episode_resolution",
    "strike_timing_gate",
    "strike_resolved_episode_done",
]
