#!/usr/bin/env python3
"""Render a sealed two-panel comparison from saved joint-only native traces."""
import hashlib
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path("/home/ajou/yigyu/3")
A = ROOT / "stability_adapter_2"
P = ROOT / "docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1"
BASE = ROOT / "docs/2026-10-12/stability_adapter_2/results/small_wrist_motion_v1/native"
OUT = P / "artifacts"
FONT = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line]


def seal_paths(analysis, snapshot):
    paths = {Path(path) for path in analysis["input_sha256"]}
    paths.update({
        P / "analysis.json", P / "analysis.log", P / "analysis_execution.json",
        P / "analysis_source_manifest.json", P / "native_source_manifest.json",
        P / "preparation.json", P / "preparation.log", P / "preparation_execution.json",
        P / "proposal.json", P / "native_execution.json", P / "native.log",
        P / "collection_source.py", P / "collection_execution_producer.py",
        P / "collection_execution.json", P / "collection.log",
        P / "native/initial_values.json", P / "native/report.json", P / "native/capture.json",
        P / "native/raw/capture.json", P / "native/videos.json", P / "native/trace.jsonl",
        P / "native/states.jsonl", P / "native/controls.jsonl", P / "native/contacts.jsonl",
        P / "native/tasks.jsonl", P / "native/attempt.json", FONT,
        OUT / "source_snapshot.json",
        BASE / "initial_values.json", BASE / "report.json", BASE / "videos.json",
        BASE / "trace.jsonl", BASE / "states.jsonl", BASE / "controls.jsonl", BASE / "contacts.jsonl",
        BASE / "frames/hands/00000.png", BASE / "frames/hands/00150.png",
        BASE / "hands.mp4", BASE / "whole_body.mp4",
    })
    for camera in ("hands", "whole_body"):
        for frame in ("00000.png", "00150.png"):
            paths.add(P / "native/frames" / camera / frame)
    for row in snapshot["files"]:
        paths.add(OUT / row["copy_path"])
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing sealed inputs: " + ", ".join(sorted(missing)))
    return {str(path): sha256(path) for path in sorted(paths)}


def check_summary(summary, rows):
    if len(rows) != 1201 or rows[0]["time_s"] != 0.0 or rows[-1]["time_s"] != 5.0:
        raise ValueError("expected saved native trace samples from t=0 through t=5 s")
    t2 = next((r for r in rows if abs(r["time_s"] - 2.0) < 1e-9), None)
    if t2 is None:
        raise ValueError("native trace does not contain an exact t=2 s sample")
    observed = {
        "max_initial_position_error_mm": max(r["position_error_m"] * 1000.0 for r in rows),
        "max_initial_rotation_error_deg": max(r["rotation_error_deg"] for r in rows),
        "max_position_change_from_2s_mm": max(abs(r["position_error_m"] - t2["position_error_m"]) * 1000.0 for r in rows),
        "max_rotation_change_from_2s_deg": max(abs(r["rotation_error_deg"] - t2["rotation_error_deg"]) for r in rows),
    }
    for key, value in observed.items():
        if not math.isclose(value, summary[key], rel_tol=0.0, abs_tol=1e-8):
            raise ValueError("analysis summary disagrees with trace for " + key)


def main():
    outputs = (OUT / "joint_only_fixed_strap_timeseries.png", OUT / "artifact_manifest.json")
    if any(path.exists() for path in outputs):
        raise SystemExit("refusing to overwrite a successful artifact; use a new versioned path")
    analysis = read_json(P / "analysis.json")
    report = read_json(P / "native/report.json")
    execution = read_json(P / "native_execution.json")
    snapshot = read_json(OUT / "source_snapshot.json")
    if len(analysis["checks"]) != 17 or not all(analysis["checks"].values()):
        raise ValueError("analysis contract checks are incomplete")
    if analysis["new_native_initializations"] != 1 or analysis["new_physics_steps"] != 1200:
        raise ValueError("unexpected native run count in analysis")
    if not report["completed"] or report["native_initializations"] != 1 or report["physics_steps"] != 1200 or report["frame_count"] != 151:
        raise ValueError("native report does not describe one complete run")
    if execution["exit_code"] != 0:
        raise ValueError("saved native execution did not exit successfully")

    before = seal_paths(analysis, snapshot)
    for path, expected in analysis["input_sha256"].items():
        if before[path] != expected:
            raise ValueError("analysis input SHA mismatch: " + path)
    producer_before = sha256(A / "make_joint_only_fixed_strap_artifacts.py")
    if producer_before != snapshot["producer_sha256"]:
        raise ValueError("pre-run producer snapshot SHA mismatch")

    baseline = read_jsonl(BASE / "trace.jsonl")
    candidate = read_jsonl(P / "native/trace.jsonl")
    summaries = {row["label"]: row["guitar"] for row in analysis["summary"]}
    check_summary(summaries["original_LA_baseline"], baseline)
    check_summary(summaries["joint_only_original_LA"], candidate)

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 11})
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 6.8))
    fig.suptitle("Joint-only initial/PD shift with the same fixed passive strap length", fontsize=14)
    series = [
        (baseline, "Original LA baseline", "#3568a8"),
        (candidate, "Joint-only initial", "#d97728"),
    ]
    panels = [
        ("position_error_m", 1000.0, "Guitar position error to initial world pose", "Position error (mm)"),
        ("rotation_error_deg", 1.0, "Guitar rotation error to initial world pose", "Rotation error (degrees)"),
    ]
    for ax, (field, scale, title, ylabel) in zip(axes, panels):
        ax.axvspan(2.0, 5.0, color="#777777", alpha=0.10, label="2–5 s evaluation window")
        for rows, label, color in series:
            ax.plot([r["time_s"] for r in rows], [r[field] * scale for r in rows], color=color, linewidth=1.35, label=label)
        ax.set_title(title)
        ax.set_xlabel("Saved native time (s)")
        ax.set_ylabel(ylabel)
        ax.set_xlim(0.0, 5.0)
        ax.grid(True, alpha=0.24)
        ax.legend(frameon=False, loc="best", fontsize=8)
    fig.text(0.5, 0.025, "Shading marks 2–5 s; late variation is measured from t=2 s. A single run is not a success threshold.", ha="center", fontsize=8.5)
    fig.tight_layout(rect=(0.0, 0.07, 1.0, 0.91), w_pad=2.5)
    figure = OUT / "joint_only_fixed_strap_timeseries.png"
    fig.savefig(figure, dpi=180)
    plt.close(fig)

    after = seal_paths(analysis, snapshot)
    producer_after = sha256(A / "make_joint_only_fixed_strap_artifacts.py")
    if before != after or producer_before != producer_after:
        raise RuntimeError("producer or sealed inputs changed during render")
    manifest = {
        "producer": str(A / "make_joint_only_fixed_strap_artifacts.py"),
        "producer_sha256": producer_before,
        "inputs_sha256_before": before,
        "inputs_sha256_after": after,
        "outputs_sha256": {figure.name: sha256(figure)},
        "native_calls": 0,
        "physics_steps": 0,
        "actor_inference_calls": 0,
        "training_updates": 0,
        "figure": figure.name,
        "scope": "saved native guitar position/rotation traces only; no new native run, actor, or training",
    }
    (OUT / "artifact_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"figure": str(figure), "outputs_sha256": manifest["outputs_sha256"], "sealed_input_count": len(before)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
