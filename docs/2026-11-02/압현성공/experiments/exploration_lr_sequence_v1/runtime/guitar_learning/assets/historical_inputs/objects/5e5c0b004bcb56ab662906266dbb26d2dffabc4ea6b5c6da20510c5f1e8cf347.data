"""정밀 압현·유지·클래스 균형 보상의 CPU 회귀 검사."""
from __future__ import annotations

from pathlib import Path
import sys

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env.rewards.fret import (
    aggregate_active_channel_bottleneck,
    apply_binary_penalty,
    balance_press_no_press_channels,
    blend_anchor_finger_reward,
    blend_finger_coupling_reward,
    blend_goal_pair_rehearsal_anchor_reward,
    bound_fret_reward,
    cached_consensus_action_teacher,
    cached_finger_action_teacher,
    cached_finger_pose_guide,
    chord_aware_target_fraction,
    chord_fine_conjunctive_reward,
    conjunctive_chord_quality,
    conjunctive_next_goal_quality,
    dense_fret_position_quality,
    fine_alignment_distance_reward,
    fret_region_alignment,
    fret_position_inside,
    fret_position_quality,
    frozen_context_pose_guide_gate,
    gate_chord_completion_for_stage,
    gate_incomplete_static_chord_reward,
    gate_next_goal_positive_progress,
    gate_static_chord_auxiliary_reward,
    guitar_penetration_soft_cost,
    integrated_press_core_reward,
    isolated_press_conjunctive_quality,
    next_goal_approach_reward,
    next_goal_distance_potential,
    next_goal_potential_progress,
    minimum_active_target_separation,
    precise_press_success,
    press_arch_shaping_quality,
    press_precision_components,
    press_precision_gate,
    press_near_miss_mask,
    qualify_curriculum_episode_success,
    suppress_positive_reward_on_penetration,
    update_press_hold_state,
    uses_press_compatible_alignment,
    wrong_press_finger_mask,
)
from cfg import FRET


def test_static_chord_auxiliary_reward_is_gated_by_press_completion():
    balanced = torch.tensor([[0.8, 0.8], [0.8, 0.8], [0.8, 0.8]])
    press = torch.tensor([0.2, 0.2, 0.2])
    completion = torch.tensor([0.0, 0.5, 1.0])
    gated, gate = gate_static_chord_auxiliary_reward(
        balanced, press, completion, floor=0.10)
    assert torch.allclose(gate, torch.tensor([0.10, 0.55, 1.0]))
    assert torch.allclose(gated[:, 0], torch.tensor([0.26, 0.53, 0.80]))

    penalized, _ = gate_static_chord_auxiliary_reward(
        torch.tensor([[0.1, 0.1]]), torch.tensor([0.2]),
        torch.tensor([0.0]), floor=0.10)
    assert torch.allclose(penalized, torch.tensor([[0.1, 0.1]]))


def test_incomplete_static_chord_keeps_gradient_but_blocks_partial_solution():
    reward = torch.tensor([
        [0.8, 0.8], [0.8, 0.8], [-0.2, 0.8], [0.8, 0.8]])
    completion = torch.tensor([0.0, 0.5, 0.5, 0.5])
    count = torch.tensor([2, 2, 2, 1])
    gated, gate = gate_incomplete_static_chord_reward(
        reward, completion, count, floor=0.15, power=2.0)
    expected_half_gate = 0.15 + 0.85 * 0.25
    assert torch.allclose(
        gate, torch.tensor([0.15, expected_half_gate,
                            expected_half_gate, 1.0]))
    assert torch.allclose(gated[0], torch.full((2,), 0.12))
    assert torch.allclose(
        gated[1], torch.full((2,), 0.8 * expected_half_gate))
    assert gated[2, 0] == -0.2
    assert gated[3, 0] == 0.8
from env.goals import FINGER_EVENT_TIME_SCALE_S


def test_same_fret_chord_targets_stagger_for_clearance():
    fret = torch.zeros(1, 6)
    active = torch.zeros(1, 6, dtype=torch.bool)
    fret[0, 1:3] = 4
    active[0, 1:3] = True
    usable = torch.full((1, 6), 0.027926)
    base = torch.zeros(1, 6, 3)
    base[0, :, 1] = torch.arange(6) * 0.007516
    fraction = chord_aware_target_fraction(
        fret, active, base, usable, fingertip_clearance=0.0155)
    assert fraction[0, 1] < 0.20 < fraction[0, 2]
    assert torch.all((fraction >= 0.10) & (fraction <= 0.90))

    target = base.clone()
    target[..., 0] = -(fraction - 0.20) * usable
    separation = minimum_active_target_separation(target, active)
    assert separation[0] >= 0.01549

    single = active.clone()
    single[0, 2] = False
    single_fraction = chord_aware_target_fraction(
        fret, single, base, usable)
    assert single_fraction[0, 1] == 0.20


