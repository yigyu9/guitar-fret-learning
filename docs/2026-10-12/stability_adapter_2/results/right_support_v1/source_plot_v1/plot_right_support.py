"""Plot saved right-arm support-search records; does not run native physics."""
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def read_json(path):
    return json.loads(path.read_text())


def rows_by_name(comparison):
    return {row["name"]: row for row in comparison["rows"]}


def plot_native_curves(rows, output):
    colors = {"reference": "#475569", "candidate_01": "#dc2626",
              "candidate_02": "#2563eb", "candidate_03": "#16a34a"}
    fig, axes = plt.subplots(2, 1, figsize=(12.5, 8.5), sharex=True)
    shoulder_events = set()
    for name in ("reference", "candidate_01", "candidate_02", "candidate_03"):
        row = rows[name]
        run = Path(row["run"])
        trace = read_json(run / "trace.json")
        contacts = read_json(run / "contacts.json")
        time_s = np.asarray([sample["time_s"] for sample in trace])
        pos_mm = np.asarray([sample["position_error_m"] * 1000 for sample in trace])
        rot_deg = np.asarray([sample["rotation_error_deg"] for sample in trace])
        label = f"{name} · max {pos_mm.max():.3f} mm / {rot_deg.max():.3f}°"
        axes[0].plot(time_s, pos_mm, color=colors[name], lw=1.8, label=label)
        axes[1].plot(time_s, rot_deg, color=colors[name], lw=1.8, label=name)
        for sample in contacts:
            for contact in sample["contacts"]:
                pair = (contact["body0_name"], contact["body1_name"])
                if "human/R_Shoulder" in pair and any(n.startswith("guitar/") for n in pair):
                    shoulder_events.add(float(sample["time_s"]))
    for ax in axes:
        for index, event_time in enumerate(sorted(shoulder_events)):
            step = round(event_time * 240)
            style = ("#111827", "--") if index == 0 else ("#7c3aed", ":")
            ax.axvline(event_time, color=style[0], ls=style[1], lw=1.2,
                       label=f"R_Shoulder × guitar row: step {step} ({event_time:.6f} s)")
        ax.grid(True, alpha=.24)
        ax.set_xlim(0, .1)
        ax.legend(frameon=False, fontsize=8, loc="best")
    axes[0].set(title="0.1 s native guitar error to candidate goal", ylabel="Position error (mm)")
    axes[1].set(title="Rotation error to candidate goal", ylabel="Rotation error (degrees)",
                xlabel="Saved trace time (s)")
    fig.suptitle("Right-arm static-search candidates: short native trial comparison", fontsize=13)
    fig.text(.5, .012,
             "Dashed markers show observed shoulder contact-row times in candidates (same times for all three); "
             "they do not establish cause, support force, or stability.", ha="center", fontsize=8)
    fig.tight_layout(rect=(0, .04, 1, .95), h_pad=1.2)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(output)
    fig.savefig(output, dpi=160, bbox_inches="tight")
    plt.close(fig)


def _focus_shape(shape):
    if shape["actor"] == "guitar":
        return shape["body"] in {"guitar", "G:body"}
    body = shape["body"]
    return body.startswith("RH:") or body in {"R_Wrist", "R_Elbow", "R_Shoulder", "R_Thorax"}


