"""CPU contracts for the diagnostic; physical feasibility needs actual GPU replay."""
import unittest
from types import SimpleNamespace

import numpy as np
import torch
from scipy.spatial.transform import Rotation

from guitar_learning.core.control import ACTIVE_NAMES
from guitar_learning.tool.validation.press_acquisition import (
    DEFAULT_BUNDLE, REPRESENTATIVE_ROWS, action_bounds, diagnostic_streak,
    goal_measurement, integral_tracking_offset, pad_axis_flags, select_targets,
    source_geometry, trajectory_actions)


class PressAcquisitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from guitar_learning.song.task import make_task
        from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract
        cls.task = make_task(DEFAULT_BUNDLE)
        cls.contract = load_prepared_reset_contract()

    def test_representatives_are_unique_source_goals_with_frequency_and_extremes(self):
        rows = select_targets(self.task)
        self.assertEqual(len(rows), 16)
        self.assertEqual(REPRESENTATIVE_ROWS, (0, 4, 8, 12))
        self.assertEqual(rows, select_targets(self.task))
        for finger in range(1, 5):
            chosen = [row for row in rows if row['finger'] == finger]
            originals = [t for t in self.task.targets if t.finger == finger]
            self.assertEqual(len({(r['string'], r['fret']) for r in chosen}), 4)
            self.assertEqual(min(r['fret'] for r in chosen), min(t.fret for t in originals))
            self.assertEqual(max(r['fret'] for r in chosen), max(t.fret for t in originals))
            for row in chosen:
                target = self.task.targets[row['source_note_index']]
                self.assertEqual((target.string, target.fret, target.finger),
                                 (row['string'], row['fret'], row['finger']))

    def codec(self):
        active, low, high = action_bounds(self.contract)
        ref = torch.tensor(np.asarray(self.contract['target105'])[active])
        return ref, torch.tensor(low), torch.tensor(high), torch.tensor([n.startswith('LH:') for n in ACTIVE_NAMES])

    def test_hold_is_zero_incremental_and_exact_inverse_for_absolute_channels(self):
        ref, low, high, incremental = self.codec()
        desired = (low*.2+high*.8).expand(3, -1).clone()
        action = trajectory_actions(desired, desired, ref, low, high, incremental)
        self.assertTrue(torch.equal(action[:, incremental], torch.zeros_like(action[:, incremental])))
        decoded = ref+torch.where(action >= 0, high-ref, ref-low)*action
        self.assertTrue(torch.allclose(decoded[:, ~incremental], desired[:, ~incremental], atol=1e-12, rtol=0))

    def test_incremental_reads_previous_clamped_target_and_limits_requested_speed(self):
        ref, low, high, incremental = self.codec()
        current = ref.expand(2, -1).clone()
        desired = torch.stack((high, low))
        action = trajectory_actions(desired, current, ref, low, high, incremental, max_speed=.8)
        self.assertLessEqual(float(action[:, incremental].abs().max()), .2)
        delta = action[:, incremental]*(4/60)
        self.assertLessEqual(float(delta.abs().max()), .8/60+1e-15)
        # Near the goal the existing incremental controller lands exactly.
        desired = current.clone(); desired[:, incremental] += .0001
        near = trajectory_actions(desired, current, ref, low, high, incremental)
        self.assertTrue(torch.allclose(current[:, incremental]+near[:, incremental]*(4/60), desired[:, incremental]))

    def test_codec_rejects_out_of_bounds_and_nonfinite_requests(self):
        ref, low, high, incremental = self.codec()
        desired = ref[None].clone(); desired[0, 0] = high[0]+.01
        with self.assertRaises(ValueError):
            trajectory_actions(desired, ref[None], ref, low, high, incremental)
        desired = ref[None].clone(); desired[0, 0] = float('nan')
        with self.assertRaises(ValueError):
            trajectory_actions(desired, ref[None], ref, low, high, incremental)

    def test_both_endpoints_and_longest_uninterrupted_contact(self):
        streak = np.zeros(2); best = np.zeros(2)
        previous = np.array([False, True])
        for _ in range(24):
            current = np.array([True, True])
            streak, best = diagnostic_streak(previous, current, streak, best)
            previous = current
        self.assertAlmostEqual(best[0], 23/240)
        self.assertAlmostEqual(best[1], .1)
        streak, best = diagnostic_streak(previous, np.array([False, False]), streak, best)
        self.assertTrue(np.array_equal(streak, [0, 0]))
        old = best.copy()
        previous[:] = False
        for _ in range(10):
            current[:] = True
            streak, best = diagnostic_streak(previous, current, streak, best)
            previous = current.copy()
        np.testing.assert_array_equal(best, old)

    def test_axis_lateral_is_on_press_plane_not_virtual_string_height(self):
        starts = torch.zeros(3, 6, 3, dtype=torch.float64)
        starts[..., 1] = -.5; starts[..., 2] = .0123
        ends = starts.clone(); ends[..., 1] = .5
        plane = torch.tensor([0, 0, 1, -.0093], dtype=torch.float64)
        # All are one millimetre above the press plane. The third is off-string.
        points = torch.tensor([[[0, 0, .0103]], [[.0029, 0, .0103]],
                               [[.0031, 0, .0103]]], dtype=torch.float64)
        result = pad_axis_flags(points, starts, ends, torch.zeros(3, dtype=torch.long),
                                torch.full((3,), -.1), torch.full((3,), .1), plane)
        self.assertEqual(result['lateral'].tolist(), [True, True, False])
        self.assertEqual(result['cell'].tolist(), [True]*3)
        self.assertEqual(result['height'].tolist(), [True]*3)
        # Moving only the virtual string up does not change pad-plane diagnostics.
        starts[..., 2] += .05; ends[..., 2] += .05
        moved = pad_axis_flags(points, starts, ends, torch.zeros(3, dtype=torch.long),
                               torch.full((3,), -.1), torch.full((3,), .1), plane)
        self.assertTrue(torch.equal(moved['lateral'], result['lateral']))

    def test_report_keeps_source_and_physical_distances_without_duplicate_keywords(self):
        source = dict(row=0, minimum_distance_m=.001, geometry_candidate=True)
        report = goal_measurement(source, minimum_distance_m=.02, accepted_physics_samples=40)
        self.assertEqual(report['source_geometry_minimum_distance_m'], .001)
        self.assertEqual(report['minimum_distance_m'], .02)
        self.assertEqual(source['minimum_distance_m'], .001)
        self.assertTrue(report['geometry_candidate'])

    def test_outer_feedback_is_slow_masked_and_does_not_mutate_inputs(self):
        offset = torch.zeros(2, 39)
        nominal = torch.full_like(offset, .03)
        actual = torch.zeros_like(offset)
        mask = torch.zeros_like(offset, dtype=torch.bool); mask[:, :2] = True
        result = integral_tracking_offset(offset, nominal, actual, -torch.ones(39), torch.ones(39), mask)
        self.assertTrue(torch.allclose(result[:, :2], torch.full((2, 2), .03*1.5/60)))
        self.assertEqual(float(result[:, 2:].abs().max()), 0.)
        self.assertEqual(float(offset.abs().max()), 0.)
        self.assertEqual(float(actual.abs().max()), 0.)

    def test_outer_feedback_target_saturation_has_no_hidden_windup_and_reverses(self):
        nominal = torch.full((1, 39), .98, dtype=torch.float64)
        low, high = -torch.ones(39, dtype=torch.float64), torch.ones(39, dtype=torch.float64)
        offset = torch.zeros_like(nominal)
        actual = torch.zeros_like(nominal)
        mask = torch.ones_like(nominal, dtype=torch.bool)
        for _ in range(100):
            offset = integral_tracking_offset(offset, nominal, actual, low, high, mask)
        self.assertTrue(torch.allclose(offset, torch.full_like(offset, .02), atol=1e-12, rtol=0))
        reversed_offset = integral_tracking_offset(offset, nominal, torch.full_like(actual, 1.1), low, high, mask)
        self.assertTrue(bool((reversed_offset < offset).all()))
        # A wide action range is still limited by the separate0.1rad offset cap.
        capped = integral_tracking_offset(torch.full_like(offset, .099), torch.zeros_like(nominal),
            -torch.ones_like(actual), low, high, mask)
        self.assertTrue(torch.allclose(capped, torch.full_like(capped, .1)))
        action = trajectory_actions(nominal+offset, nominal, torch.zeros(39, dtype=torch.float64),
                                    low, high, mask[0])
        self.assertLessEqual(float(action.abs().max()), 1.)

    def test_current_source_fk_is_calibrated_to_actual_prepared_state(self):
        from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
        initial, state = self.contract['initial'], self.contract['state']
        q = np.array([r['pos'] for r in state['human_dof_states']])
        scene = SimpleNamespace(names=initial['joint_names'], human_bodies=initial['human_body_names'], q_ref=q)
        predicted = full_fk(scene, state)(q)
        for name, body in zip(initial['human_body_names'], state['human_body_states']):
            p, r = predicted[name]
            np.testing.assert_allclose(p, [body['pose']['p'][a] for a in 'xyz'], atol=1e-12, rtol=0)
            saved = Rotation.from_quat([body['pose']['r'][a] for a in 'xyzw'])
            self.assertLess(float((saved.inv()*r).magnitude()), 1e-12)

    def test_actual_source_targets_are_in_current_plane_and_action_ranges_are_native(self):
        rows = select_targets(self.task)
        starts, ends, low, high, plane, surface = source_geometry(self.contract, rows)
        self.assertEqual(surface['target_validation']['target_count'], 16)
        np.testing.assert_allclose(starts@plane[:3]+plane[3], 0, atol=1e-12)
        np.testing.assert_allclose(ends@plane[:3]+plane[3], 0, atol=1e-12)
        self.assertTrue((high-low > .004).all())
        active, lo, hi = action_bounds(self.contract)
        initial = self.contract['initial']['native_PD_properties']
        ref = np.asarray(self.contract['target105'])[active]
        self.assertTrue((lo >= np.asarray(initial['lower'])[active]).all())
        self.assertTrue((hi <= np.asarray(initial['upper'])[active]).all())
        self.assertTrue(((ref >= lo) & (ref <= hi)).all())


if __name__ == '__main__':
    unittest.main()
