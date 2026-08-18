"""Stage-masked reward terms for the virtual-pick strike task."""
from __future__ import annotations

import json
import math
from numbers import Real
from pathlib import Path
from typing import Mapping

import torch

try:
    from tab2body.strike_contract import STRIKE_STAGES
except ModuleNotFoundError as exc:
    if exc.name != "tab2body":
        raise
    from strike_contract import STRIKE_STAGES


STAGES = STRIKE_STAGES

_REWARD_CONFIG_KEYS = (
    "grip_weight", "reach_weight", "reach_discount",
    "ready_quality_weight",
    "crossing_reward", "completion_reward", "wrong_crossing_penalty",
    "unprepared_crossing_penalty", "miss_penalty", "zone_weight",
    "timing_core_ms",
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
        grip_weights = config.get("grip_weight")
        if not isinstance(grip_weights, Mapping):
            raise ValueError("strike grip_weight must be a mapping")
        if set(grip_weights) != set(STAGES):
            raise ValueError("grip weights must cover the five strike stages")
        self.grip_weights = {
            stage: _finite_nonnegative(
                grip_weights[stage], f"grip_weight[{stage}]")
            for stage in STAGES
        }
        self.reach_weight = _finite_nonnegative(
            config.get("reach_weight"), "reach_weight")
        self.reach_discount = _finite_number(
            config.get("reach_discount"), "reach_discount")
        if not 0.0 < self.reach_discount <= 1.0:
            raise ValueError("reach_discount must be in (0, 1]")
        ready_quality_weights = config.get("ready_quality_weight")
        if (not isinstance(ready_quality_weights, Mapping)
                or set(ready_quality_weights) != set(STAGES)):
            raise ValueError(
                "ready_quality_weight must cover the five strike stages")
        self.ready_quality_weights = {
            stage: _finite_nonnegative(
                ready_quality_weights[stage],
                f"ready_quality_weight[{stage}]")
            for stage in STAGES
        }
        self.crossing_reward = _finite_nonnegative(
            config.get("crossing_reward"), "crossing_reward")
        completion_rewards = config.get("completion_reward")
        if (not isinstance(completion_rewards, Mapping)
                or set(completion_rewards) != set(STAGES)):
            raise ValueError(
                "completion_reward must cover the five strike stages")
        self.completion_rewards = {
            stage: _finite_nonnegative(
                completion_rewards[stage], f"completion_reward[{stage}]")
            for stage in STAGES
        }
        self.wrong_penalty = _finite_nonnegative(
            config.get("wrong_crossing_penalty"), "wrong_crossing_penalty")
        self.unprepared_crossing_penalty = _finite_nonnegative(
            config.get("unprepared_crossing_penalty"),
            "unprepared_crossing_penalty")
        self.miss_penalty = _finite_nonnegative(
            config.get("miss_penalty"), "miss_penalty")
        self.zone_weight = _finite_nonnegative(
            config.get("zone_weight"), "zone_weight")
        self.timing_core_s = _finite_positive(
            config.get("timing_core_ms"), "timing_core_ms") / 1000.0

    def compute(self, stage, *, grip_quality, reach_progress, ready_quality,
                ready_pulse, ready_acquired, target_hit, wrong_crossing_count,
                miss_pulse, timing_error_s, zone_quality, zone_attempt):
        if stage not in STAGES:
            raise ValueError(f"unknown strike stage: {stage}")
        dtype = grip_quality.dtype
        reward = torch.zeros_like(grip_quality)
        terms = {}

        grip_weight = self.grip_weights[stage]
        if stage == "A0_PICK_GRIP":
            grip_term = grip_weight * grip_quality
        else:
            grip_term = -grip_weight * (1.0 - grip_quality)
        reward += grip_term
        terms["reward_grip"] = grip_term

        reach_term = torch.zeros_like(reward)
        if stage != "A0_PICK_GRIP":
            reach_term = self.reach_weight * reach_progress.clamp(-1.0, 1.0)
            reward += reach_term
        terms["reward_reach_progress"] = reach_term

        pending_ready = ~ready_acquired
        ready_quality_term = torch.zeros_like(reward)
        if stage == "A1_TIP_READY":
            ready_quality_term = (
                self.ready_quality_weights[stage] * ready_quality)
            reward += ready_quality_term
        elif stage in STAGES[2:]:
            ready_quality_term = (
                -self.ready_quality_weights[stage]
                * (1.0 - ready_quality)
                * pending_ready.to(dtype))
            reward += ready_quality_term
        terms["reward_ready_quality"] = ready_quality_term

        ready_term = torch.zeros_like(reward)
        if stage in STAGES[1:]:
            ready_term = (
                self.completion_rewards[stage] * ready_pulse.to(dtype))
            reward += ready_term
        terms["reward_ready"] = ready_term

        hit_term = torch.zeros_like(reward)
        timing_term = torch.zeros_like(reward)
        zone_term = torch.zeros_like(reward)
        prepared_hit = target_hit & ready_acquired
        unprepared_hit = target_hit & ~ready_acquired
        if stage in STAGES[2:]:
            hit_term = self.crossing_reward * prepared_hit.to(dtype)
            reward += hit_term
        if stage in STAGES[3:]:
            timing_quality = torch.exp(
                -(timing_error_s.abs() / self.timing_core_s) ** 2)
            timing_term = (0.25 * self.crossing_reward
                           * timing_quality * prepared_hit.to(dtype))
            reward += timing_term
        if stage == "A4_ZONE_CONTROL":
            zone_term = (
                self.zone_weight * zone_quality * zone_attempt.to(dtype)
                * ready_acquired.to(dtype))
            reward += zone_term
        terms["reward_crossing"] = hit_term
        terms["reward_timing"] = timing_term
        terms["reward_zone"] = zone_term

        unprepared_term = torch.zeros_like(reward)
        if stage in STAGES[2:]:
            unprepared_term = (
                -self.unprepared_crossing_penalty
                * unprepared_hit.to(dtype))
            reward += unprepared_term
        terms["penalty_unprepared_crossing"] = unprepared_term

        wrong_term = torch.zeros_like(reward)
        miss_term = torch.zeros_like(reward)
        if stage in STAGES[1:]:
            wrong_term = -self.wrong_penalty * wrong_crossing_count.to(dtype)
            reward += wrong_term
            miss_term = -self.miss_penalty * miss_pulse.to(dtype)
            reward += miss_term
        terms["penalty_wrong_crossing"] = wrong_term
        terms["penalty_miss"] = miss_term
        terms["reward_total"] = reward

        for name, value in terms.items():
            if value.shape != grip_quality.shape:
                raise RuntimeError(f"{name} changed strike reward batch shape")
            terms[name] = torch.nan_to_num(
                value, nan=0.0, posinf=0.0, neginf=0.0)
        return terms["reward_total"][:, None], terms
