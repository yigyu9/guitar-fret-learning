"""후속 실험의 의존 작업 실패 차단과 선별 경계를 검사한다."""
import json
from pathlib import Path
import tempfile
import unittest
from run_after_study import acceptable, dependency_ready, training_summary


class RunnerTests(unittest.TestCase):
    def test_waits_for_both_jobs(self):
        done = dict(completed=True, phase='complete')
        self.assertFalse(dependency_ready(dict(completed=False, phase='train'), dict(phase='complete')))
        self.assertFalse(dependency_ready(done, dict(phase='waiting_for_study')))
        self.assertTrue(dependency_ready(done, dict(phase='complete')))

    def test_failed_dependencies_block_gpu_work(self):
        for study, efficiency in ((dict(phase='failed'),dict(phase='complete')),
                                  (dict(completed=True,phase='complete'),dict(phase='failed'))):
            with self.assertRaises(RuntimeError):
                dependency_ready(study,efficiency)

    def test_selection_requires_success_and_safety(self):
        baseline = dict(mean_achieved_notes=4.,physical_failures=0,wrist_failures=0)
        self.assertTrue(acceptable(dict(baseline,mean_achieved_notes=4.25,physical_failures=2),baseline))
        self.assertFalse(acceptable(dict(baseline,mean_achieved_notes=4.24),baseline))
        self.assertFalse(acceptable(dict(baseline,mean_achieved_notes=4.25,physical_failures=3),baseline))
        self.assertFalse(acceptable(dict(baseline,mean_achieved_notes=float('nan')),baseline))

    def test_summary_uses_nested_episode_and_selected_exposure(self):
        episode = dict(termination=dict(no_contact_failure=True,physical_failure=False,wrist_failure=False),
            left_note_ledger=dict(focus_mask=[True,True,False],values=dict(exposure_time=[1.,0.,2.])))
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'episodes.jsonl'
            p.write_text(json.dumps(dict(episode=episode))+'\n')
            summary=training_summary(p)
        self.assertEqual(summary['termination_counts']['no_contact'],1)
        self.assertEqual(summary['mean_selected_targets'],2)
        self.assertEqual(summary['mean_exposed_targets'],1)


if __name__ == '__main__':
    unittest.main()
