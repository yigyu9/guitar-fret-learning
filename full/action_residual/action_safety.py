"""Production safety primitives for the Action Residual policy.

The coordinator predicts a residual in pre-tanh (logit) space, while the
environment ultimately controls a physical PD target.  A fixed logit cap does
not imply a fixed physical limit near tanh saturation, so this module converts
per-joint radian limits into direction-dependent logit limits around the
current frozen-source mean.

The tensors passed to the cap functions are *residual aligned*: callers gather
the 33 residual-owned joints from the 75D joint mean before calling this
module, then scatter ``bounded_residual`` back by the same manifest indices.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Union

import torch


TensorLike = Union[float, torch.Tensor]
DEFAULT_ATANH_EPS = 1e-6


def _require_bool_mask(name: str, value: torch.Tensor) -> torch.Tensor:
    if not isinstance(value, torch.Tensor):
        raise TypeError(f"{name} must be a torch.Tensor")
    if value.dtype != torch.bool:
        raise TypeError(f"{name} must have dtype torch.bool")
    if value.ndim not in (1, 2) or value.shape[-1] == 0:
        raise ValueError(
            f"{name} must have shape [dim] or [batch, dim]")
    if value.ndim == 2 and value.shape[0] == 0:
        raise ValueError(f"{name} batch dimension must not be empty")
    return value


def _mask_batch_size(*masks: torch.Tensor) -> int:
    """Return their broadcast batch size, rejecting ambiguous batches."""
    nontrivial = {mask.shape[0] for mask in masks
                  if mask.ndim == 2 and mask.shape[0] != 1}
    if len(nontrivial) > 1:
        raise ValueError("batched safety masks must use the same batch size")
    return next(iter(nontrivial), 1)


def _expand_mask(mask: torch.Tensor, batch: int) -> torch.Tensor:
    if mask.ndim == 1:
        return mask.unsqueeze(0).expand(batch, -1)
    if mask.shape[0] == batch:
        return mask
    if mask.shape[0] == 1:
        return mask.expand(batch, -1)
    raise ValueError(
        f"mask batch {mask.shape[0]} cannot broadcast to batch {batch}")


@dataclass(frozen=True)
class ActionSafetyMasks:
    """Three independent masks used by execution and PPO.

    Shapes are deliberately different:

    - ``residual_authority_mask`` is residual aligned, ``[..., R]``.
    - ``stochastic_execution_mask`` is joint aligned, ``[..., J]``.
    - ``ppo_credit_mask`` is joint aligned, ``[..., J]``.

    ``residual_joint_indices`` is the name-resolved R-to-J mapping from the
    action manifest.  It makes it possible to prove that an authorised
    residual is actually executed and that PPO never receives credit for a
    frozen source-only joint.  Source fingers may therefore be stochastic at
    execution time while remaining false in ``ppo_credit_mask``.
    """

    residual_authority_mask: torch.Tensor
    stochastic_execution_mask: torch.Tensor
    ppo_credit_mask: torch.Tensor
    residual_joint_indices: torch.Tensor

    def __post_init__(self) -> None:
        authority = _require_bool_mask(
            "residual_authority_mask", self.residual_authority_mask)
        execution = _require_bool_mask(
            "stochastic_execution_mask", self.stochastic_execution_mask)
        credit = _require_bool_mask("ppo_credit_mask", self.ppo_credit_mask)

        if execution.shape[-1] != credit.shape[-1]:
            raise ValueError(
                "stochastic_execution_mask and ppo_credit_mask must have "
                "the same joint dimension")
        if not (authority.device == execution.device == credit.device):
            raise ValueError("all three safety masks must be on one device")

        indices = self.residual_joint_indices
        if not isinstance(indices, torch.Tensor):
            raise TypeError("residual_joint_indices must be a torch.Tensor")
        if indices.dtype != torch.long or indices.ndim != 1:
            raise TypeError(
                "residual_joint_indices must be a 1D torch.long tensor")
        if indices.device != authority.device:
            raise ValueError(
                "residual_joint_indices and safety masks must be on one device")
        if indices.numel() != authority.shape[-1]:
            raise ValueError(
                "residual_joint_indices must match the residual dimension")
        if indices.numel() == 0:
            raise ValueError("residual_joint_indices must not be empty")
        joint_dim = execution.shape[-1]
        if bool(((indices < 0) | (indices >= joint_dim)).any()):
            raise ValueError("residual_joint_indices are outside the joint layout")
        if torch.unique(indices).numel() != indices.numel():
            raise ValueError("residual_joint_indices must be unique")

        batch = _mask_batch_size(authority, execution, credit)
        authority_b = _expand_mask(authority, batch)
        execution_b = _expand_mask(execution, batch)
        credit_b = _expand_mask(credit, batch)
        indices_b = indices.unsqueeze(0).expand(batch, -1)
        authority_joint = torch.zeros_like(execution_b)
        authority_joint.scatter_(1, indices_b, authority_b)

        if bool((authority_joint & ~execution_b).any()):
            raise ValueError(
                "every authorised residual joint must be stochastically executed")
        if bool((credit_b & ~execution_b).any()):
            raise ValueError(
                "PPO credit must be a subset of stochastic execution")
        if bool((credit_b & ~authority_joint).any()):
            raise ValueError(
                "PPO credit may only select authorised residual joints")

    @property
    def residual_dim(self) -> int:
        return self.residual_authority_mask.shape[-1]

    @property
    def joint_dim(self) -> int:
        return self.stochastic_execution_mask.shape[-1]

    @property
    def batch_size(self) -> int:
        return _mask_batch_size(
            self.residual_authority_mask,
            self.stochastic_execution_mask,
            self.ppo_credit_mask,
        )

    def expanded(
            self, batch: int
            ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Return authority, execution, and credit with an explicit batch."""
        if isinstance(batch, bool) or not isinstance(batch, int) or batch <= 0:
            raise ValueError("batch must be a positive integer")
        return (
            _expand_mask(self.residual_authority_mask, batch),
            _expand_mask(self.stochastic_execution_mask, batch),
            _expand_mask(self.ppo_credit_mask, batch),
        )

    def validate_current_profile(
            self, *, source_joint_indices: torch.Tensor,
            new_joint_indices: torch.Tensor, batch: int) -> None:
        """Enforce the 60D-source/15D-new execution semantics.

        Frozen-source joints always execute their source distribution.  A new
        body joint executes stochastically if and only if its residual has
        authority.  PPO credit is exactly the residual authority scattered
        into joint order; it never includes protected source fingers.
        """
        for name, indices in (
                ("source_joint_indices", source_joint_indices),
                ("new_joint_indices", new_joint_indices)):
            if (not isinstance(indices, torch.Tensor)
                    or indices.dtype != torch.long or indices.ndim != 1):
                raise TypeError(f"{name} must be a 1D torch.long tensor")
            if indices.device != self.residual_joint_indices.device:
                raise ValueError(f"{name} and safety masks must share a device")
            if (indices.numel() == 0
                    or bool(((indices < 0) | (indices >= self.joint_dim)).any())
                    or torch.unique(indices).numel() != indices.numel()):
                raise ValueError(f"{name} is not a valid joint index set")
        if bool(torch.isin(source_joint_indices, new_joint_indices).any()):
            raise ValueError("source and new joint sets must be disjoint")
        covered = torch.cat((source_joint_indices, new_joint_indices))
        if (covered.numel() != self.joint_dim
                or torch.unique(covered).numel() != self.joint_dim):
            raise ValueError("source and new joint sets must cover the layout")

        authority, execution, credit = self.expanded(batch)
        indices_b = self.residual_joint_indices.unsqueeze(0).expand(batch, -1)
        authority_joint = torch.zeros_like(execution)
        authority_joint.scatter_(1, indices_b, authority)
        source_joint = torch.zeros_like(execution)
        source_joint[:, source_joint_indices] = True
        new_joint = torch.zeros_like(execution)
        new_joint[:, new_joint_indices] = True
        expected_execution = source_joint | (authority_joint & new_joint)
        if not torch.equal(execution, expected_execution):
            raise ValueError(
                "execution mask must keep every source joint stochastic and "
                "every unauthorized new body joint exactly neutral")
        if not torch.equal(credit, authority_joint):
            raise ValueError(
                "PPO credit mask must equal residual authority in joint order")

    @classmethod
    def for_current_profile(
            cls, *, residual_authority_mask: torch.Tensor,
            residual_joint_indices: torch.Tensor,
            source_joint_indices: torch.Tensor,
            new_joint_indices: torch.Tensor,
            joint_dim: int) -> "ActionSafetyMasks":
        """Construct the fail-closed execution/credit masks used by Full."""
        authority = _require_bool_mask(
            "residual_authority_mask", residual_authority_mask)
        if isinstance(joint_dim, bool) or not isinstance(joint_dim, int):
            raise TypeError("joint_dim must be an integer")
        if joint_dim <= 0:
            raise ValueError("joint_dim must be positive")
        batch = authority.shape[0] if authority.ndim == 2 else 1
        execution = torch.zeros(
            batch, joint_dim, dtype=torch.bool, device=authority.device)
        execution[:, source_joint_indices] = True
        authority_b = _expand_mask(authority, batch)
        residual_b = residual_joint_indices.unsqueeze(0).expand(batch, -1)
        authority_joint = torch.zeros_like(execution)
        authority_joint.scatter_(1, residual_b, authority_b)
        new_selector = torch.zeros_like(execution)
        new_selector[:, new_joint_indices] = True
        execution |= authority_joint & new_selector
        credit = authority_joint
        if authority.ndim == 1:
            execution = execution.squeeze(0)
            credit = credit.squeeze(0)
        result = cls(
            residual_authority_mask=authority,
            stochastic_execution_mask=execution,
            ppo_credit_mask=credit,
            residual_joint_indices=residual_joint_indices,
        )
        result.validate_current_profile(
            source_joint_indices=source_joint_indices,
            new_joint_indices=new_joint_indices,
            batch=batch,
        )
        return result

    @classmethod
    def for_training(
            cls, *, residual_authority_mask: torch.Tensor,
            stochastic_execution_mask: torch.Tensor,
            residual_joint_indices: torch.Tensor) -> "ActionSafetyMasks":
        """Build the standard coordinator-training PPO credit preset.

        Credit is the authority mask scattered into the full joint layout.
        Consequently all authorised coordinator joints receive PPO credit,
        while stochastic frozen-source fingers do not.
        """
        authority = _require_bool_mask(
            "residual_authority_mask", residual_authority_mask)
        execution = _require_bool_mask(
            "stochastic_execution_mask", stochastic_execution_mask)
        if authority.device != execution.device:
            raise ValueError("authority and execution masks must be on one device")
        if not isinstance(residual_joint_indices, torch.Tensor):
            raise TypeError("residual_joint_indices must be a torch.Tensor")
        if (residual_joint_indices.dtype != torch.long
                or residual_joint_indices.ndim != 1):
            raise TypeError(
                "residual_joint_indices must be a 1D torch.long tensor")
        if residual_joint_indices.device != authority.device:
            raise ValueError(
                "residual_joint_indices and masks must be on one device")
        if residual_joint_indices.numel() != authority.shape[-1]:
            raise ValueError(
                "residual_joint_indices must match the residual dimension")
        if bool(((residual_joint_indices < 0)
                 | (residual_joint_indices >= execution.shape[-1])).any()):
            raise ValueError(
                "residual_joint_indices are outside the joint layout")
        if (torch.unique(residual_joint_indices).numel()
                != residual_joint_indices.numel()):
            raise ValueError("residual_joint_indices must be unique")

        batch = _mask_batch_size(authority, execution)
        authority_b = _expand_mask(authority, batch)
        execution_b = _expand_mask(execution, batch)
        credit = torch.zeros_like(execution_b)
        credit.scatter_(
            1,
            residual_joint_indices.unsqueeze(0).expand(batch, -1),
            authority_b,
        )
        # Retain the compact vector ABI when both inputs are unbatched.
        if authority.ndim == 1 and execution.ndim == 1:
            credit = credit.squeeze(0)
        return cls(
            residual_authority_mask=authority,
            stochastic_execution_mask=execution,
            ppo_credit_mask=credit,
            residual_joint_indices=residual_joint_indices,
        )


