"""Plot recorded lower-initial-pose search and native trial summaries; no simulation."""
import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt


COLORS = {"baseline": "#475569", "c01": "#2563a6", "c02": "#16a34a", "c03": "#d97706"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pose-output", type=Path, help="optional c02 source-geometry pose comparison PNG")
    args = parser.parse_args()
    rows = json.loads((args.results_dir / "comparison.json").read_text())["rows"]
    fig, axes = plt.subplots(2, 2, figsize=(13, 8.5))

    for row in rows:
        name = row["name"]
        samples = json.loads((args.results_dir / name / "trace.json").read_text())
        times = [sample["time_s"] for sample in samples]
        axes[0, 0].plot(times, [sample["position_error_m"] * 1000 for sample in samples],
                        label=name, color=COLORS[name], linewidth=1.7)
        axes[0, 1].plot(times, [sample["source_position_error_m"] * 1000 for sample in samples],
                        label=name, color=COLORS[name], linewidth=1.7)

    axes[0, 0].set_title("Native guitar error to each candidate goal")
    axes[0, 0].set_ylabel("Position error (mm)")
    axes[0, 0].legend(ncol=2, frameon=False)
    axes[0, 1].set_title("Native guitar error to common source goal")
    axes[0, 1].set_ylabel("Position error (mm)")
    axes[0, 1].legend(ncol=2, frameon=False)
    for ax in axes[0]:
        ax.set_xlabel("Time (s)")
        ax.grid(True, alpha=.25)

    names = [row["name"] for row in rows]
    x = list(range(len(rows)))
    ground_mm = [row["initial_ground_minimum_gap_m"] * 1000 for row in rows]
    neg_counts = [row["initial_ground_negative_pair_count"] for row in rows]
    axes[1, 0].bar(x, ground_mm, color=[COLORS[n] for n in names])
    axes[1, 0].axhline(0, color="#111827", linewidth=.8)
    axes[1, 0].set_xticks(x, names)
    axes[1, 0].set_ylabel("Minimum source-ground signed gap (mm)")
    axes[1, 0].set_title("Initial source geometry (not PhysX clearance)")
    for i, (v, count) in enumerate(zip(ground_mm, neg_counts)):
        axes[1, 0].text(i, v / 2, f"{count} negative pairs", ha="center", va="center", fontsize=8, color="white", fontweight="bold")
    axes[1, 0].grid(True, axis="y", alpha=.25)

    metric_specs = [
        ("max_leg_raw_drift_deg", "Raw leg actual−target"),
        ("max_leg_native_scalar_limit_violation_deg", "Native scalar-limit violation"),
        ("max_leg_body_orientation_drift_deg", "Leg body orientation drift"),
    ]
    width = .24
    for j, (key, label) in enumerate(metric_specs):
        values = [row[key] for row in rows]
        offset = (j - 1) * width
        axes[1, 1].bar([v + offset for v in x], values, width, label=label)
    axes[1, 1].set_xticks(x, names)
    axes[1, 1].set_ylabel("Recorded maximum (degrees)")
    axes[1, 1].set_title("Lower-body response over 0.1 s")
    axes[1, 1].legend(frameon=False, fontsize=8)
    axes[1, 1].grid(True, axis="y", alpha=.25)

    fig.suptitle("Bounded lower-initial-pose diagnostics — not stability success", fontsize=13)
    fig.text(.5, .012,
             "240 Hz CPU PhysX, 24 steps per run. Source-ground gaps are CPU source-shape queries; "
             "leg raw angles are unwrapped actual−target differences.", ha="center", fontsize=8)
    fig.tight_layout(rect=(0, .045, 1, .96), h_pad=1.5, w_pad=1.5)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=170, bbox_inches="tight")
    plt.close(fig)
    if args.pose_output:
        plot_c02_recorded_poses(args.results_dir, args.pose_output)


def plot_c02_recorded_poses(results_dir, output):
    """Reconstruct two saved c02 poses from source collision geometry; no simulation."""
    # Preserve the project import order: load Gym before MuJoCo.
    import stability_adapter_2.environment  # noqa: F401
    from stability_adapter_2.plot_physx_contacts import source_surfaces
    from stability_adapter_2.replay_contact_geometry import recorded_probe
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    import numpy as np

    run = results_dir / "c02"
    steps = (0, 24)
    geometry = []
    all_points = []
    for step in steps:
        model, data, shapes = recorded_probe(run, step)
        surfaces, _, _, _ = source_surfaces(model, data, shapes)
        pose_surfaces = []
        for triangles, shape in surfaces:
            points = triangles.reshape(-1, 3)
            all_points.append(points)
            pose_surfaces.append((triangles, shape))
        geometry.append(pose_surfaces)

    bounds = np.concatenate(all_points)
    center = (bounds.min(axis=0) + bounds.max(axis=0)) / 2
    half = float(np.ptp(bounds, axis=0).max()) / 2 + .04
    lower_bodies = {
        "Pelvis", "L_Hip", "L_Knee", "L_Ankle", "L_Toe",
        "R_Hip", "R_Knee", "R_Ankle", "R_Toe",
    }
    fig = plt.figure(figsize=(13, 7))
    for panel, (step, surfaces) in enumerate(zip(steps, geometry), start=1):
        ax = fig.add_subplot(1, 2, panel, projection="3d")
        for triangles, shape in surfaces:
            if shape["actor"] == "guitar":
                color, alpha = "#2563eb", .95
            elif shape["body"] in lower_bodies:
                color, alpha = "#ea580c", .95
            else:
                color, alpha = "#9ca3af", .20
            ax.add_collection3d(Poly3DCollection(
                triangles, facecolors=color, alpha=alpha, edgecolors="none"))
        ax.set(xlim=(center[0]-half, center[0]+half),
               ylim=(center[1]-half, center[1]+half),
               zlim=(center[2]-half, center[2]+half),
               xlabel="World X (m)", ylabel="World Y (m)", zlabel="World Z (m)")
        ax.set_box_aspect((1, 1, 1))
        ax.view_init(elev=18, azim=36)
        ax.set_title(f"Saved native pose: step {step}, t={step / 240:.3f} s")
    fig.suptitle("c02 lower-body response — source collision geometry reconstruction", fontsize=13)
    fig.text(.5, .025,
             "Blue: guitar | Orange: pelvis/legs | Gray: remaining humanoid. Same world bounds/view; "
             "source shapes placed at saved native poses. Not a PhysX/Isaac render; no dynamics run.",
             ha="center", fontsize=8)
    fig.tight_layout(rect=(0, .06, 1, .93))
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
