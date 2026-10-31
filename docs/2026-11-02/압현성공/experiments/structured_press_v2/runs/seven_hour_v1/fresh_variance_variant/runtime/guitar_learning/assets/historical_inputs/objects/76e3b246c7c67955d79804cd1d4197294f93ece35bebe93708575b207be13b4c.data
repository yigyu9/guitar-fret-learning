"""손가락·오압현·관절 한계·자연스러움 진단 그래프를 만든다."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from tab2body.tools.training_metrics import load_metric_rows


FINGERS = ("index", "middle", "ring", "pinky")
JOINT_GROUPS = (
    "shoulder", "elbow", "wrist", "thumb",
    "finger_1", "finger_2", "finger_3", "finger_4",
)


def _plot(axis, rows, key, label, scale=1.0):
    points = [
        (row["steps"], row[key] * scale)
        for row in rows if "steps" in row and key in row
        and isinstance(row[key], (int, float))]
    if points:
        x, y = zip(*points)
        axis.plot(x, y, linewidth=1.1, label=label)
    return bool(points)


def _last_values(rows, keys):
    result = {}
    for key in keys:
        values = [row[key] for row in rows
                  if isinstance(row.get(key), (int, float))]
        if values:
            result[key] = {
                "last": values[-1],
                "min": min(values),
                "max": max(values),
            }
    return result


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("metrics", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--summary", type=Path, default=None)
    args = parser.parse_args(argv)
    source = args.metrics.resolve()
    finger_rate_keys = tuple(
        f"finger_{finger}_press_success_rate" for finger in range(1, 5))
    finger_distance_keys = tuple(
        f"curriculum_finger_{finger}_target_distance"
        for finger in range(1, 5))
    precision_funnel_keys = tuple(
        f"curriculum_finger_{finger}_precision_{name}"
        for finger in range(1, 5)
        for name in (
            "press_rate", "position_rate", "arch_rate", "precise_rate",
            "streak_rate", "fraction_pass_rate", "final_rate"))
    sampler_keys = tuple(
        name
        for finger in range(1, 5)
        for name in (
            f"curriculum_practice_sampler_finger_{finger}_assignments",
            f"curriculum_practice_sampler_finger_{finger}_fraction",
            f"curriculum_practice_sampler_finger_{finger}_target_fraction",
        ))
    joint_max_keys = tuple(
        f"curriculum_joint_limit_{group}_max_usage_p95"
        for group in JOINT_GROUPS)
    joint_near_keys = tuple(
        f"curriculum_joint_limit_{group}_near_rate"
        for group in JOINT_GROUPS)
    behavior_keys = (
        "wrong_press_rate", "press_dropout_rate", "sustain_hold_rate",
        "curriculum_reach_frame_success_rate",
        "curriculum_stable_press_success_rate",
        "curriculum_fine_reach_action_scale_min",
        "curriculum_fine_reach_proximal_action_scale",
        "curriculum_early_recovery_focus_finger",
        "curriculum_early_recovery_focus_iteration",
        "curriculum_early_recovery_focus_blocks",
        "curriculum_early_recovery_total_blocks",
        "curriculum_early_recovery_max_total_blocks",
        "curriculum_early_recovery_exhausted",
        "curriculum_early_recovery_retention_max_drop",
        *(f"curriculum_early_recovery_finger_{finger}_weight"
          for finger in range(1, 5)),
        "curriculum_early_evidence_stalled",
        "curriculum_practice_focus_reset_count",
        "curriculum_practice_focus_reset_consecutive",
        "curriculum_integrated_recovery_block_count",
        "curriculum_integrated_recovery_total_iteration",
        "curriculum_integrated_recovery_retention_max_drop",
        "curriculum_integrated_recovery_min_rate_improvement",
        "curriculum_integrated_recovery_no_improvement_blocks",
        "curriculum_integrated_recovery_exhausted",
        "curriculum_practice_sampler_assignment_total",
        "curriculum_practice_sampler_focus_target_fraction",
        "curriculum_practice_sampler_focus_actual_fraction",
        "curriculum_practice_sampler_max_quota_error",
        "curriculum_practice_sampler_reset_batch_mean",
        "curriculum_practice_sampler_reset_batch_max",
        "curriculum_practice_sampler_singleton_reset_fraction",
        "wrong_press_termination", "wrong_press_termination_count",
        "curriculum_release_pose_error_deg",
        "curriculum_finger_coupling_active_rate",
        "curriculum_finger_synergy_active_rate",
        "curriculum_finger_synergy_induced_deg",
        "curriculum_reference_posture_quality",
        "curriculum_human_joint_range_quality",
        "curriculum_human_joint_range_violation_rate",
        "curriculum_human_joint_range_max_excess_deg",
        *(name
          for finger in range(1, 5)
          for name in (
              f"curriculum_early_finger_{finger}_evidence_age",
              f"curriculum_early_finger_{finger}_recent_episodes")),
        "curriculum_human_joint_range_penalty",
        "curriculum_joint_limit_max_usage_p95",
        "curriculum_joint_limit_near_rate",
        "curriculum_thorax_hold_error_deg",
        "curriculum_thorax_hold_velocity_deg_s",
        "curriculum_thorax_hold_torque_fraction",
        "curriculum_static_chord_recovery",
        "curriculum_static_chord_recovery_count",
        "curriculum_static_chord_blocked",
        "curriculum_static_chord_completion_gate",
        "curriculum_static_chord_auxiliary_gate",
        "curriculum_finger_back_soft_penalty",
        "curriculum_finger_back_proximal_min_local_z",
        "curriculum_finger_back_distal_min_local_z",
    )
    chord_rate_keys = tuple(
        f"chord_set_{signature}_success_rate"
        for signature in range(1, 16))
    keys = (
        "steps", "curriculum_stage", *finger_rate_keys,
        *finger_distance_keys, *joint_max_keys, *joint_near_keys,
        *precision_funnel_keys, *sampler_keys, *chord_rate_keys,
        *behavior_keys,
    )
    rows = load_metric_rows(source, keys)
    if not rows:
        raise SystemExit("metrics file is empty")

    fig, axes = plt.subplots(5, 2, figsize=(14, 18), dpi=150,
                             constrained_layout=True)
    for finger, label in enumerate(FINGERS, start=1):
        _plot(axes[0, 0], rows, finger_rate_keys[finger - 1], label)
        _plot(axes[0, 1], rows, finger_distance_keys[finger - 1],
              label, scale=1000.0)
    axes[0, 0].set_title("Press success by finger")
    axes[0, 0].set_ylim(-0.02, 1.02)
    axes[0, 1].set_title("Target distance by finger")
    axes[0, 1].set_ylabel("mm")

    _plot(axes[1, 0], rows, "wrong_press_rate", "wrong press")
    _plot(axes[1, 0], rows, "press_dropout_rate", "press dropout")
    _plot(axes[1, 0], rows, "sustain_hold_rate", "sustain hold")
    _plot(axes[1, 0], rows,
          "curriculum_reach_frame_success_rate", "reach success")
    _plot(axes[1, 0], rows,
          "curriculum_stable_press_success_rate", "stable press")
    axes[1, 0].set_title("Press correctness and hold")
    axes[1, 0].set_ylim(-0.02, 1.02)

    for group, key in zip(JOINT_GROUPS, joint_near_keys):
        _plot(axes[1, 1], rows, key, group)
    _plot(axes[1, 1], rows, "curriculum_joint_limit_near_rate", "all")
    axes[1, 1].set_title("Hard-limit 90% proximity rate")
    axes[1, 1].set_ylim(-0.02, 1.02)

    for group, key in zip(JOINT_GROUPS, joint_max_keys):
        _plot(axes[2, 0], rows, key, group)
    _plot(axes[2, 0], rows, "curriculum_joint_limit_max_usage_p95",
          "all")
    axes[2, 0].axhline(1.0, color="tab:red", linestyle="--", linewidth=1)
    axes[2, 0].set_title("P95 normalized joint-limit usage")

    _plot(axes[2, 1], rows, "curriculum_finger_coupling_active_rate",
          "coupling active")
    _plot(axes[2, 1], rows, "curriculum_finger_synergy_active_rate",
          "synergy active")
    _plot(axes[2, 1], rows, "curriculum_reference_posture_quality",
          "reference quality")
    _plot(axes[2, 1], rows, "curriculum_human_joint_range_quality",
          "human-range quality")
    _plot(axes[2, 1], rows,
          "curriculum_human_joint_range_violation_rate",
          "human-range violation")
    _plot(axes[2, 1], rows,
          "curriculum_fine_reach_action_scale_min", "fine min scale")
    _plot(axes[2, 1], rows,
          "curriculum_fine_reach_proximal_action_scale",
          "fine proximal scale")
    axes[2, 1].set_title("Natural-motion diagnostics")
    axes[2, 1].set_ylim(-0.02, 1.02)

    for signature, key in enumerate(chord_rate_keys, start=1):
        _plot(axes[3, 0], rows, key, f"set {signature}")
    axes[3, 0].set_title("Chord-set episode success")
    axes[3, 0].set_ylim(-0.02, 1.02)

    _plot(axes[3, 1], rows,
          "curriculum_static_chord_completion_gate", "completion gate")
    _plot(axes[3, 1], rows,
          "curriculum_static_chord_auxiliary_gate", "auxiliary gate")
    _plot(axes[3, 1], rows,
          "curriculum_static_chord_recovery", "recovery")
    _plot(axes[3, 1], rows,
          "curriculum_static_chord_blocked", "blocked")
    axes[3, 1].set_title("Static-chord recovery diagnostics")
    axes[3, 1].set_ylim(-0.02, 1.02)

    ring_prefix = "curriculum_finger_3_precision_"
    for name, label in (
            ("press_rate", "contact"),
            ("position_rate", "position"),
            ("arch_rate", "arch"),
            ("precise_rate", "combined frame"),
            ("streak_rate", "12-frame streak"),
            ("fraction_pass_rate", "80% fraction"),
            ("final_rate", "episode final")):
        _plot(axes[4, 0], rows, ring_prefix + name, label)
    axes[4, 0].set_title("Ring-finger isolated-press gates")
    axes[4, 0].set_ylim(-0.02, 1.02)

    for finger, label in enumerate(FINGERS, start=1):
        _plot(
            axes[4, 1], rows,
            f"curriculum_finger_{finger}_precision_final_rate", label)
    axes[4, 1].set_title("Strict isolated-press episode success")
    axes[4, 1].set_ylim(-0.02, 1.02)

    for axis in axes.flat:
        axis.set_xlabel("environment samples")
        axis.grid(alpha=0.25)
        handles, labels = axis.get_legend_handles_labels()
        if handles:
            axis.legend(fontsize=7, ncol=2)

    output = (args.out.resolve() if args.out else
              source.parents[1] / "plots" / "fret_diagnostics.png")
    summary = (args.summary.resolve() if args.summary else
               output.with_suffix(".summary.json"))
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output)
    summary.write_text(json.dumps({
        "metrics": str(source),
        "rows": len(rows),
        "observed": _last_values(rows, keys[2:]),
    }, indent=2, ensure_ascii=False))
    print(f"saved: {output}")
    print(f"summary: {summary}")


if __name__ == "__main__":
    main()
