"""Fresh-entry/profile integration using recorded bodies, not native PD evidence."""
import copy
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import torch

from guitar_learning.core.control import LEFT_HAND_NAMES
from guitar_learning.core.control import default_profile
from guitar_learning.runtime.finger_session import FlexibleLeftFingerSession
from guitar_learning.runtime.persistent_session import PersistentHeadlessPreparedSession
from guitar_learning.training.policy import SpecialistPolicy
from guitar_learning.song import hand_environment, runtime
from guitar_learning.song.curriculum_runtime import CurriculumCoordinator
from guitar_learning.tests.test_ppo import assert_tree
from guitar_learning.tests.test_training_environment import LongRecordedSession
from guitar_learning.tests.test_song_environment import BUNDLE, SONG
from guitar_learning.tool.validation.rollout import RolloutCollector
from guitar_learning.training import parallel
from guitar_learning.training.ppo import PPOConfig, PPOTrainer
from guitar_learning.tool.training.train_legacy import settings_document


ROOT = Path(__file__).resolve().parents[2]


class RecordingPool:
    def __init__(self):
        self.progress = []

    def set_curriculum(self, progress):
        self.progress.append(progress)
        return dict(progress=progress)


class FlexibleFingerStartTests(unittest.TestCase):
    def setUp(self):
        torch.set_num_threads(1)
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        self.environments = []

    def tearDown(self):
        for env in self.environments:
            env.close()
        self.folder.cleanup()

    def environment(self, role='left', song=None):
        sessions = []
        def factory(config, out):
            session = LongRecordedSession(config, out)
            session.finger_control_description = dict(profile=default_profile(), applied=True,
                scope='recorded interface only; no native PD change executed')
            sessions.append(session)
            return session
        def contacts(scene):
            return copy.deepcopy(sessions[-1].row()['native_contacts']['contacts'])
        config = settings_document(role, device='cpu')['song'] if song is None else song
        env = hand_environment.build_environment({}, self.root/str(len(self.environments)),
            bundle=BUNDLE, song=config, role=role, session_factory=factory,
            contact_reader=contacts)
        self.environments.append(env)
        return env, sessions

    def trainer(self, env):
        model = SpecialistPolicy(env.contract['observation']['dimension'], size='small',
                                 contract=env.contract, role='left')
        coordinator = CurriculumCoordinator(model, RecordingPool())
        trainer = PPOTrainer(model, PPOConfig(actor_lr=1e-6, target_kl=.1, epochs=1))
        return trainer, coordinator

    def assert_rng_equal(self, saved):
        self.assertTrue(torch.equal(torch.get_rng_state(), saved[0]))
        current = np.random.get_state()
        self.assertEqual(current[0], saved[1][0])
        np.testing.assert_array_equal(current[1], saved[1][1])
        self.assertEqual(current[2:], saved[1][2:])
        self.assertEqual(random.getstate(), saved[2])

    def test_default_left_profile_and_right_settings_scope(self):
        left = settings_document('left', device='cpu')
        right = settings_document('right', device='cpu')
        self.assertEqual(left['song']['finger_control'], default_profile())
        self.assertEqual(left['song_training']['observation_dimension'], 512)
        self.assertNotIn('finger_control', right['song'])
        self.assertNotIn('left_curriculum', right['song'])
        self.assertEqual(right['song_training']['observation_dimension'], 500)

    def test_entry_help_still_imports_neither_native_nor_tensor_libraries(self):
        script = '''
import importlib.abc, runpy, sys
class Guard(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in ('isaacgym', 'numpy', 'torch'):
            raise AssertionError('help imported '+fullname)
sys.meta_path.insert(0, Guard())
sys.argv = ['train', '--help']
runpy.run_module('guitar_learning.tool.training.train_legacy', run_name='__main__')
'''
        result = subprocess.run([sys.executable, '-B', '-c', script], cwd='/tmp',
            env=dict(os.environ, PYTHONPATH=str(ROOT), PYTHONDONTWRITEBYTECODE='1'),
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('--hand {left,right}', result.stdout)

    def test_spawn_worker_selects_explicit_native_session_only_for_profile(self):
        for role, expected in (('left', FlexibleLeftFingerSession),
                               ('right', PersistentHeadlessPreparedSession)):
            settings = settings_document(role, device='cpu')
            spec = dict(config={}, out=str(self.root/role), bundle=str(BUNDLE),
                        song=settings['song'], specialist=settings['specialist'])
            with patch.dict(sys.modules, {'isaacgym': SimpleNamespace()}), \
                 patch.object(parallel, '_compact', parallel._compact), \
                 patch.object(hand_environment, 'build_environment', return_value='env') as build:
                self.assertEqual(runtime.native_environment(spec, 0), 'env')
            self.assertIs(build.call_args.kwargs['session_factory'], expected)
            self.assertEqual(build.call_args.kwargs['song'], settings['song'])
            self.assertEqual(build.call_args.kwargs['role'], role)
        invalid = copy.deepcopy(spec)
        invalid['song']['finger_control'] = default_profile()
        with patch.dict(sys.modules, {'isaacgym': SimpleNamespace()}), \
             patch.object(parallel, '_compact', parallel._compact), \
             patch.object(hand_environment, 'build_environment') as build:
            with self.assertRaisesRegex(ValueError, 'left hand'):
                runtime.native_environment(invalid, 0)
            build.assert_not_called()

    def test_dispatch_rejects_wrong_role_profile_and_explicit_override(self):
        settings = settings_document('left', device='cpu')
        with patch.object(hand_environment, 'HandSongEnvironment') as construct:
            with self.assertRaisesRegex(ValueError, 'left hand'):
                hand_environment.build_environment({}, self.root/'wrong-role',
                    bundle=BUNDLE, song=settings['song'], role='right')
            with self.assertRaisesRegex(ValueError, 'owns the environment profile'):
                hand_environment.build_environment({}, self.root/'conflict',
                    bundle=BUNDLE, song=settings['song'], role='left',
                    finger_profile=default_profile())
            broken = copy.deepcopy(settings['song'])
            broken['finger_control']['finger_rate_rad_s'] = 3.
            with self.assertRaisesRegex(ValueError, 'exact flexible'):
                hand_environment.build_environment({}, self.root/'invalid',
                    bundle=BUNDLE, song=broken, role='left')
            construct.assert_not_called()

    def test_recorded_left_contract_full_limits_and_right_contract_unchanged(self):
        env, sessions = self.environment()
        observation, _ = env.reset()
        codec = env.control.contract
        fingers = [codec.names.index(name) for name in LEFT_HAND_NAMES]
        self.assertEqual(observation['state'].shape, (512,))
        self.assertEqual(env.contract['action']['target_contract']['finger_control']['profile'],
                         default_profile())
        np.testing.assert_array_equal(codec.action_lower[12:33], codec.lower[fingers])
        np.testing.assert_array_equal(codec.action_upper[12:33], codec.upper[fingers])
        np.testing.assert_array_equal(codec.rates[fingers], 4.)
        np.testing.assert_array_equal(codec.alpha[12:33], .45)
        np.testing.assert_array_equal(codec.alpha[:12], .2)
        np.testing.assert_array_equal(codec.alpha[33:], .2)
        for sign in (-1., 0., 1.):
            action = np.r_[np.full(33, sign), np.zeros(6)]
            requested, final = codec.targets(action, codec.reset_targets())
            expected = codec.lower if sign < 0 else codec.upper if sign > 0 else codec.q_ref
            np.testing.assert_array_equal(requested[fingers], expected[fingers])
            np.testing.assert_array_equal(final[codec.held_indices], codec.q_ref[codec.held_indices])
            right = [codec.names.index(name) for name in codec.active_names[33:]]
            np.testing.assert_array_equal(final[right], codec.q_ref[right])
        self.assertEqual(sessions[0].scene.steps, 0)
        right, _ = self.environment(role='right')
        old_right, _ = self.environment(role='right', song=copy.deepcopy(SONG))
        right_obs, _ = right.reset()
        old_obs, _ = old_right.reset()
        self.assertEqual(right.contract, old_right.contract)
        self.assertEqual(right_obs['state'].shape, (500,))
        self.assertNotIn('finger_control', right.contract['action']['target_contract'])
        for key in right_obs:
            np.testing.assert_array_equal(right_obs[key], old_obs[key])

    def test_same_512_old_control_checkpoint_rejected_before_state_mutation(self):
        song = settings_document('left', device='cpu')['song']
        legacy_song = copy.deepcopy(song)
        legacy_song.pop('finger_control')
        legacy, _ = self.environment(song=legacy_song)
        current, _ = self.environment(song=song)
        legacy_obs, _ = legacy.reset()
        current_obs, _ = current.reset()
        self.assertEqual(legacy_obs['state'].shape, current_obs['state'].shape)
        old_trainer, _ = self.trainer(legacy)
        path = self.root/'old_same_512.pt'
        old_trainer.save(path)
        trainer, coordinator = self.trainer(current)
        data, _ = RolloutCollector(trainer.policy, current).collect(4)
        trainer.update(data)
        before = (copy.deepcopy(trainer.policy.state_dict()),
                  copy.deepcopy(trainer.actor_optimizer.state_dict()),
                  copy.deepcopy(trainer.value_optimizer.state_dict()),
                  trainer.cost_weight, trainer.updates,
                  coordinator.state.state_vector().copy())
        rng = (torch.get_rng_state().clone(), np.random.get_state(), random.getstate())
        with self.assertRaisesRegex(ValueError, 'input/control/config mismatch'):
            trainer.load(path)
        assert_tree(self, trainer.policy.state_dict(), before[0])
        assert_tree(self, trainer.actor_optimizer.state_dict(), before[1])
        assert_tree(self, trainer.value_optimizer.state_dict(), before[2])
        self.assertEqual((trainer.cost_weight, trainer.updates), before[3:5])
        np.testing.assert_array_equal(coordinator.state.state_vector(), before[5])
        self.assert_rng_equal(rng)

    def test_same_profile_ppo_resume_preserves_optimizer_rng_and_curriculum(self):
        torch.manual_seed(29)
        env, _ = self.environment()
        env.reset()
        trainer, coordinator = self.trainer(env)
        data, _ = RolloutCollector(trainer.policy, env).collect(4)
        trainer.update(data)
        # Synthetic completed metrics exercise persistence, not native success.
        episode = dict(valid=True, reason='timeline_complete', left_curriculum=dict(
            full_safe=True, reach_fraction=.9, contact_fraction=.8))
        coordinator.advance([episode]*11, None)
        coordinator.advance([episode]*2, None)
        path = self.root/'current_profile.pt'
        trainer.save(path)
        expected_draws = (torch.rand(3), np.random.rand(), random.random())
        expected_metrics = trainer.update(data)

        restored, restored_coordinator = self.trainer(env)
        restored.load(path)
        actual_draws = (torch.rand(3), np.random.rand(), random.random())
        self.assertTrue(torch.equal(expected_draws[0], actual_draws[0]))
        self.assertEqual(expected_draws[1:], actual_draws[1:])
        restored_coordinator.restore()
        np.testing.assert_array_equal(restored_coordinator.state.state_vector(),
                                      coordinator.state.state_vector())
        self.assertEqual(restored_coordinator.pool.progress, [coordinator.state.progress])
        self.assertEqual(restored.update(data), expected_metrics)
        assert_tree(self, trainer.policy.state_dict(), restored.policy.state_dict())
        assert_tree(self, trainer.actor_optimizer.state_dict(), restored.actor_optimizer.state_dict())
        assert_tree(self, trainer.value_optimizer.state_dict(), restored.value_optimizer.state_dict())
        self.assertEqual((trainer.updates, trainer.cost_weight),
                         (restored.updates, restored.cost_weight))
        for episodes in ([], [episode]*4):
            self.assertEqual(coordinator.advance(episodes, None),
                             restored_coordinator.advance(episodes, None))


if __name__ == '__main__':
    unittest.main()
