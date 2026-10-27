"""Reproduce reward-design counterexamples; no Gym or policy execution."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    # Consume a frozen, explicit manifest rather than guessing the latest version.
    inputs = [
        ROOT / "stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md",
        ROOT / "stability_adapter_2/REWARD_DESIGN_AUDIT_V4_PLAN.md",
        Path(__file__).resolve(),
        ROOT / "tab2body/env/metrics.py",
        ROOT / "tab2body/learning/ppo.py",
    ]
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    spec = importlib.util.spec_from_file_location("audit_metrics", inputs[3])
    metrics = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(metrics)
    cases = []
    for name, drops in [
        ("scattered", {5, 13, 21, 29, 37, 45}),
        ("continuous", set(range(25, 31))),
    ]:
        trace = [i not in drops for i in range(60)]
        tracker = metrics.PressSustainTracker(1, 1, "cpu")
        for correct in trace:
            tracker.update(torch.tensor([0]), torch.tensor([True]),
                           torch.tensor([correct]))
        result = tracker.episode_metrics(torch.tensor([0]))
        # E=1 is a conditional example, not an implemented v4 E detector.
        u = sum(trace) / len(trace)
        cases.append({"name": name, "trace": trace, "correct_frames": sum(trace),
                      "eligible_frames": len(trace), "U": u,
                      "O_at_last_frame": int(trace[-1]), "assumed_E": 1,
                      "conditional_Fret_plus_U_E": 2 + 0.1 * u - 0.05,
                      "source_metrics": {k: v.item() for k, v in result.items()}})
    assert cases[0]["U"] == cases[1]["U"] == 0.9
    assert cases[0]["source_metrics"]["sustain_event_success_count"] == 1
    assert cases[1]["source_metrics"]["sustain_event_success_count"] == 0
    discount = [
        {"gamma_per_step": g, "synthetic_hz": 60,
         "half_life_seconds": math.log(0.5) / math.log(g) / 60,
         "weight_after_2s": g ** 120, "weight_after_5s": g ** 300}
        for g in (0.95, 0.99, 0.995)
    ]
    dilution = []
    for nf, checks, seconds in [(1, 6, 7), (16, 6, 22), (64, 24, 62)]:
        beta = 6 / max(6, checks)
        dilution.append({"NF": nf, "m_max": max(6, checks), "beta": beta,
                         "T_phys_seconds": seconds,
                         "U_max_per_event": 0.1 * beta / nf,
                         "A_max_per_event": 0.05 * beta / nf,
                         "B_max_per_episode": 0.025 * beta,
                         "B_cost_per_saturated_frame_at_60Hz":
                         0.025 * beta / (seconds * 60)})
    guitar = []
    for mm in (0, 10, 20, 30, 40, 100):
        x = mm / 20
        rho = x * x if x <= 1 else 2 * x - 1
        raw = 0.5 * rho
        guitar.append({"pure_position_outside_mm": mm, "rotation_outside_deg": 0,
                       "C_raw": raw, "C_g": min(1, raw)})
    assert [v["C_g"] for v in guitar[-3:]] == [1, 1, 1]
    # Constant actual pressure accuracy at two target durations. The cumulative
    # minimum stays zero until the later eligible window opens.
    staggered = {"T_each_seconds": 1, "first_window": [0, 1],
                 "second_window": [1, 2], "sample_times": [0.5, 1, 1.5, 2],
                 "cumulative_u": [[0.5, 0], [1, 0], [1, 0.5], [1, 1]],
                 "U_min": [0, 0, 0.5, 1]}
    for p in inputs:
        assert hashlib.sha256(p.read_bytes()).hexdigest() == hashes[str(p)]
    output = {"scope": "synthetic arithmetic + actual CPU sustain tracker; no physics/training",
              "torch_version": torch.__version__, "input_sha256": hashes,
              "discount": discount, "dilution": dilution,
              "dropout": cases, "guitar_cap": guitar, "staggered_min": staggered,
              "checks": {"same_U": True, "different_source_success": True,
                         "guitar_cap_plateau": True, "inputs_unchanged": True},
              "native_runs": 0, "training_updates": 0}
    with args.out.open("x", encoding="utf-8") as handle:
        json.dump(output, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps({"out": str(args.out), "checks": output["checks"],
                      "source_success_counts": [c["source_metrics"]["sustain_event_success_count"]
                                                for c in cases]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
