"""Fail-closed loading of song-specific frozen Fret-v2 and Strike-v2 skills."""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Mapping

import torch

from tab2body.fret_v2_contract import (
    FRET_V2_OBSERVATION_CONTRACT,
    FRET_V2_OBSERVATION_DIM,
    fret_v2_block_manifest,
)
from tab2body.learning.checkpoint_contract import (
    CHECKPOINT_CONTRACT_SCHEMA,
    STRIKE_CHECKPOINT_CONTRACT_SCHEMA,
    canonical_sha256,
    file_sha256,
    validate_contract_document,
)
from tab2body.learning.fret_v2_model import (
    FRET_V2_MODEL_ARCHITECTURE,
    FretV2ActorCritic,
)
from tab2body.learning.strike_v2_model import (
    STRIKE_V2_MODEL_ARCHITECTURE,
    StrikeV2ActorCritic,
)
from tab2body.learning.models import POLICY_DISTRIBUTION_VERSION
from tab2body.strike_v2_contract import (
    STRIKE_V2_OBSERVATION_CONTRACT,
    STRIKE_V2_OBSERVATION_DIM,
    strike_v2_block_manifest,
)


SOURCE_POLICY_SCHEMA = "tab2body.frozen_source_pair.v2"
SOURCE_QUALIFICATION_SCHEMA = "tab2body.g0_source_qualification.v1"
SOURCE_EXECUTION_CONTEXT_SCHEMA = "tab2body.source_execution_context.v1"
_SHARED_ASSET_PATHS = (
    "assets/smpl_mpl_hands_body.xml",
    "assets/guitar_asset.xml",
    "assets/seated_pose.json",
    "_gen/mjcf_gains.json",
)


def _require_mapping(value, label):
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return value


def _bundle_manifest(bundle_path):
    root = Path(bundle_path).resolve()
    path = root / "manifest.json"
    if not path.is_file():
        raise FileNotFoundError(f"song bundle manifest not found: {path}")
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("schema") != "tab2body.song_bundle.v1":
        raise ValueError("unsupported song bundle manifest schema")
    song_id = document.get("song_id")
    if not isinstance(song_id, str) or not song_id or root.name != song_id:
        raise ValueError("song bundle directory and manifest song_id disagree")
    files = _require_mapping(document.get("files"), "song bundle files")
    return root, document, files


def _verified_bundle_file(root, files, relative_path):
    record = _require_mapping(
        files.get(relative_path), f"bundle file record {relative_path}")
    expected = record.get("sha256")
    if not isinstance(expected, str) or len(expected) != 64:
        raise ValueError(f"bundle file lacks SHA-256: {relative_path}")
    path = root / relative_path
    if not path.is_file():
        raise FileNotFoundError(f"song bundle file not found: {path}")
    actual = file_sha256(path)
    if actual != expected:
        raise ValueError(
            f"song bundle file SHA-256 mismatch: {relative_path}")
    return path, actual


def _checkpoint_load(path, device):
    path = Path(path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"source checkpoint not found: {path}")
    try:
        checkpoint = torch.load(
            str(path), map_location=device, weights_only=True)
    except TypeError as exc:
        raise RuntimeError(
            "secure source loading requires torch.load(weights_only=True)") from exc
    if not isinstance(checkpoint, Mapping):
        raise ValueError("source checkpoint must be an object")
    if "checkpoint_contract" not in checkpoint or "model" not in checkpoint:
        raise ValueError(
            "source checkpoint requires model and checkpoint_contract")
    contract = validate_contract_document(checkpoint["checkpoint_contract"])
    state = _require_mapping(checkpoint["model"], "checkpoint model state")
    for name, value in state.items():
        if not isinstance(value, torch.Tensor):
            raise ValueError(f"checkpoint model entry is not a tensor: {name}")
        if value.is_floating_point() and not torch.isfinite(value).all():
            raise ValueError(f"checkpoint model tensor is non-finite: {name}")
    return path, checkpoint, contract


