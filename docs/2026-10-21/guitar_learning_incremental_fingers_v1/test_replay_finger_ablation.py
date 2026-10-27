"""CPU-only ablation selection/action/comparison checks; no native pool/GL."""
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

PHASE = Path(__file__).resolve().parent
sys.path.insert(0, str(PHASE))
import replay_finger_ablation as replay


def report():
    return dict(completed=True, source_optimizer_updates=100, num_envs=1024, deterministic=True,
        gpu_scene=dict(closed=True, physx_use_gpu=True, use_gpu_pipeline=True),
        episodes=[dict(env_id=i, reason='timeline_complete', left_curriculum=dict(full_safe=True)) for i in range(1024)])


class ReplayAblationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.control = json.loads((PHASE/'probe_n4_retry02/control_contract.json').read_text())
        cls.order = cls.control['action_order']

    def test_lowest_captured_failure_only_and_no_score_selection(self):
        value = report()
        self.assertIsNone(replay.select_failure(value))
        for i in (7, 2, 900):
            value['episodes'][i].update(reason='terminal_failure', left_curriculum=dict(full_safe=False), musical_score=1000-i)
        self.assertEqual(replay.select_failure(value)['env_id'], 2)
        value['episodes'][2].update(reason='timeline_complete', left_curriculum=dict(full_safe=True))
        self.assertEqual(replay.select_failure(value)['env_id'], 7)
        value['episodes'][7].update(reason='timeline_complete', left_curriculum=dict(full_safe=True))
        self.assertIsNone(replay.select_failure(value))  # Uncaptured env900 is not eligible.

    def test_4cases_keep_other18_actions_identical_and_do_not_mutate_source(self):
        action = np.linspace(-.95, .95, 39, dtype=np.float32); before = action.copy()
        actual = replay.case_actions(action, self.order, [True]*4)
        thumb = [i for i, n in enumerate(self.order) if n.startswith('LH:thumb')]
        fingers = [i for i, n in enumerate(self.order) if n.startswith('LH:') and not n.startswith('LH:thumb')]
        other = [i for i, n in enumerate(self.order) if not n.startswith('LH:')]
        np.testing.assert_array_equal(actual[:, other], np.repeat(action[None, other], 4, axis=0))
        np.testing.assert_array_equal(actual[0], action)
        np.testing.assert_array_equal(actual[1, fingers], action[fingers])
        np.testing.assert_array_equal(actual[2, thumb], action[thumb])
        self.assertTrue((actual[1, thumb] == 0).all() and (actual[2, fingers] == 0).all() and (actual[3, thumb+fingers] == 0).all())
        np.testing.assert_array_equal(action, before)

    def test_ended_rows_get_zero39_padding_and_live_rows_keep_prescribed_actions(self):
        action = np.full(39, .2, dtype=np.float32)
        all_live = replay.case_actions(action, self.order, [True]*4)
        actual = replay.case_actions(action, self.order, [True, False, True, False])
        np.testing.assert_array_equal(actual[[0, 2]], all_live[[0, 2]])
        self.assertTrue((actual[[1, 3]] == 0).all())

    def test_reference_error_uses_only_common_prefix_and_antipodal_quaternion(self):
        def trace(frames):
            body = np.zeros((frames, 106, 13)); body[..., 6] = 1
            return dict(clock=np.arange(frames)*4, body_state=body,
                q=np.zeros((frames, 105)), qd=np.zeros((frames, 105)), target=np.zeros((frames, 105)))
        source, other = trace(6), trace(3)
        native, _ = replay.mapping(self.control)
        other['body_state'][..., 0] = .01; other['body_state'][..., 6] = -1
        other['q'][:, 1] = .02; other['qd'][:, 1] = .04; other['target'][:, native] = .003
        value = replay.reference_errors(source, other, native, dict(task_time_s=5/60), dict(reason='terminal_failure', task_time_s=2/60))
        self.assertEqual(value['common_control_steps'], 2)
        self.assertAlmostEqual(value['body_position_max_error_m'], .01)
        self.assertEqual(value['body_rotation_max_error_rad'], 0.)
        self.assertAlmostEqual(value['q_max_abs_error_rad'], .02)
        self.assertAlmostEqual(value['qd_max_abs_error_rad_s'], .04)
        self.assertAlmostEqual(value['left21_target_max_abs_error_rad'], .003)
        self.assertAlmostEqual(value['failure_time_delta_s'], -3/60)
        censored = replay.reference_errors(source, other, native, dict(task_time_s=5/60), None)
        self.assertIsNone(censored['failure_time_delta_s'])
        self.assertFalse(censored['replay_failure_observed'])

    def test_no_captured_failure_path_creates_not_applicable_without_native_import(self):
        self.assertNotIn('isaacgym', sys.modules)
        with tempfile.TemporaryDirectory() as folder:
            source, out = Path(folder)/'source', Path(folder)/'output'; source.mkdir()
            (source/'report.json').write_text(json.dumps(report()))
            (source/'inputs_before.json').write_text('{}')
            with patch.object(sys, 'argv', ['replay_finger_ablation', '--evaluation', str(source), '--out', str(out)]), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(replay.main(), 0)
            value = json.loads((out/'report.json').read_text())
            self.assertEqual(value['status'], 'not_applicable')
            self.assertFalse(value['completed'] or value['applicable'])
            self.assertEqual(value['GPU_simulators_created'], 0)
        self.assertNotIn('isaacgym', sys.modules)
        self.assertNotIn('torch', sys.modules)
        self.assertNotIn('mujoco', sys.modules)

    def test_incomplete_or_wrong_checkpoint_is_rejected(self):
        for key, value in (('completed', False), ('source_optimizer_updates', 0), ('num_envs', 4)):
            sample = report(); sample[key] = value
            with self.subTest(field=key), self.assertRaises(ValueError):
                replay.select_failure(sample)


if __name__ == '__main__':
    unittest.main(verbosity=2)
