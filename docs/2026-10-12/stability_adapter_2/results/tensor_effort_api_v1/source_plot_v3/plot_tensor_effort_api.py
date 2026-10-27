"""Plot saved 1-hinge CPU POS/EFFORT traces; never initializes a simulator."""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", type=Path, required=True, help="saved rollout directory")
    ap.add_argument("--out", type=Path, required=True, help="new PNG path")
    args = ap.parse_args()
    manifest_path = args.out.with_suffix(".manifest.json")
    if args.out.exists() or manifest_path.exists():
        raise FileExistsError("preserve existing PNG/manifest; choose a new output path")
    comparison_path = args.run / "comparison.json"
    comparison = json.loads(comparison_path.read_text())
    if comparison.get("fresh_simulations") != 6 or comparison.get("physics_steps") != 144:
        raise ValueError("unexpected saved rollout count")
    for path_text, expected in comparison["input_sha256"].items():
        path = Path(path_text)
        if not path.is_file() or sha(path) != expected:
            raise ValueError(f"stale comparison input: {path}")
    runs = {}
    paths = [comparison_path]
    for mode in ("EFFORT", "POS"):
        for torque in (0, 1, -1):
            path = args.run / f"{mode}_{torque}.json"
            data = json.loads(path.read_text())
            if data["drive"] != mode or data["torque_nm"] != torque or len(data["trace"]) != 25 or len(data["submissions"]) != 24:
                raise ValueError(f"unexpected run shape: {path.name}")
            if len(data["checks"]) != 9 or not all(data["checks"].values()) or not all(x["API_accepted"] for x in data["submissions"]) or len(data["contacts"]) != 24 or any(data["contacts"]):
                raise ValueError(f"saved run contract failed: {path.name}")
            runs[(mode, torque)] = data
            paths.append(path)
    times = [x["time_s"] for x in runs[("EFFORT", 0)]["trace"]]
    for run in runs.values():
        if [x["time_s"] for x in run["trace"]] != times:
            raise ValueError("trace timestamps differ")
    colors = {"EFFORT": "#1769aa", "POS": "#c24838"}
    styles = {0: "-", 1: "--", -1: ":"}
    labels = {0: "0 Nm", 1: "+1 Nm", -1: "−1 Nm"}
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), constrained_layout=True)
    for (mode, torque), run in runs.items():
        trace = run["trace"]
        label = f"{mode} {labels[torque]}"
        axes[0].plot(times, [x["q_rad"] * 180 / 3.141592653589793 for x in trace], color=colors[mode], linestyle=styles[torque], label=label)
        axes[1].plot(times, [x["velocity_rad_s"] for x in trace], color=colors[mode], linestyle=styles[torque], label=label)
    axes[0].set(title="Native hinge coordinate", xlabel="Time (s)", ylabel="q (deg)")
    axes[1].set(title="Native hinge angular velocity", xlabel="Time (s)", ylabel="Velocity (rad/s)")
    for ax in axes:
        ax.grid(True, alpha=.25)
        ax.legend(fontsize=8, ncol=2)
    fig.suptitle("Saved CPU single-hinge PhysX traces — not humanoid or guitar validation\nPOS 0 / ±1 Nm traces overlap exactly at zero in both panels; no visual offset")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=170)
    plt.close(fig)
    source_hashes = {str(path.resolve()): sha(path) for path in paths}
    manifest = {"purpose": "Read-only plot of six saved 24-step single-hinge runs; no simulator initialization",
                "comparison_input_sha256": comparison["input_sha256"],
                "rollout_json_sha256": source_hashes,
                "plotter_sha256": sha(Path(__file__).resolve()),
                "output_png": str(args.out.resolve()), "output_png_sha256": sha(args.out),
                "fresh_simulations_in_source": 6, "physics_steps_in_source": 144}
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"output": str(args.out), "manifest": str(manifest_path), "source_runs": 6}, indent=2))


if __name__ == "__main__":
    main()
