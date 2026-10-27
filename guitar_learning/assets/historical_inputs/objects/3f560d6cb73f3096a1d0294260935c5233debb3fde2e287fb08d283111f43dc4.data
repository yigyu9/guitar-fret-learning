"""모든 신규 fret 정책의 손가락 굽힘 초기화 계약."""
from pathlib import Path
import copy
import sys

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from learning.models import ActorCritic, configure_finger_flexion_policy


def main():
    fingers = ("index", "middle", "ring", "pinky")
    names = [
        name
        for finger in fingers
        for name in (f"LH:{finger}1_x", f"LH:{finger}2", f"LH:{finger}3")
    ]
    model = ActorCritic(5, len(names), 1, actor_hidden=(8,),
                        critic_hidden=(8,), init_std=0.02,
                        init_mean=torch.zeros(len(names)))
    indices = configure_finger_flexion_policy(
        model, names, torch.zeros(len(names)), torch.ones(len(names)), 1.0,
        exploration_std=0.08, pip_degrees=15.0, dip_degrees=10.0)
    assert indices == list(range(12))
    assert torch.allclose(
        model.log_std.exp(), torch.full((12,), 0.08), atol=1e-7)

    action = torch.tanh(model.actor(torch.zeros(1, 5)))[0]
    for index, name in enumerate(names):
        if name.endswith("2"):
            expected = torch.tensor(15.0 * torch.pi / 180.0)
        elif name.endswith("3"):
            expected = torch.tensor(10.0 * torch.pi / 180.0)
        else:
            expected = torch.tensor(0.0)
        assert torch.isclose(action[index], expected, atol=1e-6), (
            name, action[index], expected)

    thumb_names = [
        "LH:thumb1_x", "LH:thumb1_y", "LH:thumb1_z",
        "LH:thumb2", "LH:thumb3"]
    full_names = thumb_names + names
    thumb_model = ActorCritic(
        5, len(full_names), 1, actor_hidden=(8,), critic_hidden=(8,),
        init_std=0.02, init_mean=torch.zeros(len(full_names)))
    thumb_output_before = thumb_model.actor[-1].weight[:5].clone()
    thumb_bias_before = thumb_model.actor[-1].bias[:5].clone()
    configure_finger_flexion_policy(
        thumb_model, full_names, torch.zeros(len(full_names)),
        torch.ones(len(full_names)), 1.0,
        exploration_std=0.08, pip_degrees=15.0, dip_degrees=10.0,
        thumb_exploration_std=0.07,
        thumb_base_exploration_std=0.20)
    assert torch.allclose(
        thumb_model.log_std[:3].exp(), torch.full((3,), 0.20), atol=1e-7)
    assert torch.allclose(
        thumb_model.log_std[3:5].exp(), torch.full((2,), 0.07), atol=1e-7)
    assert torch.allclose(
        thumb_model.log_std[5:].exp(), torch.full((12,), 0.08), atol=1e-7)
    assert torch.equal(
        thumb_model.actor[-1].weight[:5], thumb_output_before)
    assert torch.equal(
        thumb_model.actor[-1].bias[:5], thumb_bias_before)

    repair_model = ActorCritic(
        5, len(full_names), 1, actor_hidden=(4,), critic_hidden=(4,),
        init_std=0.11, init_mean=torch.zeros(len(full_names)))
    with torch.no_grad():
        repair_model.actor[0].weight.zero_()
        repair_model.actor[0].bias.fill_(0.5)
        output = repair_model.actor[-1]
        output.weight.normal_(mean=0.0, std=0.1)
        output.bias.normal_(mean=0.0, std=0.1)
        output.weight[0].zero_()
        output.weight[0, 0] = 4.0
        output.bias[0] = 0.0
        output.weight[1].zero_()
        output.weight[1, 0] = 0.5
        output.bias[1] = 0.0
        output.weight[2].zero_()
        output.weight[2, 0] = -4.0
        output.bias[2] = 0.0
    neutral = torch.zeros(1, repair_model.obs_dim)
    before_action = torch.tanh(repair_model.actor(neutral))[0]
    assert before_action[0] > 0.8
    assert before_action[2] < -0.8
    assert before_action[1].abs() < 0.8
    weight_before = repair_model.actor[-1].weight.clone()
    bias_before = repair_model.actor[-1].bias.clone()
    std_before = repair_model.log_std.clone()
    probe = torch.randn(9, repair_model.obs_dim)
    probe_before = repair_model.actor(probe).detach().clone()
    axis_model = copy.deepcopy(repair_model)

    configure_finger_flexion_policy(
        repair_model, full_names, torch.zeros(len(full_names)),
        torch.ones(len(full_names)), 1.0,
        exploration_std=0.08, pip_degrees=15.0, dip_degrees=10.0,
        seed_mean=False, repair_saturated_thumb_base=True)
    after_action = torch.tanh(repair_model.actor(neutral))[0]
    assert torch.isclose(after_action[0], torch.tensor(0.8), atol=1e-6)
    assert torch.isclose(after_action[2], torch.tensor(-0.8), atol=1e-6)
    assert torch.equal(repair_model.actor[-1].weight, weight_before)
    assert torch.equal(repair_model.actor[-1].bias[1], bias_before[1])
    assert torch.equal(repair_model.actor[-1].bias[3:], bias_before[3:])
    assert not torch.equal(repair_model.actor[-1].bias[0], bias_before[0])
    assert not torch.equal(repair_model.actor[-1].bias[2], bias_before[2])
    probe_after = repair_model.actor(probe).detach()
    bias_shift = repair_model.actor[-1].bias - bias_before
    assert torch.allclose(
        probe_after - probe_before,
        bias_shift[None].expand_as(probe_after),
        atol=1e-6, rtol=1e-6)
    assert torch.equal(repair_model.log_std, std_before)

    axis_weight_before = axis_model.actor[-1].weight.clone()
    axis_bias_before = axis_model.actor[-1].bias.clone()
    axis_before = torch.tanh(axis_model.actor(neutral))[0].clone()
    configure_finger_flexion_policy(
        axis_model, full_names, torch.zeros(len(full_names)),
        torch.ones(len(full_names)), 1.0,
        exploration_std=0.08, pip_degrees=15.0, dip_degrees=10.0,
        seed_mean=False, repair_saturated_thumb_base=True,
        thumb_base_action_limit=(0.85, 0.98, 0.98))
    axis_after = torch.tanh(axis_model.actor(neutral))[0]
    assert torch.isclose(axis_after[0], torch.tensor(0.85), atol=1e-6)
    assert torch.equal(axis_after[1:3], axis_before[1:3])
    assert torch.equal(axis_model.actor[-1].weight, axis_weight_before)
    assert not torch.equal(axis_model.actor[-1].bias[0], axis_bias_before[0])
    assert torch.equal(
        axis_model.actor[-1].bias[1:], axis_bias_before[1:])
    print(
        "PASS: finger/thumb std floors and opt-in thumb saturation repair")


if __name__ == "__main__":
    main()
