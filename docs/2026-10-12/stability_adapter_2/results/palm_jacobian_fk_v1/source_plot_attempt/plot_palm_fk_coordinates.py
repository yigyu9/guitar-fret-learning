#!/usr/bin/env python3
"""Plot raw and coordinate-corrected palm Jacobian/FK comparison errors."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


GROUPS = (
    ("Thorax", "L_Thorax_"),
    ("Shoulder", "L_Shoulder_"),
    ("Elbow", "L_Elbow_"),
    ("Wrist", "L_Wrist_"),
)
OUTPUT_NAME = "palm_fk_coordinate_errors.png"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_json(path: Path, count: int) -> dict:
    data = json.loads(path.read_text())
    checks = data.get("checks", {})
    if not checks or not all(checks.values()):
        raise ValueError(f"checks failed in {path}")
    hashes = data.get("input_sha256", {})
    if len(hashes) != count:
        raise ValueError(f"expected {count} input SHA records in {path}")
    for name, expected in hashes.items():
        source = Path(name)
        if not source.is_file() or sha256(source) != expected:
            raise ValueError(f"input SHA mismatch: {name}")
    return data


def group_max(rows: list[dict], prefix: str, key: str) -> float:
    values = [row[key] for row in rows if row["joint"].startswith(prefix)]
    if len(values) != 3:
        raise ValueError(f"expected three coordinate rows for {prefix}")
    return max(values)


def plot(raw: dict, corrected: dict, destination: Path) -> None:
    pairs = (
        ("COM_error_m_per_rad", "COM_error", "Palm point position residual", "mm/rad"),
        ("angular_error_rad_per_rad", "angular_error", "Angular residual", "rad/rad"),
    )
    fig, axes = plt.subplots(1, 3, figsize=(14, 5.2))
    x = list(range(len(GROUPS)))
    width = 0.36
    colors = ("#b45248", "#287b69")
    for ax, (raw_key, fixed_key, title, unit) in zip(axes[:2], pairs):
        raw_values = [group_max(raw["rows"], prefix, raw_key) for _, prefix in GROUPS]
        corrected_values = [group_max(corrected["rows"], prefix, fixed_key) for _, prefix in GROUPS]
        ax.bar([v - width / 2 for v in x], raw_values, width, label="Native Jacobian vs coordinate FD", color=colors[0])
        ax.bar([v + width / 2 for v in x], corrected_values, width, label="Tangent-corrected Jacobian vs coordinate FD", color=colors[1])
        ax.set_title(title)
        ax.set_ylabel(unit)
        ax.set_yscale("log")
        ax.grid(axis="y", which="both", alpha=0.24)
        ax.set_axisbelow(True)
        ax.set_xticks(x, [name for name, _ in GROUPS])
        ax.legend(frameon=False, fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=1)

    origin_values = [group_max(corrected["rows"], prefix, "source_from_origin_error") for _, prefix in GROUPS]
    com_values = [group_max(corrected["rows"], prefix, "source_from_COM_error") for _, prefix in GROUPS]
    axes[2].bar([v - width / 2 for v in x], origin_values, width, label="Tangent corrected; source at origin", color=colors[0])
    axes[2].bar([v + width / 2 for v in x], com_values, width, label="Tangent corrected; COM to source", color=colors[1])
    axes[2].set_title("Source-center position residual")
    axes[2].set_ylabel("mm/rad")
    axes[2].set_yscale("log")
    axes[2].grid(axis="y", which="both", alpha=0.24)
    axes[2].set_axisbelow(True)
    axes[2].set_xticks(x, [name for name, _ in GROUPS])
    axes[2].legend(frameon=False, fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=1)

    fig.suptitle("Worst sampled coordinate error by left-arm joint group", y=0.98)
    fig.text(
        0.5,
        0.012,
        "Bars show the maximum x/y/z coordinate norm per group; log scales. Current initial pose only, not an importer or runtime certificate.",
        ha="center",
        fontsize=9,
    )
    fig.subplots_adjust(left=0.06, right=0.985, bottom=0.27, top=0.86, wspace=0.24)
    fig.savefig(destination, dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()
    result_dir = args.results_dir.resolve()
    out_dir = args.out_dir.resolve()
    if out_dir.exists() and any(out_dir.iterdir()):
        raise SystemExit(f"refusing to overwrite nonempty output directory: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_path = result_dir / "measurements_validated" / "comparison.json"
    corrected_path = result_dir / "coordinate_comparison.json"
    raw = checked_json(raw_path, 93)
    corrected = checked_json(corrected_path, 98)
    if len(raw.get("rows", [])) != 12 or len(corrected.get("rows", [])) != 12:
        raise ValueError("expected twelve matched coordinate rows")
    if {r["joint"] for r in raw["rows"]} != {r["joint"] for r in corrected["rows"]}:
        raise ValueError("raw and corrected joint rows do not match")
    methods = [row["method"] for row in raw["rows"]]
    if methods.count("central") != 10 or methods.count("forward") != 1 or methods.count("backward") != 1:
        raise ValueError("unexpected central/one-sided finite-difference row counts")

    image_path = out_dir / OUTPUT_NAME
    plot(raw, corrected, image_path)
    manifest = {
        "scope": "JSON-only saved coordinate error plot; no native run",
        "inputs": {
            "raw_comparison": {"path": str(raw_path), "sha256": sha256(raw_path), "embedded_input_sha256": raw["input_sha256"]},
            "coordinate_comparison": {"path": str(corrected_path), "sha256": sha256(corrected_path), "embedded_input_sha256": corrected["input_sha256"]},
        },
        "checks": {"raw_all_true": all(raw["checks"].values()), "corrected_all_true": all(corrected["checks"].values()), "raw_rows": len(raw["rows"]), "corrected_rows": len(corrected["rows"])},
        "plotter": {"path": str(Path(__file__).resolve()), "sha256": sha256(Path(__file__).resolve())},
        "outputs": {OUTPUT_NAME: {"path": str(image_path), "sha256": sha256(image_path)}},
    }
    (out_dir / "plot_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
