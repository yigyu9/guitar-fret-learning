"""허용 범위·원본 조건·측정 여유를 검사한다. GPU나 압현 성공을 가정하지 않는다."""
import copy
import json
from pathlib import Path
import sys
import unittest
import tempfile
import native_check
from types import SimpleNamespace
import numpy as np
from scipy.spatial.transform import Rotation
import geometry
import build_inputs

class GeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document=json.loads(build_inputs.DEFAULT.read_text())
        cls.row=next(r for r in cls.document['rows'] if r['case']=='middle_s3_f6')
        cls.planner=geometry.Planner(cls.document['catalog_base'],cls.row)

    def test_joint_axes_intersection_and_nonassigned(self):
        axes,lo,hi=self.planner.preparation_axes(True)
        self.assertEqual(len(axes),16)
        names=self.planner.contract['initial']['joint_names']
        self.assertTrue(all(names[i].startswith('LH:middle') for i in axes[12:]))
        native=self.planner.contract['initial']['native_PD_properties']
        self.assertTrue(np.all(lo>=np.asarray(native['lower'])[axes]))
        self.assertTrue(np.all(hi<=np.asarray(native['upper'])[axes]))
        q,meta=self.planner.endpoint(np.asarray(self.row['transport_waypoints'][-1]['q105']),2,joint_finger=True)
        fixed=np.setdiff1d(np.arange(105),axes)
        np.testing.assert_array_equal(q[fixed],self.planner.q0[fixed])
        self.assertTrue(np.all((q[axes]>=lo)&(q[axes]<=hi)))

    def test_baseline_axes_and_endpoint_preserve_old_rule(self):
        axes,_,_=self.planner.preparation_axes(False)
        self.assertEqual(len(axes),12)
        q,_=self.planner.endpoint(np.asarray(self.row['transport_waypoints'][-1]['q105']),2)
        fixed=np.setdiff1d(np.arange(105),axes)
        np.testing.assert_array_equal(q[fixed],self.planner.q0[fixed])

    def test_path_initial_clearance_contract(self):
        gaps=np.array([.00166254,.003,0.])
        np.testing.assert_allclose(geometry.path_clearance_threshold(gaps,0.),[.00166254,.002,.002])
        halfway=geometry.path_clearance_threshold(gaps,.1)
        self.assertGreater(halfway[0],gaps[0]);self.assertLess(halfway[0],.002)
        np.testing.assert_allclose(geometry.path_clearance_threshold(gaps,.2),[.002]*3)
        np.testing.assert_allclose(geometry.path_clearance_threshold(gaps,1.),[.002]*3)
        with self.assertRaises(ValueError):geometry.path_clearance_threshold(np.array([-.0001]),0.)

    def test_zero_length_route_still_requires_final_clearance(self):
        progress=geometry.joint_path_progress([np.zeros(105),np.zeros(105)])
        np.testing.assert_array_equal(progress,[0.,1.])
        self.assertAlmostEqual(geometry.path_clearance_threshold(np.array([.00166]),progress[-1])[0],.002)
        np.testing.assert_array_equal(geometry.joint_path_progress([np.zeros(105)]),[1.])

    def test_path_rejects_other_finger_and_bounds(self):
        q=self.planner.q0.copy();q[56]+=.1
        with self.assertRaises(ValueError):self.planner.path(q,2,joint_finger=True)
        axes,lo,hi=self.planner.preparation_axes(True)
        q=self.planner.q0.copy();q[axes[0]]=hi[0]+.1
        with self.assertRaises(ValueError):self.planner.path(q,2,joint_finger=True)

    def test_margin_uses_one_eligible_sample(self):
        # 첫 점의 위치 여유가 커도 방향이 부적합하면 모든 조건을 만족하는 두 번째 점을 선택한다.
        points=np.array([[0.,.5,0.],[0.,.5,0.]])
        result=geometry.contact_margin(points,np.array([.001,.001]),np.array([0.,.001]),np.array([0.,.8]),0.,1.,np.array([False,True]))
        self.assertEqual(result['margin_sample_index'],1)
        self.assertTrue(result['margin_sample_valid'])
        self.assertGreater(result['contact_margin_normalized'],0)
        self.assertAlmostEqual(result['contact_margin_m'],.002)

    def test_joint_limit_margin(self):
        result=geometry.joint_margin(np.array([0.,1.]),np.array([-1.,0.]),np.array([1.,2.]))
        self.assertAlmostEqual(result['joint_margin_normalized'],1.)
        result=geometry.joint_margin(np.array([1.,1.]),np.array([-1.,0.]),np.array([1.,2.]))
        self.assertEqual(result['joint_margin_normalized'],0.)

    def test_candidate_selection_single_change(self):
        candidates=[dict(geometry_candidate=True,finger4_rad=[.1]*4,robust_score=.1,target_error_m=0.),
                    dict(geometry_candidate=True,finger4_rad=[.3]*4,robust_score=.4,target_error_m=.0001)]
        self.assertEqual(geometry.choose_press_candidate(candidates,np.zeros(105),[0,1,2,3]),0)
        self.assertEqual(geometry.choose_press_candidate(candidates,np.zeros(105),[0,1,2,3],robust=True),1)
        self.assertEqual(geometry.select_robust_candidate(dict(candidates=candidates)),1)
        candidates[1]['geometry_candidate']=False
        self.assertEqual(geometry.choose_press_candidate(candidates,np.zeros(105),[0,1,2,3],robust=True),0)

    def test_baseline_press_candidates_reproduce_saved_values(self):
        base=build_inputs.DEFAULT.parent/'middle_s3_f6/attempt01'
        arrival=json.loads((base/'arrival.json').read_text())
        old=json.loads((base/'press_candidates.json').read_text())
        native=self.planner.contract['initial']['native_PD_properties']
        new=geometry.press_candidates(self.planner,arrival['state'],arrival['q105'],native['lower'],native['upper'])
        self.assertEqual(new['indices'],old['indices'])
        self.assertEqual(len(new['candidates']),len(old['candidates']))
        for actual,expected in zip(new['candidates'],old['candidates']):
            self.assertEqual(actual['geometry_candidate'],expected['geometry_candidate'])
            np.testing.assert_allclose(actual['q105'],expected['q105'],atol=1e-10,rtol=0)
        self.assertAlmostEqual(new['fk_reproduction_position_error_m'],old['fk_reproduction_position_error_m'])

    def test_pad_jacobian_predicts_small_motion(self):
        from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
        p=self.planner;q=p.q0.copy();state=p.contract['state'];result=geometry.pad_geometry_jacobian(p,state,q,0)
        J=np.asarray(result['point_jacobian_G_m_per_rad']);self.assertEqual(J.shape,(3,4));self.assertTrue(np.isfinite(J).all())
        fk=full_fk(SimpleNamespace(names=p.contract['initial']['joint_names'],human_bodies=p.contract['initial']['human_body_names'],q_ref=q),state)
        local=p.pad['points_local'][p.finger][p.pad['valid'][p.finger]][0]
        body='LH:middle3';delta=np.array([1e-5,-2e-5,1e-5,2e-5]);trial=q.copy();trial[result['indices']]+=delta
        gp=state['guitar_body_states'][0]['pose'];pos=np.array([gp['p'][a] for a in 'xyz']);rot=Rotation.from_quat([gp['r'][a] for a in 'xyzw'])
        translation,orientation=fk(trial)[body]
        actual=rot.inv().apply(translation+orientation.apply(local)-pos)
        predicted=np.asarray(result['point_G_m'])+J@delta
        np.testing.assert_allclose(actual,predicted,atol=1e-8,rtol=0)

