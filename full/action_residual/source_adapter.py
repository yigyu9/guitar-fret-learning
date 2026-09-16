"""Frozen source adapter that exposes means, never hidden activations."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Iterable

import torch
from torch import nn

from .checkpoint_utils import validate_finite_state_dict
from .source_projection import (
    FrozenSourceObservationProjector,
    ProjectedSourceObservation,
    SourceProjectionManifest,
)


RAW_SOURCE_OBSERVATION_ID = "full.source_observation.native_raw.v1"


@dataclass(frozen=True)
class RawSourceObservation:
    """Tagged native raw input; an already-normalized tensor is not valid."""

    value: torch.Tensor
    source_name: str
    checkpoint_sha256: str
    input_space_id: str = RAW_SOURCE_OBSERVATION_ID

    def __post_init__(self) -> None:
        if (not isinstance(self.value, torch.Tensor)
                or self.value.ndim != 2):
            raise ValueError("raw source value must have shape [batch, obs]")
        if self.value.dtype != torch.float32:
            raise TypeError("raw source observations must use torch.float32")
        if not torch.isfinite(self.value).all():
            raise ValueError("raw source observations must be finite")
        if not isinstance(self.source_name, str) or not self.source_name:
            raise ValueError("source_name must be non-empty")
        digest = str(self.checkpoint_sha256)
        if (len(digest) != 64
                or any(char not in "0123456789abcdef" for char in digest)):
            raise ValueError("checkpoint_sha256 must be lowercase SHA-256")
        object.__setattr__(self, "checkpoint_sha256", digest)
        if self.input_space_id != RAW_SOURCE_OBSERVATION_ID:
            raise ValueError("unsupported raw source input_space_id")


@dataclass(frozen=True)
class SourceProposal:
    mean: torch.Tensor
    log_std: torch.Tensor
    action_names: tuple[str, ...]
    checkpoint_sha256: str

    def __post_init__(self) -> None:
        names = tuple(str(name) for name in self.action_names)
        if not names or len(set(names)) != len(names):
            raise ValueError("source proposal action names must be unique")
        if self.mean.ndim != 2 or self.mean.shape[-1] != len(names):
            raise ValueError(
                "source proposal mean must have shape [batch, action]")
        if self.log_std.shape != (len(names),):
            raise ValueError(
                "source proposal log_std must have shape [action]")
        if (self.mean.dtype != torch.float32
                or self.log_std.dtype != torch.float32):
            raise TypeError("source proposal tensors must use torch.float32")
        if self.mean.device != self.log_std.device:
            raise ValueError("source proposal tensors must share a device")
        if (not torch.isfinite(self.mean).all()
                or not torch.isfinite(self.log_std).all()):
            raise ValueError("source proposal tensors must be finite")
        digest = str(self.checkpoint_sha256)
        if (len(digest) != 64
                or any(c not in "0123456789abcdef" for c in digest)):
            raise ValueError(
                "source proposal checkpoint_sha256 must be lowercase SHA-256")
        object.__setattr__(self, "action_names", names)
        object.__setattr__(self, "checkpoint_sha256", digest)


class FrozenSourcePolicyAdapter(nn.Module):
    """Read-only wrapper for the existing ``ActorCritic.distribution`` API."""

    def __init__(
            self, policy: nn.Module, action_names: Iterable[str],
            checkpoint_sha256: str, *, source_name: str,
            projection_manifest: SourceProjectionManifest | None = None) -> None:
        super().__init__()
        names = tuple(str(name) for name in action_names)
        if not names or len(set(names)) != len(names):
            raise ValueError("source action names must be non-empty and unique")
        if (len(checkpoint_sha256) != 64
                or any(c not in "0123456789abcdef"
                       for c in checkpoint_sha256)):
            raise ValueError(
                "checkpoint_sha256 must be a non-empty lowercase SHA-256")
        if not hasattr(policy, "distribution"):
            raise TypeError("source policy must provide distribution(obs)")
        source_name = str(source_name)
        if not source_name:
            raise ValueError("source_name must be non-empty")
        action_dim = getattr(policy, "action_dim", len(names))
        if int(action_dim) != len(names):
            raise ValueError("source action names must match policy action_dim")

        self.policy = policy
        self.action_names = names
        self.checkpoint_sha256 = checkpoint_sha256
        self.source_name = source_name
        self.observation_dim = int(getattr(policy, "obs_dim", -1))
        if self.observation_dim <= 0:
            raise ValueError("source policy must expose a positive obs_dim")
        self.projection_manifest = projection_manifest
        if projection_manifest is not None:
            if projection_manifest.source_name != source_name:
                raise ValueError("projection source_name does not match adapter")
            if projection_manifest.checkpoint_sha256 != checkpoint_sha256:
                raise ValueError(
                    "projection checkpoint SHA-256 does not match adapter")
            if projection_manifest.observation_dim != self.observation_dim:
                raise ValueError(
                    "projection observation dimension does not match policy")
            obs_rms = getattr(policy, "obs_rms", None)
            if (obs_rms is None or not hasattr(obs_rms, "mean")
                    or not hasattr(obs_rms, "var")
                    or not hasattr(obs_rms, "clip")):
                raise TypeError(
                    "projected source policy must expose frozen obs_rms")
            actual_rms_sha = FrozenSourceObservationProjector.rms_sha256(
                obs_rms.mean,
                obs_rms.var,
                epsilon=1e-8,
                clip=float(obs_rms.clip),
            )
            if actual_rms_sha != projection_manifest.rms_sha256:
                raise ValueError(
                    "source policy RMS does not match projection manifest")
        for parameter in self.policy.parameters():
            if parameter.dtype != torch.float32:
                raise TypeError("frozen source policy must use torch.float32")
            parameter.requires_grad_(False)
        if any(buffer.is_floating_point() and buffer.dtype != torch.float32
               for buffer in self.policy.buffers()):
            raise TypeError("frozen source policy buffers must use torch.float32")
        self.policy.eval()
        self._seal_frozen_structure()
        self.register_load_state_dict_post_hook(
            self._post_load_reseal_frozen_structure)

    @staticmethod
    def _post_load_reseal_frozen_structure(module, incompatible_keys) -> None:
        del incompatible_keys
        module._seal_frozen_structure()

    def _seal_frozen_structure(self) -> None:
        def record(items):
            return tuple(
                (name, id(tensor), tensor.data_ptr(), tensor._version)
                for name, tensor in items)
        self._frozen_parameter_signature = record(
            self.policy.named_parameters())
        self._frozen_buffer_signature = record(self.policy.named_buffers())

    def assert_frozen_integrity(self) -> None:
        """Detect in-process source mutation between rollout audits."""
        def current(items):
            return tuple(
                (name, id(tensor), tensor.data_ptr(), tensor._version)
                for name, tensor in items)
        if current(self.policy.named_parameters()) != (
                self._frozen_parameter_signature):
            raise RuntimeError("frozen source policy parameters were mutated")
        if current(self.policy.named_buffers()) != self._frozen_buffer_signature:
            raise RuntimeError("frozen source policy buffers were mutated")
        if any(parameter.requires_grad for parameter in self.policy.parameters()):
            raise RuntimeError("frozen source policy entered the optimizer graph")
        if self.policy.training:
            raise RuntimeError("frozen source policy left eval mode")
        if (any(parameter.dtype != torch.float32
                for parameter in self.policy.parameters())
                or any(buffer.is_floating_point()
                       and buffer.dtype != torch.float32
                       for buffer in self.policy.buffers())):
            raise RuntimeError("frozen source policy left its FP32 contract")

    def _apply(self, fn, recurse: bool = True):
        reference = next(self.policy.parameters(), None)
        if reference is not None:
            probe = torch.empty(
                0, dtype=torch.float32, device=reference.device)
            if fn(probe).dtype != torch.float32:
                raise TypeError("frozen source policy must remain torch.float32")
        result = super()._apply(fn, recurse=recurse)
        # Device moves are authorized module operations; re-seal afterwards.
        if hasattr(self, "policy"):
            self._seal_frozen_structure()
        return result

    def train(self, mode: bool = True):
        super().train(False)
        self.policy.eval()
        return self

    @torch.no_grad()
    def _run_raw_tensor(self, observation: torch.Tensor) -> SourceProposal:
        self.assert_frozen_integrity()
        if (observation.ndim != 2
                or observation.shape[-1] != self.observation_dim):
            raise ValueError(
                "raw source observation does not match policy obs_dim")
        if observation.dtype != torch.float32:
            raise TypeError("source inference must use torch.float32")
        if not torch.isfinite(observation).all():
            raise ValueError("raw source observation must be finite")
        parameter = next(self.policy.parameters(), None)
        if parameter is not None and parameter.device != observation.device:
            raise ValueError("source observation and policy must share a device")
        # Do not inherit an outer AMP region for frozen-source inference.
        with torch.autocast(device_type=observation.device.type, enabled=False):
            distribution = self.policy.distribution(observation)
        mean = distribution.mean.detach()
        log_std = distribution.scale.log().detach()
        if mean.shape[-1] != len(self.action_names):
            raise RuntimeError("source proposal action dimension changed")
        if log_std.ndim == 2:
            reference = log_std[0]
            if not torch.allclose(log_std, reference.unsqueeze(0).expand_as(log_std)):
                raise RuntimeError(
                    "Action Residual v1 expects state-independent source std")
            log_std = reference
        return SourceProposal(
            mean=mean,
            log_std=log_std,
            action_names=self.action_names,
            checkpoint_sha256=self.checkpoint_sha256,
        )

    @torch.no_grad()
    def forward(
            self,
            observation: RawSourceObservation | ProjectedSourceObservation,
            ) -> SourceProposal:
        """Accept only tagged raw spaces, preventing accidental double RMS."""

        if isinstance(observation, ProjectedSourceObservation):
            return self.forward_projected(observation)
        if not isinstance(observation, RawSourceObservation):
            raise TypeError(
                "source adapter requires RawSourceObservation or "
                "ProjectedSourceObservation; bare tensors are ambiguous")
        if observation.source_name != self.source_name:
            raise ValueError("raw observation source_name does not match adapter")
        if observation.checkpoint_sha256 != self.checkpoint_sha256:
            raise ValueError(
                "raw observation checkpoint SHA-256 does not match adapter")
        return self._run_raw_tensor(observation.value)

    @torch.no_grad()
    def forward_projected(
            self, observation: ProjectedSourceObservation) -> SourceProposal:
        """Use raw projection and prove that source RMS is applied once."""
        if not isinstance(observation, ProjectedSourceObservation):
            raise TypeError(
                "observation must be a ProjectedSourceObservation")
        if observation.checkpoint_sha256 != self.checkpoint_sha256:
            raise ValueError(
                "projected observation source checkpoint does not match adapter")
        if observation.source_name != self.source_name:
            raise ValueError(
                "projected observation source_name does not match adapter")
        if observation.observation_dim != self.observation_dim:
            raise ValueError(
                "projected observation width does not match source policy")
        if self.projection_manifest is None:
            raise RuntimeError(
                "adapter requires a projection_manifest before using "
                "projected observations")
        if (observation.projection_manifest_sha256
                != self.projection_manifest.sha256()):
            raise ValueError(
                "projected observation manifest does not match adapter")
        # ActorCritic.distribution performs the single frozen obs_rms pass.
        return self._run_raw_tensor(observation.raw_projected)

    def checkpoint_manifest(self) -> dict[str, object]:
        return {
            "source_name": self.source_name,
            "action_names": list(self.action_names),
            "observation_dim": self.observation_dim,
            "checkpoint_sha256": self.checkpoint_sha256,
            "projection_manifest": (
                None if self.projection_manifest is None
                else self.projection_manifest.payload()),
        }

    def get_extra_state(self) -> dict[str, object]:
        return deepcopy(self.checkpoint_manifest())

    def set_extra_state(self, state: dict[str, object]) -> None:
        if not isinstance(state, dict) or state != self.checkpoint_manifest():
            raise RuntimeError("frozen source adapter checkpoint mismatch")

    def _load_from_state_dict(
            self, state_dict, prefix, local_metadata, strict,
            missing_keys, unexpected_keys, error_msgs):
        validate_finite_state_dict(state_dict, label="frozen source adapter")
        if state_dict.get(f"{prefix}_extra_state") != self.get_extra_state():
            raise RuntimeError("frozen source adapter checkpoint mismatch")
        return super()._load_from_state_dict(
            state_dict, prefix, local_metadata, strict,
            missing_keys, unexpected_keys, error_msgs)

    def load_state_dict(self, state_dict, strict: bool = True, assign: bool = False):
        validate_finite_state_dict(state_dict, label="frozen source adapter")
        if state_dict.get("_extra_state") != self.get_extra_state():
            raise RuntimeError("frozen source adapter checkpoint mismatch")
        result = super().load_state_dict(
            state_dict, strict=strict, assign=assign)
        self._seal_frozen_structure()
        return result
