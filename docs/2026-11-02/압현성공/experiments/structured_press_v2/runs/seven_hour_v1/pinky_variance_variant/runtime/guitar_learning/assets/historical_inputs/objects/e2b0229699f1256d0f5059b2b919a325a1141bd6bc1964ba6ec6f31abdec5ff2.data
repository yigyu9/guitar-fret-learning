"""Pure timing bookkeeping tests; native eligibility is supplied, never invented."""
import copy
import math
import unittest
from guitar_learning.music_task import ScoreTarget, ScoreTask
from guitar_learning.timing_curriculum import (TimingConfig, TimingLedger,
    TIMING_HISTORY_FIELDS, history_scales)


def task(duration=.2322):
    return ScoreTask((ScoreTarget('t', 'event0', 1, 7, 3, 1,
        2.12, 2.12+duration, 2., 1.12, 1.12+duration),),
        provenance=dict(source='synthetic_cpu_shifted_clock_fixture'))


def sample(tick, candidate=False, crossings=()):
    return dict(physics_step=480+tick, task_time_s=tick/240.,
        targets={'t':dict(candidate=candidate)}, crossings=list(crossings),
        summary=dict(matched50=0, matched100=0, sentinel='original music unchanged'))


def crossing(identity, at, *, string=2, direction=1):
    return dict(crossing_id=identity, task_time_s=at, string_number=string,
                direction=direction, valid=True, reason_flags=[])


