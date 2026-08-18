"""CPU contracts for checkpointed Strike curriculum wiring."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
from types import SimpleNamespace


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tab2body.strike_cfg import STRIKE
from tab2body.strike_training_runtime import (
    StrikeCurriculumRuntime,
    build_strike_curriculum,
    validate_strike_goal_for_training,
    validate_strike_training_alignment,
)


class FakeEnv:
    curriculum_stage = "UNSET"
    timing_tolerance_ms = None

    def set_curriculum_stage(self, stage, tolerance_ms, reset=False):
        changed = (
            self.curriculum_stage != stage
            or self.timing_tolerance_ms != tolerance_ms)
        self.curriculum_stage = stage
        self.timing_tolerance_ms = tolerance_ms
        return "reset-observation" if reset and changed else None


def main():
    config = deepcopy(STRIKE)
    config["curriculum"]["terminal_evidence_fraction"] = 0.5
    curriculum = build_strike_curriculum(config, 8)
    assert curriculum.config.terminal_evidence_episodes == 4

    validation = validate_strike_goal_for_training(
        config["goal_path"], config, require_a4=True)
    assert validation["contract_valid"]
    unsafe = deepcopy(config)
    unsafe["safety"]["penetration_threshold_m"] = 0.0
    try:
        validate_strike_goal_for_training(
            unsafe["goal_path"], unsafe, require_a4=False)
    except ValueError as exc:
        assert "penetration_threshold_m" in str(exc)
    else:
        raise AssertionError("invalid Strike safety must fail before GPU allocation")
    wrong_termination = deepcopy(config)
    wrong_termination["safety"]["penetration_termination"] = "false"
    try:
        validate_strike_goal_for_training(
            wrong_termination["goal_path"], wrong_termination,
            require_a4=False)
    except TypeError as exc:
        assert "penetration_termination" in str(exc)
    else:
        raise AssertionError("Strike safety booleans must fail closed")
    short_horizon = deepcopy(config)
    short_horizon["episode"]["A3_TIMED_CROSSING"] = 107
    try:
        validate_strike_goal_for_training(
            short_horizon["goal_path"], short_horizon, require_a4=False)
    except ValueError as exc:
        assert "A3_TIMED_CROSSING=107 (requires >= 108)" in str(exc)
    else:
        raise AssertionError("late timing and recovery tail must fit horizon")
    hold_goal = (
        PROJECT_ROOT / "data" / "song_bundles"
        / "03_Rock1-130-A_solo" / "training" / "strike_training.json")
    validate_strike_goal_for_training(
        hold_goal, config, require_a4=False)
    close_validation = validate_strike_goal_for_training(
        hold_goal, config, require_a4=True)
    assert close_validation["compiled_num_events"] > 0
    assert close_validation["window_fraction"] < 0.5

    runtime = StrikeCurriculumRuntime(
        curriculum,
        fixed_stage="A3_TIMED_CROSSING",
        tolerance_ms=67)
    env = FakeEnv()
    state, reset = runtime.apply(env)
    assert reset == "reset-observation"
    assert state["curriculum_stage"] == "A3_TIMED_CROSSING"
    assert state["curriculum_timing_tolerance_ms"] == 67
    state, reset, transition = runtime.after_iteration({}, env)
    assert reset is None and transition is None
    assert state["curriculum_stage_iteration"] == 1

    aligned_env = SimpleNamespace(
        reward_fn=SimpleNamespace(reach_discount=0.95))
    validate_strike_training_alignment(
        aligned_env, SimpleNamespace(gamma=0.95))
    try:
        validate_strike_training_alignment(
            aligned_env, SimpleNamespace(gamma=0.99))
    except ValueError as exc:
        assert "must exactly match" in str(exc)
    else:
        raise AssertionError("reward and PPO discounts must not diverge")

    try:
        build_strike_curriculum(config, True)
    except ValueError as exc:
        assert "num_envs" in str(exc)
    else:
        raise AssertionError("boolean num_envs must fail closed")

    unknown = deepcopy(config)
    unknown["curriculum"]["typo_gate"] = 1.0
    try:
        build_strike_curriculum(unknown, 8)
    except ValueError as exc:
        assert "unknown=['typo_gate']" in str(exc)
    else:
        raise AssertionError("unknown curriculum keys must fail closed")

    try:
        StrikeCurriculumRuntime(
            build_strike_curriculum(config, 8),
            fixed_stage="A3_TIMED_CROSSING",
            tolerance_ms=66.6)
    except ValueError as exc:
        assert "must be one of" in str(exc)
    else:
        raise AssertionError("fixed tolerance must match the schedule exactly")

    print("PASS: Strike curriculum mapping and lifecycle are runtime-fingerprinted")


if __name__ == "__main__":
    main()
