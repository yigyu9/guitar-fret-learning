"""Plot an approved paired guitar-Z trial from saved data; never simulates."""
import argparse
import json
from pathlib import Path
from types import SimpleNamespace

import matplotlib.pyplot as plt


COLORS = {"h0": "#2563a6", "z5": "#d97706"}
LABELS = {"h0": "H0", "z5": "Initial guitar Z +5 mm"}


def read_json(path):
    return json.loads(path.read_text())


def plot_timeline(results_root, output):
    comparison = read_json(results_root / "comparison.json")
    traces = {name: read_json(results_root / name / "trace.json") for name in ("h0", "z5")}
    fig, axes = plt.subplots(3, 1, figsize=(12.5, 8.2), sharex=True)

    ax = axes[0]
    h0 = traces["h0"]
    z5 = traces["z5"]
    ax.plot([s["time_s"] for s in h0], [s["position_error_m"] * 1000 for s in h0],
            color=COLORS["h0"], label="H0 vs H0 goal")
    ax.plot([s["time_s"] for s in z5], [s["position_error_m"] * 1000 for s in z5],
            color=COLORS["z5"], label="+5 mm vs raised goal")
    ax.plot([s["time_s"] for s in z5], [s["source_position_error_m"] * 1000 for s in z5],
            color=COLORS["z5"], ls="--", label="+5 mm vs original H0 goal")
    ax.set_ylabel("Position error (mm)")
    ax.set_title("Per-trial target error and deviation from original goal")
    ax.grid(True, alpha=.25)
    ax.legend(fontsize=8)

    ax = axes[1]
    for name, trace in traces.items():
        ax.plot([s["time_s"] for s in trace], [s["rotation_error_deg"] for s in trace],
                color=COLORS[name], label=LABELS[name])
    ax.set_ylabel("Rotation error (deg)")
    ax.grid(True, alpha=.25)
    ax.legend(fontsize=8)

    ax = axes[2]
    for name, trace in traces.items():
        ax.plot([s["time_s"] for s in trace], [s["strap_length_m"] for s in trace],
                color=COLORS[name], label=f"{LABELS[name]} route")
    rest_length = comparison["rows"][0]["absolute_rest_length_m"]
    ax.axhline(rest_length, color="#444", ls="--", lw=1, label="Shared absolute rest length")
    ax.set_ylabel("Strap route (m)")
    ax.set_xlabel("Time (s)")
    ax.grid(True, alpha=.25)
    ax.legend(fontsize=8)

    fig.suptitle("Paired native CPU PhysX diagnostic — 240 Hz, 24 steps, 0.1 s", fontsize=12)
    fig.text(.5, .01,
             "H0 max applied strap tension: 0 N; +5 mm: 0 N. Curves are saved traces; this is not a stability-success plot.",
             ha="center", fontsize=8)
    fig.tight_layout(rect=(0, .035, 1, .96), h_pad=1.0)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=170, bbox_inches="tight")
    plt.close(fig)


def plot_initial_source_geometry(results_root, output):
    # Replay the saved t=0 body poses into the CPU source-geometry probe; no dynamics are stepped.
    import numpy as np
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from stability_adapter_2.plot_physx_contacts import source_surfaces
    from stability_adapter_2.initial_overlap import build_probe

    comparisons = read_json(results_root / "comparison.json")["rows"]
    config = read_json(Path(__file__).resolve().parent / "config.json")
    fig = plt.figure(figsize=(13, 6.7))
    gathered = []
    for index, name in enumerate(("h0", "z5"), start=1):
        run = results_root / name
        report = read_json(run / "report.json")
        initial_state = next(s for s in read_json(run / "states.json") if s["physics_step"] == 0)
        body_names = [report["human_body_names"], report["guitar_body_names"]]
        body_states = [initial_state["human_body_states"], initial_state["guitar_body_states"]]
        scene = SimpleNamespace(config=config, human=0, guitar=1, env=None,
                                gym=SimpleNamespace(get_actor_rigid_body_names=
                                    lambda _env, actor: body_names[actor]),
                                bodies=lambda actor: body_states[actor])
        model, data, shapes = build_probe(scene)
        surfaces, negative_ids, witnesses, query = source_surfaces(model, data, shapes)
        gathered.append((name, surfaces, negative_ids, witnesses, query, comparisons[index - 1]))

    all_points = np.concatenate([triangles.reshape(-1, 3)
                                 for _, surfaces, *_ in gathered
                                 for triangles, _shape in surfaces])
    focus_points = np.concatenate([triangles.reshape(-1, 3)
                                   for _, surfaces, *_ in gathered
                                   for triangles, shape in surfaces if shape["actor"] == "guitar"])
    center = (focus_points.min(axis=0) + focus_points.max(axis=0)) / 2
    half = max(float(np.ptp(all_points, axis=0).max()) * .32, .32)

    for panel, (name, surfaces, negative_ids, witnesses, query, row) in enumerate(gathered, start=1):
        ax = fig.add_subplot(1, 2, panel, projection="3d")
        for triangles, shape in surfaces:
            actor = shape["actor"]
            color = ("#dc2626" if shape["geom_id"] in negative_ids else
                     "#2563eb" if actor == "guitar" else "#a8b0bb")
            ax.add_collection3d(Poly3DCollection(triangles, facecolors=color,
                                                 alpha=.55, edgecolors="none"))
        if witnesses.size:
            points = witnesses.reshape(-1, 3)
            ax.scatter(points[:, 0], points[:, 1], points[:, 2], color="#111827",
                       marker="x", s=14, label="query witnesses")
        ax.set(xlim=(center[0] - half, center[0] + half),
               ylim=(center[1] - half, center[1] + half),
               zlim=(center[2] - half, center[2] + half),
               xlabel="World X (m)", ylabel="World Y (m)", zlabel="World Z (m)")
        ax.set_box_aspect((1, 1, 1))
        ax.view_init(elev=19, azim=36)
        ax.set_title(f"{LABELS[name]} · saved t=0 pose\n"
                     f"stored source-query negative pairs: {row['source_initial_negative_pair_count']}")
    fig.suptitle("Initial source collision shapes reconstructed from saved poses — not Isaac Gym render", fontsize=12)
    fig.text(.5, .02,
             "Gray: humanoid source shapes | Blue: guitar | Red: shapes in negative source-query pairs | "
             "×: query witnesses. CPU geometry reconstruction only; no physics stepping.",
             ha="center", fontsize=8)
    fig.tight_layout(rect=(0, .06, 1, .92))
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-root", type=Path, required=True,
                        help="directory containing comparison.json and h0/z5 raw run folders")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    plot_timeline(args.results_root, args.output_dir / "guitar_z_trial_v1_timeline.png")
    plot_initial_source_geometry(args.results_root,
                                 args.output_dir / "guitar_z_trial_v1_source_geometry_t0.png")


if __name__ == "__main__":
    main()
