"""Verify policy/RMS expansion and fail-before-mutation input validation."""
from dataclasses import asdict
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import torch
from .deadline_ppo_v1 import DeadlinePPO, PPOConfig
from .joint_policy_v1 import JointActorCritic, digest
from .deadline_warm_start_v1 import expanded_state, equivalence, migrate, sha

GROUPS = ['body']*9+['head']*6+['arm']*24+['finger']*42


class MigrationTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(7)
        self.old = JointActorCritic(820, GROUPS)
        self.new = JointActorCritic(825, GROUPS)
        # Exercise a nonzero learned actor and nontrivial normalization.
        with torch.no_grad():
            self.old.actor[-1].weight.normal_(std=.01)
            self.old.obs_rms.mean.normal_()
            self.old.obs_rms.var.uniform_(.1, 2.)
            self.old.obs_rms.count.fill_(256.0001)
        self.legacy = {'version': 'test_legacy820', 'observation': {'dimension': 820}, 'groups': GROUPS}
        self.abi = {'observation': {'dimension': 825}, 'action_dimension': 81}

    def test_actor_critic_distribution_and_RMS_preserved(self):
        state = expanded_state(self.old.state_dict(), self.new.state_dict())
        self.new.load_state_dict(state, strict=True)
        record = equivalence(self.old, self.new, torch.randn(825))
        self.assertTrue(record['RMS_count_exact'])
        self.assertTrue(record['first_820_RMS_exact'])
        self.assertTrue(torch.equal(self.new.actor[0].weight[:, 820:], torch.zeros(512, 5)))
        self.assertTrue(torch.equal(self.new.critic[0].weight[:, 820:], torch.zeros(512, 5)))
        self.assertTrue(torch.equal(self.new.obs_rms.mean[820:], torch.zeros(5)))
        self.assertTrue(torch.equal(self.new.obs_rms.var[820:], torch.ones(5)))

    def test_shape_and_nonfinite_rejected(self):
        state = self.old.state_dict()
        state['critic.0.weight'] = torch.zeros(512, 819)
        with self.assertRaises(ValueError): expanded_state(state, self.new.state_dict())
        state = self.old.state_dict()
        state['log_std'][0] = float('nan')
        with self.assertRaises(ValueError): expanded_state(state, self.new.state_dict())

    def test_migrate_new_Adam_and_legacy_rejection_before_mutation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root/'source.py'
            source.write_text('frozen source\n')
            old_abi = dict(self.legacy, source_sha256={str(source): sha(source)}, action_dimension=81)
            payload = {'schema': 'deadline_pilot_ppo_v1', 'abi': old_abi,
                       'abi_sha256': digest(old_abi), 'model': self.old.state_dict(),
                       'ppo_config': asdict(PPOConfig()), 'updates': 1, 'transitions': 256}
            cp = root/'old.pt'; torch.save(payload, cp)
            trainer = DeadlinePPO(self.new, self.abi)
            with patch('stability_adapter_2.deadline_warm_start_v1.WARM_START_SHA256', sha(cp)):
                prior = self.new.actor[0].weight.clone()
                with self.assertRaises(ValueError): migrate(trainer, cp, dict(self.legacy, version='changed'), torch.randn(825))
                self.assertTrue(torch.equal(prior, self.new.actor[0].weight))
                record = migrate(trainer, cp, self.legacy, torch.randn(825))
                self.assertEqual(trainer.updates, 0); self.assertEqual(trainer.transitions, 0)
                self.assertFalse(trainer.optimizer.state)
                self.assertTrue(record['new_optimizer_empty'])
                source.write_text('changed source\n')
                with self.assertRaises(ValueError): migrate(trainer, cp, self.legacy, torch.randn(825))
            with self.assertRaises(ValueError): migrate(trainer, cp, self.legacy, torch.randn(825))


if __name__ == '__main__':
    torch.set_num_threads(1)
    unittest.main(verbosity=2)
