"""두 목표·독립 actor/critic·실제27축 분포와 K1 PPO 연결을 CPU에서 검사한다."""
import copy
from pathlib import Path
import tempfile
import unittest

import torch
from torch.distributions import Normal, kl_divergence

from guitar_learning.training.compact_strike import CompactStrikePolicy, OBSERVATION_SCHEMA
from guitar_learning.training.ppo import DecisionPPOTrainer, PPOConfig
from guitar_learning.tool.experiments.compact_strike import CompactStrikeCollector
from guitar_learning.tool.experiments.right27.control import ACTION_NAMES
from guitar_learning.tests.test_finger_decisions import FakeDecisionPool
from guitar_learning.gpu.compact_strike import (STATE_DIM, GOAL_DIM, STATE_FIELDS,
    STATE_SCALES, GOAL_FIELDS, GOAL_SCALES)


def contract(state_dim=STATE_DIM, event_dim=GOAL_DIM):
    return dict(schema='guitar_learning.training.v1', compact_strike=dict(schema=OBSERVATION_SCHEMA),
        observation=dict(dimension=state_dim, fields=list(STATE_FIELDS), scales=list(STATE_SCALES),
            event_dim=event_dim, goal_fields=list(GOAL_FIELDS), goal_scales=list(GOAL_SCALES), priority_slots=2),
        action=dict(dimension=39, names=list(ACTION_NAMES), active_indices=list(range(12, 39)),
                    inactive_indices=list(range(12))))


def inputs(count=2, state_dim=STATE_DIM, event_dim=GOAL_DIM):
    return (torch.randn(count, state_dim), torch.zeros(count, 0, event_dim),
        torch.zeros(count, 0, dtype=torch.bool), torch.randn(count, 2, event_dim),
        torch.ones(count, 2, dtype=torch.bool))


class StrikePool(FakeDecisionPool):
    def _obs(self):
        state, events, mask, goals, valid = inputs()
        state.zero_(); state[:, 0] = self.clock
        goals.zero_()
        return dict(state=state, events=events, mask=mask, priority_events=goals, priority_mask=valid)


class CompactStrikePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def test_fixed_widths_separate_encoders_and_history_dimensions(self):
        for size in ('small', 'medium', 'large'):
            policy = CompactStrikePolicy(STATE_DIM, size=size, contract=contract())
            data = inputs()
            self.assertEqual(policy.actor_encoder.features(data[0], data[3], data[4]).shape, (2, 384))
            self.assertEqual(policy.actor_encoder.fusion[0].weight.shape, (512, 384))
            self.assertEqual(policy.value_encoder.fusion[0].weight.shape, (256, 384))
            self.assertEqual(policy.actor_head.weight.shape, (27, 256))
            self.assertFalse({id(p) for p in policy.actor_parameters()} &
                             {id(p) for p in policy.value_parameters()})
        for state_dim, event_dim in ((STATE_DIM-1, GOAL_DIM), (STATE_DIM, GOAL_DIM-1)):
            with self.assertRaises(ValueError):
                CompactStrikePolicy(state_dim, contract=contract(state_dim, event_dim))

    def test27_distribution_and_fixed12_transport(self):
        policy, data = CompactStrikePolicy(STATE_DIM, contract=contract()), inputs()
        for deterministic in (False, True):
            result = policy.act(*data, deterministic=deterministic)
            for key in ('action', 'latent', 'mean', 'log_std'):
                self.assertEqual(result[key].shape, (2, 39))
                self.assertTrue(bool((result[key][:, :12] == 0).all()))
            evaluated = policy.evaluate(*data, result['latent'])
            torch.testing.assert_close(evaluated['logp'], result['logp'])
            distribution = Normal(result['mean'][:, 12:], result['log_std'][:, 12:].exp())
            torch.testing.assert_close(evaluated['entropy'], distribution.entropy().sum(-1))
            latent = result['latent'].clone(); latent[:, :12] = 100.
            torch.testing.assert_close(policy.evaluate(*data, latent)['logp'], result['logp'])
            changed = result['mean'].clone(); changed[:, :12] = 100.; changed[:, 12:] += .01
            torch.testing.assert_close(policy.analytic_kl(result['mean'], result['log_std'],
                changed, result['log_std']), kl_divergence(distribution,
                    Normal(changed[:, 12:], distribution.scale)).sum(-1))

    def test_empty_goals_stay_zero_after_bias_and_nan_payload(self):
        policy, data = CompactStrikePolicy(STATE_DIM, contract=contract()), list(inputs())
        data[4][:, 1] = False
        features = policy.actor_encoder.features(data[0], data[3], data[4])
        self.assertTrue(bool((features[:, 320:] == 0).all()))
        data[3][:, 1] = float('nan')
        torch.testing.assert_close(features, policy.actor_encoder.features(data[0], data[3], data[4]))
        self.assertTrue(all(torch.isfinite(value).all() for value in policy(*data).values()))
        data[4][:, 1] = True
        with self.assertRaises(ValueError):
            policy(*data)

    def test_contract_and_general_event_rejection(self):
        for kind, key, value in (('compact_strike', 'schema', 'old'),
                ('action', 'active_indices', list(range(33))),
                ('observation', 'priority_slots', 8), ('observation', 'scales', [0.]*STATE_DIM),
                ('observation', 'goal_fields', list(reversed(GOAL_FIELDS))),
                ('observation', 'goal_scales', [0.]*GOAL_DIM)):
            bad = copy.deepcopy(contract()); bad[kind][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                CompactStrikePolicy(STATE_DIM, contract=bad)
        policy, data = CompactStrikePolicy(STATE_DIM, contract=contract()), list(inputs())
        data[1] = torch.zeros(2, 1, GOAL_DIM); data[2] = torch.ones(2, 1, dtype=torch.bool)
        with self.assertRaisesRegex(ValueError, 'empty general'):
            policy(*data)

    def test_collector_keeps_elbow_wrist6_and_decision_ppo_roundtrip(self):
        torch.manual_seed(7)
        policy, pool = CompactStrikePolicy(STATE_DIM, contract=contract()), StrikePool(failure=False)
        collector = CompactStrikeCollector(policy, pool)
        buffer, episodes = collector.collect(4)
        self.assertTrue(bool(buffer['valid'].all()))
        self.assertTrue(bool((buffer['duration'] == 1).all()))
        self.assertTrue(any(bool((action[:, 33:] != 0).any()) for action in pool.actions))
        for tick, action in enumerate(pool.actions):
            torch.testing.assert_close(action, buffer['latent'][tick].tanh())
            self.assertTrue(bool((action[:, :12] == 0).all()))
        config = PPOConfig(actor_lr=1e-5, epochs=1, minibatch_size=8)
        trainer = DecisionPPOTrainer(policy, config)
        before = policy.actor_head.weight.detach().clone()
        metrics = trainer.update(buffer, episodes)
        self.assertFalse(torch.equal(before, policy.actor_head.weight))
        self.assertEqual(metrics['diagnostics']['valid_decisions'], 8)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'policy.pt'; trainer.save(path)
            restored = DecisionPPOTrainer(CompactStrikePolicy(STATE_DIM, contract=contract()), config)
            restored.load(path)
            for key, value in policy.state_dict().items():
                torch.testing.assert_close(value, restored.policy.state_dict()[key], rtol=0, atol=0)


if __name__ == '__main__':
    unittest.main()
