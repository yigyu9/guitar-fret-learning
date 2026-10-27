"""Audit diagnostic-only pressed fingertip travel during MOVE transitions."""
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
from learning import ActorCritic


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", default=None)
    ap.add_argument("--num-envs", type=int, default=8)
    ap.add_argument("--steps", type=int, default=861)
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    env = FretTask(**configured_kwargs(
              FretTask, FRET,
              reward_config=FRET,
              goal_path=FRET["goal_path"],
              hand_targets_path=FRET["hand_targets_path"],
              num_envs=args.num_envs,
              device=FRET["device"],
              headless=True,
              reset_noise=0.0,
              random_start=False,
              pressed_drag_threshold=FRET["pressed_drag_threshold"]
          ))
    init_action = ((env.init_pose[env.ctrl_idx] - env.ctrl_mid[0]) /
                   (env.action_scale * env.ctrl_half[0]).clamp_min(1e-6)).clamp(-1.0, 1.0)
    model = None
    if args.checkpoint:
        model = ActorCritic(env.num_obs, env.num_actions, env.value_dim,
                            init_mean=init_action).to(env.device)
        checkpoint = torch.load(args.checkpoint, map_location=env.device)
        model.load_state_dict(checkpoint["model"])
        model.eval()

    obs = env.reset()
    finger_names = ("index", "middle", "ring", "pinky")
    started = torch.zeros(4, device=env.device)
    completed = torch.zeros(4, device=env.device)
    violations = torch.zeros(4, device=env.device)
    candidate_frames = torch.zeros(4, device=env.device)
    confirmed_frames = torch.zeros(4, device=env.device)
    candidate_distance = torch.zeros(4, device=env.device)
    confirmed_distance = torch.zeros(4, device=env.device)
    max_confirmed_move = torch.zeros(4, device=env.device)
    for _ in range(args.steps):
        action = (init_action.repeat(env.num_envs, 1) if model is None
                  else model.act(obs, deterministic=True)[0])
        obs, _, _, info = env.step(action)
        started += info["r28_move_started"].sum(dim=0)
        completed += info["r28_move_completed"].sum(dim=0)
        violations += info["r28_drag_violation_started"].sum(dim=0)
        candidate_frames += info["r28_pressed_endpoint_candidate"].sum(dim=0)
        confirmed_frames += info["r28_same_cell_drag"].sum(dim=0)
        candidate_distance += info["r28_candidate_step_distance"].sum(dim=0)
        confirmed_distance += info["r28_confirmed_step_distance"].sum(dim=0)
        max_confirmed_move = torch.maximum(
            max_confirmed_move,
            info["r28_confirmed_cumulative_distance"].amax(dim=0))

    result = {
        "diagnostic_only": True,
        "reward_or_termination_effect": False,
        "threshold_m": FRET["pressed_drag_threshold"],
        "discrete_frame_caveat": (
            "confirmed drag requires the same pressed string/fret cell at both "
            "control-frame endpoints; endpoint-only contact is a candidate channel"),
        "checkpoint": str(Path(args.checkpoint).resolve()) if args.checkpoint else None,
        "num_envs": args.num_envs,
        "steps": args.steps,
        "fingers": {
            name: {
                "move_started": int(started[i].cpu()),
                "move_completed": int(completed[i].cpu()),
                "violation_started": int(violations[i].cpu()),
                "candidate_env_frames": int(candidate_frames[i].cpu()),
                "confirmed_env_frames": int(confirmed_frames[i].cpu()),
                "candidate_distance_m": float(candidate_distance[i].cpu()),
                "confirmed_distance_m": float(confirmed_distance[i].cpu()),
                "max_confirmed_move_distance_m": float(max_confirmed_move[i].cpu()),
            }
            for i, name in enumerate(finger_names)
        },
    }
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered + "\n")
    print(rendered)
    env.close()


if __name__ == "__main__":
    main()
