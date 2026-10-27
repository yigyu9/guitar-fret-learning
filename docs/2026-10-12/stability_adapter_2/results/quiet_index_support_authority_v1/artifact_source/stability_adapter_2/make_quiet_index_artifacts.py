#!/usr/bin/env python3
"""Plot the saved quiet index-support trials and baseline without simulation."""

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
PHASE = DATA / "results/quiet_index_support_authority_v1"
ARTIFACTS = PHASE / "artifacts"
ANALYSIS = PHASE / "analysis.json"
SERIES = PHASE / "series.json"
ANALYZER = ROOT / "stability_adapter_2/analyze_quiet_index_support_v2.py"
RUNNER = ROOT / "stability_adapter_2/run_quiet_index_support.py"
PHASE_RUNNER = ROOT / "stability_adapter_2/run_quiet_index_support_phase.py"
PLAN = ROOT / "stability_adapter_2/QUIET_INDEX_SUPPORT_AUTHORITY_PLAN.md"
LEAF = ROOT / "stability_adapter_2/QUIET_INDEX_SUPPORT_EXECUTION.md"
RETRY_LEAF = ROOT / "stability_adapter_2/QUIET_INDEX_NATIVE_RETRY_V2.md"
CRASH_RECORD = PHASE / "minus_native_crash.json"
PRODUCER = ROOT / "stability_adapter_2/make_quiet_index_artifacts.py"
WRAPPER = ARTIFACTS / "run_producer.sh"
OUTPUT = ARTIFACTS / "quiet_index_support_response.png"
MANIFEST = ARTIFACTS / "manifest.json"
LABELS = ["baseline", "plus", "minus"]
COLORS = {"baseline": "#555b66", "plus": "#2a7f62", "minus": "#c36a2d"}


