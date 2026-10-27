"""Deterministic, fail-closed checkpoint contracts for fret policies.

A model state dict is not enough to decide whether a checkpoint is safe to
resume or evaluate.  Observation layouts, controlled-DOF ordering, reward
semantics and the fixed-song inputs can all change while tensor shapes remain
loadable.  This module seals those inputs into canonical JSON and verifies both
the checkpoint's internal integrity and equality with the live environment.

The module intentionally has no Isaac Gym dependency so its compatibility
logic can be exercised by a small CPU-only unit test.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping


CHECKPOINT_CONTRACT_SCHEMA = "tab2body.fret_checkpoint_contract.v2"
LEGACY_FRET_CHECKPOINT_CONTRACT_SCHEMA = (
    "tab2body.fret_checkpoint_contract.v1")
STRIKE_CHECKPOINT_CONTRACT_SCHEMA = "tab2body.strike_checkpoint_contract.v14"
LEGACY_STRIKE_CHECKPOINT_CONTRACT_SCHEMA = (
    "tab2body.strike_checkpoint_contract.v13")
OLDER_STRIKE_CHECKPOINT_CONTRACT_SCHEMA = (
    "tab2body.strike_checkpoint_contract.v12")
OLDEST_STRIKE_CHECKPOINT_CONTRACT_SCHEMA = (
    "tab2body.strike_checkpoint_contract.v11")
SUPPORTED_CHECKPOINT_CONTRACT_SCHEMAS = {
    CHECKPOINT_CONTRACT_SCHEMA,
    LEGACY_FRET_CHECKPOINT_CONTRACT_SCHEMA,
    STRIKE_CHECKPOINT_CONTRACT_SCHEMA,
    LEGACY_STRIKE_CHECKPOINT_CONTRACT_SCHEMA,
    OLDER_STRIKE_CHECKPOINT_CONTRACT_SCHEMA,
    OLDEST_STRIKE_CHECKPOINT_CONTRACT_SCHEMA,
}
SCALAR_ADVANTAGE_VERSION = (
    "reward_weighted_value_heads_then_single_global_standardization.v1")
STRIKE_POLICY_TRANSFER_ALLOWED_DIFFERENCE_PREFIXES = (
    "schema",
    "objective",
    "model.policy_init_std",
    "config.model.policy_init_std",
    "config.objective",
    "config.strike.reward",
    "config.strike.curriculum",
    "config.strike.evaluation",
    "config.strike.timing_reward_contract",
    "config.strike.strum_motion_contract",
    "config.strike.metric_contract",
    "config.strike.curriculum_contract",
    "config.strike.success_event",
    "fingerprints.implementation",
    "fingerprints.config_sha256",
)
STRIKE_POLICY_TRANSFER_ALLOWED_EXACT_DIFFERENCE_PATHS = (
    "config.ppo.completed_strike_lr_multiplier",
)


def _json_value(value: Any) -> Any:
    """Convert a contract value to a strict, portable JSON value."""
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return value
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        value = float(value)
        if not math.isfinite(value):
            raise ValueError("checkpoint contract cannot contain NaN or Inf")
        return value
    # Numpy scalar support without importing numpy into this pure helper.
    if hasattr(value, "item"):
        return _json_value(value.item())
    raise TypeError(
        f"unsupported checkpoint contract value: {type(value).__name__}")


def canonical_json(value: Any) -> str:
    """Return the one canonical JSON representation used for all signatures."""
    return json.dumps(
        _json_value(value), sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False)


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def file_sha256(path: Path | str) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fingerprint_file_set(project_root: Path | str,
                         entries: Iterable[Path | str]) -> dict[str, Any]:
    """Hash an explicit deterministic set of files/directories.

    Manifest paths are relative to ``project_root`` so moving the workspace does
    not invalidate a checkpoint.  Missing inputs fail immediately rather than
    silently producing a different, incomplete manifest.
    """
    root = Path(project_root).resolve()
    files: dict[str, Path] = {}
    for entry in entries:
        path = (root / entry).resolve()
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"fingerprint entry escapes project root: {entry}") from exc
        if not path.exists():
            raise FileNotFoundError(f"checkpoint fingerprint input missing: {path}")
        candidates = [path] if path.is_file() else sorted(
            candidate for candidate in path.rglob("*") if candidate.is_file())
        for candidate in candidates:
            relative = candidate.relative_to(root).as_posix()
            files[relative] = candidate
    manifest = [
        {"path": relative, "bytes": files[relative].stat().st_size,
         "sha256": file_sha256(files[relative])}
        for relative in sorted(files)
    ]
    if not manifest:
        raise ValueError("checkpoint fingerprint file set is empty")
    return {"sha256": canonical_sha256(manifest), "manifest": manifest}


def build_fret_contract_payload(*, controlled_dof_names: Iterable[str],
                                num_obs: int, num_actions: int, value_dim: int,
                                action_scale: float, action_alpha: float,
                                reset_soft_limit_fraction: float,
                                policy_init_std: float,
                                raw_reward_weights: Iterable[float],
                                active_string_mask: Iterable[bool],
                                actor_reward_weights: Iterable[float],
                                reward_safety_config: Mapping[str, Any],
                                ppo_config: Mapping[str, Any],
                                preparation_frames: int,
                                sim_hz: int, sim_substeps: int,
                                goal_sha256: str,
                                hand_targets_sha256: str | None,
                                asset_fingerprint: Mapping[str, Any],
                                implementation_fingerprint: Mapping[str, Any],
                                policy_distribution_version: str,
                                observation_contract: str =
                                "fret.observation.v1",
                                observation_manifest: Iterable[str] | None = None,
                                model_architecture_version: str =
                                "actor_critic.mlp.v1") -> dict[str, Any]:
    """Build the semantic payload later sealed into a checkpoint contract."""
    names = [str(name) for name in controlled_dof_names]
    raw_weights = [float(value) for value in raw_reward_weights]
    active = [bool(value) for value in active_string_mask]
    actor_weights = [float(value) for value in actor_reward_weights]
    num_obs = int(num_obs)
    num_actions = int(num_actions)
    value_dim = int(value_dim)
    action_scale = float(action_scale)
    action_alpha = float(action_alpha)
    reset_soft_limit_fraction = float(reset_soft_limit_fraction)
    policy_init_std = float(policy_init_std)
    preparation_frames = int(preparation_frames)
    sim_hz = int(sim_hz)
    sim_substeps = int(sim_substeps)
    policy_distribution_version = str(policy_distribution_version)
    observation_contract = str(observation_contract)
    model_architecture_version = str(model_architecture_version)
    manifest = ([str(field) for field in observation_manifest]
                if observation_manifest is not None
                else [f"fret_v1.legacy_index.{index:03d}"
                      for index in range(num_obs)])
    if num_obs <= 0 or num_actions <= 0 or value_dim <= 0:
        raise ValueError("model dimensions must be positive")
    if not math.isfinite(action_scale) or action_scale <= 0.0:
        raise ValueError("action_scale must be finite and positive")
    if not math.isfinite(action_alpha) or not 0.0 <= action_alpha <= 1.0:
        raise ValueError("action_alpha must be finite and in [0, 1]")
    if (not math.isfinite(reset_soft_limit_fraction)
            or not 0.0 <= reset_soft_limit_fraction < 0.5):
        raise ValueError("reset_soft_limit_fraction must be finite and in [0, 0.5)")
    if not math.isfinite(policy_init_std) or policy_init_std <= 0.0:
        raise ValueError("policy_init_std must be finite and positive")
    if preparation_frames < 0 or sim_hz <= 0 or sim_substeps <= 0:
        raise ValueError("timing values must be non-negative/positive")
    if not policy_distribution_version:
        raise ValueError("policy_distribution_version must be non-empty")
    if observation_contract not in (
            "fret.observation.v1", "fret.observation.v2"):
        raise ValueError("unsupported fret observation contract")
    if not model_architecture_version:
        raise ValueError("model_architecture_version must be non-empty")
    if len(manifest) != num_obs or len(set(manifest)) != num_obs:
        raise ValueError(
            "observation manifest must contain num_obs unique fields")
    if len(names) != num_actions:
        raise ValueError("controlled DOF name count must equal num_actions")
    if len(set(names)) != len(names):
        raise ValueError("controlled DOF names must be unique and ordered")
    if not (len(raw_weights) == len(active) == len(actor_weights) == value_dim):
        raise ValueError("reward weights, active mask and actor weights must match value_dim")
    if not all(math.isfinite(value) for value in raw_weights + actor_weights):
        raise ValueError("reward weights must be finite")
    if any(value < 0.0 for value in actor_weights):
        raise ValueError("actor reward weights must be non-negative")
    if not math.isclose(sum(actor_weights), 1.0, rel_tol=1e-6, abs_tol=1e-6):
        raise ValueError("actor reward weights must sum to one")
    if any((not enabled) and abs(weight) > 1e-12
           for enabled, weight in zip(active, actor_weights)):
        raise ValueError("inactive strings must have zero actor reward weight")
    for name, digest in (("goal_sha256", goal_sha256),
                         ("hand_targets_sha256", hand_targets_sha256)):
        if digest is not None and (len(digest) != 64
                                   or any(c not in "0123456789abcdef" for c in digest)):
            raise ValueError(f"{name} must be a lowercase SHA-256 digest or null")

    model_contract = {
        "num_obs": num_obs,
        "num_actions": num_actions,
        "value_dim": value_dim,
        "policy_distribution_version": policy_distribution_version,
        "policy_init_std": policy_init_std,
        "model_architecture_version": model_architecture_version,
    }
    observation_contract_payload = {
        "schema": observation_contract,
        "dimension": num_obs,
        "manifest": manifest,
        "manifest_sha256": canonical_sha256(manifest),
    }
    control_contract = {
        "controlled_dof_names": names,
        "action_scale": action_scale,
        "action_alpha": action_alpha,
        "reset_soft_limit_fraction": reset_soft_limit_fraction,
    }
    objective_contract = {
        "raw_reward_weights": raw_weights,
        "active_string_mask": active,
        "actor_reward_weights": actor_weights,
        "scalar_advantage_version": SCALAR_ADVANTAGE_VERSION,
    }
    semantic_config = {
        "model": model_contract,
        "observation": observation_contract_payload,
        "control": control_contract,
        "objective": objective_contract,
        "reward_safety": reward_safety_config,
        "ppo": ppo_config,
        "timing": {
            "preparation_frames": preparation_frames,
            "sim_hz": sim_hz,
            "sim_substeps": sim_substeps,
        },
    }
    payload = {
        "schema": CHECKPOINT_CONTRACT_SCHEMA,
        "task": "fret",
        "model": model_contract,
        "observation": observation_contract_payload,
        "control": control_contract,
        "objective": objective_contract,
        "inputs": {
            "goal_sha256": goal_sha256,
            "hand_targets_sha256": hand_targets_sha256,
        },
        "config": _json_value(semantic_config),
        "fingerprints": {
            "asset": _json_value(asset_fingerprint),
            "implementation": _json_value(implementation_fingerprint),
            "config_sha256": canonical_sha256(semantic_config),
        },
    }
    return _json_value(payload)


def build_strike_contract_payload(
        *, controlled_dof_names: Iterable[str],
        num_obs: int, num_actions: int, value_dim: int,
        action_scale: float, action_alpha: float,
        reset_soft_limit_fraction: float, policy_init_std: float,
        strike_config: Mapping[str, Any], ppo_config: Mapping[str, Any],
        observation_manifest: Iterable[str],
        goal_sha256: str, grip_reference_sha256: str,
        asset_fingerprint: Mapping[str, Any],
        implementation_fingerprint: Mapping[str, Any],
        policy_distribution_version: str,
        sim_hz: int, sim_substeps: int) -> dict[str, Any]:
    """Build the independent semantic contract for a virtual-pick policy."""
    names = [str(name) for name in controlled_dof_names]
    observation_manifest = [str(name) for name in observation_manifest]
    num_obs = int(num_obs)
    num_actions = int(num_actions)
    value_dim = int(value_dim)
    if len(names) != num_actions or len(set(names)) != len(names):
        raise ValueError(
            "strike controlled DOF names must be unique and equal num_actions")
    if num_obs <= 0 or num_actions <= 0 or value_dim != 1:
        raise ValueError(
            "strike model dimensions must be positive with scalar value_dim=1")
    if not observation_manifest:
        raise ValueError("strike observation manifest cannot be empty")
    if len(set(observation_manifest)) != len(observation_manifest):
        raise ValueError("strike observation manifest entries must be unique")
    for label, digest in (
            ("goal_sha256", goal_sha256),
            ("grip_reference_sha256", grip_reference_sha256)):
        if (len(str(digest)) != 64
                or any(c not in "0123456789abcdef" for c in str(digest))):
            raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    for label, value in (
            ("action_scale", action_scale),
            ("policy_init_std", policy_init_std)):
        if not math.isfinite(float(value)) or float(value) <= 0.0:
            raise ValueError(f"{label} must be finite and positive")
    if (not math.isfinite(float(action_alpha))
            or not 0.0 <= float(action_alpha) <= 1.0):
        raise ValueError("action_alpha must be finite and in [0,1]")
    if (not math.isfinite(float(reset_soft_limit_fraction))
            or not 0.0 <= float(reset_soft_limit_fraction) < 0.5):
        raise ValueError(
            "reset_soft_limit_fraction must be finite and in [0,0.5)")
    if int(sim_hz) <= 0 or int(sim_substeps) <= 0:
        raise ValueError("strike simulation rates must be positive")

    model = {
        "num_obs": num_obs,
        "num_actions": num_actions,
        "value_dim": value_dim,
        "policy_distribution_version": str(policy_distribution_version),
        "policy_init_std": float(policy_init_std),
    }
    control = {
        "controlled_dof_names": names,
        "action_scale": float(action_scale),
        "action_alpha": float(action_alpha),
        "reset_soft_limit_fraction": float(reset_soft_limit_fraction),
    }
    semantic_config = {
        "model": model,
        "control": control,
        "objective": {
            "value_heads": ["strike_scalar"],
            "scalar_advantage_version": SCALAR_ADVANTAGE_VERSION,
        },
        "observation_manifest": observation_manifest,
        "strike": _json_value(strike_config),
        "ppo": _json_value(ppo_config),
        "timing": {
            "sim_hz": int(sim_hz),
            "sim_substeps": int(sim_substeps),
        },
    }
    payload = {
        "schema": STRIKE_CHECKPOINT_CONTRACT_SCHEMA,
        "task": "strike",
        "model": model,
        "control": control,
        "objective": semantic_config["objective"],
        "inputs": {
            "goal_sha256": str(goal_sha256),
            "grip_reference_sha256": str(grip_reference_sha256),
        },
        "config": semantic_config,
        "fingerprints": {
            "asset": _json_value(asset_fingerprint),
            "implementation": _json_value(implementation_fingerprint),
            "config_sha256": canonical_sha256(semantic_config),
        },
    }
    return _json_value(payload)


def seal_checkpoint_contract(payload: Mapping[str, Any]) -> dict[str, Any]:
    payload = _json_value(payload)
    if payload.get("schema") not in SUPPORTED_CHECKPOINT_CONTRACT_SCHEMAS:
        raise ValueError(
            f"unsupported checkpoint contract schema: {payload.get('schema')!r}")
    return {"payload": payload, "sha256": canonical_sha256(payload)}


def _flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key in sorted(value):
            path = f"{prefix}.{key}" if prefix else str(key)
            result.update(_flatten(value[key], path))
        return result
    if isinstance(value, list):
        result = {}
        for index, item in enumerate(value):
            result.update(_flatten(item, f"{prefix}[{index}]"))
        if not value:
            result[prefix] = []
        return result
    return {prefix: value}


def contract_differences(saved_payload: Mapping[str, Any],
                         expected_payload: Mapping[str, Any]) -> list[str]:
    saved = _flatten(_json_value(saved_payload))
    expected = _flatten(_json_value(expected_payload))
    differences = []
    for key in sorted(set(saved) | set(expected)):
        if key not in saved:
            differences.append(f"{key}: missing in checkpoint")
        elif key not in expected:
            differences.append(f"{key}: unexpected checkpoint field")
        elif saved[key] != expected[key]:
            differences.append(
                f"{key}: checkpoint={saved[key]!r}, live={expected[key]!r}")
    return differences


def validate_contract_document(contract: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(contract, Mapping):
        raise ValueError("checkpoint_contract must be an object")
    if set(contract) != {"payload", "sha256"}:
        raise ValueError("checkpoint_contract must contain only payload and sha256")
    payload = _json_value(contract["payload"])
    if payload.get("schema") not in SUPPORTED_CHECKPOINT_CONTRACT_SCHEMAS:
        raise ValueError(
            f"unsupported checkpoint contract schema: {payload.get('schema')!r}")
    actual = canonical_sha256(payload)
    if contract["sha256"] != actual:
        raise ValueError(
            "checkpoint contract integrity failure: payload SHA-256 does not match")
    return {"payload": payload, "sha256": actual}


def checkpoint_evaluation_hyperparameters(
        checkpoint: Mapping[str, Any]) -> tuple[float, dict[str, Any]]:
    """Read the exact policy-init/PPO settings for strike evaluation.

    The checkpoint contract remains authoritative even when a run used smoke
    or custom PPO settings.  This helper is Isaac-free so integrity and
    fail-closed behavior can be tested on CPU before model construction.
    """
    if (not isinstance(checkpoint, Mapping)
            or "checkpoint_contract" not in checkpoint):
        raise ValueError(
            "evaluation checkpoint must contain checkpoint_contract")
    payload = validate_contract_document(
        checkpoint["checkpoint_contract"])["payload"]
    if payload.get("task") != "strike":
        raise ValueError("evaluation checkpoint is not a strike policy")
    model = payload.get("model")
    config = payload.get("config")
    if not isinstance(model, dict) or not isinstance(config, dict):
        raise ValueError("strike checkpoint contract lacks model/config")
    ppo = config.get("ppo")
    if not isinstance(ppo, dict) or not ppo:
        raise ValueError("strike checkpoint contract lacks PPO settings")
    try:
        initial_std = float(model["policy_init_std"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            "strike checkpoint contract lacks policy_init_std") from exc
    if not math.isfinite(initial_std) or initial_std <= 0.0:
        raise ValueError(
            "strike checkpoint policy_init_std must be finite and positive")
    return initial_std, deepcopy(ppo)


def verify_checkpoint_contract(checkpoint: Mapping[str, Any],
                               expected_contract: Mapping[str, Any],
                               purpose: str = "resume") -> None:
    """Reject legacy, tampered or incompatible checkpoints before state loading."""
    if "checkpoint_contract" not in checkpoint:
        raise ValueError(
            f"cannot {purpose} legacy checkpoint: required checkpoint_contract is "
            "missing; start a new run with the current environment")
    saved = validate_contract_document(checkpoint["checkpoint_contract"])
    expected = validate_contract_document(expected_contract)
    if saved["sha256"] == expected["sha256"]:
        return
    differences = contract_differences(saved["payload"], expected["payload"])
    detail = "; ".join(differences[:8])
    if len(differences) > 8:
        detail += f"; ... and {len(differences) - 8} more"
    raise ValueError(
        f"checkpoint contract mismatch; refusing to {purpose}. {detail}")


def verify_strike_policy_initialization_contract(
        checkpoint: Mapping[str, Any],
        expected_contract: Mapping[str, Any]) -> None:
    """Verify a policy-only strike transfer without weakening strict resume.

    A policy transfer deliberately starts a new optimizer, critic, curriculum
    and environment trajectory, so reward/curriculum/metric semantics may
    change.  Everything that determines how the copied actor interprets its
    observations and actions remains exact.  Unknown differences fail closed;
    adding a new exception requires extending the documented prefix list
    below rather than silently broadening this check.
    """
    if "checkpoint_contract" not in checkpoint:
        raise ValueError(
            "policy initialization requires a checkpoint_contract")
    saved = validate_contract_document(checkpoint["checkpoint_contract"])[
        "payload"]
    expected = validate_contract_document(expected_contract)["payload"]
    required_paths = (
        ("task",),
        ("model", "num_obs"),
        ("model", "num_actions"),
        ("model", "value_dim"),
        ("model", "policy_distribution_version"),
        ("control",),
        ("inputs", "goal_sha256"),
        ("inputs", "grip_reference_sha256"),
        ("config", "observation_manifest"),
        ("config", "timing"),
        ("config", "strike", "grip_control"),
        ("config", "strike", "direction_profile"),
        ("config", "strike", "transition_profile"),
        ("config", "strike", "recovery_contract"),
        ("config", "strike", "pick_representation"),
        ("config", "strike", "string_representation"),
        ("fingerprints", "asset"),
    )

    missing = object()

    def value_at(payload, path):
        value = payload
        for key in path:
            if not isinstance(value, Mapping) or key not in value:
                return missing
            value = value[key]
        return value

    differences = []
    for path in required_paths:
        source = value_at(saved, path)
        target = value_at(expected, path)
        if source is missing or target is missing:
            differences.append(
                f"{'.'.join(path)}: required policy interface field is missing")
        elif source != target:
            differences.append(
                f"{'.'.join(path)}: checkpoint={source!r}, live={target!r}")

    maintenance_lr_path = (
        "config", "ppo", "completed_strike_lr_multiplier")
    source_maintenance_lr = value_at(saved, maintenance_lr_path)
    if (source_maintenance_lr is not missing
            and (isinstance(source_maintenance_lr, bool)
                 or not isinstance(source_maintenance_lr, (int, float))
                 or not math.isfinite(float(source_maintenance_lr)))):
        differences.append(
            ".".join(maintenance_lr_path)
            + ": must be a finite number when present")

    def allowed(path):
        return (
            path in STRIKE_POLICY_TRANSFER_ALLOWED_EXACT_DIFFERENCE_PATHS
            or any(
                path == prefix
                or path.startswith(prefix + ".")
                or path.startswith(prefix + "[")
                for prefix in STRIKE_POLICY_TRANSFER_ALLOWED_DIFFERENCE_PREFIXES))

    for difference in contract_differences(saved, expected):
        path = difference.split(":", 1)[0]
        if not allowed(path):
            differences.append(difference)
    if differences:
        differences = list(dict.fromkeys(differences))
        detail = "; ".join(differences[:8])
        if len(differences) > 8:
            detail += f"; ... and {len(differences) - 8} more"
        raise ValueError(
            "strike policy initialization interface mismatch; "
            + detail)


def strike_s2_policy_transfer_spec(
        checkpoint: Mapping[str, Any],
        expected_contract: Mapping[str, Any],
        *, required_source_iteration: int | None = None) -> dict[str, Any]:
    """Return the audited policy-only transfer plan for an S2 checkpoint.

    The returned tensor list is intentionally limited to the actor,
    observation normalizer and learned exploration standard deviation.  It is
    suitable for logging beside a new run; it is not a resume operation.
    """
    verify_strike_policy_initialization_contract(checkpoint, expected_contract)
    if not isinstance(checkpoint, Mapping):
        raise TypeError("S2 policy initialization checkpoint must be a mapping")
    source_iteration = checkpoint.get("iteration")
    if isinstance(source_iteration, bool):
        raise ValueError("S2 policy initialization iteration must be an integer")
    try:
        source_iteration = int(source_iteration)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(
            "S2 policy initialization checkpoint lacks an iteration") from exc
    if source_iteration < 1:
        raise ValueError("S2 policy initialization iteration must be positive")
    if (required_source_iteration is not None
            and source_iteration != int(required_source_iteration)):
        raise ValueError(
            "S2 policy initialization source iteration mismatch: "
            f"checkpoint={source_iteration}, "
            f"required={int(required_source_iteration)}")

    context = checkpoint.get("training_context")
    environment = checkpoint.get("environment_state")
    if not isinstance(context, Mapping) or not isinstance(environment, Mapping):
        raise ValueError(
            "S2 policy initialization requires training_context and "
            "environment_state")
    source_stage = context.get("curriculum_stage")
    environment_stage = environment.get("curriculum_stage")
    if (source_stage not in ("S1_STRUM_SPAN", "S2_TIMED_STRUM")
            or environment_stage != source_stage):
        raise ValueError(
            "S2 policy initialization requires aligned S1-final or S2-entry state; "
            f"training_context={source_stage!r}, "
            f"environment_state={environment_stage!r}")
    raw_span = environment.get(
        "strum_span", context.get("curriculum_strum_span"))
    if isinstance(raw_span, bool):
        raise ValueError("S2 policy initialization strum span must be 6")
    try:
        source_span = int(raw_span)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(
            "S2 policy initialization checkpoint lacks strum span") from exc
    if source_span != 6:
        raise ValueError(
            "S2 policy initialization requires a learned six-string span")
    stalled = bool(
        context.get("curriculum_stalled", False)
        or environment.get("curriculum_stalled", False))
    if stalled:
        raise ValueError(
            "S2 policy initialization refuses a stalled source checkpoint")
    if source_stage == "S2_TIMED_STRUM":
        stage_iteration = context.get("curriculum_stage_iteration")
        evidence_episodes = context.get("curriculum_evidence_episodes")
        if (isinstance(stage_iteration, bool)
                or isinstance(evidence_episodes, bool)):
            raise ValueError(
                "S2 entry checkpoint has invalid stage/evidence counters")
        try:
            stage_iteration = int(stage_iteration)
            evidence_episodes = int(evidence_episodes)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(
                "S2 entry checkpoint lacks stage/evidence counters") from exc
        if stage_iteration != 0 or evidence_episodes != 0:
            raise ValueError(
                "S2 policy initialization refuses a later S2 checkpoint; "
                "source must have stage_iteration=0 and no S2 evidence")
    elif context.get("curriculum_last_evidence_passed") is not True:
        raise ValueError(
            "S1 policy initialization source must be a final passed S1 checkpoint")

    model = checkpoint.get("model")
    if not isinstance(model, Mapping):
        raise ValueError("S2 policy initialization checkpoint lacks model state")
    selected = tuple(sorted(
        key for key in model
        if key == "log_std"
        or key.startswith("actor.")
        or key.startswith("obs_rms.")))
    required_groups = {
        "actor": any(key.startswith("actor.") for key in selected),
        "obs_rms.mean": "obs_rms.mean" in selected,
        "obs_rms.var": "obs_rms.var" in selected,
        "obs_rms.count": "obs_rms.count" in selected,
        "log_std": "log_std" in selected,
    }
    missing_groups = [name for name, present in required_groups.items()
                      if not present]
    if missing_groups:
        raise ValueError(
            "S2 policy initialization checkpoint is missing policy tensors: "
            + ", ".join(missing_groups))
    if any(key.startswith("critic.") for key in selected):
        raise AssertionError("critic tensors entered the policy transfer plan")
    for key in selected:
        tensor = model[key]
        try:
            finite = bool(tensor.detach().isfinite().all().item())
        except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
            raise ValueError(
                f"S2 policy initialization tensor {key!r} is not a tensor") from exc
        if not finite:
            raise ValueError(
                f"S2 policy initialization tensor {key!r} is nonfinite")
    try:
        expected_payload = validate_contract_document(expected_contract)[
            "payload"]
        expected_num_obs = int(expected_payload["model"]["num_obs"])
        expected_num_actions = int(expected_payload["model"]["num_actions"])
        log_std_size = int(model["log_std"].numel())
        obs_mean_size = int(model["obs_rms.mean"].numel())
        obs_var_size = int(model["obs_rms.var"].numel())
        obs_count_size = int(model["obs_rms.count"].numel())
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            "S2 policy initialization tensor dimensions are invalid") from exc
    if log_std_size != expected_num_actions:
        raise ValueError(
            "S2 policy initialization source std size does not match actions")
    if (obs_mean_size != expected_num_obs
            or obs_var_size != expected_num_obs
            or obs_count_size != 1):
        raise ValueError(
            "S2 policy initialization observation normalizer shape mismatch")
    if not bool((model["obs_rms.var"] > 0).all().item()):
        raise ValueError(
            "S2 policy initialization observation variance must be positive")
    if not bool((model["obs_rms.count"] > 0).all().item()):
        raise ValueError(
            "S2 policy initialization observation count must be positive")

    return {
        "schema": "tab2body.strike_policy_transfer.v1",
        "mode": "s2_actor_obs_rms_source_std",
        "source_iteration": source_iteration,
        "source_stage": source_stage,
        "source_strum_span": source_span,
        "source_contract_sha256": checkpoint[
            "checkpoint_contract"]["sha256"],
        "target_contract_sha256": validate_contract_document(
            expected_contract)["sha256"],
        "allowed_semantic_difference_prefixes": list(
            STRIKE_POLICY_TRANSFER_ALLOWED_DIFFERENCE_PREFIXES),
        "copied_model_tensors": list(selected),
        "copied_source_log_std": True,
        "reset_critic": True,
        "reset_optimizer": True,
        "reset_curriculum": True,
        "reset_environment_state": True,
        "reset_environment_rng": True,
        "ignored_checkpoint_sections": [
            "optimizer", "training_context", "environment_state"],
    }


def copy_validated_contract(contract: Mapping[str, Any]) -> dict[str, Any]:
    """Return an isolated validated copy suitable for ``torch.save``."""
    return deepcopy(validate_contract_document(contract))
