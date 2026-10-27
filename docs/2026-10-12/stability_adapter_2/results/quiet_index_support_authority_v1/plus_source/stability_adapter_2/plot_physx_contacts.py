"""Plot recorded H0 contact diagnostics and source shapes without rerunning physics."""
import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt


def read_json(path):
    return json.loads(path.read_text())


def body_pair(contact):
    return contact.get("body0_name", ""), contact.get("body1_name", "")


def plot_timeline(run, output):
    report = read_json(run / "report.json")
    trace = read_json(run / "trace.json")
    contacts = read_json(run / "contacts.json")
    states = read_json(run / "states.json")
    names = report["human_joint_names"]
    target = report["initial_joint_targets_rad"]
    hip_indices = [names.index(name) for name in ("L_Hip_x", "L_Hip_y", "L_Hip_z")]
    hip_target = [target[i] for i in hip_indices]
    time_trace = [sample["time_s"] for sample in trace]

    fig, axes = plt.subplots(3, 1, figsize=(13, 10), sharex=True,
                             gridspec_kw={"height_ratios": [1.1, 1, 1.15]})
    ax_pos = axes[0]
    position_mm = [sample["position_error_m"] * 1000 for sample in trace]
    rotation_deg = [sample["rotation_error_deg"] for sample in trace]
    ax_pos.plot(time_trace, position_mm, color="#2563a6", marker="o", ms=2.6,
                label="Guitar position error")
    ax_rot = ax_pos.twinx()
    ax_rot.plot(time_trace, rotation_deg, color="#d97706", marker=".", ms=3,
                label="Guitar rotation error")
    ax_pos.set_ylabel("Position error (mm)")
    ax_rot.set_ylabel("Rotation error (deg)")
    ax_pos.set_title("Recorded H0 CPU PhysX diagnostic — 240 Hz, 24 steps, 0.1 s")
    ax_pos.grid(True, alpha=.25)
    lines = ax_pos.get_lines() + ax_rot.get_lines()
    ax_pos.legend(lines, [line.get_label() for line in lines], loc="upper left")

    state_times, hip_delta = [], [[], [], []]
    for state in states:
        state_times.append(state["physics_step"] / report["physics_hz"])
        dof = state["human_dof_states"]
        for axis, index in enumerate(hip_indices):
            hip_delta[axis].append((dof[index]["pos"] - hip_target[axis]) * 180 / 3.141592653589793)
    for label, values, color in zip(("L_Hip_x", "L_Hip_y", "L_Hip_z"), hip_delta,
                                    ("#2563a6", "#d97706", "#24835b")):
        axes[1].plot(state_times, values, label=label, color=color, marker=".", ms=3)
    axes[1].set_ylabel("L_Hip actual − target (deg)")
    axes[1].grid(True, alpha=.25)
    axes[1].legend(loc="upper left", ncol=3)

    selected = {
        ("guitar/G:body", "human/R_Hip"): ("G:body × R_Hip", "#b91c1c", "o"),
        ("guitar/guitar", "human/L_Knee"): ("guitar × L_Knee", "#7c3aed", "s"),
        ("human/R_Ankle", "ground"): ("R_Ankle × ground", "#0891b2", "^"),
        ("human/R_Toe", "ground"): ("R_Toe × ground", "#0f766e", "v"),
    }
    seen = set()
    for row in contacts:
        for contact in row["contacts"]:
            pair = body_pair(contact)
            reverse = pair[::-1]
            key = pair if pair in selected else reverse if reverse in selected else None
            if key is None:
                continue
            label, color, marker = selected[key]
            axes[2].scatter(row["time_s"], contact["initialOverlap"] * 1000,
                            color=color, marker=marker, s=28, alpha=.8,
                            label=label if key not in seen else None)
            seen.add(key)
    axes[2].axhline(0, color="black", lw=.8)
    axes[2].set_ylabel("Raw initialOverlap (mm)")
    axes[2].set_xlabel("Recorded time (s)")
    axes[2].grid(True, alpha=.25)
    axes[2].legend(loc="best", ncol=2, fontsize=8)

    impact_time = 12 / report["physics_hz"]
    for ax in axes:
        ax.axvline(impact_time, color="#555", linestyle="--", lw=1, alpha=.7)
    axes[0].annotate("step 11→12 jump\n5.183→60.272 mm; 0.690→6.319°",
                     xy=(impact_time, position_mm[12]), xytext=(.055, max(position_mm) * .45),
                     arrowprops={"arrowstyle": "->", "color": "#555"}, fontsize=8)
    fig.text(.5, .012,
             "Strap applied tension: max 0 N over 24 physics steps. Contact remains present; "
             "lambda units are uncalibrated. initialOverlap is raw native signed gap (step-start sample); "
             "minDist is target distance, not clearance.", ha="center", fontsize=8)
    fig.tight_layout(rect=(0, .04, 1, 1))
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=160, bbox_inches="tight")
    plt.close(fig)


