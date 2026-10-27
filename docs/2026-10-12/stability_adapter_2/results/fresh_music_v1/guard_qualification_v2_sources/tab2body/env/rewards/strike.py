"""Stage-masked reward terms for the virtual-pick strike task."""
from __future__ import annotations

import json
import math
from numbers import Real
from pathlib import Path
from typing import Mapping

import torch

try:
    from tab2body.strike_contract import (
        A0_PICK_GRIP, A1_TIP_READY, A3_TIMED_SINGLE,
        STRIKE_STAGES, STRUM_STAGES, TIMED_STAGES, ZONE_STAGES)
except ModuleNotFoundError as exc:
    if exc.name != "tab2body":
        raise
    from strike_contract import (
        A0_PICK_GRIP, A1_TIP_READY, A3_TIMED_SINGLE,
        STRIKE_STAGES, STRUM_STAGES, TIMED_STAGES, ZONE_STAGES)


STAGES = STRIKE_STAGES

_REWARD_CONFIG_KEYS = (
    "grip_weight", "reach_weight", "reach_discount",
    "ready_quality_weight", "approach_progress_weight",
    "crossing_reward", "timing_progress_reward", "timing_wait_reward",
    "early_timing_penalty", "strum_progress_reward",
    "strum_terminal_progress_reward",
    "strum_physical_completion_reward",
    "strum_microtiming_weight",
    "strum_duration_core_ms", "completion_reward",
    "wrong_crossing_penalty",
    "unprepared_crossing_penalty", "miss_penalty",
    "premature_release_penalty", "zone_weight",
    "timing_core_ms", "recovery_progress_reward",
    "recovery_completion_reward", "recovery_speed_penalty_weight",
    "recovery_speed_limit_m_s", "recovery_speed_excess_m_s",
)


def _finite_number(value, name):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be a finite number")
    return result


def _finite_nonnegative(value, name):
    result = _finite_number(value, name)
    if result < 0.0:
        raise ValueError(f"{name} must be non-negative")
    return result


def _stage_nonnegative(config, name):
    values = config.get(name)
    if not isinstance(values, Mapping) or set(values) != set(STAGES):
        raise ValueError(f"{name} must cover all strike stages")
    return {
        stage: _finite_nonnegative(values[stage], f"{name}[{stage}]")
        for stage in STAGES
    }


def _finite_positive(value, name):
    result = _finite_number(value, name)
    if result <= 0.0:
        raise ValueError(f"{name} must be positive")
    return result


def _finite_unit_interval(value, name):
    result = _finite_number(value, name)
    if not 0.0 <= result <= 1.0:
        raise ValueError(f"{name} must be in [0, 1]")
    return result


def constrain_pick_grip_actions(
        policy_actions: torch.Tensor,
        reference_actions: torch.Tensor,
        residual_action_span: torch.Tensor,
        hand_mask: torch.Tensor) -> torch.Tensor:
    if policy_actions.ndim != 2:
        raise ValueError("policy_actions must have shape [N, A]")
    if reference_actions.shape not in (
            policy_actions.shape, (1, policy_actions.shape[1])):
        raise ValueError(
            "reference_actions must have shape [N, A] or [1, A]")
    if residual_action_span.shape != (policy_actions.shape[1],):
        raise ValueError("residual_action_span must have shape [A]")
    if hand_mask.shape != (policy_actions.shape[1],) \
            or hand_mask.dtype != torch.bool:
        raise ValueError("hand_mask must be a bool tensor with shape [A]")
    if (reference_actions.device != policy_actions.device
            or residual_action_span.device != policy_actions.device
            or hand_mask.device != policy_actions.device):
        raise ValueError("pick-grip action tensors must share a device")
    if (reference_actions.dtype != policy_actions.dtype
            or residual_action_span.dtype != policy_actions.dtype):
        raise ValueError("pick-grip action tensors must share a dtype")
    if (not torch.isfinite(reference_actions).all()
            or not torch.isfinite(residual_action_span).all()
            or torch.any(residual_action_span < 0.0)):
        raise ValueError("pick-grip action contract must be finite and non-negative")
    constrained = (
        reference_actions
        + policy_actions.clamp(-1.0, 1.0) * residual_action_span[None]
    ).clamp(-1.0, 1.0)
    return torch.where(hand_mask[None], constrained, policy_actions)


