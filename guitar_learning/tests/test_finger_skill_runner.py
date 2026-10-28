"""J 전용 실행·노출 복원·입력 검증과 단계 전환 제거를 검사한다."""
import copy
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

import torch

from guitar_learning.training import finger_skill_runner as runner
from guitar_learning.training.launch import settings_document
from guitar_learning.training.ppo import DecisionPPOTrainer, PPOConfig
from guitar_learning.tests.test_finger_decisions import TinyDecisionPolicy


def settings():
    return settings_document(updates=4, num_envs=2, horizon=3, size='small')


class JointRunnerTests(unittest.TestCase):
    def _run(self, active, out, train, resume=None):
        with patch.dict('sys.modules', {'isaacgym': SimpleNamespace()}), \
                patch('torch.cuda.is_available', return_value=True), \
                patch.object(runner, '_train_phase', side_effect=train), \
                patch.object(runner, 'evaluate_checkpoint') as evaluate:
            report = runner.run(active, SimpleNamespace(out=out, resume=resume))
        evaluate.assert_not_called()
        return report

    def test_one_joint_run_without_readiness_transfer_or_extra_stages(self):
        calls = []
        def train(active, out, schedule, **options):
            calls.append((out.name, options))
            schedule.commit(active['horizon']*active['num_envs']*options['updates'])
            return dict(report=dict(stopped='updates_complete', exposure_transitions=dict(phrases=24, full_song=0)),
                        checkpoint=str(out/'final.pt'))
        with tempfile.TemporaryDirectory() as tmp:
            report = self._run(settings(), Path(tmp)/'run', train)
        self.assertEqual(calls, [('J', dict(resume=None, updates=4))])
        self.assertTrue(report['completed'])
        self.assertEqual(report['training_transitions'], 24)
        self.assertEqual(report['final_phase'], 'J')
        self.assertNotIn('evaluations', report)
        self.assertFalse(hasattr(runner, 'FingerSkillCurriculum'))
        self.assertFalse(hasattr(runner, '_transfer'))
        self.assertFalse(hasattr(runner, 'phase_budgets'))

    def test_resume_preserves_original_quarter_and_allows_additional_updates(self):
        active = settings()
        schedule = runner.ExposureSchedule(24)
        schedule.commit(24)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkpoint = root/'prior.pt'
            torch.save(dict(metadata=dict(schema=runner.RESUME_SCHEMA, settings=active,
                input_pins={}, curriculum=schedule.state_dict())), checkpoint)
            active = copy.deepcopy(active)
            active['updates'] = 1
            active['finger_skill'].update(planned_transitions=6, full_song_after=1)
            def train(value, out, restored, **options):
                self.assertEqual(restored.config, dict(planned_transitions=24, full_song_after=6))
                self.assertEqual(value['finger_skill']['planned_transitions'], 24)
                self.assertEqual(options, dict(resume=checkpoint, updates=1))
                restored.commit(6)
                return dict(report=dict(stopped='updates_complete', exposure_transitions={}),
                            checkpoint=str(out/'final.pt'))
            result = self._run(active, root/'resume', train, checkpoint)
        self.assertEqual(result['training_transitions'], 30)
        self.assertTrue(result['manual_budget_extension'])

    def test_restore_sampler_and_exposure_before_fresh_prepared_reset(self):
        trainer = DecisionPPOTrainer(TinyDecisionPolicy(), PPOConfig(epochs=1))
        active, schedule, calls = settings(), runner.ExposureSchedule(24), []
        schedule.commit(7)
        sampler = SimpleNamespace(state_dict=lambda: dict(index=3),
            load_state_dict=lambda value: calls.append(('sampler', value)))
        pool = SimpleNamespace(environment=SimpleNamespace(sampler=sampler), observation=None,
            set_training_progress=lambda value: calls.append(('progress', value)))
        def reset():
            calls.append(('reset', None))
            return dict(state='prepared'), []
        pool.reset = reset
        with tempfile.TemporaryDirectory() as tmp:
            checkpoint = Path(tmp)/'joint.pt'
            trainer.save(checkpoint, runner.checkpoint_metadata(active, schedule, pool))
            restored = runner.ExposureSchedule(24)
            runner.restore_checkpoint(trainer, pool, restored, checkpoint)
        self.assertEqual(calls, [('sampler', dict(index=3)), ('progress', 7), ('reset', None)])
        self.assertEqual(pool.observation, dict(state='prepared'))
        self.assertEqual(restored.status()['next_reset_scope'], 'full_song')

    def test_rejects_old_checkpoint_before_training_and_keeps_gpu_requirement(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = root/'old.pt'
            torch.save(dict(metadata=dict(schema='guitar_learning.finger_skill_resume.v2')), old)
            with self.assertRaisesRegex(ValueError, 'J-only'):
                self._run(settings(), root/'new', lambda *a, **kw: self.fail('trained old checkpoint'), old)
            with patch.dict('sys.modules', {'isaacgym': SimpleNamespace()}), \
                    patch('torch.cuda.is_available', return_value=False), self.assertRaisesRegex(RuntimeError, 'CUDA'):
                runner.run(settings(), SimpleNamespace(out=root/'no_gpu', resume=None))

    def test_old_phase_or_different_objective_cannot_enter_joint_runner(self):
        for name, value in (('phase', 'R'), ('phase', 'F'), ('scope', 'full_song'),
                            ('hold_ticks', 3), ('exploration', 'correlated')):
            active = settings()
            active['finger_skill'][name] = value
            with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                runner._validate_joint_settings(active)
        active = settings()
        active['ppo']['advantage_normalization'] = 'separate'
        with self.assertRaises(ValueError): runner._validate_joint_settings(active)
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)/'source.py'
            source.write_text('changed')
            with self.assertRaisesRegex(ValueError, 'sources changed'):
                runner._validate_pins(dict(input_pins={str(source): '0'*64}))


if __name__ == '__main__':
    unittest.main()
