#!/usr/bin/env python3
"""Plot saved per-axis local linear correction ranges from authority JSON."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


OUTPUT_NAME = "palm_axis_authority.png"
AXES = ("x", "y", "z")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_authority(path: Path) -> dict:
    data = json.loads(path.read_text())
    checks = data.get("checks", {})
    if set(checks) != {"25_aligned_samples", "finite_records", "existing_delta_box_contains_zero"} or not all(checks.values()):
        raise ValueError("authority checks must all pass with the expected contract")
    hashes = data.get("input_sha256", {})
    if len(hashes) != 76:
        raise ValueError("expected 76 embedded input SHA records")
    for filename, expected in hashes.items():
        source = Path(filename)
        if not source.is_file() or sha256(source) != expected:
            raise ValueError(f"embedded input SHA mismatch: {filename}")
    rows = data.get("records", [])
    if len(rows) != 25 or [row["physics_step"] for row in rows] != list(range(25)):
        raise ValueError("expected aligned saved steps 0 through 24")
    if any(not all(row["required_within_each_axis_interval"]) for row in rows):
        raise ValueError("a required axis correction lies outside its recorded interval")
    return data


def plot(data: dict, output_path: Path) -> None:
    rows = data["records"]
    times = [row["time_s"] for row in rows]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.8), sharex=True)
    for index, (ax, axis) in enumerate(zip(axes, AXES)):
        lower = [1000.0 * row["axis_interval_lower_m"][index] for row in rows]
        upper = [1000.0 * row["axis_interval_upper_m"][index] for row in rows]
        needed = [1000.0 * row["required_displacement_m"][index] for row in rows]
        ax.fill_between(times, lower, upper, color="#89b9d4", alpha=0.38,
                        label="Independent-axis interval")
        ax.plot(times, needed, color="#b34f42", linewidth=2.0,
                label="Required local correction")
        ax.axhline(0.0, color="#555555", linewidth=0.8, alpha=0.7)
        ax.set_title(f"{axis.upper()} displacement")
        ax.set_xlabel("Saved run time (s)")
        ax.set_ylabel("Local linear displacement (mm)")
        ax.grid(True, alpha=0.22)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.92),
               ncol=2, frameon=False, fontsize=9)
    fig.suptitle("Saved per-axis local authority envelope", y=0.98)
    fig.text(0.5, 0.015,
             "Axis intervals are independent linear bounds, not simultaneous joint feasibility or full-FK reachability.",
             ha="center", fontsize=9)
    fig.subplots_adjust(left=0.07, right=0.98, bottom=0.15, top=0.83, wspace=0.28)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()
    results_dir = args.results_dir.resolve()
    out_dir = args.out_dir.resolve()
    if out_dir.exists() and any(out_dir.iterdir()):
        raise SystemExit(f"refusing to overwrite nonempty output directory: {out_dir}")
    input_path = results_dir / "authority.json"
    data = load_authority(input_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    image_path = out_dir / OUTPUT_NAME
    plot(data, image_path)
    manifest = {
        "scope": "JSON-only saved per-axis local linear authority figure; no native run",
        "inputs": {"authority_json": {"path": str(input_path), "sha256": sha256(input_path),
                                        "embedded_input_sha256": data["input_sha256"]}},
        "checks": {"all_true": all(data["checks"].values()), "records": len(data["records"])},
        "plotter": {"path": str(Path(__file__).resolve()), "sha256": sha256(Path(__file__).resolve())},
        "outputs": {OUTPUT_NAME: {"path": str(image_path), "sha256": sha256(image_path)}},
    }
    (out_dir / "plot_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