def test_chord_targets_preserve_runtime_device_and_dtype():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    fret = torch.tensor([[0, 4, 4, 0, 0, 0]], device=device)
    active = fret > 0
    usable = torch.full(
        fret.shape, 0.027926, dtype=torch.float32, device=device)
    base = torch.zeros(
        (*fret.shape, 3), dtype=torch.float32, device=device)
    base[0, :, 1] = torch.arange(
        fret.shape[1], dtype=base.dtype, device=device) * 0.007516
    fraction = chord_aware_target_fraction(fret, active, base, usable)
    assert fraction.device == usable.device
    assert fraction.dtype == usable.dtype
    assert torch.isfinite(fraction).all()


def test_fine_distance_reward_is_precision_sensitive():
    distance = torch.tensor(
        [0.0, 0.005, 0.010, 0.020, 0.040], requires_grad=True)
    reward = fine_alignment_distance_reward(distance)
    assert reward[0] == 1
    assert torch.all(reward[:-1] > reward[1:])
    assert reward[2] > 0.50
    assert reward[3] < 0.35
    assert reward[4] < 0.15
    reward[3:].sum().backward()
    assert torch.all(distance.grad[3:] < 0)


def test_integrated_press_reward_keeps_precontact_lateral_gradient():
    lateral = torch.tensor([0.2, 0.8], requires_grad=True)
    reward = integrated_press_core_reward(
        torch.full((2,), 0.7),
        torch.full((2,), 0.6),
        lateral,
        torch.full((2,), 0.8),
        torch.full((2,), 0.7),
        torch.zeros(2),
        torch.zeros(2),
        torch.zeros(2, dtype=torch.bool),
        torch.zeros(2))
    assert reward[1] > reward[0]
    reward.sum().backward()
    assert torch.all(lateral.grad > 0)


def test_curriculum_episode_requires_sustained_settling_success():
    qualified, fraction = qualify_curriculum_episode_success(
        torch.tensor([True, True, False]),
        torch.tensor([12.0, 27.0, 30.0]),
        torch.tensor([30.0, 30.0, 30.0]),
        minimum_fraction=0.80)
    assert torch.allclose(fraction, torch.tensor([0.4, 0.9, 1.0]))
    assert qualified.tolist() == [False, True, False]


def test_position_has_uniform_valid_region():
    x = torch.tensor([0.0, 0.05, 0.10, 0.20, 0.50, 0.90, 0.95, 1.0])
    quality = fret_position_quality(x)
    assert quality[0] == 0 and quality[-1] == 0
    assert torch.all(quality[2:6] == 1)
    assert torch.isclose(quality[1], quality[6], atol=1e-6)
    assert torch.equal(
        fret_position_inside(x),
        torch.tensor([False, False, True, True, True, True, False, False]))


def test_dense_position_gradient_and_gate():
    x = torch.tensor(
        [-0.10, 0.05, 0.20, 0.50, 0.90, 0.95, 1.10],
        requires_grad=True)
    dense = dense_fret_position_quality(x, scale=0.20)
    assert torch.all(dense[2:5] == 1)
    assert dense[1] > dense[0] > 0
    assert torch.isclose(dense[1], dense[5], atol=1e-6)
    assert torch.isclose(dense[0], dense[6], atol=1e-6)
    dense.sum().backward()
    assert x.grad[0] > 0 and x.grad[-1] < 0
    assert torch.all(x.grad[2:5] == 0)

    gate = press_precision_gate(dense.detach(), floor=0.40)
    assert torch.all((gate >= 0.40) & (gate <= 1.0))
    assert torch.all(gate[2:5] == 1)


def test_wider_position_region_does_not_create_an_internal_peak():
    x = torch.tensor([0.05, 0.20, 0.35, 0.50, 0.90])
    strict = fret_position_quality(x, upper=0.35)
    relaxed = fret_position_quality(x, upper=0.90)
    assert torch.all(relaxed[1:] == 1.0)
    assert relaxed[3] > strict[3]

    strict_dense = dense_fret_position_quality(
        x, scale=0.20, upper=0.35)
    relaxed_dense = dense_fret_position_quality(
        x, scale=0.30, upper=0.90)
    strict_gate = press_precision_gate(strict_dense, floor=0.40)
    relaxed_gate = press_precision_gate(relaxed_dense, floor=0.60)
    assert relaxed_gate[1] == 1.0
    assert torch.all(relaxed_gate >= strict_gate)
    assert relaxed_gate[-1] == 1.0


