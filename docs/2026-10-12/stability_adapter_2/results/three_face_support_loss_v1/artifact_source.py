#!/usr/bin/env python3
"""Render the two approved support-loss figures from sealed saved analysis."""
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT / "docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1"
ANALYSIS = PHASE / "analysis.json"
BRIEF = PHASE / "artifact_brief.json"
EXPECTED_ANALYSIS_SHA = "c7d14a89d7eb420eb5b4a0d7d64c47b35fffb42617c457144ce032b43dda9daf"
FIGURES = ("support_loss_metrics.png", "support_loss_source_geometry.png")
LABELS = ("saved_finger_targets", "initial_finger_targets")
DISPLAY = {LABELS[0]: "Saved finger targets", LABELS[1]: "Initial finger targets"}


def sha256(path):
    h = hashlib.sha256()
    with open(str(path), "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    out_dir = Path(args.out_dir).resolve()

    # Seal every declared input and this producer before importing plot libraries
    # or reading JSON. The source-analysis inventory is part of the input closure.
    producer = Path(__file__).resolve()
    pre_hashes = {str(p): sha256(p) for p in (producer, BRIEF, ANALYSIS)}
    if pre_hashes[str(ANALYSIS)] != EXPECTED_ANALYSIS_SHA:
        raise RuntimeError("analysis SHA does not match the approved brief")
    if pre_hashes[str(producer)] != sha256(producer):
        raise RuntimeError("producer changed during initial sealing")

    with open(str(ANALYSIS), "r") as stream:
        analysis = json.load(stream)
    with open(str(BRIEF), "r") as stream:
        brief = json.load(stream)
    if brief["analysis_sha256"] != EXPECTED_ANALYSIS_SHA:
        raise AssertionError("brief analysis SHA mismatch")
    if not all(analysis["checks"].values()):
        raise AssertionError("analysis contains an incomplete check")
    if analysis["counts"] != {"native_initializations": 1, "physics_steps": 1200,
                               "offline_actual_pose_samples": 12}:
        raise AssertionError("analysis counts differ from approved completed phase")
    if len(analysis["rows"]) != 12 or len(analysis["geometry"]) != 12:
        raise AssertionError("expected 12 saved samples")
    for path, digest in analysis["input_sha256"].items():
        if sha256(path) != digest:
            raise AssertionError("sealed analysis input changed: " + path)
        pre_hashes[path] = digest

    # Matplotlib/NumPy imports happen only after the direct and transitive source
    # hashes above have been checked.
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    from matplotlib.patches import Patch
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    font_path = Path(font_manager.findfont(matplotlib.rcParams["font.family"][0]))
    pre_hashes[str(font_path)] = sha256(font_path)
    for path, digest in pre_hashes.items():
        if sha256(path) != digest:
            raise AssertionError("input changed after plotting imports: " + path)

    out_dir.mkdir(parents=True, exist_ok=True)
    if any((out_dir / name).exists() for name in FIGURES):
        raise FileExistsError("refusing to overwrite an existing artifact")
    labels = LABELS
    colors = {labels[0]: "#1769aa", labels[1]: "#d1495b"}
    rows = analysis["rows"]
    times = sorted(set(r["time_s"] for r in rows))
    positions = dict((time_value, i) for i, time_value in enumerate(times))

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.4), constrained_layout=True)
    for label in labels:
        group = [r for r in rows if r["label"] == label]
        color = colors[label]
        x = [positions[r["time_s"]] for r in group]
        axes[0].plot(x,
                     [1000.0 * r["metrics"]["LH:palm"]["hull_gap_m"] for r in group],
                     marker="o", color=color, label=DISPLAY[label])
        axes[1].plot(x,
                     [math.degrees(r["max_abs_coordinate_error_rad"]["left_arm12"]) for r in group],
                     marker="o", color=color, linestyle="-", label=DISPLAY[label] + " — left arm")
        axes[1].plot(x,
                     [math.degrees(r["max_abs_coordinate_error_rad"]["finger21"]) for r in group],
                     marker="s", color=color, linestyle="--", label=DISPLAY[label] + " — fingers")
        axes[1].plot(x,
                     [math.degrees(r["max_abs_coordinate_error_rad"]["torso9"]) for r in group],
                     marker="^", color=color, linestyle=":", label=DISPLAY[label] + " — torso")
        axes[2].plot(x,
                     [r["metrics"]["LH:thumb3"]["inward_alignment_dot"] for r in group],
                     marker="o", color=color, label=DISPLAY[label] + " — thumb facet")
        axes[2].plot(x,
                     [r["metrics"]["LH:palm"]["inward_alignment_dot"] for r in group],
                     marker="s", color=color, linestyle="--", label=DISPLAY[label] + " — palm facet")
    axes[0].set(title="Palm source-hull gap", xlabel="Saved sample time (s)", ylabel="Gap (mm)")
    axes[1].set(title="Maximum absolute coordinate error", xlabel="Saved sample time (s)", ylabel="Error (degrees)")
    axes[2].set(title="Selected-facet inward alignment", xlabel="Saved sample time (s)", ylabel="Dimensionless dot product")
    for ax in axes:
        ax.set_xticks(range(len(times)))
        ax.set_xticklabels(["{:g}".format(t) for t in times])
        ax.grid(True, alpha=.25)
    axes[0].legend(frameon=False, fontsize=8)
    axes[1].legend(frameon=False, fontsize=7, ncol=2)
    axes[2].legend(frameon=False, fontsize=7)
    fig.suptitle("Saved actual-pose CPU source-geometry diagnostics; discrete samples only")
    fig.savefig(str(out_dir / FIGURES[0]), dpi=180)
    plt.close(fig)

    selected_steps = (0, 120, 1200)
    geo_by_key = {(g["label"], g["physics_step"]): g for g in analysis["geometry"]}
    region_colors = {"front": "#f2cc8f", "thumb": "#5b8e7d", "palm": "#d1495b"}
    region_labels = {"front": "front", "thumb": "rear", "palm": "side"}
    region_names = list(analysis["regions_G_m"].keys())
    body_names = ("LH:thumb3", "LH:index3", "LH:middle3", "LH:ring3", "LH:pinky3", "LH:palm")
    fig = plt.figure(figsize=(14, 7), constrained_layout=True)
    global_points = []
    for selected_label in labels:
        for selected_step in selected_steps:
            selected = geo_by_key[(selected_label, selected_step)]
            global_points.extend(np.asarray(selected["hand_hulls"][b]["vertices_G_m"], dtype=float) * 1000.0
                                 for b in body_names)
    for name in region_names:
        poly = np.asarray(analysis["regions_G_m"][name], dtype=float).copy() * 1000.0
        if name == "front":
            poly[:, 2] = analysis["front_outer_source_z_G_m"] * 1000.0
        global_points.append(poly)
    global_points = np.vstack(global_points)
    shared_lo, shared_hi = global_points.min(axis=0), global_points.max(axis=0)
    shared_center = (shared_lo + shared_hi) / 2.0
    shared_radius = max(float((shared_hi - shared_lo).max()) / 2.0, 1.0)
    for col, step in enumerate(selected_steps, start=1):
        for row_i, label in enumerate(labels, start=1):
            ax = fig.add_subplot(2, 3, (row_i - 1) * 3 + col, projection="3d")
            item = geo_by_key[(label, step)]
            for body_i, body in enumerate(body_names):
                mesh = item["hand_hulls"][body]
                v = np.asarray(mesh["vertices_G_m"], dtype=float) * 1000.0
                f = np.asarray(mesh["faces"], dtype=int)
                ax.plot_trisurf(v[:, 0], v[:, 1], v[:, 2], triangles=f,
                                color=plt.cm.tab10(body_i), alpha=.30,
                                linewidth=.12, edgecolor="#333333")
            for name in region_names:
                poly = np.asarray(analysis["regions_G_m"][name], dtype=float) * 1000.0
                if name == "front":
                    poly[:, 2] = analysis["front_outer_source_z_G_m"] * 1000.0
                ax.add_collection3d(Poly3DCollection(
                    [poly], facecolors=region_colors[name], alpha=.25,
                    edgecolors=region_colors[name], linewidths=.7))
            ax.set_title(DISPLAY[label] +
                         "\nstep {} (t={:g}s)".format(step, step / 240.0), fontsize=9)
            ax.set_xlabel("G-local X (mm)", labelpad=1)
            ax.set_ylabel("G-local Y (mm)", labelpad=1)
            ax.set_zlabel("G-local Z (mm)", labelpad=1)
            ax.set_xlim(shared_center[0]-shared_radius, shared_center[0]+shared_radius)
            ax.set_ylim(shared_center[1]-shared_radius, shared_center[1]+shared_radius)
            ax.set_zlim(shared_center[2]-shared_radius, shared_center[2]+shared_radius)
            ax.set_box_aspect((1, 1, 1))
            ax.view_init(elev=24, azim=-58)
    legend_items = [Patch(facecolor=plt.cm.tab10(i), edgecolor="#333333",
                          label=body.split(":", 1)[1])
                    for i, body in enumerate(body_names)]
    legend_items.extend(Patch(facecolor=region_colors[name], edgecolor=region_colors[name],
                              alpha=.45, label=region_labels[name])
                        for name in region_names)
    fig.legend(handles=legend_items, loc="lower center", ncol=9, frameon=False)
    fig.suptitle("Six saved hand hulls in guitar-local source geometry — CPU placement only")
    fig.savefig(str(out_dir / FIGURES[1]), dpi=170)
    plt.close(fig)

    for path, digest in pre_hashes.items():
        if sha256(path) != digest:
            raise AssertionError("input changed during artifact generation: " + path)
    output_files = {str((out_dir / name).resolve()): sha256(out_dir / name) for name in FIGURES}
    if len(output_files) != 2:
        raise AssertionError("expected exactly two PNG outputs")
    post_hashes = {path: sha256(path) for path in pre_hashes}
    if post_hashes != pre_hashes:
        raise AssertionError("pre/post input SHA mismatch")
    manifest = {
        "phase": brief["phase"],
        "producer_path": str(producer),
        "producer_sha256": sha256(producer),
        "analysis_sha256": pre_hashes[str(ANALYSIS)],
        "inputs_sha256_before": dict(sorted(pre_hashes.items())),
        "inputs_sha256_after": dict(sorted(post_hashes.items())),
        "outputs_sha256": output_files,
        "native_calls": 0,
        "source_geometry_only": True,
        "sample_times_s": times,
        "geometry_steps": list(selected_steps),
    }
    with open(str(out_dir / "artifact_manifest.json"), "w") as stream:
        json.dump(manifest, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"output_sha256": output_files, "native_calls": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
