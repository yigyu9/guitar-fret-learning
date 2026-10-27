"""Isaac-free source-action postprocessing for the fixed-guitar G0 player.

The frozen Fret and Strike actors were trained with deterministic action
transforms outside their neural networks.  Reusing only the actor weights
would therefore change the source skills:

* Fret transfers a small flexion delta to an *available* adjacent finger.
* Strike constrains every right-hand joint around the authored pick grip.

This module reproduces those transforms without owning a simulator.  A future
single-simulator backend supplies its local controlled-joint names/ranges and,
for Fret, prepares the current per-finger state before each actor call.  The
objects themselves implement ``callback(action, previous_action)`` and can be
passed directly to :class:`tab2body.full.runtime.G0SynchronizationRuntime`.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from numbers import Real
from pathlib import Path
from typing import Mapping, Sequence
import xml.etree.ElementTree as ET

import torch

from tab2body.env.rewards.fret import (
    adjacent_finger_action_synergy,
    finger_synergy_follower_mask,
)
from tab2body.env.rewards.strike import constrain_pick_grip_actions
from tab2body.learning.checkpoint_contract import (
    CHECKPOINT_CONTRACT_SCHEMA,
    STRIKE_CHECKPOINT_CONTRACT_SCHEMA,
    canonical_sha256,
    file_sha256,
    validate_contract_document,
)


SOURCE_POSTPROCESSING_SCHEMA = "tab2body.g0_source_postprocessing.v2"
SOURCE_ACTION_DIM = 30
FRET_FINGER_ORDER = ("index", "middle", "ring", "pinky")
FRET_FLEXION_ACTION_NAMES = tuple(
    (f"LH:{finger}1_x", f"LH:{finger}2", f"LH:{finger}3")
    for finger in FRET_FINGER_ORDER
)


def _finite_float(value, label, *, positive=False):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{label} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be a finite number")
    if positive and result <= 0.0:
        raise ValueError(f"{label} must be positive")
    return result


def _name_tuple(value: Sequence[str], label: str) -> tuple:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{label} must be an ordered name sequence")
    result = tuple(value)
    if (len(result) != SOURCE_ACTION_DIM
            or any(not isinstance(name, str) or not name for name in result)
            or len(set(result)) != len(result)):
        raise ValueError(
            f"{label} must contain {SOURCE_ACTION_DIM} unique non-empty names")
    return result


def validate_source_backend_action_alignment(
        source_action_names: Sequence[str],
        backend_action_names: Sequence[str]) -> tuple:
    """Fail unless a backend local action view exactly matches its source ABI.

    Name-set equality is insufficient: all range/reference tensors are ordered,
    so even a harmless-looking permutation would apply a correction to the
    wrong physical joint.
    """
    source = _name_tuple(source_action_names, "source_action_names")
    backend = _name_tuple(backend_action_names, "backend_action_names")
    if source != backend:
        mismatch = next(
            index for index, pair in enumerate(zip(source, backend))
            if pair[0] != pair[1])
        raise ValueError(
            "source/backend action-name order mismatch at index "
            f"{mismatch}: source={source[mismatch]!r}, "
            f"backend={backend[mismatch]!r}")
    return source


def _require_mapping(value, label):
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return value


def _validated_source_payload(contract, *, task, schema):
    document = validate_contract_document(contract)
    payload = document["payload"]
    if payload.get("schema") != schema or payload.get("task") != task:
        raise ValueError(
            f"expected current {task} checkpoint contract for postprocessing")
    return payload


def _checkpoint_asset_sha256(payload, relative_path):
    fingerprints = _require_mapping(
        payload.get("fingerprints"), "source fingerprints")
    asset = _require_mapping(fingerprints.get("asset"), "source asset fingerprint")
    manifest = asset.get("manifest")
    if not isinstance(manifest, list):
        raise ValueError("source checkpoint lacks an asset manifest")
    matches = [
        record for record in manifest
        if isinstance(record, Mapping) and record.get("path") == relative_path
    ]
    if len(matches) != 1:
        raise ValueError(
            f"source asset manifest must contain exactly one {relative_path}")
    digest = matches[0].get("sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError(f"source asset digest is invalid: {relative_path}")
    return digest


def _mjcf_control_limits(path, action_names):
    path = Path(path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"humanoid MJCF not found: {path}")
    root = ET.parse(str(path)).getroot()
    compiler = root.find("compiler")
    angle = "degree" if compiler is None else compiler.get("angle", "degree")
    if angle not in ("degree", "radian"):
        raise ValueError(f"unsupported MJCF angle unit: {angle!r}")
    scale = math.pi / 180.0 if angle == "degree" else 1.0
    records = {}
    for joint in root.iter("joint"):
        name = joint.get("name")
        range_text = joint.get("range")
        if not name or range_text is None:
            continue
        try:
            values = tuple(float(value) for value in range_text.split())
        except ValueError as exc:
            raise ValueError(f"invalid MJCF joint range for {name}") from exc
        if len(values) != 2 or not all(math.isfinite(value) for value in values):
            raise ValueError(f"invalid MJCF joint range for {name}")
        if name in records:
            raise ValueError(f"duplicate MJCF joint name: {name}")
        records[name] = (scale * values[0], scale * values[1])
    missing = [name for name in action_names if name not in records]
    if missing:
        raise ValueError(f"MJCF lacks controlled joint ranges: {missing}")
    lower = torch.tensor(
        [records[name][0] for name in action_names], dtype=torch.float64)
    upper = torch.tensor(
        [records[name][1] for name in action_names], dtype=torch.float64)
    if not bool((lower < upper).all().item()):
        raise ValueError("controlled MJCF joint limits must be increasing")
    return path, lower, upper


def _apply_fret_hard_limit_profile(
        path, action_names, authored_lower, authored_upper):
    path = Path(path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Fret hard-limit profile not found: {path}")
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("schema") != "tab2body.fret-human-joint-profile.v1":
        raise ValueError("unsupported Fret hard-limit profile schema")
    joints = document.get("joints")
    if not isinstance(joints, Mapping) or not joints:
        raise ValueError("Fret hard-limit profile has no joints")
    index = {name: offset for offset, name in enumerate(action_names)}
    unknown = [name for name in joints if name not in index]
    if unknown:
        raise ValueError(
            f"Fret hard-limit profile contains non-source joints: {unknown}")
    lower = authored_lower.clone()
    upper = authored_upper.clone()
    tolerance = math.radians(0.02)
    for name, entry in joints.items():
        if not isinstance(entry, Mapping):
            raise ValueError(f"invalid Fret hard-limit entry: {name}")
        try:
            lo = math.radians(float(entry["lower_deg"]))
            hi = math.radians(float(entry["upper_deg"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"invalid Fret hard-limit entry: {name}") from exc
        offset = index[name]
        authored_lo = float(authored_lower[offset])
        authored_hi = float(authored_upper[offset])
        if (not math.isfinite(lo) or not math.isfinite(hi) or lo >= hi
                or lo < authored_lo - tolerance
                or hi > authored_hi + tolerance):
            raise ValueError(f"invalid Fret hard-limit range: {name}")
        lower[offset] = max(lo, authored_lo)
        upper[offset] = min(hi, authored_hi)
    if not bool((lower < upper).all().item()):
        raise ValueError("Fret hard-limit profile produced an empty range")
    return path, lower, upper


def _backend_control_tensor(value, label):
    if (not isinstance(value, torch.Tensor)
            or not value.is_floating_point()
            or value.ndim not in (1, 2)
            or value.shape[-1] != SOURCE_ACTION_DIM):
        raise ValueError(
            f"{label} must be floating [30] or [N,30]")
    if value.dtype != torch.float32:
        raise ValueError(f"{label} must use float32 for the source-policy ABI")
    if not torch.isfinite(value).all():
        raise ValueError(f"{label} must be finite")
    return value.detach().clone()


def _tensor_signature(value):
    raw = value.detach().cpu().contiguous().numpy().tobytes()
    return (
        id(value), value.data_ptr(), value._version, tuple(value.shape),
        str(value.dtype), str(value.device), hashlib.sha256(raw).hexdigest())


def _valid_sha256(value, label):
    if (not isinstance(value, str) or len(value) != 64
            or any(char not in "0123456789abcdef" for char in value)):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    return value


@dataclass(frozen=True)
class SourceActuatorHandshake:
    """Verified local view of the future common 105D actuator."""

    task: str
    action_names: tuple
    backend_control_mid: torch.Tensor
    backend_half_ranges: torch.Tensor
    action_scale: float
    action_alpha: float
    reset_soft_limit_fraction: float
    limit_mode: str
    humanoid_mjcf_sha256: str
    hard_limit_profile_sha256: str | None
    mapping_sha256: str

    def __post_init__(self):
        mid = self.backend_control_mid.detach().clone()
        half = self.backend_half_ranges.detach().clone()
        if mid.dtype != torch.float32 or half.dtype != torch.float32:
            raise ValueError("source actuator handshake tensors must use float32")
        object.__setattr__(self, "backend_control_mid", mid)
        object.__setattr__(self, "backend_half_ranges", half)
        object.__setattr__(self, "_tensor_signatures", (
            _tensor_signature(mid), _tensor_signature(half)))

    def assert_integrity(self):
        current = (
            _tensor_signature(self.backend_control_mid),
            _tensor_signature(self.backend_half_ranges))
        if current != self._tensor_signatures:
            raise RuntimeError(
                f"{self.task} source actuator handshake tensor was mutated")

    def to_manifest(self):
        self.assert_integrity()
        return {
            "task": self.task,
            "action_names": list(self.action_names),
            "action_scale": self.action_scale,
            "action_alpha": self.action_alpha,
            "reset_soft_limit_fraction": self.reset_soft_limit_fraction,
            "limit_mode": self.limit_mode,
            "humanoid_mjcf_sha256": self.humanoid_mjcf_sha256,
            "hard_limit_profile_sha256": self.hard_limit_profile_sha256,
            "mapping_sha256": self.mapping_sha256,
        }


def validate_source_actuator_handshake(
        checkpoint_contract, *, backend_action_names,
        backend_control_mid, backend_control_half_ranges,
        backend_action_scale, backend_action_alpha,
        backend_reset_soft_limit_fraction, humanoid_mjcf_path,
        human_hard_limit_profile_path=None) -> SourceActuatorHandshake:
    """Verify that a backend's normalized action has source-identical meaning.

    Fret checkpoints may narrow their left-hand/elbow/wrist hard limits using a
    profiled range, while Strike uses the authored MJCF limits.  Consequently,
    checking only the 30 names is unsafe; the same normalized number can map to
    a different joint angle.  This handshake reconstructs the checkpoint's
    expected limits and compares both midpoint and half-range tensor values.
    """
    document = validate_contract_document(checkpoint_contract)
    payload = document["payload"]
    task = payload.get("task")
    if task not in ("fret", "strike"):
        raise ValueError("actuator handshake requires a Fret or Strike source")
    control = _require_mapping(payload.get("control"), f"{task} control")
    source_names = control.get("controlled_dof_names", ())
    action_names = validate_source_backend_action_alignment(
        source_names, backend_action_names)
    source_scale = _finite_float(
        control.get("action_scale"), f"{task} source action_scale",
        positive=True)
    source_alpha = _finite_float(
        control.get("action_alpha"), f"{task} source action_alpha")
    source_reset = _finite_float(
        control.get("reset_soft_limit_fraction"),
        f"{task} source reset_soft_limit_fraction")
    backend_scale = _finite_float(
        backend_action_scale, "backend action_scale", positive=True)
    backend_alpha = _finite_float(
        backend_action_alpha, "backend action_alpha")
    backend_reset = _finite_float(
        backend_reset_soft_limit_fraction,
        "backend reset_soft_limit_fraction")
    if (source_scale != backend_scale or source_alpha != backend_alpha
            or source_reset != backend_reset):
        raise ValueError(
            f"{task} source/backend actuator scalar contract mismatch")
    if (not 0.0 <= source_alpha <= 1.0
            or not 0.0 <= source_reset < 0.5):
        raise ValueError(f"{task} source actuator scalar contract is invalid")

    expected_mjcf_sha = _checkpoint_asset_sha256(
        payload, "assets/smpl_mpl_hands_body.xml")
    mjcf_path, lower, upper = _mjcf_control_limits(
        humanoid_mjcf_path, action_names)
    actual_mjcf_sha = file_sha256(mjcf_path)
    if actual_mjcf_sha != expected_mjcf_sha:
        raise ValueError("backend humanoid MJCF differs from source checkpoint")

    profile_sha = None
    limit_mode = "authored_mjcf"
    if task == "fret":
        config = _require_mapping(payload.get("config"), "Fret config")
        safety = _require_mapping(
            config.get("reward_safety"), "Fret reward_safety")
        enabled = safety.get("human_hard_limits_enabled")
        if not isinstance(enabled, bool):
            raise ValueError(
                "Fret checkpoint lacks human_hard_limits_enabled")
        expected_profile_sha = safety.get(
            "human_hard_limit_profile_sha256")
        if enabled:
            if not isinstance(expected_profile_sha, str) \
                    or len(expected_profile_sha) != 64:
                raise ValueError(
                    "Fret checkpoint lacks hard-limit profile SHA-256")
            if human_hard_limit_profile_path is None:
                raise ValueError(
                    "Fret actuator handshake requires its hard-limit profile")
            profile_path, lower, upper = _apply_fret_hard_limit_profile(
                human_hard_limit_profile_path, action_names, lower, upper)
            profile_sha = file_sha256(profile_path)
            if profile_sha != expected_profile_sha:
                raise ValueError(
                    "backend Fret hard-limit profile differs from checkpoint")
            limit_mode = "fret_human_hard_limit_profile"
        elif expected_profile_sha is not None:
            raise ValueError(
                "disabled Fret hard limits must not seal a profile digest")
    elif human_hard_limit_profile_path is not None:
        raise ValueError("Strike actuator must use authored MJCF limits")

    expected_mid = 0.5 * (lower + upper)
    expected_half = 0.5 * (upper - lower)
    backend_mid = _backend_control_tensor(
        backend_control_mid, "backend_control_mid")
    backend_half = _backend_control_tensor(
        backend_control_half_ranges, "backend_control_half_ranges")
    if (backend_mid.shape != backend_half.shape
            or backend_mid.dtype != backend_half.dtype
            or backend_mid.device != backend_half.device
            or bool((backend_half <= 0.0).any().item())):
        raise ValueError(
            "backend midpoint/half-range tensors must share a positive contract")
    expected_mid_like = expected_mid.to(
        device=backend_mid.device, dtype=backend_mid.dtype)
    expected_half_like = expected_half.to(
        device=backend_half.device, dtype=backend_half.dtype)
    if backend_mid.ndim == 2:
        expected_mid_like = expected_mid_like[None].expand_as(backend_mid)
        expected_half_like = expected_half_like[None].expand_as(backend_half)
    if (not torch.allclose(
            backend_mid, expected_mid_like, atol=2e-6, rtol=1e-6)
            or not torch.allclose(
                backend_half, expected_half_like, atol=2e-6, rtol=1e-6)):
        raise ValueError(
            f"backend normalized-to-joint mapping differs from {task} source")
    mapping_sha = canonical_sha256({
        "action_names": list(action_names),
        "control_mid_rad": expected_mid.tolist(),
        "control_half_range_rad": expected_half.tolist(),
        "action_scale": source_scale,
        "action_alpha": source_alpha,
    })
    return SourceActuatorHandshake(
        task=task, action_names=action_names,
        backend_control_mid=backend_mid,
        backend_half_ranges=backend_half,
        action_scale=source_scale, action_alpha=source_alpha,
        reset_soft_limit_fraction=source_reset, limit_mode=limit_mode,
        humanoid_mjcf_sha256=actual_mjcf_sha,
        hard_limit_profile_sha256=profile_sha,
        mapping_sha256=mapping_sha)


def _action_pair(action, previous_action, *, width=SOURCE_ACTION_DIM):
    if not isinstance(action, torch.Tensor) or not isinstance(
            previous_action, torch.Tensor):
        raise TypeError("action and previous_action must be torch tensors")
    if action.ndim != 2 or action.shape[1] != width:
        raise ValueError(f"action must have shape [N,{width}]")
    if previous_action.shape != action.shape:
        raise ValueError("previous_action must have the same shape as action")
    if (not action.is_floating_point()
            or previous_action.dtype != action.dtype):
        raise TypeError("action tensors must share a floating dtype")
    if previous_action.device != action.device:
        raise ValueError("action tensors must share a device")
    if (not torch.isfinite(action).all()
            or not torch.isfinite(previous_action).all()):
        raise ValueError("action tensors must be finite")
    tolerance = 1e-6
    if (bool((action.abs() > 1.0 + tolerance).any().item())
            or bool((previous_action.abs() > 1.0 + tolerance).any().item())):
        raise ValueError("normalized action tensors must remain in [-1,1]")


@dataclass(frozen=True)
class FretSynergyDiagnostics:
    induced_delta_deg: torch.Tensor
    follower_gate: torch.Tensor


@dataclass(frozen=True)
class VerifiedSourceQualification:
    task: str
    curriculum_stage: str
    training_context_sha256: str


def _verified_qualification(value, *, task, final_stage=None):
    """Accept ``SourceQualification`` or its serialized mapping, fail closed."""
    if isinstance(value, Mapping):
        source_task = value.get("task")
        stage = value.get("curriculum_stage")
        qualified = value.get("qualified_for_g0")
        reasons = value.get("reasons", ())
        evidence_sealed = value.get("evidence_sealed")
        context_sha = value.get("training_context_sha256")
    else:
        source_task = getattr(value, "task", None)
        stage = getattr(value, "curriculum_stage", None)
        qualified = getattr(value, "qualified_for_g0", None)
        reasons = getattr(value, "reasons", ())
        evidence_sealed = getattr(value, "evidence_sealed", None)
        context_sha = getattr(value, "training_context_sha256", None)
    if source_task != task or not isinstance(stage, str) or not stage:
        raise ValueError(f"{task} source qualification metadata is invalid")
    if qualified is not True:
        raise ValueError(
            f"unqualified {task} source cannot build a physical G0 "
            f"postprocessor: {tuple(reasons) if reasons else 'unknown reason'}")
    if evidence_sealed is not True:
        raise ValueError(
            f"{task} source qualification is not sealed in its checkpoint contract")
    _valid_sha256(context_sha, f"{task} training-context hash")
    if isinstance(reasons, (str, bytes)) or tuple(reasons):
        raise ValueError(
            f"qualified {task} source must not retain failure reasons")
    if final_stage is not None and stage != final_stage:
        raise ValueError(
            f"{task} postprocessor implements only the {final_stage!r} "
            f"action transform, not stage {stage!r}")
    return VerifiedSourceQualification(
        task=task, curriculum_stage=stage,
        training_context_sha256=context_sha)


class FretSynergyPostprocessor:
    """Per-step adapter for the trained adjacent-finger synergy transform.

    Call :meth:`prepare_step` (or :meth:`prepare_follower_mask`) exactly once
    before each runtime ``before_physics`` call.  Consuming the state prevents
    an old event's follower mask from leaking into the next score frame.
    """

    def __init__(
            self, *, actuator_handshake, coefficients, min_driver_delta_deg,
            full_driver_delta_deg, max_induced_delta_deg,
            source_qualification, source_contract_sha256,
            source_checkpoint_sha256):
        # Earlier Fret curriculum stages also apply stage-specific action masks
        # and scales.  This focused adapter intentionally reproduces only the
        # final full-song transform, so accepting an earlier checkpoint would
        # silently change its physical semantics.
        self.source_qualification = _verified_qualification(
            source_qualification, task="fret", final_stage="full_song")
        if (not isinstance(actuator_handshake, SourceActuatorHandshake)
                or actuator_handshake.task != "fret"):
            raise ValueError(
                "Fret postprocessor requires a verified Fret actuator handshake")
        self.actuator_handshake = actuator_handshake
        self.source_contract_sha256 = _valid_sha256(
            source_contract_sha256, "Fret source contract hash")
        self.source_checkpoint_sha256 = _valid_sha256(
            source_checkpoint_sha256, "Fret source checkpoint hash")
        self.action_names = actuator_handshake.action_names
        action_index = {name: index for index, name in enumerate(
            self.action_names)}
        missing = [
            name for row in FRET_FLEXION_ACTION_NAMES for name in row
            if name not in action_index
        ]
        if missing:
            raise ValueError(
                f"Fret source is missing synergy flexion actions: {missing}")
        self.flexion_action_indices = torch.tensor([
            [action_index[name] for name in row]
            for row in FRET_FLEXION_ACTION_NAMES
        ], dtype=torch.long)
        self.half_ranges = actuator_handshake.backend_half_ranges.clone()
        self.action_scale = actuator_handshake.action_scale
        if (isinstance(coefficients, (str, bytes))
                or not isinstance(coefficients, Sequence)
                or len(coefficients) != 3):
            raise ValueError("Fret synergy coefficients must contain 3 values")
        self.coefficients = tuple(
            _finite_float(value, "Fret synergy coefficient")
            for value in coefficients)
        if any(value < 0.0 or value >= 1.0 for value in self.coefficients):
            raise ValueError("Fret synergy coefficients must be in [0,1)")
        self.min_driver_delta_deg = _finite_float(
            min_driver_delta_deg, "Fret minimum driver delta")
        self.full_driver_delta_deg = _finite_float(
            full_driver_delta_deg, "Fret full driver delta")
        self.max_induced_delta_deg = _finite_float(
            max_induced_delta_deg, "Fret maximum induced delta",
            positive=True)
        if (self.min_driver_delta_deg < 0.0
                or self.min_driver_delta_deg >= self.full_driver_delta_deg):
            raise ValueError("Fret synergy driver thresholds are invalid")
        self._pending_follower_mask = None
        self.last_diagnostics = None
        self._tensor_signatures = (
            _tensor_signature(self.flexion_action_indices),
            _tensor_signature(self.half_ranges))
        self._config_signature = (
            id(self.actuator_handshake), self.action_names, self.coefficients,
            self.min_driver_delta_deg, self.full_driver_delta_deg,
            self.max_induced_delta_deg, self.action_scale,
            self.source_contract_sha256, self.source_checkpoint_sha256,
            self.source_qualification)

    def assert_integrity(self):
        self.actuator_handshake.assert_integrity()
        current = (
            _tensor_signature(self.flexion_action_indices),
            _tensor_signature(self.half_ranges))
        if current != self._tensor_signatures:
            raise RuntimeError("Fret source postprocessor tensor was mutated")
        current_config = (
            id(self.actuator_handshake), self.action_names, self.coefficients,
            self.min_driver_delta_deg, self.full_driver_delta_deg,
            self.max_induced_delta_deg, self.action_scale,
            self.source_contract_sha256, self.source_checkpoint_sha256,
            self.source_qualification)
        if current_config != self._config_signature:
            raise RuntimeError("Fret source postprocessor config was mutated")

    @classmethod
    def from_checkpoint_contract(
            cls, checkpoint_contract, *, backend_action_names,
            backend_control_mid, backend_control_half_ranges,
            backend_action_scale, backend_action_alpha,
            backend_reset_soft_limit_fraction, humanoid_mjcf_path,
            human_hard_limit_profile_path, source_qualification,
            source_checkpoint_sha256):
        """Build the exact transform sealed with a frozen Fret checkpoint."""
        payload = _validated_source_payload(
            checkpoint_contract, task="fret",
            schema=CHECKPOINT_CONTRACT_SCHEMA)
        config = _require_mapping(payload.get("config"), "Fret config")
        safety = _require_mapping(
            config.get("reward_safety"), "Fret reward_safety")
        required = (
            "finger_synergy_coefficients",
            "finger_synergy_min_driver_delta_deg",
            "finger_synergy_full_driver_delta_deg",
            "finger_synergy_max_induced_delta_deg",
        )
        missing = [name for name in required if name not in safety]
        if missing:
            raise ValueError(
                f"Fret checkpoint lacks postprocessing settings: {missing}")
        handshake = validate_source_actuator_handshake(
            checkpoint_contract,
            backend_action_names=backend_action_names,
            backend_control_mid=backend_control_mid,
            backend_control_half_ranges=backend_control_half_ranges,
            backend_action_scale=backend_action_scale,
            backend_action_alpha=backend_action_alpha,
            backend_reset_soft_limit_fraction=
                backend_reset_soft_limit_fraction,
            humanoid_mjcf_path=humanoid_mjcf_path,
            human_hard_limit_profile_path=human_hard_limit_profile_path)
        return cls(
            actuator_handshake=handshake,
            coefficients=safety["finger_synergy_coefficients"],
            min_driver_delta_deg=safety[
                "finger_synergy_min_driver_delta_deg"],
            full_driver_delta_deg=safety[
                "finger_synergy_full_driver_delta_deg"],
            max_induced_delta_deg=safety[
                "finger_synergy_max_induced_delta_deg"],
            source_qualification=source_qualification,
            source_contract_sha256=validate_contract_document(
                checkpoint_contract)["sha256"],
            source_checkpoint_sha256=source_checkpoint_sha256,
        )

    @property
    def manifest(self):
        self.assert_integrity()
        return {
            "schema": SOURCE_POSTPROCESSING_SCHEMA,
            "task": "fret",
            "transform": "adjacent_finger_action_synergy.full_song.v1",
            "action_names": list(self.action_names),
            "source_curriculum_stage": (
                self.source_qualification.curriculum_stage),
            "requires_qualified_source": True,
            "source_contract_sha256": self.source_contract_sha256,
            "source_checkpoint_sha256": self.source_checkpoint_sha256,
            "source_training_context_sha256": (
                self.source_qualification.training_context_sha256),
            "stage_specific_action_mask": False,
            "parameters": {
                "coefficients": list(self.coefficients),
                "min_driver_delta_deg": self.min_driver_delta_deg,
                "full_driver_delta_deg": self.full_driver_delta_deg,
                "max_induced_delta_deg": self.max_induced_delta_deg,
            },
            "actuator_handshake": self.actuator_handshake.to_manifest(),
        }

    @property
    def step_state_prepared(self):
        return self._pending_follower_mask is not None

    def clear_step_state(self):
        self._pending_follower_mask = None

    def prepare_follower_mask(self, follower_allowed: torch.Tensor):
        """Prepare an explicit ``[N,4]`` index/middle/ring/pinky mask."""
        if (not isinstance(follower_allowed, torch.Tensor)
                or follower_allowed.ndim != 2
                or follower_allowed.shape[1] != 4
                or follower_allowed.dtype != torch.bool):
            raise ValueError("follower_allowed must be bool [N,4]")
        if self._pending_follower_mask is not None:
            raise RuntimeError(
                "previous Fret synergy step state has not been consumed")
        self._pending_follower_mask = follower_allowed.detach().clone()
        return self._pending_follower_mask.clone()

    def prepare_step(
            self, *, current_finger_active: torch.Tensor,
            finger_event: torch.Tensor):
        """Derive the exact source-task mask from the current goal projection.

        ``current_finger_active`` uses index/middle/ring/pinky order and means
        "assigned to the current musical target", not measured contact.  The
        13-field ``finger_event`` is the native Fret goal projection; the reused
        helper protects a finger with a current press assignment or an upcoming
        movement.
        """
        if (not isinstance(current_finger_active, torch.Tensor)
                or current_finger_active.ndim != 2
                or current_finger_active.shape[1] != 4
                or current_finger_active.dtype != torch.bool):
            raise ValueError("current_finger_active must be bool [N,4]")
        if (not isinstance(finger_event, torch.Tensor)
                or finger_event.shape != (*current_finger_active.shape, 13)
                or not finger_event.is_floating_point()
                or not torch.isfinite(finger_event).all()):
            raise ValueError("finger_event must be finite floating [N,4,13]")
        if finger_event.device != current_finger_active.device:
            raise ValueError("Fret synergy state tensors must share a device")
        follower = finger_synergy_follower_mask(
            current_finger_active, finger_event)
        return self.prepare_follower_mask(follower)

    def __call__(self, action, previous_action):
        self.assert_integrity()
        _action_pair(action, previous_action)
        follower = self._pending_follower_mask
        if follower is None:
            raise RuntimeError(
                "prepare Fret synergy state before each source actor call")
        if (follower.shape[0] != action.shape[0]
                or follower.device != action.device):
            raise ValueError(
                "prepared Fret synergy state does not match the action batch/device")
        if (self.half_ranges.device != action.device
                or self.half_ranges.dtype != action.dtype):
            raise ValueError(
                "Fret half_ranges must match the source action device/dtype")
        if (self.half_ranges.ndim == 2
                and self.half_ranges.shape[0] != action.shape[0]):
            raise ValueError("batched Fret half_ranges do not match action batch")
        result, induced, gate = adjacent_finger_action_synergy(
            action, previous_action, self.flexion_action_indices,
            follower, self.half_ranges, action_scale=self.action_scale,
            coefficients=self.coefficients,
            min_driver_delta_deg=self.min_driver_delta_deg,
            full_driver_delta_deg=self.full_driver_delta_deg,
            max_induced_delta_deg=self.max_induced_delta_deg)
        self._pending_follower_mask = None
        self.last_diagnostics = FretSynergyDiagnostics(
            induced_delta_deg=induced.detach().clone(),
            follower_gate=gate.detach().clone())
        return result


class StrikePickGripPostprocessor:
    """Checkpoint-matched right-hand residual constraint around a pick grip."""

    def __init__(
            self, *, actuator_handshake, reference_actions,
            pinch_action_names, free_action_names,
            pinch_residual_rad, free_residual_rad, source_qualification,
            grip_reference_sha256, source_contract_sha256,
            source_checkpoint_sha256):
        self.source_qualification = _verified_qualification(
            source_qualification, task="strike")
        if (not isinstance(actuator_handshake, SourceActuatorHandshake)
                or actuator_handshake.task != "strike"):
            raise ValueError(
                "Strike postprocessor requires a verified Strike actuator handshake")
        self.actuator_handshake = actuator_handshake
        self.source_contract_sha256 = _valid_sha256(
            source_contract_sha256, "Strike source contract hash")
        self.source_checkpoint_sha256 = _valid_sha256(
            source_checkpoint_sha256, "Strike source checkpoint hash")
        self.action_names = actuator_handshake.action_names
        action_index = {name: index for index, name in enumerate(
            self.action_names)}
        hand_names = tuple(
            name for name in self.action_names if name.startswith("RH:"))
        if len(hand_names) != 21:
            raise ValueError("Strike source must expose exactly 21 RH hand actions")
        pinch = self._grip_group(
            pinch_action_names, "pinch_action_names", action_index)
        free = self._grip_group(
            free_action_names, "free_action_names", action_index)
        if set(pinch) & set(free):
            raise ValueError("Strike pick-grip groups must be disjoint")
        if set(pinch) | set(free) != set(hand_names):
            raise ValueError(
                "Strike pick-grip groups must cover every RH hand action exactly")

        if (not isinstance(reference_actions, torch.Tensor)
                or not reference_actions.is_floating_point()
                or reference_actions.ndim != 2
                or reference_actions.shape[1] != SOURCE_ACTION_DIM
                or reference_actions.shape[0] < 1):
            raise ValueError(
                "Strike reference_actions must be floating [1,30] or [N,30]")
        if (not torch.isfinite(reference_actions).all()
                or bool((reference_actions.abs() > 1.0 + 1e-6).any().item())):
            raise ValueError(
                "Strike reference_actions must be finite normalized actions")
        self.reference_actions = reference_actions.detach().clone()
        if actuator_handshake.backend_half_ranges.ndim == 2:
            # Every row was verified against the same authored limits.  Grip
            # residual spans are one per action and therefore use one row.
            self.half_ranges = actuator_handshake.backend_half_ranges[0].clone()
        else:
            self.half_ranges = actuator_handshake.backend_half_ranges.clone()
        if (self.half_ranges.device != self.reference_actions.device
                or self.half_ranges.dtype != self.reference_actions.dtype):
            raise ValueError(
                "Strike reference_actions and half_ranges must share device/dtype")
        self.action_scale = actuator_handshake.action_scale
        self.pinch_residual_rad = _finite_float(
            pinch_residual_rad, "Strike pinch residual", positive=True)
        self.free_residual_rad = _finite_float(
            free_residual_rad, "Strike free-finger residual", positive=True)
        if self.pinch_residual_rad >= self.free_residual_rad:
            raise ValueError(
                "Strike pinch residual must be smaller than free-finger residual")
        if (not isinstance(grip_reference_sha256, str)
                or len(grip_reference_sha256) != 64):
            raise ValueError("Strike grip reference SHA-256 is invalid")
        self.grip_reference_sha256 = grip_reference_sha256

        self.hand_mask = torch.tensor(
            [name in set(hand_names) for name in self.action_names],
            dtype=torch.bool, device=self.reference_actions.device)
        self.residual_action_span = torch.zeros_like(self.half_ranges)
        pinch_indices = torch.tensor(
            [action_index[name] for name in pinch], dtype=torch.long,
            device=self.reference_actions.device)
        free_indices = torch.tensor(
            [action_index[name] for name in free], dtype=torch.long,
            device=self.reference_actions.device)
        self.residual_action_span[pinch_indices] = (
            self.pinch_residual_rad
            / (self.action_scale * self.half_ranges[pinch_indices]))
        self.residual_action_span[free_indices] = (
            self.free_residual_rad
            / (self.action_scale * self.half_ranges[free_indices]))
        self.pinch_action_names = pinch
        self.free_action_names = free
        self._tensor_signatures = tuple(_tensor_signature(value) for value in (
            self.reference_actions, self.half_ranges, self.hand_mask,
            self.residual_action_span))
        self._config_signature = (
            id(self.actuator_handshake), self.action_names,
            self.pinch_action_names, self.free_action_names,
            self.pinch_residual_rad, self.free_residual_rad, self.action_scale,
            self.grip_reference_sha256, self.source_contract_sha256,
            self.source_checkpoint_sha256, self.source_qualification)

    def assert_integrity(self):
        self.actuator_handshake.assert_integrity()
        current = tuple(_tensor_signature(value) for value in (
            self.reference_actions, self.half_ranges, self.hand_mask,
            self.residual_action_span))
        if current != self._tensor_signatures:
            raise RuntimeError("Strike source postprocessor tensor was mutated")
        current_config = (
            id(self.actuator_handshake), self.action_names,
            self.pinch_action_names, self.free_action_names,
            self.pinch_residual_rad, self.free_residual_rad, self.action_scale,
            self.grip_reference_sha256, self.source_contract_sha256,
            self.source_checkpoint_sha256, self.source_qualification)
        if current_config != self._config_signature:
            raise RuntimeError("Strike source postprocessor config was mutated")

    @staticmethod
    def _grip_group(values, label, action_index):
        if (isinstance(values, (str, bytes))
                or not isinstance(values, Sequence)):
            raise TypeError(f"{label} must be an ordered name sequence")
        names = tuple(values)
        if (not names or any(
                not isinstance(name, str) or not name for name in names)
                or len(names) != len(set(names))):
            raise ValueError(f"{label} must contain unique non-empty names")
        missing = [name for name in names if name not in action_index]
        if missing:
            raise ValueError(f"{label} contains unknown actions: {missing}")
        return names

    @classmethod
    def from_checkpoint_contract(
            cls, checkpoint_contract, *, backend_action_names,
            backend_control_mid, backend_control_half_ranges,
            backend_action_scale, backend_action_alpha,
            backend_reset_soft_limit_fraction, humanoid_mjcf_path,
            reference_actions, grip_reference_path, source_qualification,
            source_checkpoint_sha256):
        """Build the exact grip transform sealed with a Strike checkpoint."""
        payload = _validated_source_payload(
            checkpoint_contract, task="strike",
            schema=STRIKE_CHECKPOINT_CONTRACT_SCHEMA)
        config = _require_mapping(payload.get("config"), "Strike config")
        strike = _require_mapping(config.get("strike"), "Strike semantics")
        grip = _require_mapping(
            strike.get("grip_control"), "Strike grip_control")
        required = ("pinch_residual_rad", "free_residual_rad")
        missing = [name for name in required if name not in grip]
        if missing:
            raise ValueError(
                f"Strike checkpoint lacks postprocessing settings: {missing}")
        handshake = validate_source_actuator_handshake(
            checkpoint_contract,
            backend_action_names=backend_action_names,
            backend_control_mid=backend_control_mid,
            backend_control_half_ranges=backend_control_half_ranges,
            backend_action_scale=backend_action_scale,
            backend_action_alpha=backend_action_alpha,
            backend_reset_soft_limit_fraction=
                backend_reset_soft_limit_fraction,
            humanoid_mjcf_path=humanoid_mjcf_path)
        grip_path = Path(grip_reference_path).resolve()
        if not grip_path.is_file():
            raise FileNotFoundError(
                f"Strike pick-grip reference not found: {grip_path}")
        expected_grip_sha = _require_mapping(
            payload.get("inputs"), "Strike inputs").get(
                "grip_reference_sha256")
        if file_sha256(grip_path) != expected_grip_sha:
            raise ValueError(
                "Strike pick-grip reference differs from source checkpoint")
        grip_document = json.loads(grip_path.read_text(encoding="utf-8"))
        if grip_document.get("schema") != "tab2body.pick_grip_reference.v1":
            raise ValueError("unsupported Strike pick-grip reference schema")
        groups = _require_mapping(
            grip_document.get("groups"), "Strike pick-grip groups")
        targets = _require_mapping(
            grip_document.get("joint_targets_rad"),
            "Strike pick-grip joint targets")
        hand_names = tuple(
            name for name in handshake.action_names if name.startswith("RH:"))
        if set(targets) != set(hand_names):
            raise ValueError(
                "Strike pick-grip targets do not match source hand actions")
        cls._validate_reference_action_values(
            reference_actions, handshake, targets)
        return cls(
            actuator_handshake=handshake,
            reference_actions=reference_actions,
            pinch_action_names=groups.get("pinch", ()),
            free_action_names=groups.get("free", ()),
            pinch_residual_rad=grip["pinch_residual_rad"],
            free_residual_rad=grip["free_residual_rad"],
            source_qualification=source_qualification,
            grip_reference_sha256=expected_grip_sha,
            source_contract_sha256=validate_contract_document(
                checkpoint_contract)["sha256"],
            source_checkpoint_sha256=source_checkpoint_sha256,
        )

    @staticmethod
    def _validate_reference_action_values(reference_actions, handshake, targets):
        if (not isinstance(reference_actions, torch.Tensor)
                or not reference_actions.is_floating_point()
                or reference_actions.ndim != 2
                or reference_actions.shape[1] != SOURCE_ACTION_DIM):
            raise ValueError(
                "Strike reference_actions must be floating [1,30] or [N,30]")
        mid = handshake.backend_control_mid
        half = handshake.backend_half_ranges
        if mid.ndim == 2:
            mid = mid[0]
            half = half[0]
        mid = mid.to(
            device=reference_actions.device, dtype=reference_actions.dtype)
        half = half.to(
            device=reference_actions.device, dtype=reference_actions.dtype)
        indices = {name: index for index, name in enumerate(
            handshake.action_names)}
        hand_names = tuple(
            name for name in handshake.action_names if name.startswith("RH:"))
        hand_indices = torch.tensor(
            [indices[name] for name in hand_names], dtype=torch.long,
            device=reference_actions.device)
        try:
            target = torch.tensor(
                [float(targets[name]) for name in hand_names],
                dtype=reference_actions.dtype,
                device=reference_actions.device)
        except (TypeError, ValueError) as exc:
            raise ValueError("Strike pick-grip target is not finite") from exc
        if not torch.isfinite(target).all():
            raise ValueError("Strike pick-grip target is not finite")
        normalized = (
            (target - mid[hand_indices])
            / (handshake.action_scale * half[hand_indices]))
        if bool((normalized.abs() > 1.0 + 1e-6).any().item()):
            raise ValueError(
                "Strike pick-grip target lies outside backend hard limits")
        expected = normalized[None].expand(reference_actions.shape[0], -1)
        actual = reference_actions[:, hand_indices]
        if not torch.allclose(actual, expected, atol=2e-6, rtol=1e-6):
            raise ValueError(
                "normalized Strike grip reference differs from source mapping")

    @property
    def manifest(self):
        self.assert_integrity()
        return {
            "schema": SOURCE_POSTPROCESSING_SCHEMA,
            "task": "strike",
            "transform": "pick_grip_residual_constraint.v1",
            "action_names": list(self.action_names),
            "source_curriculum_stage": (
                self.source_qualification.curriculum_stage),
            "requires_qualified_source": True,
            "source_contract_sha256": self.source_contract_sha256,
            "source_checkpoint_sha256": self.source_checkpoint_sha256,
            "source_training_context_sha256": (
                self.source_qualification.training_context_sha256),
            "stage_specific_action_mask": False,
            "grip_reference_sha256": self.grip_reference_sha256,
            "parameters": {
                "pinch_residual_rad": self.pinch_residual_rad,
                "free_residual_rad": self.free_residual_rad,
                "pinch_action_names": list(self.pinch_action_names),
                "free_action_names": list(self.free_action_names),
            },
            "actuator_handshake": self.actuator_handshake.to_manifest(),
        }

    def __call__(self, action, previous_action):
        self.assert_integrity()
        # previous_action is intentionally unused by the static grip transform,
        # but validating it keeps this callback's ABI identical to Fret/runtime.
        _action_pair(action, previous_action)
        if (self.reference_actions.device != action.device
                or self.reference_actions.dtype != action.dtype):
            raise ValueError(
                "Strike grip tensors must match source action device/dtype")
        if self.reference_actions.shape[0] not in (1, action.shape[0]):
            raise ValueError(
                "batched Strike reference_actions do not match action batch")
        return constrain_pick_grip_actions(
            action, self.reference_actions,
            self.residual_action_span, self.hand_mask)


__all__ = [
    "FRET_FINGER_ORDER",
    "FRET_FLEXION_ACTION_NAMES",
    "FretSynergyDiagnostics",
    "FretSynergyPostprocessor",
    "SOURCE_ACTION_DIM",
    "SOURCE_POSTPROCESSING_SCHEMA",
    "SourceActuatorHandshake",
    "StrikePickGripPostprocessor",
    "VerifiedSourceQualification",
    "validate_source_actuator_handshake",
    "validate_source_backend_action_alignment",
]
