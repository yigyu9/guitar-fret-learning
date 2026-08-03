"""CPU checks for flexible MCP/PIP/DIP arch shaping."""
from pathlib import Path
import sys

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env.rewards.fret import (
    adjacent_finger_action_synergy,
    adjacent_finger_coupling_reward,
    apply_finger_arch_shaping,
    finger_arch_quality,
    finger_synergy_follower_mask,
    released_finger_pose_reward,
)


def main():
    deg = torch.pi / 180.0
    straight = finger_arch_quality(
        torch.tensor([0.0]), torch.tensor([0.0]), torch.tensor([0.0]))
    natural_a = finger_arch_quality(
        torch.tensor([35.0 * deg]), torch.tensor([55.0 * deg]),
        torch.tensor([30.0 * deg]))
    natural_b = finger_arch_quality(
        torch.tensor([65.0 * deg]), torch.tensor([80.0 * deg]),
        torch.tensor([50.0 * deg]))
    reversed_pose = finger_arch_quality(
        torch.tensor([-35.0 * deg]), torch.tensor([-10.0 * deg]),
        torch.tensor([-5.0 * deg]))
    assert natural_a.item() > 0.9
    assert natural_b.item() > 0.85
    assert natural_a.item() > straight.item()
    assert natural_a.item() > reversed_pose.item()
    neutral_pip = torch.tensor([0.0], requires_grad=True)
    finger_arch_quality(
        torch.tensor([35.0 * deg]), neutral_pip,
        torch.tensor([0.0])).sum().backward()
    assert neutral_pip.grad.item() > 0.0, (
        "neutral PIP pose must have a positive learning gradient")

    base = torch.tensor([0.5, 0.5, 0.5])
    shaped = apply_finger_arch_shaping(
        base, torch.tensor([1.0, 0.0, 1.0]),
        torch.tensor([0.01, 0.01, 0.25]),
        torch.tensor([True, True, True]), weight=0.10)
    assert shaped[0] > base[0]
    assert shaped[1] < base[1]
    assert torch.isclose(shaped[2], 0.9 * base[2], atol=1e-6)
    inactive = apply_finger_arch_shaping(
        base, torch.ones(3), torch.zeros(3),
        torch.zeros(3, dtype=torch.bool), weight=0.10)
    assert torch.equal(inactive, base)

    anchor = torch.deg2rad(torch.tensor([[[40.0, 55.0, 30.0]]]))
    gate = torch.tensor([[True]])
    held, _, held_error = released_finger_pose_reward(
        anchor, anchor, torch.zeros(1, 1), gate)
    assert torch.isclose(held[0], torch.tensor(1.0))
    relaxed = torch.deg2rad(torch.tensor([[[40.0, 25.0, 10.0]]]))
    eased, _, eased_error = released_finger_pose_reward(
        relaxed, anchor, torch.full((1, 1), 0.30), gate)
    assert torch.isclose(eased[0], torch.tensor(1.0), atol=1e-6)
    straight_release, _, _ = released_finger_pose_reward(
        torch.zeros_like(anchor), anchor, torch.zeros(1, 1), gate)
    assert straight_release[0] < held[0]
    assert held_error[0, 0] == 0 and eased_error[0, 0] < 1e-5

    deg = torch.pi / 180.0
    velocity = torch.zeros(1, 4, 3)
    velocity[0, 1] = 60.0 * deg
    velocity[0, 0] = 9.0 * deg
    velocity[0, 2] = 12.0 * deg
    followers = torch.tensor([[True, False, True, False]])
    coupled, _, coupling_gate, target_speed = (
        adjacent_finger_coupling_reward(
            velocity, followers, torch.tensor([True])))
    assert coupled[0] > 0.99
    assert coupling_gate.tolist() == [[True, False, True, False]]
    assert torch.allclose(
        target_speed[0, [0, 2]], torch.tensor([9.0, 12.0]), atol=1e-5)
    stationary = velocity.clone()
    stationary[0, 0] = 0.0
    stationary[0, 2] = 0.0
    uncoupled, _, _, _ = adjacent_finger_coupling_reward(
        stationary, followers, torch.tensor([True]))
    assert uncoupled[0] == 0.0
    unprotected, _, protected_gate, _ = adjacent_finger_coupling_reward(
        velocity, followers, torch.tensor([False]))
    assert unprotected[0] == 0.0 and not protected_gate.any()

    actions = torch.zeros(1, 12)
    previous = torch.zeros_like(actions)
    indices = torch.arange(12).reshape(4, 3)
    actions[:, indices[1]] = 0.10
    follower_allowed = torch.tensor([[True, False, True, True]])
    coupled_actions, induced_deg, action_gate = (
        adjacent_finger_action_synergy(
            actions, previous, indices, follower_allowed,
            torch.ones(12), coefficients=(0.10, 0.15, 0.18),
            min_driver_delta_deg=0.25,
            full_driver_delta_deg=1.50,
            max_induced_delta_deg=1.50))
    assert action_gate.tolist() == [[True, False, True, False]]
    assert torch.all(coupled_actions[:, indices[0]] > 0.0)
    assert torch.all(coupled_actions[:, indices[2]] > 0.0)
    assert torch.equal(
        coupled_actions[:, indices[1]], actions[:, indices[1]])
    assert induced_deg[0, 2] > induced_deg[0, 0] > 0.0

    events = torch.zeros(1, 4, 13)
    events[0, 3, 8] = 1.0
    events[0, 3, 11] = 1.0
    active = torch.tensor([[True, False, False, False]])
    protected_followers = finger_synergy_follower_mask(active, events)
    assert protected_followers.tolist() == [[False, True, True, False]]
    actions = torch.zeros(1, 12)
    actions[:, indices[2]] = 0.10
    protected_actions, _, protected_gate = adjacent_finger_action_synergy(
        actions, previous, indices, protected_followers,
        torch.ones(12), coefficients=(0.10, 0.15, 0.18),
        min_driver_delta_deg=0.25,
        full_driver_delta_deg=1.50,
        max_induced_delta_deg=1.50)
    assert not protected_gate[0, 0]
    assert not protected_gate[0, 3]
    assert torch.equal(
        protected_actions[:, indices[3]], actions[:, indices[3]])
    print("PASS: broad natural arch plateau beats straight/reversed poses")


if __name__ == "__main__":
    main()
