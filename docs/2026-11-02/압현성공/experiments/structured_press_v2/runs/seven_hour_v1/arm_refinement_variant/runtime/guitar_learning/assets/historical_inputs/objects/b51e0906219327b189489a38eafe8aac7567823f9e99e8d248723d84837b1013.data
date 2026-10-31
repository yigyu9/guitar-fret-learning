"""CPU score boundaries and reward isolation; no dynamics or sound claim."""
import unittest
import numpy as np
from guitar_learning.music_task import ScoreTask, ScoreTarget
from guitar_learning.song.metrics import SongLedger as OriginalSongLedger
from guitar_learning.song.quality import SongLedger, HISTORY_FIELDS, HISTORY_SCALES, metadata
from guitar_learning.tests.test_song_metrics import sample, crossing, target


class SongRewardV2MetricsTests(unittest.TestCase):
    def test_current_ring_fret7_not_penalized_as_future_index_fret5(self):
        targets = (
            ScoreTarget('ring7', 'a', 1, 7, 3, 1, 0., .2, 0., 0., .2),
            ScoreTarget('index5', 'b', 1, 5, 1, 1, .2, .4, .05, .2, .4),
        )
        task = ScoreTask(targets)
        clean = dict(ring7=True, index5=False)
        initial = sample(0, targets, clean=clean, wrong=True)
        old, new = OriginalSongLedger(task, initial), SongLedger(task, initial)
        old_wrong = new_wrong = 0.
        for step in range(1, 49):
            measured = sample(step, targets, clean=clean, wrong=True)
            old_terms, new_terms = old.update(measured), new.update(measured)
            old_wrong += old_terms['song_wrong_press']
            new_wrong += new_terms['song_wrong_press']
            for name in old_terms:
                if name not in ('song_wrong_press', 'song_right_guide'):
                    self.assertEqual(old_terms[name], new_terms[name])
        self.assertAlmostEqual(old_wrong, -.15)
        self.assertEqual(new_wrong, 0.)
        self.assertEqual(new.notes['index5']['wrong_press_s'], 0.)
        self.assertEqual(new.notes['ring7']['clean_audible_s'], old.notes['ring7']['clean_audible_s'])
        self.assertEqual(new.summary()['left_success_count'], 1)
        sounding = new.update(sample(49, targets, clean=clean, wrong=True))
        self.assertAlmostEqual(sounding['song_wrong_press'], -1/240.)
        self.assertAlmostEqual(new.notes['index5']['wrong_press_s'], 1/240.)

    def test_audible_fractional_boundaries_and_endpoint_average(self):
        targets = (ScoreTarget('a', 'a', 0, 5, 1, 1, .002, .009, 0., .002, .009),)
        ledger = SongLedger(ScoreTask(targets), sample(0, targets, False, wrong=False))
        terms1 = ledger.update(sample(1, targets, False, wrong=True))
        terms2 = ledger.update(sample(2, targets, False, wrong=True))
        terms3 = ledger.update(sample(3, targets, False, wrong=False))
        expected = (.004166666666666667-.002)*.5 + 1/240. + (.009-2/240.)*.5
        self.assertAlmostEqual(terms1['song_wrong_press'], -(1/240.-.002)*.5)
        self.assertAlmostEqual(-sum(row['song_wrong_press'] for row in (terms1, terms2, terms3)), expected)
        self.assertAlmostEqual(ledger.notes['a']['wrong_press_s'], expected)
        later = ledger.update(sample(4, targets, False, wrong=True))
        self.assertEqual(later['song_wrong_press'], 0.)
        self.assertAlmostEqual(ledger.notes['a']['wrong_press_s'], expected)

    def test_post_note_contact_does_not_require_full_release(self):
        targets = (target(end=2/240.),)
        ledger = SongLedger(ScoreTask(targets), sample(0, targets))
        for step in range(1, 3):
            ledger.update(sample(step, targets, crossings=[crossing(step)] if step == 1 else []))
        before = ledger.summary()['per_note']['a'].copy()
        for step in range(3, 12):
            terms = ledger.update(sample(step, targets, False, wrong=True))
            self.assertEqual(terms['song_wrong_press'], 0.)
            self.assertEqual(terms['song_missing_press'], 0.)
        self.assertEqual(ledger.summary()['per_note']['a'], before)

    def test_old_guide_dwell_positive_but_v2_zero(self):
        targets = (target(onset=.2, end=.3),)
        task = ScoreTask(targets)
        old = OriginalSongLedger(task, sample(0, targets))
        new = SongLedger(task, sample(0, targets))
        geometry = dict(physics_step=1, starts_G_m=[[0., -.5, 0.]]*6,
            ends_G_m=[[0., -.2, 0.]]*6, pick_G_m=[-.008, -.36, -.004])
        old_terms = old.update(sample(1, targets), dict(geometry=geometry))
        new_terms = new.update(sample(1, targets), dict(geometry=geometry))
        self.assertGreater(old_terms['song_right_guide'], 0.)
        self.assertEqual(new_terms['song_right_guide'], 0.)
        with self.assertRaisesRegex(ValueError, 'same-step'):
            new.update(sample(2, targets), dict(geometry=geometry))

    def test_success_strict_denominator_history_and_failures_unchanged(self):
        targets = (target('a', 1/240., 4/240.), target('b', 8/240., 12/240.))
        task = ScoreTask(targets)
        old = OriginalSongLedger(task, sample(0, targets), window_s=.002)
        new = SongLedger(task, sample(0, targets), window_s=.002)
        for step in range(1, 38):
            events = [crossing(step, str(step))] if step in (1, 8) else []
            measured = sample(step, targets, crossings=events)
            self.assertEqual(old.update(measured), new.update(measured))
            np.testing.assert_array_equal(old.history(), new.history())
        before, after = old.summary(True), new.summary(True)
        for name in before:
            if name != 'schema': self.assertEqual(before[name], after[name])
        self.assertEqual(after['denominator'], 2)
        self.assertEqual(after['coupled_hit_count'], 2)
        self.assertTrue(after['stage_success'])
        self.assertEqual(after['strict_music']['matched50'], 0)
        self.assertEqual(len(HISTORY_FIELDS), 32)
        self.assertEqual(len(HISTORY_SCALES), 32)
        unsafe = SongLedger(task, sample(0, targets))
        unsafe.invalidate(['unsafe'])
        terms = unsafe.update(sample(1, targets, crossings=[crossing(1)]))
        self.assertTrue(all(value <= 0 for value in terms.values()))
        self.assertTrue(unsafe.summary()['safety_invalidated'])
        self.assertFalse(unsafe.summary(True)['stage_success'])
        with self.assertRaisesRegex(ValueError, 'consecutive'):
            unsafe.update(sample(3, targets))
        with self.assertRaisesRegex(ValueError, 'clock zero'):
            SongLedger(task, sample(1, targets))

    def test_metadata_explicitly_versions_two_reward_changes(self):
        value = metadata()
        self.assertEqual(value['schema'], 'guitar_learning.song_metrics.v2')
        self.assertIn('audible', value['wrong_press_phase'])
        self.assertEqual(value['rewards']['wrong_press_second'], -1.)
        self.assertEqual(value['rewards']['right_guide_second'], 0.)
        self.assertEqual(value['right_progress']['beta'], .25)
        self.assertEqual(value['right_progress']['gamma'], .99)
        self.assertEqual(value['right_progress']['scale_m'], .03)
        self.assertEqual(value['right_progress']['goal'], 'endpoint_departure')


if __name__ == '__main__': unittest.main()
