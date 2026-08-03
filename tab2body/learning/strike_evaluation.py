"""Pure, stage-aware evaluation gates for pick-only strike learning."""
from __future__ import annotations

import math
from typing import Mapping, Sequence

from .strike_curriculum import (
    A0_PICK_GRIP,
    A1_TIP_READY,
    A2_FREE_CROSSING,
    A3_TIMED_CROSSING,
    A4_ZONE_CONTROL,
    STRIKE_STAGES,
)


_METRIC_ALIASES = {
    "grip_success_rate": (
        "grip_success_rate", "curriculum_grip_success_rate"),
    "tip_ready_success_rate": (
        "tip_ready_success_rate", "curriculum_tip_ready_success_rate"),
    "precision": (
        "precision", "strike_precision"),
    "release_recall": (
        "release_recall", "curriculum_release_recall"),
    "false_positive_rate": (
        "false_positive_rate", "release_false_positive_rate",
        "curriculum_false_positive_rate"),
    "strike_f1": (
        "strike_f1", "curriculum_strike_f1"),
    "timing_p95_ms": (
        "timing_p95_ms", "curriculum_timing_p95_ms"),
    "zone_success_rate": (
        "zone_success_rate", "curriculum_zone_success_rate"),
}


def _required_metric(metrics: Mapping[str, object], name: str) -> float:
    for key in _METRIC_ALIASES[name]:
        if key not in metrics:
            continue
        try:
            value = float(metrics[key])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{key} must be a finite scalar") from exc
        if not math.isfinite(value):
            raise ValueError(f"{key} must be a finite scalar")
        if name == "timing_p95_ms":
            if value < 0.0:
                raise ValueError("timing_p95_ms must be non-negative")
        elif not 0.0 <= value <= 1.0:
            raise ValueError(f"{key} must be in [0, 1]")
        return value
    raise ValueError(f"missing applicable strike metric: {name}")


def _validate_gate(value, name):
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be finite and in [0, 1]")
    return value


