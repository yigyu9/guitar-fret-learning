"""CPU unit checks for the R13 palm-to-floor termination geometry and filter."""
from pathlib import Path
import sys

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env.safety import palm_inward_normal, update_consecutive_violation


def main():
    wrist = torch.tensor([[0.0, 0.0, 0.0]])
    middle = torch.tensor([[1.0, 0.0, 0.0]])
    index_up = torch.tensor([[0.0, 1.0, 0.0]])
    pinky_up = torch.tensor([[0.0, 0.0, 0.0]])
    normal_up, valid_up = palm_inward_normal(wrist, index_up, middle, pinky_up)
    assert valid_up.item() and torch.allclose(normal_up, torch.tensor([[0.0, 0.0, 1.0]]))

    index_down = torch.tensor([[0.0, 0.0, 0.0]])
    pinky_down = torch.tensor([[0.0, 1.0, 0.0]])
    normal_down, valid_down = palm_inward_normal(wrist, index_down, middle, pinky_down)
    assert valid_down.item() and normal_down[0, 2] < -0.3

    streak = torch.zeros(1, dtype=torch.long)
    for expected in (1, 2, 3):
        streak = update_consecutive_violation(streak, torch.tensor([True]), valid_down)
        assert streak.item() == expected
    assert (streak >= 3).item()
    streak = update_consecutive_violation(streak, torch.tensor([False]), valid_down)
    assert streak.item() == 0

    _, invalid = palm_inward_normal(wrist, wrist, wrist, wrist)
    streak.fill_(2)
    streak = update_consecutive_violation(streak, torch.tensor([True]), invalid)
    assert streak.item() == 0
    print("PASS: R13 fixed palm normal, -0.3 threshold, 3-frame filter, invalid reset")


if __name__ == "__main__":
    main()
