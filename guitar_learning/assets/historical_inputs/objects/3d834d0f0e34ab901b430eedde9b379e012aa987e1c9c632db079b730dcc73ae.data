from __future__ import annotations

from collections import deque
import math


STRIKE_EPISODE_METRIC_KEYS = (
    "strike_uniform_evidence_eligible",
    "strike_grip_success_rate",
    "strike_grip_quality_mean",
    "strike_grip_quality_p05",
    "strike_grip_quality_min",
    "strike_grip_pinch_quality_mean",
    "strike_grip_free_quality_mean",
    "strike_grip_bad_frame_rate",
    "strike_grip_bad_streak_max_frames",
    "strike_grip_frame_count",
    "strike_tip_ready_success_rate",
    "strike_precision",
    "strike_release_recall",
    "strike_false_positive_rate",
    "strike_episode_f1",
    "strike_true_positive_count",
    "strike_false_positive_count",
    "strike_false_negative_count",
    "strike_wrong_crossing_rate_exceeded",
    "strike_timing_mae_ms",
    "strike_timing_p95_ms",
    "strike_timing_signed_mean_ms",
    "strike_timing_signed_p10_ms",
    "strike_timing_signed_p50_ms",
    "strike_timing_signed_p90_ms",
    "strike_timing_pass_rate",
    "strike_timing_early_rate",
    "strike_timing_late_rate",
    "strike_premature_release_rate",
    "strike_timing_event_count",
    "strike_zone_success_rate",
    "strike_zone_mean_quality",
    "strike_raw_zone_success_rate",
    "strike_raw_zone_mean_quality",
    "strike_raw_zone_attempt_count",
    "strike_single_precision",
    "strike_single_recall",
    "strike_single_f1",
    "strike_single_event_count",
    "strike_strum_completion_rate",
    "strike_strum_traversal_recall",
    "strike_strum_order_accuracy",
    "strike_strum_direction_accuracy",
    "strike_strum_unplanned_crossing_rate",
    "strike_strum_duplicate_crossing_rate",
    "strike_blocked_crossing_count",
    "strike_blocked_crossing_rate",
    "strike_strum_event_count",
    "strike_strum_timing_rms_ms",
    "strike_strum_timing_p95_ms",
    "strike_strum_sweep_duration_mae_ms",
    "strike_strum_sweep_duration_p95_ms",
    "strike_strum_microtiming_sample_count",
    "strike_recovery_completion_rate",
    "strike_recovery_event_count",
    "strike_scheduled_recovery_completion_rate",
    "strike_scheduled_recovery_event_count",
    "strike_scheduled_recovery_completed_count",
    "strike_conditional_recovery_completion_rate",
    "strike_end_to_end_recovery_completion_rate",
    "strike_full_recovery_completion_rate",
    "strike_full_recovery_event_count",
    "strike_full_recovery_completed_count",
    "strike_handoff_recovery_completion_rate",
    "strike_handoff_recovery_event_count",
    "strike_handoff_recovery_completed_count",
    "strike_handoff_required_frames_mean",
    "strike_recovery_reset_count",
    "strike_recovery_reset_rate",
    "strike_first_target_release_frame",
    "strike_down_completion_rate",
    "strike_down_event_count",
    "strike_down_completed_count",
    "strike_up_completion_rate",
    "strike_up_event_count",
    "strike_up_completed_count",
    "strike_worst_direction_completion_rate",
    "strike_final_string_miss_count",
    "strike_final_remaining_count_at_resolution",
    "strike_strum_exit_distance_mean_m",
    "strike_strum_exit_distance_sample_count",
    "strike_reward_timing_return",
    "strike_reward_timing_wait_return",
    "strike_reward_strum_progress_return",
    "strike_reward_strum_terminal_progress_return",
    "strike_reward_strum_physical_completion_return",
    "strike_penalty_premature_release_return",
    "strike_penalty_early_timing_return",
    "strike_penalty_miss_return",
    "curriculum_success_rate",
)


