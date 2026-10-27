"""Render verified saved guitar-error traces; this module does not run physics."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


def read_json(path):
    return json.loads(path.read_text())


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plot(comparison, output):
    rows = comparison["rows"]
    groups = defaultdict(list)
    for row in rows:
        groups[float(row["duration_s"])].append(row)
    durations = sorted(groups)
    if len(durations) != 2 or any(len(groups[duration]) != 2 for duration in durations):
        raise ValueError("expected two saved durations with two rows each")

    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=False)
    colors = ("#374151", "#2563a6", "#d97706", "#7c3aed")
    for row_index, duration in enumerate(durations):
        for condition_index, row in enumerate(groups[duration]):
            trace_path = Path(row["run"]) / "trace.json"
            trace = read_json(trace_path)
            time = [sample["time_s"] for sample in trace]
            label = f"{row['name']} · {row['mode']}"
            color = colors[condition_index]
            axes[row_index, 0].plot(time, [sample["position_error_m"] * 1000 for sample in trace],
                                    color=color, label=label)
            axes[row_index, 1].plot(time, [sample["rotation_error_deg"] for sample in trace],
                                    color=color, label=label)
        for column, title, ylabel in ((0, "Position error", "mm"),
                                     (1, "Rotation error", "degrees")):
            ax = axes[row_index, column]
            ax.set(title=f"{duration:g} s · {title}", xlabel="Time (s)", ylabel=ylabel,
                   xlim=(0, duration))
            ax.grid(True, alpha=.25)
            ax.legend(fontsize=8, frameon=False)
    fig.suptitle("Saved native-run traces · right elbow Y negative-angle comparison")
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(f"preserve existing output: {output}")
    fig.savefig(output, dpi=160, bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.out_dir.exists() and any(args.out_dir.iterdir()):
        raise FileExistsError(f"preserve existing outputs: {args.out_dir}")

    comparison_path = args.results_dir / "comparison.json"
    comparison = read_json(comparison_path)
    rows = comparison["rows"]
    if not all(comparison["checks"].values()) or not all(
            all(row["checks"].values()) for row in rows):
        raise ValueError("comparison contains a failed check")
    for source, expected in comparison["input_sha256"].items():
        path = Path(source)
        if not path.is_file() or sha256(path) != expected:
            raise ValueError(f"embedded input SHA mismatch: {path}")

    output = args.out_dir / "right_elbow_y_negative_v1.png"
    plot(comparison, output)
    manifest = {
        "purpose": "read-only plots from saved traces; no native simulation",
        "comparison_sha256": {str(comparison_path.resolve()): sha256(comparison_path)},
        "embedded_input_sha256": comparison["input_sha256"],
        "plotter_sha256": {str(Path(__file__).resolve()): sha256(Path(__file__))},
        "output_sha256": {str(output.resolve()): sha256(output)},
    }
    (args.out_dir / "plot_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
