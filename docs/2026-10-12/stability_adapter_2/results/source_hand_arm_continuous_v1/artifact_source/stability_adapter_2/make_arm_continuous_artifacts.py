#!/usr/bin/env python3
"""Render progress for the saved bounded arm-source evaluations."""

import hashlib
import json
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


ROOT = Path("/home/ajou/yigyu/3")
PHASE = ROOT / "docs/2026-10-12/stability_adapter_2/results/source_hand_arm_continuous_v1"
ARTIFACTS = PHASE / "artifacts"
SEARCH = PHASE / "search.json"
EVALUATIONS = PHASE / "evaluations.jsonl"
SEARCH_EXEC = PHASE / "search_execution.json"
SEARCH_MANIFEST = PHASE / "search_source_manifest.json"
ANALYSIS_V2 = PHASE / "analysis_v2.json"
ANALYSIS_EXEC = PHASE / "analysis_v2_execution.json"
ANALYSIS_V2_MANIFEST = PHASE / "analysis_v2_source_manifest.json"
ANALYSIS_FAILURE = PHASE / "analysis_failure.json"
ANALYSIS_INVOCATION = PHASE / "analysis_invocation.json"
ANALYSIS_OLD_MANIFEST = PHASE / "analysis_source_manifest.json"
ANALYSIS_V2_INVOCATION = PHASE / "analysis_v2_invocation.json"
PLAN = ROOT / "stability_adapter_2/SOURCE_HAND_ARM_CONTINUOUS_PLAN.md"
EXECUTION_LEAF = ROOT / "stability_adapter_2/ARM_CONTINUOUS_EXECUTION.md"
ANALYSIS_LEAF = ROOT / "stability_adapter_2/ARM_CONTINUOUS_ANALYSIS_V2.md"
NEXT_PLAN = ROOT / "stability_adapter_2/QUIET_INDEX_SUPPORT_AUTHORITY_PLAN.md"
SEARCHER = ROOT / "stability_adapter_2/search_arm_continuous.py"
FAILED_ANALYZER = ROOT / "stability_adapter_2/analyze_arm_continuous.py"
ANALYZER_V2 = ROOT / "stability_adapter_2/analyze_arm_continuous_v2.py"
PRODUCER = ROOT / "stability_adapter_2/make_arm_continuous_artifacts.py"
WRAPPER = ARTIFACTS / "run_producer.sh"
OUTPUT = ARTIFACTS / "arm_continuous_progress.png"
MANIFEST = ARTIFACTS / "manifest.json"


