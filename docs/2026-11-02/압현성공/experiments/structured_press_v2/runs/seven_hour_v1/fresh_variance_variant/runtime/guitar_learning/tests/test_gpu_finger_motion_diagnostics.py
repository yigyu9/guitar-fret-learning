"""CPU tensor diagnostics checks; no native motion, contact or audio claim."""
import math
import unittest

import torch

from guitar_learning.core.control import LEFT_HAND_NAMES
from guitar_learning.gpu.environment import TensorSongEnvironment, FINGER_MOTION_CONTRACT
from guitar_learning.tests import test_gpu_environment as fixtures


class FingerMotionDiagnosticsTests(unittest.TestCase):
    environment = fixtures.TensorSongTests.environment
    advance = staticmethod(fixtures.TensorSongTests.advance)

    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    @staticmethod
    def values(env, index=0):
        return env._finger_motion_episode(index)['values']

    def test_real_target_action_and_error_have_distinct_sampling_denominators(self):
        env, snapshot, _ = self.environment()
        joint, channel = int(env.finger_joint_indices[0]), int(env.finger_action_indices[0])
        low, high = float(env.finger_lower[0]), float(env.finger_upper[0])
        mid = (low+high)/2
        snapshot['q'][:, joint] = 0.
        snapshot['target'][:, joint] = low
        env.reset([0, 1], snapshot)
        for value, q, target in ((-.5, .2, high), (.25, .1, mid), (0., .15, low)):
            action = torch.zeros(2, 39); action[:, channel] = value
            env.begin_control(action)
            snapshot['q'][:, joint] = q
            snapshot['target'][:, joint] = target
            for _ in range(4):
                env.substep(snapshot)
            env.end_control()
        row = env._finger_motion_episode(0)
        self.assertEqual(row['joint_names'], list(LEFT_HAND_NAMES))
        self.assertEqual((row['range_samples'], row['endpoint_samples'], row['action_samples'], row['action_change_pairs']), (4, 3, 3, 2))
        values = row['values']
        self.assertTrue(all(len(v) == 21 and all(math.isfinite(x) for x in v) for v in values.values()))
        self.assertAlmostEqual(values['actual_min_rad'][0], 0.)  # t0 included.
        self.assertAlmostEqual(values['actual_range_rad'][0], .2, places=6)
        self.assertAlmostEqual(values['target_range_rad'][0], high-low, places=6)
        self.assertAlmostEqual(values['action_mean'][0], -.25/3)
        self.assertAlmostEqual(values['action_mean_abs'][0], .75/3)
        for field in ('action_positive_fraction', 'action_negative_fraction', 'action_zero_fraction'):
            self.assertAlmostEqual(values[field][0], 1/3)
        self.assertAlmostEqual(values['action_mean_abs_change'][0], .5)
        self.assertAlmostEqual(values['action_opposite_sign_fraction'][0], .5)
        # 직접 위치 요청은 native 범위 안으로 제한되므로 바깥 방향 누적 명령이 없다.
        self.assertEqual(values['limit_outward_command_fraction'][0], 0.)
        errors = [high-.2, mid-.1, low-.15]
        self.assertAlmostEqual(values['tracking_error_rms_rad'][0], math.sqrt(sum(e*e for e in errors)/3), places=6)
        self.assertAlmostEqual(values['tracking_error_max_abs_rad'][0], max(abs(e) for e in errors), places=6)

    def test_240hz_spike_is_not_claimed_as_60hz_extremum_and_first_delta_excluded(self):
        env, snapshot, _ = self.environment()
        joint, channel = int(env.finger_joint_indices[0]), int(env.finger_action_indices[0])
        snapshot['q'][:, joint] = 0.
        snapshot['target'][:, joint] = 0.
        env.reset([0, 1], snapshot)
        action = torch.zeros(2, 39); action[:, channel] = 1.
        env.begin_control(action)
        for q in (10., -.5, .3, .2):
            snapshot['q'][:, joint] = q
            snapshot['target'][:, joint] = .1
            env.substep(snapshot)
        env.end_control()
        row = env._finger_motion_episode(0)
        self.assertEqual(row['action_change_pairs'], 0)
        self.assertEqual(row['values']['action_mean_abs_change'][0], 0.)
        self.assertAlmostEqual(row['values']['actual_max_rad'][0], .2, places=6)
        self.assertEqual(row['values']['actual_min_rad'][0], 0.)
        self.assertAlmostEqual(row['values']['tracking_error_rms_rad'][0], .1, places=6)
        self.assertIn('not240Hz', FINGER_MOTION_CONTRACT['range_samples'])

    def test_h32_window_reset_preserves_episode_and_storage_size(self):
        env, snapshot, _ = self.environment()
        pointers = {k: (v.data_ptr(), v.shape) for k, v in env.finger_motion.items()}
        action = torch.zeros(2, 39); action[:, env.finger_action_indices] = .25
        for _ in range(32):
            self.advance(env, snapshot, action)
        env.reset_reward_window()  # A rollout/PPO window is not an episode reset.
        for _ in range(32):
            self.advance(env, snapshot, -action)
        row = env._finger_motion_episode(0)
        self.assertEqual((row['endpoint_samples'], row['range_samples'], row['action_change_pairs']), (64, 65, 63))
        self.assertAlmostEqual(row['values']['action_mean_abs'][0], .25)
        self.assertAlmostEqual(row['values']['action_mean_abs_change'][0], .5/63)
        self.assertAlmostEqual(row['values']['action_opposite_sign_fraction'][0], 1/63)
        self.assertEqual(pointers, {k: (v.data_ptr(), v.shape) for k, v in env.finger_motion.items()})
        self.assertEqual(sum(v.numel() for v in env.finger_motion.values()), 15*2*21+6*2*4)

    def test_partial_reset_changes_only_selected_diagnostics_and_new_t0(self):
        env, snapshot, _ = self.environment()
        action = torch.zeros(2, 39); action[:, env.finger_action_indices] = .5
        self.advance(env, snapshot, action)
        saved = {key: value[1].clone() for key, value in env.finger_motion.items()}
        previous = env.previous_action[1].clone()
        snapshot['q'][0, env.finger_joint_indices] += .125
        snapshot['target'][0, env.finger_joint_indices] -= .25
        env.reset([0], snapshot)
        self.assertEqual(env.steps.tolist(), [0, 1])
        for key, value in saved.items():
            torch.testing.assert_close(env.finger_motion[key][1], value)
        torch.testing.assert_close(env.previous_action[1], previous)
        reset = self.values(env)
        self.assertTrue(all(value == 0 for value in reset['actual_range_rad']))
        self.assertTrue(all(value == 0 for value in reset['target_range_rad']))
        torch.testing.assert_close(env.finger_motion['actual_min'][0], snapshot['q'][0, env.finger_joint_indices].double())
        self.advance(env, snapshot, -action)
        self.assertEqual(env._finger_motion_episode(0)['action_change_pairs'], 0)
        self.assertEqual(env._finger_motion_episode(1)['action_change_pairs'], 1)
        self.assertTrue(all(v == 0. for v in self.values(env, 0)['action_mean_abs_change']))
        self.assertTrue(all(v == 1. for v in self.values(env, 1)['action_mean_abs_change']))

    def test_diagnostics_do_not_change_learning_outputs_or_existing_episode_fields(self):
        left, snapshot, _ = self.environment()
        comparison, other, _ = self.environment()
        comparison._record_finger_motion = lambda: None
        action = torch.zeros(2, 39); action[:, left.finger_action_indices] = .2
        snapshot['body_state'][0, left.guitar_index, 0] += .1
        other['body_state'][0, comparison.guitar_index, 0] += .1
        a, b = self.advance(left, snapshot, action), self.advance(comparison, other, action)
        for key in a[0]:
            torch.testing.assert_close(a[0][key], b[0][key], rtol=0, atol=0)
        for first, second in zip(a[1:5], b[1:5]):
            torch.testing.assert_close(first, second, rtol=0, atol=0)
        self.assertEqual(len(a[5]), 1)
        self.assertIn('left_finger_motion', a[5][0])
        self.assertEqual(a[5][0]['left_finger_motion']['endpoint_samples'], a[5][0]['steps'])
        without = lambda e: {k: v for k, v in e.items() if k != 'left_finger_motion'}
        self.assertEqual(without(a[5][0]), without(b[5][0]))

    def test_right_has_no_diagnostics_or_left_bound_requirement(self):
        metadata, snapshot = fixtures.fixture()
        metadata['action_contract'] = dict(schema='fixture.control')
        env = TensorSongEnvironment(metadata, bundle=fixtures.BUNDLE, song=fixtures.SONG, hand='right', device='cpu')
        env.reset([0, 1], snapshot)
        self.assertNotIn('diagnostics', env.contract)
        self.assertFalse(hasattr(env, 'finger_motion'))
        snapshot['body_state'][0, env.guitar_index, 0] += .1
        completed = self.advance(env, snapshot)[5]
        self.assertNotIn('left_finger_motion', completed[0])

    def test_left_rejects_invalid_diagnostic_bound_contract(self):
        for key, value in (('action_lower_rad', [0.]*38), ('action_upper_rad', [float('nan')]*39)):
            metadata, _ = fixtures.fixture()
            metadata['action_contract'][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'bounds'):
                TensorSongEnvironment(metadata, bundle=fixtures.BUNDLE, song=fixtures.SONG, hand='left', device='cpu')


