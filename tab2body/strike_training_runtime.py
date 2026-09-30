"""Checkpointed curriculum wiring for Strike training.

Launch, plotting and file-layout code belongs to ``train_strike.py``.  The
configuration mapping and the exact before/after-iteration stage semantics
live here so their implementation is part of the policy runtime fingerprint.
This module stays import-light: it imports neither Isaac Gym nor torch.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Mapping

from tab2body.strike_contract import (
    A0_PICK_GRIP,
    A1_TIP_READY,
    A2_SINGLE_CROSSING,
    A3_TIMED_SINGLE,
    A4_STRUM_CONTEXT_RECOVERY,
    S0_TWO_STRING_STRUM,
    S1_STRUM_SPAN,
    S2_TIMED_STRUM,
    S3_SONG_INTEGRATION,
    TIMED_PRACTICE_MIN_TIME_S,
    minimum_strike_stage_horizon,
    strike_curriculum_stages,
)


_CURRICULUM_KEYS = frozenset((
    "min_iterations",
    "max_iterations",
    "promotion_windows",
    "terminal_evidence_fraction",
    "timing_tolerances_ms",
    "s2_profiles",
    "s2_rollback_windows",
    "s2_rollback_cooldown_iterations",
    "s2_profile_adaptation_iterations",
    "s2_rollback_timing_pass_rate",
    "s2_rollback_completion_rate",
    "s2_rollback_traversal_rate",
    "s2_rollback_direction_rate",
    "s2_rollback_false_positive_rate",
    "s2_endpoint_recovery_windows",
    "s2_endpoint_recovery_trigger_rate",
    "s2_endpoint_focus_fraction",
    "s2_endpoint_proximal_std_floor",
    "s2_endpoint_std_floor_profiles",
    "tempo_lambdas",
    "s3_episode_event_counts",
    "s3_tempo_gates",
    "stalled_hard_sample_fraction",
    "stalled_hard_rehearsal_events",
    "stalled_failure_score_decay",
    "stalled_failure_prior_exposure",
    "stalled_hard_window_probability_cap",
    "s3_upstroke_sample_fraction",
    "s3_upstroke_window_probability_cap",
    "s3_uniform_curriculum_evidence_only",
    "s3_stalled_original_tempo_recovery",
    "s3_original_tempo_retention_drop_f1",
    "s3_original_tempo_holdout_max_age_iterations",
    "strum_spans",
    "grip_success_rate",
    "grip_quality_mean",
    "grip_quality_p05",
    "pinch_quality_mean",
    "free_quality_mean",
    "max_grip_bad_frame_rate",
    "max_grip_bad_streak_frames",
    "ready_success_rate",
    "release_recall",
    "max_wrong_rate_by_stage",
    "max_failure_rate_by_stage",
    "timed_f1_by_level",
    "zone_f1",
    "zone_success_rate",
    "strum_completion_rate",
    "strum_traversal_recall",
    "strum_order_accuracy",
    "strum_direction_accuracy_by_stage",
    "recovery_completion_rate",
    "full_recovery_completion_rate",
    "handoff_recovery_completion_rate",
    "max_recovery_reset_rate_by_stage",
    "max_blocked_crossing_rate_by_stage",
    "strum_timing_rms_ms",
    "strum_sweep_duration_mae_ms",
))


def _closed_mapping(name, value, expected):
    if not isinstance(value, Mapping):
        raise TypeError(f"{name} must be a mapping")
    missing = sorted(set(expected) - set(value))
    unknown = sorted(set(value) - set(expected))
    if missing or unknown:
        raise ValueError(
            f"{name} must have exact keys; missing={missing}, "
            f"unknown={unknown}")
    return value


def build_strike_curriculum(
        config: Mapping[str, object], num_envs: int, *, song_has_strum=True):
    """Build the closed curriculum object from the public Strike config."""
    from tab2body.learning.strike_curriculum import (
        StrikeCurriculum,
        StrikeCurriculumConfig,
    )

    if isinstance(num_envs, bool) or not isinstance(num_envs, int) or num_envs < 1:
        raise ValueError("num_envs must be a positive integer")
    if not isinstance(song_has_strum, bool):
        raise TypeError("song_has_strum must be bool")
    if not isinstance(config, Mapping):
        raise TypeError("strike config must be a mapping")
    curriculum = _closed_mapping(
        "strike curriculum config",
        config["curriculum"],
        _CURRICULUM_KEYS)
    raw_evidence_fraction = curriculum.get(
        "terminal_evidence_fraction", 1.0)
    if isinstance(raw_evidence_fraction, bool):
        raise ValueError(
            "terminal_evidence_fraction must be finite and in (0, 1]")
    evidence_fraction = float(raw_evidence_fraction)
    if (not math.isfinite(evidence_fraction)
            or not 0.0 < evidence_fraction <= 1.0):
        raise ValueError(
            "terminal_evidence_fraction must be finite and in (0, 1]")
    minimum = _closed_mapping(
        "strike curriculum min_iterations",
        curriculum["min_iterations"],
        StrikeCurriculum.STAGES)
    maximum = _closed_mapping(
        "strike curriculum max_iterations",
        curriculum["max_iterations"],
        StrikeCurriculum.STAGES)
    false_positive_rates = _closed_mapping(
        "strike curriculum max_wrong_rate_by_stage",
        curriculum["max_wrong_rate_by_stage"],
        StrikeCurriculum.STAGES)
    failure_rates = _closed_mapping(
        "strike curriculum max_failure_rate_by_stage",
        curriculum["max_failure_rate_by_stage"],
        StrikeCurriculum.STAGES)
    direction_rates = _closed_mapping(
        "strike curriculum strum_direction_accuracy_by_stage",
        curriculum["strum_direction_accuracy_by_stage"],
        StrikeCurriculum.STAGES)
    recovery_reset_rates = _closed_mapping(
        "strike curriculum max_recovery_reset_rate_by_stage",
        curriculum["max_recovery_reset_rate_by_stage"],
        StrikeCurriculum.STAGES)
    blocked_crossing_rates = _closed_mapping(
        "strike curriculum max_blocked_crossing_rate_by_stage",
        curriculum["max_blocked_crossing_rate_by_stage"],
        StrikeCurriculum.STAGES)
    failure_mining_values = {
        name: float(curriculum[name])
        for name in (
            "stalled_hard_sample_fraction",
            "stalled_failure_score_decay",
            "stalled_failure_prior_exposure",
            "stalled_hard_window_probability_cap",
            "s3_upstroke_sample_fraction",
            "s3_upstroke_window_probability_cap",
        )
        if not isinstance(curriculum[name], bool)
    }
    if len(failure_mining_values) != 6 or any(
            not math.isfinite(value)
            for value in failure_mining_values.values()):
        raise ValueError("strike failure-mining values must be finite numbers")
    if (not 0.0 <= failure_mining_values[
            "stalled_hard_sample_fraction"] <= 1.0
            or not 0.0 < failure_mining_values[
                "stalled_failure_score_decay"] <= 1.0
            or failure_mining_values[
                "stalled_failure_prior_exposure"] < 0.0
            or not 0.0 < failure_mining_values[
                "stalled_hard_window_probability_cap"] <= 1.0
            or not 0.0 <= failure_mining_values[
                "s3_upstroke_sample_fraction"] <= 1.0
            or failure_mining_values["stalled_hard_sample_fraction"]
            + failure_mining_values["s3_upstroke_sample_fraction"] > 0.75
            or not 0.0 < failure_mining_values[
                "s3_upstroke_window_probability_cap"] <= 1.0
            or not isinstance(
                curriculum["s3_uniform_curriculum_evidence_only"], bool)):
        raise ValueError("strike failure-mining configuration is invalid")
    rehearsal_events = curriculum["stalled_hard_rehearsal_events"]
    if (isinstance(rehearsal_events, bool)
            or not isinstance(rehearsal_events, int)
            or rehearsal_events < 2):
        raise ValueError(
            "strike failure-mining stalled_hard_rehearsal_events must be "
            "an integer >= 2")
    result = StrikeCurriculumConfig(
        min_iterations=dict(minimum),
        max_iterations=dict(maximum),
        default_approach_lead_s=config["trajectory"]["approach_lead_s"],
        promotion_windows=curriculum["promotion_windows"],
        terminal_evidence_episodes=max(
            1, int(math.ceil(num_envs * evidence_fraction))),
        grip_success_gate=curriculum["grip_success_rate"],
        grip_quality_mean_gate=curriculum["grip_quality_mean"],
        grip_quality_p05_gate=curriculum["grip_quality_p05"],
        pinch_quality_mean_gate=curriculum["pinch_quality_mean"],
        free_quality_mean_gate=curriculum["free_quality_mean"],
        max_grip_bad_frame_rate=curriculum[
            "max_grip_bad_frame_rate"],
        max_grip_bad_streak_frames=curriculum[
            "max_grip_bad_streak_frames"],
        tip_ready_success_gate=curriculum["ready_success_rate"],
        release_recall_gate=curriculum["release_recall"],
        false_positive_rate_by_stage=dict(false_positive_rates),
        failure_rate_by_stage=dict(failure_rates),
        timing_tolerances_ms=tuple(curriculum["timing_tolerances_ms"]),
        s2_profiles=tuple(curriculum["s2_profiles"]),
        s2_rollback_windows=curriculum["s2_rollback_windows"],
        s2_rollback_cooldown_iterations=curriculum[
            "s2_rollback_cooldown_iterations"],
        s2_profile_adaptation_iterations=curriculum[
            "s2_profile_adaptation_iterations"],
        s2_rollback_timing_pass_rate=curriculum[
            "s2_rollback_timing_pass_rate"],
        s2_rollback_completion_rate=curriculum[
            "s2_rollback_completion_rate"],
        s2_rollback_traversal_rate=curriculum[
            "s2_rollback_traversal_rate"],
        s2_rollback_direction_rate=curriculum[
            "s2_rollback_direction_rate"],
        s2_rollback_false_positive_rate=curriculum[
            "s2_rollback_false_positive_rate"],
        s2_endpoint_recovery_windows=curriculum[
            "s2_endpoint_recovery_windows"],
        s2_endpoint_recovery_trigger_rate=curriculum[
            "s2_endpoint_recovery_trigger_rate"],
        s2_endpoint_focus_fraction=curriculum[
            "s2_endpoint_focus_fraction"],
        tempo_lambdas=tuple(curriculum["tempo_lambdas"]),
        s3_episode_event_counts=tuple(
            curriculum["s3_episode_event_counts"]),
        s3_tempo_gates=tuple(curriculum["s3_tempo_gates"]),
        s3_uniform_curriculum_evidence_only=curriculum[
            "s3_uniform_curriculum_evidence_only"],
        s3_stalled_original_tempo_recovery=curriculum[
            "s3_stalled_original_tempo_recovery"],
        s3_original_tempo_retention_drop_f1=curriculum[
            "s3_original_tempo_retention_drop_f1"],
        s3_original_tempo_holdout_max_age_iterations=curriculum[
            "s3_original_tempo_holdout_max_age_iterations"],
        strum_spans=tuple(curriculum["strum_spans"]),
        timed_f1_by_level=tuple(curriculum["timed_f1_by_level"]),
        song_f1_gate=curriculum["zone_f1"],
        zone_success_gate=curriculum["zone_success_rate"],
        strum_completion_gate=curriculum["strum_completion_rate"],
        strum_traversal_gate=curriculum["strum_traversal_recall"],
        strum_order_gate=curriculum["strum_order_accuracy"],
        strum_direction_gate_by_stage=dict(direction_rates),
        recovery_completion_gate=curriculum["recovery_completion_rate"],
        full_recovery_completion_gate=curriculum[
            "full_recovery_completion_rate"],
        handoff_recovery_completion_gate=curriculum[
            "handoff_recovery_completion_rate"],
        recovery_reset_rate_by_stage=dict(recovery_reset_rates),
        blocked_crossing_rate_by_stage=dict(blocked_crossing_rates),
        strum_timing_rms_gate_ms=curriculum["strum_timing_rms_ms"],
        strum_duration_mae_gate_ms=curriculum[
            "strum_sweep_duration_mae_ms"],
    )
    return StrikeCurriculum(result, song_has_strum=song_has_strum)


def validate_strike_goal_for_training(
        goal_path, config: Mapping[str, object], *, require_song: bool):
    """Fail before GPU allocation if the selected training mode is impossible."""
    from tab2body.env.strike_goals import StrikeGoalSequence

    if not isinstance(require_song, bool):
        raise TypeError("require_song must be bool")
    build_strike_curriculum(config, 1)
    curriculum_config = _closed_mapping(
        "strike curriculum config", config["curriculum"],
        _CURRICULUM_KEYS)
    raw_std_floor = curriculum_config["s2_endpoint_proximal_std_floor"]
    if (isinstance(raw_std_floor, bool)
            or not isinstance(raw_std_floor, (int, float))
            or not math.isfinite(float(raw_std_floor))
            or not 0.0 < float(raw_std_floor) <= 1.0):
        raise ValueError(
            "s2_endpoint_proximal_std_floor must be finite in (0, 1]")
    floor_profiles = curriculum_config["s2_endpoint_std_floor_profiles"]
    profile_names = tuple(
        str(profile["name"])
        for profile in curriculum_config["s2_profiles"])
    if (not isinstance(floor_profiles, (tuple, list))
            or not floor_profiles
            or not all(isinstance(name, str) and name
                       for name in floor_profiles)
            or len(set(floor_profiles)) != len(floor_profiles)
            or not set(floor_profiles).issubset(profile_names)):
        raise ValueError(
            "s2_endpoint_std_floor_profiles must be unique S2 profile names")
    detector = config["detector"]
    trajectory = config["trajectory"]
    tolerances = config["curriculum"]["timing_tolerances_ms"]
    s2_tolerances = tuple(
        int(profile["tolerance_ms"])
        for profile in config["curriculum"]["s2_profiles"])
    goals = StrikeGoalSequence(
        Path(goal_path).resolve(),
        device="cpu",
        rearm_min_frames=detector["rearm_min_frames"],
        follow_through_min_frames=trajectory["follow_through_min_frames"],
        initial_timing_tolerance_ms=tolerances[0])
    if goals.validation_metadata["schema"] != "tab2body.strike_plan.v4":
        raise ValueError(
            "strike training requires compiled strike_plan.json; keep the raw "
            "[time, frame, string] input in strike_training.json and run "
            "tools/build_strike_plan.py")
    goals.require_supported_gestures()
    strum_mask = goals.gesture == 1
    song_has_strum = bool(strum_mask.any().item())
    maximum_strum_span = (
        int(goals.traversal_mask[strum_mask].sum(dim=1).max().item())
        if song_has_strum else 0)
    if require_song:
        if song_has_strum:
            required_strum_span = max(config["curriculum"]["strum_spans"])
            if maximum_strum_span < required_strum_span:
                raise ValueError(
                    "strike goal cannot satisfy the strum curriculum: maximum "
                    f"span={maximum_strum_span}, required={required_strum_span}")
        goals.require_feasible_original_tempo_transitions()
    safety = config["safety"]
    penetration_threshold = safety["penetration_threshold_m"]
    if (isinstance(penetration_threshold, bool)
            or not isinstance(penetration_threshold, (int, float))
            or not math.isfinite(float(penetration_threshold))
            or float(penetration_threshold) <= 0.0):
        raise ValueError(
            "safety.penetration_threshold_m must be finite and positive")
    penetration_frames = safety["penetration_frames"]
    if (isinstance(penetration_frames, bool)
            or not isinstance(penetration_frames, int)
            or penetration_frames < 1):
        raise ValueError(
            "safety.penetration_frames must be a positive integer")
    if not isinstance(safety["penetration_termination"], bool):
        raise TypeError("safety.penetration_termination must be bool")
    if trajectory["crossing_depth_m"] < detector["min_depth_m"]:
        raise ValueError(
            "trajectory.crossing_depth_m must reach detector.min_depth_m")
    for name in ("clearance_height_m", "clearance_distance_m"):
        value = trajectory[name]
        if (isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                or float(value) <= 0.0):
            raise ValueError(
                f"trajectory.{name} must be finite and positive")
    if trajectory["clearance_height_m"] < detector["rearm_distance_m"]:
        raise ValueError(
            "trajectory.clearance_height_m must reach detector rearm distance")
    if (math.hypot(
            trajectory["exit_across_offset_m"],
            trajectory["crossing_depth_m"])
            < detector["rearm_distance_m"]):
        raise ValueError(
            "trajectory exit point cannot reach detector rearm distance")
    if (trajectory["ready_hold_frames"] + 1
            > math.floor(TIMED_PRACTICE_MIN_TIME_S * goals.fps)):
        raise ValueError(
            "READY hold cannot finish before the earliest A3 target")
    episode = config["episode"]
    shared_stages = (
        (A1_TIP_READY, None),
        (A2_SINGLE_CROSSING, None),
        (A3_TIMED_SINGLE, tolerances[0]),
    )
    strum_stages = (
        (A4_STRUM_CONTEXT_RECOVERY, None),
        (S0_TWO_STRING_STRUM, None),
        (S1_STRUM_SPAN, None),
        (S2_TIMED_STRUM, s2_tolerances[0]),
    )
    stages = shared_stages + (strum_stages if song_has_strum else ())
    if require_song:
        stages += ((S3_SONG_INTEGRATION, s2_tolerances[-1]),)
    for stage, tolerance in stages:
        minimum = minimum_strike_stage_horizon(
            stage,
            goals.easy_time.detach().cpu().tolist(),
            sim_hz=goals.fps,
            ready_hold_frames=trajectory["ready_hold_frames"],
            recovery_frames=trajectory["recovery_frames"],
            rearm_min_frames=detector["rearm_min_frames"],
            timed_lead_frames=episode["timed_lead_frames"],
            song_events_per_episode=episode["song_events_per_episode"],
            timing_tolerance_ms=tolerance)
        if episode[stage] < minimum:
            raise ValueError(
                "strike episode horizon is infeasible: "
                f"{stage}={episode[stage]} (requires >= {minimum})")
    if require_song:
        goals.require_nonoverlapping_match_windows(s2_tolerances[-1])
        final_approach_lead_s = float(
            config["curriculum"]["s2_profiles"][-1]["approach_lead_s"])
        if (final_approach_lead_s + s2_tolerances[-1] / 1000.0
                < 1.0 / goals.fps):
            raise ValueError(
                "S3 approach lead and timing tolerance must leave at least "
                "one APPROACH action")
    validation = dict(goals.validation_metadata)
    active_stages = strike_curriculum_stages(song_has_strum)
    validation.update({
        "song_has_strum": song_has_strum,
        "maximum_strum_span": maximum_strum_span,
        "curriculum_route": (
            "pick_and_strum" if song_has_strum else "pick_only"),
        "curriculum_active_stages": list(active_stages),
    })
    return validation


def _set_fixed_curriculum(curriculum, stage, tolerance_ms=None):
    from tab2body.strike_contract import (
        A3_TIMED_SINGLE,
        S2_TIMED_STRUM,
        S3_SONG_INTEGRATION,
        STRIKE_STAGES,
    )

    if stage not in STRIKE_STAGES:
        raise ValueError(f"unknown fixed Strike stage: {stage!r}")
    if stage not in curriculum.active_stages:
        raise ValueError(
            f"{stage} is unavailable for a pick-only song curriculum")
    curriculum.stage = stage
    curriculum.stage_iteration = 0
    curriculum.total_iteration = 0
    curriculum.stalled = False
    curriculum.promotion_streak = 0
    curriculum.rollback_streak = 0
    curriculum.rollback_cooldown = 0
    curriculum.s2_adaptation_remaining = 0
    curriculum._reset_s2_endpoint_recovery()
    curriculum.span_level = 0
    curriculum.tempo_level = 0
    curriculum.complete = False
    schedule = curriculum.config.timing_tolerances_ms
    if stage == S3_SONG_INTEGRATION:
        curriculum.timing_level = len(schedule) - 1
        curriculum.s2_profile_index = len(curriculum.config.s2_profiles) - 1
        curriculum.tempo_level = len(curriculum.config.tempo_lambdas) - 1
    elif stage in (A3_TIMED_SINGLE, S2_TIMED_STRUM):
        stage_schedule = (
            tuple(int(profile["tolerance_ms"])
                  for profile in curriculum.config.s2_profiles)
            if stage == S2_TIMED_STRUM else schedule)
        if tolerance_ms is None:
            desired = stage_schedule[0]
        else:
            if isinstance(tolerance_ms, bool):
                raise ValueError("fixed timing tolerance must be numeric")
            desired_value = float(tolerance_ms)
            if not math.isfinite(desired_value):
                raise ValueError("fixed timing tolerance must be finite")
            matches = [
                value for value in stage_schedule
                if abs(desired_value - value) <= 1e-6]
            if not matches:
                raise ValueError(
                    f"timed-stage tolerance must be one of {stage_schedule}, "
                    f"got {tolerance_ms}")
            desired = matches[0]
        if desired not in stage_schedule:
            raise ValueError(
                f"timed-stage tolerance must be one of {stage_schedule}, got {desired}")
        if stage == S2_TIMED_STRUM:
            curriculum.s2_profile_index = stage_schedule.index(desired)
        else:
            curriculum.timing_level = schedule.index(desired)
    else:
        curriculum.timing_level = 0
        if tolerance_ms is not None:
            raise ValueError(
                "--timing-tolerance-ms applies only to A3, S2, or S3")
    if stage == S3_SONG_INTEGRATION and tolerance_ms is not None:
        if isinstance(tolerance_ms, bool):
            raise ValueError("fixed timing tolerance must be numeric")
        value = float(tolerance_ms)
        if (not math.isfinite(value)
                or abs(value - schedule[-1]) > 1e-6):
            raise ValueError(
                f"S3 keeps the final {schedule[-1]} ms tolerance")


class StrikeCurriculumRuntime:
    """Own the checkpoint-relevant curriculum lifecycle around PPO updates."""

    def __init__(self, curriculum, *, fixed_stage=None, tolerance_ms=None):
        self.curriculum = curriculum
        self.fixed_stage = fixed_stage
        if fixed_stage is not None:
            _set_fixed_curriculum(curriculum, fixed_stage, tolerance_ms)

    def restore(self, training_context):
        if self.fixed_stage is None:
            self.curriculum.load_context(training_context)

    def apply(self, env):
        state = self.curriculum.apply(env)
        reset_observation = state.pop("_reset_observation", None)
        return state, reset_observation

    def record_original_tempo_evaluation(self, iteration, metrics,
                                         case_summary=None, case_protocol=None):
        """Store the latest full-song holdout without changing the env."""
        return self.curriculum.record_original_tempo_evaluation(
            iteration, metrics, case_summary, case_protocol)

    def after_iteration(self, stats, env):
        previous_stage = self.curriculum.stage
        previous_tolerance = self.curriculum.timing_tolerance_ms
        previous_tempo_lambda = self.curriculum.tempo_lambda
        previous_strum_span = self.curriculum.strum_span
        previous_s2_profile = self.curriculum.s2_profile_name
        previous_endpoint_recovery = (
            self.curriculum.s2_endpoint_recovery_active)
        previous_focus_direction = self.curriculum.s2_focus_direction
        previous_focus_fraction = self.curriculum.s2_focus_fraction
        previous_rollback_count = self.curriculum.rollback_count
        previous_complete = self.curriculum.complete
        previous_stalled = self.curriculum.stalled
        previous_rehearsal = (
            self.curriculum.s3_original_tempo_rehearsal_active)
        if self.fixed_stage is None:
            state = self.curriculum.after_iteration(stats)
        else:
            self.curriculum.total_iteration += 1
            self.curriculum.stage_iteration += 1
            state = self.curriculum.state()
        applied, reset_observation = self.apply(env)
        state.update(applied)
        changed = (
            state["curriculum_stage"] != previous_stage
            or state["curriculum_timing_tolerance_ms"] != previous_tolerance
            or state["curriculum_tempo_lambda"] != previous_tempo_lambda
            or state["curriculum_strum_span"] != previous_strum_span
            or state["curriculum_s2_profile_name"] != previous_s2_profile
            or state["curriculum_s2_endpoint_recovery_active"]
            != previous_endpoint_recovery
            or state["curriculum_s2_focus_direction"]
            != previous_focus_direction
            or state["curriculum_s2_focus_fraction"]
            != previous_focus_fraction
            or state["curriculum_s2_rollback_count"] != previous_rollback_count
            or state["curriculum_complete"] != previous_complete
            or state["curriculum_stalled"] != previous_stalled
            or state["curriculum_s3_original_tempo_rehearsal_active"]
            != previous_rehearsal)
        transition = None
        if changed:
            transition = {
                "from": previous_stage,
                "to": state["curriculum_stage"],
                "from_tolerance_ms": previous_tolerance,
                "to_tolerance_ms": state[
                    "curriculum_timing_tolerance_ms"],
                "from_tempo_lambda": previous_tempo_lambda,
                "to_tempo_lambda": state["curriculum_tempo_lambda"],
                "from_strum_span": previous_strum_span,
                "to_strum_span": state["curriculum_strum_span"],
                "from_s2_profile": previous_s2_profile,
                "to_s2_profile": state["curriculum_s2_profile_name"],
                "from_s2_endpoint_recovery_active": (
                    previous_endpoint_recovery),
                "to_s2_endpoint_recovery_active": state[
                    "curriculum_s2_endpoint_recovery_active"],
                "from_s2_focus_direction": previous_focus_direction,
                "to_s2_focus_direction": state[
                    "curriculum_s2_focus_direction"],
                "from_s2_focus_fraction": previous_focus_fraction,
                "to_s2_focus_fraction": state[
                    "curriculum_s2_focus_fraction"],
                "from_rollback_count": previous_rollback_count,
                "to_rollback_count": state[
                    "curriculum_s2_rollback_count"],
                "from_complete": previous_complete,
                "to_complete": state["curriculum_complete"],
                "from_stalled": previous_stalled,
                "to_stalled": state["curriculum_stalled"],
                "from_s3_original_tempo_rehearsal": previous_rehearsal,
                "to_s3_original_tempo_rehearsal": state[
                    "curriculum_s3_original_tempo_rehearsal_active"],
            }
        return state, reset_observation, transition


def validate_strike_training_alignment(env, ppo_config):
    """Keep gamma-correct task shaping aligned with the PPO discount."""
    reach_discount = getattr(
        getattr(env, "reward_fn", None), "reach_discount", None)
    ppo_discount = getattr(ppo_config, "gamma", None)
    try:
        reach_discount = float(reach_discount)
        ppo_discount = float(ppo_discount)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "Strike reward/PPO discount alignment is unavailable") from exc
    if (not math.isfinite(reach_discount)
            or not math.isfinite(ppo_discount)
            or abs(reach_discount - ppo_discount) > 1e-12):
        raise ValueError(
            "reward.reach_discount must exactly match ppo.gamma")


__all__ = [
    "StrikeCurriculumRuntime",
    "build_strike_curriculum",
    "validate_strike_goal_for_training",
    "validate_strike_training_alignment",
]