def sha256(path):
    digest = hashlib.sha256()
    with open(str(path), "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path):
    with open(str(path), "r", encoding="utf-8") as stream:
        return json.load(stream)


def write_json(path, value):
    with open(str(path), "w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")


def maximum_hg_mm(row):
    pairs = row.get("source_human_guitar_intersections")
    if not isinstance(pairs, list) or not pairs:
        raise ValueError("every evaluated source row must retain at least one HG pair")
    return max(float(pair["common_radius_m"]) for pair in pairs) * 1000.0


def main():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    if OUTPUT.exists() or MANIFEST.exists():
        raise RuntimeError("refusing to overwrite frozen progress plot or manifest")

    search = load_json(SEARCH)
    analysis = load_json(ANALYSIS_V2)
    search_exec = load_json(SEARCH_EXEC)
    analysis_exec = load_json(ANALYSIS_EXEC)
    failure = load_json(ANALYSIS_FAILURE)
    old_invocation = load_json(ANALYSIS_INVOCATION)
    new_invocation = load_json(ANALYSIS_V2_INVOCATION)
    before_expected = analysis.get("input_sha256_before", {})
    if len(before_expected) != 81 or before_expected != analysis.get("input_sha256_after"):
        raise ValueError("v2 analysis must preserve the saved 81-input closure")
    input_paths = sorted(
        set(
            [Path(path) for path in before_expected]
            + [
                SEARCH, EVALUATIONS, SEARCH_EXEC, SEARCH_MANIFEST,
                ANALYSIS_V2, ANALYSIS_EXEC, ANALYSIS_V2_MANIFEST,
                ANALYSIS_FAILURE, ANALYSIS_INVOCATION, ANALYSIS_OLD_MANIFEST,
                ANALYSIS_V2_INVOCATION, PLAN, EXECUTION_LEAF, ANALYSIS_LEAF,
                NEXT_PLAN, SEARCHER, FAILED_ANALYZER, ANALYZER_V2, PRODUCER, WRAPPER,
            ]
        ),
        key=str,
    )
    before = {str(path): sha256(path) for path in input_paths}

    if len(search.get("checks", {})) != 10 or not all(search["checks"].values()):
        raise ValueError("search source contract must have ten passing checks")
    if len(analysis.get("checks", {})) != 11 or not all(analysis["checks"].values()):
        raise ValueError("v2 analysis must have eleven passing checks")
    if search_exec.get("exit_code") != 0 or len(search_exec.get("input_sha256_before", {})) != 72:
        raise ValueError("source optimizer execution must be the preserved exit-zero 72-input run")
    if search_exec["input_sha256_before"] != search_exec["input_sha256_after"]:
        raise ValueError("source optimizer inputs changed during its run")
    if analysis_exec.get("exit_code") != 0:
        raise ValueError("corrected saved-data analysis must exit zero")
    if analysis_exec["input_sha256_before"] != analysis_exec["input_sha256_after"]:
        raise ValueError("v2 analyzer inputs changed during its run")
    if analysis_exec["input_sha256_before"] != before_expected:
        raise ValueError("v2 execution and analysis input closures differ")
    if search.get("selected") is not None or search.get("clear_count") != 0:
        raise ValueError("the approved source-only run must have no selected or clear row")
    if len(search.get("rows", [])) != 800 or len(analysis.get("rows", [])) != 800:
        raise ValueError("expected exactly 800 saved source evaluations")
    if search.get("native_initializations") != 0 or search.get("physics_steps") != 0:
        raise ValueError("saved optimizer results must report zero native dynamics")
    if analysis.get("native_initializations") != 0 or analysis.get("physics_steps") != 0:
        raise ValueError("v2 analysis must report zero native dynamics")
    if analysis.get("five_second_stability_measured") is not False:
        raise ValueError("five-second stability must remain unmeasured")
    if failure.get("first_mismatching_row") != 33 or old_invocation.get("producer_sha256") != failure.get("producer_sha256"):
        raise ValueError("preserved failed v1 analysis lineage does not match the recorded failure")
    if new_invocation.get("producer_sha256") != sha256(ANALYZER_V2):
        raise ValueError("v2 analyzer invocation SHA differs from its current source")

    for path, expected in before_expected.items():
        if not Path(path).is_file() or sha256(path) != expected:
            raise ValueError("v2 analysis closure no longer matches saved SHA: " + path)
    for path, expected in search_exec["input_sha256_before"].items():
        if not Path(path).is_file() or sha256(path) != expected:
            raise ValueError("search closure no longer matches saved SHA: " + path)

    if len(search.get("solves", [])) != 2:
        raise ValueError("expected two bounded Powell solves")
    for solve in search["solves"]:
        if solve.get("nfev") != 400 or solve.get("stored_evaluations") != 400 or solve.get("success") is not False or solve.get("status") != 1:
            raise ValueError("both Powell runs must explicitly end at the 400-evaluation budget")
        if "Maximum number of function evaluations" not in solve.get("message", ""):
            raise ValueError("optimizer terminal status is not the preserved maxfev termination")

    raw_rows = search["rows"]
    analyzed_rows = analysis["rows"]
    if [row["order"] for row in raw_rows] != [row["order"] for row in analyzed_rows]:
        raise ValueError("raw and v2 analyzed row orders differ")
    by_seed = {0: [], 1: []}
    seen = set()
    for raw, analyzed in zip(raw_rows, analyzed_rows):
        order = int(raw["order"])
        seed = int(raw["seed_id"])
        evaluation = int(raw["seed_evaluation"])
        if seed not in by_seed or evaluation < 0 or evaluation >= 400 or (seed, evaluation) in seen:
            raise ValueError("evaluation seed/index is invalid or duplicated")
        seen.add((seed, evaluation))
        if raw.get("source_evaluated") is not True or raw.get("source_clear") is not False:
            raise ValueError("expected every row to be evaluated and retain an HG intersection")
        if raw.get("source_cross_hand_intersections") is not None or raw.get("source_self_intersections") is not None or raw.get("self_pair_count") is not None:
            raise ValueError("cross-hand/self checks must remain unmeasured while HG overlaps")
        current = maximum_hg_mm(raw)
        if not abs(current - float(analyzed["max_HG_common_radius_mm"])) <= 1e-9:
            raise ValueError("recomputed raw HG maximum differs from v2 analysis")
        if int(analyzed["order"]) != order or int(analyzed["seed_id"]) != seed:
            raise ValueError("v2 row identity differs from search row")
        if not abs(float(raw["objective_value"]) - float(analyzed["objective_value"])) <= 1e-9:
            raise ValueError("objective values differ between raw and v2 analysis")
        by_seed[seed].append((evaluation + 1, current, order, analyzed))
    if len(by_seed[0]) != 400 or len(by_seed[1]) != 400 or len(seen) != 800:
        raise ValueError("expected exactly 400 evaluations per seed")
    for seed in [0, 1]:
        by_seed[seed].sort(key=lambda item: item[0])
        if [row[0] for row in by_seed[seed]] != list(range(1, 401)):
            raise ValueError("each plotted seed must contain evaluations 1 through 400")

    expected_best = {
        "0": {"objective_order": 398, "radius_order": 260, "radius_mm": 0.879617000239572},
        "1": {"objective_order": 798, "radius_order": 798, "radius_mm": 0.7834171165074373},
    }
    for seed_key, expected in expected_best.items():
        record = analysis["best_per_seed"][seed_key]
        if record["objective"]["order"] != expected["objective_order"] or record["max_HG"]["order"] != expected["radius_order"]:
            raise ValueError("best-row index differs from approved v2 summary")
        if not abs(float(record["max_HG"]["max_HG_common_radius_mm"]) - expected["radius_mm"]) <= 1e-9:
            raise ValueError("best-so-far HG radius differs from approved v2 summary")

    eval_lines = [json.loads(line) for line in EVALUATIONS.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(eval_lines) != 800 or [row["order"] for row in eval_lines] != [row["order"] for row in raw_rows]:
        raise ValueError("evaluations.jsonl does not match the 800 saved search rows")

    all_values = [entry[1] for entries in by_seed.values() for entry in entries]
    y_limit = max(all_values) * 1.12
    colors = {0: "#2d6a9f", 1: "#d1782c"}
    fig, axes = plt.subplots(1, 2, figsize=(14.5, 7.5), sharey=True)
    fig.suptitle("Bounded arm-source search: HG radius over 400 evaluations per seed", fontsize=15, y=0.97)
    for seed, ax in zip([0, 1], axes):
        rows = by_seed[seed]
        x = [entry[0] for entry in rows]
        current = [entry[1] for entry in rows]
        best = []
        minimum = float("inf")
        for value in current:
            minimum = min(minimum, value)
            best.append(minimum)
        ax.plot(x, current, color=colors[seed], alpha=0.20, lw=0.8)
        ax.scatter(x, current, color=colors[seed], alpha=0.22, s=9, edgecolors="none")
        ax.plot(x, best, color=colors[seed], lw=2.8, label="Best-so-far: running minimum HG radius")
        title = "Seed 0: original pose" if seed == 0 else "Seed 1: Wrist_y −0.1 + Thorax_z +0.025 rad"
        ax.set_title(title, fontsize=12)
        ax.set_xlim(1, 400)
        ax.set_ylim(0, y_limit)
        ax.set_xticks([1, 100, 200, 300, 400])
        ax.set_xlabel("Evaluation index within seed (1–400)")
        ax.grid(color="#dddddd", linewidth=0.7)
    axes[0].set_ylabel("Maximum reported HG common radius (mm)")
    legend = [
        Line2D([0], [0], color="#666666", alpha=0.35, marker="o", lw=1.2, markersize=4, label="Current evaluation"),
        Line2D([0], [0], color=colors[0], lw=2.8, label="Seed 0 running minimum"),
        Line2D([0], [0], color=colors[1], lw=2.8, label="Seed 1 running minimum"),
    ]
    fig.legend(handles=legend, loc="upper center", bbox_to_anchor=(0.5, 0.915), ncol=3, frameon=False, fontsize=9)
    fig.text(
        0.5,
        0.025,
        "Faint points/line: current evaluation; bold line: best-so-far by maximum HG radius, not the weighted objective.\n"
        "Seed 0 weighted-objective best is row 398; its minimum HG radius is row 260. Both bounded Powell calls ended at maxfev=400, not convergence.\n"
        "All 800 rows retain HG overlap; cross/self were deferred and are unmeasured. Static source LP only: no selected candidate, native rollout, or 5 s stability test.",
        ha="center",
        va="bottom",
        fontsize=9,
    )
    fig.tight_layout(rect=(0.04, 0.13, 0.99, 0.86))
    fig.savefig(str(OUTPUT), dpi=190, bbox_inches="tight")
    plt.close(fig)

    after = {str(path): sha256(path) for path in input_paths}
    if before != after:
        raise RuntimeError("an input changed during artifact generation")
    producer_sha = sha256(PRODUCER)
    if producer_sha != os.environ.get("ARM_CONTINUOUS_PRODUCER_SHA256"):
        raise RuntimeError("producer SHA changed after pre-run snapshot")
    write_json(
        MANIFEST,
        {
            "producer_sha256_before": os.environ["ARM_CONTINUOUS_PRODUCER_SHA256"],
            "producer_sha256_after": producer_sha,
            "inputs_sha256_before": before,
            "inputs_sha256_after": after,
            "outputs_sha256": {OUTPUT.name: sha256(OUTPUT)},
            "evaluations": {"total": 800, "seed0": 400, "seed1": 400},
            "native_calls": 0,
            "physics_steps": 0,
            "actor_inference_calls": 0,
            "training_updates": 0,
        },
    )


if __name__ == "__main__":
    main()
