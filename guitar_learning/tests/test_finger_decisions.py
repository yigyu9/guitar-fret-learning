"""J 공동 정책의 매 tick 표본화·종료 가치·수집 경계 보존을 검사한다."""
import unittest
from unittest.mock import patch

import torch
from torch import nn
from torch.distributions import Normal

from guitar_learning.training.rollout import DecisionCollector, GpuPool


class TinyDecisionPolicy(nn.Module):
    """상태 시계로 가치와 지지 명령이 변하는 작은 J 정책이다."""
    phase = 'J'

    def __init__(self):
        super().__init__()
        self.actor = nn.Linear(5, 39)
        self.log_std = nn.Parameter(torch.full((39,), -3.))
        self.reward_critic = nn.Linear(5, 1)
        self.cost_critic = nn.Linear(5, 1)
        self.architecture = dict(schema='tiny_joint_decision_test', phase='J')
        self.sample_calls = 0
        with torch.no_grad():
            self.actor.weight.zero_()
            self.actor.bias.zero_()
            self.actor.weight[:17, 0] = .1
            for critic in (self.reward_critic, self.cost_critic):
                critic.weight.zero_()
                critic.weight[:, 1] = 1.
                critic.bias.zero_()

    def actor_parameters(self):
        return list(self.actor.parameters())+[self.log_std]

    def value_parameters(self):
        return list(self.reward_critic.parameters())+list(self.cost_critic.parameters())

    def _active_mask(self):
        mask = torch.zeros(39, dtype=torch.bool)
        mask[:33] = True
        return mask

    def forward(self, state, events, mask, priority_events, priority_mask):
        return dict(mean=self.actor(state), log_std=self.log_std.expand(len(state), -1),
                    reward_value=self.reward_critic(state).squeeze(-1),
                    cost_value=self.cost_critic(state).squeeze(-1))

    def log_probability(self, mean, log_std, latent):
        active = self._active_mask()
        z = latent[:, active]
        return (Normal(mean[:, active], log_std[:, active].exp()).log_prob(z)-
                torch.log(1-z.tanh().square()+1e-8)).sum(-1)

    def act(self, *inputs, deterministic=False):
        self.sample_calls += 1
        result = self(*inputs)
        latent = result['mean'].clone()
        active = self._active_mask()
        if not deterministic:
            latent[:, active] += torch.randn_like(latent[:, active])*result['log_std'][:, active].exp()
        result.update(action=latent.tanh(), latent=latent,
                      logp=self.log_probability(result['mean'], result['log_std'], latent))
        return result

    def evaluate(self, *inputs):
        latent = inputs[-1]
        result = self(*inputs[:-1])
        result.update(logp=self.log_probability(result['mean'], result['log_std'], latent),
                      entropy=(result['log_std'][:, self._active_mask()]+1.4189385332).sum(-1))
        return result

    def analytic_kl(self, old_mean, old_std, mean, log_std):
        active = self._active_mask()
        return (log_std-old_std+(old_std.mul(2).exp()+(old_mean-mean).square())/
                (2*log_std.mul(2).exp())-.5)[:, active].sum(-1)


class FakeDecisionPool:
    """한 행만 2 tick마다 종료해 부분 초기화를 관찰하는 CPU 환경 묶음이다."""
    def __init__(self, failure=True, truncate=False):
        self.num_envs = 2
        self.failure, self.truncate = failure, truncate
        self.valid = True
        self.clock = torch.zeros(2)
        self.actions, self.resets = [], []
        self.contract = {}
        self.observation = self._obs()

    def _obs(self):
        state = torch.zeros(2, 5)
        state[:, 0] = self.clock
        state[:, 1] = self.clock/6.
        return dict(state=state, events=torch.zeros(2, 1, 24), mask=torch.ones(2, 1, dtype=torch.bool),
                    priority_events=torch.zeros(2, 1, 24), priority_mask=torch.ones(2, 1, dtype=torch.bool))

    def step(self, action):
        self.actions.append(action.clone())
        self.clock += 1
        done = torch.tensor([self.failure and self.clock[0] == 2, False])
        terminated = done & (not self.truncate)
        truncated = done & self.truncate
        self.observation = self._obs()
        episodes = [dict(cost=2., valid=True, reason='terminal_failure')] if bool(done[0]) else []
        return self.observation, torch.ones(2), torch.ones(2)*2, terminated, truncated, episodes

    def reset(self, ids):
        self.resets.append(ids.tolist())
        self.clock[ids] = 0
        self.observation = self._obs()
        return self.observation, []