def stable_atanh(
        value: torch.Tensor, eps: float = DEFAULT_ATANH_EPS) -> torch.Tensor:
    """Numerically stable inverse tanh with an explicit open-interval clamp."""
    if not isinstance(value, torch.Tensor):
        raise TypeError("value must be a torch.Tensor")
    if not value.dtype.is_floating_point:
        raise TypeError("value must have a floating-point dtype")
    if not torch.isfinite(value).all():
        raise ValueError("value must be finite")
    eps = float(eps)
    if not math.isfinite(eps) or not 0.0 < eps < 0.5:
        raise ValueError("eps must be finite and in (0, 0.5)")
    effective_eps = max(eps, float(torch.finfo(value.dtype).eps))
    clipped = value.clamp(-1.0 + effective_eps, 1.0 - effective_eps)
    return 0.5 * (torch.log1p(clipped) - torch.log1p(-clipped))


def _require_float_matrix(name: str, value: torch.Tensor) -> torch.Tensor:
    if not isinstance(value, torch.Tensor):
        raise TypeError(f"{name} must be a torch.Tensor")
    if not value.dtype.is_floating_point:
        raise TypeError(f"{name} must have a floating-point dtype")
    if value.ndim != 2 or value.shape[0] == 0 or value.shape[1] == 0:
        raise ValueError(f"{name} must have shape [batch, residual]")
    if not torch.isfinite(value).all():
        raise ValueError(f"{name} must be finite")
    return value


