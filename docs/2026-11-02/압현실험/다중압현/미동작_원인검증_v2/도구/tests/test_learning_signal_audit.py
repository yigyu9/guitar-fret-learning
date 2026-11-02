"""CPU checks for target timing and temporal comparisons used by the audit."""
import importlib.util
from pathlib import Path
import unittest

import numpy as np

SPEC = importlib.util.spec_from_file_location('learning_signal_audit',
    Path(__file__).resolve().parents[1]/'learning_signal_audit.py')
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class LearningSignalTests(unittest.TestCase):
    def test_real_compiled_press_differs_from_onset_and_approach_is_delayed(self):
        task = AUDIT.make_task(AUDIT.BUNDLE, pre_roll_s=3., tail_s=.5)
        self.assertEqual([t.press_s for t in task.targets], [3., 3.])
        self.assertEqual([t.onset_s for t in task.targets], [3.24, 3.3])
        rows = AUDIT.gate_table(task, [.995, 1., 2.5, 2.6, 2.65])
        self.assertEqual(rows[0]['targets_exposed'][:2], [False, False])
        self.assertEqual(rows[1]['targets_exposed'][:2], [True, True])
        self.assertEqual(task.lookahead_s, 4.)
        self.assertEqual(rows[0]['general_events_visible'], [True, True])
        self.assertEqual(rows[1]['general_events_visible'], [True, True])
        self.assertEqual(rows[2]['approach_tracking_weight'][:2], [0., 0.])
        np.testing.assert_allclose(rows[3]['approach_tracking_weight'][:2], [.5, .5])
        np.testing.assert_allclose(rows[4]['approach_tracking_weight'][:2], [1., 1.])

    def test_temporal_correlation_excludes_reset_pair_and_held_substeps(self):
        rows = []
        for episode in (0, 1):
            for tick in range(1, 4):
                for substep in range(1, 5):
                    rows.append(dict(env_id=0, episode_id=episode,
                        control_tick=tick, substep=substep, action=[(-1.)**tick]))
        result = AUDIT.temporal(rows, [0])
        self.assertEqual(result['control_samples'], 6)
        self.assertEqual(result['adjacent_pairs'], 4)
        np.testing.assert_allclose(result['action_lag1'], [-1.])
        self.assertEqual(result['opposite_sign_fraction'], [1.])

    def test_matched_absolute_commands_have_equal_variance_and_filter_attenuation(self):
        result = AUDIT.matched_noise(count=3200)
        for row in result['response_by_tau_s'].values():
            self.assertAlmostEqual(row['iid_K1']['command_std'], row['held_K16']['command_std'])
            self.assertLess(row['iid_K1']['response_std'], row['held_K16']['response_std'])
            self.assertLess(row['held_K16']['response_std'], result['command_std'])


if __name__ == '__main__':
    unittest.main()
