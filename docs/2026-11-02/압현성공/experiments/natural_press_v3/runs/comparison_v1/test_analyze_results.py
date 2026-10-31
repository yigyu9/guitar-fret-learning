"""물리/GPU 없이 합성 최초32 평가와 단일 궤적 수치를 검증한다."""
import copy
import gzip
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('natural_analysis',Path(__file__).with_name('analyze_results.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
NAMES=['LH:thumb'+str(i) for i in range(5)]+['LH:'+f+s for f in a.FINGERS for s in ('1_x','1_z','2','3')]


def fixture(path):
    report=dict(completed=True,lifecycle_verified=True,first_episode_per_env_per_batch=True,
        failed_episodes_in_denominator=True,episodes=32,settings=dict(natural_press=dict(condition='E4',finger='middle')))
    (path/'report.json').write_text(json.dumps(report))
    (path/'episode_metadata.json').write_text(json.dumps(dict(fields=[dict(path=['left_finger_motion','joint_names'],value=NAMES)])))
    rows=[]
    for env in range(32):
        reward=dict.fromkeys(a.TERMS,0.);reward['song_left_approach']=1.
        e=dict(env_id=env,valid=env!=31,task_time_s=6.,reward=1.,cost=5. if env==31 else 0.,
            termination=dict(physical_failure=env==31,wrist_failure=env==31),
            song=dict(stage_success=env!=31,target_count=1),
            left_note_ledger=dict(values=dict(clean=[2.5 if env!=31 else 0.],wrong=[env*.01],missing=[2.5 if env==31 else 0.])),
            reward_components=reward,natural_preparation=dict(condition='E4',columns=['unready_slow_wrist_s','early_candidate_s'],
                per_finger_seconds=[[0.,0.],[env*.1,env*.001],[0.,0.],[0.,0.]],
                longest_continuous_ready_before_descent_s=[0.,.2 if env<16 else .1,0.,0.]),
            finger_control_diagnostics=dict(episode_id=1,joint_names=NAMES,values={key:[.1]*21 for key in
                ('requested_tracking_error_rad_rms','applied_tracking_error_rad_rms','rate_limit_gap_rad_rms','velocity_rad_s_rms')}),
            left_finger_motion=dict(values=dict(actual_range_rad=[.1]*21,target_range_rad=[.2]*21)))
        rows.append(dict(episode=e))
    (path/'episodes.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in rows))
    trace=[];ix=NAMES.index('LH:middle1_x');ip=NAMES.index('LH:middle2')
    for t,q,r in ((1/240.,.5,.4),(.5,.3,.2),(59/60.,.25,.2),(61/60.,.2,.15),(2.,.1,.05),(3.,.4,.4),(6.,.5,.4)):
        actual=[0.]*21;request=[0.]*21;actual[ix],actual[ip]=q,q+.1;request[ix],request[ip]=r,r+.1
        trace.append(dict(env_id=0,episode_id=1,episode_time_s=t,joint_names=NAMES,actual_rad=actual,requested_target_rad=request,
            natural_preparation=dict(fingers=[dict(finger=2,observation_exposed=t>=.5,preparation_valid=True,ready=t>=2.,descent_blend=1. if t>=3. else 0.)])))
    write_trace(path,trace)
    return rows,trace


def write_trace(path,rows):
    with gzip.open(path/'finger_control_trace.jsonl.gz','wt') as stream:
        for row in rows:stream.write(json.dumps(row)+'\n')


class AnalysisTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name);self.rows,self.trace=fixture(self.path)
    def tearDown(self):self.tmp.cleanup()

    def test_failed_episode_stays_in_32_and_scalar_metrics(self):
        result=a.analyze_evaluation(self.path)
        self.assertEqual(result['episodes'],32);self.assertEqual(result['success_count'],31)
        self.assertEqual(result['physical_failure_count'],1);self.assertEqual(result['wrist_failure_count'],1)
        self.assertEqual(result['any_failure_count'],1);self.assertEqual(result['min_clean_s'],0.)
        self.assertAlmostEqual(result['mean_clean_s'],31*2.5/32)
        self.assertAlmostEqual(result['mean_wrong_s'],.155)
        self.assertAlmostEqual(result['mean_unready_slow_wrist_s'],1.55)
        self.assertAlmostEqual(result['p90_unready_slow_wrist_s'],2.79)
        self.assertEqual(result['ready_02_count'],16);self.assertFalse(result['pressure_performance_sufficient'])
        self.assertEqual(result['reward_term_means']['song_left_approach'],1.)
        json.dumps(result,allow_nan=False)

    def test_first_episode_filter_ignores_later_env0_episode(self):
        extra=copy.deepcopy(self.rows[0]);extra['episode']['song']['stage_success']=False
        extra['episode']['left_note_ledger']['values']['clean']=[0.]
        with (self.path/'episodes.jsonl').open('a') as stream:stream.write(json.dumps(extra)+'\n')
        self.assertEqual(a.analyze_evaluation(self.path)['success_count'],31)

    def test_trace_exact_angles_reversal_and_first_observed_times(self):
        result=a.analyze_evaluation(self.path)['env0_trace']
        self.assertAlmostEqual(result['max_actual_initial_extension_deg'][0],math.degrees(.4))
        self.assertAlmostEqual(result['max_requested_initial_extension_deg'][0],math.degrees(.45))
        self.assertAlmostEqual(result['joints']['MCP_x']['requested_additional_extension_degrees_at_1s'],math.degrees(.05))
        self.assertEqual(result['first_observed_times_s'],dict(observation_exposed=.5,preparation_valid=1/240.,ready=2.,descent_started=3.))
        ranges=a.analyze_evaluation(self.path)['joint_ranges_degrees']
        self.assertAlmostEqual(ranges['actual_range_rad/LH:middle1_x']['maximum'],math.degrees(.1))

    def test_missing_environment_or_failed_denominator_rejected(self):
        (self.path/'episodes.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in self.rows[:-1]))
        with self.assertRaises(ValueError):a.analyze_evaluation(self.path)
        fixture(self.path);report=json.loads((self.path/'report.json').read_text());report['failed_episodes_in_denominator']=False
        (self.path/'report.json').write_text(json.dumps(report))
        with self.assertRaises(ValueError):a.analyze_evaluation(self.path)

    def test_missing_trace_observation_and_nonfinite_rejected(self):
        del self.trace[0]['natural_preparation'];write_trace(self.path,self.trace)
        with self.assertRaises((KeyError,ValueError)):a.analyze_evaluation(self.path)
        _,trace=fixture(self.path);trace[0]['actual_rad'][NAMES.index('LH:middle1_x')]=float('nan');write_trace(self.path,trace)
        with self.assertRaises(ValueError):a.analyze_evaluation(self.path)


if __name__=='__main__':unittest.main()
