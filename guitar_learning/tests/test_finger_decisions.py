import unittest

import torch
from torch import nn
from torch.distributions import Normal

from guitar_learning.training.finger_decisions import DecisionCollector


class TinyDecisionPolicy(nn.Module):
    def __init__(self, phase='F'):
        super().__init__()
        self.phase = phase
        self.actor = nn.Linear(5, 39)
        self.log_std = nn.Parameter(torch.full((39,), -3.))
        self.reward_critic = nn.Linear(5, 1)
        self.cost_critic = nn.Linear(5, 1)
        self.architecture = dict(schema='tiny_decision_test', phase=phase)
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
        mask[17:33] = True
        if self.phase == 'R':
            mask = ~mask
            mask[33:] = False
        elif self.phase == 'J':
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
    def __init__(self, k=3, failure=True, truncate=False):
        self.num_envs = 2
        self.k, self.failure, self.truncate = k, failure, truncate
        self.valid = True
        self.clock = torch.zeros(2)
        self.actions, self.resets = [], []
        self.contract = {}
        self.observation = self._obs()

    def _obs(self):
        state = torch.zeros(2, 5)
        state[:, 0] = self.clock
        return dict(state=state, events=torch.zeros(2, 1, 24), mask=torch.ones(2, 1, dtype=torch.bool),
                    priority_events=torch.zeros(2, 1, 24), priority_mask=torch.ones(2, 1, dtype=torch.bool))

    def plan_decisions(self, remaining_ticks):
        return torch.full((2,), min(self.k, remaining_ticks), dtype=torch.long)

    def decision_observation(self, planned_ticks, observation=None):
        obs = {key: value.clone() for key, value in (observation or self.observation).items()}
        obs['state'][:, 1] = planned_ticks/6.
        return obs

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
    def test_async_failure_discount_padding_and_raw_journal(self):
        pool = FakeDecisionPool()
        collector = DecisionCollector(TinyDecisionPolicy(), pool, gamma=.5, cost_gamma=.25)
        raw, decisions = [], []
        b, episodes = collector.collect(5, transition_callback=lambda *args: raw.append(args[0]),
            decision_callback=decisions.append, policy_version=7)
        self.assertEqual(b['duration'].tolist(), [[2, 3], [2, 2], [1, 0]])
        self.assertEqual(b['valid'].tolist(), [[True, True], [True, True], [True, False]])
        self.assertEqual(b['episode_id'][:, 0].tolist(), [0, 1, 2])
        self.assertEqual(pool.resets, [[0], [0]])
        self.assertEqual(len(episodes), 2)
        self.assertEqual(raw, list(range(5)))
        self.assertEqual(len(decisions), 5)
        self.assertTrue(all(row['policy_version'] == 7 for row in decisions))
        self.assertAlmostEqual(float(b['reward'][0, 1]), 1.75)
        self.assertAlmostEqual(float(b['cost'][0, 1]), 2.625)
        self.assertEqual(float(b['next_reward_value'][0, 0]), 0.)
        self.assertEqual(int(b['start_control_tick'][1, 1]), 3)
        # Bootstrap at tick3 sees the next plan2, while the rollout cut sees plan3.
        self.assertAlmostEqual(float(b['next_reward_value'][0, 1]), 2/6)
        self.assertAlmostEqual(float(b['next_reward_value'][1, 1]), 3/6)

    def test_only_fingers_held_support_fresh_and_no_cross_update_hold(self):
        pool = FakeDecisionPool(failure=False)
        model = TinyDecisionPolicy()
        collector = DecisionCollector(model, pool)
        first, _ = collector.collect(5)
        self.assertTrue(torch.equal(pool.actions[0][:, 17:33], pool.actions[1][:, 17:33]))
        self.assertFalse(torch.equal(pool.actions[0][:, :17], pool.actions[1][:, :17]))
        self.assertTrue(all(bool((action[:, 33:] == 0).all()) for action in pool.actions))
        with torch.no_grad():
            model.actor.bias[17:33] += 1.
        second, _ = collector.collect(2)
        self.assertTrue(bool((pool.actions[5][:, 17:33] > .5).all()))
        self.assertEqual(second['start_control_tick'][0].tolist(), [5, 5])
        self.assertEqual(pool.resets, [])
        self.assertEqual(int(first['duration'].sum()), 10)

    def test_k1_and_truncation_uses_final_observation(self):
        model = TinyDecisionPolicy('J')
        pool = FakeDecisionPool(k=1, truncate=True)
        b, _ = DecisionCollector(model, pool).collect(3)
        self.assertTrue(bool(b['valid'].all()))
        self.assertTrue(bool((b['duration'] == 1).all()))
        self.assertTrue(bool(b['truncated'][1, 0]))
        self.assertAlmostEqual(float(b['next_reward_value'][1, 0]), 1/6)
        self.assertEqual(b['state'][:, 0, 0].tolist(), [0., 1., 0.])

    def test_invalid_raw_cost_invalidates_collector(self):
        pool = FakeDecisionPool()
        step = pool.step
        def invalid(action):
            values = list(step(action))
            values[2][0] = -1
            return tuple(values)
        pool.step = invalid
        collector = DecisionCollector(TinyDecisionPolicy(), pool)
        with self.assertRaises(FloatingPointError):
            collector.collect(2)
        self.assertFalse(collector.valid)
        self.assertFalse(pool.valid)


if __name__ == '__main__':
    unittest.main()
