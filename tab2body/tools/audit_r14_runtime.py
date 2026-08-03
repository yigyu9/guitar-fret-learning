"""Short GPU runtime audit for collision filters and R14 penetration diagnostics."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import isaacgym  # noqa: F401 -- must precede torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cfg import FRET
from env.config import configured_kwargs
from env.tasks import FretTask


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--num-envs", type=int, default=8)
    ap.add_argument("--steps", type=int, default=12)
    ap.add_argument("--reset-noise", type=float, default=0.0)
    args = ap.parse_args(argv)
    env = FretTask(**configured_kwargs(
              FretTask, FRET,
              goal_path=FRET["goal_path"],
              hand_targets_path=FRET["hand_targets_path"],
              num_envs=args.num_envs,
              device=FRET["device"],
              headless=True,
              reset_noise=args.reset_noise,
              random_start=False,
              palm_down_threshold=FRET["palm_down_threshold"],
              palm_down_frames=FRET["palm_down_frames"],
              penetration_threshold=FRET["penetration_threshold"],
              penetration_frames=FRET["penetration_frames"],
              penetration_termination=FRET["penetration_termination"]
          ))
    action = ((env.init_pose[env.ctrl_idx] - env.ctrl_mid[0]) /
              (env.action_scale * env.ctrl_half[0]).clamp_min(1e-6)).clamp(-1.0, 1.0)
    action = action.repeat(env.num_envs, 1)
    env.reset()
    max_depth = max_swept = 0.0
    initial_overlap = tunneled = penetration_done = total_done = 0
    last_info = None
    for _ in range(args.steps):
        _, _, done, info = env.step(action)
        last_info = info
        max_depth = max(max_depth, float(info["guitar_penetration_depth"].max().cpu()))
        max_swept = max(max_swept, float(info["guitar_swept_penetration_depth"].max().cpu()))
        initial_overlap += int(info["guitar_initial_overlap"].sum().cpu())
        tunneled += int(info["guitar_tunneled"].sum().cpu())
        penetration_done += int(info["guitar_penetration_termination"].sum().cpu())
        total_done += int(done.sum().cpu())
    result = {
        "collision_audit": env.collision_audit,
        "penetration_termination_enabled": FRET["penetration_termination"],
        "threshold_m": FRET["penetration_threshold"],
        "frames": FRET["penetration_frames"],
        "reset_noise_rad": args.reset_noise,
        "max_current_depth_m": max_depth,
        "max_swept_depth_m": max_swept,
        "initial_overlap_count": initial_overlap,
        "tunneled_count": tunneled,
        "penetration_termination_count": penetration_done,
        "all_done_count": total_done,
        "last_palm_world_z_min": float(last_info["palm_world_z"].min().cpu()),
        "controlled_torque_caps": sorted(set(float(x) for x in
            env.tau_limit.view(env.num_envs, env.n_dof)[0, env.ctrl_idx].cpu().tolist())),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    env.close()


if __name__ == "__main__":
    main()
