"""CPU contracts for the five-stage, performance-gated strike curriculum."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from learning.strike_curriculum import (  # noqa: E402
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
    return {"curriculum_grip_success_rate": value}


def ready(value=0.95):
    return {
        "episodes": 1,
        "strike_grip_success_rate": 0.95,
        "strike_tip_ready_success_rate": value,
    }


def crossing(recall=0.99, false_positive=0.01):
    return {
        "episodes": 1,
        "strike_grip_success_rate": 0.95,
        "strike_tip_ready_success_rate": 0.95,
        "strike_release_recall": recall,
        "strike_false_positive_rate": false_positive,
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

    # Maximum iteration is a stalled diagnostic, never an automatic promotion.
    curriculum.after_iteration(grip(0.0))
    stalled = curriculum.after_iteration(grip(0.0))
    assert curriculum.stage == A0_PICK_GRIP
    assert stalled["curriculum_stalled"]
    curriculum.after_iteration(grip())
    assert curriculum.stage == A0_PICK_GRIP  # one passing window is insufficient
    curriculum.after_iteration(grip())
    assert curriculum.stage == A1_TIP_READY
    assert not curriculum.stalled and curriculum.stage_iteration == 0

    # Missing a retained episode grip metric fails closed.  A rollout without
    # a terminal A1 episode is no evidence and preserves, but cannot advance,
    # the streak; a completed failed episode breaks it.
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
    promote(curriculum, ready())
    assert curriculum.stage == A2_FREE_CROSSING

    # Terminal gates pool a complete non-overlapping episode cohort.  Three
    # tiny success-only rollouts cannot hide the failure that completes the
    # fourth row, and a partially accumulated cohort survives checkpointing.
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

    # A2 has no timing gate.  Recall/FP and all earlier skills gate promotion.
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

    # A3 needs a fresh run of consecutive windows at every tolerance level.
    curriculum.after_iteration(timed(90))
    state = curriculum.after_iteration(timed(90))
    assert curriculum.stage == A3_TIMED_CROSSING
    assert state["curriculum_timing_tolerance_ms"] == 67
    assert state["curriculum_strike_f1_gate"] == 0.90
    assert state["curriculum_timing_streak"] == 0

    # Tightening is itself an environment change and therefore requests reset.
    applied = curriculum.apply(env)
    assert env.calls[-1] == (A3_TIMED_CROSSING, 67, True)
    assert "_reset_observation" in applied

    curriculum.after_iteration(timed(60))
    curriculum.after_iteration(timed(70))  # outside +/-67 ms: reset streak
    assert curriculum.timing_streak == 0
    curriculum.after_iteration(timed(60))
    state = curriculum.after_iteration(timed(60))
    assert state["curriculum_timing_tolerance_ms"] == 50
    assert state["curriculum_strike_f1_gate"] == 0.95
    assert curriculum.stage == A3_TIMED_CROSSING

    # Save/restore preserves a partial final-tolerance streak exactly.
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

    # Live per-frame diagnostics cannot complete A4.  A rollout with no
    # terminal episode is "no evidence": it neither advances nor resets a
    # legitimate episode-based promotion streak.
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
    assert restored.complete and completed["curriculum_complete"]
    final_iteration = restored.stage_iteration
    restored.after_iteration(zone())
    assert restored.stage == A4_ZONE_CONTROL
    assert restored.stage_iteration == final_iteration + 1

    # Context/config mismatch fails instead of silently changing tolerance.
    bad = dict(saved, curriculum_timing_tolerance_ms=51)
    expect_error("disagrees", lambda: StrikeCurriculum(config()).load_context(bad))
    bad = dict(saved, curriculum_timing_level=9)
    expect_error("outside", lambda: StrikeCurriculum(config()).load_context(bad))

    # Timing schedule must narrow strictly.
    expect_error(
        "strictly decreasing",
        lambda: StrikeCurriculumConfig(timing_tolerances_ms=(100, 100, 50)))
    expect_error(
        "positive integer",
        lambda: StrikeCurriculumConfig(terminal_evidence_episodes=0))

    # Success before the minimum is capped below the transition threshold, so
    # every normally saved checkpoint remains resumable.
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
