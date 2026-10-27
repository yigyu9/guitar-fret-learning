"""Action semantics, diagnostics and strict checkpoint compatibility together."""
import copy
from pathlib import Path
import tempfile
import unittest

import torch

from guitar_learning.gpu.control import BatchedController
from guitar_learning.gpu.environment import TensorSongEnvironment
from guitar_learning.skills.specialist_policy import SpecialistPolicy
from guitar_learning.training.ppo import PPOConfig, PPOTrainer
from guitar_learning.tool.training.train_legacy import settings_document
from guitar_learning.tests.test_gpu_control import fake_scene
from guitar_learning.tests import test_gpu_environment as fixtures


class FingerStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def environment(self, mode):
        scene, _ = fake_scene()
        controller = BatchedController(scene, finger_action_mode=mode)
        metadata, snapshot = fixtures.fixture()
        metadata['action_contract'] = controller.contract
        env = TensorSongEnvironment(metadata, bundle=fixtures.BUNDLE,
            song=dict(fixtures.SONG, finger_action_mode=mode), hand='left', device='cpu')
        env.reset([0, 1], snapshot)
        return env, snapshot

    def test_default_and_comparison_change_only_the_codec_setting(self):
        position = settings_document('left', device='cuda:0', finger_action_mode='position')
        incremental = settings_document('left', device='cuda:0')
        self.assertEqual(position['song'].pop('finger_action_mode'), 'position')
        self.assertEqual(incremental['song'].pop('finger_action_mode'), 'incremental')
        self.assertEqual(position, incremental)
        self.assertEqual(position['song_training']['target_count'], 67)
        self.assertEqual(position['song_training']['control_ticks'], 1969)

    def test_explicit_codec_is_rejected_outside_gpu_left(self):
        for hand, device, physics in (('left', 'cpu', 'cpu'), ('right', 'cpu', 'cpu'),
                                      ('right', 'cuda:0', 'gpu')):
            self.assertNotIn('finger_action_mode', settings_document(hand, device=device, physics=physics)['song'])
            for mode in ('position', 'incremental'):
                with self.subTest(hand=hand, mode=mode), self.assertRaises(ValueError):
                    settings_document(hand, device=device, physics=physics, finger_action_mode=mode)
        for mode in ('', 'velocity', True):
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                settings_document('left', finger_action_mode=mode)

    def test_position_sign_is_not_outward_velocity_and_native_limits_are_separate(self):
        for mode, outward in (('position', 0.), ('incremental', 1.)):
            env, snapshot = self.environment(mode)
            joint = int(env.finger_joint_indices[0])
            channel = int(env.finger_action_indices[0])
            snapshot['target'][:, joint] = env.finger_upper[0]
            snapshot['q'][:, joint] = (env.finger_lower[0]+env.finger_upper[0])/2
            env.reset([0, 1], snapshot)
            action = torch.zeros(2, 39); action[:, channel] = .02
            fixtures.TensorSongTests.advance(env, snapshot, action)
            row = env._finger_motion_episode(0)
            self.assertEqual(row['action_mode'], mode)
            self.assertEqual(row['values']['limit_outward_command_fraction'][0], outward)
            self.assertEqual(row['values']['target_native_limit_fraction'][0], 1.)
            self.assertEqual(row['values']['actual_native_limit_fraction'][0], 0.)

    def test_setting_cannot_mislabel_actual_controller_semantics(self):
        metadata, _ = fixtures.fixture()
        metadata['action_contract']['action_codec'] = dict(mode='incremental')
        with self.assertRaisesRegex(ValueError, 'disagree'):
            TensorSongEnvironment(metadata, bundle=fixtures.BUNDLE,
                song=dict(fixtures.SONG, finger_action_mode='position'), hand='left', device='cpu')

    def test_strict_resume_rejects_other_codec_before_mutating_model(self):
        trainers = {}
        for mode in ('position', 'incremental'):
            env, _ = self.environment(mode)
            torch.manual_seed(7)
            policy = SpecialistPolicy(552, size='small', role='left', contract=env.contract)
            trainers[mode] = PPOTrainer(policy, PPOConfig())
        initial = {k: v.clone() for k, v in trainers['position'].policy.state_dict().items()}
        for key, value in trainers['incremental'].policy.state_dict().items():
            torch.testing.assert_close(value, initial[key], rtol=0, atol=0)
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory)/'position.pt'
            trainers['position'].save(checkpoint)
            with self.assertRaisesRegex(ValueError, 'mismatch'):
                trainers['incremental'].load(checkpoint)
            for key, value in trainers['incremental'].policy.state_dict().items():
                torch.testing.assert_close(value, initial[key], rtol=0, atol=0)
            trainers['position'].load(checkpoint)

    def test_reward_and_termination_remain_identical_between_modes(self):
        position, _ = self.environment('position')
        incremental, _ = self.environment('incremental')
        for key in ('reward', 'termination', 'observation'):
            self.assertEqual(position.contract[key], incremental.contract[key])
        position_task, incremental_task = (copy.deepcopy(env.contract['task'])
                                          for env in (position, incremental))
        for task in (position_task, incremental_task):
            task['song'].pop('finger_action_mode')
        self.assertEqual(position_task, incremental_task)


if __name__ == '__main__':
    unittest.main()
