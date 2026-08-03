"""Stage-masked reward terms for the virtual-pick strike task."""
from __future__ import annotations

import json
from pathlib import Path

import torch


STAGES = (
    "A0_PICK_GRIP",
    "A1_TIP_READY",
    "A2_FREE_CROSSING",
    "A3_TIMED_CROSSING",
    "A4_ZONE_CONTROL",
)


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
        if not isinstance(targets, dict) or not isinstance(groups, dict):
            raise ValueError("pick-grip reference is missing targets/groups")
        expected = {name for name in dof_names if name.startswith("RH:")}
        if set(targets) != expected:
            raise ValueError(
                "pick-grip target names must exactly match the current RH hand DOFs")
        index = {name: i for i, name in enumerate(dof_names)}
        ordered_names = [name for name in dof_names if name.startswith("RH:")]
        self.names = tuple(ordered_names)
        self.indices = torch.tensor(
            [index[name] for name in ordered_names],
            dtype=torch.long, device=device)
        self.target = torch.tensor(
            [float(targets[name]) for name in ordered_names],
            dtype=torch.float32, device=device)
        local_index = {name: i for i, name in enumerate(ordered_names)}
        self.pinch = torch.tensor(
            [local_index[name] for name in groups["pinch"]],
            dtype=torch.long, device=device)
        self.free = torch.tensor(
            [local_index[name] for name in groups["free"]],
            dtype=torch.long, device=device)
        if set(groups["pinch"]) | set(groups["free"]) != expected:
            raise ValueError("grip groups must cover every RH hand DOF exactly")
        if set(groups["pinch"]) & set(groups["free"]):
            raise ValueError("grip groups must be disjoint")
        self.pinch_weight = float(reward["pinch_weight"])
        self.free_weight = float(reward["free_weight"])
        if abs(self.pinch_weight + self.free_weight - 1.0) > 1e-6:
            raise ValueError("pick-grip group weights must sum to one")
        self.pinch_scale = float(reward["pinch_scale_rad"])
        self.free_scale = float(reward["free_scale_rad"])
        self.success_pinch_rms = float(reward["success_pinch_rms_rad"])
        self.success_free_rms = float(reward["success_free_rms_rad"])
        if min(self.pinch_scale, self.free_scale,
               self.success_pinch_rms, self.success_free_rms) <= 0.0:
            raise ValueError("pick-grip scales and thresholds must be positive")

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
        self.config = dict(config)
        self.grip_weights = {
            str(key): float(value)
            for key, value in self.config["grip_weight"].items()
        }
        if set(self.grip_weights) != set(STAGES):
            raise ValueError("grip weights must cover the five strike stages")
        self.reach_weight = float(self.config["reach_weight"])
        self.ready_quality_weight = float(
            self.config.get("ready_quality_weight", 0.0))
        self.crossing_reward = float(self.config["crossing_reward"])
        self.completion_reward = float(self.config["completion_reward"])
        self.wrong_penalty = float(self.config["wrong_crossing_penalty"])
        self.miss_penalty = float(self.config["miss_penalty"])
        self.zone_weight = float(self.config["zone_weight"])
        self.timing_core_s = float(self.config["timing_core_ms"]) / 1000.0
        if min(self.reach_weight, self.ready_quality_weight,
               self.crossing_reward,
               self.completion_reward, self.wrong_penalty,
               self.miss_penalty, self.zone_weight,
               self.timing_core_s) < 0.0:
            raise ValueError("strike reward parameters must be non-negative")

    def compute(self, stage, *, grip_quality, reach_progress, ready_quality,
                ready_pulse, target_hit, wrong_crossing_count,
                miss_pulse, timing_error_s, zone_quality, zone_attempt):
        if stage not in STAGES:
            raise ValueError(f"unknown strike stage: {stage}")
        dtype, device = grip_quality.dtype, grip_quality.device
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

        ready_quality_term = torch.zeros_like(reward)
        if stage == "A1_TIP_READY":
            ready_quality_term = self.ready_quality_weight * ready_quality
            reward += ready_quality_term
        terms["reward_ready_quality"] = ready_quality_term

        ready_term = torch.zeros_like(reward)
        if stage == "A1_TIP_READY":
            ready_term = self.completion_reward * ready_pulse.to(dtype)
            reward += ready_term
        terms["reward_ready"] = ready_term

        hit_term = torch.zeros_like(reward)
        timing_term = torch.zeros_like(reward)
        zone_term = torch.zeros_like(reward)
        if stage in STAGES[2:]:
            hit_term = self.crossing_reward * target_hit.to(dtype)
            reward += hit_term
        if stage in STAGES[3:]:
            timing_quality = torch.exp(
                -(timing_error_s.abs() / max(self.timing_core_s, 1e-8)) ** 2)
            timing_term = (0.25 * self.crossing_reward
                           * timing_quality * target_hit.to(dtype))
            reward += timing_term
        if stage == "A4_ZONE_CONTROL":
            zone_term = (
                self.zone_weight * zone_quality * zone_attempt.to(dtype))
            reward += zone_term
        terms["reward_crossing"] = hit_term
        terms["reward_timing"] = timing_term
        terms["reward_zone"] = zone_term

        wrong_term = torch.zeros_like(reward)
        miss_term = torch.zeros_like(reward)
        if stage in STAGES[1:]:
            wrong_term = -self.wrong_penalty * wrong_crossing_count.to(dtype)
            reward += wrong_term
        if stage in STAGES[1:]:
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
