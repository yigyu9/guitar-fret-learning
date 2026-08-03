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

The observation and 30-DOF action layouts stay unchanged throughout the five
acquisition stages.  Stage masks and rewards change, never tensor shapes.
"""
from __future__ import annotations

import math
from typing import Dict, Iterable, Optional, Tuple

import torch
from isaacgym import gymtorch

from ..base import GuitarEnvBase
from ..collision import (
    DISABLED_COLLISION_FILTER,
    GUITAR_COLLISION_FILTER,
    HUMANOID_COLLISION_FILTER,
    THUMB_SUPPORT_PROXY_BODY,
)
from ..rewards.strike import PickGripReference, STAGES, StrikeReward
from ..strike_events import (
    strike_ready_episode_resolution,
    strike_ready_latch,
    strike_resolved_episode_done,
    strike_timing_gate,
)
from ..strike_detector import (
    DIRECTION_DOWN,
    PickStrikeDetector,
    strike_lane_gate,
    strike_lane_quality,
)
from ..strike_goals import N_GUITAR_STRINGS, StrikeGoalSequence


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
        "curriculum_success_rate",
    )
    episode_reason_keys = (
        "goal_finished",
        "failure_termination",
        "early_timeout",
        "nonfinite",
        "velocity_blowup",
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
        "release_count",
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
            zone=None,
            trajectory=None,
            detector=None,
            reward=None,
            episode=None,
            failure_termination_penalty=-10.0,
            random_start=True):
        self._config_zone = dict(zone or {})
        self._config_trajectory = dict(trajectory or {})
        self._config_detector = dict(detector or {})
        self._config_episode = dict(episode or {})
        self.random_start = bool(random_start)
        self.failure_termination_penalty = float(failure_termination_penalty)
        if (not math.isfinite(self.failure_termination_penalty)
                or self.failure_termination_penalty > 0.0):
            raise ValueError(
                "failure_termination_penalty must be finite and non-positive")

        # The exact stage horizon is applied after all task state exists.
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
        self._action_is_hand = torch.tensor(
            [name.startswith("RH:") for name in control_names],
            dtype=torch.bool, device=self.device)

        # The broad historical pluck-range box is only a visualization.  Its
        # collision shape otherwise blocks the virtual marker before it can
        # cross the fixed string segments.
        self._disable_pluck_range_collision()

        self.goals = StrikeGoalSequence(goal_path, device=device)
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
            float(self._config_zone.get("allowed_y_min_m", -0.385)),
            float(self._config_zone.get("allowed_y_max_m", -0.255)),
        )
        self.preferred_y = (
            float(self._config_zone.get("preferred_y_min_m", -0.355)),
            float(self._config_zone.get("preferred_y_max_m", -0.295)),
        )
        self.phrase_lane_y = float(
            self._config_zone.get("phrase_lane_y_m", -0.325))
        self.lane_core_half_width = float(
            self._config_zone.get("lane_core_half_width_m", 0.006))
        self.lane_allowed_half_width = float(
            self._config_zone.get("lane_allowed_half_width_m", 0.0125))
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

        self.ready_across = float(
            self._config_trajectory.get("ready_across_offset_m", 0.003))
        self.entry_across = float(
            self._config_trajectory.get("entry_across_offset_m", 0.0015))
        self.exit_across = float(
            self._config_trajectory.get("exit_across_offset_m", 0.003))
        self.ready_height = float(
            self._config_trajectory.get("ready_height_m", 0.008))
        self.crossing_depth = float(
            self._config_trajectory.get("crossing_depth_m", 0.0015))
        self.ready_distance = float(
            self._config_trajectory.get("ready_distance_m", 0.010))
        self.entry_distance = float(
            self._config_trajectory.get("entry_distance_m", 0.006))
        self.ready_hold_frames = int(
            self._config_trajectory.get("ready_hold_frames", 6))
        self.recovery_frames = int(
            self._config_trajectory.get("recovery_frames", 12))
        self.approach_lead_s = float(
            self._config_trajectory.get("approach_lead_s", 0.20))
        positive_trajectory = (
            self.ready_across, self.entry_across, self.exit_across,
            self.ready_height, self.crossing_depth,
            self.ready_distance, self.entry_distance)
        if any(not math.isfinite(value) or value <= 0.0
               for value in positive_trajectory):
            raise ValueError("strike trajectory distances must be finite and positive")
        if self.ready_hold_frames < 1 or self.recovery_frames < 1:
            raise ValueError("strike hold/recovery frames must be positive")

        min_speed = float(
            self._config_detector.get("min_across_speed_m_s", 0.05))
        if "min_displacement_m" in self._config_detector:
            min_speed = max(
                min_speed,
                float(self._config_detector["min_displacement_m"])
                * self.SIM_HZ)
        self.detector = PickStrikeDetector(
            num_envs=self.num_envs,
            num_strings=N_GUITAR_STRINGS,
            device=self.device,
            min_across_speed=min_speed,
            min_depth=float(
                self._config_detector.get("min_depth_m", 0.001)),
            rearm_separation=float(
                self._config_detector.get("rearm_distance_m", 0.003)),
            rearm_min_frames=int(
                self._config_detector.get("rearm_min_frames", 2)),
            parallel_epsilon=float(
                self._config_detector.get("parallel_epsilon", 1e-9)),
            allowed_y=self.allowed_y,
            preferred_y=self.preferred_y,
        )
        self.goals.require_physical_rearm_spacing(
            self.detector.rearm_min_frames)
        self.reward_fn = StrikeReward(reward or {
            "grip_weight": {stage: 0.0 for stage in STAGES},
            "reach_weight": 0.2,
            "ready_quality_weight": 0.75,
            "crossing_reward": 1.0,
            "completion_reward": 0.15,
            "wrong_crossing_penalty": 0.35,
            "miss_penalty": 0.5,
            "zone_weight": 0.2,
            "timing_core_ms": 20.0,
        })

        self.stage_horizons = {
            stage: int(self._config_episode.get(stage, default))
            for stage, default in zip(STAGES, (120, 180, 240, 240, 600))
        }
        if any(value < 1 for value in self.stage_horizons.values()):
            raise ValueError("every strike stage horizon must be positive")
        self.a4_events_per_episode = int(
            self._config_episode.get("a4_events_per_episode", 8))
        self.timed_lead_frames = int(
            self._config_episode.get("timed_lead_frames", 30))
        if self.a4_events_per_episode < 1 or self.timed_lead_frames < 0:
            raise ValueError("invalid strike episode event/lead configuration")
        self.full_song_start_time_s = (
            float(self.goals.time[0].item())
            - self.timed_lead_frames / self.SIM_HZ)

        self.curriculum_stage = STAGES[0]
        self.timing_tolerance_ms = 100.0
        self.evaluation_full_song = False
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
        self.recovery_count = torch.zeros(n, dtype=torch.long, device=d)
        self._timeline_finished = torch.zeros(n, dtype=torch.bool, device=d)
        self._previous_tip_g = torch.zeros(n, 3, device=d)
        self._tip_velocity_g = torch.zeros(n, 3, device=d)
        self._previous_tip_valid = torch.zeros(n, dtype=torch.bool, device=d)
        self._last_release = torch.zeros(
            n, N_GUITAR_STRINGS, dtype=torch.bool, device=d)
        self._last_target_hit = torch.zeros(n, dtype=torch.bool, device=d)
        self._last_wrong_count = torch.zeros(n, device=d)
        self._last_miss = torch.zeros(n, dtype=torch.bool, device=d)
        self._last_timing_error_s = torch.zeros(n, device=d)
        self._last_zone_quality = torch.zeros(n, device=d)
        self._previous_target_distance = torch.zeros(n, device=d)
        self._target_distance_valid = torch.zeros(n, dtype=torch.bool, device=d)

        self._metric_names = (
            "metric_grip_success_frames", "metric_grip_frames",
            "metric_ready_success", "metric_tp", "metric_fp", "metric_fn",
            "metric_zone_attempts", "metric_zone_hits",
            "metric_zone_quality_sum",
        )
        for name in self._metric_names:
            setattr(self, name, torch.zeros(n, device=d))
        self._grip_history_length = 30
        self._grip_success_history = torch.zeros(
            n, self._grip_history_length, dtype=torch.bool, device=d)
        # At most one target-string timing attempt can be observed per control
        # frame.  Keep enough raw samples for even a full-song evaluation so
        # p95 is computed from the uncensored attempt distribution instead of
        # silently overwriting its tail.
        full_song_frames = int(math.ceil(
            (float(self.goals.time[-1].item())
             + max(self.timing_tolerance_ms, 100.0) / 1000.0
             + self.recovery_frames / self.SIM_HZ
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

    # ------------------------------------------------------------------
    # Asset and geometry contracts
    # ------------------------------------------------------------------
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

    def _string_lane_geometry(self):
        start, end = self.string_segments_g()
        denominator = end[..., 1] - start[..., 1]
        if torch.any(denominator.abs() < 1e-8):
            raise RuntimeError("a guitar string is degenerate along the strike lane")
        u = (
            (self.target_lane_y[:, None] - start[..., 1]) / denominator
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
        lane, normal = self._string_lane_geometry()
        target_string = self._current_target_string()
        rows = torch.arange(self.num_envs, device=self.device)
        center = lane[rows, target_string]
        across = normal[rows, target_string]
        ready = center - self.ready_across * across
        ready = ready.clone()
        ready[:, 2] += self.ready_height
        entry = center - self.entry_across * across
        entry = entry.clone()
        entry[:, 2] -= self.crossing_depth
        exit_point = center + self.exit_across * across
        exit_point = exit_point.clone()
        exit_point[:, 2] -= self.crossing_depth
        return target_string, center, ready, entry, exit_point

    # ------------------------------------------------------------------
    # Goal state
    # ------------------------------------------------------------------
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
        return self.goals.time[index]

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
                0.75 + 0.75 * torch.rand(
                    env_ids.numel(), generator=self.rng,
                    device=self.device))
            self.song_time_s[env_ids] = 0.0
        elif self.curriculum_stage == STAGES[4]:
            if self.evaluation_full_song:
                self.song_time_s[env_ids] = self.full_song_start_time_s
            else:
                target_time = self.goals.time[sampled]
                self.song_time_s[env_ids] = (
                    target_time - self.timed_lead_frames / self.SIM_HZ
                )
        else:
            self.song_time_s[env_ids] = 0.0
        if self.curriculum_stage == STAGES[4]:
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
        self.recovery_count[env_ids] = 0
        self._timeline_finished[env_ids] = False
        self._tip_velocity_g[env_ids] = 0.0
        self._previous_tip_valid[env_ids] = False
        self._last_release[env_ids] = False
        self._last_target_hit[env_ids] = False
        self._last_wrong_count[env_ids] = 0.0
        self._last_miss[env_ids] = False
        self._last_timing_error_s[env_ids] = 0.0
        self._last_zone_quality[env_ids] = 0.0
        self._target_distance_valid[env_ids] = False
        self.detector.reset(env_ids)
        for name in self._metric_names:
            getattr(self, name)[env_ids] = 0.0
        self._grip_success_history[env_ids] = False
        self._timing_abs_ms[env_ids] = 0.0
        self._timing_count[env_ids] = 0

    def _advance_a4_events(self, resolved, target_hit):
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
            lane_lo, lane_hi = self.preferred_y
            self.target_lane_y[continuing] = (
                lane_lo + (lane_hi - lane_lo) * torch.rand(
                    continuing.numel(), generator=self.rng,
                    device=self.device))
            # A hit keeps a short RELEASE_RECOVER phase which may overlap the
            # next approach.  A miss has no release to recover from and moves
            # directly into repositioning for the next event.
            self.motor_phase[continuing] = torch.where(
                target_hit[continuing],
                torch.full_like(
                    self.motor_phase[continuing], PHASE_RELEASE_RECOVER),
                torch.full_like(
                    self.motor_phase[continuing], PHASE_APPROACH))
            self.ready_streak[continuing] = 0
            self.event_resolved[continuing] = False
            self.recovery_count[continuing] = 0

    # ------------------------------------------------------------------
    # Curriculum and checkpoint state
    # ------------------------------------------------------------------
    def set_curriculum_stage(self, stage, tolerance_ms, reset=False):
        if stage not in STAGES:
            raise ValueError(f"unknown strike stage: {stage}")
        tolerance_ms = float(tolerance_ms)
        if not math.isfinite(tolerance_ms) or tolerance_ms <= 0.0:
            raise ValueError("timing tolerance must be finite and positive")
        changed = (
            stage != self.curriculum_stage
            or abs(tolerance_ms - self.timing_tolerance_ms) > 1e-9)
        self.curriculum_stage = str(stage)
        self.timing_tolerance_ms = tolerance_ms
        self.max_episode_length = self._stage_episode_limit()
        if reset and changed:
            return self.reset()
        return None

    def set_evaluation_mode(self, full_song=True, reset=False):
        changed = self.evaluation_full_song != bool(full_song)
        self.evaluation_full_song = bool(full_song)
        self.max_episode_length = self._stage_episode_limit()
        if reset and changed:
            return self.reset()
        return None

    def _stage_episode_limit(self):
        if self.curriculum_stage == STAGES[4] and self.evaluation_full_song:
            final_time_s = float(self.goals.time[-1].item())
            required = int(math.ceil(
                (final_time_s
                 + self.timing_tolerance_ms / 1000.0
                 + self.recovery_frames / self.SIM_HZ
                 - self.full_song_start_time_s)
                * self.SIM_HZ)) + 2
            return max(
                required,
                self.stage_horizons[STAGES[4]],
            )
        return self.stage_horizons[self.curriculum_stage]

    def curriculum_state_dict(self):
        return {
            "schema": "tab2body.strike_environment_state.v1",
            "curriculum_stage": self.curriculum_stage,
            "timing_tolerance_ms": float(self.timing_tolerance_ms),
            "evaluation_full_song": bool(self.evaluation_full_song),
            "random_start": bool(self.random_start),
            "rng_state": self.rng.get_state(),
            "reset_generation": self._reset_generation.detach().cpu(),
        }

    def load_curriculum_state_dict(self, state):
        if state.get("schema") != "tab2body.strike_environment_state.v1":
            raise ValueError("unsupported strike environment checkpoint state")
        if bool(state.get("random_start")) != self.random_start:
            raise ValueError("strike random_start changed across checkpoint resume")
        self.curriculum_stage = str(state["curriculum_stage"])
        if self.curriculum_stage not in STAGES:
            raise ValueError("checkpoint contains an unknown strike stage")
        self.timing_tolerance_ms = float(state["timing_tolerance_ms"])
        self.evaluation_full_song = bool(state.get("evaluation_full_song", False))
        self.max_episode_length = self._stage_episode_limit()
        rng_state = state["rng_state"]
        if (not isinstance(rng_state, torch.Tensor)
                or rng_state.dtype != torch.uint8
                or rng_state.ndim != 1):
            raise ValueError(
                "checkpoint RNG state must be a one-dimensional ByteTensor")
        # torch.load(map_location="cuda") also moves generator state tensors,
        # while Generator.set_state requires its serialized ByteTensor on CPU
        # even for a CUDA generator.
        self.rng.set_state(rng_state.detach().cpu())
        generation = state["reset_generation"].to(
            device=self.device, dtype=torch.long)
        if generation.shape != self._reset_generation.shape:
            raise ValueError("strike reset-generation shape changed")
        self._reset_generation.copy_(generation)
        return self.reset()

    # ------------------------------------------------------------------
    # Reset, action mask and observations
    # ------------------------------------------------------------------
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
        names += [f"strike.target_string.{index}" for index in range(6)]
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
        names += [f"strike.detector_armed.{index}" for index in range(6)]
        names += [f"strike.last_release.{index}" for index in range(6)]
        for lookahead in (1, 2):
            names.append(f"strike.lookahead_{lookahead}.delta_s")
            names += [
                f"strike.lookahead_{lookahead}.string.{index}"
                for index in range(6)]
        return tuple(names)

    def _lookahead_observation(self, offset):
        if self.curriculum_stage != STAGES[4]:
            return torch.zeros(
                self.num_envs, 7, device=self.device)
        index = self.event_index + int(offset)
        valid = index < self.goals.num_events
        safe = index.clamp(0, self.goals.num_events - 1)
        delta = (self.goals.time[safe] - self.song_time_s).clamp(-1.0, 2.0)
        delta = torch.where(valid, delta, torch.zeros_like(delta))
        string = _one_hot(
            self.goals.string[safe], N_GUITAR_STRINGS,
            dtype=self.song_time_s.dtype)
        string = string * valid[:, None]
        return torch.cat([delta[:, None], string], dim=-1)

    def _build_strike_observation(self, tip_override=None, velocity_override=None):
        tip = (tip_override if tip_override is not None else
               self.to_guitar_frame(self.hbody_pos("RH:pick")[:, None])[:, 0])
        velocity = (
            velocity_override if velocity_override is not None
            else self._tip_velocity_g)
        target_string, _, ready, entry, exit_point = (
            self._current_target_geometry())
        stage_index = torch.full(
            (self.num_envs,), STAGES.index(self.curriculum_stage),
            dtype=torch.long, device=self.device)
        stage = _one_hot(stage_index, len(STAGES), dtype=tip.dtype)
        target_one_hot = _one_hot(
            target_string, N_GUITAR_STRINGS, dtype=tip.dtype)
        phase = _one_hot(self.motor_phase, N_PHASES, dtype=tip.dtype)
        target_time = self._current_target_time()
        timed = self.curriculum_stage in STAGES[3:]
        tolerance_s = self.timing_tolerance_ms / 1000.0
        if timed:
            time_to = (target_time - self.song_time_s).clamp(-1.0, 2.0)
            window_open = (
                target_time - tolerance_s - self.song_time_s).clamp(-1.0, 2.0)
            window_close = (
                target_time + tolerance_s - self.song_time_s).clamp(-1.0, 2.0)
            tolerance = torch.full_like(time_to, tolerance_s)
        else:
            time_to = torch.zeros(self.num_envs, device=self.device)
            window_open = torch.zeros_like(time_to)
            window_close = torch.zeros_like(time_to)
            tolerance = torch.zeros_like(time_to)
        lane_offset = tip[:, 1] - self.target_lane_y
        direction = torch.tensor(
            [1.0, 0.0], device=self.device, dtype=tip.dtype
        )[None].expand(self.num_envs, -1)
        detector_armed = (self.detector.state == 0).to(tip.dtype)
        observation = torch.cat([
            stage,
            tip,
            velocity,
            target_one_hot,
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

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------
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
            curriculum_success = (recall >= 1.0 - 1e-6) & (fp <= 0.0)
        elif self.curriculum_stage == STAGES[3]:
            curriculum_success = (
                (f1 >= 1.0 - 1e-6)
                & (timing_p95 <= self.timing_tolerance_ms))
        else:
            curriculum_success = (
                (f1 >= 0.98)
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
            "curriculum_success_rate": curriculum_success.float(),
        }

    # ------------------------------------------------------------------
    # One control step
    # ------------------------------------------------------------------
    def step(self, actions):
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

        target_string, _, ready, entry, exit_point = (
            self._current_target_geometry())
        ready_distance = torch.linalg.vector_norm(tip - ready, dim=-1)
        previous_entry_distance = torch.linalg.vector_norm(
            previous_tip - entry, dim=-1)
        phase_before = self.motor_phase.clone()
        target_time = self._current_target_time()
        release_to_approach = (
            (phase_before == PHASE_RELEASE_RECOVER)
            & (self.curriculum_stage == STAGES[4])
            & ~self.event_resolved
            & ((target_time - self.song_time_s) <= self.approach_lead_s))
        self.motor_phase = torch.where(
            release_to_approach,
            torch.full_like(self.motor_phase, PHASE_APPROACH),
            self.motor_phase)
        at_ready = ready_distance <= self.ready_distance
        ready_state = strike_ready_latch(
            at_ready,
            grip["grip_success"],
            self.ready_streak,
            self.metric_ready_success > 0.0,
            hold_frames=self.ready_hold_frames,
        )
        self.ready_streak.copy_(ready_state["ready_streak"])
        # The pulse is an episode-level acquisition event, not a repeatable
        # per-visit bonus.  A0 diagnoses the pose only and never emits it.
        ready_pulse = (
            ready_state["ready_pulse"]
            & (self.curriculum_stage != STAGES[0]))
        self.metric_ready_success = torch.maximum(
            self.metric_ready_success, ready_pulse.float())
        ready_latched = (
            (self.motor_phase == PHASE_READY)
            & (self.ready_streak >= self.ready_hold_frames)
            & (self.curriculum_stage in STAGES[2:]))
        self.motor_phase = torch.where(
            ready_latched,
            torch.full_like(self.motor_phase, PHASE_APPROACH),
            self.motor_phase)

        phase_target = torch.where(
            (self.motor_phase == PHASE_READY)[:, None], ready,
            torch.where(
                (self.motor_phase == PHASE_APPROACH)[:, None],
                entry, exit_point))
        target_distance = torch.linalg.vector_norm(tip - phase_target, dim=-1)
        ready_quality = (
            0.4 * torch.exp(-(ready_distance / 0.120) ** 2)
            + 0.6 * torch.exp(-(ready_distance / 0.025) ** 2))
        reach_progress = torch.where(
            self._target_distance_valid,
            (self._previous_target_distance - target_distance)
            / max(self.ready_distance, 1e-6),
            torch.zeros_like(target_distance))
        self._previous_target_distance.copy_(target_distance)
        self._target_distance_valid.fill_(True)

        target_columns = _one_hot(
            target_string, N_GUITAR_STRINGS,
            dtype=torch.bool)
        down = detection["direction"] == DIRECTION_DOWN
        release_target = (release & target_columns & down).any(dim=1)
        rows = torch.arange(self.num_envs, device=self.device)
        target_subframe = detection["subframe_t"][rows, target_string]
        target_crossing_time = (
            self.song_time_s + target_subframe / self.SIM_HZ)
        timing_error_s = target_crossing_time - target_time
        tolerance_s = self.timing_tolerance_ms / 1000.0
        timing_ok = timing_error_s.abs() <= tolerance_s
        zone_allowed = detection["zone_allowed"][rows, target_string]
        global_zone_quality = detection[
            "zone_quality"][rows, target_string]
        crossing_y = detection[
            "crossing_pos_g"][rows, target_string, 1]
        lane_quality = strike_lane_quality(
            crossing_y,
            self.target_lane_y,
            core_half_width=self.lane_core_half_width,
            allowed_half_width=self.lane_allowed_half_width,
        )
        lane_allowed = (
            (crossing_y - self.target_lane_y).abs()
            <= self.lane_allowed_half_width)
        eligible_phase = self.motor_phase == PHASE_APPROACH
        entry_ready = (
            valid_previous
            & (previous_entry_distance <= self.entry_distance))

        physical_target_candidate = (
            release_target & eligible_phase & entry_ready
            & ~self.event_resolved & ~nonfinite)
        timing_gate = strike_timing_gate(
            physical_target_candidate,
            timing_ok,
            timing_required=self.curriculum_stage in STAGES[3:],
        )
        timing_sample = timing_gate["timing_sample"]
        target_candidate = timing_gate["success_candidate"]
        zone_attempt = torch.zeros_like(target_candidate)
        target_hit = target_candidate
        if self.curriculum_stage == STAGES[4]:
            zone_gate = strike_lane_gate(
                target_candidate,
                zone_allowed,
                crossing_y,
                self.target_lane_y,
                core_half_width=self.lane_core_half_width,
                allowed_half_width=self.lane_allowed_half_width,
            )
            zone_attempt = zone_gate["attempt"]
            target_hit = zone_gate["hit"]
            lane_allowed = zone_gate["lane_allowed"]
            lane_quality = zone_gate["lane_quality"]

        release_count = release.sum(dim=1)
        wrong_count = (
            release_count - target_hit.long()).clamp_min(0).float()
        miss_pulse = torch.zeros(
            self.num_envs, dtype=torch.bool, device=self.device)
        next_song_time = self.song_time_s + 1.0 / self.SIM_HZ
        if self.curriculum_stage in STAGES[3:]:
            miss_pulse = (
                ~self.event_resolved
                & ~target_hit
                & (next_song_time > target_time + tolerance_s))

        # The free-crossing target remains eligible for the whole episode.
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
        self.metric_tp += target_hit.float()
        self.metric_fp += wrong_count
        self.metric_fn += miss_pulse.float()
        self.metric_zone_attempts += zone_attempt.float()
        self.metric_zone_hits += target_hit.float()
        self.metric_zone_quality_sum += (
            lane_quality * zone_attempt.float())
        # Record the onset error before applying the timing/zone success gates.
        # Otherwise every retained sample is guaranteed to lie within the
        # current tolerance and the p95 curriculum gate becomes tautological.
        self._record_timing(timing_sample, timing_error_s)
        self.event_resolved |= newly_resolved
        self.motor_phase = torch.where(
            target_hit,
            torch.full_like(self.motor_phase, PHASE_RELEASE_RECOVER),
            self.motor_phase)
        self.recovery_count = torch.where(
            self.motor_phase == PHASE_RELEASE_RECOVER,
            self.recovery_count + 1,
            torch.zeros_like(self.recovery_count))
        if self.curriculum_stage == STAGES[4]:
            self._advance_a4_events(newly_resolved, target_hit)
            quota = (
                self.goals.num_events if self.evaluation_full_song
                else min(self.a4_events_per_episode, self.goals.num_events))
            final_event_resolved = (
                self.event_resolved
                & ((self.episode_event_count >= quota)
                   | (self.event_index >= self.goals.num_events - 1)))
            recovery_finished = (
                (self.motor_phase != PHASE_RELEASE_RECOVER)
                | (self.recovery_count >= self.recovery_frames))
            self._timeline_finished |= (
                final_event_resolved & recovery_finished)

        self._last_target_hit.copy_(target_hit)
        self._last_wrong_count.copy_(wrong_count)
        self._last_miss.copy_(miss_pulse)
        self._last_timing_error_s.copy_(torch.where(
            target_hit, timing_error_s,
            torch.zeros_like(timing_error_s)))
        self._last_zone_quality.copy_(torch.where(
            zone_attempt, lane_quality, torch.zeros_like(lane_quality)))

        reward, reward_terms = self.reward_fn.compute(
            self.curriculum_stage,
            grip_quality=grip["grip_quality"],
            reach_progress=reach_progress,
            ready_quality=ready_quality,
            ready_pulse=ready_pulse,
            target_hit=target_hit,
            wrong_crossing_count=wrong_count,
            miss_pulse=miss_pulse,
            timing_error_s=timing_error_s,
            zone_quality=lane_quality,
            zone_attempt=zone_attempt,
        )
        reward_nonfinite = ~torch.isfinite(reward).all(dim=1)
        nonfinite |= reward_nonfinite

        if self.curriculum_stage in STAGES[3:]:
            self.song_time_s.copy_(next_song_time)

        if self.curriculum_stage == STAGES[0]:
            stage_done = stage_timeout
        elif self.curriculum_stage == STAGES[1]:
            # Keep success and failure episodes the same length.  Ending on
            # ready_pulse made staying just outside the 10 mm boundary more
            # profitable than succeeding under discounted return.
            stage_done = ready_resolution["done"]
        elif self.curriculum_stage in STAGES[2:4]:
            resolution = strike_resolved_episode_done(
                self.event_resolved,
                self.motor_phase,
                self.recovery_count,
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
        failure_termination = (
            base_failure | reward_nonfinite | observation_nonfinite
            | early_timeout)
        done = stage_done | base_reasons["base_termination"] | failure_termination
        goal_finished = stage_done & ~early_timeout
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
            # A bounded upper statistic is sufficient for rollout gating; the
            # exact ragged p95 is emitted at episode completion.
            timing_p95_live = self._timing_abs_ms.max(dim=1).values
        grip_rate = (
            self.metric_grip_success_frames
            / self.metric_grip_frames.clamp_min(1.0))
        ready_rate = self.metric_ready_success.clamp(0.0, 1.0)
        zone_rate = (
            self.metric_zone_hits
            / self.metric_zone_attempts.clamp_min(1.0))
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
            "reach_progress": reach_progress,
            "release_count": release_count.float(),
            "blocked_release_count":
                detection["blocked_wait_rearm"].sum(dim=1).float(),
            "target_hit": target_hit,
            "wrong_crossing_count": wrong_count,
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
            "timing_tolerance_ms": torch.full(
                (self.num_envs,), self.timing_tolerance_ms,
                device=self.device),
            "goal_finished": goal_finished,
            "timeout": base_timeout | stage_timeout,
            "early_timeout": early_timeout,
            "nonfinite": nonfinite,
            "velocity_blowup": velocity_blowup,
            "failure_termination": failure_termination,
        }
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
            "nonfinite": nonfinite,
            "velocity_blowup": velocity_blowup,
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
