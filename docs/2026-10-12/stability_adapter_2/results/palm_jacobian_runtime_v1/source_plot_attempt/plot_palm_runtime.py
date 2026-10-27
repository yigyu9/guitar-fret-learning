#!/usr/bin/env python3
"""Plot saved runtime palm Jacobian/velocity residuals from JSON only."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


OUTPUT_NAME = "palm_runtime_velocity_residuals.png"
SIDES = (("L", "Left palm", "#2864a5"), ("R", "Right palm", "#d17632"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_checked(path: Path, expected_hash_count: int) -> dict:
    data = json.loads(path.read_text())
    if not data.get("checks") or not all(data["checks"].values()):
        raise ValueError(f"checks failed in {path}")
    hashes = data.get("input_sha256", {})
    if len(hashes) != expected_hash_count:
        raise ValueError(f"expected {expected_hash_count} embedded input hashes in {path}")
    for filename, expected in hashes.items():
        source = Path(filename)
        if not source.is_file() or sha256(source) != expected:
            raise ValueError(f"input SHA mismatch: {filename}")
    return data


def plot(queries: list[dict], output_path: Path) -> None:
    samples = [sample for sample in queries if sample["physics_step"] > 0]
    times = [sample["time_s"] for sample in samples]
    fig, axes = plt.subplots(1, 3, figsize=(14, 5.4))
    panels = (
        ("COM_linear_error_mps", "COM linear velocity residual", "mm/s", 1000.0, ("before_refresh", "refreshed")),
        ("angular_error_rad_s", "Angular velocity residual", "rad/s", 1.0, ("before_refresh", "refreshed")),
    )
    styles = {"before_refresh": "--", "refreshed": "-"}
    labels = {"before_refresh": "Jacobian before refresh", "refreshed": "Jacobian after refresh"}

    for ax, (key, title, unit, scale, caches) in zip(axes[:2], panels):
        for side, side_name, color in SIDES:
            for cache in caches:
                values = [
                    sample["palms"][side]["velocity_comparisons"][cache][key] * scale
                    for sample in samples
                ]
                ax.plot(times, values, color=color, linestyle=styles[cache], linewidth=1.7,
                        label=f"{side_name} · {labels[cache]}")
        ax.set_title(title)
        ax.set_ylabel(unit)
        ax.set_yscale("log")
        ax.grid(True, which="both", alpha=0.24)
        ax.legend(frameon=False, fontsize=7)

    for side, side_name, color in SIDES:
        com_values = [
            sample["palms"][side]["velocity_comparisons"]["refreshed"]["COM_linear_error_mps"] * 1000.0
            for sample in samples
        ]
        origin_values = [
            sample["palms"][side]["velocity_comparisons"]["refreshed"]["body_velocity_as_origin_COM_error_mps"] * 1000.0
            for sample in samples
        ]
        ax = axes[2]
        ax.plot(times, com_values, color=color, linestyle="-", linewidth=1.7,
                label=f"{side_name} · COM interpretation")
        ax.plot(times, origin_values, color=color, linestyle="--", linewidth=1.7,
                label=f"{side_name} · origin interpreted as COM")
    axes[2].set_title("Refreshed linear-J point interpretation")
    axes[2].set_ylabel("mm/s")
    axes[2].set_yscale("log")
    axes[2].grid(True, which="both", alpha=0.24)
    axes[2].legend(frameon=False, fontsize=7)

    for ax in axes:
        ax.set_xlabel("Completed physics time (s)")
    fig.suptitle("Runtime palm Jacobian / velocity residuals · post-step samples only", y=0.98)
    fig.text(0.5, 0.015,
             "t=0 pre-refresh buffer is zero and omitted from lines; snapshots are query-time diagnostics, not a control or stability certificate.",
             ha="center", fontsize=8.5)
    fig.tight_layout(rect=(0.02, 0.09, 0.98, 0.92))
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
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
    report_path = result_dir / "measurements" / "report.json"
    query_path = result_dir / "measurements" / "queries.json"
    cache_path = result_dir / "cache_comparison.json"
    report = load_checked(report_path, 71)
    cache = load_checked(cache_path, 75)
    queries = json.loads(query_path.read_text())
    if sha256(query_path) not in cache["input_sha256"].values():
        raise ValueError("queries.json is not covered by cache input SHA")
    if report.get("physics_steps") != 24 or len(queries) != 25:
        raise ValueError("expected 24 physics steps and 25 query snapshots")
    if [sample["physics_step"] for sample in queries] != list(range(25)):
        raise ValueError("query snapshots must be contiguous from step 0 through 24")
    if any(not sample.get("reads_preserve_states_targets_PD", False) for sample in queries):
        raise ValueError("a query sample failed state/target preservation")
    for sample in queries:
        for side, _, _ in SIDES:
            if "velocity_comparisons" not in sample["palms"][side]:
                raise ValueError("missing saved velocity comparison")

    out_dir.mkdir(parents=True, exist_ok=True)
    image_path = out_dir / OUTPUT_NAME
    plot(queries, image_path)
    manifest = {
        "scope": "JSON-only post-step runtime Jacobian/velocity plot; no native run",
        "inputs": {
            "report_json": {"path": str(report_path), "sha256": sha256(report_path), "embedded_input_sha256": report["input_sha256"]},
            "cache_comparison_json": {"path": str(cache_path), "sha256": sha256(cache_path), "embedded_input_sha256": cache["input_sha256"]},
            "queries_json": {"path": str(query_path), "sha256": sha256(query_path)},
        },
        "checks": {"report_all_true": all(report["checks"].values()), "cache_all_true": all(cache["checks"].values()), "query_count": len(queries), "physics_steps": report["physics_steps"]},
        "plotter": {"path": str(Path(__file__).resolve()), "sha256": sha256(Path(__file__).resolve())},
        "outputs": {OUTPUT_NAME: {"path": str(image_path), "sha256": sha256(image_path)}},
    }
    (out_dir / "plot_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
