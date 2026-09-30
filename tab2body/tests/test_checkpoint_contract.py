"""CPU-only regression checks for strict fret checkpoint compatibility."""
from copy import deepcopy
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT.parent):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from learning.checkpoint_contract import (  # noqa: E402
    CHECKPOINT_CONTRACT_SCHEMA,
    LEGACY_STRIKE_CHECKPOINT_CONTRACT_SCHEMA,
    STRIKE_CHECKPOINT_CONTRACT_SCHEMA,
    build_fret_contract_payload,
    build_strike_contract_payload,
    canonical_sha256,
    fingerprint_file_set,
    seal_checkpoint_contract,
    strike_s2_policy_transfer_spec,
    verify_checkpoint_contract,
    verify_strike_policy_initialization_contract,
)
from learning.models import ActorCritic  # noqa: E402
from learning.ppo import (  # noqa: E402
    PPOTrainer,
    verify_checkpoint_curriculum_alignment,
)
from learning.run_layout import layout_for  # noqa: E402
import torch  # noqa: E402


def verify_workspace_s2_entry_checkpoint():
    checkpoint_path = (
        ROOT.parent / "strike" / "training" / "runs"
        / "20260830_1928_00_SS1-68-E_comp" / "checkpoints"
        / "strike_003147.pt")
    if not checkpoint_path.is_file():
        return False
    from strike_cfg import STRIKE
    from strike_checkpoint import semantic_strike_config

    checkpoint = torch.load(
        checkpoint_path, map_location="cpu", weights_only=False)
    target_payload = deepcopy(
        checkpoint["checkpoint_contract"]["payload"])
    target_payload["schema"] = STRIKE_CHECKPOINT_CONTRACT_SCHEMA
    source_strike = target_payload["config"]["strike"]
    target_semantic = semantic_strike_config(
        STRIKE,
        direction_profile=source_strike["direction_profile"],
        transition_profile=source_strike["transition_profile"])
    # This workspace artifact predates the explicit v1/v2 observation label.
    # Reproduce its 327D v1 semantic payload for the historical S2-transfer
    # regression; a live 303D v2 contract is intentionally incompatible.
    target_semantic.pop("observation_contract", None)
    target_payload["config"]["strike"] = target_semantic
    target_payload["fingerprints"]["implementation"] = {
        "sha256": "f" * 64, "manifest": []}
    target_payload["fingerprints"]["config_sha256"] = canonical_sha256(
        target_payload["config"])
    spec = strike_s2_policy_transfer_spec(
        checkpoint, seal_checkpoint_contract(target_payload),
        required_source_iteration=3147)
    assert spec["source_stage"] == "S2_TIMED_STRUM"
    assert spec["source_strum_span"] == 6
    assert spec["copied_source_log_std"]
    return True


def payload(**overrides):
    values = dict(
        controlled_dof_names=("L_Shoulder_x", "LH:index1_x"),
        num_obs=341,
        num_actions=2,
        value_dim=6,
        action_scale=1.0,
        action_alpha=0.5,
        reset_soft_limit_fraction=0.02,
        policy_init_std=0.02,
        raw_reward_weights=[1.0 / 6.0] * 6,
        active_string_mask=[False, True, True, True, False, False],
        actor_reward_weights=[0.0, 1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0, 0.0, 0.0],
        reward_safety_config={"press": {"position": 0.2, "contact": 0.5},
                              "failure_penalty": -25.0},
        ppo_config={"gamma": 0.95, "horizon": 32},
        preparation_frames=60,
        sim_hz=60,
        sim_substeps=4,
        goal_sha256="1" * 64,
        hand_targets_sha256="2" * 64,
        asset_fingerprint={"sha256": "3" * 64, "manifest": []},
        implementation_fingerprint={"sha256": "4" * 64, "manifest": []},
        policy_distribution_version="tanh_squashed_diagonal_gaussian.v1",
    )
    values.update(overrides)
    return build_fret_contract_payload(**values)


def expect_error(fragment, callback):
    try:
        callback()
    except ValueError as exc:
        assert fragment in str(exc), (fragment, str(exc))
    else:
        raise AssertionError(f"expected ValueError containing {fragment!r}")


