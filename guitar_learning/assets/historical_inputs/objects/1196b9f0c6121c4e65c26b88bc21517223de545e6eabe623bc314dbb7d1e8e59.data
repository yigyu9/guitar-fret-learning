"""Meaningful codec and transactional-update regressions, CPU only."""
import copy
import unittest
from unittest.mock import patch
import numpy as np
import torch
from .deadline_bounded_residual_v1 import CAPS_RAD, bounded_target
from .deadline_guarded_ppo_v3 import GuardedPPO
from .joint_policy_v1 import JointActorCritic
from .joint_ppo_v1 import PPOConfig
from .deadline_rms_initialize_v1 import initialize

GROUPS = ['body']*9+['head']*6+['arm']*12+['finger']*21+['arm']*12+['finger']*21


def exact(a, b):
    if torch.is_tensor(a): return torch.equal(a, b)
    if isinstance(a, dict): return set(a) == set(b) and all(exact(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)): return len(a) == len(b) and all(exact(x, y) for x, y in zip(a, b))
    return a == b


class GuardedUpdateTests(unittest.TestCase):
    def setUp(self):
        torch.set_num_threads(1); torch.manual_seed(103)
        self.model = JointActorCritic(825, GROUPS)
        self.trainer = GuardedPPO(self.model, {'observation': {'dimension': 825}, 'action_dimension': 81},
                                  PPOConfig(learning_rate=3e-5, epochs=2, minibatch_size=16))

    def test_codec_zero_caps_interleaved_and_limits(self):
        nominal = np.zeros(81); lo = np.full(81, -.5); hi = np.full(81, .5)
        self.assertTrue(np.array_equal(bounded_target(np.zeros(81), nominal, lo, hi, GROUPS), nominal))
        caps = np.array([CAPS_RAD[g] for g in GROUPS])
        self.assertTrue(np.array_equal(bounded_target(np.ones(81), nominal, lo, hi, GROUPS), caps))
        self.assertTrue(np.array_equal(bounded_target(-np.ones(81), nominal, lo, hi, GROUPS), -caps))
        nominal[55] = .49
        self.assertEqual(bounded_target(np.ones(81), nominal, lo, hi, GROUPS)[55], .5)
        with self.assertRaises(ValueError): bounded_target(np.full(81, 1.1), nominal, lo, hi, GROUPS)

    def test_analytic_kl_matches_reference(self):
        obs = torch.randn(5, 825)
        with torch.no_grad():
            old = self.model.distribution(obs)
            mean, std = old.mean.clone(), old.stddev.clone()
            self.model.actor[-1].bias.add_(.0005)
            new = self.model.distribution(obs)
            expected = torch.distributions.kl_divergence(torch.distributions.Normal(mean, std), new).sum(-1).mean()
        self.assertEqual(self.trainer._kl(obs, mean, std), float(expected))

    def test_rejected_candidates_restore_model_and_populated_adam(self):
        obs = torch.randn(4, 825)
        self.model.actor[-1].bias.grad = torch.ones(81)
        with torch.no_grad():
            d = self.model.distribution(obs); mean, std = d.mean.clone(), d.stddev.clone()
        accepted, _ = self.trainer._guarded_step(obs, mean, std)
        self.assertTrue(accepted); self.assertTrue(self.trainer.optimizer.state)
        before_model = copy.deepcopy(self.model.state_dict())
        before_adam = copy.deepcopy(self.trainer.optimizer.state_dict())
        with patch.object(self.trainer, '_kl', return_value=1.):
            accepted, attempts = self.trainer._guarded_step(obs, mean, std)
        self.assertFalse(accepted); self.assertEqual(len(attempts), 8)
        self.assertTrue(exact(before_model, self.model.state_dict()))
        self.assertTrue(exact(before_adam, self.trainer.optimizer.state_dict()))

    def test_backtracking_rolls_back_before_reduced_retry(self):
        obs = torch.randn(4, 825)
        self.model.actor[-1].bias.grad = torch.ones(81)
        with torch.no_grad():
            d = self.model.distribution(obs); mean, std = d.mean.clone(), d.stddev.clone()
        with patch.object(self.trainer, '_kl', side_effect=[1., .01]):
            accepted, attempts = self.trainer._guarded_step(obs, mean, std)
        self.assertTrue(accepted)
        self.assertAlmostEqual(float(self.model.actor[-1].bias[0]), -1.5e-5, places=9)
        self.assertEqual(float(self.trainer.optimizer.state[self.model.actor[-1].bias]['step']), 1.)
        self.assertEqual(attempts[-1]['learning_rate'], 1.5e-5)

    def test_full_update_frozen_RMS_and_cumulative_KL(self):
        obs = torch.randn(32, 825)
        sample = self.model.sample(obs)
        batch = {k: sample[k][:, None] for k in ('latent', 'action', 'log_prob', 'value')}
        batch.update(obs=obs[:, None], reward=torch.linspace(-1, 1, 32)[:, None],
                     next_value=torch.zeros(32, 1), terminated=torch.zeros(32, 1, dtype=torch.bool),
                     truncated=torch.zeros(32, 1, dtype=torch.bool))
        before = copy.deepcopy(self.model.obs_rms.state_dict())
        actor = copy.deepcopy(self.model.actor.state_dict())
        result = self.trainer.update(batch)
        self.assertGreater(result['optimizer_steps'], 0)
        self.assertLessEqual(result['final_analytic_kl'], .02)
        self.assertFalse(result['RMS_updated'])
        self.assertTrue(exact(before, self.model.obs_rms.state_dict()))
        self.assertFalse(exact(actor, self.model.actor.state_dict()))
        for step in result['minibatches']: self.assertLessEqual(step['kl'], .02)

    def test_nonfinite_candidate_and_KL_exception_rollback(self):
        obs = torch.randn(4, 825)
        self.model.actor[-1].bias.grad = torch.ones(81)
        with torch.no_grad():
            d = self.model.distribution(obs); mean, std = d.mean.clone(), d.stddev.clone()
        before = copy.deepcopy(self.model.state_dict())
        def corrupt():
            with torch.no_grad(): self.model.actor[-1].bias.fill_(float('nan'))
        with patch.object(self.trainer.optimizer, 'step', side_effect=corrupt):
            accepted, _ = self.trainer._guarded_step(obs, mean, std)
        self.assertFalse(accepted)
        self.assertTrue(exact(before, self.model.state_dict()))
        self.assertFalse(self.trainer.optimizer.state)
        with patch.object(self.trainer, '_kl', side_effect=ValueError('nonfinite Normal')):
            accepted, _ = self.trainer._guarded_step(obs, mean, std)
        self.assertFalse(accepted)
        self.assertTrue(exact(before, self.model.state_dict()))
        self.assertFalse(self.trainer.optimizer.state)

    def test_wrong_pin_fails_before_mutation(self):
        before = copy.deepcopy(self.model.state_dict())
        with patch('stability_adapter_2.deadline_rms_initialize_v1.sha', return_value='bad'):
            with self.assertRaises(ValueError): initialize(self.trainer, 'unused', {'strap_enabled': True})
        self.assertTrue(exact(before, self.model.state_dict()))
        self.assertFalse(self.trainer.optimizer.state)


if __name__ == '__main__': unittest.main()
