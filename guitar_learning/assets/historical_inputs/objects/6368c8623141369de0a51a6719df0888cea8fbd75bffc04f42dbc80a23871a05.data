"""Isaac Gym task for learning a natural right-hand virtual-pick strike.

The public music input remains the minimal ``[time, frame, string]`` event
timeline.  Everything else in this task is derived from that input and the
live guitar geometry:

* ``RH:pick`` is a geometry-less point rigidly attached to the index finger.
* the six strings are fixed finite segments defined by guitar marker bodies;
* a strike is a debounced RELEASE event after a sufficiently deep, sufficiently
  fast swept-point crossing;
* a deterministic phrase planner derives down/up before RL execution;
* the policy observes and executes that fixed direction without changing it.

The observation and 30-DOF action layouts stay unchanged throughout the eight
acquisition stages.  Stage masks and rewards change, never tensor shapes.
"""
from __future__ import annotations

from collections.abc import Mapping
import math
from numbers import Real
from typing import Tuple

import torch
from isaacgym import gymtorch

from ..base import GuitarEnvBase, quat_rotate_inverse
from ..collision import (
    DISABLED_COLLISION_FILTER,
    GUITAR_COLLISION_FILTER,
    HUMANOID_COLLISION_FILTER,
    THUMB_SUPPORT_PROXY_BODY,
)
from ..rewards.strike import (
    PickGripReference,
    STAGES,
    StrikeReward,
    constrain_pick_grip_actions,
    strike_reach_potential_delta,
    strike_terminal_potential_delta,
)
from ..strike_events import (
    strike_balanced_practice_direction,
    strike_focused_practice_direction,
    strike_early_timing_cost,
    strike_premature_release,
    strike_rational_timing_quality,
    strike_song_continuing_phase,
    strike_clean_recovery_progress,
    strike_clearance_waypoint_state,
    strike_recovery_clearance_target,
    strike_dual_recovery_plan,
    strike_dual_recovery_progress,
    strike_dual_recovery_to_approach,
    strike_directional_strum_outcomes,
    strike_event_outcome_masks,
    strike_completed_recovery_frames,
    strike_limit_traversal_span,
    strike_motion_target_context,
    strike_next_traversal_string,
    strike_physical_target_candidate,
    strike_ordered_release_progress,
    strike_ready_episode_resolution,
    strike_ready_latch,
    strike_recovery_incomplete_timeout,
    strike_release_recovery_context,
    strike_resolved_episode_done,
    strike_timing_gate,
    strike_timed_approach_open,
    strike_traversal_timing,
    strike_strum_terminal_progress,
    strike_uniform_traversal_offsets,
)
from ..strike_detector import (
    DETECTOR_ARMED,
    DIRECTION_DOWN,
    DIRECTION_UP,
    PickStrikeDetector,
    strike_lane_gate,
)
from ..strike_goals import N_GUITAR_STRINGS, StrikeGoalSequence
from ..safety import GuitarPenetrationMonitor
from ..metrics import (
    bounded_failure_sampling_probabilities,
    event_predecessor_rehearsal_scores,
    event_mask_window_scores,
    normalized_joint_limit_usage,
    update_event_failure_statistics,
    update_wrong_crossing_termination,
)
try:
    from ...strike_contract import (
        A0_PICK_GRIP,
        A1_TIP_READY,
        A2_SINGLE_CROSSING,
        A3_TIMED_SINGLE,
        A4_STRUM_CONTEXT_RECOVERY,
        S0_TWO_STRING_STRUM,
        S1_STRUM_SPAN,
        S2_TIMED_STRUM,
        S3_SONG_INTEGRATION,
        SINGLE_PRACTICE_STAGES,
        PRACTICE_DIRECTION_STAGES,
        STRUM_STAGES,
        STRUM_ONLY_STAGES,
        TIMED_STAGES,
        ZONE_STAGES,
        SONG_TIMELINE_STAGES,
        TIMED_PRACTICE_MAX_TIME_S,
        TIMED_PRACTICE_MIN_TIME_S,
        minimum_strike_stage_horizon,
    )
    from ...strike_metrics import STRIKE_EPISODE_METRIC_KEYS
    from ...strike_v2_contract import (
        STRIKE_V1_OBSERVATION_CONTRACT,
        STRIKE_V2_BLOCK_SLICES,
        STRIKE_V2_OBSERVATION_CONTRACT,
        STRIKE_V2_OBSERVATION_DIM,
        pack_strike_v2_blocks,
        strike_v2_block_manifest,
    )
except (ImportError, ValueError):
    # Keep the historical ``env.tasks`` import path working for legacy GPU
    # regression entry points.
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
        SINGLE_PRACTICE_STAGES,
        PRACTICE_DIRECTION_STAGES,
        STRUM_STAGES,
        STRUM_ONLY_STAGES,
        TIMED_STAGES,
        ZONE_STAGES,
        SONG_TIMELINE_STAGES,
        TIMED_PRACTICE_MAX_TIME_S,
        TIMED_PRACTICE_MIN_TIME_S,
        minimum_strike_stage_horizon,
    )
    from tab2body.strike_metrics import STRIKE_EPISODE_METRIC_KEYS
    from tab2body.strike_v2_contract import (
        STRIKE_V1_OBSERVATION_CONTRACT,
        STRIKE_V2_BLOCK_SLICES,
        STRIKE_V2_OBSERVATION_CONTRACT,
        STRIKE_V2_OBSERVATION_DIM,
        pack_strike_v2_blocks,
        strike_v2_block_manifest,
    )


STRIKE_CONTROL_PREFIXES = (
    "R_Shoulder", "R_Elbow", "R_Wrist", "RH:",
)
STRIKE_OBS_BODIES = (
    "R_Wrist", "RH:palm", "RH:pick",
)
PHASE_READY = 0
PHASE_APPROACH = 1
PHASE_RELEASE_RECOVER = 2
N_PHASES = 3

_AXES = ("x", "y", "z")

_ZONE_CONFIG_KEYS = (
    "allowed_y_min_m", "allowed_y_max_m",
    "preferred_y_min_m", "preferred_y_max_m", "phrase_lane_y_m",
    "lane_core_half_width_m", "lane_allowed_half_width_m",
)
_TRAJECTORY_CONFIG_KEYS = (
    "ready_across_offset_m", "entry_across_offset_m",
    "exit_across_offset_m", "ready_height_m", "crossing_depth_m",
    "ready_distance_m", "entry_distance_m", "ready_hold_frames",
    "recovery_frames", "follow_through_min_frames", "approach_lead_s",
    "clearance_height_m", "clearance_distance_m",
)
_DETECTOR_CONFIG_KEYS = (
    "min_depth_m", "min_across_speed_m_s", "parallel_epsilon",
    "min_displacement_m", "rearm_distance_m", "rearm_min_frames",
)
_SAFETY_CONFIG_KEYS = (
    "penetration_threshold_m", "penetration_frames",
    "penetration_termination",
)
_WRONG_CROSSING_TERMINATION_KEYS = (
    "enabled", "minimum_tempo_lambda", "minimum_resolved_events",
    "max_count", "max_rate", "consecutive_event_limit",
    "terminate_on_rate",
)
_JOINT_LIMIT_CONFIG_KEYS = (
    "diagnostic_fraction", "soft_penalty_start_fraction",
    "soft_penalty_weight",
)
_GRIP_CONTROL_CONFIG_KEYS = (
    "pinch_residual_rad", "free_residual_rad", "bad_quality_threshold",
)
_EPISODE_CONFIG_KEYS = (
    *STAGES, "song_events_per_episode", "timed_lead_frames",
)
_CURRICULUM_CONFIG_KEYS = (
    "min_iterations", "max_iterations", "promotion_windows",
    "terminal_evidence_fraction", "timing_tolerances_ms",
    "s2_profiles", "s2_rollback_windows",
    "s2_rollback_cooldown_iterations",
    "s2_profile_adaptation_iterations",
    "s2_rollback_timing_pass_rate", "s2_rollback_completion_rate",
    "s2_rollback_traversal_rate", "s2_rollback_direction_rate",
    "s2_rollback_false_positive_rate",
    "s2_endpoint_recovery_windows",
    "s2_endpoint_recovery_trigger_rate",
    "s2_endpoint_focus_fraction",
    "s2_endpoint_proximal_std_floor",
    "s2_endpoint_std_floor_profiles",
    "tempo_lambdas", "s3_episode_event_counts", "s3_tempo_gates",
    "stalled_hard_sample_fraction", "stalled_failure_score_decay",
    "stalled_hard_rehearsal_events",
    "stalled_failure_prior_exposure",
    "stalled_hard_window_probability_cap",
    "s3_upstroke_sample_fraction",
    "s3_upstroke_window_probability_cap",
    "s3_uniform_curriculum_evidence_only",
    "s3_stalled_original_tempo_recovery",
    "s3_original_tempo_retention_drop_f1",
    "s3_original_tempo_holdout_max_age_iterations",
    "strum_spans", "grip_success_rate",
    "grip_quality_mean", "grip_quality_p05",
    "pinch_quality_mean", "free_quality_mean",
    "max_grip_bad_frame_rate", "max_grip_bad_streak_frames",
    "ready_success_rate", "release_recall", "max_wrong_rate_by_stage",
    "max_failure_rate_by_stage",
    "timed_f1_by_level", "zone_f1", "zone_success_rate",
    "strum_completion_rate", "strum_traversal_recall",
    "strum_order_accuracy", "strum_direction_accuracy_by_stage",
    "recovery_completion_rate", "full_recovery_completion_rate",
    "handoff_recovery_completion_rate",
    "max_recovery_reset_rate_by_stage",
    "max_blocked_crossing_rate_by_stage", "strum_timing_rms_ms",
    "strum_sweep_duration_mae_ms",
)


class RightGuitarPenetrationMonitor(GuitarPenetrationMonitor):
    """Right-arm/hand variant of the analytical guitar-solid monitor."""

    CHAINS = (
        ("R_Shoulder", "R_Elbow", "R_Wrist", "RH:palm"),
        ("RH:palm", "RH:thumb1", "RH:thumb2", "RH:thumb3", "RH:thumb_top"),
        ("RH:palm", "RH:index1", "RH:index2", "RH:index3", "RH:index_top"),
        ("RH:palm", "RH:middle1", "RH:middle2", "RH:middle3", "RH:middle_top"),
        ("RH:palm", "RH:ring1", "RH:ring2", "RH:ring3", "RH:ring_top"),
        ("RH:palm", "RH:pinky1", "RH:pinky2", "RH:pinky3", "RH:pinky_top"),
    )


def _closed_config(name, value, required_keys):
    if not isinstance(value, Mapping):
        raise TypeError(f"{name} must be a mapping")
    result = dict(value)
    expected = set(required_keys)
    missing = sorted(expected - set(result))
    unknown = sorted(set(result) - expected)
    if missing or unknown:
        details = []
        if missing:
            details.append("missing=" + ",".join(missing))
        if unknown:
            details.append("unknown=" + ",".join(unknown))
        raise ValueError(f"{name} config must be closed ({'; '.join(details)})")
    return result


def _integer_config(name, value, *, minimum):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < minimum:
        relation = "positive" if minimum == 1 else f">= {minimum}"
        raise ValueError(f"{name} must be {relation}")
    return value


def _finite_config(name, value):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _one_hot(index: torch.Tensor, size: int, dtype=torch.float32) -> torch.Tensor:
    result = torch.zeros(
        index.shape[0], size, dtype=dtype, device=index.device)
    valid = (index >= 0) & (index < size)
    if valid.any():
        rows = torch.nonzero(valid).squeeze(-1)
        result[rows, index[rows]] = 1.0
    return result


