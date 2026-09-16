"""Executable tests for production Action Residual safety primitives.

Run directly when pytest is unavailable::

    python full/action_residual/tests/test_action_safety.py
"""
from __future__ import annotations

from pathlib import Path
import sys

import torch


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from full.action_residual.action_safety import (  # noqa: E402
    ActionSafetyMasks,
    apply_physical_residual,
    directional_pre_tanh_caps,
    stable_atanh,
)


def _raises(error: type[BaseException], fn) -> None:
    try:
        fn()
    except error:
        return
    raise AssertionError(f"expected {error.__name__}")


def _training_masks(batch: int | None = None) -> ActionSafetyMasks:
    # Residual slots 0, 1, 2 map to non-contiguous joints 0, 3, 5.
    residual_indices = torch.tensor([0, 3, 5], dtype=torch.long)
    authority = torch.tensor([True, False, True])
    execution = torch.tensor([True, True, True, True, False, True])
    if batch is not None:
        authority = authority.unsqueeze(0).expand(batch, -1).clone()
        execution = execution.unsqueeze(0).expand(batch, -1).clone()
    return ActionSafetyMasks.for_training(
        residual_authority_mask=authority,
        stochastic_execution_mask=execution,
        residual_joint_indices=residual_indices,
    )


def test_three_masks_are_independent_and_fail_closed() -> None:
    masks = _training_masks()
    assert masks.residual_dim == 3
    assert masks.joint_dim == 6
    assert torch.equal(
        masks.residual_authority_mask,
        torch.tensor([True, False, True]),
    )
    # Joint 1 represents a stochastic frozen-source finger: it is executed,
    # but the coordinator receives no PPO credit for it.
    assert bool(masks.stochastic_execution_mask[1])
    assert not bool(masks.ppo_credit_mask[1])
    assert torch.equal(
        masks.ppo_credit_mask,
        torch.tensor([True, False, False, False, False, True]),
    )

    indices = torch.tensor([0, 3, 5], dtype=torch.long)
    _raises(TypeError, lambda: ActionSafetyMasks(
        residual_authority_mask=torch.ones(3),
        stochastic_execution_mask=torch.ones(6, dtype=torch.bool),
        ppo_credit_mask=torch.zeros(6, dtype=torch.bool),
        residual_joint_indices=indices,
    ))
    _raises(ValueError, lambda: ActionSafetyMasks(
        residual_authority_mask=torch.tensor([True, False, True]),
        stochastic_execution_mask=torch.tensor(
            [False, True, True, True, False, True]),
        ppo_credit_mask=torch.zeros(6, dtype=torch.bool),
        residual_joint_indices=indices,
    ))
    _raises(ValueError, lambda: ActionSafetyMasks(
        residual_authority_mask=torch.tensor([True, False, True]),
        stochastic_execution_mask=torch.tensor(
            [True, True, True, True, False, True]),
        ppo_credit_mask=torch.tensor(
            [True, True, False, False, False, True]),
        residual_joint_indices=indices,
    ))
    _raises(ValueError, lambda: ActionSafetyMasks(
        residual_authority_mask=torch.tensor([True, False, True]),
        stochastic_execution_mask=torch.ones(6, dtype=torch.bool),
        ppo_credit_mask=torch.zeros(6, dtype=torch.bool),
        residual_joint_indices=torch.tensor([0, 0, 5]),
    ))


