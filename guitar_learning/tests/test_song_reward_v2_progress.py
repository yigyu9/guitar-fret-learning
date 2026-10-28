"""Fixed-owner control-rate potential: signed, bounded and read-only."""
import copy
import unittest
import numpy as np
from guitar_learning.song.task import ScoreTask
from guitar_learning.song import progress
from guitar_learning.tests.test_song_metrics import target
from guitar_learning.tests.test_dense_environment import geometry


class SongRewardV2ProgressTests(unittest.TestCase):
    def test_same_owner_exact_discounted_formula_and_failed_positive_suppression(self):
        before = dict(target_id='a', potential=.2)
        after = dict(target_id='a', potential=.8)
        expected = .25*(.99*.8-.2)
        self.assertAlmostEqual(progress.reward(before, after)['value'], expected)
        self.assertEqual(progress.reward(before, after, failed=True)['value'], 0.)
        negative = progress.reward(after, before)['value']
        self.assertLess(negative, 0.)
        self.assertEqual(progress.reward(after, before, failed=True)['value'], negative)

    def test_entry_exit_owner_switch_and_hover_have_no_positive_bonus(self):
        absent = dict(target_id=None, potential=0.)
        present = dict(target_id='a', potential=.8)
        other = dict(target_id='b', potential=1.)
        for before, after in ((absent, present), (present, absent), (present, other), (absent, absent)):
            self.assertEqual(progress.reward(before, after)['value'], 0.)
        self.assertLessEqual(progress.reward(present, present)['value'], 0.)

    def test_discounted_closed_cycle_telescopes_without_positive_farming(self):
        values = [.2, .8, .3, .9, .2]
        terms = [progress.reward(dict(target_id='a', potential=before),
            dict(target_id='a', potential=after))['value']
            for before, after in zip(values, values[1:])]
        discounted = sum(.99**index*value for index, value in enumerate(terms))
        self.assertAlmostEqual(discounted, .25*(.99**4*values[-1]-values[0]))
        self.assertLessEqual(discounted, 0.)

    def test_live_fixed_departure_point_and_clock_alignment(self):
        t = target(onset=.2, end=.4, string=1)
        task = ScoreTask((t,))
        notes = dict(a=dict(right_crossing_id=None))
        g = geometry(1)
        goal, _ = progress.pick_guide(g, t, t.onset_s-progress.GUIDE.sweep_half_window_s, progress.GUIDE)
        g['pick_G_m'] = goal.copy()
        original = copy.deepcopy(g)
        snap = progress.snapshot(task, notes, dict(task_time_s=1/240., physics_step=1), dict(geometry=g), .5)
        self.assertEqual(snap['target_id'], 'a')
        self.assertAlmostEqual(snap['distance_m'], 0.)
        self.assertAlmostEqual(snap['potential'], 1.)
        # A later clock cannot move the departure target underneath a static pick.
        same = progress.snapshot(task, notes, dict(task_time_s=.23, physics_step=1), dict(geometry=g), .5)
        self.assertEqual(snap, same)
        for name in original: np.testing.assert_array_equal(g[name], original[name])
        g['pick_G_m'] = goal+np.array([progress.SCALE_M, 0., 0.])
        farther = progress.snapshot(task, notes, dict(task_time_s=.1, physics_step=1), dict(geometry=g), .5)
        self.assertAlmostEqual(farther['potential'], np.exp(-1.))
        with self.assertRaisesRegex(ValueError, 'same-step'):
            progress.snapshot(task, notes, dict(task_time_s=.1, physics_step=2), dict(geometry=g), .5)
        g['pick_G_m'] = [float('nan'), 0., 0.]
        with self.assertRaisesRegex(ValueError, 'finite'):
            progress.snapshot(task, notes, dict(task_time_s=.1, physics_step=1), dict(geometry=g), .5)

    def test_owner_unavailable_until_lookahead_and_removed_after_hit_or_deadline(self):
        t = target(onset=3., end=3.2)
        task = ScoreTask((t,), lookahead_s=2.)
        notes = dict(a=dict(right_crossing_id=None))
        g = dict(geometry=geometry(1))
        def at(now): return progress.snapshot(task, notes, dict(task_time_s=now, physics_step=1), g, .1)
        self.assertIsNone(at(.99)['target_id'])
        self.assertEqual(at(1.)['target_id'], 'a')
        self.assertIsNone(at(3.1)['target_id'])
        notes['a']['right_crossing_id'] = 'native-hit'
        self.assertIsNone(at(2.)['target_id'])


if __name__ == '__main__': unittest.main()