def strike_reach_potential_delta(
        previous: torch.Tensor,
        current: torch.Tensor,
        valid_previous: torch.Tensor,
        *,
        discount: float) -> torch.Tensor:
    """Return gamma-correct potential shaping with no first-frame jump."""
    if not all(isinstance(value, torch.Tensor) for value in (
            previous, current, valid_previous)):
        raise TypeError("strike reach potential inputs must be tensors")
    if (not previous.is_floating_point()
            or current.dtype != previous.dtype):
        raise TypeError("strike reach potentials must share a floating dtype")
    if valid_previous.dtype != torch.bool:
        raise TypeError("valid_previous must use torch.bool")
    if (previous.shape != current.shape
            or previous.shape != valid_previous.shape):
        raise ValueError("strike reach potential inputs must share a shape")
    if (previous.device != current.device
            or previous.device != valid_previous.device):
        raise ValueError("strike reach potential inputs must share a device")
    if (not torch.isfinite(previous).all()
            or not torch.isfinite(current).all()
            or torch.any(previous < 0.0) or torch.any(previous > 1.0)
            or torch.any(current < 0.0) or torch.any(current > 1.0)):
        raise ValueError("strike reach potentials must be finite in [0, 1]")
    discount = _finite_number(discount, "reach discount")
    if not 0.0 < discount <= 1.0:
        raise ValueError("reach discount must be in (0, 1]")
    return torch.where(
        valid_previous,
        discount * current - previous,
        torch.zeros_like(current))


def strike_terminal_potential_delta(
        previous: torch.Tensor,
        current: torch.Tensor,
        terminal: torch.Tensor,
        *,
        discount: float) -> torch.Tensor:
    if (previous.shape != current.shape or terminal.shape != previous.shape
            or terminal.dtype != torch.bool):
        raise ValueError("terminal potential inputs must share shape [N]")
    if (not previous.is_floating_point() or current.dtype != previous.dtype
            or previous.device != current.device
            or previous.device != terminal.device):
        raise TypeError("terminal potentials must share floating dtype/device")
    if (not torch.isfinite(previous).all()
            or not torch.isfinite(current).all()
            or torch.any(previous < 0.0) or torch.any(previous > 1.0)
            or torch.any(current < 0.0) or torch.any(current > 1.0)):
        raise ValueError("terminal potentials must be finite in [0, 1]")
    discount = _finite_number(discount, "potential discount")
    if not 0.0 < discount <= 1.0:
        raise ValueError("potential discount must be in (0, 1]")
    next_potential = torch.where(
        terminal, torch.zeros_like(current), current)
    return discount * next_potential - previous


