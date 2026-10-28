import copy
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

import torch

from guitar_learning.tests.test_finger_decisions import TinyDecisionPolicy, FakeDecisionPool
from guitar_learning.tests.test_ppo import assert_tree
from guitar_learning.training.rollout import DecisionCollector
from guitar_learning.training.ppo import DecisionPPOTrainer, compute_decision_gae
from guitar_learning.training.ppo import PPOConfig, compute_gae, KLGuardError


class DecisionPPOTests(unittest.TestCase):
    def test_duration_gae_manual_and_k1_equivalence(self):
        reward = torch.tensor([[1.], [2.], [3.], [4.]])
        value = reward*.2
        nxt = value+1.
        terminal = torch.tensor([[False], [True], [False], [False]])
        truncated = torch.tensor([[False], [False], [True], [False]])
        duration = torch.tensor([[1], [2], [3], [6]])
        valid = torch.ones_like(terminal)
        ar, ret = compute_decision_gae(reward, value, nxt, terminal, truncated, duration, valid, .5, .8)
        delta = reward+.5**duration*(~terminal)*nxt-value
        expected = delta.clone()
        expected[0] += .4*delta[1]
        self.assertTrue(torch.allclose(ar, expected))
        self.assertTrue(torch.allclose(ret, expected+value))
        a, r = compute_decision_gae(reward, value, nxt, terminal, truncated, torch.ones_like(duration), valid, .99, .95)
        old_a, old_r = compute_gae(reward, value, nxt, terminal, truncated, .99, .95)
        self.assertTrue(torch.equal(a, old_a))
        self.assertTrue(torch.equal(r, old_r))

    def test_padding_nan_ignored_everywhere_and_optimizer_changes(self):
        torch.manual_seed(3)
        model = TinyDecisionPolicy()
        trainer = DecisionPPOTrainer(model, PPOConfig(epochs=1, target_kl=.1))
        b, _ = DecisionCollector(model, FakeDecisionPool()).collect(5)
        # K1 수집은 모든 칸이 유효하므로 끝에 명시적 padding 행을 붙인다.
        b = {key: torch.cat((value, torch.zeros_like(value[:1])), dim=0) for key, value in b.items()}
        for value in b.values():
            if value.is_floating_point():
                value[~b['valid']] = float('nan')
        actor = copy.deepcopy(model.actor.state_dict())
        reward = model.reward_critic.weight.detach().clone()
        cost = model.cost_critic.weight.detach().clone()
        result = trainer.update(b)
        self.assertFalse(torch.equal(actor['bias'], model.actor.bias))
        self.assertFalse(torch.equal(reward, model.reward_critic.weight))
        self.assertFalse(torch.equal(cost, model.cost_critic.weight))
        self.assertEqual(result['diagnostics']['valid_decisions'], 10)
        self.assertEqual(result['diagnostics']['physical_transitions'], 10)
        self.assertEqual(result['diagnostics']['advantages']['reward_raw']['count'], 10)

    def test_noncontiguous_mask_and_nonfinite_valid_rejected(self):
        b, _ = DecisionCollector(TinyDecisionPolicy(), FakeDecisionPool()).collect(5)
        args = [b[key] for key in ('reward', 'reward_value', 'next_reward_value', 'terminated', 'truncated', 'duration', 'valid')]
        args[-1] = args[-1].clone()
        args[-1][1, 0] = False
        with self.assertRaisesRegex(ValueError, 'prefix'):
            compute_decision_gae(*args, .99, .95)
        args[-1] = b['valid']
        args[0][0, 0] = float('nan')
        with self.assertRaisesRegex(ValueError, 'nonfinite'):
            compute_decision_gae(*args, .99, .95)

    def test_transaction_rollback_and_policy_kl_dispatch(self):
        trainer = DecisionPPOTrainer(TinyDecisionPolicy(), PPOConfig(epochs=1, target_kl=.01, kl_retries=0))
        b, _ = DecisionCollector(trainer.policy, FakeDecisionPool()).collect(5)
        before = copy.deepcopy(trainer.policy.state_dict())
        actor = copy.deepcopy(trainer.actor_optimizer.state_dict())
        rng = torch.get_rng_state()
        with patch.object(trainer.policy, 'analytic_kl', return_value=torch.ones(10)) as kl:
            with self.assertRaises(KLGuardError):
                trainer.update(b)
            self.assertTrue(kl.called)
        assert_tree(self, before, trainer.policy.state_dict())
        assert_tree(self, actor, trainer.actor_optimizer.state_dict())
        self.assertTrue(torch.equal(rng, torch.get_rng_state()))
        self.assertEqual(trainer.updates, 0)

    def test_large_post_update_policy_evaluation_is_bounded(self):
        model = TinyDecisionPolicy()
        trainer = DecisionPPOTrainer(model, PPOConfig(epochs=1, target_kl=.1, minibatch_size=4096))
        original, _ = DecisionCollector(model, FakeDecisionPool()).collect(1)
        b = {key: value[:1, :1].repeat((4097, 1)+(1,)*(value.ndim-2)) for key, value in original.items()}
        sizes = []
        evaluate = model.evaluate
        def bounded(*inputs):
            sizes.append(len(inputs[0]))
            self.assertLessEqual(len(inputs[0]), 4096)
            return evaluate(*inputs)
        with patch.object(model, 'evaluate', side_effect=bounded):
            result = trainer.update(b)
        self.assertEqual(result['diagnostics']['valid_decisions'], 4097)
        self.assertEqual(sizes[-2:], [4096, 1])

    def test_strict_checkpoint_and_eligible_episode_budget(self):
        config = PPOConfig(epochs=1, target_kl=.1, episode_cost_budget=1., lambda_lr=.2)
        trainer = DecisionPPOTrainer(TinyDecisionPolicy(), config)
        b, _ = DecisionCollector(trainer.policy, FakeDecisionPool()).collect(5)
        trainer.update(b, [dict(valid=True, reason='terminal_failure', cost=2.),
                           dict(valid=False, reason='terminal', cost=100.),
                           dict(valid=True, reason='partial', cost=100.)])
        self.assertAlmostEqual(trainer.cost_weight, 1.2)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'decision.pt'
            trainer.save(path, dict(scope='J'))
            expected_rng = torch.get_rng_state()
            other = DecisionPPOTrainer(TinyDecisionPolicy(), config)
            self.assertEqual(other.load(path), dict(scope='J'))
            assert_tree(self, trainer.policy.state_dict(), other.policy.state_dict())
            assert_tree(self, trainer.actor_optimizer.state_dict(), other.actor_optimizer.state_dict())
            assert_tree(self, trainer.value_optimizer.state_dict(), other.value_optimizer.state_dict())
            self.assertTrue(torch.equal(expected_rng, torch.get_rng_state()))
            self.assertEqual(other.updates, 1)
            wrong_policy = TinyDecisionPolicy()
            wrong_policy.architecture = dict(wrong_policy.architecture, schema='incompatible_test_contract')
            wrong = DecisionPPOTrainer(wrong_policy, config)
            with self.assertRaises(ValueError):
                wrong.load(path)


if __name__ == '__main__':
    unittest.main()
