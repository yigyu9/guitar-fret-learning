"""Summarize left-hand pose ranges directly observable in guitar mocap markers.

The public CSV files contain marker positions, not anatomical joint rotations.
This tool therefore reports geometric proxies and deliberately does not label
them as simulator joint coordinates:

* base flexion/abduction: proximal finger direction in the dorsal-palm frame;
* chain bend: bend between the two marker segments of each digit;
* hand heading/elevation/roll: dorsal-palm pose in the guitar frame.

An articulated IK/retargeting pass is still required before these values can be
used as hard limits for the MPL/SMPL model.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA = PROJECT_ROOT / "related_work/guitar/dataset/data"
DEFAULT_OUT = PROJECT_ROOT / "docs/2026-08-19/guitar_marker_joint_ranges"
DIGITS = {
    "thumb": "A",
    "index": "B",
    "middle": "C",
    "ring": "D",
    "pinky": "E",
}
QUANTILES = (0.01, 0.05, 0.50, 0.95, 0.99)


def _points(table, prefix):
    names = tuple(f"{prefix}-{axis}" for axis in "XYZ")
    if not all(name in table for name in names):
        return None
    return np.column_stack([table[name] for name in names])


def _unit(vector):
    norm = np.linalg.norm(vector, axis=1, keepdims=True)
    valid = np.isfinite(norm[:, 0]) & (norm[:, 0] > 1e-6)
    result = np.full_like(vector, np.nan, dtype=np.float64)
    result[valid] = vector[valid] / norm[valid]
    return result


def _dot(left, right):
    return np.einsum("ij,ij->i", left, right)


def _signed_angle(reference, target, axis):
    return np.degrees(np.arctan2(
        _dot(np.cross(reference, target), axis),
        np.clip(_dot(reference, target), -1.0, 1.0)))


def _read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        rows = list(reader)
    if not rows:
        return {}, 0
    array = np.asarray(rows, dtype=np.float64)
    return {name: array[:, index] for index, name in enumerate(header)}, len(rows)


def _compute(table):
    result = {}
    inner = _points(table, "L-Wan-nei")
    outer = _points(table, "L-Wan-wai")
    dorsal_1 = _points(table, "L-Wan-1")
    dorsal_2 = _points(table, "L-Wan-2")
    if any(value is None for value in (inner, outer, dorsal_1, dorsal_2)):
        return result

    wrist_center = 0.5 * (inner + outer)
    dorsal_center = 0.5 * (dorsal_1 + dorsal_2)
    palm_long = _unit(dorsal_center - wrist_center)
    palm_side_seed = _unit(outer - inner)
    palm_normal = _unit(np.cross(palm_side_seed, palm_long))
    palm_side = _unit(np.cross(palm_long, palm_normal))

    guitar = [_points(table, f"Marker{index}") for index in range(1, 5)]
    if all(value is not None for value in guitar):
        body_center = 0.5 * (guitar[0] + guitar[1])
        head_center = 0.5 * (guitar[2] + guitar[3])
        guitar_long = _unit(head_center - body_center)
        width_seed = _unit(guitar[1] - guitar[0])
        guitar_normal = _unit(np.cross(guitar_long, width_seed))
        guitar_side = _unit(np.cross(guitar_normal, guitar_long))
        result["hand_heading_vs_neck_deg"] = np.degrees(np.arctan2(
            _dot(palm_long, guitar_side), _dot(palm_long, guitar_long)))
        result["hand_elevation_vs_guitar_deg"] = np.degrees(np.arctan2(
            _dot(palm_long, guitar_normal),
            np.hypot(_dot(palm_long, guitar_long),
                     _dot(palm_long, guitar_side))))
        result["palm_roll_vs_guitar_deg"] = _signed_angle(
            guitar_normal, palm_normal, palm_long)

    for digit, marker in DIGITS.items():
        distal = _points(table, f"L-{marker}1")
        middle = _points(table, f"L-{marker}2")
        base = _points(table, f"L-{marker}3")
        if any(value is None for value in (distal, middle, base)):
            continue
        distal_segment = distal - middle
        proximal_segment = middle - base
        distal_length = np.linalg.norm(distal_segment, axis=1)
        proximal_length = np.linalg.norm(proximal_segment, axis=1)
        plausible = (
            np.isfinite(distal_length) & np.isfinite(proximal_length)
            & (distal_length >= 5.0) & (distal_length <= 100.0)
            & (proximal_length >= 5.0) & (proximal_length <= 100.0))
        distal_direction = _unit(distal_segment)
        proximal_direction = _unit(proximal_segment)
        chain_bend = np.degrees(np.arccos(np.clip(
            _dot(distal_direction, proximal_direction), -1.0, 1.0)))
        normal_component = np.clip(
            _dot(proximal_direction, palm_normal), -1.0, 1.0)
        base_flexion = np.degrees(np.arcsin(normal_component))
        proximal_planar = _unit(
            proximal_direction - normal_component[:, None] * palm_normal)
        metacarpal_reference = base - dorsal_center
        metacarpal_reference = _unit(
            metacarpal_reference
            - _dot(metacarpal_reference, palm_normal)[:, None] * palm_normal)
        base_abduction = _signed_angle(
            metacarpal_reference, proximal_planar, palm_normal)
        for name, values in (
                (f"{digit}_base_flexion_proxy_deg", base_flexion),
                (f"{digit}_base_abduction_proxy_deg", base_abduction),
                (f"{digit}_chain_bend_proxy_deg", chain_bend)):
            values = values.copy()
            values[~plausible] = np.nan
            result[name] = values
    return result


def _metric_role(name):
    if name.startswith("hand_") or name.startswith("palm_"):
        return "hand pose relative to guitar; not anatomical wrist joint angle"
    if "chain_bend" in name:
        return "combined marker-chain bend; primarily PIP, DIP not separable"
    if "base_flexion" in name:
        return "proximal digit elevation in palm frame; MCP flexion proxy"
    return "proximal digit heading in palm frame; MCP ab/adduction proxy"


def _metric_quality(name):
    if "chain_bend" in name:
        return "medium-high"
    if "base_flexion" in name:
        return "medium"
    if "abduction" in name:
        return "exploratory-low"
    return "medium"


def _circular_recenter(values):
    """Move a circular degree series onto the branch around its circular mean."""
    radians = np.radians(values)
    center = np.degrees(np.arctan2(
        np.mean(np.sin(radians)), np.mean(np.cos(radians))))
    return center + (values - center + 180.0) % 360.0 - 180.0


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    paths = sorted(args.data.glob("*.csv"))
    if not paths:
        raise FileNotFoundError(f"no CSV files under {args.data}")
    series = {}
    total_frames = 0
    used_files = []
    for path in paths:
        table, frames = _read_csv(path)
        computed = _compute(table)
        if computed:
            used_files.append(path.name)
            total_frames += frames
        for name, values in computed.items():
            series.setdefault(name, []).append(values)

    rows = []
    for name in sorted(series):
        values = np.concatenate(series[name])
        values = values[np.isfinite(values)]
        if not len(values):
            continue
        if ("heading" in name or "roll" in name or "abduction" in name):
            values = _circular_recenter(values)
        q = np.quantile(values, QUANTILES)
        rows.append({
            "metric": name,
            "role": _metric_role(name),
            "quality": _metric_quality(name),
            "safe_as_simulator_hard_limit": False,
            "valid_frames": int(len(values)),
            "valid_fraction": float(len(values) / total_frames),
            "p01_deg": float(q[0]),
            "p05_deg": float(q[1]),
            "median_deg": float(q[2]),
            "p95_deg": float(q[3]),
            "p99_deg": float(q[4]),
        })

    args.out.mkdir(parents=True, exist_ok=True)
    csv_path = args.out / "left_hand_marker_joint_ranges.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    payload = {
        "schema": "tab2body.guitar-marker-joint-ranges.v1",
        "source": str(args.data.resolve()),
        "fps": 120,
        "files_seen": len(paths),
        "files_with_left_hand": len(used_files),
        "total_left_hand_frames": total_frames,
        "method_notes": [
            "Raw files contain surface marker XYZ positions, not joint angles.",
            "Angles are marker geometry proxies and are not MPL/SMPL coordinates.",
            "DIP and anatomical wrist angles are not identifiable from this marker set.",
            "Use articulated IK/retargeting before setting simulator hard limits.",
        ],
        "metrics": rows,
    }
    json_path = args.out / "left_hand_marker_joint_ranges.json"
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    plot_rows = [row for row in rows if "abduction" not in row["metric"]]
    names = [row["metric"].replace("_proxy_deg", "") for row in plot_rows]
    y = np.arange(len(plot_rows))
    p01 = np.array([row["p01_deg"] for row in plot_rows])
    p05 = np.array([row["p05_deg"] for row in plot_rows])
    med = np.array([row["median_deg"] for row in plot_rows])
    p95 = np.array([row["p95_deg"] for row in plot_rows])
    p99 = np.array([row["p99_deg"] for row in plot_rows])
    fig, axis = plt.subplots(figsize=(13, 10), dpi=160)
    axis.hlines(y, p01, p99, color="#b8c4d6", linewidth=5, label="p01-p99")
    axis.hlines(y, p05, p95, color="#277da1", linewidth=5, label="p05-p95")
    axis.scatter(med, y, color="#f3722c", s=25, label="median", zorder=3)
    axis.set_yticks(y, names)
    axis.invert_yaxis()
    axis.set_xlabel("marker-derived angle (degrees)")
    axis.set_title("Professional guitarist: left-hand marker-derived ranges")
    axis.grid(axis="x", alpha=0.25)
    axis.legend()
    fig.tight_layout()
    plot_path = args.out / "left_hand_marker_joint_ranges.png"
    fig.savefig(plot_path)
    print(json.dumps({
        "csv": str(csv_path), "json": str(json_path), "plot": str(plot_path),
        "files_with_left_hand": len(used_files), "frames": total_frames,
    }))


if __name__ == "__main__":
    main()
