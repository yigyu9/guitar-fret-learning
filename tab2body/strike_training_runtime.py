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
    A1_TIP_READY,
    A2_FREE_CROSSING,
    A3_TIMED_CROSSING,
    A4_ZONE_CONTROL,
    TIMED_PRACTICE_MIN_TIME_S,
    minimum_strike_stage_horizon,
)


_CURRICULUM_KEYS = frozenset((
    "min_iterations",
    "max_iterations",
    "promotion_windows",
    "terminal_evidence_fraction",
    "timing_tolerances_ms",
    "tempo_lambdas",
    "grip_success_rate",
    "ready_success_rate",
    "release_recall",
    "max_wrong_rate",
    "timed_f1_by_level",
    "zone_f1",
    "zone_success_rate",
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


def build_strike_curriculum(config: Mapping[str, object], num_envs: int):
    """Build the closed curriculum object from the public Strike config."""
    from tab2body.learning.strike_curriculum import (
        StrikeCurriculum,
        StrikeCurriculumConfig,
    )

    if isinstance(num_envs, bool) or not isinstance(num_envs, int) or num_envs < 1:
        raise ValueError("num_envs must be a positive integer")
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
    result = StrikeCurriculumConfig(
        grip_min_iterations=minimum["A0_PICK_GRIP"],
        grip_max_iterations=maximum["A0_PICK_GRIP"],
        ready_min_iterations=minimum["A1_TIP_READY"],
        ready_max_iterations=maximum["A1_TIP_READY"],
        crossing_min_iterations=minimum["A2_FREE_CROSSING"],
        crossing_max_iterations=maximum["A2_FREE_CROSSING"],
        timed_min_iterations=minimum["A3_TIMED_CROSSING"],
        timed_max_iterations=maximum["A3_TIMED_CROSSING"],
        zone_min_iterations=minimum["A4_ZONE_CONTROL"],
        zone_max_iterations=maximum["A4_ZONE_CONTROL"],
        promotion_windows=curriculum["promotion_windows"],
        terminal_evidence_episodes=max(
            1, int(math.ceil(num_envs * evidence_fraction))),
        grip_success_gate=curriculum["grip_success_rate"],
        tip_ready_success_gate=curriculum["ready_success_rate"],
        release_recall_gate=curriculum["release_recall"],
        false_positive_rate_gate=curriculum["max_wrong_rate"],
        strike_f1_gate=curriculum["timed_f1_by_level"][-1],
        timing_tolerances_ms=tuple(curriculum["timing_tolerances_ms"]),
        tempo_lambdas=tuple(curriculum["tempo_lambdas"]),
        timed_f1_by_level=tuple(curriculum["timed_f1_by_level"]),
        zone_f1_gate=curriculum["zone_f1"],
        zone_success_gate=curriculum["zone_success_rate"],
    )
    return StrikeCurriculum(result)


def validate_strike_goal_for_training(
        goal_path, config: Mapping[str, object], *, require_a4: bool):
    """Fail before GPU allocation if the selected training mode is impossible."""
    from tab2body.env.strike_goals import StrikeGoalSequence

    if not isinstance(require_a4, bool):
        raise TypeError("require_a4 must be bool")
    detector = config["detector"]
    trajectory = config["trajectory"]
    tolerances = config["curriculum"]["timing_tolerances_ms"]
    goals = StrikeGoalSequence(
        Path(goal_path).resolve(),
        device="cpu",
        rearm_min_frames=detector["rearm_min_frames"],
        follow_through_min_frames=trajectory["follow_through_min_frames"],
        initial_timing_tolerance_ms=tolerances[0])
    goals.require_supported_gestures()
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
    stages = (
        (A1_TIP_READY, None),
        (A2_FREE_CROSSING, None),
        (A3_TIMED_CROSSING, tolerances[0]),
    )
    if require_a4:
        stages += ((A4_ZONE_CONTROL, tolerances[-1]),)
    for stage, tolerance in stages:
        minimum = minimum_strike_stage_horizon(
            stage,
            goals.easy_time.detach().cpu().tolist(),
            sim_hz=goals.fps,
            ready_hold_frames=trajectory["ready_hold_frames"],
            recovery_frames=trajectory["recovery_frames"],
            rearm_min_frames=detector["rearm_min_frames"],
            timed_lead_frames=episode["timed_lead_frames"],
            a4_events_per_episode=episode["a4_events_per_episode"],
            timing_tolerance_ms=tolerance)
        if episode[stage] < minimum:
            raise ValueError(
                "strike episode horizon is infeasible: "
                f"{stage}={episode[stage]} (requires >= {minimum})")
    if require_a4:
        goals.require_nonoverlapping_match_windows(tolerances[-1])
        if (trajectory["approach_lead_s"] + tolerances[-1] / 1000.0
                < 1.0 / goals.fps):
            raise ValueError(
                "A4 approach lead and timing tolerance must leave at least "
                "one APPROACH action")
    return goals.validation_metadata


def _set_fixed_curriculum(curriculum, stage, tolerance_ms=None):
    from tab2body.strike_contract import (
        A3_TIMED_CROSSING,
        A4_ZONE_CONTROL,
        STRIKE_STAGES,
    )

    if stage not in STRIKE_STAGES:
        raise ValueError(f"unknown fixed Strike stage: {stage!r}")
    curriculum.stage = stage
    curriculum.stage_iteration = 0
    curriculum.total_iteration = 0
    curriculum.stalled = False
    curriculum.promotion_streak = 0
    curriculum.timing_streak = 0
    curriculum.tempo_level = 0
    curriculum.complete = False
    curriculum._reset_terminal_evidence()
    schedule = curriculum.config.timing_tolerances_ms
    if stage == A4_ZONE_CONTROL:
        curriculum.timing_level = len(schedule) - 1
        curriculum.tempo_level = len(curriculum.config.tempo_lambdas) - 1
    elif stage == A3_TIMED_CROSSING:
        if tolerance_ms is None:
            desired = schedule[0]
        else:
            if isinstance(tolerance_ms, bool):
                raise ValueError("fixed timing tolerance must be numeric")
            desired_value = float(tolerance_ms)
            if not math.isfinite(desired_value):
                raise ValueError("fixed timing tolerance must be finite")
            matches = [
                value for value in schedule
                if abs(desired_value - value) <= 1e-6]
            if not matches:
                raise ValueError(
                    f"A3 tolerance must be one of {schedule}, "
                    f"got {tolerance_ms}")
            desired = matches[0]
        if desired not in schedule:
            raise ValueError(
                f"A3 tolerance must be one of {schedule}, got {desired}")
        curriculum.timing_level = schedule.index(desired)
    else:
        curriculum.timing_level = 0
        if tolerance_ms is not None:
            raise ValueError(
                "--timing-tolerance-ms applies only to A3/A4")
    if stage == A4_ZONE_CONTROL and tolerance_ms is not None:
        if isinstance(tolerance_ms, bool):
            raise ValueError("fixed timing tolerance must be numeric")
        value = float(tolerance_ms)
        if (not math.isfinite(value)
                or abs(value - schedule[-1]) > 1e-6):
            raise ValueError(
                f"A4 keeps the final {schedule[-1]} ms tolerance")


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

    def after_iteration(self, stats, env):
        previous_stage = self.curriculum.stage
        previous_tolerance = self.curriculum.timing_tolerance_ms
        previous_tempo_lambda = self.curriculum.tempo_lambda
        previous_complete = self.curriculum.complete
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
            or state["curriculum_complete"] != previous_complete)
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
                "from_complete": previous_complete,
                "to_complete": state["curriculum_complete"],
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
