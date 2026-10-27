"""Pure aggregation and saved-pose geometry checks; no GPU/physics execution."""
import copy
import importlib.util
from pathlib import Path
import unittest

import numpy as np

SPEC=importlib.util.spec_from_file_location('v20_a500_analysis',Path(__file__).with_name('analyze.py'))
A=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(A)


def episode(outside=1,unknown=1,returned=1):
    planned=outside+unknown
    by_finger=[dict(planned_windows=planned,planned_s=planned*5.,observed_s=outside*5.,
        valid_s=outside*5.,in_band_s=outside*3.,complete_windows=outside,
        incomplete_or_unobserved_windows=unknown,started_outside_windows=outside,
        return_within3s_windows=returned,started_inside_windows=0,
        initially_unobserved_or_invalid_windows=unknown,
        post_last_ge5s=dict(planned_windows=planned,complete_windows=outside,
            incomplete_or_unobserved_windows=unknown,started_outside_windows=outside,
            started_inside_windows=0,initially_unobserved_or_invalid_windows=unknown,
            return_within3s_windows=returned,evaluable=planned>0)) for _ in range(4)]
    initial=dict(reference_quality=[.5]*4,reference_valid=[True]*4,
        observed_s=[1.]*4,declined_s=[.25]*4,evaluable=[True]*4)
    runs=dict(count=[2]*4,total_s=[5.]*4,in_band_s=[3.]*4,max_s=[4.]*4,
        long_count=[[2,2,1]]*4,long_total_s=[[5.,5.,4.]]*4,long_in_band_s=[[3.,3.,2.]]*4)
    angles=dict(valid_weighted_s=[[1.,1.,1.]]*4,mean_rad=[[.1,.2,.3]]*4)
    diag=dict(recovery=dict(by_finger=by_finger),standby=dict(initial_quality_decline=initial,
        actual_gate_runs=runs,full_gate_runs=runs),idle_angles=angles,press_angles=angles)
    return dict(left_episode_diagnostics=diag)


def music(n=1024,score=5.,safe=.9):
    row=dict(episodes=n,achieved_mean=score,safe_complete_count=int(round(n*safe)),
        safe_complete_fraction=safe,wrong_audible_fraction=.1,missing_audible_fraction=.8,
        fingers={})
    for name,count in zip(A.FINGERS,(25,18,12,12)):
        row['fingers'][name]=dict(targets_per_song=count,audible_s_per_song=1.,
            near_fraction=.4,contact_fraction=.3,success_fraction=.2,clean_fraction=.2,
            mean_achieved_notes=.2*count,wrong_mean_s=.1,missing_mean_s=.8,
            wrong_audible_fraction=.1,missing_audible_fraction=.8)
    return row


