"""공통 운반의 초기상태·비팔 고정·매끄러운 경유점·범위 CPU 검사."""
import copy
import importlib.util
from pathlib import Path
import unittest
import torch
spec=importlib.util.spec_from_file_location('transport_runtime',Path(__file__).with_name('transport_runtime.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def fixture():
    q=[0.]*105;goal=q.copy();goal[0]=.2
    catalog=dict(action_indices=list(range(39)),active_names=['L_'+str(i) for i in range(12)]+['other']*27,
        action_lower=[-1.]*39,action_upper=[1.]*39)
    p=dict(wrist_position_G_m=[0.,0.,0.],wrist_quaternion_G_xyzw=[0.,0.,0.,1.])
    row=dict(q105=q,final_hover_q105=goal,transport_waypoints=[dict(p,label='start',q105=q),
        dict(p,label='hover',q105=goal,minimum_duration_s=2.)])
    return catalog,row


class TransportTests(unittest.TestCase):
    def test_frames_and_midpoint_no_state_modification(self):
        catalog,row=fixture();original=copy.deepcopy(row)
        frames=m.make_frames(catalog,row)
        self.assertEqual([f['time_s'] for f in frames],[0.,.5,2.5])
        q,p,r,index=m.sample_frames(frames,1.5)
        self.assertAlmostEqual(float(q[0]),.1,places=6)
        self.assertTrue(torch.equal(q[12:],torch.zeros(93)))
        self.assertEqual(row,original)
        self.assertAlmostEqual(float(torch.linalg.vector_norm(r)),1.,places=6)

    def test_reject_non_arm_or_out_of_bounds(self):
        for kind in ('finger','bounds','start'):
            catalog,row=fixture()
            if kind=='finger':row['transport_waypoints'][-1]['q105'][20]=.1
            elif kind=='bounds':row['transport_waypoints'][-1]['q105'][0]=2.
            else:row['transport_waypoints'][0]['q105']=[.1]*105
            with self.assertRaises(ValueError):m.make_frames(catalog,row)

    def test_rate_duration_and_quaternion_hemisphere(self):
        catalog,row=fixture();row['transport_waypoints'][-1]['minimum_duration_s']=.01
        row['transport_waypoints'][-1]['wrist_quaternion_G_xyzw']=[0.,0.,0.,-1.]
        frames=m.make_frames(catalog,row)
        self.assertGreaterEqual(frames[-1]['time_s']-.5,1.875*.2/3.-1e-7)
        _,_,r,_=m.sample_frames(frames,frames[-1]['time_s'])
        self.assertTrue(torch.allclose(r,torch.tensor([[0.,0.,0.,1.]])))


if __name__=='__main__':unittest.main()
