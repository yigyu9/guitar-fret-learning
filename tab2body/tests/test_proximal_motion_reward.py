"""CPU unit checks for the R12 goal-aware motion hierarchy."""
from pathlib import Path
import sys

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env.rewards.motion import (
    proximal_priority_reward,
    target_settling_gate,
    wrist_settling_gate,
)


def main():
    distance = torch.tensor([0.04, 0.07, 0.11, 0.14])
    radius = torch.full_like(distance, 0.04)
    gate = wrist_settling_gate(distance, radius, transition=0.10)
    assert torch.allclose(gate[[0, 3]], torch.tensor([1.0, 0.0]))
    assert gate[0] > gate[1] > gate[2] > gate[3]

    tip_distance = torch.tensor([0.010, 0.025, 0.045, 0.060])
    tip_gate = target_settling_gate(tip_distance, transition=0.040)
    assert torch.allclose(tip_gate[[0, 3]], torch.tensor([1.0, 0.0]))
    assert tip_gate[0] > tip_gate[1] > tip_gate[2] > tip_gate[3]

    ones = torch.ones(1)
    zeros = torch.zeros(1)
    base = {name: zeros.clone() for name in ("finger", "wrist", "elbow", "shoulder")}
    rewards = {}
    for name in base:
        motion = {key: value.clone() for key, value in base.items()}
        motion[name] = ones.clone()
        rewards[name] = float(proximal_priority_reward(motion, ones)[0])
    assert rewards["finger"] > rewards["wrist"] > rewards["elbow"] > rewards["shoulder"]

    moving = {name: torch.full((1,), 10.0) for name in base}
    free_reward, _ = proximal_priority_reward(moving, zeros)
    assert torch.allclose(free_reward, torch.ones_like(free_reward))
    print("PASS: fingertip gate and finger<wrist<elbow<shoulder motion priority")


if __name__ == "__main__":
    main()
