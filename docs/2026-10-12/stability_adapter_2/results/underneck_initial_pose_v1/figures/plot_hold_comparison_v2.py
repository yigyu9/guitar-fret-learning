#!/usr/bin/env python3
"""Plot saved guitar traces for the three 5 s underneck runs; no simulation."""
import hashlib
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures" / "hold_compare_v5_v2"
RUNS = {
    "physics_off": "No hold",
    "physics_follow": "Follow",
    "physics_hold_v5": "Arm hold v5",
}
INPUTS = [ROOT / name / "trace.json" for name in RUNS]
INPUTS += [ROOT / name / "report.json" for name in RUNS]
INPUTS += [ROOT / name / "images" / "videos.json" for name in RUNS]


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def finite_tree(value):
    if isinstance(value, dict):
        return all(finite_tree(v) for v in value.values())
    if isinstance(value, list):
        return all(finite_tree(v) for v in value)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return math.isfinite(value)
    return True


def main():
    if OUT.exists() and any(OUT.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty output: {OUT}")
    OUT.mkdir(parents=True, exist_ok=True)
    before = {str(p): sha(p) for p in INPUTS}
    traces = {}
    for run in RUNS:
        trace = json.loads((ROOT / run / "trace.json").read_text())
        if not isinstance(trace, list) or len(trace) != 151:
            raise ValueError(f"{run}: expected 151 saved samples")
        if [row["physics_step"] for row in trace] != list(range(0, 1201, 8)):
            raise ValueError(f"{run}: unexpected sampled physics steps")
        if not finite_tree(trace):
            raise ValueError(f"{run}: non-finite trace value")
        if trace[0]["time_s"] != 0.0 or trace[-1]["time_s"] != 5.0:
            raise ValueError(f"{run}: unexpected time coverage")
        traces[run] = trace

    colors = {"physics_off": "#777777", "physics_follow": "#d97706", "physics_hold_v5": "#2563eb"}
    fig, axes = plt.subplots(3, 1, figsize=(11.5, 10), sharex=True)
    for run, label in RUNS.items():
        rows = traces[run]
        t = [r["time_s"] for r in rows]
        axes[0].plot(t, [r["position_change_m"] * 1000 for r in rows], label=label, color=colors[run], lw=2)
        axes[1].plot(t, [r["rotation_change_deg"] for r in rows], label=label, color=colors[run], lw=2)
        axes[2].plot(t, [r["position_W_m"][2] for r in rows], label=label, color=colors[run], lw=2)
    axes[0].set_ylabel("Guitar position change (mm)")
    axes[1].set_ylabel("Guitar rotation change (deg)")
    axes[2].set_ylabel("Guitar world Z (m)")
    axes[2].set_xlabel("Saved simulation time (s)")
    axes[2].axhline(0.65, color="#b91c1c", ls="--", lw=1.4, label="Position-box lower Z (0.65 m)")
    for ax in axes:
        ax.set_xlim(0, 5)
        ax.grid(True, alpha=.25)
    handles, labels = axes[0].get_legend_handles_labels()
    bound_handles, bound_labels = axes[2].get_legend_handles_labels()
    fig.legend(handles + bound_handles[-1:], labels + bound_labels[-1:], loc="upper center",
               bbox_to_anchor=(.5, .945), ncol=4, frameon=False)
    fig.suptitle("Saved PhysX guitar traces — 5 s comparison", fontsize=15, y=.985)
    fig.text(.5, .012, "Saved native state measurements; this plot is not a rendered scene. All 151 samples per run are shown.", ha="center", fontsize=9)
    fig.tight_layout(rect=(0, .035, 1, .89))
    png = OUT / "hold_comparison_v5_v2.png"
    fig.savefig(png, dpi=180)
    plt.close(fig)

    after = {str(p): sha(p) for p in INPUTS}
    if before != after:
        raise RuntimeError("input changed while plotting")
    manifest = {
        "producer": str(Path(__file__).resolve()),
        "producer_sha256": sha(Path(__file__).resolve()),
        "inputs_sha256": before,
        "outputs_sha256": {str(png): sha(png)},
        "runs": list(RUNS),
        "sample_count_per_run": 151,
        "sampled_physics_steps": [0, 8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 88, 96, 104, 112, 120, 128, 136, 144, 152, 160, 168, 176, 184, 192, 200, 208, 216, 224, 232, 240, 248, 256, 264, 272, 280, 288, 296, 304, 312, 320, 328, 336, 344, 352, 360, 368, 376, 384, 392, 400, 408, 416, 424, 432, 440, 448, 456, 464, 472, 480, 488, 496, 504, 512, 520, 528, 536, 544, 552, 560, 568, 576, 584, 592, 600, 608, 616, 624, 632, 640, 648, 656, 664, 672, 680, 688, 696, 704, 712, 720, 728, 736, 744, 752, 760, 768, 776, 784, 792, 800, 808, 816, 824, 832, 840, 848, 856, 864, 872, 880, 888, 896, 904, 912, 920, 928, 936, 944, 952, 960, 968, 976, 984, 992, 1000, 1008, 1016, 1024, 1032, 1040, 1048, 1056, 1064, 1072, 1080, 1088, 1096, 1104, 1112, 1120, 1128, 1136, 1144, 1152, 1160, 1168, 1176, 1184, 1192, 1200],
        "interpretation": "Saved-state traces only; no native simulation or rendering was run by this producer.",
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