def strike_evaluation_gate_summary(
        metrics: Mapping[str, object],
        episode_rows: Sequence[Mapping[str, object]],
        *,
        stage: str,
        timing_tolerance_ms: float = 50.0,
        safety_passed: bool = True,
        grip_success_gate: float = 0.90,
        tip_ready_success_gate: float = 0.90,
        precision_gate: float = 0.98,
        release_recall_gate: float = 0.98,
        false_positive_rate_gate: float = 0.02,
        strike_f1_gate: float = 0.98,
        zone_success_gate: float = 0.95):
    """Return explicit gates applicable to one strike curriculum stage.

    Earlier skills remain applicable at later stages.  Metrics belonging only
    to a future stage are neither required nor allowed to influence ``passed``.
    """
    if stage not in STRIKE_STAGES:
        raise ValueError(f"unknown strike evaluation stage: {stage!r}")
    if not episode_rows:
        raise ValueError("strike evaluation requires at least one episode")

    grip_success_gate = _validate_gate(
        grip_success_gate, "grip_success_gate")
    tip_ready_success_gate = _validate_gate(
        tip_ready_success_gate, "tip_ready_success_gate")
    precision_gate = _validate_gate(
        precision_gate, "precision_gate")
    release_recall_gate = _validate_gate(
        release_recall_gate, "release_recall_gate")
    false_positive_rate_gate = _validate_gate(
        false_positive_rate_gate, "false_positive_rate_gate")
    strike_f1_gate = _validate_gate(strike_f1_gate, "strike_f1_gate")
    zone_success_gate = _validate_gate(
        zone_success_gate, "zone_success_gate")
    timing_tolerance_ms = float(timing_tolerance_ms)
    if (not math.isfinite(timing_tolerance_ms)
            or timing_tolerance_ms <= 0.0):
        raise ValueError("timing_tolerance_ms must be finite and positive")

    stage_index = STRIKE_STAGES.index(stage)
    applicability = {
        "grip": True,
        "tip_ready": stage_index >= STRIKE_STAGES.index(A1_TIP_READY),
        "release": stage_index >= STRIKE_STAGES.index(A2_FREE_CROSSING),
        "timing": stage_index >= STRIKE_STAGES.index(A3_TIMED_CROSSING),
        "zone": stage_index >= STRIKE_STAGES.index(A4_ZONE_CONTROL),
    }

    grip_rate = _required_metric(metrics, "grip_success_rate")
    grip_passed = grip_rate >= grip_success_gate

    ready_rate = None
    ready_passed = True
    if applicability["tip_ready"]:
        ready_rate = _required_metric(metrics, "tip_ready_success_rate")
        ready_passed = ready_rate >= tip_ready_success_gate

    precision = None
    release_recall = None
    false_positive_rate = None
    release_passed = True
    if applicability["release"]:
        precision = _required_metric(metrics, "precision")
        release_recall = _required_metric(metrics, "release_recall")
        false_positive_rate = _required_metric(
            metrics, "false_positive_rate")
        release_passed = (
            precision >= precision_gate
            and release_recall >= release_recall_gate
            and false_positive_rate <= false_positive_rate_gate
        )

    strike_f1 = None
    timing_p95_ms = None
    timing_passed = True
    if applicability["timing"]:
        strike_f1 = _required_metric(metrics, "strike_f1")
        timing_p95_ms = _required_metric(metrics, "timing_p95_ms")
        timing_passed = (
            strike_f1 >= strike_f1_gate
            and timing_p95_ms <= timing_tolerance_ms
        )

    zone_rate = None
    zone_passed = True
    if applicability["zone"]:
        zone_rate = _required_metric(metrics, "zone_success_rate")
        zone_passed = zone_rate >= zone_success_gate

    try:
        completion_rate = sum(
            float(bool(row["goal_finished"])) for row in episode_rows
        ) / len(episode_rows)
        failure_rate = sum(
            float(bool(row["failure_termination"])) for row in episode_rows
        ) / len(episode_rows)
    except KeyError as exc:
        raise ValueError(
            f"episode row is missing required field: {exc.args[0]}") from exc
    full_episode_passed = (
        completion_rate >= 1.0 - 1e-9
        and failure_rate <= 1e-9
    )

    task_passed = bool(
        grip_passed
        and ready_passed
        and release_passed
        and timing_passed
        and zone_passed
        and full_episode_passed
    )
    passed = task_passed and bool(safety_passed)
    return {
        "stage": stage,
        "stage_index": stage_index,
        "grip_applicable": True,
        "grip_success_rate": grip_rate,
        "gate_grip_success_rate": grip_success_gate,
        "grip_passed": bool(grip_passed),
        "tip_ready_applicable": applicability["tip_ready"],
        "tip_ready_success_rate": ready_rate,
        "gate_tip_ready_success_rate": tip_ready_success_gate,
        "tip_ready_passed": bool(ready_passed),
        "release_applicable": applicability["release"],
        "precision": precision,
        "release_recall": release_recall,
        "false_positive_rate": false_positive_rate,
        "gate_precision": precision_gate,
        "gate_release_recall": release_recall_gate,
        "gate_false_positive_rate": false_positive_rate_gate,
        "release_passed": bool(release_passed),
        "timing_applicable": applicability["timing"],
        "strike_f1": strike_f1,
        "timing_p95_ms": timing_p95_ms,
        "gate_strike_f1": strike_f1_gate,
        "gate_timing_p95_ms": timing_tolerance_ms,
        "timing_passed": bool(timing_passed),
        "zone_applicable": applicability["zone"],
        "zone_success_rate": zone_rate,
        "gate_zone_success_rate": zone_success_gate,
        "zone_passed": bool(zone_passed),
        "full_episode_completion_rate": completion_rate,
        "failure_termination_rate": failure_rate,
        "full_episode_passed": bool(full_episode_passed),
        "task_passed": task_passed,
        "safety_passed": bool(safety_passed),
        "human_like_review_required": True,
        "passed": bool(passed),
    }


__all__ = ["strike_evaluation_gate_summary"]
