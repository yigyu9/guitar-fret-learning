"""Record R24 anatomical contact-force and controlled-torque distributions."""
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


def distribution(values):
    values = torch.cat(values).float()
    q = torch.quantile(values, torch.tensor([0.50, 0.95, 0.99]))
    return {"mean": float(values.mean()), "p50": float(q[0]),
            "p95": float(q[1]), "p99": float(q[2]), "max": float(values.max())}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", default=None,
                    help="optional compatible policy; otherwise hold the initial pose")
    ap.add_argument("--num-envs", type=int, default=8)
    ap.add_argument("--steps", type=int, default=120)
    ap.add_argument("--reset-noise", type=float, default=0.0)
    ap.add_argument("--out", default=None, help="optional JSON report path")
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
              random_start=False
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
    channels = {
        "distal_force_n": [], "middle_force_n": [], "proximal_force_n": [],
        "support_force_n": [], "target_distal_force_n": [],
        "inactive_distal_force_n": [], "control_torque_nm": [],
        "control_torque_fraction": [], "mean_press_depth_m": [],
    }
    for _ in range(args.steps):
        if model is None:
            action = init_action.repeat(env.num_envs, 1)
        else:
            action, _, _ = model.act(obs, deterministic=True)
        obs, _, _, info = env.step(action)
        mapping = {
            "distal_force_n": info["r24_distal_contact_force"],
            "middle_force_n": info["r24_middle_contact_force"],
            "proximal_force_n": info["r24_proximal_contact_force"],
            "support_force_n": info["r24_support_contact_force"],
            "control_torque_nm": info["r24_control_torque"],
            "control_torque_fraction": info["r24_control_torque_fraction"],
            "mean_press_depth_m": info["mean_press_depth"],
        }
        for name, value in mapping.items():
            channels[name].append(value.detach().cpu().reshape(-1))
        active = info["r24_active_fretting_finger"]
        fretting_distal = info["r24_distal_contact_force"][:, 1:]
        channels["target_distal_force_n"].append(
            fretting_distal[active].detach().cpu().reshape(-1))
        channels["inactive_distal_force_n"].append(
            fretting_distal[~active].detach().cpu().reshape(-1))

    result = {
        "diagnostic_only": True,
        "net_force_caveat": "rigid-body net force does not identify the contact counterpart",
        "checkpoint": str(Path(args.checkpoint).resolve()) if args.checkpoint else None,
        "num_envs": args.num_envs,
        "steps": args.steps,
        "body_order": {
            "finger": list(env.contact_load_monitor.FINGERS),
            "support": list(env.contact_load_monitor.SUPPORT_BODIES),
            "control_dof": [env.dof_names[i] for i in env.ctrl_idx.cpu().tolist()],
        },
        "distributions": {name: distribution(values)
                          for name, values in channels.items()},
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
