"""Plot saved right-clearance v3 runs and source shapes; no native simulation."""
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


RUNS = ("reference", "ty015_sx010", "ty0175_sx015", "ty0175_sx0175")
COLORS = {"reference": "#475569", "ty015_sx010": "#0284c7",
          "ty0175_sx015": "#d97706", "ty0175_sx0175": "#dc2626"}


def read_json(path):
    return json.loads(path.read_text())


def rows_by_name(comparison):
    return {row["name"]: row for row in comparison["rows"]}


def shoulder_events(contacts):
    events = []
    for sample in contacts:
        for contact in sample["contacts"]:
            pair = {contact.get("body0_name"), contact.get("body1_name")}
            if "human/R_Shoulder" in pair and any(str(n).startswith("guitar/") for n in pair):
                events.append((sample["time_s"], sample["physics_step"], contact["initialOverlap"]))
    return events


def plot_curves(runs, output):
    fig, axes = plt.subplots(2, 1, figsize=(12, 8.3), sharex=True)
    event_times = {}
    for name in RUNS:
        trace = read_json(runs[name] / "trace.json")
        contacts = read_json(runs[name] / "contacts.json")
        time_s = np.asarray([s["time_s"] for s in trace])
        position_mm = np.asarray([s["position_error_m"] * 1000 for s in trace])
        rotation_deg = np.asarray([s["rotation_error_deg"] for s in trace])
        label = f"{name} · max {position_mm.max():.3f} mm / {rotation_deg.max():.3f}°"
        axes[0].plot(time_s, position_mm, color=COLORS[name], lw=1.8, label=label)
        axes[1].plot(time_s, rotation_deg, color=COLORS[name], lw=1.8, label=name)
        event_times[name] = shoulder_events(contacts)
    shared_events = sorted({t for name in RUNS if name != "reference"
                            for t, _, _ in event_times[name]})
    for t in shared_events:
        for ax in axes:
            ax.axvline(t, color="#7c3aed", ls="--", lw=1, alpha=.6)
    for t in shared_events:
        axes[0].annotate(f"step {round(t * 240)}", (t, 0.99), xycoords=("data", "axes fraction"),
                         xytext=(3, -5), textcoords="offset points", rotation=90,
                         va="top", fontsize=7, color="#6d28d9")
    for ax in axes:
        ax.grid(True, alpha=.24)
        ax.set_xlim(0, .1)
        ax.legend(frameon=False, fontsize=8, loc="best")
    axes[0].set(title="Saved native guitar position error to the fixed target", ylabel="Position error (mm)")
    axes[1].set(title="Saved native guitar rotation error to the fixed target", ylabel="Rotation error (degrees)",
                xlabel="Saved trace time (s)")
    fig.suptitle("right_clearance_v3 — reference and three 0.1 s native diagnostics", fontsize=13)
    fig.text(.5, .012,
             "Purple markers (steps 3 and 5) are observed R_Shoulder × guitar raw contact-row times in both ty0175 trials; "
             "they do not establish cause or support.", ha="center", fontsize=8)
    fig.tight_layout(rect=(0, .04, 1, .95), h_pad=1.2)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(output)
    fig.savefig(output, dpi=165, bbox_inches="tight")
    plt.close(fig)


def focus_shape(shape):
    if shape["actor"] == "guitar":
        return shape["body"] in {"guitar", "G:body"}
    return shape["body"].startswith("RH:") or shape["body"] in {"R_Wrist", "R_Elbow", "R_Shoulder", "R_Thorax"}


