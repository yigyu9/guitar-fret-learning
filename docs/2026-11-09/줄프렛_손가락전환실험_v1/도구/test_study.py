"""검사 실패와 과제 실패를 구분하고 실패 환경을 평가 분모에서 제외하지 않는다."""
import json
from pathlib import Path
import tempfile
import unittest
import run_study

class SummaryTests(unittest.TestCase):
    def test_failed_episode_stays_in_denominator(self):
        good=dict(valid=True,song=dict(stage_success=True),termination=dict(physical_failure=False,wrist_failure=False),
            left_note_ledger=dict(values=dict(left=[True,True],clean=[1.5,1.5],wrong=[0.,0.],best_clean_streak=[1.5,1.5])))
        bad=dict(good,valid=False,song=dict(stage_success=False),termination=dict(physical_failure=True,wrist_failure=False))
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'episodes.jsonl';p.write_text('\n'.join(json.dumps(dict(episode=x)) for x in (good,bad)))
            result=run_study.metrics(p)
        self.assertEqual(result['episodes'],2);self.assertEqual(result['target_success'],[1,1]);self.assertEqual(result['raw_target_latches'],[2,2])
        self.assertEqual(result['all_notes_success'],1);self.assertEqual(result['full_duration_all_notes'],1)
        self.assertEqual(result['physical'],1)

    def test_empty_evaluation_is_not_success(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'episodes.jsonl';p.write_text('')
            with self.assertRaises(ValueError):run_study.metrics(p)

if __name__=='__main__':unittest.main()