def _broadcast_numeric(
        name: str, value: TensorLike, reference: torch.Tensor, *,
        nonnegative: bool = False, positive: bool = False,
        unit_interval: bool = False) -> torch.Tensor:
    result = torch.as_tensor(
        value, dtype=reference.dtype, device=reference.device)
    if result.ndim == 0:
        result = result.expand_as(reference)
    elif result.ndim == 1 and result.shape[0] == reference.shape[-1]:
        result = result.unsqueeze(0).expand_as(reference)
    elif result.ndim == 2 and result.shape[-1] == reference.shape[-1]:
        if result.shape[0] == 1:
            result = result.expand_as(reference)
        elif result.shape != reference.shape:
            raise ValueError(
                f"{name} batch dimension does not match the base mean")
    else:
        raise ValueError(
            f"{name} must be scalar, [residual], or [batch, residual]")
    if not torch.isfinite(result).all():
        raise ValueError(f"{name} must be finite")
    if positive and not bool((result > 0.0).all()):
        raise ValueError(f"{name} must be strictly positive")
    if nonnegative and bool((result < 0.0).any()):
        raise ValueError(f"{name} must be non-negative")
    if unit_interval and bool(((result < 0.0) | (result > 1.0)).any()):
        raise ValueError(f"{name} must be in [0, 1]")
    return result


