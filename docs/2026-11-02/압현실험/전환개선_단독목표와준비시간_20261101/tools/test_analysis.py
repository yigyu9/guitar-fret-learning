"""합성 원장·240Hz trace로 단독 B와 전환 평가 집계가 섞이지 않는지 검사한다."""
import gzip
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('single_gap_analysis_tests',HERE/'run_study.py')
study=importlib.util.module_from_spec(spec);spec.loader.exec_module(study)


def episode(env, goals, *, failed=False, episode_id=None):
    count=len(goals)
    return dict(env_id=env, valid=not failed,
        termination=dict(physical_failure=failed,wrist_failure=False),
        finger_control_diagnostics=dict(episode_id=env+10 if episode_id is None else episode_id),
        left_note_ledger=dict(values=dict(left=[not failed]*count,clean=[0. if failed else g['end_s']-g['onset_s'] for g in goals],wrong=[.2 if failed else 0.]*count)),
        transition_diagnostics=dict(first_contact_s=[None if failed else g['onset_s'] for g in goals]),
        reward_components=dict(approach=2. if failed else 4.,failure=-2. if failed else 0.),reward=0. if failed else 4.)


def transition(config,times, *, ids=None, position=True,facing=True,loaded=True,wrong=False,distance=.026):
    count=len(times);M=len(config['schedule'])
    field=lambda value:[[value]*M for _ in range(count)]
    return dict(schema=config['schema'],sequence_sha256=config['sequence_sha256'],
        all_env_episode_ids=list(range(10,10+count)) if ids is None else ids,
        all_env_episode_time_s=times,
        all_env_candidate=field(position and facing and loaded),all_env_wrong=field(wrong),
        all_env_position_geometry=field(position),all_env_facing_geometry=field(facing),
        all_env_assigned_loaded=field(loaded),all_env_distance_m=field(distance))


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory(prefix='single_gap_analysis_')
        self.folder=Path(self.directory.name)
        self.addCleanup(self.directory.cleanup)

    def fixture(self, goals, *, rows=None, traces=None, roles=None):
        M=len(goals)
        config=dict(schema='synthetic.strict.v2',sequence_sha256='a'*64,
            condition='b_only' if M==1 else 'gap150',schedule=goals,
            goal_roles=roles or (['B'] if M==1 else ['A','B']))
        rows=rows if rows is not None else [episode(0,goals)]
        count=len({r['env_id'] for r in rows})
        report=dict(completed=True,lifecycle_verified=True,failed_episodes_in_denominator=True,
            first_episode_per_env_per_batch=True,episodes=count,settings=dict(transition=config))
        (self.folder/'report.json').write_text(json.dumps(report))
        (self.folder/'episode_metadata.json').write_text(json.dumps(dict(fields=[])))
        (self.folder/'episodes.jsonl').write_text(''.join(json.dumps(dict(episode=r))+'\n' for r in rows))
        self.traces=traces if traces is not None else [transition(config,[goals[-1]['onset_s']]*count)]
        self.write_traces()
        return config,report

    def write_traces(self):
        with gzip.open(self.folder/'finger_control_trace.jsonl.gz','wt') as f:
            for tr in self.traces:f.write(json.dumps(dict(natural_preparation=dict(transition=tr)))+'\n')

    def test_single_b_index_zero_and_duration(self):
        goals=[dict(onset_s=3.,end_s=4.5,fret=8)]
        self.fixture(goals)
        result=study.analyze(self.folder,1)
        self.assertEqual(result['goal_roles'],['B'])
        self.assertEqual(result['achievement'],[1])
        self.assertEqual(result['clean_s'],[1.5])
        self.assertEqual((result['joint_achievement'],result['entire_hold'],result['on_time']),(1,1,1))
        self.assertIsNone(result['previous_tail_and_on_time'])
        self.assertEqual(result['B_pad_distance_median_m'],.026)
        self.assertEqual(result['rejection'],[dict(position=0,facing=0,load=0,wrong=0,clean=1)])
        self.assertEqual(json.loads((self.folder/'analysis.json').read_text()),result)

    def test_dynamic_pair_schedule_and_previous_tail(self):
        goals=[dict(onset_s=2.,end_s=3.),dict(onset_s=4.75,end_s=5.5)]
        config,_=self.fixture(goals)
        self.traces=[transition(config,[3.-(12-i)/240]) for i in range(12)]
        self.traces.append(transition(config,[4.75],distance=.018));self.write_traces()
        result=study.analyze(self.folder,1)
        self.assertEqual(result['clean_s'],[1.,.75])
        self.assertEqual((result['entire_hold'],result['on_time'],result['previous_tail_and_on_time']),(1,1,1))
        self.assertEqual(result['B_pad_distance_min_m'],.018)

    def test_failed_first_episode_keeps_denominator_and_ignores_later_success(self):
        goals=[dict(onset_s=3.,end_s=4.5)]
        rows=[episode(1,goals,failed=True),episode(0,goals),episode(1,goals,episode_id=99)]
        self.fixture(goals,rows=rows)
        result=study.analyze(self.folder,2)
        self.assertEqual(result['episodes'],2)
        self.assertEqual((result['physical'],result['joint_achievement']),(1,1))
        self.assertEqual(result['achievement'],[1])
        self.assertEqual(result['clean_s'],[.75])
        self.assertEqual(result['wrong_s'],[.1])
        self.assertEqual(result['reward_terms'],dict(approach=3.,failure=-1.))

    def test_trace_replay_and_outside_audible_window_excluded(self):
        goals=[dict(onset_s=3.,end_s=4.5)]
        config,_=self.fixture(goals)
        self.traces=[transition(config,[3.],distance=.024),transition(config,[3.],ids=[99],position=False,distance=9.),
                     transition(config,[2.99],distance=10.),transition(config,[4.5],distance=11.)]
        self.write_traces();result=study.analyze(self.folder,1)
        self.assertEqual(sum(result['rejection'][0].values()),1)
        self.assertEqual(result['B_pad_distance_median_m'],.024)

    def test_rejection_classification_priority(self):
        goals=[dict(onset_s=3.,end_s=4.5)]
        config,_=self.fixture(goals)
        self.traces=[transition(config,[3.1],**kw) for kw in (
            dict(position=False,facing=False,loaded=False,wrong=True),
            dict(facing=False,loaded=False,wrong=True),dict(loaded=False,wrong=True),dict(wrong=True),{})]
        self.write_traces();result=study.analyze(self.folder,1)
        self.assertEqual(result['rejection'][0],dict(position=1,facing=1,load=1,wrong=1,clean=1))

    def test_reward_mismatch_is_rejected(self):
        goals=[dict(onset_s=3.,end_s=4.5)];row=episode(0,goals);row['reward']=9.
        self.fixture(goals,rows=[row])
        with self.assertRaisesRegex(ValueError,'보상 합계'):study.analyze(self.folder,1)

    def test_trace_identity_mismatch_is_rejected(self):
        goals=[dict(onset_s=3.,end_s=4.5)];self.fixture(goals)
        self.traces[0]['sequence_sha256']='b'*64;self.write_traces()
        with self.assertRaisesRegex(ValueError,'trace 조건'):study.analyze(self.folder,1)

    def test_missing_env_and_false_denominator_contract_rejected(self):
        goals=[dict(onset_s=3.,end_s=4.5)]
        _,report=self.fixture(goals,rows=[episode(1,goals)])
        with self.assertRaisesRegex(ValueError,'분모 누락'):study.analyze(self.folder,1)
        self.fixture(goals);report=json.loads((self.folder/'report.json').read_text())
        report['failed_episodes_in_denominator']=False;(self.folder/'report.json').write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError,'실패포함분모'):study.analyze(self.folder,1)


if __name__=='__main__':unittest.main()