def _validate_shared_assets(payload, package_root):
    fingerprint = _require_mapping(
        _require_mapping(payload.get("fingerprints"), "fingerprints").get(
            "asset"), "asset fingerprint")
    manifest = fingerprint.get("manifest")
    if not isinstance(manifest, list):
        raise ValueError("source checkpoint lacks asset fingerprint manifest")
    records = {
        item.get("path"): item for item in manifest
        if isinstance(item, Mapping) and isinstance(item.get("path"), str)
    }
    for relative in _SHARED_ASSET_PATHS:
        record = records.get(relative)
        if not isinstance(record, Mapping):
            raise ValueError(
                f"source checkpoint asset fingerprint omits {relative}")
        path = Path(package_root) / relative
        if not path.is_file() or file_sha256(path) != record.get("sha256"):
            raise ValueError(
                f"live shared asset does not match source checkpoint: {relative}")


@dataclass(frozen=True)
class SourceQualification:
    task: str
    curriculum_stage: str
    qualified_for_g0: bool
    reasons: tuple
    evidence_sealed: bool
    training_context_sha256: str

    def to_document(self):
        return {
            "task": self.task,
            "curriculum_stage": self.curriculum_stage,
            "qualified_for_g0": self.qualified_for_g0,
            "reasons": list(self.reasons),
            "evidence_sealed": self.evidence_sealed,
            "training_context_sha256": self.training_context_sha256,
        }


