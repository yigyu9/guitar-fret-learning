#!/usr/bin/env python3
"""Plot saved wrist Y/Z feedback responses without running physics."""

import hashlib
import json
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np


ROOT = Path("/home/ajou/yigyu/3")
DATA = ROOT / "docs/2026-10-12/stability_adapter_2"
PHASE = DATA / "results/quiet_wrist_yz_feedback_v1"
ARTIFACTS = PHASE / "artifacts"
ANALYSIS = PHASE / "analysis.json"
SERIES = PHASE / "series.json"
ANALYZER = ROOT / "stability_adapter_2/analyze_quiet_wrist_yz_feedback.py"
RUNNER = ROOT / "stability_adapter_2/run_quiet_wrist_yz_feedback.py"
PHASE_RUNNER = ROOT / "stability_adapter_2/run_quiet_wrist_yz_feedback_phase.py"
FEEDBACK = ROOT / "stability_adapter_2/wrist_yz_guitar_feedback.py"
PLAN = ROOT / "stability_adapter_2/QUIET_WRIST_YZ_FEEDBACK_PLAN.md"
LEAF = ROOT / "stability_adapter_2/QUIET_WRIST_YZ_FEEDBACK_EXECUTION.md"
PRODUCER = ROOT / "stability_adapter_2/make_wrist_yz_feedback_artifacts.py"
WRAPPER = ARTIFACTS / "run_producer.sh"
OUTPUT = ARTIFACTS / "quiet_wrist_yz_feedback_response.png"
MANIFEST = ARTIFACTS / "manifest.json"
LABELS = ("baseline", "off", "on")
COLORS = {"baseline": "#555b66", "off": "#2678a5", "on": "#c36a2d"}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path):
    with Path(path).open("r", encoding="utf-8") as stream:
        return json.load(stream)


def write_json(path, value):
    with Path(path).open("w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")