class DecisionCollectorTests(unittest.TestCase):
    def test_each_tick_is_one_valid_decision_and_partial_reset_preserves_other_clock(self):
        pool = FakeDecisionPool()
        policy = TinyDecisionPolicy()
        collector = DecisionCollector(policy, pool, gamma=.5, cost_gamma=.25)
        raw, decisions, progress = [], [], []
        b, episodes = collector.collect(5, transition_callback=lambda *args: raw.append(args[0]),
            decision_callback=decisions.append, progress_callback=progress.append, policy_version=7)
        self.assertTrue(bool(b['valid'].all()))
        self.assertEqual(b['duration'].tolist(), [[1, 1]]*5)
        self.assertEqual(b['episode_id'].tolist(), [[0, 0], [0, 0], [1, 0], [1, 0], [2, 0]])
        self.assertEqual(b['state'][:, 0, 0].tolist(), [0., 1., 0., 1., 0.])
        self.assertEqual(b['state'][:, 1, 0].tolist(), [0., 1., 2., 3., 4.])
        self.assertEqual(pool.resets, [[0], [0]])
        self.assertEqual(len(episodes), 2)
        self.assertEqual(policy.sample_calls, 5)
        self.assertEqual(raw, list(range(5)))
        self.assertEqual(len(decisions), 10)
        self.assertTrue(torch.equal(b['reward'], torch.ones(5, 2)))
        self.assertTrue(torch.equal(b['cost'], torch.full((5, 2), 2.)))
        self.assertEqual(b['next_reward_value'][1, 0].item(), 0.)
        self.assertAlmostEqual(b['next_reward_value'][1, 1].item(), 2/6)
        self.assertAlmostEqual(b['next_reward_value'][4, 1].item(), 5/6)
        self.assertEqual(progress[-1]['transitions'], 10)
        for tick in range(5):
            for identity in range(2):
                row = decisions[tick*2+identity]
                self.assertEqual(row['env_id'], identity)
                self.assertEqual(row['episode_id'], int(b['episode_id'][tick, identity]))
                self.assertEqual(row['policy_version'], 7)
                self.assertEqual(row['start_control_tick'], tick)
                self.assertEqual(row['end_control_tick'], tick+1)
                self.assertEqual(row['duration'], 1)
                self.assertEqual(row['raw_control_ticks'], [tick])
                self.assertEqual(row['discounted_reward'], 1.)
                self.assertEqual(row['discounted_cost'], 2.)
                self.assertNotIn('planned_ticks', row)

    def test_joint_actions_resample_each_tick_and_collection_boundary_keeps_clock(self):
        torch.manual_seed(7)
        pool = FakeDecisionPool(failure=False)
        model = TinyDecisionPolicy()
        collector = DecisionCollector(model, pool)
        first, _ = collector.collect(5)
        self.assertFalse(torch.equal(pool.actions[0][:, 17:33], pool.actions[1][:, 17:33]))
        self.assertFalse(torch.equal(pool.actions[0][:, :17], pool.actions[1][:, :17]))
        self.assertTrue(all(bool((action[:, 33:] == 0).all()) for action in pool.actions))
        with torch.no_grad():
            model.actor.bias[17:33] += 1.
        decisions = []
        second, _ = collector.collect(2, decision_callback=decisions.append)
        self.assertTrue(bool((pool.actions[5][:, 17:33] > .5).all()))
        self.assertEqual(second['start_control_tick'][0].tolist(), [5, 5])
        self.assertEqual(second['state'][:, 0, 0].tolist(), [5., 6.])
        self.assertEqual([row['raw_control_ticks'] for row in decisions], [[5], [5], [6], [6]])
        self.assertEqual(pool.resets, [])
        self.assertEqual(collector.control_ticks, 7)
        self.assertEqual(model.sample_calls, 7)
        self.assertEqual(int(first['duration'].sum()), 10)

    def test_truncation_bootstraps_final_observation_before_reset(self):
        pool = FakeDecisionPool(truncate=True)
        b, _ = DecisionCollector(TinyDecisionPolicy(), pool).collect(3)
        self.assertTrue(bool(b['truncated'][1, 0]))
        self.assertFalse(bool(b['terminated'].any()))
        self.assertAlmostEqual(float(b['next_reward_value'][1, 0]), 2/6)
        self.assertAlmostEqual(float(b['next_cost_value'][1, 0]), 2/6)
        self.assertEqual(b['state'][:, 0, 0].tolist(), [0., 1., 0.])

    def test_buffer_is_detached_and_independent_of_next_collection(self):
        collector = DecisionCollector(TinyDecisionPolicy(), FakeDecisionPool())
        first, episodes = collector.collect(3)
        preserved = {key: value.clone() for key, value in first.items()}
        collector.collect(2)
        for key, value in first.items():
            self.assertFalse(value.requires_grad)
            self.assertTrue(torch.equal(value, preserved[key]), key)
        self.assertEqual(episodes, [dict(cost=2., valid=True, reason='terminal_failure')])

    def test_invalid_raw_cost_invalidates_collector_without_returning_partial_batch(self):
        for bad_cost in (-1., float('inf'), float('nan')):
            with self.subTest(cost=bad_cost):
                pool = FakeDecisionPool()
                step = pool.step
                def invalid(action):
                    values = list(step(action))
                    values[2][0] = bad_cost
                    return tuple(values)
                pool.step = invalid
                collector = DecisionCollector(TinyDecisionPolicy(), pool)
                with self.assertRaises(FloatingPointError):
                    collector.collect(2)
                self.assertFalse(collector.valid)
                self.assertFalse(pool.valid)
                with self.assertRaises(ValueError):
                    collector.collect(1)
                self.assertEqual(len(pool.actions), 1)

    def test_callback_failure_invalidates_collector(self):
        pool = FakeDecisionPool()
        collector = DecisionCollector(TinyDecisionPolicy(), pool)
        def fail(_):
            raise RuntimeError('journal write failed')
        with self.assertRaisesRegex(RuntimeError, 'journal write failed'):
            collector.collect(3, decision_callback=fail)
        self.assertFalse(collector.valid)
        self.assertFalse(pool.valid)
        self.assertEqual(collector.control_ticks, 0)

    def test_old_skill_schema_is_rejected_before_scene_creation(self):
        for schema in ('guitar_learning.finger_skill.v1', 'guitar_learning.finger_skill.v2'):
            with self.subTest(schema=schema), patch.object(GpuPool, '_create_scene') as create:
                with self.assertRaisesRegex(ValueError, 'v3'):
                    GpuPool(dict(num_envs=2, finger_skill=dict(schema=schema)), None)
                create.assert_not_called()


if __name__ == '__main__':
    unittest.main()
