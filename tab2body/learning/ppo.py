"""줄별 멀티크리틱 PPO."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import math
import time

import torch

from .checkpoint_contract import (
    copy_validated_contract,
    verify_checkpoint_contract,
)
from .run_layout import layout_for


EPISODE_METRIC_KEYS = (
    "accuracy_l", "precision_l", "recall_l", "f1_l",
    "no_press_accuracy", "no_press_correct_count",
    "no_press_evidence_count", "wrong_press_rate",
    "sustain_hold_rate", "sustain_event_success_rate",
    "sustain_event_success_count",
    "sustain_min_event_hold_rate", "sustain_max_dropout_frames",
    "sustain_interruption_count", "sustain_event_count",
    "curriculum_success_rate",
    "chord_ready_rate", "chord_hold_quality",
    "press_dropout_rate", "press_max_dropout_frames",
    "curriculum_finger_1_success", "curriculum_finger_1_count",
    "curriculum_finger_2_success", "curriculum_finger_2_count",
    "curriculum_finger_3_success", "curriculum_finger_3_count",
    "curriculum_finger_4_success", "curriculum_finger_4_count",
    "press_finger_1_success", "press_finger_1_count",
    "press_finger_2_success", "press_finger_2_count",
    "press_finger_3_success", "press_finger_3_count",
    "press_finger_4_success", "press_finger_4_count",
) + tuple(
    name
    for signature in range(1, 16)
    for name in (
        f"curriculum_chord_set_{signature}_success",
        f"curriculum_chord_set_{signature}_count",
    )
)
EPISODE_REASON_KEYS = (
    "goal_finished", "failure_termination", "early_timeout",
    "nonfinite", "velocity_blowup", "palm_down_termination",
    "thumb_overforce_termination",
    "wrong_press_termination",
    "wrist_safety_termination", "finger_back_termination",
    "guitar_penetration_termination",
) + tuple(
    f"guitar_penetration_{chain}_termination"
    for chain in ("arm", "thumb", "index", "middle", "ring", "pinky")
)
ROLLOUT_DIAGNOSTIC_KEYS = (
    "mean_target_distance", "mean_local_reach_margin",
    "joint_limit_max_usage", "joint_limit_near_rate",
    "cell_alignment_rate",
    "mean_position_quality", "mean_ergonomic_position_quality",
    "mean_target_fraction", "target_min_separation",
    "target_clearance_rate", "mean_dense_position_quality",
    "mean_precision_gate", "mean_arch_quality",
    "mean_good_position_quality", "press_success_rate",
    "mean_press_hold_quality", "press_hold_acquired_rate",
    "frame_press_dropout_rate", "frame_press_near_miss_rate",
    "max_press_dropout_streak",
    "chord_ready", "frame_chord_hold_quality",
    "mean_mcp_flexion_deg", "mean_pip_flexion_deg",
    "mean_dip_flexion_deg", "tip_contact_rate",
    "non_tip_contact_rate",
    "mean_fine_distance_reward", "mean_fine_alignment_quality",
    "mean_fine_longitudinal_quality", "mean_fine_lateral_quality",
    "mean_fine_normal_quality",
    "mean_approach_progress", "isolated_press_active",
    "isolated_press_restricted",
    "release_pose_reward", "release_pose_error_deg",
    "release_pose_active_rate",
    "finger_coupling_reward", "finger_coupling_active_rate",
    "finger_coupling_target_speed_deg",
    "finger_coupling_press_protected",
    "reference_finger_posture_quality",
    "reference_thumb_posture_quality",
    "reference_posture_quality", "reference_posture_penalty",
    "reference_posture_active",
    "finger_synergy_active_rate", "finger_synergy_induced_deg",
    "goal_pair_action_routing_active",
    "goal_pair_action_release_active",
    "next_goal_approach_reward", "next_goal_approach_active_rate",
    "next_goal_approach_distance",
    "next_goal_progress_reward", "next_goal_progress_active_rate",
    "next_goal_current_press_preserved",
    "next_goal_current_press_preservation_quality",
    "next_goal_current_press_preservation_gate",
    "next_goal_joint_preservation_quality",
    "goal_pair_rehearsal_anchor_reward",
    "goal_pair_rehearsal_anchor_active",
    "goal_pair_anchor_next_reward", "goal_pair_anchor_next_active",
    "success_pose_guide_reward", "success_pose_guide_active",
    "success_pose_guide_anchor_reward",
    "success_pose_guide_anchor_active",
    "success_pose_guide_proximal_reward",
    "success_pose_guide_proximal_active",
    "press_class_reward", "press_class_mean_reward",
    "press_class_min_reward", "no_press_class_reward",
    "press_class_completion", "no_press_class_completion",
    "effective_press_class_weight",
    "effective_no_press_class_weight", "class_balanced_reward",
    "class_balance_enabled", "chord_joint_quality",
    "chord_bridge_bottleneck_reward", "chord_bridge_mean_reward",
    "chord_bridge_min_reward",
    "chord_fine_joint_reward", "chord_fine_joint_mean_reward",
    "chord_fine_joint_min_reward", "chord_fine_axis_min_quality",
    "chord_fine_broad_depth_progress",
    "thumb_reward", "thumb_distance", "thumb_gap", "thumb_contact_force",
    "thumb_contact", "thumb_in_back_region", "thumb_support",
    "thumb_wrong_contact", "thumb_goal_gate",
    "thumb_compression", "thumb_compression_quality",
    "thumb_solver_force_quality", "thumb_overforce",
    "thumb_solver_overforce",
    "thumb_geometric_support_quality", "thumb_footprint_quality",
    "thumb_gap_quality", "thumb_geometry_ready", "thumb_support_ready",
    "thumb_press_readiness", "thumb_press_factor", "thumb_support_streak",
    "thumb_support_stable_6", "thumb_support_stable_12",
    "thumb_base_action_saturation",
    "thumb_base_action_x", "thumb_base_action_y", "thumb_base_action_z",
    "thumb_base_action_saturation_x", "thumb_base_action_saturation_y",
    "thumb_base_action_saturation_z",
    "thumb_base_saturation_penalty",
    "finger_back_soft_penalty", "finger_back_min_local_z",
    "success_rsi_reset", "success_rsi_reset_quality",
    "success_rsi_cache_fraction",
    "success_finger_pose_cache_fraction",
    "success_finger_action_cache_fraction",
    "policy_teacher_proximal_active",
    "guitar_penetration_soft_cost",
    "guitar_penetration_effective_depth",
    "guitar_penetration_thumb_chain_excluded",
) + tuple(
    f"policy_teacher_finger_{finger}_active"
    for finger in range(1, 5)
) + tuple(
    name
    for finger in range(1, 5)
    for name in (
        f"success_pose_guide_finger_{finger}_reward",
        f"success_pose_guide_finger_{finger}_active",
    )
) + (
    "goal_pair_pretransition_active",
    "goal_pair_pretransition_current_press_preserved",
    "goal_pair_pretransition_current_press_quality",
) + tuple(
    name
    for finger in range(1, 5)
    for name in (
        f"goal_pair_incoming_finger_{finger}_active",
        f"goal_pair_incoming_finger_{finger}_wrong_press",
    )
) + tuple(
    name
    for finger in range(1, 5)
    for name in (
        f"finger_{finger}_target_active",
        f"finger_{finger}_target_distance",
        f"finger_{finger}_local_reach_margin",
        f"finger_{finger}_fine_alignment_quality",
        f"finger_{finger}_fine_longitudinal_quality",
        f"finger_{finger}_fine_lateral_quality",
        f"finger_{finger}_fine_normal_quality",
    )
) + tuple(
    name
    for cohort in ("rehearsal", "transition", "sequence", "full_song")
    for finger in range(1, 5)
    for name in (
        f"goal_pair_{cohort}_finger_{finger}_target_active",
        f"goal_pair_{cohort}_finger_{finger}_target_distance",
        f"goal_pair_{cohort}_finger_{finger}_press_success",
        f"goal_pair_{cohort}_finger_{finger}_hold_quality",
        f"goal_pair_{cohort}_finger_{finger}_dropout_rate",
        f"goal_pair_{cohort}_finger_{finger}_wrong_press",
    )
) + tuple(
    name
    for finger in range(1, 5)
    for name in (
        f"goal_pair_transition_finger_{finger}_next_active",
        f"goal_pair_transition_finger_{finger}_next_distance",
        f"goal_pair_transition_finger_{finger}_next_progress",
    )
) + tuple(
    f"goal_pair_{scope}_{name}"
    for scope in ("sequence", "full_song")
    for name in (
        "active", "event_count", "press_success", "no_press_success", "wrong_press",
        "thumb_support", "penetration",
    )
) + tuple(
    name
    for source in range(5)
    for target in range(1, 5)
    for name in (
        f"goal_pair_transition_{source}_to_{target}_target_active",
        f"goal_pair_transition_{source}_to_{target}_press_success",
        f"goal_pair_transition_{source}_to_{target}_wrong_press",
    )
) + tuple(
    f"joint_limit_{group}_{metric}"
    for group in (
        "thorax", "shoulder", "elbow", "wrist", "thumb",
        "finger_1", "finger_2", "finger_3", "finger_4",
    )
    for metric in ("max_usage", "near_rate")
)


def _diagnostic_uses_live_gate(name):
    """Whether an explicitly phase-gated metric precedes settling."""
    return (
        name.startswith("next_goal_")
        or name.startswith("goal_pair_pretransition_")
        or (name.startswith("goal_pair_transition_finger_")
            and "_next_" in name)
    )


def _conditional_diagnostic_active_key(name):
    """Return the per-env evidence mask for a conditional diagnostic."""
    if name == "next_goal_current_press_preservation_quality":
        return "next_goal_current_press_preservation_gate"
    if name in (
            "goal_pair_pretransition_current_press_preserved",
            "goal_pair_pretransition_current_press_quality"):
        return "goal_pair_pretransition_active"
    if (name.startswith("goal_pair_transition_finger_")
            and name.endswith(("_next_distance", "_next_progress"))):
        return name.rsplit("_", 1)[0] + "_active"
    if (name.startswith("goal_pair_incoming_finger_")
            and name.endswith("_wrong_press")):
        return name.rsplit("_", 2)[0] + "_active"
    if (name.startswith("goal_pair_transition_")
            and "_to_" in name
            and name.endswith(("_press_success", "_wrong_press"))):
        return name.rsplit("_", 2)[0] + "_target_active"
    if (name.startswith("goal_pair_") and "_finger_" in name
            and name.endswith((
                "_target_distance", "_press_success",
                "_hold_quality", "_dropout_rate", "_wrong_press"))):
        prefix, suffix = name.split("_finger_", 1)
        finger = suffix.split("_", 1)[0]
        return f"{prefix}_finger_{finger}_target_active"
    return None


def _format_metric(value):
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (float, int)):
        return f"{value:.4f}"
    return str(value)


def detailed_training_line(stats):
    return " ".join(
        [f"iter={int(stats['iteration'])}", f"steps={int(stats['steps'])}"]
        + [f"{key}={_format_metric(value)}"
           for key, value in stats.items()
           if key not in ("iteration", "steps")
           and isinstance(value, (bool, int, float, str))])


def compact_training_stats(stats):
    """Keep JSONL useful for plots without repeating checkpoint-sized state."""
    return {
        key: value
        for key, value in stats.items()
        if isinstance(value, (bool, int, float, str))
    }


def concise_training_line(stats, first, last):
    iteration = int(stats["iteration"])
    completed = iteration - int(first) + 1
    total = max(int(last) - int(first) + 1, 1)
    fields = [f"epoch {iteration}/{last} ({100.0 * completed / total:5.1f}%)"]
    stage = stats.get("curriculum_stage")
    if stage is not None:
        stage_iteration = int(stats.get("curriculum_stage_iteration", 0))
        fields.append(f"stage={stage}:{stage_iteration}")
    if stats.get("curriculum_stalled", False):
        fields.append("stalled=continue")
    if stats.get("curriculum_goal_pair_recovery", False):
        reason = stats.get(
            "curriculum_goal_pair_recovery_reason", "recovery")
        recovery_iteration = int(stats.get(
            "curriculum_goal_pair_recovery_iteration", 0))
        recovery_max = int(stats.get(
            "curriculum_goal_pair_recovery_max_iterations", 0))
        fields.append(
            f"recovery={reason}:{recovery_iteration}/{recovery_max}")
    if stats.get("curriculum_goal_pair_recovery_rollback", False):
        rollback = stats.get(
            "curriculum_goal_pair_last_recovery_rollback", "unknown")
        fields.append(f"rollback={rollback}")
    if stats.get("curriculum_forced_advance", False):
        previous = stats.get("curriculum_last_forced_advance_from", "unknown")
        fields.append(f"forced-advance={previous}")
    if stats.get("curriculum_complete", False):
        fields.append("curriculum=complete")
    fields.append(f"reward={float(stats.get('reward', 0.0)):.4f}")
    p90 = stats.get("curriculum_p90_target_distance")
    if p90 is not None:
        fields.append(f"p90={1000.0 * float(p90):.1f}mm")
    success = stats.get("curriculum_success_rate")
    if success is not None:
        fields.append(f"success={100.0 * float(success):.1f}%")
    f1 = stats.get("f1_l")
    if f1 is None:
        f1 = stats.get("strike_f1")
    if f1 is None:
        f1 = stats.get("strike_episode_f1")
    if f1 is None:
        f1 = stats.get("curriculum_strike_f1")
    if f1 is not None:
        fields.append(f"F1={float(f1):.3f}")
    tolerance = stats.get("timing_tolerance_ms")
    if tolerance is None:
        tolerance = stats.get("curriculum_timing_tolerance_ms")
    if tolerance is not None:
        fields.append(f"tol={float(tolerance):.0f}ms")
    grip = stats.get("curriculum_grip_quality")
    if grip is not None:
        fields.append(f"grip={float(grip):.3f}")
    failure = stats.get("failure_termination")
    if failure is not None:
        fields.append(f"fail={100.0 * float(failure):.1f}%")
    return " | ".join(fields)


def combine_actor_advantages(advantages, weights):
    """Combine value-head advantages before applying PPO normalization.

    Contract version: ``SCALAR_ADVANTAGE_VERSION``.  The reward coefficients
    have already been applied inside the environment.
    Normalizing every value head independently would erase their relative scale
    and give permanently unsupervised strings the same actor influence as active
    strings.  A single normalization after the weighted sum preserves the scalar
    objective seen by the policy.
    """
    if advantages.ndim < 2:
        raise ValueError("advantages must have a value-head dimension")
    weights = torch.as_tensor(
        weights, dtype=advantages.dtype, device=advantages.device).flatten()
    if weights.numel() != advantages.shape[-1]:
        raise ValueError(
            f"advantage weights {weights.numel()} != value heads {advantages.shape[-1]}")
    if not torch.isfinite(advantages).all() or not torch.isfinite(weights).all():
        raise FloatingPointError("non-finite advantage or actor reward weight")
    if (weights < 0).any() or float(weights.sum()) <= 0.0:
        raise ValueError("actor reward weights must be non-negative with a positive sum")
    weights = weights / weights.sum()
    scalar = (advantages * weights).sum(dim=-1)
    flat = scalar.reshape(-1)
    return (flat - flat.mean()) / (flat.std(unbiased=False) + 1e-8)


def verify_checkpoint_curriculum_alignment(checkpoint):
    """Fail if trainer and task snapshots describe different curricula."""
    context = checkpoint.get("training_context")
    environment = checkpoint.get("environment_state")
    if not isinstance(context, dict) or not isinstance(environment, dict):
        return
    pairs = (
        ("curriculum_stage", "curriculum_stage"),
        ("curriculum_timing_tolerance_ms", "timing_tolerance_ms"),
    )
    for context_key, environment_key in pairs:
        if context_key not in context or environment_key not in environment:
            continue
        expected = context[context_key]
        actual = environment[environment_key]
        if context_key.endswith("_ms"):
            try:
                matches = abs(float(expected) - float(actual)) <= 1e-9
            except (TypeError, ValueError):
                matches = False
        else:
            matches = expected == actual
        if not matches:
            raise ValueError(
                "checkpoint curriculum state mismatch: "
                f"training_context.{context_key}={expected!r}, "
                f"environment_state.{environment_key}={actual!r}")


def aggregate_episode_rows(rows, metric_keys, reason_keys):
    """Aggregate completed episodes, pooling raw strike timing samples."""
    if not rows:
        return {}
    result = {"episodes": len(rows)}
    timing_samples = [
        float(value)
        for row in rows
        for value in row.get("_timing_abs_ms", [])
    ]
    for key in tuple(metric_keys) + tuple(reason_keys):
        values = [row[key] for row in rows]
        total = sum(values)
        if key in ("sustain_max_dropout_frames",
                   "press_max_dropout_frames"):
            result[key] = max(values)
        elif key == "strike_timing_p95_ms" and timing_samples:
            result[key] = float(torch.quantile(
                torch.tensor(timing_samples), 0.95))
        elif key == "strike_timing_mae_ms" and timing_samples:
            result[key] = sum(timing_samples) / len(timing_samples)
        else:
            result[key] = total / len(values)
        if key in reason_keys:
            result[f"{key}_count"] = int(round(total))
    for source, target in (
            ("sustain_max_dropout_frames",
             "sustain_p95_dropout_frames"),
            ("press_max_dropout_frames",
             "press_p95_dropout_frames")):
        if source in rows[0]:
            result[target] = float(torch.quantile(
                torch.tensor(
                    [float(row[source]) for row in rows]),
                0.95))
    for finger in range(1, 5):
        success_key = f"press_finger_{finger}_success"
        count_key = f"press_finger_{finger}_count"
        if success_key not in result or count_key not in result:
            continue
        success_frames = int(round(sum(
            float(row[success_key]) for row in rows)))
        target_frames = int(round(sum(
            float(row[count_key]) for row in rows)))
        result[f"finger_{finger}_press_success_frames"] = success_frames
        result[f"finger_{finger}_press_target_frames"] = target_frames
        count = float(result[count_key])
        result[f"finger_{finger}_press_success_rate"] = (
            float(result[success_key]) / count if count > 0.0 else -1.0)
    available_fingers = [
        finger for finger in range(1, 5)
        if f"finger_{finger}_press_success_frames" in result]
    if available_fingers:
        result["press_success_frames"] = sum(
            result[f"finger_{finger}_press_success_frames"]
            for finger in available_fingers)
        result["press_target_frames"] = sum(
            result[f"finger_{finger}_press_target_frames"]
            for finger in available_fingers)
        target_frames = result["press_target_frames"]
        result["press_success_rate"] = (
            result["press_success_frames"] / target_frames
            if target_frames > 0 else -1.0)
    if ("sustain_event_success_count" in rows[0]
            and "sustain_event_count" in rows[0]):
        result["sustain_event_success_total"] = int(round(sum(
            float(row["sustain_event_success_count"]) for row in rows)))
        result["sustain_event_total"] = int(round(sum(
            float(row["sustain_event_count"]) for row in rows)))
        event_total = result["sustain_event_total"]
        result["sustain_event_success_rate_pooled"] = (
            result["sustain_event_success_total"] / event_total
            if event_total > 0 else -1.0)
    if "curriculum_success_rate" in rows[0]:
        result["curriculum_success_episodes"] = int(round(sum(
            float(row["curriculum_success_rate"]) for row in rows)))
        result["curriculum_episode_total"] = len(rows)
    for signature in range(1, 16):
        success_key = f"curriculum_chord_set_{signature}_success"
        count_key = f"curriculum_chord_set_{signature}_count"
        if success_key not in rows[0] or count_key not in rows[0]:
            continue
        success_total = int(round(sum(
            float(row[success_key]) for row in rows)))
        target_total = int(round(sum(
            float(row[count_key]) for row in rows)))
        if target_total <= 0:
            continue
        prefix = f"chord_set_{signature}"
        result[f"{prefix}_success_episodes"] = success_total
        result[f"{prefix}_target_episodes"] = target_total
        result[f"{prefix}_success_rate"] = success_total / target_total
    if timing_samples:
        result["strike_timing_sample_count"] = len(timing_samples)
    return result


def action_saturation_regularization(
        mean_action, action_indices, threshold, action_mask=None):
    """선택한 deterministic mean action의 경계 초과분을 제곱 평균한다."""
    if not isinstance(mean_action, torch.Tensor):
        raise TypeError("mean_action must be a torch.Tensor")
    if mean_action.ndim != 2:
        raise ValueError(
            f"mean_action must have shape [batch, action], got {mean_action.shape}")
    if not torch.is_floating_point(mean_action):
        raise TypeError("mean_action must be floating point")
    if not bool(torch.isfinite(mean_action).all()):
        raise FloatingPointError("mean_action contains a non-finite value")

    threshold = float(threshold)
    if not math.isfinite(threshold) or not 0.0 <= threshold < 1.0:
        raise ValueError("action saturation threshold must be in [0, 1)")

    indices = torch.as_tensor(action_indices, device=mean_action.device)
    if indices.ndim != 1 or indices.numel() == 0:
        raise ValueError("action_indices must be a non-empty rank-1 sequence")
    if indices.dtype == torch.bool or torch.is_floating_point(indices):
        raise TypeError("action_indices must contain integers")
    indices = indices.to(dtype=torch.long)
    if (int(indices.min()) < 0
            or int(indices.max()) >= mean_action.shape[1]):
        raise IndexError(
            "action saturation index is outside the policy action dimension")
    if torch.unique(indices).numel() != indices.numel():
        raise ValueError("action_indices must not contain duplicates")

    selected = mean_action.index_select(1, indices)
    excess = ((selected.abs() - threshold)
              / (1.0 - threshold)).clamp_min(0.0)
    squared = excess.square()
    if action_mask is None:
        return squared.mean()

    mask = torch.as_tensor(action_mask, device=mean_action.device)
    if mask.shape != mean_action.shape:
        raise ValueError(
            f"action mask shape {mask.shape} != {mean_action.shape}")
    if torch.is_floating_point(mask) and not bool(torch.isfinite(mask).all()):
        raise FloatingPointError("action mask contains a non-finite value")
    selected_mask = mask.to(dtype=torch.bool).index_select(1, indices)
    active = selected_mask.to(dtype=squared.dtype)
    active_count = active.sum()
    return (squared * active).sum() / active_count.clamp_min(1.0)


def masked_action_teacher_loss(mean_action, target_action, teacher_mask):
    """성공 자세가 있는 각 action 차원을 빈도와 무관하게 맞춘다."""
    if not isinstance(mean_action, torch.Tensor):
        raise TypeError("mean_action must be a torch.Tensor")
    if (mean_action.shape != target_action.shape
            or teacher_mask.shape != mean_action.shape):
        raise ValueError("action teacher tensors must share shape [N,A]")
    if mean_action.ndim != 2:
        raise ValueError("action teacher tensors must have shape [N,A]")
    if not torch.is_floating_point(mean_action):
        raise TypeError("action teacher tensors must be floating point")
    if (not torch.isfinite(mean_action).all()
            or not torch.isfinite(target_action).all()):
        raise FloatingPointError("action teacher tensors must be finite")
    active = teacher_mask.bool().to(mean_action.dtype)
    active_per_action = active.sum(dim=0)
    per_action_loss = (
        ((mean_action - target_action).square() * active).sum(dim=0)
        / active_per_action.clamp_min(1.0))
    available = (active_per_action > 0).to(mean_action.dtype)
    return (per_action_loss * available).sum() / available.sum().clamp_min(1.0)


@dataclass
class PPOConfig:
    horizon: int = 32
    epochs: int = 5
    minibatch_size: int = 4096
    gamma: float = 0.95
    gae_lambda: float = 0.95
    clip_ratio: float = 0.2
    value_coef: float = 1.0
    entropy_coef: float = 0.001
    actor_learning_rate: float = 3e-6
    learning_rate: float = 3e-4
    max_grad_norm: float = 1.0
    target_kl: float = 0.03
    action_saturation_regularization_weight: float = 0.0
    action_saturation_regularization_threshold: float = 0.90
    action_teacher_weight: float = 0.0
    save_interval: int = 500
    log_interval: int = 1


class PPOTrainer:
    def __init__(self, env, model, config: PPOConfig, out_dir=None):
        self.env = env
        self.model = model
        self.cfg = config
        self.device = torch.device(env.device)
        actor_parameters = list(model.actor.parameters()) + [model.log_std]
        critic_parameters = list(model.critic.parameters())
        known = {id(parameter) for parameter in actor_parameters + critic_parameters}
        unexpected = [parameter for parameter in model.parameters()
                      if id(parameter) not in known]
        if unexpected:
            raise ValueError("ActorCritic has unassigned trainable parameters")
        if config.actor_learning_rate <= 0.0 or config.learning_rate <= 0.0:
            raise ValueError("actor and critic learning rates must be positive")
        saturation_weight = float(
            config.action_saturation_regularization_weight)
        saturation_threshold = float(
            config.action_saturation_regularization_threshold)
        if not math.isfinite(saturation_weight) or saturation_weight < 0.0:
            raise ValueError(
                "action saturation regularization weight must be finite and non-negative")
        if (not math.isfinite(saturation_threshold)
                or not 0.0 <= saturation_threshold < 1.0):
            raise ValueError(
                "action saturation regularization threshold must be in [0, 1)")
        self.action_saturation_regularization_weight = saturation_weight
        self.action_saturation_regularization_threshold = saturation_threshold
        self.action_teacher_weight = float(config.action_teacher_weight)
        if (not math.isfinite(self.action_teacher_weight)
                or self.action_teacher_weight < 0.0):
            raise ValueError(
                "action teacher weight must be finite and non-negative")
        self.action_saturation_regularization_indices = None
        if saturation_weight > 0.0:
            indices = getattr(
                env, "action_saturation_regularization_indices", None)
            if indices is None:
                raise ValueError(
                    "positive action saturation regularization requires "
                    "environment action indices")
            indices = torch.as_tensor(indices, device=self.device)
            if indices.ndim != 1 or indices.numel() == 0:
                raise ValueError(
                    "environment action saturation indices must be non-empty rank-1")
            if indices.dtype == torch.bool or torch.is_floating_point(indices):
                raise TypeError(
                    "environment action saturation indices must be integers")
            indices = indices.to(dtype=torch.long)
            if (int(indices.min()) < 0
                    or int(indices.max()) >= env.num_actions):
                raise IndexError(
                    "environment action saturation index is out of bounds")
            if torch.unique(indices).numel() != indices.numel():
                raise ValueError(
                    "environment action saturation indices contain duplicates")
            self.action_saturation_regularization_indices = indices
        self.optimizer = torch.optim.Adam([
            {"params": actor_parameters, "lr": config.actor_learning_rate},
            {"params": critic_parameters, "lr": config.learning_rate},
        ])
        self.out_dir = Path(out_dir) if out_dir else None
        if self.out_dir:
            self.run_layout = layout_for(self.out_dir, create=True)
            self.checkpoint_dir = self.run_layout.checkpoints
            self.metrics_path = self.run_layout.metrics
            self.training_log_path = self.run_layout.training_log
        else:
            self.run_layout = None
            self.checkpoint_dir = None
            self.metrics_path = None
            self.training_log_path = None
        self.obs = env.reset()
        reward_weights = torch.as_tensor(
            env.reward_weights, dtype=torch.float32, device=self.device).clone()
        # A fixed-song policy has no useful task signal on strings that are
        # DONT_CARE for the whole song.  Their replicated auxiliary reward may
        # still train the value head, but must not occupy actor weight.
        if hasattr(env, "goals") and hasattr(env.goals, "fret"):
            supervised_strings = (env.goals.fret != 0).any(dim=0)
            if supervised_strings.numel() == reward_weights.numel():
                reward_weights *= supervised_strings.to(reward_weights.dtype)
        if float(reward_weights.sum()) <= 0.0:
            raise ValueError("the goal contains no supervised string for actor training")
        self.actor_reward_weights = reward_weights / reward_weights.sum()
        self.global_step = 0
        self.iteration = 0
        self.training_context = {}
        self.checkpoint_contract = None
        self.episode_metric_keys = tuple(getattr(
            env, "episode_metric_keys", EPISODE_METRIC_KEYS))
        self.episode_reason_keys = tuple(getattr(
            env, "episode_reason_keys", EPISODE_REASON_KEYS))
        self.rollout_diagnostic_keys = tuple(getattr(
            env, "rollout_diagnostic_keys", ROLLOUT_DIAGNOSTIC_KEYS))
        if not self.episode_metric_keys:
            raise ValueError("environment episode_metric_keys cannot be empty")

    @torch.no_grad()
    def collect(self):
        obs_b, act_b, logp_b, value_b, reward_b, done_b = [], [], [], [], [], []
        action_mask_b = []
        teacher_action_b, teacher_mask_b = [], []
        episode = []
        diagnostic_chunks = {
            name: [] for name in self.rollout_diagnostic_keys}
        for _ in range(self.cfg.horizon):
            action_mask_fn = getattr(self.env, "policy_action_mask", None)
            action_mask = (
                action_mask_fn() if callable(action_mask_fn) else None)
            action, logp, value = self.model.act(
                self.obs, action_mask=action_mask)
            # Isaac Gym tasks return their reusable ``obs_buf``.  Preserve the
            # observation that produced this action before ``env.step``
            # overwrites the buffer with the next frame.
            policy_obs = self.obs.clone()
            next_obs, reward, done, info = self.env.step(action)
            obs_b.append(policy_obs)
            act_b.append(action)
            logp_b.append(logp)
            value_b.append(value)
            reward_b.append(reward)
            done_b.append(done)
            if action_mask is not None:
                action_mask_b.append(action_mask.clone())
            teacher_action = info.get("policy_teacher_action")
            teacher_mask = info.get("policy_teacher_mask")
            if (teacher_action is None) != (teacher_mask is None):
                raise KeyError(
                    "environment must provide both policy teacher tensors")
            if teacher_action is not None:
                if (teacher_action.shape != action.shape
                        or teacher_mask.shape != action.shape):
                    raise ValueError(
                        "policy teacher tensors must match action shape")
                if not bool(torch.isfinite(teacher_action).all()):
                    raise FloatingPointError(
                        "policy teacher action contains a non-finite value")
                teacher_action_b.append(teacher_action.clone())
                teacher_mask_b.append(teacher_mask.clone())
            episode_trigger = self.episode_metric_keys[0]
            if episode_trigger in info:
                for key in self.episode_metric_keys:
                    if key not in info:
                        raise KeyError(
                            f"environment omitted episode metric {key!r}")
                for key in self.episode_reason_keys:
                    if f"episode_{key}" not in info:
                        raise KeyError(
                            f"environment omitted episode reason {key!r}")
                row_keys = (
                    tuple(self.episode_metric_keys)
                    + tuple(self.episode_reason_keys))
                row_tensors = [info[key] for key in self.episode_metric_keys]
                row_tensors.extend(
                    info[f"episode_{key}"]
                    for key in self.episode_reason_keys)
                cpu_rows = torch.stack([
                    value.detach().to(dtype=torch.float32)
                    for value in row_tensors
                ], dim=1).cpu()
                timing_count = info.get("episode_timing_count")
                timing_values = info.get("episode_timing_abs_ms")
                cpu_timing_count = (
                    timing_count.detach().cpu()
                    if timing_count is not None else None)
                cpu_timing_values = (
                    timing_values.detach().cpu()
                    if timing_values is not None else None)
                for i, values in enumerate(cpu_rows.tolist()):
                    row = dict(zip(row_keys, values))
                    if (cpu_timing_count is not None
                            and cpu_timing_values is not None):
                        count = int(cpu_timing_count[i])
                        row["_timing_abs_ms"] = (
                            cpu_timing_values[i, :count].tolist())
                    episode.append(row)
            active = info.get("diagnostic_active", info.get("active_count"))
            if active is not None:
                live_active_mask = (
                    active.bool() if active.dtype == torch.bool
                    else active > 0)
                diagnostic_gate = info.get("curriculum_diagnostic_enabled")
                settled_active_mask = live_active_mask
                if diagnostic_gate is not None:
                    settled_active_mask = (
                        live_active_mask & diagnostic_gate)
                for name in diagnostic_chunks:
                    value = info.get(name)
                    if value is not None:
                        sequence_scope = name.startswith((
                            "goal_pair_sequence_",
                            "goal_pair_full_song_"))
                        if sequence_scope:
                            scope = (
                                "goal_pair_full_song_active"
                                if name.startswith("goal_pair_full_song_")
                                else "goal_pair_sequence_active")
                            scope_active = info.get(scope)
                            if scope_active is None:
                                continue
                            metric_mask = scope_active.bool()
                        else:
                            metric_mask = (
                                live_active_mask
                                if _diagnostic_uses_live_gate(name)
                                else settled_active_mask)
                        if (name.startswith("finger_")
                                and not name.endswith("_target_active")):
                            finger = name.split("_", 2)[1]
                            finger_active = info.get(
                                f"finger_{finger}_target_active")
                            if finger_active is not None:
                                metric_mask = (
                                    settled_active_mask
                                    & finger_active.bool())
                        else:
                            active_name = (
                                _conditional_diagnostic_active_key(name))
                            conditional_active = info.get(active_name)
                            if conditional_active is not None:
                                metric_mask = (
                                    metric_mask
                                    & conditional_active.bool())
                        diagnostic_chunks[name].append(
                            value[metric_mask].detach())
            self.obs = next_obs
            self.global_step += self.env.num_envs
        next_value = self.model.value(self.obs)
        diagnostic_tensors = {}
        for name, chunks in diagnostic_chunks.items():
            if chunks:
                values = torch.cat(chunks)
                if values.numel() == 0:
                    continue
                # Boolean/integer diagnostics are logged as rates or means.
                mean_values = (
                    values if torch.is_floating_point(values)
                    else values.float())
                metric_name = f"curriculum_{name}"
                diagnostic_tensors[metric_name] = mean_values.mean()
                if name.endswith("_active"):
                    active_count = mean_values.sum()
                    diagnostic_tensors[f"{metric_name}_count"] = active_count
                    if name == "goal_pair_pretransition_active":
                        diagnostic_tensors[
                            "curriculum_goal_pair_pretransition_"
                            "current_press_preserved_count"] = active_count
                        diagnostic_tensors[
                            "curriculum_goal_pair_pretransition_"
                            "current_press_quality_count"] = active_count
                if name == "mean_target_distance":
                    diagnostic_tensors["curriculum_p90_target_distance"] = (
                        torch.quantile(mean_values, 0.90))
                elif name == "joint_limit_max_usage" or name.endswith(
                        "_max_usage"):
                    diagnostic_tensors[f"{metric_name}_p95"] = (
                        torch.quantile(mean_values, 0.95))
                elif name == "thumb_gap":
                    diagnostic_tensors["curriculum_thumb_gap_p10"] = (
                        torch.quantile(mean_values, 0.10))
                    diagnostic_tensors["curriculum_thumb_gap_p90"] = (
                        torch.quantile(mean_values, 0.90))
                elif name == "thumb_contact_force":
                    diagnostic_tensors[
                        "curriculum_thumb_contact_force_p95"] = (
                            torch.quantile(mean_values, 0.95))
                    diagnostic_tensors[
                        "curriculum_thumb_contact_force_max"] = (
                            mean_values.max())
        diagnostic_stats = {}
        if diagnostic_tensors:
            names = tuple(diagnostic_tensors)
            values = torch.stack([
                diagnostic_tensors[name].to(dtype=torch.float32)
                for name in names
            ]).detach().cpu().tolist()
            diagnostic_stats.update(zip(names, values))
        rollout = {
            "obs": torch.stack(obs_b), "actions": torch.stack(act_b),
            "logp": torch.stack(logp_b), "values": torch.stack(value_b),
            "rewards": torch.stack(reward_b), "dones": torch.stack(done_b),
            "next_value": next_value, "episode": episode,
            "diagnostics": diagnostic_stats,
        }
        if action_mask_b:
            rollout["action_masks"] = torch.stack(action_mask_b)
            rollout["diagnostics"]["policy_active_action_fraction"] = float(
                rollout["action_masks"].float().mean().cpu())
        if teacher_action_b:
            rollout["teacher_actions"] = torch.stack(teacher_action_b)
            rollout["teacher_masks"] = torch.stack(teacher_mask_b)
            rollout["diagnostics"]["policy_teacher_action_fraction"] = float(
                rollout["teacher_masks"].float().mean().cpu())
        # One synchronization per rollout, rather than several GPU->CPU checks
        # per control frame.  The environment already contains per-row finite
        # guards; this is the final fail-fast boundary before optimizer/RMS use.
        finite = torch.isfinite(next_value).all()
        for key in ("obs", "actions", "logp", "values", "rewards"):
            finite &= torch.isfinite(rollout[key]).all()
        if "teacher_actions" in rollout:
            finite &= torch.isfinite(rollout["teacher_actions"]).all()
        if not bool(finite):
            raise FloatingPointError("non-finite value reached the PPO rollout boundary")
        return rollout

    def advantages(self, rollout):
        rewards, values, dones = rollout["rewards"], rollout["values"], rollout["dones"]
        adv = torch.zeros_like(rewards)
        gae = torch.zeros_like(rollout["next_value"])
        next_value = rollout["next_value"]
        for t in reversed(range(self.cfg.horizon)):
            mask = (~dones[t]).float().unsqueeze(-1)
            delta = rewards[t] + self.cfg.gamma * next_value * mask - values[t]
            gae = delta + self.cfg.gamma * self.cfg.gae_lambda * mask * gae
            adv[t] = gae
            next_value = values[t]
        returns = adv + values
        flat = adv.reshape(-1, adv.shape[-1])
        actor_adv = combine_actor_advantages(flat, self.actor_reward_weights)
        return returns.reshape(-1, returns.shape[-1]), actor_adv

    def update(self, rollout):
        returns, actor_adv = self.advantages(rollout)
        obs = rollout["obs"].reshape(-1, self.env.num_obs)
        actions = rollout["actions"].reshape(-1, self.env.num_actions)
        old_logp = rollout["logp"].reshape(-1)
        old_values = rollout["values"].reshape(-1, self.env.value_dim)
        action_masks = rollout.get("action_masks")
        if action_masks is not None:
            action_masks = action_masks.reshape(-1, self.env.num_actions)
        teacher_actions = rollout.get("teacher_actions")
        teacher_masks = rollout.get("teacher_masks")
        if teacher_actions is not None:
            teacher_actions = teacher_actions.reshape(
                -1, self.env.num_actions)
            teacher_masks = teacher_masks.reshape(
                -1, self.env.num_actions)
        n = obs.shape[0]
        mb = min(self.cfg.minibatch_size, n)
        stats = {
            "policy_loss": 0.0,
            "value_loss": 0.0,
            "entropy": 0.0,
            "kl": 0.0,
            "action_saturation_loss": 0.0,
            "action_teacher_loss": 0.0,
        }
        updates = 0
        stop = False
        preupdate_kl = 0.0
        for _ in range(self.cfg.epochs):
            for idx in torch.randperm(n, device=self.device).split(mb):
                minibatch_mask = (
                    action_masks[idx] if action_masks is not None else None)
                deterministic_mean_action = None
                needs_mean_action = (
                    self.action_saturation_regularization_weight > 0.0
                    or (self.action_teacher_weight > 0.0
                        and teacher_actions is not None))
                if needs_mean_action:
                    (logp, entropy, value,
                     deterministic_mean_action) = self.model.evaluate_actions(
                        obs[idx], actions[idx],
                        action_mask=minibatch_mask,
                        return_mean_action=True)
                else:
                    logp, entropy, value = self.model.evaluate_actions(
                        obs[idx], actions[idx],
                        action_mask=minibatch_mask)
                # Stop before another mutation once the current policy has
                # already left the trust region.  The former post-step check
                # always applied one extra update after detecting overshoot.
                kl = (old_logp[idx] - logp).mean().detach()
                preupdate_kl = float(kl)
                if kl > self.cfg.target_kl:
                    stop = True
                    break
                ratio = (logp - old_logp[idx]).exp()
                unclipped = ratio * actor_adv[idx]
                clipped = ratio.clamp(1.0 - self.cfg.clip_ratio,
                                      1.0 + self.cfg.clip_ratio) * actor_adv[idx]
                policy_loss = -torch.minimum(unclipped, clipped).mean()

                value_clipped = old_values[idx] + (value - old_values[idx]).clamp(
                    -self.cfg.clip_ratio, self.cfg.clip_ratio)
                value_loss = 0.5 * torch.maximum(
                    (value - returns[idx]).square(),
                    (value_clipped - returns[idx]).square()).mean()
                entropy_mean = entropy.mean()
                loss = (policy_loss + self.cfg.value_coef * value_loss
                        - self.cfg.entropy_coef * entropy_mean)
                action_saturation_loss = None
                if self.action_saturation_regularization_weight > 0.0:
                    action_saturation_loss = (
                        self.action_saturation_regularization_weight
                        * action_saturation_regularization(
                            deterministic_mean_action,
                            self.action_saturation_regularization_indices,
                            self.action_saturation_regularization_threshold,
                            action_mask=minibatch_mask))
                    loss = loss + action_saturation_loss
                action_teacher_loss = None
                if (self.action_teacher_weight > 0.0
                        and teacher_actions is not None):
                    action_teacher_loss = (
                        self.action_teacher_weight
                        * masked_action_teacher_loss(
                            deterministic_mean_action,
                            teacher_actions[idx], teacher_masks[idx]))
                    loss = loss + action_teacher_loss

                self.optimizer.zero_grad(set_to_none=True)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.cfg.max_grad_norm)
                self.optimizer.step()
                stats["policy_loss"] += float(policy_loss.detach())
                stats["value_loss"] += float(value_loss.detach())
                stats["entropy"] += float(entropy_mean.detach())
                stats["kl"] += float(kl)
                if action_saturation_loss is not None:
                    stats["action_saturation_loss"] += float(
                        action_saturation_loss.detach())
                if action_teacher_loss is not None:
                    stats["action_teacher_loss"] += float(
                        action_teacher_loss.detach())
                updates += 1
            if stop:
                break
        # old_logp와 update 중 policy가 같은 정규화를 보도록 통계는 update 뒤 갱신한다.
        with torch.no_grad():
            self.model.obs_rms.update(obs)
        averaged = {k: v / max(1, updates) for k, v in stats.items()}
        averaged.update({
            "ppo_updates": updates,
            "ppo_preupdate_kl": preupdate_kl,
            "ppo_early_stop": stop,
        })
        return averaged

    def save(self, iteration):
        if not self.out_dir:
            return
        if self.checkpoint_contract is None:
            raise RuntimeError(
                "refusing to save a checkpoint without a configured environment contract")
        contract = copy_validated_contract(self.checkpoint_contract)
        context = dict(self.training_context)
        context["checkpoint_contract_sha256"] = contract["sha256"]
        environment = getattr(self, "env", None)
        task_name = getattr(environment, "task_name", "fret")
        target = self.checkpoint_dir / f"{task_name}_{iteration:06d}.pt"
        temporary = target.with_suffix(".pt.tmp")
        environment_state = (environment.curriculum_state_dict()
                             if hasattr(environment, "curriculum_state_dict") else None)
        checkpoint = {
            "iteration": iteration,
            "global_step": self.global_step,
            "model": self.model.state_dict(),
            "optimizer": self.optimizer.state_dict(),
            "training_context": context,
            "environment_state": environment_state,
            "checkpoint_contract": contract,
        }
        verify_checkpoint_curriculum_alignment(checkpoint)
        torch.save(checkpoint, temporary)
        # os.replace semantics on the same filesystem: an interruption can
        # leave a disposable .tmp, but never a half-written named checkpoint.
        temporary.replace(target)

    def set_checkpoint_contract(self, contract):
        self.checkpoint_contract = copy_validated_contract(contract)

    def _restore_checkpoint_state(self, checkpoint, model_state):
        self.model.load_state_dict(model_state, strict=True)
        if "optimizer" in checkpoint:
            self.optimizer.load_state_dict(checkpoint["optimizer"])
        self.iteration = int(checkpoint.get("iteration", 0))
        self.global_step = int(checkpoint.get("global_step", 0))
        self.training_context = dict(checkpoint.get("training_context", {}))
        environment_state = checkpoint.get("environment_state")
        environment = getattr(self, "env", None)
        if (environment_state is not None
                and hasattr(environment, "load_curriculum_state_dict")):
            reset_observation = environment.load_curriculum_state_dict(
                environment_state)
            if reset_observation is not None:
                self.obs = reset_observation

    def resume(self, checkpoint, purpose="resume"):
        """Verify compatibility, then restore model, optimizer and counters."""
        if self.checkpoint_contract is None:
            raise RuntimeError(
                "set_checkpoint_contract() is required before loading a checkpoint")
        # Verification deliberately precedes load_state_dict: a same-shaped but
        # semantically incompatible policy must never partially mutate this run.
        verify_checkpoint_contract(
            checkpoint, self.checkpoint_contract, purpose=purpose)
        verify_checkpoint_curriculum_alignment(checkpoint)
        self._restore_checkpoint_state(checkpoint, checkpoint["model"])

    def resume_migrated(self, checkpoint):
        """Restore a checkpoint after an explicit, user-requested contract migration.

        The normal ``resume`` path remains fail-closed.  This path is only for
        source-compatible changes such as curriculum thresholds: it still
        requires an exact model tensor layout and restores optimizer, counters,
        context, and environment state before the new contract is used for
        subsequent checkpoints.
        """
        if not isinstance(checkpoint, dict):
            raise TypeError("migrated checkpoint must be a mapping")
        source_model = checkpoint.get("model")
        if not isinstance(source_model, dict):
            raise ValueError("migrated checkpoint is missing model state")
        target_model = self.model.state_dict()
        if set(source_model) != set(target_model):
            raise ValueError("migrated checkpoint model keys do not match")
        for key, target in target_model.items():
            source = source_model[key]
            if source.shape != target.shape:
                raise ValueError(
                    f"migrated checkpoint tensor shape mismatch for {key}: "
                    f"{tuple(source.shape)} != {tuple(target.shape)}")
        self._restore_checkpoint_state(checkpoint, source_model)

    def learn(self, iterations, iteration_callback=None,
              iteration_result_callback=None, post_iteration_callback=None,
              history_limit=None):
        if history_limit is not None:
            history_limit = int(history_limit)
            if history_limit < 0:
                raise ValueError("history_limit must be non-negative or None")
        started = time.time()
        history = []
        first = self.iteration + 1
        last = self.iteration + int(iterations)
        for iteration in range(first, last + 1):
            iteration_context = (iteration_callback(iteration)
                                 if iteration_callback is not None else {})
            iteration_context = dict(iteration_context or {})
            reset_observation = iteration_context.pop("_reset_observation", None)
            if reset_observation is not None:
                self.obs = reset_observation
            if iteration_context:
                self.training_context.update(iteration_context)
            rollout = self.collect()
            stats = self.update(rollout)
            stats["iteration"] = iteration
            stats["steps"] = self.global_step
            stats["reward"] = float(rollout["rewards"].mean())
            stats.update(rollout.get("diagnostics", {}))
            stats.update(iteration_context)
            if rollout["episode"]:
                stats.update(aggregate_episode_rows(
                    rollout["episode"],
                    self.episode_metric_keys,
                    self.episode_reason_keys))
            if iteration_result_callback is not None:
                result_context = iteration_result_callback(stats) or {}
                self.training_context.update(result_context)
                for key, value in result_context.items():
                    if key in iteration_context:
                        stats[f"next_{key}"] = value
                    else:
                        stats[key] = value
            if history_limit is None or history_limit > 0:
                history.append(stats)
                if (history_limit is not None
                        and len(history) > history_limit):
                    del history[:-history_limit]
            stage = stats.get("curriculum_stage")
            previous_stage = getattr(self, "_last_logged_stage", None)
            write_log = (
                iteration == first
                or iteration == last
                or iteration % self.cfg.log_interval == 0
                or (self.out_dir
                    and iteration % self.cfg.save_interval == 0)
                or stage != previous_stage)
            if self.metrics_path and write_log:
                with self.metrics_path.open("a") as f:
                    f.write(json.dumps(
                        compact_training_stats(stats), sort_keys=True) + "\n")
                self._last_logged_stage = stage
            if iteration % self.cfg.log_interval == 0:
                detailed = detailed_training_line(stats)
                if self.training_log_path:
                    with self.training_log_path.open("a") as stream:
                        stream.write(detailed + "\n")
                print(concise_training_line(stats, first, last), flush=True)
            if self.out_dir and iteration % self.cfg.save_interval == 0:
                self.save(iteration)
            self.iteration = iteration
            if post_iteration_callback is not None:
                post_iteration_callback(iteration, stats)
        if self.out_dir:
            self.save(self.iteration)
        message = (f"training finished: {self.global_step} samples "
                   f"in {time.time()-started:.1f}s")
        if self.training_log_path:
            with self.training_log_path.open("a") as stream:
                stream.write(message + "\n")
        print(message)
        return history
