"""B is an optional idle preference; pressing must get zero posture reward."""
import copy
import math
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import torch
from scipy.spatial.transform import Rotation

from guitar_learning.gpu.finger_reward import (
    B_PREPARATION_INPUT_DEGREES, B_PREPARATION_SPREAD_DEGREES,
    B_PREPARATION_ANGLES_DEGREES, FINGER_COORDINATION_CONTRACT,
    FINGER_PREPARATION_CONTRACT, finger_preparation_reward)
from guitar_learning.skills.specialist_policy import SpecialistPolicy
from guitar_learning.song.curriculum_runtime import CurriculumCoordinator
from guitar_learning.tests import test_gpu_environment as fixtures
from guitar_learning.tests import test_gpu_finger_reward as posture_fixtures
from guitar_learning.tests.test_gpu_surface_learning import task
from guitar_learning.training.ppo import PPOTrainer


def inputs(times=(0.,)):
    n = len(times)
    data = posture_fixtures.FingerPostureTests().inputs(times=times)
    segments = []
    for (mcp, pip, dip), spread in zip(B_PREPARATION_INPUT_DEGREES, B_PREPARATION_SPREAD_DEGREES):
        first = Rotation.from_rotvec([math.radians(mcp), 0., math.radians(spread)])
        second = first*Rotation.from_euler('x', pip, degrees=True)
        third = second*Rotation.from_euler('x', dip, degrees=True)
        segments.append([q.as_quat() for q in (first, second, third)])
    data.update(onset=torch.tensor([4.], dtype=torch.float64),
        end=torch.tensor([5.], dtype=torch.float64), press=torch.tensor([3.], dtype=torch.float64),
        finger=torch.tensor([1]), contact=torch.zeros(n, dtype=torch.bool),
        distance=torch.ones(n, 1, dtype=torch.float64),
        segment_quaternion=torch.tensor(np.array(segments), dtype=torch.float64).expand(n, -1, -1, -1).clone())
    return data