class FrozenSourcePolicy:
    """Read-only native actor with an explicit observation-view adapter."""

    def __init__(self, *, task, model, checkpoint_path, checkpoint_sha256,
                 contract, action_names, observation_manifest,
                 qualification, execution_context):
        self.task = str(task)
        self.model = model
        self.checkpoint_path = Path(checkpoint_path)
        self.checkpoint_sha256 = str(checkpoint_sha256)
        self.contract = contract
        self.contract_sha256 = contract["sha256"]
        self.action_names = tuple(action_names)
        self.observation_manifest = tuple(observation_manifest)
        self.observation_index = {
            name: index for index, name in enumerate(self.observation_manifest)
        }
        self.qualification = qualification
        self.execution_context = dict(execution_context)
        self.model.eval()
        self.model.requires_grad_(False)
        self._seal_integrity()

    @property
    def obs_dim(self):
        return len(self.observation_manifest)

    @property
    def action_dim(self):
        return len(self.action_names)

    def _seal_integrity(self):
        self._parameter_signature = tuple(
            (name, id(value), value.data_ptr(), value._version)
            for name, value in self.model.named_parameters())
        self._buffer_signature = tuple(
            (name, id(value), value.data_ptr(), value._version)
            for name, value in self.model.named_buffers())

    def assert_frozen_integrity(self):
        parameters = tuple(
            (name, id(value), value.data_ptr(), value._version)
            for name, value in self.model.named_parameters())
        buffers = tuple(
            (name, id(value), value.data_ptr(), value._version)
            for name, value in self.model.named_buffers())
        if parameters != self._parameter_signature or buffers != self._buffer_signature:
            raise RuntimeError(f"frozen {self.task} policy state was mutated")
        if self.model.training or any(
                parameter.requires_grad for parameter in self.model.parameters()):
            raise RuntimeError(f"frozen {self.task} policy left eval/frozen mode")

    def _history_names(self):
        prefix = f"{self.task}_v2.history.previous_executed_action."
        return tuple(prefix + name for name in self.action_names)

    def prepare_observation(self, observation, *, previous_executed_action,
                            timing_shift_s=None):
        """Create the exact native source view used for deterministic inference.

        The existing checkpoints saw Synchronizer channels only at ``(1, 0)``;
        varying them would be a severe normalized OOD input.  Hard permission
        therefore stays outside the actor.  Strike delay is represented in its
        ordinary trained time-to-target/window fields.
        """
        if not isinstance(observation, torch.Tensor) or observation.shape[-1:] != (
                self.obs_dim,):
            raise ValueError(
                f"{self.task} observation must end in dimension {self.obs_dim}")
        if observation.ndim != 2:
            raise ValueError(f"{self.task} observation must have shape [N,obs]")
        if observation.dtype != torch.float32 or not torch.isfinite(
                observation).all():
            raise ValueError(
                f"{self.task} observation must be finite float32")
        previous = torch.as_tensor(
            previous_executed_action, device=observation.device,
            dtype=observation.dtype)
        if previous.shape != (observation.shape[0], self.action_dim):
            raise ValueError(
                f"previous {self.task} action has the wrong shape")
        if not torch.isfinite(previous).all():
            raise ValueError(f"previous {self.task} action must be finite")
        parameter = next(self.model.parameters(), None)
        if parameter is not None and parameter.device != observation.device:
            raise ValueError(
                f"{self.task} observation and policy must share a device")

        result = observation.clone()
        sync_prefix = f"{self.task}_v2.synchronizer."
        release_name = sync_prefix + "release_enable"
        offset_name = sync_prefix + "timing_offset_s"
        try:
            result[:, self.observation_index[release_name]] = 1.0
            result[:, self.observation_index[offset_name]] = 0.0
            history_indices = [
                self.observation_index[name] for name in self._history_names()]
        except KeyError as exc:
            raise RuntimeError(
                f"{self.task} observation manifest lacks the frozen-source bridge") from exc
        result[:, history_indices] = previous

        if timing_shift_s is not None:
            shift = torch.as_tensor(
                timing_shift_s, dtype=result.dtype, device=result.device)
            if shift.shape != (result.shape[0],) or not torch.isfinite(shift).all():
                raise ValueError("timing_shift_s must be finite with shape [N]")
            if self.task == "strike":
                for name in (
                        "strike_v2.event.time_to_target_s",
                        "strike_v2.event.window_open_delta_s",
                        "strike_v2.event.window_close_delta_s"):
                    index = self.observation_index.get(name)
                    if index is None:
                        raise RuntimeError(
                            f"Strike-v2 manifest lacks timing field {name}")
                    result[:, index] = (
                        result[:, index] + shift).clamp(-1.0, 2.0)
            elif bool((shift != 0.0).any().item()):
                # Fret delay is enforced by the outer phase/action bridge; its
                # dense goal view cannot safely be retimed by changing one field.
                pass
        return result

    @torch.no_grad()
    def deterministic_action(self, native_observation):
        self.assert_frozen_integrity()
        distribution = self.model.distribution(native_observation)
        action = torch.tanh(distribution.mean)
        if action.shape != (native_observation.shape[0], self.action_dim):
            raise RuntimeError(f"{self.task} actor output shape changed")
        if action.dtype != torch.float32 or not torch.isfinite(action).all():
            raise RuntimeError(f"{self.task} actor produced an invalid action")
        return action

    def to_reference_document(self, project_root):
        root = Path(project_root).resolve()
        try:
            relative = self.checkpoint_path.resolve().relative_to(root).as_posix()
        except ValueError as exc:
            raise ValueError(
                f"{self.task} checkpoint is outside the project root") from exc
        return {
            "task": self.task,
            "path": relative,
            "file_sha256": self.checkpoint_sha256,
            "checkpoint_contract_sha256": self.contract_sha256,
            "observation_dimension": self.obs_dim,
            "action_names": list(self.action_names),
            "qualification": self.qualification.to_document(),
            "execution_context": dict(self.execution_context),
        }


@dataclass(frozen=True)
class FrozenSkillPair:
    song_id: str
    bundle_path: Path
    fret: FrozenSourcePolicy
    strike: FrozenSourcePolicy
    fps: int
    sim_substeps: int

    @property
    def qualified_for_g0(self):
        return (
            self.fret.qualification.qualified_for_g0
            and self.strike.qualification.qualified_for_g0)


def _training_context(checkpoint):
    context = checkpoint.get("training_context")
    if context is None:
        return {}
    if not isinstance(context, Mapping):
        raise ValueError("checkpoint training_context must be an object")
    return dict(context)


