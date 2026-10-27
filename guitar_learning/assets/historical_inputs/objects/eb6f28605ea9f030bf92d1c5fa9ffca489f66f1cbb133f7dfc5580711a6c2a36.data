"""Task-neutral sounding-fret readiness used by the Synchronizer."""
from __future__ import annotations

from dataclasses import dataclass

import torch


FRET_READINESS_SCHEMA = "tab2body.fret_readiness.sounding_fret.v1"


@dataclass(frozen=True)
class FretReadiness:
    target_active_mask: torch.Tensor
    effective_sounding_fret: torch.Tensor
    ready_mask: torch.Tensor
    interfering_mask: torch.Tensor
    harmless_extra_press_mask: torch.Tensor


@dataclass(frozen=True)
class StrikeReadiness:
    ready: torch.Tensor
    phase_ready: torch.Tensor
    grip_ready: torch.Tensor
    entry_ready: torch.Tensor
    entry_side_ready: torch.Tensor
    detector_ready: torch.Tensor
    direction_ready: torch.Tensor


def evaluate_sounding_fret_readiness(active_press_cells, target_frets):
    """Evaluate musical pitch from occupied virtual fret cells.

    ``active_press_cells`` has shape ``[N,6,F]`` where index zero denotes
    physical fret 1.  Contact force is intentionally absent: the simulator's
    geometric string/surface detector decides whether a cell is occupied.
    The sounding fret is the highest occupied fret on a string, matching real
    string shortening.  Consequently a lower extra press is harmless when the
    target fret is also occupied, while any higher press changes the pitch.

    ``target_frets`` is ``-1`` for a non-audible string, ``0`` for open, and a
    positive fret otherwise.  Finger identity is not part of musical success;
    it may be logged separately as fingering adherence.
    """
    if not isinstance(active_press_cells, torch.Tensor):
        raise TypeError("active_press_cells must be a torch.Tensor")
    if active_press_cells.ndim != 3 or active_press_cells.shape[1] != 6:
        raise ValueError("active_press_cells must have shape [N,6,F]")
    if active_press_cells.dtype != torch.bool:
        raise TypeError("active_press_cells must use torch.bool")
    if active_press_cells.shape[2] < 1:
        raise ValueError("active_press_cells must contain at least one fret")
    targets = torch.as_tensor(
        target_frets, dtype=torch.long, device=active_press_cells.device)
    if targets.shape != active_press_cells.shape[:2]:
        raise ValueError("target_frets must have shape [N,6]")
    if bool((targets < -1).any().item()):
        raise ValueError("target_frets must use -1, 0, or a positive fret")
    if bool((targets > active_press_cells.shape[2]).any().item()):
        raise ValueError("target_fret exceeds the physical fret-cell count")

    fret_numbers = torch.arange(
        1, active_press_cells.shape[2] + 1,
        dtype=torch.long, device=active_press_cells.device)
    sounding = torch.where(
        active_press_cells,
        fret_numbers.view(1, 1, -1),
        torch.zeros(1, 1, active_press_cells.shape[2],
                    dtype=torch.long, device=active_press_cells.device),
    ).amax(dim=-1)
    target_active = targets >= 0
    ready = target_active & (sounding == targets)
    interfering = target_active & (sounding != targets)
    target_present = (
        (targets > 0)
        & active_press_cells.gather(
            2, (targets.clamp_min(1) - 1).unsqueeze(-1)).squeeze(-1))
    lower_any = (
        active_press_cells
        & (fret_numbers.view(1, 1, -1) < targets.unsqueeze(-1))
    ).any(dim=-1)
    harmless_extra = ready & target_present & lower_any
    return FretReadiness(
        target_active_mask=target_active,
        effective_sounding_fret=sounding,
        ready_mask=ready,
        interfering_mask=interfering,
        harmless_extra_press_mask=harmless_extra,
    )


def evaluate_strike_readiness(
        motor_phase, grip_success, entry_distance_m, detector_armed,
        approach_direction_ok, entry_signed_distance_m, *,
        approach_phase: int, entry_distance_threshold_m: float,
        pre_side_epsilon_m: float):
    """Reduce right-hand physical state to the supervisor's readiness bit.

    This is deliberately stricter than actor intent: the pick must be in the
    approach phase, retain its grip, be near the entry target *and still on the
    pre-crossing side* of the planned traversal plane, have the first-string
    detector armed, and move in an admissible direction.  A distance-only test
    is unsafe because a pick that already crossed the plane may still be close
    to the entry target.  Negative signed distance denotes the pre side.  The
    shared physical task computes these facts from its one Strike detector
    snapshot before calling the Synchronizer.
    """
    phase = torch.as_tensor(motor_phase, dtype=torch.long)
    if phase.ndim != 1:
        raise ValueError("motor_phase must have shape [N]")
    device = phase.device
    grip = torch.as_tensor(grip_success, dtype=torch.bool, device=device)
    distance = torch.as_tensor(
        entry_distance_m, dtype=torch.float32, device=device)
    armed = torch.as_tensor(detector_armed, dtype=torch.bool, device=device)
    direction = torch.as_tensor(
        approach_direction_ok, dtype=torch.bool, device=device)
    signed_distance = torch.as_tensor(
        entry_signed_distance_m, dtype=torch.float32, device=device)
    expected = phase.shape
    if any(value.shape != expected for value in (
            grip, distance, armed, direction, signed_distance)):
        raise ValueError("Strike readiness inputs must share shape [N]")
    if (not torch.isfinite(distance).all()
            or not torch.isfinite(signed_distance).all()):
        raise ValueError("Strike entry distances must be finite")
    threshold = float(entry_distance_threshold_m)
    if not 0.0 < threshold < float("inf"):
        raise ValueError("entry distance threshold must be finite and positive")
    epsilon = float(pre_side_epsilon_m)
    if not 0.0 <= epsilon < float("inf"):
        raise ValueError("pre-side epsilon must be finite and non-negative")
    phase_ready = phase == int(approach_phase)
    entry_ready = distance <= threshold
    entry_side_ready = signed_distance < -epsilon
    ready = (
        phase_ready & grip & entry_ready & entry_side_ready
        & armed & direction)
    return StrikeReadiness(
        ready=ready,
        phase_ready=phase_ready,
        grip_ready=grip,
        entry_ready=entry_ready,
        entry_side_ready=entry_side_ready,
        detector_ready=armed,
        direction_ready=direction,
    )


__all__ = [
    "FRET_READINESS_SCHEMA",
    "FretReadiness",
    "StrikeReadiness",
    "evaluate_sounding_fret_readiness",
    "evaluate_strike_readiness",
]
