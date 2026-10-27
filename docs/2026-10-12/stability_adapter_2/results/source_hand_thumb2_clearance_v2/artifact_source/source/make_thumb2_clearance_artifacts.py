#!/usr/bin/env python3
"""Plot the saved seven-point static thumb2 source-LP sweep."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path("/home/ajou/yigyu/3")
PHASE = ROOT / "docs/2026-10-12/stability_adapter_2/results/source_hand_thumb2_clearance_v2"
ARTIFACTS = PHASE / "artifacts"
PRODUCER = ROOT / "stability_adapter_2/make_thumb2_clearance_artifacts.py"
INPUTS = [
    PHASE / "search.json",
    PHASE / "search_execution.json",
    PHASE / "search_source_manifest.json",
    PHASE / "search.log",
    ROOT / "docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/native/frames/hands/00000.png",
]
OUTPUT = ARTIFACTS / "thumb2_source_radius_sweep.png"


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    for path in [OUTPUT, ARTIFACTS / "manifest.json"]:
        if path.exists():
            raise SystemExit("refusing to overwrite existing artifact: " + str(path))
    input_before = {str(path): sha256(path) for path in INPUTS}
    producer_before = sha256(PRODUCER)

    data = json.loads(INPUTS[0].read_text())
    execution = json.loads(INPUTS[1].read_text())
    source_manifest = json.loads(INPUTS[2].read_text())
    checks = data.get("checks", {})
    if len(checks) != 8 or not all(checks.values()):
        raise ValueError("expected all eight saved search checks to pass")
    if data.get("selected") is not None:
        raise ValueError("the saved search must have no selected candidate")
    if execution.get("exit_code") != 0 or execution.get("terminal_state") != "completed":
        raise ValueError("saved source search execution did not complete successfully")
    before = execution.get("input_sha256_before", {})
    after = execution.get("input_sha256_after", {})
    if len(before) != 68 or len(after) != 68 or before != after:
        raise ValueError("expected an exact 68-input source-search closure")
    if not source_manifest:
        raise ValueError("source manifest is empty")

    rows = sorted(data.get("rows", []), key=lambda row: row["actual_delta_rad"])
    if len(rows) != 7:
        raise ValueError("expected seven scalar source conditions")
    for row in rows:
        pairs = row.get("source_human_guitar_intersections", [])
        matches = [pair for pair in pairs if pair.get("a") == "LH:thumb2" and pair.get("b") == "guitar"]
        if len(matches) != 1 or row.get("source_clear") is not False:
            raise ValueError("every tested condition must retain exactly one thumb2-guitar intersection")
        if not row.get("other_pose_identity") or not row.get("within_effective_range"):
            raise ValueError("saved row violates the pose-identity or range checks")
        if row.get("self_pair_count") != 1188 or row.get("source_cross_hand_intersections") or row.get("source_self_intersections"):
            raise ValueError("unexpected cross-hand or self-screen result")

    x = [row["actual_delta_rad"] for row in rows]
    radius_mm = [row["source_human_guitar_intersections"][0]["common_radius_m"] * 1000.0 for row in rows]
    labels = ["{:+.3f}".format(value) for value in x]
    fig, ax = plt.subplots(figsize=(9.0, 5.7))
    fig.subplots_adjust(left=0.12, right=0.97, top=0.83, bottom=0.29)
    ax.plot(x, radius_mm, color="#1769aa", linewidth=1.8, marker="o", markersize=7,
            label="LH:thumb2 – guitar (source LP)")
    for index, (x_value, y_value, label) in enumerate(zip(x, radius_mm, labels)):
        vertical = 13 if index % 2 == 0 else -19
        ax.annotate("{:.3f} mm\nΔ {} rad".format(y_value, label), (x_value, y_value),
                    xytext=(0, vertical), textcoords="offset points", ha="center", fontsize=8)
    ax.set_title("Static thumb2–guitar source intersection across scalar offsets", pad=18)
    ax.set_xlabel("Actual thumb2 offset from current pose (rad)")
    ax.set_ylabel("LP common inscribed radius (mm)")
    ax.set_xticks(x, ["{:+.3f}".format(value) for value in x])
    ax.set_ylim(0.0, max(radius_mm) + 1.15)
    ax.set_xlim(min(x) - 0.045, max(x) + 0.045)
    ax.grid(axis="y", color="#d9dee5", linewidth=0.8)
    ax.legend(loc="upper left", frameon=False)
    fig.suptitle("Saved-data static source geometry sweep", y=0.96, fontsize=13)
    fig.text(0.12, 0.17, "Static source LP sweep only; no new Isaac Gym rendering or dynamics.", fontsize=9)
    fig.text(0.12, 0.12, "All seven sampled offsets retain a thumb2–guitar intersection; radius is not PhysX penetration depth.", fontsize=9)
    fig.text(0.12, 0.07, "The ±0.2 rad sweep bounds only tested offsets; it does not prove full-joint-range impossibility.", fontsize=9)
    fig.savefig(OUTPUT, dpi=180, facecolor="white")
    plt.close(fig)

    input_after = {str(path): sha256(path) for path in INPUTS}
    producer_after = sha256(PRODUCER)
    if input_before != input_after or producer_before != producer_after:
        raise RuntimeError("input or producer changed during artifact generation")
    manifest = {
        "producer": str(PRODUCER),
        "producer_sha256_before": producer_before,
        "producer_sha256_after": producer_after,
        "input_count": len(INPUTS),
        "inputs_sha256_before": input_before,
        "inputs_sha256_after": input_after,
        "outputs_sha256": {"thumb2_source_radius_sweep.png": sha256(OUTPUT)},
        "native_calls": 0,
        "physics_steps": 0,
        "actor_inference_calls": 0,
        "training_updates": 0,
        "source_search_closure_count": len(before),
        "source_search_closure_before_after_equal": before == after,
        "rows_plotted": len(rows),
        "all_sampled_conditions_source_clear": all(row["source_clear"] for row in rows),
    }
    (ARTIFACTS / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