def plot_source_geometry(results_dir, rows, output):
    # The replay helper loads Gym before MuJoCo and only restores saved body poses.
    import stability_adapter_2.environment  # noqa: F401
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from stability_adapter_2.plot_physx_contacts import source_surfaces
    from stability_adapter_2.replay_contact_geometry import recorded_probe

    panels = [("reference", 0), ("candidate_01", 0),
              ("reference", 24), ("candidate_01", 24)]
    snapshots, bound_points = [], []
    for name, step in panels:
        row = rows[name]
        run = Path(row["run"])
        model, data, shapes = recorded_probe(run, step)
        surfaces, _, _, _ = source_surfaces(model, data, shapes)
        focus = [(triangles, shape) for triangles, shape in surfaces if _focus_shape(shape)]
        trace = read_json(run / "trace.json")
        sample = next(s for s in trace if abs(s["time_s"] - step / 240) < 1e-9)
        hull_key = "initial_right_palm_body_hulls" if step == 0 else "final_right_palm_body_hulls"
        hull = row[hull_key]
        witness = np.asarray(hull["hull_witness_points_m"], dtype=float)
        snapshots.append((name, step, focus, witness, hull["source_hull_distance_m"],
                          sample["position_error_m"] * 1000, sample["rotation_error_deg"]))
        bound_points.extend([tri.reshape(-1, 3) for tri, _ in focus])
        bound_points.append(witness)
    all_points = np.concatenate(bound_points)
    center = (all_points.min(0) + all_points.max(0)) / 2
    half = float(np.ptp(all_points, axis=0).max()) / 2 + .035
    fig = plt.figure(figsize=(14, 10))
    for panel, (name, step, surfaces, witness, distance, pos_mm, rot_deg) in enumerate(snapshots, 1):
        ax = fig.add_subplot(2, 2, panel, projection="3d")
        for triangles, shape in surfaces:
            color = "#2563eb" if shape["actor"] == "guitar" else "#16a34a"
            ax.add_collection3d(Poly3DCollection(triangles, facecolors=color,
                                                 alpha=.56, edgecolors="none"))
        ax.plot(witness[:, 0], witness[:, 1], witness[:, 2], color="#f59e0b",
                marker="o", ms=7, lw=3, label="RH:palm / G:body witness")
        ax.scatter(witness[:, 0], witness[:, 1], witness[:, 2], color="#f59e0b",
                   edgecolors="#111827", linewidths=.7, s=40, depthshade=False)
        ax.set(xlim=(center[0]-half, center[0]+half),
               ylim=(center[1]-half, center[1]+half),
               zlim=(center[2]-half, center[2]+half),
               xlabel="World X (m)", ylabel="World Y (m)", zlabel="World Z (m)")
        ax.set_box_aspect((1, 1, 1))
        ax.view_init(elev=20, azim=116)
        when = "t=0" if step == 0 else "t=0.1 s"
        ax.set_title(f"{name} · {when} · RH/G:body hull {distance*1000:.3f} mm\n"
                     f"candidate-goal error {pos_mm:.2f} mm / {rot_deg:.2f}°")
        if panel == 1:
            ax.legend(loc="upper left", fontsize=7, frameon=False)
    fig.suptitle("Right palm and guitar source shapes at saved native poses — CPU reconstruction", fontsize=13)
    fig.text(.5, .014,
             "Green: right-arm/hand source shapes | blue: guitar G:body | orange: unsigned hull witness segment. "
             "Same bounds/view; not Isaac/PhysX renderer, cooked clearance, contact or support certification.",
             ha="center", fontsize=8)
    fig.tight_layout(rect=(0, .045, 1, .95), h_pad=1.1, w_pad=.8)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(output)
    fig.savefig(output, dpi=155, bbox_inches="tight")
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
        xml = ET.parse(xml_path).getroot()
        compiler = xml.find("compiler")
        meshdir = xml_path.parent / (compiler.get("meshdir", "") if compiler is not None else "")
        for mesh in xml.findall("./asset/mesh"):
            paths.add((meshdir / mesh.attrib["file"]).resolve())
    return sorted(p for p in paths if p.is_file())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    images = args.out_dir / "images"
    manifest_path = args.out_dir / "plot_manifest.json"
    if images.exists() or manifest_path.exists():
        raise FileExistsError(f"preserve existing artifacts: {images}, {manifest_path}")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    comparison_path = args.results_dir / "comparison_v2.json"
    if not comparison_path.exists():
        comparison_path = args.results_dir / "comparison.json"
    comparison = read_json(comparison_path)
    rows = rows_by_name(comparison)
    plot_native_curves(rows, images / "right_support_v1_native_curves.png")
    plot_source_geometry(args.results_dir, rows, images / "right_support_v1_source_geometry.png")
    runs = [Path(row["run"]) for row in comparison["rows"]]
    inputs = [comparison_path, args.results_dir / "comparison.json",
              args.results_dir / "search/search.json", args.results_dir / "short_commands.json",
              args.results_dir / "source/search_hand_support.py",
              args.results_dir / "source_manifest.json",
              args.results_dir / "source_snapshot_validation.json"]
    inputs += [run / name for run in runs
               for name in ("report.json", "trace.json", "states.json", "contacts.json")]
    helpers = [Path(__file__).resolve()] + [Path(__file__).with_name(name).resolve()
             for name in ("plot_physx_contacts.py", "replay_contact_geometry.py", "initial_overlap.py",
                          "environment.py", "plot_neck_palm.py")]
    payload = {
        "purpose": "read-only plots from static-search and saved native traces; no rollout",
        "inputs_sha256": {str(p.resolve()): sha256(p) for p in sorted(p for p in inputs if p.is_file())},
        "plot_sources_sha256": {str(p): sha256(p) for p in helpers},
        "source_geometry_assets_sha256": {str(p): sha256(p) for p in geometry_asset_paths()},
        "embedded_search_source_hashes": read_json(args.results_dir / "search/search.json")["source_sha256"],
        "preserved_initial_comparison_sha256": sha256(args.results_dir / "comparison.json"),
        "embedded_comparison_source_hashes": comparison["input_sha256"],
        "outputs_sha256": {str(p.resolve()): sha256(p) for p in sorted(images.glob("*.png"))},
    }
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n")


if __name__ == "__main__":
    main()
