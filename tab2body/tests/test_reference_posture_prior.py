import json
import math
import tempfile
from pathlib import Path
import sys

import torch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tab2body.env.rewards.reference_posture import (
    ReferenceHandPosturePrior,
    load_reference_postures,
)


def _quat(axis, degrees):
    angle = math.radians(degrees) / 2.0
    value = [0.0, 0.0, 0.0, math.cos(angle)]
    value[axis] = math.sin(angle)
    return value


def _frame(offset):
    frame = {}
    for finger in ("index", "middle", "ring", "pinky"):
        for joint in (1, 2, 3):
            frame[f"LH:{finger}{joint}"] = _quat(0, offset)
    frame["LH:thumb1"] = _quat(2, offset)
    frame["LH:thumb2"] = _quat(2, offset)
    frame["LH:thumb3"] = _quat(2, offset)
    return frame


class _Env:
    def __init__(self):
        self.num_envs = 2
        self.device = torch.device("cpu")
        self.dof_names = []
        for finger in ("index", "middle", "ring", "pinky"):
            self.dof_names.extend((
                f"LH:{finger}1_x", f"LH:{finger}2", f"LH:{finger}3"))
        self.dof_names.extend((
            "LH:thumb1_x", "LH:thumb1_y", "LH:thumb1_z",
            "LH:thumb2", "LH:thumb3"))
        self.n_dof = len(self.dof_names)
        self.dof_state = torch.zeros(self.num_envs * self.n_dof, 2)


def main():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "motion.json"
        path.write_text(json.dumps({
            "fps": 120,
            "frames": [_frame(0.0), _frame(20.0), _frame(40.0)],
        }))
        finger, thumb = load_reference_postures(path, max_exemplars=3)
        assert finger.shape == (3, 4, 3)
        assert thumb.shape == (3, 5)

        env = _Env()
        prior = ReferenceHandPosturePrior(env, path, max_exemplars=3)
        active = torch.zeros(2, 4, dtype=torch.bool)
        finger_quality, thumb_quality = prior.compute(active)
        assert torch.allclose(finger_quality, torch.ones(2), atol=1e-6)
        assert torch.allclose(thumb_quality, torch.ones(2), atol=1e-6)

        state = env.dof_state.view(env.num_envs, env.n_dof, 2)
        state[0, :3, 0] = math.radians(90.0)
        degraded, _ = prior.compute(active)
        assert degraded[0] < degraded[1]
        active[0, 0] = True
        protected, _ = prior.compute(active)
        assert protected[0] > degraded[0]
    print("PASS: reference posture prior")


if __name__ == "__main__":
    main()
