"""Explicit experiment settings must not silently change budgets or PPO defaults."""
import math
import unittest
from guitar_learning.training.runner import settings_document


class SettingsTests(unittest.TestCase):
    def test_partial_ppo_settings_are_expanded_for_reproducibility(self):
        result=settings_document(dict(num_envs=8,horizon=128,updates=4,initial_std=.12,
                                      ppo=dict(actor_lr=1e-4,minibatch_size=256)))
        self.assertEqual(result['num_envs']*result['horizon'],1024)
        self.assertEqual(result['ppo']['actor_lr'],1e-4)
        self.assertEqual(result['ppo']['gamma'],.99)
        self.assertAlmostEqual(result['initial_std'],.12)

    def test_invalid_or_silent_extra_budgets_rejected(self):
        for value in (dict(num_envs=3),dict(horizon=0),dict(updates=True),dict(max_wall_seconds=-1),
                      dict(initial_std=0),dict(initial_std=math.nan),dict(envs=8),dict(stage='full')):
            with self.subTest(value=value),self.assertRaises(ValueError):settings_document(value)

    def test_defaults_preserve_existing_policy_and_task(self):
        value=settings_document({})
        self.assertAlmostEqual(value['initial_std'],math.exp(-3))
        self.assertEqual((value['stage'],value['size']),('B','medium'))
        self.assertEqual(value['ppo']['target_kl'],.02)
        self.assertEqual(value['ppo']['cost_weight'],1.)
        self.assertEqual((value['num_envs'],value['horizon'],value['checkpoint_every']),(8,256,5))
        self.assertEqual(value['min_available_memory_gib'],4.)
        self.assertEqual(value['music'],dict(reward_mode='legacy',goal_event_indices=None))

    def test_monitoring_and_music_settings_validation(self):
        for value in (dict(min_available_memory_gib=0),dict(resource_interval_seconds=True),
            dict(heartbeat_seconds=math.nan),dict(worker_timeout_seconds=-1),dict(music=[]),
            dict(music=dict(reward_mode='unknown')),dict(music=dict(goal_event_indices=[])),
            dict(music=dict(goal_event_indices=[1,1])),dict(music=dict(goal_event_indices=[True])),
            dict(stage='C',music=dict(goal_event_indices=[1]))):
            with self.subTest(value=value),self.assertRaises(ValueError):settings_document(value)
        value=settings_document(dict(music=dict(goal_event_indices=[0,3],reward_mode='dense_v2')))
        self.assertEqual(value['music']['goal_event_indices'],[0,3])
