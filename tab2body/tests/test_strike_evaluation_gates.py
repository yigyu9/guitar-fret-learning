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
    A2_FREE_CROSSING,
    A3_TIMED_CROSSING,
    A4_ZONE_CONTROL,
)
from tab2body.learning.strike_evaluation import (
    strike_evaluation_gate_summary,
)


def metrics():
    return {
        "grip_success_rate": 0.95,
        "tip_ready_success_rate": 0.95,
        "precision": 0.99,
        "release_recall": 0.99,
        "false_positive_rate": 0.01,
        "strike_f1": 0.99,
        "timing_p95_ms": 45.0,
        "zone_success_rate": 0.97,
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
    a0 = gates(A0_PICK_GRIP, {"grip_success_rate": 0.95})
    assert a0["passed"] and a0["grip_applicable"]
    assert not a0["tip_ready_applicable"]
    assert not a0["release_applicable"]
    assert not a0["timing_applicable"]
    assert not a0["zone_applicable"]


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

    a2 = gates(A2_FREE_CROSSING)
    assert a2["passed"] and a2["release_applicable"]
    assert not a2["timing_applicable"]
    bad = metrics()
    bad["precision"] = 0.97
    assert not gates(A2_FREE_CROSSING, bad)["release_passed"]
    bad = metrics()
    bad["release_recall"] = 0.97
    assert not gates(A2_FREE_CROSSING, bad)["release_passed"]
    bad = metrics()
    bad["false_positive_rate"] = 0.021
    assert not gates(A2_FREE_CROSSING, bad)["release_passed"]

    bad = metrics()
    bad["timing_p95_ms"] = 100000.0
    assert gates(A2_FREE_CROSSING, bad)["passed"]

    a3 = gates(A3_TIMED_CROSSING)
    assert a3["passed"] and a3["timing_applicable"]
    assert not a3["zone_applicable"]
    bad = metrics()
    bad["strike_f1"] = 0.97
    assert not gates(A3_TIMED_CROSSING, bad)["timing_passed"]
    at_67 = metrics()
    at_67["timing_p95_ms"] = 67.0
    assert gates(
        A3_TIMED_CROSSING, at_67, timing_tolerance_ms=67)["passed"]
    at_67["timing_p95_ms"] = 67.001
    assert not gates(
        A3_TIMED_CROSSING, at_67,
        timing_tolerance_ms=67)["timing_passed"]

    a4 = gates(A4_ZONE_CONTROL)
    assert a4["passed"] and a4["zone_applicable"]
    canonical = {
        "strike_grip_success_rate": 0.95,
        "strike_tip_ready_success_rate": 0.95,
        "strike_precision": 0.99,
        "strike_release_recall": 0.99,
        "strike_false_positive_rate": 0.01,
        "strike_episode_f1": 0.99,
        "strike_timing_p95_ms": 45.0,
        "strike_zone_success_rate": 0.97,
    }
    assert gates(A4_ZONE_CONTROL, canonical)["passed"]
    canonical["precision"] = 0.0
    assert gates(A4_ZONE_CONTROL, canonical)["precision"] == 0.99
    bad = metrics()
    bad["zone_success_rate"] = 0.94
    assert not gates(A4_ZONE_CONTROL, bad)["zone_passed"]

    strum = metrics()
    strum.update({
        "strum_event_count": 8,
        "strum_completion_rate": 0.98,
        "strum_traversal_recall": 1.0,
        "strum_order_accuracy": 1.0,
        "strum_direction_accuracy": 1.0,
        "strum_protected_crossing_rate": 0.0,
    })
    assert gates(A4_ZONE_CONTROL, strum)["strum_passed"]
    strum["strum_order_accuracy"] = 0.8
    assert not gates(A4_ZONE_CONTROL, strum)["strum_passed"]

    incomplete = rows()
    incomplete[0] = {
        "goal_finished": False, "failure_termination": False}
    result = gates(A0_PICK_GRIP, episode_rows=incomplete)
    assert not result["full_episode_passed"] and not result["passed"]
    unsafe = gates(A4_ZONE_CONTROL, safety_passed=False)
    assert unsafe["task_passed"] and not unsafe["passed"]


    missing = metrics()
    del missing["timing_p95_ms"]
    expect_error(
        "timing_p95_ms",
        lambda: gates(A3_TIMED_CROSSING, missing))
    invalid = metrics()
    invalid["release_recall"] = float("nan")
    expect_error(
        "finite",
        lambda: gates(A2_FREE_CROSSING, invalid))
    invalid = metrics()
    invalid["release_recall"] = True
    expect_error(
        "finite scalar",
        lambda: gates(A2_FREE_CROSSING, invalid))
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
    print("PASS: A0-A4 evaluation gates apply only acquired strike skills")


if __name__ == "__main__":
    main()
