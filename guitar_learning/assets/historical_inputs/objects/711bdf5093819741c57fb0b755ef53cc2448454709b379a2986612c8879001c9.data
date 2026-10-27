import random
import tempfile
import unittest
from pathlib import Path

import numpy as np
import torch

from .policy import Policy
from .ppo import PPOConfig, PPOTrainer, compute_gae


class PolicyPPOTests(unittest.TestCase):
    def test_zero_actor_random_hidden_and_shapes(self):
        policy = Policy(7, 16)
        obs = torch.randn(3, 7)
        result = policy.act(obs, deterministic=True)
        self.assertEqual(result['action'].shape, (3, 54))
        self.assertEqual(result['reward_value'].shape, (3,))
        self.assertTrue(torch.equal(result['action'], torch.zeros(3, 54)))
        self.assertGreater(float(policy.encoder[0].weight.abs().sum()), 0)
        sample = policy.act(obs)
        self.assertTrue(torch.allclose(sample['logp'], policy.evaluate(obs, sample['latent'])['logp']))
        extreme = policy.evaluate(obs, torch.full((3, 54), 100.))
        self.assertTrue(torch.isfinite(extreme['logp']).all())

    def test_gae_terminal_truncated_and_rollout_boundary(self):
        reward = torch.tensor([[1.], [2.], [3.]])
        value = torch.tensor([[.5], [.6], [.7]])
        next_value = torch.tensor([[.6], [9.], [4.]])
        terminated = torch.tensor([[False], [True], [False]])
        truncated = torch.zeros_like(terminated)
        advantage, returns = compute_gae(reward, value, next_value, terminated, truncated, .9, .8)
        self.assertTrue(torch.allclose(advantage[:, 0], torch.tensor([1.04+.72*1.4, 1.4, 5.9])))
        truncated[1] = True
        terminated[1] = False
        advantage, _ = compute_gae(reward, value, next_value, terminated, truncated, .9, .8)
        self.assertAlmostEqual(float(advantage[1]), 9.5, places=5)
        self.assertTrue(torch.allclose(returns[2], torch.tensor([6.6])))

    def buffer(self, policy):
        obs = torch.randn(8, 1, policy.obs_dim)
        with torch.no_grad():
            sample = policy.act(obs)
        return dict(obs=obs, latent=sample['latent'], logp=sample['logp'],
            reward_value=sample['reward_value'], cost_value=sample['cost_value'],
            next_reward_value=torch.zeros(8, 1), next_cost_value=torch.zeros(8, 1),
            reward=torch.arange(8.).reshape(8, 1), cost=torch.linspace(0, 1, 8).reshape(8, 1),
            terminated=torch.zeros(8, 1, dtype=torch.bool), truncated=torch.zeros(8, 1, dtype=torch.bool))

    def test_update_and_strict_deterministic_checkpoint(self):
        torch.manual_seed(5)
        policy = Policy(7, 16)
        config = PPOConfig(epochs=2, minibatch_size=4)
        trainer = PPOTrainer(policy, config)
        buffer = self.buffer(policy)
        before = {k: v.clone() for k, v in policy.state_dict().items()}
        trainer.update(buffer)
        for prefix in ('actor_heads', 'reward_critic', 'cost_critic'):
            self.assertTrue(any(not torch.equal(v, before[k]) for k, v in policy.state_dict().items() if k.startswith(prefix)))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'fresh.pt'
            trainer.save(path, {'resume': 'fresh physical episode'})
            expected_random = (random.random(), np.random.rand(), torch.rand(2))
            expected_metrics = trainer.update(buffer)
            expected_state = {k: v.clone() for k, v in policy.state_dict().items()}
            restored = PPOTrainer(Policy(7, 16), config)
            self.assertEqual(restored.load(path), {'resume': 'fresh physical episode'})
            actual_random = (random.random(), np.random.rand(), torch.rand(2))
            self.assertEqual(expected_random[:2], actual_random[:2])
            self.assertTrue(torch.equal(expected_random[2], actual_random[2]))
            self.assertEqual(expected_metrics, restored.update(buffer))
            for key, value in restored.policy.state_dict().items():
                self.assertTrue(torch.equal(value, expected_state[key]), key)
            with self.assertRaises(FileExistsError):
                restored.save(path)
            with self.assertRaises(ValueError):
                PPOTrainer(Policy(7, 16), PPOConfig(epochs=1)).load(path)
            old_path = Path(directory) / 'legacy.pt'
            torch.save({'model': policy.state_dict()}, old_path)
            with self.assertRaises(ValueError):
                restored.load(old_path)


if __name__ == '__main__':
    unittest.main()
