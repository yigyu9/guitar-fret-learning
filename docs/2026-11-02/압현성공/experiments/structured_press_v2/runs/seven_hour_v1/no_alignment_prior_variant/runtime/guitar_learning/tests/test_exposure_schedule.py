import copy
import unittest

from guitar_learning.training.finger_skill_runner import ExposureSchedule


class ExposureScheduleTests(unittest.TestCase):
    def test_fixed_quarter_boundary_counts_only_committed_raw_transitions(self):
        value = ExposureSchedule(101)
        self.assertEqual(value.config['full_song_after'], 25)
        self.assertEqual(value.status()['next_reset_scope'], 'phrases')
        value.commit(24)
        self.assertEqual(value.status()['next_reset_scope'], 'phrases')
        self.assertEqual(value.commit(1)['next_reset_scope'], 'full_song')
        value.commit(1000)
        self.assertEqual(value.config, dict(planned_transitions=101, full_song_after=25))
        self.assertEqual(value.committed_transitions, 1025)
        self.assertEqual(value.status()['remaining_transitions'], 0)
        self.assertFalse(value.status()['mastery_gate'])

    def test_resume_and_extra_budget_cannot_recalculate_or_reverse_scope(self):
        source = ExposureSchedule(80)
        source.commit(21)
        restored = ExposureSchedule(80)
        restored.load_state_dict(source.state_dict())
        restored.commit(3)
        self.assertEqual(restored.status()['next_reset_scope'], 'full_song')
        self.assertEqual(restored.config['full_song_after'], 20)
        with self.assertRaisesRegex(ValueError, 'mismatch'):
            ExposureSchedule(12).load_state_dict(source.state_dict())

    def test_invalid_state_does_not_mutate_schedule(self):
        schedule = ExposureSchedule(8)
        schedule.commit(3)
        expected = schedule.state_dict()
        for field, value in (('committed_transitions', -1), ('committed_transitions', True),
                             ('schema', 'legacy'), ('config', dict(planned_transitions=8, full_song_after=3))):
            state = copy.deepcopy(expected)
            state[field] = value
            with self.assertRaises(ValueError):
                schedule.load_state_dict(state)
            self.assertEqual(schedule.state_dict(), expected)
        for planned in (0, -1, True, 1.5):
            with self.assertRaises(ValueError): ExposureSchedule(planned)
        with self.assertRaises(ValueError): ExposureSchedule(8, 1)
        for committed in (-1, False, 1.5):
            with self.assertRaises(ValueError): schedule.commit(committed)

    def test_short_budget_has_an_immediate_full_song_boundary(self):
        self.assertEqual(ExposureSchedule(3).status()['next_reset_scope'], 'full_song')


if __name__ == '__main__':
    unittest.main()
