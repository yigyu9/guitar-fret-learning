"""CPU regression for S3 event advance versus physical follow-through."""
from __future__ import annotations

from pathlib import Path
import sys


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PACKAGE_ROOT.parent
for path in (str(PACKAGE_ROOT), str(PROJECT_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

import torch

from env.strike_events import (
    strike_song_continuing_phase,
    strike_completed_recovery_frames,
    strike_motion_target_context,
    strike_recovery_to_approach,
)


def main():
    phase_release = 2
    phase_approach = 1
    context = strike_motion_target_context(
        torch.tensor([4, 4, 2], dtype=torch.long),
        torch.tensor([-0.30, -0.31, -0.32]),
        torch.tensor([-1, -1, -1], dtype=torch.long),
        torch.tensor([1, 3, 5], dtype=torch.long),
        torch.tensor([-0.34, -0.35, -0.36]),
        torch.tensor([-1, 1, -1], dtype=torch.long),
        torch.tensor([True, False, True]),
        torch.tensor([phase_release, phase_release, phase_approach]),
        release_recover_phase=phase_release,
    )



    assert torch.equal(
        context["target_string"], torch.tensor([1, 4, 2]))
    assert torch.allclose(
        context["target_lane_y"], torch.tensor([-0.34, -0.31, -0.32]))
    assert torch.equal(
        context["target_direction"], torch.tensor([-1, -1, -1]))

    phase_advance = strike_song_continuing_phase(
        torch.tensor([0, 1, 2, 1], dtype=torch.long),
        torch.tensor([False, False, False, True]),
        torch.tensor([False, False, True, True]),
        release_recover_phase=phase_release,
    )
    assert torch.equal(
        phase_advance["motor_phase"],
        torch.tensor([0, 1, 2, 2], dtype=torch.long))
    assert torch.equal(
        phase_advance["preserve_recovery"],
        torch.tensor([False, False, True, True]))

    resolved = torch.zeros(3, dtype=torch.bool)




    hit_frame_count = strike_completed_recovery_frames(
        torch.tensor([phase_approach]),
        torch.tensor([0], dtype=torch.long),
        release_recover_phase=phase_release,
    )
    assert hit_frame_count.item() == 0
    first_recovery_count = strike_completed_recovery_frames(
        torch.tensor([phase_release]),
        hit_frame_count,
        release_recover_phase=phase_release,
    )
    assert first_recovery_count.item() == 1

    transition = strike_recovery_to_approach(
        torch.tensor([phase_release, phase_release, phase_approach]),
        resolved,
        torch.tensor([0, 1, 2], dtype=torch.long),
        torch.tensor([True, True, True]),
        torch.tensor([0.10, 0.10, 0.10]),
        release_recover_phase=phase_release,
        minimum_follow_through_frames=1,
        approach_lead_s=0.20,
    )
    assert torch.equal(transition, torch.tensor([False, True, False]))

    resolved[1] = True
    assert not strike_recovery_to_approach(
        torch.tensor([phase_release, phase_release, phase_approach]),
        resolved,
        torch.tensor([0, 1, 2], dtype=torch.long),
        torch.tensor([True, True, True]),
        torch.tensor([0.10, 0.10, 0.10]),
        release_recover_phase=phase_release,
        minimum_follow_through_frames=1,
        approach_lead_s=0.20,
    )[1]

    assert not strike_recovery_to_approach(
        torch.tensor([phase_release]),
        torch.tensor([False]),
        torch.tensor([1], dtype=torch.long),
        torch.tensor([False]),
        torch.tensor([0.10]),
        release_recover_phase=phase_release,
        minimum_follow_through_frames=1,
        approach_lead_s=0.20,
    )[0]

    print("PASS: S3 recovery preserves the released string/lane before approach")


if __name__ == "__main__":
    main()
