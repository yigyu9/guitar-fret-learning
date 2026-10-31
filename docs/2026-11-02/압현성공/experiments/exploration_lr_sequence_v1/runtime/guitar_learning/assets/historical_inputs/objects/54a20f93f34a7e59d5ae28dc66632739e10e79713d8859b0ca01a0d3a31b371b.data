"""Reward weighting, safety-bound and fail-before-mutation transfer checks."""
from dataclasses import asdict
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import torch
from .deadline_stability_reward_v1 import priority_reward, base_reward
from .deadline_native_v4 import settlement, GAMMA, REWARD_SCALE, PROFILE
from .deadline_ppo_v1 import DeadlinePPO, PPOConfig
from .deadline_priority_transfer_v1 import migrate, sha
from .joint_policy_v1 import JointActorCritic, digest

GROUPS = ['body']*9+['head']*6+['arm']*24+['finger']*42


class PriorityTests(unittest.TestCase):
    def reward(self, p, r, active=True):
        return (p, r, .8, .6, .4, [0., .03], [.2, .4], 1, 2, 1, 1, active)

    def test_only_two_costs_change_by_four(self):
        for active in (False, True):
            args = self.reward([.02, .1, 0.], .3, active)
            _, before = base_reward(*args); total, after = priority_reward(*args)
            for key in before:
                self.assertEqual(after[key], before[key]*(4 if key in ('position', 'rotation_upper_proxy') else 1))
            self.assertEqual(total, sum(after.values()))
        self.assertEqual(PROFILE['continuous_per_second']['position_loss'], -8.)
        self.assertEqual(PROFILE['continuous_per_second']['rotation_upper_loss'], -4.)

    def test_inside_zero_and_monotonic_outside(self):
        _, inside = priority_reward(*self.reward([0., 0., 0.], 0.))
        self.assertEqual(inside['position'], 0.); self.assertEqual(inside['rotation_upper_proxy'], 0.)
        costs = [priority_reward(*self.reward([x, 0., 0.], x))[0] for x in (.01, .05, .1)]
        self.assertGreater(costs[0], costs[1]); self.assertGreater(costs[1], costs[2])

    def test_floor_retains_weight_and_fatal_dominates_remaining_floor(self):
        scaled, raw, ledger = settlement(-6.)
        self.assertEqual(raw, -6.); self.assertAlmostEqual(scaled, -.6)
        scaled, raw, ledger = settlement(-9.)
        self.assertEqual(raw, -8.); self.assertEqual(ledger['floor_adjustment'], 1.)
        for ticks in (0, 1, 120, 981):
            scaled, raw, _ = settlement(100., ticks, True)
            worst = -8.*sum(GAMMA**k for k in range(ticks+1))
            self.assertAlmostEqual(raw, worst-1., places=8)
            self.assertLess(scaled, worst*REWARD_SCALE)

    def test_bad_measurement_and_invalid_tail_rejected(self):
        with self.assertRaises(ValueError): priority_reward(*self.reward([float('nan'), 0., 0.], 0.))
        with self.assertRaises(ValueError): settlement(0., -1, True)

    def test_transfer_and_rejection_before_mutation(self):
        with tempfile.TemporaryDirectory() as folder:
            source_file = Path(folder)/'source.py'; source_file.write_text('unchanged\n')
            prior_abi = {'version': 'test_old825', 'observation': {'dimension': 825},
                         'action_dimension': 81, 'groups': GROUPS, 'strap_enabled': True}
            abi = dict(prior_abi, source_sha256={str(source_file): sha(source_file)})
            old = JointActorCritic(825, GROUPS)
            with torch.no_grad():
                old.actor[-1].weight.normal_(std=.01); old.obs_rms.mean.normal_()
                old.obs_rms.var.uniform_(.1, 2.); old.obs_rms.count.fill_(300.)
            cp = Path(folder)/'old.pt'
            torch.save({'schema': 'deadline_pilot_ppo_v1', 'abi': abi, 'abi_sha256': digest(abi),
                'model': old.state_dict(), 'ppo_config': asdict(PPOConfig()), 'updates': 92,
                'transitions': 23552}, cp)
            new = JointActorCritic(825, GROUPS)
            trainer = DeadlinePPO(new, prior_abi)
            initial = {k: v.clone() for k, v in new.state_dict().items()}
            with patch('stability_adapter_2.deadline_priority_transfer_v1.SOURCE_SHA256', {True: sha(cp)}):
                with self.assertRaises(ValueError): migrate(trainer, cp, dict(prior_abi, version='wrong'), np.zeros(825))
                self.assertTrue(all(torch.equal(v, initial[k]) for k, v in new.state_dict().items()))
                record = migrate(trainer, cp, prior_abi, np.zeros(825))
                self.assertEqual(record['source_updates'], 92)
                self.assertFalse(trainer.optimizer.state); self.assertEqual(trainer.updates, 0)
                for k, v in new.state_dict().items():
                    self.assertTrue(torch.equal(v, initial[k] if k.startswith('critic.') else old.state_dict()[k]))
                before = {k: v.clone() for k, v in new.state_dict().items()}
                source_file.write_text('changed\n')
                with self.assertRaises(ValueError): migrate(trainer, cp, prior_abi, np.zeros(825))
                self.assertTrue(all(torch.equal(v, before[k]) for k, v in new.state_dict().items()))
            with self.assertRaises(ValueError): migrate(trainer, cp, prior_abi, np.zeros(825))


if __name__ == '__main__':
    torch.set_num_threads(1)
    unittest.main(verbosity=2)
