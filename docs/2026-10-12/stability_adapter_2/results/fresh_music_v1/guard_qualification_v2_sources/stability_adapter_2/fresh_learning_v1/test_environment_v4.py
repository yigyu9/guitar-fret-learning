"""Causal validation history and a deliberately inconsistent velocity are rejected."""
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np
from .environment_v4 import aligned_validation_jacobian,ScalarEffortController,JacobianConsistencyError


class AlignmentTests(unittest.TestCase):
    def test_validation_uses_exactly_previous_jacobian(self):
        current,previous = np.ones((1,6,81)),np.zeros((1,6,81))
        validation,step = aligned_validation_jacobian(current,previous,268,267,np.zeros(81))
        self.assertIs(validation,previous)
        self.assertEqual(step,267)
        np.testing.assert_array_equal(current,np.ones((1,6,81)))

    def test_reset_requires_zero_velocity_and_no_history(self):
        current = np.zeros((1,6,81))
        result,step = aligned_validation_jacobian(current,None,0,None,np.zeros(81))
        self.assertIs(result,current)
        with self.assertRaises(RuntimeError): aligned_validation_jacobian(current,None,0,None,np.ones(81))
        with self.assertRaises(RuntimeError): aligned_validation_jacobian(current,current,0,0,np.zeros(81))

    def test_missing_stale_nonfinite_history_fatal(self):
        current = np.zeros((1,6,81))
        for previous,step in [(None,None),(current,265),(np.full_like(current,np.nan),267)]:
            with self.assertRaises(RuntimeError): aligned_validation_jacobian(current,previous,268,step,np.zeros(81))

    def test_inconsistent_native_velocity_still_fatal(self):
        state = {'human_dof_states':[{'pos':0.,'vel':0.} for _ in range(81)],
                 'human_body_states':[{}, {'vel':{'linear':{'x':.02,'y':0.,'z':0.}}}]}
        controller = ScalarEffortController.__new__(ScalarEffortController)
        jac = np.zeros((1,1,6,81))
        controller.tensor = SimpleNamespace(detach=lambda:SimpleNamespace(cpu=lambda:SimpleNamespace(numpy=lambda:jac)))
        controller.previous_jacobian = jac[0].copy()
        controller.previous_jacobian_step = 267
        controller.scene = SimpleNamespace(steps=268,sim=None,human_bodies=['root','test_body'],
            gym=SimpleNamespace(refresh_jacobian_tensors=lambda sim:None))
        modules = {'stability_adapter_2.run_joint_hold':SimpleNamespace(native_state=lambda scene:state),
                   'stability_adapter_2.initial_pose_noise_v1':SimpleNamespace(pose=None),
                   'stability_adapter_2.dual_shoulder_effort_v1':SimpleNamespace(skew=None)}
        with patch.dict(sys.modules,modules),self.assertRaises(JacobianConsistencyError) as caught:
            controller()
        self.assertAlmostEqual(caught.exception.diagnostic['mode_max_errors_m_s']['previous_pose_COM'],.02)
        self.assertFalse(caught.exception.diagnostic['faulting_controller_effort_submitted'])


if __name__=='__main__': unittest.main()
