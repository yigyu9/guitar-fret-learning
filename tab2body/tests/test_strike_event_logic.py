"""CPU contracts for ready, timing and release-aware completion."""
from __future__ import annotations

from pathlib import Path
import sys

import torch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env.strike_events import (
    strike_false_positive_count,
    strike_physical_target_candidate,
    strike_release_recovery_context,
    strike_recovery_incomplete_timeout,
    strike_ready_episode_resolution,
    strike_ready_latch,
    strike_resolved_episode_done,
    strike_timing_gate,
    strike_ordered_release_progress,
)


def main():
    previous = torch.zeros(4, 6, dtype=torch.bool)
    release = torch.zeros_like(previous)
    release[0, [5, 4, 3]] = True
    release[1, [5, 3]] = True
    release[2, [3, 4]] = True
    release[3, [5, 4]] = True
    subframe = torch.zeros(4, 6)
    subframe[0, [5, 4, 3]] = torch.tensor([0.1, 0.2, 0.3])
    subframe[1, [5, 3]] = torch.tensor([0.1, 0.2])
    subframe[2, [3, 4]] = torch.tensor([0.1, 0.2])
    subframe[3, [5, 4]] = torch.tensor([0.1, 0.2])
    directions = torch.ones(4, 6, dtype=torch.int8)
    directions[3, 4] = -1
    traversal = torch.zeros_like(previous)
    traversal[:, 3:6] = True
    ordered = strike_ordered_release_progress(
        previous, release, subframe, directions, traversal,
        torch.ones(4, dtype=torch.int8))
    assert ordered["complete"].tolist() == [True, False, False, False]
    assert ordered["order_violation_count"].tolist() == [0, 1, 2, 0]
    assert ordered["wrong_direction_count"].tolist() == [0, 0, 0, 1]
    assert ordered["accumulated_release"][1, 5]
    assert not ordered["accumulated_release"][1, 3]

    streak = torch.zeros(1, dtype=torch.long)
    success = torch.zeros(1, dtype=torch.bool)
    pulses = []
    for _ in range(6):
        ready = strike_ready_latch(
            torch.ones(1, dtype=torch.bool),
            torch.ones(1, dtype=torch.bool),
            streak,
            success,
            hold_frames=6,
        )
        streak = ready["ready_streak"]
        success = ready["ready_success"]
        pulses.append(bool(ready["ready_pulse"].item()))
    assert pulses == [False, False, False, False, False, True]
    assert success.item()



    ready = strike_ready_latch(
        torch.zeros(1, dtype=torch.bool),
        torch.ones(1, dtype=torch.bool),
        streak,
        success,
        hold_frames=6,
    )
    streak = ready["ready_streak"]
    for _ in range(6):
        ready = strike_ready_latch(
            torch.ones(1, dtype=torch.bool),
            torch.ones(1, dtype=torch.bool),
            streak,
            success,
            hold_frames=6,
        )
        streak = ready["ready_streak"]
        assert not ready["ready_pulse"].item()

    a1 = strike_ready_episode_resolution(
        torch.tensor([False, True, True]),
        torch.tensor([True, True, False]),
    )
    assert torch.equal(a1["done"], torch.tensor([False, True, True]))
    assert torch.equal(a1["success"], torch.tensor([False, True, False]))
    assert torch.equal(a1["miss"], torch.tensor([False, False, True]))

    physical = torch.tensor([True, True, False])
    timing_ok = torch.tensor([True, False, True])
    timed = strike_timing_gate(
        physical, timing_ok, timing_required=True)
    assert torch.equal(
        timed["timing_sample"], torch.tensor([True, True, False]))
    assert torch.equal(
        timed["success_candidate"], torch.tensor([True, False, False]))
    assert (timed["timing_sample"].data_ptr()
            != timed["success_candidate"].data_ptr())

    untimed = strike_timing_gate(
        physical, timing_ok, timing_required=False)
    assert not untimed["timing_sample"].any()
    assert torch.equal(untimed["success_candidate"], physical)

    matcher_candidate = strike_physical_target_candidate(
        torch.tensor([True, True, True, True]),
        torch.tensor([False, False, True, False]),
        torch.tensor([False, False, False, True]),
    )
    assert torch.equal(
        matcher_candidate, torch.tensor([True, True, False, False]))

    false_positives = strike_false_positive_count(
        torch.tensor([
            [True, False, False],
            [True, True, False],
            [False, False, False],
        ]),
        torch.tensor([True, True, False]),
        torch.tensor([
            [False, False, False],
            [False, False, True],
            [True, False, True],
        ]),
    )
    assert torch.equal(false_positives, torch.tensor([0.0, 2.0, 2.0]))

    recovery_context = strike_release_recovery_context(
        torch.tensor([
            [True, False, True],
            [False, False, False],
        ]),
        torch.tensor([
            [0.2, 0.0, 0.8],
            [0.0, 0.0, 0.0],
        ]),
        torch.tensor([
            [[0.0, -0.30, 0.0], [0.0, 0.0, 0.0],
             [0.0, -0.35, 0.0]],
            [[0.0, 0.0, 0.0]] * 3,
        ]),
        torch.tensor([
            [1, 0, -1],
            [0, 0, 0],
        ], dtype=torch.int8),
    )
    assert torch.equal(
        recovery_context["released"], torch.tensor([True, False]))
    assert torch.equal(
        recovery_context["release_string"], torch.tensor([2, 0]))
    assert torch.allclose(
        recovery_context["release_lane_y"], torch.tensor([-0.35, 0.0]))
    assert torch.equal(
        recovery_context["release_direction"], torch.tensor([-1, 1]))

    recovery_timeout = strike_recovery_incomplete_timeout(
        torch.tensor([True, True, True, False]),
        torch.tensor([True, True, True, True]),
        torch.tensor([11, 12, 12, 0], dtype=torch.long),
        torch.tensor([True, False, True, False]),
        recovery_frames=12,
    )
    assert torch.equal(
        recovery_timeout, torch.tensor([True, True, False, False]))





    resolved = torch.tensor([True, True, True, False])
    phase = torch.tensor([1, 2, 2, 1], dtype=torch.long)
    recovery = torch.tensor([0, 11, 12, 0], dtype=torch.long)
    timeout = torch.tensor([False, False, False, True])
    result = strike_resolved_episode_done(
        resolved,
        phase,
        recovery,
        torch.tensor([True, True, True, True]),
        timeout,
        release_recover_phase=2,
        recovery_frames=12,
    )
    assert torch.equal(
        result["recovery_finished"],
        torch.tensor([True, False, True, True]))
    assert torch.equal(
        result["done"],
        torch.tensor([True, False, True, True]))
    not_rearmed = strike_resolved_episode_done(
        torch.tensor([True]),
        torch.tensor([2], dtype=torch.long),
        torch.tensor([12], dtype=torch.long),
        torch.tensor([False]),
        torch.tensor([False]),
        release_recover_phase=2,
        recovery_frames=12,
    )
    assert not not_rearmed["recovery_finished"].item()
    assert not not_rearmed["done"].item()

    print("PASS: fixed-horizon ready, uncensored timing and release recovery")


if __name__ == "__main__":
    main()
