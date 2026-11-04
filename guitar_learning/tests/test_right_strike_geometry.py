"""CPU source-FK path checks; no simulator and no reachability proof."""
import copy
from pathlib import Path
import unittest

import numpy as np
from scipy.spatial.transform import Rotation

from guitar_learning.runtime.prepared_reset_v1 import load_gpu_prepared_reset_contract
from guitar_learning.tool.experiments.right_strike.geometry import fit_path


class RightStrikeGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = load_gpu_prepared_reset_contract('right')
        names = cls.contract['initial']['guitar_body_names']
        state = cls.contract['state']
        guitar = state['guitar_body_states'][0]['pose']
        p = np.array([guitar['p'][key] for key in 'xyz'])
        r = Rotation.from_quat([guitar['r'][key] for key in 'xyzw'])
        cls.geometry = []
        for suffix in ('', '_end'):
            points = np.array([[state['guitar_body_states'][names.index('G:string%d%s' % (i, suffix))]['pose']['p'][key]
                                for key in 'xyz'] for i in range(1, 7)])
            cls.geometry.append(r.inv().apply(points-p))
        cls.report = fit_path(cls.contract, *cls.geometry)

    def test_prepared_actual_fk_reproduction_and_bounded_right6(self):
        report = self.report
        self.assertEqual(report['waypoint_labels'], ['pre', 'post', 'lift'])
        self.assertEqual(len(report['waypoints_q105']), 3)
        self.assertEqual(len(report['right_indices']), 6)
        self.assertLess(report['reproduction']['pick_position_error_m'], 1e-12)
        self.assertLess(report['reproduction']['max_rotation_error_rad'], 1e-12)
        indices = report['right_indices']
        low, high = np.array(report['action_lower_rad']), np.array(report['action_upper_rad'])
        reference = np.array(report['action_reference_rad'])
        self.assertTrue(np.all(low >= reference-.25))
        self.assertTrue(np.all(high <= reference+.25))
        actual = np.array([row['pos'] for row in self.contract['state']['human_dof_states']])
        fixed = sorted(set(range(105))-set(indices))
        for waypoint in report['waypoints_q105']:
            np.testing.assert_array_equal(np.asarray(waypoint)[fixed], actual[fixed])
            self.assertTrue(np.all(np.asarray(waypoint)[indices] >= low))
            self.assertTrue(np.all(np.asarray(waypoint)[indices] <= high))
        self.assertTrue(all(1 <= row['nfev'] <= 60 for row in report['errors']))

    def test_three_requested_points_have_original_depth_direction_and_lift(self):
        pre, post, lift = [np.array(row['target_G_m']) for row in self.report['errors']]
        self.assertAlmostEqual((pre[1]+post[1])/2, self.report['strike_y_m'], places=12)
        self.assertAlmostEqual(float(np.linalg.norm((post-pre)[:2])), .008, places=12)
        self.assertGreater(post[0], pre[0])
        np.testing.assert_allclose(lift-post, [0., 0., .008], atol=1e-12)
        start, end = self.geometry[0][2], self.geometry[1][2]
        center = start+(self.report['strike_y_m']-start[1])/(end[1]-start[1])*(end-start)
        self.assertAlmostEqual((pre[2]+post[2])/2, center[2]-.004, places=12)

    def test_all_three_declared_y_conditions_are_recorded_and_selection_is_fixed(self):
        report = self.report
        self.assertEqual(report['declared_strike_y_m'], [-.35, -.32, -.29])
        self.assertEqual([row['strike_y_m'] for row in report['attempts']], [-.35, -.32, -.29])
        errors = [row['maximum_position_error_m'] for row in report['attempts']]
        expected = min(range(3), key=lambda index: errors[index])
        self.assertEqual(report['selected_attempt'], expected)
        self.assertEqual(report['waypoints_q105'], report['attempts'][expected]['waypoints_q105'])
        self.assertTrue(all(row['nfev'] <= 60 for attempt in report['attempts'] for row in attempt['errors']))

    def test_unresolved_is_distinct_from_physical_failure_or_success(self):
        report = self.report
        expected = all(row['position_error_m'] <= .001 for row in report['errors'])
        self.assertEqual(report['geometry_candidate'], expected)
        self.assertEqual(report['both_geometry_candidate_only'], expected)
        self.assertEqual(report['outcome'], 'geometry_candidate' if expected else 'finite_search_unresolved')
        self.assertFalse(report['native_verified'])
        self.assertEqual(report['physics_steps_executed'], 0)
        self.assertIn('not impossibility', report['limitation'])

    def test_action_reference_or_native_bound_widening_is_rejected(self):
        for field in ('reference', 'bound'):
            bad = copy.deepcopy(self.contract)
            index = self.report['right_indices'][0]
            if field == 'reference':
                bad['target105'][index] += .01
            else:
                bad['initial']['native_PD_properties']['upper'][index] += 1.
            with self.assertRaises(ValueError):
                fit_path(bad, *self.geometry)

    def test_mismatched_names_geometry_nonfinite_and_quaternion_are_rejected(self):
        bad = copy.deepcopy(self.contract)
        bad['initial']['joint_names'][0:2] = reversed(bad['initial']['joint_names'][0:2])
        with self.assertRaises(ValueError):
            fit_path(bad, *self.geometry)
        bad = copy.deepcopy(self.contract)
        bad['state']['human_body_states'][0]['pose']['r']['w'] = 2.
        with self.assertRaises(ValueError):
            fit_path(bad, *self.geometry)
        bad_geometry = [value.copy() for value in self.geometry]
        bad_geometry[0][2, 0] += .01
        with self.assertRaises(ValueError):
            fit_path(self.contract, *bad_geometry)
        bad_geometry[0][2, 0] = np.nan
        with self.assertRaises(ValueError):
            fit_path(self.contract, *bad_geometry)
        for kwargs in (dict(string_index=True), dict(direction=0)):
            with self.assertRaises(ValueError):
                fit_path(self.contract, *self.geometry, **kwargs)

    def test_source_pin_tampering_is_rejected(self):
        bad = copy.deepcopy(self.contract)
        first = next(iter(bad['source_sha256']))
        bad['source_sha256'][first] = '0'*64
        with self.assertRaises(ValueError):
            fit_path(bad, *self.geometry)

    def test_existing_helper_or_fk_pin_is_never_replaced_by_current_hash(self):
        import guitar_learning.core.control as control
        import guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 as fk
        import guitar_learning.tool.experiments.right_strike.geometry as geometry
        for module in (geometry, fk, control):
            bad = copy.deepcopy(self.contract)
            bad['source_sha256'][str(Path(module.__file__).resolve())] = '0'*64
            with self.assertRaisesRegex(ValueError, 'Existing source SHA expectation'):
                fit_path(bad, *self.geometry)


if __name__ == '__main__':
    unittest.main()
