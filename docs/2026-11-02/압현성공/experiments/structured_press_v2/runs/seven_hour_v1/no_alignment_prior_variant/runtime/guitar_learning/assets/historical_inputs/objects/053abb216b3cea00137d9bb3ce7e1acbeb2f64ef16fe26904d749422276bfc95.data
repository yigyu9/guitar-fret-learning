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
    tempo_lambda = None
    strum_span = None
    s2_profile_name = None
    zone_gate_active = None
    timing_reward_core_ms = None
    duration_reward_core_ms = None
    approach_lead_s = None
    timing_early_grace_ms = None
    timing_early_penalty_scale_ms = None
    curriculum_song_f1_gate = None
    song_events_per_episode = 8
    curriculum_stalled = False
    goals = SimpleNamespace(num_events=123)

    def set_curriculum_stage(
            self, stage, tolerance_ms, tempo_lambda=1.0,
            strum_span=1, s2_profile_name=None, zone_active=None,
            timing_reward_core_ms=None, duration_reward_core_ms=None,
            approach_lead_s=None, timing_early_grace_ms=None,
            timing_early_penalty_scale_ms=None,
            song_f1_gate=None,
            song_events_per_episode=None,
            stalled=False,
            reset=False):
        changed = (
            self.curriculum_stage != stage
            or self.timing_tolerance_ms != tolerance_ms)
        self.curriculum_stage = stage
        self.timing_tolerance_ms = tolerance_ms
        self.tempo_lambda = tempo_lambda
        self.strum_span = strum_span
        self.s2_profile_name = s2_profile_name
        self.zone_gate_active = zone_active
        self.timing_reward_core_ms = timing_reward_core_ms
        self.duration_reward_core_ms = duration_reward_core_ms
        self.approach_lead_s = approach_lead_s
        self.timing_early_grace_ms = timing_early_grace_ms
        self.timing_early_penalty_scale_ms = timing_early_penalty_scale_ms
        self.curriculum_song_f1_gate = song_f1_gate
        self.song_events_per_episode = song_events_per_episode
        self.curriculum_stalled = stalled
        return "reset-observation" if reset and changed else None


