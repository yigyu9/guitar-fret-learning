"""Composition runtime for frozen source skills and the G0 Synchronizer."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

import torch

from tab2body.learning.checkpoint_contract import canonical_sha256

from .action import ArbitratedAction, FullActionManifest, G0ActionArbiter
from .clock import CanonicalEventBatch, CanonicalScoreClock
from .events import CanonicalEventTimeline
from .source_policies import FrozenSkillPair
from .postprocessing import (
    FretSynergyPostprocessor,
    StrikePickGripPostprocessor,
)
from .synchronizer import (
    RuleBasedSynchronizer,
    SynchronizerDecision,
    SynchronizerResult,
)


G0_RUNTIME_SCHEMA = "tab2body.g0_synchronizer_runtime.v2"


@dataclass(frozen=True)
class G0RuntimeCommand:
    """Everything a one-simulator FullG0Task needs before physics."""

    decision: SynchronizerDecision
    event: CanonicalEventBatch
    action: ArbitratedAction
    actor_fret_action: torch.Tensor
    actor_strike_action: torch.Tensor
    actor_fret_observation: torch.Tensor
    actor_strike_observation: torch.Tensor


class G0SynchronizationRuntime:
    """Frozen dual-policy inference plus external timing/action arbitration.

    This class does not create an Isaac simulator.  A shared ``FullG0Task``
    supplies both native observations from one physical state, calls this
    object once, applies the returned 105D command through one EMA/PD update,
    and reports one detector snapshot to :meth:`after_physics`.

    Optional source postprocessors let the shared task preserve the existing
    Fret finger-synergy and Strike pick-grip contracts before named scatter.
    They must be deterministic and return the same shape/dtype/device.
    """

    def __init__(
            self, source_pair: FrozenSkillPair,
            timeline: CanonicalEventTimeline,
            action_manifest: FullActionManifest, *, num_envs: int,
            fret_postprocessor: Optional[Callable] = None,
            strike_postprocessor: Optional[Callable] = None,
            max_delay_frames: int = 3, readiness_dwell_frames: int = 1,
            common_preroll_frames: int = 60,
            allow_identity_postprocessors: bool = False):
        self.source_pair = source_pair
        self.timeline = timeline
        self.action_manifest = action_manifest
        if timeline.song_id != source_pair.song_id:
            raise ValueError("canonical timeline and source pair song disagree")
        if timeline.fps != source_pair.fps:
            raise ValueError("canonical timeline and source pair FPS disagree")
        if tuple(action_manifest.fret_action_names) != tuple(
                source_pair.fret.action_names):
            raise ValueError("Full action manifest does not match Fret source")
        if tuple(action_manifest.strike_action_names) != tuple(
                source_pair.strike.action_names):
            raise ValueError("Full action manifest does not match Strike source")
        fret_parameter = next(source_pair.fret.model.parameters())
        strike_parameter = next(source_pair.strike.model.parameters())
        if fret_parameter.device != strike_parameter.device:
            raise ValueError("Fret and Strike policies must share a device")
        self.device = fret_parameter.device
        self.num_envs = int(num_envs)
        self.supervisor = RuleBasedSynchronizer(
            self.num_envs, device=self.device, fps=source_pair.fps,
            configured_max_delay_frames=max_delay_frames,
            readiness_dwell_frames=readiness_dwell_frames)
        self.clock = CanonicalScoreClock(
            timeline, num_envs=self.num_envs, device=self.device,
            preroll_frames=common_preroll_frames)
        self.arbiter = G0ActionArbiter(action_manifest)
        one_postprocessor_missing = (
            (fret_postprocessor is None) != (strike_postprocessor is None))
        if one_postprocessor_missing:
            raise ValueError(
                "Fret and Strike source postprocessors must be supplied together")
        identity_postprocessors = fret_postprocessor is None
        if identity_postprocessors and not allow_identity_postprocessors:
            raise ValueError(
                "physical G0 runtime requires both the Fret synergy and "
                "Strike pick-grip action postprocessors")
        if not identity_postprocessors:
            if not isinstance(fret_postprocessor, FretSynergyPostprocessor):
                raise TypeError(
                    "physical G0 requires a verified FretSynergyPostprocessor")
            if not isinstance(
                    strike_postprocessor, StrikePickGripPostprocessor):
                raise TypeError(
                    "physical G0 requires a verified StrikePickGripPostprocessor")
            if not source_pair.qualified_for_g0:
                raise ValueError(
                    "physical G0 rejects source checkpoints that have not "
                    "passed their final-stage qualification")
            if tuple(fret_postprocessor.action_names) != tuple(
                    source_pair.fret.action_names):
                raise ValueError(
                    "Fret postprocessor does not match the frozen source ABI")
            if tuple(strike_postprocessor.action_names) != tuple(
                    source_pair.strike.action_names):
                raise ValueError(
                    "Strike postprocessor does not match the frozen source ABI")
            for task, processor, source in (
                    ("Fret", fret_postprocessor, source_pair.fret),
                    ("Strike", strike_postprocessor, source_pair.strike)):
                processor.assert_integrity()
                if (processor.source_contract_sha256
                        != source.contract_sha256
                        or processor.source_checkpoint_sha256
                        != source.checkpoint_sha256
                        or processor.source_qualification.training_context_sha256
                        != source.qualification.training_context_sha256):
                    raise ValueError(
                        f"{task} postprocessor is bound to a different source")
                tensor = processor.half_ranges
                if tensor.dtype != torch.float32 or tensor.device != self.device:
                    raise ValueError(
                        f"{task} postprocessor tensor ABI differs from its policy")
        self.fret_postprocessor = fret_postprocessor
        self.strike_postprocessor = strike_postprocessor
        self.allow_identity_postprocessors = bool(
            allow_identity_postprocessors)
        if identity_postprocessors:
            self.postprocessor_contract = {
                "mode": "identity_integration_probe_only",
            }
        else:
            self.postprocessor_contract = {
                "mode": "source_exact_physical",
                "fret": fret_postprocessor.manifest,
                "strike": strike_postprocessor.manifest,
            }
        self.postprocessor_contract_sha256 = canonical_sha256(
            self.postprocessor_contract)
        self.previous_fret_action = None
        self.previous_strike_action = None
        self._awaiting_executed_action = False
        self._awaiting_after_physics = False
        self._active_event_batch = None

    def reset(self, hold_action: torch.Tensor, env_ids=None):
        if self._awaiting_executed_action or self._awaiting_after_physics:
            raise RuntimeError(
                "cannot reset G0 runtime during an incomplete physics step")
        if (not isinstance(hold_action, torch.Tensor)
                or hold_action.shape != (self.num_envs, 105)
                or hold_action.dtype != torch.float32
                or hold_action.device != self.device
                or not torch.isfinite(hold_action).all()):
            raise ValueError(
                "runtime reset hold_action must be finite float32 [N,105] "
                "on the policy device")
        if bool((hold_action.abs() > 1.0 + 1e-6).any().item()):
            raise ValueError("runtime reset hold_action must remain in [-1,1]")
        fret_indices = torch.as_tensor(
            self.action_manifest.fret_indices, dtype=torch.long,
            device=self.device)
        strike_indices = torch.as_tensor(
            self.action_manifest.strike_indices, dtype=torch.long,
            device=self.device)
        if self.previous_fret_action is None:
            self.previous_fret_action = hold_action[:, fret_indices].clone()
            self.previous_strike_action = hold_action[:, strike_indices].clone()
        if env_ids is None:
            ids = torch.arange(
                self.num_envs, dtype=torch.long, device=self.device)
        else:
            ids = torch.as_tensor(
                env_ids, dtype=torch.long, device=self.device).reshape(-1)
            if ids.numel() and bool(
                    ((ids < 0) | (ids >= self.num_envs)).any().item()):
                raise IndexError("runtime reset env_ids are outside the batch")
        self.previous_fret_action[ids] = hold_action[ids][:, fret_indices]
        self.previous_strike_action[ids] = hold_action[ids][:, strike_indices]
        self.supervisor.reset(ids)
        self.clock.reset(ids)
        if self.fret_postprocessor is not None:
            self.fret_postprocessor.clear_step_state()
        self._active_event_batch = None

    @staticmethod
    def _postprocess(callback, action, previous_action, label):
        if callback is None:
            return action
        value = callback(action, previous_action)
        if (not isinstance(value, torch.Tensor)
                or value.shape != action.shape
                or value.dtype != action.dtype
                or value.device != action.device
                or not torch.isfinite(value).all()):
            raise RuntimeError(
                f"{label} source postprocessor broke its action contract")
        if bool((value.abs() > 1.0 + 1e-6).any().item()):
            raise RuntimeError(
                f"{label} source postprocessor returned an action outside [-1,1]")
        return value

    def before_physics(
            self, *, fret_observation, strike_observation, hold_action,
            fret_ready_mask, strike_ready, guitar_stable=None,
            strike_entry_hold_action=None
            ) -> G0RuntimeCommand:
        if self.previous_fret_action is None:
            raise RuntimeError("call runtime.reset(hold_action) before inference")
        if self._awaiting_executed_action:
            raise RuntimeError(
                "commit_executed_action() is required before the next step")
        if self._awaiting_after_physics:
            raise RuntimeError(
                "after_physics() is required before the next step")
        event = self.clock.current()
        decision = self.supervisor.before_step(
            event_id=event.event_index,
            score_frame=event.score_frame,
            release_boundary_frame=event.release_boundary_frame,
            traversal_end_frame=event.traversal_end_frame,
            delay_budget_frames=event.delay_budget_frames,
            target_frets=event.target_frets,
            audible_mask=event.audible_mask,
            traversal_mask=event.traversal_mask,
            traversal_order=event.traversal_order,
            traversal_offsets_s=event.traversal_offsets_s,
            strike_direction=event.strike_direction,
            fret_ready_mask=fret_ready_mask,
            strike_ready=strike_ready,
            guitar_stable=guitar_stable,
        )

        fret_native = self.source_pair.fret.prepare_observation(
            fret_observation,
            previous_executed_action=self.previous_fret_action)
        strike_native = self.source_pair.strike.prepare_observation(
            strike_observation,
            previous_executed_action=self.previous_strike_action,
            timing_shift_s=decision.timing_shift_s)
        fret_actor_action = self.source_pair.fret.deterministic_action(
            fret_native)
        strike_actor_action = self.source_pair.strike.deterministic_action(
            strike_native)
        fret_source_action = self._postprocess(
            self.fret_postprocessor, fret_actor_action,
            self.previous_fret_action, "Fret")
        strike_source_action = self._postprocess(
            self.strike_postprocessor, strike_actor_action,
            self.previous_strike_action, "Strike")
        if (bool(decision.hold_strike_action.any().item())
                and not self.allow_identity_postprocessors
                and strike_entry_hold_action is None):
            raise RuntimeError(
                "physical G0 entry hold requires a current-pose, pre-EMA "
                "Strike hold action from the shared actuator backend")
        arbitrated = self.arbiter.merge(
            fret_source_action, strike_source_action, hold_action,
            hold_fret=decision.hold_fret_action,
            hold_strike=decision.hold_strike_action,
            previous_fret_action=self.previous_fret_action,
            previous_strike_action=self.previous_strike_action,
            strike_entry_hold_action=strike_entry_hold_action)
        self._awaiting_executed_action = True
        self._awaiting_after_physics = True
        self._active_event_batch = event
        self.source_pair.fret.assert_frozen_integrity()
        self.source_pair.strike.assert_frozen_integrity()
        return G0RuntimeCommand(
            decision=decision,
            event=event,
            action=arbitrated,
            actor_fret_action=fret_actor_action,
            actor_strike_action=strike_actor_action,
            actor_fret_observation=fret_native,
            actor_strike_observation=strike_native,
        )

    def commit_executed_action(self, executed_full_action: torch.Tensor):
        """Commit the one common actuator's post-EMA 105D action.

        ``before_physics`` returns a pre-EMA command.  The shared Isaac task
        applies EMA/PD exactly once and calls this method with the finite,
        normalized action state that actually generated the PD target.  This
        is the only value written into the frozen policies' next
        ``O_history`` blocks.
        """
        if not self._awaiting_executed_action:
            raise RuntimeError(
                "no G0 command is waiting for an executed-action commit")
        if (not isinstance(executed_full_action, torch.Tensor)
                or executed_full_action.shape != (self.num_envs, 105)
                or executed_full_action.dtype != torch.float32
                or executed_full_action.device != self.device
                or not torch.isfinite(executed_full_action).all()):
            raise ValueError(
                "executed_full_action must be finite float32 [N,105] "
                "on the policy device")
        if bool((executed_full_action.abs() > 1.0 + 1e-6).any().item()):
            raise ValueError(
                "executed_full_action must be the exact normalized post-EMA "
                "action in [-1,1]")
        fret_indices = torch.as_tensor(
            self.action_manifest.fret_indices, dtype=torch.long,
            device=self.device)
        strike_indices = torch.as_tensor(
            self.action_manifest.strike_indices, dtype=torch.long,
            device=self.device)
        self.previous_fret_action.copy_(executed_full_action[:, fret_indices])
        self.previous_strike_action.copy_(
            executed_full_action[:, strike_indices])
        self._awaiting_executed_action = False

    def after_physics(self, *, crossing_mask, crossing_subframe_t,
                      crossing_direction, fret_ready_mask) -> SynchronizerResult:
        if self._awaiting_executed_action:
            raise RuntimeError(
                "commit the actual post-EMA action before after_physics()")
        if not self._awaiting_after_physics:
            raise RuntimeError("no G0 physics step is waiting for a result")
        if self._active_event_batch is None:
            raise RuntimeError("G0 event batch was lost before physics result")
        result = self.supervisor.after_step(
            score_frame=self._active_event_batch.score_frame,
            crossing_mask=crossing_mask,
            crossing_subframe_t=crossing_subframe_t,
            crossing_direction=crossing_direction,
            fret_ready_mask=fret_ready_mask)
        self.clock.consume_resolution(
            result.event_id, result.resolved_pulse)
        self.clock.advance_physics()
        self._awaiting_after_physics = False
        self._active_event_batch = None
        return result

    def checkpoint_state(self):
        if self.previous_fret_action is None:
            raise RuntimeError("cannot checkpoint an uninitialized G0 runtime")
        if self._awaiting_executed_action or self._awaiting_after_physics:
            raise RuntimeError(
                "checkpoint only at a completed control-step boundary")
        return {
            "schema": G0_RUNTIME_SCHEMA,
            "timeline_sha256": self.timeline.content_sha256,
            "source_contracts": {
                "fret": self.source_pair.fret.contract_sha256,
                "strike": self.source_pair.strike.contract_sha256,
            },
            "source_checkpoint_sha256": {
                "fret": self.source_pair.fret.checkpoint_sha256,
                "strike": self.source_pair.strike.checkpoint_sha256,
            },
            "action_manifest_sha256": self.action_manifest.sha256,
            "identity_postprocessors_allowed": (
                self.allow_identity_postprocessors),
            "postprocessor_contract_sha256": (
                self.postprocessor_contract_sha256),
            "previous_fret_action": self.previous_fret_action.clone(),
            "previous_strike_action": self.previous_strike_action.clone(),
            "score_clock": self.clock.state_dict(),
            "synchronizer": self.supervisor.state_dict(),
        }

    def load_checkpoint_state(self, state):
        """Restore only a state sealed to the same sources/timeline/action ABI."""
        if self._awaiting_executed_action or self._awaiting_after_physics:
            raise RuntimeError(
                "restore only at a completed control-step boundary")
        expected_keys = {
            "schema", "timeline_sha256", "source_contracts",
            "source_checkpoint_sha256", "action_manifest_sha256",
            "identity_postprocessors_allowed",
            "postprocessor_contract_sha256", "previous_fret_action",
            "previous_strike_action", "score_clock", "synchronizer",
        }
        if (not isinstance(state, dict)
                or set(state) != expected_keys
                or state.get("schema") != G0_RUNTIME_SCHEMA):
            raise ValueError("invalid G0 runtime state schema")
        if state.get("timeline_sha256") != self.timeline.content_sha256:
            raise ValueError("G0 runtime timeline hash mismatch")
        contracts = state.get("source_contracts")
        if contracts != {
                "fret": self.source_pair.fret.contract_sha256,
                "strike": self.source_pair.strike.contract_sha256}:
            raise ValueError("G0 runtime source contract mismatch")
        checkpoint_hashes = state.get("source_checkpoint_sha256")
        if checkpoint_hashes != {
                "fret": self.source_pair.fret.checkpoint_sha256,
                "strike": self.source_pair.strike.checkpoint_sha256}:
            raise ValueError("G0 runtime source checkpoint weights mismatch")
        if state.get("action_manifest_sha256") != self.action_manifest.sha256:
            raise ValueError("G0 runtime action manifest mismatch")
        identity_allowed = state.get("identity_postprocessors_allowed")
        if (not isinstance(identity_allowed, bool)
                or identity_allowed != self.allow_identity_postprocessors):
            raise ValueError("G0 runtime postprocessor mode mismatch")
        if state.get("postprocessor_contract_sha256") != (
                self.postprocessor_contract_sha256):
            raise ValueError("G0 runtime postprocessor contract mismatch")
        if self.previous_fret_action is None:
            raise RuntimeError(
                "call reset(hold_action) before restoring G0 runtime state")
        tensors = (
            ("previous_fret_action", self.previous_fret_action, 30),
            ("previous_strike_action", self.previous_strike_action, 30),
        )
        validated_actions = {}
        for name, destination, width in tensors:
            value = torch.as_tensor(state.get(name), device=self.device)
            if (value.shape != (self.num_envs, width)
                    or value.dtype != torch.float32
                    or not torch.isfinite(value).all()):
                raise ValueError(f"invalid G0 runtime tensor: {name}")
            if bool((value.abs() > 1.0 + 1e-6).any().item()):
                raise ValueError(
                    f"G0 runtime tensor is outside normalized range: {name}")
            validated_actions[name] = value.clone()

        # Validate child states and their cross-object invariants on temporary
        # instances first.  A late error must not leave half of the live runtime
        # restored and half unchanged.
        candidate_clock = CanonicalScoreClock(
            self.timeline, num_envs=self.num_envs, device=self.device,
            preroll_frames=self.clock.preroll_frames)
        candidate_clock.load_state_dict(state.get("score_clock"))
        candidate_supervisor = RuleBasedSynchronizer(
            self.num_envs, device=self.device, fps=self.source_pair.fps,
            configured_max_delay_frames=(
                self.supervisor.configured_max_delay_frames),
            readiness_dwell_frames=self.supervisor.readiness_dwell_frames)
        candidate_supervisor.load_state_dict(
            state.get("synchronizer"),
            max_event_count=len(self.timeline.events))
        initialized = candidate_supervisor._clock_initialized
        if bool((initialized & (
                candidate_clock.score_frame
                != candidate_supervisor._last_score_frame + 1)).any().item()):
            raise ValueError("G0 score and Synchronizer frames are inconsistent")
        if bool((~initialized & (
                (candidate_supervisor.event_id != -1)
                | (candidate_clock.event_index != 0)
                | (candidate_clock.score_frame
                   != -candidate_clock.preroll_frames))).any().item()):
            raise ValueError("G0 reset clock and Synchronizer are inconsistent")
        unresolved = initialized & ~candidate_supervisor.resolved
        if bool((unresolved & (
                candidate_supervisor.event_id
                != candidate_clock.event_index)).any().item()):
            raise ValueError("G0 active event cursors are inconsistent")
        resolved = initialized & candidate_supervisor.resolved
        expected_resolved_event = torch.where(
            candidate_clock.finished,
            candidate_clock.event_index,
            candidate_clock.event_index - 1)
        if bool((resolved & (
                candidate_supervisor.event_id
                != expected_resolved_event)).any().item()):
            raise ValueError("G0 resolved event cursors are inconsistent")
        if bool(candidate_supervisor._before_step_pending.any().item()) or bool(
                candidate_supervisor._resolution_pending.any().item()):
            raise ValueError(
                "G0 checkpoint is not at a completed control-step boundary")

        self.previous_fret_action.copy_(
            validated_actions["previous_fret_action"])
        self.previous_strike_action.copy_(
            validated_actions["previous_strike_action"])
        self.clock.load_state_dict(state["score_clock"])
        self.supervisor.load_state_dict(
            state["synchronizer"], max_event_count=len(self.timeline.events))
        self.source_pair.fret.assert_frozen_integrity()
        self.source_pair.strike.assert_frozen_integrity()
        self._active_event_batch = None


__all__ = [
    "G0_RUNTIME_SCHEMA",
    "G0RuntimeCommand",
    "G0SynchronizationRuntime",
]
