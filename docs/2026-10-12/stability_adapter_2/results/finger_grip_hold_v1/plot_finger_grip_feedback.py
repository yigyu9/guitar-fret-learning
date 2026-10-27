"""Plot saved guitar-error traces for the 0.5 s and 1 s feedback comparisons."""
import argparse
import hashlib
import json
import math
from pathlib import Path

import matplotlib.pyplot as plt

PHASE = Path(__file__).resolve().parent
RUNS = {
    "baseline_05": ("hold_05s/baseline", 120),
    "finger_preload_05": ("hold_05s/seed120_preload050_hold", 120),
    "palm_feedback_05": ("hold_05s/seed120_palm_feedback_v2", 120),
    "palm_cap030_05": ("hold_05s/seed120_palm_cap030", 120),
    "baseline_1": ("hold_1s/baseline", 240),
    "palm_feedback_1": ("hold_1s/seed120_palm_feedback_v2", 240),
    "palm_cap030_1": ("hold_1s/seed120_palm_cap030", 240),
}


def read_json(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_run(relative, steps):
    run = PHASE / relative
    report = read_json(run / "report.json")
    trace = read_json(run / "trace.json")
    contacts = read_json(run / "lh_contacts.json")
    controls = read_json(run / "controls.json")
    if report.get("physics_steps") != steps or report.get("physics_hz") != 240:
        raise ValueError(f"unexpected duration/rate: {relative}")
    if not report.get("checks") or not all(report["checks"].values()):
        raise ValueError(f"saved report checks failed: {relative}")
    if len(trace) != steps + 1 or len(controls) != steps:
        raise ValueError(f"unexpected trace/control count: {relative}")
    for i, row in enumerate(trace):
        if abs(row["time_s"] - i / 240) > 1e-12 or not row.get("finite", False):
            raise ValueError(f"invalid time/finite sample: {relative} #{i}")
        if not math.isfinite(row["position_error_m"]) or not math.isfinite(row["rotation_error_deg"]):
            raise ValueError(f"nonfinite guitar error: {relative} #{i}")
    if abs(max(x["position_error_m"] for x in trace) - report["max_position_error_m"]) > 1e-12:
        raise ValueError(f"position peak differs from report: {relative}")
    if abs(max(x["rotation_error_deg"] for x in trace) - report["max_rotation_error_deg"]) > 1e-12:
        raise ValueError(f"rotation peak differs from report: {relative}")
    return report, trace, contacts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    out = args.out_dir.resolve()
    if out.exists():
        raise FileExistsError(f"preserve existing artifacts: {out}")
    out.mkdir(parents=True)

    names = list(RUNS)
    input_paths = [PHASE / rel / f for rel, _ in RUNS.values()
                   for f in ("report.json", "trace.json", "controls.json", "lh_contacts.json")]
    input_paths.append(Path(__file__).resolve())
    input_paths = sorted(set(input_paths))
    before = {str(p): sha(p) for p in input_paths}
    loaded = {name: load_run(*RUNS[name]) for name in names}

    fig, axes = plt.subplots(2, 2, figsize=(13, 8), constrained_layout=True, sharex="col")
    panels = [
        (axes[0, 0], axes[1, 0], "palm_feedback_05", 0.5),
        (axes[0, 1], axes[1, 1], "palm_feedback_1", 1.0),
    ]
    palette = {
        "baseline_05": ("#245c9f", "Baseline, 0.5 s"),
        "finger_preload_05": ("#d46b22", "Finger seed + preload/hold, 0.5 s"),
        "palm_feedback_05": ("#198754", "Palm feedback v2, 0.5 s"),
        "baseline_1": ("#245c9f", "Baseline, 1 s"),
        "palm_feedback_1": ("#198754", "Palm feedback v2, 1 s"),
        "palm_cap030_1": ("#a43f9f", "Palm cap 0.30 rad, 1 s"),
    }
    for p_ax, q_ax, feedback_key, duration in panels:
        keys = ("baseline_05", "finger_preload_05", feedback_key) if duration == 0.5 else ("baseline_1", "palm_feedback_1", "palm_cap030_1")
        for key in keys:
            color, label = palette[key]
            trace = loaded[key][1]
            t = [r["time_s"] for r in trace]
            p = [r["position_error_m"] * 1000 for r in trace]
            q = [r["rotation_error_deg"] for r in trace]
            line_style = "--" if key == "palm_cap030_1" else "-"
            p_ax.plot(t, p, color=color, linewidth=1.8, linestyle=line_style, label=label)
            q_ax.plot(t, q, color=color, linewidth=1.8, linestyle=line_style, label=label)
        p_ax.set_title(f"Guitar position error, {duration:g} s")
        q_ax.set_title(f"Guitar rotation error, {duration:g} s")
        p_ax.set_ylabel("Position error (mm)")
        q_ax.set_ylabel("Rotation error (deg)")
        for ax in (p_ax, q_ax):
            ax.set_xlim(0, duration)
            ax.set_xlabel("Time (s)")
            ax.grid(True, alpha=.25)
            ax.legend(loc="best", fontsize=8)
    fig.suptitle("Saved PhysX trace comparison (no new simulation)")
    image = out / "guitar_error_feedback_hold.png"
    fig.savefig(image, dpi=180)
    plt.close(fig)

    after = {str(p): sha(p) for p in input_paths}
    if before != after:
        raise RuntimeError("an input changed during plotting")
    manifest = {
        "phase": "finger_grip_hold_v1",
        "measurement_source": "saved report/trace/control/contact JSON only; no simulation run",
        "runs": {name: {"path": str(PHASE / rel), "steps": steps,
                         "report_checks_all_true": all(loaded[name][0]["checks"].values()),
                         "max_position_error_mm": loaded[name][0]["max_position_error_m"] * 1000,
                         "max_rotation_error_deg": loaded[name][0]["max_rotation_error_deg"],
                         "lh_contact_rows": len(loaded[name][2])}
                 for name, (rel, steps) in RUNS.items()},
        "inputs_sha256_before": before,
        "inputs_sha256_after": after,
        "plot_source_sha256": sha(Path(__file__).resolve()),
        "outputs_sha256": {image.name: sha(image)},
    }
    (out / "plot_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"out_dir": str(out), "image": str(image), "input_count": len(input_paths)}))


if __name__ == "__main__":
    main()
