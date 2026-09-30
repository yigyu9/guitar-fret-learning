"""CPU unit checks for the R1/R2 reward geometry; no Isaac Gym scene required."""
from __future__ import annotations

from pathlib import Path
import sys

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env.rewards.fret import (FretReward, blend_wrong_press_avoidance,
                              cylindrical_pad_depth, multi_scale_approach_reward,
                              fingertip_slip_reward, fret_position_quality,
                              fret_position_inside,
                              fret_requirement_masks,
                              one_sided_pad_distance, released_finger_hover_reward,
                              released_finger_outward_velocity_reward,
                              released_finger_velocity_gate,
                              press_depth_progress, thumb_goal_proximity_gate,
                              update_press_hysteresis,
                              wrong_press_avoidance_reward, wrong_press_mask)


def main():
    x = torch.tensor([0.0, 0.05, 0.10, 0.20, 0.50, 0.90, 0.95, 1.0])
    q = fret_position_quality(x)
    assert q[0] == 0 and q[-1] == 0
    assert torch.all(q[2:6] == 1)
    assert 0 < q[1] < 1 and 0 < q[6] < 1
    assert torch.isclose(q[1], q[6], atol=1e-6)
    assert torch.equal(
        fret_position_inside(x),
        torch.tensor([False, False, True, True, True, True, False, False]))

    d = torch.tensor([0.0, 0.01, 0.02, 0.05, 0.10])
    r = multi_scale_approach_reward(d)
    assert torch.all(r[:-1] > r[1:]) and torch.isclose(r[0], torch.tensor(1.0))
    assert r[-1] > 0.09  # coarse transport gradient remains useful at 10cm

    progress = press_depth_progress(torch.tensor([-0.0063, -0.005, -0.002, 0.001]))
    assert progress[0] == 0 and progress[1] == 0 and progress[-1] == 1
    assert 0 < progress[2] < 1
    gate = thumb_goal_proximity_gate(
        torch.tensor([[0.020, 0.100], [0.090, 0.100], [0.010, 0.010]]),
        torch.tensor([[True, False], [True, False], [False, False]]))
    assert gate[0] == 1 and gate[1] == 0 and gate[2] == 0

    normal = torch.tensor([0.0, 0.0, 1.0])
    radius = 0.0063
    far = one_sided_pad_distance(torch.tensor([0.0, 0.0, 0.010]), normal, radius)
    touching = one_sided_pad_distance(torch.tensor([0.0, 0.0, 0.005]), normal, radius)
    inward = one_sided_pad_distance(torch.tensor([0.0, 0.0, -0.002]), normal, radius)
    assert torch.isclose(far, torch.tensor(0.0037), atol=1e-6)
    assert touching < 2e-6 and inward < 2e-6

    depth, lateral_ok = cylindrical_pad_depth(
        torch.tensor([[0.0, 0.0, 0.0050], [0.0, 0.0, 0.0060],
                      [0.0070, 0.0, 0.0]]), normal, radius)
    assert lateral_ok.tolist() == [True, True, False]
    assert depth[0] > 0.001 and depth[1] < 0.0005

    reward = FretReward.__new__(FretReward)
    reward._sample_alpha = torch.linspace(0.0, 1.0, 5).view(1, 1, 1, -1, 1)
    samples = torch.full((1, 4, 3, 5, 3), 0.1)
    desired_z = reward.PAD_RADIUS + reward.FINE_NORMAL_CLEARANCE
    samples[0, 0, 2, 3:] = torch.tensor([0.0, 0.0, desired_z])
    target = torch.zeros(1, 6, 3)
    direction = torch.zeros(1, 6, 3)
    direction[..., 0] = 1.0
    outward = torch.zeros(1, 6, 3)
    outward[..., 2] = 1.0
    finger_index = torch.zeros(1, 6, dtype=torch.long)
    barre = torch.zeros(1, 6, dtype=torch.bool)
    fine = reward._fine_alignment_metrics(
        samples, target, direction, outward, finger_index, barre)
    assert torch.all(fine["fine_alignment_quality"] > 0.999)
    assert torch.all(fine["fine_center_distance"] < 2e-6)
    samples[0, 0, 2, 3:, 2] = -0.02
    inward_fine = reward._fine_alignment_metrics(
        samples, target, direction, outward, finger_index, barre)
    assert torch.all(inward_fine["fine_normal_quality"] < 1e-5)
    press_fine = reward._fine_alignment_metrics(
        samples, target, direction, outward, finger_index, barre,
        press_compatible=True)
    assert torch.all(press_fine["fine_normal_quality"] > 0.999)
    assert torch.all(press_fine["fine_center_distance"] < 2e-6)

    state = torch.tensor([False, False, True, True])
    depths = torch.tensor([0.0011, 0.0007, 0.0007, 0.0004])
    updated = update_press_hysteresis(state, depths)
    assert updated.tolist() == [True, False, True, False]

    goals = torch.tensor([[4, -1, 0]])
    press_req, no_press_req, dontcare = fret_requirement_masks(goals, max_fret=22)
    assert press_req[0, 0].nonzero().flatten().tolist() == [3]
    assert dontcare[0, 0, :3].all() and no_press_req[0, 0, 4:].all()
    assert no_press_req[0, 1].all() and dontcare[0, 2].all()

    actual = torch.zeros(1, 3, 22, dtype=torch.bool)
    actual[0, 0, 1] = True   # fret 2: lower than target 4, ignored
    assert not wrong_press_mask(actual, no_press_req)[0, 0]
    actual[0, 0, 5] = True   # fret 6: overrides target 4
    actual[0, 0, 12] = True  # fret 13: outside the S0 curriculum still overrides
    actual[0, 1, 8] = True   # any fret violates whole-string NO_PRESS
    wrong = wrong_press_mask(actual, no_press_req)
    assert wrong.tolist() == [[True, True, False]]

    avoid = wrong_press_avoidance_reward(torch.tensor([-0.002, 0.0, 0.001]))
    assert torch.isclose(avoid[0], torch.tensor(1.0))
    assert 0 < avoid[1] < 1 and avoid[2] == 0

    forbidden_depth = torch.tensor(
        [[-0.002, 0.0, 0.0008, 0.001]], requires_grad=True)
    dense_avoidance = wrong_press_avoidance_reward(forbidden_depth)
    avoidance_core = torch.tensor([[0.2, 0.4, 0.6, 0.8]])
    supervised = torch.tensor([[True, True, True, False]])
    actual_wrong = torch.tensor([[False, False, True, False]])
    shaped = blend_wrong_press_avoidance(
        avoidance_core, dense_avoidance, supervised, actual_wrong, 0.4)
    assert torch.allclose(
        shaped, torch.tensor([[0.52, 0.44, 0.0, 0.8]]), atol=1e-6)
    shaped.sum().backward()
    assert forbidden_depth.grad[0, 1] < 0
    assert forbidden_depth.grad[0, 2] == 0
    assert forbidden_depth.grad[0, 3] == 0
    disabled = blend_wrong_press_avoidance(
        avoidance_core, dense_avoidance.detach(),
        supervised, actual_wrong, 0.0)
    assert torch.equal(disabled, torch.tensor([[0.2, 0.4, 0.0, 0.8]]))

    string_start = torch.tensor([[[0.0, 0.0, 0.0], [0.02, 0.0, 0.0]]])
    string_end = torch.tensor([[[0.0, 1.0, 0.0], [0.02, 1.0, 0.0]]])
    tips = torch.tensor([[[0.0, 0.5, 0.0163], [0.02, 0.5, 0.0363],
                          [0.0, 0.5, 0.0763], [0.0, 0.5, 0.20]]])
    gate = torch.tensor([[True, True, True, False]])
    hover, gap, per_finger = released_finger_hover_reward(
        tips, string_start, string_end, gate, pad_radius=0.0063,
        free_gap=0.030, decay_scale=0.040)
    assert torch.allclose(gap[:,:3], torch.tensor([[0.010, 0.030, 0.070]]), atol=1e-5)
    assert torch.isclose(per_finger[0, 0], torch.tensor(1.0))
    assert torch.isclose(per_finger[0, 1], torch.tensor(1.0))
    assert 0 < per_finger[0, 2] < 1
    expected = per_finger[0, :3].mean()
    assert torch.isclose(hover[0], expected)
    no_gate, _, _ = released_finger_hover_reward(
        tips, string_start, string_end, torch.zeros_like(gate))
    assert torch.isclose(no_gate[0], torch.tensor(1.0))

    speed = torch.tensor([[0.05, 0.10, 0.35, 1.0]])
    velocity, velocity_per_finger = released_finger_outward_velocity_reward(
        speed, gate, free_speed=0.10, decay_scale=0.25)
    assert torch.isclose(velocity_per_finger[0, 0], torch.tensor(1.0))
    assert torch.isclose(velocity_per_finger[0, 1], torch.tensor(1.0))
    assert 0 < velocity_per_finger[0, 2] < 1
    assert torch.isclose(velocity, velocity_per_finger[0, :3].mean()[None])
    no_velocity, _ = released_finger_outward_velocity_reward(
        speed, torch.zeros_like(gate))
    assert torch.isclose(no_velocity[0], torch.tensor(1.0))

    velocity_gate = released_finger_velocity_gate(
        torch.tensor([[True, True, True, False]]),
        torch.tensor([[False, False, False, False]]),
        torch.ones(1, 4, dtype=torch.bool),
        torch.tensor([[True, False, False, True]]),
        torch.tensor([[False, True, True, False]]),
        torch.tensor([[0.0, 0.50, 0.10, 0.0]]),
        move_release_time=0.25)
    assert velocity_gate.tolist() == [[True, True, False, False]]
    preparation_gate = released_finger_velocity_gate(
        torch.tensor([[True, True, True, False]]),
        torch.tensor([[False, False, False, False]]),
        torch.ones(1, 4, dtype=torch.bool),
        torch.tensor([[True, False, False, True]]),
        torch.tensor([[False, True, True, False]]),
        torch.tensor([[0.0, 1.20, 0.80, 0.0]]),
        move_release_time=1.0)
    assert preparation_gate.tolist() == [[True, True, False, False]]

    slip_distance = torch.tensor([[0.0, 0.002, 0.005, 0.020]])
    slip_gate = torch.tensor([[True, True, True, False]])
    slip, slip_per_finger = fingertip_slip_reward(
        slip_distance, slip_gate, free_distance=0.002, decay_scale=0.003)
    assert torch.isclose(slip_per_finger[0, 0], torch.tensor(1.0))
    assert torch.isclose(slip_per_finger[0, 1], torch.tensor(1.0))
    assert 0 < slip_per_finger[0, 2] < 1
    assert torch.isclose(slip, slip_per_finger[0, :3].mean()[None])
    no_slip_gate, _ = fingertip_slip_reward(
        slip_distance, torch.zeros_like(slip_gate))
    assert torch.isclose(no_slip_gate[0], torch.tensor(1.0))
    print("PASS: R1/R2 geometry, wrong-press, R18 hover, and R23 slip")


if __name__ == "__main__":
    main()
