"""곡별 반복 최적화를 위한 명시 운지 왼손 fret 태스크."""
from __future__ import annotations

from collections.abc import Mapping
import math

import torch
from isaacgym import gymtorch

from ..base import GuitarEnvBase
from ..collision import THUMB_PAD_BODY
from ..config import configured_kwargs
from ..goals import (
    FINGER_EVENT_TIME_SCALE_S,
    FretGoalSequence,
    goal_pair_finger_action_routing,
)
from ..metrics import (
    PressSustainTracker,
    normalized_joint_limit_usage,
    update_live_dropout_streak,
    update_wrong_press_termination,
)
from ..rewards.fret import (
    FretReward,
    adjacent_finger_action_synergy,
    cached_finger_action_teacher,
    finger_synergy_follower_mask,
    guitar_penetration_soft_cost,
    suppress_positive_reward_on_penetration,
)
from ..rewards.thumb import (
    THUMB_GEOMETRY_OBS_DIM,
    thumb_geometry_observation,
)
from ..safety import (
    ContactLoadMonitor,
    FingerBackLimitMonitor,
    FingerSelfIntersectionMonitor,
    GuitarPenetrationMonitor,
    WristSafetyBoxMonitor,
    exclude_thumb_from_generic_penetration,
    palm_inward_normal,
    update_consecutive_violation,
)


FRET_CONTROL_PREFIXES = (
    "L_Thorax", "L_Shoulder", "L_Elbow", "L_Wrist",
    "LH:thumb", "LH:index", "LH:middle", "LH:ring", "LH:pinky",
)

WRONG_PRESS_TERMINATION_STAGES = (
    "goal_pair", "transition_window", "coverage", "integration", "full_song",
)

JOINT_LIMIT_GROUP_PREFIXES = (
    ("thorax", "L_Thorax"),
    ("shoulder", "L_Shoulder"),
    ("elbow", "L_Elbow"),
    ("wrist", "L_Wrist"),
    ("thumb", "LH:thumb"),
    ("finger_1", "LH:index"),
    ("finger_2", "LH:middle"),
    ("finger_3", "LH:ring"),
    ("finger_4", "LH:pinky"),
)

FRET_OBS_BODIES = (
    "L_Wrist", "LH:palm",
    "LH:index_top", "LH:middle_top", "LH:ring_top", "LH:pinky_top",
)

FRET_THUMB_OBS_BODIES = ("LH:thumb3", "LH:thumb_top")
FRET_THUMB_RAW_OBS_DIM = 3 * len(FRET_THUMB_OBS_BODIES)
FRET_THUMB_OBS_DIM = FRET_THUMB_RAW_OBS_DIM + THUMB_GEOMETRY_OBS_DIM

# ``FretTask`` used these defaults before reward configuration was separated.
# The remaining FretReward defaults already match the former task defaults.
DEFAULT_FRET_REWARD_OVERRIDES = {
    "finger_coupling_weight": 0.015,
    "finger_coupling_coefficients": (0.15, 0.20, 0.25),
    "finger_coupling_min_speed_deg": 5.0,
    "finger_coupling_full_speed_deg": 30.0,
}

DIRECT_INFO_METRIC_KEYS = (
    "chord_ready", "target_min_separation", "curriculum_frame_success",
    "curriculum_success", "curriculum_episode_success", "thumb_reward",
    "thumb_distance", "thumb_gap", "thumb_contact_force",
    "thumb_in_back_region", "thumb_geometric_support_quality", "thumb_footprint_quality",
    "thumb_gap_quality", "thumb_support", "thumb_wrong_contact",
    "thumb_penetration", "thumb_compression", "thumb_force_quality",
    "thumb_compression_quality", "thumb_solver_force_quality", "thumb_overforce",
    "thumb_solver_overforce", "thumb_goal_gate", "thumb_geometry_ready",
    "thumb_support_ready", "thumb_press_readiness", "thumb_press_factor",
    "thumb_support_streak", "thumb_support_stable_6", "thumb_support_stable_12",
    "thumb_base_saturation_penalty", "proximal_reward", "proximal_gate",
    "finger_motion", "wrist_motion", "elbow_motion",
    "shoulder_motion", "proximal_target_distance", "hover_reward",
    "hover_gap", "hover_gate", "hover_position_reward",
    "hover_velocity_reward", "hover_outward_speed", "hover_velocity_gate",
    "release_pose_reward", "finger_coupling_reward", "finger_coupling_press_protected",
    "reference_finger_posture_quality", "reference_thumb_posture_quality",
    "reference_posture_quality", "reference_posture_penalty",
    "reference_posture_active",
    "next_goal_approach_reward", "next_goal_progress_reward", "next_goal_current_press_preserved",
    "next_goal_current_press_preservation_quality", "next_goal_current_press_preservation_gate", "next_goal_joint_preservation_quality",
    "press_class_reward", "press_class_mean_reward", "press_class_min_reward",
    "no_press_class_reward", "press_class_completion", "no_press_class_completion",
    "effective_press_class_weight", "effective_no_press_class_weight", "class_balanced_reward",
    "chord_joint_quality", "chord_bridge_bottleneck_reward", "chord_bridge_mean_reward",
    "chord_bridge_min_reward", "chord_fine_joint_reward",
    "chord_fine_joint_mean_reward", "chord_fine_joint_min_reward",
    "chord_fine_axis_min_quality", "chord_fine_broad_depth_progress",
    "goal_pair_rehearsal_anchor_reward",
    "goal_pair_rehearsal_anchor_active", "class_balance_enabled", "slip_reward",
    "goal_pair_anchor_next_reward", "goal_pair_anchor_next_active",
    "success_pose_guide_reward", "success_pose_guide_active",
    "success_pose_guide_anchor_reward",
    "success_pose_guide_anchor_active",
    "success_pose_guide_proximal_reward",
    "success_pose_guide_proximal_active",
    "slip_distance", "slip_instant", "slip_gate",
    "slip_streak", "r28_move_active", "r28_move_started",
    "r28_move_completed", "r28_pressed_endpoint_candidate", "r28_same_cell_drag",
    "r28_candidate_step_distance", "r28_confirmed_step_distance", "r28_candidate_cumulative_distance",
    "r28_confirmed_cumulative_distance", "r28_confirmed_drag_frames", "r28_drag_violation_started",
    "wrist_distance", "all_correct",
)


def goal_pair_phase_diagnostics(
        stage, metrics_enabled, rehearsal_mask, before_remaining,
        incoming_finger, next_progress_gate, current_press_preserved,
        current_press_quality, next_distance, next_progress):
    """Return MOVE-phase diagnostics without mixing in rehearsal/hold frames.

    Goal-pair episodes spend time on both sides of the transition, and static
    rehearsal episodes never transition at all.  The generic live-frame gate
    is therefore too broad for measuring whether the incoming finger moves
    toward its next target while the currently pressed fingers remain held.
    """
    if stage != "goal_pair":
        return {}
    if (next_progress_gate.ndim != 2
            or next_progress_gate.shape[1] != 4
            or next_distance.shape != next_progress_gate.shape
            or next_progress.shape != next_progress_gate.shape):
        raise ValueError(
            "goal-pair next diagnostics must have shape [N,4]")
    batch = next_progress_gate.shape[0]
    vectors = (
        metrics_enabled, rehearsal_mask, before_remaining,
        incoming_finger, current_press_preserved, current_press_quality)
    if any(value.ndim != 1 or value.shape[0] != batch for value in vectors):
        raise ValueError(
            "goal-pair phase diagnostics require matching rank-1 env state")

    transition = ~rehearsal_mask.bool()
    pretransition = before_remaining > 0
    live_transition = metrics_enabled.bool() & transition & pretransition
    diagnostics = {}
    incoming_active = []
    for finger_index in range(4):
        finger_number = finger_index + 1
        active = (
            live_transition
            & (incoming_finger == finger_number)
            & next_progress_gate[:, finger_index].bool())
        incoming_active.append(active)
        prefix = (
            f"goal_pair_transition_finger_{finger_number}_next")
        diagnostics[f"{prefix}_active"] = active
        diagnostics[f"{prefix}_distance"] = torch.where(
            active, next_distance[:, finger_index],
            torch.zeros_like(next_distance[:, finger_index]))
        diagnostics[f"{prefix}_progress"] = torch.where(
            active, next_progress[:, finger_index],
            torch.zeros_like(next_progress[:, finger_index]))

    move_active = torch.stack(incoming_active, dim=1).any(dim=1)
    diagnostics["goal_pair_pretransition_active"] = move_active
    diagnostics[
        "goal_pair_pretransition_current_press_preserved"] = torch.where(
            move_active, current_press_preserved.bool(),
            torch.zeros_like(move_active))
    diagnostics[
        "goal_pair_pretransition_current_press_quality"] = torch.where(
            move_active, current_press_quality.float(),
            torch.zeros_like(current_press_quality, dtype=torch.float32))
    return diagnostics


