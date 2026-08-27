"""CPU boundary and three-frame termination checks for R7 and R8."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch

from env.safety import (FingerBackLimitMonitor, WristSafetyBoxMonitor,
                        exclude_thumb_from_generic_penetration,
                        finger_back_limit_violation, wrist_box_violation)


class FakeEnv:
    def __init__(self):
        self.num_envs = 1
        self.device = "cpu"
        names = ["L_Wrist"]
        for finger in FingerBackLimitMonitor.FINGERS:
            names += ([f"LH:{finger}{i}" for i in range(1, 4)]
                      + [f"LH:{finger}_top"])
        self.hbody_index = {name: i for i, name in enumerate(names)}
        self.positions = {name: torch.zeros(1, 3) for name in names}

    def hbody_pos(self, name):
        return self.positions[name]

    def to_guitar_frame(self, points):
        return points


def main():
    inside = torch.tensor([[0.0, 0.0, 0.0], [0.30, 0.35, 0.25]])
    by_axis, violation = wrist_box_violation(
        inside, (-0.20, -0.35, -0.30), (0.30, 0.35, 0.25))
    assert not by_axis.any() and not violation.any()  # boundary equality is safe
    _, outside = wrist_box_violation(
        torch.tensor([[0.301, 0.0, 0.0]]),
        (-0.20, -0.35, -0.30), (0.30, 0.35, 0.25))
    assert outside.item()

    samples = torch.zeros(1, 4, 3, 5, 3)
    by_finger, any_back, fraction = finger_back_limit_violation(samples, -0.050)
    assert not by_finger.any() and not any_back.any()
    samples[0, 2, 0, :, 2] = -0.051
    by_finger, any_back, fraction = finger_back_limit_violation(samples, -0.050)
    assert by_finger[0, 2] and any_back[0]
    assert fraction[0, 2] >= 0.25

    env = FakeEnv()
    wrist = WristSafetyBoxMonitor(env, frames=3)
    env.positions["L_Wrist"][0, 0] = 0.31
    assert not wrist.compute()["wrist_safety_termination"].item()
    assert not wrist.compute()["wrist_safety_termination"].item()
    assert wrist.compute()["wrist_safety_termination"].item()
    env.positions["L_Wrist"].zero_()
    assert not wrist.compute()["wrist_safety_termination"].item()

    back = FingerBackLimitMonitor(env, limit_z=-0.050, frames=3,
                                  samples_per_segment=5)
    for name in back.chains[0]:
        env.positions[name][0, 2] = -0.051
    assert not back.compute()["finger_back_termination"].item()
    assert not back.compute()["finger_back_termination"].item()
    result = back.compute()
    assert result["finger_back_termination"].item()
    assert result["finger_back_violation_by_finger"][0, 0]
    assert result["finger_back_soft_penalty"].item() > 0.0

    layered = FingerBackLimitMonitor(
        env, limit_z=-0.025, proximal_limit_z=-0.035,
        soft_limit_z=-0.012, frames=1, samples_per_segment=5)
    for name in {name for chain in layered.chains for name in chain}:
        env.positions[name].zero_()
    env.positions["LH:index3"][0, 2] = -0.026
    env.positions["LH:index_top"][0, 2] = -0.026
    layered_result = layered.compute()
    assert layered_result["finger_back_termination"].item()
    assert layered_result["finger_back_distal_fraction_by_finger"][0, 0] >= 0.25

    # Three different fingers violating once each are not one persistent breach.
    back.reset(torch.tensor([0]))
    for name in {name for chain in back.chains for name in chain}:
        env.positions[name].zero_()
    for finger in range(3):
        for name in back.chains[finger]:
            env.positions[name][0, 2] = -0.051
        assert not back.compute()["finger_back_termination"].item()
        for name in back.chains[finger]:
            env.positions[name].zero_()
    assert back.streak.max().item() <= 1

    depth = torch.tensor([
        [0.0, 0.006, 0.0],
        [0.0, 0.006, 0.0],
        [0.0, 0.006, 0.007],
    ])
    tunneled = torch.zeros_like(depth, dtype=torch.bool)
    termination = depth > 0.005
    filtered = exclude_thumb_from_generic_penetration(
        depth, tunneled, termination, penetration_threshold=0.005)
    assert filtered["raw_thumb_unsafe"].tolist() == [True, True, True]
    assert not filtered["termination"][0]
    assert not filtered["termination"][1]
    assert filtered["termination"][2]
    print("PASS: R7/R8 bounds, sampling, debounce, and termination")


if __name__ == "__main__":
    main()