class PickGripReference:
    """Machine-readable, achievable joint-coordinate grip reference."""

    def __init__(self, path, dof_names, device):
        self.path = Path(path).resolve()
        document = json.loads(self.path.read_text(encoding="utf-8"))
        if document.get("schema") != "tab2body.pick_grip_reference.v1":
            raise ValueError("unsupported pick-grip reference schema")
        targets = document.get("joint_targets_rad")
        groups = document.get("groups")
        reward = document.get("reward")
        if (not isinstance(targets, Mapping)
                or not isinstance(groups, Mapping)
                or not isinstance(reward, Mapping)):
            raise ValueError(
                "pick-grip reference is missing targets/groups/reward")
        expected = {name for name in dof_names if name.startswith("RH:")}
        if set(targets) != expected:
            raise ValueError(
                "pick-grip target names must exactly match the current RH hand DOFs")
        index = {name: i for i, name in enumerate(dof_names)}
        ordered_names = [name for name in dof_names if name.startswith("RH:")]
        target_values = {
            name: _finite_number(targets[name], f"joint target {name}")
            for name in ordered_names
        }
        pinch_names = groups.get("pinch")
        free_names = groups.get("free")
        for name, values in (("pinch", pinch_names), ("free", free_names)):
            if (not isinstance(values, (list, tuple)) or not values
                    or not all(isinstance(value, str) for value in values)):
                raise ValueError(
                    f"pick-grip group {name} must be a non-empty name array")
            if len(set(values)) != len(values):
                raise ValueError(
                    f"pick-grip group {name} must not contain duplicate DOFs")
        if set(pinch_names) | set(free_names) != expected:
            raise ValueError("grip groups must cover every RH hand DOF exactly")
        if set(pinch_names) & set(free_names):
            raise ValueError("grip groups must be disjoint")
        self.names = tuple(ordered_names)
        self.pinch_names = tuple(pinch_names)
        self.free_names = tuple(free_names)
        self.indices = torch.tensor(
            [index[name] for name in ordered_names],
            dtype=torch.long, device=device)
        self.target = torch.tensor(
            [target_values[name] for name in ordered_names],
            dtype=torch.float32, device=device)
        local_index = {name: i for i, name in enumerate(ordered_names)}
        self.pinch = torch.tensor(
            [local_index[name] for name in pinch_names],
            dtype=torch.long, device=device)
        self.free = torch.tensor(
            [local_index[name] for name in free_names],
            dtype=torch.long, device=device)
        self.pinch_weight = _finite_unit_interval(
            reward.get("pinch_weight"), "pick-grip pinch_weight")
        self.free_weight = _finite_unit_interval(
            reward.get("free_weight"), "pick-grip free_weight")
        if abs(self.pinch_weight + self.free_weight - 1.0) > 1e-6:
            raise ValueError("pick-grip group weights must sum to one")
        self.pinch_scale = _finite_positive(
            reward.get("pinch_scale_rad"), "pick-grip pinch_scale_rad")
        self.free_scale = _finite_positive(
            reward.get("free_scale_rad"), "pick-grip free_scale_rad")
        self.success_pinch_rms = _finite_positive(
            reward.get("success_pinch_rms_rad"),
            "pick-grip success_pinch_rms_rad")
        self.success_free_rms = _finite_positive(
            reward.get("success_free_rms_rad"),
            "pick-grip success_free_rms_rad")

    def apply_to_pose(self, pose):
        pose = pose.clone()
        pose[self.indices] = self.target.to(dtype=pose.dtype)
        return pose

    def measure(self, dof_position):
        """Return grip quality and angular errors for ``(N,n_dof)`` positions."""
        current = dof_position[:, self.indices]
        error = current - self.target.to(dtype=current.dtype)[None]
        pinch_rms = error[:, self.pinch].square().mean(dim=-1).sqrt()
        free_rms = error[:, self.free].square().mean(dim=-1).sqrt()
        pinch_quality = torch.exp(
            -(pinch_rms / self.pinch_scale) ** 2)
        free_quality = torch.exp(
            -(free_rms / self.free_scale) ** 2)
        quality = (self.pinch_weight * pinch_quality
                   + self.free_weight * free_quality)
        success = ((pinch_rms <= self.success_pinch_rms)
                   & (free_rms <= self.success_free_rms))
        return {
            "grip_quality": quality,
            "grip_success": success,
            "grip_pinch_rms_rad": pinch_rms,
            "grip_free_rms_rad": free_rms,
            "grip_pinch_quality": pinch_quality,
            "grip_free_quality": free_quality,
        }