def plot_source_poses(runs, comparison_rows, output):
    import stability_adapter_2.environment  # Gym before MuJoCo
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from stability_adapter_2.plot_physx_contacts import source_surfaces
    from stability_adapter_2.replay_contact_geometry import recorded_probe

    panels = [(name, step) for name in ("reference", "ty015_sx010") for step in (0, 24)]
    snapshots, all_points = [], []
    for name, step in panels:
        model, data, shapes = recorded_probe(runs[name], step)
        surfaces, _, _, _ = source_surfaces(model, data, shapes)
        focus = [(triangles, shape) for triangles, shape in surfaces if focus_shape(shape)]
        row = comparison_rows[name]
        hull_key = "initial_right_palm_body_hulls" if step == 0 else "final_right_palm_body_hulls"
        witness = np.asarray(row[hull_key]["hull_witness_points_m"], dtype=float)
        distance_mm = row[hull_key]["source_hull_distance_m"] * 1000
        trace = read_json(runs[name] / "trace.json")
        sample = next(item for item in trace if abs(item["time_s"] - step / 240) < 1e-9)
        snapshots.append((name, step, focus, witness, distance_mm,
                          sample["position_error_m"] * 1000, sample["rotation_error_deg"]))
        all_points.extend([tri.reshape(-1, 3) for tri, _ in focus])
        all_points.append(witness)
    points = np.concatenate(all_points)
    center = (points.min(0) + points.max(0)) / 2
    half = float(np.ptp(points, axis=0).max()) / 2 + .035
    fig = plt.figure(figsize=(13.5, 9.2))
    for index, (name, step, surfaces, witness, distance, pos, rot) in enumerate(snapshots, 1):
        ax = fig.add_subplot(2, 2, index, projection="3d")
        for triangles, shape in surfaces:
            color = "#2563eb" if shape["actor"] == "guitar" else "#16a34a"
            ax.add_collection3d(Poly3DCollection(triangles, facecolors=color, alpha=.56, edgecolors="none"))
        ax.plot(witness[:, 0], witness[:, 1], witness[:, 2], color="#f59e0b", marker="o",
                ms=5, lw=2.5, label="RH:palm / G:body witness")
        ax.set(xlim=(center[0]-half, center[0]+half), ylim=(center[1]-half, center[1]+half),
               zlim=(center[2]-half, center[2]+half), xlabel="World X (m)", ylabel="World Y (m)", zlabel="World Z (m)")
        ax.set_box_aspect((1, 1, 1))
        ax.view_init(elev=20, azim=116)
        when = "t=0" if step == 0 else "t=0.1 s"
        ax.set_title(f"{name} · {when} · RH palm/G:body {distance:.3f} mm\n"
                     f"guitar error {pos:.3f} mm / {rot:.3f}°")
        if index == 1:
            ax.legend(loc="upper left", fontsize=7, frameon=False)
    fig.suptitle("Reference and ty015_sx010 at saved native poses — source-shape reconstruction", fontsize=13)
    fig.text(.5, .012,
             "Green: right arm/hand source shapes | blue: guitar body/neck | orange: source-hull witness. "
             "Same world bounds/view; CPU reconstruction, not native renderer or cooked-clearance certification.",
             ha="center", fontsize=8)
    fig.tight_layout(rect=(0, .045, 1, .95), h_pad=1.1, w_pad=.8)
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=155, bbox_inches="tight")
    plt.close(fig)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def geometry_assets():
    root = Path(__file__).resolve().parents[1]
    config_path = Path(__file__).with_name("config.json").resolve()
    config = read_json(config_path)
    paths = {config_path}
    for key in ("humanoid_asset", "guitar_asset"):
        xml = (root / config[key]).resolve()
        paths.add(xml)
        xml_root = ET.parse(xml).getroot()
        compiler = xml_root.find("compiler")
        mesh_dir = xml.parent / (compiler.get("meshdir", "") if compiler is not None else "")
        for mesh in xml_root.findall("./asset/mesh"):
            paths.add((mesh_dir / mesh.attrib["file"]).resolve())
    return sorted(p for p in paths if p.is_file())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.out_dir.exists() and any(args.out_dir.iterdir()):
        raise FileExistsError(f"preserve existing artifacts: {args.out_dir}")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    comparison_path = args.results_dir / "comparison.json"
    search_path = args.results_dir / "search/search.json"
    comparison, search = read_json(comparison_path), read_json(search_path)
    rows = rows_by_name(comparison)
    if tuple(rows) != RUNS or len(search["evaluations"]) != 10:
        raise ValueError("unexpected right_clearance_v3 rows or search count")
    runs = {name: Path(rows[name]["run"]) for name in RUNS}
    plot_curves(runs, args.out_dir / "right_clearance_v3_native_curves.png")
    plot_source_poses(runs, rows, args.out_dir / "right_clearance_v3_source_poses.png")
    raw_inputs = [comparison_path, search_path, args.results_dir / "short_commands.json"]
    raw_inputs += [runs[name] / fname for name in RUNS
                   for fname in ("report.json", "trace.json", "states.json", "contacts.json")]
    helper_names = ("plot_right_clearance.py", "replay_contact_geometry.py", "plot_physx_contacts.py",
                    "initial_overlap.py", "environment.py", "trial_settings.py")
    helpers = [Path(__file__).with_name(name).resolve() for name in helper_names]
    assets = geometry_assets()
    payload = {
        "purpose": "read-only plots of the ten-row static search context and four saved short native runs; no native execution",
        "input_sha256": {str(p.resolve()): sha256(p) for p in raw_inputs if p.is_file()},
        "search_embedded_source_sha256": search["source_sha256"],
        "helper_sha256": {str(p): sha256(p) for p in helpers if p.is_file()},
        "geometry_assets_sha256": {str(p): sha256(p) for p in assets},
        "geometry_asset_count_including_config": len(assets),
        "outputs_sha256": {str(p.resolve()): sha256(p) for p in sorted(args.out_dir.glob("*.png"))},
    }
    (args.out_dir / "plot_manifest.json").write_text(json.dumps(payload, indent=2) + "\n")


if __name__ == "__main__":
    main()
