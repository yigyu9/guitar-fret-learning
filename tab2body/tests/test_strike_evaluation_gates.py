"""CPU checks for stage-specific strike evaluation applicability."""
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tab2body.learning.strike_curriculum import (
    A0_PICK_GRIP,
    A1_TIP_READY,
    A2_SINGLE_CROSSING,
    A3_TIMED_SINGLE,
    A4_STRUM_CONTEXT_RECOVERY,
    S2_TIMED_STRUM,
    S3_SONG_INTEGRATION,
)
from tab2body.learning.strike_evaluation import (
    strike_evaluation_gate_summary,
)


def metrics():
    return {
        "grip_success_rate": 0.95,
        "grip_quality_mean": 0.96,
        "grip_quality_p05": 0.92,
        "grip_quality_min": 0.88,
        "pinch_quality_mean": 0.98,
        "free_quality_mean": 0.92,
        "grip_bad_frame_rate": 0.01,
        "grip_bad_streak_max_frames": 2,
        "tip_ready_success_rate": 0.95,
        "precision": 0.99,
        "release_recall": 0.99,
        "false_positive_rate": 0.01,
        "strike_f1": 0.99,
        "timing_p95_ms": 45.0,
        "timing_pass_rate": 0.75,
        "timing_signed_mean_ms": -20.0,
        "timing_signed_p10_ms": -40.0,
        "timing_signed_p90_ms": 5.0,
        "zone_success_rate": 0.97,
        "strum_event_count": 8,
        "strum_completion_rate": 0.98,
        "strum_traversal_recall": 1.0,
        "strum_order_accuracy": 1.0,
        "strum_direction_accuracy": 1.0,
        "strum_unplanned_crossing_rate": 0.0,
        "strum_timing_rms_ms": 20.0,
        "strum_sweep_duration_mae_ms": 15.0,
        "strum_microtiming_sample_count": 8,
        "recovery_completion_rate": 1.0,
        "scheduled_recovery_completion_rate": 1.0,
        "conditional_recovery_completion_rate": 1.0,
        "end_to_end_recovery_completion_rate": 1.0,
        "worst_direction_completion_rate": 0.98,
        "full_recovery_completion_rate": 1.0,
        "full_recovery_event_count": 4,
        "handoff_recovery_completion_rate": 1.0,
        "handoff_recovery_event_count": 4,
        "recovery_event_count": 8,
        "recovery_reset_count": 0,
        "blocked_crossing_count": 0,
    }


def rows():
    return [
        {"goal_finished": True, "failure_termination": False},
        {"goal_finished": True, "failure_termination": False},
    ]


def gates(stage, source=None, episode_rows=None, **kwargs):
    return strike_evaluation_gate_summary(
        metrics() if source is None else source,
        rows() if episode_rows is None else episode_rows,
        stage=stage,
        timing_tolerance_ms=kwargs.pop("timing_tolerance_ms", 50),
        safety_passed=kwargs.pop("safety_passed", True),
        **kwargs,
    )


def expect_error(fragment, callback):
    try:
        callback()
    except ValueError as exc:
        assert fragment in str(exc), str(exc)
    else:
        raise AssertionError(f"expected ValueError containing {fragment!r}")


