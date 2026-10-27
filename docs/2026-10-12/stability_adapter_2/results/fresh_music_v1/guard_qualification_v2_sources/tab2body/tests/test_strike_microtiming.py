from __future__ import annotations

from pathlib import Path
import sys

import torch


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from env.strike_events import (
    strike_balanced_practice_direction,
    strike_premature_release,
    strike_rational_timing_quality,
    strike_traversal_timing,
    strike_uniform_traversal_offsets,
)
from env.strike_goal_compiler import compile_strike_events


def main():
    env_ids = torch.arange(8, dtype=torch.long)
    generation = torch.ones(8, dtype=torch.long)
    balanced = strike_balanced_practice_direction(env_ids, generation)
    assert int((balanced == 1).sum()) == 4
    assert int((balanced == -1).sum()) == 4
    next_balanced = strike_balanced_practice_direction(
        env_ids, generation + 1)
    assert torch.equal(next_balanced, -balanced)

    practice_mask = torch.tensor([
        [False, False, True, True, True, True],
        [False, False, True, True, True, True],
    ])
    practice_offsets = strike_uniform_traversal_offsets(
        practice_mask,
        torch.tensor([1, -1]),
        torch.tensor([0.007, 0.007]))
    assert torch.equal(
        practice_offsets[0, practice_mask[0]],
        torch.flip(practice_offsets[1, practice_mask[1]], dims=(0,)))
    assert practice_offsets[0, 5] < practice_offsets[0, 2]
    assert practice_offsets[1, 2] < practice_offsets[1, 5]

    chained = [
        {"time": 0.00, "frame": 0, "string": 5},
        {"time": 0.04, "frame": 2, "string": 4},
        {"time": 0.08, "frame": 5, "string": 3},
    ]
    compiled = compile_strike_events(
        chained, fps=60, rearm_min_frames=2,
        follow_through_min_frames=1, initial_timing_tolerance_ms=100)
    assert len(compiled.events) == 2
    assert compiled.events[0].gesture == "strum"
    assert max(compiled.events[0].source_times_s) \
        - min(compiled.events[0].source_times_s) <= 0.050
    assert abs(compiled.events[0].time_s - 0.020) < 1e-12

    traversal = torch.tensor([[False, False, False, True, True, True]])
    offsets = torch.tensor([[0.0, 0.0, 0.0, 0.010, 0.000, -0.010]])
    release_times = torch.tensor([[0.0, 0.0, 0.0, 1.010, 1.000, 0.990]])
    valid = traversal.clone()
    exact = strike_traversal_timing(
        release_times, valid, traversal, torch.tensor([1.0]), offsets,
        torch.tensor([0.015]), torch.tensor([0.015]))
    assert exact["complete"].item()
    assert exact["timing_ok"].item()
    assert not exact["early"].item()
    assert not exact["late"].item()
    assert abs(exact["actual_duration_s"].item() - 0.020) < 1e-6
    assert abs(exact["duration_error_s"].item()) < 1e-6

    release_times[0, 3] += 0.020
    late = strike_traversal_timing(
        release_times, valid, traversal, torch.tensor([1.0]), offsets,
        torch.tensor([0.015]), torch.tensor([0.015]))
    assert not late["timing_ok"].item()
    assert not late["early"].item()
    assert late["late"].item()
    assert abs(late["worst_error_s"].item() - 0.020) < 1e-6
    assert abs(late["duration_error_s"].item() - 0.020) < 1e-6

    early_times = torch.tensor(
        [[0.0, 0.0, 0.0, 0.990, 0.960, 0.950]])
    early = strike_traversal_timing(
        early_times, valid, traversal, torch.tensor([1.0]), offsets,
        torch.tensor([0.015]), torch.tensor([0.015]))
    assert early["early"].item()
    assert not early["late"].item()

    premature = strike_premature_release(
        torch.tensor([[False, False, True, False, False, False]]),
        torch.tensor([[0.0, 0.0, 0.55, 0.0, 0.0, 0.0]]),
        torch.tensor([1.0]),
        torch.zeros(1, 6),
        torch.tensor([0.40]))
    assert premature["premature"].item()
    boundary = strike_premature_release(
        torch.tensor([[False, False, True, False, False, False]]),
        torch.tensor([[0.0, 0.0, 0.60, 0.0, 0.0, 0.0]]),
        torch.tensor([1.0]),
        torch.zeros(1, 6),
        torch.tensor([0.40]))
    assert not boundary["premature"].item()
    quality = strike_rational_timing_quality(
        torch.tensor([0.0, 0.30, 0.60]), 0.30)
    assert torch.allclose(quality, torch.tensor([1.0, 0.5, 0.2]))

    print("PASS: bounded grouping and direction-aligned strum microtiming")


if __name__ == "__main__":
    main()
