"""Run a short GPU rollout and summarize R22 inter-finger proxy intersections."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import isaacgym  # noqa: F401 -- must precede torch
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cfg import FRET
from env.config import configured_kwargs
from env.tasks import FretTask


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--num-envs", type=int, default=8)
    ap.add_argument("--steps", type=int, default=120)
    ap.add_argument("--reset-noise", type=float, default=0.0)
    args = ap.parse_args(argv)
    env = FretTask(**configured_kwargs(
              FretTask, FRET,
              reward_config=FRET,
              goal_path=FRET["goal_path"],
              hand_targets_path=FRET["hand_targets_path"],
              num_envs=args.num_envs,
              device=FRET["device"],
              headless=True,
              reset_noise=args.reset_noise,
              random_start=False,
              finger_capsule_radius=FRET["finger_capsule_radius"],
              finger_overlap_tolerance=FRET["finger_overlap_tolerance"]
          ))
    action = ((env.init_pose[env.ctrl_idx] - env.ctrl_mid[0]) /
              (env.action_scale * env.ctrl_half[0]).clamp_min(1e-6)).clamp(-1.0, 1.0)
    action = action.repeat(env.num_envs, 1)
    env.reset()
    n_pairs = len(env.finger_intersection_monitor.pair_names)
    pair_max = torch.zeros(n_pairs, device=env.device)
    pair_frames = torch.zeros(n_pairs, device=env.device)
    max_streak = initial_overlap = 0
    for _ in range(args.steps):
        _, _, _, info = env.step(action)
        pair_max = torch.maximum(pair_max, info["finger_pair_penetration"].amax(dim=0))
        pair_frames += info["finger_pair_overlap"].sum(dim=0)
        max_streak = max(max_streak, int(info["finger_intersection_streak"].max().cpu()))
        initial_overlap += int(info["finger_initial_overlap"].sum().cpu())
    result = {
        "diagnostic_only": True,
        "capsule_radius_m": FRET["finger_capsule_radius"],
        "overlap_tolerance_m": FRET["finger_overlap_tolerance"],
        "num_envs": args.num_envs,
        "steps": args.steps,
        "max_streak": max_streak,
        "initial_overlap_count": initial_overlap,
        "pairs": {
            name: {"max_penetration_m": float(pair_max[i].cpu()),
                   "overlap_env_frames": int(pair_frames[i].cpu())}
            for i, name in enumerate(env.finger_intersection_monitor.pair_names)
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    env.close()


if __name__ == "__main__":
    main()
