"""Plot fingertip curriculum metrics from a training JSONL log."""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from tab2body.tools.training_metrics import load_metric_rows


STAGE_NAMES = (
    "fine_reach", "isolated_press", "integrated_press",
    "chord_reach", "chord_fine_reach", "static_chord",
    "frozen_context", "goal_pair", "transition_window",
    "coverage", "integration", "full_song",
)
SERIES = (
    ("curriculum_mean_target_distance", "Mean target distance", 1000.0),
    ("curriculum_p90_target_distance", "P90 target distance", 1000.0),
    ("curriculum_cell_alignment_rate", "Fret-cell alignment rate", 1.0),
    ("curriculum_press_success_rate", "Instant press success", 1.0),
    ("curriculum_mean_position_quality", "Strict fret-position quality", 1.0),
    ("curriculum_mean_dense_position_quality", "Dense fret-position quality", 1.0),
    ("curriculum_mean_arch_quality", "Active-finger arch quality", 1.0),
    ("curriculum_press_hold_acquired_rate", "Stable press acquired", 1.0),
    ("curriculum_frame_press_dropout_rate", "Press dropout rate", 1.0),
    ("curriculum_chord_ready", "Chord-ready rate", 1.0),
    ("curriculum_frame_chord_hold_quality", "Chord hold quality", 1.0),
    ("curriculum_chord_joint_quality", "Joint chord quality", 1.0),
    ("curriculum_thumb_distance", "Thumb distance", 1000.0),
    ("curriculum_thumb_support", "Thumb support rate", 1.0),
)
BRIDGE_SERIES = (
    ("curriculum_chord_bridge_mean_reward", "bridge mean"),
    ("curriculum_chord_bridge_min_reward", "bridge minimum"),
    ("curriculum_chord_bridge_bottleneck_reward", "bridge aggregate"),
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("metrics")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    source = Path(args.metrics).resolve()
    keys = (
        "steps", "curriculum_stage",
        *(key for key, _, _ in SERIES),
        *(key for key, _ in BRIDGE_SERIES),
    )
    rows = load_metric_rows(source, keys)
    if not rows:
        raise SystemExit("metrics file is empty")
    x = [row["steps"] for row in rows]
    transitions = [(stage, next((row["steps"] for row in rows
                                 if row.get("curriculum_stage") == stage), None))
                   for stage in STAGE_NAMES]

    fig, axes = plt.subplots(7, 2, figsize=(14, 23), constrained_layout=True)
    for axis, (key, title, scale) in zip(axes.flat, SERIES):
        y = [row.get(key, float("nan")) * scale for row in rows]
        axis.plot(x, y, linewidth=1.0)
        for stage, transition in transitions:
            if transition is not None:
                axis.axvline(transition, linestyle="--", alpha=0.45,
                             label=stage)
        if any(value is not None for _, value in transitions):
            axis.legend()
        axis.set_title(title)
        axis.set_xlabel("environment samples")
        axis.grid(alpha=0.3)
    bridge_axis = axes[5, 1]
    for key, label in BRIDGE_SERIES:
        bridge_axis.plot(
            x, [row.get(key, float("nan")) for row in rows],
            linewidth=1.0, label=label)
    bridge_axis.set_title("Joint chord / bridge bottleneck quality")
    bridge_axis.legend()
    axes[0, 0].set_ylabel("mm")
    axes[0, 1].set_ylabel("mm")
    axes[1, 0].set_ylim(-0.02, 1.02)
    axes[1, 1].set_ylim(-0.02, 1.02)
    for axis in axes.flat[2:12]:
        axis.set_ylim(-0.02, 1.02)
    axes[6, 0].set_ylabel("mm")
    axes[6, 1].set_ylim(-0.02, 1.02)
    target = (Path(args.out).resolve() if args.out else
              source.parents[1] / "plots" / "fingertip_curriculum.png")
    target.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(target, dpi=160)
    print(f"saved: {target}")


if __name__ == "__main__":
    main()
