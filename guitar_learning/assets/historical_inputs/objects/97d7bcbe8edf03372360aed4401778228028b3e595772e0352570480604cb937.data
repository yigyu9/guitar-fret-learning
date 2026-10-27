"""Render the legacy-guitar pick-grip reference on the current Isaac Gym body.

The seated full-body pose is left unchanged.  Only the 21 ``RH:*`` finger
joint coordinates are replaced with the scale-motion frame 2227 targets
documented in ``docs/2026-07-29/pick_grip_pose_from_guitar_research.txt``.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

import isaacgym  # noqa: F401  (Isaac Gym must be imported before torch)
from isaacgym import gymapi
import torch


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PACKAGE_ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tab2body.env.base import GuitarEnvBase


REFERENCE_SOURCE = "related_work/guitar/assets/motions/scale.json"
REFERENCE_FRAME = 2227
REFERENCE_TIME_S = 18.558333

# Axis-coordinate targets derived from the local quaternions of scale frame
# 2227.  These are the values documented for the current 21-DOF MJCF hand.
PICK_GRIP_TARGETS_RAD = {
    "RH:thumb1_x": 0.127301,
    "RH:thumb1_y": 0.315130,
    "RH:thumb1_z": -0.760646,
    "RH:thumb2": -0.640054,
    "RH:thumb3": -0.352066,
    "RH:index1_x": 0.643775,
    "RH:index1_z": 0.028566,
    "RH:index2": 1.445906,
    "RH:index3": 1.359653,
    "RH:middle1_x": -0.099999,
    "RH:middle1_z": 0.036538,
    "RH:middle2": 1.227628,
    "RH:middle3": 1.020861,
    "RH:ring1_x": -0.025703,
    "RH:ring1_z": -0.013535,
    "RH:ring2": 1.035659,
    "RH:ring3": 0.837959,
    "RH:pinky1_x": 0.041113,
    "RH:pinky1_z": -0.086802,
    "RH:pinky2": 0.823321,
    "RH:pinky3": 0.663379,
}

# Frozen strike views from PROJECT_CONTEXT.md.  Each vector points from the
# shared target toward the camera; both are normalized to the same distance.
CAMERA_DIRECTIONS = {
    "remembered": (0.15, 0.85, 0.62),
    "current": (-0.7474, 0.4317, 0.62),
}


def parser():
    ap = argparse.ArgumentParser(
        description="render the selected pick-grip pose in the current Isaac Gym scene")
    ap.add_argument(
        "--out-dir",
        default=str(PROJECT_ROOT / "docs" / "2026-07-29"),
    )
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--width", type=int, default=1600)
    ap.add_argument("--height", type=int, default=900)
    ap.add_argument("--fov", type=float, default=42.0)
    ap.add_argument("--distance", type=float, default=0.7)
    return ap


def _unit(values):
    norm = math.sqrt(sum(value * value for value in values))
    if norm <= 0.0:
        raise ValueError("camera direction must be non-zero")
    return tuple(value / norm for value in values)


def main(argv=None):
    args = parser().parse_args(argv)
    if args.width <= 0 or args.height <= 0:
        raise ValueError("image dimensions must be positive")
    if args.distance <= 0.0:
        raise ValueError("camera distance must be positive")

    env = GuitarEnvBase(
        num_envs=1,
        control_dofs=("RH:",),
        device=args.device,
        headless=True,
        seed=0,
        reset_noise=0.0,
        reset_soft_limit_fraction=0.0,
        obs_body_names=("R_Wrist", "RH:palm"),
    )
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        dof_index = {name: index for index, name in enumerate(env.dof_names)}
        actual_rh_names = {name for name in env.dof_names if name.startswith("RH:")}
        expected_rh_names = set(PICK_GRIP_TARGETS_RAD)
        if actual_rh_names != expected_rh_names:
            missing = sorted(actual_rh_names - expected_rh_names)
            extra = sorted(expected_rh_names - actual_rh_names)
            raise RuntimeError(
                f"right-hand target mismatch; missing targets={missing}, "
                f"unknown targets={extra}")

        base_pose = env.init_pose.clone()
        for name, value in PICK_GRIP_TARGETS_RAD.items():
            env.init_pose[dof_index[name]] = value

        # Fail rather than silently clipping a research target.
        lower = env.dof_lower[:env.n_dof]
        upper = env.dof_upper[:env.n_dof]
        if torch.any(env.init_pose < lower) or torch.any(env.init_pose > upper):
            bad = [
                name for name in PICK_GRIP_TARGETS_RAD
                if not (float(lower[dof_index[name]].cpu())
                        <= PICK_GRIP_TARGETS_RAD[name]
                        <= float(upper[dof_index[name]].cpu()))
            ]
            raise RuntimeError(f"pick-grip targets outside Isaac limits: {bad}")

        env.pd_target.copy_(env.init_pose)
        env.reset()
        env.refresh()

        target_tensor = env.hbody_pos("RH:palm")[0].detach().cpu()
        target = tuple(float(value) for value in target_tensor)
        camera_properties = gymapi.CameraProperties()
        camera_properties.width = args.width
        camera_properties.height = args.height
        camera_properties.horizontal_fov = args.fov
        cameras = {}
        camera_specs = {}
        for name, direction in CAMERA_DIRECTIONS.items():
            direction = _unit(direction)
            eye = tuple(
                target[axis] + args.distance * direction[axis]
                for axis in range(3)
            )
            camera = env.gym.create_camera_sensor(env.envs[0], camera_properties)
            env.gym.set_camera_location(
                camera,
                env.envs[0],
                gymapi.Vec3(*eye),
                gymapi.Vec3(*target),
            )
            cameras[name] = camera
            camera_specs[name] = {
                "eye_world_m": list(eye),
                "target_world_m": list(target),
                "direction_target_to_camera": list(direction),
                "distance_m": args.distance,
                "horizontal_fov_deg": args.fov,
                "width": args.width,
                "height": args.height,
            }

        env.gym.step_graphics(env.sim)
        env.gym.render_all_camera_sensors(env.sim)
        outputs = {}
        for name, camera in cameras.items():
            path = out_dir / f"pick_grip_pose_isaac_gym_{name}.png"
            env.gym.write_camera_image_to_file(
                env.sim,
                env.envs[0],
                camera,
                gymapi.IMAGE_COLOR,
                str(path),
            )
            outputs[name] = str(path)

        env.gym.refresh_dof_state_tensor(env.sim)
        rendered_q = env.dof_state.view(1, env.n_dof, 2)[0, :, 0]
        non_right = torch.tensor(
            [index for index, name in enumerate(env.dof_names)
             if not name.startswith("RH:")],
            device=env.device,
            dtype=torch.long,
        )
        right = torch.tensor(
            [dof_index[name] for name in sorted(PICK_GRIP_TARGETS_RAD)],
            device=env.device,
            dtype=torch.long,
        )
        report = {
            "schema": "tab2body.pick-grip-render.v1",
            "renderer": "Isaac Gym camera sensor",
            "reference": {
                "source": REFERENCE_SOURCE,
                "frame": REFERENCE_FRAME,
                "time_s": REFERENCE_TIME_S,
            },
            "pose_contract": {
                "base": "tab2body/assets/seated_pose.json joints_isaac",
                "changed_dofs": sorted(PICK_GRIP_TARGETS_RAD),
                "changed_dof_count": len(PICK_GRIP_TARGETS_RAD),
                "unchanged_dof_count": int(non_right.numel()),
                "targets_rad": {
                    name: PICK_GRIP_TARGETS_RAD[name]
                    for name in sorted(PICK_GRIP_TARGETS_RAD)
                },
            },
            "post_step_error": {
                "right_hand_max_abs_rad": float(
                    (rendered_q[right] - env.init_pose[right]).abs().max().cpu()),
                "non_right_max_abs_from_base_rad": float(
                    (rendered_q[non_right] - base_pose[non_right]).abs().max().cpu()),
            },
            "cameras": camera_specs,
            "images": outputs,
        }
        report_path = out_dir / "pick_grip_pose_isaac_gym.json"
        report_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(report, indent=2, ensure_ascii=False))
        print(f"report: {report_path}")
    finally:
        if getattr(env, "sim", None) is not None:
            env.gym.destroy_sim(env.sim)
            env.sim = None


if __name__ == "__main__":
    main()
