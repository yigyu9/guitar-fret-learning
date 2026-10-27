"""Pure, stage-aware evaluation gates for single-pick and strum learning."""
from __future__ import annotations

import math
from typing import Mapping, Optional, Sequence

from .strike_curriculum import (
    A0_PICK_GRIP,
    A1_TIP_READY,
    A2_SINGLE_CROSSING,
    A3_TIMED_SINGLE,
    S0_TWO_STRING_STRUM,
    S1_STRUM_SPAN,
    S2_TIMED_STRUM,
    S3_SONG_INTEGRATION,
    STRIKE_STAGES,
)
from tab2body.strike_contract import (
    STRUM_MICROTIMING_STAGES,
    STRUM_STAGES,
    TIMED_STAGES,
    ZONE_STAGES,
)


_METRIC_ALIASES = {
    "grip_success_rate": (
        "strike_grip_success_rate", "grip_success_rate",
        "curriculum_grip_success_rate"),
    "grip_quality_mean": (
        "strike_grip_quality_mean", "grip_quality_mean",
        "curriculum_grip_quality_mean"),
    "grip_quality_p05": (
        "strike_grip_quality_p05", "grip_quality_p05"),
    "grip_quality_min": (
        "strike_grip_quality_min", "grip_quality_min"),
    "pinch_quality_mean": (
        "strike_grip_pinch_quality_mean", "pinch_quality_mean"),
    "free_quality_mean": (
        "strike_grip_free_quality_mean", "free_quality_mean"),
    "grip_bad_frame_rate": (
        "strike_grip_bad_frame_rate", "grip_bad_frame_rate"),
    "tip_ready_success_rate": (
        "strike_tip_ready_success_rate", "tip_ready_success_rate",
        "curriculum_tip_ready_success_rate"),
    "precision": (
        "strike_precision", "precision"),
    "release_recall": (
        "strike_release_recall", "release_recall",
        "curriculum_release_recall"),
    "false_positive_rate": (
        "strike_false_positive_rate", "false_positive_rate",
        "release_false_positive_rate",
        "curriculum_false_positive_rate"),
    "strike_f1": (
        "strike_episode_f1", "strike_f1", "curriculum_strike_f1"),
    "timing_p95_ms": (
        "strike_timing_p95_ms", "timing_p95_ms",
        "curriculum_timing_p95_ms"),
    "timing_pass_rate": (
        "strike_timing_pass_rate", "timing_pass_rate",
        "curriculum_timing_pass_rate"),
    "timing_signed_mean_ms": (
        "strike_timing_signed_mean_ms", "timing_signed_mean_ms"),
    "timing_signed_p10_ms": (
        "strike_timing_signed_p10_ms", "timing_signed_p10_ms"),
    "timing_signed_p90_ms": (
        "strike_timing_signed_p90_ms", "timing_signed_p90_ms"),
    "strum_timing_rms_ms": (
        "strike_strum_timing_rms_ms", "strum_timing_rms_ms",
        "curriculum_strum_timing_rms_ms"),
    "strum_sweep_duration_mae_ms": (
        "strike_strum_sweep_duration_mae_ms",
        "strum_sweep_duration_mae_ms",
        "curriculum_strum_sweep_duration_mae_ms"),
    "zone_success_rate": (
        "strike_zone_success_rate", "zone_success_rate",
        "curriculum_zone_success_rate"),
    "recovery_completion_rate": (
        "strike_recovery_completion_rate", "recovery_completion_rate",
        "curriculum_recovery_completion_rate"),
    "scheduled_recovery_completion_rate": (
        "strike_scheduled_recovery_completion_rate",
        "scheduled_recovery_completion_rate"),
    "conditional_recovery_completion_rate": (
        "strike_conditional_recovery_completion_rate",
        "conditional_recovery_completion_rate"),
    "end_to_end_recovery_completion_rate": (
        "strike_end_to_end_recovery_completion_rate",
        "end_to_end_recovery_completion_rate"),
    "worst_direction_completion_rate": (
        "strike_worst_direction_completion_rate",
        "worst_direction_completion_rate"),
    "full_recovery_completion_rate": (
        "strike_full_recovery_completion_rate",
        "full_recovery_completion_rate"),
    "handoff_recovery_completion_rate": (
        "strike_handoff_recovery_completion_rate",
        "handoff_recovery_completion_rate"),
}


