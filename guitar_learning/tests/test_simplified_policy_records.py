"""Joint actor state and distinct task/physical failure reporting."""
import copy
from pathlib import Path
import tempfile
import unittest

import numpy as np
import torch

from guitar_learning.training.policy import FingerSkillPolicy
from guitar_learning.training.policy import WRIST_TERMINATION_FIELDS
from guitar_learning.tests.test_finger_skill_policy import contract, inputs
from guitar_learning.training.training_log_io import episode_summary
from guitar_learning.training.ppo import policy_advantages


def simplified_contract():
    return contract()


class SimplifiedPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def test_both_actors_active_and_all_termination_state_observed(self):
        spec = simplified_contract()
        model = FingerSkillPolicy(557, size='small', contract=spec)
        self.assertEqual(int(model._active_mask().sum()), 33)
        self.assertTrue(all(p.requires_grad for p in model.actor_parameters()))
        for name in WRIST_TERMINATION_FIELDS:
            self.assertIn(name, model.architecture['support_fields'])
        batch = list(inputs())
        batch[0] = torch.randn(4, 557)
        sample = model.act(*batch)
        self.assertTrue(torch.equal(sample['action'][:, 33:], torch.zeros(4, 6)))
        self.assertGreater(float(sample['action'][:, :17].abs().sum()), 0)
        self.assertGreater(float(sample['action'][:, 17:33].abs().sum()), 0)
        loss = -model.evaluate(*batch, sample['latent'])['logp'].mean()
        loss.backward()
        self.assertGreater(float(model.support_head.bias.grad.abs().sum()), 0)
        for head in model.finger_heads.values():
            self.assertGreater(float(head[-1].bias.grad.abs().sum()), 0)

    def test_timer_state_reaches_support_actor_and_critic(self):
        model = FingerSkillPolicy(557, size='small', contract=simplified_contract())
        with torch.no_grad():
            model.support_head.weight.normal_(0, .01)
        batch = list(inputs())
        batch[0] = torch.zeros(4, 557)
        first = model(*batch)
        batch[0][:, -4:] = torch.tensor([1., .9, .5, .8])
        second = model(*batch)
        self.assertFalse(torch.equal(first['mean'][:, :17], second['mean'][:, :17]))
        self.assertFalse(torch.equal(first['reward_value'], second['reward_value']))

    def test_old_state_and_phase_contracts_cannot_masquerade_as_v25(self):
        value = simplified_contract()
        for phase, exploration in [('R', 'independent'), ('F', 'independent'), ('J', 'correlated')]:
            with self.assertRaises(ValueError):
                changed = copy.deepcopy(value)
                changed['task']['finger_skill'].update(phase=phase, exploration=exploration)
                FingerSkillPolicy(557, size='small', contract=changed)
        bad = copy.deepcopy(value)
        bad['observation']['fields'][-1] = 'hidden_timer'
        with self.assertRaises(ValueError):
            FingerSkillPolicy(557, size='small', contract=bad)
        with self.assertRaises(ValueError):
            FingerSkillPolicy(561, size='small', contract=value)

    def test_previous_wrist_rule_checkpoint_is_rejected_without_model_mutation(self):
        from guitar_learning.tests.test_simplified_finger_environment import make
        from guitar_learning.training.ppo import DecisionPPOTrainer
        env, _, _ = make()
        current = env.contract
        previous = copy.deepcopy(current)
        previous['observation']['scales'][-3] = .75
        previous['termination']['wrist'].update(schema='guitar_learning.wrist_termination.v1',
                                               normal_duration_s=.75)
        for key in ('normal_timer', 'recovery_rate', 'normal_timer_scope'):
            previous['termination']['wrist'].pop(key)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'previous.pt'
            old = DecisionPPOTrainer(FingerSkillPolicy(557, size='small', contract=previous))
            old.save(path)
            trainer = DecisionPPOTrainer(FingerSkillPolicy(557, size='small', contract=current))
            before = {k:v.clone() for k,v in trainer.policy.state_dict().items()}
            with self.assertRaises(ValueError):
                trainer.load(path)
            for key, value in before.items():
                torch.testing.assert_close(trainer.policy.state_dict()[key], value, rtol=0, atol=0)


class SimplifiedFailureRecordsTests(unittest.TestCase):
    def test_wrist_failure_does_not_count_as_physical_failure(self):
        base = dict(reason='terminal_failure', reward=0., cost=10.,
                    song=dict(stage_success=False, left_success_count=0, right_success_count=0))
        wrist = dict(base, termination=dict(physical_failure=False, wrist_failure=True))
        physical = dict(base, termination=dict(physical_failure=True, wrist_failure=False))
        result = episode_summary([wrist, physical])
        self.assertEqual(result['count'], 2)
        self.assertEqual(result['physical_failure'], 1)
        self.assertEqual(result['wrist_failure'], 1)
        self.assertNotIn('wrist_failure', episode_summary([base]))

    def test_cost_relative_scale_survives_joint_normalization(self):
        reward = torch.tensor([.4, .9, -.1, .6])
        cost = torch.tensor([0., 3., 1., 0.])
        _, first, _, _ = policy_advantages(reward, cost, 1., 'joint')
        _, second, _, _ = policy_advantages(reward, cost*2, 1., 'joint')
        self.assertFalse(np.allclose(first, second))
        self.assertTrue(torch.isfinite(second).all())


if __name__ == '__main__':
    unittest.main()