def test_directional_cap_respects_physical_radian_limit() -> None:
    torch.manual_seed(101)
    dtype = torch.float64
    base_mean = torch.tensor([
        [-12.0, -1.5, 0.0],
        [12.0, 0.7, 2.3],
        [-0.2, 4.0, -5.0],
        [0.3, -0.9, 1.1],
    ], dtype=dtype)
    raw_residual = torch.tensor([
        [1.0e6, -1.0e6, 1.0e6],
        [-1.0e6, 1.0e6, -1.0e6],
        [9.0, -9.0, 9.0],
        [-9.0, 9.0, -9.0],
    ], dtype=dtype)
    ctrl_mid = torch.tensor([0.4, -0.2, 1.3], dtype=dtype)
    ctrl_half = torch.tensor([0.8, 1.7, 0.35], dtype=dtype)
    action_scale = torch.tensor(1.25, dtype=dtype)
    cap_rad = torch.tensor([0.025, 0.11, 0.0], dtype=dtype)
    masks = ActionSafetyMasks.for_training(
        residual_authority_mask=torch.ones(
            base_mean.shape[0], 3, dtype=torch.bool),
        stochastic_execution_mask=torch.ones(
            base_mean.shape[0], 6, dtype=torch.bool),
        residual_joint_indices=torch.tensor([0, 3, 5], dtype=torch.long),
    )

    result = apply_physical_residual(
        base_mean=base_mean,
        raw_residual=raw_residual,
        cap_rad=cap_rad,
        ctrl_half=ctrl_half,
        action_scale=action_scale,
        masks=masks,
    )
    base_target = (
        ctrl_mid + action_scale * ctrl_half * torch.tanh(base_mean))
    corrected_target = (
        ctrl_mid + action_scale * ctrl_half
        * torch.tanh(result.corrected_mean))
    physical_change = (corrected_target - base_target).abs()

    assert bool((physical_change <= cap_rad + 1e-12).all())
    assert bool((physical_change[:, :2] > 0.0).any())
    # A zero physical cap must remain exactly unchanged.
    assert torch.equal(
        result.bounded_residual[:, 2],
        torch.zeros_like(result.bounded_residual[:, 2]),
    )
    assert bool((result.caps.positive >= 0.0).all())
    assert bool((result.caps.negative >= 0.0).all())


def test_batch_broadcast_scale_and_gradients() -> None:
    dtype = torch.float64
    base = torch.tensor([
        [-2.0, 0.4, 1.0],
        [1.7, -0.8, 0.2],
    ], dtype=dtype)
    raw = torch.tensor([
        [2.0, -3.0, 4.0],
        [-2.0, 3.0, -4.0],
    ], dtype=dtype, requires_grad=True)
    masks = _training_masks()
    result = apply_physical_residual(
        base_mean=base,
        raw_residual=raw,
        cap_rad=torch.tensor([0.08, 0.08, 0.08], dtype=dtype),
        ctrl_half=torch.tensor([[1.0, 2.0, 0.5]], dtype=dtype),
        action_scale=1.0,
        cap_scale=torch.tensor([0.5, 1.0, 0.25], dtype=dtype),
        masks=masks,
    )
    result.corrected_mean.sum().backward()
    assert raw.grad is not None
    assert bool(torch.isfinite(raw.grad).all())
    assert float(raw.grad[:, 1].abs().max()) == 0.0


def test_invalid_numeric_contracts_fail() -> None:
    base = torch.zeros(2, 3)
    masks = _training_masks()
    _raises(ValueError, lambda: directional_pre_tanh_caps(
        base_mean=base,
        cap_rad=torch.tensor([0.1, -0.1, 0.1]),
        ctrl_half=torch.ones(3),
        action_scale=1.0,
    ))
    _raises(ValueError, lambda: directional_pre_tanh_caps(
        base_mean=base,
        cap_rad=torch.ones(3),
        ctrl_half=torch.tensor([1.0, 0.0, 1.0]),
        action_scale=1.0,
    ))
    _raises(ValueError, lambda: directional_pre_tanh_caps(
        base_mean=base,
        cap_rad=torch.ones(3),
        ctrl_half=torch.ones(3),
        action_scale=float("inf"),
    ))
    _raises(ValueError, lambda: directional_pre_tanh_caps(
        base_mean=torch.tensor([[0.0, float("nan"), 0.0]]),
        cap_rad=torch.ones(3),
        ctrl_half=torch.ones(3),
        action_scale=1.0,
    ))
    _raises(ValueError, lambda: apply_physical_residual(
        base_mean=base,
        raw_residual=torch.zeros(2, 2),
        cap_rad=torch.ones(3),
        ctrl_half=torch.ones(3),
        action_scale=1.0,
        masks=masks,
    ))
    _raises(ValueError, lambda: apply_physical_residual(
        base_mean=base,
        raw_residual=torch.zeros_like(base),
        cap_rad=torch.ones(3),
        ctrl_half=torch.ones(3),
        action_scale=1.0,
        cap_scale=1.1,
        masks=masks,
    ))
    clamped = stable_atanh(torch.tensor([-2.0, 0.0, 2.0]))
    assert bool(torch.isfinite(clamped).all())


def main() -> None:
    tests = (
        test_three_masks_are_independent_and_fail_closed,
        test_directional_cap_respects_physical_radian_limit,
        test_batch_broadcast_scale_and_gradients,
        test_invalid_numeric_contracts_fail,
    )
    for test in tests:
        test()
    print(f"{len(tests)} action safety tests passed")


if __name__ == "__main__":
    main()
