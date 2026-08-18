"""CPU contracts for the five-stage, performance-gated strike curriculum."""
from __future__ import annotations

from dataclasses import replace
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
    StrikeCurriculum,
    StrikeCurriculumConfig,
)


class FakeEnv:
    def __init__(self):
        self.curriculum_stage = "UNSET"
        self.timing_tolerance_ms = None
        self.calls = []

    def set_curriculum_stage(self, stage, tolerance_ms, reset=False):
        self.calls.append((stage, tolerance_ms, reset))
        self.curriculum_stage = stage
        self.timing_tolerance_ms = tolerance_ms
        return f"reset:{stage}:{tolerance_ms}" if reset else None


def config():
    return StrikeCurriculumConfig(
        grip_min_iterations=1,
        grip_max_iterations=2,
        ready_min_iterations=1,
        ready_max_iterations=3,
        crossing_min_iterations=1,
        crossing_max_iterations=3,
        timed_min_iterations=1,
        timed_max_iterations=20,
        zone_min_iterations=1,
        zone_max_iterations=5,
        promotion_windows=2,
        grip_success_gate=0.90,
        tip_ready_success_gate=0.90,
        release_recall_gate=0.98,
        false_positive_rate_gate=0.02,
        strike_f1_gate=0.98,
        timing_tolerances_ms=(100, 67, 50),
        timed_f1_by_level=(0.80, 0.90, 0.95),
        zone_f1_gate=0.98,
        zone_success_gate=0.95,
    )


def grip(value=0.95):
    return {
        "episodes": 1,
        "strike_grip_success_rate": value,
        "failure_termination": 0.0,
    }


def ready(value=0.95):
    return {
        "episodes": 1,
        "strike_grip_success_rate": 0.95,
        "strike_tip_ready_success_rate": value,
        "failure_termination": 0.0,
    }


def crossing(recall=0.99, false_positive=0.01):
    return {
        "episodes": 1,
        "strike_grip_success_rate": 0.95,
        "strike_tip_ready_success_rate": 0.95,
        "strike_release_recall": recall,
        "strike_false_positive_rate": false_positive,
        "failure_termination": 0.0,
    }


def timed(p95, f1=0.99):
    return {
        **crossing(),
        "strike_episode_f1": f1,
        "strike_timing_p95_ms": p95,
    }


def zone(p95=45, f1=0.99, zone_success=0.98):
    return {
        **timed(p95, f1=f1),
        "strike_zone_success_rate": zone_success,
    }


def promote(curriculum, stats):
    curriculum.after_iteration(stats)
    return curriculum.after_iteration(stats)


def expect_error(fragment, callback):
    try:
        callback()
    except ValueError as exc:
        assert fragment in str(exc), str(exc)
    else:
        raise AssertionError(f"expected ValueError containing {fragment!r}")


