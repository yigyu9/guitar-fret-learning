"""CPU mathematics/finite codec/witness checks; creates no native scene."""
import math
import unittest

import numpy as np
import torch
from scipy.spatial.transform import Rotation

from driver import inputs
from protocol import schedule,summarize
from guitar_learning.gpu.control import BatchedController
from guitar_learning.tests.test_gpu_control import fake_scene
from guitar_learning.tool.validation.press_acquisition import trajectory_actions
from guitar_learning.tool.experiments.short_finger_learning.wrist import bounded_wrist_target,interpolated_pose
from guitar_learning.gpu.fingertip_pad import pad_target_geometry


class FacingDirectionChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.metadata,cls.protocol,_=inputs()

    def test_sealed_assignments_original_clock_and_finite_goals(self):
        p=self.protocol;n=p['numerical']
        self.assertEqual(len(n['assignments']),16)
        self.assertEqual([sum(x['condition']==k for x in n['assignments']) for k in range(8)],[2]*8)
        self.assertEqual(p['view']['duration_ticks'],218)
        self.assertAlmostEqual(218*4/240,3.6333333333333333)
        f=np.asarray(n['finger_goals_rad']);s=n['selected_action_indices']
        self.assertTrue(np.isfinite(f).all())
        self.assertTrue((f>=np.asarray(n['action_lower_rad'])[s]).all())
        self.assertTrue((f<=np.asarray(n['action_upper_rad'])[s]).all())
        np.testing.assert_array_equal(f[2,[0,2,3]],np.asarray(n['action_lower_rad'])[np.asarray(s)[[0,2,3]]])
        self.assertEqual(f[3,3],n['action_upper_rad'][s[3]])

    def test_schedule_boundaries_and_original_control(self):
        time=torch.tensor([0,1/60,2,2+1/60,2.8,218/60],dtype=torch.float64)
        fraction,clearance=schedule(time,torch.ones(6,dtype=torch.long),torch=torch)
        torch.testing.assert_close(fraction,torch.tensor([0,1/120,1,1,1,1],dtype=torch.float64))
        torch.testing.assert_close(clearance,torch.tensor([.015,.015,.015,.015*(1-1/48),0,0],dtype=torch.float64))
        _,original=schedule(time,torch.zeros(6,dtype=torch.long),torch=torch)
        self.assertTrue(torch.equal(original,torch.zeros_like(time)))
        self.assertTrue(bool((clearance>=0).all() and (clearance<=.015).all()))
        n=self.protocol['numerical'];base=torch.tensor(n['wrist_position_G_m'],dtype=torch.float64)
        initial=base[None]+torch.tensor([[.1,.2,.3]],dtype=torch.float64)
        iq=torch.tensor([[0.,0.,0.,1.]],dtype=torch.float64)
        goal=torch.tensor(n['wrist_goals_G_xyzw'][0],dtype=torch.float64)
        for t in time:
            f,_=schedule(t[None],torch.zeros(1,dtype=torch.long),torch=torch)
            actual=interpolated_pose(initial,iq,base,goal,f)
            expected=interpolated_pose(initial,iq,base,goal,(t[None]/2).clamp(0,1))
            torch.testing.assert_close(actual[0],expected[0]);torch.testing.assert_close(actual[1],expected[1])

    def test_rotations_are_left_composed_in_declared_guitar_axes(self):
        n=self.protocol['numerical'];q=Rotation.from_quat(n['wrist_goals_G_xyzw'])
        np.testing.assert_allclose(np.linalg.norm(n['wrist_goals_G_xyzw'],axis=-1),1,atol=1e-12)
        for k,axis,sign in ((4,n['string_axis_G'],1),(5,n['string_axis_G'],-1),(6,n['cross_axis_G'],1),(7,n['cross_axis_G'],-1)):
            np.testing.assert_allclose((q[k]*q[0].inv()).as_rotvec(),np.asarray(axis)*sign*math.pi/2,atol=1e-12)
        u,v,z=map(np.asarray,(n['string_axis_G'],n['cross_axis_G'],n['plane_normal_G']))
        np.testing.assert_allclose([u@v,u@z,v@z],[0,0,0],atol=1e-12)

    def test_existing_inverse_codec_and_native_finite_rate_at_all_endpoints(self):
        scene,snapshot=fake_scene(num_envs=16)
        controller=BatchedController(scene,finger_action_mode='incremental')
        original={k:v.clone() for k,v in snapshot.items()}
        ref=controller.reference[controller.active];selected=[21,22,23,24]
        goal=ref.repeat(16,1)
        goal[:,selected]=torch.tensor(self.protocol['numerical']['finger_goals_rad'],dtype=ref.dtype).repeat(2,1)
        incremental=torch.zeros(39,dtype=torch.bool);incremental[controller.incremental_actions]=True
        for tick in range(1,219):
            fraction,_=schedule(torch.full((16,),tick/60,dtype=ref.dtype),torch.arange(16)%8,torch=torch)
            desired=ref+fraction[:,None]*(goal-ref)
            old=controller.target[:,controller.active].clone()
            action=trajectory_actions(desired,old,ref,controller.action_low,controller.action_high,incremental,max_speed=4.)
            target=controller.targets(action,snapshot)[:,controller.active]
            self.assertTrue(bool(torch.isfinite(action).all()))
            self.assertTrue(bool((action.abs()<=1).all()))
            self.assertLessEqual(float((target[:,selected]-old[:,selected]).abs().max()),4/60+1e-12)
            self.assertTrue(bool(((target>=controller.action_low)&(target<=controller.action_high)).all()))
        for key,value in original.items():self.assertTrue(torch.equal(snapshot[key],value),key)

    def test_original_wrist_bounds_rate_and_half_degree_correction(self):
        n=self.protocol['numerical'];low=torch.tensor(n['action_lower_rad'][:12],dtype=torch.float64)
        high=torch.tensor(n['action_upper_rad'][:12],dtype=torch.float64)
        base=((low+high)/2).repeat(16,1);previous=base.clone()
        correction=torch.ones_like(base)*100
        jac=torch.eye(6,12,dtype=torch.float64).repeat(16,1,1)
        arm,offset,delta=bounded_wrist_target(base,correction,previous,jac,torch.ones(16,6,dtype=torch.float64)*100,
            torch.ones(16,dtype=torch.bool),low,high,torch.ones(12,dtype=torch.float64)*3)
        self.assertLessEqual(float(delta.abs().max()),math.radians(.5)+1e-12)
        self.assertLessEqual(float((arm-previous).abs().max()),3/60+1e-12)
        self.assertTrue(bool(((arm>=low)&(arm<=high)).all()))

    def test_original_geometry_requires_same_position_and_facing_sample(self):
        # Synthetic CPU mathematics only; never reported as actual native evidence.
        points=torch.zeros(1,4,2,3,dtype=torch.float64);points[...,2]=.001;points[:,:,1,2]=.02
        normals=torch.zeros_like(points);normals[:,:,0,2]=1;normals[:,:,1,2]=-1
        start=torch.zeros(1,6,3,dtype=torch.float64);start[...,1]=-1
        end=start.clone();end[...,1]=1
        result=pad_target_geometry(points,normals,torch.zeros_like(points),torch.ones(4,2,dtype=torch.bool),start,end,
            torch.tensor([[-.1]],dtype=torch.float64),torch.tensor([[.1]],dtype=torch.float64),
            torch.tensor([2]),torch.tensor([2]),torch.ones(1,4,dtype=torch.bool),torch.tensor([0.,0.,1.,0.],dtype=torch.float64))
        self.assertTrue(bool(result['position_geometry'][0,0]))
        self.assertFalse(bool(result['facing_geometry'][0,0]))
        self.assertFalse(bool(result['positive'][0,0]))

    def test_witness_failure_mask_norm_gate_and_conservative_span(self):
        T=14;N=16
        a=dict(first_attempt=np.ones((T,N),bool),failed=np.zeros((T,N),bool),
            clock=np.tile(np.arange(1,T+1)[:,None],(1,N)),local_time_s=np.ones((T,N))*3,
            position_mask=np.ones((T,N,2),bool),facing_mask=np.zeros((T,N,2),bool),
            normal_cos=np.zeros((T,N,2)),orientation_error_rad=np.zeros((T,N)),distal_force_n=np.zeros((T,N,3)))
        a['distal_force_n'][1:,:,0]=-.01  # vector norm, never component sign
        a['failed'][7:,1]=True;a['first_attempt'][1:,2]=False;a['distal_force_n'][:,3]=.001
        a['position_mask'][:,4]=False;a['facing_mask'][:,5]=True
        a['clock'][8:,6]+=1  # missing physical sample cannot count toward span
        episodes={i:dict(reason='timeline_complete',termination=dict(physical_failure=False,wrist_failure=False)) for i in range(N)}
        episodes[1]['termination']['wrist_failure']=True
        rows=summarize(a,episodes,self.protocol)
        self.assertTrue(rows[0]['stable50ms']);self.assertEqual(rows[0]['max_contiguous_samples'],13)
        self.assertFalse(rows[1]['stable50ms']);self.assertTrue(rows[1]['loaded_negative_witness'])
        self.assertFalse(rows[1]['safe_episode_witness'])
        self.assertTrue(rows[1]['loaded_negative_before_failure'])
        self.assertFalse(rows[2]['loaded_negative_witness'])
        self.assertEqual(rows[3]['cause'],'negative_geometry_unloaded')
        self.assertEqual(rows[4]['cause'],'position_not_observed')
        self.assertEqual(rows[5]['cause'],'same_sample_facing_remained')
        self.assertFalse(rows[6]['stable50ms'])
        self.assertIsNone(rows[2]['first_witness'])


if __name__=='__main__':unittest.main(verbosity=2)
