"""Plot saved 0.5 s guitar-error traces for the baseline and seeded hold runs."""
import argparse
import hashlib
import json
import math
from pathlib import Path

import matplotlib.pyplot as plt


PHASE = Path(__file__).resolve().parent
RUNS = {
    "baseline": {"short": "short/baseline", "hold": "hold_05s/baseline"},
    "seed120_preload050_hold": {
        "short": "short/seed120_preload050_hold",
        "hold": "hold_05s/seed120_preload050_hold",
    },
}
PROBES = ("probe.json", "probe_deep.json", "probe_mixed.json")


def read_json(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def contact_windows(contacts):
    steps = sorted({row["physics_step"] for row in contacts})
    windows = []
    for step in steps:
        if not windows or step > windows[-1][-1] + 1:
            windows.append([step])
        else:
            windows[-1].append(step)
    return steps, [[window[0], window[-1]] for window in windows]


def load_run(relative, steps):
    run = PHASE / relative
    report = read_json(run / "report.json")
    trace = read_json(run / "trace.json")
    controls = read_json(run / "controls.json")
    contacts = read_json(run / "lh_contacts.json")
    if not all(report["checks"].values()) or report["physics_steps"] != steps or report["physics_hz"] != 240:
        raise ValueError(f"invalid saved-run contract: {relative}")
    if len(trace) != steps + 1 or len(controls) != steps:
        raise ValueError(f"unexpected saved sample count: {relative}")
    for i, row in enumerate(trace):
        if abs(row["time_s"] - i / 240) > 1e-12 or not row.get("finite", False):
            raise ValueError(f"invalid sample time/finite flag: {relative}, index {i}")
        if not math.isfinite(row["position_error_m"]) or not math.isfinite(row["rotation_error_deg"]):
            raise ValueError(f"nonfinite guitar error: {relative}, index {i}")
    recorded_max_p = max(row["position_error_m"] for row in trace)
    recorded_max_q = max(row["rotation_error_deg"] for row in trace)
    if (abs(recorded_max_p - report["max_position_error_m"]) > 1e-12
            or abs(recorded_max_q - report["max_rotation_error_deg"]) > 1e-12):
        raise ValueError(f"report/trace peak mismatch: {relative}")
    for row in contacts:
        if not 1 <= row["physics_step"] <= steps or "contact" not in row:
            raise ValueError(f"invalid saved LH contact row: {relative}")
    sample_steps, windows = contact_windows(contacts)
    summary = {
        "run": relative,
        "physics_steps": steps,
        "max_position_error_mm": recorded_max_p * 1000,
        "max_rotation_error_deg": recorded_max_q,
        "final_position_error_mm": trace[-1]["position_error_m"] * 1000,
        "final_rotation_error_deg": trace[-1]["rotation_error_deg"],
        "left_hand_contact_rows": len(contacts),
        "left_hand_contact_sample_steps": sample_steps,
        "left_hand_contact_step_windows": windows,
        "left_hand_contact_pairs": sorted({
            (row["contact"]["body0_name"], row["contact"]["body1_name"]) for row in contacts
        }),
    }
    return report, trace, summary


def audit_probe(path):
    data = read_json(path)
    before, after = data["input_sha256"], data["input_sha256_after"]
    if before != after or data["physics_steps"] != 0:
        raise ValueError(f"source-only probe changed inputs or advanced physics: {path.name}")
    return {"file": path.name, "rows": len(data["rows"]),
            "native_initializations": data["native_initializations"], "physics_steps": data["physics_steps"]}


def audit_source_hashes(label, recorded, recorded_after, run_dir=None):
    if recorded != recorded_after:
        raise ValueError(f"source SHA map changed during recorded run: {label}")
    audits = []
    for source, expected in recorded.items():
        path = Path(source)
        current = sha(path) if path.is_file() else None
        if current == expected:
            continue
        candidates = []
        if path.name == "run_finger_grip_hold.py" and run_dir is not None:
            candidates.append(run_dir / "producer.py")
        if path.name == "finger_grip_probe.py":
            candidates.extend(PHASE / name for name in
                             ("probe_producer_v1.py", "probe_producer_deep.py", "probe_producer_mixed.py"))
        matched = next((candidate for candidate in candidates
                        if candidate.is_file() and sha(candidate) == expected), None)
        if matched is None:
            raise ValueError(f"recorded source SHA has no matching live file or producer snapshot: {label}: {source}")
        audits.append({"recorded_source": source, "recorded_sha256": expected,
                       "preserved_producer_snapshot": str(matched),
                       "producer_snapshot_sha256": sha(matched)})
    return {"recorded_before_after_equal": True, "historical_source_sha_resolved_by_snapshot": audits}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    out = args.out_dir.resolve()
    if out.exists():
        raise FileExistsError(f"preserve existing artifacts: {out}")
    out.mkdir(parents=True)

    input_paths = [PHASE / name for name in PROBES]
    input_paths.extend(PHASE / name for name in
                       ("probe_producer_v1.py", "probe_producer_deep.py", "probe_producer_mixed.py"))
    for probe_name in PROBES:
        probe_data = read_json(PHASE / probe_name)
        input_paths.extend(Path(path) for path in probe_data["input_sha256"])
    for paths in RUNS.values():
        for phase_name, steps in (("short", 24), ("hold", 120)):
            run = PHASE / paths[phase_name]
            input_paths.extend(run / name for name in
                               ("report.json", "trace.json", "controls.json", "lh_contacts.json", "producer.py"))
            report = read_json(run / "report.json")
            input_paths.extend(Path(path) for path in report["source_sha256"])
    input_paths.append(Path(__file__).resolve())
    input_paths = sorted(set(input_paths))
    before = {str(path): sha(path) for path in input_paths}
    probe_summary = [audit_probe(path) for path in input_paths if path.name in PROBES]

    results = {}
    loaded = {}
    for name, paths in RUNS.items():
        loaded[name] = {}
        results[name] = {}
        for phase_name, steps in (("short", 24), ("hold", 120)):
            report, trace, summary = load_run(paths[phase_name], steps)
            loaded[name][phase_name] = (report, trace)
            results[name][phase_name] = summary

    baseline, seeded = (loaded[name]["hold"][0] for name in RUNS)
    base_angles = baseline["initial_settings"]["joint_angles_rad"]
    seed_angles = seeded["initial_settings"]["joint_angles_rad"]
    angle_changes = sorted(name for name in base_angles if base_angles[name] != seed_angles[name])
    source_audits = {}
    for name, paths in RUNS.items():
        source_audits[name] = {}
        for phase_name in ("short", "hold"):
            report = loaded[name][phase_name][0]
            run_dir = PHASE / paths[phase_name]
            source_audits[name][phase_name] = audit_source_hashes(
                f"{name}/{phase_name}", report["source_sha256"], report["source_sha256_after"], run_dir)
    probe_source_audits = {}
    probe_snapshot = {"probe.json": "probe_producer_v1.py", "probe_deep.json": "probe_producer_deep.py",
                      "probe_mixed.json": "probe_producer_mixed.py"}
    for probe_name, producer_name in probe_snapshot.items():
        data = read_json(PHASE / probe_name)
        current_code = Path("/home/ajou/yigyu/3/stability_adapter_2/finger_grip_probe.py")
        expected = data["input_sha256"][str(current_code)]
        actual_live = sha(current_code)
        saved = PHASE / producer_name
        if data["input_sha256"] != data["input_sha256_after"]:
            raise ValueError(f"probe input SHA changed in its recorded run: {probe_name}")
        if actual_live != expected and sha(saved) != expected:
            raise ValueError(f"probe producer snapshot does not resolve recorded code SHA: {probe_name}")
        probe_source_audits[probe_name] = {"recorded_source_sha256": expected,
            "current_source_sha256": actual_live, "producer_snapshot": str(saved),
            "producer_snapshot_sha256": sha(saved), "snapshot_matches_recorded_source": sha(saved) == expected}
    same_initial_guitar_goal = (
        baseline["guitar_goal_position_m"] == seeded["guitar_goal_position_m"]
        and baseline["guitar_goal_quaternion_xyzw"] == seeded["guitar_goal_quaternion_xyzw"]
    )
    same_length = baseline["absolute_rest_length_m"] == seeded["absolute_rest_length_m"]
    same_pd = (baseline["native_pd_kp"] == seeded["native_pd_kp"]
               and baseline["native_pd_kd"] == seeded["native_pd_kd"])
    bias_same = baseline["arm_static_bias_rad"] == seeded["arm_static_bias_rad"]
    cap_same = baseline["arm_target_delta_cap_rad"] == seeded["arm_target_delta_cap_rad"]

    fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True, constrained_layout=True)
    styles = (("baseline", "#245c9f", "Baseline"),
              ("seed120_preload050_hold", "#d46b22", "LH finger seed + preload/hold"))
    for name, color, label in styles:
        trace = loaded[name]["hold"][1]
        time = [row["time_s"] for row in trace]
        position = [row["position_error_m"] * 1000 for row in trace]
        rotation = [row["rotation_error_deg"] for row in trace]
        axes[0].plot(time, position, color=color, linewidth=2, label=label)
        axes[1].plot(time, rotation, color=color, linewidth=2, label=label)
        axes[0].scatter([time[-1]], [position[-1]], color=color, s=20, zorder=3)
        axes[1].scatter([time[-1]], [rotation[-1]], color=color, s=20, zorder=3)
    axes[0].set_title("Saved 0.5 s guitar-error traces")
    axes[0].set_ylabel("Position error (mm)")
    axes[1].set_ylabel("Rotation error (deg)")
    axes[1].set_xlabel("Time (s)")
    axes[1].set_xlim(0, 0.5)
    for ax in axes:
        ax.grid(True, alpha=.25)
        ax.legend(loc="upper left")
    fig.savefig(out / "guitar_error_hold_05s.png", dpi=180)
    plt.close(fig)

    after = {str(path): sha(path) for path in input_paths}
    if before != after:
        raise RuntimeError("an input changed while making the read-only plot")
    summary = {
        "phase": "finger_grip_hold_v1",
        "measurement_source": "saved report/trace/control/contact JSON; no simulation run",
        "probes": probe_summary,
        "producer_source_audit": {"runs": source_audits, "source_only_probes": probe_source_audits},
        "conditions": results,
        "initial_comparison": {
            "changed_initial_joint_angles": angle_changes,
            "changed_joint_angle_count": len(angle_changes),
            "same_guitar_goal_position_and_quaternion": same_initial_guitar_goal,
            "same_absolute_rest_length": same_length,
            "same_native_pd_kp_kd": same_pd,
            "same_arm_static_bias": bias_same,
            "same_arm_target_delta_cap": cap_same,
            "baseline_arm_target_delta_cap_rad": baseline["arm_target_delta_cap_rad"],
            "seeded_arm_target_delta_cap_rad": seeded["arm_target_delta_cap_rad"],
        },
        "inputs_sha256_before": before,
        "inputs_sha256_after": after,
        "plot_producer_sha256_before": before[str(Path(__file__).resolve())],
        "plot_producer_sha256_after": sha(Path(__file__).resolve()),
        "outputs_sha256": {"guitar_error_hold_05s.png": sha(out / "guitar_error_hold_05s.png")},
    }
    (out / "analysis_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"out_dir": str(out), "image": "guitar_error_hold_05s.png",
                      "inputs": len(input_paths), "probes": len(probe_summary)}))


if __name__ == "__main__":
    main()
