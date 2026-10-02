"""CPU preview of the XPBD strap without Isaac Gym.

Places the body capsules and strap buttons at the seated pose by MJCF forward kinematics,
drapes the strap, then hangs the guitar from it as a translating point mass integrated at
SIM_HZ x SUBSTEPS with the same one-control-step force hold as GuitarEnvBase.

    python tools/strap_chain_preview.py [--seconds 3] [--png out.png]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env.strap_chain import (StrapChain, StrapChainParams, load_strap_config,
                             resolve_colliders)

ASSETS = ROOT / "assets"
SIM_HZ, SUBSTEPS = 60, 4


def _quat_matrix(w, x, y, z):
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def _axis_rotation(axis, angle):
    axis = np.asarray(axis, float) / np.linalg.norm(axis)
    k = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + math.sin(angle) * k + (1 - math.cos(angle)) * k @ k


def seated_body_frames():
    """World (position, rotation) of every humanoid body at the seated pose (hinge FK)."""
    pose = json.load(open(ASSETS / "seated_pose.json"))
    joints = pose["joints_isaac"]
    root = ET.parse(ASSETS / "smpl_mpl_hands_body.xml").getroot()
    frames = {}

    def walk(body, pos, rot):
        for joint in body.findall("joint"):
            if joint.get("type", "hinge") == "hinge":
                axis = [float(v) for v in joint.get("axis").split()]
                rot = rot @ _axis_rotation(axis, joints.get(joint.get("name"), 0.0))
        frames[body.get("name")] = (pos, rot)
        for child in body.findall("body"):
            child_rot = rot
            if child.get("quat"):
                child_rot = rot @ _quat_matrix(*[float(v) for v in child.get("quat").split()])
            walk(child, pos + rot @ np.array([float(v) for v in child.get("pos").split()]),
                 child_rot)

    rq = pose["root_qpos"]
    walk(root.find(".//body[@name='Pelvis']"), np.array(rq[:3]), _quat_matrix(*rq[3:]))
    guitar = (np.array(pose["params"]["guitar_pos_computed"]),
              _quat_matrix(*pose["params"]["guitar_quat_wxyz_computed"]))
    return frames, guitar


def seated_strap_geometry(config_path=ASSETS / "strap_chain.json"):
    """Return (cfg, params, radii, capsules [1,C,2,3], route [1,K,3], guitar (pos, rot))."""
    cfg = load_strap_config(config_path)
    frames, guitar = seated_body_frames()
    colliders = resolve_colliders(cfg, ASSETS / "smpl_mpl_hands_body.xml")
    capsules = []
    for body, start, end, _ in colliders:
        pos, rot = frames[body]
        capsules.append([pos + rot @ np.array(start), pos + rot @ np.array(end)])
    gpos, grot = guitar
    end_pin = gpos + grot @ np.array(cfg["guitar_anchors"]["end_pin"])
    heel = gpos + grot @ np.array(cfg["guitar_anchors"]["heel"])
    guides = [frames[p["body"]][0] + frames[p["body"]][1] @ np.array(p["local"])
              for p in cfg["route"]]
    route = np.array([end_pin, *guides, heel])
    return (cfg, StrapChainParams.from_dict(cfg.get("params", {})),
            [c[3] for c in colliders],
            torch.tensor(np.array(capsules), dtype=torch.float32)[None],
            torch.tensor(route, dtype=torch.float32)[None], guitar)


def hang_guitar(seconds=3.0, guitar_mass=4.5, params=None, drop=0.0, vertical_only=False):
    """Hang a translating guitar point mass from the strap. Returns a history dict.

    ``vertical_only`` stands in for the thigh/torso that stop a seated guitar from
    swinging sideways; without it the guitar swings under the shoulder like a pendulum."""
    cfg, base_params, radii, capsules, route, (gpos, grot) = seated_strap_geometry()
    params = params or base_params
    chain = StrapChain(1, radii, params)
    dt = 1.0 / SIM_HZ
    chain.initialize([0], route, capsules, dt)
    local = torch.tensor([cfg["guitar_anchors"]["end_pin"], cfg["guitar_anchors"]["heel"]],
                         dtype=torch.float32)
    rot = torch.tensor(grot, dtype=torch.float32)
    origin = torch.tensor(gpos, dtype=torch.float32) + torch.tensor([0.0, 0.0, -drop])
    velocity = torch.zeros(3)
    gravity = torch.tensor(params.gravity, dtype=torch.float32)
    anchors = (origin + local @ rot.T)[None]
    hist = {"t": [], "z": [], "lift": [], "tension": [], "body_down": [], "pen": []}
    for step in range(int(seconds * SIM_HZ)):
        force = chain.anchor_force[0].sum(0)                     # held for the whole step (ZOH)
        h = dt / SUBSTEPS
        for _ in range(SUBSTEPS):
            accel = gravity + force / guitar_mass
            if vertical_only:
                accel = accel * torch.tensor([0.0, 0.0, 1.0])
            velocity = velocity + accel * h
            origin = origin + velocity * h
        prev, anchors = anchors, (origin + local @ rot.T)[None]
        chain.step(dt, prev, anchors, capsules, capsules)
        pen = chain.penetration(chain.x, capsules)
        hist["t"].append((step + 1) * dt)
        hist["z"].append(float(origin[2]))
        hist["lift"].append(float(chain.anchor_force[0, :, 2].sum()))
        hist["tension"].append(float(chain.tension[0].max()))
        hist["body_down"].append(float(-chain.body_force[0, :, 2].sum()))
        hist["pen"].append(float(pen.max()))
    hist["x"] = chain.x[0].numpy()
    hist["capsules"] = capsules[0].numpy()
    hist["radii"] = radii
    hist["anchors"] = anchors[0].numpy()
    hist["z0"] = float(gpos[2])
    hist["contact_fraction"] = float(chain.contact.float().mean())
    hist["nonfinite"] = bool(chain.nonfinite.any())
    return hist


def _plot(hist, path, mass):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(13, 4.5))
    views = [("front (x-z)", 0, 2), ("side (y-z)", 1, 2)]
    for k, (title, a, b) in enumerate(views):
        ax = fig.add_subplot(1, 3, k + 1)
        for (p, q), r in zip(hist["capsules"], hist["radii"]):
            ax.plot([p[a], q[a]], [p[b], q[b]], color="0.75", lw=r * 600, solid_capstyle="round")
        ax.plot(hist["x"][:, a], hist["x"][:, b], "-o", color="tab:orange", ms=3, lw=2)
        ax.plot(hist["anchors"][:, a], hist["anchors"][:, b], "s", color="tab:blue", ms=7)
        ax.set_title(title); ax.set_aspect("equal"); ax.grid(alpha=0.3)
    ax = fig.add_subplot(1, 3, 3)
    ax.plot(hist["t"], hist["lift"], label="strap lift on guitar (N)")
    ax.plot(hist["t"], hist["body_down"], label="strap load on body (N)")
    ax.axhline(mass * 9.81, color="0.5", ls="--", label="guitar weight")
    ax.set_xlabel("s"); ax.legend(fontsize=8); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(path, dpi=110)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=float, default=3.0)
    parser.add_argument("--mass", type=float, default=4.5)
    parser.add_argument("--png", default=None)
    parser.add_argument("--free", action="store_true",
                        help="let the guitar swing freely (pendulum) instead of vertical-only")
    args = parser.parse_args()
    hist = hang_guitar(args.seconds, args.mass, vertical_only=not args.free)
    tail = slice(-SIM_HZ // 2, None)
    summary = {
        "guitar_sag_m": hist["z0"] - hist["z"][-1],
        "final_lift_N": float(np.mean(hist["lift"][tail])),
        "guitar_weight_N": args.mass * 9.81,
        "final_body_load_N": float(np.mean(hist["body_down"][tail])),
        "max_tension_N": float(np.max(hist["tension"])),
        "final_z_jitter_mm": 1000 * float(np.ptp(hist["z"][tail])),
        "max_penetration_mm": 1000 * max(hist["pen"]),
        "final_penetration_mm": 1000 * float(np.mean(hist["pen"][tail])),
        "contact_fraction": hist["contact_fraction"],
        "nonfinite": hist["nonfinite"],
    }
    print(json.dumps(summary, indent=2))
    if args.png:
        _plot(hist, args.png, args.mass)
        print("wrote", args.png)


if __name__ == "__main__":
    main()
