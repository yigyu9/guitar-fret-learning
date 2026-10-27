"""Plot saved right-distal fine-search and joint-hold results; no physics runs."""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def read_json(path):
    return json.loads(path.read_text())


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plot_curves(current, previous, output):
    fig, axes = plt.subplots(3, 2, figsize=(13, 10), sharex=False)
    colors = {"right_distal_v1": "#2563a6", "right_distal_fine_v1": "#d97706"}
    groups = (("short", "0.1 s"), ("hold_05s", "0.5 s"), ("hold_1s", "1.0 s"))
    for row, (group, title) in enumerate(groups):
        for root, label in ((previous, "right_distal_v1 c01"),
                            (current, "right_distal_fine_v1 c02")):
            color = colors[root.name]
            for mode, linestyle in (("off", "-"), ("on", "--")):
                run = root / "joint_hold" / group / mode
                trace = read_json(run / "trace.json")
                t = [sample["time_s"] for sample in trace]
                axes[row, 0].plot(t, [sample["position_error_m"] * 1000 for sample in trace],
                                  color=color, ls=linestyle, lw=1.7,
                                  label=f"{label} {mode.upper()}")
                axes[row, 1].plot(t, [sample["rotation_error_deg"] for sample in trace],
                                  color=color, ls=linestyle, lw=1.7,
                                  label=f"{label} {mode.upper()}")
        axes[row, 0].set(title=f"{title} guitar position error", ylabel="mm")
        axes[row, 1].set(title=f"{title} guitar rotation error", ylabel="degrees")
        for ax in axes[row]:
            ax.grid(True, alpha=.25)
            ax.legend(fontsize=7, ncol=2, frameon=False)
            ax.set_xlim(0, float(title.split()[0]))
    axes[-1, 0].set_xlabel("Time (s)")
    axes[-1, 1].set_xlabel("Time (s)")
    fig.suptitle("Saved CPU PhysX traces — candidate-goal guitar errors; OFF solid / ON dashed")
    fig.text(.5, .008,
             "Blue: prior c01 initial pose | orange: fine-search c02. Curves show guitar errors only; "
             "they do not establish stable playing or contact support.", ha="center", fontsize=8)
    fig.tight_layout(rect=(0, .03, 1, .97))
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(output)
    fig.savefig(output, dpi=160, bbox_inches="tight")
    plt.close(fig)


def snapshot(run, step):
    import stability_adapter_2.environment  # gym import order for source replay
    from stability_adapter_2.plot_physx_contacts import source_surfaces
    from stability_adapter_2.replay_contact_geometry import recorded_probe

    model, data, shapes = recorded_probe(run, step)
    surfaces, _, _, _ = source_surfaces(model, data, shapes)
    return surfaces


