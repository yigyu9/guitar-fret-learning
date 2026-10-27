"""Native-evidence predicate fixtures; no dynamic success claims."""
import copy
import unittest

from guitar_learning.transition.task import make_task
from guitar_learning.transition.metrics import TransitionLedger
from guitar_learning.tests.test_transition_task import BUNDLE, config
from guitar_learning.tests.test_fretting_v1 import fixture
from guitar_learning.tests.test_fretting_quality import add_contact, quality


def sample(task, step, behavior):
    now = step/240.
    rows = {}
    for i, t in enumerate(task.targets):
        clean, positive = behavior(i, t, now)
        rows[t.target_id] = dict(candidate=clean, fretting_quality=dict(
            clean_target_candidate=clean, positive_target_candidate=positive,
            positive_evidence_ids=['actual-feature'] if positive else []))
    return dict(physics_step=step, task_time_s=now, targets=rows)


class TransitionMetricsTests(unittest.TestCase):
    def run_ledger(self, mode, behavior, tempo=1.):
        task = make_task(BUNDLE, config(mode, tempo))
        ledger = TransitionLedger(task, sample(task, 0, behavior), config(mode, tempo))
        for step in range(1, round(task.duration_s*240)+1):
            ledger.update(sample(task, step, behavior))
        return task, ledger.summary(True)

    def test_valid_hold_then_actual_qualified_contact_release(self):
        _, result = self.run_ledger('single_b', lambda i,t,now: (now < t.end_s, now < t.end_s))
        self.assertTrue(result['diagnostic_success'])
        row = next(iter(result['per_target'].values()))
        self.assertGreater(row['clean_hold_fraction'], .99)
        self.assertGreater(row['qualified_target_contact_absent_fraction'], .99)

    def test_clean_loss_does_not_prove_physical_target_release(self):
        _, result = self.run_ledger('single_b', lambda i,t,now: (now < t.end_s, True))
        self.assertFalse(result['diagnostic_success'])
        row = next(iter(result['per_target'].values()))
        self.assertGreater(row['clean_absent_s'], .49)
        self.assertEqual(row['qualified_target_contact_absent_s'], 0.)

    def test_preparation_accepts_positive_lower_contact_while_higher_sounds(self):
        def behavior(i, t, now):
            if i == 0: return now < 3., now < 3.
            return 3. <= now < 3.5, 2.5 <= now < 3.5
        _, result = self.run_ledger('overlap', behavior)
        self.assertTrue(result['diagnostic_success'])
        self.assertGreater(result['clean_a_and_positive_b_preparation_fraction'], .99)
        self.assertIsNotNone(result['first_a_qualified_contact_absent_and_b_clean_s'])
        # Actual classifier: lower designated contact stays positive but is
        # unclean until the higher ring contact is removed.
        inputs = fixture(finger='ring3', string=2, fret_body=7, y=.09)
        inputs = add_contact(inputs, finger='index2', string=2, fret=5, y=.13)
        task = make_task(BUNDLE, config('overlap'))
        qa = quality(copy.deepcopy(inputs), task.targets[0])[0]
        qb = quality(copy.deepcopy(inputs), task.targets[1])[0]
        self.assertTrue(qa['clean_target_candidate'])
        self.assertTrue(qb['positive_target_candidate'])
        self.assertFalse(qb['clean_target_candidate'])
        self.assertTrue(qb['higher_fret'])
        inputs[3]['contacts'] = inputs[3]['contacts'][1:]
        qb_after = quality(copy.deepcopy(inputs), task.targets[1])[0]
        qa_after = quality(copy.deepcopy(inputs), task.targets[0])[0]
        self.assertTrue(qb_after['clean_target_candidate'])
        self.assertFalse(qa_after['positive_target_candidate'])

    def test_pair_preparation_is_reported_not_forced_success_gate(self):
        def behavior(i,t,now): return t.onset_s <= now < t.end_s, t.onset_s <= now < t.end_s
        _, result = self.run_ledger('pair', behavior)
        self.assertTrue(result['diagnostic_success'])
        self.assertFalse(result['preparation_overlap_pass'])
        self.assertFalse(result['criterion']['overlap_required'])

    def test_release_grace_preserves_measured_handover_delay(self):
        def behavior(i, t, now):
            return now < t.end_s, now < t.end_s+.25
        _, result = self.run_ledger('single_a', behavior)
        row = next(iter(result['per_target'].values()))
        self.assertTrue(row['release_pass'])
        self.assertGreater(row['qualified_contact_absent_latency_s'], .25)
        self.assertLess(row['qualified_contact_absent_latency_s'], .26)
        self.assertAlmostEqual(result['criterion']['release_grace_s'], .3)

    def test_clock_skip_and_fabricated_positive_fail(self):
        task = make_task(BUNDLE, config('single_a'))
        behavior = lambda i,t,now: (False, False)
        ledger = TransitionLedger(task, sample(task, 0, behavior), config('single_a'))
        with self.assertRaisesRegex(ValueError, 'consecutive'): ledger.update(sample(task, 2, behavior))
        bad = sample(task, 1, behavior)
        bad['targets'][task.targets[0].target_id]['fretting_quality']['positive_target_candidate'] = True
        with self.assertRaisesRegex(ValueError, 'evidence'): ledger.update(bad)


if __name__ == '__main__': unittest.main()
