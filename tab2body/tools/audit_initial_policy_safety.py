"""Measure whether a newly initialized stochastic fret policy survives preparation.

This is a diagnostic, not a replacement for learned-song evaluation.  It makes
the otherwise easy-to-miss interaction between policy exploration, action
scaling, EMA actuation, and hard safety termination reproducible.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import isaacgym  # noqa: F401 -- Isaac Gym must precede torch
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cfg import FRET
from env.config import configured_kwargs
from env.tasks import FretTask
from learning import ActorCritic


def parser():
    p = argparse.ArgumentParser()
    p.add_argument("--num-envs", type=int, default=32)
    p.add_argument("--frames", type=int, default=120)
    p.add_argument("--action-scale", type=float, default=FRET["action_scale"])
    p.add_argument("--action-alpha", type=float, default=FRET["action_alpha"])
    p.add_argument("--init-std", type=float, default=FRET["policy_init_std"])
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--require-zero-failures", action="store_true")
    return p


@torch.no_grad()
def main(argv=None):
    args = parser().parse_args(argv)
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)
    env = FretTask(**configured_kwargs(
              FretTask, FRET,
              goal_path=FRET["goal_path"],
              hand_targets_path=FRET["hand_targets_path"],
              num_envs=args.num_envs,
              device=FRET["device"],
              headless=True,
              seed=args.seed,
              reset_noise=FRET["reset_noise"],
              random_start=True,
              reset_soft_limit_fraction=FRET["reset_soft_limit_fraction"],
              preparation_frames=FRET["preparation_frames"]
          ))
    try:
        # Runtime overrides make parameter sweeps possible without changing the
        # training configuration.  They are applied before the first reset so
        # the actuator's inverse-hold state uses the same mapping.
        env.action_scale = float(args.action_scale)
        env.action_alpha = float(args.action_alpha)
        init_action = env.actions_for_pd_targets(
            env.init_pose[env.ctrl_idx][None].expand(env.num_envs, -1))[0]
        model = ActorCritic(
            env.num_obs, env.num_actions, env.value_dim,
            init_std=args.init_std, init_mean=init_action).to(env.device)
        obs = env.reset()
        terminated_env = torch.zeros(
            env.num_envs, dtype=torch.bool, device=env.device)
        counts = {name: 0 for name in (
            "done", "failure", "finger_back", "wrist", "palm_down",
            "nonfinite", "velocity_blowup")}
        goal_live_frames = 0
        violation_env_frames = 0
        max_abs_action = 0.0
        min_local_z = float("inf")
        for _ in range(args.frames):
            action, _, _ = model.act(obs)
            obs, _, done, info = env.step(action)
            terminated_env |= done
            counts["done"] += int(done.sum().cpu())
            counts["failure"] += int(info["failure_termination"].sum().cpu())
            counts["finger_back"] += int(
                info["finger_back_termination"].sum().cpu())
            counts["wrist"] += int(info["wrist_safety_termination"].sum().cpu())
            counts["palm_down"] += int(info["palm_down_termination"].sum().cpu())
            counts["nonfinite"] += int(info["nonfinite"].sum().cpu())
            counts["velocity_blowup"] += int(info["velocity_blowup"].sum().cpu())
            goal_live_frames += int(info["goal_metrics_enabled"].sum().cpu())
            violation_env_frames += int(info["finger_back_violation"].sum().cpu())
            max_abs_action = max(max_abs_action, float(action.abs().max().cpu()))
            min_local_z = min(
                min_local_z,
                float(info["finger_back_min_local_z"].min().cpu()))

        total_frames = args.num_envs * args.frames
        result = {
            "num_envs": args.num_envs,
            "frames": args.frames,
            "action_scale": args.action_scale,
            "action_alpha": args.action_alpha,
            "init_std": args.init_std,
            **counts,
            "unique_envs_terminated": int(terminated_env.sum().cpu()),
            "goal_live_fraction": goal_live_frames / total_frames,
            "finger_back_violation_fraction": violation_env_frames / total_frames,
            "minimum_finger_local_z_m": min_local_z,
            "max_abs_policy_action": max_abs_action,
        }
        print(json.dumps(result, indent=2))
        if args.require_zero_failures and counts["failure"]:
            raise AssertionError(
                f"initialized policy produced {counts['failure']} safety failures")
    finally:
        env.close()


if __name__ == "__main__":
    main()
