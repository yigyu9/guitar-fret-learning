"""직접 위치 제어의 설정·진단·구형 체크포인트 거부를 검증한다."""
import copy
from pathlib import Path
import tempfile
import unittest

import torch

from guitar_learning.gpu.control import BatchedController
from guitar_learning.gpu.environment import TensorSongEnvironment
from guitar_learning.training.compact_press_v5 import CompactPressV5Policy
from guitar_learning.gpu.compact_press_v5 import CompactPressV5Environment
from guitar_learning.training.ppo import PPOConfig, PPOTrainer
from guitar_learning.tool.training.train_legacy import settings_document
from guitar_learning.tests.test_gpu_control import fake_scene
from guitar_learning.tests import test_gpu_environment as fixtures


class FingerStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def environment(self, mode='position'):
        scene, _ = fake_scene()
        controller = BatchedController(scene, finger_action_mode=mode)
        metadata, snapshot = fixtures.fixture()
        metadata['action_contract'] = controller.contract
        env = TensorSongEnvironment(metadata, bundle=fixtures.BUNDLE,
            song=dict(fixtures.SONG, finger_action_mode=mode), hand='left', device='cpu')
        env.reset([0, 1], snapshot)
        return env, snapshot

    def test_position_is_the_only_default_codec_setting(self):
        explicit = settings_document('left', device='cuda:0', finger_action_mode='position')
        default = settings_document('left', device='cuda:0')
        self.assertEqual(default['song']['finger_action_mode'], 'position')
        self.assertEqual(explicit, default)
        self.assertEqual(default['song_training']['target_count'], 67)
        self.assertEqual(default['song_training']['control_ticks'], 1969)
        with self.assertRaises(ValueError):
            settings_document('left', device='cuda:0', finger_action_mode='incremental')

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
        env, snapshot = self.environment()
        joint = int(env.finger_joint_indices[0])
        channel = int(env.finger_action_indices[0])
        snapshot['target'][:, joint] = env.finger_upper[0]
        snapshot['q'][:, joint] = (env.finger_lower[0]+env.finger_upper[0])/2
        env.reset([0, 1], snapshot)
        action = torch.zeros(2, 39)
        action[:, channel] = .02
        fixtures.TensorSongTests.advance(env, snapshot, action)
        row = env._finger_motion_episode(0)
        self.assertEqual(row['action_mode'], 'position')
        self.assertEqual(row['values']['limit_outward_command_fraction'][0], 0.)
        self.assertEqual(row['values']['target_native_limit_fraction'][0], 1.)
        self.assertEqual(row['values']['actual_native_limit_fraction'][0], 0.)

    def test_legacy_codec_and_mismatched_setting_are_rejected(self):
        metadata, _ = fixtures.fixture()
        metadata['action_contract']['action_codec'] = dict(mode='incremental')
        with self.assertRaisesRegex(ValueError, 'must be position'):
            TensorSongEnvironment(metadata, bundle=fixtures.BUNDLE,
                song=dict(fixtures.SONG, finger_action_mode='position'), hand='left', device='cpu')
        metadata['action_contract']['action_codec'] = dict(mode='position')
        with self.assertRaisesRegex(ValueError, 'disagree'):
            TensorSongEnvironment(metadata, bundle=fixtures.BUNDLE,
                song=dict(fixtures.SONG, finger_action_mode='incremental'), hand='left', device='cpu')

    def test_strict_resume_rejects_archived_codec_before_mutating_model(self):
        scene, _ = fake_scene()
        metadata, _ = fixtures.fixture()
        metadata['action_contract'] = BatchedController(scene).contract
        env = CompactPressV5Environment(metadata, bundle=fixtures.BUNDLE,
            song=dict(fixtures.SONG, finger_action_mode='position'), device='cpu',
            skill=dict(schema='guitar_learning.finger_skill.v3', phase='J', scope='scheduled',
                hold_ticks=1, exploration='independent', planned_transitions=400, full_song_after=100))
        current = copy.deepcopy(env.contract)
        old = copy.deepcopy(current)
        old['action']['target_contract']['schema'] = 'guitar_learning.gpu_finite_control.v3'
        old['action']['target_contract']['action_codec'] = dict(mode='incremental')
        old['task']['song']['finger_action_mode'] = 'incremental'
        trainers = {}
        # 구형 제어를 실행하지 않고 저장본의 이전 행동 의미만 재현한다.
        for name, contract in (('current', current), ('old', old)):
            torch.manual_seed(7)
            trainers[name] = PPOTrainer(CompactPressV5Policy(464, size='small', contract=contract), PPOConfig())
        initial = {key: value.clone() for key, value in trainers['current'].policy.state_dict().items()}
        with tempfile.TemporaryDirectory() as directory:
            old_checkpoint = Path(directory)/'old_codec.pt'
            current_checkpoint = Path(directory)/'position.pt'
            trainers['old'].save(old_checkpoint)
            trainers['current'].save(current_checkpoint)
            with self.assertRaisesRegex(ValueError, 'mismatch'):
                trainers['current'].load(old_checkpoint)
            for key, value in trainers['current'].policy.state_dict().items():
                torch.testing.assert_close(value, initial[key], rtol=0, atol=0)
            trainers['current'].load(current_checkpoint)


if __name__ == '__main__':
    unittest.main()
