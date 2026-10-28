"""Recovery denominators, stable-entry rules and actual integrated payout."""
import json
import unittest

import torch

from guitar_learning.gpu.episode_diagnostics import FingerRecoveryWindows, LeftEpisodeDiagnostics
from guitar_learning.gpu.finger_reward import finger_preparation_reward, finger_shape_reward
from guitar_learning.gpu.contact import thumb_support_geometry
from guitar_learning.tests.test_gpu_finger_recovery import inputs, segments
from guitar_learning.tests import test_gpu_episode_diagnostics as diagnostic_fixtures


class RecoveryWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def windows(self, count=1, duration=10.):
        return FingerRecoveryWindows(count, 'cpu', torch.tensor([1,1]),
            torch.tensor([4.,6.]), torch.tensor([5.,7.]),duration)

    def idle_windows(self, count=1, duration=2.):
        return FingerRecoveryWindows(count,'cpu',torch.empty(0,dtype=torch.long),
            torch.empty(0),torch.empty(0),duration)

    def tick(self, windows, step, *, inside=True, valid=True):
        n=windows.values['seen_s'].shape[0]
        windows.physics(torch.full((n,),step/240.,dtype=torch.float64),
            torch.full((n,4),inside,dtype=torch.bool),torch.full((n,4),valid,dtype=torch.bool))

    def test_score_only_complement_merges_overlaps_and_absent_fingers(self):
        windows=self.windows()
        self.assertEqual(windows.windows,[(0,1.05,3.65),(0,8.05,10.),(1,1.05,10.),(2,1.05,10.),(3,1.05,10.)])
        row=windows.episode(0)
        first=row['by_finger'][0]
        self.assertEqual(float(first['planned_windows']),2)
        self.assertAlmostEqual(float(first['planned_s']),4.55)
        self.assertEqual(float(first['observed_s']),0.)
        self.assertEqual(float(first['credited_in_band_fraction']),0.)
        self.assertTrue(bool(first['evaluable']))
        self.assertEqual(int(first['incomplete_or_unobserved_windows']),2)
        for finger in row['by_finger'][1:]:self.assertEqual(float(finger['planned_s']),8.95)

    def test_failure_after_entry_is_not_return_success_and_missing_time_gets_no_credit(self):
        windows=self.windows()
        for step in range(1,493):
            self.tick(windows,step,inside=step>276)
        row=windows.episode(0)
        first=row['by_finger'][0]
        self.assertAlmostEqual(float(first['observed_s']),1.,places=12)
        self.assertAlmostEqual(float(first['in_band_s']),.9,places=12)
        self.assertAlmostEqual(float(first['observed_in_band_fraction']),.9,places=12)
        self.assertAlmostEqual(float(first['credited_in_band_fraction']),.9/4.55,places=12)
        self.assertAlmostEqual(float(row['stable_entry_latency_s'][0]),.1,places=12)
        self.assertFalse(bool(row['return_within3s'][0]))
        self.assertEqual(int(first['return_within3s_windows']),0)
        self.assertEqual(int(first['incomplete_or_unobserved_windows']),2)

    def test_complete_window_requires_stable_point2s_and_valid_outside_start(self):
        windows=self.idle_windows(count=2,duration=3.05)
        # Fixed evaluation [1.05,3.05]; row0 starts outside,
        # row1 starts inside. Both reach/retain B but only row0 is a return.
        for step in range(1,733):
            inside=torch.ones(2,4,dtype=torch.bool)
            inside[0]=step>372
            windows.physics(torch.full((2,),step/240.,dtype=torch.float64),inside,
                torch.ones(2,4,dtype=torch.bool))
        for f in range(4):
            a,b=windows.episode(0)['by_finger'][f],windows.episode(1)['by_finger'][f]
            self.assertEqual(int(a['return_within3s_windows']),1)
            self.assertEqual(int(a['started_outside_windows']),1)
            self.assertEqual(int(b['return_within3s_windows']),0)
            self.assertEqual(int(b['started_inside_windows']),1)
        self.assertAlmostEqual(float(windows.episode(0)['stable_entry_latency_s'][0]),.5,places=12)

    def test_short_band_visits_invalid_start_and_unavailable_windows_are_not_success(self):
        windows=self.idle_windows(count=2,duration=3.05)
        for step in range(1,733):
            valid=torch.ones(2,4,dtype=torch.bool)
            if step==253:valid[1]=False
            inside=torch.full((2,4),step>276 and step<=312,dtype=torch.bool) # only0.15s
            windows.physics(torch.full((2,),step/240.,dtype=torch.float64),inside,valid)
        self.assertFalse(windows.episode(0)['return_within3s'].any())
        self.assertFalse(windows.episode(1)['started_valid'].any())
        self.assertTrue((windows.episode(0)['stable_entry_latency_s']==-1).all())
        busy=FingerRecoveryWindows(1,'cpu',torch.arange(1,5),torch.zeros(4),torch.ones(4)*2,2.)
        self.assertEqual(busy.windows,[])
        for row in busy.episode(0)['by_finger']:
            self.assertFalse(bool(row['evaluable']))
            self.assertEqual(float(row['planned_s']),0.)
            self.assertEqual(float(row['credited_in_band_fraction']),0.)

    def test_post_last_ge5s_is_separate_from_general_fixed_idle_windows(self):
        windows=self.windows(duration=14.)
        planned=windows.episode(0)['by_finger']
        self.assertEqual(int(planned[0]['post_last_ge5s']['planned_windows']),1)
        self.assertEqual(int(planned[0]['planned_windows']),2)
        for step in range(1,3361):
            self.tick(windows,step,inside=step>2052) #8.55s; index evaluation postlaststarts8.05s
        rows=windows.episode(0)['by_finger']
        tail=rows[0]['post_last_ge5s']
        self.assertTrue(bool(tail['evaluable']))
        self.assertEqual(int(tail['complete_windows']),1)
        self.assertEqual(int(tail['started_outside_windows']),1)
        self.assertEqual(int(tail['return_within3s_windows']),1)
        # Absent fingers have far-idle windows but no last assigned note.
        self.assertFalse(bool(rows[1]['post_last_ge5s']['evaluable']))
        self.assertEqual(int(rows[1]['post_last_ge5s']['planned_windows']),0)
        short=self.windows(duration=10.).episode(0)['by_finger'][0]['post_last_ge5s']
        self.assertFalse(bool(short['evaluable'])) #lasttailonly3s
        self.assertEqual(int(short['planned_windows']),0)

    def test_substep_window_boundaries_and_selected_reset_are_bounded(self):
        windows=FingerRecoveryWindows(2,'cpu',torch.tensor([1]),
            torch.tensor([1.402],dtype=torch.float64),torch.tensor([1.7],dtype=torch.float64),2.)
        shapes={key:value.shape for key,value in windows.values.items()}
        for step in range(1,265):self.tick(windows,step)
        self.assertEqual(shapes,{key:value.shape for key,value in windows.values.items()})
        pointers={key:value.data_ptr() for key,value in windows.values.items()}
        before={key:value[1].clone() for key,value in windows.values.items()}
        # Source window [1.05,1.052] ends between endpoints: measure0.002s, not1/240.
        self.assertAlmostEqual(float(windows.episode(0)['sampled_s'][0]),.002,places=12)
        windows.reset([0])
        for key,value in windows.values.items():
            self.assertFalse(value[0].any())
            torch.testing.assert_close(value[1],before[key],rtol=0,atol=0)
        self.assertEqual(pointers,{key:value.data_ptr() for key,value in windows.values.items()})

    def test_own_overlap_union_short_windows_and_preparation_cutoff(self):
        w=FingerRecoveryWindows(1,'cpu',torch.tensor([1,1,1,2]),
            torch.tensor([2.,2.5,5.5,0.]),torch.tensor([3.,4.,6.,10.]),10.)
        expected=[(0,1.05,1.65),(0,5.05,5.15),(0,7.05,10.),
            (2,1.05,10.),(3,1.05,10.)]
        torch.testing.assert_close(torch.tensor(w.windows),torch.tensor(expected))
        row=w.episode(0)
        self.assertEqual(row['occupancy_evaluable'].tolist(),[True,False,True,True,True])
        self.assertEqual(int(row['by_finger'][0]['excluded_short_windows']),1)
        self.assertEqual(int(row['by_finger'][0]['planned_windows']),2)
        self.assertFalse(row['by_finger'][1]['evaluable'])
        self.assertIn('provisional',row['budget']['status'])

    def test_occupancy80_uses_full_fixed_exposure_and_failure_cannot_pass(self):
        w=self.idle_windows(count=2,duration=3.05)
        for step in range(1,733):
            # row0 completes2s and spends1.6s in band, row1 fails after1.6s.
            now=torch.tensor([step/240.,min(step,636)/240.],dtype=torch.float64)
            inside=torch.full((2,4),step<=636,dtype=torch.bool)
            if step<=636:
                w.physics(now,inside,torch.ones_like(inside))
            else:
                # Freeze row1's clock outside every fixed window: no fake
                # repeated endpoint exposure after its failure.
                now[1]=0.
                w.physics(now,inside,torch.ones_like(inside))
        a,b=w.episode(0),w.episode(1)
        self.assertTrue(a['occupancy80_met'].all())
        self.assertFalse(b['occupancy80_met'].any())
        self.assertAlmostEqual(float(b['by_finger'][0]['credited_in_band_fraction']),.8,places=12)
        self.assertAlmostEqual(float(b['by_finger'][0]['coverage_fraction']),.8,places=12)


class RecoveryPayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):torch.set_num_threads(1)

    def test_reads_actual_per_finger_rates_including_optional_stronger_coefficient(self):
        d=LeftEpisodeDiagnostics(2,'cpu')
        total_B=torch.zeros(2,4,dtype=torch.float64)
        total_shape=torch.zeros_like(total_B)
        for step in range(1,5):
            data=inputs((1.+step/240.,)*2)
            # Old near-only veto is gone: close distance alone cannot disable B.
            data['distance'][1,0]=.03
            posture=finger_preparation_reward(**data,rate_per_s=.04)
            shape=finger_shape_reward(*(data[key] for key in ('now','onset','end','press','finger')),
                posture['angles'],posture['valid'],rate_per_s=.004)
            posture['shape_per_finger_rate']=shape['per_finger_rate']
            d.physics(posture,torch.zeros(2,4,dtype=torch.bool),torch.zeros(2,3))
            total_B+=posture['per_finger_rate']/240.
            total_shape+=shape['per_finger_rate']/240.
        d.control(torch.tensor([False,True]),.37,torch.tensor([.01,.01]),torch.tensor([.01,.01]))
        for i in range(2):
            row=d.episode(i)
            torch.testing.assert_close(torch.tensor(row['standby']['raw_standby_reward'],dtype=torch.float64),total_B[i],rtol=0,atol=0)
            torch.testing.assert_close(torch.tensor(row['shape']['raw_shape_reward'],dtype=torch.float64),total_shape[i],rtol=0,atol=0)
            torch.testing.assert_close(torch.tensor(row['standby']['weighted_standby_reward'],dtype=torch.float64),total_B[i]*(.37 if i==0 else 0.),rtol=0,atol=0)
            torch.testing.assert_close(torch.tensor(row['shape']['weighted_shape_reward'],dtype=torch.float64),total_shape[i]*(.37 if i==0 else 0.),rtol=0,atol=0)
            json.dumps(row,allow_nan=False)
        self.assertGreater(total_shape[0,0],0.)
        self.assertGreater(float(total_B[1,0]),0.)
        # Calling control again cannot pay an already consumed240Hz subtotal.
        before=d.episode(0)['standby']['weighted_standby_reward']
        d.control(torch.tensor([False,False]),1.,torch.tensor([.01,.01]),torch.tensor([.01,.01]))
        self.assertEqual(d.episode(0)['standby']['weighted_standby_reward'],before)

    def test_gate_runs_count_closed_and_current_runs_once_at_each_threshold(self):
        d=LeftEpisodeDiagnostics(2,'cpu')
        posture,pressing,wrist=diagnostic_fixtures.EpisodeDiagnosticsTests().inputs()
        for length in (120,240,720):
            posture['gate'][:]=.1 # Any positivefade belongs togate>0 runs.
            for _ in range(length):d.physics(posture,pressing,wrist)
            if length!=720:
                posture['gate'][:]=0.
                d.physics(posture,pressing,wrist)
        row=d.episode(0)['standby']['actual_gate_runs']
        self.assertEqual(row['count'],[3]*4)
        self.assertEqual(row['max_s'],[3.]*4)
        self.assertEqual(row['long_count'],[[3,2,1]]*4)
        torch.testing.assert_close(torch.tensor(row['long_total_s']),torch.tensor([[4.5,4.,3.]]*4))
        self.assertEqual(d.episode(0)['standby']['actual_gate_runs'],row)
        other=d.episode(1)
        d.reset([0])
        self.assertEqual(d.episode(1),other)
        self.assertEqual(d.episode(0)['standby']['actual_gate_runs']['count'],[0]*4)

    def test_full_gate_runs_separate_fade_and_measure_band_occupancy(self):
        d=LeftEpisodeDiagnostics(2,'cpu')
        p,pressing,wrist=diagnostic_fixtures.EpisodeDiagnosticsTests().inputs()
        for step in range(240):
            p['gate'][:]=.1 if step<120 else 1.
            p['band_inside'][:]=step>=180 #last0.25sofpositiverun
            d.physics(p,pressing,wrist)
        p['gate'][:]=0.
        d.physics(p,pressing,wrist)
        for step in range(720):
            p['gate'][:]=1.
            p['band_inside'][:]=step>=360
            d.physics(p,pressing,wrist)
        positive=d.episode(0)['standby']['actual_gate_runs']
        full=d.episode(0)['standby']['full_gate_runs']
        self.assertEqual(positive['count'],[2]*4)
        self.assertEqual(full['count'],[2]*4)
        self.assertEqual(positive['long_count'],[[2,2,1]]*4)
        self.assertEqual(full['long_count'],[[2,1,1]]*4)
        self.assertEqual(positive['total_s'],[4.]*4)
        self.assertEqual(full['total_s'],[3.5]*4)
        self.assertEqual(positive['in_band_s'],[1.75]*4)
        self.assertEqual(full['in_band_s'],[1.75]*4)
        self.assertEqual(positive['long_total_s'],[[4.,4.,3.]]*4)
        self.assertEqual(full['long_total_s'],[[3.5,3.,3.]]*4)
        torch.testing.assert_close(torch.tensor(positive['long_in_band_s']),torch.tensor([[1.75,1.75,1.5]]*4))
        torch.testing.assert_close(torch.tensor(full['long_in_band_s']),torch.tensor([[1.75,1.5,1.5]]*4))
        torch.testing.assert_close(torch.tensor(full['long_in_band_fraction']),torch.tensor([[.5,.5,.5]]*4))
        self.assertEqual(d.episode(0)['standby']['full_gate_runs'],full)
        d.reset([0])
        reset=d.episode(0)['standby']['full_gate_runs']
        self.assertEqual(reset['total_s'],[0.]*4)
        self.assertEqual(reset['long_in_band_fraction'],[[0.]*3]*4)

    def test_score_diagnostics_requires_clock_and_does_not_change_policy_dependent_windows(self):
        d=LeftEpisodeDiagnostics(2,'cpu',finger=torch.tensor([1]),press=torch.tensor([3.]),end=torch.tensor([5.]),duration_s=8.)
        p,pressing,wrist=diagnostic_fixtures.EpisodeDiagnosticsTests().inputs()
        with self.assertRaisesRegex(ValueError,'actual physics time'):d.physics(p,pressing,wrist)
        # Separate fresh accumulator: the invalidcall is not a validphysics sample.
        d=LeftEpisodeDiagnostics(2,'cpu',finger=torch.tensor([1]),press=torch.tensor([3.]),end=torch.tensor([5.]),duration_s=8.)
        windows=list(d.recovery.windows)
        p['gate'][:]=0.
        d.physics(p,pressing,wrist,now=torch.full((2,),1.1,dtype=torch.float64))
        self.assertEqual(d.recovery.windows,windows)
        row=d.episode(0)
        self.assertGreater(row['recovery']['by_finger'][0]['observed_s'],0.)
        self.assertEqual(row['standby']['gate_weighted_s'],[0.]*4)
        json.dumps(row,allow_nan=False)


class NewPhysicsSummaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):torch.set_num_threads(1)

    def thumb(self,count=2):
        return dict(valid=torch.ones(count,dtype=torch.bool),
            near_geometry=torch.ones(count,dtype=torch.bool),
            contact_candidate=torch.zeros(count,dtype=torch.bool),
            normal_load=torch.zeros(count,dtype=torch.float64),
            normal_load_valid=torch.ones(count,dtype=torch.bool),
            quality=torch.ones(count,dtype=torch.float64),
            rate=torch.full((count,),.01,dtype=torch.float64),
            signed_gap=torch.full((count,),.001,dtype=torch.float64),
            normal_cos=torch.ones(count,dtype=torch.float64),
            region_excess=torch.zeros(count,dtype=torch.float64))

    def test_extreme_geometry_counts_are_score_idle_press_and_gate_independent(self):
        d=LeftEpisodeDiagnostics(2,'cpu')
        p,pressing,wrist=diagnostic_fixtures.EpisodeDiagnosticsTests().inputs()
        p['gate'][:]=0.
        p['angles'][:]=torch.deg2rad(torch.tensor([[-42.,90.,90.],[90.,90.,-5.],
            [0.,10.,80.],[30.,40.,20.]],dtype=torch.float64))
        pressing[:,1]=True
        p['valid'][1,0,0]=False
        d.physics(p,pressing,wrist)
        row=d.episode(0)['extreme_combinations']
        self.assertEqual(row['all']['index_like_s'],[1/240,0.,0.,0.])
        self.assertEqual(row['all']['pinky_like_s'],[0.,1/240,0.,0.])
        self.assertEqual(row['all']['distal_excess_s'],[0.,0.,1/240,0.])
        self.assertEqual(row['all']['any_s'],[1/240,1/240,1/240,0.])
        self.assertEqual(row['idle']['pinky_like_s'],[0.]*4)
        self.assertEqual(row['press']['pinky_like_s'],[0.,1/240,0.,0.])
        self.assertEqual(d.episode(1)['extreme_combinations']['all']['valid_s'][0],0.)

    def test_thumb240_actual_payout_failure_suppression_and_tick_consumption(self):
        d=LeftEpisodeDiagnostics(2,'cpu');m=self.thumb()
        for _ in range(4):
            d.thumb_physics(m,torch.tensor([[3.,4.,0.],[0.,0.,10.]]))
        d.control(torch.tensor([False,True]),.01,torch.zeros(2),torch.zeros(2),thumb_weight=1.)
        a,b=(d.episode(i)['thumb_support'] for i in range(2))
        self.assertEqual(a['endpoint_count'],4)
        self.assertAlmostEqual(a['sampled_s'],1/60.)
        self.assertAlmostEqual(a['weighted_reward'],.01*.01/60.)
        self.assertEqual(b['weighted_reward'],0.)
        self.assertEqual(a['native_thumb3_net_force_max_N'],5.)
        self.assertAlmostEqual(a['native_thumb3_net_force_mean_N'],5.)
        self.assertEqual(a['near_geometry_fraction'],1.)
        self.assertAlmostEqual(a['mean_signed_gap_m'],.001)
        self.assertEqual(a['mean_normal_cos'],1.)
        d.control(torch.tensor([False,False]),1.,torch.zeros(2),torch.zeros(2))
        self.assertEqual(d.episode(0)['thumb_support']['weighted_reward'],a['weighted_reward'])
        for _ in range(4):d.thumb_physics(m,torch.zeros(2,3))
        d.control(torch.tensor([False,False]),1.,torch.zeros(2),torch.zeros(2),thumb_weight=0.)
        self.assertEqual(d.episode(0)['thumb_support']['weighted_reward'],a['weighted_reward'])
        self.assertAlmostEqual(d.episode(0)['thumb_support']['raw_reward'],.01/30.)

    def test_thumb_invalid_selected_gap_flags_and_partial_reset_are_finite(self):
        d=LeftEpisodeDiagnostics(2,'cpu');m=self.thumb()
        m['signed_gap'][0]=-.002;m['quality'][0]=0.;m['rate'][0]=0.
        m['near_geometry'][:]=False
        m['quality'][1]=float('nan')
        force=torch.tensor([[0.,0.,0.],[float('inf'),0.,0.]])
        d.thumb_physics(m,force)
        a,b=(d.episode(i)['thumb_support'] for i in range(2))
        self.assertEqual(a['selected_deep_gap_s'],1/240)
        self.assertEqual(a['selected_negative_gap_s'],1/240)
        self.assertAlmostEqual(a['min_signed_gap_m'],-.002)
        self.assertAlmostEqual(a['max_signed_gap_m'],-.002)
        self.assertEqual(b['invalid_s'],1/240)
        self.assertEqual(b['force_invalid_s'],1/240)
        for i in range(2):json.dumps(d.episode(i),allow_nan=False)
        before=d.episode(1);pointers={k:v.data_ptr() for k,v in d.values.items()}
        d.reset([0])
        self.assertEqual(d.episode(1),before)
        self.assertEqual(d.episode(0)['thumb_support']['sampled_s'],0.)
        self.assertEqual(pointers,{k:v.data_ptr() for k,v in d.values.items()})
        json.dumps(d.episode(0),allow_nan=False)
        d.thumb_physics(self.thumb(),torch.zeros(2,3))
        self.assertAlmostEqual(d.episode(0)['thumb_support']['min_signed_gap_m'],.001)

    def helper_measurement(self, force=None):
        points=torch.zeros(3,1,3,dtype=torch.float64)
        points[:,0,2]=torch.tensor([-.0002,-.002,-.0002],dtype=torch.float64)
        normals=torch.zeros_like(points);normals[...,2]=1.
        return thumb_support_geometry(points,normals,torch.ones(1,dtype=torch.bool),
            torch.zeros(3,dtype=torch.float64),
            torch.tensor([[-.04,-.2,0.],[.04,-.2,0.],[.08,.2,0.],[-.08,.2,0.]],dtype=torch.float64),
            torch.tensor([0.,0.,-1.,0.],dtype=torch.float64),net_force_guitar=force)

    def test_helper_rate_contact_load_and_unloaded_near_are_distinct(self):
        d=LeftEpisodeDiagnostics(3,'cpu')
        force=torch.tensor([[0.,0.,-.02],[0.,0.,-.04],[0.,0.,0.]],dtype=torch.float64)
        m=self.helper_measurement(force)
        for _ in range(4):d.thumb_physics(m,force)
        d.control(torch.tensor([False,True,False]),.25,torch.zeros(3),torch.zeros(3))
        rows=[d.episode(i)['thumb_support'] for i in range(3)]
        for i,row in enumerate(rows):
            self.assertAlmostEqual(row['sampled_s'],1/60.)
            self.assertEqual(row['near_geometry_fraction'],1.)
            self.assertAlmostEqual(row['normal_load_valid_s'],1/60.)
            self.assertEqual(row['normal_load_invalid_s'],0.)
            self.assertAlmostEqual(row['normal_load_mean_N'],[.02,.04,0.][i])
            self.assertAlmostEqual(row['normal_load_max_N'],[.02,.04,0.][i])
            self.assertAlmostEqual(row['raw_reward'],[.02,.01,.01][i]/60.)
            self.assertAlmostEqual(row['contact_candidate_s'],[1/60.,0.,0.][i])
            self.assertAlmostEqual(row['nearbutunloaded_s'],[0.,0.,1/60.][i])
        self.assertAlmostEqual(rows[0]['weighted_reward'],.25*.02/60.)
        self.assertEqual(rows[1]['weighted_reward'],0.)
        self.assertAlmostEqual(rows[2]['weighted_reward'],.25*.01/60.)
        before=d.episode(1);pointers={k:v.data_ptr() for k,v in d.values.items()}
        d.reset([0])
        self.assertEqual(d.episode(1),before)
        for name in ('contact_candidate_s','nearbutunloaded_s','normal_load_mean_N','normal_load_max_N',
                     'normal_load_valid_s','normal_load_invalid_s'):
            self.assertEqual(d.episode(0)['thumb_support'][name],0.)
        self.assertEqual(pointers,{k:v.data_ptr() for k,v in d.values.items()})

    def test_omitted_force_is_not_a_measured_zero_load(self):
        d=LeftEpisodeDiagnostics(3,'cpu')
        missing=self.helper_measurement()
        d.thumb_physics(missing,torch.zeros(3,3))
        before=d.episode(0)['thumb_support']
        self.assertEqual(before['normal_load_valid_s'],0.)
        self.assertEqual(before['normal_load_invalid_s'],1/240.)
        self.assertEqual(before['nearbutunloaded_s'],0.)
        self.assertAlmostEqual(before['raw_reward'],.01/240.)
        measured=self.helper_measurement(torch.zeros(3,3,dtype=torch.float64))
        d.thumb_physics(measured,torch.zeros(3,3))
        after=d.episode(0)['thumb_support']
        self.assertEqual(after['normal_load_valid_s'],1/240.)
        self.assertEqual(after['normal_load_invalid_s'],1/240.)
        self.assertEqual(after['nearbutunloaded_s'],1/240.)
        self.assertAlmostEqual(after['raw_reward'],.01/120.)

    def test_nonfinite_helper_force_is_excluded_and_summary_remains_finite(self):
        d=LeftEpisodeDiagnostics(3,'cpu')
        force=torch.tensor([[float('nan'),0.,-.02],[0.,float('inf'),-.02],[0.,0.,.02]],dtype=torch.float64)
        m=self.helper_measurement(force)
        d.thumb_physics(m,force)
        for i in range(3):
            row=d.episode(i)
            self.assertEqual(row['schema'],'guitar_learning.gpu_left_episode_diagnostics.v5')
            self.assertEqual(row['thumb_support']['contact_candidate_s'],0.)
            self.assertEqual(row['thumb_support']['normal_load_mean_N'],0.)
            self.assertEqual(row['thumb_support']['normal_load_max_N'],0.)
            self.assertAlmostEqual(row['thumb_support']['raw_reward'],.01/240.)
            self.assertEqual(row['thumb_support']['normal_load_valid_s'],[0.,0.,1/240.][i])
            json.dumps(row,allow_nan=False)

    def test_thumb_invalid_force_shape_does_not_partially_accumulate(self):
        d=LeftEpisodeDiagnostics(2,'cpu');before=d.episode(0)
        with self.assertRaisesRegex(ValueError,'resultant force'):
            d.thumb_physics(self.thumb(),torch.zeros(2,2,3))
        self.assertEqual(d.episode(0),before)


class InitialQualityDeclineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):torch.set_num_threads(1)

    def diagnostic(self):
        return LeftEpisodeDiagnostics(2,'cpu',finger=torch.tensor([1,2]),
            press=torch.tensor([3.,1.]),end=torch.tensor([4.,2.]),duration_s=6.)

    def args(self):
        return diagnostic_fixtures.EpisodeDiagnosticsTests().inputs()

    def tick(self,d,args,time):
        d.physics(*args,now=torch.full((2,),time,dtype=torch.float64))

    def test_fixed_initial_window_full_gate_and_numerical_tolerance(self):
        d=self.diagnostic();args=self.args();p,_,_=args
        p['quality'][:]=torch.tensor([.8,.6,.4,.2],dtype=torch.float64)
        d.set_reset_posture([0,1],p)
        p['quality'][:]=torch.tensor([.7,.5,.3,.2-5e-7],dtype=torch.float64)
        p['gate'][1,2]=.5
        p['valid'][1,3,0]=False
        self.tick(d,args,1/240.)
        a=d.episode(0)['standby']['initial_quality_decline']
        b=d.episode(1)['standby']['initial_quality_decline']
        self.assertEqual(a['planned_window_s'],[1.,0.,6.,6.])
        self.assertEqual(a['observed_s'],[1/240.,0.,1/240.,1/240.])
        self.assertEqual(a['declined_fraction'],[1.,0.,1.,0.])
        self.assertEqual(a['evaluable'],[True,False,True,True])
        self.assertEqual(b['observed_s'],[1/240.,0.,0.,0.])
        self.assertEqual(b['evaluable'],[True,False,False,False])
        self.tick(d,args,1.) #Index first press-2 begins here, so no longerinitial.
        self.assertEqual(d.episode(0)['standby']['initial_quality_decline']['observed_s'][0],1/240.)
        self.assertEqual(d.episode(0)['standby']['initial_quality_decline']['observed_s'][2],2/240.)

    def test_invalid_reference_excluded_until_real_reset_and_missing_is_not_evaluable(self):
        d=self.diagnostic();args=self.args();p,_,_=args
        untouched=d.episode(0)['standby']['initial_quality_decline']
        self.assertEqual(untouched['observed_s'],[0.]*4)
        self.assertEqual(untouched['evaluable'],[False]*4)
        p['valid'][0,0,0]=False
        p['quality'][0,2]=float('nan')
        d.set_reset_posture([0,1],p)
        p['valid'][:]=True;p['quality'][:]=.1
        self.tick(d,args,1/240.)
        result=d.episode(0)['standby']['initial_quality_decline']
        self.assertEqual(result['reference_valid'],[False,True,False,True])
        self.assertEqual(result['observed_s'],[0.,0.,0.,1/240.])
        self.assertEqual(result['declined_fraction'],[0.,0.,0.,1.])
        json.dumps(d.episode(0),allow_nan=False)

    def test_actual_helper_quality_declines_and_partial_reset_refreshes_only_selected_row(self):
        d=self.diagnostic()
        data=inputs((0.,0.));p=finger_preparation_reward(**data)
        d.set_reset_posture([0,1],p)
        data['now'][:]=.1
        data['segment_quaternion']=segments(torch.tensor([[0.,0.,90.]]*4,dtype=torch.float64))[None].expand(2,-1,-1,-1)
        p=finger_preparation_reward(**data)
        p['shape_per_finger_rate']=torch.zeros(2,4,dtype=torch.float64)
        args=(p,torch.zeros(2,4,dtype=torch.bool),torch.zeros(2,3))
        self.tick(d,args,.1)
        a=d.episode(0)['standby']['initial_quality_decline']
        self.assertEqual(a['declined_fraction'],[1.,0.,1.,1.])
        before=d.episode(1)
        d.reset([0]);d.set_reset_posture([0],p)
        self.assertEqual(d.episode(1),before)
        self.assertEqual(d.episode(0)['standby']['initial_quality_decline']['observed_s'],[0.]*4)
        self.tick(d,args,.2)
        after=d.episode(0)['standby']['initial_quality_decline']
        self.assertEqual(after['declined_fraction'],[0.]*4)
        self.assertEqual(after['evaluable'],[True,False,True,True])
        torch.testing.assert_close(torch.tensor(after['reference_quality'],dtype=torch.float64),p['quality'][0],rtol=0,atol=0)

    def test_environment_reset_captures_actual_quality_and_h32_window_preserves_reference(self):
        from guitar_learning.gpu.control import multiply
        from guitar_learning.tests.test_gpu_surface_learning import task
        env,snapshot,_=diagnostic_fixtures.fixtures.TensorSongTests.environment(self,task=task(onset=4.,end=5.,press=3.))
        d=env.episode_diagnostics
        p=env._finger_preparation(env.clock.double()/240.)
        torch.testing.assert_close(d.initial_reference,p['quality'].double(),rtol=0,atol=0)
        before=d.episode(1)
        palm=snapshot['body_state'][:,env.finger_palm_index,3:7]
        relative=inputs((0.,0.))['segment_quaternion'].to(palm.dtype)
        snapshot['body_state'][:,env.finger_segment_indices,3:7]=multiply(palm[:,None,None],relative)
        env.reset([0],snapshot)
        current=env._finger_preparation(env.clock.double()/240.)
        torch.testing.assert_close(d.initial_reference[0],current['quality'][0].double(),rtol=0,atol=0)
        self.assertEqual(d.episode(1),before)
        reference=d.initial_reference.clone()
        env.reset_reward_window()
        torch.testing.assert_close(d.initial_reference,reference,rtol=0,atol=0)



if __name__=='__main__':unittest.main()
