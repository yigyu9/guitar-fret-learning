"""Single-sample, tanh-squashed joint policy distribution."""
from __future__ import annotations

from dataclasses import dataclass

import torch
from torch.nn import functional as F


POLICY_DTYPE = torch.float32


def _log_abs_det_jacobian(latent: torch.Tensor) -> torch.Tensor:
    return 2.0 * (
        torch.log(torch.as_tensor(
            2.0, dtype=latent.dtype, device=latent.device))
        - latent - F.softplus(-2.0 * latent)
    )


@dataclass
class JointActionSample:
    """Raw policy action and deterministic inactive-slot override."""

    policy_action: torch.Tensor
    executed_action: torch.Tensor
    latent: torch.Tensor
    log_prob: torch.Tensor


class MaskedJointTanhNormal:
    """One joint Normal with separate execution and PPO-credit masks.

    PPO must store the FP32 pre-tanh ``latent``, ``policy_action``, and its log
    probability; updates call :meth:`log_prob_from_latent`.  The environment
    receives ``executed_action`` after non-executed slots have been replaced
    by the supplied seated-hold action.  A stochastic frozen-source finger may
    be executed while excluded from coordinator log-prob, entropy, and KL
    credit.

    ``active_mask`` is retained as a legacy alias that applies one mask to both
    roles.  Production callers must pass ``stochastic_execution_mask`` and
    ``ppo_credit_mask`` explicitly.
    """

    def __init__(
            self, mean: torch.Tensor, log_std: torch.Tensor,
            active_mask: torch.Tensor | None = None,
            neutral_logits: torch.Tensor | None = None, *,
            stochastic_execution_mask: torch.Tensor | None = None,
            ppo_credit_mask: torch.Tensor | None = None) -> None:
        if mean.ndim != 2:
            raise ValueError("joint mean must have shape [batch, action]")
        if mean.dtype != POLICY_DTYPE:
            raise TypeError(
                "Action Residual policy distributions must use torch.float32; "
                "run tanh/Normal/log-prob outside AMP")
        log_std = torch.as_tensor(
            log_std, dtype=mean.dtype, device=mean.device)
        if log_std.ndim == 1:
            log_std = log_std.unsqueeze(0).expand_as(mean)
        if log_std.shape != mean.shape:
            raise ValueError("log_std must have shape [action] or [batch, action]")
        if active_mask is not None:
            if (stochastic_execution_mask is not None
                    or ppo_credit_mask is not None):
                raise ValueError(
                    "active_mask cannot be combined with separate execution/"
                    "PPO-credit masks")
            stochastic_execution_mask = active_mask
            ppo_credit_mask = active_mask
        elif (stochastic_execution_mask is None
              or ppo_credit_mask is None):
            raise ValueError(
                "provide active_mask or both stochastic_execution_mask and "
                "ppo_credit_mask")

        def prepare_mask(name: str, value: torch.Tensor) -> torch.Tensor:
            if not isinstance(value, torch.Tensor):
                raise TypeError(f"{name} must be a torch.Tensor")
            if value.dtype != torch.bool:
                raise TypeError(f"{name} must have dtype torch.bool")
            result = value.to(device=mean.device)
            if result.ndim == 1:
                result = result.unsqueeze(0).expand_as(mean)
            if result.shape != mean.shape:
                raise ValueError(
                    f"{name} must have shape [action] or [batch, action]")
            return result

        execution_mask = prepare_mask(
            "stochastic_execution_mask", stochastic_execution_mask)
        credit_mask = prepare_mask("ppo_credit_mask", ppo_credit_mask)
        if not execution_mask.any(dim=-1).all():
            raise ValueError(
                "every policy row must execute at least one stochastic action")
        if bool((credit_mask & ~execution_mask).any()):
            raise ValueError("PPO credit must be a subset of execution")
        if neutral_logits is None:
            raise ValueError("neutral_logits must be provided")
        neutral_logits = torch.as_tensor(
            neutral_logits, dtype=mean.dtype, device=mean.device)
        if neutral_logits.shape != (mean.shape[-1],):
            raise ValueError("neutral_logits must match the action dimension")
        if (not torch.isfinite(mean).all()
                or not torch.isfinite(log_std).all()
                or not torch.isfinite(neutral_logits).all()):
            raise ValueError("joint distribution parameters must be finite")

        self.mean = mean
        self.log_std = log_std.clamp(-5.0, 1.0)
        self.stochastic_execution_mask = execution_mask
        self.ppo_credit_mask = credit_mask
        # Compatibility for diagnostics written against the v1 prototype.
        self.active_mask = credit_mask
        self.neutral_logits = neutral_logits
        self.normal = torch.distributions.Normal(mean, self.log_std.exp())

    def log_prob_from_latent(self, latent: torch.Tensor) -> torch.Tensor:
        """Evaluate a rollout sample without inverting its squashed action.

        Full PPO must persist ``JointActionSample.latent`` in FP32 and call
        this method during every update epoch.  Recovering a latent from
        ``tanh(latent)`` is not lossless once the action approaches +/-1.
        """
        if latent.shape != self.mean.shape:
            raise ValueError("latent must match the joint mean shape")
        if latent.dtype != POLICY_DTYPE:
            raise TypeError("stored policy latent must use torch.float32")
        if not torch.isfinite(latent).all():
            raise ValueError("stored policy latent must be finite")
        per_action = (
            self.normal.log_prob(latent) - _log_abs_det_jacobian(latent))
        return per_action.masked_fill(~self.ppo_credit_mask, 0.0).sum(dim=-1)

    def sample(self, deterministic: bool = False) -> JointActionSample:
        latent = self.mean if deterministic else self.normal.sample()
        policy_action = torch.tanh(latent)
        neutral_action = torch.tanh(self.neutral_logits).unsqueeze(0)
        executed_action = torch.where(
            self.stochastic_execution_mask, policy_action, neutral_action)
        return JointActionSample(
            policy_action=policy_action,
            executed_action=executed_action,
            latent=latent,
            log_prob=self.log_prob_from_latent(latent),
        )

    def log_prob(self, policy_action: torch.Tensor) -> torch.Tensor:
        """Diagnostic-only inverse path for non-saturated FP32 actions.

        PPO must use :meth:`log_prob_from_latent`.  This method fails closed
        at exact tanh saturation instead of silently clamping to a different
        latent and producing a corrupt importance ratio.
        """
        if policy_action.shape != self.mean.shape:
            raise ValueError("policy_action must match the joint mean shape")
        if policy_action.dtype != POLICY_DTYPE:
            raise TypeError("policy_action inverse is supported only in FP32")
        if not torch.isfinite(policy_action).all():
            raise ValueError("policy_action must be finite")
        if bool((policy_action.abs() >= 1.0).any()):
            raise ValueError(
                "saturated policy_action cannot be inverted; store and use "
                "the pre-tanh latent")
        return self.log_prob_from_latent(torch.atanh(policy_action))

    def entropy(self) -> torch.Tensor:
        """Monte-Carlo entropy of the active tanh-squashed subspace."""
        latent = self.normal.rsample()
        per_action = (
            self.normal.entropy() + _log_abs_det_jacobian(latent))
        return per_action.masked_fill(~self.ppo_credit_mask, 0.0).sum(dim=-1)