def test_multi_press_region_does_not_prefer_one_longitudinal_point():
    usable = torch.full((1, 3), 0.030)
    target_fraction = torch.full((1, 3), 0.20)
    sample_fraction = torch.tensor([[0.05, 0.35, 0.60]])
    signed = (target_fraction - sample_fraction) * usable
    zeros = torch.zeros_like(signed)
    region = fret_region_alignment(
        signed, zeros, zeros, target_fraction, usable,
        lower=0.10, upper=0.90)
    assert torch.equal(
        region["inside"], torch.tensor([[False, True, True]]))
    assert region["distance"][0, 0] > 0.0014
    assert torch.allclose(region["distance"][0, 1:], torch.full((2,), 1e-6))
    assert torch.allclose(region["sample_fraction"], sample_fraction)


def test_contact_stages_use_press_compatible_alignment():
    for stage in (
            "isolated_press", "integrated_press", "chord_fine_reach",
            "static_chord", "frozen_context", "goal_pair",
            "transition_window", "coverage", "integration", "full_song"):
        assert uses_press_compatible_alignment(stage)
    for stage in ("coarse_reach", "fine_reach", "chord_reach"):
        assert not uses_press_compatible_alignment(stage)


def test_precise_success_uses_raw_fret_position():
    pressed = torch.tensor([[True, True, False]])
    raw = torch.tensor([[0.49, 0.50, 1.00]])
    composite = torch.tensor([[0.90, 0.70, 0.90]])
    strict = precise_press_success(pressed, raw)
    assert torch.equal(strict, torch.tensor([[False, True, False]]))
    with_arch = precise_press_success(
        pressed, raw, composite, min_arch=0.80)
    assert torch.equal(with_arch, torch.tensor([[False, False, False]]))


def test_press_precision_components_explain_each_gate():
    pressed = torch.tensor([[True, True, False, True]])
    position = torch.tensor([[0.8, 0.4, 0.9, 0.8]])
    arch = torch.tensor([[0.9, 0.9, 0.9, 0.6]])
    contact, position_pass, arch_pass, precise = (
        press_precision_components(pressed, position, arch))
    assert torch.equal(contact, pressed)
    assert torch.equal(
        position_pass, torch.tensor([[True, False, True, True]]))
    assert torch.equal(
        arch_pass, torch.tensor([[True, True, True, False]]))
    assert torch.equal(
        precise, torch.tensor([[True, False, False, False]]))


def test_press_arch_shaping_quality_targets_strict_boundary_continuously():
    quality = torch.tensor([0.0, 0.30, 0.64, 0.65, 0.80, 1.0])
    shaped = press_arch_shaping_quality(quality)
    assert shaped[0] == 0.0
    assert shaped[-1] == 1.0
    assert torch.all(shaped[:-1] < shaped[1:])
    assert shaped[3] > quality[3]


def test_isolated_press_conjunction_rejects_single_factor_shortcuts():
    contact = torch.tensor([1.0, 1.0, 0.5, 0.0])
    position = torch.tensor([1.0, 0.0, 0.5, 1.0])
    arch = torch.tensor([1.0, 1.0, 0.5, 1.0])
    quality = isolated_press_conjunctive_quality(
        contact, position, arch)
    assert torch.allclose(quality, torch.tensor([1.0, 0.0, 0.125, 0.0]))


def test_wrong_press_is_attributed_to_contacting_finger():
    pressed = torch.zeros(1, 2, 4, 3, dtype=torch.bool)
    forbidden = torch.zeros(1, 2, 3, dtype=torch.bool)
    forbidden[0, 0, 2] = True
    forbidden[0, 1, 1] = True
    pressed[0, 0, 1, 2] = True
    pressed[0, 1, 3, 0] = True
    mask = wrong_press_finger_mask(pressed, forbidden)
    assert torch.equal(mask, torch.tensor([[False, True, False, False]]))


def test_hold_and_dropout():
    shape = (1, 2)
    streak = torch.zeros(shape, dtype=torch.long)
    acquired = torch.zeros(shape, dtype=torch.bool)
    previous_fret = torch.zeros(shape, dtype=torch.long)
    previous_finger = torch.zeros(shape, dtype=torch.long)
    fret = torch.tensor([[4, -1]])
    finger = torch.tensor([[1, 0]])
    success = torch.tensor([[True, False]])

    for frame in range(1, 13):
        streak, acquired, quality, dropout, same = update_press_hold_state(
            streak, acquired, previous_fret, previous_finger,
            fret, finger, success, min_frames=6, full_frames=12)
        previous_fret = fret.clone()
        previous_finger = finger.clone()
        assert int(streak[0, 0]) == frame
        assert not bool(dropout.any())
        assert bool(acquired[0, 0]) == (frame >= 6)
        if frame < 6:
            assert quality[0, 0] == 0
    assert quality[0, 0] == 1

    failed = torch.zeros_like(success)
    streak, acquired, quality, dropout, _ = update_press_hold_state(
        streak, acquired, previous_fret, previous_finger,
        fret, finger, failed, min_frames=6, full_frames=12)
    assert bool(dropout[0, 0])
    assert bool(acquired[0, 0])
    assert streak[0, 0] == 0 and quality[0, 0] == 0

    moved_fret = torch.tensor([[5, -1]])
    _, moved_acquired, _, moved_dropout, same = update_press_hold_state(
        streak, acquired, previous_fret, previous_finger,
        moved_fret, finger, failed, min_frames=6, full_frames=12)
    assert not bool(same[0, 0])
    assert not bool(moved_dropout[0, 0])
    assert not bool(moved_acquired[0, 0])