class RuntimeTests(unittest.TestCase):
    def test_baseline_and_feedback_safety_contracts(self):
        native_check.self_test()

    def test_condition_identity_and_input_preservation(self):
        original=build_inputs.DEFAULT.read_bytes()
        root=Path(__file__).resolve().parents[1]/'검증'
        with tempfile.TemporaryDirectory(dir=str(root)) as folder:
            folder=Path(folder)
            document=build_inputs.generate(build_inputs.DEFAULT,'middle_s3_f6','baseline',folder/'built')
            self.assertEqual(document['catalog_base']['diagnostic_condition'],'baseline')
            self.assertEqual(document['rows'][0]['diagnostic_condition'],'baseline')
            source=json.loads(original)
            old=next(r for r in source['rows'] if r['case']=='middle_s3_f6')
            self.assertEqual(document['rows'][0]['transport_waypoints'],old['transport_waypoints'])
            args=SimpleNamespace(catalog=None,geometry=folder/'built/geometry.json',case='middle_s3_f6',provenance=None)
            output=folder/'runtime';output.mkdir()
            path,catalog,row,_=native_check.make_inputs(args,output)
            self.assertEqual(catalog['diagnostic_condition'],'baseline')
            self.assertEqual(row['q105'],old['transport_waypoints'][0]['q105'])
            settings,config=native_check.settings_for(path,row,7,'baseline')
            self.assertEqual(config['diagnostic_condition'],'baseline')
            self.assertEqual(settings['num_envs'],1)
            self.assertEqual(build_inputs.DEFAULT.read_bytes(),original)

if __name__=='__main__':unittest.main()