class PreparationBTests(unittest.TestCase):
    environment = fixtures.TensorSongTests.environment
    advance = staticmethod(fixtures.TensorSongTests.advance)

    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def test_selected_B_geometry_gets_small_maximum_without_changing_inputs(self):
        data = inputs(); saved = copy.deepcopy(data)
        result = finger_preparation_reward(**data)
        torch.testing.assert_close(result['quality'], torch.ones(1, 4, dtype=torch.float64), rtol=0, atol=1e-14)
        self.assertAlmostEqual(float(result['rate']), .01, places=14)
        for key in data:
            torch.testing.assert_close(data[key], saved[key], rtol=0, atol=0)
        self.assertEqual(FINGER_PREPARATION_CONTRACT['coordination_rate_per_s'], 0.)
        self.assertEqual(FINGER_COORDINATION_CONTRACT['coordination_rate_per_s'], .05)

    def test_broad_flat_band_and_independent_outside_scalar_formula(self):
        for offset in (-14., 0., 14., 45.):
            data = inputs(); angles = torch.tensor(B_PREPARATION_ANGLES_DEGREES)+offset
            relative = Rotation.from_euler('x', angles.flatten().numpy(), degrees=True).as_quat().reshape(4, 3, 4)
            for f in range(4):
                accumulated = Rotation.identity()
                for j in range(3):
                    accumulated = accumulated*Rotation.from_quat(relative[f, j])
                    data['segment_quaternion'][0, f, j] = torch.tensor(accumulated.as_quat())
            expected = .01*math.exp(-3*max(abs(offset)-15., 0.)**2/30**2)
            self.assertAlmostEqual(float(finger_preparation_reward(**data)['rate']), expected, places=9)

    def test_any_finger_preparation_hold_and_boundary_zero_whole_hand(self):
        for finger in range(1, 5):
            data = inputs(times=(1., 2., 4., 5.))
            data['finger'].fill_(finger)
            result = finger_preparation_reward(**data)
            self.assertEqual(result['gate'].tolist(), [0.]*4)
            self.assertEqual(result['rate'].tolist(), [0.]*4)

    def test_temporal_fade_and_overlapping_next_note(self):
        data = inputs(times=(.75, .875, 1., 5., 5.125, 5.25))
        result = finger_preparation_reward(**data)
        torch.testing.assert_close(result['gate'], torch.tensor([1., .5, 0., 0., .5, 1.], dtype=torch.float64))
        data.update(onset=torch.tensor([4., 6.]), end=torch.tensor([5., 7.]),
            press=torch.tensor([3., 5.]), finger=torch.tensor([1, 4]), distance=torch.ones(6, 2))
        result = finger_preparation_reward(**data)
        self.assertEqual(result['gate'][-3:].tolist(), [0., 0., 0.])

    def test_contact_blocks_whole_hand_even_outside_song_window(self):
        data = inputs(times=(0., 0.)); data['contact'][1] = True
        result = finger_preparation_reward(**data)
        self.assertEqual(result['gate'].tolist(), [1., 0.])
        self.assertEqual(float(result['rate'][1]), 0.)

    def test_proximity_inclusive_and_invalid_distance_veto(self):
        data = inputs(times=(0.,)*5)
        data['distance'][:, 0] = torch.tensor([.039, .04, .040001, float('nan'), float('inf')])
        result = finger_preparation_reward(**data)
        self.assertEqual(result['gate'].tolist(), [0., 0., 1., 0., 0.])

    def test_empty_score_zero_and_bad_pose_finger_gets_no_credit(self):
        data = inputs()
        for key in ('onset', 'end', 'press', 'finger'):
            data[key] = data[key][:0]
        data['distance'] = torch.empty(1, 0)
        self.assertEqual(float(finger_preparation_reward(**data)['rate']), 0.)
        data = inputs(); data['segment_quaternion'][:, 0] = 0.
        result = finger_preparation_reward(**data)
        self.assertEqual(float(result['quality'][0, 0]), 0.)
        self.assertAlmostEqual(float(result['rate']), .0075, places=14)

    def test_contact_and_distance_shape_validation(self):
        for key, value in (('contact', torch.zeros(1)), ('distance', torch.ones(1, 2))):
            data = inputs(); data[key] = value
            with self.assertRaisesRegex(ValueError, 'Aligned'):
                finger_preparation_reward(**data)

    def test_actual_environment_preparation_and_holding_have_no_posture_reward(self):
        env, row, _ = self.environment(task=task())
        self.advance(env, row)
        self.assertFalse(env.terms['song_finger_coordination'].any())
        self.assertFalse(env.terms['song_finger_standby'].any())
        self.assertEqual(env.contract['reward']['schema'], 'guitar_learning.gpu_tensor_song_reward.v16')
        self.assertEqual(env.contract['reward']['finger_posture']['schema'], FINGER_PREPARATION_CONTRACT['schema'])

    def test_real_environment_idle_integrates_and_one_segment_load_vetoes(self):
        env, row, _ = self.environment(task=task(onset=10., end=11., press=10.))
        # Put every target far away in this CPU measurement fixture. It is not
        # a physically reachable hand-pose or native stability test.
        row['body_state'][:, env.finger_segment_indices.flatten(), 2] += 1.
        env.reset([0, 1], row)
        self.assertTrue((env.surface_distance > .04).all())
        row['contact_force'][1, env.finger_segment_indices[2, 0], 2] = .02
        self.advance(env, row)
        self.assertGreater(float(env.terms['song_finger_standby'][0]), 0.)
        self.assertLessEqual(float(env.terms['song_finger_standby'][0]), .01/60)
        self.assertEqual(float(env.terms['song_finger_standby'][1]), 0.)
        self.assertFalse(env.terms['song_finger_coordination'].any())

    def test_v16_checkpoint_roundtrip_rejects_same_shape_v13(self):
        env, _, _ = self.environment()
        pool = SimpleNamespace(environment=env, set_curriculum=env.set_curriculum)
        def make(contract):
            policy = SpecialistPolicy(544, size='small', role='left', contract=contract)
            CurriculumCoordinator(policy, pool)
            return PPOTrainer(policy)
        current = make(env.contract)
        old = copy.deepcopy(env.contract)
        old['reward']['schema'] = 'guitar_learning.gpu_tensor_song_reward.v13'
        old['reward']['finger_posture'] = copy.deepcopy(FINGER_COORDINATION_CONTRACT)
        previous = make(old)
        with tempfile.TemporaryDirectory() as folder, patch('torch.cuda.is_available', return_value=False):
            newpath, oldpath = Path(folder)/'v16.pt', Path(folder)/'v13.pt'
            current.save(newpath); previous.save(oldpath)
            resumed = make(env.contract); resumed.load(newpath)
            before = copy.deepcopy(resumed.policy.state_dict())
            with self.assertRaisesRegex(ValueError, 'mismatch'):
                resumed.load(oldpath)
            for name, value in before.items():
                torch.testing.assert_close(resumed.policy.state_dict()[name], value, rtol=0, atol=0)
