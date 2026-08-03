"""CPU contracts for ready, timing and release-aware completion."""
from __future__ import annotations

from pathlib import Path
import sys

import torch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env.strike_events import (  # noqa: E402
    strike_ready_episode_resolution,
    strike_ready_latch,
    strike_resolved_episode_done,
    strike_timing_gate,
)


def main():
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

    # Leaving and completing another hold cannot collect another completion
    # pulse within the same fixed-length A1 episode.
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

    # Row 0: miss/approach -> finish immediately.
    # Row 1: real hit at recovery frame 11 -> keep running.
    # Row 2: real hit at recovery frame 12 -> finish.
    # Row 3: unresolved A2 event reaches its horizon -> finish by timeout.
    resolved = torch.tensor([True, True, True, False])
    phase = torch.tensor([1, 2, 2, 1], dtype=torch.long)
    recovery = torch.tensor([0, 11, 12, 0], dtype=torch.long)
    timeout = torch.tensor([False, False, False, True])
    result = strike_resolved_episode_done(
        resolved,
        phase,
        recovery,
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

    print("PASS: fixed-horizon ready, uncensored timing and release recovery")


if __name__ == "__main__":
    main()