def main():
    if OUTPUT.exists() or MANIFEST.exists():
        raise RuntimeError("refusing to overwrite existing feedback plot or manifest")

    analysis = read_json(ANALYSIS)
    series = read_json(SERIES)
    checks = analysis.get("checks", {})
    if not checks or not all(checks.values()):
        raise ValueError("saved analysis must contain only passing checks")
    if set(series) != set(LABELS):
        raise ValueError("series must contain baseline, off, and on")
    if analysis.get("physical_initializations") != 2 or analysis.get("physical_steps") != 2400:
        raise ValueError("analysis must describe two completed 1200-step trials")
    if analysis.get("actor_inference_calls") != 0 or analysis.get("training_updates") != 0:
        raise ValueError("this phase must not include actor inference or training")

    closure = analysis.get("input_sha256_before", {})
    if not closure or closure != analysis.get("input_sha256_after"):
        raise ValueError("analysis input closure must have matching before/after SHA maps")
    direct_inputs = [ANALYSIS, SERIES, ANALYZER, RUNNER, PHASE_RUNNER, FEEDBACK, PLAN, LEAF, PRODUCER, WRAPPER]
    input_paths = sorted(set([Path(path) for path in closure] + direct_inputs), key=str)
    before = {str(path): sha256(path) for path in input_paths}
    for path, expected in closure.items():
        if not Path(path).is_file() or sha256(path) != expected:
            raise ValueError("analysis closure input changed: " + path)

    times = {}
    position_errors = {}
    rotation_errors = {}
    positions = {}
    deltas = {}
    base_time = None
    for label in LABELS:
        row = series[label]
        time = np.asarray(row["time_s"], dtype=float)
        p_error = np.asarray(row["position_error_mm"], dtype=float)
        r_error = np.asarray(row["rotation_error_deg"], dtype=float)
        position = np.asarray(row["position_W_m"], dtype=float)
        quaternion = np.asarray(row["quaternion_xyzw"], dtype=float)
        support_actual = np.asarray(row["support_actual_rad"], dtype=float)
        support_target = np.asarray(row["support_target_rad"], dtype=float)
        if (time.shape != (1201,) or p_error.shape != (1201,) or r_error.shape != (1201,)
                or position.shape != (1201, 3) or quaternion.shape != (1201, 4)
                or support_actual.shape != (1201, 2) or support_target.shape != (1200, 2)):
            raise ValueError("expected 1201 state samples and 1200 post-step support targets")
        arrays = (time, p_error, r_error, position, quaternion, support_actual, support_target)
        if not all(np.isfinite(array).all() for array in arrays):
            raise ValueError("series fields must contain finite values")
        if not np.array_equal(time, np.arange(1201, dtype=float) / 240.0):
            raise ValueError("state samples must use t=k/240 s")
        if base_time is None:
            base_time = time
        elif not np.array_equal(time, base_time):
            raise ValueError("baseline/off/on must share the same recorded time grid")
        times[label] = time
        position_errors[label] = p_error
        rotation_errors[label] = r_error
        positions[label] = position
        if label != "baseline":
            delta = np.asarray(row["delta_rad"], dtype=float)
            if delta.shape != (1200, 2) or not np.isfinite(delta).all():
                raise ValueError("off/on delta_rad must contain 1200 finite Y/Z command samples")
            deltas[label] = delta

    fig, axes = plt.subplots(2, 2, figsize=(14.0, 9.4))
    ax_p, ax_r, ax_delta, ax_baseline = axes.ravel()
    fig.suptitle("Quiet guitar-position feedback OFF/ON response and saved baseline", fontsize=15, y=0.975)

    for label in LABELS:
        ax_p.plot(times[label], position_errors[label], color=COLORS[label], lw=1.7, label=label)
        ax_r.plot(times[label], rotation_errors[label], color=COLORS[label], lw=1.7, label=label)
    ax_p.set_title("Guitar position error from initial world goal")
    ax_p.set_ylabel("Position error (mm)")
    ax_r.set_title("Guitar rotation error from initial world goal")
    ax_r.set_ylabel("Rotation error (deg)")

    target_time = np.arange(1, 1201, dtype=float) / 240.0
    for label in ("off", "on"):
        ax_delta.plot(target_time, deltas[label][:, 0], color=COLORS[label], lw=1.6, ls="-", label=label + " ΔY")
        ax_delta.plot(target_time, deltas[label][:, 1], color=COLORS[label], lw=1.6, ls="--", label=label + " ΔZ")
    ax_delta.set_title("Feedback correction command after physics step")
    ax_delta.set_ylabel("Correction delta (rad)")
    ax_delta.set_xlabel("Time (s)")

    for label in ("off", "on"):
        distance_mm = np.linalg.norm(positions[label] - positions["baseline"], axis=1) * 1000.0
        ax_baseline.plot(times["baseline"], distance_mm, color=COLORS[label], lw=1.7, label=label + " vs baseline")
    ax_baseline.axhline(0.0, color=COLORS["baseline"], lw=1.0, ls=":", alpha=0.7)
    ax_baseline.set_title("World guitar position distance from saved baseline")
    ax_baseline.set_ylabel("Position distance (mm)")
    ax_baseline.set_xlabel("Time (s)")

    for ax in axes.ravel():
        ax.set_xlim(0.0, 5.0)
        ax.set_xlabel(ax.get_xlabel() or "Time (s)")
        ax.grid(color="#dddddd", linewidth=0.7)
    trial_handles = [Line2D([0], [0], color=COLORS[label], lw=1.8, label=label) for label in LABELS]
    axis_handles = [
        Line2D([0], [0], color="#333333", lw=1.6, ls="-", label="ΔY (solid)"),
        Line2D([0], [0], color="#333333", lw=1.6, ls="--", label="ΔZ (dashed)"),
    ]
    fig.legend(handles=trial_handles + axis_handles, loc="upper center", bbox_to_anchor=(0.5, 0.925), ncol=5, frameon=False)
    fig.text(
        0.5, 0.018,
        "Saved Isaac Gym data: position/rotation errors and world-position distances use 1201 states at t=k/240 s.\n"
        "Feedback ΔY/ΔZ commands are 1200 post-step samples at t=1..1200/240 s (60 Hz held updates); baseline is reused saved data.\n"
        "This is a data plot, not an Isaac Gym render or certification of natural playing or closed-loop stability.",
        ha="center", va="bottom", fontsize=8.3,
    )
    fig.tight_layout(rect=(0.045, 0.09, 0.99, 0.875))
    fig.savefig(str(OUTPUT), dpi=180, bbox_inches="tight")
    plt.close(fig)

    after = {str(path): sha256(path) for path in input_paths}
    if before != after:
        raise RuntimeError("an input changed during plot generation")
    producer_sha = sha256(PRODUCER)
    if producer_sha != os.environ.get("WRIST_YZ_FEEDBACK_PRODUCER_SHA256"):
        raise RuntimeError("producer SHA differs from the pre-run source snapshot")
    write_json(MANIFEST, {
        "producer_sha256_before": os.environ["WRIST_YZ_FEEDBACK_PRODUCER_SHA256"],
        "producer_sha256_after": producer_sha,
        "inputs_sha256_before": before,
        "inputs_sha256_after": after,
        "outputs_sha256": {OUTPUT.name: sha256(OUTPUT)},
        "native_calls": 0,
        "physics_steps": 0,
        "actor_inference_calls": 0,
        "training_updates": 0,
    })


if __name__ == "__main__":
    main()
