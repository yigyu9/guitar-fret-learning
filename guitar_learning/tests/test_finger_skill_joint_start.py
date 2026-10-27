import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from guitar_learning.training.start import settings_document
from guitar_learning.tool.training.train_legacy import settings_document as legacy_settings
from guitar_learning.training.finger_skill_runner import RESUME_SCHEMA, RESUME_SCHEMA_V2, resume_schema


class JointFingerSkillStartTests(unittest.TestCase):
    def test_default_is_identical_to_explicit_current_family(self):
        for options in ({}, dict(updates=7, num_envs=1024, horizon=32, size='large')):
            with self.subTest(options=options):
                self.assertEqual(settings_document(**options),
                    settings_document('left', learning_family='finger-skill', **options))
        self.assertEqual(settings_document()['finger_skill']['schema'],
                         'guitar_learning.finger_skill.v2')

    def test_main_dispatches_directly_to_current_runner(self):
        from guitar_learning.training import start, finger_skill_runner
        settings = settings_document()
        args = SimpleNamespace(out=Path('/tmp/unused-finger-default'), resume=None)
        with patch.dict('sys.modules', {'isaacgym': SimpleNamespace()}), \
                patch.object(finger_skill_runner, 'run', return_value='current') as run:
            self.assertEqual(start.run(settings, args), 'current')
            run.assert_called_once_with(settings, args)
        for old in (legacy_settings('left'),
                    legacy_settings('left', learning_family='finger-skill-v24')):
            with self.assertRaisesRegex(ValueError, 'train_legacy'):
                start.run(old, args)

    def test_default_cli_sets_current_family_without_native_help_imports(self):
        from guitar_learning.training import start
        expected = settings_document()
        with patch.dict('sys.modules', {'isaacgym': SimpleNamespace()}), \
                patch.object(sys, 'argv', ['train', '--out', '/tmp/unused-finger-default']), \
                patch.object(start, 'run', return_value='current') as run:
            self.assertEqual(start.main(), 'current')
            self.assertEqual(run.call_args[0][0], expected)
        script = '''
import importlib.abc, runpy, sys
class Guard(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in ('isaacgym', 'numpy', 'torch'):
            raise AssertionError('help imported '+fullname)
sys.meta_path.insert(0, Guard())
sys.argv = ['train', '--help']
runpy.run_module('guitar_learning.train', run_name='__main__')
'''
        root = Path(__file__).resolve().parents[2]
        result = subprocess.run([sys.executable, '-B', '-c', script], cwd='/tmp',
            env=dict(os.environ, PYTHONPATH=str(root)), capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('--learning-family {finger-skill}', result.stdout)
        self.assertIn('--hand {left}', result.stdout)
        self.assertNotIn('--skill-phase', result.stdout)

    def test_legacy_families_require_explicit_legacy_entry(self):
        for family in ('song', 'finger-skill-v24'):
            with self.subTest(family=family), self.assertRaisesRegex(ValueError, 'train_legacy'):
                settings_document(learning_family=family)
        with self.assertRaisesRegex(ValueError, 'guitar_learning.train'):
            legacy_settings('left', learning_family='finger-skill')

    def test_public_family_is_joint_from_first_tick_with_fixed_exposure_and_objective(self):
        settings = settings_document('left', learning_family='finger-skill', updates=7,
                                     num_envs=8, horizon=32, size='small')
        self.assertEqual(settings['finger_skill'], dict(schema='guitar_learning.finger_skill.v2',
            phase='J', exploration='independent', hold_ticks=1, scope='scheduled',
            planned_transitions=1792, full_song_after=448))
        self.assertEqual(settings['song_training']['observation_dimension'], 561)
        self.assertEqual(settings['ppo']['advantage_normalization'], 'joint')
        self.assertEqual(settings['ppo']['cost_weight'], 1.)
        self.assertEqual(settings['ppo']['lambda_lr'], 0.)
        self.assertIsNone(settings['ppo']['episode_cost_budget'])
        self.assertEqual(resume_schema(settings), RESUME_SCHEMA_V2)
        self.assertEqual(settings['song']['finger_action_mode'], 'incremental')

    def test_old_family_and_cpu_right_are_preserved(self):
        old = legacy_settings('left', learning_family='finger-skill-v24', updates=1, num_envs=1)
        self.assertEqual(old['finger_skill']['schema'], 'guitar_learning.finger_skill.v1')
        self.assertEqual(old['finger_skill']['phase'], 'auto')
        self.assertEqual(old['ppo']['advantage_normalization'], 'separate')
        self.assertEqual(old['song_training']['observation_dimension'], 557)
        self.assertEqual(resume_schema(old), RESUME_SCHEMA)
        cpu = legacy_settings('left', device='cpu', physics='cpu', updates=1, num_envs=1)
        right = legacy_settings('right', device='cpu', physics='cpu', updates=1, num_envs=1)
        self.assertNotIn('finger_skill', cpu)
        self.assertNotIn('finger_skill', right)
        self.assertEqual(cpu['song_training']['observation_dimension'], 512)
        self.assertEqual(right['song_training']['observation_dimension'], 500)

    def test_new_family_rejects_old_stages_and_other_experiments(self):
        options = [dict(skill_phase='R'), dict(skill_phase='F'), dict(skill_exploration='correlated'),
            dict(skill_hold_ticks=3), dict(skill_scope='full_song'), dict(finger_action_mode='position'),
            dict(finger_standby_rate=.04), dict(finger_shape=True), dict(device='cpu', physics='cpu')]
        for option in options:
            with self.subTest(option=option), self.assertRaises(ValueError):
                settings_document('left', learning_family='finger-skill', updates=1, num_envs=1, **option)
        with self.assertRaises(ValueError):
            settings_document('right', learning_family='finger-skill', updates=1, num_envs=1)


if __name__ == '__main__':
    unittest.main()
