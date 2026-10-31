"""Estimate Isaac finger-DOF distributions from the full raw guitar mocap set.

The raw release has surface-marker XYZ data but does not include the authors'
retargeting pipeline.  This tool uses distributional calibration, not exact IK:

1. derive palm-relative flexion/abduction and digit-chain bend marker features;
2. use all raw ``Scale*.csv`` clips as the feature calibration population;
3. quantile-match those features to the fitted ``assets/motions/scale.json``
   Isaac-compatible joint coordinates;
4. apply the monotone mapping to all left-hand raw clips and report quantiles.

The result captures technique-driven expansion beyond scale motions, but it is
an estimate.  In particular, DIP/PIP are not independently observed and thumb
base components are underdetermined by the marker layout.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA = PROJECT_ROOT / "related_work/guitar/dataset/data"
FITTED_MOTION = PROJECT_ROOT / "related_work/guitar/assets/motions/scale.json"
ASSET = PROJECT_ROOT / "tab2body/assets/smpl_mpl_hands_body.xml"
DEFAULT_OUT = PROJECT_ROOT / "docs/2026-08-19/full_guitar_isaac_finger_estimate"
PROBABILITIES = np.asarray(
    (0.001, 0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99, 0.999))
LABELS = ("p00_1_deg", "p01_deg", "p05_deg", "p25_deg", "median_deg",
          "p75_deg", "p95_deg", "p99_deg", "p99_9_deg")
FINGERS = ("index", "middle", "ring", "pinky")


def _load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _hard_limits():
    limits = {}
    for joint in ET.parse(ASSET).getroot().iter("joint"):
        name = joint.attrib.get("name")
        raw = joint.attrib.get("range")
        if name and raw:
            limits[name] = tuple(float(value) for value in raw.split())
    return limits


def _feature_for_joint(name):
    local_name = name.split(":", 1)[1]
    digit = next((finger for finger in FINGERS
                  if local_name.startswith(finger)), "thumb")
    if "thumb1_x" in name:
        return "thumb_base_flexion_proxy_deg"
    if "thumb1_y" in name or "thumb1_z" in name:
        return "thumb_base_abduction_proxy_deg"
    if name in ("LH:thumb2", "LH:thumb3"):
        return "thumb_chain_bend_proxy_deg"
    if name.endswith("1_x"):
        return f"{digit}_base_flexion_proxy_deg"
    if name.endswith("1_z"):
        return f"{digit}_base_abduction_proxy_deg"
    return f"{digit}_chain_bend_proxy_deg"


def _confidence(name):
    if name.startswith("LH:thumb"):
        return "low"
    if name.endswith("1_z"):
        return "low"
    if name.endswith("1_x"):
        return "medium-low"
    return "medium-low; PIP/DIP statistically coupled"


def _linear_interp_extrapolate(values, source_knots, target_knots):
    result = np.interp(values, source_knots, target_knots)
    lower = values < source_knots[0]
    upper = values > source_knots[-1]
    lower_span = source_knots[1] - source_knots[0]
    upper_span = source_knots[-1] - source_knots[-2]
    if lower_span > 1e-8:
        slope = (target_knots[1] - target_knots[0]) / lower_span
        result[lower] = target_knots[0] + slope * (
            values[lower] - source_knots[0])
    if upper_span > 1e-8:
        slope = (target_knots[-1] - target_knots[-2]) / upper_span
        result[upper] = target_knots[-1] + slope * (
            values[upper] - source_knots[-1])
    return result


def _summarize(values):
    quantiles = np.quantile(values, PROBABILITIES)
    result = {label: float(value)
              for label, value in zip(LABELS, quantiles)}
    result.update({
        "observed_min_deg": float(np.min(values)),
        "observed_max_deg": float(np.max(values)),
        "mean_deg": float(np.mean(values)),
        "std_deg": float(np.std(values)),
    })
    return result


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-data", type=Path, default=RAW_DATA)
    parser.add_argument("--fitted-motion", type=Path, default=FITTED_MOTION)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    marker = _load_module(
        PROJECT_ROOT / "tab2body/tools/analyze_guitar_marker_joint_ranges.py",
        "guitar_marker_ranges")
    fitted = _load_module(
        PROJECT_ROOT / "tab2body/tools/analyze_fret_isaac_finger_distributions.py",
        "fitted_finger_ranges")
    fitted_document = json.loads(args.fitted_motion.read_text(encoding="utf-8"))
    fitted_samples = fitted._samples(fitted_document["frames"])
    hard = _hard_limits()

    all_features = {}
    scale_features = {}
    file_counts = {}
    total_frames = 0
    left_files = 0
    for path in sorted(args.raw_data.glob("*.csv")):
        table, frames = marker._read_csv(path)
        computed = marker._compute(table)
        if not computed:
            continue
        left_files += 1
        total_frames += frames
        file_counts[path.name] = frames
        for name, values in computed.items():
            finite = values[np.isfinite(values)]
            if not len(finite):
                continue
            all_features.setdefault(name, []).append(finite)
            if path.stem.startswith("Scale"):
                scale_features.setdefault(name, []).append(finite)
    all_features = {name: np.concatenate(parts)
                    for name, parts in all_features.items()}
    scale_features = {name: np.concatenate(parts)
                      for name, parts in scale_features.items()}

    rows = []
    for joint in sorted(fitted_samples):
        feature = _feature_for_joint(joint)
        source = scale_features[feature]
        values = all_features[feature]
        source_knots = np.quantile(source, PROBABILITIES)
        target_knots = np.quantile(fitted_samples[joint], PROBABILITIES)
        estimated_unclipped = _linear_interp_extrapolate(
            values, source_knots, target_knots)
        lower, upper = hard[joint]
        clipped = np.clip(estimated_unclipped, lower, upper)
        row = {
            "joint": joint,
            "marker_feature": feature,
            "confidence": _confidence(joint),
            "raw_frames": int(len(values)),
            "calibration_frames": int(len(source)),
            "hard_lower_deg": lower,
            "hard_upper_deg": upper,
            "lower_clip_fraction": float(np.mean(estimated_unclipped < lower)),
            "upper_clip_fraction": float(np.mean(estimated_unclipped > upper)),
        }
        row.update(_summarize(clipped))
        rows.append(row)

    args.out.mkdir(parents=True, exist_ok=True)
    csv_path = args.out / "estimated_isaac_finger_distributions.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    json_path = args.out / "estimated_isaac_finger_distributions.json"
    json_path.write_text(json.dumps({
        "schema": "tab2body.full-guitar-estimated-isaac-finger-distributions.v1",
        "method": "marker feature to fitted Isaac DOF empirical quantile mapping",
        "raw_source": str(args.raw_data.resolve()),
        "calibration_raw_glob": "Scale*.csv",
        "fitted_calibration_source": str(args.fitted_motion.resolve()),
        "raw_files_seen": len(list(args.raw_data.glob("*.csv"))),
        "left_hand_files": left_files,
        "left_hand_frames": total_frames,
        "fps": 120,
        "duration_seconds": total_frames / 120.0,
        "warnings": [
            "This is distributional calibration, not the authors' exact IK.",
            "The fitted clip is not time-synchronized to a released raw CSV.",
            "PIP and DIP share one marker-chain feature and are not independently observed.",
            "MCP ab/adduction and all thumb-base components have low confidence.",
            "Do not install these quantiles directly as hard limits without pose validation.",
        ],
        "file_frames": file_counts,
        "joints": rows,
    }, indent=2) + "\n", encoding="utf-8")

    names = [row["joint"].removeprefix("LH:") for row in rows]
    y = np.arange(len(rows))
    lower = np.array([row["hard_lower_deg"] for row in rows])
    upper = np.array([row["hard_upper_deg"] for row in rows])
    p01 = np.array([row["p01_deg"] for row in rows])
    p05 = np.array([row["p05_deg"] for row in rows])
    median = np.array([row["median_deg"] for row in rows])
    p95 = np.array([row["p95_deg"] for row in rows])
    p99 = np.array([row["p99_deg"] for row in rows])
    fig, axis = plt.subplots(figsize=(13, 11), dpi=160)
    axis.hlines(y, lower, upper, color="#d5d9e0", linewidth=7,
                label="XML hard range")
    axis.hlines(y, p01, p99, color="#90a8c3", linewidth=5,
                label="estimated p01-p99")
    axis.hlines(y, p05, p95, color="#277da1", linewidth=5,
                label="estimated p05-p95")
    axis.scatter(median, y, color="#f3722c", s=25,
                 label="estimated median", zorder=3)
    axis.set_yticks(y, names)
    axis.invert_yaxis()
    axis.set_xlabel("estimated Isaac joint coordinate (degrees)")
    axis.set_title("Full raw professional-guitarist dataset: estimated Isaac finger DOFs")
    axis.grid(axis="x", alpha=0.25)
    axis.legend(loc="lower right")
    fig.tight_layout()
    plot_path = args.out / "estimated_isaac_finger_distributions.png"
    fig.savefig(plot_path)
    print(json.dumps({
        "csv": str(csv_path), "json": str(json_path), "plot": str(plot_path),
        "files": left_files, "frames": total_frames, "joints": len(rows),
    }))


if __name__ == "__main__":
    main()