def main():
    first_payload = payload()
    assert first_payload["schema"] == CHECKPOINT_CONTRACT_SCHEMA
    first = seal_checkpoint_contract(first_payload)
    assert first["sha256"] == canonical_sha256(first_payload)

    # Mapping insertion order and workspace location never enter the signature.
    reordered = payload(
        reward_safety_config={"failure_penalty": -25.0,
                              "press": {"contact": 0.5, "position": 0.2}},
        ppo_config={"horizon": 32, "gamma": 0.95})
    second = seal_checkpoint_contract(reordered)
    assert second == first
    verify_checkpoint_contract({"checkpoint_contract": first}, second)

    # A valid but different live environment produces a useful field-level diff.
    changed_payload = deepcopy(first_payload)
    changed_payload["control"]["action_scale"] = 2.0
    changed = seal_checkpoint_contract(changed_payload)
    expect_error(
        "control.action_scale",
        lambda: verify_checkpoint_contract(
            {"checkpoint_contract": first}, changed, purpose="resume"))

    # Editing a saved payload without re-signing is an integrity failure, not a
    # compatibility warning.
    tampered = deepcopy(first)
    tampered["payload"]["inputs"]["goal_sha256"] = "9" * 64
    expect_error(
        "integrity failure",
        lambda: verify_checkpoint_contract({"checkpoint_contract": tampered}, first))

    # Old checkpoints with only a training_context must fail closed for both
    # continuation and deterministic evaluation.
    legacy = {"training_context": {"goal_sha256": "1" * 64}}
    expect_error(
        "legacy checkpoint",
        lambda: verify_checkpoint_contract(legacy, first, purpose="evaluate"))

    verify_checkpoint_curriculum_alignment({
        "training_context": {
            "curriculum_stage": "A3_TIMED_SINGLE",
            "curriculum_timing_tolerance_ms": 67,
            "curriculum_tempo_lambda": 1.0,
            "curriculum_strum_span": 1,
            "curriculum_approach_lead_s": 0.14,
            "curriculum_timing_early_grace_ms": 75.0,
            "curriculum_timing_early_penalty_scale_ms": 150.0,
        },
        "environment_state": {
            "curriculum_stage": "A3_TIMED_SINGLE",
            "timing_tolerance_ms": 67.0,
            "tempo_lambda": 1.0,
            "strum_span": 1,
            "approach_lead_s": 0.14,
            "timing_early_grace_ms": 75.0,
            "timing_early_penalty_scale_ms": 150.0,
        },
    })
    expect_error(
        "curriculum state mismatch",
        lambda: verify_checkpoint_curriculum_alignment({
            "training_context": {
                "curriculum_stage": "A3_TIMED_SINGLE",
                "curriculum_timing_tolerance_ms": 67,
                "curriculum_tempo_lambda": 1.0,
                "curriculum_strum_span": 1,
            },
            "environment_state": {
                "curriculum_stage": "A2_SINGLE_CROSSING",
                "timing_tolerance_ms": 100,
                "tempo_lambda": 1.0,
                "strum_span": 1,
            },
        }))
    expect_error(
        "curriculum_strum_span",
        lambda: verify_checkpoint_curriculum_alignment({
            "training_context": {
                "curriculum_stage": "S1_STRUM_SPAN",
                "curriculum_strum_span": 6,
            },
            "environment_state": {
                "curriculum_stage": "S1_STRUM_SPAN",
                "strum_span": 5,
            },
        }))
    expect_error(
        "curriculum_approach_lead_s",
        lambda: verify_checkpoint_curriculum_alignment({
            "training_context": {
                "curriculum_stage": "S2_TIMED_STRUM",
                "curriculum_approach_lead_s": 0.14,
            },
            "environment_state": {
                "curriculum_stage": "S2_TIMED_STRUM",
                "approach_lead_s": 0.25,
            },
        }))

    # The trainer writes the sealed contract at the checkpoint top level and
    # validates it before loading any model tensor.
    with tempfile.TemporaryDirectory() as directory:
        trainer = PPOTrainer.__new__(PPOTrainer)
        trainer.out_dir = Path(directory)
        trainer.run_layout = layout_for(directory, create=True)
        trainer.checkpoint_dir = trainer.run_layout.checkpoints
        trainer.model = torch.nn.Linear(2, 1)
        trainer.optimizer = torch.optim.Adam(trainer.model.parameters())
        trainer.global_step = 123
        trainer.training_context = {"song_id": "unit"}
        trainer.set_checkpoint_contract(first)
        trainer.save(7)
        checkpoint = torch.load(
            Path(directory) / "checkpoints" / "fret_000007.pt", map_location="cpu",
            weights_only=False)
        assert checkpoint["checkpoint_contract"] == first
        assert (checkpoint["training_context"]["checkpoint_contract_sha256"]
                == first["sha256"])

        restored = PPOTrainer.__new__(PPOTrainer)
        restored.model = torch.nn.Linear(2, 1)
        restored.optimizer = torch.optim.Adam(restored.model.parameters())
        restored.set_checkpoint_contract(first)
        restored.resume(checkpoint, purpose="evaluate")
        assert restored.iteration == 7 and restored.global_step == 123

    # Fingerprints are deterministic and relative: entry order cannot alter the
    # result and absolute workspace paths do not leak into the manifest.
    files_a = fingerprint_file_set(
        ROOT, ("learning/checkpoint_contract.py", "learning/ppo.py"))
    files_b = fingerprint_file_set(
        ROOT, ("learning/ppo.py", "learning/checkpoint_contract.py"))
    assert files_a == files_b
    assert all(not Path(row["path"]).is_absolute() for row in files_a["manifest"])

    expect_error(
        "inactive strings",
        lambda: payload(actor_reward_weights=[0.1, 0.3, 0.3, 0.3, 0.0, 0.0]))

    strike_values = dict(
        controlled_dof_names=("R_Shoulder_x", "RH:index1_x"),
        num_obs=12,
        num_actions=2,
        value_dim=1,
        action_scale=1.0,
        action_alpha=0.5,
        reset_soft_limit_fraction=0.02,
        policy_init_std=0.02,
        strike_config={
            "reward": {"recovery": "dual"},
            "curriculum": {"stage": "old"},
            "evaluation": {"metric": "old"},
            "timing_reward_contract": "centered_timing.v2",
            "strum_motion_contract": "terminal_exit.v1",
            "metric_contract": "raw_direction.v1",
            "curriculum_contract": "endpoint_bridge.v13",
            "grip_control": {"pinch_residual_rad": 0.08},
            "direction_profile": "phrase_dp_microtiming_v3",
            "transition_profile": "entry_side_edge_gap_v2",
            "recovery_contract": "path_aware_clearance_handoff.v1",
            "pick_representation": {"body": "RH:pick"},
            "string_representation": "six_fixed_finite_segments",
            "success_event": "ordered_release",
        },
        ppo_config={"gamma": 0.99,
                    "completed_strike_lr_multiplier": 0.25},
        observation_manifest=tuple(f"obs_{index}" for index in range(12)),
        goal_sha256="5" * 64,
        grip_reference_sha256="6" * 64,
        asset_fingerprint={"sha256": "7" * 64, "manifest": []},
        implementation_fingerprint={"sha256": "8" * 64, "manifest": []},
        policy_distribution_version=(
            "tanh_squashed_masked_diagonal_gaussian.v2"),
        sim_hz=60,
        sim_substeps=4,
    )
    expected_strike = seal_checkpoint_contract(
        build_strike_contract_payload(**strike_values))
    source_payload = deepcopy(expected_strike["payload"])
    source_payload["schema"] = LEGACY_STRIKE_CHECKPOINT_CONTRACT_SCHEMA
    # Older actors predate this training-only PPO option; it does not affect
    # policy inference or the tensors copied by policy transfer.
    source_payload["config"]["ppo"].pop(
        "completed_strike_lr_multiplier")
    source_payload["objective"] = {
        "value_heads": ["legacy_strike_scalar"],
        "scalar_advantage_version": "legacy_scalar_advantage.v1",
    }
    source_payload["config"]["objective"] = deepcopy(
        source_payload["objective"])
    source_payload["config"]["strike"]["reward"] = {"recovery": "fixed"}
    source_payload["config"]["strike"]["curriculum"] = {"stage": "new"}
    source_payload["config"]["strike"]["evaluation"] = {"metric": "new"}
    source_payload["config"]["strike"]["success_event"] = (
        "legacy_ordered_release")
    source_payload["config"]["strike"].pop("strum_motion_contract")
    source_payload["config"]["strike"].pop("metric_contract")
    source_payload["config"]["strike"]["timing_reward_contract"] = (
        "legacy_timing.v1")
    source_payload["config"]["strike"]["curriculum_contract"] = (
        "legacy_curriculum.v12")
    source_payload["fingerprints"]["implementation"] = {
        "sha256": "9" * 64, "manifest": []}
    source_strike = seal_checkpoint_contract(source_payload)
    transfer_checkpoint = {"checkpoint_contract": source_strike}
    verify_strike_policy_initialization_contract(
        transfer_checkpoint, expected_strike)
    changed_maintenance_lr = deepcopy(source_payload)
    changed_maintenance_lr["config"]["ppo"][
        "completed_strike_lr_multiplier"] = 0.5
    verify_strike_policy_initialization_contract(
        {"checkpoint_contract": seal_checkpoint_contract(
            changed_maintenance_lr)}, expected_strike)
    malformed_maintenance_lr = deepcopy(source_payload)
    malformed_maintenance_lr["config"]["ppo"][
        "completed_strike_lr_multiplier"] = {}
    expect_error(
        "must be a finite number",
        lambda: verify_strike_policy_initialization_contract(
            {"checkpoint_contract": seal_checkpoint_contract(
                malformed_maintenance_lr)}, expected_strike))
    incompatible_ppo = deepcopy(source_payload)
    incompatible_ppo["config"]["ppo"]["gamma"] = 0.9
    expect_error(
        "config.ppo.gamma",
        lambda: verify_strike_policy_initialization_contract(
            {"checkpoint_contract": seal_checkpoint_contract(
                incompatible_ppo)}, expected_strike))
    incompatible_payload = deepcopy(source_payload)
    incompatible_payload["inputs"]["goal_sha256"] = "a" * 64
    expect_error(
        "inputs.goal_sha256",
        lambda: verify_strike_policy_initialization_contract(
            {"checkpoint_contract": seal_checkpoint_contract(
                incompatible_payload)}, expected_strike))
    incompatible_transition = deepcopy(source_payload)
    incompatible_transition["config"]["strike"]["transition_profile"] = (
        "entry_side_edge_gap_v1")
    expect_error(
        "config.strike.transition_profile",
        lambda: verify_strike_policy_initialization_contract(
            {"checkpoint_contract": seal_checkpoint_contract(
                incompatible_transition)}, expected_strike))
    incompatible_unknown = deepcopy(source_payload)
    incompatible_unknown["config"]["strike"]["trajectory"] = {
        "exit_across_offset_m": 0.004}
    expect_error(
        "config.strike.trajectory",
        lambda: verify_strike_policy_initialization_contract(
            {"checkpoint_contract": seal_checkpoint_contract(
                incompatible_unknown)}, expected_strike))
    missing_pick = deepcopy(source_payload)
    del missing_pick["config"]["strike"]["pick_representation"]
    expect_error(
        "config.strike.pick_representation",
        lambda: verify_strike_policy_initialization_contract(
            {"checkpoint_contract": seal_checkpoint_contract(
                missing_pick)}, expected_strike))

    source_policy = ActorCritic(12, 2, value_dim=1)
    target_policy = ActorCritic(12, 2, value_dim=1)
    with torch.no_grad():
        for parameter in source_policy.actor.parameters():
            parameter.fill_(0.25)
        for parameter in source_policy.critic.parameters():
            parameter.fill_(0.75)
        source_policy.log_std.fill_(-1.5)
        source_policy.obs_rms.mean.fill_(0.4)
        source_policy.obs_rms.var.fill_(1.4)
        source_policy.obs_rms.count.fill_(123.0)
    target_critic = {
        key: value.clone()
        for key, value in target_policy.critic.state_dict().items()}
    transfer_trainer = PPOTrainer.__new__(PPOTrainer)
    transfer_trainer.model = target_policy
    restored_keys = transfer_trainer.initialize_policy({
        "model": source_policy.state_dict()})
    assert "log_std" in restored_keys and "actor.0.weight" in restored_keys
    assert torch.equal(target_policy.log_std, source_policy.log_std)
    assert torch.equal(
        target_policy.obs_rms.mean, source_policy.obs_rms.mean)
    assert all(torch.equal(value, target_critic[key]) for key, value in (
        target_policy.critic.state_dict().items()))
    transfer_checkpoint.update({
        "iteration": 3147,
        "model": source_policy.state_dict(),
        "training_context": {
            "curriculum_stage": "S2_TIMED_STRUM",
            "curriculum_stage_iteration": 0,
            "curriculum_evidence_episodes": 0,
            "curriculum_stalled": False,
            "curriculum_strum_span": 6,
        },
        "environment_state": {
            "curriculum_stage": "S2_TIMED_STRUM",
            "curriculum_stalled": False,
            "strum_span": 6,
        },
        "optimizer": {"state": "must not transfer"},
    })
    transfer_spec = strike_s2_policy_transfer_spec(
        transfer_checkpoint, expected_strike,
        required_source_iteration=3147)
    assert transfer_spec["mode"] == "s2_actor_obs_rms_source_std"
    assert transfer_spec["source_iteration"] == 3147
    assert transfer_spec["reset_critic"]
    assert transfer_spec["reset_optimizer"]
    assert transfer_spec["reset_curriculum"]
    assert transfer_spec["reset_environment_rng"]
    assert "log_std" in transfer_spec["copied_model_tensors"]
    assert not any(key.startswith("critic.") for key in (
        transfer_spec["copied_model_tensors"]))
    bad_stage_checkpoint = deepcopy(transfer_checkpoint)
    bad_stage_checkpoint["environment_state"] = {
        "curriculum_stage": "S1_STRUM_SPAN", "strum_span": 6}
    expect_error(
        "aligned S1-final or S2-entry",
        lambda: strike_s2_policy_transfer_spec(
            bad_stage_checkpoint, expected_strike))
    late_s2_checkpoint = deepcopy(transfer_checkpoint)
    late_s2_checkpoint["training_context"][
        "curriculum_stage_iteration"] = 1
    expect_error(
        "refuses a later S2 checkpoint",
        lambda: strike_s2_policy_transfer_spec(
            late_s2_checkpoint, expected_strike))
    verify_workspace_s2_entry_checkpoint()
    print("PASS: strict deterministic checkpoint environment/learning contract")


if __name__ == "__main__":
    main()
