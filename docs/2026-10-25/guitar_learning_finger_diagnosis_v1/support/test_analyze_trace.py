"""Boundary checks for sampled run durations in the observational analyzer."""
import unittest

import numpy as np

from analyze_trace import run_stats, condition_masks, reward_integrals, require_first_episode


class TraceRunTests(unittest.TestCase):
    def test_empty_and_single_endpoint(self):
        self.assertEqual(run_stats(np.zeros(3, bool), np.arange(1, 4))['count'], 0)
        one = run_stats(np.array([False, True, False]), np.arange(1, 4))
        self.assertEqual(one['count'], 1)
        self.assertEqual(one['max_s'], 1/240)
        self.assertEqual(one['intervals'][0]['first_endpoint_s'], 2/240)
        self.assertEqual(one['intervals'][0]['last_endpoint_s'], 2/240)

    def test_threshold_is_inclusive_and_gaps_break_runs(self):
        mask = np.r_[np.ones(60, bool), False, np.ones(120, bool), False, np.ones(240, bool)]
        result = run_stats(mask, np.arange(1, len(mask)+1))
        self.assertEqual(result['count'], 3)
        self.assertEqual(result['thresholds']['0.25']['count'], 3)
        self.assertEqual(result['thresholds']['0.5']['count'], 2)
        self.assertEqual(result['thresholds']['1.0']['count'], 1)
        self.assertEqual(result['thresholds']['0.5']['total_s'], 1.5)
        self.assertEqual(result['total_s'], 1.75)

    def test_partial_fade_and_overlapping_conditions(self):
        angle = np.array([[15., 10., 60.]]*5)
        gate = np.array([0., .001, .5, .9999, 1.])
        idle = np.ones(5)
        tracking = np.array([False, True, False, True, True])
        pressing = np.array([False, False, True, False, True])
        valid = np.array([True, True, True, True, False])
        m = condition_masks(angle, valid, gate, idle, pressing, tracking, np.arange(5.), 1.)
        np.testing.assert_array_equal(m['actual_standby'], [False,True,True,True,False])
        self.assertFalse(m['full_actual_standby'].any())
        np.testing.assert_array_equal(m['standby_and_tracking'], [False,True,False,True,False])
        # Pressing/tracking/standby are overlapping labels, not a disjoint partition.
        self.assertTrue(m['pressing'][2] and m['actual_standby'][2])
        self.assertTrue(m['pattern_and_tracking'][1] and m['pattern_and_standby'][1])
        self.assertTrue(m['time_idle_but_vetoed'][0])

    def test_failed_tick_excludes_all_four_endpoints(self):
        gate = np.ones((8,4)); quality = np.full((8,4), .5)
        tracking = np.ones((8,4))
        raw, safe, track_safe = reward_integrals(gate, quality, tracking, 'timeline_complete', .7)
        raw_failed, failed, track_failed = reward_integrals(gate, quality, tracking, 'terminal_failure', .7)
        np.testing.assert_array_equal(raw, raw_failed)
        np.testing.assert_allclose(raw, np.full(4,.0025*.5*8/240))
        np.testing.assert_allclose(failed, safe/2)
        self.assertAlmostEqual(track_failed, track_safe/2)
        self.assertAlmostEqual(track_safe, 2*8/240*.7)
        raw_one, weighted_one, tracked_one = reward_integrals(gate[:4], quality[:4], tracking[:4], 'terminal_failure', 1.)
        self.assertGreater(raw_one.sum(), 0)
        self.assertEqual(weighted_one.sum(), 0)
        self.assertEqual(tracked_one, 0)

    def test_first_prefix_rejects_later_reset_or_missing_endpoints(self):
        require_first_episode(np.arange(1,9), 2)
        for clock, steps in [(np.r_[np.arange(1,5), np.arange(1,5)],2),
                             (np.arange(5,13),2), (np.arange(1,8),2)]:
            with self.assertRaises(ValueError):
                require_first_episode(clock, steps)


if __name__ == '__main__':
    unittest.main()
