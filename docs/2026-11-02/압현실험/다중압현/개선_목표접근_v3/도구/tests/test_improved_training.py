"""CPU invariants for the fresh E4 condition and strict checkpoint lineage."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import prepare_improved_training as prepare
import run_improved_job as job
from improved_environment import ImprovedPairEnvironment
from pair_environment import PairEnvironment
from guitar_learning.portability import portable, settings_digest
from guitar_learning.tests.test_gpu_environment import fixture


class ImprovedTrainingTests(unittest.TestCase):
    def setUp(self):
        import torch
        torch.set_num_threads(1)

    def make(self, cls):
        metadata, snapshot = fixture(2)
        settings = prepare.improved_settings()
        env = cls(metadata, bundle=settings['song_training']['bundle'], song=settings['song'],
            skill=settings['finger_skill'], device='cpu')
        env.set_evaluation(True, full_song=True)
        env.reset(range(2), snapshot)
        return env

    def test_same_budget_defaults_and_only_explicit_condition_changes_settings(self):
        improved = prepare.improved_settings()
        case = next(c for c in prepare.load_cases() if c['case_id'] == 'index_middle_same')
        baseline = prepare.make_settings(case, improved['song_training']['bundle'],
            updates=100, num_envs=64, horizon=32, size='medium', seed=7)
        clone = copy.deepcopy(improved)
        self.assertEqual(clone['experiment'].pop('improvement'), prepare.CONDITION)
        self.assertEqual(clone, baseline)
        self.assertEqual(improved['num_envs']*improved['horizon']*improved['updates'], 204800)
        self.assertIsNone(prepare.CONDITION['teacher'])

    def test_e4_early_signals_change_with_same_pd_physics_safety_and_dimensions(self):
        baseline, improved = self.make(PairEnvironment), self.make(ImprovedPairEnvironment)
        self.assertFalse(bool(baseline._finger_targets(baseline._score_time())['valid'].any()))
        self.assertTrue(bool(improved._finger_targets(improved._score_time())['valid'][0, :2, 0].all()))
        base_posture = baseline._finger_preparation(baseline._score_time())
        new_posture = improved._finger_preparation(improved._score_time())
        self.assertEqual(base_posture['gate'][0, :2].tolist(), [1., 1.])
        self.assertEqual(new_posture['standby_reward_gate'][0, :2].tolist(), [0., 0.])
        self.assertEqual(new_posture['standby_reward_gate'][0, 2:].tolist(), [1., 1.])
        self.assertEqual(float(baseline._surface_potential()[0]), 0.)
        self.assertGreater(float(improved._surface_potential()[0]), 0.)
        for name in ('action', 'termination', 'native_backend'):
            self.assertEqual(baseline.contract[name], improved.contract[name])
        self.assertEqual(baseline.contract['observation']['dimension'], 557)
        self.assertEqual(improved.contract['observation']['dimension'], 557)
        for name in ('begin_control', 'control', 'substep', '_safety', '_contacts'):
            if hasattr(PairEnvironment, name):
                self.assertIs(getattr(ImprovedPairEnvironment, name), getattr(PairEnvironment, name))
        self.assertTrue(bool(improved.focus_mask.all()))

    def lineage(self):
        settings = prepare.improved_settings()
        train = dict(job_id='B2_index_middle_same_train', out=str(job.STUDY/'로그/test/train'),
            settings_sha256=settings_digest(settings))
        evaluate = dict(checkpoint=str(Path(train['out'])/'J/final.pt'))
        report = dict(job_id=train['job_id'], case_id='index_middle_same', condition=job.CONDITION,
            completed=True, checkpoint=evaluate['checkpoint'], checkpoint_sha256='actual-sha')
        payload = dict(metadata=dict(settings=portable(settings)), identity=dict(architecture=dict(
            contract=dict(reward=dict(natural_preparation=job.CONDITION['natural_preparation'])))))
        return payload, evaluate, train, report

    def test_own_e4_checkpoint_is_required_and_b0_or_wrong_sha_is_rejected(self):
        payload, evaluate, train, report = self.lineage()
        job.verify_eval_identity(payload, evaluate, train, report, 'actual-sha')
        for change in ('parent_sha', 'settings', 'condition', 'architecture', 'path'):
            p, e, t, r = copy.deepcopy((payload, evaluate, train, report))
            if change == 'parent_sha':
                r['checkpoint_sha256'] = 'other'
            elif change == 'settings':
                p['metadata']['settings']['seed'] = 8
            elif change == 'condition':
                p['metadata']['settings']['experiment']['improvement']['condition'] = 'B0'
            elif change == 'architecture':
                p['identity']['architecture']['contract']['reward']['natural_preparation']['condition'] = 'E0'
            else:
                e['checkpoint'] = str(job.BASE/'로그/parallel_v1/pilot_env2/J/final.pt')
            with self.subTest(change=change), self.assertRaises(ValueError):
                job.verify_eval_identity(p, e, t, r, 'actual-sha')

    def test_waits_for_all_original_baseline_jobs_without_querying_gpu(self):
        with patch.object(job, 'verify_baseline', return_value=dict(jobs=[])), \
                patch.object(job.Path, 'read_text', return_value='{"completed":false,"status":"running"}'), \
                patch.object(job, 'single_readiness') as query:
            ready, reason, _ = job.readiness()
        self.assertFalse(ready)
        self.assertEqual(reason, 'waiting_for_original_six_case_queue')
        query.assert_not_called()


if __name__ == '__main__':
    unittest.main()
