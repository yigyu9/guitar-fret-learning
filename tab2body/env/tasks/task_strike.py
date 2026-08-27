"""Isaac Gym task for learning a natural right-hand virtual-pick strike.

The public music input remains the minimal ``[time, frame, string]`` event
timeline.  Everything else in this task is derived from that input and the
live guitar geometry:

* ``RH:pick`` is a geometry-less point rigidly attached to the index finger.
* the six strings are fixed finite segments defined by guitar marker bodies;
* a strike is a debounced RELEASE event after a sufficiently deep, sufficiently
  fast swept-point crossing;
* v1 uses one explicit direction profile, ``down_only_v1`` (+x in the guitar
  frame), because direction is intentionally absent from the external input.

# The observation and 30-DOF action layouts stay unchanged throughout the five
# acquisition stages.  Stage masks and rewards change, never tensor shapes.

The observation and 30-DOF action layouts stay unchanged throughout the
acquisition stages (A0-A4, then the X0_MINI_STRUM multi-string extension).
Stage masks and rewards change, never tensor shapes.
"""
from __future__ import annotations

from collections.abc import Mapping
import math
from numbers import Real
from typing import Tuple

import torch
from isaacgym import gymtorch

from ..base import GuitarEnvBase
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
    strike_reach_potential_delta,
)
from ..strike_events import (
    strike_a4_continuing_phase,
    strike_completed_recovery_frames,
    strike_motion_target_context,
    strike_physical_target_candidate,
    strike_ordered_release_progress,
    strike_ready_episode_resolution,
    strike_ready_latch,
    strike_recovery_incomplete_timeout,
    strike_recovery_to_approach,
    strike_release_recovery_context,
    strike_resolved_episode_done,
    strike_timing_gate,
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
    normalized_joint_limit_usage,
    update_wrong_crossing_termination,
)
from ...strike_contract import (
    SONG_GOAL_STAGES,
    TIMED_PRACTICE_MAX_TIME_S,
    TIMED_PRACTICE_MIN_TIME_S,
    minimum_strike_stage_horizon,
)


