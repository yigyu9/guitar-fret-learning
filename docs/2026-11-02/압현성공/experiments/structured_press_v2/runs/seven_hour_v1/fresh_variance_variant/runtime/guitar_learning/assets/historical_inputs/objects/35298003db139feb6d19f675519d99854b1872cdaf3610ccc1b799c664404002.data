"""Transforms/boundaries, active assignment and contact-proxy discrimination."""
import unittest
import numpy as np
from scipy.spatial.transform import Rotation
from .live_fret_geometry import pose, position_geometry, assigned_targets, actual_guitar_contacts
from .body_center_coordinates import actor_root_world


def body(p, q): return {'pose': {'p': dict(zip('xyz', p)), 'r': dict(zip('xyzw', q))}}


class GeometryTests(unittest.TestCase):
    def test_rotating_center_does_not_change_root_position_membership(self):
        pel = body([0, -.18, .592], Rotation.from_euler('z', 180, degrees=True).as_quat())
        for rotation in Rotation.random(64, random_state=7):
            row = position_geometry(body([-.4, 0, .75], rotation.as_quat()), pel, rotation, .91)
            self.assertTrue(row['user_position_inside'])
            self.assertFalse(row['rotation_set_evaluated'])
            np.testing.assert_allclose(actor_root_world(row['body_center_W_m'], rotation.as_quat()), [-.4, 0, .75], atol=1e-12)
            roots = actor_root_world(row['user_body_center_box_W_m'], rotation.as_quat())
            np.testing.assert_allclose(roots.min(0), [-.5, -.15, .65], atol=1e-12)
            np.testing.assert_allclose(roots.max(0), [-.15, .15, .91], atol=1e-12)
            self.assertAlmostEqual(row['rotation_change_deg'], 0.)

    def test_outside_corner_and_inclusive_boundary(self):
        pel = body([0, 0, 0], [0, 0, 0, 1]); identity = Rotation.identity()
        row = position_geometry(body([-.51, .17, .92], identity.as_quat()), pel, identity, .91)
        np.testing.assert_allclose(row['user_position_excess_world_axes_m'], [.01, .02, .01], atol=1e-12)
        self.assertAlmostEqual(row['user_position_box_distance_m'], np.sqrt(.0006))
        self.assertFalse(row['user_position_inside'])
        row = position_geometry(body([-.5, .15, .91], identity.as_quat()), pel, identity, .91)
        self.assertTrue(row['user_position_inside'])

    def test_signed_anatomical_axes_and_quaternion_sign(self):
        p = np.array([.2, .3, .8]); q = Rotation.from_euler('xyz', [10, 90, 30], degrees=True).as_quat()
        pel = body([0, 0, 0], Rotation.from_euler('z', 180, degrees=True).as_quat())
        a = position_geometry(body(p, q), pel, Rotation.from_quat(q), 1.)
        b = position_geometry(body(p, -q), pel, Rotation.from_quat(q), 1.)
        np.testing.assert_allclose(a['body_center_W_m'], b['body_center_W_m'])
        c = np.asarray(a['body_center_W_m'])
        np.testing.assert_allclose(a['body_center_pelvis_RFU_m'], c)

    def test_current_goal_assignment_not_nearest_finger(self):
        goal = {'fret': [[3, -1, 5, 0, 2, 4]], 'finger': [[4, 1, 2, 1, 2, 1]], 'barre': [[False]*6]}
        measurement = {'active': [[True, False, True, False, True, True]],
                       'target_world': [[[1, 0, 0]]*6], 'approach_distance': [[.01]*6], 'ready': [[False]*6]}
        tips = [[0, 0, 0], [0, 1, 0], [0, 2, 0], [0, 3, 0]]
        rows = assigned_targets(goal, measurement, tips)
        self.assertEqual([r['finger'] for r in rows], ['pinky', 'middle', 'middle', 'index'])
        self.assertEqual([r['string_index_zero_based'] for r in rows], [0, 2, 4, 5])
        self.assertAlmostEqual(rows[0]['tip_marker_distance_m'], np.sqrt(10))
        self.assertAlmostEqual(rows[0]['one_sided_pad_approach_distance_m'], .01)

    def test_contact_proxy_exclusion_and_pair_order(self):
        pairs = [('guitar/G:body', 'human/LH:thumb3'), ('human/LH:index3', 'guitar/guitar'),
                 ('guitar/G:pluck_range', 'human/LH:index3'), ('human/R_Hip', 'chair/box')]
        rows = [dict(body0_name=a, body1_name=b, **{'lambda': 0.}) for a, b in pairs]
        self.assertEqual(actual_guitar_contacts(rows), rows[:2])


if __name__ == '__main__': unittest.main()
