"""CPU-only regression checks for strict fret checkpoint compatibility."""
from copy import deepcopy
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from learning.checkpoint_contract import (  # noqa: E402
    CHECKPOINT_CONTRACT_SCHEMA,
    build_fret_contract_payload,
    canonical_sha256,
    fingerprint_file_set,
    seal_checkpoint_contract,
    verify_checkpoint_contract,
)
from learning.ppo import (  # noqa: E402
    PPOTrainer,
    verify_checkpoint_curriculum_alignment,
)
from learning.run_layout import layout_for  # noqa: E402
import torch  # noqa: E402


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
            "curriculum_stage": "A3_TIMED_CROSSING",
            "curriculum_timing_tolerance_ms": 67,
        },
        "environment_state": {
            "curriculum_stage": "A3_TIMED_CROSSING",
            "timing_tolerance_ms": 67.0,
        },
    })
    expect_error(
        "curriculum state mismatch",
        lambda: verify_checkpoint_curriculum_alignment({
            "training_context": {
                "curriculum_stage": "A3_TIMED_CROSSING",
                "curriculum_timing_tolerance_ms": 67,
            },
            "environment_state": {
                "curriculum_stage": "A2_FREE_CROSSING",
                "timing_tolerance_ms": 100,
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
    print("PASS: strict deterministic checkpoint environment/learning contract")


if __name__ == "__main__":
    main()
