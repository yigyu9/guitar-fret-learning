"""CPU-only schedule, inverse codec and capture fixtures; no native context."""
from pathlib import Path
import sys
import unittest
import numpy as np
import torch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import probe_multiaxis as probe


class MultiaxisTests(unittest.TestCase):
    def simulate(self,upper=None):
        current=torch.tensor([[.8245,.21845,1.56254,-.18895]]*6,dtype=torch.float64)
        low=current.new_tensor([-.698,-.349,-.698,-.349])
        high=current.new_tensor([1.5708,.349,1.5708,.698]) if upper is None else upper
        original_z=current[torch.arange(6),(torch.arange(6)//3)*2+1].clone()
        history=[current.clone()];actions=[]
        for tick in range(probe.TICKS):
            if tick==285:original_z=current[torch.arange(6),(torch.arange(6)//3)*2+1].clone()
            action=probe.finger_actions(tick,current,original_z)
            current=(current+action*(4./60)).clamp(low,high)
            history.append(current.clone());actions.append(action)
        return torch.stack(history),torch.stack(actions)

    def test_condition_four_seconds_hold_and_nontested_fingers(self):
        history,actions=self.simulate()
        for row,spec in enumerate(probe.case_specs()):
            x=spec['x_axis_index'];z=spec['z_axis_index'];other=[j for j in range(4) if j not in (x,z)]
            self.assertAlmostEqual(history[240,row,x].item(),spec['x_target_rad'],places=12)
            torch.testing.assert_close(history[285:,row,x],history[240,row,x].expand(241),atol=0,rtol=0)
            self.assertLessEqual(actions[:240,row,x].abs().max().item(),.1)
            self.assertEqual(actions[:,row,other].abs().max().item(),0)
            self.assertEqual(actions[240:285,row].abs().max().item(),0)
            self.assertEqual(actions[:285,row,z].abs().max().item(),0)
        self.assertEqual([probe.segment(t) for t in (0,239,240,284,285,344,345,404,405,464,465,524)],
                         [1,1,2,2,3,3,4,4,5,5,6,6])

    def test_z_positive_pulse_full_hold_return_and_posthold(self):
        history,actions=self.simulate()
        for row in range(6):
            z=(row//3)*2+1;origin=history[285,row,z]
            self.assertAlmostEqual((history[345,row,z]-origin).item(),.1,places=12)
            torch.testing.assert_close(history[345:406,row,z],history[345,row,z].expand(61),atol=0,rtol=0)
            torch.testing.assert_close(history[465:,row,z],origin.expand(61),atol=1e-12,rtol=0)
            self.assertGreater(actions[285:345,row,z].min().item(),0)
            self.assertLess(actions[405:465,row,z].max().item(),0)
            self.assertEqual(actions[345:405].abs().max().item(),0)
            self.assertEqual(actions[465:].abs().max().item(),0)

    def test_asymmetric_z_limit_clipping_no_windup_return(self):
        upper=torch.tensor([1.5708,.25,1.5708,-.15],dtype=torch.float64)
        history,actions=self.simulate(upper)
        for row in range(6):
            z=(row//3)*2+1
            self.assertAlmostEqual(history[345,row,z].item(),upper[z].item(),places=12)
            self.assertLess(actions[405,row,z].item(),0)
            self.assertLess(history[406,row,z].item(),history[405,row,z].item())
            self.assertAlmostEqual(history[465,row,z].item(),history[285,row,z].item(),places=12)

    def test_absolute_inverse_codec_holds_asymmetric_zero_span(self):
        ref=torch.linspace(-.2,.2,39,dtype=torch.float64);low=ref-.3;high=ref+.1
        hand=torch.zeros(39,dtype=torch.bool);hand[12:33]=True
        target=ref.repeat(6,1);target[:,0]+=.07;target[:,1]-=.21;target[:,12:33]+=.02
        low[2]=high[2]=ref[2]
        action=probe.absolute_hold_actions(target,ref,low,high,hand)
        request=ref+torch.where(action>=0,high-ref,ref-low)*action
        torch.testing.assert_close((target+.2*(request-target))[:,~hand],target[:,~hand],atol=1e-15,rtol=0)
        self.assertEqual(action[:,hand].abs().max().item(),0)
        target[:,2]+=.01
        with self.assertRaisesRegex(ValueError,'Zero-span'):probe.absolute_hold_actions(target,ref,low,high,hand)

    def test_capture_clock_endpoint_native_target_and_memory(self):
        slow,fast=probe.allocate()
        self.assertLess(sum(a.nbytes for a in (*slow.values(),*fast.values())),80*1024**2)
        for arrays in (slow,fast):
            for a in arrays.values():a.fill(0)
        slow={k:v[:3] for k,v in slow.items()};fast={k:v[:8] for k,v in fast.items()}
        slow['body_state'][...,6]=1;slow['clock'][:]=np.arange(3)[:,None]*4
        slow['global_physics_step'][:]=np.arange(3)*4
        fast['clock'][:]=np.arange(1,9)[:,None];fast['global_physics_step'][:]=np.arange(1,9)
        self.assertTrue(probe.audit_capture(slow,fast,2)['native_endpoint_readback_exact'])
        fast['target'][0,0,1]=.1
        with self.assertRaisesRegex(ValueError,'Within-control'):probe.audit_capture(slow,fast,2)
        self.assertNotIn('isaacgym',sys.modules);self.assertNotIn('mujoco',sys.modules)


if __name__=='__main__':unittest.main(verbosity=2)
