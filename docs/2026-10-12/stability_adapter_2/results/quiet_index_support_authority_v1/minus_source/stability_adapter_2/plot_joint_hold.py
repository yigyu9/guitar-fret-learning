"""Plot saved joint-hold OFF/ON traces and source shapes; never runs physics."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import matplotlib.pyplot as plt
import numpy as np


def read_json(path):
    return json.loads(path.read_text())


def plot_trace(results_dir, output):
    comparison = read_json(results_dir / "comparison.json")
    colors = {"off": "#2563a6", "on": "#d97706"}
    fig, axes = plt.subplots(2, 2, figsize=(13, 8.5))
    duration_dir = results_dir / "hold_1s"
    for mode in ("off", "on"):
        run = duration_dir / mode
        trace = read_json(run / "trace.json")
        states = read_json(run / "states.json")
        controls = read_json(run / "controls.json")
        report = read_json(run / "report.json")
        color = colors[mode]
        label = mode.upper()
        t = np.asarray([s["time_s"] for s in trace])
        axes[0, 0].plot(t, [s["position_error_m"] * 1000 for s in trace],
                        color=color, label=label)
        axes[0, 1].plot(t, [s["rotation_error_deg"] for s in trace],
                        color=color, label=label)
        arm = report["arm_indices"]
        initial = np.asarray(report["initial_joint_targets_rad"])[arm]
        actual = np.asarray([[d["pos"] for d in state["human_dof_states"]]
                             for state in states])[:, arm]
        drift = np.rad2deg(np.abs(actual - initial[None, :])).max(axis=1)
        state_t = np.asarray([s["physics_step"] / report["physics_hz"] for s in states])
        axes[1, 0].plot(state_t, drift, color=color, label=label)
        control_t = np.asarray([(c["physics_step"] - 1) / report["physics_hz"] for c in controls])
        delta = np.asarray([np.max(np.abs(c["applied_delta_rad"])) for c in controls])
        saturated = np.asarray([any(c["saturated"]) for c in controls])
        delta_deg = np.rad2deg(delta)
        axes[1, 1].plot(control_t, delta_deg, color=color, label=f"{label} applied δ")
        axes[1, 1].scatter(control_t[saturated], delta_deg[saturated], color=color,
                           marker="x", s=18, label=f"{label} saturated physics sample")
    axes[0, 0].set(title="Guitar position error to candidate goal", ylabel="Error (mm)")
    axes[0, 1].set(title="Guitar rotation error to candidate goal", ylabel="Error (degrees)")
    axes[1, 0].set(title="Maximum raw arm actual − original target drift",
                   ylabel="Max |drift| (degrees)", xlabel="Time (s)")
    axes[1, 1].set(title="Applied arm target correction", ylabel="Max |δ| (degrees)",
                   xlabel="Time (s)")
    cap_deg = np.rad2deg(.15)
    axes[1, 1].axhline(cap_deg, color="#555", ls="--", lw=1,
                       label="±0.15 rad cap magnitude")
    for ax in axes.flat:
        ax.grid(True, alpha=.25)
        ax.set_xlim(0, 1)
        ax.legend(fontsize=8, frameon=False)
    fig.suptitle("1.0 s saved CPU PhysX comparison — joint-error target correction, not stability success")
    fig.text(.5, .012,
             "Saturation marks are repeated held values at 240 Hz, not independent 60 Hz updates. "
             "The position/rotation curves use each run's candidate guitar goal; no guitar-error feedback is used.",
             ha="center", fontsize=8)
    fig.tight_layout(rect=(0, .04, 1, .95))
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(output)
    fig.savefig(output, dpi=160, bbox_inches="tight")
    plt.close(fig)


def geometry_snapshot(run, step):
    # environment imports Gym before MuJoCo in this saved-source replay path.
    import stability_adapter_2.environment  # noqa: F401
    from stability_adapter_2.plot_neck_palm import geometry as palm_geometry
    from stability_adapter_2.plot_physx_contacts import source_surfaces
    from stability_adapter_2.replay_contact_geometry import recorded_probe

    model, data, shapes = recorded_probe(run, step)
    surfaces, _, _, _ = source_surfaces(model, data, shapes)
    palms = {}
    for side, prefix in (("L", "LH"), ("R", "RH")):
        shape = next(s for s in shapes if s["actor"] == "human" and s["body"] == f"{prefix}:palm")
        center = palm_geometry(model, data, shape).center_mass
        def body_pos(name):
            return data.xpos[model.body("human/" + name).id].copy()
        wrist, middle = body_pos(f"{side}_Wrist"), body_pos(f"{prefix}:middle1")
        index, pinky = body_pos(f"{prefix}:index1"), body_pos(f"{prefix}:pinky1")
        normal = np.cross(middle - wrist, index - pinky)
        normal /= max(float(np.linalg.norm(normal)), 1e-12)
        palms[side] = (center, normal)
    return surfaces, palms


def plot_geometry(results_dir, output):
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    panels = [("shared initial", "short", "off", 0)]
    panels += [(f"{seconds:g}s {mode.upper()}", group, mode, step)
               for seconds, group, step in ((.5, "hold_05s", 120), (1., "hold_1s", 240))
               for mode in ("off", "on")]
    snapshots, extents = [], []
    for title, group, mode, step in panels:
        run = results_dir / group / mode
        surfaces, palms = geometry_snapshot(run, step)
        trace = read_json(run / "trace.json")
        sample = trace[step]
        route = np.asarray(sample["route_points_m"], dtype=float)
        visible = []
        for triangles, shape in surfaces:
            actor, body = shape["actor"], shape["body"]
            if actor == "guitar" or body.startswith(("LH:", "RH:")) or body in (
                    "L_Wrist", "R_Wrist", "L_Elbow", "R_Elbow", "L_Shoulder", "R_Shoulder",
                    "L_Thorax", "R_Thorax"):
                visible.append((triangles, shape))
                extents.append(triangles.reshape(-1, 3))
        extents.extend([route, *(center[None, :] for center, _ in palms.values())])
        snapshots.append((title, visible, palms, route,
                          sample["position_error_m"] * 1000, sample["rotation_error_deg"]))
    points = np.concatenate(extents)
    center = (points.min(0) + points.max(0)) / 2
    half = float(np.ptp(points, axis=0).max()) / 2 + .05
    fig = plt.figure(figsize=(17, 10))
    for i, (title, surfaces, palms, route, pos_mm, rot_deg) in enumerate(snapshots, 1):
        ax = fig.add_subplot(2, 3, i, projection="3d")
        for triangles, shape in surfaces:
            body = shape["body"]
            if shape["actor"] == "guitar":
                color, alpha = "#2563eb", .80
            elif body.startswith("LH:") or body == "L_Wrist":
                color, alpha = "#16a34a", .88
            elif body.startswith("RH:") or body == "R_Wrist":
                color, alpha = "#c026d3", .82
            else:
                color, alpha = "#9ca3af", .28
            ax.add_collection3d(Poly3DCollection(triangles, facecolors=color,
                                                 alpha=alpha, edgecolors="none"))
        ax.plot(route[:, 0], route[:, 1], route[:, 2], color="#111827", ls="--",
                lw=1.7, marker=".", ms=2, label="saved strap route")
        for side, (palm, normal) in palms.items():
            color = "#16a34a" if side == "L" else "#c026d3"
            ax.scatter(*palm, color=color, s=24, depthshade=False)
            ax.quiver(*palm, *(normal * .06), color=color, linewidth=1.5,
                      arrow_length_ratio=.25)
        ax.set(xlim=(center[0]-half, center[0]+half),
               ylim=(center[1]-half, center[1]+half),
               zlim=(center[2]-half, center[2]+half),
               xlabel="World X (m)", ylabel="World Y (m)", zlabel="World Z (m)")
        ax.set_box_aspect((1, 1, 1))
        ax.view_init(elev=18, azim=110)
        ax.set_title(f"{title}\nfinal candidate error {pos_mm:.1f} mm / {rot_deg:.1f}°")
    fig.suptitle("Saved native poses reconstructed from source collision shapes — not Isaac/PhysX renderer", y=.98)
    fig.text(.5, .015,
             "Blue: guitar | green/magenta: left/right hand source shapes | gray: remaining upper body | "
             "dashed: recorded strap route | arrows: palm-normal proxies (anatomical sign unverified). "
             "Identical world bounds and camera; reconstruction is not contact/clearance certification.",
             ha="center", fontsize=8)
    fig.tight_layout(rect=(0, .045, 1, .95), w_pad=.4)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(output)
    fig.savefig(output, dpi=145, bbox_inches="tight")
    plt.close(fig)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def geometry_asset_paths():
    config_path = Path(__file__).with_name("config.json").resolve()
    config = read_json(config_path)
    root = Path(__file__).resolve().parents[1]
    paths = {config_path}
    for key in ("humanoid_asset", "guitar_asset"):
        xml_path = (root / config[key]).resolve()
        paths.add(xml_path)
        xml_root = ET.parse(xml_path).getroot()
        compiler = xml_root.find("compiler")
        meshdir = xml_path.parent / (compiler.get("meshdir", "") if compiler is not None else "")
        for mesh in xml_root.findall("./asset/mesh"):
            paths.add((meshdir / mesh.attrib["file"]).resolve())
    return sorted(path for path in paths if path.is_file())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--manifest-path", type=Path)
    args = parser.parse_args()
    images_dir = args.out_dir / "images"
    manifest_path = args.manifest_path or args.out_dir / "plot_manifest.json"
    if images_dir.exists() or manifest_path.exists():
        raise FileExistsError(f"preserve existing plot outputs: {images_dir}, {manifest_path}")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    images = images_dir
    plot_trace(args.results_dir, images / "joint_hold_v1_1s_off_on.png")
    plot_geometry(args.results_dir, images / "joint_hold_v1_source_pose_comparison.png")
    inputs = [args.results_dir / "comparison.json"]
    run_dirs = [args.results_dir / group / mode
                for group in ("short", "hold_05s", "hold_1s")
                for mode in ("off", "on")]
    inputs += [run / name for run in run_dirs
               for name in ("report.json", "trace.json", "states.json", "contacts.json", "controls.json")]
    helpers = [Path(__file__).resolve(), Path(__file__).with_name("plot_physx_contacts.py"),
               Path(__file__).with_name("replay_contact_geometry.py"),
               Path(__file__).with_name("plot_neck_palm.py"),
               Path(__file__).with_name("initial_overlap.py"), Path(__file__).with_name("environment.py")]
    manifest = {
        "purpose": "plots only; no native simulation or raw result edits",
        "inputs_sha256": {str(p.resolve()): sha256(p) for p in sorted(inputs)},
        "plot_sources_sha256": {str(p.resolve()): sha256(p) for p in helpers},
        "source_geometry_assets_sha256": {
            str(p): sha256(p) for p in geometry_asset_paths()},
        "embedded_source_hashes": read_json(args.results_dir / "comparison.json")["input_sha256"],
        "outputs_sha256": {str(p.resolve()): sha256(p) for p in sorted(images.glob("*.png"))},
    }
    if manifest_path.exists():
        raise FileExistsError(manifest_path)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
