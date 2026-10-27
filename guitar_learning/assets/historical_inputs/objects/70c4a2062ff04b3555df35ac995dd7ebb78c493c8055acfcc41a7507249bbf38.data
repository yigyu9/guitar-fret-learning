from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from learning.ppo import (
    compact_training_stats,
    concise_training_line,
    detailed_training_line,
)


def main():
    stats = {
        "iteration": 10,
        "steps": 327680,
        "reward": 0.0383,
        "curriculum_stage": "coarse_reach",
        "curriculum_stage_iteration": 9,
        "curriculum_p90_target_distance": 0.2072,
        "curriculum_success_rate": 0.0,
        "f1_l": 0.0,
        "failure_termination": 0.0,
        "value_loss": 0.0562,
    }
    concise = concise_training_line(stats, first=1, last=50000)
    assert "epoch 10/50000" in concise
    assert "reward=0.0383" in concise
    assert "p90=207.2mm" in concise
    assert "value_loss" not in concise
    strike_s3 = concise_training_line({
        **stats,
        "curriculum_stage": "S3_SONG_INTEGRATION",
        "strike_episode_f1": 0.875,
        "f1_l": None,
    }, first=1, last=50000)
    assert "window-F1=0.875" in strike_s3
    assert " | F1=" not in strike_s3
    stalled = concise_training_line(
        {**stats, "curriculum_stalled": True}, first=1, last=50000)
    assert "stalled=continue" in stalled
    strict = concise_training_line({
        **stats,
        "curriculum_stage": "isolated_press",
        "curriculum_early_min_success_rate": 0.395,
        "curriculum_early_bottleneck_finger": 3,
        "curriculum_finger_3_precision_press_rate": 0.71,
        "curriculum_finger_3_precision_position_rate": 0.83,
        "curriculum_finger_3_precision_arch_rate": 0.50,
    }, first=1, last=50000)
    assert "strict-min=f3:39.5%" in strict
    assert "strict-gate=arch:50.0%" in strict
    forced = concise_training_line({
        **stats,
        "curriculum_forced_advance": True,
        "curriculum_last_forced_advance_from": "isolated_press",
    }, first=1, last=50000)
    assert "forced-advance=isolated_press" in forced
    recovery = concise_training_line({
        **stats,
        "curriculum_goal_pair_recovery": True,
        "curriculum_goal_pair_recovery_reason": "performance_regression",
        "curriculum_goal_pair_recovery_iteration": 200,
        "curriculum_goal_pair_recovery_max_iterations": 1200,
    }, first=1, last=50000)
    assert "recovery=performance_regression:200/1200" in recovery
    rollback = concise_training_line({
        **stats,
        "curriculum_goal_pair_recovery_rollback": True,
        "curriculum_goal_pair_last_recovery_rollback": (
            "mixed:0->retention:performance_regression"),
    }, first=1, last=50000)
    assert (
        "rollback=mixed:0->retention:performance_regression" in rollback)
    detailed = detailed_training_line(stats)
    assert "value_loss=0.0562" in detailed
    assert "steps=327680" in detailed
    nested = {**stats, "curriculum_recent": [0.1, 0.2],
              "curriculum_state": {"large": True}}
    assert "curriculum_recent" not in detailed_training_line(nested)
    compact = compact_training_stats(nested)
    assert "value_loss" in compact
    assert "curriculum_recent" not in compact
    assert "curriculum_state" not in compact
    print("PASS: concise terminal progress and detailed file log")


if __name__ == "__main__":
    main()