def main():
    config = deepcopy(STRIKE)
    config["curriculum"]["terminal_evidence_fraction"] = 0.5
    curriculum = build_strike_curriculum(config, 8)
    assert curriculum.config.terminal_evidence_episodes == 4

    hold_goal = (
        PROJECT_ROOT / "data" / "song_bundles"
        / "00_SS1-68-E_comp" / "training"
        / "strike_plan.json")
    validation = validate_strike_goal_for_training(
        hold_goal, config, require_song=True)
    assert validation["contract_valid"]
    assert validation["song_has_strum"]
    assert validation["curriculum_route"] == "pick_and_strum"
    pick_only_goal = (
        PROJECT_ROOT / "data" / "song_bundles"
        / "02_Jazz1-200-B_solo" / "training"
        / "strike_plan.json")
    pick_only_validation = validate_strike_goal_for_training(
        pick_only_goal, config, require_song=True)
    assert not pick_only_validation["song_has_strum"]
    assert pick_only_validation["maximum_strum_span"] == 0
    assert pick_only_validation["curriculum_route"] == "pick_only"
    assert pick_only_validation["curriculum_active_stages"] == [
        "A0_PICK_GRIP", "A1_TIP_READY", "A2_SINGLE_CROSSING",
        "A3_TIMED_SINGLE", "S3_SONG_INTEGRATION"]
    mismatched_gap = deepcopy(config)
    mismatched_gap["detector"]["rearm_min_frames"] = 3
    try:
        validate_strike_goal_for_training(
            hold_goal, mismatched_gap, require_song=True)
    except ValueError as exc:
        assert "different rearm/follow-through settings" in str(exc)
    else:
        raise AssertionError(
            "plan edge-gap contract must match the runtime detector config")
    unsafe = deepcopy(config)
    unsafe["safety"]["penetration_threshold_m"] = 0.0
    try:
        validate_strike_goal_for_training(
            unsafe["goal_path"], unsafe, require_song=False)
    except ValueError as exc:
        assert "penetration_threshold_m" in str(exc)
    else:
        raise AssertionError("invalid Strike safety must fail before GPU allocation")
    wrong_termination = deepcopy(config)
    wrong_termination["safety"]["penetration_termination"] = "false"
    try:
        validate_strike_goal_for_training(
            wrong_termination["goal_path"], wrong_termination,
            require_song=False)
    except TypeError as exc:
        assert "penetration_termination" in str(exc)
    else:
        raise AssertionError("Strike safety booleans must fail closed")
    low_clearance = deepcopy(config)
    low_clearance["trajectory"]["clearance_height_m"] = 0.001
    try:
        validate_strike_goal_for_training(
            hold_goal, low_clearance, require_song=False)
    except ValueError as exc:
        assert "clearance_height_m" in str(exc)
    else:
        raise AssertionError("clearance must rearm before GPU allocation")
    short_horizon = deepcopy(config)
    short_horizon["episode"]["A3_TIMED_SINGLE"] = 107
    try:
        validate_strike_goal_for_training(
            short_horizon["goal_path"], short_horizon, require_song=False)
    except ValueError as exc:
        assert "A3_TIMED_SINGLE=107 (requires >= 108)" in str(exc)
    else:
        raise AssertionError("late timing and recovery tail must fit horizon")
    validate_strike_goal_for_training(
        hold_goal, config, require_song=False)
    assert validation["compiled_num_events"] > 0
    assert validation["window_fraction"] < 0.5

    runtime = StrikeCurriculumRuntime(
        curriculum,
        fixed_stage="A3_TIMED_SINGLE",
        tolerance_ms=67)
    env = FakeEnv()
    state, reset = runtime.apply(env)
    assert reset == "reset-observation"
    assert state["curriculum_stage"] == "A3_TIMED_SINGLE"
    assert state["curriculum_timing_tolerance_ms"] == 67
    state, reset, transition = runtime.after_iteration({}, env)
    assert reset is None and transition is None
    assert state["curriculum_stage_iteration"] == 1

    continuing = build_strike_curriculum(STRIKE, 1)
    continuing.stage = "S0_TWO_STRING_STRUM"
    continuing.stage_iteration = (
        continuing.config.max_iterations[continuing.stage] - 1)
    continuing_runtime = StrikeCurriculumRuntime(continuing)
    continuing_env = FakeEnv()
    continuing_runtime.apply(continuing_env)
    stalled_stats = {
        "episodes": 1,
        "strike_grip_success_rate": 1.0,
        "strike_grip_quality_mean": 1.0,
        "strike_grip_quality_p05": 1.0,
        "strike_grip_pinch_quality_mean": 1.0,
        "strike_grip_free_quality_mean": 1.0,
        "strike_grip_bad_frame_rate": 0.0,
        "strike_grip_bad_streak_max_frames": 0.0,
        "strike_tip_ready_success_rate": 1.0,
        "strike_release_recall": 0.0,
        "strike_false_positive_rate": 0.0,
        "strike_episode_f1": 0.0,
        "strike_true_positive_count": 0.0,
        "strike_false_positive_count": 0.0,
        "strike_false_negative_count": 1.0,
        "strike_timing_p95_ms": 0.0,
        "strike_timing_pass_rate": 0.0,
        "strike_timing_signed_mean_ms": 0.0,
        "strike_timing_signed_p10_ms": 0.0,
        "strike_timing_signed_p90_ms": 0.0,
        "strike_zone_success_rate": 0.0,
        "strike_strum_completion_rate": 0.0,
        "strike_strum_traversal_recall": 0.0,
        "strike_strum_order_accuracy": 1.0,
        "strike_strum_direction_accuracy": 1.0,
        "strike_strum_timing_rms_ms": 0.0,
        "strike_strum_sweep_duration_mae_ms": 0.0,
        "strike_strum_microtiming_sample_count": 1.0,
        "strike_strum_event_count": 1.0,
        "strike_recovery_completion_rate": 1.0,
        "strike_recovery_event_count": 1.0,
        "strike_scheduled_recovery_completed_count": 1.0,
        "strike_full_recovery_event_count": 1.0,
        "strike_full_recovery_completed_count": 1.0,
        "strike_handoff_recovery_event_count": 1.0,
        "strike_handoff_recovery_completed_count": 1.0,
        "strike_recovery_reset_rate": 0.0,
        "strike_blocked_crossing_rate": 0.0,
        "strike_blocked_crossing_count": 0.0,
        "failure_termination": 0.0,
        "wrong_crossing_termination": 0.0,
        "irrecoverable_safety_failure": 0.0,
    }
    state, reset, transition = continuing_runtime.after_iteration(
        stalled_stats, continuing_env)
    assert reset is None and state["curriculum_stalled"]
    assert transition["to_stalled"] and not transition["from_stalled"]
    state, reset, transition = continuing_runtime.after_iteration(
        stalled_stats, continuing_env)
    assert reset is None and transition is None
    assert state["curriculum_stage_iteration"] > continuing.config.max_iterations[
        "S0_TWO_STRING_STRUM"]
    recovered_stats = dict(stalled_stats)
    recovered_stats.update({
        "strike_release_recall": 1.0,
        "strike_episode_f1": 1.0,
        "strike_true_positive_count": 1.0,
        "strike_false_negative_count": 0.0,
        "strike_zone_success_rate": 1.0,
        "strike_strum_completion_rate": 1.0,
        "strike_strum_traversal_recall": 1.0,
    })
    recovery_transition = None
    for _ in range(continuing.config.min_iterations[
            "S0_TWO_STRING_STRUM"] + 6):
        state, reset, transition = continuing_runtime.after_iteration(
            recovered_stats, continuing_env)
        if transition is not None and transition["from_stalled"]:
            recovery_transition = transition
        if state["curriculum_stage"] == "S1_STRUM_SPAN":
            break
    assert state["curriculum_stage"] == "S1_STRUM_SPAN"
    assert not state["curriculum_stalled"]
    assert recovery_transition["from_stalled"]
    assert not recovery_transition["to_stalled"]

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

    for key, value in (
            ("stalled_hard_sample_fraction", 1.1),
            ("stalled_hard_rehearsal_events", 1),
            ("stalled_failure_score_decay", 0.0),
            ("stalled_failure_prior_exposure", -1.0),
            ("stalled_hard_window_probability_cap", 0.0),
            ("s3_uniform_curriculum_evidence_only", 1)):
        invalid_mining = deepcopy(config)
        invalid_mining["curriculum"][key] = value
        try:
            build_strike_curriculum(invalid_mining, 8)
        except (TypeError, ValueError) as exc:
            assert "failure-mining" in str(exc)
        else:
            raise AssertionError(f"invalid failure-mining value accepted: {key}")

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
            fixed_stage="A3_TIMED_SINGLE",
            tolerance_ms=66.6)
    except ValueError as exc:
        assert "must be one of" in str(exc)
    else:
        raise AssertionError("fixed tolerance must match the schedule exactly")

    try:
        StrikeCurriculumRuntime(
            build_strike_curriculum(
                config, 8, song_has_strum=False),
            fixed_stage="S2_TIMED_STRUM")
    except ValueError as exc:
        assert "pick-only" in str(exc)
    else:
        raise AssertionError(
            "pick-only songs must reject fixed strum stages")

    rehearsal = build_strike_curriculum(
        config, 8, song_has_strum=False)
    rehearsal.stage = "S3_SONG_INTEGRATION"
    rehearsal.stalled = True
    rehearsal.tempo_level = len(rehearsal.config.tempo_lambdas) - 1
    rehearsal_runtime = StrikeCurriculumRuntime(rehearsal)
    rehearsal_env = FakeEnv()
    rehearsal_state, _ = rehearsal_runtime.apply(rehearsal_env)
    assert rehearsal.s3_original_tempo_rehearsal_active
    assert rehearsal_env.song_events_per_episode == 123
    assert rehearsal_state[
        "curriculum_training_song_events_per_episode"] == 123
    assert rehearsal_state[
        "curriculum_original_tempo_rehearsal_full_song"]

    mastered = build_strike_curriculum(STRIKE, 1, song_has_strum=False)
    mastered.initialize_song_integration_transfer(1.0)
    mastered.complete = True
    mastered_runtime = StrikeCurriculumRuntime(mastered)
    mastered_env = FakeEnv()
    mastered_runtime.apply(mastered_env)
    for _ in range(mastered.config.promotion_windows):
        state, reset, transition = mastered_runtime.after_iteration(
            {"_uniform_evidence": stalled_stats}, mastered_env)
        assert reset is None and transition is None
    assert state["curriculum_complete"]
    assert state["curriculum_quality_recovery_needed"]
    assert state["curriculum_original_tempo_holdout_status"] == "missing"
    assert state["curriculum_current_quality_passed"] is None
    assert mastered.gate_evaluation_count == mastered.config.promotion_windows
    assert mastered_env.tempo_lambda == 1.0
    assert not mastered_env.curriculum_stalled

    print("PASS: Strike curriculum mapping and lifecycle are runtime-fingerprinted")


if __name__ == "__main__":
    main()
