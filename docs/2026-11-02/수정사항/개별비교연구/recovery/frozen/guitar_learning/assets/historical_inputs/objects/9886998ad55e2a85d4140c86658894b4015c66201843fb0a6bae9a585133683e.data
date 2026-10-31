"""Pure measured-geometry quality tests; no native simulation or sound claims."""
import copy
import unittest
import numpy as np
from scipy.spatial.transform import Rotation
from guitar_learning.geometry_v1 import world_to_guitar
from guitar_learning.music_task import ScoreTarget
from guitar_learning.strike import StrikeDetector
from guitar_learning.strike_quality import StrikeQualityDetector, STRIKE_QUALITY_METADATA
from guitar_learning.tests.test_strike import geometry


def target(direction=1, string=0):
    return ScoreTarget('t', 'e', string, 5, 1, direction, 1., 2., .9, 1., 2.)


def sample(step, x, y=-.32, z=-.002): return geometry(step, [x, y, z])


class StrikeQualityTests(unittest.TestCase):
    def ready(self, detector, direction=1):
        x = -.004*direction
        result = detector.update(sample(0, x), sample(1, x))
        self.assertTrue(result['quality']['ready'])
        self.assertAlmostEqual(result['quality']['ready_dwell_s'], 1/240.)

    def test_requires_two_prior_observations_without_retroactive_readiness(self):
        d = StrikeQualityDetector(target())
        result = d.update(sample(0, -.004), sample(1, .004))
        self.assertFalse(result['events'])
        self.assertTrue(result['candidates'][0]['valid'])
        self.assertEqual(d.summary()['unprepared_count'], 1)
        self.assertEqual(d.summary()['blocked_reasons'], {'1:1': ['unprepared_matching_crossing']})
        self.assertFalse(d.summary()['ready'])
        d.reset()
        self.ready(d)
        result = d.update(sample(1, -.004), sample(2, .004))
        self.assertEqual([e['crossing_id'] for e in result['events']], ['2:1'])
        self.assertEqual(d.summary()['accepted_crossing_ids'], ['2:1'])
        self.assertFalse(d.summary()['recovered'])

    def test_departure_side_depth_zone_and_real_three_mm_separation(self):
        for x,y,z in ((.004,-.32,-.002),(-.002,-.32,-.004),(-.004,-.1,-.002),
                      (-.004,-.32,.002),(-.004,-.32,-.02)):
            d = StrikeQualityDetector(target())
            d.update(sample(0,x,y,z), sample(1,x,y,z))
            self.assertFalse(d.summary()['ready'], (x,y,z))
        d = StrikeQualityDetector(target())
        d.update(sample(0,-.004), sample(1,-.001))
        self.assertFalse(d.summary()['ready'])
        self.assertEqual(d.summary()['ready_dwell_s'], 0.)

    def test_ready_is_latched_during_approach_but_recovery_is_current(self):
        d = StrikeQualityDetector(target())
        self.ready(d)
        d.update(sample(1,-.004), sample(2,-.001))
        self.assertTrue(d.summary()['ready'])
        result = d.update(sample(2,-.001), sample(3,.004))
        self.assertEqual([e['crossing_id'] for e in result['events']], ['3:1'])
        d.update(sample(3,.004), sample(4,.004))
        self.assertFalse(d.summary()['recovered'])
        d.update(sample(4,.004), sample(5,.004))
        self.assertTrue(d.summary()['recovered'])
        self.assertAlmostEqual(d.summary()['recovery_dwell_s'], 1/240.)
        d.update(sample(5,.004), sample(6,.001))
        self.assertFalse(d.summary()['recovered'])
        self.assertEqual(d.summary()['recovery_dwell_s'], 0.)
        self.assertTrue(d.summary()['ever_recovered'])

    def test_upstroke_departure_side_and_wrong_direction_remains_native_event(self):
        d = StrikeQualityDetector(target(-1))
        self.ready(d, -1)
        result = d.update(sample(1,.004), sample(2,-.004))
        self.assertEqual([e['direction'] for e in result['events']], [-1])
        wrong = StrikeQualityDetector(target(-1))
        result = wrong.update(sample(0,-.004), sample(1,.004))
        self.assertEqual([e['direction'] for e in result['events']], [1])
        self.assertEqual(wrong.summary()['counts']['wrong_native_eligible'], 1)
        self.assertEqual(wrong.summary()['unprepared_count'], 0)

    def test_wrong_string_kept_and_second_matching_event_blocked_as_extra(self):
        wrong = StrikeQualityDetector(target(string=1))
        result = wrong.update(sample(0,-.004), sample(1,.004))
        self.assertEqual([e['string_number'] for e in result['events']], [1])
        self.assertEqual(wrong.summary()['counts']['wrong_native_eligible'], 1)
        d = StrikeQualityDetector(target()); self.ready(d)
        positions = {1:-.004,2:.004,3:.004,4:.004,5:-.004,6:-.004,7:-.004,8:.004}
        for step in range(2,9):
            result = d.update(sample(step-1,positions[step-1]), sample(step,positions[step]))
            if step == 5: self.assertEqual(len(result['events']), 1)  # wrong direction once
        self.assertFalse(result['events'])
        self.assertTrue(result['candidates'][0]['valid'])
        self.assertEqual(d.summary()['extra_crossing_ids'], ['8:1'])
        self.assertEqual(d.summary()['accepted_crossing_ids'], ['2:1'])

    def test_wait_rearm_only_matching_repeat_is_extra_without_duplicate_timing_event(self):
        d = StrikeQualityDetector(target()); self.ready(d)
        d.update(sample(1,-.004),sample(2,.004))
        d.update(sample(2,.004),sample(3,-.004))
        result = d.update(sample(3,-.004),sample(4,.004))
        self.assertFalse(result['events'])
        self.assertEqual(result['candidates'][0]['reason_flags'], ['wait_rearm'])
        self.assertEqual(d.summary()['extra_count'], 1)
        self.assertEqual(d.summary()['blocked_reasons']['4:1'], ['wait_rearm','extra_matching_crossing'])
        self.assertEqual(d.summary()['counts']['native_eligible'], 1)

    def test_lifted_or_other_ineligible_xy_passages_are_diagnostic_not_extra_or_wrong(self):
        for y,z in ((-.32,.01),(-.32,-.1),(-.39,-.002)):
            d = StrikeQualityDetector(target()); self.ready(d)
            d.update(sample(1,-.004),sample(2,.004))
            # Stay on the departure side while moving to an invalid depth/zone,
            # then make two XY passages during the original wait-rearm period.
            d.update(sample(2,.004),sample(3,.004,y,z))
            result = d.update(sample(3,.004,y,z),sample(4,-.004,y,z))
            self.assertFalse(result['events'])
            self.assertTrue(result['candidates'])
            self.assertEqual(d.summary()['extra_count'], 0)
            self.assertEqual(d.summary()['counts']['wrong_native_eligible'], 0)
            self.assertFalse(d.summary()['blocked_event_ids'])
            self.assertEqual(d.summary()['counts']['diagnostic_ineligible'], 1)

    def test_original_candidates_proxies_reset_unique_clock_and_private_summaries(self):
        d = StrikeQualityDetector(target()); original = StrikeDetector()
        a,b = sample(0,-.004),sample(1,.004)
        expected = original.update(a,b); actual = d.update(a,b)
        self.assertEqual(actual['candidates'], expected['candidates'])
        self.assertEqual(d.contract, original.contract)
        np.testing.assert_array_equal(d.armed, original.armed)
        np.testing.assert_array_equal(d.last_hit_step, original.last_hit_step)
        summary = d.summary(); summary['blocked_reasons'].clear();summary['counts'].clear()
        self.assertEqual(len(d.summary()['blocked_event_ids']), 1)
        before = copy.deepcopy(d.summary())
        with self.assertRaises(ValueError): d.update(a,b)
        self.assertEqual(d.summary(), before)
        with self.assertRaises(ValueError): d.update(b,sample(3,-.004))
        d.reset()
        self.assertEqual(d.summary()['previous_actual_step'], None)
        self.assertFalse(d.summary()['blocked_event_ids'])
        self.assertFalse(d.summary()['accepted_crossing_ids'])
        self.assertFalse(d.summary()['ready'] or d.summary()['ever_recovered'])
        self.assertEqual(d.summary()['preparation'], STRIKE_QUALITY_METADATA)

    def test_slow_waiting_passage_is_diagnostic_not_extra_or_blocked(self):
        d = StrikeQualityDetector(target()); self.ready(d)
        d.update(sample(1,-.004), sample(2,.004))
        d.update(sample(2,.004), sample(3,-.00001))
        before = copy.deepcopy(d.summary())
        result = d.update(sample(3,-.00001), sample(4,.00001))
        self.assertEqual(result['candidates'][0]['reason_flags'], ['speed','wait_rearm'])
        self.assertFalse(result['events'])
        self.assertEqual(d.summary()['extra_count'], 0)
        self.assertEqual(d.summary()['blocked_event_ids'], before['blocked_event_ids'])
        self.assertEqual(d.summary()['counts']['diagnostic_ineligible'], 1)

    def test_interrupted_preparation_does_not_accumulate_nonconsecutive_samples(self):
        d = StrikeQualityDetector(target())
        d.update(sample(0,-.004), sample(1,-.001))
        d.update(sample(1,-.001), sample(2,-.004))
        self.assertFalse(d.summary()['ready'])
        self.assertEqual(d.summary()['ready_dwell_s'], 0.)
        d.update(sample(2,-.004), sample(3,-.004))
        self.assertTrue(d.summary()['ready'])
        self.assertEqual(d.summary()['ready_consecutive_samples'], 2)

    def test_independent_moving_guitar_frames_preserve_quality_events(self):
        def measured(step,x):
            local = sample(step,x)
            rotation = Rotation.from_euler('xyz',[.1*step,-.2*step,.3*step])
            offset = np.array([.2*step,-.3*step,.1*step])
            q = rotation.as_quat()
            body = dict(pose=dict(p=dict(zip('xyz',offset)),r=dict(zip('xyzw',q))))
            for key in ('starts_G_m','ends_G_m','pick_G_m'):
                local[key] = world_to_guitar(offset+rotation.apply(local[key]),body)
            return local
        d=StrikeQualityDetector(target())
        d.update(measured(0,-.004),measured(1,-.004))
        result=d.update(measured(1,-.004),measured(2,.004))
        self.assertEqual([e['crossing_id'] for e in result['events']], ['2:1'])
        self.assertTrue(d.summary()['ready'])
        for step in (3,4):d.update(measured(step-1,.004),measured(step,.004))
        self.assertTrue(d.summary()['recovered'])


if __name__ == '__main__': unittest.main()
