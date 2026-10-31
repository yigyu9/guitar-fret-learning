"""Episode based curriculum advances only from actual recent performance."""
import json
import unittest

import numpy as np

from guitar_learning.song.left_curriculum import (
    CurriculumState, STATE_SIZE, default_config)


def episode(reach=1., contact=1., safe=True):
    return dict(full_safe=safe, reach_fraction=reach, contact_fraction=contact)


class LeftCurriculumTests(unittest.TestCase):
    def test_contract_is_json_safe_and_early_contact_never_disabled(self):
        config = json.loads(json.dumps(default_config()))
        self.assertEqual(config['window'], 8)
        self.assertEqual(config['weights']['contact'], [.15, 1., 1.])
        state = CurriculumState()
        self.assertEqual(state.weights()['wrist'], 1.)
        self.assertEqual(state.weights()['contact'], .15)
        self.assertEqual(state.summary()['stage'], 'position')

    def test_requires_four_complete_episodes_and_no_stale_advancement(self):
        state = CurriculumState()
        state.observe([episode()] * 3)
        self.assertEqual(state.progress, 0.)
        state.observe([])  # No completed episode in a partial collection.
        self.assertEqual(state.count, 3)
        state.observe([episode()])
        self.assertEqual(state.progress, .1)
        before = state.state_vector()
        for _ in range(5):
            state.observe([])
        np.testing.assert_array_equal(state.state_vector(), before)

    def test_failed_episodes_count_as_zeros_and_hold_progress(self):
        state = CurriculumState()
        state.observe([episode(), episode(), episode(safe=False),
                       episode(safe=False)])
        self.assertEqual(state.count, 4)
        self.assertEqual(state.progress, 0.)
        self.assertEqual(state.summary()['recent_safe_fraction'], .5)
        self.assertEqual(state.summary()['recent_reach_fraction'], .5)
        self.assertEqual(state.summary()['recent_contact_fraction'], .5)

    def test_failure_alone_cannot_trigger_advance_from_prior_good_history(self):
        state = CurriculumState()
        state.observe([episode()] * 3)
        state.observe([episode(safe=False)])
        self.assertEqual(state.progress, 0.)
        self.assertEqual(state.count, 4)
        state.observe([episode()])
        self.assertEqual(state.progress, .1)

    def test_reach_only_reaches_press_then_requires_contact(self):
        state = CurriculumState()
        for _ in range(30):
            state.observe([episode(contact=0.)])
        self.assertEqual(state.progress, 1.)
        self.assertEqual(state.summary()['stage'], 'press')
        self.assertEqual(state.weights()['timing'], .35)
        self.assertEqual(state.weights()['contact'], 1.)
        for _ in range(20):
            state.observe([episode()])
        self.assertEqual(state.progress, 2.)
        self.assertEqual(state.summary()['stage'], 'song_connection')
        self.assertEqual(state.weights()['wrist'], .1)
        self.assertEqual(state.weights()['approach'], 0.)

    def test_one_large_batch_advances_only_one_step_and_weights_interpolate(self):
        state = CurriculumState()
        state.observe([episode()] * 30)
        self.assertEqual(state.progress, .1)
        self.assertAlmostEqual(state.weights()['wrist'], .935)
        self.assertAlmostEqual(state.weights()['contact'], .235)
        self.assertEqual(state.count, 8)
        self.assertEqual(state.cursor, 6)
        state.observe([episode(reach=0.)] * 8)
        self.assertEqual(state.progress, .1)

    def test_contact_alone_cannot_skip_wrist_placement(self):
        state = CurriculumState()
        for _ in range(15):
            state.observe([episode(reach=.69)])
        self.assertEqual(state.progress, 0.)

    def test_restore_preserves_ring_and_exact_future_progress(self):
        original = CurriculumState()
        original.observe([episode()] * 11)
        original.observe([episode(reach=.8, contact=.4)] * 2)
        saved = original.state_vector()
        self.assertEqual(saved.dtype, np.float64)
        self.assertEqual(saved.shape, (STATE_SIZE,))
        restored = CurriculumState()
        restored.load_state(saved)
        saved[:] = 0.
        np.testing.assert_array_equal(restored.state_vector(), original.state_vector())
        for metrics in ([episode(safe=False)], [episode()] * 7, []):
            self.assertEqual(restored.observe(metrics), original.observe(metrics))
            np.testing.assert_array_equal(restored.state_vector(), original.state_vector())

    def test_malformed_restore_rejected_without_mutation(self):
        state = CurriculumState()
        state.observe([episode()] * 4)
        before = state.state_vector()
        malformed = [np.zeros(STATE_SIZE - 1), np.zeros((1, STATE_SIZE))]
        for index, value in ((0, np.nan), (0, 2.1), (0, -.1),
                             (1, 8.5), (1, 9.), (2, 8.), (2, 1.),
                             (3, .5), (4, -1.), (5, 1.1), (18, 1.)):
            bad = before.copy()
            bad[index] = value
            malformed.append(bad)
        bad = before.copy()
        bad[3] = 0.  # Unsafe row must not retain successful metrics.
        malformed.append(bad)
        for bad in malformed:
            with self.subTest(vector=bad), self.assertRaises(ValueError):
                state.load_state(bad)
            np.testing.assert_array_equal(state.state_vector(), before)

    def test_invalid_metric_batch_rejected_without_partial_insertion(self):
        state = CurriculumState()
        before = state.state_vector()
        for invalid in (episode(reach=np.inf), episode(contact=1.1),
                        episode(safe=1)):
            with self.assertRaises(ValueError):
                state.observe([episode(), invalid])
            np.testing.assert_array_equal(state.state_vector(), before)


if __name__ == '__main__':
    unittest.main()
