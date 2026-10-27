"""Plot saved pose/strap native traces and source geometry; never runs simulation."""
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib.pyplot as plt


COLORS = {
    "legacy": "#475569",
    "route-fit, 0 N preload": "#2563eb",
    "route-fit reference": "#2563eb",
    "5 N preload": "#0f766e",
    "10 N preload": "#7c3aed",
    "20 N preload": "#dc2626",
    "L_Shoulder_x −0.025 rad": "#d97706",
    "L_Shoulder_x +0.025 rad": "#16a34a",
}


def load_traces(rows):
    result = {}
    for row in rows:
        result[(row["group"], row["name"], row["duration_s"])] = json.loads(
            (Path(row["run"]) / "trace.json").read_text())
    return result


def condition_label(row):
    if row["group"] == "strap":
        return {
            "legacy": "legacy",
            "load_00n": "route-fit, 0 N preload",
            "load_05n": "5 N preload",
            "load_10n": "10 N preload",
            "load_20n": "20 N preload",
        }[row["name"]]
    if row["name"] in {"L_Shoulder_x_plus", "L_Shoulder_x_minus"}:
        return row["name"].replace("_minus", " −0.025 rad").replace("_plus", " +0.025 rad")
    if row["name"] == "reference":
        return "route-fit reference"
    if row["name"] == "legacy":
        return "legacy"
    if row["name"].startswith("load_"):
        force = row["name"].replace("load_", "").replace("n", " N")
        return force + " preload"
    return row["name"]


def plot_curves(rows, traces, output):
    strap_rows = [r for r in rows if r["group"] == "strap"]
    half_rows = [r for r in rows if r["group"] == "hold_05s" and
                 (r["name"] in {"reference", "legacy", "load_20n",
                                "L_Shoulder_x_plus", "L_Shoulder_x_minus"})]
    full_rows = [r for r in rows if r["group"] == "hold_1s" and
                 r["name"] in {"reference", "legacy", "load_10n", "load_20n"}]
    fig, axes = plt.subplots(3, 1, figsize=(13, 12), sharex=False)
    panels = [
        (axes[0], strap_rows, "0.1 s native strap settings"),
        (axes[1], half_rows, "0.5 s hold: reference, legacy, preload and shoulder perturbations"),
        (axes[2], full_rows, "1.0 s hold: persistent tracking degradation"),
    ]
    for ax, panel_rows, title in panels:
        axr = ax.twinx()
        for row in panel_rows:
            label = condition_label(row)
            color = COLORS.get(label, "#0891b2")
            samples = traces[(row["group"], row["name"], row["duration_s"])]
            times = [s["time_s"] for s in samples]
            pos = [s["position_error_m"] * 1000 for s in samples]
            rot = [s["rotation_error_deg"] for s in samples]
            ax.plot(times, pos, color=color, lw=1.8,
                    label=f"{label} · max {max(pos):.1f} mm")
            axr.plot(times, rot, color=color, lw=1.35, ls="--",
                     label=f"{label} · max {max(rot):.2f}°")
        ax.set_title(title)
        ax.set_ylabel("Position error (mm)")
        axr.set_ylabel("Rotation error (degrees)")
        ax.grid(True, alpha=.23)
        ax.set_xlabel("Time (s)")
        left_lines, left_labels = ax.get_legend_handles_labels()
        right_lines, right_labels = axr.get_legend_handles_labels()
        ax.legend(left_lines + right_lines, left_labels + right_labels,
                  frameon=False, ncol=2, fontsize=8, loc="upper left")
    fig.suptitle("Saved CPU PhysX trials — guitar tracking, not stability success", fontsize=14)
    fig.text(.5, .008,
             "Solid: position error to each run's candidate guitar goal. Dashed: rotation error. "
             "Initial lower-body pose and physical dynamics are retained in all trials.",
             ha="center", fontsize=8)
    fig.tight_layout(rect=(0, .035, 1, .97), h_pad=1.5)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=160, bbox_inches="tight")
    plt.close(fig)


def _body_position(model, data, name):
    return data.xpos[model.body("human/" + name).id].copy()


