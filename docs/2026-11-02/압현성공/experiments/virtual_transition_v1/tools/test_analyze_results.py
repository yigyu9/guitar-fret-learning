"""부분 실패를 성공 집계에서 숨기지 않는지 확인한다."""
import copy
import gzip
import json
from pathlib import Path
import tempfile
import unittest
from analyze_results import analyze_evaluation


class AnalysisTests(unittest.TestCase):
    def extra(self,t):
        goals=[dict(target_id=name,onset_s=3.+2*i,end_s=4.5+2*i,fret=6 if i%2==0 else 7,string_index=2,press_candidate=False,pad_distance_m=.002,pad_height_m=.002) for i,name in enumerate(('A1','B1','A2','B2'))]
        return dict(schema='guitar_learning.virtual_transition.v1',goals=goals,arm_actual_rad=[t]*12,arm_requested_rad=[t]*12,arm_applied_rad=[t]*12,wrist_error_m=[0.]*3)

    def fixture(self, root):
        report=dict(completed=True,lifecycle_verified=True,first_episode_per_env_per_batch=True,failed_episodes_in_denominator=True,episodes=32)
        report['settings']=dict(transition=dict(schedule=[dict(target_id=t,onset_s=3.+2*i,end_s=4.5+2*i,fret=6 if i%2==0 else 7,finger=2,string_index=2) for i,t in enumerate(('A1','B1','A2','B2'))]))
        (root/'report.json').write_text(json.dumps(report)); (root/'episode_metadata.json').write_text('{"fields":[]}')
        sample=dict(env_id=0,valid=True,task_time_s=11.,finger_skill=dict(scope='full_song'),termination=dict(physical_failure=False,wrist_failure=False),
                    reward_components=dict(a=1.),reward=1.,finger_control_diagnostics=dict(episode_id=1),
                    transition_diagnostics=dict(target_ids=['A1','B1','A2','B2'],first_contact_s=[3.,5.,7.,9.],first_achievement_s=[3.5,5.5,7.5,9.5]),
                    left_note_ledger=dict(target_ids=['A1','B1','A2','B2'],values=dict(left=[True]*4,clean=[1.5]*4,wrong=[0.]*4,missing=[0.]*4)))
        rows=[]
        for env in range(32):
            row=copy.deepcopy(sample); row['env_id']=env
            if env==31:
                row['transition_diagnostics'].update(first_contact_s=[3.,None,None,None],first_achievement_s=[None]*4)
                row['task_time_s']=4.; row['termination']['physical_failure']=True
                row['left_note_ledger']['values'].update(left=[False]*4,clean=[.5,0.,0.,0.])
            rows.append(dict(episode=row))
        (root/'episodes.jsonl').write_text('\n'.join(map(json.dumps,rows)))
        with gzip.open(root/'finger_control_trace.jsonl.gz','wt') as stream:
            for i in range(2640):
                stream.write(json.dumps(dict(env_id=0,episode_id=1,episode_time_s=(i+1)/240.,natural_preparation=dict(transition=self.extra((i+1)/240.))))+'\n')
        return rows

    def test_failure_keeps_all_note_denominators(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); self.fixture(root); result=analyze_evaluation(root)
            self.assertEqual(result['full_sequence_success_count'],31)
            self.assertEqual(result['note_success_count'],124)
            self.assertEqual(result['note_denominator'],128)
            self.assertEqual(result['notes'][1]['observed_onset_count'],31)
            self.assertIsNone(result['env0_trace']['transitions'][0]['first_target_contact_s'])

    def test_geometry_candidates_are_not_wrong_press_or_duplicate_notes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); self.fixture(root)
            with gzip.open(root/'finger_control_trace.jsonl.gz','wt') as stream:
                for i in range(2640):
                    t=(i+1)/240.
                    extra=self.extra(t)
                    for j,goal in enumerate(extra['goals']): goal['press_candidate']=(t<4.5 if j%2==0 else t>=4.)
                    stream.write(json.dumps(dict(env_id=0,episode_id=1,episode_time_s=t,natural_preparation=dict(transition=extra)))+'\n')
            result=analyze_evaluation(root)
            transition=result['env0_trace']['transitions'][0]
            self.assertGreater(transition['next_candidate_before_previous_end_s'],.49)
            self.assertLess(transition['next_candidate_before_previous_end_s'],.51)
            self.assertEqual(result['notes'][0]['mean_wrong_s'],0.)
            self.assertEqual(result['note_success_count'],124)
            self.assertAlmostEqual(transition['arm_actual_displacement_rad'][0],.5)

    def test_missing_environment_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); rows=self.fixture(root)
            (root/'episodes.jsonl').write_text('\n'.join(map(json.dumps,rows[:-1])))
            with self.assertRaisesRegex(ValueError,'최초32'): analyze_evaluation(root)

    def test_required_transition_vectors_and_goal_order(self):
        for bad in ('missing','order','nonfinite','vector'):
            with self.subTest(bad=bad), tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp); self.fixture(root)
                with gzip.open(root/'finger_control_trace.jsonl.gz','wt') as stream:
                    for i in range(2640):
                        t=(i+1)/240.; extra=self.extra(t)
                        if bad=='order': extra['goals'].reverse()
                        if bad=='nonfinite': extra['arm_actual_rad'][0]=float('nan')
                        if bad=='vector': extra['wrist_error_m']=[]
                        row=dict(env_id=0,episode_id=1,episode_time_s=t)
                        if bad!='missing': row['natural_preparation']=dict(transition=extra)
                        stream.write(json.dumps(row)+'\n')
                with self.assertRaises(ValueError): analyze_evaluation(root)

    def test_truncated_trace_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); self.fixture(root)
            with gzip.open(root/'finger_control_trace.jsonl.gz','wt') as stream:
                stream.write(json.dumps(dict(env_id=0,episode_id=1,episode_time_s=.004))+'\n')
            with self.assertRaisesRegex(ValueError,'trace'): analyze_evaluation(root)


if __name__=='__main__': unittest.main()