def plot_geometry(current, output, static_comparison):
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    panels = [
        ("Reference · t=0", "reference", "initial", current / "short/reference", 0),
        ("Reference · t=0.1 s", "reference", "final", current / "short/reference", 24),
        ("Candidate 02 · t=0", "candidate_02", "initial", current / "short/candidate_02", 0),
        ("Candidate 02 · t=0.1 s", "candidate_02", "final", current / "short/candidate_02", 24),
    ]
    comparison_rows = {row["name"]: row for row in static_comparison["rows"]}
    snapshots, points = [], []
    for title, result_name, state_name, run, step in panels:
        surfaces = snapshot(run, step)
        visible = []
        for triangles, shape in surfaces:
            body = shape["body"]
            relevant = (shape["actor"] == "guitar" or body.startswith("RH:") or
                        body in ("R_Wrist", "R_Elbow", "R_Shoulder", "R_Thorax"))
            if relevant:
                visible.append((triangles, shape))
                points.append(triangles.reshape(-1, 3))
        hull_key = f"{state_name}_right_palm_body_hulls"
        hull = comparison_rows[result_name][hull_key]
        witnesses = np.asarray(hull["hull_witness_points_m"], dtype=float)
        snapshots.append((title, visible, witnesses,
                          float(hull["source_hull_distance_m"]) * 1000.0))
    cloud = np.concatenate(points)
    center = (cloud.min(axis=0) + cloud.max(axis=0)) / 2
    half = float(np.ptp(cloud, axis=0).max()) / 2 + .035
    fig = plt.figure(figsize=(13, 9))
    for i, (title, surfaces, witnesses, gap_mm) in enumerate(snapshots, 1):
        ax = fig.add_subplot(2, 2, i, projection="3d")
        ax.computed_zorder = False
        for triangles, shape in surfaces:
            body = shape["body"]
            if shape["actor"] == "guitar":
                color, alpha = "#2563eb", .78
            elif body.startswith("RH:") or body in ("R_Wrist", "R_Elbow", "R_Shoulder"):
                color, alpha = "#c026d3", .78
            else:
                color, alpha = "#9ca3af", .23
            ax.add_collection3d(Poly3DCollection(triangles, facecolors=color,
                                                 edgecolors="none", alpha=alpha, zorder=1))
        ax.plot(witnesses[:, 0], witnesses[:, 1], witnesses[:, 2], color="#f97316",
                marker="o", markersize=6, markeredgecolor="#111827", linewidth=2.5,
                zorder=20)
        ax.set(xlim=(center[0]-half, center[0]+half),
               ylim=(center[1]-half, center[1]+half),
               zlim=(center[2]-half, center[2]+half),
               xlabel="World X (m)", ylabel="World Y (m)", zlabel="World Z (m)")
        ax.set_box_aspect((1, 1, 1))
        ax.view_init(elev=18, azim=110)
        ax.set_title(f"{title} · RH/body source hull {gap_mm:.3f} mm")
    fig.suptitle("Recorded native poses reconstructed from source collision shapes")
    fig.text(.5, .012,
             "Blue: guitar | magenta: right hand/arm | gray: selected upper body | orange: query witness overlay. "
             "Unsigned source gap/witness is not native clearance certification.",
             ha="center", fontsize=8)
    fig.tight_layout(rect=(0, .04, 1, .96))
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(output)
    fig.savefig(output, dpi=145, bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--previous-results-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.out_dir.exists() and any(args.out_dir.iterdir()):
        raise FileExistsError(f"preserve existing output directory: {args.out_dir}")
    for root in (args.results_dir, args.previous_results_dir):
        comparison = read_json(root / "joint_hold/comparison.json")
        if (len(comparison["rows"]) != 6 or
                not all(comparison["checks"].values()) or
                not all(all(row["checks"].values()) for row in comparison["rows"])):
            raise ValueError(f"incomplete joint-hold comparison: {root}")
    static_comparison = read_json(args.results_dir / "comparison_v2.json")
    if (len(static_comparison["rows"]) != 4 or
            not all(static_comparison["checks"].values()) or
            not all(all(row["checks"].values()) for row in static_comparison["rows"])):
        raise ValueError("incomplete current static/native comparison")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    curve = args.out_dir / "right_distal_fine_v1_curves.png"
    geometry = args.out_dir / "right_distal_fine_v1_source_poses.png"
    plot_curves(args.results_dir, args.previous_results_dir, curve)
    plot_geometry(args.results_dir, geometry, static_comparison)

    input_paths = [args.results_dir / "comparison_v2.json",
                   args.results_dir / "comparison.json",
                   args.results_dir / "decision.json",
                   args.results_dir / "search/search.json",
                   args.results_dir / "source_manifest.json",
                   args.results_dir / "joint_hold/comparison.json",
                   args.previous_results_dir / "joint_hold/comparison.json"]
    for root in (args.results_dir, args.previous_results_dir):
        groups = ("short", "hold_05s", "hold_1s")
        for group in groups:
            for mode in ("off", "on"):
                run = root / "joint_hold" / group / mode
                input_paths.extend(run / name for name in
                                   ("report.json", "trace.json", "states.json", "contacts.json", "controls.json"))
    for run in (args.results_dir / "short/reference", args.results_dir / "short/candidate_02"):
        input_paths.extend(run / name for name in
                           ("report.json", "trace.json", "states.json", "contacts.json"))
    helpers = [Path(__file__).resolve(), Path(__file__).with_name("plot_joint_hold.py"),
               Path(__file__).with_name("plot_physx_contacts.py"),
               Path(__file__).with_name("replay_contact_geometry.py"),
               Path(__file__).with_name("initial_overlap.py"),
               Path(__file__).with_name("environment.py"), Path(__file__).with_name("config.json")]
    assets = __import__("stability_adapter_2.plot_joint_hold", fromlist=["geometry_asset_paths"]).geometry_asset_paths()
    manifest = {
        "purpose": "read-only plots from saved results; no native simulation",
        "inputs_sha256": {str(p.resolve()): sha256(p) for p in sorted(set(input_paths))},
        "plot_sources_sha256": {str(p.resolve()): sha256(p) for p in helpers},
        "source_geometry_assets_sha256": {str(p): sha256(p) for p in assets},
        "embedded_input_hashes": {
            "static_comparison_v2_input_sha256": static_comparison.get("input_sha256", {}),
            "static_search_source_sha256": read_json(args.results_dir / "search/search.json").get("source_sha256", {}),
            "joint_hold_comparison_input_sha256": {
                str(root.resolve()): read_json(root / "joint_hold/comparison.json").get("input_sha256", {})
                for root in (args.results_dir, args.previous_results_dir)},
        },
        "outputs_sha256": {str(p.resolve()): sha256(p) for p in (curve, geometry)},
    }
    manifest_path = args.out_dir / "plot_manifest.json"
    if manifest_path.exists():
        raise FileExistsError(manifest_path)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
