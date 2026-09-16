"""Action-level coordinator that never reads source hidden activations."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
import math
from typing import Optional

import torch
from torch import nn

from .action_safety import (
    ActionSafetyMasks,
    DirectionalPreTanhCaps,
    apply_physical_residual,
)
from .checkpoint_utils import validate_finite_state_dict
from .config import ActionResidualConfig
from .context_encoding import GUITAR_SUPPORT_MANIFEST, READINESS_MANIFEST
from .distribution import MaskedJointTanhNormal
from .goal_encoder import GoalScoreBatch, GoalScoreEncoder
from .manifest import ActionResidualManifest
from .source_adapter import SourceProposal
from .source_intent import SourceIntentCalibration, SourceIntentNormalizer


def _encoder(input_dim: int, hidden_dim: int, output_dim: int) -> nn.Sequential:
    return nn.Sequential(
        nn.Linear(input_dim, hidden_dim),
        nn.ELU(),
        nn.Linear(hidden_dim, output_dim),
        nn.ELU(),
    )


def _initialize_hidden(module: nn.Module) -> None:
    for layer in module.modules():
        if isinstance(layer, nn.Linear):
            nn.init.orthogonal_(layer.weight, gain=2 ** 0.5)
            nn.init.zeros_(layer.bias)


@dataclass
class ActionResidualOutput:
    base_mean: torch.Tensor
    raw_residual: torch.Tensor
    bounded_residual: torch.Tensor
    joint_residual: torch.Tensor
    joint_mean: torch.Tensor
    fusion_feature: torch.Tensor
    directional_caps: Optional[DirectionalPreTanhCaps] = None
    safety_masks: Optional[ActionSafetyMasks] = None


class ActionResidualCoordinator(nn.Module):
    """Compose frozen source means and a bounded, named action residual.

    The model has no API for source hidden activations.  This is the deliberate
    architectural boundary between this package and a future Latent Sync model.
    All four context tensors are expected to be packed, scaled, and clipped by
    the Full runtime according to the checkpointed context manifest.
    """

    def __init__(
            self, manifest: ActionResidualManifest,
            config: Optional[ActionResidualConfig] = None,
            source_intent_calibration: Optional[
                SourceIntentCalibration] = None) -> None:
        super().__init__()
        self.manifest = manifest
        self.config = config or ActionResidualConfig()
        self.manifest.validate_current_75d_profile(
            self.config.joint_context_dim)
        self.architecture_id = manifest.architecture_id
        self.source_intent_normalizer = SourceIntentNormalizer(
            manifest, source_intent_calibration)

        # The production path accepts semantic current+future score events.
        # The pre-encoded flat path remains available for contract tests and
        # controlled ablations, but must use this module's schema in Full.
        self.goal_score_encoder = GoalScoreEncoder()
        self.action_encoder = _encoder(
            manifest.fret_action_dim + manifest.strike_action_dim,
            self.config.small_encoder_hidden_dim,
            self.config.action_feature_dim)
        self.goal_encoder = _encoder(
            self.config.goal_context_dim,
            self.config.small_encoder_hidden_dim,
            self.config.goal_feature_dim)
        self.readiness_encoder = _encoder(
            self.config.readiness_context_dim,
            self.config.small_encoder_hidden_dim,
            self.config.readiness_feature_dim)
        self.joint_encoder = _encoder(
            self.config.joint_context_dim,
            self.config.joint_encoder_hidden_dim,
            self.config.joint_feature_dim)
        self.guitar_encoder = _encoder(
            self.config.guitar_context_dim,
            self.config.small_encoder_hidden_dim,
            self.config.guitar_feature_dim)

        fusion_a, fusion_b = self.config.fusion_hidden_dims
        self.fusion = nn.Sequential(
            nn.Linear(self.config.fusion_input_dim, fusion_a),
            nn.ELU(),
            nn.Linear(fusion_a, fusion_b),
            nn.ELU(),
        )
        self.arm_head = nn.Sequential(
            nn.Linear(fusion_b, self.config.residual_head_hidden_dim),
            nn.ELU(),
            nn.Linear(
                self.config.residual_head_hidden_dim,
                len(manifest.arm_residual_names)),
        )
        self.body_head = nn.Sequential(
            nn.Linear(fusion_b, self.config.residual_head_hidden_dim),
            nn.ELU(),
            nn.Linear(
                self.config.residual_head_hidden_dim,
                len(manifest.body_residual_names)),
        )

        for module in (
                self.action_encoder, self.goal_encoder,
                self.readiness_encoder, self.joint_encoder,
                self.guitar_encoder, self.fusion,
                self.arm_head, self.body_head):
            _initialize_hidden(module)
        for head in (self.arm_head, self.body_head):
            nn.init.zeros_(head[-1].weight)
            nn.init.zeros_(head[-1].bias)

        self.register_buffer(
            "fret_indices",
            torch.tensor(
                manifest.indices(manifest.fret_action_names), dtype=torch.long),
            persistent=False)
        self.register_buffer(
            "strike_indices",
            torch.tensor(
                manifest.indices(manifest.strike_action_names), dtype=torch.long),
            persistent=False)
        self.register_buffer(
            "residual_indices",
            torch.tensor(
                manifest.indices(manifest.residual_action_names),
                dtype=torch.long),
            persistent=False)
        self.register_buffer(
            "new_action_indices",
            torch.tensor(
                manifest.indices(manifest.new_action_names), dtype=torch.long),
            persistent=False)
        self.register_buffer(
            "neutral_logits",
            torch.tensor(manifest.neutral_logits, dtype=torch.float32),
            persistent=False)
        self.register_buffer(
            "residual_caps",
            torch.tensor(manifest.residual_caps, dtype=torch.float32),
            persistent=False)
        self.new_log_std = nn.Parameter(torch.full(
            (len(manifest.new_action_names),),
            math.log(self.config.initial_new_action_std),
            dtype=torch.float32))

    @property
    def joint_action_dim(self) -> int:
        return self.manifest.joint_action_dim

    @property
    def residual_dim(self) -> int:
        return self.manifest.residual_dim

    def _apply(self, fn, recurse: bool = True):
        reference = next(self.parameters(), None)
        if reference is not None:
            probe = torch.empty(
                0, dtype=torch.float32, device=reference.device)
            if fn(probe).dtype != torch.float32:
                raise TypeError(
                    "Action Residual coordinator must remain torch.float32")
        return super()._apply(fn, recurse=recurse)

    @staticmethod
    def _check_input(
            name: str, value: torch.Tensor, batch: int, width: int) -> None:
        if value.ndim != 2 or value.shape != (batch, width):
            raise ValueError(
                f"{name} must have shape {(batch, width)}, got "
                f"{tuple(value.shape)}")
        if value.dtype != torch.float32:
            raise TypeError(f"{name} must use torch.float32")
        if not torch.isfinite(value).all():
            raise ValueError(f"{name} must be finite")

    def _base_mean(
            self, fret_mean: torch.Tensor,
            strike_mean: torch.Tensor) -> torch.Tensor:
        batch = fret_mean.shape[0]
        base = self.neutral_logits.to(
            dtype=fret_mean.dtype, device=fret_mean.device
        ).unsqueeze(0).expand(batch, -1).clone()
        base = base.scatter(
            1, self.fret_indices.unsqueeze(0).expand(batch, -1), fret_mean)
        base = base.scatter(
            1, self.strike_indices.unsqueeze(0).expand(batch, -1), strike_mean)
        return base

    def _validate_source_proposal(
            self, label: str, proposal: SourceProposal,
            expected_names: tuple[str, ...], expected_sha256: str) -> None:
        if not isinstance(proposal, SourceProposal):
            raise TypeError(f"{label}_proposal must be a SourceProposal")
        if proposal.action_names != expected_names:
            raise ValueError(
                f"{label} source action names/order do not match the manifest")
        if proposal.checkpoint_sha256 != expected_sha256:
            raise ValueError(
                f"{label} source checkpoint SHA-256 does not match the manifest")

    def forward(
            self, *, fret_proposal: SourceProposal,
            strike_proposal: SourceProposal,
            goal_context: torch.Tensor, readiness_context: torch.Tensor,
            joint_context: torch.Tensor, guitar_context: torch.Tensor,
            authority_mask: Optional[torch.Tensor] = None,
            cap_scale: Optional[torch.Tensor] = None) -> ActionResidualOutput:
        """Return a bounded pre-tanh residual and the composed joint mean.

        Runtime masks may only remove authority.  ``cap_scale`` is constrained
        to [0, 1], so a curriculum stage cannot silently exceed manifest caps.
        Source action names, order, and checkpoint hashes are checked before
        any tensor is composed.
        """
        self._validate_source_proposal(
            "fret", fret_proposal,
            self.manifest.fret_action_names,
            self.manifest.fret_checkpoint_sha256)
        self._validate_source_proposal(
            "strike", strike_proposal,
            self.manifest.strike_action_names,
            self.manifest.strike_checkpoint_sha256)
        return self._forward_means(
            fret_mean=fret_proposal.mean,
            strike_mean=strike_proposal.mean,
            goal_context=goal_context,
            readiness_context=readiness_context,
            joint_context=joint_context,
            guitar_context=guitar_context,
            authority_mask=authority_mask,
            cap_scale=cap_scale,
        )

    def forward_structured_goal(
            self, *, fret_proposal: SourceProposal,
            strike_proposal: SourceProposal, goal_score: GoalScoreBatch,
            readiness_context: torch.Tensor, joint_context: torch.Tensor,
            guitar_context: torch.Tensor,
            authority_mask: Optional[torch.Tensor] = None,
            cap_scale: Optional[torch.Tensor] = None) -> ActionResidualOutput:
        """Structured-Goal ablation using legacy fixed-logit caps.

        Production Full control must use
        :meth:`forward_structured_goal_physical_caps` so physical limits and
        the three independent safety masks cannot be bypassed.
        """

        goal_context = self.goal_score_encoder(goal_score)
        return self.forward(
            fret_proposal=fret_proposal,
            strike_proposal=strike_proposal,
            goal_context=goal_context,
            readiness_context=readiness_context,
            joint_context=joint_context,
            guitar_context=guitar_context,
            authority_mask=authority_mask,
            cap_scale=cap_scale,
        )

    def forward_physical_caps(
            self, *, fret_proposal: SourceProposal,
            strike_proposal: SourceProposal, goal_context: torch.Tensor,
            readiness_context: torch.Tensor, joint_context: torch.Tensor,
            guitar_context: torch.Tensor, safety_masks: ActionSafetyMasks,
            cap_rad: float | torch.Tensor,
            ctrl_half: float | torch.Tensor,
            action_scale: float | torch.Tensor,
            cap_scale: float | torch.Tensor = 1.0) -> ActionResidualOutput:
        """Production path using physical per-joint residual limits."""

        self._validate_source_proposal(
            "fret", fret_proposal,
            self.manifest.fret_action_names,
            self.manifest.fret_checkpoint_sha256)
        self._validate_source_proposal(
            "strike", strike_proposal,
            self.manifest.strike_action_names,
            self.manifest.strike_checkpoint_sha256)
        return self._forward_means(
            fret_mean=fret_proposal.mean,
            strike_mean=strike_proposal.mean,
            goal_context=goal_context,
            readiness_context=readiness_context,
            joint_context=joint_context,
            guitar_context=guitar_context,
            physical_safety_masks=safety_masks,
            physical_cap_rad=cap_rad,
            physical_ctrl_half=ctrl_half,
            physical_action_scale=action_scale,
            cap_scale=cap_scale,
        )

    def forward_structured_goal_physical_caps(
            self, *, fret_proposal: SourceProposal,
            strike_proposal: SourceProposal, goal_score: GoalScoreBatch,
            readiness_context: torch.Tensor, joint_context: torch.Tensor,
            guitar_context: torch.Tensor, safety_masks: ActionSafetyMasks,
            cap_rad: float | torch.Tensor,
            ctrl_half: float | torch.Tensor,
            action_scale: float | torch.Tensor,
            cap_scale: float | torch.Tensor = 1.0) -> ActionResidualOutput:
        """Production entry point for structured goals and physical caps."""

        return self.forward_physical_caps(
            fret_proposal=fret_proposal,
            strike_proposal=strike_proposal,
            goal_context=self.goal_score_encoder(goal_score),
            readiness_context=readiness_context,
            joint_context=joint_context,
            guitar_context=guitar_context,
            safety_masks=safety_masks,
            cap_rad=cap_rad,
            ctrl_half=ctrl_half,
            action_scale=action_scale,
            cap_scale=cap_scale,
        )

    def _forward_means(
            self, *, fret_mean: torch.Tensor, strike_mean: torch.Tensor,
            goal_context: torch.Tensor, readiness_context: torch.Tensor,
            joint_context: torch.Tensor, guitar_context: torch.Tensor,
            authority_mask: Optional[torch.Tensor] = None,
            cap_scale: float | torch.Tensor | None = None,
            physical_safety_masks: Optional[ActionSafetyMasks] = None,
            physical_cap_rad: float | torch.Tensor | None = None,
            physical_ctrl_half: float | torch.Tensor | None = None,
            physical_action_scale: float | torch.Tensor | None = None,
            ) -> ActionResidualOutput:
        if fret_mean.ndim != 2:
            raise ValueError("fret_mean must have shape [batch, action]")
        batch = fret_mean.shape[0]
        self._check_input(
            "fret_mean", fret_mean, batch, self.manifest.fret_action_dim)
        self._check_input(
            "strike_mean", strike_mean, batch,
            self.manifest.strike_action_dim)
        self._check_input(
            "goal_context", goal_context, batch,
            self.config.goal_context_dim)
        self._check_input(
            "readiness_context", readiness_context, batch,
            self.config.readiness_context_dim)
        self._check_input(
            "joint_context", joint_context, batch,
            self.config.joint_context_dim)
        self._check_input(
            "guitar_context", guitar_context, batch,
            self.config.guitar_context_dim)
        common = (
            fret_mean, strike_mean, goal_context, readiness_context,
            joint_context, guitar_context)
        if any(value.device != fret_mean.device for value in common[1:]):
            raise ValueError("all coordinator inputs must share one device")
        parameter = next(self.parameters(), None)
        if parameter is not None and parameter.device != fret_mean.device:
            raise ValueError("coordinator inputs and parameters must share a device")
        if parameter is not None and parameter.dtype != torch.float32:
            raise RuntimeError("coordinator parameters left their FP32 contract")

        # Only this encoder copy is normalized.  _base_mean below always uses
        # the untouched source pre-tanh means for zero-residual equivalence.
        source_intent = self.source_intent_normalizer(
            fret_mean, strike_mean)
        encoded = (
            self.action_encoder(source_intent),
            self.goal_encoder(goal_context),
            self.readiness_encoder(readiness_context),
            self.joint_encoder(joint_context),
            self.guitar_encoder(guitar_context),
        )
        fusion_feature = self.fusion(torch.cat(encoded, dim=-1))
        raw_residual = torch.cat((
            self.arm_head(fusion_feature),
            self.body_head(fusion_feature),
        ), dim=-1)

        base_mean = self._base_mean(fret_mean, strike_mean)

        if physical_safety_masks is not None:
            if authority_mask is not None:
                raise ValueError(
                    "authority_mask cannot be combined with physical_safety_masks")
            required_physical = (
                physical_cap_rad, physical_ctrl_half,
                physical_action_scale)
            if any(value is None for value in required_physical):
                raise ValueError(
                    "physical cap path requires cap_rad, ctrl_half, and "
                    "action_scale")
            expected_indices = self.residual_indices.to(
                device=physical_safety_masks.residual_joint_indices.device)
            if not torch.equal(
                    physical_safety_masks.residual_joint_indices,
                    expected_indices):
                raise ValueError(
                    "safety residual_joint_indices do not match the action "
                    "manifest")
            source_indices = torch.cat((
                self.fret_indices, self.strike_indices)).to(
                    device=expected_indices.device)
            physical_safety_masks.validate_current_profile(
                source_joint_indices=source_indices,
                new_joint_indices=self.new_action_indices.to(
                    device=expected_indices.device),
                batch=batch,
            )
            physical_result = apply_physical_residual(
                base_mean=base_mean.index_select(1, self.residual_indices),
                raw_residual=raw_residual,
                cap_rad=physical_cap_rad,
                ctrl_half=physical_ctrl_half,
                action_scale=physical_action_scale,
                masks=physical_safety_masks,
                cap_scale=1.0 if cap_scale is None else cap_scale,
            )
            bounded_residual = physical_result.bounded_residual
            directional_caps = physical_result.caps
        else:
            if any(value is not None for value in (
                    physical_cap_rad, physical_ctrl_half,
                    physical_action_scale)):
                raise ValueError(
                    "physical cap parameters require physical_safety_masks")
            directional_caps = None

            if authority_mask is None:
                authority = torch.ones(
                    batch, self.residual_dim, dtype=raw_residual.dtype,
                    device=raw_residual.device)
            else:
                authority = torch.as_tensor(
                    authority_mask, dtype=torch.bool,
                    device=raw_residual.device)
                if authority.ndim == 1:
                    authority = authority.unsqueeze(0).expand(batch, -1)
                if authority.shape != raw_residual.shape:
                    raise ValueError(
                        "authority_mask must have shape [residual] or "
                        "[batch, residual]")
                authority = authority.to(raw_residual.dtype)

            if cap_scale is None:
                scale = torch.ones_like(raw_residual)
            else:
                scale = torch.as_tensor(
                    cap_scale, dtype=raw_residual.dtype,
                    device=raw_residual.device)
                if scale.ndim == 0:
                    scale = scale.expand_as(raw_residual)
                elif scale.ndim == 1:
                    scale = scale.unsqueeze(0).expand(batch, -1)
                if scale.shape != raw_residual.shape:
                    raise ValueError(
                        "cap_scale must be scalar, [residual], or "
                        "[batch, residual]")
                if not torch.isfinite(scale).all() or not (
                        (scale >= 0.0) & (scale <= 1.0)).all():
                    raise ValueError("cap_scale must be finite and in [0, 1]")

            caps = self.residual_caps.to(
                dtype=raw_residual.dtype,
                device=raw_residual.device).unsqueeze(0)
            bounded_residual = (
                torch.tanh(raw_residual) * caps * scale * authority)
        joint_residual = raw_residual.new_zeros(
            batch, self.joint_action_dim)
        joint_residual = joint_residual.scatter(
            1, self.residual_indices.unsqueeze(0).expand(batch, -1),
            bounded_residual)
        joint_mean = base_mean + joint_residual
        return ActionResidualOutput(
            base_mean=base_mean,
            raw_residual=raw_residual,
            bounded_residual=bounded_residual,
            joint_residual=joint_residual,
            joint_mean=joint_mean,
            fusion_feature=fusion_feature,
            directional_caps=directional_caps,
            safety_masks=physical_safety_masks,
        )

    def _compose_log_std(
            self, fret_log_std: torch.Tensor,
            strike_log_std: torch.Tensor) -> torch.Tensor:
        fret_log_std = torch.as_tensor(
            fret_log_std, dtype=self.new_log_std.dtype,
            device=self.new_log_std.device)
        strike_log_std = torch.as_tensor(
            strike_log_std, dtype=self.new_log_std.dtype,
            device=self.new_log_std.device)
        if fret_log_std.shape != (self.manifest.fret_action_dim,):
            raise ValueError("fret_log_std must match Fret source actions")
        if strike_log_std.shape != (self.manifest.strike_action_dim,):
            raise ValueError("strike_log_std must match Strike source actions")
        result = self.new_log_std.new_empty(self.joint_action_dim)
        result = result.scatter(0, self.fret_indices, fret_log_std)
        result = result.scatter(0, self.strike_indices, strike_log_std)
        result = result.scatter(0, self.new_action_indices, self.new_log_std)
        return result

    def distribution(
            self, output: ActionResidualOutput, *,
            fret_proposal: SourceProposal, strike_proposal: SourceProposal,
            active_action_mask: Optional[torch.Tensor] = None,
            safety_masks: Optional[ActionSafetyMasks] = None,
            ) -> MaskedJointTanhNormal:
        self._validate_source_proposal(
            "fret", fret_proposal,
            self.manifest.fret_action_names,
            self.manifest.fret_checkpoint_sha256)
        self._validate_source_proposal(
            "strike", strike_proposal,
            self.manifest.strike_action_names,
            self.manifest.strike_checkpoint_sha256)
        batch = output.joint_mean.shape[0]
        if (fret_proposal.mean.shape[0] != batch
                or strike_proposal.mean.shape[0] != batch):
            raise ValueError(
                "source proposal batches must match the coordinator output")
        log_std = self._compose_log_std(
            fret_proposal.log_std, strike_proposal.log_std)
        if safety_masks is not None:
            if active_action_mask is not None:
                raise ValueError(
                    "active_action_mask cannot be combined with safety_masks")
            if output.safety_masks is None:
                raise ValueError(
                    "safety_masks require output from the physical-cap path")
            for name in (
                    "residual_authority_mask",
                    "stochastic_execution_mask", "ppo_credit_mask",
                    "residual_joint_indices"):
                if not torch.equal(
                        getattr(safety_masks, name),
                        getattr(output.safety_masks, name)):
                    raise ValueError(
                        "distribution safety_masks differ from the masks used "
                        "to bound the residual")
            _, execution, credit = safety_masks.expanded(batch)
            return MaskedJointTanhNormal(
                output.joint_mean,
                log_std,
                neutral_logits=self.neutral_logits,
                stochastic_execution_mask=execution,
                ppo_credit_mask=credit,
            )
        if active_action_mask is None:
            raise ValueError(
                "provide safety_masks or legacy active_action_mask")
        return MaskedJointTanhNormal(
            output.joint_mean,
            log_std,
            active_action_mask,
            self.neutral_logits,
        )

    def checkpoint_manifest(self) -> dict[str, object]:
        return {
            "architecture_id": self.architecture_id,
            "action_manifest_sha256": self.manifest.sha256(),
            "action_manifest": self.manifest.payload(),
            "actor_config": asdict(self.config),
            "context_dimensions": {
                "goal": self.config.goal_context_dim,
                "readiness": self.config.readiness_context_dim,
                "joint": self.config.joint_context_dim,
                "guitar": self.config.guitar_context_dim,
            },
            "static_context_schema": {
                "readiness_sha256": READINESS_MANIFEST.sha256(),
                "guitar_support_sha256": GUITAR_SUPPORT_MANIFEST.sha256(),
            },
            "goal_score_schema": self.goal_score_encoder.schema_metadata(),
            "source_intent_calibration":
                self.source_intent_normalizer.checkpoint_manifest(),
            "fusion_input_dim": self.config.fusion_input_dim,
            "fusion_hidden_dims": list(self.config.fusion_hidden_dims),
        }

    def get_extra_state(self) -> dict[str, object]:
        """Persist the semantic ABI that tensor shapes cannot represent."""

        return deepcopy(self.checkpoint_manifest())

    def set_extra_state(self, state: dict[str, object]) -> None:
        if not isinstance(state, dict) or state != self.checkpoint_manifest():
            raise RuntimeError(
                "Action Residual coordinator checkpoint manifest mismatch")

    def _validate_semantic_state_dict(self, state_dict, prefix: str = "") -> None:
        expected = {
            f"{prefix}_extra_state": self.get_extra_state(),
            f"{prefix}goal_score_encoder._extra_state":
                self.goal_score_encoder.get_extra_state(),
            f"{prefix}source_intent_normalizer._extra_state":
                self.source_intent_normalizer.get_extra_state(),
        }
        for key, value in expected.items():
            if state_dict.get(key) != value:
                raise RuntimeError(
                    "Action Residual coordinator checkpoint manifest mismatch")

    def _load_from_state_dict(
            self, state_dict, prefix, local_metadata, strict,
            missing_keys, unexpected_keys, error_msgs):
        validate_finite_state_dict(state_dict, label="coordinator")
        self._validate_semantic_state_dict(state_dict, prefix)
        return super()._load_from_state_dict(
            state_dict, prefix, local_metadata, strict,
            missing_keys, unexpected_keys, error_msgs)

    def load_state_dict(self, state_dict, strict: bool = True, assign: bool = False):
        """Validate semantic metadata before mutating any parameter tensor."""

        validate_finite_state_dict(state_dict, label="coordinator")
        self._validate_semantic_state_dict(state_dict)
        return super().load_state_dict(
            state_dict, strict=strict, assign=assign)