STRIKE_RAW_COUNT_METRIC_KEYS = (
    "strike_true_positive_count",
    "strike_false_positive_count",
    "strike_false_negative_count",
    "strike_strum_event_count",
    "strike_recovery_event_count",
    "strike_scheduled_recovery_event_count",
    "strike_scheduled_recovery_completed_count",
    "strike_full_recovery_event_count",
    "strike_full_recovery_completed_count",
    "strike_handoff_recovery_event_count",
    "strike_handoff_recovery_completed_count",
    "strike_down_event_count",
    "strike_down_completed_count",
    "strike_up_event_count",
    "strike_up_completed_count",
    "strike_recovery_reset_count",
    "strike_blocked_crossing_count",
    "strike_final_string_miss_count",
    "strike_final_remaining_count_at_resolution",
    "strike_strum_exit_distance_sample_count",
)


def pooled_rate_from_counts(
        totals, completed_key, event_key, *, allow_empty=False):
    if not isinstance(totals, dict) and not hasattr(totals, "get"):
        raise TypeError("count totals must be a mapping")
    completed = totals.get(completed_key)
    events = totals.get(event_key)
    if isinstance(completed, bool) or isinstance(events, bool):
        return None
    try:
        completed = float(completed)
        events = float(events)
    except (TypeError, ValueError):
        return None
    if (not math.isfinite(completed) or not math.isfinite(events)
            or completed < 0.0 or events < 0.0
            or completed > events + 1e-6):
        return None
    if events <= 0.0:
        return 0.0 if allow_empty else None
    return completed / events


def pool_strike_raw_count_rates(result):
    if not isinstance(result, dict):
        raise TypeError("strike aggregate must be a mutable dictionary")
    count_keys = tuple(f"strike_{name}_count" for name in (
        "true_positive", "false_positive", "false_negative"))
    if all(key in result for key in count_keys):
        counts = [float(result[key]) for key in count_keys]
        if not all(math.isfinite(value) and value >= 0.0 for value in counts):
            raise ValueError("Strike TP/FP/FN counts must be finite and nonnegative")
        tp, fp, fn = counts
        pooled = {
            "strike_episode_f1": 2.0 * tp / max(2.0 * tp + fp + fn, 1e-8),
            "strike_precision": tp / max(tp + fp, 1e-8),
            "strike_release_recall": tp / max(tp + fn, 1e-8),
            "strike_false_positive_rate": fp / max(tp + fp + fn, 1e-8),
        }
        for key, value in pooled.items():
            if key in result:
                result.setdefault(key + "_macro", result[key])
            result[key] = value
    down = pooled_rate_from_counts(
        result, "strike_down_completed_count", "strike_down_event_count")
    up = pooled_rate_from_counts(
        result, "strike_up_completed_count", "strike_up_event_count")
    result["strike_down_completion_rate"] = (
        down if down is not None else -1.0)
    result["strike_up_completion_rate"] = (
        up if up is not None else -1.0)
    result["strike_worst_direction_completion_rate"] = (
        min(down, up) if down is not None and up is not None else -1.0)
    overall = None
    down_counts_valid = pooled_rate_from_counts(
        result, "strike_down_completed_count", "strike_down_event_count",
        allow_empty=True) is not None
    up_counts_valid = pooled_rate_from_counts(
        result, "strike_up_completed_count", "strike_up_event_count",
        allow_empty=True) is not None
    try:
        direction_events = (
            float(result["strike_down_event_count"])
            + float(result["strike_up_event_count"]))
        direction_completed = (
            float(result["strike_down_completed_count"])
            + float(result["strike_up_completed_count"]))
        strum_events = float(result["strike_strum_event_count"])
        if (down_counts_valid and up_counts_valid
                and all(math.isfinite(value) for value in (
                direction_events, direction_completed, strum_events))
                and direction_events > 0.0
                and direction_completed >= 0.0
                and direction_completed <= direction_events + 1e-6
                and abs(direction_events - strum_events) <= 1e-6):
            overall = direction_completed / direction_events
    except (KeyError, TypeError, ValueError):
        pass
    result["strike_strum_completion_rate"] = (
        overall if overall is not None else -1.0)
    conditional = pooled_rate_from_counts(
        result,
        "strike_scheduled_recovery_completed_count",
        "strike_recovery_event_count")
    end_to_end = pooled_rate_from_counts(
        result,
        "strike_scheduled_recovery_completed_count",
        "strike_scheduled_recovery_event_count")
    result["strike_conditional_recovery_completion_rate"] = (
        conditional if conditional is not None else -1.0)
    result["strike_scheduled_recovery_completion_rate"] = (
        conditional if conditional is not None else -1.0)
    result["strike_end_to_end_recovery_completion_rate"] = (
        end_to_end if end_to_end is not None else -1.0)
    for recovery in ("full", "handoff"):
        key = f"strike_{recovery}_recovery_completion_rate"
        if key in result:
            result.setdefault(key + "_macro", result[key])
        rate = pooled_rate_from_counts(
            result, f"strike_{recovery}_recovery_completed_count",
            f"strike_{recovery}_recovery_event_count")
        result[key] = rate if rate is not None else -1.0
    return result