def sha256(path):
    digest = hashlib.sha256()
    with open(str(path), "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path):
    with open(str(path), "r", encoding="utf-8") as stream:
        return json.load(stream)


def write_json(path, value):
    with open(str(path), "w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")


def main():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    if OUTPUT.exists() or MANIFEST.exists():
        raise RuntimeError("refusing to overwrite the frozen plot or output manifest")

    analysis = read_json(ANALYSIS)
    series = read_json(SERIES)
    checks = analysis.get("checks", {})
    if not checks or not all(checks.values()):
        raise ValueError("saved analysis must contain only passing checks")
    if set(series) != set(LABELS):
        raise ValueError("series must contain baseline, plus, and minus")
    if (analysis.get("physical_initializations") != 3 or
            analysis.get("completed_trial_physics_steps") != 2400 or
            analysis.get("failed_trial_steps_observed") != 152 or
            analysis.get("total_physics_steps_observed") != 2552):
        raise ValueError("analysis must describe the preserved failed attempt and two completed trials")
    if analysis.get("actor_inference_calls") != 0 or analysis.get("training_updates") != 0:
        raise ValueError("this phase must not include actor inference or training")

    closure = analysis.get("input_sha256_before", {})
    if not closure or closure != analysis.get("input_sha256_after"):
        raise ValueError("analysis inputs must have unchanged before/after hashes")
    input_paths = sorted(
        set([Path(path) for path in closure] + [ANALYSIS, SERIES, ANALYZER, RUNNER, PHASE_RUNNER, PLAN, LEAF, RETRY_LEAF, CRASH_RECORD, PRODUCER, WRAPPER]),
        key=str,
    )
    before = {str(path): sha256(path) for path in input_paths}
    for path, expected in closure.items():
        if not Path(path).is_file() or sha256(path) != expected:
            raise ValueError("analysis closure source changed: " + path)

    times = {}
    actual = {}
    targets = {}
    positions = {}
    for label in LABELS:
        row = series[label]
        time = np.asarray(row["time_s"], dtype=float)
        actual_q = np.asarray(row["index3_actual_rad"], dtype=float)
        target_q = np.asarray(row["index3_target_rad"], dtype=float)
        if len(time) != 1201 or len(actual_q) != 1201 or len(target_q) != 1200:
            raise ValueError("expected 1201 actual state samples and 1200 post-step targets")
        if not np.array_equal(time, np.arange(1201, dtype=float) / 240.0):
            raise ValueError("state series must use the recorded 240 Hz time grid")
        if not np.isfinite(actual_q).all() or not np.isfinite(target_q).all():
            raise ValueError("index3 angle series must be finite")
        p = np.asarray(row["position_W_m"], dtype=float)
        q = np.asarray(row["quaternion_xyzw"], dtype=float)
        if p.shape != (1201, 3) or q.shape != (1201, 4) or not np.isfinite(p).all() or not np.isfinite(q).all():
            raise ValueError("world pose series must contain 1201 finite position/quaternion samples")
        qnorm = np.linalg.norm(q, axis=1)
        if not np.allclose(qnorm, 1.0, rtol=0.0, atol=1e-8):
            raise ValueError("quaternion series must be normalized")
        times[label] = time
        actual[label] = actual_q
        targets[label] = target_q
        positions[label] = p

    base_time = times["baseline"]
    position_error = {label: np.asarray(series[label]["position_error_mm"], dtype=float) for label in LABELS}
    rotation_error = {label: np.asarray(series[label]["rotation_error_deg"], dtype=float) for label in LABELS}
    for label in LABELS:
        if position_error[label].shape != (1201,) or rotation_error[label].shape != (1201,):
            raise ValueError("goal error series must contain 1201 samples")
        if not np.isfinite(position_error[label]).all() or not np.isfinite(rotation_error[label]).all():
            raise ValueError("goal error series must be finite")
        if not np.array_equal(times[label], base_time):
            raise ValueError("all trials must share the same physical time grid")

    fig, axes = plt.subplots(2, 2, figsize=(14.0, 9.4))
    ax_p, ax_r, ax_index, ax_baseline = axes.ravel()
    fig.suptitle("Quiet index3 target-ramp response: saved native trials", fontsize=15, y=0.975)

    for label in LABELS:
        time = times[label]
        ax_p.plot(time, position_error[label], color=COLORS[label], lw=1.8, label=label)
        ax_r.plot(time, rotation_error[label], color=COLORS[label], lw=1.8, label=label)
    ax_p.set_title("Guitar position error from initial world goal")
    ax_p.set_ylabel("Position error (mm)")
    ax_r.set_title("Guitar rotation error from initial world goal")
    ax_r.set_ylabel("Rotation error (deg)")

    for label in LABELS:
        time = times[label]
        ax_index.plot(time, actual[label], color=COLORS[label], lw=1.5, label=label + " actual")
        # Targets are logged after their physics step; target[0] belongs to state time 1/240 s.
        target_time = np.arange(1, 1201, dtype=float) / 240.0
        ax_index.plot(target_time, targets[label], color=COLORS[label], lw=1.0, ls="--", alpha=0.75, label=label + " target")
    ax_index.set_title("LH:index3 actual angle and post-step PD target")
    ax_index.set_ylabel("Angle (rad)")
    ax_index.set_xlabel("Time (s)")

    for label in ["plus", "minus"]:
        dp = np.linalg.norm(positions[label] - positions["baseline"], axis=1) * 1000.0
        ax_baseline.plot(base_time, dp, color=COLORS[label], lw=1.8, label=label + " vs baseline")
    ax_baseline.axhline(0.0, color=COLORS["baseline"], lw=1.0, ls="--", alpha=0.7)
    ax_baseline.set_title("World guitar position difference from baseline")
    ax_baseline.set_ylabel("Position difference (mm)")
    ax_baseline.set_xlabel("Time (s)")

    for ax in axes.ravel():
        ax.set_xlim(0.0, 5.0)
        ax.set_xlabel(ax.get_xlabel() or "Time (s)")
        ax.grid(color="#dddddd", linewidth=0.7)
    ax_index.legend(loc="upper right", fontsize=7.5, ncol=2, frameon=True)
    legend_handles = [
        Line2D([0], [0], color=COLORS[label], lw=1.8, label=label)
        for label in LABELS
    ]
    fig.legend(handles=legend_handles, loc="upper center", bbox_to_anchor=(0.5, 0.925), ncol=3, frameon=False)
    fig.text(
        0.5,
        0.018,
        "Saved Isaac Gym data: actual index3 angles use 1201 states at t=k/240 s; the 1200 post-step targets are aligned at t=1..1200/240 s.\n"
        "Commands are held at 60 Hz between control updates.\n"
        "Lower-right is world-position distance from the saved baseline. These traces describe this diagnostic only; they do not certify natural playing or policy compatibility.",
        ha="center",
        va="bottom",
        fontsize=8.5,
    )
    fig.tight_layout(rect=(0.045, 0.085, 0.99, 0.875))
    fig.savefig(str(OUTPUT), dpi=180, bbox_inches="tight")
    plt.close(fig)

    after = {str(path): sha256(path) for path in input_paths}
    if before != after:
        raise RuntimeError("an input changed during plot generation")
    producer_sha = sha256(PRODUCER)
    if producer_sha != os.environ.get("QUIET_INDEX_PRODUCER_SHA256"):
        raise RuntimeError("producer SHA differs from the pre-run source snapshot")
    write_json(
        MANIFEST,
        {
            "producer_sha256_before": os.environ["QUIET_INDEX_PRODUCER_SHA256"],
            "producer_sha256_after": producer_sha,
            "inputs_sha256_before": before,
            "inputs_sha256_after": after,
            "outputs_sha256": {OUTPUT.name: sha256(OUTPUT)},
            "native_calls": 0,
            "physics_steps": 0,
            "actor_inference_calls": 0,
            "training_updates": 0,
        },
    )


if __name__ == "__main__":
    main()