class FretTask(GuitarEnvBase):
    """고정 기타 G0에서 지정 손가락 압현을 학습하는 병렬 Isaac Gym 환경.

    step 반환 계약: ``obs, reward[N,6], done[N], info``.
    """

    def __init__(self, goal_path, hand_targets_path=None, num_envs=512,
                 device="cuda:0", headless=True, seed=0, max_episode_length=None,
                 reset_noise=0.02, reset_soft_limit_fraction=0.02,
                 action_alpha=0.5, action_scale=1.0,
                 random_start=False, reward_config=None,
                 wrist_safety_bounds_min=(-0.20, -0.35, -0.30),
                 wrist_safety_bounds_max=(0.30, 0.35, 0.25),
                 wrist_safety_frames=3,
                 finger_back_soft_limit_z=-0.025,
                 finger_back_soft_scale=0.020,
                 finger_back_soft_penalty=0.10,
                 finger_back_limit_z=-0.050,
                 finger_back_proximal_limit_z=None,
                 finger_back_frames=3,
                 finger_back_samples_per_segment=5,
                 finger_back_min_fraction=0.25,
                 thumb_force_termination_threshold=150000.0,
                 thumb_compression_termination_threshold=0.004,
                 thumb_force_termination_frames=3,
                 isolated_press_lock_after_frames=60,
                 finger_synergy_coefficients=(0.15, 0.20, 0.25),
                 finger_synergy_min_driver_delta_deg=0.10,
                 finger_synergy_full_driver_delta_deg=1.00,
                 finger_synergy_max_induced_delta_deg=2.00,
                 palm_down_threshold=-0.3, palm_down_frames=3,
                 penetration_threshold=0.005, penetration_frames=3,
                 penetration_soft_threshold=0.0025,
                 penetration_soft_penalty=0.10,
                 penetration_termination=True,
                 finger_capsule_radius=0.006,
                 finger_overlap_tolerance=0.002,
                 sustain_boundary_grace_frames=3,
                 static_chord_min_duration_seconds=0.20,
                 sustain_hold_threshold=0.90,
                 sustain_max_dropout_frames=3,
                 wrong_press_termination_frames=12,
                 joint_limit_diagnostic_fraction=0.90,
                 success_rsi_probability=0.35,
                 success_rsi_min_quality=0.75,
                 success_rsi_min_thumb_quality=0.40,
                 success_finger_pose_min_quality=0.60,
                 success_finger_pose_guide_scale_fraction=0.30,
                 success_action_teacher_min_pose_quality=0.70,
                 chord_fine_action_teacher_min_pose_quality=0.20,
                 success_action_teacher_proximal_fraction=0.0,
                 goal_pair_action_routing=False,
                 goal_pair_action_release_frames=18,
                 future_context_lookahead=(30, 60, 90),
                 preparation_frames=60,
                 curriculum_settling_frames=30,
                 failure_termination_penalty=-25.0):
        if reward_config is None:
            reward_config = DEFAULT_FRET_REWARD_OVERRIDES
        elif not isinstance(reward_config, Mapping):
            raise TypeError("reward_config must be a mapping or None")
        # 데이터 길이는 goal 로더 생성 후 알 수 있으므로 충분히 큰 기본값을 사용하고 아래서 보정.
        base_episode_length = max_episode_length or 100000
        super().__init__(num_envs=num_envs, control_dofs=FRET_CONTROL_PREFIXES,
                         device=device, headless=headless, seed=seed,
                         max_episode_length=base_episode_length,
                         action_alpha=action_alpha, action_scale=action_scale,
                         reset_noise=reset_noise,
                         reset_soft_limit_fraction=reset_soft_limit_fraction,
                         obs_body_names=FRET_OBS_BODIES)
        self.enable_thumb_support_collision()
        if self.num_actions != 33:
            raise RuntimeError(f"fret control DOF contract broken: expected 33, got {self.num_actions}")
        self.isolated_press_lock_after_frames = int(
            isolated_press_lock_after_frames)
        if self.isolated_press_lock_after_frames < 0:
            raise ValueError("isolated press lock frame must be non-negative")
        action_finger_ids = []
        for dof_index in self.ctrl_idx.detach().cpu().tolist():
            name = self.dof_names[dof_index]
            finger_id = -1
            if name.startswith("LH:thumb"):
                finger_id = 0
            else:
                for index, finger_name in enumerate(
                        ("index", "middle", "ring", "pinky"), start=1):
                    if name.startswith(f"LH:{finger_name}"):
                        finger_id = index
                        break
            action_finger_ids.append(finger_id)
        self._action_finger_ids = torch.tensor(
            action_finger_ids, dtype=torch.long, device=self.device)
        self.goal_pair_action_assist = False
        self.goal_pair_recovery_assist = False
        self.goal_pair_action_routing = bool(goal_pair_action_routing)
        self.goal_pair_action_release_frames = int(
            goal_pair_action_release_frames)
        if self.goal_pair_action_release_frames < 1:
            raise ValueError(
                "goal-pair action release frames must be positive")
        control_names = [self.dof_names[index]
                         for index in self.ctrl_idx.detach().cpu().tolist()]
        self.joint_limit_group_indices = {}
        for group, prefix in JOINT_LIMIT_GROUP_PREFIXES:
            indices = [
                index for index, name in enumerate(control_names)
                if name.startswith(prefix)]
            if not indices:
                raise RuntimeError(
                    f"joint-limit diagnostic group is empty: {group}")
            self.joint_limit_group_indices[group] = torch.tensor(
                indices, dtype=torch.long, device=self.device)
        self.joint_limit_group_names = tuple(
            self.joint_limit_group_indices)
        self._action_is_wrist = torch.tensor(
            [name.startswith("L_Wrist") for name in control_names],
            dtype=torch.bool, device=self.device)
        self._action_is_transition_proximal = torch.tensor(
            [name.startswith(("L_Wrist", "L_Elbow", "L_Shoulder"))
             for name in control_names],
            dtype=torch.bool, device=self.device)
        action_index = {
            name: index for index, name in enumerate(control_names)}
        self.thumb_base_policy_action_indices = {
            axis: action_index[f"LH:thumb1_{axis}"]
            for axis in ("x", "y", "z")
        }
        self.action_saturation_regularization_indices = (
            self.thumb_base_policy_action_indices["x"],)
        self._thumb_base_action_indices = torch.tensor(
            tuple(self.thumb_base_policy_action_indices[axis]
                  for axis in ("x", "y", "z")),
            dtype=torch.long, device=self.device)
        flexion_names = tuple(
            (f"LH:{finger}1_x", f"LH:{finger}2", f"LH:{finger}3")
            for finger in ("index", "middle", "ring", "pinky"))
        missing_flexion = [
            name for row in flexion_names for name in row
            if name not in action_index]
        if missing_flexion:
            raise KeyError(
                f"missing finger synergy actions: {missing_flexion}")
        self._finger_flexion_action_indices = torch.tensor(
            [[action_index[name] for name in row] for row in flexion_names],
            dtype=torch.long, device=self.device)
        finger_pose_actions = [
            [index for index, name in enumerate(control_names)
             if name.startswith(f"LH:{finger_name}")]
            for finger_name in ("index", "middle", "ring", "pinky")]
        if any(len(indices) != 4 for indices in finger_pose_actions):
            raise RuntimeError(
                "each fretting finger must expose four controlled pose joints")
        self._finger_pose_action_indices = torch.tensor(
            finger_pose_actions, dtype=torch.long, device=self.device)
        self._finger_pose_dof_indices = self.ctrl_idx[
            self._finger_pose_action_indices]
        success_finger_pose_guide_scale_fraction = float(
            success_finger_pose_guide_scale_fraction)
        if not 0.0 < success_finger_pose_guide_scale_fraction <= 1.0:
            raise ValueError(
                "success finger-pose guide scale fraction must be in (0, 1]")
        self._finger_pose_scale = (
            success_finger_pose_guide_scale_fraction
            * self.ctrl_half[0, self._finger_pose_action_indices]
        ).clamp_min(torch.deg2rad(torch.tensor(
            10.0, device=self.device)))
        proximal_pose_actions = [
            index for index, name in enumerate(control_names)
            if name.startswith(("L_Shoulder", "L_Elbow", "L_Wrist"))]
        if len(proximal_pose_actions) != 9:
            raise RuntimeError(
                "finger pose guide requires nine proximal arm joints")
        self._finger_pose_proximal_action_indices = torch.tensor(
            proximal_pose_actions, dtype=torch.long, device=self.device)
        self._finger_pose_proximal_dof_indices = self.ctrl_idx[
            self._finger_pose_proximal_action_indices]
        self._finger_pose_proximal_scale = (
            0.50 * self.ctrl_half[
                0, self._finger_pose_proximal_action_indices]
        ).clamp_min(torch.deg2rad(torch.tensor(
            10.0, device=self.device)))
        self.finger_synergy_coefficients = tuple(
            float(value) for value in finger_synergy_coefficients)
        self.finger_synergy_min_driver_delta_deg = float(
            finger_synergy_min_driver_delta_deg)
        self.finger_synergy_full_driver_delta_deg = float(
            finger_synergy_full_driver_delta_deg)
        self.finger_synergy_max_induced_delta_deg = float(
            finger_synergy_max_induced_delta_deg)
        self.finger_synergy_induced_deg = torch.zeros(
            self.num_envs, 4, device=self.device)
        self.finger_synergy_gate = torch.zeros(
            self.num_envs, 4, dtype=torch.bool, device=self.device)
        self.preparation_frames = int(preparation_frames)
        if self.preparation_frames < 0:
            raise ValueError("preparation_frames must be non-negative")
        self.curriculum_settling_frames = int(curriculum_settling_frames)
        if self.curriculum_settling_frames < 1:
            raise ValueError("curriculum settling frames must be positive")
        self.failure_termination_penalty = float(failure_termination_penalty)
        if (not math.isfinite(self.failure_termination_penalty)
                or self.failure_termination_penalty > 0.0):
            raise ValueError(
                "failure_termination_penalty must be finite and non-positive")
        self.preparation_remaining = torch.full(
            (self.num_envs,), self.preparation_frames,
            dtype=torch.long, device=self.device)

        self.goals = FretGoalSequence(goal_path, num_envs, device=device,
                                      hand_targets_path=hand_targets_path,
                                      random_start=random_start, seed=seed,
                                      sustain_boundary_grace_frames=
                                      sustain_boundary_grace_frames,
                                      static_chord_min_duration_seconds=
                                      static_chord_min_duration_seconds)
        self._goal_pair_previous_active = self._current_finger_activity()
        self._goal_pair_release_remaining = torch.zeros(
            self.num_envs, 4, dtype=torch.long, device=self.device)
        self._goal_pair_routed_fingers = torch.ones(
            self.num_envs, 4, dtype=torch.bool, device=self.device)
        self.curriculum_stage = "full_song"
        if max_episode_length is None:
            self.max_episode_length = self.goals.n_frames + self.preparation_frames
        self.reward_fn = FretReward(**configured_kwargs(
            FretReward, reward_config, env=self))
        self.thumb_force_termination_threshold = float(
            thumb_force_termination_threshold)
        self.thumb_compression_termination_threshold = float(
            thumb_compression_termination_threshold)
        self.thumb_force_termination_frames = int(
            thumb_force_termination_frames)
        if self.thumb_force_termination_threshold <= 0.0:
            raise ValueError("thumb force termination threshold must be positive")
        if self.thumb_compression_termination_threshold <= 0.0:
            raise ValueError(
                "thumb compression termination threshold must be positive")
        if self.thumb_force_termination_frames < 1:
            raise ValueError("thumb force termination frames must be at least 1")
        self.thumb_overforce_streak = torch.zeros(
            self.num_envs, dtype=torch.long, device=self.device)
        self.thumb_overforce_termination = torch.zeros(
            self.num_envs, dtype=torch.bool, device=self.device)
        missing_thumb_bodies = [
            name for name in FRET_THUMB_OBS_BODIES
            if name not in self.hbody_index]
        if missing_thumb_bodies:
            raise KeyError(
                f"missing thumb observation bodies: {missing_thumb_bodies}")
        self.thumb_obs_body_idx = [
            self.hbody_index[name] for name in FRET_THUMB_OBS_BODIES]
        self.base_obs_dim = self.num_obs
        self.goal_dim = self.goals.goal_dim
        # The EMA-smoothed previous action is actuator state.  Exposing it keeps
        # the single-frame MLP observation Markov without removing useful target
        # smoothing.
        self.actuator_obs_dim = self.num_actions
        self.actuator_obs_start = self.base_obs_dim + self.goal_dim
        self.thumb_obs_dim = FRET_THUMB_OBS_DIM
        self.thumb_obs_start = (
            self.actuator_obs_start + self.actuator_obs_dim)
        self.num_obs = self.thumb_obs_start + self.thumb_obs_dim
        self.future_context_lookahead = tuple(
            int(offset) for offset in future_context_lookahead)
        if (not self.future_context_lookahead
                or tuple(sorted(set(self.future_context_lookahead)))
                != self.future_context_lookahead
                or self.future_context_lookahead[0]
                <= max(self.goals.lookahead)):
            raise ValueError(
                "future context lookahead must be sorted, unique, and later "
                "than the base lookahead")
        self.future_context_obs_dim = (
            len(self.future_context_lookahead)
            * self.goals.per_lookahead_dim)
        self.future_context_obs_start = self.num_obs
        self.num_obs += self.future_context_obs_dim
        self.obs_buf = torch.zeros(self.num_envs, self.num_obs, device=self.device)
        self.success_rsi_probability = float(success_rsi_probability)
        self.success_rsi_min_quality = float(success_rsi_min_quality)
        self.success_rsi_min_thumb_quality = float(
            success_rsi_min_thumb_quality)
        self.success_finger_pose_min_quality = float(
            success_finger_pose_min_quality)
        if not 0.0 <= self.success_rsi_probability <= 1.0:
            raise ValueError("success RSI probability must be in [0, 1]")
        if not 0.0 <= self.success_rsi_min_quality <= 1.0:
            raise ValueError("success RSI quality must be in [0, 1]")
        if not 0.0 <= self.success_rsi_min_thumb_quality <= 1.0:
            raise ValueError("success RSI thumb quality must be in [0, 1]")
        if not 0.0 <= self.success_finger_pose_min_quality <= 1.0:
            raise ValueError(
                "success finger-pose quality must be in [0, 1]")
        body_start = 2 * self.n_nonlocked
        body_obs_dim = self.base_obs_dim - body_start
        pose_slots = self.goals.pose_slot_count
        finger_pose_slots = self.goals.finger_pose_slot_count
        self._success_pose_valid = torch.zeros(
            pose_slots, dtype=torch.bool, device=self.device)
        self._success_pose_quality = torch.zeros(
            pose_slots, device=self.device)
        self._success_pose_q = torch.zeros(
            pose_slots, self.n_dof, device=self.device)
        self._success_pose_body_obs = torch.zeros(
            pose_slots, body_obs_dim, device=self.device)
        self._success_pose_thumb_obs = torch.zeros(
            pose_slots, self.thumb_obs_dim, device=self.device)
        self._success_finger_pose_valid = torch.zeros(
            finger_pose_slots, 4, dtype=torch.bool, device=self.device)
        self._success_finger_pose_quality = torch.zeros(
            finger_pose_slots, 4, device=self.device)
        self._success_finger_pose_q = torch.zeros(
            finger_pose_slots, 4, 4, device=self.device)
        self._success_finger_pose_proximal_q = torch.zeros(
            finger_pose_slots, 4, 9, device=self.device)
        self._success_finger_action_valid = torch.zeros(
            finger_pose_slots, 4, dtype=torch.bool, device=self.device)
        self._success_finger_action_quality = torch.zeros(
            finger_pose_slots, 4, device=self.device)
        self._success_finger_action = torch.zeros(
            finger_pose_slots, 4, 4, device=self.device)
        self._success_finger_proximal_action = torch.zeros(
            finger_pose_slots, 4, 9, device=self.device)
        self.success_action_teacher_min_pose_quality = float(
            success_action_teacher_min_pose_quality)
        self.chord_fine_action_teacher_min_pose_quality = float(
            chord_fine_action_teacher_min_pose_quality)
        if not 0.0 <= self.success_action_teacher_min_pose_quality <= 1.0:
            raise ValueError(
                "success action teacher pose quality must be in [0, 1]")
        if not 0.0 <= self.chord_fine_action_teacher_min_pose_quality <= 1.0:
            raise ValueError(
                "chord-fine action teacher pose quality must be in [0, 1]")
        proximal_fraction = float(
            success_action_teacher_proximal_fraction)
        if not 0.0 <= proximal_fraction <= 1.0:
            raise ValueError(
                "success action teacher proximal fraction must be in [0, 1]")
        env_index = torch.arange(
            self.num_envs, dtype=torch.long, device=self.device)
        cohort_key = torch.remainder(env_index * 48271, 104729)
        self._success_action_teacher_proximal_cohort = (
            cohort_key.float() < proximal_fraction * 104729.0)
        self.goals.set_goal_pair_success_pose_valid(
            self._success_pose_valid)
        self.success_rsi_reset = torch.zeros(
            self.num_envs, dtype=torch.bool, device=self.device)
        self.success_rsi_reset_quality = torch.zeros(
            self.num_envs, device=self.device)
        self.rew_dim = 6
        self.value_dim = 6
        self.reward_weights = torch.full((6,), 1.0 / 6.0, device=self.device)
        self.palm_down_threshold = float(palm_down_threshold)
        self.palm_down_frames = int(palm_down_frames)
        if not -1.0 <= self.palm_down_threshold <= 1.0:
            raise ValueError("palm_down_threshold must be in [-1, 1]")
        if self.palm_down_frames < 1:
            raise ValueError("palm_down_frames must be at least 1")
        self.palm_down_streak = torch.zeros(
            self.num_envs, dtype=torch.long, device=self.device)
        self.palm_world_z = torch.zeros(self.num_envs, device=self.device)
        self.palm_normal_valid = torch.zeros(
            self.num_envs, dtype=torch.bool, device=self.device)
        self.palm_down_termination = torch.zeros(
            self.num_envs, dtype=torch.bool, device=self.device)
        self.wrist_safety_monitor = WristSafetyBoxMonitor(
            self, bounds_min=wrist_safety_bounds_min,
            bounds_max=wrist_safety_bounds_max, frames=wrist_safety_frames)
        self.finger_back_monitor = FingerBackLimitMonitor(
            self, limit_z=finger_back_limit_z,
            proximal_limit_z=finger_back_proximal_limit_z,
            soft_limit_z=finger_back_soft_limit_z,
            soft_scale=finger_back_soft_scale,
            frames=finger_back_frames,
            samples_per_segment=finger_back_samples_per_segment,
            min_fraction=finger_back_min_fraction)
        self.finger_back_soft_penalty = float(finger_back_soft_penalty)
        if self.finger_back_soft_penalty < 0.0:
            raise ValueError("finger back soft penalty must be non-negative")
        self.penetration_monitor = GuitarPenetrationMonitor(
            self, threshold=penetration_threshold, frames=penetration_frames,
            termination_enabled=penetration_termination)
        self.penetration_soft_threshold = float(
            penetration_soft_threshold)
        self.penetration_soft_penalty = float(penetration_soft_penalty)
        if (not 0.0 <= self.penetration_soft_threshold
                < self.penetration_monitor.threshold
                or not math.isfinite(self.penetration_soft_penalty)
                or self.penetration_soft_penalty < 0.0):
            raise ValueError(
                "penetration soft threshold/penalty must be finite and "
                "below the hard threshold")
        self.finger_intersection_monitor = FingerSelfIntersectionMonitor(
            self, capsule_radius=finger_capsule_radius,
            overlap_tolerance=finger_overlap_tolerance)
        self.contact_load_monitor = ContactLoadMonitor(self)
        self.sustain_tracker = PressSustainTracker(
            self.num_envs, self.goals.sustain_n_events, self.device,
            hold_threshold=sustain_hold_threshold,
            max_dropout_frames=sustain_max_dropout_frames)
        self.wrong_press_termination_frames = int(
            wrong_press_termination_frames)
        if self.wrong_press_termination_frames < 0:
            raise ValueError(
                "wrong-press termination frames must be non-negative")
        self.joint_limit_diagnostic_fraction = float(
            joint_limit_diagnostic_fraction)
        if not 0.0 < self.joint_limit_diagnostic_fraction <= 1.0:
            raise ValueError(
                "joint-limit diagnostic fraction must be in (0, 1]")
        self.wrong_press_streak = torch.zeros(
            self.num_envs, dtype=torch.long, device=self.device)
        self.wrong_press_termination = torch.zeros(
            self.num_envs, dtype=torch.bool, device=self.device)

        self.metric_tp = torch.zeros(self.num_envs, device=self.device)
        self.metric_fp = torch.zeros(self.num_envs, device=self.device)
        self.metric_fn = torch.zeros(self.num_envs, device=self.device)
        self.metric_correct = torch.zeros(self.num_envs, device=self.device)
        self.metric_total = torch.zeros(self.num_envs, device=self.device)
        self.metric_no_press_correct = torch.zeros(self.num_envs, device=self.device)
        self.metric_no_press_total = torch.zeros(self.num_envs, device=self.device)
        self.metric_wrong_press = torch.zeros(self.num_envs, device=self.device)
        self.metric_supervised_total = torch.zeros(self.num_envs, device=self.device)
        self.metric_finger_success = torch.zeros(
            self.num_envs, 4, device=self.device)
        self.metric_finger_target = torch.zeros(
            self.num_envs, 4, device=self.device)
        self.metric_chord_ready = torch.zeros(
            self.num_envs, device=self.device)
        self.metric_chord_hold_quality = torch.zeros(
            self.num_envs, device=self.device)
        self.metric_chord_total = torch.zeros(
            self.num_envs, device=self.device)
        self.metric_press_dropout = torch.zeros(
            self.num_envs, device=self.device)
        self.metric_press_target_total = torch.zeros(
            self.num_envs, device=self.device)
        self.metric_current_press_dropout_streak = torch.zeros(
            self.num_envs, 6, device=self.device)
        self.metric_max_press_dropout_streak = torch.zeros(
            self.num_envs, device=self.device)

    def reset(self):
        """Reset every environment and cache a physically refreshed reset-body observation.

        Isaac Gym updates the DOF tensor immediately in :meth:`reset_idx`, but it does not
        recompute rigid-body transforms until the next simulation.  A partial auto-reset must
        not expose the just-finished episode's hand/body positions as the new episode's
        observation.  The full reset performed here includes the held physics step from the
        base class, so its guitar-relative body channels are a valid, settled reset snapshot.
        Partial auto-resets reuse the base-body and appended-thumb slices; proprioception and
        goal slices still come from the newly sampled reset state.

        This task currently uses the fixed-guitar G0 environment.  A future moving-guitar task
        must replace this snapshot with forward kinematics or an indexed reset-state cache.
        """
        self._full_reset_in_progress = True
        try:
            obs = super().reset()
        finally:
            self._full_reset_in_progress = False
        ds = self.dof_state.view(self.num_envs, self.n_dof, 2)
        # Keep one physically refreshed RSI pose per parallel environment.  Reusing
        # this exact q/body pair on asynchronous resets makes every returned reset
        # observation internally consistent; diversity still comes from the many
        # environments and from random song starts.
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
        self._settled_reset_thumb_obs = obs[
            :, self.thumb_obs_start:
            self.thumb_obs_start + self.thumb_obs_dim].detach().clone()
        self._reset_body_obs = self._settled_reset_body_obs.clone()
        self._reset_thumb_obs = self._settled_reset_thumb_obs.clone()
        self.success_rsi_reset.zero_()
        self.success_rsi_reset_quality.zero_()
        # Refresh just the proprioceptive slice after zeroing reset velocities;
        # body positions remain the valid post-PhysX snapshot above.
        obs = self.compute_observations()
        obs[:, body_start:self.base_obs_dim] = self._settled_reset_body_obs
        obs[:, self.thumb_obs_start:
            self.thumb_obs_start + self.thumb_obs_dim] = (
                self._settled_reset_thumb_obs)
        self.obs_buf.copy_(obs)
        return obs

    def set_curriculum_stage(self, stage, duration_frames=None, reset=False):
        """Apply a fingertip curriculum stage and optionally restart all envs."""
        changed = stage != self.curriculum_stage
        self.curriculum_stage = str(stage)
        self.goals.set_curriculum_stage(stage, duration_frames=duration_frames)
        if reset and changed:
            return self.reset()
        return None

    def set_goal_pair_action_assist(self, enabled):
        self.goal_pair_action_assist = bool(enabled)

    def set_goal_pair_recovery_assist(self, enabled):
        self.goal_pair_recovery_assist = bool(enabled)

    def _current_finger_activity(self):
        current = self.goals.current()
        finger_numbers = torch.arange(
            1, 5, device=self.device).view(1, 1, 4)
        return (
            (current["fret"] > 0)[..., None]
            & (current["finger"].long()[..., None] == finger_numbers)
        ).any(dim=1)

    def _update_goal_pair_action_routing(self, env_ids, reset=False):
        env_ids = torch.as_tensor(
            env_ids, dtype=torch.long, device=self.device).reshape(-1)
        if env_ids.numel() == 0:
            return
        active = self._current_finger_activity()[env_ids]
        if reset:
            remaining = torch.zeros_like(
                self._goal_pair_release_remaining[env_ids])
        else:
            remaining = (
                self._goal_pair_release_remaining[env_ids] - 1
            ).clamp_min(0)
            released = (
                self._goal_pair_previous_active[env_ids] & ~active)
            remaining = torch.where(
                released,
                torch.full_like(
                    remaining, self.goal_pair_action_release_frames),
                remaining)
        self._goal_pair_release_remaining[env_ids] = remaining
        self._goal_pair_previous_active[env_ids] = active

    def policy_action_mask(self, include_goal_pair_routing=True):
        mask = torch.ones(
            self.num_envs, self.num_actions,
            dtype=torch.bool, device=self.device)
        if (hasattr(self, "goals")
                and self.curriculum_stage == "isolated_press"):
            restricted = (
                self.progress_buf >= self.isolated_press_lock_after_frames)
            if restricted.any():
                current = self.goals.current()
                target_finger = current["finger"].amax(dim=1).long()
                allowed = ((self._action_finger_ids[None] == 0)
                           | (self._action_finger_ids[None]
                              == target_finger[:, None]))
                allowed |= self._action_is_wrist[None]
                mask = torch.where(
                    restricted[:, None], allowed.expand_as(mask), mask)
        if (include_goal_pair_routing
                and hasattr(self, "goals")
                and self.curriculum_stage == "goal_pair"
                and (self.goal_pair_action_assist
                     or self.goal_pair_recovery_assist)):
            preview_assisted = torch.zeros(
                self.num_envs, dtype=torch.bool, device=self.device)
            if self.goal_pair_action_assist:
                preview_assisted |= self.goals.goal_pair_preview_mask
            recovery_assisted = torch.zeros_like(preview_assisted)
            if self.goal_pair_recovery_assist:
                recovery_assisted |= self.goals.goal_pair_rehearsal_mask
            ready = self.preparation_remaining <= 0
            preview_assisted &= ready
            recovery_assisted &= ready
            assisted = preview_assisted | recovery_assisted
            if assisted.any():
                current = self.goals.current()
                finger_numbers = torch.arange(
                    1, 5, device=self.device).view(1, 1, 4)
                current_fingers = (
                    (current["fret"] > 0)[..., None]
                    & (current["finger"].long()[..., None]
                       == finger_numbers)).any(dim=1)
                incoming = self.goals.goal_pair_incoming_finger
                allowed = (
                    self._action_finger_ids[None] == 0
                ).expand(self.num_envs, -1).clone()
                allowed |= recovery_assisted[:, None]
                allowed |= (
                    preview_assisted[:, None]
                    & self._action_is_transition_proximal[None])
                for finger_number in range(1, 5):
                    finger_allowed = (
                        current_fingers[:, finger_number - 1]
                        | (incoming == finger_number))
                    allowed |= (
                        finger_allowed[:, None]
                        & (self._action_finger_ids[None]
                           == finger_number))
                mask = torch.where(
                    assisted[:, None], allowed, mask)
        if (hasattr(self, "goals")
                and self.curriculum_stage == "goal_pair"
                and self.goal_pair_action_routing):
            current = self.goals.current()
            current_active = self._current_finger_activity()
            routed_fingers = goal_pair_finger_action_routing(
                current_active, current["finger_event"],
                self._goal_pair_release_remaining > 0,
                preparation_remaining=self.preparation_remaining,
                fps=self.goals.fps,
                lookahead_s=self.reward_fn.next_goal_lookahead_s)
            self._goal_pair_routed_fingers.copy_(routed_fingers)
            routed_actions = (
                self._action_finger_ids[None] <= 0
            ).expand(self.num_envs, -1).clone()
            for finger_number in range(1, 5):
                routed_actions |= (
                    routed_fingers[:, finger_number - 1, None]
                    & (self._action_finger_ids[None] == finger_number))
            mask &= routed_actions
        else:
            self._goal_pair_routed_fingers.fill_(True)
        return mask

    def apply_actions(self, actions):
        """Progressively unlock wrist and elbow after finger-only acquisition."""
        # Goal Pair routing isolates PPO log-probability gradients only.  The
        # physical controller keeps every finger available for hover, release
        # and anticipatory hand shaping.
        action_mask = self.policy_action_mask(
            include_goal_pair_routing=False)
        actions = torch.where(action_mask, actions, self.prev_action)
        if hasattr(self, "goals"):
            current = self.goals.current()
            finger_numbers = torch.arange(
                1, 5, device=self.device).view(1, 1, 4)
            active = (
                (current["fret"] > 0)[..., None]
                & (current["finger"].long()[..., None] == finger_numbers)
            ).any(dim=1)
            follower_allowed = finger_synergy_follower_mask(
                active, current["finger_event"])
            actions, induced_deg, gate = adjacent_finger_action_synergy(
                actions, self.prev_action,
                self._finger_flexion_action_indices, follower_allowed,
                self.ctrl_half, action_scale=self.action_scale,
                coefficients=self.finger_synergy_coefficients,
                min_driver_delta_deg=
                    self.finger_synergy_min_driver_delta_deg,
                full_driver_delta_deg=
                    self.finger_synergy_full_driver_delta_deg,
                max_induced_delta_deg=
                    self.finger_synergy_max_induced_delta_deg)
            self.finger_synergy_induced_deg.copy_(induced_deg)
            self.finger_synergy_gate.copy_(gate)
        actions = torch.where(action_mask, actions, self.prev_action)
        super().apply_actions(actions)

    def curriculum_state_dict(self):
        return {
            "goal_sampler": self.goals.curriculum_sampler_state_dict(),
            "success_rsi": {
                "valid": self._success_pose_valid.detach().cpu(),
                "quality": self._success_pose_quality.detach().cpu(),
                "q": self._success_pose_q.detach().cpu(),
                "body_obs": self._success_pose_body_obs.detach().cpu(),
                "thumb_obs": self._success_pose_thumb_obs.detach().cpu(),
                "finger_valid":
                    self._success_finger_pose_valid.detach().cpu(),
                "finger_quality":
                    self._success_finger_pose_quality.detach().cpu(),
                "finger_q": self._success_finger_pose_q.detach().cpu(),
                "finger_proximal_q":
                    self._success_finger_pose_proximal_q.detach().cpu(),
                "finger_action_valid":
                    self._success_finger_action_valid.detach().cpu(),
                "finger_action_quality":
                    self._success_finger_action_quality.detach().cpu(),
                "finger_action":
                    self._success_finger_action.detach().cpu(),
                "finger_proximal_action":
                    self._success_finger_proximal_action.detach().cpu(),
            },
        }

    def load_curriculum_state_dict(self, state):
        sampler = state.get("goal_sampler", state)
        self.goals.load_curriculum_sampler_state_dict(sampler)
        cache = state.get("success_rsi")
        if cache is None:
            return None
        targets = {
            "valid": self._success_pose_valid,
            "quality": self._success_pose_quality,
            "q": self._success_pose_q,
            "body_obs": self._success_pose_body_obs,
            "thumb_obs": self._success_pose_thumb_obs,
        }
        for name, target in targets.items():
            source = cache.get(name)
            if source is None or tuple(source.shape) != tuple(target.shape):
                raise ValueError(
                    f"success RSI {name} shape mismatch: expected "
                    f"{tuple(target.shape)}")
            target.copy_(source.to(device=self.device, dtype=target.dtype))
        pose_targets = {
            "finger_valid": self._success_finger_pose_valid,
            "finger_quality": self._success_finger_pose_quality,
            "finger_q": self._success_finger_pose_q,
            "finger_proximal_q":
                self._success_finger_pose_proximal_q,
        }
        action_targets = {
            "finger_action_valid": self._success_finger_action_valid,
            "finger_action_quality": self._success_finger_action_quality,
            "finger_action": self._success_finger_action,
            "finger_proximal_action":
                self._success_finger_proximal_action,
        }
        for optional_targets in (pose_targets, action_targets):
            optional_sources = {
                name: cache.get(name) for name in optional_targets}
            present = [
                source is not None for source in optional_sources.values()]
            if any(present) and not all(present):
                raise ValueError(
                    "success RSI optional cache group is incomplete")
            for name, target in optional_targets.items():
                source = optional_sources[name]
                if source is None:
                    continue
                if tuple(source.shape) != tuple(target.shape):
                    raise ValueError(
                        f"success RSI {name} shape mismatch: expected "
                        f"{tuple(target.shape)}")
                target.copy_(
                    source.to(device=self.device, dtype=target.dtype))
        return None

    def _apply_success_rsi(self, env_ids):
        self.success_rsi_reset[env_ids] = False
        self.success_rsi_reset_quality[env_ids] = 0.0
        if (self.goals.pose_slot_count == 0
                or self.success_rsi_probability <= 0.0
                or self.curriculum_stage not in (
                    "static_chord", "frozen_context", "goal_pair",
                    "transition_window", "coverage", "integration",
                    "full_song")):
            return
        slots = self.goals.frame_pose_slot[
            self.goals.frame_idx[env_ids]]
        eligible = slots >= 0
        safe_slots = slots.clamp_min(0)
        eligible &= self._success_pose_valid[safe_slots]
        sampled = torch.rand(
            env_ids.numel(), generator=self.rng,
            device=self.device) < self.success_rsi_probability
        selected = eligible & sampled
        if not selected.any():
            return
        selected_envs = env_ids[selected]
        selected_slots = slots[selected]
        ds = self.dof_state.view(self.num_envs, self.n_dof, 2)
        ds[selected_envs, :, 0] = self._success_pose_q[selected_slots]
        self._reset_body_obs[selected_envs] = (
            self._success_pose_body_obs[selected_slots])
        self._reset_thumb_obs[selected_envs] = (
            self._success_pose_thumb_obs[selected_slots])
        self.success_rsi_reset[selected_envs] = True
        self.success_rsi_reset_quality[selected_envs] = (
            self._success_pose_quality[selected_slots])

    def _update_success_rsi_cache(
            self, frame_idx, metrics, terminal_obs, safe):
        if self.goals.pose_slot_count == 0:
            return
        active = metrics["active"]
        active_count = active.sum(dim=1)
        position_quality = (
            metrics["good_position_quality"].masked_fill(~active, 0.0)
            .sum(dim=1) / active_count.clamp_min(1))
        thumb_quality = metrics["thumb_support_quality"]
        quality = (
            metrics["chord_hold_quality"]
            * position_quality
            * thumb_quality).clamp_min(0.0).pow(1.0 / 3.0)
        candidate = (
            safe & (active_count > 0) & metrics["chord_ready"]
            & metrics["all_correct"] & metrics["thumb_support"]
            & (thumb_quality >= self.success_rsi_min_thumb_quality)
            & (quality >= self.success_rsi_min_quality))
        slots = self.goals.frame_pose_slot[frame_idx]
        finger_slots = self.goals.finger_pose_slot[frame_idx]
        candidate &= slots >= 0
        body_start = 2 * self.n_nonlocked
        body_obs = terminal_obs[:, body_start:self.base_obs_dim]
        thumb_obs = terminal_obs[
            :, self.thumb_obs_start:
            self.thumb_obs_start + self.thumb_obs_dim]
        q = self.dof_state.view(
            self.num_envs, self.n_dof, 2)[:, :, 0]
        required = (
            active[..., None] & metrics["finger_assignment"])
        required_count = required.sum(dim=1)
        finger_press = (
            (~required) | metrics["press_success"][..., None]).all(dim=1)
        finger_position = (
            (metrics["good_position_quality"][..., None]
             * required.float()).sum(dim=1)
            / required_count.clamp_min(1))
        finger_hold = metrics["press_hold_quality"][..., None].masked_fill(
            ~required, float("inf")).amin(dim=1)
        finger_hold = torch.where(
            required_count > 0, finger_hold,
            torch.zeros_like(finger_hold))
        finger_quality = (
            finger_position * finger_hold).clamp_min(0.0).sqrt()
        finger_candidate = (
            safe[:, None] & (finger_slots >= 0)
            & (required_count > 0) & finger_press
            & ~metrics["wrong_press"].any(dim=1)[:, None]
            & (finger_quality >= self.success_finger_pose_min_quality))
        finger_q = q[:, self._finger_pose_dof_indices]
        proximal_q = q[:, self._finger_pose_proximal_dof_indices]
        finger_action = self.prev_action[
            :, self._finger_pose_action_indices]
        proximal_action = self.prev_action[
            :, self._finger_pose_proximal_action_indices]
        for finger_index in range(4):
            selected = finger_candidate[:, finger_index]
            if not selected.any():
                continue
            selected_slots = finger_slots[selected, finger_index]
            best_by_slot = torch.full_like(
                self._success_finger_pose_quality[:, finger_index],
                -float("inf"))
            best_by_slot.scatter_reduce_(
                0, selected_slots, finger_quality[selected, finger_index],
                reduce="amax", include_self=True)
            improved = (
                torch.isfinite(best_by_slot)
                & (~self._success_finger_pose_valid[:, finger_index]
                   | (best_by_slot
                      > self._success_finger_pose_quality[:, finger_index])))
            action_improved = (
                torch.isfinite(best_by_slot)
                & (~self._success_finger_action_valid[:, finger_index]
                   | (best_by_slot
                      > self._success_finger_action_quality[:, finger_index])))
            for slot in torch.nonzero(
                    improved | action_improved,
                    as_tuple=False).squeeze(-1).tolist():
                rows = torch.nonzero(
                    selected & (finger_slots[:, finger_index] == slot),
                    as_tuple=False).squeeze(-1)
                row = rows[
                    finger_quality[rows, finger_index].argmax()]
                if improved[slot]:
                    self._success_finger_pose_valid[slot, finger_index] = True
                    self._success_finger_pose_quality[slot, finger_index] = (
                        finger_quality[row, finger_index])
                    self._success_finger_pose_q[slot, finger_index] = (
                        finger_q[row, finger_index])
                    self._success_finger_pose_proximal_q[
                        slot, finger_index] = proximal_q[row]
                if action_improved[slot]:
                    self._success_finger_action_valid[
                        slot, finger_index] = True
                    self._success_finger_action_quality[
                        slot, finger_index] = (
                            finger_quality[row, finger_index])
                    self._success_finger_action[slot, finger_index] = (
                        finger_action[row, finger_index])
                    self._success_finger_proximal_action[
                        slot, finger_index] = proximal_action[row]
        if not candidate.any():
            return
        best_by_slot = torch.full_like(
            self._success_pose_quality, -float("inf"))
        best_by_slot.scatter_reduce_(
            0, slots[candidate], quality[candidate],
            reduce="amax", include_self=True)
        improved = (
            torch.isfinite(best_by_slot)
            & (~self._success_pose_valid
               | (best_by_slot > self._success_pose_quality)))
        for slot in torch.nonzero(
                improved, as_tuple=False).squeeze(-1).tolist():
            rows = torch.nonzero(
                candidate & (slots == slot), as_tuple=False).squeeze(-1)
            row = rows[quality[rows].argmax()]
            self._success_pose_valid[slot] = True
            self._success_pose_quality[slot] = quality[row]
            self._success_pose_q[slot] = q[row]
            self._success_pose_body_obs[slot] = body_obs[row]
            self._success_pose_thumb_obs[slot] = thumb_obs[row]

    def _success_pose_policy_teacher(self, goal, metrics):
        """성공한 손가락 자세는 동시에 복습하고, 상위 관절은 초점 하나만 따른다."""
        teacher = torch.zeros(
            self.num_envs, self.num_actions, device=self.device)
        mask = torch.zeros(
            self.num_envs, self.num_actions,
            dtype=torch.bool, device=self.device)
        if self.curriculum_stage not in (
                "chord_fine_reach", "static_chord", "goal_pair"):
            return teacher, mask
        slots = goal["finger_pose_slot"].long()
        finger_gate = metrics["success_pose_guide_active_per_finger"]
        finger_pose_quality = metrics[
            "success_pose_guide_per_finger"]
        minimum_quality = (
            self.chord_fine_action_teacher_min_pose_quality
            if self.curriculum_stage in (
                "chord_fine_reach", "static_chord")
            else self.success_action_teacher_min_pose_quality)
        safe_slots = slots.clamp_min(0)
        finger_indices = torch.arange(
            4, device=self.device).view(1, 4)
        cached_action = self._success_finger_action[
            safe_slots, finger_indices]
        cached_valid = (
            (slots >= 0)
            & self._success_finger_action_valid[
                safe_slots, finger_indices])
        finger_teacher, finger_mask = cached_finger_action_teacher(
            cached_action, cached_valid, finger_gate,
            finger_pose_quality, minimum_quality=minimum_quality)
        for finger_index in range(4):
            action_indices = self._finger_pose_action_indices[finger_index]
            teacher[:, action_indices] = finger_teacher[:, finger_index]
            mask[:, action_indices] = finger_mask[:, finger_index]

        if self.curriculum_stage != "goal_pair":
            return teacher, mask

        proximal_candidate = (
            metrics["next_goal_inactive_move_gate"]
            & (slots >= 0)
            & self._success_finger_action_valid[
                safe_slots, finger_indices]
            & self._success_action_teacher_proximal_cohort[:, None])
        chosen_finger = torch.where(
            proximal_candidate,
            finger_pose_quality,
            torch.full_like(finger_pose_quality, float("inf")),
        ).argmin(dim=1)
        proximal_rows = torch.nonzero(
            proximal_candidate.any(dim=1),
            as_tuple=False).squeeze(-1)
        if proximal_rows.numel() > 0:
            selected_fingers = chosen_finger[proximal_rows]
            selected_slots = slots[
                proximal_rows, selected_fingers]
            proximal_indices = self._finger_pose_proximal_action_indices
            proximal_action = self._success_finger_proximal_action[
                selected_slots, selected_fingers]
            teacher[
                proximal_rows[:, None], proximal_indices[None]
            ] = proximal_action
            mask[
                proximal_rows[:, None], proximal_indices[None]
            ] = True
        return teacher, mask

    def reset_idx(self, env_ids):
        super().reset_idx(env_ids)
        if hasattr(self, "goals"):
            self.goals.reset(env_ids)
        if hasattr(self, "_goal_pair_release_remaining"):
            self._update_goal_pair_action_routing(env_ids, reset=True)
        full_reset = bool(getattr(
            self, "_full_reset_in_progress", False))
        if full_reset and hasattr(self, "success_rsi_reset"):
            self.success_rsi_reset[env_ids] = False
            self.success_rsi_reset_quality[env_ids] = 0.0
        if (hasattr(self, "_settled_reset_q")
                and env_ids.numel() > 0 and not full_reset):
            # Base reset samples bounded RSI noise.  Once a valid body snapshot
            # exists, restore its matching q so partial-reset proprioception and
            # rigid-body geometry describe the same physical pose.
            ds = self.dof_state.view(self.num_envs, self.n_dof, 2)
            ds[env_ids, :, 0] = self._settled_reset_q[env_ids]
            ds[env_ids, :, 1] = 0.0
            self._reset_body_obs[env_ids] = (
                self._settled_reset_body_obs[env_ids])
            self._reset_thumb_obs[env_ids] = (
                self._settled_reset_thumb_obs[env_ids])
            self._apply_success_rsi(env_ids)
            self.gym.set_dof_state_tensor(
                self.sim, gymtorch.unwrap_tensor(self.dof_state))
            self.pd_target.view(self.num_envs, self.n_dof)[env_ids] = (
                ds[env_ids, :, 0])
            self.prev_action[env_ids] = self.actions_for_pd_targets(
                ds[env_ids][:, self.ctrl_idx, 0], env_ids)
        if hasattr(self, "reward_fn"):
            self.reward_fn.reset(env_ids)
        if hasattr(self, "finger_synergy_induced_deg"):
            self.finger_synergy_induced_deg[env_ids] = 0.0
            self.finger_synergy_gate[env_ids] = False
        reset_names = (
            "metric_tp", "metric_fp", "metric_fn", "metric_correct",
            "metric_total", "metric_no_press_correct", "metric_no_press_total",
            "metric_wrong_press", "metric_supervised_total",
            "metric_finger_success", "metric_finger_target",
            "metric_chord_ready", "metric_chord_hold_quality",
            "metric_chord_total", "metric_press_dropout",
            "metric_press_target_total", "metric_current_press_dropout_streak",
            "metric_max_press_dropout_streak", "palm_down_streak",
            "palm_world_z", "palm_normal_valid", "palm_down_termination",
            "thumb_overforce_streak", "thumb_overforce_termination",
            "wrong_press_streak", "wrong_press_termination",
        )
        for name in reset_names:
            if hasattr(self, name):
                getattr(self, name)[env_ids] = 0
        if hasattr(self, "penetration_monitor"):
            self.penetration_monitor.reset(env_ids)
        if hasattr(self, "finger_intersection_monitor"):
            self.finger_intersection_monitor.reset(env_ids)
        if hasattr(self, "wrist_safety_monitor"):
            self.wrist_safety_monitor.reset(env_ids)
        if hasattr(self, "finger_back_monitor"):
            self.finger_back_monitor.reset(env_ids)
        if hasattr(self, "sustain_tracker"):
            self.sustain_tracker.reset(env_ids)
        if hasattr(self, "preparation_remaining"):
            self.preparation_remaining[env_ids] = self.preparation_frames

    def compute_observations(self):
        base = super().compute_observations()
        goal_obs = self.goals.observe(self.preparation_remaining)
        bs = self.body_state.view(self.num_envs, self._bpe, 13)
        thumb_endpoints_local = self.to_guitar_frame(
            bs[:, self.thumb_obs_body_idx, 0:3])
        thumb_raw_obs = thumb_endpoints_local.reshape(
            self.num_envs, FRET_THUMB_RAW_OBS_DIM)
        thumb_force = self.hbody_contact_force(THUMB_PAD_BODY).norm(dim=-1)
        thumb_contact = (
            torch.isfinite(thumb_force)
            & (thumb_force
               >= self.reward_fn.thumb_reward.contact_on_force))
        thumb_derived_obs = thumb_geometry_observation(
            thumb_endpoints_local, thumb_contact,
            pad_radius=self.reward_fn.thumb_reward.pad_radius,
            n_samples=self.reward_fn.thumb_reward.N_SAMPLES,
            sample_alpha=self.reward_fn.thumb_reward.sample_alpha)
        thumb_obs = torch.cat(
            (thumb_raw_obs, thumb_derived_obs), dim=-1)
        self.last_nonfinite_observation |= self.rows_with_nonfinite(
            thumb_obs)
        thumb_obs = self.sanitize_finite(thumb_obs)
        future_context = self.goals.observe_future_context(
            self.future_context_lookahead,
            self.preparation_remaining)
        self.last_nonfinite_observation |= self.rows_with_nonfinite(
            future_context)
        future_context = self.sanitize_finite(future_context)
        obs = torch.cat(
            [base, goal_obs, self.prev_action, thumb_obs, future_context],
            dim=-1)
        self.obs_buf[:] = obs
        return obs

    def _compose_reset_observation(self, terminal_obs, env_ids):
        """Return next-policy observations after resetting ``env_ids``.

        DOF/goal channels are read after reset.  Rigid-body channels would still contain the
        terminal transforms until PhysX simulates again, so replace just that slice with the
        valid snapshot cached by :meth:`reset`.  Non-reset environments retain their fresh
        post-step observation unchanged.
        """
        if env_ids.numel() == 0:
            return terminal_obs
        if not hasattr(self, "_settled_reset_body_obs"):
            raise RuntimeError(
                "FretTask.reset() must be called before automatic partial resets")

        reset_obs = self.compute_observations()
        body_start = 2 * self.n_nonlocked
        reset_obs[env_ids, body_start:self.base_obs_dim] = (
            self._reset_body_obs[env_ids])
        reset_obs[
            env_ids,
            self.thumb_obs_start:self.thumb_obs_start + self.thumb_obs_dim
        ] = self._reset_thumb_obs[env_ids]
        self.obs_buf.copy_(reset_obs)
        return reset_obs

    def _update_palm_down_termination(self):
        """R13: terminate only when the anatomical palm normal clearly faces the floor."""
        wrist = self.hbody_pos("L_Wrist")
        index = self.hbody_pos("LH:index1")
        middle = self.hbody_pos("LH:middle1")
        pinky = self.hbody_pos("LH:pinky1")
        normal, valid = palm_inward_normal(wrist, index, middle, pinky)
        world_z = normal[:, 2]
        violation = world_z < self.palm_down_threshold
        self.palm_down_streak.copy_(update_consecutive_violation(
            self.palm_down_streak, violation, valid))
        self.palm_world_z.copy_(world_z)
        self.palm_normal_valid.copy_(valid)
        self.palm_down_termination.copy_(
            valid & (self.palm_down_streak >= self.palm_down_frames))
        return self.palm_down_termination

    def _accumulate_metrics(self, metrics, enabled=None):
        if enabled is None:
            enabled = torch.ones(
                self.num_envs, dtype=torch.bool, device=self.device)
        frame_enabled = enabled
        enabled = frame_enabled[:, None]
        active = metrics["active"] & enabled
        correct = metrics["correct"] & active
        wrong_finger_contact = metrics["any_finger_on_target"] & ~metrics["correct"] & active
        self.metric_tp += correct.sum(dim=1)
        self.metric_fp += wrong_finger_contact.sum(dim=1)
        self.metric_fn += (~metrics["correct"] & active).sum(dim=1)
        self.metric_correct += correct.sum(dim=1)
        self.metric_total += active.sum(dim=1)
        no_press = metrics["no_press_active"] & enabled
        self.metric_no_press_correct += (metrics["no_press_success"]
                                         & enabled).sum(dim=1)
        self.metric_no_press_total += no_press.sum(dim=1)
        supervised = metrics["supervised"] & enabled
        self.metric_wrong_press += (metrics["wrong_press"] & supervised).sum(dim=1)
        self.metric_supervised_total += supervised.sum(dim=1)
        assignment = metrics["finger_assignment"]
        finger_target = active[..., None] & assignment
        finger_success = correct[..., None] & assignment
        self.metric_finger_target += finger_target.sum(dim=1)
        self.metric_finger_success += finger_success.sum(dim=1)
        has_press = active.any(dim=1)
        self.metric_chord_ready += (
            metrics["chord_ready"] & has_press).float()
        self.metric_chord_hold_quality += (
            metrics["chord_hold_quality"] * has_press.float())
        self.metric_chord_total += has_press.float()
        self.metric_press_dropout += (
            metrics["press_dropout"] & active).sum(dim=1)
        self.metric_press_target_total += active.sum(dim=1)
        frame_dropout = metrics["press_dropout"] & active
        self.metric_current_press_dropout_streak.copy_(
            update_live_dropout_streak(
                self.metric_current_press_dropout_streak,
                frame_dropout, frame_enabled))
        active_dropout_streak = (
            self.metric_current_press_dropout_streak.amax(dim=1).float())
        self.metric_max_press_dropout_streak.copy_(torch.maximum(
            self.metric_max_press_dropout_streak, active_dropout_streak))

    def _episode_metrics(self, done):
        ids = torch.nonzero(done).squeeze(-1)
        if ids.numel() == 0:
            empty = torch.empty(0, device=self.device)
            result = {"accuracy_l": empty, "precision_l": empty,
                    "recall_l": empty, "f1_l": empty,
                    "no_press_accuracy": empty,
                    "no_press_correct_count": empty,
                    "no_press_evidence_count": empty,
                    "wrong_press_rate": empty,
                    "curriculum_success_rate": empty,
                    "chord_ready_rate": empty,
                    "chord_hold_quality": empty,
                    "press_dropout_rate": empty,
                    "press_max_dropout_frames": empty}
            for finger in range(1, 5):
                result[f"curriculum_finger_{finger}_success"] = empty
                result[f"curriculum_finger_{finger}_count"] = empty
                result[f"press_finger_{finger}_success"] = empty
                result[f"press_finger_{finger}_count"] = empty
            for signature in range(1, 16):
                result[
                    f"curriculum_chord_set_{signature}_success"] = empty
                result[
                    f"curriculum_chord_set_{signature}_count"] = empty
            return result
        eps = 1e-8
        tp, fp, fn = self.metric_tp[ids], self.metric_fp[ids], self.metric_fn[ids]
        precision = tp / (tp + fp + eps)
        recall = tp / (tp + fn + eps)
        no_press_total = self.metric_no_press_total[ids]
        no_press_accuracy = torch.where(
            no_press_total > 0,
            self.metric_no_press_correct[ids] / no_press_total.clamp_min(1.0),
            torch.ones_like(no_press_total))
        result = {
            "accuracy_l": self.metric_correct[ids] / self.metric_total[ids].clamp_min(1.0),
            "precision_l": precision,
            "recall_l": recall,
            "f1_l": 2.0 * precision * recall / (precision + recall + eps),
            "no_press_accuracy": no_press_accuracy,
            "no_press_correct_count": self.metric_no_press_correct[ids],
            "no_press_evidence_count": no_press_total,
            "wrong_press_rate": self.metric_wrong_press[ids] /
                self.metric_supervised_total[ids].clamp_min(1.0),
            "curriculum_success_rate":
                self.reward_fn._curriculum_episode_success[ids].float(),
            "chord_ready_rate": self.metric_chord_ready[ids] /
                self.metric_chord_total[ids].clamp_min(1.0),
            "chord_hold_quality": self.metric_chord_hold_quality[ids] /
                self.metric_chord_total[ids].clamp_min(1.0),
            "press_dropout_rate": self.metric_press_dropout[ids] /
                self.metric_press_target_total[ids].clamp_min(1.0),
            "press_max_dropout_frames":
                self.metric_max_press_dropout_streak[ids],
        }
        target_fingers = torch.zeros(
            ids.numel(), 4, dtype=torch.bool, device=self.device)
        if self.curriculum_stage in (
                "coarse_reach", "fine_reach",
                "isolated_press", "integrated_press"):
            goal = self.goals.current()
            env_index = torch.arange(self.num_envs, device=self.device)
            target_finger = goal["finger"][
                env_index, self.goals.practice_string][ids]
            target_fingers = (
                target_finger[:, None]
                == torch.arange(1, 5, device=self.device)[None])
        elif self.curriculum_stage in (
                "chord_reach", "chord_fine_reach", "static_chord"):
            goal_finger = self.goals.current()["finger"][ids]
            target_fingers = (
                goal_finger[..., None]
                == torch.arange(1, 5, device=self.device)[None, None]
            ).any(dim=1)
        curriculum_success = (
            self.reward_fn._curriculum_episode_success[ids].float())
        if self.curriculum_stage in (
                "chord_reach", "chord_fine_reach", "static_chord"):
            goal_finger = self.goals.current()["finger"][ids]
            active_fingers = torch.stack([
                (goal_finger == finger).any(dim=1)
                for finger in range(1, 5)
            ], dim=1)
            chord_signature = (
                active_fingers.long()
                * torch.tensor(
                    [1, 2, 4, 8], device=self.device)[None]
            ).sum(dim=1)
        else:
            chord_signature = torch.zeros_like(ids)
        for finger in range(1, 5):
            selected = target_fingers[:, finger - 1].float()
            result[f"curriculum_finger_{finger}_success"] = (
                curriculum_success * selected)
            result[f"curriculum_finger_{finger}_count"] = selected
            result[f"press_finger_{finger}_success"] = (
                self.metric_finger_success[ids, finger - 1])
            result[f"press_finger_{finger}_count"] = (
                self.metric_finger_target[ids, finger - 1])
        for signature in range(1, 16):
            selected = (chord_signature == signature).float()
            result[f"curriculum_chord_set_{signature}_success"] = (
                curriculum_success * selected)
            result[f"curriculum_chord_set_{signature}_count"] = selected
        return result

    def step(self, actions):
        self.apply_actions(actions)
        self.step_physics()
        self.refresh()
        self.progress_buf += 1

        base_reasons = self.termination_reasons()
        timeout = base_reasons["timeout"]
        base_termination = base_reasons["base_termination"]
        nonfinite = torch.zeros(
            self.num_envs, dtype=torch.bool, device=self.device)
        for name, value in base_reasons.items():
            if name.startswith("nonfinite_"):
                nonfinite |= value
        velocity_blowup = base_reasons["velocity_blowup"]
        preparing = self.preparation_remaining > 0
        goal_frame_idx = self.goals.frame_idx.clone()
        goal = self.goals.current()
        event = goal["finger_event"].clone()
        delay = (
            self.preparation_remaining.float()
            / float(self.goals.fps)
            / FINGER_EVENT_TIME_SCALE_S)
        next_valid = event[..., 8] > 0.5
        event[..., 7] = torch.where(
            next_valid,
            (event[..., 7] + delay[:, None]).clamp(max=1.0),
            event[..., 7])
        finger_numbers = torch.arange(
            1, 5, device=self.device).view(1, 1, 4)
        current_active = (
            (goal["fret"] > 0)[..., None]
            & (goal["finger"][..., None] == finger_numbers)
        ).any(dim=1)
        event[..., 9] = torch.where(
            current_active,
            (event[..., 9] + delay[:, None]).clamp(max=1.0),
            event[..., 9])
        goal = dict(goal)
        goal["finger_event"] = event
        reward, metrics = self.reward_fn.compute(goal)
        (policy_teacher_action,
         policy_teacher_mask) = self._success_pose_policy_teacher(
            goal, metrics)
        finger_back = self.finger_back_monitor.compute()
        finger_back_cost = (
            self.finger_back_soft_penalty
            * finger_back["finger_back_soft_penalty"][:, None])
        reward = reward - finger_back_cost
        reward_nonfinite = ~torch.isfinite(reward).all(dim=1)
        nonfinite |= reward_nonfinite
        live = ~preparing
        metrics_enabled = live & ~nonfinite
        practice_stage = self.curriculum_stage in (
            "coarse_reach", "fine_reach",
            "isolated_press", "integrated_press",
            "chord_reach", "chord_fine_reach",
            "static_chord", "frozen_context", "goal_pair",
            "transition_window")
        if practice_stage:
            settling = ((self.goals.practice_remaining > 0)
                        & (self.goals.practice_remaining
                           <= self.curriculum_settling_frames))
            curriculum_diagnostic_enabled = metrics_enabled & settling
        else:
            curriculum_diagnostic_enabled = metrics_enabled
        # Capture the goal-pair phase before ``advance`` mutates the countdown
        # and switches the current frame.  These diagnostics deliberately use
        # the live MOVE gate rather than the end-of-episode settling gate.
        goal_pair_diagnostics = goal_pair_phase_diagnostics(
            self.curriculum_stage,
            metrics_enabled,
            self.goals.goal_pair_rehearsal_mask
            | self.goals.goal_pair_sequence_mask,
            self.goals.goal_pair_before_remaining,
            self.goals.goal_pair_incoming_finger,
            metrics["next_goal_progress_gate"],
            metrics["next_goal_current_press_preserved"],
            metrics["next_goal_current_press_preservation_quality"],
            metrics["next_goal_approach_distance"],
            metrics["next_goal_progress_per_finger"],
        )
        # Capture completion before advance so the final goal frame is evaluated.
        goal_finished = live & self.goals.done
        self._accumulate_metrics(metrics, enabled=metrics_enabled)
        self.sustain_tracker.update(
            goal["sustain_event_id"],
            goal["sustain_eligible"] & metrics_enabled[:, None],
            metrics["press_success"])
        wrong_press_now = metrics["wrong_press"].any(dim=1)
        wrong_press_streak, wrong_press_termination = (
            update_wrong_press_termination(
                self.wrong_press_streak,
                wrong_press_now,
                metrics_enabled,
                stage=self.curriculum_stage,
                frames=self.wrong_press_termination_frames,
                stages=WRONG_PRESS_TERMINATION_STAGES))
        self.wrong_press_streak.copy_(wrong_press_streak)
        self.wrong_press_termination.copy_(wrong_press_termination)
        self.goals.advance(live)
        if self.goal_pair_action_routing:
            self._update_goal_pair_action_routing(
                torch.nonzero(live, as_tuple=False).squeeze(-1))
        self.preparation_remaining.sub_(1).clamp_(min=0)
        penetration = self.penetration_monitor.compute(self.progress_buf)
        filtered_penetration = exclude_thumb_from_generic_penetration(
            penetration["guitar_penetration_depth_by_chain"],
            penetration["guitar_tunneled_by_chain"],
            penetration["guitar_penetration_termination_by_chain"],
            penetration_threshold=self.penetration_monitor.threshold)
        raw_termination = penetration["guitar_penetration_termination"]
        penetration["guitar_penetration_raw_termination"] = raw_termination
        penetration["guitar_penetration_thumb_chain_excluded"] = (
            filtered_penetration["raw_thumb_unsafe"])
        penetration["guitar_penetration_effective_depth"] = (
            filtered_penetration["effective_depth"])
        penetration["guitar_penetration_termination"] = (
            filtered_penetration["termination"])
        penetration["guitar_penetration_termination_by_chain"] = (
            filtered_penetration["termination_by_chain"])
        penetration_soft_cost = guitar_penetration_soft_cost(
            filtered_penetration["effective_depth"],
            soft_threshold=self.penetration_soft_threshold,
            hard_threshold=self.penetration_monitor.threshold,
            max_cost=self.penetration_soft_penalty)
        reward = reward - penetration_soft_cost[:, None]
        unsafe_penetration = filtered_penetration["unsafe"]
        reward = suppress_positive_reward_on_penetration(
            reward, unsafe_penetration)
        finger_intersection = self.finger_intersection_monitor.compute(self.progress_buf)
        contact_load = self.contact_load_monitor.compute(goal)
        wrist_safety = self.wrist_safety_monitor.compute()
        palm_down_termination = self._update_palm_down_termination()
        thumb_force_violation = (
            metrics["thumb_contact_force"]
            > self.thumb_force_termination_threshold)
        thumb_compression_violation = (
            metrics["thumb_support"]
            & (metrics["thumb_compression"]
               > self.thumb_compression_termination_threshold))
        self.thumb_overforce_streak.copy_(update_consecutive_violation(
            self.thumb_overforce_streak,
            thumb_force_violation | thumb_compression_violation))
        self.thumb_overforce_termination.copy_(
            self.thumb_overforce_streak >= self.thumb_force_termination_frames)

        terminal_obs = self.compute_observations()
        # Base observations are sanitized before concatenation so PhysX/actor
        # never receive NaN/Inf.  Preserve the pre-sanitization latch as a
        # same-frame failure reason instead of accidentally treating zeros as
        # a valid observation for one transition.
        observation_nonfinite = (
            self.last_nonfinite_observation.clone()
            | ~torch.isfinite(terminal_obs).all(dim=1))
        nonfinite |= observation_nonfinite
        task_failure = (palm_down_termination
                        | self.thumb_overforce_termination
                        | self.wrong_press_termination
                        | wrist_safety["wrist_safety_termination"]
                        | finger_back["finger_back_termination"]
                        | penetration["guitar_penetration_termination"])
        self._update_success_rsi_cache(
            goal_frame_idx, metrics, terminal_obs,
            metrics_enabled & ~unsafe_penetration & ~task_failure
            & ~observation_nonfinite)
        # Reaching the planned time limit together with the final goal is normal.  A time limit
        # before the song finishes is a failure, as are non-finite state, velocity blow-up and
        # every hard task-safety reason.  A safety failure wins if it coincides with completion.
        early_timeout = timeout & ~goal_finished
        base_failure = torch.zeros_like(base_termination)
        for name, value in base_reasons.items():
            if name not in ("timeout", "base_termination"):
                base_failure |= value
        base_failure |= early_timeout | reward_nonfinite | observation_nonfinite
        failure_termination = base_failure | task_failure
        done = (base_termination | goal_finished | task_failure
                | reward_nonfinite | observation_nonfinite)
        normal_termination = done & ~failure_termination
        episode_success = goal_finished & ~failure_termination
        reward = torch.where(
            failure_termination[:, None],
            torch.full_like(reward, self.failure_termination_penalty),
            reward)
        # Keep the outward-facing done tensor independent from reset_buf.
        # reset_idx clears reset_buf for the next episode; aliasing the two
        # would therefore erase the terminal signal before it reaches PPO.
        self.reset_buf.copy_(done)
        active = metrics["active"]
        active_count = active.sum(dim=1)

        def active_mean(value):
            return value.masked_fill(~active, 0.0).sum(dim=1) / \
                active_count.clamp_min(1)

        arch_angles = torch.rad2deg(metrics["designated_arch_angles"])
        controlled_position = self.dof_state.view(
            self.num_envs, self.n_dof, 2)[:, self.ctrl_idx, 0]
        joint_limit_usage = normalized_joint_limit_usage(
            controlled_position, self.ctrl_lo, self.ctrl_hi)
        joint_limit_near = (
            joint_limit_usage >= self.joint_limit_diagnostic_fraction)
        if self.goals.finger_pose_slot_count:
            finger_pose_cache_fraction = (
                self._success_finger_pose_valid.any(dim=1).float().mean())
            finger_action_cache_fraction = (
                self._success_finger_action_valid.any(dim=1).float().mean())
        else:
            finger_pose_cache_fraction = torch.zeros(
                (), device=self.device)
            finger_action_cache_fraction = torch.zeros(
                (), device=self.device)
        info = {
            "mean_target_distance": active_mean(metrics["target_distance"]),
            "mean_local_reach_margin": active_mean(
                metrics["local_reach_margin"]),
            "active_count": active_count,
            "mean_press_depth": active_mean(metrics["press_depth"]),
            "mean_press_depth_progress": active_mean(
                metrics["press_depth_progress"]),
            "mean_press_hold_quality": active_mean(
                metrics["press_hold_quality"]),
            "press_hold_acquired_rate": active_mean(
                metrics["press_hold_acquired"].float()),
            "frame_press_dropout_rate": active_mean(
                metrics["press_dropout"].float()),
            "frame_press_near_miss_rate": active_mean(
                metrics["press_near_miss"].float()),
            "max_press_dropout_streak":
                metrics["press_dropout_streak"].amax(dim=1),
            "frame_chord_hold_quality": metrics["chord_hold_quality"],
            "mean_position_quality": active_mean(metrics["position_quality"]),
            "mean_ergonomic_position_quality": active_mean(
                metrics["ergonomic_position_quality"]),
            "mean_target_fraction": active_mean(
                metrics["target_fraction"]),
            "target_clearance_rate": metrics["target_clearance_ok"].float(),
            "mean_dense_position_quality": active_mean(
                metrics["dense_position_quality"]),
            "mean_precision_gate": active_mean(metrics["precision_gate"]),
            "mean_arch_quality": active_mean(metrics["arch_quality"]),
            "mean_good_position_quality": active_mean(
                metrics["good_position_quality"]),
            "mean_mcp_flexion_deg": active_mean(arch_angles[..., 0]),
            "mean_pip_flexion_deg": active_mean(arch_angles[..., 1]),
            "mean_dip_flexion_deg": active_mean(arch_angles[..., 2]),
            "tip_contact_rate": active_mean(metrics["tip_contact"].float()),
            "non_tip_contact_rate": active_mean(
                metrics["non_tip_contact"].float()),
            "mean_linear_distance_reward": active_mean(
                metrics["linear_distance_reward"]),
            "mean_fine_distance_reward": active_mean(
                metrics["fine_distance_reward"]),
            "mean_fine_alignment_quality": active_mean(
                metrics["fine_alignment_quality"]),
            "mean_fine_longitudinal_quality": active_mean(
                metrics["fine_longitudinal_quality"]),
            "mean_fine_lateral_quality": active_mean(
                metrics["fine_lateral_quality"]),
            "mean_fine_normal_quality": active_mean(
                metrics["fine_normal_quality"]),
            "mean_approach_progress": active_mean(metrics["approach_progress"]),
            "cell_alignment_rate": active_mean(metrics["cell_aligned"].float()),
            "curriculum_diagnostic_enabled": curriculum_diagnostic_enabled,
            "press_success_rate": active_mean(metrics["press_success"].float()),
            "wrong_press_count": metrics["wrong_press"].sum(dim=1),
            "wrong_press_streak": self.wrong_press_streak.clone(),
            "wrong_press_termination":
                self.wrong_press_termination.clone(),
            "supervised_count": metrics["supervised"].sum(dim=1),
            "joint_limit_max_usage": joint_limit_usage.amax(dim=1),
            "joint_limit_near_rate": joint_limit_near.float().mean(dim=1),
            "thumb_contact": metrics["thumb_contact"].clone(),
            "thumb_base_action_saturation":
                (self.prev_action[:, self._thumb_base_action_indices].abs()
                 > 0.95).float().mean(dim=1),
            "thumb_base_action_x":
                self.prev_action[:, self._thumb_base_action_indices[0]],
            "thumb_base_action_y":
                self.prev_action[:, self._thumb_base_action_indices[1]],
            "thumb_base_action_z":
                self.prev_action[:, self._thumb_base_action_indices[2]],
            "thumb_base_action_saturation_x":
                (self.prev_action[
                    :, self._thumb_base_action_indices[0]].abs()
                 > 0.95),
            "thumb_base_action_saturation_y":
                (self.prev_action[
                    :, self._thumb_base_action_indices[1]].abs()
                 > 0.95),
            "thumb_base_action_saturation_z":
                (self.prev_action[
                    :, self._thumb_base_action_indices[2]].abs()
                 > 0.95),
            "thumb_overforce_streak": self.thumb_overforce_streak.clone(),
            "thumb_force_violation": thumb_force_violation,
            "thumb_compression_violation": thumb_compression_violation,
            "thumb_overforce_termination":
                self.thumb_overforce_termination.clone(),
            "isolated_press_active": (
                (self.curriculum_stage == "isolated_press")
                & (self.progress_buf
                   >= self.isolated_press_lock_after_frames)),
            "isolated_press_restricted": (
                (self.curriculum_stage == "isolated_press")
                & (self.progress_buf
                   >= self.isolated_press_lock_after_frames)),
            "release_pose_error_deg": (
                metrics["release_pose_error_deg"]
                * metrics["release_pose_gate"].float()).sum(dim=1)
                / metrics["release_pose_gate"].sum(dim=1).clamp_min(1),
            "release_pose_active_rate":
                metrics["release_pose_gate"].float().mean(dim=1),
            "finger_coupling_active_rate":
                metrics["finger_coupling_gate"].float().mean(dim=1),
            "finger_coupling_target_speed_deg": (
                metrics["finger_coupling_target_speed_deg"]
                * metrics["finger_coupling_gate"].float()).sum(dim=1)
                / metrics["finger_coupling_gate"].sum(dim=1).clamp_min(1),
            "finger_synergy_active_rate":
                self.finger_synergy_gate.float().mean(dim=1),
            "finger_synergy_induced_deg": (
                self.finger_synergy_induced_deg
                * self.finger_synergy_gate.float()).sum(dim=1)
                / self.finger_synergy_gate.sum(dim=1).clamp_min(1),
            "goal_pair_action_routing_active":
                self._goal_pair_routed_fingers.float().mean(dim=1),
            "goal_pair_action_release_active":
                (self._goal_pair_release_remaining > 0).float().mean(dim=1),
            "next_goal_approach_active_rate":
                metrics["next_goal_approach_gate"].float().mean(dim=1),
            "next_goal_approach_distance": (
                metrics["next_goal_approach_distance"]
                * metrics["next_goal_approach_gate"].float()).sum(dim=1)
                / metrics["next_goal_approach_gate"].sum(dim=1).clamp_min(1),
            "next_goal_progress_active_rate":
                metrics["next_goal_progress_gate"].float().mean(dim=1),
            "palm_world_z": self.palm_world_z.clone(),
            "palm_normal_valid": self.palm_normal_valid.clone(),
            "palm_down_streak": self.palm_down_streak.clone(),
            "palm_down_termination": self.palm_down_termination.clone(),
            "goal_finished": goal_finished.clone(),
            "timeout": timeout.clone(),
            "early_timeout": early_timeout.clone(),
            "nonfinite": nonfinite.clone(),
            "nonfinite_reward": reward_nonfinite.clone(),
            "nonfinite_observation": observation_nonfinite.clone(),
            "velocity_blowup": velocity_blowup.clone(),
            "failure_termination": failure_termination.clone(),
            "normal_termination": normal_termination.clone(),
            "successful_termination": episode_success.clone(),
            "preparing": preparing.clone(),
            "goal_metrics_enabled": metrics_enabled.clone(),
            "preparation_remaining_frames": self.preparation_remaining.clone(),
            "success_rsi_reset": self.success_rsi_reset.clone(),
            "success_rsi_reset_quality":
                self.success_rsi_reset_quality.clone(),
            "success_rsi_cache_fraction":
                self._success_pose_valid.float().mean().expand(self.num_envs),
            "success_finger_pose_cache_fraction":
                finger_pose_cache_fraction.expand(self.num_envs),
            "success_finger_action_cache_fraction":
                finger_action_cache_fraction.expand(self.num_envs),
            "policy_teacher_action": policy_teacher_action,
            "policy_teacher_mask": policy_teacher_mask,
            "policy_teacher_proximal_active": policy_teacher_mask[
                :, self._finger_pose_proximal_action_indices].any(dim=1),
            "guitar_penetration_soft_cost": penetration_soft_cost,
        }
        for finger_index in range(4):
            info[f"policy_teacher_finger_{finger_index + 1}_active"] = (
                policy_teacher_mask[
                    :, self._finger_pose_action_indices[finger_index]
                ].any(dim=1))
        for group, indices in self.joint_limit_group_indices.items():
            group_usage = joint_limit_usage[:, indices]
            info[f"joint_limit_{group}_max_usage"] = group_usage.amax(dim=1)
            info[f"joint_limit_{group}_near_rate"] = (
                group_usage >= self.joint_limit_diagnostic_fraction
            ).float().mean(dim=1)
        info.update({name: metrics[name] for name in DIRECT_INFO_METRIC_KEYS})
        for finger_index in range(4):
            finger_number = finger_index + 1
            info[
                f"success_pose_guide_finger_{finger_number}_reward"] = (
                    metrics["success_pose_guide_per_finger"][
                        :, finger_index])
            info[
                f"success_pose_guide_finger_{finger_number}_active"] = (
                    metrics["success_pose_guide_active_per_finger"][
                        :, finger_index])
        if self.curriculum_stage == "goal_pair":
            sequence_active = (
                metrics_enabled & self.goals.goal_pair_sequence_mask)
            pair_active = (
                metrics_enabled
                & ~self.goals.goal_pair_rehearsal_mask
                & ~self.goals.goal_pair_sequence_mask)
            full_song_active = (
                sequence_active & self.goals.goal_pair_full_song_mask)
            press_count = metrics["active"].sum(dim=1)
            sequence_press_success = (
                (metrics["press_success"] & metrics["active"])
                .sum(dim=1).float() / press_count.clamp_min(1))
            sequence_press_success = torch.where(
                press_count > 0, sequence_press_success,
                torch.ones_like(sequence_press_success))
            no_press_count = metrics["no_press_active"].sum(dim=1)
            sequence_no_press_success = (
                (metrics["no_press_success"]
                 & metrics["no_press_active"]).sum(dim=1).float()
                / no_press_count.clamp_min(1))
            sequence_no_press_success = torch.where(
                no_press_count > 0, sequence_no_press_success,
                torch.ones_like(sequence_no_press_success))
            supervised_count = metrics["supervised"].sum(dim=1)
            sequence_wrong_press = (
                (metrics["wrong_press"] & metrics["supervised"])
                .sum(dim=1).float() / supervised_count.clamp_min(1))
            sequence_values = {
                "event_count":
                    self.goals.goal_pair_sequence_event_count.float(),
                "press_success": sequence_press_success,
                "no_press_success": sequence_no_press_success,
                "wrong_press": sequence_wrong_press,
                "thumb_support": metrics["thumb_support"].float(),
                "penetration": unsafe_penetration.float(),
            }
            info["goal_pair_sequence_active"] = sequence_active
            info["goal_pair_full_song_active"] = full_song_active
            for finger_number in range(1, 5):
                incoming_active = (
                    pair_active
                    & (self.goals.goal_pair_incoming_finger
                       == finger_number))
                info[f"goal_pair_incoming_finger_{finger_number}_active"] = (
                    incoming_active)
                info[
                    f"goal_pair_incoming_finger_{finger_number}_wrong_press"
                ] = metrics["wrong_press"].any(dim=1).float()
            for name, value in sequence_values.items():
                info[f"goal_pair_sequence_{name}"] = value
                info[f"goal_pair_full_song_{name}"] = value
        info.update(goal_pair_diagnostics)
        for finger_index in range(4):
            finger_mask = (
                active & metrics["finger_assignment"][..., finger_index])
            finger_count = finger_mask.sum(dim=1)

            def finger_mean(value):
                return (
                    value.masked_fill(~finger_mask, 0.0).sum(dim=1)
                    / finger_count.clamp_min(1))

            finger_number = finger_index + 1
            info[f"finger_{finger_number}_target_active"] = (
                finger_count > 0)
            info[f"finger_{finger_number}_target_distance"] = finger_mean(
                metrics["target_distance"])
            info[f"finger_{finger_number}_local_reach_margin"] = finger_mean(
                metrics["local_reach_margin"])
            info[f"finger_{finger_number}_fine_alignment_quality"] = (
                finger_mean(metrics["fine_alignment_quality"]))
            info[f"finger_{finger_number}_fine_longitudinal_quality"] = (
                finger_mean(metrics["fine_longitudinal_quality"]))
            info[f"finger_{finger_number}_fine_lateral_quality"] = (
                finger_mean(metrics["fine_lateral_quality"]))
            info[f"finger_{finger_number}_fine_normal_quality"] = (
                finger_mean(metrics["fine_normal_quality"]))
            if self.curriculum_stage == "goal_pair":
                rehearsal = self.goals.goal_pair_rehearsal_mask
                sequence = self.goals.goal_pair_sequence_mask
                finger_active = (finger_count > 0) & metrics_enabled
                finger_success = finger_mean(
                    metrics["press_success"].float())
                finger_distance = finger_mean(metrics["target_distance"])
                finger_hold_quality = finger_mean(
                    metrics["press_hold_quality"])
                finger_dropout_rate = finger_mean(
                    metrics["press_dropout"].float())
                finger_wrong_press = metrics[
                    "wrong_press_per_finger"][:, finger_index].float()
                cohorts = {
                    "rehearsal": rehearsal,
                    "transition": ~rehearsal & ~sequence,
                    "sequence": sequence,
                    "full_song": self.goals.goal_pair_full_song_mask,
                }
                for cohort_name, cohort_mask in cohorts.items():
                    prefix = (
                        f"goal_pair_{cohort_name}_finger_{finger_number}")
                    info[f"{prefix}_target_active"] = (
                        finger_active & cohort_mask)
                    info[f"{prefix}_target_distance"] = finger_distance
                    info[f"{prefix}_press_success"] = finger_success
                    info[f"{prefix}_hold_quality"] = finger_hold_quality
                    info[f"{prefix}_dropout_rate"] = finger_dropout_rate
                    info[f"{prefix}_wrong_press"] = finger_wrong_press
                incoming_target = (
                    pair_active
                    & (self.goals.goal_pair_incoming_finger
                       == finger_number))
                previous_mask = self.goals.goal_pair_previous_finger_mask
                for source_finger in range(5):
                    source_active = (
                        ~previous_mask.any(dim=1)
                        if source_finger == 0
                        else previous_mask[:, source_finger - 1])
                    matrix_prefix = (
                        f"goal_pair_transition_{source_finger}"
                        f"_to_{finger_number}")
                    info[f"{matrix_prefix}_target_active"] = (
                        finger_active & incoming_target & source_active)
                    info[f"{matrix_prefix}_press_success"] = finger_success
                    info[f"{matrix_prefix}_wrong_press"] = (
                        metrics["wrong_press"].any(dim=1).float())
        info.update({name: value.clone() for name, value in penetration.items()})
        info.update({name: value.clone() for name, value in finger_intersection.items()})
        info.update({name: value.clone() for name, value in contact_load.items()})
        info.update({name: value.clone() for name, value in wrist_safety.items()})
        info.update({name: value.clone() for name, value in finger_back.items()})
        info.update(self._episode_metrics(done))
        info.update(self.sustain_tracker.episode_metrics(done))

        env_ids = torch.nonzero(done).squeeze(-1)
        info["terminal_env_ids"] = env_ids.clone()
        info["terminal_observation"] = terminal_obs[env_ids].clone()
        episode_reasons = {
            "goal_finished": goal_finished,
            "timeout": timeout,
            "early_timeout": early_timeout,
            "nonfinite": nonfinite,
            "velocity_blowup": velocity_blowup,
            "palm_down_termination": palm_down_termination,
            "thumb_overforce_termination": self.thumb_overforce_termination,
            "wrong_press_termination": self.wrong_press_termination,
            "wrist_safety_termination":
                wrist_safety["wrist_safety_termination"],
            "finger_back_termination":
                finger_back["finger_back_termination"],
            "guitar_penetration_termination":
                penetration["guitar_penetration_termination"],
            "failure_termination": failure_termination,
            "normal_termination": normal_termination,
            "success": episode_success,
        }
        for chain_index, chain_name in enumerate(
                self.penetration_monitor.CHAIN_NAMES):
            episode_reasons[
                f"guitar_penetration_{chain_name}_termination"] = (
                    penetration[
                        "guitar_penetration_termination_by_chain"
                    ][:, chain_index])
        info.update({f"episode_{name}": value[env_ids].clone()
                     for name, value in episode_reasons.items()})
        for name, value in base_reasons.items():
            info.setdefault(name, value.clone())
        # Preserve the boolean reason fields while preventing invalid physical
        # diagnostics from poisoning evaluation aggregation/logging.
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