def _palm_and_normal(model, data, shapes, side, palm_geometry):
    palm_name = "LH:palm" if side == "L" else "RH:palm"
    palm_shape = next(s for s in shapes if s["actor"] == "human" and s["body"] == palm_name)
    palm_center = palm_geometry(model, data, palm_shape).center_mass
    prefix = "LH" if side == "L" else "RH"
    wrist = _body_position(model, data, f"{side}_Wrist")
    middle = _body_position(model, data, f"{prefix}:middle1")
    index = _body_position(model, data, f"{prefix}:index1")
    pinky = _body_position(model, data, f"{prefix}:pinky1")
    normal = __import__("numpy").cross(middle - wrist, index - pinky)
    norm = float(__import__("numpy").linalg.norm(normal))
    if norm > 1e-8:
        normal = normal / norm
    return palm_center, normal if norm > 1e-8 else None


def plot_reference_geometry(results_dir, output):
    # Load Gym before MuJoCo, as required by the saved-pose source-geometry helpers.
    import stability_adapter_2.environment  # noqa: F401
    from stability_adapter_2.plot_neck_palm import geometry as palm_geometry
    from stability_adapter_2.plot_physx_contacts import source_surfaces
    from stability_adapter_2.replay_contact_geometry import recorded_probe
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    import numpy as np

    run = results_dir / "hold_1s" / "reference"
    report = json.loads((run / "report.json").read_text())
    traces = json.loads((run / "trace.json").read_text())
    steps = (0, 120, 240)
    snapshots, bound_points = [], []
    for step in steps:
        model, data, shapes = recorded_probe(run, step)
        surfaces, _, _, _ = source_surfaces(model, data, shapes)
        palms = {side: _palm_and_normal(model, data, shapes, side, palm_geometry)
                 for side in ("L", "R")}
        sample = min(traces, key=lambda s: abs(s["time_s"] - step / report["physics_hz"]))
        route = np.asarray(sample["route_points_m"], dtype=float)
        snapshot = {"surfaces": surfaces, "palms": palms, "route": route,
                    "position_error_m": sample["position_error_m"],
                    "rotation_error_deg": sample["rotation_error_deg"]}
        snapshots.append(snapshot)
        bound_points.extend([tri.reshape(-1, 3) for tri, _ in surfaces])
        bound_points.extend([route, *(p[0][None, :] for p in palms.values())])

    bounds = np.concatenate(bound_points)
    center = (bounds.min(0) + bounds.max(0)) / 2
    half = float(np.ptp(bounds, axis=0).max()) / 2 + .06
    colors = {"L": "#16a34a", "R": "#c026d3"}
    fig = plt.figure(figsize=(17, 6.8))
    for panel, (step, snapshot) in enumerate(zip(steps, snapshots), start=1):
        ax = fig.add_subplot(1, 3, panel, projection="3d")
        for triangles, shape in snapshot["surfaces"]:
            body = shape["body"]
            if shape["actor"] == "guitar":
                color, alpha = "#2563eb", .75
            elif body.startswith("LH:") or body == "L_Wrist":
                color, alpha = colors["L"], .82
            elif body.startswith("RH:") or body == "R_Wrist":
                color, alpha = colors["R"], .82
            else:
                color, alpha = "#9ca3af", .12
            ax.add_collection3d(Poly3DCollection(
                triangles, facecolors=color, alpha=alpha, edgecolors="none"))
        route = snapshot["route"]
        ax.plot(route[:, 0], route[:, 1], route[:, 2], color="#111827", lw=2.2,
                ls="--", marker=".", ms=3, label="saved strap route")
        for side, (palm, normal) in snapshot["palms"].items():
            color = colors[side]
            ax.scatter(*palm, color=color, s=30, depthshade=False,
                       label=f"{side} palm center")
            if normal is not None:
                ax.quiver(*palm, *(normal * .10), color=color, linewidth=2,
                          arrow_length_ratio=.24, label=f"{side} normal proxy")
        ax.set(xlim=(center[0]-half, center[0]+half),
               ylim=(center[1]-half, center[1]+half),
               zlim=(center[2]-half, center[2]+half),
               xlabel="World X (m)", ylabel="World Y (m)", zlabel="World Z (m)")
        ax.set_box_aspect((1, 1, 1))
        ax.view_init(elev=19, azim=110)
        seconds = step / report["physics_hz"]
        ax.set_title(f"Reference saved pose · t={seconds:g} s\n"
                     f"candidate-goal error {snapshot['position_error_m']*1000:.1f} mm / "
                     f"{snapshot['rotation_error_deg']:.1f}°")
        if panel == 1:
            ax.legend(loc="upper left", fontsize=7, frameon=False)
    fig.suptitle("Reference hand–guitar geometry and routed strap at saved native poses", fontsize=13)
    fig.text(.5, .018,
             "Blue: guitar | Green/magenta: left/right hand source shapes | Gray: remaining humanoid | "
             "dashed: saved strap route | arrows: palm-normal proxies (anatomical sign unverified). "
             "Same world bounds/view. CPU source-geometry reconstruction, not Isaac/PhysX render or contact validation.",
             ha="center", fontsize=8)
    fig.tight_layout(rect=(0, .06, 1, .92), w_pad=.5)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150, bbox_inches="tight")
    plt.close(fig)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest_paths(comparison_path, rows, results_dir):
    paths = {Path(__file__).resolve(),
             Path(__file__).with_name("plot_physx_contacts.py").resolve(),
             Path(__file__).with_name("replay_contact_geometry.py").resolve(),
             Path(__file__).with_name("initial_overlap.py").resolve(),
             Path(__file__).with_name("environment.py").resolve(),
             Path(__file__).with_name("control.py").resolve(),
             Path(__file__).with_name("strap.py").resolve(),
             Path(__file__).with_name("trial_settings.py").resolve(),
             Path(__file__).with_name("physics_presets.py").resolve(),
             Path(__file__).with_name("config.json").resolve(),
             Path(__file__).with_name("plot_neck_palm.py").resolve(),
             comparison_path.resolve()}
    for row in rows:
        run = Path(row["run"])
        paths.add((run / "trace.json").resolve())
    geometry_run = results_dir / "hold_1s" / "reference"
    paths.update((geometry_run / n).resolve() for n in ("report.json", "states.json", "trace.json"))
    config = json.loads(Path(__file__).with_name("config.json").read_text())
    root = Path(__file__).resolve().parents[1]
    for key in ("humanoid_asset", "guitar_asset", "pose_source"):
        asset = (root / config[key]).resolve()
        paths.add(asset)
        if asset.suffix == ".xml":
            xml = ET.parse(asset).getroot()
            compiler = xml.find("compiler")
            meshdir = asset.parent / (compiler.get("meshdir", "") if compiler is not None else "")
            for mesh in xml.findall("./asset/mesh"):
                paths.add((meshdir / mesh.attrib["file"]).resolve())
    return sorted(p for p in paths if p.is_file())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--curve-output", type=Path, required=True)
    parser.add_argument("--geometry-output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    for path in (args.curve_output, args.geometry_output, args.manifest):
        if path.exists():
            parser.error(f"refusing to overwrite existing artifact: {path}")
    comparison = json.loads(args.comparison.read_text())
    rows = comparison["rows"]
    traces = load_traces(rows)
    plot_curves(rows, traces, args.curve_output)
    plot_reference_geometry(args.results_dir, args.geometry_output)
    input_paths = manifest_paths(args.comparison, rows, args.results_dir)
    payload = {
        "purpose": "read-only plots from saved comparison/traces/native states; no rollout",
        "plot_script": str(Path(__file__).resolve()),
        "input_hashes_sha256": {str(p): sha256(p) for p in input_paths},
        "outputs_sha256": {str(p.resolve()): sha256(p) for p in
                           (args.curve_output, args.geometry_output)},
        "native_trace_count": len(rows),
        "geometry_run": str((args.results_dir / "hold_1s" / "reference").resolve()),
        "geometry_steps": [0, 120, 240],
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(payload, indent=2) + "\n")


if __name__ == "__main__":
    main()
