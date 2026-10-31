"""단일 요인 실험의 수치 동등성·KL 제한·분포·엄격 재개를 CPU에서 확인한다."""
import copy
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import torch

from guitar_learning.tool.experiments.finger_ablation_learning import (
    FACTORS, LearningPolicy, LearningTrainer, validate_research_config)
from guitar_learning.training.ppo import DecisionPPOTrainer, KLGuardError, PPOConfig
from guitar_learning.training.rollout import DecisionCollector
from guitar_learning.tests.test_finger_decisions import TinyDecisionPolicy, FakeDecisionPool
from guitar_learning.tests.test_finger_skill_policy import contract, inputs
from guitar_learning.tests.test_ppo import assert_tree


def factors(**changes):
    result = dict.fromkeys(FACTORS, False)
    result.update(changes)
    return result


class AblationLearningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def test_exact_boolean_factor_contract(self):
        self.assertEqual(validate_research_config(), factors())
        for value in ({}, factors(exploration=1), dict(factors(), extra=False), []):
            with self.assertRaises(ValueError): validate_research_config(value)

    def test_disabled_distribution_exact_and_exploration_only_sixteen_axes(self):
        cfg = factors()
        torch.manual_seed(13)
        baseline = LearningPolicy(557, size='small', contract=contract(), research_config=cfg)
        expanded = LearningPolicy(557, size='small', contract=contract(),
                                  research_config=factors(exploration=True))
        expanded.load_state_dict(baseline.state_dict())
        with torch.no_grad(): expanded.finger_log_std.fill_(math.log(.10))
        data = inputs()
        expected, actual = baseline(*data), expanded(*data)
        for key in ('mean', 'reward_value', 'cost_value'):
            self.assertTrue(torch.equal(expected[key], actual[key]))
        self.assertTrue(torch.equal(expected['log_std'][:, :17], actual['log_std'][:, :17]))
        self.assertTrue(torch.equal(expected['log_std'][:, 33:], actual['log_std'][:, 33:]))
        torch.testing.assert_close(actual['log_std'][:, 17:33].exp(), torch.full((4, 16), .10))
        with torch.no_grad(): expanded.finger_log_std.fill_(-5.)
        torch.testing.assert_close(expanded(*data)['log_std'][:, 17:33].exp(), torch.full((4, 16), .07))
        sample = expanded.act(*data)
        torch.testing.assert_close(sample['logp'], expanded.evaluate(*data, sample['latent'])['logp'])
        self.assertEqual(expanded.architecture['research_config'], factors(exploration=True))
        # 평균·분포를 바꾸지 않은 연구 baseline은 기본 정책과 정확히 같다.
        from guitar_learning.training.policy import FingerSkillPolicy
        original = FingerSkillPolicy(557, size='small', contract=contract())
        original.load_state_dict(baseline.state_dict())
        self.assertTrue(all(torch.equal(expected[k], original(*data)[k]) for k in expected))

    def test_fresh_exploration_initialization_and_profile_mismatch(self):
        cfg = factors(exploration=True)
        model = LearningPolicy(557, size='small', contract=contract(), research_config=cfg)
        torch.testing.assert_close(model.finger_log_std.exp(), torch.full((16,), .10))
        torch.testing.assert_close(model.support_log_std, torch.full((17,), -3.))
        with self.assertRaisesRegex(ValueError, 'mismatch'):
            LearningTrainer(model, PPOConfig(), factors())
        with self.assertRaisesRegex(ValueError, 'actor_lr'):
            LearningTrainer(TinyDecisionPolicy(), PPOConfig(actor_lr=1e-5), factors(adaptive_lr=True))

    def test_accepted_but_high_kl_resets_recovery_streak(self):
        trainer = LearningTrainer(TinyDecisionPolicy(), PPOConfig(epochs=1), factors(adaptive_lr=True))
        group = trainer.actor_optimizer.param_groups[0]
        group['research_stable_updates'] = 9
        group['lr'] = 1.5e-5
        data, _ = DecisionCollector(trainer.policy, FakeDecisionPool()).collect(5)
        with patch.object(trainer.policy, 'analytic_kl', return_value=torch.full((10,), .01)):
            result = trainer.update(data)
        self.assertEqual(result['kl_retries'], 0)
        self.assertEqual(group['research_stable_updates'], 0)
        self.assertAlmostEqual(result['actor_lr'], 1.5e-5)
        self.assertFalse(result['diagnostics']['research_learning_rate']['recovered'])

    def test_disabled_trainer_bit_exact_update(self):
        torch.manual_seed(9)
        model = TinyDecisionPolicy()
        data, _ = DecisionCollector(model, FakeDecisionPool()).collect(5)
        config = PPOConfig(epochs=1, actor_lr=1e-6)
        original = DecisionPPOTrainer(copy.deepcopy(model), config)
        research = LearningTrainer(copy.deepcopy(model), config, factors())
        rng = torch.get_rng_state()
        expected = original.update(data)
        final_rng = torch.get_rng_state()
        torch.set_rng_state(rng)
        self.assertEqual(expected, research.update(data))
        self.assertTrue(torch.equal(final_rng, torch.get_rng_state()))
        for name in ('policy', 'actor_optimizer', 'value_optimizer'):
            assert_tree(self, getattr(original, name).state_dict(), getattr(research, name).state_dict())

    def test_retry_halves_each_attempt_and_respects_floor(self):
        trainer = LearningTrainer(TinyDecisionPolicy(), PPOConfig(), factors(adaptive_lr=True))
        snapshot = trainer._actor_snapshot()
        for retry, expected in ((0, 1.5e-5), (1, 7.5e-6), (8, 3e-6)):
            trainer._actor_restore(snapshot)
            trainer._retry_actor_lr(retry)
            self.assertAlmostEqual(trainer.actor_optimizer.param_groups[0]['lr'], expected)

    def test_real_retry_stable_recovery_and_failed_update_rollback(self):
        trainer = LearningTrainer(TinyDecisionPolicy(), PPOConfig(epochs=1, kl_retries=2),
                                  factors(adaptive_lr=True))
        data, _ = DecisionCollector(trainer.policy, FakeDecisionPool()).collect(5)
        # 첫 시도만 거부하고 다음 시도를 승인한다. KL 상한 자체는 바꾸지 않는다.
        with patch.object(trainer.policy, 'analytic_kl', side_effect=[torch.ones(10), torch.zeros(10)]):
            result = trainer.update(data)
        self.assertEqual(result['kl_retries'], 1)
        self.assertAlmostEqual(result['actor_lr'], 1.5e-5)
        self.assertEqual(trainer.actor_optimizer.param_groups[0]['research_stable_updates'], 0)
        for i in range(10):
            data, _ = DecisionCollector(trainer.policy, FakeDecisionPool()).collect(5)
            with patch.object(trainer.policy, 'analytic_kl', return_value=torch.zeros(10)):
                result = trainer.update(data)
            self.assertEqual(result['diagnostics']['research_learning_rate']['recovered'], i == 9)
        self.assertAlmostEqual(result['actor_lr'], 1.8e-5)
        model = copy.deepcopy(trainer.policy.state_dict())
        optimizer = copy.deepcopy(trainer.actor_optimizer.state_dict())
        updates = trainer.updates
        rng = torch.get_rng_state()
        with patch.object(trainer.policy, 'analytic_kl', return_value=torch.ones(10)):
            with self.assertRaises(KLGuardError): trainer.update(data)
        assert_tree(self, model, trainer.policy.state_dict())
        assert_tree(self, optimizer, trainer.actor_optimizer.state_dict())
        self.assertEqual(updates, trainer.updates)
        self.assertTrue(torch.equal(rng, torch.get_rng_state()))

    def test_strict_resume_preserves_stability_and_rejects_factor_changes(self):
        cfg = factors(adaptive_lr=True)
        trainer = LearningTrainer(TinyDecisionPolicy(), PPOConfig(epochs=1), cfg)
        trainer.actor_optimizer.param_groups[0]['research_stable_updates'] = 7
        trainer.actor_optimizer.param_groups[0]['lr'] = 1.5e-5
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'research.pt'
            trainer.save(path, dict(scope='test'))
            other = LearningTrainer(TinyDecisionPolicy(), PPOConfig(epochs=1), cfg)
            self.assertEqual(other.load(path), dict(scope='test'))
            self.assertEqual(other.actor_optimizer.param_groups[0]['research_stable_updates'], 7)
            self.assertAlmostEqual(other.actor_optimizer.param_groups[0]['lr'], 1.5e-5)
            wrong = LearningTrainer(TinyDecisionPolicy(), PPOConfig(epochs=1), factors())
            with self.assertRaisesRegex(ValueError, 'mismatch'): wrong.load(path)


if __name__ == '__main__':
    unittest.main()
