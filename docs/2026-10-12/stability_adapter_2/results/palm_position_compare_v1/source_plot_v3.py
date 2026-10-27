#!/usr/bin/env python3
"""Plot saved palm-position controller comparisons; never runs physics."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


MODES = ("PI", "RATE_PI", "PALM_RATE")
UPDATE_STEPS = (1, 5, 9, 13, 17, 21)
COLORS = {"PI": "#2563a6", "RATE_PI": "#d97706", "PALM_RATE": "#16835d"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text())


def target_updates(report, controls):
    indices = report["arm_indices"]
    previous = np.asarray(report["initial_joint_targets_rad"], dtype=float)[indices]
    times, changes = [], []
    updates = [c for c in controls if c["updated_before_step"]]
    if [c["physics_step"] for c in updates] != list(UPDATE_STEPS):
        raise ValueError("expected the six saved 60 Hz target updates")
    for control in updates:
        current = np.asarray(control["final_arm_targets_rad"], dtype=float)
        if current.shape != previous.shape:
            raise ValueError("delivered target vector does not match arm index vector")
        times.append((control["physics_step"] - 1) / 240.0)
        changes.append(float(np.max(np.abs(current - previous))))
        previous = current
    return times, changes


def load_data(results: Path):
    comparison_path = results / "comparison.json"
    comparison = read_json(comparison_path)
    checks = comparison.get("checks", {})
    if len(checks) != 5 or not all(checks.values()):
        raise ValueError("comparison must have five passing contract checks")
    if [row.get("mode") for row in comparison.get("rows", [])] != list(MODES):
        raise ValueError("comparison rows do not match expected modes")
    expected_hashes = comparison.get("input_sha256", {})
    if len(expected_hashes) != 103:
        raise ValueError("expected 103 embedded input SHA entries")
    for name, expected in expected_hashes.items():
        source = Path(name)
        if not source.is_file() or sha256(source) != expected:
            raise ValueError(f"comparison input SHA mismatch: {source}")
    exact_guitar = comparison.get("all_saved_guitar_body_states_exactly_equal_to_PI", {})
    if set(exact_guitar) != set(MODES[1:]) or not all(exact_guitar.values()):
        raise ValueError("saved guitar states are not verified as exactly equal")

    series = {}
    consumed = [comparison_path]
    for mode in MODES:
        run = results / mode
        paths = {name: run / f"{name}.json" for name in ("report", "trace", "queries", "controls")}
        raw = {name: read_json(path) for name, path in paths.items()}
        report, trace, queries, controls = (raw[n] for n in ("report", "trace", "queries", "controls"))
        if not all(report["checks"].values()) or len(trace) != 25 or len(queries) != 25 or len(controls) != 24:
            raise ValueError(f"saved {mode} run contract/record count mismatch")
        if [q["physics_step"] for q in queries] != list(range(25)) or \
                [t["time_s"] for t in trace] != [i / 240.0 for i in range(25)] or \
                [q["time_s"] for q in queries] != [i / 240.0 for i in range(25)]:
            raise ValueError(f"saved {mode} query steps are not 0..24")
        target_updates(report, controls)
        series[mode] = {**raw, "paths": paths}
        consumed.extend(paths.values())

    # Exact coincidence is checked from the saved trace arrays, not inferred from rounded maxima.
    reference = series["PI"]["trace"]
    for mode in MODES[1:]:
        other = series[mode]["trace"]
        if [r["position_error_m"] for r in other] != [r["position_error_m"] for r in reference] or \
                [r["rotation_error_deg"] for r in other] != [r["rotation_error_deg"] for r in reference]:
            raise ValueError("guitar position/rotation traces are not exactly coincident")
    return comparison_path, comparison, series, consumed


def plot(data, output: Path):
    fig, axes = plt.subplots(2, 2, figsize=(12.5, 8.1))
    for mode in MODES:
        run = data[mode]
        queries, trace, controls, report = (run[n] for n in ("queries", "trace", "controls", "report"))
        color = COLORS[mode]
        times = np.asarray([q["time_s"] for q in queries])
        palm_mm = np.asarray([
            np.linalg.norm(np.asarray(q["left_source_world_m"]) - np.asarray(q["palm_goal_world_m"])) * 1000
            for q in queries
        ])
        axes[0, 0].plot(times, palm_mm, color=color, marker="o", ms=3.2, lw=1.5, label=mode)
        axes[0, 1].plot(times, [s["position_error_m"] * 1000 for s in trace],
                         color=color, marker=".", ms=3.5, lw=1.4, label=mode)
        axes[1, 0].plot(times, [s["rotation_error_deg"] for s in trace],
                         color=color, marker=".", ms=3.5, lw=1.4, label=mode)

        update_times, changes = target_updates(report, controls)
        axes[1, 1].scatter(update_times, changes, color=color, marker={"PI": "o", "RATE_PI": "s", "PALM_RATE": "^"}[mode],
                           s=34, label=mode, zorder=3)

    axes[0, 0].set(title="Left source center to palm goal", ylabel="Distance (mm)")
    axes[0, 1].set(title="Guitar position error", ylabel="Error (mm)")
    axes[1, 0].set(title="Guitar rotation error", ylabel="Error (degrees)")
    axes[1, 1].set(title="Maximum arm-target change at updates", ylabel="Max |Δ target| (rad)")
    axes[1, 1].set_xticks(np.arange(0, .101, 1/60), labels=[f"{i/60:.3f}" for i in range(7)], rotation=35)
    for ax in axes.flat:
        ax.set_xlabel("Time (s)")
        ax.grid(True, alpha=.24)
        ax.legend(frameon=False, fontsize=8)
    fig.suptitle("Saved 0.1 s palm-position comparison — three diagnostic modes", y=.99)
    fig.text(.5, .012,
             "Guitar position/rotation traces are exactly coincident across all three modes; no visual offset is applied.",
             ha="center", fontsize=9)
    fig.tight_layout(rect=(0, .04, 1, .96), h_pad=2.0, w_pad=1.7)
    fig.savefig(output, dpi=170, bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()
    out = args.out_dir.resolve()
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"refusing to overwrite nonempty output directory: {out}")
    comparison_path, comparison, series, consumed = load_data(args.results_dir.resolve())
    out.mkdir(parents=True, exist_ok=True)
    image = out / "palm_position_compare.png"
    plot(series, image)
    manifest = {
        "scope": "saved 0.1 s data visualization only; no native query or run",
        "comparison": {"path": str(comparison_path), "sha256": sha256(comparison_path),
                       "checks": comparison["checks"]},
        "embedded_source_sha256": comparison["input_sha256"],
        "consumed_json_sha256": {str(p.resolve()): sha256(p) for p in consumed},
        "plotter": {"path": str(Path(__file__).resolve()), "sha256": sha256(Path(__file__).resolve())},
        "outputs": {image.name: {"path": str(image), "sha256": sha256(image)}},
        "derivations": {
            "left_source_goal_mm": "1000 * norm(queries.left_source_world_m - queries.palm_goal_world_m)",
            "target_change": "max abs change across delivered arm target vector at six updated_before_step controls; initial baseline is report.initial_joint_targets_rad[arm_indices]",
            "target_update_time_s": "(physics_step - 1) / 240",
            "guitar_error": "trace.position_error_m * 1000 and trace.rotation_error_deg",
        },
    }
    (out / "plot_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
