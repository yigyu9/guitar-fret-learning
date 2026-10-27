"""CPU tensor checks for GuitarEnvBase reset/action/finite contracts."""
from __future__ import annotations

from pathlib import Path
import sys

import isaacgym  # noqa: F401 -- must precede torch
import torch

WORKSPACE = Path(__file__).resolve().parents[2]
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from tab2body.env.base import GuitarEnvBase


def _bare_base(num_envs=8, n_dof=3, num_actions=2):
    """Build the tensor-only portion without starting Isaac Gym."""
    env = object.__new__(GuitarEnvBase)
    env.num_envs = num_envs
    env.n_dof = n_dof
    env.num_actions = num_actions
    env.device = "cpu"
    env.action_scale = 2.0
    env.ctrl_mid = torch.tensor([[0.5, -0.5]]).repeat(num_envs, 1)
    env.ctrl_half = torch.tensor([[1.0, 2.0]]).repeat(num_envs, 1)
    env.prev_action = torch.zeros(num_envs, num_actions)
    env.pd_target = torch.zeros(num_envs * n_dof)
    env.applied_tau = torch.zeros(num_envs, n_dof)
    env.dof_state = torch.zeros(num_envs * n_dof, 2)
    env.root_state = torch.zeros(num_envs * 3, 13)
    env.body_state = torch.zeros(num_envs * 5, 13)
    env.contact_force = torch.zeros(num_envs * 5, 3)
    env._bpe = 5
    env.progress_buf = torch.zeros(num_envs, dtype=torch.long)
    env.max_episode_length = 100
    for name in ("_nonfinite_action_state", "_nonfinite_dof_pos",
                 "_nonfinite_dof_vel", "_nonfinite_root_state",
                 "_nonfinite_body_state", "_nonfinite_contact_force"):
        setattr(env, name, torch.zeros(num_envs, dtype=torch.bool))
    env.last_nonfinite_observation = torch.zeros(num_envs, dtype=torch.bool)
    return env


def test_inverse_action_round_trip():
    env = _bare_base()
    target = torch.tensor([[1.1, -1.7]]).repeat(env.num_envs, 1)
    action = env.actions_for_pd_targets(target)
    reconstructed = env.ctrl_mid + env.action_scale * action * env.ctrl_half
    assert torch.allclose(reconstructed, target, atol=1e-7)

    ids = torch.tensor([1, 4, 7])
    subset = target[ids]
    subset_action = env.actions_for_pd_targets(subset, ids)
    subset_reconstructed = (
        env.ctrl_mid[ids] + env.action_scale * subset_action * env.ctrl_half[ids])
    assert torch.allclose(subset_reconstructed, subset, atol=1e-7)


def test_finite_helpers():
    value = torch.tensor([[1.0, float("nan")],
                          [float("inf"), 2.0],
                          [3.0, 4.0]])
    assert GuitarEnvBase.rows_with_nonfinite(value).tolist() == [True, True, False]
    safe = GuitarEnvBase.sanitize_finite(value, fill=-3.0)
    assert torch.isfinite(safe).all()
    assert safe.tolist() == [[1.0, -3.0], [-3.0, 2.0], [3.0, 4.0]]


def test_named_termination_reasons():
    env = _bare_base()
    ds = env.dof_state.view(env.num_envs, env.n_dof, 2)
    ds[0, 0, 0] = float("nan")
    ds[1, 0, 1] = float("inf")
    ds[2, 0, 1] = 51.0
    env.root_state.view(env.num_envs, -1, 13)[3, 0, 0] = float("nan")
    env.body_state.view(env.num_envs, -1, 13)[4, 0, 0] = float("inf")
    env.contact_force.view(env.num_envs, -1, 3)[5, 0, 0] = float("nan")
    env._nonfinite_action_state[6] = True
    env.last_nonfinite_observation[6] = True
    env.progress_buf[7] = env.max_episode_length

    reasons = env.termination_reasons()
    expected_keys = {
        "timeout", "nonfinite_dof_pos", "nonfinite_dof_vel",
        "nonfinite_root_state", "nonfinite_body_state",
        "nonfinite_contact_force", "nonfinite_action_state",
        "nonfinite_observation",
        "velocity_blowup", "base_termination",
    }
    assert set(reasons) == expected_keys
    assert reasons["nonfinite_dof_pos"].tolist() == [True] + [False] * 7
    assert reasons["nonfinite_dof_vel"][1]
    assert reasons["velocity_blowup"][2]
    assert reasons["nonfinite_root_state"][3]
    assert reasons["nonfinite_body_state"][4]
    assert reasons["nonfinite_contact_force"][5]
    assert reasons["nonfinite_action_state"][6]
    assert reasons["nonfinite_observation"][6]
    assert reasons["timeout"][7]
    assert reasons["base_termination"].all()
    assert torch.equal(env.check_termination(), reasons["base_termination"])


def main():
    test_inverse_action_round_trip()
    test_finite_helpers()
    test_named_termination_reasons()
    print("PASS: base inverse-action and non-finite termination contracts")


if __name__ == "__main__":
    main()