class Aggregation(unittest.TestCase):
    def audible_fixture(self,failures=True):
        targets=[dict(target_id=str(i),finger=f,onset_s=3.,end_s=4.,press_s=2.8)
            for f,count in enumerate((25,18,12,12),1) for i in range(sum((25,18,12,12)[:f-1]),sum((25,18,12,12)[:f]))]
        def rows():
            for i in range(1024):
                failed=failures and i<512
                duration=3.5 if failed else 5.
                yield dict(env_id=i,valid=True,reason='terminal_failure' if failed else 'timeline_complete',
                    task_time_s=duration,left_curriculum=dict(full_safe=not failed),
                    left_note_ledger=dict(target_ids=[t['target_id'] for t in targets],
                        values=dict(exposure_time=[min(duration,4.)-.8]*67,
                            clean=[.05 if failed else .1]*67,wrong=[.25 if failed else .1]*67,
                            missing=[.2 if failed else .8]*67)))
        return rows(),targets

    def test_audible_exposure_splits_failure_and_approach_windows(self):
        rows,targets=self.audible_fixture()
        output=A.audible_summary(rows,targets)
        failed=output['groups']['failed']['fingers']['index']
        safe=output['groups']['full_safe']['fingers']['index']
        self.assertEqual(output['groups']['failed']['episodes'],512)
        self.assertAlmostEqual(failed['observed_audible_s'],512*25*.5)
        self.assertAlmostEqual(failed['approach_exposure_s'],512*25*2.7)
        self.assertAlmostEqual(failed['wrong_fraction_planned_audible'],.25)
        self.assertAlmostEqual(failed['wrong_fraction_observed_audible'],.5)
        self.assertAlmostEqual(safe['wrong_fraction_observed_audible'],.1)
        self.assertAlmostEqual(failed['unobserved_audible_s'],512*25*.5)

    def test_zero_failure_group_is_none_and_safe_comparison_still_applies(self):
        rows,targets=self.audible_fixture(False)
        output=A.audible_summary(rows,targets)
        self.assertFalse(output['groups']['failed']['evaluable'])
        self.assertIsNone(output['groups']['failed']['all_notes']['wrong_fraction_observed_audible'])
        pooled=A.pooled_exposure([output,output,output])
        self.assertEqual(pooled['groups']['full_safe']['episodes'],3072)
        result=A.compare_exposure(pooled,pooled)
        self.assertTrue(result['all_and_full_safe_point_comparison_pass'])
        self.assertEqual(result['groups']['failed']['index']['status'],'unknown')

    def test_markdown_keeps_zero_failure_denominator_and_scope_visible(self):
        rows,targets=self.audible_fixture(False)
        exposure=A.audible_summary(rows,targets)
        recovery=A.recovery_summary([episode()])
        sample=dict(fingers={name:dict(press_pattern_fraction=None,
            fixed_window_credited_occupancy=0.) for name in A.FINGERS})
        m=music()
        repeat=dict(repeat=1,music=m,sampled_posture=sample,comparison_to_v19=A.compare_music(m,m),
            exposure_comparison_to_v19=A.compare_exposure(exposure,exposure))
        pooled=dict(music=m,recovery=recovery,audible_exposure=exposure)
        output=A.markdown(dict(historical_anchor=dict(music=m,sampled_posture=sample),
            baseline_pooled=pooled,current_pooled=pooled,baselines=[repeat],repeats=[repeat],
            pooled_recovery_comparison=A.recovery_comparison(recovery,recovery),
            recommendation=dict(text='후속 검토 필요')))
        self.assertIn('물리 실패 0곡',output)
        self.assertIn('판정 불가',output)
        self.assertIn('접근 노출과 음이 울리는',output)

    def test_unknown_and_failure_windows_do_not_become_success(self):
        summary=A.recovery_summary([episode(),episode(2,0,1)])['fingers']['index']
        fixed=summary['fixed_score_windows']
        self.assertEqual(fixed['planned_windows'],4)
        self.assertEqual(fixed['initially_unobserved_or_invalid_windows'],1)
        self.assertEqual(fixed['credited_in_band_fraction'],9/20)
        self.assertEqual(fixed['observed_in_band_fraction'],9/15)
        tail=summary['post_last_ge5s']
        self.assertEqual(tail['return_fraction_known_outside'],2/3)
        self.assertEqual(tail['return_fraction_unknown_as_nonreturn'],2/4)
        self.assertEqual(tail['criterion70_status'],'unknown')

    def test_missing_historical_diagnostics_remain_unknown(self):
        output=A.recovery_summary([dict(left_episode_diagnostics={})])
        self.assertFalse(output['known'])

    def test_no_scheduled_window_is_not_an_automatic_pass(self):
        output=A.recovery_summary([episode(0,0,0)])['fingers']['pinky']
        self.assertFalse(output['fixed_score_windows']['evaluable'])
        self.assertIsNone(output['fixed_score_windows']['credited_in_band_fraction'])
        self.assertEqual(output['post_last_ge5s']['criterion70_status'],'unknown')

    def test_initial_decline_and_long_runs_use_time_weights(self):
        one,two=episode(),episode()
        two['left_episode_diagnostics']['standby']['initial_quality_decline']['observed_s']=[3.]*4
        two['left_episode_diagnostics']['standby']['initial_quality_decline']['declined_s']=[0.]*4
        output=A.recovery_summary([one,two])['fingers']['ring']
        self.assertEqual(output['initial_quality_decline']['declined_fraction'],.25/4)
        self.assertEqual(output['full_gate_runs']['long_count'],[4,4,2])
        self.assertEqual(output['full_gate_runs']['long_in_band_fraction'],[.6,.6,.5])

    def test_musical_deterioration_identifies_single_finger(self):
        old=music()
        new=copy.deepcopy(old)
        self.assertTrue(A.compare_music(new,old)['point_comparison_pass'])
        new['fingers']['middle']['wrong_audible_fraction']+=.051
        result=A.compare_music(new,old)
        self.assertFalse(result['point_comparison_pass'])
        self.assertEqual(result['fingers']['middle']['status'],'fail')
        self.assertEqual(result['fingers']['index']['status'],'pass')

    def test_pooled_music_preserves_episode_denominators(self):
        output=A.pooled_music([music(10,2.,.8),music(30,6.,1.)])
        self.assertEqual(output['episodes'],40)
        self.assertEqual(output['achieved_mean'],5.)
        self.assertEqual(output['safe_complete_count'],38)
        self.assertEqual(output['safe_complete_fraction'],.95)

    def test_fixed_window_merges_overlapping_preparation_and_clips(self):
        targets=[dict(finger=1,press_s=1.,end_s=2.),dict(finger=1,press_s=3.,end_s=4.),
            dict(finger=1,press_s=8.,end_s=9.)]
        windows=A.fixed_windows(targets,15.)
        index=[r for r in windows if r['finger']==1]
        self.assertEqual([(r['start_s'],r['end_s']) for r in index],[(4.,6.),(9.,15.)])
        self.assertEqual([r['post_last_ge5s'] for r in index],[False,True])
        self.assertEqual([(r['start_s'],r['end_s']) for r in windows if r['finger']==2],[(0.,15.)])


class Geometry(unittest.TestCase):
    def test_source_parent_relative_flexion_is_global_frame_invariant(self):
        # Bodies: palm, then three segment bodies for each of four fingers.
        state=np.zeros((2,13,13))
        state[...,6]=1.
        angles=np.radians([25.,35.,12.])
        cumulative=np.cumsum(angles)
        for f in range(4):
            state[:,1+f*3:4+f*3,3]=np.sin(cumulative/2)
            state[:,1+f*3:4+f*3,6]=np.cos(cumulative/2)
        # Apply the same nontrivial global rotation to every body in frame1.
        from scipy.spatial.transform import Rotation
        global_rotation=Rotation.from_euler('xyz',[.6,-.4,.8])
        state[1,:,3:7]=(global_rotation*Rotation.from_quat(state[1,:,3:7])).as_quat()
        meta=dict(palm_body_index=0,segment_body_indices=np.arange(1,13).reshape(4,3).tolist())
        output,valid=A.geometric_angles(state,meta)
        self.assertTrue(valid.all())
        np.testing.assert_allclose(output,np.broadcast_to(angles,output.shape),atol=1e-12)
        state[0,2,3:7]=0.
        _,valid=A.geometric_angles(state,meta)
        self.assertFalse(valid[0,0,1])
        self.assertFalse(valid[0,0,2])


if __name__=='__main__':
    unittest.main()