def _required_metric(metrics: Mapping[str, object], name: str) -> float:
    for key in _METRIC_ALIASES[name]:
        if key not in metrics:
            continue
        if isinstance(metrics[key], bool):
            raise ValueError(f"{key} must be a finite scalar")
        try:
            value = float(metrics[key])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{key} must be a finite scalar") from exc
        if not math.isfinite(value):
            raise ValueError(f"{key} must be a finite scalar")
        if name in (
                "timing_signed_mean_ms", "timing_signed_p10_ms",
                "timing_signed_p90_ms"):
            pass
        elif name in (
                "timing_p95_ms", "strum_timing_rms_ms",
                "strum_sweep_duration_mae_ms"):
            if value < 0.0:
                raise ValueError("timing_p95_ms must be non-negative")
        elif not 0.0 <= value <= 1.0:
            raise ValueError(f"{key} must be in [0, 1]")
        return value
    raise ValueError(f"missing applicable strike metric: {name}")


def _validate_gate(value, name):
    if isinstance(value, bool):
        raise ValueError(f"{name} must be finite and in [0, 1]")
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be finite and in [0, 1]")
    return value


def _validate_nonnegative(value, name):
    if isinstance(value, bool):
        raise ValueError(f"{name} must be finite and non-negative")
    try:
        value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be finite and non-negative") from exc
    if not math.isfinite(value) or value < 0.0:
        raise ValueError(f"{name} must be finite and non-negative")
    return value


def _nonnegative_scalar(metrics: Mapping[str, object], name: str) -> float:
    if name not in metrics or isinstance(metrics[name], bool):
        raise ValueError(f"{name} must be a finite non-negative scalar")
    try:
        value = float(metrics[name])
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{name} must be a finite non-negative scalar") from exc
    if not math.isfinite(value) or value < 0.0:
        raise ValueError(f"{name} must be a finite non-negative scalar")
    return value


def _strict_bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be bool")
    return value