class StrikeReward:
    """Compose only the terms unlocked by the current acquisition stage.

    A0 uses positive posture quality.  Later stages use posture as a zero-at-
    reference penalty, preventing an accumulated idle baseline from overpowering
    the one-shot crossing objective.
    """

    def __init__(self, config):
        if not isinstance(config, Mapping):
            raise ValueError("strike reward config must be a mapping")
        missing = sorted(set(_REWARD_CONFIG_KEYS) - set(config))
        unknown = sorted(set(config) - set(_REWARD_CONFIG_KEYS))
        if missing or unknown:
            details = []
            if missing:
                details.append("missing=" + ",".join(missing))
            if unknown:
                details.append("unknown=" + ",".join(unknown))
            raise ValueError(
                "strike reward config must be closed ("
                + "; ".join(details) + ")")
        self.grip_weights = _stage_nonnegative(config, "grip_weight")
        self.reach_weight = _finite_nonnegative(
            config.get("reach_weight"), "reach_weight")
        self.reach_discount = _finite_number(
            config.get("reach_discount"), "reach_discount")
        if not 0.0 < self.reach_discount <= 1.0:
            raise ValueError("reach_discount must be in (0, 1]")
        self.ready_quality_weights = _stage_nonnegative(
            config, "ready_quality_weight")
        self.approach_progress_weights = _stage_nonnegative(
            config, "approach_progress_weight")
        self.crossing_reward = _finite_nonnegative(
            config.get("crossing_reward"), "crossing_reward")
        self.timing_progress_rewards = _stage_nonnegative(
            config, "timing_progress_reward")
        self.timing_wait_rewards = _stage_nonnegative(
            config, "timing_wait_reward")
        self.early_timing_penalties = _stage_nonnegative(
            config, "early_timing_penalty")
        self.strum_progress_rewards = _stage_nonnegative(
            config, "strum_progress_reward")
        self.strum_terminal_progress_rewards = _stage_nonnegative(
            config, "strum_terminal_progress_reward")
        self.strum_physical_completion_rewards = _stage_nonnegative(
            config, "strum_physical_completion_reward")
        self.strum_microtiming_weights = _stage_nonnegative(
            config, "strum_microtiming_weight")
        self.strum_duration_core_s = _finite_positive(
            config.get("strum_duration_core_ms"),
            "strum_duration_core_ms") / 1000.0
        completion_rewards = config.get("completion_reward")
        if (not isinstance(completion_rewards, Mapping)
                or set(completion_rewards) != set(STAGES)):
            raise ValueError(
                "completion_reward must cover all strike stages")
        self.completion_rewards = {
            stage: _finite_nonnegative(
                completion_rewards[stage], f"completion_reward[{stage}]")
            for stage in STAGES
        }
        self.wrong_penalties = _stage_nonnegative(
            config, "wrong_crossing_penalty")
        self.unprepared_crossing_penalties = _stage_nonnegative(
            config, "unprepared_crossing_penalty")
        self.miss_penalties = _stage_nonnegative(config, "miss_penalty")
        self.premature_release_penalties = _stage_nonnegative(
            config, "premature_release_penalty")
        self.zone_weight = _finite_nonnegative(
            config.get("zone_weight"), "zone_weight")
        self.timing_core_s = _finite_positive(
            config.get("timing_core_ms"), "timing_core_ms") / 1000.0
        self.recovery_progress_rewards = _stage_nonnegative(
            config, "recovery_progress_reward")
        self.recovery_completion_rewards = _stage_nonnegative(
            config, "recovery_completion_reward")
        self.recovery_speed_penalties = _stage_nonnegative(
            config, "recovery_speed_penalty_weight")
        self.recovery_speed_limit = _finite_nonnegative(
            config.get("recovery_speed_limit_m_s"),
            "recovery_speed_limit_m_s")
        self.recovery_speed_excess = _finite_positive(
            config.get("recovery_speed_excess_m_s"),
            "recovery_speed_excess_m_s")

    def compute(self, stage, *, grip_quality, reach_progress,
                ready_quality,
                ready_pulse, ready_acquired, target_hit, strum_progress,
                strum_terminal_progress, strum_physical_completion_pulse,
                timing_progress_quality, timing_wait_quality,
                early_timing_cost, strum_timing_sample,
                strum_timing_rms_s, strum_duration_error_s,
                wrong_crossing_count, miss_pulse, premature_release,
                clean_event,
                timing_core_s, duration_core_s,
                zone_quality, zone_attempt, recovery_active,
                recovery_progress, recovery_complete_pulse,
                recovery_speed_m_s):
        if stage not in STAGES:
            raise ValueError(f"unknown strike stage: {stage}")
        if (clean_event.shape != grip_quality.shape
                or clean_event.dtype != torch.bool
                or clean_event.device != grip_quality.device):
            raise ValueError(
                "clean_event must be a matching bool tensor")
        if (strum_terminal_progress.shape != grip_quality.shape
                or not strum_terminal_progress.is_floating_point()
                or strum_terminal_progress.device != grip_quality.device
                or not torch.isfinite(strum_terminal_progress).all()
                or torch.any(strum_terminal_progress < 0.0)
                or torch.any(strum_terminal_progress > 1.0)):
            raise ValueError(
                "strum_terminal_progress must be finite in [0, 1]")
        if (strum_physical_completion_pulse.shape != grip_quality.shape
                or strum_physical_completion_pulse.dtype != torch.bool
                or strum_physical_completion_pulse.device
                != grip_quality.device):
            raise ValueError(
                "strum_physical_completion_pulse must be a matching bool tensor")
        dtype = grip_quality.dtype
        reward = torch.zeros_like(grip_quality)
        terms = {}

        grip_weight = self.grip_weights[stage]
        if stage == A0_PICK_GRIP:
            grip_term = grip_weight * grip_quality
        else:
            grip_term = -grip_weight * (1.0 - grip_quality)
        reward += grip_term
        terms["reward_grip"] = grip_term

        reach_term = torch.zeros_like(reward)
        if stage != A0_PICK_GRIP:
            reach_term = self.reach_weight * reach_progress.clamp(-1.0, 1.0)
            reward += reach_term
        terms["reward_reach_progress"] = reach_term

        approach_progress_term = (
            self.approach_progress_weights[stage]
            * reach_progress.clamp(-1.0, 1.0))
        reward += approach_progress_term
        terms["reward_approach_progress"] = approach_progress_term

        pending_ready = ~ready_acquired
        ready_quality_term = torch.zeros_like(reward)
        if stage == A1_TIP_READY:
            ready_quality_term = (
                self.ready_quality_weights[stage] * ready_quality)
            reward += ready_quality_term
        elif stage not in (A0_PICK_GRIP, A1_TIP_READY):
            ready_quality_term = (
                -self.ready_quality_weights[stage]
                * (1.0 - ready_quality)
                * pending_ready.to(dtype))
            reward += ready_quality_term
        terms["reward_ready_quality"] = ready_quality_term

        ready_term = torch.zeros_like(reward)
        if stage != A0_PICK_GRIP:
            ready_term = (
                self.completion_rewards[stage] * ready_pulse.to(dtype))
            reward += ready_term
        terms["reward_ready"] = ready_term

        hit_term = torch.zeros_like(reward)
        timing_term = torch.zeros_like(reward)
        zone_term = torch.zeros_like(reward)
        prepared_hit = target_hit & ready_acquired
        unprepared_hit = target_hit & ~ready_acquired
        strum_progress_term = torch.zeros_like(reward)
        if stage in STRUM_STAGES:
            strum_progress_term = (
                self.strum_progress_rewards[stage] * strum_progress
                * ready_acquired.to(dtype))
            reward += strum_progress_term
        strum_terminal_progress_term = torch.zeros_like(reward)
        strum_physical_completion_term = torch.zeros_like(reward)
        if stage in STRUM_STAGES:
            strum_terminal_progress_term = (
                self.strum_terminal_progress_rewards[stage]
                * strum_terminal_progress
                * clean_event.to(dtype)
                * ready_acquired.to(dtype))
            strum_physical_completion_term = (
                self.strum_physical_completion_rewards[stage]
                * strum_physical_completion_pulse.to(dtype)
                * clean_event.to(dtype)
                * ready_acquired.to(dtype))
            reward += strum_terminal_progress_term
            reward += strum_physical_completion_term
        strum_microtiming_term = torch.zeros_like(reward)
        if stage in TIMED_STAGES and stage in STRUM_STAGES:
            timing_quality = 1.0 / (
                1.0 + (strum_timing_rms_s.abs() / timing_core_s) ** 2)
            duration_quality = 1.0 / (
                1.0 + (strum_duration_error_s.abs()
                        / duration_core_s) ** 2)
            strum_microtiming_term = (
                self.strum_microtiming_weights[stage]
                * 0.5 * (timing_quality + duration_quality)
                * strum_timing_sample.to(dtype)
                * clean_event.to(dtype)
                * ready_acquired.to(dtype))
            reward += strum_microtiming_term
        if stage not in (A0_PICK_GRIP, A1_TIP_READY):
            hit_term = self.crossing_reward * prepared_hit.to(dtype)
            reward += hit_term
        if stage in TIMED_STAGES:
            timing_term = (self.timing_progress_rewards[stage]
                           * timing_progress_quality.clamp(0.0, 1.0)
                           * clean_event.to(dtype)
                           * ready_acquired.to(dtype))
            reward += timing_term
        timing_wait_term = torch.zeros_like(reward)
        if stage in TIMED_STAGES:
            timing_wait_term = (
                self.timing_wait_rewards[stage]
                * timing_wait_quality.clamp(0.0, 1.0))
            reward += timing_wait_term
        if stage in TIMED_STAGES:
            zone_term = (
                self.zone_weight * zone_quality * zone_attempt.to(dtype)
                * ready_acquired.to(dtype))
            reward += zone_term
        terms["reward_crossing"] = hit_term
        terms["reward_strum_progress"] = strum_progress_term
        terms["reward_strum_terminal_progress"] = (
            strum_terminal_progress_term)
        terms["reward_strum_physical_completion"] = (
            strum_physical_completion_term)
        terms["reward_strum_microtiming"] = strum_microtiming_term
        terms["reward_timing"] = timing_term
        terms["reward_timing_wait"] = timing_wait_term
        terms["reward_zone"] = zone_term

        recovery_progress_term = (
            self.recovery_progress_rewards[stage] * recovery_progress)
        reward += recovery_progress_term
        terms["reward_recovery_progress"] = recovery_progress_term

        recovery_completion_term = (
            self.recovery_completion_rewards[stage]
            * recovery_complete_pulse.to(dtype))
        reward += recovery_completion_term
        terms["reward_recovery_completion"] = recovery_completion_term

        recovery_speed_excess = (
            (recovery_speed_m_s - self.recovery_speed_limit)
            / self.recovery_speed_excess
        ).clamp(0.0, 1.0)
        recovery_speed_term = (
            -self.recovery_speed_penalties[stage]
            * recovery_speed_excess.square()
            * recovery_active.to(dtype))
        reward += recovery_speed_term
        terms["penalty_recovery_speed"] = recovery_speed_term

        unprepared_term = torch.zeros_like(reward)
        if stage not in (A0_PICK_GRIP, A1_TIP_READY):
            unprepared_term = (
                -self.unprepared_crossing_penalties[stage]
                * unprepared_hit.to(dtype))
            reward += unprepared_term
        terms["penalty_unprepared_crossing"] = unprepared_term

        wrong_term = torch.zeros_like(reward)
        miss_term = torch.zeros_like(reward)
        premature_term = torch.zeros_like(reward)
        early_timing_term = torch.zeros_like(reward)
        if stage != A0_PICK_GRIP:
            wrong_term = (
                -self.wrong_penalties[stage] * wrong_crossing_count.to(dtype))
            reward += wrong_term
            miss_term = -self.miss_penalties[stage] * miss_pulse.to(dtype)
            reward += miss_term
            premature_term = (
                -self.premature_release_penalties[stage]
                * premature_release.to(dtype))
            reward += premature_term
            early_timing_term = (
                -self.early_timing_penalties[stage]
                * early_timing_cost.clamp(0.0, 1.0))
            reward += early_timing_term
        terms["penalty_wrong_crossing"] = wrong_term
        terms["penalty_miss"] = miss_term
        terms["penalty_premature_release"] = premature_term
        terms["penalty_early_timing"] = early_timing_term
        terms["reward_total"] = reward

        for name, value in terms.items():
            if value.shape != grip_quality.shape:
                raise RuntimeError(f"{name} changed strike reward batch shape")
            terms[name] = torch.nan_to_num(
                value, nan=0.0, posinf=0.0, neginf=0.0)
        return terms["reward_total"][:, None], terms
