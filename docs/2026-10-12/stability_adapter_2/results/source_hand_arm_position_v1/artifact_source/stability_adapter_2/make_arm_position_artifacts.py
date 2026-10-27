#!/usr/bin/env python3
"""Create the frozen source-only arm-position comparison figure."""

import hashlib
import json
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D


ROOT = Path("/home/ajou/yigyu/3")
PHASE = ROOT / "docs/2026-10-12/stability_adapter_2/results/source_hand_arm_position_v1"
ARTIFACTS = PHASE / "artifacts"
SEARCH = PHASE / "search.json"
ANALYSIS = PHASE / "analysis.json"
SEARCH_EXEC = PHASE / "search_execution.json"
ANALYSIS_EXEC = PHASE / "analysis_execution.json"
SEARCH_MANIFEST = PHASE / "search_source_manifest.json"
ANALYSIS_MANIFEST = PHASE / "analysis_source_manifest.json"
INVOCATION = PHASE / "analysis_invocation.json"
PLAN = ROOT / "stability_adapter_2/SOURCE_HAND_ARM_POSITION_PLAN.md"
EXEC_PLAN = ROOT / "stability_adapter_2/ARM_POSITION_EXECUTION.md"
ANALYZER = ROOT / "stability_adapter_2/analyze_arm_position.py"
SEARCHER = ROOT / "stability_adapter_2/search_arm_position.py"
PRODUCER = ROOT / "stability_adapter_2/make_arm_position_artifacts.py"
WRAPPER = ARTIFACTS / "run_producer.sh"

DIRECT_INPUTS = [
    SEARCH,
    ANALYSIS,
    SEARCH_EXEC,
    ANALYSIS_EXEC,
    SEARCH_MANIFEST,
    ANALYSIS_MANIFEST,
    INVOCATION,
    PLAN,
    EXEC_PLAN,
    ANALYZER,
    SEARCHER,
]
DELTAS = [-0.05, -0.025, 0.025, 0.05]
SEEDS = [0.0, -0.1]
JOINTS = ["L_Thorax", "L_Shoulder", "L_Elbow"]
AXES = ["x", "y", "z"]


