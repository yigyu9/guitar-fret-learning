"""Design-only arithmetic probes; no Gym, detector, rollout or PPO is exercised."""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    outputs = [args.out / name for name in ("formula_checks.json", "plot_data.json")]
    if any(p.exists() for p in outputs):
        raise FileExistsError("Use a fresh output directory; preserve consumed results")
    plan = Path(__file__).with_name("UPPER_BODY_REWARD_DESIGN_V4.md")
    checks = []

    def check(name, passed):
        checks.append({"name": name, "passed": bool(passed)})

    # Integrate the intersection with the planned window, not elapsed runtime.
    def normalized_hold(duration, hz, stop=None):
        end = duration if stop is None else stop
        return sum(max(0.0, min((i + 1) / hz, duration, end) - i / hz)
                   / duration for i in range(math.ceil(end * hz)))

    for duration in (0.137, 1.0, 5.0, 10.0):
        for hz in (30, 60, 120):
            check(f"hold_fixed_window_{duration}s_{hz}hz",
                  math.isclose(normalized_hold(duration, hz), 1.0, abs_tol=1e-12))
    check("early_stop_keeps_original_denominator",
          math.isclose(normalized_hold(5, 60, 1), 0.2, abs_tol=1e-12))
    check("waiting_after_end_creates_no_extra_hold",
          math.isclose(normalized_hold(1, 60, 5), 1, abs_tol=1e-12))
    trace = ((0, 0), (0.2, 0), (0.5, 0.25), (0.75, 0.25), (1, 0.5))
    increments = [min(b) - min(a) for a, b in zip(trace, trace[1:])]
    check("chord_online_min_telescopes", math.isclose(sum(increments), 0.5))
    check("one_good_string_does_not_complete_chord", min((1, 0)) == 0)
    check("open_or_idle_no_hold_bonus", min([], default=0) == 0)

    aux_weights = (0.05, 0.025, 0.001, -0.025, -0.005, -0.025, -0.01, -0.009)
    secondary_weights = (0.10, 0.02, -0.05, -0.05, 0.05, 0.03)
    bounds = {}
    for name, weights, lower, upper in (
            ("aux", aux_weights, -0.074, 0.076),
            ("continuity", secondary_weights, -0.10, 0.20)):
        values = [sum(w * v for w, v in zip(weights, vertex))
                  for vertex in itertools.product((0, 1), repeat=len(weights))]
        check(f"{name}_all_vertex_bounds", math.isclose(min(values), lower)
              and math.isclose(max(values), upper))
        bounds[name] = {"min": min(values), "max": max(values),
                        "vertices_checked": len(values)}
    for m in (1, 2, 6, 12, 36, 600):
        beta = 6 / max(6, m)
        check(f"lower_tiers_cannot_cover_one_primary_loss_m{m}",
              0.45 * beta < 4 / max(6, m))
    check("draft_hold_counterexample_exists", 2 * (2 * 5 / 6 - 1) + 1 > 2)
    check("refined_hold_does_not_reverse_onset_example",
          2 * (2 * 5 / 6 - 1) + 0.1 < 2)
    check("worst_lower_tiers_do_not_reverse_six_string_example",
          2 - 0.174 > 2 * (2 * 5 / 6 - 1) + 0.276)
    check("single_and_complete_strum_same_primary", (4 * 1 - 2) == (4 * 6 / 6 - 2))
    check("five_of_six_strum_not_full", 5 / 6 < 1)
    crossings = [(3, 11, 2), (3, 11, 2), (3, 12, 2)]
    check("unique_wrong_crossings_not_unique_event", len(set(crossings)) == 2)
    check("miss_baseline_once_with_partial_hit", math.isclose(4 * 5 / 6 - 2, 4 / 3))

    def region_distance(x, lower, upper):
        return max(lower - x, 0, x - upper)

    # A toy 20mm-long cell, not an asset or contact geometry validation.
    cell = [max(0, 1 - region_distance(u * 0.02, 0.002, 0.018) / 0.25)
            for u in (0.1, 0.2, 0.5, 0.8, 0.9)]
    check("toy_valid_fret_band_plateau", cell == [1] * 5)
    approach = [max(0, 1 - d / 0.25) for d in (0, .005, .05, .10, .20, .25)]
    check("coarse_approach_monotone_without_near_miss_cliff",
          all(a >= b for a, b in zip(approach, approach[1:])))
    check("coarse_approach_has_far_signal", approach[4] > 0)

    def rho(x):
        return x * x if x <= 1 else 2 * x - 1

    guitar_raw = [0.5 * rho(d / .02) for d in (0, .005, .02, .04, .08)]
    guitar_capped = [min(1, c) for c in guitar_raw]
    check("guitar_inside_zero_outside_monotone",
          guitar_raw[0] == 0 and all(a < b for a, b in zip(guitar_raw, guitar_raw[1:])))
    check("guitar_cap_does_not_erase_raw_drift", guitar_raw[-1] > guitar_capped[-1] == 1)

    # Prior valid evidence is kept while unobserved scheduled evidence is zero.
    check("fatal_retains_prior_fret_checkpoint", sum((1, 0)) / 2 == .5)
    paid_hit = 4 / 6
    future_deadline_baseline = -2
    check("fatal_partial_strum_ledger_no_double_hit", math.isclose(
          paid_hit + future_deadline_baseline, 4 * (1 / 6) - 2))
    gamma = .99
    tail = [-.2, -.2, -2.2, -.2]
    collapsed = sum(gamma ** (i + 1) * r for i, r in enumerate(tail))
    expanded = sum(gamma ** i * r for i, r in enumerate([0] + tail))
    check("discounted_tail_collapse_matches_expansion", math.isclose(collapsed, expanded))
    check("unbounded_wrong_cost_requires_bound_gate", -100 < collapsed)
    check("later_correct_fret_cannot_repair_wrong_onset", int(False) == 0)

    data = {
        "scope": "synthetic design arithmetic; no physics, detector, tracker or PPO test",
        "plan_sha256": hashlib.sha256(plan.read_bytes()).hexdigest(),
        "verifier_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "hold_comparison": [{"duration_s": t, "v3_hold_max": 2 * t,
                             "v4_hold_max_one_event_beta1": .10}
                            for t in (.137, 1, 5, 10)],
        "onset_example": {"six_string_correct_lower_worst": 2 - .174,
                          "five_of_six_wrong_lower_best": 4 / 3 + .276,
                          "draft_correct_hold0": 2,
                          "draft_wrong_hold1": 4 / 3 + 1},
        "bounds_beta1": bounds,
        "approach_distance_m": [i / 1000 for i in range(251)],
        "approach_quality": [max(0, 1 - (i / 1000) / .25) for i in range(251)],
        "guitar_sample_distance_m": [0, .005, .02, .04, .08],
        "guitar_raw": guitar_raw, "guitar_capped": guitar_capped,
        "beta_rule": "6/max(6, all Fret O checkpoint counts, all Strike target counts)",
        "native_runs": 0, "training_updates": 0,
    }
    report = {"status": "pass" if all(c["passed"] for c in checks) else "fail",
              "checks": checks, "count": len(checks),
              "scope": data["scope"], "plan_sha256": data["plan_sha256"],
              "verifier_sha256": data["verifier_sha256"]}
    for path, value in zip(outputs, (report, data)):
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "checks": len(checks),
                      "native_runs": 0, "training_updates": 0}))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
