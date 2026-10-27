"""CPU press-target integration checks; no native pressure or policy-score claim."""
import ast
import copy
import hashlib
import json
import math
from pathlib import Path
import random
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import torch
from scipy.spatial.transform import Rotation

from guitar_learning.core.control import LEFT_HAND_NAMES
from guitar_learning.core.finger_control import default_profile
from guitar_learning.core.observations import EVENT_SCALES
from guitar_learning.skills.specialist_policy import SpecialistPolicy
from guitar_learning.song.curriculum_runtime import CurriculumCoordinator
from guitar_learning.tests import test_gpu_environment as fixtures
from guitar_learning.tests import test_gpu_surface_learning as surface_fixtures
from guitar_learning.training.ppo import PPOTrainer
from guitar_learning.music_task import ScoreTask, ScoreTarget


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

    def test_actual_posture_encoding_uses_body_rotations_and_preserves_native_values(self):
        env, row, _ = self.environment(task=surface_fixtures.task(onset=4., end=5., press=3.8))
        saved_q = row['q'].clone()
        palm = Rotation.from_euler('z', 34., degrees=True)
        row['body_state'][:, env.finger_palm_index, 3:7] = torch.tensor(palm.as_quat()).float()
        angles = ((40., 55., 35.), (25., 30., 15.), (-10., 20., 0.), (90., 45., 25.))
        expected = []
        for finger, triple in enumerate(angles):
            pose = palm
            for joint, degrees in enumerate(triple):
                pose = pose*Rotation.from_euler('x', degrees, degrees=True)
                row['body_state'][:, env.finger_segment_indices[finger, joint], 3:7] = torch.tensor(pose.as_quat()).float()
                expected.extend((math.sin(math.radians(degrees)), math.cos(math.radians(degrees))))
        observation = env.reset([0, 1], row)
        torch.testing.assert_close(observation['state'][:, 512:536], torch.tensor([expected]*2), atol=3e-7, rtol=0)
        torch.testing.assert_close(observation['state'][:, 536:544], torch.ones(2, 8))
        torch.testing.assert_close(row['q'], saved_q, rtol=0, atol=0)
        self.assertEqual(len(set(env.contract['observation']['fields'])), 544)
        self.assertEqual(env.contract['observation']['priority_slots'], 8)

    def test_invalid_projection_masks_whole_finger_posture_encoding(self):
        env, row, _ = self.environment(task=surface_fixtures.task(onset=4., end=5., press=3.8))
        palm = Rotation.from_quat(row['body_state'][0, env.finger_palm_index, 3:7].numpy())
        degenerate = palm*Rotation.from_euler('z', 90., degrees=True)
        row['body_state'][:, env.finger_segment_indices[0, 0], 3:7] = torch.tensor(degenerate.as_quat()).float()
        obs = env.reset([0, 1], row)
        torch.testing.assert_close(obs['state'][:, 512:518], torch.zeros(2, 6), rtol=0, atol=0)
        torch.testing.assert_close(obs['state'][:, 536], torch.zeros(2), rtol=0, atol=0)
        self.assertTrue(torch.isfinite(obs['state']).all())
        torch.testing.assert_close(obs['state'][:, 537:540], torch.ones(2, 3))

    def test_each_finger_priority_keeps_tracking_and_next_even_outside_general_window(self):
        targets = []
        for finger in range(1, 5):
            for onset, end, press, fret in ((.5, 1.5, .4, 5), (3.2, 3.5, 3., 6)):
                index = len(targets)
                targets.append(ScoreTarget('note-%d'%index, 'event-%d'%index,
                    finger-1, fret, finger, 1, onset, end, press, onset, end))
        env, row, _ = self.environment(task=ScoreTask(tuple(targets)))
        env.clock[:] = 240
        obs = env.observation()
        self.assertTrue(obs['priority_mask'].all())
        priority = obs['priority_events']*env.event_scales
        torch.testing.assert_close(priority[:, :, 5], torch.tensor([[1., 1., 2., 2., 3., 3., 4., 4.]]).expand(2, -1))
        torch.testing.assert_close(priority[:, ::2, 0], torch.full((2, 4), -.5))
        torch.testing.assert_close(priority[:, 1::2, 0], torch.full((2, 4), 2.2))
        self.assertEqual(obs['mask'].sum(-1).tolist(), [4, 4])
        # Every finger is preparing/holding; standby is not inferred from global focus.
        torch.testing.assert_close(obs['state'][:, 540:544], torch.zeros(2, 4))
        env.clock[:] = 960
        obs = env.observation()
        self.assertFalse(obs['priority_mask'].any())
        self.assertFalse(obs['priority_events'].any())
        torch.testing.assert_close(obs['state'][:, 540:544], torch.ones(2, 4))

    def test_four_actual_substep_rates_integrate_once_and_preserve_inputs(self):
        env, row = self.placed_environment()
        torch.testing.assert_close(env.surface_distance, torch.zeros(2, 1), atol=2e-6, rtol=0)
        saved = {k:v.clone() for k, v in row.items()}
        action = torch.zeros(2, 39)
        env.begin_control(action)
        expected_rate = 2.  # Zero distance; candidate adds no tracking multiplier.
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
        # Any prepared/pressing finger suppresses the whole-hand B preference.
        for name in ('song_finger_coordination', 'song_finger_standby'):
            self.assertFalse(env.terms[name].any())
            torch.testing.assert_close(env.episode_reward_terms[name], env.terms[name], rtol=0, atol=0)

    def test_all_finger_command_changes_are_free_with_same_q_geometry_and_forces(self):
        env, row = self.placed_environment()
        saved = {k:v.clone() for k,v in row.items()}
        for commands in (torch.full((21,), .4), torch.linspace(-.9, .9, 21), torch.full((21,), -.7), torch.zeros(21)):
            action = torch.zeros(2, 39); action[1, env.finger_action_indices] = commands
            original = action.clone()
            moving = {k:v.clone() for k,v in row.items()}
            moving['qd'][1] = 3.
            moving['body_state'][1, :, 7:13] = .4
            self.advance(env, moving, action)
            for key in ('song_finger_tracking', 'song_finger_coordination', 'song_finger_standby'):
                torch.testing.assert_close(env.terms[key][1], env.terms[key][0], rtol=0, atol=0)
            self.assertEqual(env.terms['action_change'].tolist(), [0., 0.])
            torch.testing.assert_close(action,original,rtol=0,atol=0)
        for key in row:torch.testing.assert_close(row[key],saved[key],rtol=0,atol=0)

    def test_left_grouped_deadband_and_original_right_cost_keep39_denominator(self):
        for hand in ('left', 'right'):
            env, row, _ = self.environment(hand=hand)
            previous = torch.zeros(2, 39)
            channels = list(range(12)) if hand == 'left' else list(range(33, 39))
            for scale in (.5, -.75, 0.):
                action = torch.zeros(2, 39)
                action[1, channels] = scale
                if hand == 'left':action[1, env.finger_action_indices] = .8*scale
                delta = action[1, channels]-previous[1, channels]
                if hand == 'left':
                    expected = -sum((.0025 if channel >= 9 else .01)*max(abs(float(value))-.05, 0.)**2
                                    for channel, value in zip(channels, delta))/39/60
                else:
                    expected = -.01*float(delta.square().sum())/39/60
                self.advance(env, row, action)
                self.assertAlmostEqual(float(env.terms['action_change'][1]), expected, places=11)
                self.assertEqual(float(env.terms['action_change'][0]), 0.)
                previous = action.clone()
        self.assertNotIn('action_change', env.contract['reward'])

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
        for name in ('song_finger_coordination', 'song_finger_standby'):
            self.assertEqual(float(env.terms[name][0]), 0.)
            self.assertEqual(float(env.terms[name][1]), 0.)
            self.assertEqual(result[-1][0]['reward_components'][name], 0.)

    def test_pad_candidate_success_and_approach_share_physical_press_target(self):
        env, row = self.placed_environment()
        self.assertTrue(env.candidate.all())
        self.assertFalse(env.wrong.any())
        torch.testing.assert_close(env.surface_delta[..., :2], torch.zeros(2, 1, 2), atol=2e-6, rtol=0)
        torch.testing.assert_close(env.surface_delta[..., 2], torch.zeros(2, 1), atol=2e-6, rtol=0)
        self.assertEqual(env.contract['observation']['surface_geometry']['schema'], 'guitar_learning.left_surface_events.v4')
        self.assertEqual(env.contract['reward']['schema'], 'guitar_learning.gpu_tensor_song_reward.v16')
        self.assertEqual(env.contract['reward']['finger_tracking']['schema'], 'guitar_learning.gpu_finger_tracking_rate.v7')
        self.assertEqual(env.contract['reward']['action_change']['excluded_joint_names'], list(LEFT_HAND_NAMES))
        self.assertEqual(env.contract['reward']['action_change']['normalization_dimensions'], 39)
        self.assertEqual(env.contract['reward']['action_change']['coefficient_per_s'], .01)
        self.assertIn('frame_source', env.contract['reward']['finger_posture'])
        self.assertEqual(env.observation()['state'].shape, (2, 544))
        self.assertEqual(env.contract['action']['dimension'], 39)
        for _ in range(3):
            self.advance(env, row)
        self.assertTrue(env.note['contact_done'].all())
        self.assertAlmostEqual(float(env.note['clean'][0, 0]), .05, places=12)
        ledger = env._episode(0, False)['left_note_ledger']
        self.assertEqual(ledger['schema'], 'guitar_learning.surface_note_ledger.v6')
        self.assertIn('press plane', ledger['scope'])

    def test_h32_window_and_partial_reset_preserve_other_episode_tracking(self):
        env, row = self.placed_environment()
        for _ in range(32):
            self.advance(env, row)
        posture_before = {name: env.episode_reward_terms[name].clone()
                          for name in ('song_finger_coordination', 'song_finger_standby')}
        before = env.episode_reward_terms['song_finger_tracking'].clone()
        self.assertTrue((before > 0).all())
        env.reset_reward_window()
        self.assertEqual(env.clock.tolist(), [128, 128])
        torch.testing.assert_close(env.episode_reward_terms['song_finger_tracking'], before)
        for name, value in posture_before.items():
            torch.testing.assert_close(env.episode_reward_terms[name], value, rtol=0, atol=0)
        self.advance(env, row)
        after = env.episode_reward_terms['song_finger_tracking'].clone()
        self.assertTrue((after > before).all())
        window = env.reward_window_means(2)['song_finger_tracking']
        posture_after = {name: env.episode_reward_terms[name].clone() for name in posture_before}
        env.reset([0], row)
        self.assertEqual(env.clock.tolist(), [0, 132])
        self.assertEqual(float(env.episode_reward_terms['song_finger_tracking'][0]), 0.)
        torch.testing.assert_close(env.episode_reward_terms['song_finger_tracking'][1], after[1], rtol=0, atol=0)
        self.assertEqual(env.reward_window_means(2)['song_finger_tracking'], window)
        for name, value in posture_after.items():
            self.assertEqual(float(env.episode_reward_terms[name][0]), 0.)
            torch.testing.assert_close(env.episode_reward_terms[name][1], value[1], rtol=0, atol=0)

    def test_right_keeps_original_contract_scaling_reward_and_no_new_term(self):
        env, row, obs = self.environment(hand='right')
        self.assertEqual(obs['state'].shape, (2, 500))
        self.assertEqual(env.contract['reward']['schema'], 'guitar_learning.gpu_tensor_song_reward.v1')
        self.assertIsNone(env.contract['reward']['left_curriculum'])
        self.assertNotIn('surface_geometry', env.contract['observation'])
        self.assertNotIn('finger_tracking', env.contract['reward'])
        self.assertNotIn('finger_posture', env.contract['reward'])
        torch.testing.assert_close(env.event_scales, torch.tensor(EVENT_SCALES, dtype=env.event_scales.dtype))
        selected, present = torch.zeros(2, dtype=torch.long), torch.ones(2, dtype=torch.bool)
        potentials = [(selected, present, torch.full((2,), p)) for p in (.8, .7)]
        with patch('guitar_learning.gpu.environment.pad_tracking_reward', side_effect=AssertionError('left-only helper')):
            with patch.object(env, '_right_potential', side_effect=potentials):
                result = self.advance(env, row)
        torch.testing.assert_close(result[1], torch.full((2,), .25*(.99*.7-.8)), atol=1e-7, rtol=0)
        self.assertNotIn('song_finger_tracking', env.terms)
        self.assertNotIn('song_finger_coordination', env.terms)
        self.assertNotIn('song_finger_standby', env.terms)
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

    def test_v16_same3331_roundtrip_and_v7_identity_rejection_without_mutation(self):
        env, _, obs = self.environment()
        pool = SimpleNamespace(environment=env, set_curriculum=env.set_curriculum)
        def make(contract):
            policy = SpecialistPolicy(contract['observation']['dimension'], size='small', role='left', contract=contract)
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
        # Read only metadata AST from the SHA-preserved v7 source; never import it.
        root = Path(__file__).resolve().parents[2]
        archive = root/'guitar_learning/archive/20261022_before_targeted_finger_learning_v1'
        manifest = json.loads((archive/'manifest.json').read_text())
        trees = {}
        for relative in ('guitar_learning/gpu/finger_reward.py', 'guitar_learning/gpu/environment.py'):
            path = archive/relative
            record = next(r for r in manifest['files'] if r['archived'] == relative)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), record['sha256'])
            trees[relative] = ast.parse(path.read_text())
        old_contract = copy.deepcopy(env.contract)
        old_contract['reward']['schema'] = 'guitar_learning.gpu_tensor_song_reward.v7'
        for name, key in (('FINGER_REWARD_CONTRACT', 'finger_tracking'),
                          ('FINGER_COORDINATION_CONTRACT', 'finger_posture')):
            value = next(node.value for node in trees['guitar_learning/gpu/finger_reward.py'].body
                         if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets))
            old_contract['reward'][key].update({kw.arg:ast.literal_eval(kw.value) for kw in value.keywords
                                               if kw.arg != 'target_selector_schema'})
        surface = next(node for node in ast.walk(trees['guitar_learning/gpu/environment.py'])
                       if isinstance(node, ast.Call) and {'potential', 'approach'} <= {kw.arg for kw in node.keywords})
        for kw in surface.keywords:
            if kw.arg in ('schema', 'potential'):
                old_contract['reward']['surface_learning'][kw.arg] = ast.literal_eval(kw.value)
        for key in ('target_selector_schema', 'potential_distance_scale_m'):
            old_contract['reward']['surface_learning'].pop(key)
        self.assertEqual(old_contract['reward']['finger_tracking']['schema'], 'guitar_learning.gpu_finger_tracking_rate.v4')
        self.assertEqual(old_contract['reward']['finger_posture']['schema'], 'guitar_learning.gpu_finger_posture_rate.v1')
        # All non-reward contracts, including motion-free action semantics, stay identical.
        for key in ('observation', 'action', 'termination', 'task', 'native_backend'):
            self.assertEqual(old_contract[key], env.contract[key])
        old_policy, _, old_trainer = make(old_contract)
        self.assertEqual(tuple(old_policy.left_curriculum_state.shape), (3331,))
        with tempfile.TemporaryDirectory() as folder, patch('torch.cuda.is_available', return_value=False):
            current, previous = Path(folder)/'current.pt', Path(folder)/'v7.pt'
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
