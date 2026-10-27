"""CPU-only target laws and capture fixtures, never a native/GPU context."""
from pathlib import Path
import sys
import unittest

import numpy as np
import torch

sys.path.insert(0,str(Path(__file__).resolve().parent))
import probe


class RingPinkyTests(unittest.TestCase):
    def simulate(self,low=None,high=None,origin=None,reference=None):
        low=torch.full((8,),-2.,dtype=torch.float64) if low is None else low
        high=torch.full((8,),2.,dtype=torch.float64) if high is None else high
        origin=torch.zeros((18,8),dtype=torch.float64) if origin is None else origin
        reference=torch.zeros(8,dtype=torch.float64) if reference is None else reference
        target=origin.clone();history=[target.clone()];actions=[]
        for tick in range(180):
            action=probe.finger_actions(tick,target,origin,reference)
            target=(target+action*(4./60)).clamp(low,high)
            history.append(target.clone());actions.append(action)
        return torch.stack(history),torch.stack(actions)

    def test_16_pulse_axes_sign_stage_hold_return_and_all_other_axes(self):
        history,action=self.simulate()
        for row in range(16):
            axis=row//2;sign=1 if row%2==0 else -1
            self.assertAlmostEqual(history[60,row,axis].item(),sign*.2,places=12)
            self.assertAlmostEqual(history[90,row,axis].item(),sign*.2,places=12)
            self.assertLess(history[150:,row,axis].abs().max().item(),1e-12)
            other=[i for i in range(8) if i!=axis]
            self.assertEqual(action[:,row,other].abs().max().item(),0)
            self.assertEqual(action[60:90,row].abs().max().item(),0)
            self.assertEqual(action[150:,row].abs().max().item(),0)
        self.assertEqual(history[:,16].abs().max().item(),0)
        self.assertEqual([probe.segment(t,0) for t in (0,59,60,89,90,149,150,179)],[2,2,3,3,4,4,5,5])
        self.assertEqual(probe.segment(0,17),6)
        self.assertEqual([probe.segment(t,16) for t in (0,60,90,179)],[3,3,3,3])
        specs=probe.case_specs();self.assertEqual(len(specs),18)
        self.assertEqual([r['joint'] for r in specs[::2][:8]],list(probe.JOINTS))

    def test_asymmetric_native_clipping_no_room_and_immediate_reverse_no_windup(self):
        low=torch.full((8,),-.02,dtype=torch.float64);high=torch.full((8,),.07,dtype=torch.float64)
        origin=torch.zeros((18,8),dtype=torch.float64);origin[0,0]=high[0]
        history,action=self.simulate(low,high,origin)
        self.assertEqual((history[:91,0,0]-high[0]).abs().max().item(),0)  # Positive request has zero room.
        self.assertAlmostEqual(history[60,1,0].item(),-.02,places=12)
        self.assertGreater(action[90,1,0].item(),0)
        self.assertGreater(history[91,1,0].item(),history[90,1,0].item())
        self.assertLess((history[150:,:16]-origin[:16]).abs().max().item(),1e-12)
        self.assertTrue((history>=low-1e-12).all() and (history<=high+1e-12).all())

    def test_coordinated_return_has_pointwise_speed_cap_no_overshoot_or_forced_full_return(self):
        origin=torch.zeros((18,8),dtype=torch.float64)
        origin[17]=torch.tensor([1.,-.7,.1,-.1,0.,.3,-.2,.6])
        history,action=self.simulate(origin=origin)
        self.assertLessEqual(action[:,17].abs().max().item(),.05)
        expected=origin[17]-(origin[17]).clamp(-.6,.6)
        torch.testing.assert_close(history[-1,17],expected,atol=1e-12,rtol=0)
        self.assertGreater(history[-1,17,0].item(),0)  # 3s cannot restore a1rad offset at0.2rad/s.
        self.assertEqual(history[-1,17,2].item(),0)
        self.assertEqual(history[-1,17,4].item(),0)
        self.assertLessEqual((history[1:,17]-history[:-1,17]).abs().max().item(),.2/60+1e-12)

    def test_absolute_codec_inverse_holds_asymmetric_targets_while_incremental_channels_zero(self):
        reference=torch.linspace(-.2,.2,39,dtype=torch.float64)
        low=reference-.3;high=reference+.1
        hand=torch.zeros(39,dtype=torch.bool);hand[12:33]=True
        target=reference.repeat(18,1)
        target[:,0]+=.07;target[:,1]-=.21;target[:,12:33]+=.02
        low[2]=reference[2];high[2]=reference[2]  # Zero-span channel with no requested offset.
        action=probe.absolute_hold_actions(target,reference,low,high,hand)
        self.assertEqual(action[:,hand].abs().max().item(),0)
        request=reference+torch.where(action>=0,high-reference,reference-low)*action
        next_target=target+.2*(request-target)
        torch.testing.assert_close(next_target[:,~hand],target[:,~hand],atol=1e-15,rtol=0)
        self.assertEqual(action[:,2].abs().max().item(),0)
        bad=target.clone();bad[:,2]+=.001
        with self.assertRaisesRegex(ValueError,'Zero-span'):
            probe.absolute_hold_actions(bad,reference,low,high,hand)

    def test_240hz_and_60hz_capture_clock_and_target_readback(self):
        slow,fast=probe.allocate(2)
        for values in (slow,fast):
            for a in values.values():a.fill(0)
        slow['body_state'][...,6]=1
        slow['clock'][:]=np.arange(3)[:,None]*4;slow['global_physics_step'][:]=slow['clock']
        fast['clock'][:]=np.arange(1,9)[:,None];fast['global_physics_step'][:]=np.arange(1,9)
        proof=probe.audit_capture(slow,fast,2);self.assertTrue(proof['native_endpoint_readback_exact'])
        fast['target'][0,0,0]=.1
        with self.assertRaisesRegex(ValueError,'Within-control'):
            probe.audit_capture(slow,fast,2)
        self.assertNotIn('isaacgym',sys.modules)
        self.assertNotIn('mujoco',sys.modules)

    def test_native_recording_memory_cap(self):
        slow,fast=probe.allocate(780)
        self.assertLess(sum(v.nbytes for v in fast.values()),100*1024**2)
        self.assertLess(sum(v.nbytes for v in (*slow.values(),*fast.values())),220*1024**2)
        self.assertEqual(fast['contact_force_norm'].shape,(3120,18,68))


if __name__=='__main__':unittest.main(verbosity=2)
