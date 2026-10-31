"""이전 실험의 중복 성공·미관측 음 누락이 재발하지 않는지 검사한다."""
import gzip
import json
from pathlib import Path
import tempfile
import unittest
from analyze_results import analyze_evaluation


class AnalysisTests(unittest.TestCase):
    def fixture(self,path,*,dual=False,raw_dual=False,missing_sample=False):
        schedule=[dict(target_id=str(i),fret=fret,finger=2,string_index=2,onset_s=t,end_s=t+1.5)
            for i,fret,t in ((0,6,3.),(1,7,5.))]
        report=dict(completed=True,lifecycle_verified=True,first_episode_per_env_per_batch=True,
            failed_episodes_in_denominator=True,episodes=32,settings=dict(transition=dict(schedule=schedule)))
        (path/'report.json').write_text(json.dumps(report))
        (path/'action_mode.json').write_text(json.dumps(dict(action_mode='mean')))
        (path/'episode_metadata.json').write_text(json.dumps(dict(fields=[])))
        episode=dict(left_note_ledger=dict(target_ids=['0','1'],values=dict(left=[False,False],clean=[0.,0.],wrong=[0.,0.],missing=[0.,0.])),
            transition_diagnostics=dict(target_ids=['0','1'],first_contact_s=[None,None],first_achievement_s=[None,None]),
            termination=dict(physical_failure=True,wrist_failure=False),valid=True,task_time_s=4/240,
            reward=0.,reward_components=dict(song_left_approach=0.),finger_control_diagnostics=dict(episode_id=1))
        with (path/'episodes.jsonl').open('w')as stream:
            for i in range(32):stream.write(json.dumps(dict(episode=dict(episode,env_id=i)))+'\n')
        with gzip.open(path/'finger_control_trace.jsonl.gz','wt')as stream:
            for step in range(1,5):
                if missing_sample and step==2:continue
                extra=dict(all_env_episode_time_s=[step/240]*32,all_env_episode_ids=[1]*32,
                    all_env_candidate=[[True,True]if dual else [False,False]for _ in range(32)],
                    all_env_wrong=[[False,False]for _ in range(32)],
                    all_env_raw_candidate=[[raw_dual,raw_dual]for _ in range(32)],
                    all_env_current_next_indices=[[0,1]for _ in range(32)])
                stream.write(json.dumps(dict(natural_preparation=dict(transition=extra)))+'\n')

    def test_failed_before_onsets_keeps_all_denominators(self):
        with tempfile.TemporaryDirectory()as tmp:
            p=Path(tmp);self.fixture(p);m=analyze_evaluation(p)
            self.assertEqual(m['episodes'],32);self.assertEqual(m['note_denominator'],64)
            self.assertEqual(m['physical_failure_count'],32);self.assertEqual(m['note_success_count'],0)
            self.assertEqual(m['notes'][1]['first_contact_s'],[None]*32)

    def test_effective_dual_candidate_is_rejected(self):
        with tempfile.TemporaryDirectory()as tmp:
            p=Path(tmp);self.fixture(p,dual=True)
            with self.assertRaisesRegex(ValueError,'동시 유효'):analyze_evaluation(p)

    def test_raw_dual_candidate_is_diagnostic_not_success(self):
        with tempfile.TemporaryDirectory()as tmp:
            p=Path(tmp);self.fixture(p,raw_dual=True);m=analyze_evaluation(p)
            self.assertEqual(m['raw_dual_sample_count'],128);self.assertEqual(m['note_success_count'],0)

    def test_missing_physics_sample_is_rejected(self):
        with tempfile.TemporaryDirectory()as tmp:
            p=Path(tmp);self.fixture(p,missing_sample=True)
            with self.assertRaisesRegex(ValueError,'240Hz'):analyze_evaluation(p)


if __name__=='__main__':unittest.main()