class FingerControlDiagnosticsTests(unittest.TestCase):
    def make(self, out=None, detail_ticks=600):
        from guitar_learning.gpu.episode_diagnostics import FingerControlDiagnostics
        return FingerControlDiagnostics(2, ['LH:index1_x', 'LH:index2'],
            torch.tensor([0, 1]), torch.tensor([2., 3.]), torch.tensor([1]),
            out, detail_control_ticks=detail_ticks)

    def test_completed_substep_denominators_and_selected_reset(self):
        from types import SimpleNamespace
        observer = self.make()
        observer.reset(torch.tensor([0, 1]))
        sample = dict(q=torch.tensor([[0., 1.], [0., 1.]]),
            qd=torch.tensor([[2., 3.], [2., 3.]]),
            dof_force_sensor=torch.tensor([[7., 8.], [7., 8.]]))
        for _ in range(128):  # H32 is not an episode reset.
            observer.record(torch.ones(2, 2)*2, torch.ones(2, 2), sample,
                            torch.tensor([[2., 0.], [2., 0.]]), SimpleNamespace())
        row = observer.episode(0)
        self.assertEqual(row['completed_physics_samples'], 128)
        self.assertAlmostEqual(row['duration_s'], 128/240)
        values = row['values']
        self.assertEqual(values['requested_tracking_error_rad_rms'], [2., 1.])
        self.assertEqual(values['applied_tracking_error_rad_rms'], [1., 0.])
        self.assertEqual(values['rate_limit_gap_rad_rms'], [1., 1.])
        self.assertEqual(values['submitted_effort_cap_fraction'], [1., 0.])
        self.assertEqual(row['submitted_effort_available'], [True, False])
        self.assertEqual(values['native_sensor_net_generalized_force_mean_abs_Nm'], [7., 8.])
        observer.reset(torch.tensor([0]))
        self.assertEqual(observer.episode(0)['completed_physics_samples'], 0)
        self.assertEqual(observer.episode(0)['episode_id'], 1)
        self.assertEqual(observer.episode(1)['completed_physics_samples'], 128)
        self.assertEqual(observer.episode(1)['episode_id'], 0)

    def test_nonfinite_sensor_is_excluded_without_touching_inputs(self):
        from types import SimpleNamespace
        observer = self.make()
        observer.reset(torch.tensor([0, 1]))
        sensor = torch.tensor([[float('nan'), 2.], [float('inf'), 3.]])
        sample = dict(q=torch.zeros(2, 2), qd=torch.zeros(2, 2), dof_force_sensor=sensor)
        observer.record(torch.zeros(2, 2), torch.zeros(2, 2), sample,
                        torch.zeros(2, 2), SimpleNamespace())
        row = observer.episode(0)
        self.assertEqual(row['sensor_samples'], [0, 1])
        self.assertEqual(row['values']['native_sensor_net_generalized_force_mean_abs_Nm'], [None, 2.])
        self.assertTrue(torch.isnan(sensor[0, 0]))
        self.assertEqual(row['env_id'], 0)

    def test_trace_budget_identity_absent_goals_and_no_state_mutation(self):
        import gzip
        import json
        import tempfile
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as out:
            observer = self.make(out, detail_ticks=1)
            observer.reset(torch.tensor([0, 1]))
            env = SimpleNamespace(action=torch.zeros(2, 2), finger_action_indices=torch.tensor([0, 1]),
                _score_time=lambda: torch.tensor([-3., -3.]),
                _finger_targets=lambda now: dict(indices=torch.full((2, 4, 2), -1),
                                                valid=torch.zeros(2, 4, 2, dtype=torch.bool)))
            sample = dict(q=torch.zeros(2, 2), qd=torch.ones(2, 2))
            for tick in range(6):
                if tick == 2:
                    observer.reset(torch.tensor([0]))
                observer.record(torch.zeros(2, 2), torch.zeros(2, 2), sample,
                                torch.zeros(2, 2), env)
            self.assertIsNone(observer.stream)
            with gzip.open(str(observer.path), 'rt') as stream:
                rows = [json.loads(line) for line in stream]
            self.assertEqual(len(rows), 4)
            self.assertEqual([r['episode_id'] for r in rows], [0, 0, 1, 1])
            self.assertEqual([r['episode_physics_step'] for r in rows], [1, 2, 1, 2])
            self.assertTrue(all(not t['target_present'] and t['target_index'] is None
                                for r in rows for t in r['targets']))
            self.assertIsNone(rows[0]['native_sensor_net_generalized_force_Nm'])
            self.assertEqual(float(sample['q'].abs().sum()), 0.)
            self.assertEqual(float(sample['qd'].sum()), 4.)
            self.assertEqual(observer.episode(0)['completed_physics_samples'], 4)


if __name__ == '__main__':
    unittest.main()
