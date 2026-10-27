import unittest

import numpy as np
from scipy.spatial.transform import Rotation

from stability_adapter_2.palm_position_residual import (
    RatePalmResidual, bounded_delta, source_position_jacobian)


class PalmPositionResidualTests(unittest.TestCase):
    def controller(self, palm=False):
        return RatePalmResidual(np.zeros(24), np.full(24, -.3), np.full(24, .3), palm)

    def test_source_point_derivative_against_rotations(self):
        q = np.zeros(12)
        q[:3] = [.2, -.3, .4]
        native = np.zeros((6, 12))
        native[3:, :3] = np.eye(3)
        r = np.array([.1, .02, -.03])
        actual = source_position_jacobian(native, q, r)
        origin = Rotation.from_rotvec(q[:3]).inv()
        expected = []
        for k in range(3):
            d = np.eye(3)[k]*1e-6
            plus = (Rotation.from_rotvec(q[:3]+d)*origin).apply(r)
            minus = (Rotation.from_rotvec(q[:3]-d)*origin).apply(r)
            expected.append((plus-minus)/2e-6)
        np.testing.assert_allclose(actual[:, :3], np.column_stack(expected), atol=2e-10)
        np.testing.assert_array_equal(actual[:, 3:], 0)

    def test_dense_solution_and_fixed_axes(self):
        matrix = np.array([[2., 1.], [1., -3.], [.05, 0], [0, .05]])
        desired = np.array([.03, -.02, .001, -.001])
        expected = np.linalg.lstsq(matrix, desired, rcond=None)[0]
        result = bounded_delta(matrix, desired, np.full(2, -.15), np.full(2, .15))
        np.testing.assert_allclose(result, expected, atol=1e-12)
        result = bounded_delta(matrix, desired, np.array([.01, -.15]), np.array([.01, .15]))
        expected_y = np.dot(matrix[:, 1], desired-matrix[:, 0]*.01)/np.dot(matrix[:, 1], matrix[:, 1])
        np.testing.assert_allclose(result, [.01, expected_y], atol=1e-12)
        with self.assertRaises(ValueError):
            bounded_delta(matrix, desired, np.ones(2), np.zeros(2))

    def test_rate_cap_global_bounds_and_integral_rollback(self):
        c = self.controller()
        c.upper[0] = .01
        target, record = c.update(np.full(24, -.2), 1/60)
        self.assertEqual(target[0], .01)
        np.testing.assert_allclose(target[1:], .02)
        np.testing.assert_array_equal(c.integral, 0)
        self.assertTrue(all(record['integral_blocked']))
        self.assertLessEqual(len(record['anti_windup_iterations']), 25)
        previous = target.copy()
        for _ in range(12):
            target, record = c.update(np.full(24, -.2), 1/60)
            self.assertLessEqual(np.max(np.abs(target-previous)), .02+1e-12)
            self.assertLessEqual(np.max(np.abs(target)), .15+1e-12)
            previous = target.copy()

    def test_position_objective_and_matched_right_arm(self):
        rate, palm = self.controller(), self.controller(True)
        matrix = np.column_stack([np.eye(3), np.zeros((3, 9))])
        for k in range(6):
            actual = np.full(24, -.003*(k+1))
            rate_target, _ = rate.update(actual, 1/60)
            palm_target, record = palm.update(actual, 1/60, matrix, [.03, -.03, .02])
            np.testing.assert_allclose(palm_target[12:], rate_target[12:], atol=1e-15)
            lo, hi = np.array(record['delta_lower_rad']), np.array(record['delta_upper_rad'])
            pi = np.array(record['delta_PI_rad'])
            feasible_pi = np.clip(pi, lo, hi)
            desired = 2*np.array([.03, -.03, .02])
            pi_error = matrix @ (feasible_pi[:12]-actual[:12])-desired
            pi_objective = np.linalg.norm(pi_error)**2+.05**2*np.linalg.norm(feasible_pi[:12]-pi[:12])**2
            self.assertLessEqual(record['objective'], pi_objective+1e-12)
            masks = [np.array(v['blocked_before']) for v in record['anti_windup_iterations']]
            self.assertTrue(all((~a | b).all() for a, b in zip(masks, masks[1:])))
        with self.assertRaises(ValueError):
            palm.update(np.full(24, np.nan), 1/60, matrix, [0, 0, 0])
        with self.assertRaises(ValueError):
            palm.update(np.zeros(24), 1/60, np.full((3, 12), np.nan), [0, 0, 0])


if __name__ == '__main__':
    unittest.main()