@dataclass(frozen=True)
class DirectionalPreTanhCaps:
    """Positive/negative logit limits aligned with residual-owned joints."""

    positive: torch.Tensor
    negative: torch.Tensor
    normalized_action_cap: torch.Tensor

    def __post_init__(self) -> None:
        positive = _require_float_matrix("positive cap", self.positive)
        negative = _require_float_matrix("negative cap", self.negative)
        normalized = _require_float_matrix(
            "normalized_action_cap", self.normalized_action_cap)
        if positive.shape != negative.shape or positive.shape != normalized.shape:
            raise ValueError("all directional cap tensors must have one shape")
        if not (positive.device == negative.device == normalized.device):
            raise ValueError("all directional cap tensors must be on one device")
        if not (positive.dtype == negative.dtype == normalized.dtype):
            raise ValueError("all directional cap tensors must have one dtype")
        for label, tensor in (
                ("positive cap", positive),
                ("negative cap", negative),
                ("normalized_action_cap", normalized)):
            if bool((tensor < 0.0).any()):
                raise ValueError(f"{label} must be non-negative")


def directional_pre_tanh_caps(
        *, base_mean: torch.Tensor, cap_rad: TensorLike,
        ctrl_half: TensorLike, action_scale: TensorLike,
        eps: float = DEFAULT_ATANH_EPS) -> DirectionalPreTanhCaps:
    """Convert a physical radian cap into directional pre-tanh caps.

    The environment mapping is assumed to be::

        target = ctrl_mid + action_scale * ctrl_half * tanh(mean)

    ``ctrl_mid`` cancels when measuring a target change and is therefore not
    an input.  The returned positive and negative limits are generally
    different because tanh is nonlinear around ``base_mean``.
    """
    base = _require_float_matrix("base_mean", base_mean)
    cap = _broadcast_numeric(
        "cap_rad", cap_rad, base, nonnegative=True)
    half = _broadcast_numeric(
        "ctrl_half", ctrl_half, base, positive=True)
    scale = _broadcast_numeric(
        "action_scale", action_scale, base, positive=True)

    # No action can move farther than two normalized action units.  Capping
    # here also keeps division by an extremely small but valid control range
    # finite without weakening the physical guarantee.
    action_cap = (cap / (half * scale)).clamp(min=0.0, max=2.0)
    if not torch.isfinite(action_cap).all():
        raise ValueError(
            "cap_rad / (ctrl_half * action_scale) must be finite")

    base_action = torch.tanh(base)
    positive = (
        stable_atanh(base_action + action_cap, eps=eps) - base
    ).clamp_min(0.0)
    negative = (
        base - stable_atanh(base_action - action_cap, eps=eps)
    ).clamp_min(0.0)

    # At extreme saturation the open-interval clamp can be farther from the
    # base action than a microscopic requested cap.  Falling back to zero is
    # conservative and preserves the hard physical bound.
    positive_change = (
        torch.tanh(base + positive) - base_action).abs()
    negative_change = (
        torch.tanh(base - negative) - base_action).abs()
    positive = torch.where(
        positive_change <= action_cap, positive, torch.zeros_like(positive))
    negative = torch.where(
        negative_change <= action_cap, negative, torch.zeros_like(negative))
    zero_cap = cap == 0.0
    positive = torch.where(zero_cap, torch.zeros_like(positive), positive)
    negative = torch.where(zero_cap, torch.zeros_like(negative), negative)

    return DirectionalPreTanhCaps(
        positive=positive,
        negative=negative,
        normalized_action_cap=action_cap,
    )