def test_large_failure_penalties_keep_reward_bounded():
    reward = torch.full((1, 4), 0.8)
    dropout = torch.tensor([[True, False, True, False]])
    wrong = torch.tensor([[True, True, False, False]])
    shaped = apply_binary_penalty(reward, dropout, 1_000_000.0)
    shaped = apply_binary_penalty(shaped, wrong, 2_000_000.0)
    assert torch.isfinite(shaped).all()

    bounded = bound_fret_reward(
        shaped, "full_song",
        wrong_press_penalty=2_000_000.0,
        press_dropout_penalty=1_000_000.0)
    assert torch.equal(bounded, torch.tensor([[-1.0, -1.0, -1.0, 0.8]]))
    assert torch.isfinite(bounded).all()
    assert bool(((bounded >= -1.0) & (bounded <= 1.0)).all())

    combined = apply_binary_penalty(
        torch.zeros(1, 1), torch.ones(1, 1, dtype=torch.bool), 0.25)
    combined = apply_binary_penalty(
        combined, torch.ones(1, 1, dtype=torch.bool), 0.35)
    assert torch.equal(
        bound_fret_reward(combined, "full_song", 0.35, 0.25),
        torch.tensor([[-0.60]]))
    assert torch.equal(
        bound_fret_reward(
            torch.tensor([[-0.5, 0.5]]), "full_song", 0.0, 0.0),
        torch.tensor([[0.0, 0.5]]))

    try:
        apply_binary_penalty(reward, dropout, float("inf"))
    except ValueError:
        pass
    else:
        raise AssertionError("non-finite penalty was accepted")


def test_near_miss_is_diagnostic_only_in_training_config():
    active = torch.tensor([[True, True, True, False]])
    success = torch.tensor([[False, False, True, False]])
    distance = torch.tensor([[0.010, 0.030, 0.005, 0.001]])
    miss = press_near_miss_mask(
        active, success, distance, max_distance=0.015)
    assert torch.equal(
        miss, torch.tensor([[True, False, False, False]]))
    assert FRET["press_near_miss_penalty"] == 0.0
    value = torch.tensor([[0.60, 0.40, 0.80, 0.20]])
    assert torch.equal(
        apply_binary_penalty(
            value, miss, FRET["press_near_miss_penalty"]),
        value)