def _source_execution_context(task, context):
    context_sha = canonical_sha256(context)
    result = {
        "schema": SOURCE_EXECUTION_CONTEXT_SCHEMA,
        "task": task,
        "training_context_sha256": context_sha,
        "curriculum_stage": str(context.get("curriculum_stage", "unknown")),
    }
    if task == "fret":
        preparation = context.get("preparation_frames", 60)
        if isinstance(preparation, bool):
            raise ValueError("Fret preparation_frames must be an integer")
        result["preparation_frames"] = int(preparation)
        if result["preparation_frames"] < 0:
            raise ValueError("Fret preparation_frames must be non-negative")
    else:
        numeric = {}
        for output_name, context_name in (
                ("tempo_lambda", "curriculum_tempo_lambda"),
                ("timing_tolerance_ms", "curriculum_timing_tolerance_ms"),
                ("approach_lead_s", "curriculum_approach_lead_s")):
            try:
                number = float(context.get(context_name, -1.0))
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Strike {context_name} must be numeric") from exc
            if not math.isfinite(number):
                raise ValueError(f"Strike {context_name} must be finite")
            numeric[output_name] = number
        span = context.get("curriculum_strum_span", -1)
        if isinstance(span, bool):
            raise ValueError("Strike curriculum_strum_span must be an integer")
        result.update({
            "curriculum_complete": (
                context.get("curriculum_complete") is True),
            "tempo_lambda": numeric["tempo_lambda"],
            "timing_tolerance_ms": numeric["timing_tolerance_ms"],
            "approach_lead_s": numeric["approach_lead_s"],
            "strum_span": int(span),
            "timing_profile": str(
                context.get("curriculum_s2_profile_name", "unknown")),
        })
    return result


def _source_qualification(task, checkpoint, contract):
    context = _training_context(checkpoint)
    stage_value = context.get("curriculum_stage", "unknown")
    stage = stage_value if isinstance(stage_value, str) else "invalid"
    reasons = []
    stalled = context.get("curriculum_stalled", False)
    if not isinstance(stalled, bool):
        reasons.append("invalid_curriculum_stalled_type")
    elif stalled:
        reasons.append("curriculum_stalled")
    if task == "fret":
        if stage != "full_song":
            reasons.append("fret_not_at_full_song_stage")
    else:
        if stage != "S3_SONG_INTEGRATION":
            reasons.append("strike_not_at_song_integration_stage")
        if context.get("curriculum_complete") is not True:
            reasons.append("strike_curriculum_incomplete")
        try:
            tempo = float(context.get("curriculum_tempo_lambda", -1.0))
        except (TypeError, ValueError):
            tempo = -1.0
        if not math.isfinite(tempo) or abs(tempo - 1.0) > 1e-9:
            reasons.append("strike_not_at_original_tempo")
    context_sha = canonical_sha256(context)
    attestation = contract["payload"].get("g0_qualification")
    evidence_sealed = attestation is not None
    if attestation is None:
        reasons.append("qualification_not_sealed_in_checkpoint_contract")
    else:
        attestation = _require_mapping(
            attestation, "sealed G0 source qualification")
        expected_keys = {
            "schema", "task", "training_context_sha256",
            "curriculum_stage", "evaluation_passed",
        }
        if set(attestation) != expected_keys:
            raise ValueError(
                "sealed G0 qualification field set is incompatible")
        if (attestation.get("schema") != SOURCE_QUALIFICATION_SCHEMA
                or attestation.get("task") != task
                or attestation.get("training_context_sha256") != context_sha
                or attestation.get("curriculum_stage") != stage
                or not isinstance(attestation.get("evaluation_passed"), bool)):
            raise ValueError("sealed G0 qualification does not match checkpoint")
        if attestation["evaluation_passed"] is not True:
            reasons.append("g0_source_evaluation_not_passed")
    return SourceQualification(
        task=task, curriculum_stage=stage,
        qualified_for_g0=not reasons, reasons=tuple(reasons),
        evidence_sealed=evidence_sealed,
        training_context_sha256=context_sha)


