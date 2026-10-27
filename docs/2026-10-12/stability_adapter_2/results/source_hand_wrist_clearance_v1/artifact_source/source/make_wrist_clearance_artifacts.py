#!/usr/bin/env python3
"""Plot the saved 13-condition static wrist source intersection search."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path("/home/ajou/yigyu/3")
PHASE = ROOT / "docs/2026-10-12/stability_adapter_2/results/source_hand_wrist_clearance_v1"
ART = PHASE / "artifacts"
PRODUCER = ROOT / "stability_adapter_2/make_wrist_clearance_artifacts.py"
BASELINE_IMAGE = ROOT / "docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/native/frames/hands/00000.png"
INPUTS = [
    PHASE / "search.json",
    PHASE / "search_execution.json",
    PHASE / "search_source_manifest.json",
    PHASE / "search.log",
    BASELINE_IMAGE,
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
]
OUTPUT = ART / "wrist_source_clearance_radii.png"
EXPECTED = [(None, 0.0)] + [(joint, delta) for joint in ["L_Wrist_x", "L_Wrist_y", "L_Wrist_z"]
                            for delta in [-0.05, 0.05, -0.10, 0.10]]


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    for path in [OUTPUT, ART / "manifest.json"]:
        if path.exists():
            raise SystemExit("refusing to overwrite existing artifact: " + str(path))
    input_before = {str(path): sha256(path) for path in INPUTS}
    producer_before = sha256(PRODUCER)
    data = json.loads(INPUTS[0].read_text())
    execution = json.loads(INPUTS[1].read_text())
    source_manifest = json.loads(INPUTS[2].read_text())
    checks = data.get("checks", {})
    if len(checks) != 8 or not all(checks.values()):
        raise ValueError("expected all eight static wrist source checks to pass")
    if data.get("selected") is not None or data.get("native_initializations") != 0 or data.get("physics_steps") != 0:
        raise ValueError("unexpected candidate selection or physical execution in source search")
    if execution.get("exit_code") != 0 or execution.get("terminal_state") != "completed":
        raise ValueError("saved source search execution did not complete")
    before = execution.get("input_sha256_before", {})
    after = execution.get("input_sha256_after", {})
    if len(before) != 69 or len(after) != 69 or before != after:
        raise ValueError("expected exact before/after hashes for the 69-input search closure")
    if not source_manifest:
        raise ValueError("search source manifest is empty")

    rows = data.get("rows", [])
    if len(rows) != 13:
        raise ValueError("expected the baseline and twelve wrist offsets")
    thumb_mm, other_max_mm, pair_counts, xlabels = [], [], [], []
    for index, (row, (joint, delta)) in enumerate(zip(rows, EXPECTED)):
        if row.get("joint") != joint or row.get("requested_delta_rad") != delta:
            raise ValueError("rows are not in the approved fixed condition order")
        if row.get("source_clear") is not False or row.get("self_pair_count") != 1188:
            raise ValueError("a row does not preserve the failed HG / 1188 self-screen result")
        if row.get("source_cross_hand_intersections") or row.get("source_self_intersections"):
            raise ValueError("unexpected cross-hand or self intersection")
        if row.get("palm_up_proxy_z", 0.0) <= 0.0:
            raise ValueError("palm-up proxy must remain positive")
        if not row.get("other80_q_and_held_exact") or not row.get("upper_arm_identity") or not row.get("hand_relative_identity"):
            raise ValueError("saved row violates preserved-pose identity checks")
        pairs = row.get("source_human_guitar_intersections", [])
        thumb = [pair for pair in pairs if pair.get("a") == "LH:thumb2" and pair.get("b") == "guitar"]
        if len(thumb) != 1:
            raise ValueError("every condition must retain exactly one thumb2-guitar intersection")
        others = [pair["common_radius_m"] * 1000.0 for pair in pairs if pair not in thumb]
        thumb_mm.append(thumb[0]["common_radius_m"] * 1000.0)
        other_max_mm.append(max(others, default=0.0))
        pair_counts.append(len(pairs))
        if index == 0:
            xlabels.append("base")
        else:
            axis = {"L_Wrist_x": "x", "L_Wrist_y": "y", "L_Wrist_z": "z"}[joint]
            xlabels.append("{} {:+.2f}".format(axis, delta))

    positions = list(range(13))
    width = 0.36
    fig, ax = plt.subplots(figsize=(14.2, 7.4))
    fig.subplots_adjust(left=0.09, right=0.99, top=0.81, bottom=0.34)
    first = ax.bar([pos - width / 2.0 for pos in positions], thumb_mm, width,
                   color="#1769aa", label="thumb2–guitar LP radius")
    second = ax.bar([pos + width / 2.0 for pos in positions], other_max_mm, width,
                    color="#e58b27", label="max other reported HG-pair radius")
    for index, value in enumerate(thumb_mm):
        ax.text(index - width / 2.0, value + 0.06, "{:.2f}".format(value),
                ha="center", va="bottom", fontsize=7)
    for index, value in enumerate(other_max_mm):
        ax.text(index + width / 2.0, (value + 0.07) if value else 0.07,
                "{:.2f}".format(value) if value else "none", ha="center", va="bottom", fontsize=7)
    ax.set_title("Conditional wrist source intersections across 13 saved conditions", pad=14)
    ax.set_ylabel("LP common inscribed radius (mm)")
    ax.set_xticks(positions, xlabels, rotation=0, fontsize=7.5)
    ax.set_ylim(0.0, max(thumb_mm + other_max_mm) + 1.05)
    ax.grid(axis="y", color="#d9dee5", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", ncol=2, frameon=False, fontsize=8)
    fig.text(0.09, 0.23, "Static conditional source query only; no new Gym rendering or dynamics.", fontsize=9)
    fig.text(0.09, 0.17, "A 'none' second-series label means no other pair exceeded the 1e−7 m LP reporting threshold, not zero physical distance.", fontsize=9)
    fig.text(0.09, 0.11, "LP radii are not PhysX penetration depths or contact certification; all 13 conditions retain thumb2–guitar overlap.", fontsize=9)
    fig.savefig(OUTPUT, dpi=180, facecolor="white")
    plt.close(fig)

    input_after = {str(path): sha256(path) for path in INPUTS}
    producer_after = sha256(PRODUCER)
    if input_before != input_after or producer_before != producer_after:
        raise RuntimeError("direct input or producer changed during artifact generation")
    manifest = {
        "producer": str(PRODUCER),
        "producer_sha256_before": producer_before,
        "producer_sha256_after": producer_after,
        "input_count": len(INPUTS),
        "inputs_sha256_before": input_before,
        "inputs_sha256_after": input_after,
        "outputs_sha256": {OUTPUT.name: sha256(OUTPUT)},
        "native_calls": 0,
        "physics_steps": 0,
        "actor_inference_calls": 0,
        "training_updates": 0,
        "saved_search_closure_count": len(before),
        "saved_search_closure_before_after_equal": before == after,
        "conditions_plotted": len(rows),
        "candidate_selected": data["selected"],
    }
    (ART / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
