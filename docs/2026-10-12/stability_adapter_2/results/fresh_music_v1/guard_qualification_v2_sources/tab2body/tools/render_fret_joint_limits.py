"""Render every fret-controlled DOF at its lower, initial, and upper limit."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import re
import sys
import tempfile

import isaacgym  # noqa: F401
from isaacgym import gymapi, gymtorch
from PIL import Image, ImageDraw, ImageFont
import torch


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PACKAGE_ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tab2body.cfg import FRET
from tab2body.env.base import GuitarEnvBase
from tab2body.env.tasks.task_fret import FRET_CONTROL_PREFIXES


VIEWS = (
    ("front", (0.15, 0.85, 0.35)),
    ("side", (-0.80, 0.20, 0.30)),
)

GROUPS = (
    ("shoulder", "L_Shoulder"),
    ("elbow", "L_Elbow"),
    ("wrist", "L_Wrist"),
    ("thumb", "LH:thumb"),
    ("index", "LH:index"),
    ("middle", "LH:middle"),
    ("ring", "LH:ring"),
    ("pinky", "LH:pinky"),
)


def parser():
    ap = argparse.ArgumentParser(
        description="render the current 30-DOF fret control limits without the guitar")
    ap.add_argument(
        "--out-dir",
        default=str(PROJECT_ROOT / "docs" / "2026-09-01" / "fret_joint_limits"),
    )
    ap.add_argument("--device", default=FRET["device"])
    ap.add_argument("--panel-width", type=int, default=800)
    ap.add_argument("--panel-height", type=int, default=600)
    ap.add_argument("--fov", type=float, default=50.0)
    return ap


def _unit(values):
    length = math.sqrt(sum(value * value for value in values))
    if length <= 0.0:
        raise ValueError("camera direction must be non-zero")
    return tuple(value / length for value in values)


def _slug(name):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", name)


def _group_for(name):
    for group, prefix in GROUPS:
        if name.startswith(prefix):
            return group
    raise ValueError(f"unclassified fret-controlled DOF: {name}")


def _camera_spec(env, group):
    if group == "shoulder":
        bodies = ("L_Shoulder", "L_Elbow", "L_Wrist", "LH:palm")
        distance = 1.05
    elif group == "elbow":
        bodies = ("L_Elbow", "L_Wrist", "LH:palm")
        distance = 0.82
    elif group == "wrist":
        bodies = ("L_Wrist", "LH:palm")
        distance = 0.55
    else:
        bodies = ("LH:palm",)
        distance = 0.34
    points = torch.stack([env.hbody_pos(body)[0] for body in bodies])
    target = points.mean(dim=0).detach().cpu().tolist()
    return tuple(float(value) for value in target), distance


def _font(size):
    candidates = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    )
    for path in candidates:
        if Path(path).is_file():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def _annotate(path, title, subtitle):
    image = Image.open(path).convert("RGB")
    title_font = _font(24)
    subtitle_font = _font(19)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rectangle((0, 0, image.width, 74), fill=(12, 15, 22, 225))
    draw.text((18, 10), title, font=title_font, fill=(255, 255, 255, 255))
    draw.text((18, 42), subtitle, font=subtitle_font, fill=(195, 220, 255, 255))
    image.save(path)


def _make_sheet(
        panel_paths, dof_name, group, values_deg, observed_deg, output):
    states = ("LOWER LIMIT", "INITIAL POSE", "UPPER LIMIT")
    sample = Image.open(panel_paths[0][0]).convert("RGB")
    panel_width, panel_height = sample.size
    header_height = 86
    sheet = Image.new(
        "RGB", (panel_width * 3, header_height + panel_height * 2),
        (18, 21, 27))
    draw = ImageDraw.Draw(sheet)
    draw.text(
        (20, 12), f"{dof_name}  |  group={group}",
        font=_font(28), fill=(255, 255, 255))
    draw.text(
        (20, 49),
        (f"hard range {values_deg[0]:+.2f} deg to {values_deg[2]:+.2f} deg"
         f"  |  initial {values_deg[1]:+.2f} deg"),
        font=_font(21), fill=(190, 215, 255))
    for row, view in enumerate(VIEWS):
        for column, state in enumerate(states):
            image = Image.open(panel_paths[column][row]).convert("RGB")
            sheet.paste(image, (column * panel_width, header_height + row * panel_height))
            band_y = header_height + row * panel_height
            draw.rectangle(
                (column * panel_width, band_y,
                 (column + 1) * panel_width, band_y + 35),
                fill=(0, 0, 0))
            draw.text(
                (column * panel_width + 12, band_y + 6),
                (f"{state}: target {values_deg[column]:+.2f} deg, "
                 f"rendered {observed_deg[column]:+.2f} deg"
                 f"  |  {view[0].upper()} VIEW"),
                font=_font(18), fill=(255, 255, 255))
    sheet.save(output, quality=95)


def _make_group_overview(paths, group, output):
    thumb_width, thumb_height = 720, 430
    columns = 2
    rows = math.ceil(len(paths) / columns)
    header = 64
    sheet = Image.new(
        "RGB", (columns * thumb_width, header + rows * thumb_height),
        (18, 21, 27))
    draw = ImageDraw.Draw(sheet)
    draw.text(
        (18, 14), f"FRET JOINT LIMITS: {group.upper()}",
        font=_font(28), fill=(255, 255, 255))
    for index, path in enumerate(paths):
        image = Image.open(path).convert("RGB")
        image.thumbnail((thumb_width, thumb_height), Image.Resampling.LANCZOS)
        x = (index % columns) * thumb_width + (thumb_width - image.width) // 2
        y = header + (index // columns) * thumb_height + (thumb_height - image.height) // 2
        sheet.paste(image, (x, y))
    sheet.save(output, quality=93)


def _set_pose(env, pose):
    state = env.dof_state.view(1, env.n_dof, 2)
    state[0, :, 0] = pose
    state[0, :, 1] = 0.0
    env.pd_target.view(1, env.n_dof)[0] = pose
    env.gym.set_dof_state_tensor(env.sim, gymtorch.unwrap_tensor(env.dof_state))
    env.step_physics()
    env.refresh()


def _remove_guitar(env):
    env.gym.refresh_actor_root_state_tensor(env.sim)
    roots = env.root_state.view(1, -1, 13)
    if roots.shape[1] != 3:
        raise RuntimeError(
            f"expected humanoid, guitar, chair actors; found {roots.shape[1]}")
    roots[0, 1, :3] = torch.tensor((50.0, 50.0, 50.0), device=env.device)
    roots[0, 1, 7:] = 0.0
    env.gym.set_actor_root_state_tensor(
        env.sim, gymtorch.unwrap_tensor(env.root_state))


def main(argv=None):
    args = parser().parse_args(argv)
    if args.panel_width <= 0 or args.panel_height <= 0:
        raise ValueError("panel dimensions must be positive")
    out_dir = Path(args.out_dir).resolve()
    image_dir = out_dir / "individual"
    overview_dir = out_dir / "overview"
    image_dir.mkdir(parents=True, exist_ok=True)
    overview_dir.mkdir(parents=True, exist_ok=True)

    env = GuitarEnvBase(
        num_envs=1,
        control_dofs=FRET_CONTROL_PREFIXES,
        device=args.device,
        headless=True,
        seed=FRET["seed"],
        action_alpha=FRET["action_alpha"],
        action_scale=FRET["action_scale"],
        reset_noise=0.0,
        reset_soft_limit_fraction=FRET["reset_soft_limit_fraction"],
        obs_body_names=("L_Shoulder", "L_Elbow", "L_Wrist", "LH:palm"),
    )
    try:
        env.reset()
        _remove_guitar(env)
        base_pose = env.init_pose.clone()
        _set_pose(env, base_pose)
        controlled = [
            (int(index), env.dof_names[int(index)])
            for index in env.ctrl_idx.detach().cpu().tolist()
        ]
        if len(controlled) != 30:
            raise RuntimeError(
                f"expected 30 fret-controlled DOFs, found {len(controlled)}")

        camera_properties = gymapi.CameraProperties()
        camera_properties.width = args.panel_width
        camera_properties.height = args.panel_height
        camera_properties.horizontal_fov = args.fov
        camera = env.gym.create_camera_sensor(env.envs[0], camera_properties)

        rows = []
        group_images = {group: [] for group, _ in GROUPS}
        with tempfile.TemporaryDirectory(prefix="fret_joint_limits_") as temporary:
            temporary = Path(temporary)
            for order, (dof_index, dof_name) in enumerate(controlled, start=1):
                group = _group_for(dof_name)
                _set_pose(env, base_pose)
                target, distance = _camera_spec(env, group)
                lower = float(env.dof_lower[dof_index].detach().cpu())
                initial = float(base_pose[dof_index].detach().cpu())
                upper = float(env.dof_upper[dof_index].detach().cpu())
                values = (lower, initial, upper)
                values_deg = tuple(math.degrees(value) for value in values)
                observed = []
                panel_paths = []
                for state_index, (state_name, value) in enumerate(zip(
                        ("lower", "initial", "upper"), values)):
                    pose = base_pose.clone()
                    pose[dof_index] = value
                    _set_pose(env, pose)
                    rendered = float(
                        env.dof_state.view(1, env.n_dof, 2)[0, dof_index, 0]
                        .detach().cpu())
                    observed.append(rendered)
                    state_panels = []
                    for view_name, direction in VIEWS:
                        direction = _unit(direction)
                        eye = tuple(
                            target[axis] + distance * direction[axis]
                            for axis in range(3))
                        env.gym.set_camera_location(
                            camera, env.envs[0], gymapi.Vec3(*eye),
                            gymapi.Vec3(*target))
                        env.gym.step_graphics(env.sim)
                        env.gym.render_all_camera_sensors(env.sim)
                        panel = temporary / (
                            f"{order:02d}_{_slug(dof_name)}_{state_name}_{view_name}.png")
                        env.gym.write_camera_image_to_file(
                            env.sim, env.envs[0], camera,
                            gymapi.IMAGE_COLOR, str(panel))
                        _annotate(
                            panel, dof_name,
                            (f"{state_name.upper()} target {math.degrees(value):+.2f} deg"
                             f" | rendered {math.degrees(rendered):+.2f} deg"))
                        state_panels.append(panel)
                    panel_paths.append(state_panels)

                output = image_dir / f"{order:02d}_{_slug(dof_name)}.png"
                observed_deg = tuple(math.degrees(value) for value in observed)
                _make_sheet(
                    panel_paths, dof_name, group, values_deg, observed_deg, output)
                group_images[group].append(output)
                rows.append({
                    "order": order,
                    "group": group,
                    "dof": dof_name,
                    "lower_rad": lower,
                    "initial_rad": initial,
                    "upper_rad": upper,
                    "lower_deg": values_deg[0],
                    "initial_deg": values_deg[1],
                    "upper_deg": values_deg[2],
                    "span_deg": values_deg[2] - values_deg[0],
                    "rendered_lower_deg": math.degrees(observed[0]),
                    "rendered_initial_deg": math.degrees(observed[1]),
                    "rendered_upper_deg": math.degrees(observed[2]),
                    "max_render_error_deg": max(
                        abs(actual - target)
                        for actual, target in zip(observed_deg, values_deg)),
                    "image": str(output.relative_to(out_dir)),
                })
                print(f"[{order:02d}/30] {dof_name}: {output}", flush=True)

        overviews = {}
        for group, paths in group_images.items():
            output = overview_dir / f"{group}_joint_limits.png"
            _make_group_overview(paths, group, output)
            overviews[group] = str(output.relative_to(out_dir))

        csv_path = out_dir / "joint_limit_ranges.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

        report = {
            "schema": "tab2body.fret-joint-limit-render.v1",
            "controlled_dof_count": len(rows),
            "control_prefixes": list(FRET_CONTROL_PREFIXES),
            "base_pose": "assets/seated_pose.json with current hard clamp and 2% reset inset",
            "scene": "guitar moved outside the scene; humanoid remains seated on the chair",
            "action_scale": env.action_scale,
            "policy_target_range": (
                "full hard-limit range" if env.action_scale == 1.0
                else f"{env.action_scale:.3f} of each half range"),
            "render_method": (
                "one DOF changed at a time; every other DOF held at the authoritative "
                "fret initial pose; two fixed camera directions per DOF"),
            "rows": rows,
            "overviews": overviews,
        }
        json_path = out_dir / "joint_limit_ranges.json"
        json_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
        print(f"CSV: {csv_path}")
        print(f"JSON: {json_path}")
    finally:
        if getattr(env, "sim", None) is not None:
            env.gym.destroy_sim(env.sim)
            env.sim = None


if __name__ == "__main__":
    main()
