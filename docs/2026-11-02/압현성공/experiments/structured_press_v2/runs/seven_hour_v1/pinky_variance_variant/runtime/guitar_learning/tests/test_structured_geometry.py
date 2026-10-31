"""정렬 후보의 한 표본 공동 판정·관절/몸체 스냅샷 일치·팔 오차 분포 검사."""
import copy
import unittest

import numpy as np
from scipy.spatial.transform import Rotation
from guitar_learning.tool.experiments.structured_geometry import (
    alignment_metrics, perturbation_candidates, snapshot_for_q)


class StructuredGeometryTests(unittest.TestCase):
    def test_same_sample_must_meet_all_alignment_conditions(self):
        points = np.array([[0., 0., .010], [.020, 0., .010]])
        result = alignment_metrics(points, np.array([-.5, .5]), np.zeros(3), np.array([0., 0., 1.]))
        self.assertFalse(result['candidate_valid'])
        result = alignment_metrics(points, np.array([.5, .5]), np.zeros(3), np.array([0., 0., 1.]))
        self.assertTrue(result['candidate_valid'])
        self.assertAlmostEqual(result['height_m'], .010)

    def test_requested_height_changes_selected_sample_without_widening_band(self):
        points = np.array([[0., 0., .010], [0., 0., .014]])
        result = alignment_metrics(points, np.ones(2), np.zeros(3), np.array([0., 0., 1.]), .014)
        self.assertEqual(result['selected_sample'], 1)
        self.assertTrue(result['candidate_valid'])
        self.assertAlmostEqual(result['height_m'], .014)

    def test_snapshot_updates_all_human_bodies_and_preserves_other_actors(self):
        body = dict(pose=dict(p=dict.fromkeys('xyz', 7.), r=dict(x=0., y=0., z=0., w=1.)),
            vel=dict(linear=dict.fromkeys('xyz', 8.), angular=dict.fromkeys('xyz', 9.)))
        state = dict(human_dof_states=[dict(pos=0., vel=3.) for _ in range(105)],
            human_body_states=[copy.deepcopy(body), copy.deepcopy(body)],
            guitar_body_states=[copy.deepcopy(body)], chair_body_states=[copy.deepcopy(body)])
        contract = dict(state=state, initial=dict(human_body_names=['root', 'finger']))
        q = np.zeros(105); q[0] = .2
        def fk(values):
            return dict(root=(np.array([1., 2., 3.]), Rotation.identity()),
                finger=(np.array([values[0], 0., 0.]), Rotation.from_euler('x', values[0])))
        result = snapshot_for_q(contract, q, fk)
        self.assertEqual(result['human_dof_states'][0], dict(pos=.2, vel=0.))
        self.assertEqual(result['human_body_states'][1]['pose']['p']['x'], .2)
        self.assertEqual(result['human_body_states'][0]['vel']['angular']['x'], 0.)
        self.assertEqual(result['guitar_body_states'], state['guitar_body_states'])
        self.assertEqual(result['chair_body_states'], state['chair_body_states'])
        self.assertEqual(state['human_dof_states'][0]['vel'], 3.)

    def test_perturbations_are_joint_reachable_and_report_measured_offsets(self):
        q = np.zeros(105)
        def fk(values):
            return {'L_Wrist': (values[:3], Rotation.from_rotvec(values[3:6]))}
        candidates = perturbation_candidates(fk, q, np.arange(6), -np.ones(6), np.ones(6))
        self.assertEqual(len(candidates), 14)
        for row in candidates:
            self.assertTrue(row['candidate_valid'])
            self.assertFalse(row['native_verified'])
            np.testing.assert_array_equal(row['q105'][6:], q[6:])
            np.testing.assert_allclose(row['actual_position_delta_world_m'], row['q105'][:3])
            self.assertLessEqual(max(abs(np.array(row['actual_position_delta_world_m']))), .010001)


if __name__ == '__main__':
    unittest.main()
