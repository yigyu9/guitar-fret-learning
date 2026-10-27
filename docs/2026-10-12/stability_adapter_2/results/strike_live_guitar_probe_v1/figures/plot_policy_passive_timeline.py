#!/usr/bin/env python3
"""Plot the saved native guitar trace across policy stop and passive continuation."""
import hashlib
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PHASE = Path(__file__).resolve().parents[1]
OUT = PHASE / "figures" / "policy_timeline_v2"
SUMMARY = PHASE / "analysis" / "summary.json"
TRACE = PHASE / "native_v2" / "trial" / "trace.json"
REPORT = PHASE / "native_v2" / "trial" / "report.json"
INPUTS = [Path(__file__).resolve(), SUMMARY, TRACE, REPORT]


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def finite(value):
    if isinstance(value, dict):
        return all(finite(v) for v in value.values())
    if isinstance(value, list):
        return all(finite(v) for v in value)
    return not isinstance(value, float) or math.isfinite(value)


def main():
    if OUT.exists() and any(OUT.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty output: {OUT}")
    OUT.mkdir(parents=True, exist_ok=True)
    input_hashes_before = {str(path): sha(path) for path in INPUTS}

    summary = json.loads(SUMMARY.read_text())
    trace = json.loads(TRACE.read_text())
    report = json.loads(REPORT.read_text())
    if not finite(summary) or not finite(trace) or not finite(report):
        raise ValueError("non-finite input")
    if len(trace) != 151 or report.get("physics_steps") != 1200:
        raise ValueError("expected 151 saved states and 1200 physics steps")
    if [row.get("physics_step") for row in trace] != list(range(0, 1201, 8)):
        raise ValueError("unexpected trace sampling")
    policy_end = report.get("policy_end_physics_step")
    policy_end_time = summary.get("policy_end_time_s")
    if policy_end != 196 or policy_end_time is None:
        raise ValueError("missing report policy end or summary timestamp")
    if abs(policy_end_time - policy_end / 240.0) > 1e-12:
        raise ValueError("policy-end timestamp mismatch")
    if not summary.get("post_termination_passive_only") or not report.get("post_termination_passive_only"):
        raise ValueError("passive continuation not recorded")

    times = [row["time_s"] for row in trace]
    position_mm = [row["position_change_m"] * 1000.0 for row in trace]
    rotation_deg = [row["rotation_change_deg"] for row in trace]
    policy_end_time = float(policy_end_time)
    fig, axes = plt.subplots(2, 1, figsize=(11.5, 7.8), sharex=True)
    axes[0].plot(times, position_mm, color="#2563eb", linewidth=2)
    axes[1].plot(times, rotation_deg, color="#d97706", linewidth=2)
    for ax in axes:
        ax.axvline(policy_end_time, color="#b91c1c", linestyle="--", linewidth=1.5)
        ax.axvspan(policy_end_time, 5.0, color="#94a3b8", alpha=.18)
        ax.grid(True, alpha=.25)
        ax.set_xlim(0.0, 5.0)
    axes[0].set_ylabel("Guitar position change (mm)")
    axes[1].set_ylabel("Guitar rotation change (deg)")
    axes[1].set_xlabel("Physics time (s)")
    axes[1].text(.84, .92, "policy stopped\npassive continuation", transform=axes[1].transAxes,
                 ha="left", va="top", fontsize=9, color="#7f1d1d")
    fig.suptitle("Native guitar state: policy phase and passive continuation", fontsize=14)
    fig.text(.5, .012, "Termination at step 196 (0.816667 s; between saved samples 192 and 200). Shaded interval holds the final 81 PD targets; not a playing-policy evaluation.", ha="center", fontsize=8.5)
    fig.tight_layout(rect=(0, .04, 1, .95))
    output = OUT / "policy_passive_timeline.png"
    fig.savefig(output, dpi=180)
    plt.close(fig)

    input_hashes_after = {str(path): sha(path) for path in INPUTS}
    if input_hashes_before != input_hashes_after:
        raise RuntimeError("an input changed while plotting")
    manifest = {
        "producer": str(Path(__file__).resolve()),
        "producer_sha256": sha(Path(__file__).resolve()),
        "inputs_sha256": input_hashes_before,
        "outputs_sha256": {str(output): sha(output)},
        "trace_samples": len(trace),
        "trace_step_interval": 8,
        "physics_steps": report["physics_steps"],
        "policy_end_step": policy_end,
        "policy_end_time_s": policy_end_time,
        "policy_end_sampled": any(row["physics_step"] == policy_end for row in trace),
        "post_termination_passive_only": True,
        "native_initializations_by_plotter": 0,
        "physics_steps_by_plotter": 0,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
