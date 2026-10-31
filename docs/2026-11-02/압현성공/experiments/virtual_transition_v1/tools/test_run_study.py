"""GPU 없이 큐의 봉인·의존성·진행률 계약을 검증한다."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import run_study as queue


class QueueTests(unittest.TestCase):
    def test_structured_nonfinite_failure_stops_entire_study(self):
        for report_path, failure in (
            ('report.json',dict(type='FloatingPointError',message='bad state')),
            ('J/report.json',dict(type='ValueError',message='finite explicit natural_press state required')),
            ('report.json',dict(type='RuntimeError',message='nativefinite required')),
            ('J/report.json',dict(type='ValueError',message='native q must be finite'))):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp); path=root/report_path; path.parent.mkdir(exist_ok=True)
                path.write_text(json.dumps(dict(failure=failure)))
                self.assertIsNotNone(queue.nonfinite_failure(root,'no traceback'))
        self.assertTrue(issubclass(queue.FatalStudyError,RuntimeError))

    def test_nonfinite_log_fallback_only_without_structured_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            self.assertIsNotNone(queue.nonfinite_failure(root,'ValueError: finite explicit natural_press state required'))
            self.assertIsNotNone(queue.nonfinite_failure(root,'FloatingPointError: state broken'))
            (root/'report.json').write_text(json.dumps(dict(completed=True,failure=None)))
            self.assertIsNone(queue.nonfinite_failure(root,'contract nonfinite diagnostics'))
            (root/'report.json').write_text(json.dumps(dict(failure=dict(type='KLGuardError',message='KL too large'))))
            self.assertIsNone(queue.nonfinite_failure(root,'KLGuardError: KL too large'))

    def test_changed_source_fatal(self):
        with tempfile.TemporaryDirectory(dir=queue.ROOT) as tmp:
            path=Path(tmp)/'source.py'; path.write_text('before')
            seal={str(path.relative_to(queue.ROOT)):queue.digest(path)}
            queue.verify_sources(seal); path.write_text('after')
            with self.assertRaises(queue.FatalStudyError):queue.verify_sources(seal)

    def test_missing_checkpoint_skips_extension(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); state=dict(status='running',jobs={},results={})
            queue.block(state,root,'E4',7,200)
            self.assertEqual(state['jobs']['seed7_E4_u200_train']['status'],'skipped')
            self.assertEqual(json.loads((root/'progress.json').read_text())['completed_train_updates'],0)

    def test_resume_checks_additional_and_cumulative_transitions_separately(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); previous=root/'blocks/seed7_E0_u100/train/J/final.pt'
            previous.parent.mkdir(parents=True); previous.touch()
            current=root/'blocks/seed7_E0_u200/train/J'; current.mkdir(parents=True)
            (current/'report.json').write_text(json.dumps(dict(optimizer_updates=200,transitions=204800,curriculum=dict(committed_transitions=409600))))
            state=dict(status='running',jobs={'seed7_E0_u100_train':dict(status='complete')},results={})
            with patch.object(queue,'run_job',side_effect=[{},None]) as job:
                queue.block(state,root,'E0',7,200)
                self.assertEqual(job.call_count,2)
            phase=json.loads((current/'report.json').read_text()); phase['curriculum']['committed_transitions']=204800
            (current/'report.json').write_text(json.dumps(phase))
            with patch.object(queue,'run_job',return_value={}):
                with self.assertRaises(queue.FatalStudyError): queue.block(state,root,'E0',7,200)

    def test_live_metrics_counts_partial_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/'J').mkdir()
            (root/'J/learning_metrics.jsonl').write_text('{"collection_s":2,"update_s":3}\n{"collection_s":')
            self.assertEqual(queue.live_updates(root),(1,5.))

    def test_evaluation_failure_does_not_hide_existing_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); previous=root/'blocks/seed7_E4_u100/train/J/final.pt'; previous.parent.mkdir(parents=True); previous.touch()
            state=dict(status='running',jobs={'seed7_E4_u100_train':dict(status='complete')},results={})
            with patch.object(queue,'run_job',return_value=None) as job:
                queue.block(state,root,'E4',7,200)
                self.assertEqual(job.call_count,1)
                self.assertIn(str(previous),map(str,job.call_args.args[4]))


if __name__=='__main__': unittest.main()
