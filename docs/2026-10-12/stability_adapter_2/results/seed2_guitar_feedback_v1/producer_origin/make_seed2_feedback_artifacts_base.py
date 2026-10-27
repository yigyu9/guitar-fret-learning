#!/usr/bin/env python3
"""Render saved Seed 2 locality analyses and native camera frames; no simulation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Dict, List

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

matplotlib.rcParams["font.family"] = "NanumGothic"
matplotlib.rcParams["axes.unicode_minus"] = False

ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT / "docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1"
OLD = ROOT / "docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1"
FONT = Path("/usr/share/fonts/truetype/nanum/NanumGothic.ttf")
NEW_LABELS = ["negative_shoulder_y", "negative_wrist_z", "half_heldout"]
CAMERA_LABELS = NEW_LABELS
DISPLAY = {
    "saved_base": "Saved base",
    "saved_positive_shoulder_y": "Saved +Shoulder Y",
    "negative_shoulder_y": "New -Shoulder Y",
    "saved_positive_wrist_z": "Saved +Wrist Z",
    "negative_wrist_z": "New -Wrist Z",
    "saved_full_heldout": "Saved full heldout",
    "half_heldout": "New half heldout",
}
COLORS = {
    "saved_base": "#222222",
    "saved_positive_shoulder_y": "#1f77b4",
    "negative_shoulder_y": "#d62728",
    "saved_positive_wrist_z": "#9467bd",
    "negative_wrist_z": "#2ca02c",
    "saved_full_heldout": "#ff7f0e",
    "half_heldout": "#17becf",
}
SAVED_LABELS = [
    "saved_base", "saved_positive_shoulder_y", "saved_positive_wrist_z", "saved_full_heldout"
]
ALL_LABELS = SAVED_LABELS[:2] + ["negative_shoulder_y", SAVED_LABELS[2], "negative_wrist_z", SAVED_LABELS[3], "half_heldout"]


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def finite_series(values, label: str) -> np.ndarray:
    result = np.asarray(values, dtype=float)
    if result.ndim != 1 or not np.isfinite(result).all():
        raise ValueError(f"{label} must be finite one-dimensional data")
    return result


def input_paths() -> List[Path]:
    paths = [
        Path(__file__).resolve(), FONT,
        PHASE / "artifact_brief.json", PHASE / "analysis.json",
        OLD / "probe_analysis.json", OLD / "heldout_analysis.json",
    ]
    for label in NEW_LABELS:
        run = PHASE / "native" / label
        paths.extend([run / "report.json", run / "initial_values.json", run / "capture.json"])
        paths.extend(run / "frames" / "hands" / f"{frame:05d}.png" for frame in (0, 150))
    return paths


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()
    out = args.out_dir.resolve()
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"refusing nonempty output directory: {out}")
    out.mkdir(parents=True, exist_ok=True)

    inputs = input_paths()
    missing = [str(path) for path in inputs if not path.is_file()]
    if missing:
        raise SystemExit("missing inputs: " + ", ".join(missing))
    before = {str(path): sha(path) for path in inputs}

    brief = read_json(PHASE / "artifact_brief.json")
    analysis = read_json(PHASE / "analysis.json")
    old_probe = read_json(OLD / "probe_analysis.json")
    old_heldout = read_json(OLD / "heldout_analysis.json")
    if analysis.get("counts") != {"native_initializations": 3, "physics_steps": 3600}:
        raise ValueError("unexpected fresh native counts")
    if not analysis.get("checks") or not all(analysis["checks"].values()):
        raise ValueError("locality analysis checks failed")
    if list(analysis.get("curves", {})) != NEW_LABELS:
        raise ValueError("unexpected new curve labels")
    if not old_probe.get("checks") or not all(old_probe["checks"].values()):
        raise ValueError("saved probe analysis checks failed")
    if not old_heldout.get("checks") or not all(old_heldout["checks"].values()):
        raise ValueError("saved heldout analysis checks failed")
    if old_probe.get("counts") != {"native_initializations": 7, "physics_steps": 8400}:
        raise ValueError("unexpected historical probe counts")
    old_counts = old_heldout.get("counts", {})
    if old_counts.get("phase_native_initializations") != 8 or old_counts.get("phase_physics_steps") != 9600:
        raise ValueError("unexpected historical heldout count schema")
    if not isinstance(analysis.get("guitar_first24_pose_exact_vs_saved_base"), dict):
        raise ValueError("missing initial-state exactness record")
    prefix = analysis["guitar_first24_pose_exact_vs_saved_base"]
    if set(prefix) != set(NEW_LABELS) or not all(type(prefix[label]) is bool for label in NEW_LABELS):
        raise ValueError("new initial prefix exactness observation schema is incomplete")

    series: Dict[str, dict] = {
        "saved_base": old_probe["curves"]["base"],
        "saved_positive_shoulder_y": old_probe["curves"]["shoulder_y"],
        "negative_shoulder_y": analysis["curves"]["negative_shoulder_y"],
        "saved_positive_wrist_z": old_probe["curves"]["wrist_z"],
        "negative_wrist_z": analysis["curves"]["negative_wrist_z"],
        "saved_full_heldout": old_heldout["curves"],
        "half_heldout": analysis["curves"]["half_heldout"],
    }
    fig, axes = plt.subplots(2, 1, figsize=(13.2, 8.7), sharex=False, constrained_layout=True)
    for ax, field, title, ylabel in (
        (axes[0], "guitar_position_error_mm", "Guitar position error", "Error (mm)"),
        (axes[1], "guitar_rotation_error_deg", "Guitar rotation error", "World SO(3) error (degrees)"),
    ):
        for label in ALL_LABELS:
            curve = series[label]
            x = finite_series(curve["time_s"], f"{label}.time_s")
            y = finite_series(curve[field], f"{label}.{field}")
            if len(x) != 1201 or len(y) != 1201 or not np.all(np.diff(x) > 0):
                raise ValueError(f"unexpected sample sequence: {label}.{field}")
            if not np.isclose(x[0], 0.0) or not np.isclose(x[-1], 5.0):
                raise ValueError(f"unexpected time coverage: {label}.{field}")
            ax.plot(x, y, color=COLORS[label], linewidth=1.45,
                    linestyle="--" if label.startswith("saved_") else "-",
                    label=DISPLAY[label])
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=.25)
        ax.set_xlim(0.0, 5.0)
        ax.legend(loc="best", ncol=2, fontsize=8)
    axes[-1].set_xlabel("Time (s)")
    fig.suptitle("Seed 2 response locality: saved references and new runs", fontsize=13)
    curve_path = out / "seed2_response_locality_curves.png"
    fig.savefig(curve_path, dpi=170)
    plt.close(fig)

    fig, axes = plt.subplots(2, 3, figsize=(12.8, 5.5), constrained_layout=True)
    camera_meta = {}
    for col, label in enumerate(CAMERA_LABELS):
        run = PHASE / "native" / label
        capture = read_json(run / "capture.json")
        frames = capture.get("frames", [])
        if capture.get("fps") != 30 or len(frames) != 151:
            raise ValueError(f"unexpected actual-camera metadata for {label}")
        camera_meta[label] = {"fps": 30, "frame_count": 151, "displayed_steps": [0, 1200]}
        for row, (step, idx) in enumerate(((0, 0), (1200, 150))):
            record = next((item for item in frames if item.get("physics_step") == step), None)
            if record is None or record.get("render_preserves_states") is not True:
                raise ValueError(f"missing state-preserving capture frame: {label}/{step}")
            if not np.isclose(float(record.get("time_s", -1)), step / 240.0):
                raise ValueError(f"camera timestamp mismatch: {label}/{step}")
            image_path = (run / "frames" / "hands" / f"{idx:05d}.png").resolve()
            recorded = record.get("image_sha256", {})
            match = next((key for key in recorded if Path(key).resolve() == image_path), None)
            if match is None or sha(image_path) != recorded[match]:
                raise ValueError(f"camera image SHA mismatch: {image_path}")
            ax = axes[row, col]
            ax.imshow(plt.imread(image_path))
            ax.set_axis_off()
            if row == 0:
                ax.set_title(label.replace("_", " "), fontsize=9)
            ax.text(.02, .03, f"t={step / 240:.1f} s | step {step}", transform=ax.transAxes,
                    color="white", fontsize=8, va="bottom",
                    bbox={"facecolor": "black", "alpha": .65, "pad": 3})
    fig.suptitle("Recorded Isaac Gym hands-camera frames: three new runs", fontsize=13)
    camera_path = out / "seed2_response_locality_hands_camera.png"
    fig.savefig(camera_path, dpi=150)
    plt.close(fig)

    after = {str(path): sha(path) for path in inputs}
    if before != after:
        raise RuntimeError("input SHA changed during artifact generation")
    manifest = {
        "producer": str(Path(__file__).resolve()),
        "producer_sha256": sha(Path(__file__).resolve()),
        "input_count": len(inputs),
        "inputs_sha256_before": before,
        "inputs_sha256_after": after,
        "fresh_phase_counts": analysis["counts"],
        "historical_probe_counts": old_probe["counts"],
        "historical_heldout_counts": old_counts,
        "fresh_analysis_checks": analysis["checks"],
        "historical_probe_checks": old_probe["checks"],
        "historical_heldout_checks": old_heldout["checks"],
        "historical_runs_are_saved_references_not_new_trials": True,
        "camera_frames": camera_meta,
        "native_calls_by_producer": 0,
        "outputs_sha256": {str(path): sha(path) for path in (curve_path, camera_path)},
    }
    manifest_path = out / "artifact_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
                             encoding="utf-8")
    print(curve_path)
    print(camera_path)
    print(manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
