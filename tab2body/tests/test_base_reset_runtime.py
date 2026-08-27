"""GPU regression for hard-limit RSI resets, EMA reset state and finite guards."""
from __future__ import annotations

from pathlib import Path
import sys

import isaacgym  # noqa: F401 -- must precede torch
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cfg import FRET
from env.tasks import FretTask


def _assert_reset_contract(env, tolerance=2e-6):
    ds = env.dof_state.view(env.num_envs, env.n_dof, 2)
    q = ds[:, :, 0]
    lo = env.dof_lower.view(env.num_envs, env.n_dof)
    hi = env.dof_upper.view(env.num_envs, env.n_dof)
    # PhysX may settle a hard-limit joint by sub-microradian numerical tolerance during the
    # single refresh step used by env.reset(); reset_idx itself is exactly clamped.
    assert (q >= lo - tolerance).all(), float((lo - q).clamp_min(0).max())
    assert (q <= hi + tolerance).all(), float((q - hi).clamp_min(0).max())
    assert torch.isfinite(q).all() and torch.isfinite(ds[:, :, 1]).all()

    q_ctrl = q[:, env.ctrl_idx]
    reconstructed = (
        env.ctrl_mid + env.action_scale * env.prev_action * env.ctrl_half
    ).clamp(env.ctrl_lo, env.ctrl_hi)
    assert torch.allclose(reconstructed, q_ctrl, atol=2e-6), float(
        (reconstructed - q_ctrl).abs().max())
    pd = env.pd_target.view(env.num_envs, env.n_dof)
    assert torch.allclose(pd, q, atol=1e-7), float((pd - q).abs().max())


def main():
    env = FretTask(
        FRET["goal_path"], FRET["hand_targets_path"], num_envs=128,
        device=FRET["device"], headless=True, reset_noise=0.02,
        random_start=False, preparation_frames=60)
    try:
        env.reset()
        all_ids = torch.arange(env.num_envs, device=env.device)
        assert torch.all(env.init_pose >= env.dof_lower[:env.n_dof] - 1e-7)
        assert torch.all(env.init_pose <= env.dof_upper[:env.n_dof] + 1e-7)
        # env.reset() deliberately performs one physics refresh, after which gravity may move a
        # free joint slightly away from its reset target.  Validate the exact reset_idx contract
        # below, before another physics step.
        q_after_refresh = env.dof_state.view(env.num_envs, env.n_dof, 2)[:, :, 0]
        lo = env.dof_lower.view(env.num_envs, env.n_dof)
        hi = env.dof_upper.view(env.num_envs, env.n_dof)
        assert (q_after_refresh >= lo - 2e-6).all()
        assert (q_after_refresh <= hi + 2e-6).all()

        # Repeated RSI draws used to put every batch outside a finger hard limit.
        for _ in range(16):
            env.reset_idx(all_ids)
            _assert_reset_contract(env)

        # A command matching the reset pose must be a true hold through the EMA.
        before = env.pd_target.view(env.num_envs, env.n_dof)[:, env.ctrl_idx].clone()
        hold_action = env.prev_action.clone()
        env.apply_actions(hold_action)
        after = env.pd_target.view(env.num_envs, env.n_dof)[:, env.ctrl_idx]
        assert torch.allclose(after, before, atol=2e-6), float((after - before).abs().max())

        # The standard authored-init action removes only the bounded RSI offset
        # plus the sub-milliradian one-step settling displacement, rather than
        # jumping shoulder/finger targets by tens of degrees from action zero.
        env.reset_idx(all_ids)
        reset_q = env.dof_state.view(env.num_envs, env.n_dof, 2)[
            :, env.ctrl_idx, 0].clone()
        init_targets = env.init_pose[env.ctrl_idx][None].expand(env.num_envs, -1)
        init_action = env.actions_for_pd_targets(init_targets)
        env.apply_actions(init_action)
        first_target = env.pd_target.view(env.num_envs, env.n_dof)[
            :, env.ctrl_idx]
        max_first_shift = float((first_target - reset_q).abs().max())
        settling_tolerance = 1e-3
        assert max_first_shift <= ((1.0 - env.action_alpha)
                                   * (env.reset_noise + settling_tolerance)), \
            max_first_shift

        # Non-finite policy commands terminate only their own environments and never reach PD.
        env.reset_idx(all_ids)
        action = env.prev_action.clone()
        action[0, 0] = float("nan")
        action[1, 1] = float("inf")
        env.pd_target.view(env.num_envs, env.n_dof)[4, 0] = float("inf")
        env.applied_tau[5, 0] = float("nan")
        env.apply_actions(action)
        reasons = env.termination_reasons()
        assert reasons["nonfinite_action_state"][:2].all()
        assert reasons["nonfinite_action_state"][4:6].all()
        expected_action_failures = torch.zeros(
            env.num_envs, dtype=torch.bool, device=env.device)
        expected_action_failures[[0, 1, 4, 5]] = True
        assert torch.equal(
            reasons["nonfinite_action_state"], expected_action_failures)
        assert torch.isfinite(env.prev_action).all()
        assert torch.isfinite(env.pd_target).all()
        assert torch.isfinite(env.applied_tau).all()

        # Invalid simulator DOFs are latched by cause and made finite before reward/obs math.
        env.reset_idx(all_ids)
        ds = env.dof_state.view(env.num_envs, env.n_dof, 2)
        ds[2, 0, 0] = float("nan")
        ds[3, 0, 1] = float("inf")
        env._capture_and_sanitize_dof_state()
        reasons = env.termination_reasons()
        assert reasons["nonfinite_dof_pos"][2]
        assert reasons["nonfinite_dof_vel"][3]
        assert torch.isfinite(ds[2:4]).all()

        adjusted = torch.nonzero(
            env.init_pose_limit_adjustment.abs() > 1e-8).numel()
        print({
            "authored_init_dofs_clamped": int(adjusted),
            "max_first_target_shift_rad": max_first_shift,
            "reset_batches_checked": 17,
        })
    finally:
        env.close()
    print("PASS: hard-limit reset, EMA hold and non-finite runtime guards")


if __name__ == "__main__":
    main()
