"""CPU checks for stage-masked strike reward semantics."""
from __future__ import annotations

from pathlib import Path
import sys

import torch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env.rewards.strike import STAGES, StrikeReward  # noqa: E402


def build_reward():
    return StrikeReward({
        "grip_weight": {
            "A0_PICK_GRIP": 1.0,
            "A1_TIP_READY": 0.05,
            "A2_FREE_CROSSING": 0.005,
            "A3_TIMED_CROSSING": 0.003,
            "A4_ZONE_CONTROL": 0.003,
        },
        "reach_weight": 0.2,
        "ready_quality_weight": 0.75,
        "crossing_reward": 1.0,
        "completion_reward": 0.15,
        "wrong_crossing_penalty": 0.35,
        "miss_penalty": 0.5,
        "zone_weight": 0.2,
        "timing_core_ms": 20.0,
    })


def compute(reward, stage, **overrides):
    values = {
        "grip_quality": torch.tensor([1.0, 0.5]),
        "reach_progress": torch.tensor([0.25, -0.25]),
        "ready_quality": torch.tensor([0.8, 0.2]),
        "ready_pulse": torch.tensor([True, False]),
        "target_hit": torch.tensor([True, False]),
        "wrong_crossing_count": torch.tensor([0.0, 1.0]),
        "miss_pulse": torch.tensor([False, True]),
        "timing_error_s": torch.tensor([0.0, 0.1]),
        "zone_quality": torch.tensor([0.75, 0.0]),
        "zone_attempt": torch.tensor([True, False]),
    }
    values.update(overrides)
    return reward.compute(stage, **values)


def main():
    reward = build_reward()

    a0, terms = compute(reward, STAGES[0])
    assert a0.shape == (2, 1)
    assert torch.allclose(a0[:, 0], torch.tensor([1.0, 0.5]))
    assert not terms["reward_reach_progress"].any()
    assert not terms["reward_crossing"].any()
    assert not terms["penalty_wrong_crossing"].any()

    a1, terms = compute(reward, STAGES[1])
    expected_first = 0.75 * 0.8 + 0.2 * 0.25 + 0.15
    assert torch.isclose(a1[0, 0], torch.tensor(expected_first))
    assert terms["reward_ready_quality"][0] > 0
    assert terms["penalty_wrong_crossing"][1] < 0
    assert not terms["reward_crossing"].any()
    assert terms["penalty_miss"][1] == -0.5

    # With A1's fixed 180-frame horizon, reaching the target and latching once
    # must dominate deliberately staying just outside the 10 mm boundary.
    outside_distance = 0.010001
    outside_quality = (
        0.4 * torch.exp(torch.tensor(-(outside_distance / 0.120) ** 2))
        + 0.6 * torch.exp(torch.tensor(-(outside_distance / 0.025) ** 2)))
    common = {
        "grip_quality": torch.ones(2),
        "reach_progress": torch.zeros(2),
        "ready_quality": torch.tensor([1.0, outside_quality]),
        "ready_pulse": torch.zeros(2, dtype=torch.bool),
        "target_hit": torch.zeros(2, dtype=torch.bool),
        "wrong_crossing_count": torch.zeros(2),
        "miss_pulse": torch.zeros(2, dtype=torch.bool),
        "timing_error_s": torch.zeros(2),
        "zone_quality": torch.zeros(2),
        "zone_attempt": torch.zeros(2, dtype=torch.bool),
    }
    base, _ = reward.compute(STAGES[1], **common)
    pulse_values = dict(common)
    pulse_values["ready_pulse"] = torch.tensor([True, False])
    pulse, _ = reward.compute(STAGES[1], **pulse_values)
    timeout_values = dict(common)
    timeout_values["miss_pulse"] = torch.tensor([False, True])
    timeout, _ = reward.compute(STAGES[1], **timeout_values)
    gamma = 0.95
    target_return = sum(
        gamma ** frame * float(
            pulse[0, 0] if frame == 5 else base[0, 0])
        for frame in range(180))
    outside_return = sum(
        gamma ** frame * float(
            timeout[1, 0] if frame == 179 else base[1, 0])
        for frame in range(180))
    assert target_return > outside_return

    a2, terms = compute(reward, STAGES[2])
    assert terms["reward_crossing"][0] == 1.0
    assert terms["penalty_miss"][1] == -0.5
    assert not terms["reward_timing"].any()
    assert not terms["reward_zone"].any()

    _a3, terms = compute(reward, STAGES[3])
    assert terms["reward_timing"][0] > 0
    assert not terms["reward_zone"].any()

    _a4, terms = compute(reward, STAGES[4])
    assert torch.isclose(terms["reward_zone"][0], torch.tensor(0.15))
    assert terms["reward_timing"][0] > 0

    # Later-stage grip shaping is zero at the reference and negative away
    # from it, so an idle posture cannot accumulate a positive baseline.
    _, terms = compute(reward, STAGES[4])
    assert terms["reward_grip"][0] == 0.0
    assert terms["reward_grip"][1] < 0.0
    print("PASS: A0-A4 strike reward terms are stage-masked")


if __name__ == "__main__":
    main()