class StrikeTask(GuitarEnvBase):
    """Nine-stage right-hand single-pick and strum environment."""

    task_name = "strike"
    episode_metric_keys = STRIKE_EPISODE_METRIC_KEYS
    episode_reason_keys = (
        "goal_finished",
        "failure_termination",
        "recovery_incomplete_timeout",
        "early_timeout",
        "nonfinite",
        "velocity_blowup",
        "guitar_penetration_termination",
        "wrong_crossing_termination",
        "wrong_crossing_count_termination",
        "wrong_crossing_rate_termination",
        "wrong_crossing_consecutive_termination",
        "irrecoverable_safety_failure",
        "performance_failure_termination",
    )
    rollout_diagnostic_keys = (
        "grip_quality",
        "grip_pinch_quality",
        "grip_free_quality",
        "grip_success_rate",
        "tip_ready_success_rate",
        "release_recall",
        "false_positive_rate",
        "strike_f1",
        "timing_worst_ms",
        "timing_pass_rate",
        "timing_early_rate",
        "timing_late_rate",
        "premature_release_rate",
        "zone_success_rate",
        "raw_zone_success_rate",
        "raw_zone_mean_quality",
        "tip_target_distance",
        "approach_motion_quality",
        "timing_wait_quality",
        "early_timing_cost",
        "approach_open",
        "time_to_approach_s",
        "approach_lead_s",
        "timing_early_grace_ms",
        "timing_early_penalty_scale_ms",
        "entry_ready",
        "entry_distance_m",
        "tip_speed_m_s",
        "guitar_penetration_depth",
        "guitar_swept_penetration_depth",
        "guitar_penetration",
        "action_saturation_fraction",
        "release_count",
        "blocked_release_count",
        "release_phase_violation",
        "prepared_target_hit",
        "unprepared_target_hit",
        "target_lane_shift_m",
        "strum_order_violation_count",
        "strum_wrong_direction_count",
        "strum_unplanned_crossing_count",
        "strum_duplicate_crossing_count",
        "recovery_progress",
        "recovery_complete_pulse",
        "scheduled_recovery_progress",
        "scheduled_recovery_complete_pulse",
        "recovery_handoff",
        "recovery_same_string_handoff",
        "recovery_path_crossing_count",
        "recovery_clearance_required",
        "recovery_clearance_lifted",
        "recovery_clearance_reached",
        "recovery_required_frames",
        "recovery_available_frames",
        "recovery_reset_count",
        "strum_progress",
        "strum_terminal_progress",
        "strum_terminal_progress_best",
        "strum_exit_distance_m",
        "strum_physical_completion_pulse",
        "strum_final_string_remaining",
        "strum_final_string_miss_at_timeout",
        "strum_remaining_string_count",
        "down_completed_count",
        "up_completed_count",
        "strum_max_strings",
        "strum_timing_rms_ms",
        "strum_sweep_duration_error_ms",
        "target_direction_down",
        "wrong_crossing_rate",
        "wrong_crossing_rate_limit_exceeded",
        "wrong_crossing_count_termination",
        "wrong_crossing_rate_termination",
        "wrong_crossing_consecutive_termination",
        "wrong_crossing_termination",
        "hard_sampled_window",
        "upstroke_sampled_window",
        "s2_focus_sampled",
        "s2_endpoint_recovery_active",
        "failure_score_max",
        "failure_score_mean",
        "failure_exposure_min",
        "failure_exposure_max",
        "hard_window_probability_max",
        "upstroke_window_probability_max",
        "joint_limit_max_usage",
        "joint_limit_near_rate",
        "joint_limit_shoulder_max_usage",
        "joint_limit_elbow_max_usage",
        "joint_limit_wrist_max_usage",
        "joint_limit_hand_max_usage",
        "minimum_effective_gap_s",
        "overlap_window_count",
        "s2_profile_index",
        "s2_zone_gate_active",
        "reward_timing",
        "reward_timing_wait",
        "reward_strum_progress",
        "reward_strum_terminal_progress",
        "reward_strum_physical_completion",
        "penalty_premature_release",
        "penalty_early_timing",
        "penalty_miss",
    )

    def __init__(
            self,
            goal_path,
            grip_reference_path,
            *,
            num_envs=512,
            device="cuda:0",
            headless=True,
            seed=0,
            action_alpha=0.5,
            action_scale=1.0,
            reset_noise=0.0,
            reset_soft_limit_fraction=0.02,
            grip_control,
            zone,
            trajectory,
            detector,
            safety,
            wrong_crossing_termination,
            joint_limits,
            reward,
            episode,
            curriculum,
            failure_termination_penalty=-10.0,
            random_start=True,
            observation_contract=STRIKE_V1_OBSERVATION_CONTRACT):
        if observation_contract not in (
                STRIKE_V1_OBSERVATION_CONTRACT,
                STRIKE_V2_OBSERVATION_CONTRACT):
            raise ValueError(
                "observation_contract must be strike.observation.v1 or "
                "strike.observation.v2")
        self.observation_contract = str(observation_contract)
        grip_control_config = _closed_config(
            "grip_control", grip_control, _GRIP_CONTROL_CONFIG_KEYS)
        zone_config = _closed_config("zone", zone, _ZONE_CONFIG_KEYS)
        trajectory_config = _closed_config(
            "trajectory", trajectory, _TRAJECTORY_CONFIG_KEYS)
        detector_config = _closed_config(
            "detector", detector, _DETECTOR_CONFIG_KEYS)
        safety_config = _closed_config(
            "safety", safety, _SAFETY_CONFIG_KEYS)
        wrong_termination_config = _closed_config(
            "wrong_crossing_termination", wrong_crossing_termination,
            _WRONG_CROSSING_TERMINATION_KEYS)
        joint_limit_config = _closed_config(
            "joint_limits", joint_limits, _JOINT_LIMIT_CONFIG_KEYS)
        episode_config = _closed_config(
            "episode", episode, _EPISODE_CONFIG_KEYS)
        curriculum_config = _closed_config(
            "curriculum", curriculum, _CURRICULUM_CONFIG_KEYS)
        self.grip_pinch_residual_rad = _finite_config(
            "grip_control.pinch_residual_rad",
            grip_control_config["pinch_residual_rad"])
        self.grip_free_residual_rad = _finite_config(
            "grip_control.free_residual_rad",
            grip_control_config["free_residual_rad"])
        self.grip_bad_quality_threshold = _finite_config(
            "grip_control.bad_quality_threshold",
            grip_control_config["bad_quality_threshold"])
        if (self.grip_pinch_residual_rad <= 0.0
                or self.grip_free_residual_rad <= 0.0
                or self.grip_pinch_residual_rad >= self.grip_free_residual_rad
                or not 0.0 < self.grip_bad_quality_threshold < 1.0):
            raise ValueError("strike grip-control configuration is invalid")
        self.curriculum_grip_gate = _finite_config(
            "curriculum.grip_success_rate",
            curriculum_config["grip_success_rate"])
        self.curriculum_grip_quality_mean_gate = _finite_config(
            "curriculum.grip_quality_mean",
            curriculum_config["grip_quality_mean"])
        self.curriculum_grip_quality_p05_gate = _finite_config(
            "curriculum.grip_quality_p05",
            curriculum_config["grip_quality_p05"])
        self.curriculum_pinch_quality_mean_gate = _finite_config(
            "curriculum.pinch_quality_mean",
            curriculum_config["pinch_quality_mean"])
        self.curriculum_free_quality_mean_gate = _finite_config(
            "curriculum.free_quality_mean",
            curriculum_config["free_quality_mean"])
        self.curriculum_max_grip_bad_frame_rate = _finite_config(
            "curriculum.max_grip_bad_frame_rate",
            curriculum_config["max_grip_bad_frame_rate"])
        self.curriculum_max_grip_bad_streak_frames = _integer_config(
            "curriculum.max_grip_bad_streak_frames",
            curriculum_config["max_grip_bad_streak_frames"], minimum=0)
        self.curriculum_ready_gate = _finite_config(
            "curriculum.ready_success_rate",
            curriculum_config["ready_success_rate"])
        self.curriculum_recall_gate = _finite_config(
            "curriculum.release_recall", curriculum_config["release_recall"])
        wrong_gates = _closed_config(
            "curriculum.max_wrong_rate_by_stage",
            curriculum_config["max_wrong_rate_by_stage"], STAGES)
        self.curriculum_wrong_gates = {
            stage: _finite_config(
                f"curriculum.max_wrong_rate_by_stage[{stage}]",
                wrong_gates[stage])
            for stage in STAGES
        }
        self.curriculum_song_f1_gate = _finite_config(
            "curriculum.zone_f1", curriculum_config["zone_f1"])
        self.curriculum_zone_gate = _finite_config(
            "curriculum.zone_success_rate",
            curriculum_config["zone_success_rate"])
        self.curriculum_strum_completion_gate = _finite_config(
            "curriculum.strum_completion_rate",
            curriculum_config["strum_completion_rate"])
        self.curriculum_strum_traversal_gate = _finite_config(
            "curriculum.strum_traversal_recall",
            curriculum_config["strum_traversal_recall"])
        self.curriculum_strum_order_gate = _finite_config(
            "curriculum.strum_order_accuracy",
            curriculum_config["strum_order_accuracy"])
        direction_gates = _closed_config(
            "curriculum.strum_direction_accuracy_by_stage",
            curriculum_config["strum_direction_accuracy_by_stage"], STAGES)
        self.curriculum_strum_direction_gates = {
            stage: _finite_config(
                f"curriculum.strum_direction_accuracy_by_stage[{stage}]",
                direction_gates[stage])
            for stage in STAGES
        }
        self.curriculum_recovery_completion_gate = _finite_config(
            "curriculum.recovery_completion_rate",
            curriculum_config["recovery_completion_rate"])
        self.curriculum_full_recovery_completion_gate = _finite_config(
            "curriculum.full_recovery_completion_rate",
            curriculum_config["full_recovery_completion_rate"])
        self.curriculum_handoff_recovery_completion_gate = _finite_config(
            "curriculum.handoff_recovery_completion_rate",
            curriculum_config["handoff_recovery_completion_rate"])
        recovery_reset_gates = _closed_config(
            "curriculum.max_recovery_reset_rate_by_stage",
            curriculum_config["max_recovery_reset_rate_by_stage"], STAGES)
        self.curriculum_recovery_reset_gates = {
            stage: _finite_config(
                f"curriculum.max_recovery_reset_rate_by_stage[{stage}]",
                recovery_reset_gates[stage])
            for stage in STAGES
        }
        blocked_crossing_gates = _closed_config(
            "curriculum.max_blocked_crossing_rate_by_stage",
            curriculum_config["max_blocked_crossing_rate_by_stage"], STAGES)
        self.curriculum_blocked_crossing_gates = {
            stage: _finite_config(
                f"curriculum.max_blocked_crossing_rate_by_stage[{stage}]",
                blocked_crossing_gates[stage])
            for stage in STAGES
        }
        rate_gates = (
            self.curriculum_grip_gate,
            self.curriculum_grip_quality_mean_gate,
            self.curriculum_grip_quality_p05_gate,
            self.curriculum_pinch_quality_mean_gate,
            self.curriculum_free_quality_mean_gate,
            self.curriculum_max_grip_bad_frame_rate,
            self.curriculum_ready_gate,
            self.curriculum_recall_gate,
            self.curriculum_recovery_completion_gate,
            self.curriculum_full_recovery_completion_gate,
            self.curriculum_handoff_recovery_completion_gate,
            *self.curriculum_wrong_gates.values(),
            *self.curriculum_strum_direction_gates.values(),
            *self.curriculum_recovery_reset_gates.values(),
            *self.curriculum_blocked_crossing_gates.values(),
        )
        if any(not 0.0 <= value <= 1.0 for value in rate_gates):
            raise ValueError("strike curriculum rate gates must be in [0, 1]")
        self.curriculum_strum_timing_rms_gate_ms = _finite_config(
            "curriculum.strum_timing_rms_ms",
            curriculum_config["strum_timing_rms_ms"])
        self.curriculum_strum_duration_mae_gate_ms = _finite_config(
            "curriculum.strum_sweep_duration_mae_ms",
            curriculum_config["strum_sweep_duration_mae_ms"])
        self.stalled_hard_sample_fraction = _finite_config(
            "curriculum.stalled_hard_sample_fraction",
            curriculum_config["stalled_hard_sample_fraction"])
        self.stalled_hard_rehearsal_events = _integer_config(
            "curriculum.stalled_hard_rehearsal_events",
            curriculum_config["stalled_hard_rehearsal_events"], minimum=2)
        self.stalled_failure_score_decay = _finite_config(
            "curriculum.stalled_failure_score_decay",
            curriculum_config["stalled_failure_score_decay"])
        self.stalled_failure_prior_exposure = _finite_config(
            "curriculum.stalled_failure_prior_exposure",
            curriculum_config["stalled_failure_prior_exposure"])
        self.stalled_hard_window_probability_cap = _finite_config(
            "curriculum.stalled_hard_window_probability_cap",
            curriculum_config["stalled_hard_window_probability_cap"])
        self.s3_upstroke_sample_fraction = _finite_config(
            "curriculum.s3_upstroke_sample_fraction",
            curriculum_config["s3_upstroke_sample_fraction"])
        self.s3_upstroke_window_probability_cap = _finite_config(
            "curriculum.s3_upstroke_window_probability_cap",
            curriculum_config["s3_upstroke_window_probability_cap"])
        self.s3_uniform_curriculum_evidence_only = curriculum_config[
            "s3_uniform_curriculum_evidence_only"]
        if (not 0.0 <= self.stalled_hard_sample_fraction <= 1.0
                or not 0.0 < self.stalled_failure_score_decay <= 1.0
                or self.stalled_failure_prior_exposure < 0.0
                or not 0.0 < self.stalled_hard_window_probability_cap <= 1.0
                or not 0.0 <= self.s3_upstroke_sample_fraction <= 1.0
                or (self.stalled_hard_sample_fraction
                    + self.s3_upstroke_sample_fraction > 0.75)
                or not 0.0 < self.s3_upstroke_window_probability_cap <= 1.0
                or not isinstance(
                    self.s3_uniform_curriculum_evidence_only, bool)):
            raise ValueError(
                "stalled failure-mining configuration is invalid")
        self.curriculum_timing_tolerances = tuple(
            int(value) for value in curriculum_config["timing_tolerances_ms"])
        self.curriculum_timed_f1_gates = tuple(
            float(value) for value in curriculum_config["timed_f1_by_level"])
        raw_s2_profiles = curriculum_config["s2_profiles"]
        if not isinstance(raw_s2_profiles, (tuple, list)) or not raw_s2_profiles:
            raise ValueError("curriculum.s2_profiles must be non-empty")
        self.curriculum_s2_profiles = tuple(dict(value)
                                            for value in raw_s2_profiles)
        self.s2_endpoint_recovery_windows = _integer_config(
            "curriculum.s2_endpoint_recovery_windows",
            curriculum_config["s2_endpoint_recovery_windows"], minimum=1)
        self.s2_endpoint_recovery_trigger_rate = _finite_config(
            "curriculum.s2_endpoint_recovery_trigger_rate",
            curriculum_config["s2_endpoint_recovery_trigger_rate"])
        self.s2_endpoint_focus_fraction_config = _finite_config(
            "curriculum.s2_endpoint_focus_fraction",
            curriculum_config["s2_endpoint_focus_fraction"])
        self.s2_endpoint_proximal_std_floor = _finite_config(
            "curriculum.s2_endpoint_proximal_std_floor",
            curriculum_config["s2_endpoint_proximal_std_floor"])
        raw_floor_profiles = curriculum_config[
            "s2_endpoint_std_floor_profiles"]
        if (not isinstance(raw_floor_profiles, (tuple, list))
                or not raw_floor_profiles
                or not all(
                    isinstance(value, str) and value
                    for value in raw_floor_profiles)
                or len(set(raw_floor_profiles)) != len(raw_floor_profiles)):
            raise ValueError(
                "curriculum.s2_endpoint_std_floor_profiles must be unique names")
        profile_names = {
            str(profile.get("name", ""))
            for profile in self.curriculum_s2_profiles}
        if not set(raw_floor_profiles).issubset(profile_names):
            raise ValueError(
                "endpoint std-floor profiles must exist in s2_profiles")
        self.s2_endpoint_std_floor_profiles = tuple(raw_floor_profiles)
        if (not 0.0 <= self.s2_endpoint_recovery_trigger_rate <= 1.0
                or not 0.5 <= self.s2_endpoint_focus_fraction_config <= 0.7
                or not 0.0 < self.s2_endpoint_proximal_std_floor <= 1.0):
            raise ValueError("S2 endpoint-recovery configuration is invalid")
        if (len(self.curriculum_timing_tolerances)
                != len(self.curriculum_timed_f1_gates)):
            raise ValueError("curriculum timing schedule and F1 gates differ")
        if (self.curriculum_strum_timing_rms_gate_ms <= 0.0
                or self.curriculum_strum_duration_mae_gate_ms <= 0.0):
            raise ValueError("strum microtiming gates must be positive")
        frame_values = {
            name: _integer_config(
                f"trajectory.{name}", trajectory_config[name], minimum=1)
            for name in (
                "ready_hold_frames", "recovery_frames",
                "follow_through_min_frames")
        }
        detector_rearm_min_frames = _integer_config(
            "detector.rearm_min_frames",
            detector_config["rearm_min_frames"], minimum=1)
        penetration_frames = _integer_config(
            "safety.penetration_frames",
            safety_config["penetration_frames"], minimum=1)
        penetration_threshold = _finite_config(
            "safety.penetration_threshold_m",
            safety_config["penetration_threshold_m"])
        penetration_termination = safety_config[
            "penetration_termination"]
        if not isinstance(wrong_termination_config["enabled"], bool):
            raise TypeError("wrong_crossing_termination.enabled must be bool")
        self.wrong_crossing_termination_enabled = (
            wrong_termination_config["enabled"])
        self.wrong_crossing_minimum_tempo = _finite_config(
            "wrong_crossing_termination.minimum_tempo_lambda",
            wrong_termination_config["minimum_tempo_lambda"])
        self.wrong_crossing_minimum_events = _integer_config(
            "wrong_crossing_termination.minimum_resolved_events",
            wrong_termination_config["minimum_resolved_events"], minimum=0)
        self.wrong_crossing_max_count = _integer_config(
            "wrong_crossing_termination.max_count",
            wrong_termination_config["max_count"], minimum=1)
        self.wrong_crossing_max_rate = _finite_config(
            "wrong_crossing_termination.max_rate",
            wrong_termination_config["max_rate"])
        self.wrong_crossing_consecutive_limit = _integer_config(
            "wrong_crossing_termination.consecutive_event_limit",
            wrong_termination_config["consecutive_event_limit"], minimum=1)
        self.wrong_crossing_terminate_on_rate = wrong_termination_config[
            "terminate_on_rate"]
        if not isinstance(self.wrong_crossing_terminate_on_rate, bool):
            raise TypeError(
                "wrong_crossing_termination.terminate_on_rate must be bool")
        if not 0.0 <= self.wrong_crossing_minimum_tempo <= 1.0 \
                or not 0.0 <= self.wrong_crossing_max_rate <= 1.0:
            raise ValueError("wrong-crossing termination rates must be in [0, 1]")
        self.joint_limit_diagnostic_fraction = _finite_config(
            "joint_limits.diagnostic_fraction",
            joint_limit_config["diagnostic_fraction"])
        self.joint_limit_soft_start_fraction = _finite_config(
            "joint_limits.soft_penalty_start_fraction",
            joint_limit_config["soft_penalty_start_fraction"])
        self.joint_limit_soft_penalty_weight = _finite_config(
            "joint_limits.soft_penalty_weight",
            joint_limit_config["soft_penalty_weight"])
        if not 0.0 < self.joint_limit_diagnostic_fraction <= 1.0 \
                or not 0.0 < self.joint_limit_soft_start_fraction <= 1.0 \
                or self.joint_limit_soft_penalty_weight < 0.0:
            raise ValueError("strike joint-limit configuration is invalid")
        if penetration_threshold <= 0.0:
            raise ValueError(
                "safety.penetration_threshold_m must be positive")
        if not isinstance(penetration_termination, bool):
            raise TypeError(
                "safety.penetration_termination must be bool")
        stage_horizons = {
            stage: _integer_config(
                f"episode.{stage}", episode_config[stage], minimum=1)
            for stage in STAGES
        }
        song_events_per_episode = _integer_config(
            "episode.song_events_per_episode",
            episode_config["song_events_per_episode"], minimum=1)
        timed_lead_frames = _integer_config(
            "episode.timed_lead_frames",
            episode_config["timed_lead_frames"], minimum=0)
        self.random_start = bool(random_start)
        self.failure_termination_penalty = _finite_config(
            "failure_termination_penalty", failure_termination_penalty)
        if self.failure_termination_penalty > 0.0:
            raise ValueError(
                "failure_termination_penalty must be finite and non-positive")


        super().__init__(
            num_envs=num_envs,
            control_dofs=STRIKE_CONTROL_PREFIXES,
            device=device,
            headless=headless,
            seed=seed,
            max_episode_length=100000,
            action_alpha=action_alpha,
            action_scale=action_scale,
            reset_noise=reset_noise,
            reset_soft_limit_fraction=reset_soft_limit_fraction,
            obs_body_names=STRIKE_OBS_BODIES,
        )
        if self.num_actions != 30:
            raise RuntimeError(
                "strike control contract broken: expected 30 DOFs "
                f"(shoulder/elbow/wrist 9 + RH hand 21), got {self.num_actions}")
        control_names = [
            self.dof_names[index]
            for index in self.ctrl_idx.detach().cpu().tolist()]
        expected_prefix_counts = {
            "R_Shoulder": 3, "R_Elbow": 3, "R_Wrist": 3, "RH:": 21}
        for prefix, count in expected_prefix_counts.items():
            actual = sum(name.startswith(prefix) for name in control_names)
            if actual != count:
                raise RuntimeError(
                    f"strike control contract expected {count} {prefix} DOFs, "
                    f"got {actual}")
        if any(name.startswith("R_Thorax") for name in control_names):
            raise RuntimeError("R_Thorax must remain held outside strike control")
        self.controlled_dof_names = tuple(control_names)
        self.action_saturation_regularization_indices = tuple(
            index for index, name in enumerate(control_names)
            if name.startswith(("R_Shoulder", "R_Elbow", "R_Wrist")))
        if len(self.action_saturation_regularization_indices) != 9:
            raise RuntimeError(
                "strike saturation regularization expected 9 arm/wrist DOFs")
        self.joint_limit_group_indices = {
            group: torch.tensor(
                [index for index, name in enumerate(control_names)
                 if name.startswith(prefix)],
                dtype=torch.long, device=self.device)
            for group, prefix in (
                ("shoulder", "R_Shoulder"),
                ("elbow", "R_Elbow"),
                ("wrist", "R_Wrist"),
                ("hand", "RH:"),
            )
        }
        if any(indices.numel() == 0
               for indices in self.joint_limit_group_indices.values()):
            raise RuntimeError("strike joint-limit diagnostic group is empty")
        self._action_is_hand = torch.tensor(
            [name.startswith("RH:") for name in control_names],
            dtype=torch.bool, device=self.device)




        self._disable_pluck_range_collision()

        self.goals = StrikeGoalSequence(
            goal_path,
            device=device,
            rearm_min_frames=detector_rearm_min_frames,
            follow_through_min_frames=frame_values[
                "follow_through_min_frames"],
            initial_timing_tolerance_ms=100)
        self.goals.require_supported_gestures()
        self._strum_event_indices = torch.nonzero(
            self.goals.gesture == 1).squeeze(-1)
        self.song_has_strum = bool(self._strum_event_indices.numel())
        if self.goals.fps != self.SIM_HZ:
            raise RuntimeError(
                f"goal fps {self.goals.fps} != simulator {self.SIM_HZ}")
        self.grip_reference = PickGripReference(
            grip_reference_path, self.dof_names, self.device)
        reference_pose = self.grip_reference.apply_to_pose(self.init_pose)
        lower = self.dof_lower.view(self.num_envs, self.n_dof)[0]
        upper = self.dof_upper.view(self.num_envs, self.n_dof)[0]
        clamped = torch.maximum(torch.minimum(reference_pose, upper), lower)
        reference_error = (
            clamped[self.grip_reference.indices]
            - reference_pose[self.grip_reference.indices]).abs().max()
        if float(reference_error) > 1e-6:
            raise RuntimeError(
                "pick-grip reference is outside the current Isaac joint limits")
        self.init_pose.copy_(clamped)
        self.pd_target.copy_(self.init_pose.repeat(self.num_envs))
        self.grip_hold_action = self.actions_for_pd_targets(
            self.init_pose[self.ctrl_idx][None].expand(self.num_envs, -1))
        self._action_is_pinch = torch.tensor(
            [name in self.grip_reference.pinch_names for name in control_names],
            dtype=torch.bool, device=self.device)
        self._action_is_free_finger = torch.tensor(
            [name in self.grip_reference.free_names for name in control_names],
            dtype=torch.bool, device=self.device)
        if (int(self._action_is_pinch.sum())
                != len(self.grip_reference.pinch_names)
                or int(self._action_is_free_finger.sum())
                != len(self.grip_reference.free_names)
                or torch.any(
                    self._action_is_pinch & self._action_is_free_finger)
                or not torch.equal(
                    self._action_is_pinch | self._action_is_free_finger,
                    self._action_is_hand)):
            raise RuntimeError("pick-grip action groups do not cover RH hand")
        residual_rad = torch.zeros(
            self.num_actions, dtype=self.ctrl_half.dtype, device=self.device)
        residual_rad[self._action_is_pinch] = self.grip_pinch_residual_rad
        residual_rad[self._action_is_free_finger] = self.grip_free_residual_rad
        self._grip_residual_action_span = (
            residual_rad / (self.action_scale * self.ctrl_half[0]))
        self._grip_reference_action = self.grip_hold_action[:1].clone()
        self.policy_neutral_action = torch.where(
            self._action_is_hand[None],
            torch.zeros_like(self.grip_hold_action),
            self.grip_hold_action)

        self.allowed_y = (
            _finite_config(
                "zone.allowed_y_min_m", zone_config["allowed_y_min_m"]),
            _finite_config(
                "zone.allowed_y_max_m", zone_config["allowed_y_max_m"]),
        )
        self.preferred_y = (
            _finite_config(
                "zone.preferred_y_min_m", zone_config["preferred_y_min_m"]),
            _finite_config(
                "zone.preferred_y_max_m", zone_config["preferred_y_max_m"]),
        )
        self.phrase_lane_y = _finite_config(
            "zone.phrase_lane_y_m", zone_config["phrase_lane_y_m"])
        self.lane_core_half_width = _finite_config(
            "zone.lane_core_half_width_m",
            zone_config["lane_core_half_width_m"])
        self.lane_allowed_half_width = _finite_config(
            "zone.lane_allowed_half_width_m",
            zone_config["lane_allowed_half_width_m"])
        if not (
                self.allowed_y[0] < self.preferred_y[0]
                <= self.phrase_lane_y
                <= self.preferred_y[1] < self.allowed_y[1]):
            raise ValueError(
                "strike zone must order allowed/preferred/phrase ranges")
        if (not 0.0 <= self.lane_core_half_width
                < self.lane_allowed_half_width):
            raise ValueError(
                "strike lane widths must satisfy 0 <= core < allowed")
        if (
            self.preferred_y[0] - self.lane_allowed_half_width
                < self.allowed_y[0]
            or self.preferred_y[1] + self.lane_allowed_half_width
                > self.allowed_y[1]
        ):
            raise ValueError(
                "every sampled preferred lane band must stay inside allowed y")

        self.ready_across = _finite_config(
            "trajectory.ready_across_offset_m",
            trajectory_config["ready_across_offset_m"])
        self.entry_across = _finite_config(
            "trajectory.entry_across_offset_m",
            trajectory_config["entry_across_offset_m"])
        self.exit_across = _finite_config(
            "trajectory.exit_across_offset_m",
            trajectory_config["exit_across_offset_m"])
        self.ready_height = _finite_config(
            "trajectory.ready_height_m", trajectory_config["ready_height_m"])
        self.crossing_depth = _finite_config(
            "trajectory.crossing_depth_m",
            trajectory_config["crossing_depth_m"])
        self.ready_distance = _finite_config(
            "trajectory.ready_distance_m",
            trajectory_config["ready_distance_m"])
        self.entry_distance = _finite_config(
            "trajectory.entry_distance_m",
            trajectory_config["entry_distance_m"])
        self.clearance_height = _finite_config(
            "trajectory.clearance_height_m",
            trajectory_config["clearance_height_m"])
        self.clearance_distance = _finite_config(
            "trajectory.clearance_distance_m",
            trajectory_config["clearance_distance_m"])
        self.ready_hold_frames = frame_values["ready_hold_frames"]
        self.recovery_frames = frame_values["recovery_frames"]
        self.follow_through_min_frames = frame_values[
            "follow_through_min_frames"]
        self.approach_lead_s = _finite_config(
            "trajectory.approach_lead_s",
            trajectory_config["approach_lead_s"])
        positive_trajectory = (
            self.ready_across, self.entry_across, self.exit_across,
            self.ready_height, self.crossing_depth,
            self.ready_distance, self.entry_distance,
            self.clearance_height, self.clearance_distance)
        if any(value <= 0.0 for value in positive_trajectory):
            raise ValueError("strike trajectory distances must be finite and positive")
        if self.approach_lead_s <= 0.0:
            raise ValueError("trajectory.approach_lead_s must be positive")
        if not 1 <= self.follow_through_min_frames <= self.recovery_frames:
            raise ValueError(
                "follow_through_min_frames must be in [1, recovery_frames]")

        min_across_speed = _finite_config(
            "detector.min_across_speed_m_s",
            detector_config["min_across_speed_m_s"])
        min_displacement = _finite_config(
            "detector.min_displacement_m",
            detector_config["min_displacement_m"])
        min_depth = _finite_config(
            "detector.min_depth_m", detector_config["min_depth_m"])
        rearm_distance = _finite_config(
            "detector.rearm_distance_m",
            detector_config["rearm_distance_m"])
        parallel_epsilon = _finite_config(
            "detector.parallel_epsilon",
            detector_config["parallel_epsilon"])
        if min(
                min_across_speed, min_displacement, min_depth,
                rearm_distance) <= 0.0:
            raise ValueError("strike detector distances/speed must be positive")
        if self.crossing_depth + 1e-12 < min_depth:
            raise ValueError(
                "trajectory.crossing_depth_m must reach detector.min_depth_m")
        exit_separation = math.hypot(
            self.exit_across, self.crossing_depth)
        if exit_separation + 1e-12 < rearm_distance:
            raise ValueError(
                "trajectory exit point cannot reach detector rearm distance")
        if self.clearance_height + 1e-12 < rearm_distance:
            raise ValueError(
                "trajectory clearance height cannot reach detector rearm distance")
        if parallel_epsilon <= 0.0:
            raise ValueError("detector.parallel_epsilon must be positive")
        min_speed = max(
            min_across_speed, min_displacement * self.SIM_HZ)
        self.detector = PickStrikeDetector(
            num_envs=self.num_envs,
            num_strings=N_GUITAR_STRINGS,
            device=self.device,
            min_across_speed=min_speed,
            min_depth=min_depth,
            rearm_separation=rearm_distance,
            rearm_min_frames=detector_rearm_min_frames,
            parallel_epsilon=parallel_epsilon,
            allowed_y=self.allowed_y,
            preferred_y=self.preferred_y,
        )
        self.reward_fn = StrikeReward(reward)
        self.penetration_monitor = RightGuitarPenetrationMonitor(
            self,
            threshold=penetration_threshold,
            frames=penetration_frames,
            termination_enabled=penetration_termination,
        )

        self.stage_horizons = stage_horizons
        self.song_events_per_episode = song_events_per_episode
        self.base_song_events_per_episode = song_events_per_episode
        self.timed_lead_frames = timed_lead_frames
        self.full_song_start_time_s = (
            float(self.goals.time[0].item())
            - self.timed_lead_frames / self.SIM_HZ)

        self.curriculum_stage = STAGES[0]
        self.curriculum_stalled = False
        self.timing_tolerance_ms = 100.0
        self.tempo_lambda = 1.0
        self.strum_span = 1
        self.s2_profile_name = str(
            self.curriculum_s2_profiles[0]["name"])
        self.s2_endpoint_recovery_active = False
        self.s2_focus_direction = "balanced"
        self.s2_focus_fraction = 0.5
        self.zone_gate_active = False
        self.timing_reward_core_ms = float(
            self.curriculum_s2_profiles[0]["timing_reward_core_ms"])
        self.duration_reward_core_ms = float(
            self.curriculum_s2_profiles[0]["duration_reward_core_ms"])
        self.timing_early_grace_ms = 0.0
        self.timing_early_penalty_scale_ms = 1.0
        self._event_times = self.goals.runtime_time(self.tempo_lambda)
        self._event_left_tolerance, self._event_right_tolerance = (
            self.goals.runtime_windows(
                self.tempo_lambda, self.timing_tolerance_ms))
        self._gap_diagnostics = self.goals.gap_diagnostics(
            self.tempo_lambda, self.timing_tolerance_ms)
        self.evaluation_full_song = False
        self._validate_episode_feasibility()
        self.direction_profile = self.goals.compiled.direction_profile
        self.transition_profile = self.goals.compiled.transition_profile
        self.max_episode_length = self.stage_horizons[self.curriculum_stage]

        n = self.num_envs
        d = self.device
        self.practice_string = torch.arange(
            n, dtype=torch.long, device=d) % N_GUITAR_STRINGS
        self.practice_direction = torch.where(
            torch.arange(n, device=d) % 2 == 0,
            torch.full((n,), DIRECTION_DOWN, dtype=torch.long, device=d),
            torch.full((n,), DIRECTION_UP, dtype=torch.long, device=d))
        self.practice_target_time_s = torch.ones(n, device=d)
        self.target_lane_y = torch.full(
            (n,), self.phrase_lane_y, device=d)
        self._reset_generation = torch.zeros(n, dtype=torch.long, device=d)
        self.event_index = torch.zeros(n, dtype=torch.long, device=d)
        self.episode_event_count = torch.zeros(n, dtype=torch.long, device=d)
        self._episode_event_quota = torch.ones(
            n, dtype=torch.long, device=d)
        self.song_time_s = torch.zeros(n, device=d)
        self.motor_phase = torch.zeros(n, dtype=torch.long, device=d)
        self.ready_streak = torch.zeros(n, dtype=torch.long, device=d)
        self.event_resolved = torch.zeros(n, dtype=torch.bool, device=d)
        self._event_release_mask = torch.zeros(
            n, N_GUITAR_STRINGS, dtype=torch.bool, device=d)
        self._event_release_time_s = torch.zeros(
            n, N_GUITAR_STRINGS, device=d)
        self._event_onset_time_s = torch.zeros(n, device=d)
        self._event_onset_valid = torch.zeros(n, dtype=torch.bool, device=d)
        self._event_zone_valid = torch.ones(n, dtype=torch.bool, device=d)
        self._event_zone_quality = torch.ones(n, device=d)
        self._event_timing_valid = torch.zeros(
            n, dtype=torch.bool, device=d)
        self.recovery_count = torch.zeros(n, dtype=torch.long, device=d)
        self._recovery_best_count = torch.zeros(
            n, dtype=torch.long, device=d)
        self._recovery_completion_recorded = torch.zeros(
            n, dtype=torch.bool, device=d)
        self._scheduled_recovery_best_count = torch.zeros(
            n, dtype=torch.long, device=d)
        self._scheduled_recovery_completion_recorded = torch.zeros(
            n, dtype=torch.bool, device=d)
        self._recovery_required_frames = torch.full(
            (n,), self.recovery_frames, dtype=torch.long, device=d)
        self._recovery_available_frames = torch.full(
            (n,), self.recovery_frames, dtype=torch.long, device=d)
        self._recovery_handoff = torch.zeros(
            n, dtype=torch.bool, device=d)
        self._recovery_same_string_handoff = torch.zeros(
            n, dtype=torch.bool, device=d)
        self._recovery_path_crossing_mask = torch.zeros(
            n, N_GUITAR_STRINGS, dtype=torch.bool, device=d)
        self._recovery_clearance_required = torch.zeros(
            n, dtype=torch.bool, device=d)
        self._recovery_clearance_lifted = torch.zeros(
            n, dtype=torch.bool, device=d)
        self._recovery_clearance_reached = torch.zeros(
            n, dtype=torch.bool, device=d)
        self._recovery_next_entry_string = torch.zeros(
            n, dtype=torch.long, device=d)
        self._recovery_next_direction = torch.full(
            (n,), DIRECTION_DOWN, dtype=torch.long, device=d)
        self._recovery_next_target_lane_y = torch.full(
            (n,), self.phrase_lane_y, device=d)
        self._recovery_reward_valid = torch.zeros(
            n, dtype=torch.bool, device=d)
        self._recovery_target_string = torch.zeros(
            n, dtype=torch.long, device=d)
        self._recovery_target_lane_y = torch.full(
            (n,), self.phrase_lane_y, device=d)
        self._recovery_direction = torch.full(
            (n,), DIRECTION_DOWN, dtype=torch.long, device=d)
        self._recovery_context_valid = torch.zeros(
            n, dtype=torch.bool, device=d)
        self._timeline_finished = torch.zeros(n, dtype=torch.bool, device=d)
        self._previous_tip_g = torch.zeros(n, 3, device=d)
        self._tip_velocity_g = torch.zeros(n, 3, device=d)
        self._previous_tip_valid = torch.zeros(n, dtype=torch.bool, device=d)
        self._last_release = torch.zeros(
            n, N_GUITAR_STRINGS, dtype=torch.bool, device=d)
        # Standalone G0 training always permits release and applies no timing
        # correction.  FullBodyPlayer can update these two policy-facing
        # supervisor signals without exposing raw Fret state to Strike.
        self._synchronizer_release_enable = torch.ones(
            n, dtype=torch.bool, device=d)
        self._synchronizer_timing_offset_s = torch.zeros(n, device=d)
        self._previous_reach_potential = torch.zeros(n, device=d)
        self._previous_strum_progress_potential = torch.zeros(n, device=d)
        self._strum_terminal_progress_best = torch.zeros(n, device=d)
        self._target_distance_valid = torch.zeros(n, dtype=torch.bool, device=d)
        self._wrong_crossing_total = torch.zeros(n, device=d)
        self._wrong_crossing_resolved_events = torch.zeros(
            n, dtype=torch.long, device=d)
        self._wrong_crossing_consecutive_events = torch.zeros(
            n, dtype=torch.long, device=d)
        self._event_had_wrong_crossing = torch.zeros(
            n, dtype=torch.bool, device=d)
        self._wrong_crossing_rate_exceeded = torch.zeros(
            n, dtype=torch.bool, device=d)
        self._event_failure_mass = torch.zeros(
            self.goals.num_events, device=d)
        self._event_failure_exposure = torch.zeros_like(
            self._event_failure_mass)
        self._event_failure_score = torch.zeros_like(
            self._event_failure_mass)
        self._hard_window_probability_max = 0.0
        self._upstroke_window_probability_max = 0.0
        self.failure_mining_updates_enabled = True
        self._sampled_hard_window = torch.zeros(
            n, dtype=torch.bool, device=d)
        self._sampled_upstroke_window = torch.zeros(
            n, dtype=torch.bool, device=d)
        self._sampled_s2_focus = torch.zeros(
            n, dtype=torch.bool, device=d)
        self._forced_start_event_index = None

        self._metric_names = (
            "metric_grip_success_frames", "metric_grip_frames",
            "metric_grip_quality_sum", "metric_grip_pinch_quality_sum",
            "metric_grip_free_quality_sum", "metric_grip_bad_frames",
            "metric_ready_success", "metric_tp", "metric_fp", "metric_fn",
            "metric_zone_attempts", "metric_zone_hits",
            "metric_zone_quality_sum",
            "metric_single_tp", "metric_single_fp", "metric_single_fn",
            "metric_strum_events", "metric_strum_completed",
            "metric_strum_traversal_required",
            "metric_strum_traversal_completed",
            "metric_strum_order_violations",
            "metric_strum_direction_violations",
            "metric_strum_unplanned_crossings",
            "metric_strum_duplicate_crossings",
            "metric_strum_release_attempts",
            "metric_blocked_crossings", "metric_recovery_resets",
            "metric_recovery_completed",
            "metric_scheduled_recovery_completed",
            "metric_full_recovery_events",
            "metric_full_recovery_completed",
            "metric_handoff_recovery_events",
            "metric_handoff_recovery_completed",
            "metric_handoff_required_frames",
            "metric_down_events", "metric_down_completed",
            "metric_up_events", "metric_up_completed",
            "metric_final_string_miss",
            "metric_final_remaining_at_resolution",
            "metric_strum_exit_distance_sum",
            "metric_strum_exit_distance_samples",
            "metric_timing_events", "metric_timing_passed",
            "metric_timing_early", "metric_timing_late",
            "metric_premature_release",
            "metric_raw_zone_attempts", "metric_raw_zone_hits",
            "metric_raw_zone_quality_sum",
            "metric_reward_timing_return",
            "metric_reward_timing_wait_return",
            "metric_reward_strum_progress_return",
            "metric_reward_strum_terminal_progress_return",
            "metric_reward_strum_physical_completion_return",
            "metric_penalty_premature_release_return",
            "metric_penalty_early_timing_return",
            "metric_penalty_miss_return",
        )
        for name in self._metric_names:
            setattr(self, name, torch.zeros(n, device=d))
        self._first_target_release_frame = torch.full(
            (n,), -1, dtype=torch.long, device=d)
        self._grip_history_length = 30
        self._grip_success_history = torch.zeros(
            n, self._grip_history_length, dtype=torch.bool, device=d)
        self._grip_bad_streak = torch.zeros(n, dtype=torch.long, device=d)
        self._grip_bad_streak_max = torch.zeros(
            n, dtype=torch.long, device=d)




        full_song_frames = int(math.ceil(
            (float(self.goals.easy_time[-1].item())
             + max(self.timing_tolerance_ms, 100.0) / 1000.0
             + max(
                 self.recovery_frames,
                 self.detector.rearm_min_frames) / self.SIM_HZ
             - self.full_song_start_time_s)
            * self.SIM_HZ)) + 2
        self._timing_capacity = max(
            self.goals.num_events,
            max(self.stage_horizons.values()),
            full_song_frames,
            1,
        )
        self._grip_quality_samples = torch.zeros(
            n, self._timing_capacity, device=d)
        self._timing_abs_ms = torch.zeros(
            n, self._timing_capacity, device=d)
        self._timing_signed_ms = torch.zeros(
            n, self._timing_capacity, device=d)
        self._timing_count = torch.zeros(n, dtype=torch.long, device=d)
        self._strum_timing_rms_ms = torch.zeros(
            n, self._timing_capacity, device=d)
        self._strum_duration_error_ms = torch.zeros(
            n, self._timing_capacity, device=d)
        self._strum_microtiming_count = torch.zeros(
            n, dtype=torch.long, device=d)

        self.base_obs_dim = self.num_obs
        self.actuator_obs_dim = self.num_actions
        if self.observation_contract == STRIKE_V1_OBSERVATION_CONTRACT:
            self.strike_obs_manifest = self._build_strike_obs_manifest()
            self.strike_obs_dim = len(self.strike_obs_manifest)
            self.num_obs = (
                self.base_obs_dim + self.strike_obs_dim
                + self.actuator_obs_dim)
            self.observation_manifest = tuple(
                self._build_base_obs_manifest()
                + list(self.strike_obs_manifest)
                + [f"actuator.previous_action.{name}"
                   for name in self.controlled_dof_names])
            self.observation_block_slices = None
        else:
            block_manifest = strike_v2_block_manifest(
                self.controlled_dof_names)
            self.strike_obs_manifest = tuple(
                field for fields in block_manifest.values()
                for field in fields)
            self.strike_obs_dim = STRIKE_V2_OBSERVATION_DIM
            self.num_obs = STRIKE_V2_OBSERVATION_DIM
            self.observation_manifest = self.strike_obs_manifest
            self.observation_block_slices = dict(STRIKE_V2_BLOCK_SLICES)
        self.obs_buf = torch.zeros(n, self.num_obs, device=d)
        if len(self.observation_manifest) != self.num_obs:
            raise RuntimeError("strike observation manifest/dimension mismatch")
        self.rew_dim = 1
        self.value_dim = 1
        self.reward_weights = torch.ones(1, device=d)




    def _disable_pluck_range_collision(self):
        if "G:pluck_range" not in self.gbody_index:
            raise RuntimeError("guitar asset is missing G:pluck_range")
        body_index = self.gbody_index["G:pluck_range"]
        disabled_shapes = None
        for env, actor in zip(self.envs, self.g_actors):
            indices = self.gym.get_actor_rigid_body_shape_indices(env, actor)
            record = indices[body_index]
            start, count = int(record.start), int(record.count)
            if count < 1:
                raise RuntimeError("G:pluck_range has no collision shape to disable")
            properties = self.gym.get_actor_rigid_shape_properties(env, actor)
            for shape_index in range(start, start + count):
                properties[shape_index].filter = HUMANOID_COLLISION_FILTER
            self.gym.set_actor_rigid_shape_properties(env, actor, properties)
            disabled_shapes = count

        properties = self.gym.get_actor_rigid_shape_properties(
            self.envs[0], self.g_actors[0])
        indices = self.gym.get_actor_rigid_body_shape_indices(
            self.envs[0], self.g_actors[0])
        record = indices[body_index]
        pluck_indices = set(range(
            int(record.start), int(record.start) + int(record.count)))
        proxy_indices = set(self._body_shape_indices(
            self.envs[0], self.g_actors[0], self.gbody_names,
            THUMB_SUPPORT_PROXY_BODY))
        for index, prop in enumerate(properties):
            expected = (HUMANOID_COLLISION_FILTER
                        if index in pluck_indices
                        else DISABLED_COLLISION_FILTER
                        if index in proxy_indices
                        else GUITAR_COLLISION_FILTER)
            if int(prop.filter) != expected:
                raise RuntimeError(
                    "strike collision audit changed a non-pluck guitar shape")
        self.strike_collision_audit = {
            "pluck_range_shapes": int(disabled_shapes or 0),
            "pluck_range_filter": HUMANOID_COLLISION_FILTER,
            "other_guitar_filter": GUITAR_COLLISION_FILTER,
            "pluck_range_human_collision_enabled": False,
        }

    def string_segments_g(self) -> Tuple[torch.Tensor, torch.Tensor]:
        start_world = torch.stack([
            self.gbody_pos(f"G:string{index}")
            for index in range(1, N_GUITAR_STRINGS + 1)], dim=1)
        end_world = torch.stack([
            self.gbody_pos(f"G:string{index}_end")
            for index in range(1, N_GUITAR_STRINGS + 1)], dim=1)
        return (
            self.to_guitar_frame(start_world),
            self.to_guitar_frame(end_world),
        )

    def _string_lane_geometry(
            self, target_lane_y=None, *, segments=None,
            validate_degenerate=True):
        start, end = (
            self.string_segments_g() if segments is None else segments)
        if target_lane_y is None:
            target_lane_y = self.target_lane_y
        denominator = end[..., 1] - start[..., 1]
        if validate_degenerate and torch.any(denominator.abs() < 1e-8):
            raise RuntimeError("a guitar string is degenerate along the strike lane")
        u = (
            (target_lane_y[:, None] - start[..., 1]) / denominator
        ).clamp(0.0, 1.0)
        lane = start + u[..., None] * (end - start)
        tangent_xy = end[..., :2] - start[..., :2]
        tangent_xy = tangent_xy / torch.linalg.vector_norm(
            tangent_xy, dim=-1, keepdim=True).clamp_min(1e-8)
        normal_xy = torch.stack(
            [-tangent_xy[..., 1], tangent_xy[..., 0]], dim=-1)
        sign = torch.where(
            normal_xy[..., 0] < 0.0,
            -torch.ones_like(normal_xy[..., 0]),
            torch.ones_like(normal_xy[..., 0]))
        normal_xy = normal_xy * sign[..., None]
        normal = torch.cat(
            [normal_xy, torch.zeros_like(normal_xy[..., :1])], dim=-1)
        return lane, normal

    def _current_target_geometry(self):
        motion = self._current_motion_context()
        target_string = motion["target_string"]
        target_lane_y = motion["target_lane_y"]
        direction = motion["target_direction"].to(self.target_lane_y.dtype)
        segments = self.string_segments_g()
        lane, normal = self._string_lane_geometry(
            target_lane_y, segments=segments)
        rows = torch.arange(self.num_envs, device=self.device)
        exit_string = target_string
        active_song_gesture = (
            (self.curriculum_stage in STRUM_STAGES)
            & ~self._recovery_context_valid)
        if isinstance(active_song_gesture, bool):
            active_song_gesture = torch.full(
                (self.num_envs,), active_song_gesture,
                dtype=torch.bool, device=self.device)
        event_index = self.event_index.clamp(0, self.goals.num_events - 1)
        target_masks = self._event_target_masks(event_index)
        event_direction = self._current_target_direction()
        effective_exit_string = strike_next_traversal_string(
            target_masks,
            torch.zeros_like(target_masks),
            -event_direction,
            self.goals.exit_string[event_index],
        )
        approach_string = strike_next_traversal_string(
            target_masks,
            self._event_release_mask,
            event_direction,
            effective_exit_string,
        )
        use_approach_string = (
            active_song_gesture
            & (self.motor_phase == PHASE_APPROACH))
        target_string = torch.where(
            use_approach_string, approach_string, target_string)
        exit_string = torch.where(
            active_song_gesture,
            effective_exit_string,
            exit_string)
        center = lane[rows, target_string]
        exit_center = lane[rows, exit_string]
        across = normal[rows, target_string]
        signed_across = direction[:, None] * across
        ready = center - self.ready_across * signed_across
        ready = ready.clone()
        ready[:, 2] += self.ready_height
        entry = center - self.entry_across * signed_across
        entry = entry.clone()
        entry[:, 2] -= self.crossing_depth
        exit_point = exit_center + self.exit_across * signed_across
        exit_point = exit_point.clone()
        exit_point[:, 2] -= self.crossing_depth
        release_lift, next_entry_lift = self._recovery_clearance_points(
            lane, normal, segments)
        next_ready = next_entry_lift.clone()
        next_ready[:, 2] += self.ready_height - self.clearance_height
        clearance = strike_recovery_clearance_target(
            self._recovery_context_valid
            & (self.motor_phase == PHASE_RELEASE_RECOVER),
            self._recovery_clearance_required,
            self._recovery_clearance_lifted,
            self._recovery_clearance_reached,
            release_lift,
            next_entry_lift,
            next_ready)
        exit_point = torch.where(
            clearance["active"][:, None], clearance["target"], exit_point)
        return (
            target_string, target_lane_y, center, ready, entry, exit_point,
            exit_center)


    def _recovery_clearance_points(
            self, release_lane, release_normal, segments):
        rows = torch.arange(self.num_envs, device=self.device)
        release_center = release_lane[
            rows, self._recovery_target_string]
        release_across = release_normal[
            rows, self._recovery_target_string]
        release_direction = self._recovery_direction.to(
            release_center.dtype)
        release_lift = (
            release_center
            + self.exit_across
            * release_direction[:, None] * release_across)
        release_lift = release_lift.clone()
        release_lift[:, 2] += self.clearance_height

        entry_lane, entry_normal = self._string_lane_geometry(
            self._recovery_next_target_lane_y,
            segments=segments,
            validate_degenerate=False)
        entry_center = entry_lane[
            rows, self._recovery_next_entry_string]
        entry_across = entry_normal[
            rows, self._recovery_next_entry_string]
        next_direction = self._recovery_next_direction.to(
            entry_center.dtype)
        next_entry_lift = (
            entry_center
            - self.ready_across
            * next_direction[:, None] * entry_across)
        next_entry_lift = next_entry_lift.clone()
        next_entry_lift[:, 2] += self.clearance_height
        return release_lift, next_entry_lift

    def _update_recovery_clearance(self, tip, clearance_target):
        active = (
            self._recovery_context_valid
            & (self.motor_phase == PHASE_RELEASE_RECOVER)
            & self._recovery_clearance_required
            & ~self._recovery_clearance_reached)
        target_distance = torch.linalg.vector_norm(
            tip - clearance_target, dim=-1)
        state = strike_clearance_waypoint_state(
            active,
            self._recovery_clearance_lifted,
            self._recovery_clearance_reached,
            target_distance,
            distance_threshold=self.clearance_distance)
        self._recovery_clearance_lifted.copy_(state["lifted"])
        self._recovery_clearance_reached.copy_(state["reached"])
        return state["target_changed"]




    def _current_target_string(self):
        if self.curriculum_stage in SINGLE_PRACTICE_STAGES:
            return self.practice_string
        index = self.event_index.clamp(0, self.goals.num_events - 1)
        if self.curriculum_stage in STRUM_ONLY_STAGES:
            traversal = self._event_target_masks(index)
            string_indices = torch.arange(
                N_GUITAR_STRINGS, device=self.device)[None]
            down_entry = torch.where(
                traversal, string_indices,
                torch.full_like(string_indices, -1)).amax(dim=1)
            up_entry = torch.where(
                traversal, string_indices,
                torch.full_like(string_indices, N_GUITAR_STRINGS)).amin(dim=1)
            return torch.where(
                self.practice_direction == DIRECTION_DOWN,
                down_entry, up_entry)
        return self.goals.string[index]

    def _current_target_time(self):
        if self.curriculum_stage in (A0_PICK_GRIP, A1_TIP_READY,
                                      A2_SINGLE_CROSSING,
                                      A4_STRUM_CONTEXT_RECOVERY,
                                      S0_TWO_STRING_STRUM,
                                      S1_STRUM_SPAN):
            return torch.zeros(self.num_envs, device=self.device)
        if self.curriculum_stage in (A3_TIMED_SINGLE, S2_TIMED_STRUM):
            return self.practice_target_time_s
        index = self.event_index.clamp(0, self.goals.num_events - 1)
        return self._event_times[index]

    def _effective_target_time(self):
        """Return the musical deadline after Synchronizer correction."""
        return (
            self._current_target_time()
            + self._synchronizer_timing_offset_s)

    def _current_target_direction(self):
        if self.curriculum_stage in PRACTICE_DIRECTION_STAGES:
            return self.practice_direction
        index = self.event_index.clamp(0, self.goals.num_events - 1)
        return self.goals.direction[index]

    def _current_target_offsets(self):
        index = self.event_index.clamp(0, self.goals.num_events - 1)
        if self.curriculum_stage in STRUM_ONLY_STAGES:
            mask = self._current_target_masks()
            full_count = self.goals.traversal_mask[index].sum(
                dim=1).clamp_min(1).to(self.song_time_s.dtype)
            interval = torch.where(
                full_count > 1.0,
                self.goals.sweep_duration[index] / (full_count - 1.0),
                torch.full_like(full_count, 0.007))
            return strike_uniform_traversal_offsets(
                mask, self.practice_direction, interval)
        offsets = self.goals.traversal_offset[index].clone()
        mask = self._current_target_masks()
        positive_inf = torch.full_like(offsets, float("inf"))
        negative_inf = torch.full_like(offsets, float("-inf"))
        minimum = torch.where(mask, offsets, positive_inf).amin(dim=1)
        maximum = torch.where(mask, offsets, negative_inf).amax(dim=1)
        center = 0.5 * (minimum + maximum)
        return torch.where(mask, offsets - center[:, None], torch.zeros_like(offsets))

    def _current_target_sweep_duration(self):
        offsets = self._current_target_offsets()
        mask = self._current_target_masks()
        minimum = torch.where(
            mask, offsets, torch.full_like(offsets, float("inf"))).amin(dim=1)
        maximum = torch.where(
            mask, offsets, torch.full_like(offsets, float("-inf"))).amax(dim=1)
        return maximum - minimum

    def _current_target_masks(self):
        if self.curriculum_stage in SINGLE_PRACTICE_STAGES:
            return _one_hot(
                self._current_target_string(),
                N_GUITAR_STRINGS, dtype=torch.bool)
        index = self.event_index.clamp(0, self.goals.num_events - 1)
        return self._event_target_masks(index)

    def _event_target_masks(self, index):
        traversal = self.goals.traversal_mask[index]
        if self.curriculum_stage not in STRUM_STAGES:
            return traversal
        direction = (
            self.practice_direction
            if self.curriculum_stage in STRUM_ONLY_STAGES
            else self.goals.direction[index])
        return strike_limit_traversal_span(
            traversal, direction, self.strum_span)

    def _current_timing_tolerances(self):
        tolerance = torch.full(
            (self.num_envs,), self.timing_tolerance_ms / 1000.0,
            device=self.device)
        if self.curriculum_stage != S3_SONG_INTEGRATION:
            return tolerance, tolerance
        index = self.event_index.clamp(0, self.goals.num_events - 1)
        return (
            self._event_left_tolerance[index],
            self._event_right_tolerance[index])

    def _current_motion_context(self):
        """Return geometry and direction that own the current motor trajectory.

        S3 advances the musical event immediately after resolving it so the
        next event remains visible to the policy.  Physical follow-through
        nevertheless stays attached to the just-released string and lane
        until the motor phase leaves ``RELEASE_RECOVER``.
        """
        context = strike_motion_target_context(
            self._current_target_string(),
            self.target_lane_y,
            self._current_target_direction(),
            self._recovery_target_string,
            self._recovery_target_lane_y,
            self._recovery_direction,
            self._recovery_context_valid,
            self.motor_phase,
            release_recover_phase=PHASE_RELEASE_RECOVER,
        )
        return context

    def _current_motion_target(self):
        context = self._current_motion_context()
        return context["target_string"], context["target_lane_y"]

    def _plan_recovery(
            self, physical_hit, release_string, release_direction,
            event_time):
        next_index = (self.event_index + 1).clamp_max(
            self.goals.num_events - 1)
        continuing = (
            physical_hit
            & torch.full_like(
                physical_hit,
                self.curriculum_stage == S3_SONG_INTEGRATION)
            & ((self.episode_event_count + 1) < self._episode_event_quota)
            & ((self.event_index + 1) < self.goals.num_events))
        next_target_time = torch.where(
            continuing,
            self._event_times[next_index],
            event_time + 1.0)
        next_direction = self.goals.direction[next_index]
        next_traversal = self._event_target_masks(next_index)
        next_entry_string = strike_next_traversal_string(
            next_traversal,
            torch.zeros_like(next_traversal),
            next_direction,
            self.goals.string[next_index])
        plan = strike_dual_recovery_plan(
            event_time,
            next_target_time,
            continuing,
            release_string,
            release_direction,
            next_entry_string,
            next_direction,
            num_strings=N_GUITAR_STRINGS,
            sim_hz=self.SIM_HZ,
            approach_lead_s=self.approach_lead_s,
            full_recovery_frames=self.recovery_frames,
            minimum_handoff_frames=self.follow_through_min_frames,
        )
        self._recovery_required_frames[physical_hit] = plan[
            "required_frames"][physical_hit]
        self._recovery_available_frames[physical_hit] = plan[
            "available_frames"][physical_hit]
        self._recovery_handoff[physical_hit] = plan["handoff"][physical_hit]
        self._recovery_same_string_handoff[physical_hit] = plan[
            "same_string_handoff"][physical_hit]
        self._recovery_path_crossing_mask[physical_hit] = plan[
            "path_crossing_mask"][physical_hit]
        self._recovery_clearance_required[physical_hit] = plan[
            "clearance_required"][physical_hit]
        self._recovery_clearance_lifted[physical_hit] = False
        self._recovery_clearance_reached[physical_hit] = False
        self._recovery_next_entry_string[physical_hit] = (
            next_entry_string[physical_hit])
        self._recovery_next_direction[physical_hit] = (
            next_direction[physical_hit])
        self._recovery_next_target_lane_y[physical_hit] = (
            self.target_lane_y[physical_hit])
        self._recovery_completion_recorded[physical_hit] = False
        self._scheduled_recovery_best_count[physical_hit] = 0
        self._scheduled_recovery_completion_recorded[physical_hit] = False
        full = physical_hit & ~plan["handoff"]
        handoff = physical_hit & plan["handoff"]
        self.metric_full_recovery_events += full.float()
        self.metric_handoff_recovery_events += handoff.float()
        self.metric_handoff_required_frames += (
            plan["required_frames"].float() * handoff.float())

    def _recovery_rearmed(self):
        rows = torch.arange(self.num_envs, device=self.device)
        armed = (
            self.detector.state[
                rows, self._recovery_target_string] == DETECTOR_ARMED)
        return ~self._recovery_context_valid | armed

    def _sample_event_index(self, env_ids):
        count = env_ids.numel()
        if count == 0:
            return torch.empty(0, dtype=torch.long, device=self.device)
        self._sampled_hard_window[env_ids] = False
        self._sampled_upstroke_window[env_ids] = False
        self._sampled_s2_focus[env_ids] = False
        default_quota = (
            self.goals.num_events if self.evaluation_full_song
            else min(self.song_events_per_episode, self.goals.num_events))
        self._episode_event_quota[env_ids] = default_quota
        if self.curriculum_stage in STRUM_ONLY_STAGES:
            event_spans = self.goals.traversal_mask[
                self._strum_event_indices].sum(dim=1)
            eligible = self._strum_event_indices[event_spans >= self.strum_span]
            if eligible.numel() == 0:
                raise RuntimeError(
                    f"{self.curriculum_stage} requires a strum spanning at "
                    f"least {self.strum_span} strings, but the goal has none")
            slots = torch.randint(
                eligible.numel(), (count,),
                generator=self.rng, device=self.device)
            return eligible[slots]
        if self.curriculum_stage == A3_TIMED_SINGLE:
            self._episode_event_quota[env_ids] = 1
            return torch.zeros(count, dtype=torch.long, device=self.device)
        max_start = max(self.goals.num_events - default_quota, 0)
        if self._forced_start_event_index is not None:
            forced = int(self._forced_start_event_index)
            if forced < 0 or forced > max_start:
                raise ValueError(
                    "forced Strike start event is outside the current window")
            return torch.full(
                (count,), forced, dtype=torch.long, device=self.device)
        if self.evaluation_full_song or not self.random_start:
            return torch.zeros(count, dtype=torch.long, device=self.device)
        sampled = (torch.randint(
            max_start + 1, (count,), generator=self.rng, device=self.device)
            if max_start > 0 else
            torch.zeros(count, dtype=torch.long, device=self.device))
        hard_mask = torch.zeros(count, dtype=torch.bool, device=self.device)
        upstroke_mask = torch.zeros(
            count, dtype=torch.bool, device=self.device)
        selector = torch.rand(
            count, generator=self.rng, device=self.device)
        hard_sampling_active = False
        if (self.curriculum_stage == S3_SONG_INTEGRATION
                and self.stalled_hard_sample_fraction > 0.0):
            rehearsal_quota = min(
                self.stalled_hard_rehearsal_events,
                default_quota,
                self.goals.num_events)
            window_scores = event_predecessor_rehearsal_scores(
                self._event_failure_score, rehearsal_quota)
            if bool((window_scores > 0.0).any()):
                hard_sampling_active = True
                probability_cap = max(
                    self.stalled_hard_window_probability_cap,
                    1.0 / window_scores.numel())
                window_probabilities = (
                    bounded_failure_sampling_probabilities(
                        window_scores, probability_cap))
                self._hard_window_probability_max = float(
                    window_probabilities.max().item())
                hard_mask = selector < self.stalled_hard_sample_fraction
                hard_count = int(hard_mask.sum().item())
                if hard_count > 0:
                    sampled[hard_mask] = torch.multinomial(
                        window_probabilities,
                        hard_count,
                        replacement=True,
                        generator=self.rng)
                    self._episode_event_quota[
                        env_ids[hard_mask]] = rehearsal_quota
            else:
                self._hard_window_probability_max = 0.0
        if (self.curriculum_stage == S3_SONG_INTEGRATION
                and self.s3_upstroke_sample_fraction > 0.0):
            upstroke_scores = event_mask_window_scores(
                self.goals.direction == DIRECTION_UP, default_quota)
            if bool((upstroke_scores > 0.0).any()):
                probability_cap = max(
                    self.s3_upstroke_window_probability_cap,
                    1.0 / upstroke_scores.numel())
                upstroke_probabilities = (
                    bounded_failure_sampling_probabilities(
                        upstroke_scores, probability_cap))
                self._upstroke_window_probability_max = float(
                    upstroke_probabilities.max().item())
                lower = (
                    self.stalled_hard_sample_fraction
                    if hard_sampling_active else 0.0)
                upstroke_mask = (
                    ~hard_mask
                    & (selector >= lower)
                    & (selector < lower + self.s3_upstroke_sample_fraction))
                upstroke_count = int(upstroke_mask.sum().item())
                if upstroke_count > 0:
                    sampled[upstroke_mask] = torch.multinomial(
                        upstroke_probabilities,
                        upstroke_count,
                        replacement=True,
                        generator=self.rng)
            else:
                self._upstroke_window_probability_max = 0.0
        self._sampled_hard_window[env_ids] = hard_mask
        self._sampled_upstroke_window[env_ids] = upstroke_mask
        return sampled

    def _record_event_failure_scores(self, event_index, exposed, failure):
        if (self.curriculum_stage != S3_SONG_INTEGRATION
                or not self.failure_mining_updates_enabled
                or self.evaluation_full_song):
            return
        exposed = exposed.bool()
        failure = failure.bool() & exposed
        if not bool(exposed.any()):
            return
        updated = update_event_failure_statistics(
            self._event_failure_mass,
            self._event_failure_exposure,
            event_index,
            exposed,
            failure,
            decay=self.stalled_failure_score_decay,
            prior_exposure=self.stalled_failure_prior_exposure)
        self._event_failure_mass.copy_(updated["failure_mass"])
        self._event_failure_exposure.copy_(updated["exposure_mass"])
        self._event_failure_score.copy_(updated["score"])

    def _validate_episode_feasibility(
            self, stage=None, tolerance_ms=None):
        """Reject horizons that cannot complete their own motor contract."""
        if self.timed_lead_frames < self.ready_hold_frames + 1:
            raise ValueError(
                "episode.timed_lead_frames must allow READY hold and one "
                "APPROACH action")
        earliest_practice_frames = int(math.floor(
            TIMED_PRACTICE_MIN_TIME_S * self.SIM_HZ))
        if self.ready_hold_frames + 1 > earliest_practice_frames:
            raise ValueError(
                "READY hold cannot finish before the earliest A3 target")
        if (stage == S3_SONG_INTEGRATION
                and self.approach_lead_s + float(tolerance_ms) / 1000.0
                < 1.0 / self.SIM_HZ):
            raise ValueError(
                "S3 approach lead and timing tolerance must leave at "
                "least one APPROACH action")
        candidates = (
            (A1_TIP_READY, None),
            (A2_SINGLE_CROSSING, None),
        ) if stage is None else ((stage, tolerance_ms),)
        goal_times = self._event_times.detach().cpu().tolist()
        required = {
            name: minimum_strike_stage_horizon(
                name,
                goal_times,
                sim_hz=self.SIM_HZ,
                ready_hold_frames=self.ready_hold_frames,
                recovery_frames=self.recovery_frames,
                rearm_min_frames=self.detector.rearm_min_frames,
                timed_lead_frames=self.timed_lead_frames,
                song_events_per_episode=self.song_events_per_episode,
                timing_tolerance_ms=tolerance)
            for name, tolerance in candidates
        }
        impossible = {
            stage: (self.stage_horizons[stage], minimum)
            for stage, minimum in required.items()
            if stage != S3_SONG_INTEGRATION
            and self.stage_horizons[stage] < minimum
        }
        if impossible:
            detail = ", ".join(
                f"{stage}={actual} (requires >= {minimum})"
                for stage, (actual, minimum) in impossible.items())
            raise ValueError(f"strike episode horizon is infeasible: {detail}")

    def _reset_task_state(self, env_ids):
        if env_ids.numel() == 0:
            return
        self._reset_generation[env_ids] += 1
        self.practice_string[env_ids] = (
            env_ids + self._reset_generation[env_ids] - 1
        ) % N_GUITAR_STRINGS
        sampled = self._sample_event_index(env_ids)
        self.event_index[env_ids] = sampled
        balanced_direction = strike_balanced_practice_direction(
            env_ids, self._reset_generation[env_ids])
        if self.curriculum_stage in PRACTICE_DIRECTION_STAGES:
            self.practice_direction[env_ids] = balanced_direction
            if (self.curriculum_stage == S2_TIMED_STRUM
                    and self.s2_endpoint_recovery_active):
                focus_direction = (
                    DIRECTION_DOWN
                    if self.s2_focus_direction == "down"
                    else DIRECTION_UP)
                focus = strike_focused_practice_direction(
                    balanced_direction,
                    torch.rand(
                        env_ids.numel(), generator=self.rng,
                        device=self.device),
                    focus_direction=focus_direction,
                    target_focus_fraction=self.s2_focus_fraction)
                self.practice_direction[env_ids] = focus["direction"]
                self._sampled_s2_focus[env_ids] = focus[
                    "focused_subset"]
        else:
            self.practice_direction[env_ids] = self.goals.direction[sampled]
        self.episode_event_count[env_ids] = 0
        if self.curriculum_stage in (A3_TIMED_SINGLE, S2_TIMED_STRUM):
            self.practice_target_time_s[env_ids] = (
                TIMED_PRACTICE_MIN_TIME_S
                + (TIMED_PRACTICE_MAX_TIME_S
                   - TIMED_PRACTICE_MIN_TIME_S) * torch.rand(
                    env_ids.numel(), generator=self.rng,
                    device=self.device))
            self.song_time_s[env_ids] = 0.0
        elif self.curriculum_stage == S3_SONG_INTEGRATION:
            if self.evaluation_full_song:
                self.song_time_s[env_ids] = self.full_song_start_time_s
            else:
                target_time = self._event_times[sampled]
                self.song_time_s[env_ids] = (
                    target_time - self.timed_lead_frames / self.SIM_HZ
                )
        else:
            self.song_time_s[env_ids] = 0.0
        if self.zone_gate_active:
            lane_lo, lane_hi = self.preferred_y
            self.target_lane_y[env_ids] = (
                lane_lo + (lane_hi - lane_lo) * torch.rand(
                    env_ids.numel(), generator=self.rng,
                    device=self.device))
        else:
            self.target_lane_y[env_ids] = self.phrase_lane_y
        self.motor_phase[env_ids] = PHASE_READY
        self.ready_streak[env_ids] = 0
        self.event_resolved[env_ids] = False
        self._event_release_mask[env_ids] = False
        self._event_release_time_s[env_ids] = 0.0
        self._event_onset_time_s[env_ids] = 0.0
        self._event_onset_valid[env_ids] = False
        self._event_zone_valid[env_ids] = True
        self._event_zone_quality[env_ids] = 1.0
        self._event_timing_valid[env_ids] = False
        self.recovery_count[env_ids] = 0
        self._recovery_best_count[env_ids] = 0
        self._recovery_completion_recorded[env_ids] = False
        self._scheduled_recovery_best_count[env_ids] = 0
        self._scheduled_recovery_completion_recorded[env_ids] = False
        self._recovery_required_frames[env_ids] = self.recovery_frames
        self._recovery_available_frames[env_ids] = self.recovery_frames
        self._recovery_handoff[env_ids] = False
        self._recovery_same_string_handoff[env_ids] = False
        self._recovery_path_crossing_mask[env_ids] = False
        self._recovery_clearance_required[env_ids] = False
        self._recovery_clearance_lifted[env_ids] = False
        self._recovery_clearance_reached[env_ids] = False
        self._recovery_next_entry_string[env_ids] = 0
        self._recovery_next_direction[env_ids] = DIRECTION_DOWN
        self._recovery_next_target_lane_y[env_ids] = self.phrase_lane_y
        self._recovery_reward_valid[env_ids] = False
        self._recovery_direction[env_ids] = DIRECTION_DOWN
        self._recovery_context_valid[env_ids] = False
        self._timeline_finished[env_ids] = False
        self._tip_velocity_g[env_ids] = 0.0
        self._previous_tip_valid[env_ids] = False
        self._last_release[env_ids] = False
        self._synchronizer_release_enable[env_ids] = True
        self._synchronizer_timing_offset_s[env_ids] = 0.0
        self._previous_reach_potential[env_ids] = 0.0
        self._previous_strum_progress_potential[env_ids] = 0.0
        self._strum_terminal_progress_best[env_ids] = 0.0
        self._target_distance_valid[env_ids] = False
        self._wrong_crossing_total[env_ids] = 0.0
        self._wrong_crossing_resolved_events[env_ids] = 0
        self._wrong_crossing_consecutive_events[env_ids] = 0
        self._event_had_wrong_crossing[env_ids] = False
        self._wrong_crossing_rate_exceeded[env_ids] = False
        self.detector.reset(env_ids)
        if hasattr(self, "penetration_monitor"):
            self.penetration_monitor.reset(env_ids)
        for name in self._metric_names:
            getattr(self, name)[env_ids] = 0.0
        self._first_target_release_frame[env_ids] = -1
        self._grip_success_history[env_ids] = False
        self._grip_bad_streak[env_ids] = 0
        self._grip_bad_streak_max[env_ids] = 0
        self._grip_quality_samples[env_ids] = 0.0
        self._timing_abs_ms[env_ids] = 0.0
        self._timing_signed_ms[env_ids] = 0.0
        self._timing_count[env_ids] = 0
        self._strum_timing_rms_ms[env_ids] = 0.0
        self._strum_duration_error_ms[env_ids] = 0.0
        self._strum_microtiming_count[env_ids] = 0

    def _advance_song_events(self, resolved, physical_release):
        ids = torch.nonzero(resolved).squeeze(-1)
        if ids.numel() == 0:
            return
        self.episode_event_count[ids] += 1
        self._target_distance_valid[ids] = False
        next_index = self.event_index[ids] + 1
        finished = (
            (self.episode_event_count[ids] >= self._episode_event_quota[ids])
            | (next_index >= self.goals.num_events))
        continuing = ids[~finished]
        if continuing.numel() > 0:
            self.event_index[continuing] += 1
            phase_advance = strike_song_continuing_phase(
                self.motor_phase[continuing],
                physical_release[continuing],
                self._recovery_context_valid[continuing],
                release_recover_phase=PHASE_RELEASE_RECOVER)
            preserve_recovery = phase_advance["preserve_recovery"]
            self.motor_phase[continuing] = phase_advance["motor_phase"]
            self.ready_streak[continuing] = 0
            self.event_resolved[continuing] = False
            self._event_release_mask[continuing] = False
            self._event_release_time_s[continuing] = 0.0
            self._event_onset_time_s[continuing] = 0.0
            self._event_onset_valid[continuing] = False
            self._event_zone_valid[continuing] = True
            self._event_zone_quality[continuing] = 1.0
            self._event_timing_valid[continuing] = False
            self._recovery_best_count[continuing] = 0
            self._strum_terminal_progress_best[continuing] = 0.0
            self._recovery_context_valid[
                continuing[~preserve_recovery]] = False




    def _validate_stage_goal_contract(self, stage, tolerance_ms):
        if stage == S3_SONG_INTEGRATION:
            self.goals.require_nonoverlapping_match_windows(tolerance_ms)
        self._validate_episode_feasibility(stage, tolerance_ms)

    def set_curriculum_stage(
            self, stage, tolerance_ms, tempo_lambda=1.0,
            strum_span=1, s2_profile_name=None,
            s2_endpoint_recovery_active=False,
            s2_focus_direction="balanced", s2_focus_fraction=0.5,
            zone_active=None,
            timing_reward_core_ms=None, duration_reward_core_ms=None,
            approach_lead_s=None, timing_early_grace_ms=None,
            timing_early_penalty_scale_ms=None,
            song_f1_gate=None,
            song_events_per_episode=None,
            stalled=False,
            reset=False):
        if stage not in STAGES:
            raise ValueError(f"unknown strike stage: {stage}")
        tolerance_ms = float(tolerance_ms)
        if not math.isfinite(tolerance_ms) or tolerance_ms <= 0.0:
            raise ValueError("timing tolerance must be finite and positive")
        tempo_lambda = float(tempo_lambda)
        if not math.isfinite(tempo_lambda) or not 0.0 <= tempo_lambda <= 1.0:
            raise ValueError("tempo lambda must be finite and in [0, 1]")
        if stage != S3_SONG_INTEGRATION:
            tempo_lambda = 1.0
        failure_context_changed = (
            stage != self.curriculum_stage
            or (stage == S3_SONG_INTEGRATION
                and abs(tempo_lambda - self.tempo_lambda) > 1e-9))
        strum_span = int(strum_span)
        if strum_span < 1 or strum_span > N_GUITAR_STRINGS:
            raise ValueError("strum span must be in [1, 6]")
        if s2_profile_name is None:
            s2_profile_name = self.s2_profile_name
        if not isinstance(s2_profile_name, str) or not s2_profile_name:
            raise ValueError("S2 profile name must be a non-empty string")
        if not isinstance(s2_endpoint_recovery_active, bool):
            raise TypeError("s2_endpoint_recovery_active must be bool")
        if s2_focus_direction not in ("balanced", "down", "up"):
            raise ValueError(
                "s2_focus_direction must be balanced, down or up")
        if isinstance(s2_focus_fraction, bool):
            raise TypeError("s2_focus_fraction must be numeric")
        s2_focus_fraction = float(s2_focus_fraction)
        if (not math.isfinite(s2_focus_fraction)
                or not 0.5 <= s2_focus_fraction <= 0.7
                or s2_focus_fraction
                > self.s2_endpoint_focus_fraction_config + 1e-9):
            raise ValueError("s2_focus_fraction is outside its configured range")
        if s2_endpoint_recovery_active:
            if stage != S2_TIMED_STRUM:
                raise ValueError("endpoint recovery is valid only in S2")
            if s2_focus_direction not in ("down", "up"):
                raise ValueError(
                    "active endpoint recovery requires a focus direction")
        elif s2_focus_direction != "balanced" \
                or abs(s2_focus_fraction - 0.5) > 1e-9:
            raise ValueError(
                "inactive endpoint recovery must remain balanced")
        if zone_active is None:
            zone_active = stage in (A3_TIMED_SINGLE, S3_SONG_INTEGRATION)
        if not isinstance(zone_active, bool):
            raise TypeError("zone_active must be bool")
        if not isinstance(stalled, bool):
            raise TypeError("stalled must be bool")
        if song_f1_gate is None:
            song_f1_gate = self.curriculum_song_f1_gate
        song_f1_gate = float(song_f1_gate)
        if not math.isfinite(song_f1_gate) or not 0.0 <= song_f1_gate <= 1.0:
            raise ValueError("song F1 gate must be finite in [0, 1]")
        if song_events_per_episode is None:
            song_events_per_episode = self.song_events_per_episode
        song_events_per_episode = _integer_config(
            "song_events_per_episode", song_events_per_episode, minimum=1)
        song_events_per_episode = min(
            song_events_per_episode, self.goals.num_events)
        if timing_reward_core_ms is None:
            timing_reward_core_ms = self.reward_fn.timing_core_s * 1000.0
        if duration_reward_core_ms is None:
            duration_reward_core_ms = (
                self.reward_fn.strum_duration_core_s * 1000.0)
        timing_reward_core_ms = float(timing_reward_core_ms)
        duration_reward_core_ms = float(duration_reward_core_ms)
        if (not math.isfinite(timing_reward_core_ms)
                or not math.isfinite(duration_reward_core_ms)
                or timing_reward_core_ms <= 0.0
                or duration_reward_core_ms <= 0.0):
            raise ValueError("timing reward cores must be finite and positive")
        if approach_lead_s is None:
            approach_lead_s = self.approach_lead_s
        if timing_early_grace_ms is None:
            timing_early_grace_ms = self.timing_early_grace_ms
        if timing_early_penalty_scale_ms is None:
            timing_early_penalty_scale_ms = (
                self.timing_early_penalty_scale_ms)
        approach_lead_s = float(approach_lead_s)
        timing_early_grace_ms = float(timing_early_grace_ms)
        timing_early_penalty_scale_ms = float(
            timing_early_penalty_scale_ms)
        if (not math.isfinite(approach_lead_s) or approach_lead_s <= 0.0
                or not math.isfinite(timing_early_grace_ms)
                or timing_early_grace_ms < 0.0
                or timing_early_grace_ms > tolerance_ms
                or not math.isfinite(timing_early_penalty_scale_ms)
                or timing_early_penalty_scale_ms <= 0.0):
            raise ValueError(
                "timed approach lead/grace/scale must be finite and valid")
        self._event_times = self.goals.runtime_time(tempo_lambda)
        self._event_left_tolerance, self._event_right_tolerance = (
            self.goals.runtime_windows(tempo_lambda, tolerance_ms))
        self._gap_diagnostics = self.goals.gap_diagnostics(
            tempo_lambda, tolerance_ms)
        previous_song_events = self.song_events_per_episode
        self.song_events_per_episode = song_events_per_episode
        try:
            self._validate_stage_goal_contract(stage, tolerance_ms)
        except BaseException:
            self.song_events_per_episode = previous_song_events
            raise
        changed = (
            stage != self.curriculum_stage
            or abs(tolerance_ms - self.timing_tolerance_ms) > 1e-9
            or abs(tempo_lambda - self.tempo_lambda) > 1e-9
            or strum_span != self.strum_span
            or s2_profile_name != self.s2_profile_name
            or (s2_endpoint_recovery_active
                != self.s2_endpoint_recovery_active)
            or s2_focus_direction != self.s2_focus_direction
            or abs(s2_focus_fraction - self.s2_focus_fraction) > 1e-9
            or zone_active != self.zone_gate_active
            or abs(timing_reward_core_ms - self.timing_reward_core_ms) > 1e-9
            or abs(duration_reward_core_ms - self.duration_reward_core_ms) > 1e-9
            or abs(approach_lead_s - self.approach_lead_s) > 1e-9
            or abs(timing_early_grace_ms - self.timing_early_grace_ms) > 1e-9
            or abs(timing_early_penalty_scale_ms
                   - self.timing_early_penalty_scale_ms) > 1e-9
            or abs(song_f1_gate - self.curriculum_song_f1_gate) > 1e-9
            or song_events_per_episode != previous_song_events
            or stalled != self.curriculum_stalled)
        self.curriculum_stage = str(stage)
        self.timing_tolerance_ms = tolerance_ms
        self.tempo_lambda = tempo_lambda
        self.strum_span = strum_span
        self.s2_profile_name = s2_profile_name
        self.s2_endpoint_recovery_active = s2_endpoint_recovery_active
        self.s2_focus_direction = s2_focus_direction
        self.s2_focus_fraction = s2_focus_fraction
        self.zone_gate_active = zone_active
        self.timing_reward_core_ms = timing_reward_core_ms
        self.duration_reward_core_ms = duration_reward_core_ms
        self.approach_lead_s = approach_lead_s
        self.timing_early_grace_ms = timing_early_grace_ms
        self.timing_early_penalty_scale_ms = timing_early_penalty_scale_ms
        self.curriculum_song_f1_gate = song_f1_gate
        self.curriculum_stalled = stalled
        if failure_context_changed:
            self._event_failure_mass.zero_()
            self._event_failure_exposure.zero_()
            self._event_failure_score.zero_()
            self._hard_window_probability_max = 0.0
            self._upstroke_window_probability_max = 0.0
        self.max_episode_length = self._stage_episode_limit()
        if reset and changed:
            return self.reset()
        return None

    def set_evaluation_mode(self, full_song=True, reset=False):
        changed = (
            self.evaluation_full_song != bool(full_song)
            or (bool(full_song) and self.tempo_lambda != 1.0))
        self.evaluation_full_song = bool(full_song)
        if self.evaluation_full_song:
            self.tempo_lambda = 1.0
            self._event_times = self.goals.runtime_time(1.0)
            self._event_left_tolerance, self._event_right_tolerance = (
                self.goals.runtime_windows(1.0, self.timing_tolerance_ms))
            self._gap_diagnostics = self.goals.gap_diagnostics(
                1.0, self.timing_tolerance_ms)
        self.max_episode_length = self._stage_episode_limit()
        if reset and changed:
            return self.reset()
        return None

    def set_diagnostic_event_window(
            self, start_event_index, event_count, *, tempo_lambda):
        """Reset into an exact deterministic S3 event window.

        The diagnostic owns neither training evidence nor checkpoint state.  It
        exists to distinguish an isolated target/geometry failure from a
        transition/recovery failure using the same physical task implementation.
        """
        start_event_index = _integer_config(
            "start_event_index", start_event_index, minimum=0)
        event_count = _integer_config("event_count", event_count, minimum=1)
        if start_event_index + event_count > self.goals.num_events:
            raise ValueError("diagnostic Strike event window exceeds the song")
        tempo_lambda = float(tempo_lambda)
        if not math.isfinite(tempo_lambda) or not 0.0 <= tempo_lambda <= 1.0:
            raise ValueError("diagnostic tempo lambda must be in [0, 1]")
        self._forced_start_event_index = start_event_index
        self.failure_mining_updates_enabled = False
        self.evaluation_full_song = False
        self.set_curriculum_stage(
            S3_SONG_INTEGRATION,
            self.timing_tolerance_ms,
            tempo_lambda=tempo_lambda,
            song_events_per_episode=event_count,
            strum_span=self.strum_span,
            s2_profile_name=self.s2_profile_name,
            zone_active=self.zone_gate_active,
            timing_reward_core_ms=self.timing_reward_core_ms,
            duration_reward_core_ms=self.duration_reward_core_ms,
            approach_lead_s=self.approach_lead_s,
            timing_early_grace_ms=self.timing_early_grace_ms,
            timing_early_penalty_scale_ms=(
                self.timing_early_penalty_scale_ms),
            song_f1_gate=self.curriculum_song_f1_gate,
            stalled=False,
            reset=False)
        return self.reset()

    def _stage_episode_limit(self):
        if self.curriculum_stage == S3_SONG_INTEGRATION:
            quota = (
                self.goals.num_events if self.evaluation_full_song
                else self.song_events_per_episode)
            required = minimum_strike_stage_horizon(
                S3_SONG_INTEGRATION,
                self._event_times.detach().cpu().tolist(),
                sim_hz=self.SIM_HZ,
                ready_hold_frames=self.ready_hold_frames,
                recovery_frames=self.recovery_frames,
                rearm_min_frames=self.detector.rearm_min_frames,
                timed_lead_frames=self.timed_lead_frames,
                song_events_per_episode=quota,
                timing_tolerance_ms=self.timing_tolerance_ms) + 2
            return max(
                required,
                self.stage_horizons[S3_SONG_INTEGRATION],
            )
        return self.stage_horizons[self.curriculum_stage]

    def curriculum_state_dict(self):
        return {
            "schema": "tab2body.strike_environment_state.v14",
            "curriculum_stage": self.curriculum_stage,
            "timing_tolerance_ms": float(self.timing_tolerance_ms),
            "tempo_lambda": float(self.tempo_lambda),
            "strum_span": int(self.strum_span),
            "s2_profile_name": self.s2_profile_name,
            "s2_endpoint_recovery_active": bool(
                self.s2_endpoint_recovery_active),
            "s2_focus_direction": self.s2_focus_direction,
            "s2_focus_fraction": float(self.s2_focus_fraction),
            "zone_gate_active": bool(self.zone_gate_active),
            "timing_reward_core_ms": float(self.timing_reward_core_ms),
            "duration_reward_core_ms": float(self.duration_reward_core_ms),
            "approach_lead_s": float(self.approach_lead_s),
            "timing_early_grace_ms": float(self.timing_early_grace_ms),
            "timing_early_penalty_scale_ms": float(
                self.timing_early_penalty_scale_ms),
            "song_f1_gate": float(self.curriculum_song_f1_gate),
            "song_events_per_episode": int(self.song_events_per_episode),
            "evaluation_full_song": bool(self.evaluation_full_song),
            "curriculum_stalled": bool(self.curriculum_stalled),
            "random_start": bool(self.random_start),
            "rng_state": self.rng.get_state(),
            "reset_generation": self._reset_generation.detach().cpu(),
            "event_failure_mass": self._event_failure_mass.detach().cpu(),
            "event_failure_exposure": (
                self._event_failure_exposure.detach().cpu()),
            "event_failure_score": self._event_failure_score.detach().cpu(),
        }

    def load_curriculum_state_dict(self, state):
        if state.get("schema") != "tab2body.strike_environment_state.v14":
            raise ValueError("unsupported strike environment checkpoint state")
        if bool(state.get("random_start")) != self.random_start:
            raise ValueError("strike random_start changed across checkpoint resume")
        self.curriculum_stage = str(state["curriculum_stage"])
        if self.curriculum_stage not in STAGES:
            raise ValueError("checkpoint contains an unknown strike stage")
        self.timing_tolerance_ms = float(state["timing_tolerance_ms"])
        if (not math.isfinite(self.timing_tolerance_ms)
                or self.timing_tolerance_ms <= 0.0):
            raise ValueError(
                "checkpoint timing tolerance must be finite and positive")
        self.tempo_lambda = float(state["tempo_lambda"])
        if not math.isfinite(self.tempo_lambda) or not 0.0 <= self.tempo_lambda <= 1.0:
            raise ValueError("checkpoint tempo lambda must be in [0, 1]")
        self.strum_span = int(state["strum_span"])
        if not 1 <= self.strum_span <= N_GUITAR_STRINGS:
            raise ValueError("checkpoint strum span must be in [1, 6]")
        self.song_events_per_episode = _integer_config(
            "checkpoint song_events_per_episode",
            state.get(
                "song_events_per_episode", self.base_song_events_per_episode),
            minimum=1)
        if self.song_events_per_episode > self.goals.num_events:
            raise ValueError(
                "checkpoint song-event quota exceeds the current goal")
        self.s2_profile_name = str(state["s2_profile_name"])
        saved_endpoint_active = state["s2_endpoint_recovery_active"]
        if not isinstance(saved_endpoint_active, bool):
            raise TypeError(
                "checkpoint endpoint recovery state must be bool")
        self.s2_endpoint_recovery_active = saved_endpoint_active
        self.s2_focus_direction = state["s2_focus_direction"]
        self.s2_focus_fraction = float(state["s2_focus_fraction"])
        self.zone_gate_active = bool(state["zone_gate_active"])
        self.timing_reward_core_ms = float(state["timing_reward_core_ms"])
        self.duration_reward_core_ms = float(state["duration_reward_core_ms"])
        self.approach_lead_s = float(state["approach_lead_s"])
        self.timing_early_grace_ms = float(state[
            "timing_early_grace_ms"])
        self.timing_early_penalty_scale_ms = float(state[
            "timing_early_penalty_scale_ms"])
        self.curriculum_song_f1_gate = float(state["song_f1_gate"])
        if (not self.s2_profile_name
                or self.s2_profile_name not in {
                    str(profile["name"])
                    for profile in self.curriculum_s2_profiles}
                or self.s2_focus_direction
                not in ("balanced", "down", "up")
                or not math.isfinite(self.s2_focus_fraction)
                or not 0.5 <= self.s2_focus_fraction <= 0.7
                or self.s2_focus_fraction
                > self.s2_endpoint_focus_fraction_config + 1e-9
                or (self.s2_endpoint_recovery_active
                    and (self.curriculum_stage != S2_TIMED_STRUM
                         or self.s2_focus_direction
                         not in ("down", "up")))
                or (not self.s2_endpoint_recovery_active
                    and (self.s2_focus_direction != "balanced"
                         or abs(self.s2_focus_fraction - 0.5) > 1e-9))
                or not math.isfinite(self.timing_reward_core_ms)
                or not math.isfinite(self.duration_reward_core_ms)
                or self.timing_reward_core_ms <= 0.0
                or self.duration_reward_core_ms <= 0.0
                or not math.isfinite(self.approach_lead_s)
                or self.approach_lead_s <= 0.0
                or not math.isfinite(self.timing_early_grace_ms)
                or self.timing_early_grace_ms < 0.0
                or self.timing_early_grace_ms > self.timing_tolerance_ms
                or not math.isfinite(self.timing_early_penalty_scale_ms)
                or self.timing_early_penalty_scale_ms <= 0.0
                or not math.isfinite(self.curriculum_song_f1_gate)
                or not 0.0 <= self.curriculum_song_f1_gate <= 1.0):
            raise ValueError("checkpoint S2 profile state is invalid")
        self._event_times = self.goals.runtime_time(self.tempo_lambda)
        self._event_left_tolerance, self._event_right_tolerance = (
            self.goals.runtime_windows(
                self.tempo_lambda, self.timing_tolerance_ms))
        self._gap_diagnostics = self.goals.gap_diagnostics(
            self.tempo_lambda, self.timing_tolerance_ms)
        self._validate_stage_goal_contract(
            self.curriculum_stage, self.timing_tolerance_ms)
        self.evaluation_full_song = bool(state.get("evaluation_full_song", False))
        self.curriculum_stalled = bool(
            state.get("curriculum_stalled", False))
        self.max_episode_length = self._stage_episode_limit()
        rng_state = state["rng_state"]
        if (not isinstance(rng_state, torch.Tensor)
                or rng_state.dtype != torch.uint8
                or rng_state.ndim != 1):
            raise ValueError(
                "checkpoint RNG state must be a one-dimensional ByteTensor")



        self.rng.set_state(rng_state.detach().cpu())
        generation = state["reset_generation"].to(
            device=self.device, dtype=torch.long)
        if generation.shape != self._reset_generation.shape:
            raise ValueError("strike reset-generation shape changed")
        self._reset_generation.copy_(generation)
        failure_mass = state["event_failure_mass"].to(
            device=self.device, dtype=self._event_failure_mass.dtype)
        failure_exposure = state["event_failure_exposure"].to(
            device=self.device, dtype=self._event_failure_exposure.dtype)
        failure_score = state["event_failure_score"].to(
            device=self.device, dtype=self._event_failure_score.dtype)
        if (failure_mass.shape != self._event_failure_mass.shape
                or failure_exposure.shape
                != self._event_failure_exposure.shape
                or failure_score.shape != self._event_failure_score.shape):
            raise ValueError("strike event-failure statistic shape changed")
        if (not torch.isfinite(failure_mass).all()
                or not torch.isfinite(failure_exposure).all()
                or not torch.isfinite(failure_score).all()
                or bool((failure_mass < 0.0).any())
                or bool((failure_exposure < 0.0).any())
                or bool((failure_mass > failure_exposure + 1e-6).any())
                or bool((failure_score < 0.0).any())
                or bool((failure_score > 1.0).any())):
            raise ValueError("strike event-failure statistics are invalid")
        global_rate = (
            failure_mass.sum() / failure_exposure.sum().clamp_min(1.0))
        expected_score = (
            (failure_mass
             + self.stalled_failure_prior_exposure * global_rate)
            / (failure_exposure
               + self.stalled_failure_prior_exposure).clamp_min(1e-8))
        expected_score = torch.where(
            failure_exposure > 0.0,
            expected_score.clamp(0.0, 1.0),
            torch.zeros_like(expected_score))
        if not torch.allclose(
                failure_score, expected_score, atol=1e-6, rtol=1e-5):
            raise ValueError(
                "strike event-failure score does not match mass/exposure")
        self._event_failure_mass.copy_(failure_mass)
        self._event_failure_exposure.copy_(failure_exposure)
        self._event_failure_score.copy_(failure_score)
        return self.reset()




    def apply_actions(self, actions):
        actions = constrain_pick_grip_actions(
            actions,
            self._grip_reference_action,
            self._grip_residual_action_span,
            self._action_is_hand)
        if self.curriculum_stage == A0_PICK_GRIP:
            actions = torch.where(
                self._action_is_hand[None], actions, self.grip_hold_action)
        super().apply_actions(actions)

    def policy_action_std_floor(self):
        if (self.curriculum_stage != S2_TIMED_STRUM
                or self.s2_profile_name
                not in self.s2_endpoint_std_floor_profiles):
            return None
        floor = torch.full(
            (self.num_actions,), 1e-6,
            dtype=torch.float32, device=self.device)
        proximal_indices = torch.as_tensor(
            self.action_saturation_regularization_indices,
            dtype=torch.long, device=self.device)
        floor[proximal_indices] = self.s2_endpoint_proximal_std_floor
        return floor

    def reset_idx(self, env_ids):
        env_ids = torch.as_tensor(
            env_ids, dtype=torch.long, device=self.device).reshape(-1)
        super().reset_idx(env_ids)
        if hasattr(self, "_settled_reset_q") and env_ids.numel() > 0:
            ds = self.dof_state.view(self.num_envs, self.n_dof, 2)
            ds[env_ids, :, 0] = self._settled_reset_q[env_ids]
            ds[env_ids, :, 1] = 0.0
            self.gym.set_dof_state_tensor(
                self.sim, gymtorch.unwrap_tensor(self.dof_state))
            self.pd_target.view(self.num_envs, self.n_dof)[env_ids] = (
                self._settled_reset_q[env_ids])
            self.prev_action[env_ids] = self.actions_for_pd_targets(
                self._settled_reset_q[env_ids][:, self.ctrl_idx], env_ids)
        if hasattr(self, "event_index"):
            self._reset_task_state(env_ids)
            if hasattr(self, "_settled_reset_tip_g"):
                self._previous_tip_g[env_ids] = self._settled_reset_tip_g[env_ids]
                self._previous_tip_valid[env_ids] = True

    def reset(self):
        obs = super().reset()
        ds = self.dof_state.view(self.num_envs, self.n_dof, 2)
        ds[:, :, 1] = 0.0
        self.gym.set_dof_state_tensor(
            self.sim, gymtorch.unwrap_tensor(self.dof_state))
        self.pd_target.view(self.num_envs, self.n_dof)[:] = ds[:, :, 0]
        self.prev_action.copy_(self.actions_for_pd_targets(
            ds[:, self.ctrl_idx, 0]))
        self._settled_reset_q = ds[:, :, 0].detach().clone()
        tip = self.to_guitar_frame(self.hbody_pos("RH:pick")[:, None])[:, 0]
        self._settled_reset_tip_g = tip.detach().clone()
        self._previous_tip_g.copy_(tip)
        self._previous_tip_valid.fill_(True)
        self._tip_velocity_g.zero_()
        obs = self.compute_observations()
        if self.observation_contract == STRIKE_V1_OBSERVATION_CONTRACT:
            body_start = 2 * self.n_nonlocked
            self._settled_reset_body_obs = obs[
                :, body_start:self.base_obs_dim].detach().clone()
            obs[:, body_start:self.base_obs_dim] = self._settled_reset_body_obs
        else:
            reset_blocks = self._build_strike_v2_blocks(tip_override=tip)
            reset_blocks["O_arm_anchor"][:, 9:15] = 0.0
            reset_blocks["O_hand_geometry"][:, 9:15] = 0.0
            reset_blocks["O_hand_geometry"][:, 24:30] = 0.0
            self._settled_reset_v2_blocks = {
                name: reset_blocks[name].detach().clone()
                for name in (
                    "O_arm_anchor", "O_hand_geometry", "O_grip_safety")
            }
            for name, settled in self._settled_reset_v2_blocks.items():
                obs[:, STRIKE_V2_BLOCK_SLICES[name]] = settled
        self.obs_buf.copy_(obs)
        return obs

    def _build_base_obs_manifest(self):
        names = []
        for kind in ("position", "velocity"):
            names.extend(
                f"proprio.{kind}.{self.dof_names[index]}"
                for index in self.nonlocked_idx.detach().cpu().tolist())
        for body in self.obs_body_names:
            names.extend(f"body_g.{body}.{axis}" for axis in _AXES)
        return names

    def set_synchronizer_command(self, release_enable, timing_offset_s):
        """Set the compact timing-supervisor command exposed to Strike-v2.

        Raw Fret readiness is intentionally not accepted here.  A future Full
        environment must reduce it to these two stable interface fields.
        """
        release = torch.as_tensor(
            release_enable, device=self.device, dtype=torch.bool)
        offset = torch.as_tensor(
            timing_offset_s, device=self.device,
            dtype=self._synchronizer_timing_offset_s.dtype)
        expected = (self.num_envs,)
        if release.shape != expected or offset.shape != expected:
            raise ValueError(
                "Synchronizer command fields must both have shape "
                f"{expected}")
        if not torch.isfinite(offset).all():
            raise ValueError("Synchronizer timing offset must be finite")
        self._synchronizer_release_enable.copy_(release)
        self._synchronizer_timing_offset_s.copy_(offset.clamp(-1.0, 1.0))

    def _strike_v2_lookahead(self, offset):
        if self.curriculum_stage != S3_SONG_INTEGRATION:
            return torch.zeros(self.num_envs, 26, device=self.device)
        index = self.event_index + int(offset)
        valid = index < self.goals.num_events
        safe = index.clamp(0, self.goals.num_events - 1)
        dtype = self.song_time_s.dtype
        delta = (self._event_times[safe] - self.song_time_s).clamp(-1.0, 2.0)
        delta = torch.where(valid, delta, torch.zeros_like(delta))
        gesture = _one_hot(self.goals.gesture[safe], 3, dtype=dtype)
        traversal = self.goals.traversal_mask[safe].to(dtype)
        audible = self.goals.audible_mask[safe].to(dtype)
        direction = torch.stack([
            self.goals.direction[safe] == DIRECTION_DOWN,
            self.goals.direction[safe] == DIRECTION_UP,
        ], dim=-1).to(dtype)
        offsets = self.goals.traversal_offset[safe].to(dtype)
        sweep = self.goals.sweep_duration[safe].to(dtype)
        mask = valid[:, None].to(dtype)
        return torch.cat([
            valid[:, None].to(dtype),
            delta[:, None],
            gesture * mask,
            traversal * mask,
            audible * mask,
            direction * mask,
            offsets * mask,
            sweep[:, None] * mask,
        ], dim=-1)

    def _strike_v2_physical_blocks(self):
        ds = self.dof_state.view(self.num_envs, self.n_dof, 2)
        proprio = torch.cat([
            ds[:, self.ctrl_idx, 0], ds[:, self.ctrl_idx, 1]], dim=-1)

        thorax = self.body_pose_twist_in_guitar_frame("R_Thorax")
        thorax_state = self.hbody_state("R_Thorax")
        gravity_world = torch.zeros(
            self.num_envs, 3, dtype=proprio.dtype, device=self.device)
        gravity_world[:, 2] = -1.0
        projected_gravity = quat_rotate_inverse(
            thorax_state[:, 3:7], gravity_world)
        arm_anchor = torch.cat([
            thorax["position_g"], thorax["rotation6d_g"],
            thorax["linear_velocity_g"], thorax["angular_velocity_g"],
            projected_gravity,
        ], dim=-1)

        hand_parts = []
        for body_name in ("RH:palm", "RH:pick"):
            state = self.body_pose_twist_in_guitar_frame(body_name)
            hand_parts += [
                state["position_g"], state["rotation6d_g"],
                state["linear_velocity_g"], state["angular_velocity_g"],
            ]
        hand_geometry = torch.cat(hand_parts, dim=-1)

        grip = self.grip_reference.measure(ds[:, :, 0])
        depth = self.penetration_monitor.current_depth_by_chain()
        grouped_depth = torch.stack([
            depth[:, 0],
            depth[:, 1],
            depth[:, 2],
            depth[:, 3:6].amax(dim=-1),
        ], dim=-1)
        penetration_margin = (
            (self.penetration_monitor.threshold - grouped_depth)
            / self.penetration_monitor.threshold).clamp(-1.0, 1.0)
        grip_safety = torch.cat([
            grip["grip_quality"][:, None],
            grip["grip_pinch_quality"][:, None],
            grip["grip_free_quality"][:, None],
            penetration_margin,
        ], dim=-1)
        return {
            "O_proprio": proprio,
            "O_arm_anchor": arm_anchor,
            "O_hand_geometry": hand_geometry,
            "O_grip_safety": grip_safety,
        }

    def _build_strike_v2_blocks(self, tip_override=None):
        blocks = self._strike_v2_physical_blocks()
        dtype = self.song_time_s.dtype
        tip = (tip_override if tip_override is not None else
               self.body_pose_twist_in_guitar_frame("RH:pick")["position_g"])
        (target_string, motion_lane_y, _center, ready, entry, exit_point,
         _final_string_point) = self._current_target_geometry()
        target_masks = self._current_target_masks()
        target_offsets = self._current_target_offsets().to(dtype)
        target_direction = self._current_target_direction()
        motion_direction = self._current_motion_context()["target_direction"]
        event_index = self.event_index.clamp(0, self.goals.num_events - 1)

        if self.curriculum_stage in STRUM_STAGES:
            audible = self.goals.audible_mask[event_index].to(dtype)
            if self.curriculum_stage in STRUM_ONLY_STAGES:
                audible = audible * target_masks.to(dtype)
            gesture = _one_hot(self.goals.gesture[event_index], 3, dtype=dtype)
        else:
            audible = target_masks.to(dtype)
            gesture = torch.zeros(self.num_envs, 3, device=self.device)
            gesture[:, 0] = 1.0

        left_tolerance, right_tolerance = self._current_timing_tolerances()
        target_time = self._effective_target_time()
        target_offset_min = torch.where(
            target_masks, target_offsets,
            torch.full_like(target_offsets, float("inf"))).amin(dim=1)
        target_offset_max = torch.where(
            target_masks, target_offsets,
            torch.full_like(target_offsets, float("-inf"))).amax(dim=1)
        timed = self.curriculum_stage in TIMED_STAGES
        if timed:
            time_to = (target_time - self.song_time_s).clamp(-1.0, 2.0)
            window_open = (
                target_time + target_offset_min - left_tolerance
                - self.song_time_s).clamp(-1.0, 2.0)
            window_close = (
                target_time + target_offset_max + right_tolerance
                - self.song_time_s).clamp(-1.0, 2.0)
        else:
            time_to = torch.zeros(self.num_envs, device=self.device)
            window_open = torch.zeros_like(time_to)
            window_close = torch.zeros_like(time_to)

        musical_direction = torch.stack([
            target_direction == DIRECTION_DOWN,
            target_direction == DIRECTION_UP,
        ], dim=-1).to(dtype)
        motor_direction = torch.stack([
            motion_direction == DIRECTION_DOWN,
            motion_direction == DIRECTION_UP,
        ], dim=-1).to(dtype)
        event_valid = (~self._timeline_finished).to(dtype)
        blocks["O_current_event"] = torch.cat([
            event_valid[:, None], gesture,
            target_masks.to(dtype), audible, target_offsets,
            musical_direction, motor_direction,
            self._current_target_sweep_duration().to(dtype)[:, None],
            time_to[:, None], window_open[:, None], window_close[:, None],
            torch.full(
                (self.num_envs, 1), self.approach_lead_s,
                dtype=dtype, device=self.device),
            torch.full(
                (self.num_envs, 1), self.tempo_lambda,
                dtype=dtype, device=self.device),
        ], dim=-1)

        remaining = target_masks & ~self._event_release_mask
        string_indices = torch.arange(
            N_GUITAR_STRINGS, device=self.device)[None]
        down_next = torch.where(
            remaining, string_indices,
            torch.full_like(string_indices, -1)).amax(dim=1)
        up_next = torch.where(
            remaining, string_indices,
            torch.full_like(string_indices, N_GUITAR_STRINGS)).amin(dim=1)
        next_string = torch.where(
            target_direction == DIRECTION_DOWN, down_next, up_next)
        phase_target = torch.where(
            (self.motor_phase == PHASE_READY)[:, None], ready,
            torch.where(
                (self.motor_phase == PHASE_APPROACH)[:, None],
                entry, exit_point))
        blocks["O_target_geometry"] = torch.cat([
            ready - tip, entry - tip, exit_point - tip, phase_target - tip,
            (tip[:, 1] - motion_lane_y)[:, None],
            _one_hot(target_string, N_GUITAR_STRINGS, dtype=dtype),
            _one_hot(next_string, N_GUITAR_STRINGS, dtype=dtype),
        ], dim=-1)

        blocks["O_lookahead"] = torch.cat([
            self._strike_v2_lookahead(1),
            self._strike_v2_lookahead(2),
        ], dim=-1)

        detector_armed = (
            self.detector.state == DETECTOR_ARMED).to(dtype)
        rearm_progress = (
            self.detector.wait_frames.to(dtype)
            / float(self.detector.rearm_min_frames)).clamp(0.0, 1.0)
        blocks["O_phase_detector"] = torch.cat([
            _one_hot(self.motor_phase, N_PHASES, dtype=dtype),
            (self.ready_streak.to(dtype)
             / float(self.ready_hold_frames)).clamp(0.0, 1.0)[:, None],
            self.event_resolved.to(dtype)[:, None],
            (self._event_release_mask & target_masks).to(dtype),
            detector_armed, rearm_progress,
            self._last_release.to(dtype),
        ], dim=-1)

        recovery_valid = self._recovery_context_valid
        denominator = self._recovery_required_frames.clamp_min(1).to(dtype)
        recovery_progress = (
            self.recovery_count.to(dtype) / denominator).clamp(0.0, 1.0)
        base_recovery_frames = float(max(self.recovery_frames, 1))
        mode = torch.stack([
            recovery_valid & ~self._recovery_handoff,
            recovery_valid & self._recovery_handoff,
            recovery_valid & self._recovery_same_string_handoff,
        ], dim=-1).to(dtype)
        recovery_lane, recovery_normal = self._string_lane_geometry()
        _release_lift, next_entry = self._recovery_clearance_points(
            recovery_lane, recovery_normal, self.string_segments_g())
        recovery_mask = recovery_valid[:, None].to(dtype)
        recovery_direction = torch.stack([
            self._recovery_direction == DIRECTION_DOWN,
            self._recovery_direction == DIRECTION_UP,
        ], dim=-1).to(dtype) * recovery_mask
        blocks["O_recovery"] = torch.cat([
            recovery_valid.to(dtype)[:, None], mode,
            recovery_progress[:, None] * recovery_mask,
            (self._recovery_required_frames.to(dtype)
             / base_recovery_frames).clamp(0.0, 2.0)[:, None]
            * recovery_mask,
            (self._recovery_available_frames.to(dtype)
             / base_recovery_frames).clamp(0.0, 2.0)[:, None]
            * recovery_mask,
            torch.stack([
                self._recovery_clearance_required,
                self._recovery_clearance_lifted,
                self._recovery_clearance_reached,
            ], dim=-1).to(dtype) * recovery_mask,
            (exit_point - tip) * recovery_mask,
            (next_entry - tip) * recovery_mask,
            recovery_direction,
        ], dim=-1)

        blocks["O_synchronizer"] = torch.stack([
            self._synchronizer_release_enable.to(dtype),
            self._synchronizer_timing_offset_s,
        ], dim=-1)
        blocks["O_history"] = self.prev_action
        return blocks

    def _build_strike_v2_observation(self, tip_override=None):
        blocks = self._build_strike_v2_blocks(tip_override=tip_override)
        observation = pack_strike_v2_blocks(
            blocks, validate_finite=False)
        self.last_nonfinite_observation |= self.rows_with_nonfinite(observation)
        return self.sanitize_finite(observation)

    def _build_strike_obs_manifest(self):
        names = [
            "strike.skill.grip_focus",
            "strike.skill.ready_required",
            "strike.skill.crossing_required",
            "strike.skill.strum_required",
            "strike.skill.timing_required",
            "strike.skill.zone_required",
            "strike.skill.target_span_fraction",
            "strike.skill.song_integration",
        ]
        names += [f"strike.tip_g.{axis}" for axis in _AXES]
        names += [f"strike.tip_velocity_g.{axis}" for axis in _AXES]
        names += [
            f"strike.target_string.{index}"
            for index in range(N_GUITAR_STRINGS)
        ]
        names += [
            f"strike.target_traversal.{index}"
            for index in range(N_GUITAR_STRINGS)
        ]
        names += [
            f"strike.target_audible.{index}"
            for index in range(N_GUITAR_STRINGS)
        ]
        names += [
            f"strike.target_offset_s.{index}"
            for index in range(N_GUITAR_STRINGS)
        ]
        names.append("strike.target_sweep_duration_s")
        names += [
            f"strike.completed_traversal.{index}"
            for index in range(N_GUITAR_STRINGS)
        ]
        names += [
            f"strike.next_traversal.{index}"
            for index in range(N_GUITAR_STRINGS)
        ]
        names += [
            "strike.gesture.single_pick",
            "strike.gesture.strum",
            "strike.gesture.alternate_restrike",
            "strike.tempo_lambda",
            "strike.left_tolerance_s",
            "strike.right_tolerance_s",
        ]
        for point in ("ready_vector", "entry_vector", "exit_vector"):
            names += [f"strike.{point}.{axis}" for axis in _AXES]
        names += [f"strike.phase.{index}" for index in range(N_PHASES)]
        names += [
            "strike.time_to_target_s",
            "strike.window_open_delta_s",
            "strike.window_close_delta_s",
            "strike.tolerance_s",
            "strike.lane_offset_m",
            "strike.direction.down",
            "strike.direction.up",
            "strike.recovery_direction.down",
            "strike.recovery_direction.up",
            "strike.musical_direction.down",
            "strike.musical_direction.up",
            "strike.clearance.required",
            "strike.clearance.reached",
        ]
        names += [
            f"strike.detector_armed.{index}"
            for index in range(N_GUITAR_STRINGS)
        ]
        names += [
            f"strike.last_release.{index}"
            for index in range(N_GUITAR_STRINGS)
        ]
        for lookahead in (1, 2):
            names.append(f"strike.lookahead_{lookahead}.delta_s")
            names += [
                f"strike.lookahead_{lookahead}.traversal.{index}"
                for index in range(N_GUITAR_STRINGS)]
            names += [
                f"strike.lookahead_{lookahead}.direction.down",
                f"strike.lookahead_{lookahead}.direction.up",
            ]
            names += [
                f"strike.lookahead_{lookahead}.offset_s.{index}"
                for index in range(N_GUITAR_STRINGS)]
            names.append(
                f"strike.lookahead_{lookahead}.sweep_duration_s")
        return tuple(names)

    def _lookahead_observation(self, offset):
        if self.curriculum_stage != S3_SONG_INTEGRATION:
            return torch.zeros(
                self.num_envs, 16, device=self.device)
        index = self.event_index + int(offset)
        valid = index < self.goals.num_events
        safe = index.clamp(0, self.goals.num_events - 1)
        delta = (self._event_times[safe] - self.song_time_s).clamp(-1.0, 2.0)
        delta = torch.where(valid, delta, torch.zeros_like(delta))
        string = self.goals.traversal_mask[safe].to(self.song_time_s.dtype)
        string = string * valid[:, None]
        direction = torch.stack([
            self.goals.direction[safe] == DIRECTION_DOWN,
            self.goals.direction[safe] == DIRECTION_UP,
        ], dim=-1).to(self.song_time_s.dtype)
        direction = direction * valid[:, None]
        timing_offset = self.goals.traversal_offset[safe] * valid[:, None]
        sweep_duration = self.goals.sweep_duration[safe] * valid
        return torch.cat([
            delta[:, None], string, direction, timing_offset,
            sweep_duration[:, None]], dim=-1)

    def _build_strike_observation(self, tip_override=None, velocity_override=None):
        tip = (tip_override if tip_override is not None else
               self.to_guitar_frame(self.hbody_pos("RH:pick")[:, None])[:, 0])
        velocity = (
            velocity_override if velocity_override is not None
            else self._tip_velocity_g)
        _, motion_lane_y, _, ready, entry, exit_point, _ = (
            self._current_target_geometry())
        target_string = self._current_target_string()
        target_one_hot = _one_hot(
            target_string, N_GUITAR_STRINGS, dtype=tip.dtype)
        target_traversal = self._current_target_masks().to(tip.dtype)
        target_offsets = self._current_target_offsets().to(tip.dtype)
        target_sweep_duration = self._current_target_sweep_duration().to(tip.dtype)
        unit = torch.ones(self.num_envs, device=self.device, dtype=tip.dtype)
        zero = torch.zeros_like(unit)
        skill = torch.stack([
            unit if self.curriculum_stage == A0_PICK_GRIP else zero,
            zero if self.curriculum_stage == A0_PICK_GRIP else unit,
            unit if self.curriculum_stage not in (
                A0_PICK_GRIP, A1_TIP_READY) else zero,
            unit if self.curriculum_stage in STRUM_STAGES else zero,
            unit if self.curriculum_stage in TIMED_STAGES else zero,
            unit if self.zone_gate_active else zero,
            target_traversal.sum(dim=1) / float(N_GUITAR_STRINGS),
            unit if self.curriculum_stage == S3_SONG_INTEGRATION else zero,
        ], dim=-1)
        if self.curriculum_stage in STRUM_STAGES:
            event_index = self.event_index.clamp(0, self.goals.num_events - 1)
            target_audible = self.goals.audible_mask[event_index].to(tip.dtype)
            if self.curriculum_stage in STRUM_ONLY_STAGES:
                target_audible = target_audible * target_traversal
            gesture = _one_hot(
                self.goals.gesture[event_index], 3, dtype=tip.dtype)
            target_direction = self._current_target_direction()
        else:
            target_audible = target_traversal
            gesture = torch.zeros(self.num_envs, 3, device=self.device)
            gesture[:, 0] = 1.0
            target_direction = self._current_target_direction()
        completed_traversal = (
            self._event_release_mask & self._current_target_masks()).to(tip.dtype)
        remaining_traversal = (
            self._current_target_masks() & ~self._event_release_mask)
        string_indices = torch.arange(
            N_GUITAR_STRINGS, device=self.device)[None]
        down_next = torch.where(
            remaining_traversal, string_indices,
            torch.full_like(string_indices, -1)).amax(dim=1)
        up_next = torch.where(
            remaining_traversal, string_indices,
            torch.full_like(string_indices, N_GUITAR_STRINGS)).amin(dim=1)
        next_string = torch.where(
            target_direction == DIRECTION_DOWN, down_next, up_next)
        next_traversal = _one_hot(
            next_string, N_GUITAR_STRINGS, dtype=tip.dtype)
        phase = _one_hot(self.motor_phase, N_PHASES, dtype=tip.dtype)
        target_time = self._effective_target_time()
        target_offset_min = torch.where(
            self._current_target_masks(), self._current_target_offsets(),
            torch.full_like(target_offsets, float("inf"))).amin(dim=1)
        target_offset_max = torch.where(
            self._current_target_masks(), self._current_target_offsets(),
            torch.full_like(target_offsets, float("-inf"))).amax(dim=1)
        timed = self.curriculum_stage in TIMED_STAGES
        left_tolerance, right_tolerance = self._current_timing_tolerances()
        if timed:
            time_to = (target_time - self.song_time_s).clamp(-1.0, 2.0)
            window_open = (
                target_time + target_offset_min
                - left_tolerance - self.song_time_s).clamp(-1.0, 2.0)
            window_close = (
                target_time + target_offset_max
                + right_tolerance - self.song_time_s).clamp(-1.0, 2.0)
            tolerance = torch.maximum(left_tolerance, right_tolerance)
        else:
            time_to = torch.zeros(self.num_envs, device=self.device)
            window_open = torch.zeros_like(time_to)
            window_close = torch.zeros_like(time_to)
            tolerance = torch.zeros_like(time_to)
        lane_offset = tip[:, 1] - motion_lane_y
        motion_direction = self._current_motion_context()[
            "target_direction"]
        direction = torch.stack([
            motion_direction == DIRECTION_DOWN,
            motion_direction == DIRECTION_UP,
        ], dim=-1).to(tip.dtype)
        recovery_direction = torch.stack([
            self._recovery_direction == DIRECTION_DOWN,
            self._recovery_direction == DIRECTION_UP,
        ], dim=-1).to(tip.dtype)
        recovery_direction *= self._recovery_context_valid[:, None].to(
            tip.dtype)
        musical_direction = torch.stack([
            target_direction == DIRECTION_DOWN,
            target_direction == DIRECTION_UP,
        ], dim=-1).to(tip.dtype)
        clearance_state = torch.stack([
            self._recovery_clearance_required,
            self._recovery_clearance_reached,
        ], dim=-1).to(tip.dtype)
        clearance_state *= self._recovery_context_valid[:, None].to(
            tip.dtype)
        detector_armed = (
            self.detector.state == DETECTOR_ARMED).to(tip.dtype)
        observation = torch.cat([
            skill,
            tip,
            velocity,
            target_one_hot,
            target_traversal,
            target_audible,
            target_offsets,
            target_sweep_duration[:, None],
            completed_traversal,
            next_traversal,
            gesture,
            torch.full(
                (self.num_envs, 1), self.tempo_lambda,
                device=self.device, dtype=tip.dtype),
            left_tolerance[:, None] if timed else torch.zeros_like(time_to[:, None]),
            right_tolerance[:, None] if timed else torch.zeros_like(time_to[:, None]),
            ready - tip,
            entry - tip,
            exit_point - tip,
            phase,
            time_to[:, None],
            window_open[:, None],
            window_close[:, None],
            tolerance[:, None],
            lane_offset[:, None],
            direction,
            recovery_direction,
            musical_direction,
            clearance_state,
            detector_armed,
            self._last_release.to(tip.dtype),
            self._lookahead_observation(1),
            self._lookahead_observation(2),
        ], dim=-1)
        if observation.shape[1] != self.strike_obs_dim:
            raise RuntimeError("strike goal observation changed shape")
        return self.sanitize_finite(observation)

    def compute_observations(self):
        if self.observation_contract == STRIKE_V2_OBSERVATION_CONTRACT:
            obs = self._build_strike_v2_observation()
            self.obs_buf.copy_(obs)
            return obs
        base = super().compute_observations()
        strike = self._build_strike_observation()
        obs = torch.cat([base, strike, self.prev_action], dim=-1)
        self.last_nonfinite_observation |= self.rows_with_nonfinite(obs)
        obs = self.sanitize_finite(obs)
        self.obs_buf.copy_(obs)
        return obs

    def _compose_reset_observation(self, terminal_obs, env_ids):
        if env_ids.numel() == 0:
            return terminal_obs
        if self.observation_contract == STRIKE_V2_OBSERVATION_CONTRACT:
            if not hasattr(self, "_settled_reset_v2_blocks"):
                raise RuntimeError(
                    "StrikeTask.reset() must precede automatic partial reset")
            tip = self.to_guitar_frame(
                self.hbody_pos("RH:pick")[:, None])[:, 0]
            tip[env_ids] = self._settled_reset_tip_g[env_ids]
            reset_obs = self._build_strike_v2_observation(
                tip_override=tip)
            for name, settled in self._settled_reset_v2_blocks.items():
                block_slice = STRIKE_V2_BLOCK_SLICES[name]
                reset_obs[env_ids, block_slice] = settled[env_ids]
            self.obs_buf.copy_(reset_obs)
            return reset_obs
        if not hasattr(self, "_settled_reset_body_obs"):
            raise RuntimeError(
                "StrikeTask.reset() must precede automatic partial reset")
        reset_obs = self.compute_observations()
        body_start = 2 * self.n_nonlocked
        reset_obs[env_ids, body_start:self.base_obs_dim] = (
            self._settled_reset_body_obs[env_ids])
        tip = self.to_guitar_frame(self.hbody_pos("RH:pick")[:, None])[:, 0]
        velocity = self._tip_velocity_g.clone()
        tip[env_ids] = self._settled_reset_tip_g[env_ids]
        velocity[env_ids] = 0.0
        strike = self._build_strike_observation(
            tip_override=tip, velocity_override=velocity)
        strike_start = self.base_obs_dim
        reset_obs[env_ids, strike_start:(
            strike_start + self.strike_obs_dim)] = strike[env_ids]
        self.obs_buf.copy_(reset_obs)
        return reset_obs




    def _record_timing(self, hit, timing_error_s):
        ids = torch.nonzero(hit).squeeze(-1)
        if ids.numel() == 0:
            return
        slots = self._timing_count[ids].clamp_max(self._timing_capacity - 1)
        self._timing_abs_ms[ids, slots] = (
            timing_error_s[ids].abs() * 1000.0)
        self._timing_signed_ms[ids, slots] = timing_error_s[ids] * 1000.0
        self._timing_count[ids] = (
            self._timing_count[ids] + 1).clamp_max(self._timing_capacity)

    def _record_strum_microtiming(
            self, sample, rms_error_s, duration_error_s):
        ids = torch.nonzero(sample).squeeze(-1)
        if ids.numel() == 0:
            return
        slots = self._strum_microtiming_count[ids].clamp_max(
            self._timing_capacity - 1)
        self._strum_timing_rms_ms[ids, slots] = (
            rms_error_s[ids].abs() * 1000.0)
        self._strum_duration_error_ms[ids, slots] = (
            duration_error_s[ids].abs() * 1000.0)
        self._strum_microtiming_count[ids] = (
            self._strum_microtiming_count[ids] + 1).clamp_max(
                self._timing_capacity)

    def _episode_metrics(self, done, failure_termination):
        ids = torch.nonzero(done).squeeze(-1)
        if ids.numel() == 0:
            empty = torch.empty(0, device=self.device)
            return {name: empty for name in self.episode_metric_keys}
        eps = 1e-8
        tp = self.metric_tp[ids]
        fp = self.metric_fp[ids]
        fn = self.metric_fn[ids]
        precision = tp / (tp + fp + eps)
        recall = tp / (tp + fn + eps)
        f1 = 2.0 * precision * recall / (precision + recall + eps)
        false_positive_rate = fp / (tp + fp + fn).clamp_min(1.0)
        timing_mae = torch.zeros_like(tp)
        timing_p95 = torch.zeros_like(tp)
        timing_signed_mean = torch.zeros_like(tp)
        timing_signed_p10 = torch.zeros_like(tp)
        timing_signed_p50 = torch.zeros_like(tp)
        timing_signed_p90 = torch.zeros_like(tp)
        strum_timing_rms = torch.zeros_like(tp)
        strum_timing_p95 = torch.zeros_like(tp)
        strum_duration_mae = torch.zeros_like(tp)
        strum_duration_p95 = torch.zeros_like(tp)
        grip_quality_p05 = torch.zeros_like(tp)
        grip_quality_min = torch.zeros_like(tp)
        for output_index, env_id in enumerate(ids.detach().cpu().tolist()):
            grip_count = min(
                int(self.metric_grip_frames[env_id].item()),
                self._timing_capacity)
            if grip_count:
                grip_values = self._grip_quality_samples[
                    env_id, :grip_count]
                grip_quality_p05[output_index] = torch.quantile(
                    grip_values, 0.05)
                grip_quality_min[output_index] = grip_values.min()
            count = int(self._timing_count[env_id].item())
            if count:
                values = self._timing_abs_ms[env_id, :count]
                signed_values = self._timing_signed_ms[env_id, :count]
                timing_mae[output_index] = values.mean()
                timing_p95[output_index] = torch.quantile(values, 0.95)
                timing_signed_mean[output_index] = signed_values.mean()
                timing_signed_p10[output_index] = torch.quantile(
                    signed_values, 0.10)
                timing_signed_p50[output_index] = torch.quantile(
                    signed_values, 0.50)
                timing_signed_p90[output_index] = torch.quantile(
                    signed_values, 0.90)
            strum_count = int(self._strum_microtiming_count[env_id].item())
            if strum_count:
                rms_values = self._strum_timing_rms_ms[
                    env_id, :strum_count]
                duration_values = self._strum_duration_error_ms[
                    env_id, :strum_count]
                strum_timing_rms[output_index] = rms_values.mean()
                strum_timing_p95[output_index] = torch.quantile(
                    rms_values, 0.95)
                strum_duration_mae[output_index] = duration_values.mean()
                strum_duration_p95[output_index] = torch.quantile(
                    duration_values, 0.95)
        grip_rate = (
            self.metric_grip_success_frames[ids]
            / self.metric_grip_frames[ids].clamp_min(1.0))
        grip_frames = self.metric_grip_frames[ids].clamp_min(1.0)
        grip_quality_mean = self.metric_grip_quality_sum[ids] / grip_frames
        grip_pinch_quality_mean = (
            self.metric_grip_pinch_quality_sum[ids] / grip_frames)
        grip_free_quality_mean = (
            self.metric_grip_free_quality_sum[ids] / grip_frames)
        grip_bad_frame_rate = self.metric_grip_bad_frames[ids] / grip_frames
        grip_bad_streak_max = self._grip_bad_streak_max[ids].to(tp.dtype)
        ready_rate = self.metric_ready_success[ids].clamp(0.0, 1.0)
        zone_attempts = self.metric_zone_attempts[ids]
        zone_rate = self.metric_zone_hits[ids] / zone_attempts.clamp_min(1.0)
        zone_quality = (
            self.metric_zone_quality_sum[ids]
            / zone_attempts.clamp_min(1.0))
        raw_zone_attempts = self.metric_raw_zone_attempts[ids]
        raw_zone_rate = (
            self.metric_raw_zone_hits[ids]
            / raw_zone_attempts.clamp_min(1.0))
        raw_zone_quality = (
            self.metric_raw_zone_quality_sum[ids]
            / raw_zone_attempts.clamp_min(1.0))
        timing_events = self.metric_timing_events[ids]
        timing_pass_rate = (
            self.metric_timing_passed[ids]
            / timing_events.clamp_min(1.0))
        timing_early_rate = (
            self.metric_timing_early[ids]
            / timing_events.clamp_min(1.0))
        timing_late_rate = (
            self.metric_timing_late[ids]
            / timing_events.clamp_min(1.0))
        premature_rate = (
            self.metric_premature_release[ids]
            / timing_events.clamp_min(1.0))
        single_tp = self.metric_single_tp[ids]
        single_fp = self.metric_single_fp[ids]
        single_fn = self.metric_single_fn[ids]
        single_precision = single_tp / (single_tp + single_fp + eps)
        single_recall = single_tp / (single_tp + single_fn + eps)
        single_f1 = (
            2.0 * single_precision * single_recall
            / (single_precision + single_recall + eps))
        strum_events = self.metric_strum_events[ids]
        strum_completion = (
            self.metric_strum_completed[ids] / strum_events.clamp_min(1.0))
        strum_traversal_recall = (
            self.metric_strum_traversal_completed[ids]
            / self.metric_strum_traversal_required[ids].clamp_min(1.0))
        strum_attempts = self.metric_strum_release_attempts[ids].clamp_min(1.0)
        strum_order_accuracy = (
            1.0 - self.metric_strum_order_violations[ids] / strum_attempts
        ).clamp(0.0, 1.0)
        strum_direction_accuracy = (
            1.0 - self.metric_strum_direction_violations[ids] / strum_attempts
        ).clamp(0.0, 1.0)
        strum_unplanned_rate = (
            self.metric_strum_unplanned_crossings[ids] / strum_attempts)
        strum_duplicate_rate = (
            self.metric_strum_duplicate_crossings[ids] / strum_attempts)
        blocked_crossings = self.metric_blocked_crossings[ids]
        recovery_events = tp
        recovery_completion = (
            self.metric_recovery_completed[ids]
            / recovery_events.clamp_min(1.0))
        scheduled_recovery_completion = (
            self.metric_scheduled_recovery_completed[ids]
            / recovery_events.clamp_min(1.0))
        scheduled_recovery_events = tp + fn
        end_to_end_recovery_completion = (
            self.metric_scheduled_recovery_completed[ids]
            / scheduled_recovery_events.clamp_min(1.0))
        full_recovery_events = self.metric_full_recovery_events[ids]
        full_recovery_completion = (
            self.metric_full_recovery_completed[ids]
            / full_recovery_events.clamp_min(1.0))
        handoff_recovery_events = self.metric_handoff_recovery_events[ids]
        handoff_recovery_completion = (
            self.metric_handoff_recovery_completed[ids]
            / handoff_recovery_events.clamp_min(1.0))
        handoff_required_frames_mean = (
            self.metric_handoff_required_frames[ids]
            / handoff_recovery_events.clamp_min(1.0))
        recovery_reset_rate = (
            self.metric_recovery_resets[ids]
            / recovery_events.clamp_min(1.0))
        blocked_crossing_rate = (
            blocked_crossings / recovery_events.clamp_min(1.0))
        first_release_frame = torch.where(
            self._first_target_release_frame[ids] >= 0,
            self._first_target_release_frame[ids].to(tp.dtype),
            torch.zeros_like(tp))
        down_events = self.metric_down_events[ids]
        up_events = self.metric_up_events[ids]
        down_completion = (
            self.metric_down_completed[ids] / down_events.clamp_min(1.0))
        up_completion = (
            self.metric_up_completed[ids] / up_events.clamp_min(1.0))
        worst_direction_completion = torch.where(
            (down_events > 0.0) & (up_events > 0.0),
            torch.minimum(down_completion, up_completion),
            torch.where(
                down_events > 0.0,
                down_completion,
                torch.where(
                    up_events > 0.0,
                    up_completion,
                    torch.zeros_like(up_completion))))
        exit_distance_samples = self.metric_strum_exit_distance_samples[ids]
        exit_distance_mean = (
            self.metric_strum_exit_distance_sum[ids]
            / exit_distance_samples.clamp_min(1.0))

        common_grip = (
            (grip_rate >= self.curriculum_grip_gate)
            & (grip_quality_mean
               >= self.curriculum_grip_quality_mean_gate)
            & (grip_quality_p05
               >= self.curriculum_grip_quality_p05_gate)
            & (grip_pinch_quality_mean
               >= self.curriculum_pinch_quality_mean_gate)
            & (grip_free_quality_mean
               >= self.curriculum_free_quality_mean_gate)
            & (grip_bad_frame_rate
               <= self.curriculum_max_grip_bad_frame_rate)
            & (grip_bad_streak_max
               <= self.curriculum_max_grip_bad_streak_frames))
        common_ready = common_grip & (ready_rate >= self.curriculum_ready_gate)
        fixed_clean_recovery = (
            (recovery_events > 0.0)
            & (recovery_completion
               >= self.curriculum_recovery_completion_gate)
            & (recovery_reset_rate
               <= self.curriculum_recovery_reset_gates[
                   self.curriculum_stage])
            & (blocked_crossing_rate
               <= self.curriculum_blocked_crossing_gates[
                   self.curriculum_stage]))
        dual_clean_recovery = (
            (recovery_events > 0.0)
            & (scheduled_recovery_completion
               >= self.curriculum_recovery_completion_gate)
            & ((full_recovery_events <= 0.0)
               | (full_recovery_completion
                  >= self.curriculum_full_recovery_completion_gate))
            & ((handoff_recovery_events <= 0.0)
               | (handoff_recovery_completion
                  >= self.curriculum_handoff_recovery_completion_gate))
            & (recovery_reset_rate
               <= self.curriculum_recovery_reset_gates[
                   self.curriculum_stage])
            & (blocked_crossing_rate
               <= self.curriculum_blocked_crossing_gates[
                   self.curriculum_stage]))
        clean_recovery = (
            dual_clean_recovery
            if self.curriculum_stage == S3_SONG_INTEGRATION
            else fixed_clean_recovery)
        common_crossing = (
            common_ready
            & (recall >= self.curriculum_recall_gate)
            & (false_positive_rate
               <= self.curriculum_wrong_gates[self.curriculum_stage])
            & clean_recovery)
        s2_profile = next(
            profile for profile in self.curriculum_s2_profiles
            if profile["name"] == self.s2_profile_name)
        s2_endpoint_profile_active = (
            self.curriculum_stage == S2_TIMED_STRUM
            and self.s2_profile_name
            == str(self.curriculum_s2_profiles[0]["name"]))
        strum_completion_gate = (
            float(s2_profile["completion_rate"])
            if self.curriculum_stage == S2_TIMED_STRUM
            else self.curriculum_strum_completion_gate)
        strum_gate = (
            (strum_events > 0.0)
            & (strum_completion >= strum_completion_gate)
            & (strum_traversal_recall >= self.curriculum_strum_traversal_gate)
            & (strum_order_accuracy >= self.curriculum_strum_order_gate)
            & (strum_direction_accuracy
               >= self.curriculum_strum_direction_gates[
                   self.curriculum_stage]))
        s2_direction_completion_gate = (
            ((down_events + up_events) > 0.0)
            & (worst_direction_completion
               >= float(s2_profile["worst_direction_completion_rate"])))
        s2_end_to_end_recovery_gate = (
            end_to_end_recovery_completion
            >= float(s2_profile["end_to_end_recovery_rate"]))
        timing_index = min(
            range(len(self.curriculum_timing_tolerances)),
            key=lambda index: abs(
                self.curriculum_timing_tolerances[index]
                - self.timing_tolerance_ms))
        timed_single_gate = self.curriculum_timed_f1_gates[timing_index]
        if self.curriculum_stage == S2_TIMED_STRUM:
            timed_gate = (
                (timing_events > 0.0)
                & (timing_pass_rate >= float(s2_profile["timing_pass_rate"]))
                & (timing_signed_mean.abs() <= float(
                    s2_profile["timing_center_mean_abs_ms"]))
                & (timing_signed_p10 >= -float(
                    s2_profile["timing_center_tail_abs_ms"]))
                & (timing_signed_p90 <= float(
                    s2_profile["timing_center_tail_abs_ms"])))
            if self.zone_gate_active:
                timed_gate &= zone_rate >= float(
                    s2_profile["zone_success_rate"])
        else:
            timed_gate = (
                (timing_p95 <= self.timing_tolerance_ms)
                & (zone_rate >= self.curriculum_zone_gate))
            if self.curriculum_stage == S3_SONG_INTEGRATION:
                final_profile = self.curriculum_s2_profiles[-1]
                timed_gate &= (
                    (timing_signed_mean.abs() <= float(
                        final_profile["timing_center_mean_abs_ms"]))
                    & (timing_signed_p10 >= -float(
                        final_profile["timing_center_tail_abs_ms"]))
                    & (timing_signed_p90 <= float(
                        final_profile["timing_center_tail_abs_ms"])))
        strum_microtiming_gate = (
            (self._strum_microtiming_count[ids] > 0)
            & (strum_timing_rms
               <= (float(s2_profile["timing_rms_ms"])
                   if self.curriculum_stage == S2_TIMED_STRUM
                   else self.curriculum_strum_timing_rms_gate_ms))
            & (strum_duration_mae
               <= (float(s2_profile["duration_mae_ms"])
                   if self.curriculum_stage == S2_TIMED_STRUM
                   else self.curriculum_strum_duration_mae_gate_ms)))

        if self.curriculum_stage == A0_PICK_GRIP:
            recent_frames = torch.minimum(
                self.progress_buf[ids],
                torch.full_like(self.progress_buf[ids],
                                self._grip_history_length))
            recent_success = self._grip_success_history[ids].sum(dim=1)
            curriculum_success = (
                recent_success >= (0.8 * recent_frames.float()).ceil()
            ) & (recent_frames > 0) & common_grip
        elif self.curriculum_stage == A1_TIP_READY:
            curriculum_success = common_ready
        elif self.curriculum_stage == A2_SINGLE_CROSSING:
            curriculum_success = common_crossing
        elif self.curriculum_stage == A3_TIMED_SINGLE:
            curriculum_success = (
                common_crossing
                & (f1 >= timed_single_gate)
                & timed_gate)
        elif self.curriculum_stage in (
                A4_STRUM_CONTEXT_RECOVERY,
                S0_TWO_STRING_STRUM, S1_STRUM_SPAN):
            curriculum_success = common_crossing & strum_gate
        elif self.curriculum_stage == S2_TIMED_STRUM:
            curriculum_success = (
                common_crossing
                & strum_gate
                & s2_direction_completion_gate
                & s2_end_to_end_recovery_gate)
            if not s2_endpoint_profile_active:
                curriculum_success &= timed_gate & strum_microtiming_gate
        else:
            curriculum_success = (
                common_crossing
                & ((strum_events <= 0.0) | strum_gate)
                & timed_gate
                & ((strum_events <= 0.0) | strum_microtiming_gate)
                & (f1 >= self.curriculum_song_f1_gate))
        curriculum_success &= ~failure_termination[ids]
        return {
            "strike_uniform_evidence_eligible": (
                (~self._sampled_hard_window[ids]
                 & ~self._sampled_upstroke_window[ids]
                 & ~self._sampled_s2_focus[ids]).to(tp.dtype)),
            "strike_grip_success_rate": grip_rate,
            "strike_grip_quality_mean": grip_quality_mean,
            "strike_grip_quality_p05": grip_quality_p05,
            "strike_grip_quality_min": grip_quality_min,
            "strike_grip_pinch_quality_mean": grip_pinch_quality_mean,
            "strike_grip_free_quality_mean": grip_free_quality_mean,
            "strike_grip_bad_frame_rate": grip_bad_frame_rate,
            "strike_grip_bad_streak_max_frames": grip_bad_streak_max,
            "strike_grip_frame_count": self.metric_grip_frames[ids],
            "strike_tip_ready_success_rate": ready_rate,
            "strike_precision": precision,
            "strike_release_recall": recall,
            "strike_false_positive_rate": false_positive_rate,
            "strike_episode_f1": f1,
            "strike_true_positive_count": tp,
            "strike_false_positive_count": fp,
            "strike_false_negative_count": fn,
            "strike_wrong_crossing_rate_exceeded": (
                self._wrong_crossing_rate_exceeded[ids].to(tp.dtype)),
            "strike_timing_mae_ms": timing_mae,
            "strike_timing_p95_ms": timing_p95,
            "strike_timing_signed_mean_ms": timing_signed_mean,
            "strike_timing_signed_p10_ms": timing_signed_p10,
            "strike_timing_signed_p50_ms": timing_signed_p50,
            "strike_timing_signed_p90_ms": timing_signed_p90,
            "strike_timing_pass_rate": timing_pass_rate,
            "strike_timing_early_rate": timing_early_rate,
            "strike_timing_late_rate": timing_late_rate,
            "strike_premature_release_rate": premature_rate,
            "strike_timing_event_count": timing_events,
            "strike_zone_success_rate": zone_rate,
            "strike_zone_mean_quality": zone_quality,
            "strike_raw_zone_success_rate": raw_zone_rate,
            "strike_raw_zone_mean_quality": raw_zone_quality,
            "strike_raw_zone_attempt_count": raw_zone_attempts,
            "strike_single_precision": single_precision,
            "strike_single_recall": single_recall,
            "strike_single_f1": single_f1,
            "strike_single_event_count": single_tp + single_fn,
            "strike_strum_completion_rate": strum_completion,
            "strike_strum_traversal_recall": strum_traversal_recall,
            "strike_strum_order_accuracy": strum_order_accuracy,
            "strike_strum_direction_accuracy": strum_direction_accuracy,
            "strike_strum_unplanned_crossing_rate": strum_unplanned_rate,
            "strike_strum_duplicate_crossing_rate": strum_duplicate_rate,
            "strike_blocked_crossing_count": blocked_crossings,
            "strike_blocked_crossing_rate": blocked_crossing_rate,
            "strike_strum_event_count": strum_events,
            "strike_strum_timing_rms_ms": strum_timing_rms,
            "strike_strum_timing_p95_ms": strum_timing_p95,
            "strike_strum_sweep_duration_mae_ms": strum_duration_mae,
            "strike_strum_sweep_duration_p95_ms": strum_duration_p95,
            "strike_strum_microtiming_sample_count": (
                self._strum_microtiming_count[ids].to(tp.dtype)),
            "strike_recovery_completion_rate": recovery_completion,
            "strike_recovery_event_count": recovery_events,
            "strike_scheduled_recovery_completion_rate": (
                scheduled_recovery_completion),
            "strike_conditional_recovery_completion_rate": (
                scheduled_recovery_completion),
            "strike_end_to_end_recovery_completion_rate": (
                end_to_end_recovery_completion),
            "strike_scheduled_recovery_event_count": (
                scheduled_recovery_events),
            "strike_scheduled_recovery_completed_count": (
                self.metric_scheduled_recovery_completed[ids]),
            "strike_full_recovery_completion_rate": (
                full_recovery_completion),
            "strike_full_recovery_event_count": full_recovery_events,
            "strike_full_recovery_completed_count": (
                self.metric_full_recovery_completed[ids]),
            "strike_handoff_recovery_completion_rate": (
                handoff_recovery_completion),
            "strike_handoff_recovery_event_count": handoff_recovery_events,
            "strike_handoff_recovery_completed_count": (
                self.metric_handoff_recovery_completed[ids]),
            "strike_handoff_required_frames_mean": (
                handoff_required_frames_mean),
            "strike_recovery_reset_count": self.metric_recovery_resets[ids],
            "strike_recovery_reset_rate": recovery_reset_rate,
            "strike_first_target_release_frame": first_release_frame,
            "strike_down_completion_rate": down_completion,
            "strike_down_event_count": down_events,
            "strike_down_completed_count": self.metric_down_completed[ids],
            "strike_up_completion_rate": up_completion,
            "strike_up_event_count": up_events,
            "strike_up_completed_count": self.metric_up_completed[ids],
            "strike_worst_direction_completion_rate": (
                worst_direction_completion),
            "strike_final_string_miss_count": (
                self.metric_final_string_miss[ids]),
            "strike_final_remaining_count_at_resolution": (
                self.metric_final_remaining_at_resolution[ids]),
            "strike_strum_exit_distance_mean_m": exit_distance_mean,
            "strike_strum_exit_distance_sample_count": (
                exit_distance_samples),
            "strike_reward_timing_return": (
                self.metric_reward_timing_return[ids]),
            "strike_reward_timing_wait_return": (
                self.metric_reward_timing_wait_return[ids]),
            "strike_reward_strum_progress_return": (
                self.metric_reward_strum_progress_return[ids]),
            "strike_reward_strum_terminal_progress_return": (
                self.metric_reward_strum_terminal_progress_return[ids]),
            "strike_reward_strum_physical_completion_return": (
                self.metric_reward_strum_physical_completion_return[ids]),
            "strike_penalty_premature_release_return": (
                self.metric_penalty_premature_release_return[ids]),
            "strike_penalty_early_timing_return": (
                self.metric_penalty_early_timing_return[ids]),
            "strike_penalty_miss_return": (
                self.metric_penalty_miss_return[ids]),
            "curriculum_success_rate": curriculum_success.float(),
        }





    def step(self, actions):



        action_phase = self.motor_phase.clone()
        self.apply_actions(actions)
        self.step_physics()
        self.refresh()
        self.progress_buf += 1

        base_reasons = self.termination_reasons()
        base_timeout = base_reasons["timeout"]
        nonfinite = torch.zeros(
            self.num_envs, dtype=torch.bool, device=self.device)
        for name, value in base_reasons.items():
            if name.startswith("nonfinite_"):
                nonfinite |= value
        velocity_blowup = base_reasons["velocity_blowup"]
        penetration = self.penetration_monitor.compute(self.progress_buf)

        tip = self.to_guitar_frame(self.hbody_pos("RH:pick")[:, None])[:, 0]
        valid_previous = self._previous_tip_valid.clone()
        previous_tip = self._previous_tip_g.clone()
        delta = tip - self._previous_tip_g
        self._tip_velocity_g.copy_(torch.where(
            valid_previous[:, None], delta * self.SIM_HZ,
            torch.zeros_like(delta)))
        start, end = self.string_segments_g()
        detection = self.detector.step(
            torch.where(
                valid_previous[:, None], self._previous_tip_g, tip),
            tip, start, end, dt=1.0 / self.SIM_HZ)
        release = detection["release"] & valid_previous[:, None]
        supervisor_blocked_release = (
            release
            & ~self._synchronizer_release_enable[:, None])
        release_eligible_for_score = (
            release
            & self._synchronizer_release_enable[:, None])
        release_context = strike_release_recovery_context(
            release,
            detection["subframe_t"],
            detection["crossing_pos_g"],
            detection["direction"])
        physical_release = release_context["released"]
        recovery_release = (
            physical_release
            & (self.curriculum_stage not in (
                A0_PICK_GRIP, A1_TIP_READY)))
        self._previous_tip_g.copy_(tip)
        self._previous_tip_valid.fill_(True)
        self._last_release.copy_(release)

        grip = self.grip_reference.measure(
            self.dof_state.view(self.num_envs, self.n_dof, 2)[:, :, 0])
        grip_slots = self.metric_grip_frames.long().clamp_max(
            self._timing_capacity - 1)
        grip_rows = torch.arange(self.num_envs, device=self.device)
        self._grip_quality_samples[grip_rows, grip_slots] = grip[
            "grip_quality"]
        self.metric_grip_success_frames += grip["grip_success"].float()
        self.metric_grip_frames += 1.0
        self.metric_grip_quality_sum += grip["grip_quality"]
        self.metric_grip_pinch_quality_sum += grip["grip_pinch_quality"]
        self.metric_grip_free_quality_sum += grip["grip_free_quality"]
        grip_bad = grip["grip_quality"] < self.grip_bad_quality_threshold
        self.metric_grip_bad_frames += grip_bad.float()
        self._grip_bad_streak.copy_(torch.where(
            grip_bad, self._grip_bad_streak + 1,
            torch.zeros_like(self._grip_bad_streak)))
        self._grip_bad_streak_max.copy_(torch.maximum(
            self._grip_bad_streak_max, self._grip_bad_streak))
        history_slot = (
            (self.progress_buf - 1) % self._grip_history_length).long()
        self._grip_success_history[grip_rows, history_slot] = grip[
            "grip_success"]

        target_time = self._effective_target_time()
        target_string = self._current_target_string()
        (motion_target_string, _, _, ready, entry, exit_point,
         final_string_point) = self._current_target_geometry()
        target_event_index = self.event_index.clamp(
            0, self.goals.num_events - 1)
        target_columns_before_release = self._current_target_masks()
        target_direction_before_release = self._current_target_direction()
        stage_has_strum_contract = self.curriculum_stage in STRUM_STAGES
        target_is_strum_before_release = (
            torch.full_like(
                self.event_resolved,
                stage_has_strum_contract)
            & (self.goals.gesture[target_event_index] == 1))
        final_string = strike_next_traversal_string(
            target_columns_before_release,
            torch.zeros_like(target_columns_before_release),
            -target_direction_before_release,
            target_string)
        remaining_before_release = (
            target_columns_before_release & ~self._event_release_mask)
        final_string_remaining_before_release = remaining_before_release[
            torch.arange(self.num_envs, device=self.device), final_string]
        terminal_approach_active = (
            target_is_strum_before_release
            & (self.motor_phase == PHASE_APPROACH)
            & ~self.event_resolved
            & final_string_remaining_before_release
            & (remaining_before_release.sum(dim=1) == 1))
        clearance_target_changed = self._update_recovery_clearance(
            tip, exit_point)
        ready_distance = torch.linalg.vector_norm(tip - ready, dim=-1)
        previous_entry_distance = torch.linalg.vector_norm(
            previous_tip - entry, dim=-1)
        at_ready = ready_distance <= self.ready_distance
        ready_state = strike_ready_latch(
            at_ready,
            grip["grip_success"],
            self.ready_streak,
            self.metric_ready_success > 0.0,
            hold_frames=self.ready_hold_frames,
        )
        self.ready_streak.copy_(ready_state["ready_streak"])


        ready_pulse = (
            ready_state["ready_pulse"]
            & (self.curriculum_stage != A0_PICK_GRIP))
        self.metric_ready_success = torch.maximum(
            self.metric_ready_success, ready_pulse.float())
        ready_acquired = self.metric_ready_success > 0.0
        ready_latched = (
            (self.motor_phase == PHASE_READY)
            & (self.ready_streak >= self.ready_hold_frames)
            & (self.curriculum_stage not in (
                A0_PICK_GRIP, A1_TIP_READY)))
        approach_open = torch.ones(
            self.num_envs, dtype=torch.bool, device=self.device)
        time_to_approach_s = torch.zeros(
            self.num_envs, dtype=tip.dtype, device=self.device)
        if self.curriculum_stage in TIMED_STAGES:
            current_mask = self._current_target_masks()
            current_offsets = self._current_target_offsets()
            first_offset = torch.where(
                current_mask, current_offsets,
                torch.full_like(current_offsets, float("inf"))).amin(dim=1)
            approach_context = strike_timed_approach_open(
                self.song_time_s,
                target_time,
                first_offset,
                self.approach_lead_s)
            approach_open = approach_context["approach_open"]
            time_to_approach_s = approach_context["time_to_approach_s"]
            ready_latched &= approach_open
        timing_wait_active = (
            (self.motor_phase == PHASE_READY)
            & ready_acquired
            & ~approach_open)
        self.motor_phase = torch.where(
            ready_latched,
            torch.full_like(self.motor_phase, PHASE_APPROACH),
            self.motor_phase)
        self._target_distance_valid[ready_latched] = False

        phase_target = torch.where(
            (self.motor_phase == PHASE_READY)[:, None], ready,
            torch.where(
                (self.motor_phase == PHASE_APPROACH)[:, None],
                entry, exit_point))
        phase_target = torch.where(
            terminal_approach_active[:, None], exit_point, phase_target)
        target_distance = torch.linalg.vector_norm(tip - phase_target, dim=-1)
        ready_quality = (
            0.4 * torch.exp(-(ready_distance / 0.120) ** 2)
            + 0.6 * torch.exp(-(ready_distance / 0.025) ** 2))
        timing_wait_quality = (
            ready_quality * timing_wait_active.to(tip.dtype))
        reach_potential = torch.exp(
            -target_distance / max(self.ready_distance, 1e-6))
        reach_progress = strike_reach_potential_delta(
            self._previous_reach_potential,
            reach_potential,
            self._target_distance_valid,
            discount=self.reward_fn.reach_discount)
        target_direction_vector = phase_target - tip
        target_unit_vector = (
            target_direction_vector
            / target_distance.clamp_min(1e-6)[:, None])
        target_approach_speed = (
            self._tip_velocity_g * target_unit_vector).sum(dim=-1)
        approach_motion_quality = (
            torch.exp(
                -target_distance / max(2.0 * self.ready_distance, 1e-6))
            * (target_approach_speed / 0.15).clamp(0.0, 1.0)
            * ((self.motor_phase == PHASE_APPROACH)
               & ready_acquired
               & ~self.event_resolved).to(tip.dtype))
        self._previous_reach_potential.copy_(reach_potential)
        self._target_distance_valid.fill_(True)
        self._previous_reach_potential[clearance_target_changed] = 0.0
        self._target_distance_valid[clearance_target_changed] = False
        recovery_was_valid = self._recovery_reward_valid.clone()

        terminal_progress_state = strike_strum_terminal_progress(
            tip,
            final_string_point,
            exit_point,
            self._strum_terminal_progress_best,
            terminal_approach_active)
        strum_terminal_progress = terminal_progress_state["increment"]
        self._strum_terminal_progress_best.copy_(
            terminal_progress_state["best"])

        target_columns = target_columns_before_release
        if self.curriculum_stage in STRUM_STAGES:
            target_gesture = self.goals.gesture[target_event_index]
            target_direction = target_direction_before_release
        else:
            target_gesture = torch.zeros(
                self.num_envs, dtype=torch.long, device=self.device)
            target_direction = target_direction_before_release
        ordered_release = strike_ordered_release_progress(
            self._event_release_mask,
            release_eligible_for_score,
            detection["subframe_t"],
            detection["direction"],
            target_columns,
            target_direction,
        )
        accepted_release = ordered_release["accepted_release"]
        accumulated_release = ordered_release["accumulated_release"]
        required_complete = ordered_release["complete"]
        newly_accepted_count = accepted_release.sum(dim=1).to(tip.dtype)
        traversal_count = target_columns.sum(dim=1).clamp_min(1).to(tip.dtype)
        strum_progress = (
            newly_accepted_count / traversal_count
            * (target_gesture == 1).to(tip.dtype))
        partial_strum_progress = (
            (target_gesture == 1)
            & accepted_release.any(dim=1)
            & ~required_complete)
        self._target_distance_valid[partial_strum_progress] = False
        first_release = accepted_release.any(dim=1) & ~self._event_onset_valid
        masked_subframe = torch.where(
            accepted_release,
            detection["subframe_t"],
            torch.full_like(detection["subframe_t"], float("inf")))
        onset_subframe = masked_subframe.min(dim=1).values
        onset_time = self.song_time_s + onset_subframe / self.SIM_HZ
        self._event_onset_time_s[first_release] = onset_time[first_release]
        self._event_onset_valid |= accepted_release.any(dim=1)
        release_time_all = (
            self.song_time_s[:, None]
            + detection["subframe_t"] / self.SIM_HZ)
        self._event_release_time_s = torch.where(
            accepted_release, release_time_all,
            self._event_release_time_s)
        crossing_y_all = detection["crossing_pos_g"][..., 1]
        lane_allowed_all = (
            detection["zone_allowed"]
            & ((crossing_y_all - self.target_lane_y[:, None]).abs()
               <= self.lane_allowed_half_width))
        release_zone_valid = (
            ~accepted_release | lane_allowed_all).all(dim=1)
        self._event_zone_valid &= release_zone_valid
        release_quality = torch.where(
            accepted_release,
            detection["zone_quality"],
            torch.ones_like(detection["zone_quality"])).min(dim=1).values
        self._event_zone_quality = torch.minimum(
            self._event_zone_quality, release_quality)
        self._event_release_mask.copy_(accumulated_release)
        release_target = required_complete & accepted_release.any(dim=1)
        left_tolerance, right_tolerance = self._current_timing_tolerances()
        traversal_timing = strike_traversal_timing(
            self._event_release_time_s,
            accumulated_release,
            target_columns,
            target_time,
            self._current_target_offsets(),
            left_tolerance,
            right_tolerance,
        )
        timing_error_s = traversal_timing["worst_error_s"]
        timing_ok = traversal_timing["timing_ok"]
        premature_evidence = strike_premature_release(
            accepted_release,
            release_time_all,
            target_time,
            self._current_target_offsets(),
            left_tolerance)
        per_string_signed_error = premature_evidence["signed_error_s"]
        expected_release_time = (
            target_time[:, None] + self._current_target_offsets())
        timing_core_s = self.timing_reward_core_ms / 1000.0
        per_string_timing_quality = strike_rational_timing_quality(
            per_string_signed_error, timing_core_s)
        if self.curriculum_stage not in TIMED_STAGES:
            per_string_timing_quality = torch.ones_like(
                per_string_timing_quality)
        timing_progress_quality = (
            torch.where(
                accepted_release,
                per_string_timing_quality,
                torch.zeros_like(per_string_timing_quality)).sum(dim=1)
            / traversal_count)
        early_timing_per_string = strike_early_timing_cost(
            accepted_release,
            per_string_signed_error,
            grace_s=self.timing_early_grace_ms / 1000.0,
            scale_s=self.timing_early_penalty_scale_ms / 1000.0)
        early_timing_cost = (
            early_timing_per_string.sum(dim=1) / traversal_count)
        if self.curriculum_stage not in TIMED_STAGES:
            early_timing_cost.zero_()
        strum_progress_potential = (
            torch.where(
                accumulated_release & target_columns,
                strike_rational_timing_quality(
                    self._event_release_time_s - expected_release_time,
                    timing_core_s)
                if self.curriculum_stage in TIMED_STAGES
                else torch.ones_like(self._event_release_time_s),
                torch.zeros_like(self._event_release_time_s)).sum(dim=1)
            / traversal_count
            * (target_gesture == 1).to(tip.dtype))
        rows = torch.arange(self.num_envs, device=self.device)
        zone_allowed = self._event_zone_valid
        global_zone_quality = self._event_zone_quality
        crossing_y = self.target_lane_y
        release_phase_violation = (
            physical_release & (action_phase != PHASE_APPROACH))
        entry_ready = (
            valid_previous
            & (previous_entry_distance <= self.entry_distance))

        physical_target_candidate = strike_physical_target_candidate(
            release_target,
            self.event_resolved,
            nonfinite)
        strum_physical_completion_pulse = (
            physical_target_candidate & (target_gesture == 1))
        timing_gate = strike_timing_gate(
            physical_target_candidate,
            timing_ok,
            timing_required=self.curriculum_stage in TIMED_STAGES,
        )
        timing_sample = timing_gate["timing_sample"]
        target_candidate = timing_gate["success_candidate"]
        self._event_timing_valid |= target_candidate
        zone_gate = strike_lane_gate(
            physical_target_candidate,
            zone_allowed,
            crossing_y,
            self.target_lane_y,
            core_half_width=self.lane_core_half_width,
            allowed_half_width=self.lane_allowed_half_width,
        )
        lane_allowed = zone_gate["lane_allowed"]
        lane_quality = zone_gate["lane_quality"]
        zone_attempt = torch.zeros_like(physical_target_candidate)
        zone_hit = torch.zeros_like(physical_target_candidate)
        raw_zone_attempt = (
            accepted_release.any(dim=1)
            & torch.full_like(
                target_candidate,
                self.curriculum_stage in TIMED_STAGES))
        raw_zone_quality = release_quality
        target_hit = target_candidate
        if self.zone_gate_active:
            zone_attempt = physical_target_candidate
            zone_hit = physical_target_candidate & self._event_zone_valid
            target_hit = target_candidate & self._event_zone_valid
            lane_allowed = self._event_zone_valid
            lane_quality = self._event_zone_quality

        release_count = release.sum(dim=1)
        blocked_release_count = detection["blocked_wait_rearm"].sum(dim=1)
        wrong_count = sum(
            ordered_release[name]
            for name in (
                "unplanned_crossing_count",
                "wrong_direction_count",
                "order_violation_count",
                "duplicate_crossing_count",
            )) + blocked_release_count.to(tip.dtype) + (
                supervisor_blocked_release.sum(dim=1).to(tip.dtype))
        miss_pulse = torch.zeros(
            self.num_envs, dtype=torch.bool, device=self.device)
        premature_release = torch.zeros_like(physical_target_candidate)
        late_release = torch.zeros_like(physical_target_candidate)
        if self.curriculum_stage in TIMED_STAGES:
            premature_release = (
                physical_target_candidate & traversal_timing["early"])
            late_release = (
                physical_target_candidate & traversal_timing["late"])
        next_song_time = self.song_time_s + 1.0 / self.SIM_HZ
        if self.curriculum_stage in TIMED_STAGES:
            target_window_end = (
                target_time
                + self._current_target_offsets().amax(dim=1)
                + right_tolerance)
            miss_pulse = (
                ~self.event_resolved
                & ~target_hit
                & (next_song_time > target_window_end))
            miss_pulse |= physical_target_candidate & ~target_hit


        stage_timeout = self.progress_buf >= self.max_episode_length
        ready_resolution = None
        if self.curriculum_stage == A1_TIP_READY:
            ready_resolution = strike_ready_episode_resolution(
                stage_timeout,
                self.metric_ready_success > 0.0)
            miss_pulse |= ready_resolution["miss"]
        elif self.curriculum_stage in (
                A2_SINGLE_CROSSING, A4_STRUM_CONTEXT_RECOVERY,
                S0_TWO_STRING_STRUM,
                S1_STRUM_SPAN):
            miss_pulse |= (
                stage_timeout & ~self.event_resolved & ~target_hit)

        event_outcome = strike_event_outcome_masks(
            physical_target_candidate, target_hit, miss_pulse)
        newly_resolved = event_outcome["newly_resolved"]
        event_had_wrong = (
            self._event_had_wrong_crossing | (wrong_count > 0))
        resolved_with_wrong = (
            newly_resolved
            & event_had_wrong)
        clean_event = ~event_had_wrong
        physical_hit = event_outcome["physical_hit"]
        physical_miss = event_outcome["physical_miss"]
        remaining_at_resolution = (
            target_columns & ~accumulated_release).sum(dim=1)
        final_string_released = accumulated_release[rows, final_string]
        final_string_remaining = (
            (target_gesture == 1) & ~final_string_released)
        strum_progress_shaping = strike_terminal_potential_delta(
            self._previous_strum_progress_potential,
            strum_progress_potential,
            newly_resolved,
            discount=self.reward_fn.reach_discount)
        self._previous_strum_progress_potential.copy_(torch.where(
            newly_resolved,
            torch.zeros_like(strum_progress_potential),
            strum_progress_potential))
        self._strum_terminal_progress_best[newly_resolved] = 0.0
        wrong_termination_active = torch.full(
            (self.num_envs,),
            bool(
                self.wrong_crossing_termination_enabled
                and self.curriculum_stage == S3_SONG_INTEGRATION
                and self.tempo_lambda >= self.wrong_crossing_minimum_tempo),
            dtype=torch.bool, device=self.device)
        wrong_termination_state = update_wrong_crossing_termination(
            self._wrong_crossing_total,
            self._wrong_crossing_consecutive_events,
            self._event_had_wrong_crossing,
            wrong_count,
            newly_resolved,
            self._wrong_crossing_resolved_events,
            wrong_termination_active,
            minimum_resolved_events=self.wrong_crossing_minimum_events,
            max_count=self.wrong_crossing_max_count,
            max_rate=self.wrong_crossing_max_rate,
            consecutive_event_limit=self.wrong_crossing_consecutive_limit,
            terminate_on_rate=self.wrong_crossing_terminate_on_rate,
        )
        self._wrong_crossing_total.copy_(
            wrong_termination_state["total_wrong"])
        self._wrong_crossing_resolved_events.copy_(
            wrong_termination_state["resolved_events"])
        self._wrong_crossing_consecutive_events.copy_(
            wrong_termination_state["consecutive_wrong_events"])
        self._event_had_wrong_crossing.copy_(
            wrong_termination_state["event_had_wrong"])
        self._wrong_crossing_rate_exceeded |= wrong_termination_state[
            "rate_limit_exceeded"]
        wrong_crossing_termination = wrong_termination_state["termination"]
        recovery_release = (
            physical_target_candidate
            & torch.full_like(
                physical_target_candidate,
                self.curriculum_stage not in (
                    A0_PICK_GRIP, A1_TIP_READY)))
        self.metric_tp += physical_hit.float()
        self.metric_fp += wrong_count
        self.metric_fn += physical_miss.float()
        self.metric_zone_attempts += zone_attempt.float()
        self.metric_zone_hits += zone_hit.float()
        self.metric_zone_quality_sum += (
            lane_quality * zone_attempt.float())
        self.metric_raw_zone_attempts += raw_zone_attempt.float()
        self.metric_raw_zone_hits += (
            raw_zone_attempt & release_zone_valid).float()
        self.metric_raw_zone_quality_sum += (
            raw_zone_quality * raw_zone_attempt.float())
        timed_resolved = newly_resolved & torch.full_like(
            newly_resolved, self.curriculum_stage in TIMED_STAGES)
        self.metric_timing_events += timed_resolved.float()
        self.metric_timing_passed += (
            timed_resolved & self._event_timing_valid).float()
        self.metric_timing_early += (
            timed_resolved & premature_release).float()
        self.metric_timing_late += (
            timed_resolved & late_release).float()
        self.metric_premature_release += (
            timed_resolved & premature_release).float()
        is_strum = target_gesture == 1
        is_single = ~is_strum
        strum_timing_sample = timing_sample & is_strum
        self.metric_single_tp += (physical_hit & is_single).float()
        self.metric_single_fn += (physical_miss & is_single).float()
        self.metric_single_fp += wrong_count * is_single.float()
        resolved_strum = newly_resolved & is_strum
        self.metric_strum_events += resolved_strum.float()
        self.metric_strum_completed += (physical_hit & is_strum).float()
        self.metric_strum_traversal_required += (
            target_columns.sum(dim=1).float() * resolved_strum.float())
        self.metric_strum_traversal_completed += (
            accumulated_release.sum(dim=1).float() * resolved_strum.float())
        self.metric_strum_order_violations += (
            ordered_release["order_violation_count"] * is_strum.float())
        self.metric_strum_direction_violations += (
            ordered_release["wrong_direction_count"] * is_strum.float())
        self.metric_strum_unplanned_crossings += (
            ordered_release["unplanned_crossing_count"] * is_strum.float())
        self.metric_strum_duplicate_crossings += (
            ordered_release["duplicate_crossing_count"] * is_strum.float())
        self.metric_strum_release_attempts += (
            release.sum(dim=1).float() * is_strum.float())
        self.metric_final_string_miss += (
            resolved_strum & ~final_string_released).float()
        self.metric_final_remaining_at_resolution += (
            remaining_at_resolution.to(tip.dtype)
            * resolved_strum.float())
        self.metric_strum_exit_distance_sum += (
            terminal_progress_state["exit_distance_m"]
            * resolved_strum.float())
        self.metric_strum_exit_distance_samples += resolved_strum.float()
        self.metric_blocked_crossings += blocked_release_count.to(tip.dtype)
        directional_strum = strike_directional_strum_outcomes(
            newly_resolved, physical_hit, is_strum, target_direction)
        self.metric_down_events += directional_strum["down_event"].float()
        self.metric_up_events += directional_strum["up_event"].float()
        self.metric_down_completed += directional_strum[
            "down_completed"].float()
        self.metric_up_completed += directional_strum[
            "up_completed"].float()



        self._record_timing(timing_sample, timing_error_s)
        self._record_strum_microtiming(
            strum_timing_sample,
            traversal_timing["rms_error_s"],
            traversal_timing["duration_error_s"])
        self.event_resolved |= newly_resolved
        first_target_release = (
            physical_hit & (self._first_target_release_frame < 0))
        self._first_target_release_frame[first_target_release] = (
            self.progress_buf[first_target_release])
        self._recovery_best_count[physical_hit] = 0
        self._recovery_reward_valid[physical_hit] = True
        self._plan_recovery(
            physical_hit,
            release_context["release_string"],
            release_context["release_direction"],
            next_song_time)
        recovery_reset = (
            recovery_was_valid
            & (physical_release | (blocked_release_count > 0)))
        self.metric_recovery_resets += recovery_reset.float()
        self._recovery_best_count[recovery_reset] = 0
        self._scheduled_recovery_best_count[recovery_reset] = 0



        self.recovery_count = strike_completed_recovery_frames(
            action_phase,
            self.recovery_count,
            release_recover_phase=PHASE_RELEASE_RECOVER,
            disruption=recovery_reset)
        self._recovery_target_string[recovery_release] = (
            release_context["release_string"][recovery_release])
        self._recovery_target_lane_y[recovery_release] = (
            release_context["release_lane_y"][recovery_release])
        self._recovery_direction[recovery_release] = (
            release_context["release_direction"][recovery_release])
        self._recovery_context_valid[recovery_release] = True
        self._target_distance_valid[recovery_release] = False
        self.motor_phase = torch.where(
            recovery_release,
            torch.full_like(self.motor_phase, PHASE_RELEASE_RECOVER),
            self.motor_phase)
        self.recovery_count[recovery_release] = 0
        previous_target_lane_y = self.target_lane_y.clone()
        if self.curriculum_stage == S3_SONG_INTEGRATION:
            self._advance_song_events(newly_resolved, recovery_release)
            recovery_rearmed = self._recovery_rearmed()
            final_event_resolved = (
                self.event_resolved
                & ((self.episode_event_count >= self._episode_event_quota)
                   | (self.event_index >= self.goals.num_events - 1)))
            recovery_finished = (
                (self.motor_phase != PHASE_RELEASE_RECOVER)
                | ((self.recovery_count >= self.recovery_frames)
                   & recovery_rearmed))
            self._timeline_finished |= (
                final_event_resolved & recovery_finished)

        recovery_rearmed = self._recovery_rearmed()
        recovery_active = (
            (self.motor_phase == PHASE_RELEASE_RECOVER)
            & self._recovery_context_valid
            & self._recovery_reward_valid)
        recovery_shaping = strike_clean_recovery_progress(
            self.recovery_count,
            self._recovery_best_count,
            recovery_rearmed,
            recovery_active,
            self._recovery_completion_recorded,
            recovery_frames=self.recovery_frames)
        recovery_progress = recovery_shaping["progress"].to(tip.dtype)
        recovery_complete_pulse = recovery_shaping["complete_pulse"]
        self._recovery_best_count.copy_(recovery_shaping["best_count"])
        self._recovery_completion_recorded.copy_(
            recovery_shaping["completion_recorded"])
        self.metric_recovery_completed += recovery_complete_pulse.float()
        if self.curriculum_stage == S3_SONG_INTEGRATION:
            release_to_approach = strike_dual_recovery_to_approach(
                self.motor_phase,
                self.event_resolved,
                self.recovery_count,
                recovery_rearmed,
                self._effective_target_time() - next_song_time,
                self._recovery_required_frames,
                self._recovery_handoff,
                self._recovery_same_string_handoff,
                self._recovery_clearance_required,
                self._recovery_clearance_reached,
                release_recover_phase=PHASE_RELEASE_RECOVER,
                approach_lead_s=self.approach_lead_s)
        else:
            release_to_approach = torch.zeros_like(self.event_resolved)
        scheduled_recovery_shaping = strike_dual_recovery_progress(
            self.recovery_count,
            self._scheduled_recovery_best_count,
            recovery_rearmed,
            recovery_active,
            self._recovery_required_frames,
            self._recovery_handoff,
            release_to_approach,
            self._recovery_clearance_required,
            self._recovery_clearance_reached,
            self._scheduled_recovery_completion_recorded)
        scheduled_recovery_progress = scheduled_recovery_shaping[
            "progress"].to(tip.dtype)
        scheduled_recovery_complete_pulse = scheduled_recovery_shaping[
            "complete_pulse"]
        self._scheduled_recovery_best_count.copy_(
            scheduled_recovery_shaping["best_count"])
        self._scheduled_recovery_completion_recorded.copy_(
            scheduled_recovery_shaping["completion_recorded"])
        self.metric_scheduled_recovery_completed += (
            scheduled_recovery_complete_pulse.float())
        self.metric_full_recovery_completed += (
            scheduled_recovery_complete_pulse
            & ~self._recovery_handoff).float()
        self.metric_handoff_recovery_completed += (
            scheduled_recovery_complete_pulse
            & self._recovery_handoff).float()

        reward, reward_terms = self.reward_fn.compute(
            self.curriculum_stage,
            grip_quality=grip["grip_quality"],
            reach_progress=reach_progress,
            ready_quality=ready_quality,
            ready_pulse=ready_pulse,
            ready_acquired=ready_acquired,
            target_hit=target_hit,
            strum_progress=strum_progress_shaping,
            strum_terminal_progress=strum_terminal_progress,
            strum_physical_completion_pulse=(
                strum_physical_completion_pulse),
            timing_progress_quality=timing_progress_quality,
            timing_wait_quality=timing_wait_quality,
            early_timing_cost=early_timing_cost,
            strum_timing_sample=strum_timing_sample,
            strum_timing_rms_s=traversal_timing["rms_error_s"],
            strum_duration_error_s=traversal_timing["duration_error_s"],
            wrong_crossing_count=wrong_count,
            miss_pulse=miss_pulse,
            premature_release=premature_release,
            clean_event=clean_event,
            timing_core_s=timing_core_s,
            duration_core_s=self.duration_reward_core_ms / 1000.0,
            zone_quality=raw_zone_quality,
            zone_attempt=raw_zone_attempt,
            recovery_active=recovery_active,
            recovery_progress=scheduled_recovery_progress,
            recovery_complete_pulse=scheduled_recovery_complete_pulse,
            recovery_speed_m_s=torch.linalg.vector_norm(
                self._tip_velocity_g, dim=-1),
        )
        controlled_position = self.dof_state.view(
            self.num_envs, self.n_dof, 2)[:, self.ctrl_idx, 0]
        controlled_lower = self.dof_lower.view(
            self.num_envs, self.n_dof)[:, self.ctrl_idx]
        controlled_upper = self.dof_upper.view(
            self.num_envs, self.n_dof)[:, self.ctrl_idx]
        joint_limit_usage = normalized_joint_limit_usage(
            controlled_position, controlled_lower, controlled_upper)
        joint_limit_excess = (
            (joint_limit_usage - self.joint_limit_soft_start_fraction)
            / max(1.0 - self.joint_limit_soft_start_fraction, 1e-6)
        ).clamp_min(0.0)
        joint_limit_penalty = (
            -self.joint_limit_soft_penalty_weight
            * joint_limit_excess.square().mean(dim=1))
        reward += joint_limit_penalty[:, None]
        reward_terms["penalty_joint_limit"] = joint_limit_penalty
        reward_terms["reward_total"] = reward[:, 0]
        self.metric_reward_timing_return += reward_terms["reward_timing"]
        self.metric_reward_timing_wait_return += reward_terms[
            "reward_timing_wait"]
        self.metric_reward_strum_progress_return += reward_terms[
            "reward_strum_progress"]
        self.metric_reward_strum_terminal_progress_return += reward_terms[
            "reward_strum_terminal_progress"]
        self.metric_reward_strum_physical_completion_return += reward_terms[
            "reward_strum_physical_completion"]
        self.metric_penalty_premature_release_return += reward_terms[
            "penalty_premature_release"]
        self.metric_penalty_early_timing_return += reward_terms[
            "penalty_early_timing"]
        self.metric_penalty_miss_return += reward_terms["penalty_miss"]
        reward_nonfinite = ~torch.isfinite(reward).all(dim=1)
        nonfinite |= reward_nonfinite

        if self.curriculum_stage in TIMED_STAGES:
            self.song_time_s.copy_(next_song_time)
        if self.curriculum_stage == S3_SONG_INTEGRATION:
            self.motor_phase = torch.where(
                release_to_approach,
                torch.full_like(self.motor_phase, PHASE_APPROACH),
                self.motor_phase)
            self._recovery_context_valid[release_to_approach] = False
            self._recovery_reward_valid[release_to_approach] = False
            self._target_distance_valid[release_to_approach] = False
        elif self.curriculum_stage not in (
                A0_PICK_GRIP, A1_TIP_READY, S3_SONG_INTEGRATION):
            recovery_rearmed = self._recovery_rearmed()
            retry_after_recovery = (
                (self.motor_phase == PHASE_RELEASE_RECOVER)
                & ~self.event_resolved
                & (self.recovery_count >= self.recovery_frames)
                & recovery_rearmed)
            self.motor_phase = torch.where(
                retry_after_recovery,
                torch.full_like(self.motor_phase, PHASE_APPROACH),
                self.motor_phase)
            self._recovery_context_valid[retry_after_recovery] = False
            self._recovery_reward_valid[retry_after_recovery] = False
            self._target_distance_valid[retry_after_recovery] = False

        if self.curriculum_stage == A0_PICK_GRIP:
            stage_done = stage_timeout
        elif self.curriculum_stage == A1_TIP_READY:



            stage_done = ready_resolution["done"]
        elif self.curriculum_stage != S3_SONG_INTEGRATION:
            recovery_rearmed = self._recovery_rearmed()
            resolution = strike_resolved_episode_done(
                self.event_resolved,
                self.motor_phase,
                self.recovery_count,
                recovery_rearmed,
                stage_timeout,
                release_recover_phase=PHASE_RELEASE_RECOVER,
                recovery_frames=self.recovery_frames,
            )
            stage_done = resolution["done"]
        else:
            stage_done = self._timeline_finished.clone()
            if not self.evaluation_full_song:
                stage_done |= stage_timeout

        terminal_obs = self.compute_observations()
        observation_nonfinite = (
            self.last_nonfinite_observation.clone()
            | ~torch.isfinite(terminal_obs).all(dim=1))
        nonfinite |= observation_nonfinite
        base_failure = torch.zeros_like(stage_done)
        for name, value in base_reasons.items():
            if name not in ("timeout", "base_termination"):
                base_failure |= value
        early_timeout = (
            base_timeout
            & self.evaluation_full_song
            & ~self._timeline_finished)
        recovery_incomplete_timeout = strike_recovery_incomplete_timeout(
            stage_timeout,
            self._recovery_context_valid,
            self.recovery_count,
            self._recovery_rearmed(),
            recovery_frames=self.recovery_frames)
        failure_termination = (
            base_failure | reward_nonfinite | observation_nonfinite
            | early_timeout | recovery_incomplete_timeout
            | wrong_crossing_termination
            | penetration["guitar_penetration_termination"])
        irrecoverable_safety_failure = (
            base_failure | reward_nonfinite | observation_nonfinite
            | penetration["guitar_penetration_termination"])
        performance_failure_termination = (
            early_timeout | recovery_incomplete_timeout
            | wrong_crossing_termination)
        failure_exposure = newly_resolved | performance_failure_termination
        self._record_event_failure_scores(
            target_event_index,
            failure_exposure,
            physical_miss | resolved_with_wrong
            | performance_failure_termination)
        done = stage_done | base_reasons["base_termination"] | failure_termination
        goal_finished = stage_done & ~failure_termination
        if self.curriculum_stage == A1_TIP_READY:
            goal_finished &= ready_resolution["success"]
        reward = torch.where(
            failure_termination[:, None],
            torch.full_like(reward, self.failure_termination_penalty),
            reward)
        reward = self.sanitize_finite(reward)
        self.reset_buf.copy_(done)

        tp = self.metric_tp
        fp = self.metric_fp
        fn = self.metric_fn
        precision = tp / (tp + fp + 1e-8)
        recall = tp / (tp + fn + 1e-8)
        f1 = 2.0 * precision * recall / (precision + recall + 1e-8)
        false_positive_rate = fp / (tp + fp + fn).clamp_min(1.0)
        timing_p95_live = torch.zeros_like(tp)
        has_timing = self._timing_count > 0
        if has_timing.any():


            timing_p95_live = self._timing_abs_ms.max(dim=1).values
        grip_rate = (
            self.metric_grip_success_frames
            / self.metric_grip_frames.clamp_min(1.0))
        ready_rate = self.metric_ready_success.clamp(0.0, 1.0)
        zone_rate = (
            self.metric_zone_hits
            / self.metric_zone_attempts.clamp_min(1.0))
        timing_event_count = self.metric_timing_events.clamp_min(1.0)
        raw_zone_count = self.metric_raw_zone_attempts.clamp_min(1.0)
        s2_profile_index = next(
            index for index, profile in enumerate(self.curriculum_s2_profiles)
            if profile["name"] == self.s2_profile_name)
        post_target_string = self._current_target_string()
        post_motion_target_string, _post_motion_lane_y = (
            self._current_motion_target())
        info = {
            "diagnostic_active": torch.ones(
                self.num_envs, dtype=torch.bool, device=self.device),
            "curriculum_diagnostic_enabled": ~nonfinite,
            "grip_quality": grip["grip_quality"],
            "grip_pinch_quality": grip["grip_pinch_quality"],
            "grip_free_quality": grip["grip_free_quality"],
            "grip_success_rate": grip_rate,
            "grip_pinch_rms_rad": grip["grip_pinch_rms_rad"],
            "grip_free_rms_rad": grip["grip_free_rms_rad"],
            "tip_ready_success_rate": ready_rate,
            "release_recall": recall,
            "false_positive_rate": false_positive_rate,
            "strike_f1": f1,
            "timing_worst_ms": timing_p95_live,
            "timing_pass_rate": (
                self.metric_timing_passed / timing_event_count),
            "timing_early_rate": (
                self.metric_timing_early / timing_event_count),
            "timing_late_rate": (
                self.metric_timing_late / timing_event_count),
            "premature_release_rate": (
                self.metric_premature_release / timing_event_count),
            "zone_success_rate": zone_rate,
            "raw_zone_success_rate": (
                self.metric_raw_zone_hits / raw_zone_count),
            "raw_zone_mean_quality": (
                self.metric_raw_zone_quality_sum / raw_zone_count),
            "tip_target_distance": target_distance,
            "approach_motion_quality": approach_motion_quality,
            "timing_wait_quality": timing_wait_quality,
            "early_timing_cost": early_timing_cost,
            "approach_open": approach_open,
            "time_to_approach_s": time_to_approach_s,
            "approach_lead_s": torch.full(
                (self.num_envs,), self.approach_lead_s,
                dtype=tip.dtype, device=self.device),
            "timing_early_grace_ms": torch.full(
                (self.num_envs,), self.timing_early_grace_ms,
                dtype=tip.dtype, device=self.device),
            "timing_early_penalty_scale_ms": torch.full(
                (self.num_envs,), self.timing_early_penalty_scale_ms,
                dtype=tip.dtype, device=self.device),
            "entry_ready": entry_ready,
            "entry_distance_m": previous_entry_distance,
            "tip_position_g": tip.clone(),
            "tip_velocity_g": self._tip_velocity_g.clone(),
            "tip_speed_m_s": torch.linalg.vector_norm(
                self._tip_velocity_g, dim=-1),
            "action_saturation_fraction": (
                self.prev_action.abs() >= 0.95).float().mean(dim=1),
            "reach_progress": reach_progress,
            "release_mask": release.clone(),
            "blocked_release_mask": detection["blocked_wait_rearm"].clone(),
            "release_direction": detection["direction"].clone(),
            "release_subframe_t": detection["subframe_t"].clone(),
            "release_depth_m": detection["depth"].clone(),
            "release_across_speed_m_s": detection[
                "across_speed"].clone(),
            "release_crossing_y": detection[
                "crossing_pos_g"][..., 1].clone(),
            "release_zone_allowed": detection["zone_allowed"].clone(),
            "release_zone_quality": detection["zone_quality"].clone(),
            "physical_release": physical_release,
            "physical_release_string": release_context["release_string"],
            "physical_release_lane_y": release_context["release_lane_y"],
            "physical_release_direction": release_context[
                "release_direction"],


            "release_phase_violation": release_phase_violation,
            "prepared_target_hit": target_hit & ready_acquired,
            "unprepared_target_hit": target_hit & ~ready_acquired,
            "target_lane_shift_m": (
                self.target_lane_y - previous_target_lane_y).abs(),
            "action_motor_phase": action_phase.clone(),
            "release_count": release_count.float(),
            "blocked_release_count": blocked_release_count.float(),
            "target_hit": target_hit,
            "physical_target_hit": physical_hit.clone(),
            "physical_target_miss": physical_miss.clone(),
            "target_event_index_before_step": target_event_index.clone(),
            "wrong_crossing_count": wrong_count,
            "wrong_crossing_rate": wrong_termination_state["wrong_rate"],
            "wrong_crossing_rate_limit_exceeded": (
                wrong_termination_state["rate_limit_exceeded"]),
            "wrong_crossing_count_termination": (
                wrong_termination_state["count_termination"]),
            "wrong_crossing_rate_termination": (
                wrong_termination_state["rate_termination"]),
            "wrong_crossing_consecutive_termination": (
                wrong_termination_state["consecutive_termination"]),
            "wrong_crossing_termination": wrong_crossing_termination,
            "hard_sampled_window": self._sampled_hard_window.float().clone(),
            "upstroke_sampled_window": (
                self._sampled_upstroke_window.float().clone()),
            "s2_focus_sampled": self._sampled_s2_focus.float().clone(),
            "s2_endpoint_recovery_active": torch.full(
                (self.num_envs,),
                float(self.s2_endpoint_recovery_active),
                device=self.device),
            "failure_score_max": self._event_failure_score.max().expand(
                self.num_envs),
            "failure_score_mean": self._event_failure_score.mean().expand(
                self.num_envs),
            "failure_exposure_min": torch.where(
                (self._event_failure_exposure > 0.0).any(),
                torch.where(
                    self._event_failure_exposure > 0.0,
                    self._event_failure_exposure,
                    torch.full_like(
                        self._event_failure_exposure, float("inf"))).min(),
                torch.zeros((), device=self.device)).expand(self.num_envs),
            "failure_exposure_max": (
                self._event_failure_exposure.max().expand(self.num_envs)),
            "hard_window_probability_max": torch.full(
                (self.num_envs,),
                self._hard_window_probability_max,
                device=self.device),
            "upstroke_window_probability_max": torch.full(
                (self.num_envs,),
                self._upstroke_window_probability_max,
                device=self.device),
            "strum_order_violation_count": ordered_release[
                "order_violation_count"],
            "strum_wrong_direction_count": ordered_release[
                "wrong_direction_count"],
            "strum_unplanned_crossing_count": ordered_release[
                "unplanned_crossing_count"],
            "strum_duplicate_crossing_count": ordered_release[
                "duplicate_crossing_count"],
            "recovery_progress": recovery_progress,
            "recovery_complete_pulse": recovery_complete_pulse,
            "scheduled_recovery_progress": scheduled_recovery_progress,
            "scheduled_recovery_complete_pulse": (
                scheduled_recovery_complete_pulse),
            "recovery_handoff": self._recovery_handoff.clone(),
            "recovery_same_string_handoff": (
                self._recovery_same_string_handoff.clone()),
            "recovery_path_crossing_count": (
                self._recovery_path_crossing_mask.sum(dim=1).float()
                * self._recovery_context_valid.float()),
            "recovery_clearance_required": (
                self._recovery_clearance_required
                & self._recovery_context_valid),
            "recovery_clearance_lifted": (
                self._recovery_clearance_lifted
                & self._recovery_context_valid),
            "recovery_clearance_reached": (
                self._recovery_clearance_reached
                & self._recovery_context_valid),
            "recovery_required_frames": (
                self._recovery_required_frames.float()),
            "recovery_available_frames": (
                self._recovery_available_frames.float()),
            "recovery_reset_count": recovery_reset.float(),
            "miss": miss_pulse,
            "premature_release": premature_release,
            "timing_error_ms": torch.where(
                timing_sample,
                timing_error_s * 1000.0,
                torch.zeros_like(timing_error_s)),
            "strum_timing_rms_ms": torch.where(
                timing_sample,
                traversal_timing["rms_error_s"] * 1000.0,
                torch.zeros_like(timing_error_s)),
            "strum_sweep_duration_error_ms": torch.where(
                timing_sample,
                traversal_timing["duration_error_s"].abs() * 1000.0,
                torch.zeros_like(timing_error_s)),
            "strum_planned_sweep_duration_ms": (
                traversal_timing["planned_duration_s"] * 1000.0),
            "strum_actual_sweep_duration_ms": torch.where(
                traversal_timing["complete"],
                traversal_timing["actual_duration_s"] * 1000.0,
                torch.zeros_like(timing_error_s)),
            "strum_per_string_timing_error_ms": (
                traversal_timing["per_string_error_s"] * 1000.0),
            "timing_sample": timing_sample,
            "strum_timing_sample": strum_timing_sample,
            "target_direction_down": (
                target_direction == DIRECTION_DOWN).float(),
            "zone_quality": lane_quality,
            "zone_global_quality": global_zone_quality,
            "zone_lane_allowed": lane_allowed,
            "motor_phase": self.motor_phase.clone(),
            "target_string": target_string.clone(),
            "target_gesture": target_gesture.clone(),
            "target_traversal_mask": target_columns.clone(),
            "target_release_progress_mask": accumulated_release.clone(),
            "accepted_release_mask": accepted_release.clone(),
            "strum_progress": strum_progress.clone(),
            "strum_terminal_progress": strum_terminal_progress.clone(),
            "strum_terminal_progress_best": (
                terminal_progress_state["best"].clone()),
            "strum_exit_distance_m": (
                terminal_progress_state["exit_distance_m"].clone()),
            "strum_physical_completion_pulse": (
                strum_physical_completion_pulse.clone()),
            "strum_final_string_remaining": final_string_remaining.clone(),
            "strum_final_string_miss_at_timeout": (
                stage_timeout & final_string_remaining),
            "strum_remaining_string_count": (
                (target_columns & ~accumulated_release)
                .sum(dim=1).to(tip.dtype)),
            "down_completed_count": self.metric_down_completed.clone(),
            "up_completed_count": self.metric_up_completed.clone(),
            "strum_max_strings": torch.full(
                (self.num_envs,),
                self.strum_span,
                dtype=tip.dtype, device=self.device),
            "motion_target_string": motion_target_string.clone(),
            "event_index_after_step": self.event_index.clone(),
            "event_target_string_after_step": post_target_string.clone(),
            "motion_target_string_after_step":
                post_motion_target_string.clone(),
            "timing_tolerance_ms": torch.full(
                (self.num_envs,), self.timing_tolerance_ms,
                device=self.device),
            "timing_left_tolerance_ms": left_tolerance * 1000.0,
            "timing_right_tolerance_ms": right_tolerance * 1000.0,
            "tempo_lambda": torch.full(
                (self.num_envs,), self.tempo_lambda,
                device=self.device),
            "target_original_time_s": self.goals.time[
                target_event_index].clone(),
            "target_effective_time_s": target_time.clone(),
            "goal_finished": goal_finished,
            "timeout": base_timeout | stage_timeout,
            "early_timeout": early_timeout,
            "recovery_incomplete_timeout": recovery_incomplete_timeout,
            "nonfinite": nonfinite,
            "velocity_blowup": velocity_blowup,
            "failure_termination": failure_termination,
            "joint_limit_max_usage": joint_limit_usage.amax(dim=1),
            "joint_limit_near_rate": (
                joint_limit_usage >= self.joint_limit_diagnostic_fraction
            ).float().mean(dim=1),
            "minimum_effective_gap_s": torch.full(
                (self.num_envs,),
                float(self._gap_diagnostics[
                    "minimum_effective_gap_s"] or 0.0),
                device=self.device),
            "overlap_window_count": torch.full(
                (self.num_envs,),
                float(self._gap_diagnostics["overlap_window_count"]),
                device=self.device),
            "s2_profile_index": torch.full(
                (self.num_envs,), float(s2_profile_index),
                device=self.device),
            "s2_zone_gate_active": torch.full(
                (self.num_envs,), float(self.zone_gate_active),
                device=self.device),
        }
        for group, indices in self.joint_limit_group_indices.items():
            group_usage = joint_limit_usage[:, indices]
            info[f"joint_limit_{group}_max_usage"] = group_usage.amax(dim=1)
            info[f"joint_limit_{group}_near_rate"] = (
                group_usage >= self.joint_limit_diagnostic_fraction
            ).float().mean(dim=1)
        info.update({
            name: value.clone() for name, value in penetration.items()})
        env_ids = torch.nonzero(done).squeeze(-1)
        info.update({name: value for name, value in reward_terms.items()})
        info.update(self._episode_metrics(done, failure_termination))
        info["episode_timing_count"] = (
            self._timing_count[env_ids].clone())
        info["episode_timing_abs_ms"] = (
            self._timing_abs_ms[env_ids].clone())
        info["episode_timing_signed_ms"] = (
            self._timing_signed_ms[env_ids].clone())
        info["episode_grip_quality_count"] = (
            self.metric_grip_frames[env_ids].long().clamp_max(
                self._timing_capacity))
        info["episode_grip_quality_samples"] = (
            self._grip_quality_samples[env_ids].clone())
        info["episode_strum_microtiming_count"] = (
            self._strum_microtiming_count[env_ids].clone())
        info["episode_strum_timing_rms_ms"] = (
            self._strum_timing_rms_ms[env_ids].clone())
        info["episode_strum_duration_error_ms"] = (
            self._strum_duration_error_ms[env_ids].clone())
        info["terminal_env_ids"] = env_ids.clone()
        info["terminal_observation"] = terminal_obs[env_ids].clone()
        episode_reasons = {
            "goal_finished": goal_finished,
            "failure_termination": failure_termination,
            "early_timeout": early_timeout,
            "recovery_incomplete_timeout": recovery_incomplete_timeout,
            "nonfinite": nonfinite,
            "velocity_blowup": velocity_blowup,
            "guitar_penetration_termination": penetration[
                "guitar_penetration_termination"],
            "wrong_crossing_termination": wrong_crossing_termination,
            "wrong_crossing_count_termination": (
                wrong_termination_state["count_termination"]),
            "wrong_crossing_rate_termination": (
                wrong_termination_state["rate_termination"]),
            "wrong_crossing_consecutive_termination": (
                wrong_termination_state["consecutive_termination"]),
            "irrecoverable_safety_failure": irrecoverable_safety_failure,
            "performance_failure_termination": (
                performance_failure_termination),
        }
        info.update({
            f"episode_{name}": value[env_ids].clone()
            for name, value in episode_reasons.items()
        })
        for name, value in base_reasons.items():
            info.setdefault(name, value.clone())
        for name, value in tuple(info.items()):
            if (name != "terminal_observation"
                    and isinstance(value, torch.Tensor)
                    and value.is_floating_point()):
                info[name] = torch.nan_to_num(
                    value, nan=0.0, posinf=0.0, neginf=0.0)

        if env_ids.numel() > 0:
            self.reset_idx(env_ids)
        obs = self._compose_reset_observation(terminal_obs, env_ids)
        return obs, reward, done, info

    def close(self):
        if getattr(self, "sim", None) is not None:
            self.gym.destroy_sim(self.sim)
            self.sim = None

__all__ = [
    "STRIKE_CONTROL_PREFIXES",
    "STRIKE_OBS_BODIES",
    "STRIKE_DIRECTION_PROFILE",
    "PHASE_READY",
    "PHASE_APPROACH",
    "PHASE_RELEASE_RECOVER",
    "StrikeTask",
]
