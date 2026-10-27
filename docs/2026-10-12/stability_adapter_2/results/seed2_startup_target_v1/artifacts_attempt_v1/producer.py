#!/usr/bin/env python3
"""Render saved startup-target comparison curves and recorded hand-camera frames."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

matplotlib.rcParams["font.family"] = "NanumGothic"

ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT / "docs/2026-10-12/stability_adapter_2/results/seed2_startup_target_v1"
FONT = Path("/usr/share/fonts/truetype/nanum/NanumGothic.ttf")
RUNS = [
    ("off", "편차 OFF", PHASE / "native/off"),
    ("half", "초기 편차 0.5×", PHASE / "native/half"),
    ("full", "초기 편차 1×", PHASE / "native/full"),
]


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def series(values, label: str) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if arr.ndim != 1 or not np.isfinite(arr).all():
        raise ValueError(f"{label} must be finite 1-D numeric data")
    return arr


def input_paths() -> list[Path]:
    paths = [Path(__file__).resolve(), PHASE / "analysis.json", PHASE / "artifact_brief.json", FONT]
    for _, _, run in RUNS:
        paths.extend([run / "report.json", run / "capture.json", run / "initial_values.json"])
        for frame in range(151):
            for view in ("hands", "whole_body"):
                paths.append(run / "frames" / view / f"{frame:05d}.png")
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
    missing = [str(p) for p in inputs if not p.is_file()]
    if missing:
        raise SystemExit("missing inputs: " + ", ".join(missing))
    before = {str(p): sha(p) for p in inputs}

    analysis = load_json(PHASE / "analysis.json")
    brief = load_json(PHASE / "artifact_brief.json")
    checks = analysis.get("checks", {})
    if len(checks) != 8 or not all(checks.values()):
        raise ValueError("expected eight passing analysis checks")
    if analysis.get("counts") != {"native_initializations": 3, "physics_steps": 3600}:
        raise ValueError("unexpected fresh-run counts")
    if not isinstance(analysis.get("baseline_full5s_five_arrays_exact"), bool):
        raise ValueError("missing full5s reproducibility observation")
    labels = [key for key, _, _ in RUNS]
    if list(analysis.get("curves", {})) != labels:
        raise ValueError("unexpected analysis curve labels")

    colors = {"off": "#404040", "half": "#1769aa", "full": "#d17c00"}
    display = {key: name for key, name, _ in RUNS}
    fig, axes = plt.subplots(3, 1, figsize=(11, 9), sharex=False, constrained_layout=True)
    panels = [
        ("guitar_position_error_mm", "Guitar position error", "Error (mm)"),
        ("guitar_rotation_error_deg", "Guitar rotation error", "SO(3) error (degrees)"),
    ]
    for ax, (field, title, ylabel) in zip(axes[:2], panels):
        for key, _, _ in RUNS:
            curve = analysis["curves"][key]
            x = series(curve["time_s"], f"{key}.time_s")
            y = series(curve[field], f"{key}.{field}")
            if len(x) != 1201 or len(y) != 1201 or not np.all(np.diff(x) > 0):
                raise ValueError(f"unexpected {field} series length/time for {key}")
            ax.plot(x, y, color=colors[key], linewidth=1.5, label=display[key])
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=.25)
        ax.legend(loc="best", fontsize=8)

    target_ax = axes[2]
    target_ax.set_title("Left-arm target jump (dashed) vs actual coordinate drift (solid)")
    for key, _, _ in RUNS:
        curve = analysis["curves"][key]
        x = series(curve["time_s"], f"{key}.time_s")
        drift = series(curve["max_actual_left_arm_coordinate_drift_deg"],
                       f"{key}.max_actual_left_arm_coordinate_drift_deg")
        if len(x) != 1201 or len(drift) != 1201 or not np.all(np.diff(x) > 0):
            raise ValueError(f"unexpected left-arm drift series length/time for {key}")
        target = next(row for row in analysis["summary"] if row["label"] == key)["startup_target"]
        delta = series(target["actual_target_delta_rad"], f"{key}.actual_target_delta_rad")
        if len(delta) != 12:
            raise ValueError(f"expected 12 left-arm target deltas for {key}")
        jump = float(target["max_abs_target_delta_deg"])
        if not np.isfinite(jump):
            raise ValueError(f"non-finite target jump for {key}")
        target_ax.plot(x, drift, color=colors[key], linewidth=1.5,
                       label=f"{display[key]} actual max |q−q0|")
        target_ax.axhline(jump, color=colors[key], linestyle="--", linewidth=1.2,
                          label=f"{display[key]} initial target Δ={jump:.3f}°")
    target_ax.set_ylabel("Magnitude (degrees)")
    target_ax.set_xlabel("Time (s)")
    target_ax.grid(True, alpha=.25)
    target_ax.legend(loc="best", fontsize=7)
    for ax in axes:
        ax.set_xlim(0, 5)
    axes[1].set_xlabel("Time (s)")
    fig.suptitle("Saved 5-second startup target comparison", fontsize=13)
    curve_path = out / "seed2_startup_target_curves.png"
    fig.savefig(curve_path, dpi=170)
    plt.close(fig)

    fig, axes = plt.subplots(2, 3, figsize=(12.6, 5.4), constrained_layout=True)
    initial_LA = {}
    for col, (key, title, run) in enumerate(RUNS):
        report = load_json(run / "report.json")
        if not report.get("completed") or report.get("native_initializations") != 1 or report.get("physics_steps") != 1200 or report.get("frame_count") != 151:
            raise ValueError(f"unexpected completed-run report: {key}")
        if len(report.get("checks", {})) != 9 or not all(report["checks"].values()):
            raise ValueError(f"run report checks failed: {key}")
        initial = load_json(run / "initial_values.json")
        initial_LA[key] = {
            "absolute_rest_length_m": initial["absolute_strap_rest_length_m"],
            "initial_route_length_m": initial["initial_route_length_m"],
        }
        capture = load_json(run / "capture.json")
        frames = capture.get("frames", [])
        if capture.get("fps") != 30 or len(frames) != 151:
            raise ValueError(f"unexpected hand-camera capture metadata: {key}")
        for index, frame in enumerate(frames):
            step = index * 8
            if frame.get("physics_step") != step or abs(float(frame.get("time_s", -1)) - step / 240) > 1e-12:
                raise ValueError(f"unexpected frame time mapping: {key}/{index}")
            if frame.get("render_preserves_states") is not True:
                raise ValueError(f"camera frame is not marked state-preserving: {key}/{index}")
            recorded = frame.get("image_sha256", {})
            for view in ("hands", "whole_body"):
                image = (run / "frames" / view / f"{index:05d}.png").resolve()
                match = next((name for name in recorded if Path(name).resolve() == image), None)
                if match is None or sha(image) != recorded[match]:
                    raise ValueError(f"missing or mismatched {view} image: {image}")
        for row, step in enumerate((0, 1200)):
            frame = next((item for item in frames if item.get("physics_step") == step), None)
            if frame is None:
                raise ValueError(f"missing requested step {step} for {key}")
            image_path = (run / "frames/hands" / f"{step // 8:05d}.png").resolve()
            image = plt.imread(image_path)
            ax = axes[row, col]
            ax.imshow(image)
            ax.set_axis_off()
            if row == 0:
                ax.set_title(title, fontsize=10)
            ax.text(.02, .03, f"t={step/240:.1f} s | step {step}", transform=ax.transAxes,
                    color="white", fontsize=8, va="bottom",
                    bbox={"facecolor": "black", "alpha": .65, "pad": 3})
    fig.suptitle("Recorded Isaac Gym hand-camera frames", fontsize=13)
    camera_path = out / "seed2_startup_target_hands_camera.png"
    fig.savefig(camera_path, dpi=150)
    plt.close(fig)

    after = {str(p): sha(p) for p in inputs}
    if before != after:
        raise RuntimeError("input SHA changed during artifact generation")
    manifest = {
        "producer": str(Path(__file__).resolve()),
        "producer_sha256": sha(Path(__file__).resolve()),
        "input_count": len(inputs),
        "inputs_sha256_before": before,
        "inputs_sha256_after": after,
        "fresh_native_runs": analysis["counts"],
        "analysis_check_count": len(checks),
        "analysis_checks": checks,
        "full5s_baseline_raw_five_arrays_exact_observation": analysis["baseline_full5s_five_arrays_exact"],
        "initial_strap_lengths": initial_LA,
        "startup_target_max_abs_delta_deg": {key: next(row for row in analysis["summary"] if row["label"] == key)["startup_target"]["max_abs_target_delta_deg"] for key, _, _ in RUNS},
        "camera_frames": {"per_run": 151, "runs": 3, "views_hashed": ["hands", "whole_body"],
                          "displayed_view": "hands", "displayed_physics_steps": [0, 1200], "fps": 30},
        "target_drift_note": "target offsets are maximum left-arm setpoint deltas from q0; actual drift is max absolute native coordinate q(t)-q0 across 12 axes, not per-joint residual or guitar SO(3).",
        "outputs_sha256": {str(path): sha(path) for path in (curve_path, camera_path)},
        "scope": brief.get("requested"),
    }
    (out / "artifact_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    print(curve_path)
    print(camera_path)
    print(out / "artifact_manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