def main():
    curriculum = StrikeCurriculum(config())
    assert curriculum.stage == A0_PICK_GRIP
    assert curriculum.timing_tolerance_ms == 100
    assert not curriculum.timing_applicable

    env = FakeEnv()
    applied = curriculum.apply(env)
    assert env.calls[-1] == (A0_PICK_GRIP, 100, True)
    assert applied["_reset_observation"] == "reset:A0_PICK_GRIP:100"
    applied = curriculum.apply(env)
    assert env.calls[-1] == (A0_PICK_GRIP, 100, False)
    assert "_reset_observation" not in applied


    curriculum.after_iteration(grip(0.0))
    stalled = curriculum.after_iteration(grip(0.0))
    assert curriculum.stage == A0_PICK_GRIP
    assert stalled["curriculum_stalled"]
    unsafe_grip = grip()
    unsafe_grip["failure_termination"] = 1.0
    curriculum.after_iteration(unsafe_grip)
    assert curriculum.promotion_streak == 0
    curriculum.after_iteration(grip())
    assert curriculum.stage == A0_PICK_GRIP
    curriculum.after_iteration(grip())
    assert curriculum.stage == A1_TIP_READY
    assert not curriculum.stalled and curriculum.stage_iteration == 0




    curriculum.after_iteration(
        {"episodes": 1, "strike_tip_ready_success_rate": 1.0})
    curriculum.after_iteration(ready())
    ready_streak = curriculum.promotion_streak
    curriculum.after_iteration({
        "curriculum_grip_success_rate": 1.0,
        "curriculum_tip_ready_success_rate": 1.0,
    })
    assert curriculum.promotion_streak == ready_streak
    curriculum.after_iteration(ready(0.0))
    assert curriculum.stage == A1_TIP_READY
    failed_recovery = ready()
    failed_recovery["failure_termination"] = 1.0
    curriculum.after_iteration(failed_recovery)
    assert curriculum.promotion_streak == 0
    promote(curriculum, ready())
    assert curriculum.stage == A2_FREE_CROSSING




    pooled_config = replace(
        config(), terminal_evidence_episodes=4)
    pooled = StrikeCurriculum(pooled_config)
    pooled.stage = A1_TIP_READY
    for _ in range(3):
        pooled.after_iteration(ready())
    assert pooled.promotion_streak == 0
    assert pooled.state()["curriculum_evidence_episodes"] == 3
    pooled_saved = pooled.state()
    pooled_restored = StrikeCurriculum(pooled_config)
    pooled_restored.load_context(pooled_saved)
    assert pooled_restored.state() == pooled_saved
    pooled_restored.after_iteration(ready(0.0))
    assert pooled_restored.promotion_streak == 0
    assert pooled_restored.state()["curriculum_evidence_episodes"] == 0
    for _ in range(4):
        pooled_restored.after_iteration(ready())
    assert pooled_restored.promotion_streak == 1
    for _ in range(4):
        pooled_restored.after_iteration(ready())
    assert pooled_restored.stage == A2_FREE_CROSSING


    curriculum.after_iteration({
        **crossing(),
        "curriculum_timing_p95_ms": 10000.0,
    })
    curriculum.after_iteration({
        **crossing(false_positive=0.03),
        "curriculum_timing_p95_ms": 0.0,
    })
    assert curriculum.stage == A2_FREE_CROSSING
    promote(curriculum, crossing())
    assert curriculum.stage == A3_TIMED_CROSSING
    assert curriculum.timing_applicable
    assert curriculum.timing_tolerance_ms == 100
    assert curriculum.current_timed_f1_gate == 0.80


    curriculum.after_iteration(timed(90))
    state = curriculum.after_iteration(timed(90))
    assert curriculum.stage == A3_TIMED_CROSSING
    assert state["curriculum_timing_tolerance_ms"] == 67
    assert state["curriculum_strike_f1_gate"] == 0.90
    assert state["curriculum_timing_streak"] == 0


    applied = curriculum.apply(env)
    assert env.calls[-1] == (A3_TIMED_CROSSING, 67, True)
    assert "_reset_observation" in applied

    curriculum.after_iteration(timed(60))
    curriculum.after_iteration(timed(70))
    assert curriculum.timing_streak == 0
    curriculum.after_iteration(timed(60))
    state = curriculum.after_iteration(timed(60))
    assert state["curriculum_timing_tolerance_ms"] == 50
    assert state["curriculum_strike_f1_gate"] == 0.95
    assert curriculum.stage == A3_TIMED_CROSSING


    curriculum.after_iteration(timed(45))
    saved = curriculum.state()
    restored = StrikeCurriculum(config())
    restored.load_context(saved)
    assert restored.state() == saved
    restored.after_iteration(timed(45))
    assert restored.stage == A4_ZONE_CONTROL
    assert restored.timing_tolerance_ms == 50
    assert restored.current_strike_f1_gate == 0.98
    assert restored.state()["curriculum_strike_f1_gate"] == 0.98
    assert not restored.complete




    live_only = {
        "curriculum_grip_success_rate": 1.0,
        "curriculum_tip_ready_success_rate": 1.0,
        "curriculum_release_recall": 1.0,
        "curriculum_false_positive_rate": 0.0,
        "curriculum_strike_f1": 1.0,
        "curriculum_timing_p95_ms": 0.0,
        "curriculum_zone_success_rate": 1.0,
    }
    restored.after_iteration(live_only)
    assert restored.promotion_streak == 0 and not restored.complete
    restored.after_iteration(zone())
    streak = restored.promotion_streak
    restored.after_iteration(live_only)
    assert restored.promotion_streak == streak and not restored.complete
    completed = restored.after_iteration(zone())
    assert not restored.complete
    assert completed["curriculum_tempo_lambda"] == 0.25
    previous_lambda = restored.tempo_lambda
    for _ in range(20):
        completed = restored.after_iteration(zone())
        assert restored.tempo_lambda >= previous_lambda
        previous_lambda = restored.tempo_lambda
        if restored.complete:
            break
    assert restored.complete and completed["curriculum_complete"]
    assert completed["curriculum_original_tempo_reached"]
    assert completed["curriculum_tempo_lambda"] == 1.0
    final_iteration = restored.stage_iteration
    restored.after_iteration(zone())
    assert restored.stage == A4_ZONE_CONTROL
    assert restored.stage_iteration == final_iteration + 1


    bad = dict(saved, curriculum_timing_tolerance_ms=51)
    expect_error("disagrees", lambda: StrikeCurriculum(config()).load_context(bad))
    bad = dict(saved, curriculum_timing_level=9)
    expect_error("outside", lambda: StrikeCurriculum(config()).load_context(bad))
    bad = dict(saved, curriculum_stalled="false")
    expect_error("must be bool", lambda: StrikeCurriculum(config()).load_context(bad))


    expect_error(
        "strictly decreasing",
        lambda: StrikeCurriculumConfig(timing_tolerances_ms=(100, 100, 50)))
    expect_error(
        "positive integer",
        lambda: StrikeCurriculumConfig(terminal_evidence_episodes=0))
    expect_error(
        "must be integers",
        lambda: StrikeCurriculumConfig(grip_min_iterations=0.5))
    expect_error(
        "positive integer",
        lambda: StrikeCurriculumConfig(promotion_windows=True))



    invalid_live = StrikeCurriculum(replace(
        config(), grip_min_iterations=0, promotion_windows=1))
    invalid_live.after_iteration(grip(1.0001))
    assert invalid_live.stage == A0_PICK_GRIP
    assert invalid_live.promotion_streak == 0
    invalid_live.after_iteration(grip(True))
    assert invalid_live.stage == A0_PICK_GRIP
    assert invalid_live.promotion_streak == 0

    for invalid_value in (-0.01, 1.01):
        invalid_rate = StrikeCurriculum(replace(
            config(), ready_min_iterations=0, promotion_windows=1))
        invalid_rate.stage = A1_TIP_READY
        bad_ready = ready()
        bad_ready["strike_tip_ready_success_rate"] = invalid_value
        invalid_rate.after_iteration(bad_ready)
        assert invalid_rate.stage == A1_TIP_READY
        assert invalid_rate.promotion_streak == 0

    invalid_timing = StrikeCurriculum(replace(
        config(), timed_min_iterations=0, promotion_windows=1))
    invalid_timing.stage = A3_TIMED_CROSSING
    invalid_timing.after_iteration(timed(-0.001))
    assert invalid_timing.stage == A3_TIMED_CROSSING
    assert invalid_timing.timing_level == 0
    assert invalid_timing.timing_streak == 0



    long_minimum = StrikeCurriculumConfig(
        grip_min_iterations=5,
        grip_max_iterations=10,
        promotion_windows=2)
    early = StrikeCurriculum(long_minimum)
    for _ in range(4):
        early.after_iteration(grip())
    assert early.promotion_streak == 1
    resumed = StrikeCurriculum(long_minimum)
    resumed.load_context(early.state())
    assert resumed.state() == early.state()
    print("PASS: A0->A4 performance gates and 100->67->50ms timing curriculum")


if __name__ == "__main__":
    main()