def main():
    grip_only = {
        key: value for key, value in metrics().items()
        if key.startswith("grip_") or key in (
            "pinch_quality_mean", "free_quality_mean")
    }
    a0 = gates(A0_PICK_GRIP, grip_only)
    assert a0["passed"] and a0["grip_applicable"]
    assert not a0["tip_ready_applicable"]
    assert not a0["release_applicable"]
    assert not a0["timing_applicable"]
    assert not a0["zone_applicable"]
    bad_grip = metrics()
    bad_grip["grip_quality_p05"] = 0.84
    assert not gates(A0_PICK_GRIP, bad_grip)["grip_passed"]
    bad_grip = metrics()
    bad_grip["grip_bad_streak_max_frames"] = 13
    assert not gates(A0_PICK_GRIP, bad_grip)["grip_passed"]


    future_bad = metrics()
    future_bad.update(
        tip_ready_success_rate=0.0,
        release_recall=0.0,
        false_positive_rate=1.0,
        strike_f1=0.0,
        timing_p95_ms=1000.0,
        zone_success_rate=0.0,
    )
    assert gates(A0_PICK_GRIP, future_bad)["passed"]

    a1 = gates(A1_TIP_READY)
    assert a1["passed"] and a1["tip_ready_applicable"]
    assert not a1["release_applicable"]
    bad = metrics()
    bad["tip_ready_success_rate"] = 0.89
    assert not gates(A1_TIP_READY, bad)["tip_ready_passed"]

    a2 = gates(A2_SINGLE_CROSSING)
    assert a2["passed"] and a2["release_applicable"]
    assert a2["recovery_applicable"] and a2["recovery_passed"]
    assert not a2["timing_applicable"]
    bad = metrics()
    bad["precision"] = 0.97
    assert not gates(A2_SINGLE_CROSSING, bad)["release_passed"]
    bad = metrics()
    bad["release_recall"] = 0.97
    assert not gates(A2_SINGLE_CROSSING, bad)["release_passed"]
    bad = metrics()
    bad["false_positive_rate"] = 0.021
    assert not gates(A2_SINGLE_CROSSING, bad)["release_passed"]
    bad = metrics()
    bad["recovery_completion_rate"] = 0.99
    assert not gates(A2_SINGLE_CROSSING, bad)["recovery_passed"]
    bad = metrics()
    bad["recovery_reset_count"] = 1
    assert not gates(A2_SINGLE_CROSSING, bad)["recovery_passed"]
    bad = metrics()
    bad["blocked_crossing_count"] = 1
    assert not gates(A2_SINGLE_CROSSING, bad)["recovery_passed"]

    bad = metrics()
    bad["timing_p95_ms"] = 100000.0
    assert gates(A2_SINGLE_CROSSING, bad)["passed"]

    a3 = gates(A3_TIMED_SINGLE)
    assert a3["passed"] and a3["timing_applicable"]
    assert a3["zone_applicable"]
    bad = metrics()
    bad["strike_f1"] = 0.97
    assert not gates(A3_TIMED_SINGLE, bad)["timing_passed"]
    at_67 = metrics()
    at_67["timing_p95_ms"] = 67.0
    assert gates(
        A3_TIMED_SINGLE, at_67, timing_tolerance_ms=67)["passed"]
    at_67["timing_p95_ms"] = 67.001
    assert not gates(
        A3_TIMED_SINGLE, at_67,
        timing_tolerance_ms=67)["timing_passed"]

    a4 = gates(A4_STRUM_CONTEXT_RECOVERY)
    assert a4["passed"] and a4["strum_applicable"]
    coarse_s2 = gates(
        S2_TIMED_STRUM,
        timing_tolerance_ms=400,
        timing_pass_rate_gate=0.70,
        timing_center_mean_abs_gate_ms=110,
        timing_center_tail_abs_gate_ms=190,
        zone_applicable=False,
        strum_completion_gate=0.70,
        strum_timing_rms_gate_ms=300,
        strum_duration_mae_gate_ms=200)
    assert coarse_s2["passed"]
    assert not coarse_s2["zone_applicable"]
    assert coarse_s2["timing_pass_rate"] == 0.75
    assert coarse_s2["timing_center_passed"]
    endpoint_s2 = gates(
        S2_TIMED_STRUM,
        timing_applicable=False,
        strum_microtiming_applicable=False,
        worst_direction_completion_gate=0.75,
        end_to_end_recovery_completion_gate=0.75,
        zone_applicable=False,
        strum_completion_gate=0.80)
    assert endpoint_s2["passed"]
    assert not endpoint_s2["timing_applicable"]
    assert not endpoint_s2["strum_microtiming_applicable"]
    weak_direction = metrics()
    weak_direction["worst_direction_completion_rate"] = 0.74
    assert not gates(
        S2_TIMED_STRUM, weak_direction,
        timing_applicable=False,
        strum_microtiming_applicable=False,
        worst_direction_completion_gate=0.75,
        end_to_end_recovery_completion_gate=0.75,
        zone_applicable=False)["strum_passed"]
    weak_recovery = metrics()
    weak_recovery["end_to_end_recovery_completion_rate"] = 0.74
    assert not gates(
        S2_TIMED_STRUM, weak_recovery,
        timing_applicable=False,
        strum_microtiming_applicable=False,
        worst_direction_completion_gate=0.75,
        end_to_end_recovery_completion_gate=0.75,
        zone_applicable=False)["recovery_passed"]
    off_center_s2 = metrics()
    off_center_s2["timing_signed_mean_ms"] = -170.0
    off_center_s2["timing_signed_p10_ms"] = -200.0
    assert not gates(
        S2_TIMED_STRUM,
        off_center_s2,
        timing_tolerance_ms=250,
        timing_pass_rate_gate=0.70,
        timing_center_mean_abs_gate_ms=110,
        timing_center_tail_abs_gate_ms=190,
        zone_applicable=False,
        strum_completion_gate=0.70,
        strum_timing_rms_gate_ms=300,
        strum_duration_mae_gate_ms=200)["timing_center_passed"]
    insufficient_s2 = metrics()
    insufficient_s2["timing_pass_rate"] = 0.69
    assert not gates(
        S2_TIMED_STRUM,
        insufficient_s2,
        timing_tolerance_ms=400,
        timing_pass_rate_gate=0.70,
        zone_applicable=False,
        strum_completion_gate=0.70,
        strum_timing_rms_gate_ms=300,
        strum_duration_mae_gate_ms=200)["timing_passed"]
    song = gates(S3_SONG_INTEGRATION)
    assert song["passed"] and song["zone_applicable"]
    canonical = {
        "strike_grip_success_rate": 0.95,
        "strike_grip_quality_mean": 0.96,
        "strike_grip_quality_p05": 0.92,
        "strike_grip_quality_min": 0.88,
        "strike_grip_pinch_quality_mean": 0.98,
        "strike_grip_free_quality_mean": 0.92,
        "strike_grip_bad_frame_rate": 0.01,
        "grip_bad_streak_max_frames": 2,
        "strike_tip_ready_success_rate": 0.95,
        "strike_precision": 0.99,
        "strike_release_recall": 0.99,
        "strike_false_positive_rate": 0.01,
        "strike_episode_f1": 0.99,
        "strike_timing_p95_ms": 45.0,
        "strike_zone_success_rate": 0.97,
        "strum_event_count": 8,
        "strum_completion_rate": 0.98,
        "strum_traversal_recall": 1.0,
        "strum_order_accuracy": 1.0,
        "strum_direction_accuracy": 1.0,
        "strum_unplanned_crossing_rate": 0.0,
        "strum_timing_rms_ms": 20.0,
        "strum_sweep_duration_mae_ms": 15.0,
        "strum_microtiming_sample_count": 8,
        "recovery_completion_rate": 1.0,
        "scheduled_recovery_completion_rate": 1.0,
        "conditional_recovery_completion_rate": 1.0,
        "end_to_end_recovery_completion_rate": 1.0,
        "worst_direction_completion_rate": 0.98,
        "full_recovery_completion_rate": 1.0,
        "full_recovery_event_count": 4,
        "handoff_recovery_completion_rate": 1.0,
        "handoff_recovery_event_count": 4,
        "recovery_event_count": 8,
        "recovery_reset_count": 0,
        "blocked_crossing_count": 0,
    }
    assert gates(S3_SONG_INTEGRATION, canonical)["passed"]
    fixed_only_bad = metrics()
    fixed_only_bad["recovery_completion_rate"] = 0.77
    assert gates(S3_SONG_INTEGRATION, fixed_only_bad)["recovery_passed"]
    bad_handoff = metrics()
    bad_handoff["handoff_recovery_completion_rate"] = 0.99
    assert not gates(S3_SONG_INTEGRATION, bad_handoff)["recovery_passed"]
    canonical["precision"] = 0.0
    assert gates(S3_SONG_INTEGRATION, canonical)["precision"] == 0.99
    bad = metrics()
    bad["zone_success_rate"] = 0.94
    assert not gates(S3_SONG_INTEGRATION, bad)["zone_passed"]

    strum = metrics()
    strum.update({
        "strum_event_count": 8,
        "strum_completion_rate": 0.98,
        "strum_traversal_recall": 1.0,
        "strum_order_accuracy": 1.0,
        "strum_direction_accuracy": 1.0,
        "strum_unplanned_crossing_rate": 0.0,
    })
    assert gates(S3_SONG_INTEGRATION, strum)["strum_passed"]
    strum["strum_order_accuracy"] = 0.8
    assert not gates(S3_SONG_INTEGRATION, strum)["strum_passed"]
    slow_strum = metrics()
    slow_strum["strum_timing_rms_ms"] = 25.001
    result = gates(S3_SONG_INTEGRATION, slow_strum)
    assert not result["strum_microtiming_passed"]
    slow_strum = metrics()
    slow_strum["strum_sweep_duration_mae_ms"] = 20.001
    result = gates(S3_SONG_INTEGRATION, slow_strum)
    assert not result["strum_microtiming_passed"]
    no_microtiming = metrics()
    no_microtiming["strum_microtiming_sample_count"] = 0
    result = gates(S3_SONG_INTEGRATION, no_microtiming)
    assert not result["strum_microtiming_passed"]
    no_strum = metrics()
    no_strum["strum_event_count"] = 0
    assert not gates(S3_SONG_INTEGRATION, no_strum)["strum_passed"]
    pick_only_song = gates(
        S3_SONG_INTEGRATION,
        no_strum,
        strum_applicable=False)
    assert pick_only_song["passed"]
    assert not pick_only_song["strum_applicable"]
    assert not pick_only_song["strum_microtiming_applicable"]

    incomplete = rows()
    incomplete[0] = {
        "goal_finished": False, "failure_termination": False}
    result = gates(A0_PICK_GRIP, episode_rows=incomplete)
    assert not result["full_episode_passed"] and not result["passed"]
    unsafe = gates(S3_SONG_INTEGRATION, safety_passed=False)
    assert unsafe["task_passed"] and not unsafe["passed"]


    missing = metrics()
    del missing["timing_p95_ms"]
    expect_error(
        "timing_p95_ms",
        lambda: gates(A3_TIMED_SINGLE, missing))
    invalid = metrics()
    invalid["release_recall"] = float("nan")
    expect_error(
        "finite",
        lambda: gates(A2_SINGLE_CROSSING, invalid))
    invalid = metrics()
    invalid["release_recall"] = True
    expect_error(
        "finite scalar",
        lambda: gates(A2_SINGLE_CROSSING, invalid))
    string_goal = rows()
    string_goal[0]["goal_finished"] = "false"
    expect_error(
        "goal_finished must be bool",
        lambda: gates(A0_PICK_GRIP, episode_rows=string_goal))
    string_failure = rows()
    string_failure[0]["failure_termination"] = "false"
    expect_error(
        "failure_termination must be bool",
        lambda: gates(A0_PICK_GRIP, episode_rows=string_failure))
    expect_error(
        "safety_passed must be bool",
        lambda: gates(A0_PICK_GRIP, safety_passed="false"))
    expect_error(
        "unknown",
        lambda: gates("A9_UNKNOWN"))
    print("PASS: single and strum evaluation gates apply only acquired skills")


if __name__ == "__main__":
    main()
