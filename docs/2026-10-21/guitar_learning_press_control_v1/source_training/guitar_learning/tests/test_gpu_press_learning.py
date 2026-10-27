"""CPU press-target integration checks; no native pressure or policy-score claim."""
import copy
import math
from pathlib import Path
import random
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import torch

from guitar_learning.core.finger_control import default_profile
from guitar_learning.core.observations import EVENT_SCALES
from guitar_learning.skills.specialist_policy import SpecialistPolicy
from guitar_learning.song.curriculum_runtime import CurriculumCoordinator
from guitar_learning.tests import test_gpu_environment as fixtures
from guitar_learning.tests import test_gpu_surface_learning as surface_fixtures
from guitar_learning.training.ppo import PPOTrainer


class PressLearningTests(unittest.TestCase):
    environment = fixtures.TensorSongTests.environment
    advance = staticmethod(fixtures.TensorSongTests.advance)
    place = surface_fixtures.SurfaceLearningTests.place
    isolate_placed_sample = surface_fixtures.SurfaceLearningTests.isolate_placed_sample

    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def placed_environment(self):
        env, snapshot, _ = self.environment(task=surface_fixtures.task((1,), end=2.))
        row = self.place(env, snapshot)
        self.isolate_placed_sample(env)
        env.reset([0, 1], row)
        return env, row

    def test_four_actual_substep_rates_integrate_once_and_preserve_inputs(self):
        env, row = self.placed_environment()
        torch.testing.assert_close(env.surface_distance, torch.full((2, 1), .003), atol=2e-6, rtol=0)
        saved = {k:v.clone() for k, v in row.items()}
        action = torch.zeros(2, 39)
        env.begin_control(action)
        expected_rate = 4*math.exp(-.003/.02)  # Candidate, zero speed and zero request.
        for i in range(4):
            env.substep(row)
            torch.testing.assert_close(env.terms['song_finger_tracking'],
                torch.full((2,), expected_rate*(i+1)/240), atol=2e-7, rtol=0)
        env.end_control()
        torch.testing.assert_close(env.episode_reward_terms['song_finger_tracking'],
            torch.full((2,), expected_rate/60), atol=2e-7, rtol=0)
        self.assertEqual(env.clock.tolist(), [4, 4])
        for k in row:
            torch.testing.assert_close(row[k], saved[k], rtol=0, atol=0)
        self.assertFalse(action.any())
        self.assertEqual((default_profile()['finger_stiffness'], default_profile()['finger_damping']), (12., 1.5))
        self.assertEqual((default_profile()['thumb_stiffness'], default_profile()['thumb_damping']), (8., 1.25))

    def test_constant_request_reduces_new_term_with_same_q_geometry_and_forces(self):
        env, row = self.placed_environment()
        action = torch.zeros(2, 39)
        action[1, env.finger_action_indices] = .05
        original = action.clone()
        for _ in range(2):
            self.advance(env, row, action)
            # mean((4*.05/.2)^2)=1 on all21 axes: same candidate quality halves.
            self.assertAlmostEqual(float(env.terms['song_finger_tracking'][1]),
                                   float(env.terms['song_finger_tracking'][0])/2, places=7)
        self.assertEqual(env.terms['action_change'].tolist(), [0., 0.])
        torch.testing.assert_close(action, original, rtol=0, atol=0)

    def test_physical_failure_suppresses_entire_tick_tracking_and_episode_component(self):
        env, row = self.placed_environment()
        env.begin_control(torch.zeros(2, 39))
        env.substep(row)
        self.assertTrue((env.terms['song_finger_tracking'] > 0).all())
        for i in range(3):
            moved = {k:v.clone() for k, v in row.items()}
            if i == 0:
                moved['body_state'][0, env.guitar_index, 0] += .1
            env.substep(moved)
        result = env.end_control()
        self.assertEqual(result[3].tolist(), [True, False])
        self.assertEqual(float(env.terms['song_finger_tracking'][0]), 0.)
        self.assertGreater(float(env.terms['song_finger_tracking'][1]), 0.)
        self.assertEqual(result[-1][0]['reward_components']['song_finger_tracking'], 0.)

    def test_wire_candidate_success_stays_separate_from_physical_press_target(self):
        env, row = self.placed_environment()
        self.assertTrue(env.candidate.all())
        self.assertFalse(env.wrong.any())
        torch.testing.assert_close(env.surface_delta[..., :2], torch.zeros(2, 1, 2), atol=2e-6, rtol=0)
        torch.testing.assert_close(env.surface_delta[..., 2], torch.full((2, 1), -.003), atol=2e-6, rtol=0)
        self.assertEqual(env.contract['observation']['surface_geometry']['schema'], 'guitar_learning.left_surface_events.v2')
        self.assertEqual(env.contract['reward']['schema'], 'guitar_learning.gpu_tensor_song_reward.v4')
        self.assertEqual(env.observation()['state'].shape, (2, 512))
        self.assertEqual(env.contract['action']['dimension'], 39)
        for _ in range(3):
            self.advance(env, row)
        self.assertTrue(env.note['contact_done'].all())
        self.assertAlmostEqual(float(env.note['clean'][0, 0]), .05, places=12)
        ledger = env._episode(0, False)['left_note_ledger']
        self.assertEqual(ledger['schema'], 'guitar_learning.surface_note_ledger.v2')
        self.assertIn('original virtual strings', ledger['scope'])

    def test_h32_window_and_partial_reset_preserve_other_episode_tracking(self):
        env, row = self.placed_environment()
        for _ in range(32):
            self.advance(env, row)
        before = env.episode_reward_terms['song_finger_tracking'].clone()
        self.assertTrue((before > 0).all())
        env.reset_reward_window()
        self.assertEqual(env.clock.tolist(), [128, 128])
        torch.testing.assert_close(env.episode_reward_terms['song_finger_tracking'], before)
        self.advance(env, row)
        after = env.episode_reward_terms['song_finger_tracking'].clone()
        self.assertTrue((after > before).all())
        window = env.reward_window_means(2)['song_finger_tracking']
        env.reset([0], row)
        self.assertEqual(env.clock.tolist(), [0, 132])
        self.assertEqual(float(env.episode_reward_terms['song_finger_tracking'][0]), 0.)
        torch.testing.assert_close(env.episode_reward_terms['song_finger_tracking'][1], after[1], rtol=0, atol=0)
        self.assertEqual(env.reward_window_means(2)['song_finger_tracking'], window)

    def test_right_keeps_original_contract_scaling_reward_and_no_new_term(self):
        env, row, obs = self.environment(hand='right')
        self.assertEqual(obs['state'].shape, (2, 500))
        self.assertEqual(env.contract['reward']['schema'], 'guitar_learning.gpu_tensor_song_reward.v1')
        self.assertIsNone(env.contract['reward']['left_curriculum'])
        self.assertNotIn('surface_geometry', env.contract['observation'])
        self.assertNotIn('finger_tracking', env.contract['reward'])
        torch.testing.assert_close(env.event_scales, torch.tensor(EVENT_SCALES, dtype=env.event_scales.dtype))
        selected, present = torch.zeros(2, dtype=torch.long), torch.ones(2, dtype=torch.bool)
        potentials = [(selected, present, torch.full((2,), p)) for p in (.8, .7)]
        with patch('guitar_learning.gpu.environment.finger_tracking_reward', side_effect=AssertionError('left-only helper')):
            with patch.object(env, '_right_potential', side_effect=potentials):
                result = self.advance(env, row)
        torch.testing.assert_close(result[1], torch.full((2,), .25*(.99*.7-.8)), atol=1e-7, rtol=0)
        self.assertNotIn('song_finger_tracking', env.terms)
        self.assertNotIn('left_note_ledger', env._episode(0, False))

    def assert_tree_equal(self, a, b):
        if isinstance(a, torch.Tensor):
            torch.testing.assert_close(a, b, rtol=0, atol=0)
        elif isinstance(a, np.ndarray):
            np.testing.assert_array_equal(a, b)
        elif isinstance(a, dict):
            self.assertEqual(a.keys(), b.keys())
            for k in a:
                self.assert_tree_equal(a[k], b[k])
        elif isinstance(a, (tuple, list)):
            self.assertEqual(len(a), len(b))
            for x, y in zip(a, b):
                self.assert_tree_equal(x, y)
        else:
            self.assertEqual(a, b)

    def test_same3331_state_roundtrip_and_v3_identity_rejection_without_mutation(self):
        env, _, obs = self.environment()
        pool = SimpleNamespace(environment=env, set_curriculum=env.set_curriculum)
        def make(contract):
            policy = SpecialistPolicy(512, size='small', role='left', contract=contract)
            coordinator = CurriculumCoordinator(policy, pool)
            return policy, coordinator, PPOTrainer(policy)
        policy, coordinator, trainer = make(env.contract)
        self.assertEqual(tuple(policy.left_curriculum_state.shape), (3331,))
        evidence = dict(valid=True, reason='timeline_complete', left_curriculum=dict(full_safe=True,
            finger_metrics=[dict(target_count=n, near_fraction=1., contact_fraction=0., success_fraction=0.) for n in env.finger_counts]))
        coordinator.advance([evidence]*256, obs)
        # Populate both Adam states so rejection must preserve more than empty dicts.
        for optimizer in (trainer.actor_optimizer, trainer.value_optimizer):
            for group in optimizer.param_groups:
                for parameter in group['params']:
                    parameter.grad = torch.ones_like(parameter)
            optimizer.step(); optimizer.zero_grad()
        trainer.updates, trainer.cost_weight = 7, 1.25
        old_contract = copy.deepcopy(env.contract)
        old_contract['reward']['schema'] = 'guitar_learning.gpu_tensor_song_reward.v3'
        old_contract['reward'].pop('finger_tracking')
        old_contract['reward']['surface_learning'].pop('press_surface')
        old_contract['reward']['surface_learning']['schema'] = 'guitar_learning.surface_fretting.v1'
        old_contract['observation']['surface_geometry'].pop('press_surface')
        old_contract['observation']['surface_geometry']['schema'] = 'guitar_learning.left_surface_events.v1'
        old_policy, _, old_trainer = make(old_contract)
        self.assertEqual(tuple(old_policy.left_curriculum_state.shape), (3331,))
        with tempfile.TemporaryDirectory() as folder, patch('torch.cuda.is_available', return_value=False):
            current, previous = Path(folder)/'current.pt', Path(folder)/'v3.pt'
            trainer.save(current); old_trainer.save(previous)
            restored, restored_coordinator, resumed = make(env.contract)
            resumed.load(current); restored_coordinator.restore()
            self.assert_tree_equal(policy.state_dict(), restored.state_dict())
            self.assert_tree_equal(trainer.actor_optimizer.state_dict(), resumed.actor_optimizer.state_dict())
            self.assert_tree_equal(trainer.value_optimizer.state_dict(), resumed.value_optimizer.state_dict())
            np.testing.assert_array_equal(coordinator.state.state_vector(), restored_coordinator.state.state_vector())
            self.assertEqual((resumed.updates, resumed.cost_weight), (7, 1.25))
            payload = torch.load(current, map_location='cpu', weights_only=False)
            self.assert_tree_equal((torch.get_rng_state(), np.random.get_state(), random.getstate()),
                                   (payload['torch_rng'], payload['numpy_rng'], payload['python_rng']))
            before = copy.deepcopy((restored.state_dict(), resumed.actor_optimizer.state_dict(),
                resumed.value_optimizer.state_dict(), resumed.updates, resumed.cost_weight,
                torch.get_rng_state(), np.random.get_state(), random.getstate()))
            with self.assertRaisesRegex(ValueError, 'mismatch'):
                resumed.load(previous)
            after = (restored.state_dict(), resumed.actor_optimizer.state_dict(), resumed.value_optimizer.state_dict(),
                resumed.updates, resumed.cost_weight, torch.get_rng_state(), np.random.get_state(), random.getstate())
            self.assert_tree_equal(before, after)


if __name__ == '__main__':
    unittest.main()
