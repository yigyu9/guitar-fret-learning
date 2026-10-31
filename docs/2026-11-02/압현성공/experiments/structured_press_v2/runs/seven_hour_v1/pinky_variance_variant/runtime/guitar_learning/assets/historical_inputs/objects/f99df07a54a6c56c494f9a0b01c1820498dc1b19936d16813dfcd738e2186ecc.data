"""Safety termination contracts without mocking a successful physical rollout."""
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
from scipy.spatial.transform import Rotation
from .environment_v3 import FreshGuitarEnvironment, JacobianConsistencyError


class ConsistencyTerminationTests(unittest.TestCase):
    def make_env(self,error,velocity=0.,partial_steps=0):
        state = {'human_dof_states':[{'pos':0.,'vel':velocity} for _ in range(81)],
                 'human_body_states':['fixed'],'guitar_body_states':['free']}
        contract = SimpleNamespace(q_ref=np.zeros(81),mid=np.zeros(81),half=np.ones(81),
            clock=lambda step:{'physics_step':step,'physics_time_s':step/240})
        scene = SimpleNamespace(target=np.zeros(81),steps=268,right_effort_calls=268,
                                contract=contract,forbidden_calls=[])
        def step(action):
            scene.steps += partial_steps
            scene.right_effort_calls += partial_steps
            raise error
        scene.step = step
        env = FreshGuitarEnvironment.__new__(FreshGuitarEnvironment)
        env.scene,env.finished = scene,False
        env.indices,env.kept = np.arange(54),np.arange(54,81)
        env.action_lower,env.action_upper = np.full(54,-.035),np.full(54,.035)
        env.initial,env.fixed = state,[0]
        env.initial_gp,env.initial_gr = np.zeros(3),Rotation.identity()
        env.controller = SimpleNamespace(last={'physics_step':267})
        env.config = {'prep_seconds':2.}
        env.horizon = 5.
        env._observe = lambda:np.zeros(558,dtype=np.float32)
        env._palms = env._goal = lambda:np.zeros((2,3))
        env.contact_counts = np.zeros(4)
        modules = {'stability_adapter_2.run_joint_hold':SimpleNamespace(native_state=lambda scene:state),
                   'stability_adapter_2.initial_pose_noise_v1':SimpleNamespace(pose=lambda body:(np.zeros(3),Rotation.identity()))}
        return env,modules

    def test_typed_fault_zero_time_terminal_penalty(self):
        evidence = {'physics_step':268,'threshold_m_s':.01,'faulting_controller_effort_submitted':False}
        env,modules = self.make_env(JacobianConsistencyError('mismatch',evidence))
        with patch.dict(sys.modules,modules):
            obs,reward,cost,terminated,truncated,info = env.step(np.zeros(54))
        self.assertEqual((reward,cost,terminated,truncated),(-1.,1.,True,False))
        self.assertEqual(obs.shape,(558,))
        self.assertEqual(info['transition_physics_steps'],0)
        self.assertEqual(info['transition_effort_submissions'],0)
        self.assertEqual(info['Jacobian_consistency_fault'],evidence)
        self.assertTrue(env.finished)
        with self.assertRaises(RuntimeError): env.step(np.zeros(54))

    def test_partial_control_interval_explicit(self):
        env,modules = self.make_env(JacobianConsistencyError('mismatch',{}),partial_steps=2)
        with patch.dict(sys.modules,modules): result = env.step(np.zeros(54))
        self.assertEqual(result[-1]['transition_physics_steps'],2)
        self.assertEqual(result[-1]['transition_elapsed_s'],2/240)
        self.assertEqual(result[-1]['transition_effort_submissions'],2)

    def test_unsafe_state_is_fatal(self):
        env,modules = self.make_env(JacobianConsistencyError('mismatch',{}),velocity=51.)
        with patch.dict(sys.modules,modules),self.assertRaisesRegex(RuntimeError,'unsafe post-step'):
            env.step(np.zeros(54))

    def test_unrelated_native_error_is_fatal(self):
        env,modules = self.make_env(RuntimeError('native API failed'))
        with patch.dict(sys.modules,modules),self.assertRaisesRegex(RuntimeError,'native API failed'):
            env.step(np.zeros(54))

    def test_nonfinite_body_state_is_fatal(self):
        env,modules = self.make_env(JacobianConsistencyError('mismatch',{}))
        env.initial['guitar_body_states'] = [{'velocity':float('nan')}]
        with patch.dict(sys.modules,modules),self.assertRaisesRegex(RuntimeError,'nonfinite post-step native body'):
            env.step(np.zeros(54))


if __name__=='__main__': unittest.main()
