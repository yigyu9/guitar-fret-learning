from __future__ import annotations

from copy import deepcopy
from pathlib import Path


STRIKE_RUNTIME_IMPLEMENTATION_FILES = (
    "strike_checkpoint.py",
    "strike_contract.py",
    "strike_training_runtime.py",
    "env/base.py",
    "env/collision.py",
    "env/config.py",
    "env/metrics.py",
    "env/safety.py",
    "env/tasks/__init__.py",
    "env/strike_detector.py",
    "env/strike_events.py",
    "env/strike_goal_compiler.py",
    "env/strike_goals.py",
    "env/rewards/strike.py",
    "env/tasks/task_strike.py",
    "learning/checkpoint_contract.py",
    "learning/models.py",
    "learning/ppo.py",
    "learning/strike_curriculum.py",
)

STRIKE_ASSET_FILES = (
    "assets/smpl_mpl_hands_body.xml",
    "assets/guitar_asset.xml",
    "assets/seated_pose.json",
    "assets/mesh",
    "_gen/mjcf_gains.json",
)


def semantic_strike_config(config):
    """Keep task semantics in the contract and omit launch-only settings."""
    selected = (
        "action_scale", "action_alpha", "reset_noise",
        "reset_soft_limit_fraction", "failure_termination_penalty",
        "zone", "trajectory", "detector", "safety",
        "wrong_crossing_termination", "joint_limits", "reward",
        "episode", "curriculum", "evaluation",
    )
    result = {key: deepcopy(config[key]) for key in selected}
    result["direction_profile"] = "down_only_v1"
    result["pick_representation"] = {
        "body": "RH:pick",
        "tip": "RH:pick origin",
        "physical_geometry": False,
        "attachment": "fixed_to_thumb_index_pose",
    }
    result["string_representation"] = "six_fixed_finite_segments"
    result["success_event"] = "debounced_release_immediately_after_crossing"
    return result


def build_runtime_checkpoint_contract(
        env, model, goal_path, *, config, ppo_config=None):
    """Seal every semantic input needed to safely reuse a Strike policy."""
    import torch

    from tab2body.learning.checkpoint_contract import (
        build_strike_contract_payload,
        file_sha256,
        fingerprint_file_set,
        seal_checkpoint_contract,
    )

    package_root = Path(__file__).resolve().parent
    goal_path = Path(goal_path).resolve()
    grip_path = Path(config["grip_reference_path"]).resolve()
    asset_fingerprint = fingerprint_file_set(
        package_root, STRIKE_ASSET_FILES)
    implementation_fingerprint = fingerprint_file_set(
        package_root, STRIKE_RUNTIME_IMPLEMENTATION_FILES)
    initial_std = model.log_std.detach().exp().cpu()
    if initial_std.numel() != env.num_actions or not torch.allclose(
            initial_std, initial_std[:1].expand_as(initial_std)):
        raise ValueError(
            "strike contract requires one shared initial policy std")
    controlled_names = [
        env.dof_names[index]
        for index in env.ctrl_idx.detach().cpu().tolist()]
    payload = build_strike_contract_payload(
        controlled_dof_names=controlled_names,
        num_obs=env.num_obs,
        num_actions=env.num_actions,
        value_dim=env.value_dim,
        action_scale=env.action_scale,
        action_alpha=env.action_alpha,
        reset_soft_limit_fraction=env.reset_soft_limit_fraction,
        policy_init_std=float(initial_std[0]),
        strike_config=semantic_strike_config(config),
        ppo_config=deepcopy(
            ppo_config if ppo_config is not None else config["ppo"]),
        observation_manifest=env.observation_manifest,
        goal_sha256=file_sha256(goal_path),
        grip_reference_sha256=file_sha256(grip_path),
        asset_fingerprint=asset_fingerprint,
        implementation_fingerprint=implementation_fingerprint,
        policy_distribution_version=getattr(
            model, "POLICY_DISTRIBUTION_VERSION",
            "tanh_squashed_diagonal_gaussian.v1"),
        sim_hz=env.SIM_HZ,
        sim_substeps=env.SUBSTEPS,
    )
    return seal_checkpoint_contract(payload)


__all__ = [
    "STRIKE_ASSET_FILES",
    "STRIKE_RUNTIME_IMPLEMENTATION_FILES",
    "build_runtime_checkpoint_contract",
    "semantic_strike_config",
]
