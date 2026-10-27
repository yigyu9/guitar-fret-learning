"""Pure CPU command/clock fixtures; never import Isaac Gym or create GL contexts."""
import importlib.util
from pathlib import Path
import unittest
import numpy as np

HERE=Path(__file__).resolve().parent


def load(name):
    spec=importlib.util.spec_from_file_location(name,HERE/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


probe=load('probe_joint_distribution')
render=load('render_joint_distribution')


class JointDistributionTests(unittest.TestCase):
    def setUp(self):
        self.low=np.tile(np.deg2rad([-40,-30,0,-5]),4)
        self.high=np.tile(np.deg2rad([90.0002,40,90.0002,90.0002]),4)

    def test_exact_predeclared_goals_and_bounds(self):
        goal=probe.goals_rad()
        np.testing.assert_allclose(np.rad2deg(goal).reshape(4,4,4),np.repeat(np.array([
            [0,0,0,90],[40,0,55,35],[30,0,30,15],[0,0,0,0]])[:,None],4,axis=1),atol=1e-12)
        current=goal.copy();np.testing.assert_array_equal(probe.command_actions(current,goal,self.low,self.high),0)
        np.testing.assert_array_equal(current,goal)

    def test_one_tick_inverse_and_saturation(self):
        goals=probe.goals_rad();current=np.clip(goals+.02,self.low,self.high)
        action=probe.command_actions(current,goals,self.low,self.high)
        np.testing.assert_allclose(current+action*4/60,goals,atol=1e-15)
        current=goals.copy();current[0,3]=0
        action=probe.command_actions(current,goals,self.low,self.high)
        self.assertEqual(action[0,3],1)
        self.assertTrue((np.abs(action)<=1).all())

    def test_invalid_goals_rejected(self):
        goal=probe.goals_rad();bad=goal.copy();bad[0,3]=2
        with self.assertRaises(ValueError):probe.command_actions(goal,bad,self.low,self.high)
        bad=goal.copy();bad[0,0]=np.nan
        with self.assertRaises(ValueError):probe.command_actions(goal,bad,self.low,self.high)

    def test_t0_excluded_and_censored_clock_not_stretched(self):
        for ticks in (1,37,180):
            clock=np.repeat((np.arange(ticks+1)*4)[:,None],4,axis=1)
            self.assertEqual(list(render.video_indices(clock)),list(range(1,ticks+1)))
        clock[3,1]+=1
        with self.assertRaises(ValueError):render.video_indices(clock)


if __name__=='__main__':unittest.main()
