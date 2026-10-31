"""Meaningful geometry, limit-sign, ABI and timestamp checks on offline diagnostics."""
import unittest

import numpy as np
from scipy.spatial.transform import Rotation as R

from .playing_posture_diagnostic import (
    FRET_V2_BLOCK_SLICES, aligned_observations, joint_margin, posture,
    project, target_markers,
)


class DiagnosticTests(unittest.TestCase):
    def test_horizontal_neck_front_and_quaternion_sign(self):
        guitar = R.from_quat([-.5, .5, .5, .5])
        pelvis = R.from_euler('z', 180, degrees=True)
        a = posture(np.zeros(3), guitar, np.zeros(3), pelvis)
        b = posture(np.zeros(3), R.from_quat(-guitar.as_quat()), np.zeros(3), pelvis)
        self.assertEqual(a, b)
        self.assertAlmostEqual(a['neck_elevation_deg'], 0)
        self.assertAlmostEqual(a['front_angle_to_root_forward_deg'], 0)
        # Rotate about the horizontal neck: neck remains horizontal but front rolls.
        rolled = posture(np.zeros(3), guitar*R.from_euler('y', 50, degrees=True), np.zeros(3), pelvis)
        self.assertAlmostEqual(rolled['neck_elevation_deg'], 0)
        self.assertAlmostEqual(rolled['front_angle_to_root_forward_deg'], 50)

    def test_relative_body_placement_common_rigid_transform(self):
        gp, cp = np.array([.2, .5, .9]), np.array([0, .1, 1.1])
        guitar, pelvis = R.from_euler('xyz', [20, 50, 80], degrees=True), R.identity()
        common = R.from_euler('xyz', [35, -20, 40], degrees=True)
        shift = np.array([2., -4., 3.])
        a = posture(gp, guitar, cp, pelvis)
        b = posture(common.apply(gp)+shift, common*guitar, common.apply(cp)+shift, common*pelvis)
        np.testing.assert_allclose(a['root_minus_chest_right_forward_up_m'], b['root_minus_chest_right_forward_up_m'], atol=1e-14)
        self.assertAlmostEqual(a['front_angle_to_root_forward_deg'], b['front_angle_to_root_forward_deg'])
        # Neck elevation intentionally references world up, not transformed body up.

    def test_signed_limit_exceedance_is_not_clipped(self):
        result = joint_margin([1.2, 0], [-1, -2], [1, 2], ['wrist', 'elbow'], [0, 1])
        self.assertAlmostEqual(result['min_margin_rad'], -.2)
        self.assertAlmostEqual(result['min_fraction'], -.1)
        self.assertEqual(result['joint'], 'wrist')
        self.assertEqual(result['outside_count'], 1)

    def test_saved_abi_active_target_direction_and_units(self):
        obs = np.zeros(420)
        hand = obs[FRET_V2_BLOCK_SLICES['O_hand_geometry']]
        hand[42:45] = [.1, .2, .3]  # ring body marker
        event = obs[FRET_V2_BLOCK_SLICES['O_current_event']]
        event[0] = event[3] = 1
        target = obs[FRET_V2_BLOCK_SLICES['O_target_geometry']]
        target[6:9] = [.003, .004, 0]
        target[14], target[18] = -.002, .006
        target[20:23] = [0, 0, .01]
        markers, wrist = target_markers(obs)
        self.assertEqual(len(markers), 1)
        self.assertEqual(markers[0]['finger'], 'ring')
        np.testing.assert_allclose(markers[0]['target_G_m'], [.103, .204, .3])
        self.assertAlmostEqual(markers[0]['marker_distance_mm'], 5)
        self.assertEqual(markers[0]['signed_press_depth_mm'], -2)
        self.assertEqual(markers[0]['string_lateral_error_mm'], 6)
        self.assertEqual(wrist, 10)

    def test_projection_front_and_behind_camera(self):
        projection = np.zeros((4, 4))
        projection[0, 0] = projection[1, 1] = 1
        projection[2, 3] = -1
        camera = {'view_matrix': np.eye(4), 'projection_matrix': projection}
        pixels, valid = project([[0, 0, -1], [0, 0, 1], [.5, -.5, -1]], camera, 100, 100)
        np.testing.assert_allclose(pixels, [[50, 50], [50, 50], [75, 75]])
        self.assertEqual(valid.tolist(), [True, False, True])

    def test_pre_control_and_terminal_timestamps_stay_distinct(self):
        controls = [{'actor_used': False}, {'actor_used': True, 'time_s': 2.,
                    'observation': [[1]], 'source_done': [True]}]
        result = aligned_observations(controls, {'terminal_observation': [[2]]}, 484)
        self.assertEqual(result[480], ([1], 'pre_integration_observation'))
        self.assertEqual(result[484], ([2], 'terminal_observation'))
        with self.assertRaises(ValueError):
            aligned_observations(controls, {'terminal_observation': [[2]]}, 480)


if __name__ == '__main__':
    unittest.main()
