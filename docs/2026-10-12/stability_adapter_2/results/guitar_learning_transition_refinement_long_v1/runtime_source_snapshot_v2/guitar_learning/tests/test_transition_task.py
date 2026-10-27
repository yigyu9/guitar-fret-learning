"""Immutable-source subset and explicit easy/diagnostic timing checks."""
import unittest

from guitar_learning.transition.task import make_task, catalog, validate
from guitar_learning.tests.test_song_task import BUNDLE


def config(mode='pair', tempo=1., role='left'):
    return dict(schema='guitar_learning.transition.v1', mode=mode, tempo_scale=tempo, role=role)


class TransitionTaskTests(unittest.TestCase):
    def test_actual_catalog_and_selected_mapping(self):
        result = catalog(BUNDLE)
        self.assertEqual((result['source_note_count'], result['distinct_target_count'], result['distinct_pair_count']), (67, 30, 55))
        task = make_task(BUNDLE, config())
        self.assertEqual([(t.string, t.fret, t.finger) for t in task.targets], [(1, 7, 3), (1, 5, 1)])
        self.assertEqual(task.lookahead_s, 4.)
        self.assertEqual(task.targets[0].onset_s, 2.)
        self.assertAlmostEqual(task.targets[1].onset_s-task.targets[0].onset_s, .2322)
        self.assertAlmostEqual(task.targets[1].onset_s-task.targets[1].press_s, .12)

    def test_pair_time_scales_without_changing_source_clock(self):
        normal = make_task(BUNDLE, config())
        for tempo in (.25, .5):
            task = make_task(BUNDLE, config(tempo=tempo))
            for old, new in zip(normal.targets, task.targets):
                for field in ('onset_s', 'end_s', 'press_s'):
                    self.assertAlmostEqual(getattr(new, field), 2.+(getattr(old, field)-2.)/tempo)
                self.assertEqual(new.source_onset_s, old.source_onset_s)
                self.assertEqual(new.source_end_s, old.source_end_s)
            self.assertGreaterEqual(task.duration_s, task.targets[-1].end_s+.5)

    def test_diagnostic_hold_release_and_overlap_are_not_score_timing(self):
        a = make_task(BUNDLE, config('single_a'))
        b = make_task(BUNDLE, config('single_b'))
        for task in (a, b):
            self.assertEqual(len(task.targets), 1)
            self.assertEqual((task.targets[0].onset_s, task.targets[0].end_s), (2., 2.5))
            self.assertEqual(task.duration_s, 4.)
        overlap = make_task(BUNDLE, config('overlap'))
        self.assertEqual(overlap.provenance['transition']['preparation_window'], [2.5, 3.])
        self.assertEqual(overlap.targets[1].end_s, 3.5)
        self.assertAlmostEqual(overlap.duration_s, 4.3)
        self.assertEqual(overlap.provenance['transition']['release_grace_s'], .3)
        self.assertEqual(overlap.provenance['transition']['hold_fraction'], .9)
        self.assertEqual(make_task(BUNDLE, config()).provenance['transition']['overlap_fraction'], None)

    def test_invalid_config_fails(self):
        for field, value in (('tempo_scale', True), ('tempo_scale', .75), ('mode', 'full'), ('role', 'right')):
            bad = config(); bad[field] = value
            with self.assertRaises(ValueError): validate(bad)


if __name__ == '__main__': unittest.main()
