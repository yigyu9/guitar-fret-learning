"""Actual base pose diagnostics; synthetic tensors are not physics evidence."""
import math
import unittest

import numpy as np
from scipy.spatial.transform import Rotation
import torch

from guitar_learning.tests import test_gpu_environment as fixtures


class FingerBaseRotationTests(unittest.TestCase):
    environment = fixtures.TensorSongTests.environment
    advance = staticmethod(fixtures.TensorSongTests.advance)

    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    @staticmethod
    def pose(env, snapshot, vectors, parent=None):
        parent = Rotation.identity() if parent is None else parent
        snapshot['body_state'][:, env.finger_palm_index, 3:7] = torch.tensor(parent.as_quat()).float()
        for row, vector in enumerate(vectors):
            quaternion = (parent*Rotation.from_rotvec(vector)).as_quat()
            snapshot['body_state'][row, env.finger_base_indices, 3:7] = torch.tensor(quaternion).float()

    @staticmethod
    def values(env, index=0):
        return env._finger_motion_episode(index)['base_rotation']['values']

    def test_actual_pose_detects_rotation_missing_from_two_joint_numbers(self):
        env, snapshot, _ = self.environment()
        snapshot['q'][:, env.finger_base_joints[:, 0]] = .8
        snapshot['q'][:, env.finger_base_joints[:, 1]] = .1
        snapshot['target'].copy_(snapshot['q'])
        self.pose(env, snapshot, [[.8, .12, .1]]*2)
        self.advance(env, snapshot)
        values = self.values(env)
        expected = (Rotation.from_rotvec([.8, .12, .1]).inv()*Rotation.from_rotvec([.8, 0, .1])).as_rotvec()
        self.assertTrue(all(x == 0 for x in env._finger_motion_episode(0)['values']['tracking_error_rms_rad']))
        np.testing.assert_allclose(values['palm_relative_rotvec_y_rms_rad'], .12, atol=2e-7)
        np.testing.assert_allclose(values['zero_y_command_rotation_error_rms_rad'], np.linalg.norm(expected), atol=2e-7)
        np.testing.assert_allclose(values['zero_y_command_local_xz_error_rms_rad'], np.linalg.norm(expected[[0, 2]]), atol=2e-7)

    def test_rms_maximum_and_no_reset_sample(self):
        env, snapshot, _ = self.environment()
        snapshot['target'][:, env.finger_base_joints] = 0
        before = env._finger_motion_episode(0)['base_rotation']
        self.assertEqual(before['endpoint_samples'], 0)
        self.assertTrue(all(x == 0 for value in before['values'].values() for x in value))
        for angle in (.1, -.3):
            self.pose(env, snapshot, [[0, angle, 0]]*2)
            self.advance(env, snapshot)
        row = env._finger_motion_episode(0)['base_rotation']
        self.assertEqual((row['endpoint_samples'], row['sampling_hz']), (2, 60))
        values = row['values']
        np.testing.assert_allclose(values['palm_relative_rotvec_y_rms_rad'], math.sqrt(.05), atol=1e-7)
        np.testing.assert_allclose(values['palm_relative_rotvec_y_max_abs_rad'], .3, atol=1e-7)
        np.testing.assert_allclose(values['zero_y_command_rotation_error_rms_rad'], math.sqrt(.05), atol=1e-7)
        np.testing.assert_allclose(values['zero_y_command_local_xz_error_max_rad'], 0, atol=1e-7)

    def test_world_rotation_and_quaternion_sign_do_not_change_relative_metric(self):
        first, a, _ = self.environment()
        second, b, _ = self.environment()
        vectors = [[.8, .15, -.2]]*2
        self.pose(first, a, vectors)
        self.pose(second, b, vectors, Rotation.from_rotvec([.3, -.5, .7]))
        b['body_state'][:, second.finger_base_indices, 3:7] *= -1
        self.advance(first, a)
        self.advance(second, b)
        for key in self.values(first):
            np.testing.assert_allclose(self.values(first)[key], self.values(second)[key], atol=2e-7)

    def test_partial_reset_clears_only_selected_base_pose_statistics(self):
        env, snapshot, _ = self.environment()
        self.pose(env, snapshot, [[0, .1, 0], [0, .2, 0]])
        self.advance(env, snapshot)
        saved = self.values(env, 1)
        env.reset([0], snapshot)
        self.assertTrue(all(x == 0 for values in self.values(env).values() for x in values))
        self.assertEqual(self.values(env, 1), saved)
        self.assertEqual(env._finger_motion_episode(1)['base_rotation']['endpoint_samples'], 1)

    def test_substep_spike_is_excluded_from_endpoint_maximum(self):
        env, snapshot, _ = self.environment()
        env.begin_control(torch.zeros(2, 39))
        for angle in (.8, -.6, .4, .03):
            self.pose(env, snapshot, [[0, angle, 0]]*2)
            env.substep(snapshot)
        env.end_control()
        np.testing.assert_allclose(self.values(env)['palm_relative_rotvec_y_max_abs_rad'], .03, atol=1e-7)


if __name__ == '__main__':
    unittest.main()
