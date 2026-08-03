"""CPU checks for R5 PRESS/NO_PRESS/DONT_CARE frame transitions."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_fret_training_data import (build_hand_position_targets, fret_y_at,
                                            rasterize, release_windows)


def event(fret, t_press, t_release, string=0, finger=1):
    return {"fret": fret, "t_press": t_press, "t_release": t_release,
            "string": string, "finger": finger, "barre": False}


def goal_at(frames, t, string=0):
    frame = round(t * 60)
    return frames[frame]["fret_goal"][5 - string]


def main():
    # Different-fret movement: release gap is NP; next lower target makes the old
    # higher fret forbidden through the runtime highest-fret mask.
    moving = [event(6, 0.0, 0.5), event(4, 0.7, 1.0)]
    windows = release_windows(moving)
    assert len(windows) == 1 and windows[0]["released_fret"] == 6
    frames = rasterize([], moving, [], 1.1)
    assert goal_at(frames, 0.4) == 6
    assert goal_at(frames, 0.6) == -1
    assert goal_at(frames, 0.8) == 4
    assert goal_at(frames, 1.05) == 0  # no future event: DONT_CARE

    # A same-position retrigger already merged upstream has no release boundary.
    merged = [event(4, 0.0, 1.0)]
    assert release_windows(merged) == []
    frames = rasterize([], merged, [], 1.1)
    assert goal_at(frames, 0.6) == 4

    # Overlapping preparation has no NP gap; the later active event wins.
    overlap = [event(6, 0.0, 0.8), event(4, 0.7, 1.0)]
    assert release_windows(overlap) == []
    frames = rasterize([], overlap, [], 1.1)
    assert goal_at(frames, 0.75) == 4

    # Every song gets wrist targets from its own anchor timeline and actual fret y.
    hand = build_hand_position_targets(frames)
    assert hand["schema"] == "tab2body.hand_position_targets.v1"
    assert len(hand["frames"]) == len(frames)
    assert abs(fret_y_at(4.0) - 0.088313) < 1e-9
    assert fret_y_at(4.5) == (fret_y_at(4.0) + fret_y_at(5.0)) / 2.0
    assert hand["frames"][0]["allowed_radius_m"] == 0.04

    print("PASS: R5 goal timeline and per-song wrist target generation")


if __name__ == "__main__":
    main()