def test_class_balance():
    reward = torch.tensor([
        [0.4, 0.6, 1.0, 1.0, 1.0, 0.0],
        [1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
        [0.4, 0.6, 0.0, 0.0, 0.0, 0.0],
    ])
    press = torch.tensor([
        [True, True, False, False, False, False],
        [False, False, False, False, False, False],
        [True, True, False, False, False, False],
    ])
    no_press = torch.tensor([
        [False, False, True, True, True, False],
        [True, True, True, False, False, False],
        [False, False, False, False, False, False],
    ])
    success = torch.zeros_like(press)
    balanced, metrics = balance_press_no_press_channels(
        reward, press, no_press, success)
    assert torch.allclose(balanced[0], torch.full((6,), 0.475))
    assert torch.allclose(balanced[1], torch.ones(6))
    assert torch.allclose(balanced[2], torch.full((6,), 0.5))
    assert torch.isclose(
        metrics["effective_no_press_class_weight"][0],
        torch.tensor(0.10))

    success[0, :2] = True
    balanced, metrics = balance_press_no_press_channels(
        reward, press, no_press, success)
    assert torch.allclose(balanced[0], torch.full((6,), 0.625))
    assert torch.isclose(
        metrics["effective_no_press_class_weight"][0],
        torch.tensor(0.25))

    no_op_reward = torch.tensor([[0.0, 1.0]])
    mixed_press = torch.tensor([[True, False]])
    mixed_no_press = torch.tensor([[False, True]])
    no_op, _ = balance_press_no_press_channels(
        no_op_reward, mixed_press, mixed_no_press,
        torch.zeros_like(mixed_press))
    correct, _ = balance_press_no_press_channels(
        torch.ones_like(no_op_reward), mixed_press, mixed_no_press,
        mixed_press)
    assert torch.allclose(no_op, torch.full_like(no_op, 0.10))
    assert torch.allclose(correct, torch.ones_like(correct))
    assert torch.all(no_op < correct)


def test_static_chord_bottleneck_and_completion_gate():
    reward = torch.tensor([[1.0, 0.0, 1.0]])
    press = torch.tensor([[True, True, False]])
    no_press = torch.tensor([[False, False, True]])
    success = torch.tensor([[True, False, False]])
    balanced, metrics = balance_press_no_press_channels(
        reward, press, no_press, success,
        no_press_failure_credit=0.0,
        press_bottleneck_weight=0.5,
        no_press_completion_power=2.0)
    assert torch.allclose(balanced, torch.full_like(balanced, 0.25))
    assert torch.isclose(
        metrics["press_class_mean_reward"][0], torch.tensor(0.5))
    assert metrics["press_class_min_reward"][0] == 0
    assert torch.isclose(
        metrics["press_class_reward"][0], torch.tensor(0.25))
    assert torch.isclose(
        metrics["effective_no_press_class_weight"][0],
        torch.tensor(0.0625))

    complete, metrics = balance_press_no_press_channels(
        torch.ones_like(reward), press, no_press, press,
        no_press_failure_credit=0.0,
        press_bottleneck_weight=0.5,
        no_press_completion_power=2.0)
    assert torch.allclose(complete, torch.ones_like(complete))
    assert metrics["press_class_reward"][0] == 1


def test_frozen_context_completion_gate_stays_active_for_all_rows():
    balanced = torch.full((3, 2), 0.8)
    completion = torch.tensor([0.0, 0.5, 1.0])
    press_count = torch.tensor([2, 2, 2])
    frozen, gate = gate_chord_completion_for_stage(
        "frozen_context", balanced, completion, press_count,
        floor=0.15, power=2.0)
    expected_gate = 0.15 + 0.85 * completion.square()
    assert torch.allclose(gate, expected_gate)
    assert torch.allclose(frozen, balanced * expected_gate[:, None])

    unchanged, open_gate = gate_chord_completion_for_stage(
        "goal_pair", balanced, completion, press_count,
        floor=0.15, power=2.0)
    assert torch.equal(unchanged, balanced)
    assert torch.equal(open_gate, torch.ones_like(open_gate))


def test_chord_joint_quality_requires_release_and_thumb_readiness():
    quality = conjunctive_chord_quality(
        torch.tensor([1.0, 1.0, 1.0]),
        torch.tensor([1.0, 1.0, 1.0]),
        torch.tensor([1.0, 0.5, 1.0]),
        torch.tensor([1.0, 1.0, 0.4]))
    assert torch.allclose(quality, torch.tensor([1.0, 0.5, 0.4]))


def test_chord_bridge_active_finger_bottleneck():
    reward = torch.tensor([[1.0, 0.0, 9.0]])
    active = torch.tensor([[True, True, False]])
    aggregated, value, mean, minimum = (
        aggregate_active_channel_bottleneck(
            reward, active, bottleneck_weight=0.5))
    assert torch.allclose(
        aggregated, torch.tensor([[0.25, 0.25, 9.0]]))
    assert torch.isclose(value[0], torch.tensor(0.25))
    assert torch.isclose(mean[0], torch.tensor(0.5))
    assert minimum[0] == 0


def test_chord_fine_joint_reward_tracks_the_weakest_finger():
    active = torch.tensor([[True, True, False]])
    fine_distance = torch.tensor([[1.0, 0.3, 0.9]])
    longitudinal = torch.ones_like(fine_distance)
    lateral = torch.tensor([[1.0, 0.9, 1.0]])
    normal = torch.tensor(
        [[1.0, 0.0016, 1.0]], requires_grad=True)
    depth = torch.tensor([[1.0, 0.25, 1.0]])
    success = torch.tensor([[True, False, True]])
    expanded, aggregate, mean, minimum, axis_minimum = (
        chord_fine_conjunctive_reward(
            fine_distance, longitudinal, lateral, normal,
            depth, success, active, bottleneck_weight=1.0))
    assert torch.isclose(axis_minimum[0, 1], torch.tensor(0.2))
    assert torch.isclose(aggregate[0], minimum[0])
    assert aggregate[0] < mean[0]
    assert torch.equal(expanded[0, :2], aggregate.expand(2))
    aggregate.sum().backward()
    assert normal.grad[0, 1] > 0.0


def test_goal_pair_anchor_exposes_selected_finger_quality():
    balanced = torch.full((2, 3), 0.5)
    channel = torch.tensor([[0.9, 0.1, 0.8], [0.2, 0.7, 0.4]])
    anchor = torch.tensor([
        [False, True, False],
        [False, False, False],
    ])
    shaped, anchor_reward, active = (
        blend_goal_pair_rehearsal_anchor_reward(
            balanced, channel, anchor, weight=0.25))
    assert torch.allclose(shaped[0], torch.full((3,), 0.4))
    assert torch.equal(shaped[1], balanced[1])
    assert torch.allclose(anchor_reward, torch.tensor([0.1, 0.0]))
    assert torch.equal(active, torch.tensor([True, False]))


def test_goal_pair_anchor_prioritizes_selected_next_goal():
    mean = torch.tensor([0.40, 0.40, 0.40])
    per_finger = torch.tensor([
        [0.10, 0.90, 0.20, 0.30],
        [0.10, 0.90, 0.20, 0.30],
        [0.10, 0.90, 0.20, 0.30],
    ])
    active = torch.tensor([
        [False, True, False, False],
        [False, False, True, False],
        [False, True, False, False],
    ])
    blended, selected, enabled = blend_anchor_finger_reward(
        mean, per_finger, active, torch.tensor([2, 2, 0]), weight=0.25)
    assert torch.isclose(blended[0], torch.tensor(0.525))
    assert blended[1] == mean[1]
    assert blended[2] == mean[2]
    assert torch.equal(selected, torch.tensor([0.90, 0.90, 0.10]))
    assert enabled.tolist() == [True, False, False]




def test_next_goal_gate():
    tips = torch.zeros(1, 4, 3)
    tips[0, 0, 2] = 0.0063
    targets = torch.zeros(1, 6, 22, 3)
    outward = torch.zeros(1, 6, 3)
    outward[..., 2] = 1.0
    event = torch.zeros(1, 4, 13)
    event[0, 0, 2] = 1.0
    event[0, 0, 6] = 4.0 / 22.0
    event[0, 0, 7] = 0.25 / FINGER_EVENT_TIME_SCALE_S
    event[0, 0, 8] = 1.0
    event[0, 0, 11] = 1.0
    current_active = torch.zeros(1, 4, dtype=torch.bool)

    reward, metrics = next_goal_approach_reward(
        tips, targets, outward, event, current_active)
    assert bool(metrics["next_goal_approach_gate"][0, 0])
    assert reward[0] > 0
    hover_tips = tips.clone()
    hover_tips[0, 0, 2] = 0.0103
    hover_reward, _ = next_goal_approach_reward(
        hover_tips, targets, outward, event, current_active)
    assert hover_reward[0] > reward[0]
    floored_reward, floored_metrics = next_goal_approach_reward(
        tips, targets, outward, event, current_active,
        time_gate_floor=torch.tensor([0.30]))
    assert floored_reward[0] > reward[0]
    assert floored_metrics["next_goal_time_gate"][0, 0] >= 0.30
    scalar_reward, _ = next_goal_approach_reward(
        tips, targets, outward, event, current_active,
        time_gate_floor=0.30)
    assert torch.allclose(floored_reward, scalar_reward)
    for invalid in (-0.1, 1.1, float("nan")):
        try:
            next_goal_approach_reward(
                tips, targets, outward, event, current_active,
                time_gate_floor=invalid)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid next-goal time floor accepted")

    current_active[0, 0] = True
    blocked, metrics = next_goal_approach_reward(
        tips, targets, outward, event, current_active)
    assert blocked[0] == 0
    assert not bool(metrics["next_goal_approach_gate"][0, 0])

    current_active[0, 0] = False
    event[0, 0, 7] = 1.0
    distant, metrics = next_goal_approach_reward(
        tips, targets, outward, event, current_active,
        lookahead_s=1.50)
    assert distant[0] == 0
    assert not bool(metrics["next_goal_approach_gate"][0, 0])


def test_next_goal_progress_is_signed_and_target_safe():
    previous_distance = torch.tensor([[0.250, 0.200]])
    current_distance = torch.tensor([[0.249, 0.201]])
    previous = next_goal_distance_potential(previous_distance)
    valid = torch.ones(1, 2, dtype=torch.bool)
    preserved = torch.tensor([True])
    progress, current = next_goal_potential_progress(
        previous, current_distance, valid, valid, valid, preserved)
    expected = 0.001 / 0.340
    assert torch.isclose(progress[0, 0], torch.tensor(expected), atol=1e-6)
    assert torch.isclose(progress[0, 1], torch.tensor(-expected), atol=1e-6)

    reverse, _ = next_goal_potential_progress(
        current, previous_distance, valid, valid, valid, preserved)
    assert torch.allclose(progress + reverse, torch.zeros_like(progress))

    blocked, _ = next_goal_potential_progress(
        previous, current_distance, valid, valid, valid,
        torch.tensor([False]))
    assert blocked[0, 0] == 0
    assert blocked[0, 1] < 0
    graduated, _ = next_goal_potential_progress(
        previous, current_distance, valid, valid, valid,
        torch.tensor([0.0]), unprotected_positive_scale=0.25)
    assert torch.isclose(
        graduated[0, 0], torch.tensor(0.25 * expected), atol=1e-6)
    assert torch.isclose(
        graduated[0, 1], torch.tensor(-expected), atol=1e-6)

    changed, _ = next_goal_potential_progress(
        previous, current_distance, valid, torch.zeros_like(valid),
        valid, preserved)
    assert torch.equal(changed, torch.zeros_like(changed))

    narrow_previous_distance = torch.tensor([[0.055, 0.055]])
    narrow_current_distance = torch.tensor([[0.054, 0.056]])
    narrow_previous = next_goal_distance_potential(
        narrow_previous_distance, near=0.010, far=0.100)
    assert torch.allclose(
        next_goal_distance_potential(
            torch.tensor([[0.010, 0.055, 0.100]]),
            near=0.010, far=0.100),
        torch.tensor([[1.0, 0.5, 0.0]]))
    narrow, _ = next_goal_potential_progress(
        narrow_previous, narrow_current_distance,
        valid, valid, valid, torch.tensor([0.0]),
        near=0.010, far=0.100,
        unprotected_positive_scale=0.50)
    narrow_expected = 0.001 / 0.090
    assert torch.isclose(
        narrow[0, 0],
        torch.tensor(0.50 * narrow_expected), atol=1e-6)
    assert torch.isclose(
        narrow[0, 1], torch.tensor(-narrow_expected), atol=1e-6)


def test_goal_pair_positive_progress_requires_current_press_preservation():
    progress = torch.tensor([
        [0.20, -0.10, 0.0, 0.30],
        [0.20, -0.10, 0.0, 0.30],
    ])
    gated = gate_next_goal_positive_progress(
        progress,
        torch.tensor([False, True]),
        require_preservation=True)
    assert torch.equal(
        gated[0], torch.tensor([0.0, -0.10, 0.0, 0.0]))
    assert torch.equal(gated[1], progress[1])

    # Negative deltas remain visible after the positive-credit gate closes.
    signed = gate_next_goal_positive_progress(
        progress,
        torch.tensor([False, False]),
        require_preservation=True)
    assert torch.equal(signed[:, 1], progress[:, 1])


def test_coupling_does_not_tax_closed_gate():
    reward = torch.tensor([[0.8, 0.4]])
    press = torch.tensor([[True, False]])
    closed = torch.zeros(1, 4, dtype=torch.bool)
    unchanged, active = blend_finger_coupling_reward(
        reward, torch.tensor([0.0]), press, closed, weight=0.015)
    assert not bool(active[0])
    assert torch.equal(unchanged, reward)

    opened = closed.clone()
    opened[0, 1] = True
    blended, active = blend_finger_coupling_reward(
        reward, torch.tensor([0.0]), press, opened, weight=0.015)
    assert bool(active[0])
    assert blended[0, 0] < reward[0, 0]
    assert blended[0, 1] == reward[0, 1]


def test_frozen_pose_guide_does_not_mutate_shared_activity():
    active = torch.tensor([
        [True, True, False, False],
        [False, True, True, False],
    ])
    original = active.clone()
    gate = frozen_context_pose_guide_gate(
        active, torch.tensor([True, False]))
    assert torch.equal(active, original)
    assert torch.equal(gate, torch.tensor([
        [True, True, False, False],
        [False, False, False, False],
    ]))


def test_cached_finger_pose_guide_is_dense_and_strictly_gated():
    current = torch.zeros(2, 4, 4)
    target = torch.zeros_like(current)
    scale = torch.ones(4, 4)
    valid = torch.zeros(2, 4, dtype=torch.bool)
    gate = torch.zeros_like(valid)
    valid[0, 1] = True
    gate[0, 1] = True
    target[0, 1] = 1.0
    reward, per_finger, active = cached_finger_pose_guide(
        current, target, scale, valid, gate)
    expected = torch.exp(torch.tensor(-0.5))
    assert torch.isclose(reward[0], expected)
    assert reward[1] == 0.0
    assert torch.isclose(per_finger[0, 1], expected)
    assert int(active.sum()) == 1

    target[0, 1] = 0.25
    closer, _, _ = cached_finger_pose_guide(
        current, target, scale, valid, gate)
    assert closer[0] > reward[0]
    gate.zero_()
    closed, _, active = cached_finger_pose_guide(
        current, target, scale, valid, gate)
    assert torch.equal(closed, torch.zeros_like(closed))
    assert not active.any()

    proximal = torch.zeros(2, 4, 9)
    proximal_scale = torch.ones(4, 9)
    valid[1, 2] = True
    gate[1, 2] = True
    proximal_target = proximal.clone()
    proximal_target[1, 2] = 0.5
    proximal_reward, _, _ = cached_finger_pose_guide(
        proximal, proximal_target, proximal_scale, valid, gate)
    assert 0.0 < proximal_reward[1] < 1.0


def test_cached_finger_action_teacher_composes_active_fingers():
    target = torch.arange(32, dtype=torch.float32).reshape(2, 4, 4)
    valid = torch.ones(2, 4, dtype=torch.bool)
    active = torch.tensor([
        [True, True, False, False],
        [False, False, True, False],
    ])
    quality = torch.tensor([
        [0.30, 0.10, 0.0, 0.0],
        [0.0, 0.0, 0.80, 0.0],
    ])
    teacher, mask = cached_finger_action_teacher(
        target, valid, active, quality, minimum_quality=0.20)
    assert mask[0, 0].all() and not mask[0, 1:].any()
    assert mask[1, 2].all() and not mask[1, :2].any()
    assert not mask[1, 3].any()
    assert torch.equal(teacher[0, 0], target[0, 0])
    assert not teacher[0, 1:].any()


def test_cached_consensus_teacher_masks_conflicting_proximal_axes():
    target = torch.tensor([[[0.10, -0.20, 0.00],
                            [0.20, 0.70, 0.10],
                            [0.00, 0.00, 0.00],
                            [0.00, 0.00, 0.00]]])
    valid = torch.tensor([[True, True, False, False]])
    active = valid.clone()
    quality = torch.tensor([[1.0, 3.0, 0.0, 0.0]])
    teacher, mask = cached_consensus_action_teacher(
        target, valid, active, quality, max_action_spread=0.35)
    # axis 0/2는 합의하므로 품질 가중 평균, axis 1은 충돌하므로 제외한다.
    assert torch.equal(mask, torch.tensor([[True, False, True]]))
    assert torch.allclose(teacher[0, [0, 2]], torch.tensor([0.175, 0.075]))
    assert teacher[0, 1] == 0.0

    one_source = active.clone()
    one_source[0, 1] = False
    _, one_mask = cached_consensus_action_teacher(
        target, valid, one_source, quality, max_action_spread=0.35)
    assert not one_mask.any()


def test_transition_quality_requires_preservation_and_penetration_blocks_credit():
    joint = conjunctive_next_goal_quality(
        torch.tensor([0.8, 0.8, 0.8]),
        torch.tensor([1.0, 0.5, 0.0]))
    assert torch.allclose(joint, torch.tensor([0.8, 0.4, 0.0]))

    reward = torch.tensor([[0.7, -0.2], [0.4, 0.1]])
    gated = suppress_positive_reward_on_penetration(
        reward, torch.tensor([True, False]))
    assert torch.equal(gated[0], torch.tensor([0.0, -0.2]))
    assert torch.equal(gated[1], reward[1])

    cost = guitar_penetration_soft_cost(torch.tensor([
        0.0, 0.0025, 0.00375, 0.005, 0.010]))
    assert torch.allclose(
        cost, torch.tensor([0.0, 0.0, 0.0125, 0.05, 0.05]))


def main():
    test_static_chord_auxiliary_reward_is_gated_by_press_completion()
    test_incomplete_static_chord_keeps_gradient_but_blocks_partial_solution()
    test_same_fret_chord_targets_stagger_for_clearance()
    test_chord_targets_preserve_runtime_device_and_dtype()
    test_fine_distance_reward_is_precision_sensitive()
    test_integrated_press_reward_keeps_precontact_lateral_gradient()
    test_curriculum_episode_requires_sustained_settling_success()
    test_position_has_uniform_valid_region()
    test_dense_position_gradient_and_gate()
    test_wider_position_region_does_not_create_an_internal_peak()
    test_multi_press_region_does_not_prefer_one_longitudinal_point()
    test_contact_stages_use_press_compatible_alignment()
    test_precise_success_uses_raw_fret_position()
    test_press_precision_components_explain_each_gate()
    test_press_arch_shaping_quality_targets_strict_boundary_continuously()
    test_isolated_press_conjunction_rejects_single_factor_shortcuts()
    test_hold_and_dropout()
    test_large_failure_penalties_keep_reward_bounded()
    test_near_miss_is_diagnostic_only_in_training_config()
    test_class_balance()
    test_static_chord_bottleneck_and_completion_gate()
    test_frozen_context_completion_gate_stays_active_for_all_rows()
    test_chord_bridge_active_finger_bottleneck()
    test_chord_fine_joint_reward_tracks_the_weakest_finger()
    test_goal_pair_anchor_exposes_selected_finger_quality()
    test_goal_pair_anchor_prioritizes_selected_next_goal()
    test_next_goal_gate()
    test_next_goal_progress_is_signed_and_target_safe()
    test_goal_pair_positive_progress_requires_current_press_preservation()
    test_coupling_does_not_tax_closed_gate()
    test_frozen_pose_guide_does_not_mutate_shared_activity()
    test_cached_finger_pose_guide_is_dense_and_strictly_gated()
    test_cached_finger_action_teacher_composes_active_fingers()
    test_cached_consensus_teacher_masks_conflicting_proximal_axes()
    test_transition_quality_requires_preservation_and_penetration_blocks_credit()
    print("PASS: precision, hold/dropout, transition conjunction, safety gate")


if __name__ == "__main__":
    main()
