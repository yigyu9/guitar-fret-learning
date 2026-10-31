"""미디어 실행기의 CPU 전용 예산·완료·경로 안전 문턱 검사. GPU/child 실행 없음."""
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

import make_remaining_media as media


class MediaPreparationTests(unittest.TestCase):
    def test_overall_budget_not_training_deadline(self):
        budget = dict(training_deadline_utc='2026-10-31T00:00:00+00:00',
                      deadline_utc='2026-10-31T02:00:00+00:00')
        self.assertEqual(media.remaining(budget, datetime(2026,10,31,1,tzinfo=timezone.utc)),3600)
        self.assertLessEqual(media.remaining(budget, datetime(2026,10,31,3,tzinfo=timezone.utc)),0)

    def test_existing_partial_output_is_preserved_and_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            existing = Path(folder)/'partial'
            existing.write_text('keep')
            with self.assertRaises(FileExistsError):
                media.exclusive([existing])
            self.assertEqual(existing.read_text(),'keep')

    def test_incomplete_export_inner_native_report_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder);(out/'J').mkdir()
            (out/'report.json').write_text(json.dumps(dict(completed=True)))
            (out/'J/report.json').write_text(json.dumps(dict(completed=False)))
            with self.assertRaises(ValueError):
                media.validate_job(dict(out=str(out),kind='export_B0'),'unused')
        with self.assertRaises(ValueError):
            media.completed(dict(completed=False))

    def test_plan_has_twelve_sequential_jobs_and_skips_index(self):
        jobs=media.plan({finger:dict(checkpoint='/tmp/'+finger+'.pt') for finger in media.FINGERS})
        self.assertEqual(len(jobs),12)
        self.assertEqual([job['kind'] for job in jobs[:4]],
            ['export_B0','evaluate_B0','export_free','render_free'])
        self.assertEqual({job['finger'] for job in jobs},{'middle','ring','pinky'})
        self.assertIn('--initial-distribution',jobs[2]['command'])
        self.assertIn('v9',jobs[2]['command'])
        self.assertEqual(len(jobs[3]['public_videos']),2)


if __name__=='__main__':
    unittest.main()
