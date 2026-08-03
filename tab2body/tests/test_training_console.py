from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from learning.ppo import concise_training_line, detailed_training_line


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
    stalled = concise_training_line(
        {**stats, "curriculum_stalled": True}, first=1, last=50000)
    assert "stalled=continue" in stalled
    forced = concise_training_line({
        **stats,
        "curriculum_forced_advance": True,
        "curriculum_last_forced_advance_from": "isolated_press",
    }, first=1, last=50000)
    assert "forced-advance=isolated_press" in forced
    detailed = detailed_training_line(stats)
    assert "value_loss=0.0562" in detailed
    assert "steps=327680" in detailed
    print("PASS: concise terminal progress and detailed file log")


if __name__ == "__main__":
    main()
