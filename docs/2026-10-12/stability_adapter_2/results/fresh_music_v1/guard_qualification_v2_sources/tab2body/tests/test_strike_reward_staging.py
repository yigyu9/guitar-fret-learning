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
    constrain_pick_grip_actions,
    strike_reach_potential_delta,
    strike_terminal_potential_delta,
)
from tab2body.strike_metrics import STRIKE_EPISODE_METRIC_KEYS


def reward_config():
    return {
        "grip_weight": {
            "A0_PICK_GRIP": 1.0,
            "A1_TIP_READY": 0.05,
            "A2_SINGLE_CROSSING": 0.005,
            "A3_TIMED_SINGLE": 0.003,
            "A4_STRUM_CONTEXT_RECOVERY": 0.003,
            "S3_SONG_INTEGRATION": 0.003,
            "S0_TWO_STRING_STRUM": 0.003,
            "S1_STRUM_SPAN": 0.003,
            "S2_TIMED_STRUM": 0.003,
        },
        "reach_weight": 0.2,
        "reach_discount": 0.95,
        "approach_progress_weight": {
            stage: (0.5 if stage == "S0_TWO_STRING_STRUM" else 0.0)
            for stage in STAGES
        },
        "ready_quality_weight": {
            "A0_PICK_GRIP": 0.0,
            "A1_TIP_READY": 0.75,
            "A2_SINGLE_CROSSING": 0.05,
            "A3_TIMED_SINGLE": 0.03,
            "A4_STRUM_CONTEXT_RECOVERY": 0.03,
            "S3_SONG_INTEGRATION": 0.02,
            "S0_TWO_STRING_STRUM": 0.02,
            "S1_STRUM_SPAN": 0.02,
            "S2_TIMED_STRUM": 0.02,
        },
        "crossing_reward": 1.0,
        "timing_progress_reward": {
            stage: (1.0 if stage == "S2_TIMED_STRUM"
                    else 0.75 if stage == "S3_SONG_INTEGRATION"
                    else 0.5 if stage == "A3_TIMED_SINGLE" else 0.0)
            for stage in STAGES
        },
        "timing_wait_reward": {
            stage: (0.01 if stage in (
                "A3_TIMED_SINGLE", "S2_TIMED_STRUM",
                "S3_SONG_INTEGRATION") else 0.0)
            for stage in STAGES
        },
        "early_timing_penalty": {
            stage: (1.0 if stage in (
                "A3_TIMED_SINGLE", "S2_TIMED_STRUM",
                "S3_SONG_INTEGRATION") else 0.0)
            for stage in STAGES
        },
        "strum_progress_reward": {
            stage: (0.25 if stage == "A4_STRUM_CONTEXT_RECOVERY"
                    else 0.75 if stage == "S0_TWO_STRING_STRUM"
                    else 1.0 if stage.startswith("S") else 0.0)
            for stage in STAGES
        },
        "strum_terminal_progress_reward": {
            stage: (0.25 if stage == "A4_STRUM_CONTEXT_RECOVERY"
                    else 0.75 if stage == "S0_TWO_STRING_STRUM"
                    else 1.0 if stage in (
                        "S1_STRUM_SPAN", "S2_TIMED_STRUM")
                    else 0.75 if stage == "S3_SONG_INTEGRATION" else 0.0)
            for stage in STAGES
        },
        "strum_physical_completion_reward": {
            stage: (0.35 if stage == "A4_STRUM_CONTEXT_RECOVERY"
                    else 0.5 if stage in (
                        "S0_TWO_STRING_STRUM", "S1_STRUM_SPAN",
                        "S2_TIMED_STRUM")
                    else 0.4 if stage == "S3_SONG_INTEGRATION" else 0.0)
            for stage in STAGES
        },
        "strum_microtiming_weight": {
            stage: (0.25 if stage in (
                "S2_TIMED_STRUM", "S3_SONG_INTEGRATION") else 0.0)
            for stage in STAGES
        },
        "strum_duration_core_ms": 15.0,
        "completion_reward": {
            "A0_PICK_GRIP": 0.0,
            "A1_TIP_READY": 0.15,
            "A2_SINGLE_CROSSING": 0.50,
            "A3_TIMED_SINGLE": 0.35,
            "A4_STRUM_CONTEXT_RECOVERY": 0.35,
            "S3_SONG_INTEGRATION": 0.25,
            "S0_TWO_STRING_STRUM": 0.25,
            "S1_STRUM_SPAN": 0.25,
            "S2_TIMED_STRUM": 0.25,
        },
        "wrong_crossing_penalty": {stage: 0.35 for stage in STAGES},
        "unprepared_crossing_penalty": {stage: 1.0 for stage in STAGES},
        "miss_penalty": {stage: 0.5 for stage in STAGES},
        "premature_release_penalty": {stage: 1.0 for stage in STAGES},
        "zone_weight": 0.2,
        "timing_core_ms": 20.0,
        "recovery_progress_reward": {
            stage: (0.75 if stage == "A4_STRUM_CONTEXT_RECOVERY" else 0.0)
            for stage in STAGES
        },
        "recovery_completion_reward": {
            stage: (0.75 if stage == "A4_STRUM_CONTEXT_RECOVERY" else 0.0)
            for stage in STAGES
        },
        "recovery_speed_penalty_weight": {
            stage: (0.25 if stage == "A4_STRUM_CONTEXT_RECOVERY" else 0.0)
            for stage in STAGES
        },
        "recovery_speed_limit_m_s": 0.2,
        "recovery_speed_excess_m_s": 0.5,
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
        "strum_progress": torch.tensor([0.25, 0.0]),
        "strum_terminal_progress": torch.tensor([0.25, 0.0]),
        "strum_physical_completion_pulse": torch.tensor([True, False]),
        "timing_progress_quality": torch.tensor([1.0, 0.0]),
        "timing_wait_quality": torch.tensor([0.8, 0.0]),
        "early_timing_cost": torch.tensor([0.25, 0.0]),
        "strum_timing_sample": torch.tensor([True, False]),
        "strum_timing_rms_s": torch.tensor([0.0, 0.1]),
        "strum_duration_error_s": torch.tensor([0.0, 0.1]),
        "wrong_crossing_count": torch.tensor([0.0, 1.0]),
        "miss_pulse": torch.tensor([False, True]),
        "premature_release": torch.tensor([False, False]),
        "clean_event": torch.tensor([True, False]),
        "timing_core_s": 0.02,
        "duration_core_s": 0.015,
        "zone_quality": torch.tensor([0.75, 0.0]),
        "zone_attempt": torch.tensor([True, False]),
        "recovery_active": torch.tensor([True, False]),
        "recovery_progress": torch.tensor([0.25, 0.0]),
        "recovery_complete_pulse": torch.tensor([True, False]),
        "recovery_speed_m_s": torch.tensor([0.7, 0.0]),
    }
    values.update(overrides)
    return reward.compute(stage, **values)


