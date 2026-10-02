"""Isaac Gym check of the XPBD strap: free guitar hanging on the strap at the seated pose.

The body is held at the seated pose (no policy, no actions); the guitar is free with
gravity and hangs on the strap while resting on the thighs/hands by contact.  Writes a
metrics JSON, front/side stills and (if ffmpeg exists) an MP4 with the strap drawn as an
orange polyline on top of the Isaac camera image.

Isaac Gym must be imported before torch.  Run from the repository root:
  python -m tab2body.tools.strap_chain_isaac_check                      # 1 env, video
  python -m tab2body.tools.strap_chain_isaac_check --num-envs 4096 --no-video --seconds 2
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import time

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PACKAGE_ROOT.parent
LOCAL_ISAACGYM_PYTHON = PROJECT_ROOT / "isaacgym" / "python"
if (LOCAL_ISAACGYM_PYTHON / "isaacgym" / "__init__.py").is_file():
    sys.path.insert(0, str(LOCAL_ISAACGYM_PYTHON))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import isaacgym  # noqa: F401
from isaacgym import gymapi
import torch
from PIL import Image, ImageDraw

from tab2body.env.base import GuitarEnvBase
from tab2body.tools.fretboard_visualization import CameraSpec, _project

DEFAULT_CONFIG = PACKAGE_ROOT / "assets" / "strap_chain.json"
DEFAULT_OUT = PACKAGE_ROOT / "_gen" / "diagnostics" / "strap_chain_check"


def parser():
    ap = argparse.ArgumentParser(description="hang the free guitar on the XPBD strap in Isaac")
    ap.add_argument("--config", default=str(DEFAULT_CONFIG))
    ap.add_argument("--seconds", type=float, default=4.0)
    ap.add_argument("--num-envs", type=int, default=1)
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--no-video", action="store_true")
    ap.add_argument("--fps", type=int, default=30, choices=(30, 60))
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    ap.add_argument("--no-strap", action="store_true",
                    help="free guitar without the strap (control run: it should fall)")
    return ap


def body_cameras(env, width, height, fov=55.0):
    """Front (audience side) and left-side cameras aimed at the chest/guitar region."""
    chest = env.hbody_pos("Chest")[0].detach().cpu()
    guitar, _ = env.guitar_frame()
    target = 0.5 * (chest + guitar[0].detach().cpu())
    pelvis = env.hbody_pos("Pelvis")[0].detach().cpu()
    forward = target - pelvis
    forward[2] = 0.0
    forward = forward / forward.norm().clamp_min(1e-8)          # player's facing direction
    left = torch.tensor([-forward[1], forward[0], 0.0])
    up = torch.tensor([0.0, 0.0, 0.25])
    views = {"front": target + 1.4 * forward + up, "side": target + 1.4 * left + up}
    return {name: CameraSpec(tuple(float(v) for v in eye), tuple(float(v) for v in target),
                             width, height, fov)
            for name, eye in views.items()}


def draw_strap(path, points, spec):
    image = Image.open(path).convert("RGB")
    pixels, depth = _project(points, spec)
    draw = ImageDraw.Draw(image)
    visible = [tuple(map(float, p)) for p, z in zip(pixels, depth) if z > 0]
    if len(visible) >= 2:
        draw.line(visible, fill=(255, 140, 0), width=5)
    for p in (visible[0], visible[-1]) if visible else ():
        draw.rectangle([p[0] - 6, p[1] - 6, p[0] + 6, p[1] + 6], fill=(40, 90, 255))
    image.save(path)


def main(argv=None):
    args = parser().parse_args(argv)
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    env = GuitarEnvBase(
        num_envs=args.num_envs, control_dofs=[], device=args.device, headless=True,
        max_episode_length=10 ** 9, guitar_fixed=False,
        strap_chain_config=None if args.no_strap else args.config)
    strap = env.strap_chain
    env.reset()
    guitar0 = env.guitar_root_state()[:, :7].clone()

    cameras, frames = {}, {}
    if not args.no_video:
        props = gymapi.CameraProperties()
        props.width, props.height, props.horizontal_fov = args.width, args.height, 55.0
        for name, spec in body_cameras(env, args.width, args.height).items():
            handle = env.gym.create_camera_sensor(env.envs[0], props)
            env.gym.set_camera_location(handle, env.envs[0], gymapi.Vec3(*spec.eye),
                                        gymapi.Vec3(*spec.target))
            cameras[name] = (handle, spec)
            frames[name] = out / f"frames_{name}"
            shutil.rmtree(frames[name], ignore_errors=True)
            frames[name].mkdir()

    steps = int(round(args.seconds * env.SIM_HZ))
    stride = env.SIM_HZ // args.fps
    history = {"t": [], "drop_m": [], "tilt_deg": [], "end_pin_N": [], "heel_N": [],
               "max_tension_N": [], "penetration_mm": [], "contact_fraction": []}
    nonfinite = torch.zeros(env.num_envs, dtype=torch.bool, device=env.device)
    step_ms, written = [], 0
    for step in range(steps):
        torch.cuda.synchronize()
        tic = time.perf_counter()
        env.step_physics()
        env.refresh()
        torch.cuda.synchronize()
        step_ms.append(1000.0 * (time.perf_counter() - tic))

        root = env.guitar_root_state()
        drop = guitar0[:, 2] - root[:, 2]
        dot = (root[:, 3:7] * guitar0[:, 3:7]).sum(-1).abs().clamp(max=1.0)
        tilt = torch.rad2deg(2.0 * torch.acos(dot))
        nonfinite |= ~torch.isfinite(root).all(-1)
        history["t"].append((step + 1) / env.SIM_HZ)
        history["drop_m"].append(float(drop.max()))
        history["tilt_deg"].append(float(tilt.max()))
        if strap is not None:
            summary = strap.tension_summary()
            pen = strap.chain.penetration(strap.chain.x, strap.capsules_world())
            nonfinite |= strap.chain.nonfinite
            history["end_pin_N"].append(float(summary["end_pin_force"].max()))
            history["heel_N"].append(float(summary["heel_force"].max()))
            history["max_tension_N"].append(float(summary["max_tension"].max()))
            history["penetration_mm"].append(1000.0 * float(pen.max()))
            history["contact_fraction"].append(float(summary["contact_fraction"].mean()))

        if cameras and step % stride == 0:
            env.gym.step_graphics(env.sim)
            env.gym.render_all_camera_sensors(env.sim)
            for name, (handle, spec) in cameras.items():
                path = frames[name] / f"{written:05d}.png"
                env.gym.write_camera_image_to_file(env.sim, env.envs[0], handle,
                                                   gymapi.IMAGE_COLOR, str(path))
                if strap is not None:
                    draw_strap(path, strap.chain.x[0].detach().cpu().numpy(), spec)
            written += 1

    tail = slice(-env.SIM_HZ // 2, None)

    def tail_max(key):
        values = history[key][tail]
        return max(values) if values else None

    report = {
        "config": None if args.no_strap else str(Path(args.config).resolve()),
        "num_envs": env.num_envs, "seconds": args.seconds,
        "nonfinite_envs": int(nonfinite.sum()),
        "final_guitar_drop_m": history["drop_m"][-1],
        "final_guitar_tilt_deg": history["tilt_deg"][-1],
        "tail_drop_range_mm": 1000.0 * (max(history["drop_m"][tail]) - min(history["drop_m"][tail])),
        "tail_end_pin_N": tail_max("end_pin_N"), "tail_heel_N": tail_max("heel_N"),
        "max_tension_N": max(history["max_tension_N"]) if history["max_tension_N"] else None,
        "max_penetration_mm": max(history["penetration_mm"]) if history["penetration_mm"] else None,
        "step_ms_median": sorted(step_ms)[len(step_ms) // 2],
        "history": history,
    }
    checks = {
        "no_nonfinite": report["nonfinite_envs"] == 0,
        "guitar_held_within_5cm": report["final_guitar_drop_m"] < 0.05,
        "settled_within_2mm": report["tail_drop_range_mm"] < 2.0,
    }
    if strap is not None:
        checks["strap_penetration_below_5mm"] = report["max_penetration_mm"] < 5.0
        checks["strap_carries_load"] = (report["tail_end_pin_N"] or 0) + (report["tail_heel_N"] or 0) > 5.0
    report["checks"] = checks
    (out / "report.json").write_text(json.dumps(report, indent=2))

    if cameras:
        for name in cameras:
            last = frames[name] / f"{written - 1:05d}.png"
            shutil.copy(last, out / f"final_{name}.png")
            if shutil.which("ffmpeg"):
                subprocess.run(["ffmpeg", "-y", "-framerate", str(args.fps),
                                "-i", str(frames[name] / "%05d.png"), "-c:v", "libx264",
                                "-pix_fmt", "yuv420p", str(out / f"strap_{name}.mp4")],
                               check=True, capture_output=True)

    brief = {k: v for k, v in report.items() if k != "history"}
    print(json.dumps(brief, indent=2))
    print("outputs:", out)
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
