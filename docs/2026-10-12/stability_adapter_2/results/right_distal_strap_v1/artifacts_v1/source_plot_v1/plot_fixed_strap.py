"""Plot recorded fixed-strap OFF/ON traces; no native simulation."""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


LOAD_COLORS = {0: "#2563a6", 5: "#d97706", 10: "#16a34a", 20: "#7c3aed"}


def read_json(path):
    return json.loads(path.read_text())


def load_from_path(path):
    for value in (0, 5, 10, 20):
        if f"load_{value:02d}n" in str(path):
            return value
    raise ValueError(f"unrecognized load in saved run path: {path}")


def plot_comparison(rows, output):
    fig, axes = plt.subplots(2, 2, figsize=(13, 8.5), sharex="col")
    seen = set()
    for row in rows:
        group = row["group"]
        run = Path(row["run"])
        load = load_from_path(run)
        mode = row["mode"]
        trace = read_json(run / "trace.json")
        time = [sample["time_s"] for sample in trace]
        col = 0 if group == "short" else 1
        style = "-" if mode == "off" else "--"
        color = LOAD_COLORS[load]
        label = f"{load} N {mode.upper()}"
        pos = [sample["position_error_m"] * 1000 for sample in trace]
        rot = [sample["rotation_error_deg"] for sample in trace]
        axes[0, col].plot(time, pos, color=color, linestyle=style, lw=1.8, label=label)
        axes[1, col].plot(time, rot, color=color, linestyle=style, lw=1.8, label=label)
        seen.add((group, load, mode))

    for col, (title, xmax) in enumerate((("0.1 s initial load sweep", .1), ("0.5 s matched hold", .5))):
        axes[0, col].set_title(title)
        axes[0, col].set_ylabel("Guitar position error (mm)")
        axes[1, col].set_ylabel("Guitar rotation error (degrees)")
        axes[1, col].set_xlabel("Saved trace time (s)")
        for row_idx in range(2):
            axes[row_idx, col].set_xlim(0, xmax)
            axes[row_idx, col].grid(True, alpha=.24)
    axes[0, 0].set_title("0.1 s: 0/5/10/20 N initial load sweep")
    axes[0, 1].set_title("0.5 s: matched 0 N and 5 N load hold")

    load_handles = [Line2D([0], [0], color=LOAD_COLORS[n], lw=2, label=f"{n} N")
                    for n in (0, 5, 10, 20)]
    mode_handles = [Line2D([0], [0], color="#374151", lw=2, linestyle="-", label="OFF"),
                    Line2D([0], [0], color="#374151", lw=2, linestyle="--", label="ON")]
    fig.legend(handles=load_handles + mode_handles, loc="upper center", ncol=6,
               frameon=False, bbox_to_anchor=(.5, .955))
    fig.suptitle("Fixed strap law: saved guitar errors by initial preload and PI mode", y=.995, fontsize=13)
    fig.text(.5, .012,
             "0.1 s OFF/ON pairs overlay exactly for each load. Initial law tension is prescribed; "
             "rest length stays fixed during a run, but applied strap tension varies with state.",
             ha="center", fontsize=8)
    fig.tight_layout(rect=(0, .04, 1, .91), h_pad=1.1, w_pad=.8)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(output)
    fig.savefig(output, dpi=165, bbox_inches="tight")
    plt.close(fig)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.out_dir.exists() and any(args.out_dir.iterdir()):
        raise FileExistsError(f"preserve existing artifacts: {args.out_dir}")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    comparison_path = args.results_dir / "comparison_v2.json"
    comparison = read_json(comparison_path)
    rows = comparison["rows"]
    if len(rows) != 12 or not all(all(row["checks"].values()) for row in rows):
        raise ValueError("expected twelve fully checked saved runs")
    plot_path = args.out_dir / "right_distal_strap_v1_curves.png"
    plot_comparison(rows, plot_path)
    raw_inputs = [comparison_path, args.results_dir / "comparison.json",
                  args.results_dir / "strap_inputs.json", args.results_dir / "short_commands.json",
                  args.results_dir / "hold_05s_commands.json",
                  args.results_dir / "coverage_regression_validation.json",
                  args.results_dir / "source_manifest.json"]
    for row in rows:
        run = Path(row["run"])
        raw_inputs += [run / name for name in
                       ("report.json", "trace.json", "contacts.json", "controls.json")]
    plotter = Path(__file__).resolve()
    manifest = {
        "purpose": "read-only curve plot from saved right_distal_strap_v1 reports/traces; no native execution",
        "inputs_sha256": {str(p.resolve()): sha256(p) for p in sorted(set(raw_inputs)) if p.is_file()},
        "plotter_sha256": {str(plotter): sha256(plotter)},
        "embedded_runtime_source_sha256": comparison["input_sha256"],
        "outputs_sha256": {str(plot_path.resolve()): sha256(plot_path)},
    }
    (args.out_dir / "plot_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
