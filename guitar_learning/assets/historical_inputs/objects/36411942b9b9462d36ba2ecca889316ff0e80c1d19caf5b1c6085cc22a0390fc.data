"""Pure CPU counterexamples and pilot timing; no simulator imports."""

import argparse
import hashlib
import json
from pathlib import Path
import time
import unittest

import numpy as np
from scipy.spatial.transform import Rotation

from .deadline_rotation_v3 import BOUNDS_DEG, RotationEnvelope


def quat(euler):
    return Rotation.from_euler('xyz', euler, degrees=True).as_quat()


class RotationTests(unittest.TestCase):
    def setUp(self):
        self.envelope = RotationEnvelope()

    def assert_inside(self, quaternion):
        result = self.envelope.distance(quaternion)
        self.assertTrue(result['inside'])
        self.assertEqual(result['upper_rad'], 0.)
        self.assertEqual(result['lower_rad'], 0.)
        euler = result['nearest_euler_deg']
        self.assertTrue(np.all(np.array(euler) >= BOUNDS_DEG[:, 0]-1e-10))
        self.assertTrue(np.all(np.array(euler) <= BOUNDS_DEG[:, 1]+1e-10))
        error = (Rotation.from_quat(quaternion).inv()*Rotation.from_euler('xyz', euler, degrees=True)).magnitude()
        self.assertLess(error, 1e-11)

    def test_initial_and_quaternion_sign_scale(self):
        initial = np.array([-.5, .5, .5, .5])
        for q in (initial, -initial, 3*initial):
            self.assert_inside(q)
        self.assertLess((Rotation.from_quat(initial).inv()*Rotation.from_quat(quat([67.5, 90, 157.5]))).magnitude(), 1e-14)

    def test_all_box_corners_and_faces(self):
        for x in (45., 67.5, 90.):
            for y in (50., 75., 89.9999, 89.999999, 90., 90.000001, 90.0001, 95., 100.):
                for z in (135., 157.5, 180.):
                    self.assert_inside(quat([x, y, z]))

    def test_both_nonsingular_branches(self):
        for y in (50., 80., 95., 100.):
            q = quat([67., y, 158.])
            self.assert_inside(q)
            self.assert_inside(quat([247., 180.-y, 338.]))

    def test_full_gimbal_family_and_false_positives(self):
        # These representatives have X/Z outside the box but are equivalent
        # to feasible X/Z. A single scipy Euler tuple would reject them.
        for delta in (-135., -90., -45.):
            self.assert_inside(quat([0., 90., -delta]))
        for delta in (-135.00001, -44.99999, 0., 135.):
            self.assertFalse(self.envelope.distance(quat([0., 90., -delta]))['inside'])
        self.assertFalse(self.envelope.distance(quat([67., -90., 158.]))['inside'])

    def test_small_perturbations_on_boundaries(self):
        for axis, edge, delta in ((0, 45., -1e-5), (0, 90., 1e-5),
                                  (1, 50., -1e-5), (1, 100., 1e-5),
                                  (2, 135., -1e-5), (2, 180., 1e-5)):
            euler = np.array([67., 75., 158.])
            euler[axis] = edge
            self.assert_inside(quat(euler))
            euler[axis] += delta
            self.assertFalse(self.envelope.distance(quat(euler))['inside'])
            euler[axis] -= 2*delta
            self.assert_inside(quat(euler))

    def test_random_feasible_and_gimbal_membership(self):
        rng = np.random.default_rng(489)
        eulers = rng.uniform(BOUNDS_DEG[:, 0], BOUNDS_DEG[:, 1], size=(1000, 3))
        eulers[:200, 1] = 90.
        for euler in eulers:
            self.assert_inside(quat(euler))

    def test_heldout_distance_interval_and_candidate(self):
        rng = np.random.default_rng(731)
        fine = RotationEnvelope(grid_step_deg=2.)
        feasible = Rotation.from_euler('xyz', rng.uniform(BOUNDS_DEG[:, 0], BOUNDS_DEG[:, 1], size=(1000, 3)), degrees=True)
        for rotation in Rotation.random(24, random_state=rng):
            result = self.envelope.distance(rotation.as_quat())
            self.assertFalse(result['inside'])
            self.assertLessEqual(result['lower_rad'], result['upper_rad']+1e-12)
            nearest = Rotation.from_quat(result['nearest_quaternion_xyzw'])
            actual = (rotation.inv()*nearest).magnitude()
            self.assertAlmostEqual(result['upper_rad'], actual, places=12)
            self.assert_inside(nearest.as_quat())
            # A lower bound must not exceed any known feasible distance.
            samples = (rotation.inv()*feasible).magnitude()
            self.assertLessEqual(result['lower_rad'], float(np.min(samples))+1e-12)
            refined = fine.distance(rotation.as_quat())
            self.assertLessEqual(result['lower_rad'], refined['upper_rad']+1e-12)
            self.assertLessEqual(refined['lower_rad'], result['upper_rad']+1e-12)
            negated = self.envelope.distance(-rotation.as_quat())
            self.assertAlmostEqual(result['lower_rad'], negated['lower_rad'], places=11)
            self.assertAlmostEqual(result['upper_rad'], negated['upper_rad'], places=6)

    def test_invalid_input(self):
        for q in ([0., 0., 0., 0.], [1., 2.], [np.nan, 0., 0., 1.]):
            with self.assertRaises(ValueError):
                self.envelope.distance(q)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if not args.out.is_dir() or (args.out/'report.json').exists():
        raise ValueError('requires a fresh pre-snapshotted output directory')
    manifest = json.loads((args.out/'attempt.json').read_text())
    expected = manifest['source_sha256']
    if not all(hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest for path, digest in expected.items()):
        raise RuntimeError('source hash differs from pre-execution manifest')
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(RotationTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    envelope = RotationEnvelope()
    rng = np.random.default_rng(602)
    queries = Rotation.random(100, random_state=rng).as_quat()
    durations = []
    intervals = []
    for q in queries:
        start = time.perf_counter()
        intervals.append(envelope.distance(q))
        durations.append(time.perf_counter()-start)
    report = {'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
              'test_output': [{'test': str(test), 'details': details} for test, details in result.failures+result.errors],
              'grid_nodes': len(envelope.grid_euler_deg), 'grid_step_max_deg': 5.,
              'covering_radius_rad': envelope.covering_radius_rad,
              'covering_radius_deg': np.degrees(envelope.covering_radius_rad),
              'membership_so3_roundoff_tolerance_rad': 64*np.finfo(float).eps,
              'distance_exact_certified': False, 'production_gate_complete': False,
              'scope': 'analytical membership; globally conservative grid lower bound and feasible local-fit upper bound',
              'timing_100_calls_ms': {'mean': 1000*float(np.mean(durations)), 'p95': 1000*float(np.percentile(durations, 95)),
                                     'maximum': 1000*float(np.max(durations)), 'total': 1000*float(sum(durations))},
              'maximum_interval_width_rad': max(row['uncertainty_rad'] for row in intervals),
              'sources_unchanged': all(hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest for path, digest in expected.items()),
              'new_native_runs': 0, 'new_training_updates': 0}
    (args.out/'report.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    (args.out/'timing_queries.json').write_text(json.dumps({'quaternion_xyzw': queries.tolist(), 'seconds': durations, 'results': intervals}, indent=2)+'\n')
    print(json.dumps(report, indent=2))
    if not result.wasSuccessful() or not report['sources_unchanged']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