def strike_evaluation_gate_summary(
        metrics: Mapping[str, object],
        episode_rows: Sequence[Mapping[str, object]],
        *,
        stage: str,
        timing_tolerance_ms: float = 50.0,
        safety_passed: bool = True,
        grip_success_gate: float = 0.90,
        grip_quality_mean_gate: float = 0.92,
        grip_quality_p05_gate: float = 0.85,
        pinch_quality_mean_gate: float = 0.95,
        free_quality_mean_gate: float = 0.85,
        max_grip_bad_frame_rate: float = 0.05,
        max_grip_bad_streak_frames: int = 12,
        tip_ready_success_gate: float = 0.90,
        precision_gate: float = 0.98,
        release_recall_gate: float = 0.98,
        false_positive_rate_gate: float = 0.02,
        strike_f1_gate: float = 0.98,
        zone_success_gate: float = 0.95,
        strum_completion_gate: float = 0.95,
        strum_traversal_recall_gate: float = 0.99,
        strum_order_accuracy_gate: float = 0.99,
        strum_direction_accuracy_gate: float = 0.99,
        worst_direction_completion_gate: Optional[float] = None,
        strum_max_unplanned_rate: float = 0.01,
        recovery_completion_gate: float = 1.0,
        end_to_end_recovery_completion_gate: Optional[float] = None,
        full_recovery_completion_gate: float = 1.0,
        handoff_recovery_completion_gate: float = 1.0,
        max_recovery_reset_count: float = 0.0,
        max_blocked_crossing_count: float = 0.0,
        strum_timing_rms_gate_ms: float = 25.0,
        strum_duration_mae_gate_ms: float = 20.0,
        timing_pass_rate_gate: Optional[float] = None,
        timing_center_mean_abs_gate_ms: Optional[float] = None,
        timing_center_tail_abs_gate_ms: Optional[float] = None,
        zone_applicable: Optional[bool] = None,
        timing_applicable: Optional[bool] = None,
        strum_applicable: Optional[bool] = None,
        strum_microtiming_applicable: Optional[bool] = None):
    """Return explicit gates applicable to one strike curriculum stage.

    Earlier skills remain applicable at later stages.  Metrics belonging only
    to a future stage are neither required nor allowed to influence ``passed``.
    """
    if stage not in STRIKE_STAGES:
        raise ValueError(f"unknown strike evaluation stage: {stage!r}")
    if not episode_rows:
        raise ValueError("strike evaluation requires at least one episode")
    safety_passed = _strict_bool(safety_passed, "safety_passed")

    grip_success_gate = _validate_gate(
        grip_success_gate, "grip_success_gate")
    grip_quality_mean_gate = _validate_gate(
        grip_quality_mean_gate, "grip_quality_mean_gate")
    grip_quality_p05_gate = _validate_gate(
        grip_quality_p05_gate, "grip_quality_p05_gate")
    pinch_quality_mean_gate = _validate_gate(
        pinch_quality_mean_gate, "pinch_quality_mean_gate")
    free_quality_mean_gate = _validate_gate(
        free_quality_mean_gate, "free_quality_mean_gate")
    max_grip_bad_frame_rate = _validate_gate(
        max_grip_bad_frame_rate, "max_grip_bad_frame_rate")
    if (isinstance(max_grip_bad_streak_frames, bool)
            or not isinstance(max_grip_bad_streak_frames, int)
            or max_grip_bad_streak_frames < 0):
        raise ValueError(
            "max_grip_bad_streak_frames must be a non-negative integer")
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
    strum_completion_gate = _validate_gate(
        strum_completion_gate, "strum_completion_gate")
    strum_traversal_recall_gate = _validate_gate(
        strum_traversal_recall_gate, "strum_traversal_recall_gate")
    strum_order_accuracy_gate = _validate_gate(
        strum_order_accuracy_gate, "strum_order_accuracy_gate")
    strum_direction_accuracy_gate = _validate_gate(
        strum_direction_accuracy_gate, "strum_direction_accuracy_gate")
    if worst_direction_completion_gate is not None:
        worst_direction_completion_gate = _validate_gate(
            worst_direction_completion_gate,
            "worst_direction_completion_gate")
    strum_max_unplanned_rate = _validate_gate(
        strum_max_unplanned_rate, "strum_max_unplanned_rate")
    recovery_completion_gate = _validate_gate(
        recovery_completion_gate, "recovery_completion_gate")
    if end_to_end_recovery_completion_gate is not None:
        end_to_end_recovery_completion_gate = _validate_gate(
            end_to_end_recovery_completion_gate,
            "end_to_end_recovery_completion_gate")
    full_recovery_completion_gate = _validate_gate(
        full_recovery_completion_gate,
        "full_recovery_completion_gate")
    handoff_recovery_completion_gate = _validate_gate(
        handoff_recovery_completion_gate,
        "handoff_recovery_completion_gate")
    max_recovery_reset_count = _validate_nonnegative(
        max_recovery_reset_count, "max_recovery_reset_count")
    max_blocked_crossing_count = _validate_nonnegative(
        max_blocked_crossing_count, "max_blocked_crossing_count")
    for name, value in (
            ("strum_timing_rms_gate_ms", strum_timing_rms_gate_ms),
            ("strum_duration_mae_gate_ms", strum_duration_mae_gate_ms)):
        if isinstance(value, bool) or not math.isfinite(float(value)) \
                or float(value) <= 0.0:
            raise ValueError(f"{name} must be finite and positive")
    strum_timing_rms_gate_ms = float(strum_timing_rms_gate_ms)
    strum_duration_mae_gate_ms = float(strum_duration_mae_gate_ms)
    if isinstance(timing_tolerance_ms, bool):
        raise ValueError("timing_tolerance_ms must be finite and positive")
    timing_tolerance_ms = float(timing_tolerance_ms)
    if (not math.isfinite(timing_tolerance_ms)
            or timing_tolerance_ms <= 0.0):
        raise ValueError("timing_tolerance_ms must be finite and positive")
    if timing_pass_rate_gate is not None:
        timing_pass_rate_gate = _validate_gate(
            timing_pass_rate_gate, "timing_pass_rate_gate")
    for name, value in (
            ("timing_center_mean_abs_gate_ms",
             timing_center_mean_abs_gate_ms),
            ("timing_center_tail_abs_gate_ms",
             timing_center_tail_abs_gate_ms)):
        if value is not None:
            value = _validate_nonnegative(value, name)
            if value <= 0.0:
                raise ValueError(f"{name} must be positive")
            if name == "timing_center_mean_abs_gate_ms":
                timing_center_mean_abs_gate_ms = value
            else:
                timing_center_tail_abs_gate_ms = value
    if zone_applicable is not None and not isinstance(zone_applicable, bool):
        raise ValueError("zone_applicable must be bool or None")
    for name, value in (
            ("timing_applicable", timing_applicable),
            ("strum_applicable", strum_applicable),
            ("strum_microtiming_applicable",
             strum_microtiming_applicable)):
        if value is not None and not isinstance(value, bool):
            raise ValueError(f"{name} must be bool or None")

    stage_index = STRIKE_STAGES.index(stage)
    applicability = {
        "grip": True,
        "tip_ready": stage != A0_PICK_GRIP,
        "release": stage not in (A0_PICK_GRIP, A1_TIP_READY),
        "timing": (stage in TIMED_STAGES
                   if timing_applicable is None else timing_applicable),
        "zone": (stage in ZONE_STAGES
                 if zone_applicable is None else zone_applicable),
    }

    grip_rate = _required_metric(metrics, "grip_success_rate")
    grip_quality_mean = _required_metric(metrics, "grip_quality_mean")
    grip_quality_p05 = _required_metric(metrics, "grip_quality_p05")
    grip_quality_min = _required_metric(metrics, "grip_quality_min")
    pinch_quality_mean = _required_metric(metrics, "pinch_quality_mean")
    free_quality_mean = _required_metric(metrics, "free_quality_mean")
    grip_bad_frame_rate = _required_metric(metrics, "grip_bad_frame_rate")
    grip_bad_streak_frames = _nonnegative_scalar(
        metrics, "grip_bad_streak_max_frames")
    grip_passed = bool(
        grip_rate >= grip_success_gate
        and grip_quality_mean >= grip_quality_mean_gate
        and grip_quality_p05 >= grip_quality_p05_gate
        and pinch_quality_mean >= pinch_quality_mean_gate
        and free_quality_mean >= free_quality_mean_gate
        and grip_bad_frame_rate <= max_grip_bad_frame_rate
        and grip_bad_streak_frames <= max_grip_bad_streak_frames)

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

    recovery_applicable = applicability["release"]
    recovery_event_count = None
    recovery_completion_rate = None
    scheduled_recovery_completion_rate = None
    conditional_recovery_completion_rate = None
    end_to_end_recovery_completion_rate = None
    full_recovery_completion_rate = None
    full_recovery_event_count = None
    handoff_recovery_completion_rate = None
    handoff_recovery_event_count = None
    recovery_reset_count = None
    blocked_crossing_count = None
    recovery_passed = True
    if recovery_applicable:
        recovery_event_count = _nonnegative_scalar(
            metrics, "recovery_event_count")
        recovery_completion_rate = _required_metric(
            metrics, "recovery_completion_rate")
        if stage in (S2_TIMED_STRUM, S3_SONG_INTEGRATION):
            conditional_recovery_completion_rate = _required_metric(
                metrics, "conditional_recovery_completion_rate")
            end_to_end_recovery_completion_rate = _required_metric(
                metrics, "end_to_end_recovery_completion_rate")
        if stage == S3_SONG_INTEGRATION:
            scheduled_recovery_completion_rate = _required_metric(
                metrics, "scheduled_recovery_completion_rate")
            full_recovery_completion_rate = _required_metric(
                metrics, "full_recovery_completion_rate")
            full_recovery_event_count = _nonnegative_scalar(
                metrics, "full_recovery_event_count")
            handoff_recovery_completion_rate = _required_metric(
                metrics, "handoff_recovery_completion_rate")
            handoff_recovery_event_count = _nonnegative_scalar(
                metrics, "handoff_recovery_event_count")
        recovery_reset_count = _nonnegative_scalar(
            metrics, "recovery_reset_count")
        blocked_crossing_count = _nonnegative_scalar(
            metrics, "blocked_crossing_count")
        if stage == S3_SONG_INTEGRATION:
            completion_passed = (
                scheduled_recovery_completion_rate
                >= recovery_completion_gate
                and full_recovery_event_count > 0.0
                and full_recovery_completion_rate
                >= full_recovery_completion_gate
                and handoff_recovery_event_count > 0.0
                and handoff_recovery_completion_rate
                >= handoff_recovery_completion_gate)
        elif stage == S2_TIMED_STRUM:
            completion_passed = (
                conditional_recovery_completion_rate
                >= recovery_completion_gate)
        else:
            completion_passed = (
                recovery_completion_rate >= recovery_completion_gate)
        if (end_to_end_recovery_completion_gate is not None
                and stage in (S2_TIMED_STRUM, S3_SONG_INTEGRATION)):
            completion_passed = bool(
                completion_passed
                and end_to_end_recovery_completion_rate
                >= end_to_end_recovery_completion_gate)
        recovery_passed = bool(
            recovery_event_count > 0.0
            and completion_passed
            and recovery_reset_count <= max_recovery_reset_count
            and blocked_crossing_count <= max_blocked_crossing_count)

    strike_f1 = None
    timing_p95_ms = None
    timing_pass_rate = None
    timing_signed_mean_ms = None
    timing_signed_p10_ms = None
    timing_signed_p90_ms = None
    timing_center_passed = True
    timing_passed = True
    if applicability["timing"]:
        strike_f1 = _required_metric(metrics, "strike_f1")
        timing_p95_ms = _required_metric(metrics, "timing_p95_ms")
        if timing_pass_rate_gate is None:
            timing_passed = (
                strike_f1 >= strike_f1_gate
                and timing_p95_ms <= timing_tolerance_ms)
        else:
            timing_pass_rate = _required_metric(
                metrics, "timing_pass_rate")
            timing_passed = timing_pass_rate >= timing_pass_rate_gate
        if (timing_center_mean_abs_gate_ms is not None
                or timing_center_tail_abs_gate_ms is not None):
            timing_signed_mean_ms = _required_metric(
                metrics, "timing_signed_mean_ms")
            timing_signed_p10_ms = _required_metric(
                metrics, "timing_signed_p10_ms")
            timing_signed_p90_ms = _required_metric(
                metrics, "timing_signed_p90_ms")
            if timing_center_mean_abs_gate_ms is not None:
                timing_center_passed &= (
                    abs(timing_signed_mean_ms)
                    <= timing_center_mean_abs_gate_ms)
            if timing_center_tail_abs_gate_ms is not None:
                timing_center_passed &= (
                    timing_signed_p10_ms
                    >= -timing_center_tail_abs_gate_ms
                    and timing_signed_p90_ms
                    <= timing_center_tail_abs_gate_ms)
            timing_passed = timing_passed and timing_center_passed

    zone_rate = None
    zone_passed = True
    if applicability["zone"]:
        zone_rate = _required_metric(metrics, "zone_success_rate")
        zone_passed = zone_rate >= zone_success_gate

    strum_event_count = float(metrics.get("strum_event_count", 0.0))
    if not math.isfinite(strum_event_count) or strum_event_count < 0.0:
        raise ValueError("strum_event_count must be finite and non-negative")
    strum_applicable = (
        stage in STRUM_STAGES
        if strum_applicable is None else strum_applicable)
    strum_completion_rate = None
    strum_traversal_recall = None
    strum_order_accuracy = None
    strum_direction_accuracy = None
    worst_direction_completion_rate = None
    strum_unplanned_rate = None
    strum_timing_rms_ms = None
    strum_duration_mae_ms = None
    microtiming_sample_count = None
    strum_microtiming_is_applicable = (
        stage in STRUM_MICROTIMING_STAGES and strum_applicable
        if strum_microtiming_applicable is None
        else strum_microtiming_applicable)
    strum_microtiming_passed = not strum_microtiming_is_applicable
    strum_passed = not strum_applicable
    if strum_applicable and strum_event_count > 0.0:
        def strum_metric(name):
            value = metrics.get(name)
            if isinstance(value, bool):
                raise ValueError(f"{name} must be finite and in [0, 1]")
            value = float(value)
            if not math.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be finite and in [0, 1]")
            return value
        strum_completion_rate = strum_metric("strum_completion_rate")
        strum_traversal_recall = strum_metric("strum_traversal_recall")
        strum_order_accuracy = strum_metric("strum_order_accuracy")
        strum_direction_accuracy = strum_metric("strum_direction_accuracy")
        if worst_direction_completion_gate is not None:
            worst_direction_completion_rate = _required_metric(
                metrics, "worst_direction_completion_rate")
        strum_unplanned_rate = strum_metric("strum_unplanned_crossing_rate")
        strum_passed = bool(
            strum_completion_rate >= strum_completion_gate
            and strum_traversal_recall >= strum_traversal_recall_gate
            and strum_order_accuracy >= strum_order_accuracy_gate
            and strum_direction_accuracy >= strum_direction_accuracy_gate
            and strum_unplanned_rate <= strum_max_unplanned_rate
            and (worst_direction_completion_gate is None
                 or worst_direction_completion_rate
                 >= worst_direction_completion_gate))
        if strum_microtiming_is_applicable:
            microtiming_sample_count = float(
                metrics.get("strum_microtiming_sample_count", 0.0))
            if (not math.isfinite(microtiming_sample_count)
                    or microtiming_sample_count < 0.0):
                raise ValueError(
                    "strum_microtiming_sample_count must be finite and non-negative")
            strum_timing_rms_ms = _required_metric(
                metrics, "strum_timing_rms_ms")
            strum_duration_mae_ms = _required_metric(
                metrics, "strum_sweep_duration_mae_ms")
            strum_microtiming_passed = bool(
                microtiming_sample_count > 0.0
                and strum_timing_rms_ms <= strum_timing_rms_gate_ms
                and strum_duration_mae_ms <= strum_duration_mae_gate_ms)

    goal_finished = []
    failure_termination = []
    for index, row in enumerate(episode_rows):
        if not isinstance(row, Mapping):
            raise ValueError(f"episode row {index} must be a mapping")
        for field, target in (
                ("goal_finished", goal_finished),
                ("failure_termination", failure_termination)):
            if field not in row:
                raise ValueError(
                    f"episode row is missing required field: {field}")
            target.append(_strict_bool(
                row[field], f"episode row {index} {field}"))
    completion_rate = sum(float(value) for value in goal_finished) / len(
        goal_finished)
    failure_rate = sum(float(value) for value in failure_termination) / len(
        failure_termination)
    full_episode_passed = (
        completion_rate >= 1.0 - 1e-9
        and failure_rate <= 1e-9
    )

    task_passed = bool(
        grip_passed
        and ready_passed
        and release_passed
        and recovery_passed
        and timing_passed
        and zone_passed
        and strum_passed
        and strum_microtiming_passed
        and full_episode_passed
    )
    passed = task_passed and safety_passed
    return {
        "stage": stage,
        "stage_index": stage_index,
        "grip_applicable": True,
        "grip_success_rate": grip_rate,
        "gate_grip_success_rate": grip_success_gate,
        "grip_quality_mean": grip_quality_mean,
        "grip_quality_p05": grip_quality_p05,
        "grip_quality_min": grip_quality_min,
        "pinch_quality_mean": pinch_quality_mean,
        "free_quality_mean": free_quality_mean,
        "grip_bad_frame_rate": grip_bad_frame_rate,
        "grip_bad_streak_max_frames": grip_bad_streak_frames,
        "gate_grip_quality_mean": grip_quality_mean_gate,
        "gate_grip_quality_p05": grip_quality_p05_gate,
        "gate_pinch_quality_mean": pinch_quality_mean_gate,
        "gate_free_quality_mean": free_quality_mean_gate,
        "gate_max_grip_bad_frame_rate": max_grip_bad_frame_rate,
        "gate_max_grip_bad_streak_frames": max_grip_bad_streak_frames,
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
        "recovery_applicable": bool(recovery_applicable),
        "recovery_event_count": recovery_event_count,
        "recovery_completion_rate": recovery_completion_rate,
        "scheduled_recovery_completion_rate": (
            scheduled_recovery_completion_rate),
        "conditional_recovery_completion_rate": (
            conditional_recovery_completion_rate),
        "end_to_end_recovery_completion_rate": (
            end_to_end_recovery_completion_rate),
        "full_recovery_completion_rate": full_recovery_completion_rate,
        "full_recovery_event_count": full_recovery_event_count,
        "handoff_recovery_completion_rate": (
            handoff_recovery_completion_rate),
        "handoff_recovery_event_count": handoff_recovery_event_count,
        "recovery_reset_count": recovery_reset_count,
        "blocked_crossing_count": blocked_crossing_count,
        "gate_recovery_completion_rate": recovery_completion_gate,
        "gate_end_to_end_recovery_completion_rate": (
            end_to_end_recovery_completion_gate),
        "gate_full_recovery_completion_rate": (
            full_recovery_completion_gate),
        "gate_handoff_recovery_completion_rate": (
            handoff_recovery_completion_gate),
        "gate_max_recovery_reset_count": max_recovery_reset_count,
        "gate_max_blocked_crossing_count": max_blocked_crossing_count,
        "recovery_passed": bool(recovery_passed),
        "timing_applicable": applicability["timing"],
        "strike_f1": strike_f1,
        "timing_p95_ms": timing_p95_ms,
        "timing_pass_rate": timing_pass_rate,
        "timing_signed_mean_ms": timing_signed_mean_ms,
        "timing_signed_p10_ms": timing_signed_p10_ms,
        "timing_signed_p90_ms": timing_signed_p90_ms,
        "gate_timing_pass_rate": timing_pass_rate_gate,
        "gate_timing_center_mean_abs_ms": (
            timing_center_mean_abs_gate_ms),
        "gate_timing_center_tail_abs_ms": (
            timing_center_tail_abs_gate_ms),
        "timing_center_passed": bool(timing_center_passed),
        "gate_strike_f1": strike_f1_gate,
        "gate_timing_p95_ms": timing_tolerance_ms,
        "timing_passed": bool(timing_passed),
        "zone_applicable": applicability["zone"],
        "zone_success_rate": zone_rate,
        "gate_zone_success_rate": zone_success_gate,
        "zone_passed": bool(zone_passed),
        "strum_applicable": bool(strum_applicable),
        "strum_event_count": strum_event_count,
        "strum_completion_rate": strum_completion_rate,
        "strum_traversal_recall": strum_traversal_recall,
        "strum_order_accuracy": strum_order_accuracy,
        "strum_direction_accuracy": strum_direction_accuracy,
        "worst_direction_completion_rate": (
            worst_direction_completion_rate),
        "strum_unplanned_crossing_rate": strum_unplanned_rate,
        "gate_strum_completion_rate": strum_completion_gate,
        "gate_strum_traversal_recall": strum_traversal_recall_gate,
        "gate_strum_order_accuracy": strum_order_accuracy_gate,
        "gate_strum_direction_accuracy": strum_direction_accuracy_gate,
        "gate_worst_direction_completion_rate": (
            worst_direction_completion_gate),
        "gate_strum_max_unplanned_rate": strum_max_unplanned_rate,
        "strum_passed": bool(strum_passed),
        "strum_microtiming_applicable": bool(
            strum_microtiming_is_applicable),
        "strum_microtiming_sample_count": microtiming_sample_count,
        "strum_timing_rms_ms": strum_timing_rms_ms,
        "strum_sweep_duration_mae_ms": strum_duration_mae_ms,
        "gate_strum_timing_rms_ms": strum_timing_rms_gate_ms,
        "gate_strum_sweep_duration_mae_ms": strum_duration_mae_gate_ms,
        "strum_microtiming_passed": bool(strum_microtiming_passed),
        "full_episode_completion_rate": completion_rate,
        "failure_termination_rate": failure_rate,
        "full_episode_passed": bool(full_episode_passed),
        "task_passed": task_passed,
        "safety_passed": safety_passed,
        "human_like_review_required": True,
        "passed": bool(passed),
    }


__all__ = ["strike_evaluation_gate_summary"]