STRIKE_WEIGHTED_METRIC_GROUPS = (
    ("strike_grip_frame_count", (
        "strike_grip_success_rate",
        "strike_grip_quality_mean",
        "strike_grip_pinch_quality_mean",
        "strike_grip_free_quality_mean",
        "strike_grip_bad_frame_rate",
    )),
    ("strike_single_event_count", (
        "strike_single_precision",
        "strike_single_recall",
        "strike_single_f1",
    )),
    ("strike_strum_event_count", (
        "strike_strum_completion_rate",
        "strike_strum_traversal_recall",
        "strike_strum_order_accuracy",
        "strike_strum_direction_accuracy",
        "strike_strum_unplanned_crossing_rate",
        "strike_strum_duplicate_crossing_rate",
        "strike_strum_timing_rms_ms",
        "strike_strum_timing_p95_ms",
        "strike_strum_sweep_duration_mae_ms",
        "strike_strum_sweep_duration_p95_ms",
    )),
    ("strike_recovery_event_count", (
        "strike_recovery_completion_rate",
        "strike_scheduled_recovery_completion_rate",
        "strike_conditional_recovery_completion_rate",
        "strike_recovery_reset_rate",
        "strike_blocked_crossing_rate",
        "strike_first_target_release_frame",
    )),
    ("strike_scheduled_recovery_event_count", (
        "strike_end_to_end_recovery_completion_rate",
    )),
    ("strike_full_recovery_event_count", (
        "strike_full_recovery_completion_rate",
    )),
    ("strike_handoff_recovery_event_count", (
        "strike_handoff_recovery_completion_rate",
        "strike_handoff_required_frames_mean",
    )),
    ("strike_down_event_count", ("strike_down_completion_rate",)),
    ("strike_up_event_count", ("strike_up_completion_rate",)),
    ("strike_strum_exit_distance_sample_count", (
        "strike_strum_exit_distance_mean_m",
    )),
    ("strike_strum_microtiming_sample_count", ()),
    ("strike_timing_event_count", (
        "strike_timing_pass_rate",
        "strike_timing_early_rate",
        "strike_timing_late_rate",
        "strike_premature_release_rate",
    )),
    ("strike_raw_zone_attempt_count", (
        "strike_raw_zone_success_rate",
        "strike_raw_zone_mean_quality",
    )),
)


