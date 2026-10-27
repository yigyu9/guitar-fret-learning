#!/usr/bin/env python3
"""Plot saved fresh-native t=0 thumb-base source LP radii."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path("/home/ajou/yigyu/3")
PHASE = ROOT / "docs/2026-10-12/stability_adapter_2/results/source_hand_thumb_base_native_v1"
ART = PHASE / "artifacts"
PRODUCER = ROOT / "stability_adapter_2/make_thumb_base_native_artifacts.py"
LABELS = ["thumb1_x_minus005", "thumb1_y_plus005", "thumb1_x_minus010", "thumb1_y_plus010"]
INPUTS = [
    PHASE / "analysis.json",
    PHASE / "native_batch.json",
    PHASE / "preparation_execution.json",
    PHASE / "finish_execution.json",
    ROOT / "docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/native/initial_grip_audit.json",
    ROOT / "docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/native/frames/hands/00000.png",
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
] + [PHASE / "native" / label / "initial_grip_audit.json" for label in LABELS]
OUTPUT = ART / "thumb1_base_native_source_radius.png"


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
    analysis = json.loads(INPUTS[0].read_text())
    batch = json.loads(INPUTS[1].read_text())
    prep_exec = json.loads(INPUTS[2].read_text())
    finish_exec = json.loads(INPUTS[3].read_text())
    baseline_audit = json.loads(INPUTS[4].read_text())

    checks = analysis.get("checks", {})
    if len(checks) != 35 or not all(checks.values()):
        raise ValueError("expected all 35 saved analysis checks to pass")
    if prep_exec.get("exit_code") != 0 or finish_exec.get("exit_code") != 0:
        raise ValueError("saved preparation/analysis command did not exit successfully")
    if finish_exec.get("input_sha256_before") != finish_exec.get("input_sha256_after"):
        raise ValueError("saved analysis input SHA maps differ before and after")
    attempts = batch.get("attempts", [])
    if len(attempts) != 4 or batch.get("selected") is not None:
        raise ValueError("expected four candidates and no selected candidate")
    if batch.get("physical_initializations") != 4 or batch.get("physical_steps") != 0:
        raise ValueError("unexpected saved native batch counts")
    for attempt, expected in zip(attempts, LABELS):
        if attempt.get("label") != expected or attempt.get("native_initializations") != 1:
            raise ValueError("unexpected native attempt order or initialization count")
        if attempt.get("physics_steps") != 0 or attempt.get("frame_count") != 1:
            raise ValueError("expected zero-step, one-frame native attempt")

    baseline_pair = baseline_audit["source_intersections"]
    if len(baseline_pair) != 1 or baseline_pair[0].get("human") != "LH:thumb2":
        raise ValueError("unexpected baseline source intersection")
    baseline_radius = baseline_pair[0]["common_radius_m"] * 1000.0
    rows = analysis.get("rows", [])
    if [row.get("label") for row in rows] != LABELS:
        raise ValueError("analysis rows do not match the four planned candidates")
    names, values = ["Baseline\n(thumb2 current)"], [baseline_radius]
    values_mm = [baseline_radius]
    for index, (row, audit) in enumerate(zip(rows, INPUTS[7:])):
        audit_data = json.loads(audit.read_text())
        audit_checks = audit_data.get("checks", {})
        if len(audit_checks) != 15 or audit_checks.get("source_human_guitar_clear") is not False:
            raise ValueError("candidate audit did not preserve the single HG gate failure")
        if sum(bool(value) for key, value in audit_checks.items() if key != "source_human_guitar_clear") != 14:
            raise ValueError("expected fourteen other fresh-native checks to pass")
        if audit_data["complete_source_self_screen"].get("pair_count") != 1188:
            raise ValueError("expected the full 1188-pair self-screen")
        pair = row.get("source_intersections", [])
        audit_pair = audit_data.get("source_intersections", [])
        if len(pair) != 1 or len(audit_pair) != 1:
            raise ValueError("expected exactly one thumb2-guitar source intersection")
        radius = pair[0]["common_radius_m"] * 1000.0
        if abs(radius - audit_pair[0]["common_radius_m"] * 1000.0) > 1e-9:
            raise ValueError("analysis row does not match fresh native audit radius")
        if row.get("failed_initial_checks") != ["source_human_guitar_clear"] or row.get("physics_steps") != 0:
            raise ValueError("candidate result scope differs from expected t=0 rejection")
        names.append({"thumb1_x_minus005": "thumb1_x\n−0.05 rad", "thumb1_y_plus005": "thumb1_y\n+0.05 rad", "thumb1_x_minus010": "thumb1_x\n−0.10 rad", "thumb1_y_plus010": "thumb1_y\n+0.10 rad"}[row["label"]])
        values.append(radius)
        values_mm.append(radius)

    fig, ax = plt.subplots(figsize=(10.0, 5.8))
    fig.subplots_adjust(left=0.11, right=0.98, top=0.84, bottom=0.30)
    colors = ["#6b7280"] + ["#1769aa"] * 4
    bars = ax.bar(range(5), values, width=0.62, color=colors, edgecolor="white", linewidth=0.8)
    for bar, value in zip(bars, values_mm):
        ax.text(bar.get_x() + bar.get_width() / 2.0, value + 0.08, "{:.6f} mm".format(value),
                ha="center", va="bottom", fontsize=9)
    ax.set_xticks(range(5), names)
    ax.set_ylim(0.0, max(values) + 0.95)
    ax.set_ylabel("LP common inscribed radius (mm)")
    ax.set_title("Thumb2–guitar source radius at fresh native initial poses", pad=14)
    ax.grid(axis="y", color="#d9dee5", linewidth=0.8)
    ax.set_axisbelow(True)
    fig.text(0.11, 0.17, "Fresh native t=0 source diagnosis: four initializations, zero physics steps.", fontsize=9)
    fig.text(0.11, 0.12, "LP common radius is not PhysX penetration depth or a dynamic-contact measurement.", fontsize=9)
    fig.text(0.11, 0.07, "All four thumb1 candidates retain the thumb2–guitar source intersection; no candidate was selected.", fontsize=9)
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
        "saved_analysis_check_count": len(checks),
        "saved_native_initializations": batch["physical_initializations"],
        "saved_native_physics_steps": batch["physical_steps"],
        "rows_plotted_including_baseline": len(values),
        "selected_candidate": batch["selected"],
    }
    (ART / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
