"""R12 goal-aware proximal-joint motion priority."""
from __future__ import annotations

import torch

from .common import smoothstep01


GROUP_PREFIXES = {
    "finger": ("LH:",),
    "wrist": ("L_Wrist",),
    "elbow": ("L_Elbow",),
    "shoulder": ("L_Thorax", "L_Shoulder"),
}

GROUP_WEIGHTS = {
    "finger": 0.05,
    "wrist": 0.20,
    "elbow": 0.50,
    "shoulder": 1.00,
}


def target_settling_gate(distance, full_distance=0.015, transition=0.040):
    """Return 1 near the designated fingertip target and fade to 0 farther away."""
    if transition <= 0:
        raise ValueError("target settling transition must be positive")
    outside = (distance - float(full_distance)).clamp_min(0.0)
    return smoothstep01(1.0 - outside / transition)


def wrist_settling_gate(distance, radius, transition=0.10):
    """Compatibility wrapper retained for old diagnostics/tests."""
    outside = (distance - radius).clamp_min(0.0)
    return target_settling_gate(outside, full_distance=0.0,
                                transition=transition)


def proximal_priority_reward(group_motion, gate, weights=GROUP_WEIGHTS):
    """Map weighted normalized joint velocities to a [0,1] reward."""
    weighted = torch.zeros_like(gate)
    for name, weight in weights.items():
        weighted = weighted + float(weight) * group_motion[name]
    return torch.exp(-gate * weighted), weighted


class ProximalMotionReward:
    """Prefer fingers over wrist, elbow and shoulder after reaching the hand goal."""

    def __init__(self, env, transition=0.10):
        self.env = env
        self.transition = float(transition)
        if self.transition <= 0:
            raise ValueError("proximal wrist transition must be positive")
        self.indices = {}
        for group, prefixes in GROUP_PREFIXES.items():
            indices = [i for i, name in enumerate(env.dof_names)
                       if name.startswith(prefixes)]
            if not indices:
                raise KeyError(f"R12 motion group has no DOFs: {group}")
            self.indices[group] = torch.tensor(indices, device=env.device)

        lower = env.dof_lower.view(env.num_envs, env.n_dof)[0]
        upper = env.dof_upper.view(env.num_envs, env.n_dof)[0]
        min_range = torch.deg2rad(torch.tensor(10.0, device=env.device))
        self.dof_range = (upper - lower).clamp_min(min_range)

    def compute(self, target_distance, active):
        dof_velocity = self.env.dof_state.view(
            self.env.num_envs, self.env.n_dof, 2)[:, :, 1]
        group_motion = {}
        for name, indices in self.indices.items():
            normalized = dof_velocity[:, indices] / self.dof_range[indices]
            group_motion[name] = normalized.square().mean(dim=-1)

        if target_distance.shape != active.shape:
            raise ValueError("target distance and active mask must have matching shapes")
        nearest = target_distance.masked_fill(~active, float("inf")).min(dim=1).values
        nearest = torch.where(active.any(dim=1), nearest,
                              torch.full_like(nearest, 1.0))
        gate = target_settling_gate(nearest, transition=self.transition)
        reward, weighted = proximal_priority_reward(group_motion, gate)
        return reward, {
            "proximal_reward": reward,
            "proximal_gate": gate,
            "proximal_weighted_motion": weighted,
            "finger_motion": group_motion["finger"],
            "wrist_motion": group_motion["wrist"],
            "elbow_motion": group_motion["elbow"],
            "shoulder_motion": group_motion["shoulder"],
            "proximal_target_distance": nearest,
        }
