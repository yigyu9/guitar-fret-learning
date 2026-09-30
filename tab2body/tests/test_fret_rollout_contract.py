"""CPU regressions for recorder model selection and event evidence."""
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import torch
from tab2body.learning.checkpoint_contract import CHECKPOINT_CONTRACT_SCHEMA, canonical_sha256, file_sha256, seal_checkpoint_contract
from tab2body.learning.fret_v2_model import fret_actor_critic_class
from tab2body.fret_v2_contract import FRET_V2_OBSERVATION_CONTRACT, FRET_V2_OBSERVATION_DIM
from tab2body.tools.fret_rollout_contract import EventEvidence, rollout_configuration, verify_rollout_model


class RolloutTests(unittest.TestCase):
    def test_saved_configuration_and_input_integrity(self):
        with tempfile.TemporaryDirectory() as directory:
            goal = Path(directory) / "goal.json"
            goal.write_text("{}")
            payload = {"schema": CHECKPOINT_CONTRACT_SCHEMA, "task": "fret",
                       "inputs": {"goal_sha256": file_sha256(goal), "hand_targets_sha256": None},
                       "fingerprints": {"asset": {"manifest": []}},
                       "config": {"reward_safety": {"press_hold_min_frames": 9},
                                  "timing": {"preparation_frames": 60}},
                       "control": {"action_scale": .25},
                       "observation": {"schema": FRET_V2_OBSERVATION_CONTRACT}}
            checkpoint = {"checkpoint_contract": seal_checkpoint_contract(payload)}
            defaults = {"press_hold_min_frames": 2, "action_scale": 1.}
            config, _ = rollout_configuration(checkpoint, defaults, goal=goal, hand_targets=None, root=directory)
            self.assertEqual(config["press_hold_min_frames"], 9)
            self.assertEqual(config["action_scale"], .25)
            self.assertEqual(defaults["press_hold_min_frames"], 2)
            goal.write_text('{"changed": true}')
            with self.assertRaisesRegex(ValueError, "goal differs"):
                rollout_configuration(checkpoint, defaults, goal=goal, hand_targets=None, root=directory)

    def test_block_model_state_restores_and_semantics_reject_mismatch(self):
        model_class = fret_actor_critic_class(FRET_V2_OBSERVATION_CONTRACT)
        original = model_class(FRET_V2_OBSERVATION_DIM, 30, 6)
        restored = model_class(FRET_V2_OBSERVATION_DIM, 30, 6)
        restored.load_state_dict(original.state_dict())
        obs = torch.zeros(1, FRET_V2_OBSERVATION_DIM)
        self.assertTrue(torch.equal(original.act(obs, deterministic=True)[0], restored.act(obs, deterministic=True)[0]))
        env = SimpleNamespace(num_obs=FRET_V2_OBSERVATION_DIM, num_actions=30, value_dim=6,
                              observation_manifest=["a"], dof_names=list(map(str, range(30))),
                              ctrl_idx=torch.arange(30), action_scale=1., action_alpha=.5,
                              reset_soft_limit_fraction=.02, SIM_HZ=60, SUBSTEPS=2)
        payload = {"model": {"num_obs": env.num_obs, "num_actions": 30, "value_dim": 6,
                             "model_architecture_version": restored.MODEL_ARCHITECTURE_VERSION,
                             "policy_distribution_version": restored.POLICY_DISTRIBUTION_VERSION},
                   "observation": {"manifest_sha256": canonical_sha256(["a"])},
                   "control": {"controlled_dof_names": env.dof_names, "action_scale": 1.,
                               "action_alpha": .5, "reset_soft_limit_fraction": .02},
                   "config": {"timing": {"sim_hz": 60, "sim_substeps": 2}}}
        verify_rollout_model(env, restored, payload)
        env.dof_names = list(reversed(env.dof_names))
        with self.assertRaisesRegex(ValueError, "joint order"):
            verify_rollout_model(env, restored, payload)

    def test_event_evidence_does_not_attribute_barre_average(self):
        evidence = EventEvidence()
        goal = {"fret": [2, 0], "finger": [1, 0], "sustain_event_id": [4, -1], "sustain_eligible": [True, False]}
        info = {f"finger_1_{name}": 1. for name in evidence.METRICS}
        info["finger_1_precision_press_frame_rate"] = 0.
        evidence.update(10, goal, info)
        info["finger_1_precision_press_frame_rate"] = 1.
        evidence.update(11, goal, info)
        goal.update(fret=[2, 2], finger=[1, 1], sustain_event_id=[4, 5])
        evidence.update(12, goal, info)
        rows = evidence.report()
        self.assertEqual(rows[0]["first_press_frame"], 11)
        self.assertEqual(rows[0]["means"]["precision_press_frame_rate"], .5)
        self.assertEqual(rows[0]["ambiguous_frames"], 1)
        self.assertIsNone(rows[1]["means"]["precision_press_frame_rate"])


if __name__ == "__main__":
    unittest.main()