def sha256(path):
    digest = hashlib.sha256()
    with open(str(path), "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_hashes(paths):
    return {str(path): sha256(path) for path in paths}


def load_json(path):
    with open(str(path), "r", encoding="utf-8") as stream:
        return json.load(stream)


def write_json(path, value):
    with open(str(path), "w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")


def main():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    output_png = ARTIFACTS / "arm_source_geometry.png"
    manifest_path = ARTIFACTS / "manifest.json"
    if output_png.exists() or manifest_path.exists():
        raise RuntimeError("refusing to overwrite frozen artifact outputs")

    analysis = load_json(ANALYSIS)
    closure_before = analysis.get("input_sha256_before", {})
    if not isinstance(closure_before, dict) or len(closure_before) != 76:
        raise ValueError("analysis input closure count does not match the sealed 76 inputs")
    input_paths = sorted(set(DIRECT_INPUTS + [Path(path) for path in closure_before] + [PRODUCER, WRAPPER]), key=str)
    before = file_hashes(input_paths)
    search = load_json(SEARCH)
    search_exec = load_json(SEARCH_EXEC)
    analysis_exec = load_json(ANALYSIS_EXEC)

    if not all(search.get("checks", {}).values()) or len(search.get("checks", {})) != 9:
        raise ValueError("search contract must contain nine passing checks")
    if not all(analysis.get("checks", {}).values()) or len(analysis.get("checks", {})) != 11:
        raise ValueError("analysis contract must contain eleven passing checks")
    if search_exec.get("exit_code") != 0 or analysis_exec.get("exit_code") != 0:
        raise ValueError("source-search and analysis executions must both exit zero")
    if search_exec.get("input_sha256_before") != search_exec.get("input_sha256_after"):
        raise ValueError("source-search inputs changed during execution")
    if analysis_exec.get("input_sha256_before") != analysis_exec.get("input_sha256_after"):
        raise ValueError("analysis inputs changed during execution")
    if analysis.get("input_sha256_before") != analysis.get("input_sha256_after"):
        raise ValueError("analysis closure changed during analysis")
    for path, expected in closure_before.items():
        if not Path(path).is_file() or sha256(path) != expected:
            raise ValueError("analysis closure input differs from its saved SHA: " + path)
    if len(search.get("rows", [])) != 74 or len(analysis.get("rows", [])) != 74:
        raise ValueError("expected exactly 74 source proposal rows")
    if search.get("selected") is not None:
        raise ValueError("source phase unexpectedly selected a proposal")
    if analysis.get("native_initializations") != 0 or analysis.get("physics_steps") != 0:
        raise ValueError("source-only analysis must report zero native work")

    search_rows = search["rows"]
    analysis_rows = analysis["rows"]
    if [row["order"] for row in search_rows] != [row["order"] for row in analysis_rows]:
        raise ValueError("search and analysis row order differs")
    values = {}
    excluded = {}
    for raw, measured in zip(search_rows, analysis_rows):
        seed = float(raw["seed_wrist_y_rad"])
        key = (seed, raw.get("joint"), float(raw["requested_delta_rad"]))
        if raw["source_evaluated"] != measured["source_evaluated"]:
            raise ValueError("search and analysis source-evaluated flags differ")
        if raw["source_evaluated"]:
            intersections = raw.get("source_human_guitar_intersections")
            if not isinstance(intersections, list) or not intersections:
                raise ValueError("evaluated rows must preserve their reported HG intersections")
            max_radius_mm = max(float(pair["common_radius_m"]) for pair in intersections) * 1000.0
            recorded = float(measured["max_HG_common_radius_mm"])
            if not np.isclose(max_radius_mm, recorded, rtol=0.0, atol=1e-9):
                raise ValueError("raw HG maximum does not match the analyzed row")
            values[key] = max_radius_mm
        else:
            if raw.get("source_clear") is not False or not raw.get("numeric_violations"):
                raise ValueError("excluded proposal must be explicit and retain its numeric violations")
            if raw.get("source_human_guitar_intersections") is not None:
                raise ValueError("excluded proposal must not be represented as evaluated geometry")
            excluded[key] = raw["numeric_violations"]

    if len(values) != 68 or len(excluded) != 6:
        raise ValueError("expected 68 measured geometry rows and six range exclusions")
    for seed in SEEDS:
        seed_rows = [row for row in search_rows if float(row["seed_wrist_y_rad"]) == seed]
        if len(seed_rows) != 37:
            raise ValueError("each seed must retain its baseline plus 36 requested proposals")
    expected_best = {"0.0": 2.212092533120751, "-0.1": 1.2315757769876514}
    for seed_string, expected in expected_best.items():
        seed = float(seed_string)
        best = min(value for (row_seed, _, _), value in values.items() if row_seed == seed)
        if not np.isclose(best, expected, rtol=0.0, atol=1e-9):
            raise ValueError("best geometry value differs from the approved analysis")

    all_values = list(values.values())
    y_max = max(all_values) * 1.16
    colors = {0.0: "#2864a5", -0.1: "#d87524"}
    fig, axes = plt.subplots(3, 3, figsize=(14.2, 10.0), sharex=True, sharey=True)
    fig.suptitle("Source-only arm-position sweep: maximum human–guitar LP radius", fontsize=16, y=0.982)
    legend_handles = []
    for seed in SEEDS:
        label = "Wrist seed 0 rad" if seed == 0.0 else "Wrist seed −0.1 rad"
        legend_handles.append(Line2D([0], [0], color=colors[seed], marker="o", lw=2, label=label))
        legend_handles.append(Line2D([0], [0], color=colors[seed], lw=1.5, ls="--", label=label + " baseline"))

    for row_index, body in enumerate(JOINTS):
        for col_index, axis in enumerate(AXES):
            ax = axes[row_index, col_index]
            joint = body + "_" + axis
            for seed in SEEDS:
                baseline_key = (seed, None, 0.0)
                baseline = values[baseline_key]
                points = []
                for delta in DELTAS:
                    key = (seed, joint, delta)
                    points.append(values.get(key, np.nan))
                ax.plot(DELTAS, points, color=colors[seed], marker="o", lw=1.8, ms=4.5)
                ax.axhline(baseline, color=colors[seed], lw=1.2, ls="--", alpha=0.8)

            tick_labels = ["−.05", "−.025", "+.025", "+.05"]
            for idx, delta in enumerate(DELTAS):
                key0 = (0.0, joint, delta)
                key1 = (-0.1, joint, delta)
                if key0 in excluded and key1 in excluded:
                    tick_labels[idx] += "†"
            ax.set_xticks(DELTAS)
            ax.set_xticklabels(tick_labels, fontsize=8)
            ax.set_title(body.replace("L_", "") + " · " + axis.upper(), fontsize=11)
            ax.set_xlim(-0.061, 0.061)
            ax.set_ylim(0.0, y_max)
            ax.grid(axis="y", color="#dddddd", linewidth=0.7)
            if col_index == 0:
                ax.set_ylabel("Max HG common radius (mm)")
            if row_index == 2:
                ax.set_xlabel("Requested joint delta (rad)")

    fig.legend(handles=legend_handles, loc="upper center", bbox_to_anchor=(0.5, 0.947), ncol=4, frameon=False, fontsize=9)
    fig.text(
        0.5,
        0.025,
        "† Numeric range exclusion in both seeds; excluded proposals are omitted, never plotted as zero.\n"
        "Dashed lines are each seed's source baseline. Values are maximum common inscribed LP radii over reported human–guitar pairs.\n"
        "Static saved-source geometry only; LP radii are not PhysX penetration depth, cooked contact, or stability evidence.",
        ha="center",
        va="bottom",
        fontsize=9,
    )
    fig.tight_layout(rect=(0.04, 0.11, 0.99, 0.90))
    fig.savefig(str(output_png), dpi=190, bbox_inches="tight")
    plt.close(fig)

    after = file_hashes(input_paths)
    if before != after:
        raise RuntimeError("a direct input changed while producing the artifact")
    if sha256(PRODUCER) != os.environ.get("ARM_POSITION_PRODUCER_SHA256"):
        raise RuntimeError("producer source SHA changed after wrapper snapshot")
    outputs = {output_png.name: sha256(output_png)}
    write_json(
        manifest_path,
        {
            "producer_sha256_before": os.environ["ARM_POSITION_PRODUCER_SHA256"],
            "producer_sha256_after": sha256(PRODUCER),
            "inputs_sha256_before": before,
            "inputs_sha256_after": after,
            "outputs_sha256": outputs,
            "source_rows": {"proposals": 74, "evaluated": 68, "range_excluded": 6},
            "native_calls": 0,
            "physics_steps": 0,
            "actor_inference_calls": 0,
            "training_updates": 0,
        },
    )


if __name__ == "__main__":
    main()
