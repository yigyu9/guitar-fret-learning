#!/usr/bin/env python3
"""Plot saved grip-palm refinement curves and compose recorded hand-camera frames."""
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
DOCS = ROOT / "docs/2026-10-12/stability_adapter_2/results"
PHASE = DOCS / "grip_palm_refinement_v1"
BASELINE = DOCS / "multi_face_grip_v3/native/seed_2"
FONT = Path("/usr/share/fonts/truetype/nanum/NanumGothic.ttf")
LABELS = [
    ("기준 seed 2 (이전 실행)", BASELINE),
    ("새 refinement α=0.5", PHASE / "native/w1_a0p5"),
    ("새 refinement α=0.25", PHASE / "native/w1_a0p25"),
]


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def json_read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def finite(values, name: str):
    arr = np.asarray(values, dtype=float)
    if arr.ndim != 1 or not np.isfinite(arr).all():
        raise ValueError(f"{name} must be a finite 1-D series")
    return arr


def inputs_for() -> list[Path]:
    paths = [PHASE / "analysis.json", PHASE / "artifact_brief.json", FONT]
    for _, run in LABELS:
        paths.extend([run / "report.json", run / "capture.json"])
    for label, run in LABELS[1:]:
        paths.append(run / "initial_values.json")
    for _, run in LABELS:
        for step in (0, 1200):
            paths.append(run / "frames/hands" / f"{step // 8:05d}.png")
    return paths


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()
    out = args.out_dir.resolve()
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"refusing nonempty output directory: {out}")
    out.mkdir(parents=True, exist_ok=True)

    inputs = inputs_for()
    missing = [str(p) for p in inputs if not p.is_file()]
    if missing:
        raise SystemExit("missing inputs: " + ", ".join(missing))
    before = {str(p): sha(p) for p in inputs}

    analysis = json_read(PHASE / "analysis.json")
    brief = json_read(PHASE / "artifact_brief.json")
    if not all(analysis.get("checks", {}).values()):
        raise ValueError("analysis contract checks are not all true")
    if analysis.get("counts") != {"native_initializations": 2, "physics_steps": 2400}:
        raise ValueError("unexpected fresh-run counts")
    expected_labels = ["w1_a0p5", "w1_a0p25"]
    if list(analysis.get("curves", {})) != expected_labels:
        raise ValueError("unexpected analysis curve labels")

    curve_data = {"기준 seed 2 (이전 실행)": analysis["reference_seed2"]["curve"]}
    curve_data.update({"새 refinement α=0.5": analysis["curves"]["w1_a0p5"],
                       "새 refinement α=0.25": analysis["curves"]["w1_a0p25"]})
    color = {"기준 seed 2 (이전 실행)": "#404040",
             "새 refinement α=0.5": "#1769aa", "새 refinement α=0.25": "#d17c00"}
    fig, axes = plt.subplots(2, 1, figsize=(10.5, 7.4), sharex=True, constrained_layout=True)
    for title, field, ylabel in [
        ("Guitar position error", "guitar_position_error_mm", "Position error (mm)"),
        ("Guitar rotation error", "guitar_rotation_error_deg", "Rotation error (degrees)"),
    ]:
        ax = axes[0] if field.endswith("mm") else axes[1]
        for label, values in curve_data.items():
            t = finite(values["time_s"], f"{label}.time_s")
            y = finite(values[field], f"{label}.{field}")
            if len(t) != 1201 or len(y) != 1201 or not np.all(np.diff(t) > 0):
                raise ValueError(f"unexpected curve length/time for {label}")
            ax.plot(t, y, label=label, color=color[label], linewidth=1.6)
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=.25)
    axes[1].set_xlabel("Time (s)")
    axes[0].legend(loc="upper left", ncols=1, fontsize=8)
    axes[0].set_xlim(0, 5)
    fig.suptitle("Saved native-run guitar errors — 5 s", fontsize=13)
    curve_path = out / "grip_palm_refinement_curves.png"
    fig.savefig(curve_path, dpi=170)
    plt.close(fig)

    fig, axes = plt.subplots(2, 3, figsize=(12.6, 8.1), constrained_layout=True)
    col_titles = ["Baseline seed 2\n(previous run)", "New α=0.5", "New α=0.25"]
    for col, ((_, run), title) in enumerate(zip(LABELS, col_titles)):
        capture = json_read(run / "capture.json")
        if capture.get("fps") != 30 or len(capture.get("frames", [])) != 151:
            raise ValueError(f"unexpected camera capture metadata for {run}")
        for row, step in enumerate((0, 1200)):
            frame = next((f for f in capture["frames"] if f.get("physics_step") == step), None)
            if frame is None or frame.get("render_preserves_states") is not True:
                raise ValueError(f"missing state-aligned frame at step {step}: {run}")
            image_key = next((p for p in frame.get("image_sha256", {}) if "/frames/hands/" in p), None)
            if image_key is None:
                raise ValueError(f"missing hands camera image reference: {run}")
            image_path = Path(image_key)
            if image_path.resolve() != (run / "frames/hands" / f"{step // 8:05d}.png").resolve():
                raise ValueError(f"unexpected camera frame mapping: {image_path}")
            if sha(image_path) != frame["image_sha256"][image_key]:
                raise ValueError(f"camera frame SHA mismatch: {image_path}")
            img = plt.imread(image_path)
            ax = axes[row, col]
            ax.imshow(img)
            ax.set_axis_off()
            if row == 0:
                ax.set_title(title, fontsize=10)
            ax.text(.02, .03, f"t={step/240:.1f} s  |  step {step}", transform=ax.transAxes,
                    color="white", fontsize=8, va="bottom",
                    bbox={"facecolor": "black", "alpha": .65, "pad": 3})
    fig.suptitle("Recorded Isaac Gym hand-camera frames (saved native poses)", fontsize=13)
    camera_path = out / "grip_palm_refinement_hands_camera.png"
    fig.savefig(camera_path, dpi=150)
    plt.close(fig)

    after = {str(p): sha(p) for p in inputs}
    if before != after:
        raise RuntimeError("one or more input files changed during artifact generation")
    manifest = {
        "producer": str(Path(__file__).resolve()),
        "producer_sha256": sha(Path(__file__).resolve()),
        "inputs_sha256_before": before,
        "inputs_sha256_after": after,
        "input_count": len(inputs),
        "fresh_native_runs": {"initializations": 2, "physics_steps": 2400},
        "reference_source": "previous saved seed_2 run; no new initialization in this phase",
        "outputs_sha256": {str(p): sha(p) for p in (curve_path, camera_path)},
        "frame_mapping": {"capture_fps": 30, "physics_step_rate_hz": 240,
                          "displayed_steps": [0, 1200], "displayed_view": "hands"},
        "source_note": "Saved analysis curves and original Isaac Gym camera PNGs; no native or MuJoCo rendering performed by this producer.",
        "analysis_checks": analysis["checks"],
        "analysis_counts": analysis["counts"],
        "figure_scope": brief.get("requested_artifacts"),
    }
    (out / "artifact_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(curve_path)
    print(camera_path)
    print(out / "artifact_manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
