#!/usr/bin/env python3
"""Render sealed, read-only palm-witness diagnostics from saved records."""
import argparse
import hashlib
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path("/home/ajou/yigyu/3")
PHASE = ROOT / "docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1"
OLD = ROOT / "docs/2026-10-12/stability_adapter_2/results/body9_strap_minus2mm_v1/native"
OUT = PHASE / "artifacts"
FONT = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def inputs_to_seal():
    paths = {
        PHASE / name for name in ("search.json", "preparation.json", "proposal.json", "analysis.json")
    }
    paths.update(PHASE / "native" / name for name in (
        "initial_values.json", "report.json", "capture.json", "trace.jsonl", "contacts.jsonl",
        "controls.jsonl", "states.jsonl", "videos.json",
    ))
    paths.update(OLD / name for name in ("initial_values.json", "report.json", "trace.jsonl", "contacts.jsonl", "controls.jsonl", "states.jsonl", "videos.json"))
    paths.update(PHASE.glob("*_source.py"))
    paths.update(PHASE.glob("*_producer.py"))
    paths.update(PHASE.glob("*.log"))
    paths.update(PHASE.glob("*_execution.json"))
    for cam in ("hands", "whole_body"):
        paths.add(PHASE / "native/frames" / cam / "00000.png")
        paths.add(PHASE / "native/frames" / cam / "00150.png")
    # The exact upstream source files are included alongside the direct records consumed here.
    paths.add(FONT)
    missing = sorted(str(p) for p in paths if not p.is_file())
    if missing:
        raise FileNotFoundError("missing sealed inputs: " + ", ".join(missing))
    return {str(p): sha(p) for p in sorted(paths)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=OUT)
    args = parser.parse_args()
    out = args.out_dir
    if out.exists() and any(out.iterdir()):
        raise SystemExit("refusing nonempty --out-dir: " + str(out))
    out.mkdir(parents=True, exist_ok=True)
    producer_hash_before = sha(Path(__file__).resolve())
    before = inputs_to_seal()

    search = load_json(PHASE / "search.json")
    analysis = load_json(PHASE / "analysis.json")
    current = read_jsonl(PHASE / "native/trace.jsonl")
    baseline = read_jsonl(OLD / "trace.jsonl")
    assert len(search["rows"]) == 16 and len(current) == 1201 and len(baseline) == 1201
    assert len(analysis["summary"]) == 2

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 11})
    fig, axes = plt.subplots(2, 2, figsize=(13.3, 8.5), constrained_layout=True)
    fig.suptitle("Palm-witness source screen and one native hold per initial", fontsize=15)
    specs = [
        ("position_error_m", 1000.0, "Initial guitar position error (mm)", "Position (mm)"),
        ("rotation_error_deg", 1.0, "Initial guitar rotation error", "Rotation error (deg)"),
        ("last_applied_tension_n", 1.0, "Strap tension applied on previous step", "Tension (N)"),
    ]
    series = [(baseline, "Baseline −2 mm", "#3568a8"), (current, "Palm-witness initial", "#d97728")]
    for ax, (field, scale, title, ylabel) in zip(axes.flat[:3], specs):
        for rows, label, color in series:
            ax.plot([r["time_s"] for r in rows], [r[field] * scale for r in rows], label=label, color=color, linewidth=1.45)
        ax.set_title(title)
        ax.set_xlabel("Saved trace time (s)")
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.25)
        ax.legend(frameon=False, loc="best")
    ax = axes.flat[3]
    fractions = (0.0, 1.0, 0.5, 0.25)
    colors = {0.0: "#777777", 1.0: "#3568a8", 0.5: "#15906b", 0.25: "#d97728"}
    marks = {True: "o", False: "x"}
    for fraction in fractions:
        rows = [r for r in search["rows"] if r["fraction"] == fraction]
        xvals, yvals, passed = [], [], []
        for row in rows:
            distances = [v["distance_m"] for v in row["patch_distance_intervals"]["LH:palm"]]
            if not distances or not all(math.isfinite(v) and v >= 0 for v in distances):
                raise ValueError("malformed palm patch distances")
            xvals.append(row["time_s"])
            yvals.append(min(distances) * 1000.0)
            passed.append(bool(row["source_direction_screen_passed"]))
        for passed_value in (True, False):
            selected = [(x, y) for x, y, p in zip(xvals, yvals, passed) if p == passed_value]
            if selected:
                ax.scatter([x for x, _ in selected], [y for _, y in selected], color=colors[fraction], marker=marks[passed_value], s=52,
                           label="fraction {} · {}".format(fraction, "source screen pass" if passed_value else "source screen fail"))
    ax.set_title("Finite-patch distance upper bound (discrete source snapshots)")
    ax.set_xlabel("Source snapshot time (s; unconnected samples)")
    ax.set_ylabel("Minimum palm patch distance (mm)")
    ax.grid(True, alpha=0.25)
    ax.legend(frameon=False, fontsize=7, loc="best", ncol=2)
    fig.savefig(out / "palm_witness_diagnostics.png", dpi=180)
    plt.close(fig)

    outputs = {p.name: sha(p) for p in sorted(out.glob("*.png"))}
    after = inputs_to_seal()
    producer_hash_after = sha(Path(__file__).resolve())
    if before != after or producer_hash_before != producer_hash_after:
        raise RuntimeError("producer or sealed inputs changed during render")
    manifest = {
        "producer": str(Path(__file__).resolve()),
        "producer_sha256": producer_hash_before,
        "inputs_sha256_before": before,
        "inputs_sha256_after": after,
        "outputs_sha256": outputs,
        "native_calls": 0,
        "physics_steps": 0,
        "inference_calls": 0,
        "training_steps": 0,
        "figure": "palm_witness_diagnostics.png",
        "figure_content": "saved trace snapshots/series and point-only source geometry screen; no simulation or replay",
    }
    (out / "artifact_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"figure": str(out / "palm_witness_diagnostics.png"), "sha256": outputs, "sealed_input_count": len(before)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
