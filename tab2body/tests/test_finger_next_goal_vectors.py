"""CPU checks for the per-finger 13-D R15 next-goal observation."""
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env.goals import build_finger_next_goal_vectors


def main():
    def empty_frame():
        return {"fret_goal": [0] * 6, "finger_goal": [0] * 6,
                "barre_goal": [False] * 6}

    frames = [empty_frame() for _ in range(9)]
    # Finger 1: single -> explicit barre -> reduced mask -> gap -> re-press.
    for t in (1, 2):
        frames[t]["fret_goal"][0] = 3
        frames[t]["finger_goal"][0] = 1
    for string in (0, 1):
        frames[3]["fret_goal"][string] = 3
        frames[3]["finger_goal"][string] = 1
        frames[3]["barre_goal"][string] = True
    frames[4]["fret_goal"][1] = 3
    frames[4]["finger_goal"][1] = 1
    for t in (6, 7):
        frames[t]["fret_goal"][1] = 3
        frames[t]["finger_goal"][1] = 1
    # Finger 2 moves directly to a different target.
    for t in (1, 2):
        frames[t]["fret_goal"][2] = 5
        frames[t]["finger_goal"][2] = 2
    for t in (3, 4):
        frames[t]["fret_goal"][4] = 7
        frames[t]["finger_goal"][4] = 2

    vectors, metadata = build_finger_next_goal_vectors(
        frames, fps=10, allow_barre=True)
    assert vectors.shape == (9, 4, 13)
    assert np.all((vectors[:, :, :6] == 0) | (vectors[:, :, :6] == 1))
    assert np.allclose(vectors[:, :, 10:13].sum(axis=-1), 1.0)
    assert metadata["contract_valid"]
    assert metadata["multistring_finger_frames"] == 1
    assert metadata["explicit_barre_finger_frames"] == 1

    # Before the first target: one-hot string mask, fret, 0.1 s, MOVE.
    assert np.allclose(vectors[0, 0, :6], [1, 0, 0, 0, 0, 0])
    assert np.allclose(vectors[0, 0, 6:10], [3 / 22, .1, 1, 0])
    assert np.allclose(vectors[0, 0, 10:13], [0, 1, 0])
    # Mask expansion/reduction retains contact at the same fret: KEEP.
    assert np.allclose(vectors[1, 0, :6], [1, 1, 0, 0, 0, 0])
    assert np.allclose(vectors[1, 0, 7:10], [.2, 1, .2])
    assert np.allclose(vectors[1, 0, 10:13], [1, 0, 0])
    assert np.allclose(vectors[3, 0, :6], [0, 1, 0, 0, 0, 0])
    assert np.allclose(vectors[3, 0, 10:13], [1, 0, 0])
    # A release gap makes the later identical target MOVE, not KEEP.
    assert np.allclose(vectors[4, 0, 7:10], [.2, 1, .1])
    assert np.allclose(vectors[4, 0, 10:13], [0, 1, 0])
    # No later active target means REST while current-change time remains valid.
    assert np.allclose(vectors[6, 0, 10:13], [0, 0, 1])
    assert np.isclose(vectors[6, 0, 9], .2)
    # Direct different-fret transition is MOVE.
    assert np.allclose(vectors[1, 1, :6], [0, 0, 0, 0, 1, 0])
    assert np.allclose(vectors[1, 1, 10:13], [0, 1, 0])

    invalid = [empty_frame()]
    invalid[0]["fret_goal"][:2] = [3, 4]
    invalid[0]["finger_goal"][:2] = [1, 1]
    try:
        build_finger_next_goal_vectors(invalid, fps=60, allow_barre=True)
    except ValueError as exc:
        assert "one fret" in str(exc)
    else:
        raise AssertionError("simultaneous multi-fret target was not rejected")

    implicit = [empty_frame()]
    implicit[0]["fret_goal"][:2] = [3, 3]
    implicit[0]["finger_goal"][:2] = [1, 1]
    try:
        build_finger_next_goal_vectors(implicit, fps=60)
    except ValueError as exc:
        assert "allow_barre=False" in str(exc)
    else:
        raise AssertionError("implicit multi-string target was not rejected in S0")
    print("PASS: per-frame 13-D mask/fret/timing/valid/change/KEEP-MOVE-REST")


if __name__ == "__main__":
    main()
