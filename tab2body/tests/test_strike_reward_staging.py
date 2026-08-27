"""CPU checks for stage-masked strike reward semantics."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile

import torch


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tab2body.env.rewards.strike import (
    PickGripReference,
    STAGES,
    StrikeReward,
    strike_reach_potential_delta,
)


def reward_config():
    return {
        "grip_weight": {
            "A0_PICK_GRIP": 1.0,
            "A1_TIP_READY": 0.05,
            "A2_FREE_CROSSING": 0.005,
            "A3_TIMED_CROSSING": 0.003,
            "A4_ZONE_CONTROL": 0.003,
        },
        "reach_weight": 0.2,
        "reach_discount": 0.95,
        "ready_quality_weight": {
            "A0_PICK_GRIP": 0.0,
            "A1_TIP_READY": 0.75,
            "A2_FREE_CROSSING": 0.05,
            "A3_TIMED_CROSSING": 0.03,
            "A4_ZONE_CONTROL": 0.02,
        },
        "crossing_reward": 1.0,
        "completion_reward": {
            "A0_PICK_GRIP": 0.0,
            "A1_TIP_READY": 0.15,
            "A2_FREE_CROSSING": 0.50,
            "A3_TIMED_CROSSING": 0.35,
            "A4_ZONE_CONTROL": 0.25,
        },
        "wrong_crossing_penalty": 0.35,
        "unprepared_crossing_penalty": 1.0,
        "miss_penalty": 0.5,
        "zone_weight": 0.2,
        "timing_core_ms": 20.0,
    }


def build_reward():
    return StrikeReward(reward_config())


def expect_error(fragment, callback):
    try:
        callback()
    except ValueError as exc:
        assert fragment in str(exc), str(exc)
    else:
        raise AssertionError(f"expected ValueError containing {fragment!r}")


def build_grip_reference(document):
    dof_names = tuple(document["joint_targets_rad"])
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "pick-grip.json"
        path.write_text(json.dumps(document), encoding="utf-8")
        return PickGripReference(path, dof_names, "cpu")


def compute(reward, stage, **overrides):
    values = {
        "grip_quality": torch.tensor([1.0, 0.5]),
        "reach_progress": torch.tensor([0.25, -0.25]),
        "ready_quality": torch.tensor([0.8, 0.2]),
        "ready_pulse": torch.tensor([True, False]),
        "ready_acquired": torch.tensor([True, False]),
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

    gamma = reward.reach_discount
    first = strike_reach_potential_delta(
        torch.tensor([0.2]), torch.tensor([0.9]),
        torch.tensor([True]), discount=gamma)
    second = strike_reach_potential_delta(
        torch.tensor([0.9]), torch.tensor([0.2]),
        torch.tensor([True]), discount=gamma)
    discounted_cycle = first + gamma * second
    legacy_cycle = (0.9 - 0.2) + gamma * (0.2 - 0.9)
    assert discounted_cycle.item() < 0.0 < legacy_cycle

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



    outside_distance = 0.010001
    outside_quality = (
        0.4 * torch.exp(torch.tensor(-(outside_distance / 0.120) ** 2))
        + 0.6 * torch.exp(torch.tensor(-(outside_distance / 0.025) ** 2)))
    common = {
        "grip_quality": torch.ones(2),
        "reach_progress": torch.zeros(2),
        "ready_quality": torch.tensor([1.0, outside_quality]),
        "ready_pulse": torch.zeros(2, dtype=torch.bool),
        "ready_acquired": torch.zeros(2, dtype=torch.bool),
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
    gamma = reward.reach_discount
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
    assert terms["reward_ready"][0] == 0.5
    assert terms["reward_ready_quality"][1] < 0.0
    assert terms["penalty_miss"][1] == -0.5
    assert not terms["reward_timing"].any()
    assert not terms["reward_zone"].any()

    unprepared, terms = compute(
        reward, STAGES[2],
        ready_pulse=torch.zeros(2, dtype=torch.bool),
        ready_acquired=torch.zeros(2, dtype=torch.bool))
    assert terms["reward_crossing"][0] == 0.0
    assert terms["penalty_unprepared_crossing"][0] == -1.0
    assert unprepared[0, 0] < 0.0

    _a3, terms = compute(reward, STAGES[3])
    assert terms["reward_timing"][0] > 0
    assert not terms["reward_zone"].any()

    _a4, terms = compute(reward, STAGES[4])
    assert torch.isclose(terms["reward_zone"][0], torch.tensor(0.15))
    assert terms["reward_timing"][0] > 0



    _, terms = compute(reward, STAGES[4])
    assert terms["reward_grip"][0] == 0.0
    assert terms["reward_grip"][1] < 0.0

    bad = reward_config()
    del bad["ready_quality_weight"]
    expect_error("missing=ready_quality_weight", lambda: StrikeReward(bad))
    bad = reward_config()
    bad["obsolete_weight"] = 1.0
    expect_error("unknown=obsolete_weight", lambda: StrikeReward(bad))
    bad = reward_config()
    bad["grip_weight"][STAGES[0]] = float("nan")
    expect_error("finite number", lambda: StrikeReward(bad))
    bad = reward_config()
    bad["grip_weight"][STAGES[0]] = -0.01
    expect_error("non-negative", lambda: StrikeReward(bad))
    bad = reward_config()
    bad["wrong_crossing_penalty"] = -0.01
    expect_error("non-negative", lambda: StrikeReward(bad))
    bad = reward_config()
    bad["timing_core_ms"] = 0.0
    expect_error("positive", lambda: StrikeReward(bad))
    bad = reward_config()
    bad["reach_discount"] = 0.0
    expect_error("in (0, 1]", lambda: StrikeReward(bad))

    reference_path = (
        ROOT / "strike" / "02_physical_control"
        / "pick-grip-reference.json")
    reference_document = json.loads(
        reference_path.read_text(encoding="utf-8"))
    bad_reference = deepcopy(reference_document)
    bad_reference["reward"]["pinch_weight"] = 1.1
    expect_error(
        "in [0, 1]", lambda: build_grip_reference(bad_reference))
    bad_reference = deepcopy(reference_document)
    bad_reference["reward"]["free_scale_rad"] = float("inf")
    expect_error(
        "finite number", lambda: build_grip_reference(bad_reference))
    print("PASS: A0-A4 strike reward terms are stage-masked")


if __name__ == "__main__":
    main()
