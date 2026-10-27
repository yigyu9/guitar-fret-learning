"""Pure strap-law, restricted-force and early-termination discount tests."""
import unittest
from types import SimpleNamespace
import numpy as np
from .deadline_native_v2 import (
    route_law, settlement, StrapForceGuard, REST_LENGTH, GAMMA, REWARD_SCALE)


class StrapPilotContracts(unittest.TestCase):
    def points(self,length):
        points=np.zeros((13,3)); points[:,0]=np.linspace(0,length,13)
        return points

    def test_slack_no_tension_even_positive_rate(self):
        points=self.points(REST_LENGTH-.01); velocity=self.points(100.)
        forces,tension,length,rate=route_law(points,velocity)
        self.assertEqual(tension,0.); self.assertGreater(rate,0.)
        np.testing.assert_array_equal(forces,np.zeros((13,3)))

    def test_original_tension_cap_and_force_reaction(self):
        points=self.points(REST_LENGTH+.01)
        forces,tension,_,_=route_law(points,np.zeros_like(points))
        self.assertAlmostEqual(tension,60.)
        np.testing.assert_allclose(forces.sum(0),0.,atol=1e-12)
        points=self.points(REST_LENGTH+1.)
        forces,tension,_,_=route_law(points,np.zeros_like(points))
        self.assertEqual(tension,300.)
        np.testing.assert_allclose(np.cross(points,forces).sum(0),0.,atol=1e-12)

    def test_curved_route_net_force_and_torque(self):
        x=np.linspace(0,2,13); points=np.c_[x,np.sin(x),np.cos(x)]
        forces,tension,_,_=route_law(points,np.zeros_like(points))
        self.assertEqual(tension,300.)
        np.testing.assert_allclose(forces.sum(0),0.,atol=1e-10)
        np.testing.assert_allclose(np.cross(points,forces).sum(0),0.,atol=1e-10)

    def test_route_measurement_rejects_invalid(self):
        with self.assertRaises(ValueError): route_law(np.zeros((12,3)),np.zeros((12,3)))
        with self.assertRaises(ValueError): route_law(np.full((13,3),np.nan),np.zeros((13,3)))

    def test_normal_floor_and_scale(self):
        scaled,raw,ledger=settlement(-3.)
        self.assertEqual(raw,-2.); self.assertEqual(scaled,-.2)
        self.assertEqual(ledger['floor_adjustment'],1.)
        scaled,raw,ledger=settlement(.5)
        self.assertEqual(scaled,.05); self.assertEqual(ledger['floor_adjustment'],0.)

    def test_fatal_dominates_worst_remaining_rewards(self):
        for remaining in (0,1,16,120,981):
            scaled,raw,ledger=settlement(100.,remaining,True)
            explicit=-2.-2.*sum(GAMMA**k for k in range(1,remaining+1))
            self.assertAlmostEqual(raw,explicit-1.,places=9)
            self.assertLess(scaled,explicit*REWARD_SCALE)
            self.assertEqual(ledger['remaining_ticks'],remaining)

    def guard(self):
        native=SimpleNamespace(apply_body_force_at_pos=lambda *args: True)
        guarded=SimpleNamespace(gym=native, forbidden_property='original guard forwarded')
        owner=SimpleNamespace(integrating_control=True,strap_enabled=True,forbidden_calls=[])
        guard=StrapForceGuard(guarded,owner)
        force=SimpleNamespace(x=1.,y=2.,z=3.); point=SimpleNamespace(x=.1,y=.2,z=.3)
        args=('env',7,force,point,1)
        expected=('env',7,(1.,2.,3.),(.1,.2,.3),1)
        return guard,owner,args,expected

    def test_guard_exact_call_once_only(self):
        guard,owner,args,expected=self.guard()
        guard.arm([expected]); self.assertTrue(guard.apply_body_force_at_pos(*args)); guard.disarm()
        self.assertEqual(guard.allowed_calls,1)
        with self.assertRaises(RuntimeError): guard.apply_body_force_at_pos(*args)
        self.assertEqual(owner.forbidden_calls,['apply_body_force_at_pos'])
        self.assertEqual(guard.forbidden_property,'original guard forwarded')

    def test_guard_wrong_body_force_space_and_window(self):
        for index,value in ((0,'other_env'),(1,8),(2,SimpleNamespace(x=2.,y=2.,z=3.)),(4,2)):
            guard,owner,args,expected=self.guard(); guard.arm([expected])
            changed=list(args); changed[index]=value
            with self.assertRaises(RuntimeError): guard.apply_body_force_at_pos(*changed)
        guard,owner,args,expected=self.guard(); owner.integrating_control=False
        with self.assertRaises(RuntimeError): guard.arm([expected])
        guard,owner,args,expected=self.guard(); owner.strap_enabled=False
        with self.assertRaises(RuntimeError): guard.arm([expected])


if __name__=='__main__': unittest.main()