STRIKE_CONTROL_PREFIXES = (
    "R_Shoulder", "R_Elbow", "R_Wrist", "RH:",
)
STRIKE_OBS_BODIES = (
    "R_Wrist", "RH:palm", "RH:pick",
)
STRIKE_DIRECTION_PROFILE = "down_only_v1"

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
)
_JOINT_LIMIT_CONFIG_KEYS = (
    "diagnostic_fraction", "soft_penalty_start_fraction",
    "soft_penalty_weight",
)
_EPISODE_CONFIG_KEYS = (
    *STAGES, "a4_events_per_episode", "timed_lead_frames",
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
    """Five-stage right-hand strike environment with a scalar reward."""

    task_name = "strike"
    episode_metric_keys = (
        "strike_grip_success_rate",
        "strike_tip_ready_success_rate",
        "strike_precision",
        "strike_release_recall",
        "strike_false_positive_rate",
        "strike_episode_f1",
        "strike_timing_mae_ms",
        "strike_timing_p95_ms",
        "strike_zone_success_rate",
        "strike_zone_mean_quality",
        "strike_single_precision",
        "strike_single_recall",
        "strike_single_f1",
        "strike_single_event_count",
        "strike_strum_completion_rate",
        "strike_strum_traversal_recall",
        "strike_strum_order_accuracy",
        "strike_strum_direction_accuracy",
        "strike_strum_protected_crossing_rate",
        "strike_strum_duplicate_crossing_rate",
        "strike_strum_event_count",
        "curriculum_success_rate",
    )
    episode_reason_keys = (
        "goal_finished",
        "failure_termination",
        "recovery_incomplete_timeout",
        "early_timeout",
        "nonfinite",
        "velocity_blowup",
        "guitar_penetration_termination",
        "wrong_crossing_termination",
    )
    rollout_diagnostic_keys = (
        "grip_quality",
        "grip_success_rate",
        "tip_ready_success_rate",
        "release_recall",
        "false_positive_rate",
        "strike_f1",
        "timing_p95_ms",
        "zone_success_rate",
        "tip_target_distance",
        "entry_ready",
        "entry_distance_m",
        "tip_speed_m_s",
        "guitar_penetration_depth",
        "guitar_swept_penetration_depth",
        "guitar_penetration",
        "action_saturation_fraction",
        "release_count",
        "release_phase_violation",
        "prepared_target_hit",
        "unprepared_target_hit",
        "target_lane_shift_m",
        "strum_order_violation_count",
        "strum_wrong_direction_count",
        "strum_protected_crossing_count",
        "strum_duplicate_crossing_count",
        "wrong_crossing_rate",
        "wrong_crossing_termination",
        "joint_limit_max_usage",
        "joint_limit_near_rate",
        "joint_limit_shoulder_max_usage",
        "joint_limit_elbow_max_usage",
        "joint_limit_wrist_max_usage",
        "joint_limit_hand_max_usage",
        "minimum_effective_gap_s",
        "overlap_window_count",
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
            zone,
            trajectory,
            detector,
            safety,
            wrong_crossing_termination,
            joint_limits,
            reward,
            episode,
            failure_termination_penalty=-10.0,
            random_start=True):
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
        a4_events_per_episode = _integer_config(
            "episode.a4_events_per_episode",
            episode_config["a4_events_per_episode"], minimum=1)
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
            self.ready_distance, self.entry_distance)
        if any(value <= 0.0 for value in positive_trajectory):
            raise ValueError("strike trajectory distances must be finite and positive")
        if self.approach_lead_s < 0.0:
            raise ValueError("trajectory.approach_lead_s must be non-negative")
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
        self.a4_events_per_episode = a4_events_per_episode
        self.timed_lead_frames = timed_lead_frames
        self.full_song_start_time_s = (
            float(self.goals.time[0].item())
            - self.timed_lead_frames / self.SIM_HZ)

        self.curriculum_stage = STAGES[0]
        self.timing_tolerance_ms = 100.0
        self.tempo_lambda = 1.0
        self._event_times = self.goals.runtime_time(self.tempo_lambda)
        self._event_left_tolerance, self._event_right_tolerance = (
            self.goals.runtime_windows(
                self.tempo_lambda, self.timing_tolerance_ms))
        self._gap_diagnostics = self.goals.gap_diagnostics(
            self.tempo_lambda, self.timing_tolerance_ms)
        self.evaluation_full_song = False
        self._validate_episode_feasibility()
        self.direction_profile = STRIKE_DIRECTION_PROFILE
        self.max_episode_length = self.stage_horizons[self.curriculum_stage]

        n = self.num_envs
        d = self.device
        self.practice_string = torch.arange(
            n, dtype=torch.long, device=d) % N_GUITAR_STRINGS
        self.practice_target_time_s = torch.ones(n, device=d)
        self.target_lane_y = torch.full(
            (n,), self.phrase_lane_y, device=d)
        self._reset_generation = torch.zeros(n, dtype=torch.long, device=d)
        self.event_index = torch.zeros(n, dtype=torch.long, device=d)
        self.episode_event_count = torch.zeros(n, dtype=torch.long, device=d)
        self.song_time_s = torch.zeros(n, device=d)
        self.motor_phase = torch.zeros(n, dtype=torch.long, device=d)
        self.ready_streak = torch.zeros(n, dtype=torch.long, device=d)
        self.event_resolved = torch.zeros(n, dtype=torch.bool, device=d)
        self._event_release_mask = torch.zeros(
            n, N_GUITAR_STRINGS, dtype=torch.bool, device=d)
        self._event_onset_time_s = torch.zeros(n, device=d)
        self._event_onset_valid = torch.zeros(n, dtype=torch.bool, device=d)
        self._event_zone_valid = torch.ones(n, dtype=torch.bool, device=d)
        self._event_zone_quality = torch.ones(n, device=d)
        self.recovery_count = torch.zeros(n, dtype=torch.long, device=d)
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
        self._previous_reach_potential = torch.zeros(n, device=d)
        self._target_distance_valid = torch.zeros(n, dtype=torch.bool, device=d)
        self._wrong_crossing_total = torch.zeros(n, device=d)
        self._wrong_crossing_resolved_events = torch.zeros(
            n, dtype=torch.long, device=d)
        self._wrong_crossing_consecutive_events = torch.zeros(
            n, dtype=torch.long, device=d)
        self._event_had_wrong_crossing = torch.zeros(
            n, dtype=torch.bool, device=d)

        self._metric_names = (
            "metric_grip_success_frames", "metric_grip_frames",
            "metric_ready_success", "metric_tp", "metric_fp", "metric_fn",
            "metric_zone_attempts", "metric_zone_hits",
            "metric_zone_quality_sum",
            "metric_single_tp", "metric_single_fp", "metric_single_fn",
            "metric_strum_events", "metric_strum_completed",
            "metric_strum_traversal_required",
            "metric_strum_traversal_completed",
            "metric_strum_order_violations",
            "metric_strum_direction_violations",
            "metric_strum_protected_crossings",
            "metric_strum_duplicate_crossings",
            "metric_strum_release_attempts",
        )
        for name in self._metric_names:
            setattr(self, name, torch.zeros(n, device=d))
        self._grip_history_length = 30
        self._grip_success_history = torch.zeros(
            n, self._grip_history_length, dtype=torch.bool, device=d)




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
        self._timing_abs_ms = torch.zeros(
            n, self._timing_capacity, device=d)
        self._timing_count = torch.zeros(n, dtype=torch.long, device=d)

        self.base_obs_dim = self.num_obs
        self.strike_obs_manifest = self._build_strike_obs_manifest()
        self.strike_obs_dim = len(self.strike_obs_manifest)
        self.actuator_obs_dim = self.num_actions
        self.num_obs = (
            self.base_obs_dim + self.strike_obs_dim + self.actuator_obs_dim)
        self.obs_buf = torch.zeros(n, self.num_obs, device=d)
        self.observation_manifest = tuple(
            self._build_base_obs_manifest()
            + list(self.strike_obs_manifest)
            + [f"actuator.previous_action.{name}"
               for name in self.controlled_dof_names])
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

    def _string_lane_geometry(self, target_lane_y=None):
        start, end = self.string_segments_g()
        if target_lane_y is None:
            target_lane_y = self.target_lane_y
        denominator = end[..., 1] - start[..., 1]
        if torch.any(denominator.abs() < 1e-8):
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
        lane, normal = self._string_lane_geometry(target_lane_y)
        rows = torch.arange(self.num_envs, device=self.device)
        exit_string = target_string
        active_song_gesture = (
            #(self.curriculum_stage == STAGES[4])
            (self.curriculum_stage in SONG_GOAL_STAGES)
            & ~self._recovery_context_valid)
        if isinstance(active_song_gesture, bool):
            active_song_gesture = torch.full(
                (self.num_envs,), active_song_gesture,
                dtype=torch.bool, device=self.device)
        event_index = self.event_index.clamp(0, self.goals.num_events - 1)
        exit_string = torch.where(
            active_song_gesture,
            self.goals.exit_string[event_index],
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
        return (
            target_string, target_lane_y, center, ready, entry, exit_point)




    def _current_target_string(self):
        if self.curriculum_stage in STAGES[:4]:
            return self.practice_string
        index = self.event_index.clamp(0, self.goals.num_events - 1)
        return self.goals.string[index]

    def _current_target_time(self):
        if self.curriculum_stage in STAGES[:3]:
            return torch.zeros(self.num_envs, device=self.device)
        if self.curriculum_stage == STAGES[3]:
            return self.practice_target_time_s
        index = self.event_index.clamp(0, self.goals.num_events - 1)
        return self._event_times[index]

    def _current_target_masks(self):
        # if self.curriculum_stage != STAGES[4]:
        if self.curriculum_stage not in SONG_GOAL_STAGES:
            return _one_hot(
                self._current_target_string(),
                N_GUITAR_STRINGS, dtype=torch.bool)
        index = self.event_index.clamp(0, self.goals.num_events - 1)
        return self.goals.traversal_mask[index]

    def _current_timing_tolerances(self):
        tolerance = torch.full(
            (self.num_envs,), self.timing_tolerance_ms / 1000.0,
            device=self.device)
        # if self.curriculum_stage != STAGES[4]:
        if self.curriculum_stage not in SONG_GOAL_STAGES:
            return tolerance, tolerance
        index = self.event_index.clamp(0, self.goals.num_events - 1)
        return (
            self._event_left_tolerance[index],
            self._event_right_tolerance[index])

    def _current_motion_context(self):
        """Return geometry and direction that own the current motor trajectory.

        A4 advances the musical event immediately after resolving it so the
        next event remains visible to the policy.  Physical follow-through
        nevertheless stays attached to the just-released string and lane
        until the motor phase leaves ``RELEASE_RECOVER``.
        """
        context = strike_motion_target_context(
            self._current_target_string(),
            self.target_lane_y,
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

    def _release_to_approach(self, target_time):
        """Gate the next approach behind a measurable follow-through."""
        # if self.curriculum_stage != STAGES[4]:
        if self.curriculum_stage not in SONG_GOAL_STAGES:
            return torch.zeros_like(self.event_resolved)
        return strike_recovery_to_approach(
            self.motor_phase,
            self.event_resolved,
            self.recovery_count,
            self._recovery_rearmed(),
            target_time - self.song_time_s,
            release_recover_phase=PHASE_RELEASE_RECOVER,
            minimum_follow_through_frames=self.follow_through_min_frames,
            approach_lead_s=self.approach_lead_s,
        )

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
        if self.curriculum_stage == STAGES[3]:
            return torch.zeros(count, dtype=torch.long, device=self.device)
        quota = self.goals.num_events if self.evaluation_full_song else min(
            self.a4_events_per_episode, self.goals.num_events)
        max_start = max(self.goals.num_events - quota, 0)
        if self.evaluation_full_song or not self.random_start or max_start == 0:
            return torch.zeros(count, dtype=torch.long, device=self.device)
        return torch.randint(
            max_start + 1, (count,), generator=self.rng, device=self.device)

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
        # if (stage == STAGES[4]
        if (stage in SONG_GOAL_STAGES
                and self.approach_lead_s + float(tolerance_ms) / 1000.0
                < 1.0 / self.SIM_HZ):
            raise ValueError(
                # "A4 approach lead and timing tolerance must leave at "
                "A4/X0 approach lead and timing tolerance must leave at "
                "least one APPROACH action")
        candidates = (
            (STAGES[1], None),
            (STAGES[2], None),
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
                a4_events_per_episode=self.a4_events_per_episode,
                timing_tolerance_ms=tolerance)
            for name, tolerance in candidates
        }
        impossible = {
            stage: (self.stage_horizons[stage], minimum)
            for stage, minimum in required.items()
            if self.stage_horizons[stage] < minimum
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
        self.episode_event_count[env_ids] = 0
        if self.curriculum_stage == STAGES[3]:
            self.practice_target_time_s[env_ids] = (
                TIMED_PRACTICE_MIN_TIME_S
                + (TIMED_PRACTICE_MAX_TIME_S
                   - TIMED_PRACTICE_MIN_TIME_S) * torch.rand(
                    env_ids.numel(), generator=self.rng,
                    device=self.device))
            self.song_time_s[env_ids] = 0.0
        # elif self.curriculum_stage == STAGES[4]:
        elif self.curriculum_stage in SONG_GOAL_STAGES:
            if self.evaluation_full_song:
                self.song_time_s[env_ids] = self.full_song_start_time_s
            else:
                target_time = self._event_times[sampled]
                self.song_time_s[env_ids] = (
                    target_time - self.timed_lead_frames / self.SIM_HZ
                )
        else:
            self.song_time_s[env_ids] = 0.0
        # if self.curriculum_stage == STAGES[4]:
        if self.curriculum_stage in SONG_GOAL_STAGES:
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
        self._event_onset_time_s[env_ids] = 0.0
        self._event_onset_valid[env_ids] = False
        self._event_zone_valid[env_ids] = True
        self._event_zone_quality[env_ids] = 1.0
        self.recovery_count[env_ids] = 0
        self._recovery_direction[env_ids] = DIRECTION_DOWN
        self._recovery_context_valid[env_ids] = False
        self._timeline_finished[env_ids] = False
        self._tip_velocity_g[env_ids] = 0.0
        self._previous_tip_valid[env_ids] = False
        self._last_release[env_ids] = False
        self._previous_reach_potential[env_ids] = 0.0
        self._target_distance_valid[env_ids] = False
        self._wrong_crossing_total[env_ids] = 0.0
        self._wrong_crossing_resolved_events[env_ids] = 0
        self._wrong_crossing_consecutive_events[env_ids] = 0
        self._event_had_wrong_crossing[env_ids] = False
        self.detector.reset(env_ids)
        if hasattr(self, "penetration_monitor"):
            self.penetration_monitor.reset(env_ids)
        for name in self._metric_names:
            getattr(self, name)[env_ids] = 0.0
        self._grip_success_history[env_ids] = False
        self._timing_abs_ms[env_ids] = 0.0
        self._timing_count[env_ids] = 0

    def _advance_a4_events(self, resolved, physical_release):
        ids = torch.nonzero(resolved).squeeze(-1)
        if ids.numel() == 0:
            return
        self.episode_event_count[ids] += 1
        self._target_distance_valid[ids] = False
        next_index = self.event_index[ids] + 1
        quota = (
            self.goals.num_events if self.evaluation_full_song
            else min(self.a4_events_per_episode, self.goals.num_events))
        finished = (
            (self.episode_event_count[ids] >= quota)
            | (next_index >= self.goals.num_events))
        continuing = ids[~finished]
        if continuing.numel() > 0:
            self.event_index[continuing] += 1
            phase_advance = strike_a4_continuing_phase(
                self.motor_phase[continuing],
                physical_release[continuing],
                self._recovery_context_valid[continuing],
                release_recover_phase=PHASE_RELEASE_RECOVER)
            preserve_recovery = phase_advance["preserve_recovery"]
            self.motor_phase[continuing] = phase_advance["motor_phase"]
            self.ready_streak[continuing] = 0
            self.event_resolved[continuing] = False
            self._event_release_mask[continuing] = False
            self._event_onset_time_s[continuing] = 0.0
            self._event_onset_valid[continuing] = False
            self._event_zone_valid[continuing] = True
            self._event_zone_quality[continuing] = 1.0
            self._recovery_context_valid[
                continuing[~preserve_recovery]] = False




    def _validate_stage_goal_contract(self, stage, tolerance_ms):
        # if stage == STAGES[4]:
        if stage in SONG_GOAL_STAGES:
            self.goals.require_nonoverlapping_match_windows(tolerance_ms)
        self._validate_episode_feasibility(stage, tolerance_ms)

    def set_curriculum_stage(
            self, stage, tolerance_ms, tempo_lambda=1.0, reset=False):
        if stage not in STAGES:
            raise ValueError(f"unknown strike stage: {stage}")
        tolerance_ms = float(tolerance_ms)
        if not math.isfinite(tolerance_ms) or tolerance_ms <= 0.0:
            raise ValueError("timing tolerance must be finite and positive")
        tempo_lambda = float(tempo_lambda)
        if not math.isfinite(tempo_lambda) or not 0.0 <= tempo_lambda <= 1.0:
            raise ValueError("tempo lambda must be finite and in [0, 1]")
        if stage != STAGES[4]:
            tempo_lambda = 1.0
        self._event_times = self.goals.runtime_time(tempo_lambda)
        self._event_left_tolerance, self._event_right_tolerance = (
            self.goals.runtime_windows(tempo_lambda, tolerance_ms))
        self._gap_diagnostics = self.goals.gap_diagnostics(
            tempo_lambda, tolerance_ms)
        self._validate_stage_goal_contract(stage, tolerance_ms)
        changed = (
            stage != self.curriculum_stage
            or abs(tolerance_ms - self.timing_tolerance_ms) > 1e-9
            or abs(tempo_lambda - self.tempo_lambda) > 1e-9)
        self.curriculum_stage = str(stage)
        self.timing_tolerance_ms = tolerance_ms
        self.tempo_lambda = tempo_lambda
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

    def _stage_episode_limit(self):
        # if self.curriculum_stage == STAGES[4] and self.evaluation_full_song:
        if (self.curriculum_stage in SONG_GOAL_STAGES
                and self.evaluation_full_song):
            final_time_s = float(self._event_times[-1].item())
            required = int(math.ceil(
                (final_time_s
                 + self.timing_tolerance_ms / 1000.0
                 + max(
                     self.recovery_frames,
                     self.detector.rearm_min_frames) / self.SIM_HZ
                 - self.full_song_start_time_s)
                * self.SIM_HZ)) + 2
            return max(
                required,
                # self.stage_horizons[STAGES[4]],
                self.stage_horizons[self.curriculum_stage],
            )
        return self.stage_horizons[self.curriculum_stage]

    def curriculum_state_dict(self):
        return {
            "schema": "tab2body.strike_environment_state.v2",
            "curriculum_stage": self.curriculum_stage,
            "timing_tolerance_ms": float(self.timing_tolerance_ms),
            "tempo_lambda": float(self.tempo_lambda),
            "evaluation_full_song": bool(self.evaluation_full_song),
            "random_start": bool(self.random_start),
            "rng_state": self.rng.get_state(),
            "reset_generation": self._reset_generation.detach().cpu(),
        }

    def load_curriculum_state_dict(self, state):
        if state.get("schema") != "tab2body.strike_environment_state.v2":
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
        self._event_times = self.goals.runtime_time(self.tempo_lambda)
        self._event_left_tolerance, self._event_right_tolerance = (
            self.goals.runtime_windows(
                self.tempo_lambda, self.timing_tolerance_ms))
        self._gap_diagnostics = self.goals.gap_diagnostics(
            self.tempo_lambda, self.timing_tolerance_ms)
        self._validate_stage_goal_contract(
            self.curriculum_stage, self.timing_tolerance_ms)
        self.evaluation_full_song = bool(state.get("evaluation_full_song", False))
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
        return self.reset()




    def apply_actions(self, actions):
        if self.curriculum_stage == STAGES[0]:
            actions = torch.where(
                self._action_is_hand[None], actions, self.grip_hold_action)
        super().apply_actions(actions)

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
        body_start = 2 * self.n_nonlocked
        self._settled_reset_body_obs = obs[
            :, body_start:self.base_obs_dim].detach().clone()
        tip = self.to_guitar_frame(self.hbody_pos("RH:pick")[:, None])[:, 0]
        self._settled_reset_tip_g = tip.detach().clone()
        self._previous_tip_g.copy_(tip)
        self._previous_tip_valid.fill_(True)
        self._tip_velocity_g.zero_()
        obs = self.compute_observations()
        obs[:, body_start:self.base_obs_dim] = self._settled_reset_body_obs
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

    def _build_strike_obs_manifest(self):
        names = [f"strike.stage.{stage}" for stage in STAGES]
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
        return tuple(names)

    def _lookahead_observation(self, offset):
        # if self.curriculum_stage != STAGES[4]:
        if self.curriculum_stage not in SONG_GOAL_STAGES:
            return torch.zeros(
                self.num_envs, 7, device=self.device)
        index = self.event_index + int(offset)
        valid = index < self.goals.num_events
        safe = index.clamp(0, self.goals.num_events - 1)
        delta = (self._event_times[safe] - self.song_time_s).clamp(-1.0, 2.0)
        delta = torch.where(valid, delta, torch.zeros_like(delta))
        string = self.goals.traversal_mask[safe].to(self.song_time_s.dtype)
        string = string * valid[:, None]
        return torch.cat([delta[:, None], string], dim=-1)

    def _build_strike_observation(self, tip_override=None, velocity_override=None):
        tip = (tip_override if tip_override is not None else
               self.to_guitar_frame(self.hbody_pos("RH:pick")[:, None])[:, 0])
        velocity = (
            velocity_override if velocity_override is not None
            else self._tip_velocity_g)
        _, motion_lane_y, _, ready, entry, exit_point = (
            self._current_target_geometry())
        target_string = self._current_target_string()
        stage_index = torch.full(
            (self.num_envs,), STAGES.index(self.curriculum_stage),
            dtype=torch.long, device=self.device)
        stage = _one_hot(stage_index, len(STAGES), dtype=tip.dtype)
        target_one_hot = _one_hot(
            target_string, N_GUITAR_STRINGS, dtype=tip.dtype)
        target_traversal = self._current_target_masks().to(tip.dtype)
        # if self.curriculum_stage == STAGES[4]:
        if self.curriculum_stage in SONG_GOAL_STAGES:
            event_index = self.event_index.clamp(0, self.goals.num_events - 1)
            target_audible = self.goals.audible_mask[event_index].to(tip.dtype)
            gesture = _one_hot(
                self.goals.gesture[event_index], 3, dtype=tip.dtype)
            target_direction = self.goals.direction[event_index]
        else:
            target_audible = target_traversal
            gesture = torch.zeros(self.num_envs, 3, device=self.device)
            gesture[:, 0] = 1.0
            target_direction = torch.full(
                (self.num_envs,), DIRECTION_DOWN,
                dtype=torch.long, device=self.device)
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
        target_time = self._current_target_time()
        timed = self.curriculum_stage in STAGES[3:]
        left_tolerance, right_tolerance = self._current_timing_tolerances()
        if timed:
            time_to = (target_time - self.song_time_s).clamp(-1.0, 2.0)
            window_open = (
                target_time - left_tolerance - self.song_time_s).clamp(-1.0, 2.0)
            window_close = (
                target_time + right_tolerance - self.song_time_s).clamp(-1.0, 2.0)
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
        detector_armed = (
            self.detector.state == DETECTOR_ARMED).to(tip.dtype)
        observation = torch.cat([
            stage,
            tip,
            velocity,
            target_one_hot,
            target_traversal,
            target_audible,
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
            detector_armed,
            self._last_release.to(tip.dtype),
            self._lookahead_observation(1),
            self._lookahead_observation(2),
        ], dim=-1)
        if observation.shape[1] != self.strike_obs_dim:
            raise RuntimeError("strike goal observation changed shape")
        return self.sanitize_finite(observation)

    def compute_observations(self):
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
        self._timing_count[ids] = (
            self._timing_count[ids] + 1).clamp_max(self._timing_capacity)

    def _episode_metrics(self, done):
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
        for output_index, env_id in enumerate(ids.detach().cpu().tolist()):
            count = int(self._timing_count[env_id].item())
            if count:
                values = self._timing_abs_ms[env_id, :count]
                timing_mae[output_index] = values.mean()
                timing_p95[output_index] = torch.quantile(values, 0.95)
        grip_rate = (
            self.metric_grip_success_frames[ids]
            / self.metric_grip_frames[ids].clamp_min(1.0))
        ready_rate = self.metric_ready_success[ids].clamp(0.0, 1.0)
        zone_attempts = self.metric_zone_attempts[ids]
        zone_rate = self.metric_zone_hits[ids] / zone_attempts.clamp_min(1.0)
        zone_quality = (
            self.metric_zone_quality_sum[ids]
            / zone_attempts.clamp_min(1.0))
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
        strum_protected_rate = (
            self.metric_strum_protected_crossings[ids] / strum_attempts)
        strum_duplicate_rate = (
            self.metric_strum_duplicate_crossings[ids] / strum_attempts)

        if self.curriculum_stage == STAGES[0]:
            recent_frames = torch.minimum(
                self.progress_buf[ids],
                torch.full_like(self.progress_buf[ids],
                                self._grip_history_length))
            recent_success = self._grip_success_history[ids].sum(dim=1)
            curriculum_success = (
                recent_success >= (0.8 * recent_frames.float()).ceil()
            ) & (recent_frames > 0)
        elif self.curriculum_stage == STAGES[1]:
            curriculum_success = ready_rate >= 1.0
        elif self.curriculum_stage == STAGES[2]:
            curriculum_success = (
                (ready_rate >= 1.0)
                & (recall >= 1.0 - 1e-6)
                & (fp <= 0.0))
        elif self.curriculum_stage == STAGES[3]:
            curriculum_success = (
                (ready_rate >= 1.0)
                & (f1 >= 1.0 - 1e-6)
                & (timing_p95 <= self.timing_tolerance_ms))
        else:
            curriculum_success = (
                (ready_rate >= 1.0)
                & (f1 >= 0.98)
                & (timing_p95 <= self.timing_tolerance_ms)
                & (zone_rate >= 0.99))
        return {
            "strike_grip_success_rate": grip_rate,
            "strike_tip_ready_success_rate": ready_rate,
            "strike_precision": precision,
            "strike_release_recall": recall,
            "strike_false_positive_rate": false_positive_rate,
            "strike_episode_f1": f1,
            "strike_timing_mae_ms": timing_mae,
            "strike_timing_p95_ms": timing_p95,
            "strike_zone_success_rate": zone_rate,
            "strike_zone_mean_quality": zone_quality,
            "strike_single_precision": single_precision,
            "strike_single_recall": single_recall,
            "strike_single_f1": single_f1,
            "strike_single_event_count": single_tp + single_fn,
            "strike_strum_completion_rate": strum_completion,
            "strike_strum_traversal_recall": strum_traversal_recall,
            "strike_strum_order_accuracy": strum_order_accuracy,
            "strike_strum_direction_accuracy": strum_direction_accuracy,
            "strike_strum_protected_crossing_rate": strum_protected_rate,
            "strike_strum_duplicate_crossing_rate": strum_duplicate_rate,
            "strike_strum_event_count": strum_events,
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
        release_context = strike_release_recovery_context(
            release,
            detection["subframe_t"],
            detection["crossing_pos_g"],
            detection["direction"])
        physical_release = release_context["released"]
        recovery_release = (
            physical_release & (self.curriculum_stage in STAGES[2:]))
        self._previous_tip_g.copy_(tip)
        self._previous_tip_valid.fill_(True)
        self._last_release.copy_(release)

        grip = self.grip_reference.measure(
            self.dof_state.view(self.num_envs, self.n_dof, 2)[:, :, 0])
        self.metric_grip_success_frames += grip["grip_success"].float()
        self.metric_grip_frames += 1.0
        history_slot = (
            (self.progress_buf - 1) % self._grip_history_length).long()
        rows = torch.arange(self.num_envs, device=self.device)
        self._grip_success_history[rows, history_slot] = grip["grip_success"]

        target_time = self._current_target_time()
        target_string = self._current_target_string()
        motion_target_string, _, _, ready, entry, exit_point = (
            self._current_target_geometry())
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
            & (self.curriculum_stage != STAGES[0]))
        self.metric_ready_success = torch.maximum(
            self.metric_ready_success, ready_pulse.float())
        ready_acquired = self.metric_ready_success > 0.0
        ready_latched = (
            (self.motor_phase == PHASE_READY)
            & (self.ready_streak >= self.ready_hold_frames)
            & (self.curriculum_stage in STAGES[2:]))
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
        target_distance = torch.linalg.vector_norm(tip - phase_target, dim=-1)
        ready_quality = (
            0.4 * torch.exp(-(ready_distance / 0.120) ** 2)
            + 0.6 * torch.exp(-(ready_distance / 0.025) ** 2))
        reach_potential = torch.exp(
            -target_distance / max(self.ready_distance, 1e-6))
        reach_progress = strike_reach_potential_delta(
            self._previous_reach_potential,
            reach_potential,
            self._target_distance_valid,
            discount=self.reward_fn.reach_discount)
        self._previous_reach_potential.copy_(reach_potential)
        self._target_distance_valid.fill_(True)

        target_event_index = self.event_index.clamp(
            0, self.goals.num_events - 1)
        target_columns = self._current_target_masks()
        # if self.curriculum_stage == STAGES[4]:
        if self.curriculum_stage in SONG_GOAL_STAGES:
            target_gesture = self.goals.gesture[target_event_index]
            target_direction = self.goals.direction[target_event_index]
        else:
            target_gesture = torch.zeros(
                self.num_envs, dtype=torch.long, device=self.device)
            target_direction = torch.full(
                (self.num_envs,), DIRECTION_DOWN,
                dtype=torch.long, device=self.device)
        ordered_release = strike_ordered_release_progress(
            self._event_release_mask,
            release,
            detection["subframe_t"],
            detection["direction"],
            target_columns,
            target_direction,
        )
        accepted_release = ordered_release["accepted_release"]
        accumulated_release = ordered_release["accumulated_release"]
        required_complete = ordered_release["complete"]
        first_release = accepted_release.any(dim=1) & ~self._event_onset_valid
        masked_subframe = torch.where(
            accepted_release,
            detection["subframe_t"],
            torch.full_like(detection["subframe_t"], float("inf")))
        onset_subframe = masked_subframe.min(dim=1).values
        onset_time = self.song_time_s + onset_subframe / self.SIM_HZ
        self._event_onset_time_s[first_release] = onset_time[first_release]
        self._event_onset_valid |= accepted_release.any(dim=1)
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
        target_crossing_time = self._event_onset_time_s
        timing_error_s = target_crossing_time - target_time
        left_tolerance, right_tolerance = self._current_timing_tolerances()
        timing_ok = (
            timing_error_s >= -left_tolerance
        ) & (timing_error_s <= right_tolerance)
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
        timing_gate = strike_timing_gate(
            physical_target_candidate,
            timing_ok,
            timing_required=self.curriculum_stage in STAGES[3:],
        )
        timing_sample = timing_gate["timing_sample"]
        target_candidate = timing_gate["success_candidate"]
        zone_gate = strike_lane_gate(
            target_candidate,
            zone_allowed,
            crossing_y,
            self.target_lane_y,
            core_half_width=self.lane_core_half_width,
            allowed_half_width=self.lane_allowed_half_width,
        )
        lane_allowed = zone_gate["lane_allowed"]
        lane_quality = zone_gate["lane_quality"]
        zone_attempt = torch.zeros_like(target_candidate)
        target_hit = target_candidate
        # if self.curriculum_stage == STAGES[4]:
        if self.curriculum_stage in SONG_GOAL_STAGES:
            zone_attempt = target_candidate
            target_hit = target_candidate & self._event_zone_valid
            lane_allowed = self._event_zone_valid
            lane_quality = self._event_zone_quality

        release_count = release.sum(dim=1)
        blocked_release_count = detection["blocked_wait_rearm"].sum(dim=1)
        wrong_count = sum(
            ordered_release[name]
            for name in (
                "protected_crossing_count",
                "wrong_direction_count",
                "order_violation_count",
                "duplicate_crossing_count",
            ))
        miss_pulse = torch.zeros(
            self.num_envs, dtype=torch.bool, device=self.device)
        next_song_time = self.song_time_s + 1.0 / self.SIM_HZ
        if self.curriculum_stage in STAGES[3:]:
            miss_pulse = (
                ~self.event_resolved
                & ~target_hit
                & (next_song_time > target_time + right_tolerance))


        stage_timeout = self.progress_buf >= self.max_episode_length
        ready_resolution = None
        if self.curriculum_stage == STAGES[1]:
            ready_resolution = strike_ready_episode_resolution(
                stage_timeout,
                self.metric_ready_success > 0.0)
            miss_pulse |= ready_resolution["miss"]
        elif self.curriculum_stage == STAGES[2]:
            miss_pulse |= (
                stage_timeout & ~self.event_resolved & ~target_hit)

        newly_resolved = target_hit | miss_pulse
        wrong_termination_active = torch.full(
            (self.num_envs,),
            bool(
                self.wrong_crossing_termination_enabled
                # and self.curriculum_stage == STAGES[4]
                and self.curriculum_stage in SONG_GOAL_STAGES
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
        )
        self._wrong_crossing_total.copy_(
            wrong_termination_state["total_wrong"])
        self._wrong_crossing_resolved_events.copy_(
            wrong_termination_state["resolved_events"])
        self._wrong_crossing_consecutive_events.copy_(
            wrong_termination_state["consecutive_wrong_events"])
        self._event_had_wrong_crossing.copy_(
            wrong_termination_state["event_had_wrong"])
        wrong_crossing_termination = wrong_termination_state["termination"]
        # if self.curriculum_stage == STAGES[4]:
        if self.curriculum_stage in SONG_GOAL_STAGES:
            recovery_release = physical_release & required_complete
        self.metric_tp += target_hit.float()
        self.metric_fp += wrong_count
        self.metric_fn += miss_pulse.float()
        self.metric_zone_attempts += zone_attempt.float()
        self.metric_zone_hits += target_hit.float()
        self.metric_zone_quality_sum += (
            lane_quality * zone_attempt.float())
        is_strum = target_gesture == 1
        is_single = ~is_strum
        self.metric_single_tp += (target_hit & is_single).float()
        self.metric_single_fn += (miss_pulse & is_single).float()
        self.metric_single_fp += wrong_count * is_single.float()
        resolved_strum = newly_resolved & is_strum
        self.metric_strum_events += resolved_strum.float()
        self.metric_strum_completed += (target_hit & is_strum).float()
        self.metric_strum_traversal_required += (
            target_columns.sum(dim=1).float() * resolved_strum.float())
        self.metric_strum_traversal_completed += (
            accumulated_release.sum(dim=1).float() * resolved_strum.float())
        self.metric_strum_order_violations += (
            ordered_release["order_violation_count"] * is_strum.float())
        self.metric_strum_direction_violations += (
            ordered_release["wrong_direction_count"] * is_strum.float())
        self.metric_strum_protected_crossings += (
            ordered_release["protected_crossing_count"] * is_strum.float())
        self.metric_strum_duplicate_crossings += (
            ordered_release["duplicate_crossing_count"] * is_strum.float())
        self.metric_strum_release_attempts += (
            release.sum(dim=1).float() * is_strum.float())



        self._record_timing(timing_sample, timing_error_s)
        self.event_resolved |= newly_resolved



        self.recovery_count = strike_completed_recovery_frames(
            action_phase,
            self.recovery_count,
            release_recover_phase=PHASE_RELEASE_RECOVER)
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
        # if self.curriculum_stage == STAGES[4]:
        if self.curriculum_stage in SONG_GOAL_STAGES:
            self._advance_a4_events(newly_resolved, recovery_release)
            recovery_rearmed = self._recovery_rearmed()
            quota = (
                self.goals.num_events if self.evaluation_full_song
                else min(self.a4_events_per_episode, self.goals.num_events))
            final_event_resolved = (
                self.event_resolved
                & ((self.episode_event_count >= quota)
                   | (self.event_index >= self.goals.num_events - 1)))
            recovery_finished = (
                (self.motor_phase != PHASE_RELEASE_RECOVER)
                | ((self.recovery_count >= self.recovery_frames)
                   & recovery_rearmed))
            self._timeline_finished |= (
                final_event_resolved & recovery_finished)

        reward, reward_terms = self.reward_fn.compute(
            self.curriculum_stage,
            grip_quality=grip["grip_quality"],
            reach_progress=reach_progress,
            ready_quality=ready_quality,
            ready_pulse=ready_pulse,
            ready_acquired=ready_acquired,
            target_hit=target_hit,
            wrong_crossing_count=wrong_count,
            miss_pulse=miss_pulse,
            timing_error_s=timing_error_s,
            zone_quality=lane_quality,
            zone_attempt=zone_attempt,
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
        reward_nonfinite = ~torch.isfinite(reward).all(dim=1)
        nonfinite |= reward_nonfinite

        if self.curriculum_stage in STAGES[3:]:
            self.song_time_s.copy_(next_song_time)
        # if self.curriculum_stage == STAGES[4]:
        if self.curriculum_stage in SONG_GOAL_STAGES:
            release_to_approach = self._release_to_approach(
                self._current_target_time())
            self.motor_phase = torch.where(
                release_to_approach,
                torch.full_like(self.motor_phase, PHASE_APPROACH),
                self.motor_phase)
            self._recovery_context_valid[release_to_approach] = False
            self._target_distance_valid[release_to_approach] = False
        elif self.curriculum_stage in STAGES[2:4]:
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
            self._target_distance_valid[retry_after_recovery] = False

        if self.curriculum_stage == STAGES[0]:
            stage_done = stage_timeout
        elif self.curriculum_stage == STAGES[1]:



            stage_done = ready_resolution["done"]
        elif self.curriculum_stage in STAGES[2:4]:
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
        done = stage_done | base_reasons["base_termination"] | failure_termination
        goal_finished = stage_done & ~failure_termination
        if self.curriculum_stage == STAGES[1]:
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
        post_target_string = self._current_target_string()
        post_motion_target_string, _post_motion_lane_y = (
            self._current_motion_target())
        info = {
            "diagnostic_active": torch.ones(
                self.num_envs, dtype=torch.bool, device=self.device),
            "curriculum_diagnostic_enabled": ~nonfinite,
            "grip_quality": grip["grip_quality"],
            "grip_success_rate": grip_rate,
            "grip_pinch_rms_rad": grip["grip_pinch_rms_rad"],
            "grip_free_rms_rad": grip["grip_free_rms_rad"],
            "tip_ready_success_rate": ready_rate,
            "release_recall": recall,
            "false_positive_rate": false_positive_rate,
            "strike_f1": f1,
            "timing_p95_ms": timing_p95_live,
            "zone_success_rate": zone_rate,
            "tip_target_distance": target_distance,
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
            "wrong_crossing_count": wrong_count,
            "wrong_crossing_rate": wrong_termination_state["wrong_rate"],
            "wrong_crossing_termination": wrong_crossing_termination,
            "strum_order_violation_count": ordered_release[
                "order_violation_count"],
            "strum_wrong_direction_count": ordered_release[
                "wrong_direction_count"],
            "strum_protected_crossing_count": ordered_release[
                "protected_crossing_count"],
            "strum_duplicate_crossing_count": ordered_release[
                "duplicate_crossing_count"],
            "miss": miss_pulse,
            "timing_error_ms": torch.where(
                timing_sample,
                timing_error_s * 1000.0,
                torch.zeros_like(timing_error_s)),
            "timing_sample": timing_sample,
            "zone_quality": lane_quality,
            "zone_global_quality": global_zone_quality,
            "zone_lane_allowed": lane_allowed,
            "motor_phase": self.motor_phase.clone(),
            "target_string": target_string.clone(),
            "target_gesture": target_gesture.clone(),
            "target_traversal_mask": target_columns.clone(),
            "target_release_progress_mask": accumulated_release.clone(),
            "accepted_release_mask": accepted_release.clone(),
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
        info.update(self._episode_metrics(done))
        info["episode_timing_count"] = (
            self._timing_count[env_ids].clone())
        info["episode_timing_abs_ms"] = (
            self._timing_abs_ms[env_ids].clone())
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
