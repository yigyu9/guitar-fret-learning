"""CPU check for fixed-song phase context in the fret goal observation."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch

from env.goals import FretGoalSequence


def main():
    frames = []
    for frame in range(3):
        frames.append({
            "frame": frame,
            "t": frame / 60.0,
            "fret_goal": [0, 0, 0, 0, 0, 0],
            "finger_goal": [0, 0, 0, 0, 0, 0],
            "barre_goal": [False] * 6,
            "hand_anchor_fret": 1.0,
            "hand_allowed_fret_range": [1, 6],
        })
    payload = {
        "schema": "tab2body.fret_training.v1",
        "metadata": {"fps": 60},
        "frames": frames,
    }
    with tempfile.TemporaryDirectory(prefix="song_phase_", dir="/tmp") as tmp:
        path = Path(tmp) / "tiny.fret_training.json"
        path.write_text(json.dumps(payload))
        goals = FretGoalSequence(path, num_envs=2, device="cpu")
        assert goals.goal_dim == 128
        obs = goals.observe()
        assert obs.shape == (2, 128)
        assert torch.equal(obs[:, -1], torch.zeros(2))
        goals.frame_idx[:] = torch.tensor([1, 2])
        phase = goals.observe()[:, -1]
        assert torch.allclose(phase, torch.tensor([0.5, 1.0]))
        goals.frame_idx.zero_()
        delayed = goals.observe(torch.tensor([60, 0]))
        # Each 25-D lookahead slot ends in physical time-to-slot.  Preparation
        # freezes the song clock, so env 0 sees one additional second.
        assert torch.allclose(delayed[:, 24], torch.tensor([1.0, 0.0]))
        assert torch.allclose(delayed[:, 49], torch.tensor([1.1, 0.1]))
        assert torch.allclose(delayed[:, 74], torch.tensor([1.25, 0.25]))
    print("PASS: fixed-song phase context is normalized and observable")


if __name__ == "__main__":
    main()
