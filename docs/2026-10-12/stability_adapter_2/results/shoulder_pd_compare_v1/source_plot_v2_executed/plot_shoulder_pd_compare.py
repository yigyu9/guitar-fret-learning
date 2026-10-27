"""Plot the saved 0.5 s Shoulder-PD comparison without running simulation."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


EXPECTED_CHECKS = 7
EXPECTED_HASHES = 131


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text())


def finite_vector(rows, key, expected, label):
    values = np.asarray([row[key] for row in rows], dtype=float)
    if values.shape != (expected,) or not np.isfinite(values).all():
        raise ValueError(f"invalid {label} shape or non-finite values")
    return values


def load_run(run: Path, expected_stiffness: int, comparison_row: dict):
    native = run / "native"
    report = read_json(run / "report.json")
    native_report = read_json(native / "report.json")
    if report.get("physics_steps") != 120 or not all(report.get("checks", {}).values()):
        raise ValueError(f"run wrapper contract failed: {run}")
    if native_report.get("native_physics_steps") != 120 or not all(native_report.get("checks", {}).values()):
        raise ValueError(f"run contract failed: {run}")
    if expected_stiffness not in (200, 300):
        raise ValueError("unexpected stiffness")

    traces = read_json(native / "trace.json")
    queries = read_json(native / "queries.json")
    states = read_json(native / "states.json")
    controls = read_json(native / "controls.json")
    if not (len(traces) == len(queries) == len(states) == 121 and len(controls) == 120):
        raise ValueError(f"unexpected saved sample counts: {run}")

    times = finite_vector(traces, "time_s", 121, "trace times")
    expected_times = np.arange(121, dtype=float) / 240.0
    if not np.allclose(times, expected_times, rtol=0, atol=1e-12):
        raise ValueError(f"unexpected trace time schedule: {run}")
    pos_mm = finite_vector(traces, "position_error_m", 121, "position error") * 1000.0
    rot_deg = finite_vector(traces, "rotation_error_deg", 121, "rotation error")

    initial_goal = np.asarray(queries[0]["palm_goal_world_m"], dtype=float)
    palm_points = np.asarray([query["left_source_world_m"] for query in queries], dtype=float)
    if initial_goal.shape != (3,) or palm_points.shape != (121, 3):
        raise ValueError(f"invalid LH source point shape: {run}")
    if not np.isfinite(initial_goal).all() or not np.isfinite(palm_points).all():
        raise ValueError(f"non-finite LH source point: {run}")
    palm_mm = np.linalg.norm(palm_points - initial_goal, axis=1) * 1000.0

    names = report["human_joint_names"]
    arm_indices = native_report["arm_indices"]
    joint_index = names.index("L_Shoulder_x")
    arm_slot = arm_indices.index(joint_index)
    target = np.asarray([control["final_arm_targets_rad"][arm_slot] for control in controls], dtype=float)
    actual = np.asarray([state["human_dof_states"][joint_index]["pos"] for state in states[1:]], dtype=float)
    step = np.asarray([state["physics_step"] for state in states[1:]], dtype=float)
    if target.shape != (120,) or actual.shape != (120,) or not np.isfinite(target).all() or not np.isfinite(actual).all():
        raise ValueError(f"invalid shoulder target/state samples: {run}")
    if not np.array_equal(step, np.arange(1, 121, dtype=float)):
        raise ValueError(f"unexpected completed state steps: {run}")
    gap_deg = np.abs(target - actual) * (180.0 / math.pi)
    if abs(float(pos_mm.max()) - comparison_row["max_guitar_position_mm"]) > 1e-8:
        raise ValueError(f"position trace disagrees with validated comparison: {run}")
    if abs(float(rot_deg.max()) - comparison_row["max_guitar_rotation_deg"]) > 1e-8:
        raise ValueError(f"rotation trace disagrees with validated comparison: {run}")
    return {"time": times, "pos_mm": pos_mm, "rot_deg": rot_deg, "palm_mm": palm_mm,
            "gap_time": step / 240.0, "gap_deg": gap_deg, "report": report,
            "wrapper_report_path": run / "report.json", "trace_path": native / "trace.json", "queries_path": native / "queries.json",
            "states_path": native / "states.json", "controls_path": native / "controls.json",
            "report_path": native / "report.json"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True, help="shoulder_pd_compare_v1 result directory")
    parser.add_argument("--out", type=Path, required=True, help="new PNG output path")
    args = parser.parse_args()

    if args.out.exists():
        raise FileExistsError(f"preserve existing output: {args.out}")
    comparison_path = args.run / "comparison_validated.json"
    comparison = read_json(comparison_path)
    checks = comparison.get("checks", {})
    if len(checks) != EXPECTED_CHECKS or not all(checks.values()):
        raise ValueError("validated comparison contract checks failed")
    hashes = comparison.get("input_sha256", {})
    if len(hashes) != EXPECTED_HASHES:
        raise ValueError(f"expected {EXPECTED_HASHES} input hashes, found {len(hashes)}")
    for path_text, expected in hashes.items():
        path = Path(path_text)
        if not path.is_file() or sha256(path) != expected:
            raise ValueError(f"stale or missing input: {path}")

    wanted = {("hold_05s", 200), ("hold_05s", 300)}
    rows = {(row["group"], row["stiffness"]): row for row in comparison["rows"]}
    if not wanted.issubset(rows):
        raise ValueError("validated comparison is missing a requested 0.5 s row")
    data = {}
    for stiffness in (200, 300):
        row = rows[("hold_05s", stiffness)]
        run = Path(row["run"])
        data[stiffness] = load_run(run, stiffness, row)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(13, 8.2), sharex=False, constrained_layout=True)
    colors = {200: "#3569a8", 300: "#d47725"}
    labels = {200: "Shoulder stiffness 200", 300: "Shoulder stiffness 300"}
    for stiffness in (200, 300):
        item = data[stiffness]
        color = colors[stiffness]
        axes[0, 0].plot(item["time"], item["pos_mm"], color=color, label=labels[stiffness], lw=1.8)
        axes[0, 1].plot(item["time"], item["rot_deg"], color=color, label=labels[stiffness], lw=1.8)
        axes[1, 0].plot(item["time"], item["palm_mm"], color=color, label=labels[stiffness], lw=1.8)
        axes[1, 1].plot(item["gap_time"], item["gap_deg"], color=color, label=labels[stiffness], lw=1.8)
    axes[0, 0].set_title("Guitar position error")
    axes[0, 0].set_ylabel("Norm error (mm)")
    axes[0, 1].set_title("Guitar rotation error")
    axes[0, 1].set_ylabel("Error (deg)")
    axes[1, 0].set_title("LH source-point displacement")
    axes[1, 0].set_ylabel("Distance from initial goal (mm)")
    axes[1, 1].set_title("L_Shoulder_x target–actual scalar gap")
    axes[1, 1].set_ylabel("Absolute scalar gap (deg)")
    for ax in axes.flat:
        ax.set_xlabel("Saved time (s)")
        ax.set_xlim(0.0, 0.5)
        ax.grid(True, alpha=0.25)
        ax.legend(frameon=False)
    axes[1, 1].text(0.01, 0.98, "Completed steps 1–120; no t=0 gap estimate",
                    transform=axes[1, 1].transAxes, va="top", fontsize=8)
    fig.suptitle("Saved PhysX traces (not a renderer): Shoulder stiffness comparison (0.5 s)", fontsize=14)
    fig.savefig(args.out, dpi=180)
    plt.close(fig)

    used_files = [comparison_path]
    for item in data.values():
        used_files.extend(item[key] for key in ("wrapper_report_path", "report_path", "trace_path", "queries_path", "states_path", "controls_path"))
    manifest = {
        "purpose": "Saved-data visualization only; no native simulation",
        "validated_comparison_sha256": sha256(comparison_path),
        "validated_contract_checks": checks,
        "validated_input_sha256_count": len(hashes),
        "used_raw_files_sha256": {str(p.resolve()): sha256(p) for p in used_files},
        "plotter_sha256": sha256(Path(__file__).resolve()),
        "output_png": str(args.out.resolve()),
        "output_png_sha256": sha256(args.out),
        "series": {
            "guitar_position": "trace.position_error_m × 1000, mm; saved time_s",
            "guitar_rotation": "trace.rotation_error_deg; saved time_s",
            "LH_source_displacement": "norm(queries.left_source_world_m - initial palm_goal_world_m) × 1000, mm",
            "L_Shoulder_x_gap": "abs(final_arm_targets_rad - completed-state DOF pos) × 180/pi, deg; completed steps 1..120",
        },
    }
    manifest_path = args.out.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.out), "manifest": str(manifest_path),
                      "sha256": manifest["output_png_sha256"], "samples": 121,
                      "completed_gap_samples": 120}, indent=2))


if __name__ == "__main__":
    main()
