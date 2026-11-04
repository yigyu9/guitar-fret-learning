"""단일·스트럼의 순서·준비·누락·회복 원장을 CPU에서 검사한다."""
from types import SimpleNamespace
import unittest

import torch

from guitar_learning.gpu.strike_events import StrikeLedger


def event(strings=(2,), audible=None, onset=1., direction=1):
    offsets = tuple((i-(len(strings)-1)/2)*.02 for i in range(len(strings)))
    audible = strings if audible is None else audible
    return SimpleNamespace(event_id='event-'+str(onset), gesture='strum' if len(strings) > 1 else 'single_pick',
        direction=direction, onset_s=onset, traversal_strings=strings,
        audible_strings=audible, protected_strings=tuple(s for s in strings if s not in audible),
        traversal_offsets_s=offsets, sweep_duration_s=offsets[-1]-offsets[0])


class StrikeLedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def make(self, events=None, count=2):
        return StrikeLedger(count, events or (event(),), 'cpu')

    def ready(self, ledger):
        for _ in range(6):
            ledger.update_ready(torch.ones(ledger.N, dtype=torch.bool))

    def cross(self, ledger, string, time=1., direction=1, ids=None):
        ids = torch.arange(ledger.N) if ids is None else torch.tensor(ids)
        return ledger.cross(ids, torch.full_like(ids, string), torch.full_like(ids, direction),
            torch.full((len(ids),), time, dtype=torch.float64), torch.ones(len(ids)))

    def recover(self, ledger, seconds=.21, clearance=.02, armed=True, separated=True):
        result = None
        for _ in range(round(seconds*240)+1):
            result = ledger.update_recovery(torch.full((ledger.N,), clearance),
                torch.full((ledger.N,), separated), torch.full((ledger.N,), armed), 1./240.)
        return result

    def test_prepared_single_and_full_recovery(self):
        ledger = self.make()
        self.ready(ledger)
        result = self.cross(ledger, 2)
        self.assertTrue(result['completed'].all())
        self.assertTrue(ledger.current('clean_complete').all())
        torch.testing.assert_close(ledger.terms['ready'], torch.ones(2))
        torch.testing.assert_close(ledger.terms['crossing'], torch.ones(2))
        self.assertFalse(ledger.current('recovered').any())
        self.recover(ledger)
        self.assertTrue(ledger.current('recovered').all())
        torch.testing.assert_close(ledger.terms['recovery_progress'], torch.ones(2))
        torch.testing.assert_close(ledger.terms['recovery_complete'], torch.ones(2))
        ledger.advance(torch.full((2,), 1.3, dtype=torch.float64))
        self.assertTrue(ledger.done.all())
        self.assertEqual(ledger.active.tolist(), [0, 0])

    def test_ready_requires_six_consecutive_endpoints_and_only_pays_once(self):
        ledger = self.make()
        yes = torch.ones(2, dtype=torch.bool)
        for _ in range(5):
            ledger.update_ready(yes)
        self.assertFalse(ledger.current('ready').any())
        ledger.update_ready(torch.zeros_like(yes))
        self.ready(ledger)
        for _ in range(20):
            ledger.update_ready(yes)
        torch.testing.assert_close(ledger.terms['ready'], torch.ones(2))

    def test_unprepared_crossing_never_inherits_later_readiness_or_recovery_bonus(self):
        ledger = self.make()
        self.cross(ledger, 2)
        self.ready(ledger)
        self.recover(ledger)
        self.assertTrue(ledger.current('complete').all())
        self.assertFalse(ledger.current('clean_complete').any())
        torch.testing.assert_close(ledger.terms['unprepared'], torch.ones(2))
        torch.testing.assert_close(ledger.terms['crossing'], torch.zeros(2))
        torch.testing.assert_close(ledger.terms['recovery_complete'], torch.zeros(2))

    def test_protected_string_still_required_for_full_strum(self):
        ledger = self.make((event((3, 2, 1), audible=(3, 2)),))
        self.ready(ledger)
        self.cross(ledger, 3, .98)
        self.cross(ledger, 2, 1.)
        self.assertTrue(ledger.current('audible_complete').all())
        self.assertFalse(ledger.current('complete').any())
        self.cross(ledger, 1, 1.02)
        self.assertTrue(ledger.current('clean_complete').all())
        torch.testing.assert_close(ledger.terms['strum_microtiming'], torch.ones(2))
        torch.testing.assert_close(ledger.terms['strum_progress'], torch.ones(2))
        # 같은 제어 구간의 여러 현은 구역 보상을 중복 지급하지 않는다.
        torch.testing.assert_close(ledger.terms['zone'], torch.ones(2))

    def test_reverse_direction_strum_is_symmetric(self):
        ledger = self.make((event((1, 2, 3), direction=-1),))
        self.ready(ledger)
        for s, t in ((1, .98), (2, 1.), (3, 1.02)):
            self.cross(ledger, s, t, direction=-1)
        self.assertTrue(ledger.current('clean_complete').all())

    def test_order_violation_duplicate_wrong_direction_and_unplanned_are_distinct(self):
        ledger = self.make((event((3, 2, 1)),), count=1)
        self.ready(ledger)
        self.cross(ledger, 2)  # 순서 위반은 승인하지 않는다.
        self.cross(ledger, 3)
        self.cross(ledger, 3)
        self.cross(ledger, 2, direction=-1)
        self.cross(ledger, 5)
        for key in ('order_violation', 'duplicate', 'wrong_direction', 'unplanned'):
            self.assertEqual(ledger.current(key).item(), 1.)
        self.cross(ledger, 2)
        self.cross(ledger, 1)
        self.assertTrue(ledger.current('complete').all())
        self.assertFalse(ledger.current('clean_complete').any())
        self.assertEqual(ledger.terms['crossing'].item(), 0.)

    def test_wrong_after_completion_revokes_clean_and_no_recovery_reward(self):
        ledger = self.make()
        self.ready(ledger)
        self.cross(ledger, 2)
        ledger.record_wrong(torch.arange(2), torch.ones(2))
        self.assertFalse(ledger.current('clean_complete').any())
        torch.testing.assert_close(ledger.terms['crossing'], torch.zeros(2))
        self.recover(ledger)
        self.assertTrue(ledger.current('recovered').all())
        torch.testing.assert_close(ledger.terms['recovery_complete'], torch.zeros(2))

    def test_late_crossing_and_no_crossing_miss_only_once(self):
        ledger = self.make()
        self.ready(ledger)
        self.cross(ledger, 2, 1.06, ids=[0])
        ledger.advance(torch.full((2,), 1.1, dtype=torch.float64))
        ledger.advance(torch.full((2,), 1.2, dtype=torch.float64))
        self.assertTrue(ledger.history['missed'].all())
        torch.testing.assert_close(ledger.terms['miss'], torch.ones(2))

    def test_partial_strum_timeout_requires_recovery_without_success_bonus(self):
        ledger = self.make((event((3, 2, 1)),))
        self.ready(ledger)
        self.cross(ledger, 3, .98)
        ledger.advance(torch.full((2,), 1.2, dtype=torch.float64))
        self.assertTrue(ledger.current('missed').all())
        self.assertFalse(ledger.current('recovered').any())
        self.recover(ledger)
        self.assertTrue(ledger.current('recovered').all())
        torch.testing.assert_close(ledger.terms['recovery_progress'], torch.zeros(2))

    def test_full_recovery_requires_current_separation_and_armed(self):
        ledger = self.make()
        self.ready(ledger)
        self.cross(ledger, 2)
        self.recover(ledger, armed=False)
        self.assertFalse(ledger.current('recovered').any())
        self.recover(ledger, seconds=.10)
        self.recover(ledger, seconds=.01, separated=False)
        self.recover(ledger, seconds=.10)
        self.assertFalse(ledger.current('recovered').any())
        self.recover(ledger, seconds=.11)
        self.assertTrue(ledger.current('recovered').all())
        torch.testing.assert_close(ledger.terms['recovery_progress'], torch.ones(2))

    def test_short_same_string_handoff_preserves_rearm_and_moves_once(self):
        ledger = self.make((event(onset=1.), event(onset=1.15)))
        self.ready(ledger)
        self.cross(ledger, 2)
        self.assertTrue(ledger.handoff.all())
        self.assertTrue(ledger.rearm_required.all())
        self.recover(ledger, seconds=.10, armed=False)
        self.assertFalse(ledger.current('recovered').any())
        self.recover(ledger, seconds=.10)
        ledger.advance(torch.full((2,), 1.11, dtype=torch.float64))
        self.assertEqual(ledger.active.tolist(), [1, 1])
        self.assertTrue(ledger.current('ready').all())
        torch.testing.assert_close(ledger.terms['ready'], torch.ones(2))
        self.assertFalse(ledger.done.any())

    def test_path_crossing_handoff_requires_clearance(self):
        ledger = self.make((event((3,), onset=1.), event((1,), onset=1.15)))
        self.ready(ledger)
        self.cross(ledger, 3)
        self.assertTrue(ledger.clearance_required.all())
        self.recover(ledger, seconds=.2, clearance=.002)
        self.assertFalse(ledger.current('recovered').any())
        self.recover(ledger, seconds=.2, clearance=.004)
        self.assertTrue(ledger.current('recovered').all())

    def test_partial_reset_preserves_other_environment(self):
        ledger = self.make()
        self.ready(ledger)
        self.cross(ledger, 2)
        ledger.reset([0])
        self.assertEqual(ledger.current('complete').tolist(), [False, True])
        self.assertEqual(ledger.terms['crossing'].tolist(), [0., 1.])
        self.assertEqual(ledger.current('ready').tolist(), [False, True])
        self.assertEqual(ledger.episode_ready.tolist(), [False, True])

    def test_dense_single_strum_single_inherits_episode_preparation(self):
        middle = event((3, 2, 1), onset=34.8299)
        middle.traversal_offsets_s = (-.007, 0., .007)
        middle.sweep_duration_s = .014
        ledger = self.make((event((3,), onset=34.7719), middle,
                            event((1,), onset=34.888)))
        self.ready(ledger)

        def crossing(string, time):
            ledger.advance(torch.full((2,), time, dtype=torch.float64))
            self.cross(ledger, string, time)

        def handoff():
            for _ in range(9):
                ledger.update_recovery(torch.full((2,), .01), torch.ones(2, dtype=torch.bool),
                                       torch.ones(2, dtype=torch.bool), 1./240.)
                ledger.advance(ledger.now+1./240.)

        crossing(3, 34.7719)
        handoff()
        self.assertEqual(ledger.active.tolist(), [1, 1])
        crossing(3, 34.8229)
        crossing(2, 34.8299)
        crossing(1, 34.8369)
        handoff()
        self.assertEqual(ledger.active.tolist(), [2, 2])
        crossing(1, 34.888)
        self.assertTrue(ledger.history['clean_complete'].all())
        self.assertTrue(ledger.history['ready'].all())
        torch.testing.assert_close(ledger.terms['ready'], torch.ones(2))
        torch.testing.assert_close(ledger.terms['crossing'], torch.full((2,), 3.))
        ledger.reset([0])
        self.assertEqual(ledger.episode_ready.tolist(), [False, True])
        self.assertFalse(ledger.history['ready'][0].any())
        self.assertTrue(ledger.history['ready'][1].all())
        ledger.reset([1])
        self.assertFalse(ledger.episode_ready.any())

    def test_tick_transition_cancels_only_new_event_clean_credits(self):
        ledger = self.make((event(onset=1.), event(onset=1.15)))
        self.ready(ledger)
        self.cross(ledger, 2)
        self.recover(ledger, seconds=.07)
        ledger.begin_tick()
        ledger.update_recovery(torch.full((2,), .01), torch.ones(2, dtype=torch.bool),
                               torch.ones(2, dtype=torch.bool), 1./60.)
        previous_recovery = ledger.terms['recovery_progress'].clone()
        previous_completion = ledger.terms['recovery_complete'].clone()
        self.assertTrue((previous_completion > 0).all())
        ledger.advance(torch.full((2,), 1.11, dtype=torch.float64))
        self.assertEqual(ledger.active.tolist(), [1, 1])
        self.cross(ledger, 2, time=1.15)
        torch.testing.assert_close(ledger.terms['crossing'], torch.ones(2))
        self.cross(ledger, 4, time=1.151)
        torch.testing.assert_close(ledger.terms['crossing'], torch.zeros(2))
        torch.testing.assert_close(ledger.terms['timing'], torch.zeros(2))
        torch.testing.assert_close(ledger.terms['recovery_progress'], previous_recovery)
        torch.testing.assert_close(ledger.terms['recovery_complete'], previous_completion)
        self.assertTrue(ledger.history['clean_complete'][:, 0].all())
        self.assertFalse(ledger.history['clean_complete'][:, 1].any())

    def test_terminal_progress_cannot_be_farmed_by_reversing(self):
        ledger = self.make((event((2, 1)),))
        self.ready(ledger)
        self.cross(ledger, 2, .99)
        for value in (.2, .6, .1, .6, .8):
            ledger.add_terminal_progress(torch.full((2,), value))
        torch.testing.assert_close(ledger.terms['strum_terminal_progress'], torch.full((2,), .8))

    def test_new_string_progress_is_not_timing_quality_or_repeat_reward(self):
        ledger = self.make((event((3, 2, 1)),))
        self.ready(ledger)
        self.cross(ledger, 3, .95)  # 목표보다30ms일러도 새현 진행량은1/3이다.
        torch.testing.assert_close(ledger.terms['strum_progress'], torch.full((2,), 1./3.))
        ledger.begin_tick()
        torch.testing.assert_close(ledger.terms['strum_progress'], torch.zeros(2))
        self.cross(ledger, 3, .97)  # 이미 승인한 현을 반복해도 진행을 다시 주지 않는다.
        torch.testing.assert_close(ledger.terms['strum_progress'], torch.zeros(2))

    def test_recovery_holds_do_not_multiply_completion_or_progress_budget(self):
        ledger = self.make()
        self.ready(ledger)
        self.cross(ledger, 2)
        self.recover(ledger, seconds=.1)
        before = ledger.terms['recovery_progress'].clone()
        self.recover(ledger, seconds=.1, separated=False)
        for _ in range(24):
            ledger.update_recovery(torch.full((2,), .02), torch.ones(2, dtype=torch.bool),
                                   torch.ones(2, dtype=torch.bool), 1./240.)
        torch.testing.assert_close(ledger.terms['recovery_progress'], before)
        self.recover(ledger, seconds=.5)
        self.recover(ledger, seconds=.5)
        torch.testing.assert_close(ledger.terms['recovery_progress'], torch.ones(2))
        torch.testing.assert_close(ledger.terms['recovery_complete'], torch.ones(2))

    def test_new_physical_or_blocked_crossing_restarts_recovery_dwell(self):
        for blocked in (False, True):
            ledger = self.make()
            self.ready(ledger)
            self.cross(ledger, 2)
            self.recover(ledger, seconds=.18)
            self.assertTrue((ledger.recovery_elapsed > .17).all())
            if blocked:
                ledger.record_wrong(torch.arange(2), torch.ones(2))
            else:
                self.cross(ledger, 4, time=1.18)
            torch.testing.assert_close(ledger.recovery_elapsed, torch.zeros(2))
            self.recover(ledger, seconds=.05)
            self.assertFalse(ledger.current('recovered').any())
            self.recover(ledger, seconds=.17)
            self.assertTrue(ledger.current('recovered').all())
            torch.testing.assert_close(ledger.terms['recovery_complete'], torch.zeros(2))

    def test_bad_shapes_clock_order_and_event_direction_rejected(self):
        with self.assertRaises(ValueError):
            self.make((event((1, 2), direction=1),))
        ledger = self.make()
        with self.assertRaises(ValueError):
            ledger.update_ready(torch.ones(2))
        ledger.advance(torch.full((2,), .5, dtype=torch.float64))
        with self.assertRaises(ValueError):
            ledger.advance(torch.full((2,), .4, dtype=torch.float64))
        with self.assertRaises(ValueError):
            ledger.cross([0, 0], [2, 2], [1, 1], [1., 1.], [1., 1.])


if __name__ == '__main__':
    unittest.main()