def bound_raw_residual(
        *, raw_residual: torch.Tensor, caps: DirectionalPreTanhCaps,
        masks: ActionSafetyMasks, cap_scale: TensorLike = 1.0) -> torch.Tensor:
    """Smoothly bound a raw residual by sign, authority, and stage scale."""
    raw = _require_float_matrix("raw_residual", raw_residual)
    if raw.shape != caps.positive.shape:
        raise ValueError("raw_residual and directional caps must have one shape")
    if raw.device != caps.positive.device or raw.dtype != caps.positive.dtype:
        raise ValueError(
            "raw_residual and directional caps must share device and dtype")
    if raw.shape[-1] != masks.residual_dim:
        raise ValueError(
            "raw_residual width must match residual_authority_mask")
    authority, _, _ = masks.expanded(raw.shape[0])
    if authority.device != raw.device:
        raise ValueError("safety masks and residual tensors must be on one device")
    stage_scale = _broadcast_numeric(
        "cap_scale", cap_scale, raw,
        nonnegative=True, unit_interval=True)

    magnitude = torch.tanh(raw.abs())
    signed = torch.where(
        raw >= 0.0,
        magnitude * caps.positive,
        -magnitude * caps.negative,
    )
    return torch.where(
        authority, signed * stage_scale, torch.zeros_like(signed))


@dataclass(frozen=True)
class SafeResidualResult:
    """Output of :func:`apply_physical_residual`."""

    bounded_residual: torch.Tensor
    corrected_mean: torch.Tensor
    caps: DirectionalPreTanhCaps


def apply_physical_residual(
        *, base_mean: torch.Tensor, raw_residual: torch.Tensor,
        cap_rad: TensorLike, ctrl_half: TensorLike,
        action_scale: TensorLike, masks: ActionSafetyMasks,
        cap_scale: TensorLike = 1.0,
        eps: float = DEFAULT_ATANH_EPS) -> SafeResidualResult:
    """Apply the complete deterministic residual-mean safety envelope.

    ``base_mean`` and ``raw_residual`` must both be gathered into residual
    order.  This function limits the deterministic mean only; exploration,
    common EMA, velocity, torque, collision, and contact-force safety remain
    separate runtime responsibilities.
    """
    base = _require_float_matrix("base_mean", base_mean)
    raw = _require_float_matrix("raw_residual", raw_residual)
    if raw.shape != base.shape:
        raise ValueError("raw_residual must match base_mean")
    if raw.device != base.device or raw.dtype != base.dtype:
        raise ValueError("raw_residual and base_mean must share device and dtype")
    if base.shape[-1] != masks.residual_dim:
        raise ValueError("base_mean width must match the residual mask")
    caps = directional_pre_tanh_caps(
        base_mean=base,
        cap_rad=cap_rad,
        ctrl_half=ctrl_half,
        action_scale=action_scale,
        eps=eps,
    )
    bounded = bound_raw_residual(
        raw_residual=raw,
        caps=caps,
        masks=masks,
        cap_scale=cap_scale,
    )
    corrected = base + bounded
    if not torch.isfinite(corrected).all():
        raise ValueError("corrected residual mean must be finite")
    return SafeResidualResult(
        bounded_residual=bounded,
        corrected_mean=corrected,
        caps=caps,
    )


__all__ = [
    "ActionSafetyMasks",
    "DEFAULT_ATANH_EPS",
    "DirectionalPreTanhCaps",
    "SafeResidualResult",
    "apply_physical_residual",
    "bound_raw_residual",
    "directional_pre_tanh_caps",
    "stable_atanh",
]
