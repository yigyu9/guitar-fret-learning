"""Report Isaac-compatible left-finger DOF distributions from fitted motion."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSETS = PROJECT_ROOT / "tab2body/assets"
DEFAULT_MOTION = PROJECT_ROOT / "related_work/guitar/assets/motions/scale.json"
DEFAULT_OUT = PROJECT_ROOT / "docs/2026-08-19/fret_isaac_finger_distributions"
FINGERS = ("index", "middle", "ring", "pinky")
QUANTILES = (0.001, 0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99, 0.999)


def _axis_angle(quaternion, axis):
    return 2.0 * math.atan2(float(quaternion[axis]), float(quaternion[3]))


def _rotation_vector(quaternion):
    x, y, z, w = (float(value) for value in quaternion)
    norm = math.sqrt(x * x + y * y + z * z)
    if norm < 1e-9:
        return 0.0, 0.0, 0.0
    angle = 2.0 * math.atan2(norm, w)
    return angle * x / norm, angle * y / norm, angle * z / norm


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


def _hard_limits():
    root = ET.parse(ASSETS / "smpl_mpl_hands_body.xml").getroot()
    limits = {}
    for joint in root.iter("joint"):
        name = joint.attrib.get("name")
        raw = joint.attrib.get("range")
        if name and raw:
            limits[name] = tuple(float(value) for value in raw.split())
    return limits


def _joint_role(name):
    if "thumb1" in name:
        return "thumb CMC/base rotation component"
    if name == "LH:thumb2":
        return "thumb MCP flexion"
    if name == "LH:thumb3":
        return "thumb IP flexion"
    if name.endswith("1_x"):
        return "MCP flexion"
    if name.endswith("1_z"):
        return "MCP ab/adduction"
    if name.endswith("2"):
        return "PIP flexion"
    return "DIP flexion"


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--motion", type=Path, default=DEFAULT_MOTION)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    motion = json.loads(args.motion.read_text(encoding="utf-8"))
    frames = motion["frames"]
    samples = _samples(frames)
    hard = _hard_limits()
    rows = []
    labels = ("p00_1_deg", "p01_deg", "p05_deg", "p25_deg", "median_deg",
              "p75_deg", "p95_deg", "p99_deg", "p99_9_deg")
    for name in sorted(samples):
        values = samples[name]
        quantiles = np.quantile(values, QUANTILES)
        lower, upper = hard[name]
        row = {
            "joint": name,
            "role": _joint_role(name),
            "frames": len(values),
            "hard_lower_deg": lower,
            "hard_upper_deg": upper,
            "observed_min_deg": float(np.min(values)),
            "observed_max_deg": float(np.max(values)),
            "mean_deg": float(np.mean(values)),
            "std_deg": float(np.std(values)),
        }
        row.update({label: float(value)
                    for label, value in zip(labels, quantiles)})
        rows.append(row)

    args.out.mkdir(parents=True, exist_ok=True)
    csv_path = args.out / "isaac_finger_joint_distributions.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    json_path = args.out / "isaac_finger_joint_distributions.json"
    json_path.write_text(json.dumps({
        "schema": "tab2body.fret-isaac-finger-distributions.v1",
        "source": str(args.motion.resolve()),
        "fps": motion["fps"],
        "frames": len(frames),
        "duration_seconds": (len(frames) - 1) / motion["fps"],
        "coverage_warning": (
            "Isaac-compatible fitted data cover one short scale motion, not the "
            "full raw one-hour technique dataset. Use as a conservative starting "
            "point, not final population/anatomical hard-limit evidence."),
        "joints": rows,
    }, indent=2) + "\n", encoding="utf-8")

    names = [row["joint"].removeprefix("LH:") for row in rows]
    y = np.arange(len(rows))
    hard_lower = np.array([row["hard_lower_deg"] for row in rows])
    hard_upper = np.array([row["hard_upper_deg"] for row in rows])
    p01 = np.array([row["p01_deg"] for row in rows])
    p05 = np.array([row["p05_deg"] for row in rows])
    median = np.array([row["median_deg"] for row in rows])
    p95 = np.array([row["p95_deg"] for row in rows])
    p99 = np.array([row["p99_deg"] for row in rows])
    fig, axis = plt.subplots(figsize=(13, 11), dpi=160)
    axis.hlines(y, hard_lower, hard_upper, color="#d5d9e0", linewidth=7,
                label="XML hard range")
    axis.hlines(y, p01, p99, color="#90a8c3", linewidth=5, label="p01-p99")
    axis.hlines(y, p05, p95, color="#277da1", linewidth=5, label="p05-p95")
    axis.scatter(median, y, color="#f3722c", s=25, label="median", zorder=3)
    axis.set_yticks(y, names)
    axis.invert_yaxis()
    axis.set_xlabel("Isaac joint coordinate (degrees)")
    axis.set_title("Fitted professional-guitarist motion: Isaac finger DOFs")
    axis.grid(axis="x", alpha=0.25)
    axis.legend(loc="lower right")
    fig.tight_layout()
    plot_path = args.out / "isaac_finger_joint_distributions.png"
    fig.savefig(plot_path)
    print(json.dumps({
        "csv": str(csv_path), "json": str(json_path), "plot": str(plot_path),
        "frames": len(frames), "joints": len(rows),
    }))


if __name__ == "__main__":
    main()