def source_surfaces(model, data, shapes):
    import numpy as np
    from scipy.spatial import ConvexHull
    import trimesh
    from .initial_overlap import mujoco, query_pairs

    surfaces = []
    for shape in shapes:
        geom_id = shape["geom_id"]
        kind = model.geom_type[geom_id]
        if kind == mujoco.mjtGeom.mjGEOM_MESH:
            mesh_id = model.geom_dataid[geom_id]
            start, count = model.mesh_vertadr[mesh_id], model.mesh_vertnum[mesh_id]
            vertices = model.mesh_vert[start:start + count]
            faces = ConvexHull(vertices).simplices
        elif kind == mujoco.mjtGeom.mjGEOM_BOX:
            mesh = trimesh.creation.box(extents=2 * model.geom_size[geom_id])
            vertices, faces = mesh.vertices, mesh.faces
        elif kind == mujoco.mjtGeom.mjGEOM_CAPSULE:
            mesh = trimesh.creation.capsule(radius=model.geom_size[geom_id, 0],
                                            height=2 * model.geom_size[geom_id, 1], count=[8, 8])
            vertices, faces = mesh.vertices - mesh.bounds.mean(0), mesh.faces
        else:
            continue
        vertices = vertices @ data.geom_xmat[geom_id].reshape(3, 3).T + data.geom_xpos[geom_id]
        surfaces.append((vertices[faces], shape))
    result = query_pairs(model, data, shapes)
    negative_ids = {pair[k] for pair in result["pairs_within_limit"]
                    if pair["signed_gap_m"] < -1e-7
                    for k in ("human_geom_id", "guitar_geom_id")}
    negative_points = [pair["witness_points_m"] for pair in result["pairs_within_limit"]
                       if pair["signed_gap_m"] < -1e-7]
    return surfaces, negative_ids, np.asarray(negative_points, dtype=float), result


def plot_source_geometry(results_root, output):
    # Import order is deliberate: environment loads Gym before MuJoCo.
    from .replay_contact_geometry import recorded_probe
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    import numpy as np

    run = results_root / "h0_detailed"
    steps = (0, 11)
    fig = plt.figure(figsize=(13, 6.5))
    for panel, step in enumerate(steps, start=1):
        model, data, shapes = recorded_probe(run, step)
        surfaces, negative_ids, witnesses, query = source_surfaces(model, data, shapes)
        ax = fig.add_subplot(1, 2, panel, projection="3d")
        all_points, guitar_points = [], []
        for triangles, shape in surfaces:
            actor = shape["actor"]
            color = ("#dc2626" if shape["geom_id"] in negative_ids else
                     "#2563eb" if actor == "guitar" else "#a8b0bb")
            ax.add_collection3d(Poly3DCollection(triangles, facecolors=color,
                                                 alpha=.56, edgecolors="none"))
            flat = triangles.reshape(-1, 3)
            all_points.append(flat)
            if actor == "guitar":
                guitar_points.append(flat)
        if len(witnesses):
            witness_points = witnesses.reshape(-1, 3)
            ax.scatter(witness_points[:, 0], witness_points[:, 1], witness_points[:, 2],
                       color="#111827", s=12, marker="x", label="source-query witness")
        focus = np.concatenate(guitar_points)
        center = (focus.min(axis=0) + focus.max(axis=0)) / 2
        half = max(float(np.ptp(np.concatenate(all_points), axis=0).max()) * .32, .32)
        ax.set(xlim=(center[0]-half, center[0]+half),
               ylim=(center[1]-half, center[1]+half),
               zlim=(center[2]-half, center[2]+half),
               xlabel="World X (m)", ylabel="World Y (m)", zlabel="World Z (m)")
        ax.set_box_aspect((1, 1, 1))
        ax.view_init(elev=19, azim=36)
        time_s = step / 240
        ax.set_title(f"Recorded native poses: step {step}, t={time_s:.6f} s\n"
                     f"source query negative pairs: {query['negative_gap_pair_count']}")
    fig.suptitle("Source collision-geometry replay at recorded states — not an Isaac Gym render",
                 fontsize=12)
    fig.text(.5, .025,
             "Gray: humanoid source collision shapes | Blue: guitar | Red: shapes in negative source-query pairs | "
             "×: source-query witnesses. Reconstructed from saved states; no native dynamics run.",
             ha="center", fontsize=8)
    fig.tight_layout(rect=(0, .06, 1, .92))
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True,
                        help="h0_detailed directory containing report/trace/contacts/states")
    parser.add_argument("--results-root", type=Path, required=True,
                        help="physx_contact_v1 directory containing source_replay.json")
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    plot_timeline(args.run, args.out_dir / "physx_contact_v1_timeline.png")
    plot_source_geometry(args.results_root, args.out_dir / "physx_contact_v1_source_geometry_t0_step11.png")


if __name__ == "__main__":
    main()