class StrikeRewardAlignmentMonitor:
    def __init__(self, window=300):
        if isinstance(window, bool) or not isinstance(window, int) or window < 20:
            raise ValueError("reward-alignment window must be an integer >= 20")
        self.window = window
        self.rows = deque(maxlen=window)
        self.context = None

    def update(self, stats):
        stage = stats.get("curriculum_stage")
        profile = stats.get("curriculum_s2_profile_name")
        tempo = stats.get("curriculum_tempo_lambda", stats.get("tempo_lambda"))
        context_value = (
            profile if stage == "S2_TIMED_STRUM"
            else tempo if stage == "S3_SONG_INTEGRATION" else None)
        context = (stage, context_value)
        if context != self.context:
            self.rows.clear()
            self.context = context
        if stage == "S2_TIMED_STRUM":
            keys = (
                "reward", "strike_strum_completion_rate",
                "strike_worst_direction_completion_rate",
                "strike_timing_p95_ms", "strike_false_positive_rate",
                "strike_timing_signed_mean_ms")
        elif stage == "S3_SONG_INTEGRATION":
            f1_key = (
                "uniform_evidence_strike_episode_f1"
                if "uniform_evidence_strike_episode_f1" in stats
                else "strike_episode_f1")
            blocked_key = (
                "uniform_evidence_strike_blocked_crossing_rate"
                if "uniform_evidence_strike_blocked_crossing_rate" in stats
                else "strike_blocked_crossing_rate")
            keys = (
                "reward", f1_key, blocked_key)
        else:
            return {
                "reward_alignment_warning": False,
                "reward_alignment_samples": len(self.rows),
                "reward_alignment_reasons": "none",
            }
        try:
            values = tuple(float(stats[key]) for key in keys)
            if stage == "S3_SONG_INTEGRATION":
                uniform_wrong = stats.get(
                    "uniform_evidence_wrong_crossing_termination")
                wrong_values = (
                    (float(uniform_wrong),)
                    if uniform_wrong is not None else tuple(
                        float(stats[key])
                        for key in (
                            "wrong_crossing_termination",
                            "strike_wrong_crossing_rate_exceeded")
                        if key in stats))
                if not wrong_values:
                    raise KeyError("wrong-crossing metric")
                values += (max(wrong_values),)
        except (KeyError, TypeError, ValueError, OverflowError):
            return {
                "reward_alignment_warning": False,
                "reward_alignment_samples": len(self.rows),
                "reward_alignment_reasons": "none",
            }
        if not all(math.isfinite(value) for value in values):
            return {
                "reward_alignment_warning": False,
                "reward_alignment_samples": len(self.rows),
                "reward_alignment_reasons": "none",
            }
        self.rows.append(values)
        warning = False
        reasons = []
        diagnostic = {}
        if len(self.rows) == self.window:
            rows = tuple(self.rows)
            split = self.window // 2
            first = tuple(
                sum(row[index] for row in rows[:split]) / split
                for index in range(len(values)))
            second_count = self.window - split
            second = tuple(
                sum(row[index] for row in rows[split:]) / second_count
                for index in range(len(values)))
            reward_not_dropping = second[0] >= first[0] - 1e-3
            if stage == "S2_TIMED_STRUM":
                if second[1] < first[1] - 0.02:
                    reasons.append("strum_completion")
                if second[2] < first[2] - 0.02:
                    reasons.append("worst_direction_completion")
                if second[3] > first[3] + 20.0:
                    reasons.append("timing_p95")
                if second[4] > first[4] + 0.02:
                    reasons.append("false_positive")
                if abs(second[5]) > abs(first[5]) + 15.0:
                    reasons.append("timing_bias")
                diagnostic = {
                    "reward_alignment_reward_delta": second[0] - first[0],
                    "reward_alignment_strum_completion_delta": (
                        second[1] - first[1]),
                    "reward_alignment_worst_direction_delta": (
                        second[2] - first[2]),
                    "reward_alignment_timing_p95_delta_ms": (
                        second[3] - first[3]),
                }
            else:
                if second[1] < first[1] - 0.01:
                    reasons.append("song_f1")
                if second[2] > first[2] + 0.01:
                    reasons.append("blocked_crossing")
                if second[3] > first[3] + 0.005:
                    reasons.append("wrong_crossing")
                diagnostic = {
                    "reward_alignment_reward_delta": second[0] - first[0],
                    "reward_alignment_song_f1_delta": second[1] - first[1],
                    "reward_alignment_blocked_crossing_delta": (
                        second[2] - first[2]),
                    "reward_alignment_wrong_crossing_delta": (
                        second[3] - first[3]),
                }
            warning = reward_not_dropping and bool(reasons)
        return {
            "reward_alignment_warning": warning,
            "reward_alignment_samples": len(self.rows),
            "reward_alignment_reasons": (
                ",".join(reasons) if warning else "none"),
            **diagnostic,
        }


__all__ = [
    "STRIKE_EPISODE_METRIC_KEYS",
    "STRIKE_RAW_COUNT_METRIC_KEYS",
    "STRIKE_WEIGHTED_METRIC_GROUPS",
    "pooled_rate_from_counts",
    "pool_strike_raw_count_rates",
    "StrikeRewardAlignmentMonitor",
]