def inspect_source_checkpoint_metadata(task, checkpoint, contract):
    """Return qualification and execution facts bound to one checkpoint.

    Qualification is deliberately fail-closed: mutable training diagnostics
    may describe an integration probe, but only an attestation inside the
    validated checkpoint contract can authorize physical G0 evaluation.
    """
    if task not in ("fret", "strike"):
        raise ValueError("source task must be fret or strike")
    context = _training_context(checkpoint)
    return (
        _source_qualification(task, checkpoint, contract),
        _source_execution_context(task, context),
    )


def _load_one(task, path, device, *, bundle_root, bundle_files,
              package_root):
    checkpoint_path, checkpoint, contract = _checkpoint_load(path, device)
    payload = contract["payload"]
    if payload.get("task") != task:
        raise ValueError(f"expected a {task} checkpoint")
    model_payload = _require_mapping(payload.get("model"), "model contract")
    if model_payload.get(
            "policy_distribution_version") != POLICY_DISTRIBUTION_VERSION:
        raise ValueError(
            f"{task} source policy distribution contract is incompatible")
    control = _require_mapping(payload.get("control"), "control contract")
    inputs = _require_mapping(payload.get("inputs"), "input contract")
    action_names = tuple(control.get("controlled_dof_names", ()))
    if len(action_names) != 30 or len(set(action_names)) != 30:
        raise ValueError(f"{task} source must expose 30 unique action names")
    if float(control.get("action_scale", -1.0)) != 1.0:
        raise ValueError(f"{task} source action_scale must be 1.0 for G0")
    if float(control.get("action_alpha", -1.0)) != 0.5:
        raise ValueError(f"{task} source action_alpha must be 0.5 for G0")
    if float(control.get("reset_soft_limit_fraction", -1.0)) != 0.02:
        raise ValueError(
            f"{task} source reset soft-limit contract is incompatible with G0")
    _validate_shared_assets(payload, package_root)

    if task == "fret":
        if payload.get("schema") != CHECKPOINT_CONTRACT_SCHEMA:
            raise ValueError("G0 requires the current Fret checkpoint contract")
        observation = _require_mapping(
            payload.get("observation"), "Fret observation contract")
        schema = observation.get("schema")
        manifest = tuple(observation.get("manifest", ()))
        architecture = model_payload.get("model_architecture_version")
        expected_manifest = tuple(
            value for block in fret_v2_block_manifest(action_names).values()
            for value in block)
        if (schema != FRET_V2_OBSERVATION_CONTRACT
                or int(model_payload.get("num_obs", -1))
                != FRET_V2_OBSERVATION_DIM
                or int(model_payload.get("num_actions", -1)) != 30
                or int(model_payload.get("value_dim", -1)) != 6
                or architecture != FRET_V2_MODEL_ARCHITECTURE
                or manifest != expected_manifest):
            raise ValueError("Fret source observation/model ABI is incompatible")
        _, fret_goal_sha = _verified_bundle_file(
            bundle_root, bundle_files, "training/fret_training.json")
        _, hand_sha = _verified_bundle_file(
            bundle_root, bundle_files, "training/hand_position_targets.json")
        if (inputs.get("goal_sha256") != fret_goal_sha
                or inputs.get("hand_targets_sha256") != hand_sha):
            raise ValueError("Fret checkpoint belongs to different song inputs")
        model = FretV2ActorCritic(
            FRET_V2_OBSERVATION_DIM, 30, value_dim=6,
            init_std=float(model_payload["policy_init_std"]))
    else:
        if payload.get("schema") != STRIKE_CHECKPOINT_CONTRACT_SCHEMA:
            raise ValueError("G0 requires the current Strike checkpoint contract")
        config = _require_mapping(payload.get("config"), "Strike config contract")
        strike_config = _require_mapping(
            config.get("strike"), "Strike semantic config")
        schema = strike_config.get("observation_contract")
        manifest = tuple(config.get("observation_manifest", ()))
        architecture = strike_config.get("model_architecture")
        expected_manifest = tuple(
            value for block in strike_v2_block_manifest(action_names).values()
            for value in block)
        if (schema != STRIKE_V2_OBSERVATION_CONTRACT
                or int(model_payload.get("num_obs", -1))
                != STRIKE_V2_OBSERVATION_DIM
                or int(model_payload.get("num_actions", -1)) != 30
                or int(model_payload.get("value_dim", -1)) != 1
                or architecture != STRIKE_V2_MODEL_ARCHITECTURE
                or manifest != expected_manifest):
            raise ValueError("Strike source observation/model ABI is incompatible")
        _, strike_goal_sha = _verified_bundle_file(
            bundle_root, bundle_files, "training/strike_plan.json")
        if inputs.get("goal_sha256") != strike_goal_sha:
            raise ValueError("Strike checkpoint belongs to different song inputs")
        from tab2body.strike_cfg import STRIKE
        grip_path = Path(STRIKE["grip_reference_path"]).resolve()
        if (not grip_path.is_file()
                or file_sha256(grip_path)
                != inputs.get("grip_reference_sha256")):
            raise ValueError("live pick-grip reference differs from checkpoint")
        model = StrikeV2ActorCritic(
            STRIKE_V2_OBSERVATION_DIM, 30, value_dim=1,
            init_std=float(model_payload["policy_init_std"]))

    model.to(device=device, dtype=torch.float32)
    model.load_state_dict(checkpoint["model"], strict=True)
    qualification, execution_context = inspect_source_checkpoint_metadata(
        task, checkpoint, contract)
    source = FrozenSourcePolicy(
        task=task, model=model, checkpoint_path=checkpoint_path,
        checkpoint_sha256=file_sha256(checkpoint_path), contract=contract,
        action_names=action_names, observation_manifest=manifest,
        qualification=qualification, execution_context=execution_context)
    return source, payload


