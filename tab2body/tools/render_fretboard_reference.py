"""Render one annotated fretboard reference image from the actual training scene.

Example (conda environment ``guitar``):
  python tools/render_fretboard_reference.py \
    --out ../fret/renders/fretboard_reference.png --max-fret 12
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import tempfile

import isaacgym  # noqa: F401  (must be imported before torch)
from isaacgym import gymapi

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cfg import FRET
from env.config import configured_kwargs
from env.tasks import FretTask
from tools.fretboard_visualization import (
    camera_for_wrist_safety_box,
    camera_from_guitar,
    draw_fretboard_overlay,
    draw_wrist_safety_box_overlay,
)


def parser():
    ap = argparse.ArgumentParser(description="render exact fret positions and press ranges")
    ap.add_argument("--goal", default=FRET["goal_path"])
    ap.add_argument("--hand-targets", default=FRET["hand_targets_path"])
    ap.add_argument("--out", default=str(WORKSPACE / "fret" / "renders" /
                                         "fretboard_reference.png"))
    ap.add_argument("--device", default=FRET["device"])
    ap.add_argument("--width", type=int, default=1600)
    ap.add_argument("--height", type=int, default=900)
    ap.add_argument("--fov", type=float, default=55.0)
    ap.add_argument("--max-fret", type=int, default=12)
    ap.add_argument("--show-strings", action="store_true",
                    help="overlay and label live G:string1..6 centerlines")
    ap.add_argument("--show-wrist-safety-box", action="store_true",
                    help="overlay the proposed fixed guitar-local wrist safety envelope")
    return ap


def main(argv=None):
    args = parser().parse_args(argv)
    env = FretTask(**configured_kwargs(
              FretTask, FRET,
              reward_config=FRET,
              goal_path=args.goal,
              hand_targets_path=args.hand_targets or None,
              num_envs=1,
              device=args.device,
              headless=True,
              seed=FRET["seed"],
              reset_noise=0.0,
              random_start=False,
              wrist_weight=FRET["wrist_weight"],
              smooth_weight=FRET["smooth_weight"],
              proximal_weight=FRET["proximal_weight"],
              proximal_transition=FRET["proximal_transition"],
              wrist_safety_bounds_min=FRET["wrist_safety_bounds_min"],
              wrist_safety_bounds_max=FRET["wrist_safety_bounds_max"]
          ))
    try:
        env.reset()
        spec = (camera_for_wrist_safety_box(env, args.width, args.height, args.fov)
                if args.show_wrist_safety_box else
                camera_from_guitar(env, args.width, args.height, args.fov))
        cp = gymapi.CameraProperties()
        cp.width, cp.height = args.width, args.height
        cp.horizontal_fov = args.fov
        camera = env.gym.create_camera_sensor(env.envs[0], cp)
        env.gym.set_camera_location(camera, env.envs[0],
                                    gymapi.Vec3(*spec.eye), gymapi.Vec3(*spec.target))
        env.gym.step_graphics(env.sim)
        env.gym.render_all_camera_sensors(env.sim)

        out = Path(args.out).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="fretboard_reference_") as tmp:
            raw = Path(tmp) / "raw.png"
            env.gym.write_camera_image_to_file(
                env.sim, env.envs[0], camera, gymapi.IMAGE_COLOR, str(raw))
            raw.replace(out)
        draw_fretboard_overlay(out, env, spec, max_fret=args.max_fret,
                               show_strings=args.show_strings)
        if args.show_wrist_safety_box:
            draw_wrist_safety_box_overlay(out, env, spec)
        print(f"fretboard reference: {out}")
    finally:
        env.close()


if __name__ == "__main__":
    main()
