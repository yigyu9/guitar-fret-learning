"""Build a conservative fret joint soft-range profile from guitar motion."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PACKAGE_ROOT.parent
ASSETS = PACKAGE_ROOT / "assets"
FINGERS = ("index", "middle", "ring", "pinky")

ARM_SOFT_RANGES_DEG = {
    "L_Elbow_x": (-110.0, 60.0),
    "L_Elbow_y": (-150.0, 0.0),
    "L_Elbow_z": (-60.0, 60.0),
    "L_Wrist_x": (-90.0, 60.0),
    "L_Wrist_y": (-40.0, 40.0),
    "L_Wrist_z": (-45.0, 45.0),
}


def _axis_angle(quaternion, axis):
    return 2.0 * math.atan2(float(quaternion[axis]), float(quaternion[3]))


def _rotation_vector(quaternion):
    x, y, z, w = (float(value) for value in quaternion)
    norm = math.sqrt(x * x + y * y + z * z)
    if norm < 1e-9:
        return 0.0, 0.0, 0.0
    angle = 2.0 * math.atan2(norm, w)
    return angle * x / norm, angle * y / norm, angle * z / norm


def _hard_limits():
    root = ET.parse(ASSETS / "smpl_mpl_hands_body.xml").getroot()
    limits = {}
    for joint in root.iter("joint"):
        name = joint.attrib.get("name")
        values = joint.attrib.get("range")
        if name and values:
            lower, upper = (float(value) for value in values.split())
            limits[name] = (lower, upper)
    return limits


def _samples(frames):
    values = {}
    for frame in frames:
        thumb1 = _rotation_vector(frame["LH:thumb1"])
        row = {
            "LH:thumb1_x": thumb1[0],
            "LH:thumb1_y": thumb1[1],
            "LH:thumb1_z": thumb1[2],
            "LH:thumb2": _axis_angle(frame["LH:thumb2"], 2),
            "LH:thumb3": _axis_angle(frame["LH:thumb3"], 2),
        }
        for finger in FINGERS:
            row.update({
                f"LH:{finger}1_x": _axis_angle(frame[f"LH:{finger}1"], 0),
                f"LH:{finger}1_z": _axis_angle(frame[f"LH:{finger}1"], 2),
                f"LH:{finger}2": _axis_angle(frame[f"LH:{finger}2"], 0),
                f"LH:{finger}3": _axis_angle(frame[f"LH:{finger}3"], 0),
            })
        for name, value in row.items():
            values.setdefault(name, []).append(math.degrees(value))
    return {name: np.asarray(series, dtype=np.float64)
            for name, series in values.items()}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "motion", type=Path,
        default=PROJECT_ROOT / "related_work/guitar/assets/motions/scale.json",
        nargs="?")
    parser.add_argument(
        "--out", type=Path,
        default=ASSETS / "fret_human_joint_profile.json")
    parser.add_argument("--plot", type=Path, default=None)
    parser.add_argument("--quantile", type=float, default=0.01)
    parser.add_argument("--margin-deg", type=float, default=10.0)
    args = parser.parse_args(argv)
    if not 0.0 <= args.quantile < 0.5:
        raise ValueError("quantile must be in [0, 0.5)")
    if args.margin_deg < 0.0:
        raise ValueError("margin must be non-negative")

    motion_path = args.motion.resolve()
    motion = json.loads(motion_path.read_text(encoding="utf-8"))
    frames = motion.get("frames")
    if not isinstance(frames, list) or not frames:
        raise ValueError("motion must contain non-empty frames")
    samples = _samples(frames)
    hard = _hard_limits()
    initial = json.loads(
        (ASSETS / "seated_pose.json").read_text(encoding="utf-8"))["joints_isaac"]

    joints = {}
    for name, series in samples.items():
        hard_lower, hard_upper = hard[name]
        p_lower, median, p_upper = np.quantile(
            series, (args.quantile, 0.5, 1.0 - args.quantile))
        initial_deg = math.degrees(float(initial[name]))
        lower = max(
            hard_lower,
            min(float(p_lower) - args.margin_deg,
                initial_deg - 0.5 * args.margin_deg))
        upper = min(
            hard_upper,
            max(float(p_upper) + args.margin_deg,
                initial_deg + 0.5 * args.margin_deg))
        if lower >= upper:
            raise ValueError(f"invalid generated range for {name}: {lower}, {upper}")
        joints[name] = {
            "lower_deg": lower,
            "upper_deg": upper,
            "hard_lower_deg": hard_lower,
            "hard_upper_deg": hard_upper,
            "initial_deg": initial_deg,
            "p01_deg": float(p_lower),
            "median_deg": float(median),
            "p99_deg": float(p_upper),
            "source": "professional_guitarist_scale_motion",
        }

    for name, (lower, upper) in ARM_SOFT_RANGES_DEG.items():
        hard_lower, hard_upper = hard[name]
        initial_deg = math.degrees(float(initial[name]))
        if not hard_lower <= lower < initial_deg < upper <= hard_upper:
            raise ValueError(f"manual arm range does not contain initial pose: {name}")
        joints[name] = {
            "lower_deg": lower,
            "upper_deg": upper,
            "hard_lower_deg": hard_lower,
            "hard_upper_deg": hard_upper,
            "initial_deg": initial_deg,
            "source": "kinematic_safety_after_limit_render",
        }

    profile = {
        "schema": "tab2body.fret-human-joint-profile.v1",
        "motion_source": str(motion_path),
        "motion_frames": len(frames),
        "motion_fps": motion.get("fps"),
        "method": {
            "hand": (
                "reference p01-p99 plus 10 degree margin, expanded to contain "
                "the current initial pose, clamped to XML hard limits"),
            "arm": (
                "conservative elbow/wrist soft ranges selected after isolated "
                "limit rendering; no shoulder/thorax restriction without data"),
            "role": "soft reward range and optional runtime simulator hard limit",
        },
        "joints": dict(sorted(joints.items())),
    }
    output = args.out.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(profile, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")

    plot = (args.plot.resolve() if args.plot else output.with_suffix(".png"))
    names = list(profile["joints"])
    y = np.arange(len(names))
    hard_lower = np.array([joints[name]["hard_lower_deg"] for name in names])
    hard_upper = np.array([joints[name]["hard_upper_deg"] for name in names])
    soft_lower = np.array([joints[name]["lower_deg"] for name in names])
    soft_upper = np.array([joints[name]["upper_deg"] for name in names])
    initial_values = np.array([joints[name]["initial_deg"] for name in names])
    fig, axis = plt.subplots(figsize=(12, 12), dpi=160)
    axis.hlines(y, hard_lower, hard_upper, color="#c7ccd6", linewidth=6,
                label="XML hard range")
    axis.hlines(y, soft_lower, soft_upper, color="#2d7dd2", linewidth=4,
                label="proposed soft range")
    axis.scatter(initial_values, y, color="#f26419", s=18, label="initial pose")
    axis.set_yticks(y, names)
    axis.invert_yaxis()
    axis.set_xlabel("joint coordinate (degrees)")
    axis.grid(axis="x", alpha=0.25)
    axis.legend(loc="lower right")
    fig.tight_layout()
    plot.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(plot)
    print(f"profile: {output}")
    print(f"plot: {plot}")


if __name__ == "__main__":
    main()