def load_frozen_skill_pair(*, song_id, bundle_path, fret_checkpoint,
                           strike_checkpoint, device="cpu"):
    """Load and cross-check a song-specific source pair without Isaac Gym."""
    bundle_root, bundle_document, bundle_files = _bundle_manifest(bundle_path)
    if str(song_id) != bundle_document["song_id"]:
        raise ValueError("requested song_id does not match song bundle")
    package_root = Path(__file__).resolve().parents[1]
    fret, fret_payload = _load_one(
        "fret", fret_checkpoint, device, bundle_root=bundle_root,
        bundle_files=bundle_files, package_root=package_root)
    strike, strike_payload = _load_one(
        "strike", strike_checkpoint, device, bundle_root=bundle_root,
        bundle_files=bundle_files, package_root=package_root)
    if set(fret.action_names) & set(strike.action_names):
        raise ValueError("Fret and Strike checkpoints claim overlapping joints")

    fret_timing = _require_mapping(
        _require_mapping(fret_payload.get("config"), "Fret config").get(
            "timing"), "Fret timing")
    strike_timing = _require_mapping(
        _require_mapping(strike_payload.get("config"), "Strike config").get(
            "timing"), "Strike timing")
    fps = int(fret_timing.get("sim_hz", -1))
    substeps = int(fret_timing.get("sim_substeps", -1))
    if (fps != 60 or substeps != 4
            or int(strike_timing.get("sim_hz", -1)) != fps
            or int(strike_timing.get("sim_substeps", -1)) != substeps):
        raise ValueError("source policies do not share the G0 physics clock")
    return FrozenSkillPair(
        song_id=str(song_id), bundle_path=bundle_root,
        fret=fret, strike=strike, fps=fps, sim_substeps=substeps)


__all__ = [
    "FrozenSkillPair",
    "FrozenSourcePolicy",
    "SOURCE_POLICY_SCHEMA",
    "SOURCE_EXECUTION_CONTEXT_SCHEMA",
    "SOURCE_QUALIFICATION_SCHEMA",
    "SourceQualification",
    "inspect_source_checkpoint_metadata",
    "load_frozen_skill_pair",
]
