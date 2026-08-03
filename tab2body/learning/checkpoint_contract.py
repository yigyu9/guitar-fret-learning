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


CHECKPOINT_CONTRACT_SCHEMA = "tab2body.fret_checkpoint_contract.v1"
STRIKE_CHECKPOINT_CONTRACT_SCHEMA = "tab2body.strike_checkpoint_contract.v1"
SUPPORTED_CHECKPOINT_CONTRACT_SCHEMAS = {
    CHECKPOINT_CONTRACT_SCHEMA,
    STRIKE_CHECKPOINT_CONTRACT_SCHEMA,
}
SCALAR_ADVANTAGE_VERSION = (
    "reward_weighted_value_heads_then_single_global_standardization.v1")


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
                                policy_distribution_version: str) -> dict[str, Any]:
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


def copy_validated_contract(contract: Mapping[str, Any]) -> dict[str, Any]:
    """Return an isolated validated copy suitable for ``torch.save``."""
    return deepcopy(validate_contract_document(contract))