def main():
    reward = build_reward()

    policy = torch.tensor([[0.5, -0.5, 0.25]])
    reference = torch.tensor([[0.2, -0.2, 0.0]])
    spans = torch.tensor([0.1, 0.4, 0.0])
    hand_mask = torch.tensor([True, True, False])
    constrained = constrain_pick_grip_actions(
        policy, reference, spans, hand_mask)
    assert torch.allclose(constrained, torch.tensor([[0.25, -0.4, 0.25]]))

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
    switched_without_reset = strike_reach_potential_delta(
        torch.tensor([0.9]), torch.tensor([0.1]),
        torch.tensor([True]), discount=gamma)
    switched_with_reset = strike_reach_potential_delta(
        torch.tensor([0.0]), torch.tensor([0.1]),
        torch.tensor([False]), discount=gamma)
    assert switched_without_reset.item() < 0.0
    assert switched_with_reset.item() == 0.0
    s0_progress_weight = (
        reward.reach_weight
        + reward.approach_progress_weights["S0_TWO_STRING_STRUM"])
    assert (s0_progress_weight * discounted_cycle).item() < 0.0
    terminal_delta = strike_terminal_potential_delta(
        torch.tensor([0.5]), torch.tensor([1.0]),
        torch.tensor([True]), discount=gamma)
    assert torch.equal(terminal_delta, torch.tensor([-0.5]))
    previous = torch.tensor([0.0])
    discounted_shaping = 0.0
    for frame in range(11):
        current = torch.tensor([0.5])
        terminal = torch.tensor([frame == 10])
        delta = strike_terminal_potential_delta(
            previous, current, terminal, discount=gamma)
        discounted_shaping += gamma ** frame * float(delta)
        previous = torch.where(terminal, torch.zeros_like(current), current)
    assert abs(discounted_shaping) < 1e-6

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
        "strum_progress": torch.zeros(2),
        "strum_terminal_progress": torch.zeros(2),
        "strum_physical_completion_pulse": torch.zeros(
            2, dtype=torch.bool),
        "timing_progress_quality": torch.zeros(2),
        "timing_wait_quality": torch.zeros(2),
        "early_timing_cost": torch.zeros(2),
        "strum_timing_sample": torch.zeros(2, dtype=torch.bool),
        "strum_timing_rms_s": torch.zeros(2),
        "strum_duration_error_s": torch.zeros(2),
        "wrong_crossing_count": torch.zeros(2),
        "miss_pulse": torch.zeros(2, dtype=torch.bool),
        "premature_release": torch.zeros(2, dtype=torch.bool),
        "clean_event": torch.ones(2, dtype=torch.bool),
        "timing_core_s": 0.02,
        "duration_core_s": 0.015,
        "zone_quality": torch.zeros(2),
        "zone_attempt": torch.zeros(2, dtype=torch.bool),
        "recovery_active": torch.zeros(2, dtype=torch.bool),
        "recovery_progress": torch.zeros(2),
        "recovery_complete_pulse": torch.zeros(2, dtype=torch.bool),
        "recovery_speed_m_s": torch.zeros(2),
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
    assert not terms["reward_strum_progress"].any()
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
    assert terms["reward_strum_progress"][0] == 0.0
    assert terms["penalty_unprepared_crossing"][0] == -1.0
    assert unprepared[0, 0] < 0.0

    _a3, terms = compute(reward, STAGES[3])
    assert terms["reward_timing"][0] > 0
    assert terms["reward_timing_wait"][0] > 0
    assert terms["penalty_early_timing"][0] < 0
    assert terms["reward_zone"][0] > 0

    _a4, terms = compute(reward, STAGES[4])
    assert terms["reward_strum_progress"][0] == 0.0625
    assert terms["reward_strum_terminal_progress"][0] == 0.0625
    assert terms["reward_strum_physical_completion"][0] == 0.35
    assert terms["reward_recovery_progress"][0] > 0.0
    assert terms["reward_recovery_completion"][0] > 0.0
    assert terms["penalty_recovery_speed"][0] < 0.0
    assert not terms["reward_timing"].any()
    assert not terms["reward_timing_wait"].any()
    assert not terms["penalty_early_timing"].any()
    assert not terms["reward_zone"].any()

    _s0, terms = compute(reward, STAGES[5])
    assert terms["reward_approach_progress"][0] == 0.125
    assert terms["reward_strum_progress"][0] == 0.1875
    assert terms["reward_strum_terminal_progress"][0] == 0.1875
    assert terms["reward_strum_physical_completion"][0] == 0.5

    _s2, terms = compute(reward, STAGES[7])
    assert torch.isclose(terms["reward_zone"][0], torch.tensor(0.15))
    assert terms["reward_timing"][0] == 1.0
    assert terms["reward_strum_microtiming"][0] > 0
    _, premature_terms = compute(
        reward, STAGES[7],
        premature_release=torch.tensor([False, True]))
    assert premature_terms["penalty_premature_release"][1] == -1.0
    _, timing_failed_completion = compute(
        reward, STAGES[7],
        target_hit=torch.zeros(2, dtype=torch.bool),
        timing_progress_quality=torch.zeros(2))
    assert timing_failed_completion[
        "reward_strum_physical_completion"][0] == 0.5
    _, dirty_completion = compute(
        reward, STAGES[7],
        clean_event=torch.tensor([False, False]))
    assert not dirty_completion["reward_strum_physical_completion"].any()



    _, terms = compute(reward, STAGES[-1])
    assert terms["reward_grip"][0] == 0.0
    assert terms["reward_grip"][1] < 0.0
    clean_total, clean_terms = compute(
        reward, STAGES[-1],
        wrong_crossing_count=torch.zeros(2),
        clean_event=torch.tensor([True, True]))
    blocked_total, blocked_terms = compute(
        reward, STAGES[-1],
        wrong_crossing_count=torch.tensor([1.0, 0.0]),
        clean_event=torch.tensor([False, True]))
    assert clean_terms["reward_timing"][0] > 0.0
    assert blocked_terms["reward_timing"][0] == 0.0
    assert blocked_terms["reward_strum_microtiming"][0] == 0.0
    assert clean_total[0, 0] > blocked_total[0, 0]

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
    bad["wrong_crossing_penalty"][STAGES[0]] = -0.01
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
    task_source = (
        ROOT / "tab2body" / "env" / "tasks" / "task_strike.py"
    ).read_text()
    for metric_name, accumulator_name, reward_name in (
            (
                "strike_reward_strum_terminal_progress_return",
                "metric_reward_strum_terminal_progress_return",
                "reward_strum_terminal_progress",
            ),
            (
                "strike_reward_strum_physical_completion_return",
                "metric_reward_strum_physical_completion_return",
                "reward_strum_physical_completion",
            )):
        assert metric_name in STRIKE_EPISODE_METRIC_KEYS
        assert accumulator_name in task_source
        assert reward_name in task_source
    print("PASS: A0-A4 and S0-S3 strike reward terms are stage-masked")


if __name__ == "__main__":
    main()
