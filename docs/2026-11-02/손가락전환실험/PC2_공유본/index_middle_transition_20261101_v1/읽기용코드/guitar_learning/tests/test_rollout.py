import unittest
import numpy as np
import torch
from guitar_learning.tool.validation.rollout import RolloutCollector
from guitar_learning.tests.test_policy import policy


def obs(value):
    return dict(state=np.full(5,value,np.float32), events=np.zeros((2,24),np.float32),
                mask=np.zeros(2,bool), priority_events=np.zeros((2,24),np.float32),
                priority_mask=np.zeros(2,bool))


class Env:
    def __init__(self, terminated=False):
        self.terminated = terminated
        self.resets = 0
    def reset(self):
        self.resets += 1
        return obs(-10), {}
    def step(self, action):
        return obs(5), 1., self.terminated, not self.terminated, dict(cost=.25,termination_reason='timeline_complete')


class RolloutTests(unittest.TestCase):
    def test_truncated_bootstraps_final_not_reset_and_preserves_cost(self):
        model = policy()
        env = Env()
        with torch.no_grad():
            expected = model(*RolloutCollector(model, env)._inputs(obs(5)))['reward_value'].item()
        data, episodes = RolloutCollector(model,env).collect(2)
        self.assertEqual(data['state'].shape,(2,1,5))
        self.assertTrue(torch.allclose(data['next_reward_value'],torch.full((2,1),expected)))
        self.assertEqual([x['cost'] for x in episodes],[.25,.25])
        self.assertEqual(env.resets,3)

    def test_boundary_bootstraps_and_cost_accumulates_across_collects(self):
        env=Env()
        count=[0]
        def step(action):
            count[0]+=1
            return obs(count[0]), 1., False, count[0]==3, dict(cost=.25,termination_reason='time_limit' if count[0]==3 else None)
        env.step=step
        model=policy()
        collector=RolloutCollector(model,env)
        data,episodes=collector.collect(2)
        self.assertEqual(episodes,[])
        self.assertEqual(env.resets,1)
        with torch.no_grad(): expected=model(*collector._inputs(obs(2)))['reward_value'].item()
        self.assertAlmostEqual(data['next_reward_value'][-1,0].item(),expected)
        _,episodes=collector.collect(1)
        self.assertEqual(episodes[0]['cost'],.75)
        self.assertEqual(episodes[0]['steps'],3)
        self.assertEqual(episodes[0]['reason'],'time_limit')

    def test_termination_zeros_bootstrap(self):
        data,_=RolloutCollector(policy(),Env(True)).collect(2)
        self.assertTrue(torch.equal(data['next_reward_value'],torch.zeros(2,1)))
        self.assertTrue(torch.equal(data['next_cost_value'],torch.zeros(2,1)))

    def test_missing_input_invalidates_collector(self):
        env=Env()
        env.reset=lambda: ({}, {})
        collector=RolloutCollector(policy(),env)
        with self.assertRaises(ValueError): collector.collect(1)
        self.assertFalse(collector.dataset_valid)
        with self.assertRaises(RuntimeError): collector.collect(1)

    def test_failure_is_not_success(self):
        env=Env()
        def fail(action): raise RuntimeError('guard_fault')
        env.step=fail
        collector=RolloutCollector(policy(),env)
        with self.assertRaisesRegex(RuntimeError,'guard_fault'): collector.collect(1)
        self.assertFalse(collector.dataset_valid)
