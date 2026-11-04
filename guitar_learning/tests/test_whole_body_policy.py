"""상태 전용 전신 정책의37축 분포·가치망 분리·실제 CPU PPO 갱신을 검증한다."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import torch
from torch.distributions import Normal, kl_divergence

from guitar_learning.gpu.whole_body import STATE_DIM, STATE_FIELDS, STATE_SCALES
from guitar_learning.gpu.whole_body_control import ACTION_NAMES
from guitar_learning.training.whole_body import (
    WholeBodyPolicy, OBSERVATION_SCHEMA, REWARD_SCHEMA, ACTION_DIM, TRANSPORT_DIM,
)
from guitar_learning.training.ppo import DecisionPPOTrainer, PPOConfig


def contract():
    return dict(schema='guitar_learning.training.v1',
        observation=dict(schema=OBSERVATION_SCHEMA, dimension=STATE_DIM,
            fields=list(STATE_FIELDS), scales=list(STATE_SCALES), event_dim=0, priority_slots=0),
        action=dict(dimension=ACTION_DIM, names=list(ACTION_NAMES)),
        reward=dict(schema=REWARD_SCHEMA))


def inputs(count=2):
    return (torch.randn(count, STATE_DIM), torch.zeros(count, 0, 0),
        torch.zeros(count, 0, dtype=torch.bool), torch.zeros(count, 0, 0),
        torch.zeros(count, 0, dtype=torch.bool))


@torch.no_grad()
def rollout(policy, horizon=4, count=2):
    """저장 경험과 같은 형태의 합성 자료로PPO 연결만 검사하며 물리 성공은 판정하지 않는다."""
    data = inputs(horizon*count)
    sampled = policy.act(*data)
    next_result = policy(*inputs(horizon*count))
    buffer = {key: value.reshape(horizon, count, *value.shape[1:])
              for key, value in zip(('state', 'events', 'mask', 'priority_events', 'priority_mask'), data)}
    for target, source in (('latent', 'latent'), ('logp', 'logp'), ('old_mean', 'mean'),
                           ('old_log_std', 'log_std'), ('reward_value', 'reward_value'),
                           ('cost_value', 'cost_value')):
        value = sampled[source]
        buffer[target] = value.reshape(horizon, count, *value.shape[1:])
    buffer.update(reward=torch.linspace(0., 1., horizon*count).reshape(horizon, count),
        cost=torch.linspace(.2, 0., horizon*count).reshape(horizon, count),
        next_reward_value=next_result['reward_value'].reshape(horizon, count),
        next_cost_value=next_result['cost_value'].reshape(horizon, count),
        terminated=torch.zeros(horizon, count, dtype=torch.bool),
        truncated=torch.zeros(horizon, count, dtype=torch.bool),
        valid=torch.ones(horizon, count, dtype=torch.bool),
        duration=torch.ones(horizon, count, dtype=torch.long))
    buffer['terminated'][-1, 0] = True
    buffer['truncated'][-1, 1] = True
    return buffer


class WholeBodyPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def setUp(self):
        torch.manual_seed(7)
        self.policy = WholeBodyPolicy(contract=contract())

    def test_network_dimensions_and_no_goal_encoder(self):
        policy = self.policy
        self.assertEqual(STATE_DIM, 484)
        self.assertEqual(policy.actor_encoder.state[0].weight.shape, (256, STATE_DIM))
        self.assertEqual(policy.actor_encoder.fusion[0].weight.shape, (512, 256))
        self.assertEqual(policy.value_encoder.fusion[0].weight.shape, (256, 256))
        self.assertEqual(policy.actor_head.weight.shape, (37, 256))
        self.assertEqual(policy.architecture['event_dim'], 0)
        self.assertIsNone(policy.architecture['goal_encoder'])
        self.assertEqual(int(policy._active_mask().sum()), 37)
        self.assertFalse({id(p) for p in policy.actor_parameters()} &
                         {id(p) for p in policy.value_parameters()})

    def test_distribution_has_only37_random_channels(self):
        policy, data = self.policy, inputs()
        for deterministic in (False, True):
            sampled = policy.act(*data, deterministic=deterministic)
            for key in ('action', 'latent', 'mean', 'log_std'):
                self.assertEqual(sampled[key].shape, (2, TRANSPORT_DIM))
                self.assertTrue(torch.isfinite(sampled[key]).all())
                self.assertTrue((sampled[key][:, ACTION_DIM:] == 0).all())
            self.assertTrue((sampled['action'].abs() <= 1.).all())
            torch.testing.assert_close(sampled['log_std'][:, :ACTION_DIM], torch.full((2, ACTION_DIM), -3.))
            evaluated = policy.evaluate(*data, sampled['latent'])
            torch.testing.assert_close(evaluated['logp'], sampled['logp'])
            distribution = Normal(sampled['mean'][:, :ACTION_DIM], sampled['log_std'][:, :ACTION_DIM].exp())
            torch.testing.assert_close(evaluated['entropy'], distribution.entropy().sum(-1))
            inert_changed = sampled['latent'].clone(); inert_changed[:, ACTION_DIM:] = 100.
            torch.testing.assert_close(policy.evaluate(*data, inert_changed)['logp'], sampled['logp'])
            changed = sampled['mean'].clone(); changed[:, :ACTION_DIM] += .01; changed[:, ACTION_DIM:] = 100.
            torch.testing.assert_close(policy.analytic_kl(sampled['mean'], sampled['log_std'],
                changed, sampled['log_std']), kl_divergence(distribution,
                    Normal(changed[:, :ACTION_DIM], distribution.scale)).sum(-1))

    def test_actor_only_path_never_evaluates_critic(self):
        policy, data = self.policy, inputs()
        with torch.no_grad():
            policy.actor_head.weight.normal_(std=.01)
            expected = policy.act(*data, deterministic=True)['action'][:, :ACTION_DIM]
        with patch.object(policy.value_encoder, 'forward', side_effect=AssertionError('critic called')):
            torch.testing.assert_close(policy.actor_action(data[0]), expected)
            action = policy.actor_action(data[0], deterministic=False)
            self.assertEqual(action.shape, (2, ACTION_DIM))
            self.assertTrue(torch.isfinite(action).all())

    def test_actor_and_critic_gradients_are_separate(self):
        policy, data = self.policy, inputs()
        sampled = policy.act(*data)
        (-sampled['logp'].mean()).backward()
        self.assertTrue(any(p.grad is not None for p in policy.actor_parameters()))
        self.assertTrue(all(p.grad is None for p in policy.value_parameters()))
        policy.zero_grad(set_to_none=True)
        result = policy(*data)
        (result['reward_value'].square().mean()+result['cost_value'].square().mean()).backward()
        self.assertTrue(all(p.grad is None for p in policy.actor_parameters()))
        self.assertTrue(any(p.grad is not None for p in policy.value_parameters()))

    def test_rejects_goals_nonfinite_and_wrong_shapes(self):
        policy = self.policy
        for slots in (1, 2):
            data = list(inputs())
            data[3] = torch.zeros(2, slots, 1)
            data[4] = torch.ones(2, slots, dtype=torch.bool)
            with self.assertRaisesRegex(ValueError, 'empty goal'):
                policy(*data)
        data = list(inputs()); data[1] = torch.zeros(2, 1, 0)
        with self.assertRaisesRegex(ValueError, 'empty goal'):
            policy(*data)
        for state in (torch.zeros(2, STATE_DIM-1), torch.full((2, STATE_DIM), float('nan')),
                      torch.zeros(2, STATE_DIM, dtype=torch.long)):
            with self.assertRaises(ValueError):
                policy.actor_action(state)
        for latent in (torch.zeros(2, ACTION_DIM), torch.full((2, TRANSPORT_DIM), float('inf'))):
            with self.assertRaises(ValueError):
                policy.evaluate(*inputs(), latent)

    def test_strict_contract_rejection(self):
        for section, key, value in (
                ('observation', 'schema', 'old'), ('observation', 'dimension', STATE_DIM-1),
                ('observation', 'fields', list(reversed(STATE_FIELDS))),
                ('observation', 'scales', [1.]*STATE_DIM), ('observation', 'event_dim', False),
                ('observation', 'priority_slots', 2), ('action', 'dimension', 39),
                ('action', 'names', list(reversed(ACTION_NAMES))), ('reward', 'schema', 'old')):
            bad = contract(); bad[section][key] = value
            with self.subTest(section=section, key=key), self.assertRaises(ValueError):
                WholeBodyPolicy(contract=bad)
        with self.assertRaises(ValueError):
            WholeBodyPolicy(contract=None)

    def test_cpu_ppo_update_checkpoint_roundtrip_and_identity_rejection(self):
        policy = self.policy
        config = PPOConfig(actor_lr=1e-5, epochs=1, minibatch_size=8)
        trainer = DecisionPPOTrainer(policy, config)
        before_actor = policy.actor_head.weight.detach().clone()
        before_value = policy.reward_critic.weight.detach().clone()
        metrics = trainer.update(rollout(policy))
        self.assertFalse(torch.equal(before_actor, policy.actor_head.weight))
        self.assertFalse(torch.equal(before_value, policy.reward_critic.weight))
        self.assertEqual(metrics['diagnostics']['valid_decisions'], 8)
        self.assertTrue(torch.isfinite(torch.tensor(metrics['analytic_kl'])))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'whole_body.pt'
            trainer.save(path, metadata={'test': 'state-only37'})
            restored = DecisionPPOTrainer(WholeBodyPolicy(contract=contract()), config)
            self.assertEqual(restored.load(path), {'test': 'state-only37'})
            self.assertEqual(restored.updates, 1)
            for key, value in policy.state_dict().items():
                torch.testing.assert_close(value, restored.policy.state_dict()[key], rtol=0, atol=0)
            altered = copy.deepcopy(contract()); altered['reward']['coefficient'] = .5
            incompatible = DecisionPPOTrainer(WholeBodyPolicy(contract=altered), config)
            with self.assertRaisesRegex(ValueError, 'mismatch'):
                incompatible.load(path)


if __name__ == '__main__':
    unittest.main()
