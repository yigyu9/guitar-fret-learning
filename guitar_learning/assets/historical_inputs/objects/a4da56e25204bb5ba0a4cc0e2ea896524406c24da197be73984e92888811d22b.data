"""CPU checks for the diagnostic-only R28 pressed-drag monitor."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch

from env.metrics import PressedDragMonitor


def state(active=True, relation_move=False, stable=False, x=0.0,
          pressed=True, fret=4):
    mask = torch.zeros(1, 4, 6, dtype=torch.bool)
    frets = torch.zeros(1, 4, dtype=torch.long)
    relation = torch.zeros(1, 4, dtype=torch.bool)
    stable_press = torch.zeros(1, 4, dtype=torch.bool)
    tips = torch.zeros(1, 4, 2)
    cells = torch.zeros(1, 4, 6, 22, dtype=torch.bool)
    if active:
        mask[0, 0, 0] = True
        frets[0, 0] = fret
    relation[0, 0] = relation_move
    stable_press[0, 0] = stable
    tips[0, 0, 0] = x
    if pressed:
        cells[0, 0, 0, fret - 1] = True
    return mask, frets, relation, stable_press, tips, cells


def main():
    monitor = PressedDragMonitor(1, "cpu", threshold=0.003)
    monitor.update(*state(active=True, relation_move=True, stable=True,
                          x=0.000, pressed=True))
    first = monitor.update(*state(active=False, x=0.002, pressed=True))
    assert first["r28_move_started"][0, 0]
    assert first["r28_same_cell_drag"][0, 0]
    assert not first["r28_drag_violation_started"][0, 0]
    second = monitor.update(*state(active=False, x=0.004, pressed=True))
    assert second["r28_drag_violation_started"][0, 0]
    assert abs(float(second["r28_confirmed_cumulative_distance"][0, 0]) - 0.004) < 1e-7

    # A lifted finger can travel freely and is not a pressed-drag candidate.
    monitor.reset(torch.tensor([0]))
    monitor.update(*state(active=True, relation_move=True, stable=True,
                          x=0.000, pressed=True))
    lifted = monitor.update(*state(active=False, x=0.020, pressed=False))
    assert lifted["r28_move_started"][0, 0]
    assert not lifted["r28_pressed_endpoint_candidate"][0, 0]
    assert float(lifted["r28_confirmed_cumulative_distance"][0, 0]) == 0.0
    print("PASS: R28 confirmed drag and lifted MOVE separation")


if __name__ == "__main__":
    main()