class TimingCurriculumTests(unittest.TestCase):
    def ledger(self, role='left', stage=0, duration=.2322):
        return TimingLedger(task(duration), sample(0), role, TimingConfig(stage_index=stage))

    def run_to(self, ledger, tick, contact=lambda now:False, events=None, guide=None):
        rewards=[]
        while ledger.previous_step-480 < tick:
            current=ledger.previous_step-480+1
            rewards.append(ledger.update(sample(current, contact(current/240.),
                (events or {}).get(current, ())), guide))
        return rewards

    def test_stage_schedule_monotone_dwell_and_fixed_common_history(self):
        required=[]
        for stage, window in enumerate((1.5, .5, .2, .1, .05)):
            ledger=self.ledger(stage=stage)
            required.append(ledger.left_required_dwell_s)
            self.assertEqual(ledger.config.window_s, window)
            self.assertEqual(len(ledger.history()), 31)
            self.assertEqual(len(history_scales(ledger.task, ledger.config)), 31)
            self.assertEqual(ledger.history()[TIMING_HISTORY_FIELDS.index('stage_index')], stage)
            self.assertEqual(ledger.history()[TIMING_HISTORY_FIELDS.index('score_time_s')], -1.)
            self.assertEqual(ledger.config.horizon_s, 5.)
            self.assertTrue(all(math.isfinite(value) for value in ledger.history()))
            self.assertAlmostEqual(self.ledger(stage=stage, duration=.02).left_required_dwell_s, .02)
        self.assertEqual(required, sorted(required))
        self.assertAlmostEqual(required[0], .05)
        self.assertAlmostEqual(required[-1], .2322)
        for kwargs in (dict(stage_index=-1), dict(stage_index=True), dict(stage_index=5),
                dict(pre_roll_s=0), dict(pre_roll_s=1.001), dict(precision_bonus=-1),
                dict(missed_penalty=1), dict(right_guide_scale_m=float('nan'))):
            with self.assertRaises(ValueError): TimingConfig(**kwargs)

    def test_left_loose_contact_can_succeed_early_without_original_music_success(self):
        ledger=self.ledger()
        rewards=self.run_to(ledger, 1200, contact=lambda now:.7<=now<=.8)
        result=ledger.summary(completed=True)
        self.assertTrue(result['stage_success'])
        self.assertAlmostEqual(result['audible_valid_s'], 0.)
        self.assertAlmostEqual(result['window_longest_dwell_s'], .1)
        self.assertEqual(sum(r['timing_success'] for r in rewards), 1.)
        self.assertEqual(sum(r['timing_acquisition'] for r in rewards), .25)
        self.assertAlmostEqual(sum(r['timing_hold'] for r in rewards), .2)
        self.assertEqual(result['missed'], False)
        self.assertLessEqual(sum(r['timing_precision'] for r in rewards), .5)

    def test_candidate_loss_resets_contiguous_dwell_and_no_single_sample_credit(self):
        ledger=self.ledger()
        self.run_to(ledger, 180, contact=lambda now:.7<=now<=.7333333334)
        self.assertFalse(ledger.achieved)
        self.assertEqual(ledger.window_dwell_s, 0.)
        first=ledger.previous_step-480+1
        self.run_to(ledger, first+11, contact=lambda now:True)
        self.assertFalse(ledger.achieved)
        self.run_to(ledger, first+12, contact=lambda now:True)
        self.assertTrue(ledger.achieved)
        self.assertAlmostEqual(ledger.window_longest_dwell_s, .05)
        self.assertFalse(ledger.summary(completed=True)['stage_success'])
        self.assertTrue(ledger.summary()['provisional_success'])

    def test_final_left_requires_full_fractional_audible_interval(self):
        full=self.ledger(stage=4)
        broken=self.ledger(stage=4)
        self.run_to(full, 1200, contact=lambda now:2.08<=now<=2.4)
        self.run_to(broken, 1200, contact=lambda now:2.08<=now<=2.4 and not 2.22<=now<=2.23)
        result=full.summary(completed=True)
        self.assertTrue(result['stage_success'])
        self.assertAlmostEqual(result['audible_longest_dwell_s'], .2322)
        self.assertAlmostEqual(result['audible_hold_fraction'], 1.)
        self.assertFalse(broken.summary(completed=True)['stage_success'])
        self.assertLess(broken.audible_longest_dwell_s, .2322)
        self.assertGreater(broken.audible_valid_s, broken.audible_longest_dwell_s)
        self.assertTrue(broken.missed)
        early=self.ledger(stage=4)
        self.run_to(early, 1200, contact=lambda now:1.96<=now<=2.1)
        self.assertFalse(early.summary(completed=True)['stage_success'])
        self.assertGreater(early.window_longest_dwell_s, .1)
        self.assertEqual(early.audible_longest_dwell_s, 0.)

    def test_right_boundary_match_without_left_contact_and_unique_bonus(self):
        ledger=self.ledger('right', 4)
        events={509:[crossing('wrong_direction', 2.12, direction=-1)],
                512:[crossing('wrong_string', 2.13, string=3)],
                521:[crossing('boundary', 2.17)],
                522:[crossing('boundary', 2.17)]}
        rewards=self.run_to(ledger, 1200, events=events)
        result=ledger.summary(completed=True)
        self.assertTrue(result['stage_success'])
        self.assertEqual(result['first_matched_crossing'], 'boundary')
        self.assertEqual(result['wrong_crossings'], 2)
        self.assertEqual(result['duplicate_crossings'], 1)
        self.assertEqual(result['geometric_crossings'], 3)
        self.assertEqual(result['matching_window_crossings'], 1)
        self.assertEqual(sum(r['timing_success'] for r in rewards), 1.)
        self.assertEqual(result['audible_valid_s'], 0.)
        self.assertAlmostEqual(result['best_abs_error_s'], .05)

    def test_precision_rewards_closer_matches_and_total_bonus_is_bounded(self):
        early=self.ledger('right', 4);center=self.ledger('right', 4)
        early_terms=self.run_to(early, 500, events={500:[crossing('early', 2.08)]})
        center_terms=self.run_to(center, 509, events={509:[crossing('center', 2.12)]})
        self.assertLess(sum(r['timing_precision'] for r in early_terms),
                        sum(r['timing_precision'] for r in center_terms))
        # A closer second crossing may improve precision but cannot repeat success.
        more=self.run_to(early, 509, events={509:[crossing('center2', 2.12)]})
        self.assertEqual(sum(r['timing_success'] for r in more), 0.)
        self.assertEqual(sum(r['timing_unnecessary_crossing'] for r in more), -.02)
        self.assertAlmostEqual(sum(r['timing_precision'] for r in early_terms+more), .5)
        self.assertEqual(early.unnecessary_crossings, 1)

    def test_miss_and_wrong_crossing_separate_no_positive_reward_after_invalidation(self):
        ledger=self.ledger('right', 4)
        rewards=self.run_to(ledger, 1200, events={528:[crossing('late', 2.2)]})
        self.assertFalse(ledger.summary(completed=True)['stage_success'])
        self.assertEqual(sum(r['timing_missed'] for r in rewards), -.5)
        self.assertEqual(sum(r['timing_wrong_crossing'] for r in rewards), -.1)
        successful=self.ledger('right', 4)
        self.run_to(successful, 509, events={509:[crossing('center', 2.12)]})
        self.assertTrue(successful.summary()['provisional_success'])
        successful.invalidate(['guitar_displacement'])
        after=self.run_to(successful, 1200, guide=dict(distance_m=0.))
        self.assertTrue(all(value<=0 for terms in after for value in terms.values()))
        self.assertFalse(successful.summary(completed=True)['stage_success'])
        history=dict(zip(TIMING_HISTORY_FIELDS, successful.history()))
        self.assertEqual(history['achieved'], 1.)
        self.assertEqual(history['safety_invalidated'], 1.)

    def test_history_exposes_reward_history_without_mutating_original_measurements(self):
        ledger=self.ledger('right', 4)
        before=ledger.history()
        self.run_to(ledger, 508)
        measured=sample(509, crossings=[crossing('center', 2.12)])
        original=copy.deepcopy(measured)
        ledger.update(measured)
        self.assertEqual(measured, original)
        current=dict(zip(TIMING_HISTORY_FIELDS,ledger.history()))
        for key in ('achieved','has_first_success','matched_crossing','has_best_error',
                    'best_precision_quality','geometric_crossings','matching_window_crossings'):
            self.assertNotEqual(current[key],dict(zip(TIMING_HISTORY_FIELDS,before))[key])
        self.assertEqual(current['best_abs_error_s'],0.)
        with self.assertRaisesRegex(ValueError,'consecutive'):ledger.update(measured)
        invalid=sample(510,crossings=[dict(crossing('invalid',2.123),valid=False)])
        with self.assertRaisesRegex(ValueError,'eligible'):ledger.update(invalid)

    def test_right_guide_rate_integrates_in_actual_seconds(self):
        ledger=self.ledger('right', 0)
        terms=self.run_to(ledger,240,guide=dict(distance_m=0.))
        self.assertAlmostEqual(sum(row['timing_right_guide'] for row in terms),.2)


if __name__=='__main__':unittest.main()
