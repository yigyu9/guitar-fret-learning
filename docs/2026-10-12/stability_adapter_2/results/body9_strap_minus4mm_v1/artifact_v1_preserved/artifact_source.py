#!/usr/bin/env python3
"""Plot saved guitar errors and strap-law tension for three LA conditions."""
from __future__ import annotations

import hashlib
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = "/home/ajou/yigyu/3"
RESULTS = os.path.join(ROOT, "docs/2026-10-12/stability_adapter_2/results")
PHASE = os.path.join(RESULTS, "body9_strap_minus4mm_v1")
ARTIFACTS = os.path.join(PHASE, "artifacts")
ANALYSIS = os.path.join(PHASE, "analysis.json")
PLOT = os.path.join(ARTIFACTS, "body9_strap_minus4mm_comparison.png")
MANIFEST = os.path.join(ARTIFACTS, "artifact_manifest.json")

TRACES = {
    "Original LA": os.path.join(RESULTS, "small_wrist_motion_v1/native/trace.jsonl"),
    "LA −2 mm": os.path.join(RESULTS, "body9_strap_minus2mm_v1/native/trace.jsonl"),
    "LA −4 mm": os.path.join(PHASE, "native/trace.jsonl"),
}


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path):
    with open(path, "r", encoding="utf-8") as stream:
        return json.load(stream)


def read_jsonl(path):
    with open(path, "r", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def input_closure(producer):
    analysis = read_json(ANALYSIS)
    paths = set(analysis["input_sha256"])
    paths.update([ANALYSIS, producer] + list(TRACES.values()))
    before = {}
    for path in sorted(paths):
        require(os.path.isfile(path), "missing sealed input: " + path)
        before[path] = sha256(path)
    for path, expected in analysis["input_sha256"].items():
        require(before[path] == expected, "analysis input SHA mismatch: " + path)
    return analysis, before


def main():
    producer = os.path.abspath(__file__)
    require(not os.path.exists(PLOT) and not os.path.exists(MANIFEST),
            "artifact output exists; refusing to overwrite")
    os.makedirs(ARTIFACTS, exist_ok=True)
    analysis, before = input_closure(producer)
    require(len(analysis["checks"]) == 13 and all(analysis["checks"].values()),
            "analysis checks are incomplete or failed")
    require(len(analysis["summary"]) == 3 and
            [row["label"] for row in analysis["summary"]] ==
            ["baseline", "minus2mm", "minus4mm"],
            "analysis summary does not contain the expected three conditions")
    require(analysis["new_native_initializations"] == 1 and
            analysis["new_physics_steps"] == 1200,
            "saved run count differs from the one-run/1200-step brief")

    series = {}
    times = None
    for label, path in TRACES.items():
        rows = read_jsonl(path)
        require(len(rows) == 1201, label + " trace must contain t0 and 1200 steps")
        t = np.asarray([row["time_s"] for row in rows], dtype=float)
        require(np.isfinite(t).all() and np.all(np.diff(t) > 0), label + " time is invalid")
        if times is None:
            times = t
        else:
            require(np.array_equal(times, t), "comparison trace times differ")
        values = {
            "position": np.asarray([row["position_error_m"] for row in rows], dtype=float) * 1000.0,
            "rotation": np.asarray([row["rotation_error_deg"] for row in rows], dtype=float),
            "tension": np.asarray([row["last_applied_tension_n"] for row in rows], dtype=float),
        }
        require(all(np.isfinite(value).all() for value in values.values()), label + " has nonfinite plotted data")
        series[label] = values

    require(times.size == 1201 and abs(times[0]) < 1e-12 and abs(times[-1] - 5.0) < 1e-9,
            "comparison timeline is not 0–5 seconds at 1201 samples")

    plt.rcParams["font.family"] = "DejaVu Sans"
    colors = {"Original LA": "#333333", "LA −2 mm": "#3274a1", "LA −4 mm": "#d45b43"}
    fig, axes = plt.subplots(3, 1, figsize=(11.2, 10.4), sharex=True)
    fig.subplots_adjust(left=.12, right=.97, bottom=.09, top=.79, hspace=.28)
    for label in TRACES:
        axes[0].plot(times, series[label]["position"], color=colors[label], lw=1.8, label=label)
        axes[1].plot(times, series[label]["rotation"], color=colors[label], lw=1.8, label=label)
        axes[2].plot(times, series[label]["tension"], color=colors[label], lw=1.6, label=label)
    axes[0].set_ylabel("Position error (mm)")
    axes[1].set_ylabel("Rotation error (deg)")
    axes[2].set_ylabel("Last-applied tension (N)")
    axes[2].set_xlabel("Time (s)")
    for ax in axes:
        ax.grid(True, alpha=.24)
        ax.set_xlim(0, 5)
    fig.suptitle("Body-9 strap length comparison", fontsize=15, y=.98)
    fig.legend(loc="upper center", bbox_to_anchor=(.54, .91), ncol=3,
               frameon=False, fontsize=10)
    fig.text(.5, .025,
             "Trace fields: position_error_m × 1000; rotation_error_deg; last_applied_tension_n. "
             "Tension is the stored law value applied at the preceding step, not a continuous force measurement.",
             ha="center", va="bottom", fontsize=8.5, wrap=True)
    fig.savefig(PLOT, dpi=180, bbox_inches="tight")
    plt.close(fig)

    require(os.path.isfile(PLOT) and os.path.getsize(PLOT) > 1000, "PNG is missing or empty")
    analysis_after, after = input_closure(producer)
    require(before == after, "sealed input changed during plotting")
    require(analysis_after["checks"] == analysis["checks"], "analysis changed during plotting")
    manifest = {
        "schema": "body9-strap-minus4mm-artifacts-v1",
        "scope": "saved 1200-step traces; no native/physics execution",
        "producer": producer,
        "producer_sha256": after[producer],
        "input_sha256_before": before,
        "input_sha256_after": after,
        "outputs_sha256": {PLOT: sha256(PLOT)},
        "trace_rows": {label: 1201 for label in TRACES},
        "native_initializations_during_plotting": 0,
        "physics_steps_during_plotting": 0,
        "analysis_check_count": len(analysis["checks"]),
        "analysis_checks_all_true": True,
    }
    with open(MANIFEST, "x", encoding="utf-8") as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
