"""Render the R13 palm vector against world up/down from four views."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import tempfile

import isaacgym  # noqa: F401
from isaacgym import gymapi
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cfg import FRET
from env.config import configured_kwargs
from env.tasks import FretTask
from tools.fretboard_visualization import (
    camera_for_palm_world_direction_view,
    draw_fretboard_overlay,
    draw_palm_world_direction_overlay,
    palm_world_direction_geometry,
)

VIEWS = (
    ("diagonal_front", "DIAGONAL FRONT", (1.0, -0.1, 1.0)),
    ("side", "SIDE (+X)", (1.0, 0.0, 0.0)),
    ("back", "NECK BACK (-Z)", (0.0, 0.0, -1.0)),
    ("nut_end", "NUT END (+Y)", (0.0, 1.0, 0.0)),
)


def parser():
    ap = argparse.ArgumentParser(description="render the R13 palm world vector")
    ap.add_argument("--goal", default=FRET["goal_path"])
    ap.add_argument("--hand-targets", default=FRET["hand_targets_path"])
    ap.add_argument("--out-dir", default=str(WORKSPACE / "fret" / "renders"))
    ap.add_argument("--device", default=FRET["device"])
    ap.add_argument("--width", type=int, default=1600)
    ap.add_argument("--height", type=int, default=900)
    ap.add_argument("--fov", type=float, default=55.0)
    return ap


def _add_title(path, title):
    image = Image.open(path).convert("RGBA")
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    font = ImageFont.load_default()
    width = draw.textbbox((0, 0), title, font=font)[2] + 30
    draw.rounded_rectangle((image.width - width - 16, 16, image.width - 16, 52),
                           radius=6, fill=(0, 0, 0, 210),
                           outline=(70, 235, 120, 255), width=2)
    draw.text((image.width - width + 1, 28), title, font=font, fill="white")
    Image.alpha_composite(image, layer).convert("RGB").save(path, quality=95)


def _contact_sheet(paths, out):
    sheet = Image.new("RGB", (1600, 900), (20, 22, 28))
    for index, path in enumerate(paths):
        image = Image.open(path).convert("RGB").resize((800, 450), Image.Resampling.LANCZOS)
        sheet.paste(image, ((index % 2) * 800, (index // 2) * 450))
    sheet.save(out, quality=95)


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
        out_dir = Path(args.out_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        cameras = []
        for _, _, direction in VIEWS:
            spec = camera_for_palm_world_direction_view(
                env, direction, args.width, args.height, args.fov)
            cp = gymapi.CameraProperties()
            cp.width, cp.height = args.width, args.height
            cp.horizontal_fov = args.fov
            camera = env.gym.create_camera_sensor(env.envs[0], cp)
            env.gym.set_camera_location(camera, env.envs[0],
                                        gymapi.Vec3(*spec.eye), gymapi.Vec3(*spec.target))
            cameras.append((camera, spec))
        env.gym.step_graphics(env.sim)
        env.gym.render_all_camera_sensors(env.sim)

        rendered = []
        with tempfile.TemporaryDirectory(prefix="palm_world_direction_") as tmp:
            for (slug, title, _), (camera, spec) in zip(VIEWS, cameras):
                raw = Path(tmp) / f"{slug}.png"
                out = out_dir / f"palm_world_direction_{slug}.png"
                env.gym.write_camera_image_to_file(
                    env.sim, env.envs[0], camera, gymapi.IMAGE_COLOR, str(raw))
                raw.replace(out)
                draw_fretboard_overlay(out, env, spec, max_fret=12, show_strings=True)
                draw_palm_world_direction_overlay(out, env, spec)
                _add_title(out, title)
                rendered.append(out)
                print(f"palm world direction: {out}")
        sheet = out_dir / "palm_world_direction_multiview.png"
        _contact_sheet(rendered, sheet)
        geometry = palm_world_direction_geometry(env)
        print(f"palm_world_z={geometry['world_z']:+.6f}")
        print(f"palm world contact sheet: {sheet}")
    finally:
        env.close()


if __name__ == "__main__":
    main()
