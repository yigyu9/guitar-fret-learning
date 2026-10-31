"""학습 없이 순차 실행기의 시간 집계·고정 순위·증거 보존을 검사한다."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import run_study as study


def row(condition='E1', success=32, failures=0):
    return dict(condition=condition, free_v9=dict(physical_failure_count=failures,
        wrist_failure_count=0, success_count=success, mean_clean_s=2.4,
        mean_wrong_s=0., mean_early_candidate_s=0., mean_unready_slow_wrist_s=.5,
        env0_trace=dict(max_actual_initial_extension_deg=[2., 3.])))


class StudyTests(unittest.TestCase):
    def test_selection_prioritizes_safety_then_achievement_then_fixed_ties(self):
        values = [row('E4'), row('E3', success=31), row('E2', failures=1), row('E1')]
        self.assertEqual([x['condition'] for x in sorted(values, key=study.ranking)], ['E1', 'E4', 'E3', 'E2'])

    def test_source_change_stops_and_keeps_original_data(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(study, 'ROOT', Path(tmp)):
            path = Path(tmp)/'source.py'; path.write_text('old')
            seal = {'source.py': study.digest(path)}
            study.verify_sources(seal)
            path.write_text('new')
            with self.assertRaises(RuntimeError):
                study.verify_sources(seal)
            self.assertEqual(path.read_text(), 'new')

    def test_partial_metrics_row_does_not_count_uncommitted_update(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp); (out/'J').mkdir()
            (out/'J/learning_metrics.jsonl').write_text(json.dumps(dict(collection_s=4, update_s=1))+'\n{"collection_s":')
            self.assertEqual(study.live_updates(out), (1, 5.))

    def test_progress_does_not_count_current_or_failed_block_as_complete(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(study, 'HERE', Path(tmp)), \
                patch.object(study, 'live_updates', return_value=(20, 5.)):
            state = dict(status='running', jobs={
                'done': dict(status='complete', operation='train', updates=100),
                'running': dict(status='running', operation='train', updates=100),
                'eval': dict(status='complete', operation='evaluate', updates=0)},
                current_job=dict(operation='train', label='running', out='example'))
            study.progress(state)
            self.assertEqual(state['completed_train_updates'], 100)
            self.assertEqual(state['current_block_completed_updates'], 20)
            self.assertEqual(state['completed_evaluations'], 1)
            self.assertTrue((Path(tmp)/'진행상황.md').is_file())

    def test_cached_completed_job_rejects_changed_evidence(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(study, 'ROOT', Path(tmp)):
            root = Path(tmp); report = root/'report.json'; report.write_text('{"completed":true}')
            evidence = root/'final.pt'; evidence.write_bytes(b'model')
            state = dict(source_seal={}, jobs={'saved': dict(status='complete', report=str(report),
                report_sha256=study.digest(report), evidence_sha256={str(evidence): study.digest(evidence)})})
            self.assertTrue(study.run_job(state, 'saved', 'train', [], root/'unused')['completed'])
            evidence.write_bytes(b'changed')
            with self.assertRaises(RuntimeError):
                study.run_job(state, 'saved', 'train', [], root/'unused')


if __name__ == '__main__':
    unittest.main()
