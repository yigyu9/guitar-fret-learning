"""기본 J557 설정과 제거된 단계·구형 CLI의 거부를 검사한다."""
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from guitar_learning.training.launch import settings_document, build_settings
from guitar_learning.tool.training.train_legacy import settings_document as legacy_settings
from guitar_learning.training.finger_skill_runner import RESUME_SCHEMA, resume_schema


class JointFingerSkillStartTests(unittest.TestCase):
    def test_default_and_explicit_joint_settings_are_identical(self):
        for options in ({}, dict(updates=7, num_envs=1024, horizon=32, size='large')):
            self.assertEqual(settings_document(**options),
                             settings_document('left', learning_family='finger-skill', **options))
        settings = settings_document(updates=7, num_envs=8, horizon=32)
        self.assertEqual(settings['finger_skill'], dict(schema='guitar_learning.finger_skill.v3',
            phase='J', exploration='independent', hold_ticks=1, scope='scheduled',
            planned_transitions=1792, full_song_after=448))
        self.assertEqual(settings['song_training']['observation_dimension'], 557)
        self.assertEqual(settings['ppo']['advantage_normalization'], 'joint')
        self.assertEqual(settings['ppo']['cost_weight'], 1.)
        self.assertEqual(resume_schema(settings), RESUME_SCHEMA)

    def test_main_dispatches_to_joint_runner(self):
        from guitar_learning.training import launch, finger_skill_runner
        args = SimpleNamespace(out=Path('/tmp/unused-joint'), resume=None)
        value = settings_document()
        with patch.dict('sys.modules', {'isaacgym': SimpleNamespace()}), \
                patch.object(finger_skill_runner, 'run', return_value='joint') as run:
            self.assertEqual(launch.run(value, args), 'joint')
            run.assert_called_once_with(value, args)
        with self.assertRaisesRegex(ValueError, 'train_legacy'):
            launch.run(legacy_settings('left'), args)

    def test_help_imports_no_native_or_tensor_libraries_and_has_no_stage_options(self):
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
        self.assertNotIn('--skill-phase', result.stdout)
        self.assertNotIn('finger-skill-v24', result.stdout)

    def test_stage_options_and_legacy_family_are_removed(self):
        for option in (dict(skill_phase='R'), dict(skill_phase='F'), dict(skill_hold_ticks=3),
                       dict(skill_exploration='correlated'), dict(skill_scope='phrases')):
            with self.subTest(option=option), self.assertRaises(TypeError): settings_document(**option)
        with self.assertRaises(ValueError): build_settings('left', learning_family='finger-skill-v24')
        with self.assertRaises(ValueError): legacy_settings('left', learning_family='finger-skill-v24')
        with self.assertRaises(ValueError): settings_document('right')
        with self.assertRaises(ValueError): settings_document(device='cpu', physics='cpu')
        for schema in ('guitar_learning.finger_skill.v1', 'guitar_learning.finger_skill.v2'):
            with self.assertRaises(ValueError): resume_schema(dict(finger_skill=dict(schema=schema)))

    def test_legacy_song_cpu_and_right_contracts_are_separate(self):
        for hand, dimension in (('left', 512), ('right', 500)):
            value = legacy_settings(hand, device='cpu', physics='cpu', updates=1, num_envs=1)
            self.assertNotIn('finger_skill', value)
            self.assertEqual(value['song_training']['observation_dimension'], dimension)


if __name__ == '__main__':
    unittest.main()
