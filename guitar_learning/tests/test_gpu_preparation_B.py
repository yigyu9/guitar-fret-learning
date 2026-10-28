"""Optional per-finger B preference; CPU accounting, not native reachability."""
import copy
from dataclasses import replace
import math
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import torch
from scipy.spatial.transform import Rotation

from guitar_learning.gpu.finger_reward import (
    B_PREPARATION_INPUT_DEGREES, B_PREPARATION_SPREAD_DEGREES,
    B_PREPARATION_ANGLES_DEGREES, FINGER_COORDINATION_CONTRACT,
    FINGER_PREPARATION_CONTRACT, finger_preparation_reward)
from guitar_learning.training.policy import SpecialistPolicy
from guitar_learning.song.task import ScoreTask
from guitar_learning.song.curriculum_runtime import CurriculumCoordinator
from guitar_learning.tests import test_gpu_environment as fixtures
from guitar_learning.tests import test_gpu_finger_reward as posture_fixtures
from guitar_learning.tests import test_gpu_continuous_clean as clean_fixtures
from guitar_learning.tests.test_gpu_surface_learning import task
from guitar_learning.training.ppo import PPOTrainer


def inputs(times=(0.,)):
    n = len(times)
    data = posture_fixtures.FingerPostureTests().inputs(times=times)
    segments = []
    for (mcp, pip, dip), spread in zip(B_PREPARATION_INPUT_DEGREES, B_PREPARATION_SPREAD_DEGREES):
        first = Rotation.from_rotvec([math.radians(mcp), 0., math.radians(spread)])
        second = first*Rotation.from_euler('x', pip, degrees=True)
        third = second*Rotation.from_euler('x', dip, degrees=True)
        segments.append([q.as_quat() for q in (first, second, third)])
    data.update(onset=torch.tensor([4.], dtype=torch.float64),
        end=torch.tensor([5.], dtype=torch.float64), press=torch.tensor([3.], dtype=torch.float64),
        finger=torch.tensor([1]), contact=torch.zeros(n, 4, dtype=torch.bool),
        distance=torch.ones(n, 1, dtype=torch.float64),
        segment_quaternion=torch.tensor(np.array(segments), dtype=torch.float64).expand(n, -1, -1, -1).clone())
    return data


class PreparationBTests(unittest.TestCase):
    environment = fixtures.TensorSongTests.environment
    advance = staticmethod(fixtures.TensorSongTests.advance)
    tree_equal = clean_fixtures.ContinuousCleanTests.tree_equal

    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def test_selected_B_geometry_gets_small_maximum_without_changing_inputs(self):
        data = inputs(); saved = copy.deepcopy(data)
        result = finger_preparation_reward(**data)
        torch.testing.assert_close(result['quality'], torch.ones(1, 4, dtype=torch.float64), rtol=0, atol=1e-14)
        self.assertAlmostEqual(float(result['rate']), .02, places=14)
        for key in data:
            torch.testing.assert_close(data[key], saved[key], rtol=0, atol=0)
        self.assertEqual(FINGER_PREPARATION_CONTRACT['coordination_rate_per_s'], 0.)
        self.assertEqual(FINGER_COORDINATION_CONTRACT['coordination_rate_per_s'], .05)

    def test_broad_flat_band_and_independent_outside_scalar_formula(self):
        for offset in (-15., -14., 0., 14., 15., 45.):
            data = inputs(); angles = torch.tensor(B_PREPARATION_ANGLES_DEGREES)+offset
            relative = Rotation.from_euler('x', angles.flatten().numpy(), degrees=True).as_quat().reshape(4, 3, 4)
            for f in range(4):
                accumulated = Rotation.identity()
                for j in range(3):
                    accumulated = accumulated*Rotation.from_quat(relative[f, j])
                    data['segment_quaternion'][0, f, j] = torch.tensor(accumulated.as_quat())
            expected = .02/(1+3*max(abs(offset)-15., 0.)**2/30**2)
            self.assertAlmostEqual(float(finger_preparation_reward(**data)['rate']), expected, places=9)

    def test_preparation_hold_and_boundaries_only_block_assigned_finger(self):
        for finger in range(1, 5):
            data = inputs(times=(2.7, 3., 4., 5.))
            data['finger'].fill_(finger)
            result = finger_preparation_reward(**data)
            expected = torch.ones(4, 4, dtype=torch.float64)
            expected[:, finger-1] = 0.
            torch.testing.assert_close(result['gate'], expected, rtol=0, atol=0)
            torch.testing.assert_close(result['rate'], torch.full((4,), .015, dtype=torch.float64), rtol=0, atol=1e-14)

    def test_temporal_fade_and_overlapping_next_note(self):
        data = inputs(times=(2.55, 2.6, 2.65, 5.05, 5.1, 5.15))
        result = finger_preparation_reward(**data)
        torch.testing.assert_close(result['gate'][:, 0], torch.tensor([1., .5, 0., 0., .5, 1.], dtype=torch.float64))
        torch.testing.assert_close(result['gate'][:, 1:], torch.ones(6, 3, dtype=torch.float64))
        data.update(onset=torch.tensor([4., 6.], dtype=torch.float64), end=torch.tensor([5., 7.], dtype=torch.float64),
            press=torch.tensor([3., 5.], dtype=torch.float64), finger=torch.tensor([1, 4]), distance=torch.ones(6, 2))
        result = finger_preparation_reward(**data)
        torch.testing.assert_close(result['gate'][-3:],
            torch.tensor([[0., 1., 1., 0.], [.5, 1., 1., 0.], [1., 1., 1., 0.]], dtype=torch.float64),
            rtol=0, atol=1e-14)
        # Overlapping notes on the same finger keep that finger busy once.
        data['finger'].fill_(1)
        result = finger_preparation_reward(**data)
        self.assertEqual(result['gate'][-3:].tolist(), [[0., 1., 1., 1.]]*3)

    def test_residual_contact_does_not_block_score_idle_finger(self):
        data = inputs(times=(2., 2.)); data['contact'][1, 0] = True
        result = finger_preparation_reward(**data)
        self.assertEqual(result['gate'].tolist(), [[1., 1., 1., 1.], [1., 1., 1., 1.]])
        self.assertAlmostEqual(float(result['rate'][1]), .02, places=14)

    def test_stale_future_and_absent_finger_contact_masks_cannot_block(self):
        data = inputs(times=(0., 2., 6.))
        data['contact'][:] = True
        result = finger_preparation_reward(**data)
        self.assertEqual(result['contact_veto'].tolist(),
                         [[False]*4]*3)
        self.assertEqual(result['gate'].tolist(),
                         [[1.]*4]*3)

    def test_guard_is_inclusive_and_ignores_nonfinite_stale_future_distances(self):
        data = inputs(times=(.999, 1., 2., 5., 5.001, 6.))
        data['distance'][:] = float('nan')
        result = finger_preparation_reward(**data)
        self.assertEqual(result['relevant_targets'][:, 0].tolist(),
                         [False, True, True, True, False, False])
        self.assertEqual(result['nonfinite_veto'][:, 0].tolist(),
                         [False, True, True, True, False, False])
        self.assertFalse(result['near_veto'].any())
        self.assertFalse(result['nonfinite_veto'][:, 1:].any())
        self.assertEqual(result['gate'][0].tolist(), [1.]*4)
        self.assertEqual(result['gate'][-1].tolist(), [1.]*4)

    def test_short_idle_window_preserves_gaps_between_same_finger_notes(self):
        data = inputs(times=(3., 3.075, 3.15, 3.5, 3.575, 3.65, 4., 5.15))
        data.update(onset=torch.tensor([2.5, 4.5], dtype=torch.float64),
                    end=torch.tensor([3., 5.], dtype=torch.float64),
                    press=torch.tensor([2., 4.], dtype=torch.float64),
                    finger=torch.tensor([1, 1]), distance=torch.ones(8, 2))
        result = finger_preparation_reward(**data)
        torch.testing.assert_close(result['idle_weight'][:, 0],
            torch.tensor([0., .25, 1., 1., .75, 0., 0., 1.], dtype=torch.float64),
            atol=1e-14, rtol=0)
        torch.testing.assert_close(result['gate'][:, 1:], torch.ones(8, 3, dtype=torch.float64))

    def test_finite_near_distances_allow_recovery_and_invalid_distances_veto(self):
        data = inputs(times=(2.,)*5)
        data['distance'][:, 0] = torch.tensor([.039, .04, .040001, float('nan'), float('inf')])
        result = finger_preparation_reward(**data)
        self.assertEqual(result['gate'][:, 0].tolist(), [1., 1., 1., 0., 0.])
        torch.testing.assert_close(result['gate'][:, 1:], torch.ones(5, 3, dtype=torch.float64))
        torch.testing.assert_close(result['rate'], torch.tensor([.02, .02, .02, .015, .015], dtype=torch.float64), atol=1e-14, rtol=0)

    def test_only_own_relevant_targets_veto_and_absent_fingers_keep_fixed_four_denominator(self):
        data = inputs(times=(6., 6.))
        data.update(onset=torch.tensor([4., 8., 9.]), end=torch.tensor([5., 9., 10.]),
            press=torch.tensor([3., 7., 8.]), finger=torch.tensor([1, 1, 3]),
            distance=torch.tensor([[1., .04, 1.], [1., 1., float('nan')]], dtype=torch.float64))
        result = finger_preparation_reward(**data)
        self.assertEqual(result['gate'].tolist(), [[1., 1., 1., 1.], [1., 1., 0., 1.]])
        torch.testing.assert_close(result['rate'], torch.tensor([.02,.015], dtype=torch.float64), atol=1e-14, rtol=0)
        data['contact'][:] = True
        data['contact'][:, 1] = False  # Absent fingers retain their independent bonuses.
        torch.testing.assert_close(finger_preparation_reward(**data)['rate'],
                                   torch.tensor([.02,.015], dtype=torch.float64), atol=1e-14, rtol=0)

    def test_busy_finger_B_quality_cannot_change_any_idle_finger_reward(self):
        data = inputs(times=(3.,))
        before = finger_preparation_reward(**data)
        data['segment_quaternion'][:, 0] = 0.
        after = finger_preparation_reward(**data)
        self.assertEqual(float(after['quality'][0, 0]), 0.)
        torch.testing.assert_close(before['rate'], after['rate'], atol=0, rtol=0)
        torch.testing.assert_close(before['quality'][:, 1:], after['quality'][:, 1:], atol=0, rtol=0)

    def test_empty_score_zero_and_bad_pose_finger_gets_no_credit(self):
        data = inputs()
        for key in ('onset', 'end', 'press', 'finger'):
            data[key] = data[key][:0]
        data['distance'] = torch.empty(1, 0)
        empty = finger_preparation_reward(**data)
        self.assertEqual(float(empty['rate']), 0.)
        self.assertEqual(empty['gate'].tolist(), [[0.]*4])
        for invalid in (0., float('nan')):
            data = inputs(); data['segment_quaternion'][:, 0] = invalid
            result = finger_preparation_reward(**data)
            self.assertEqual(float(result['quality'][0, 0]), 0.)
            self.assertAlmostEqual(float(result['rate']), .015, places=14)

    def test_contact_and_distance_shape_validation(self):
        for key, value in (('contact', torch.zeros(1, 4)), ('contact', torch.zeros(1, dtype=torch.bool)),
                           ('contact', torch.zeros(1, 3, dtype=torch.bool)),
                           ('distance', torch.ones(1, 2)), ('distance', torch.ones(1))):
            data = inputs(); data[key] = value
            with self.assertRaisesRegex(ValueError, 'Aligned'):
                finger_preparation_reward(**data)

    def test_actual_environment_preparation_and_holding_have_no_posture_reward(self):
        env, row, _ = self.environment(task=task())
        self.advance(env, row)
        self.assertFalse(env.terms['song_finger_coordination'].any())
        self.assertFalse(env.terms['song_finger_standby'].any())
        self.assertEqual(env.contract['reward']['schema'], 'guitar_learning.gpu_tensor_song_reward.v22')
        self.assertEqual(env.contract['reward']['finger_posture']['schema'], FINGER_PREPARATION_CONTRACT['schema'])

    def idle_environment(self, score=None):
        env, row, _ = self.environment(task=score or task(onset=10., end=11., press=10.))
        # Put every target far away in this CPU measurement fixture. It is not
        # a physically reachable hand-pose or native stability test.
        row['body_state'][:, env.finger_segment_indices.flatten(), 2] += 1.
        palm = Rotation.from_quat(row['body_state'][:, env.finger_palm_index, 3:7].numpy())
        relative = inputs(times=(0., 0.))['segment_quaternion'].numpy()
        for finger in range(4):
            for segment in range(3):
                rotation = palm*Rotation.from_quat(relative[:, finger, segment])
                row['body_state'][:, env.finger_segment_indices[finger, segment], 3:7] = torch.tensor(rotation.as_quat()).float()
        env.reset([0, 1], row)
        self.assertTrue((env.surface_distance > .04).all())
        return env, row

    def test_real_environment_each_segment_load_alone_never_vetoes_and_integrates_240hz(self):
        for segment in range(3):
            env, row = self.idle_environment(task(onset=1.5, end=2.5, press=1.5))
            saved = {key:value.clone() for key,value in row.items()}
            row['contact_force'][1, env.finger_segment_indices[2, segment], 2] = .02
            with patch('guitar_learning.gpu.environment.finger_preparation_reward', wraps=finger_preparation_reward) as measured:
                self.advance(env, row)
            self.assertEqual(measured.call_count, 4)
            for call in measured.call_args_list:
                self.assertEqual(call.args[7].tolist(), [[False]*4, [False]*4])
            torch.testing.assert_close(env.terms['song_finger_standby'], torch.tensor([.02/60, .02/60]), atol=4e-11, rtol=0)
            self.assertFalse(env.terms['song_finger_coordination'].any())
            saved['contact_force'][1, env.finger_segment_indices[2, segment], 2] = .02
            for key in row:
                torch.testing.assert_close(row[key], saved[key], rtol=0, atol=0)

    def test_real_environment_previous_candidate_and_wrong_allow_recovery(self):
        env, row = self.idle_environment(task(onset=1.5, end=2.5, press=1.5))
        env.previous_candidate[0, 1] = True
        env.previous_wrong[1, 2] = True
        with patch('guitar_learning.gpu.environment.finger_preparation_reward', wraps=finger_preparation_reward) as measured:
            self.advance(env, row)
        self.assertEqual(measured.call_args_list[0].args[7].tolist(),
                         [[False, True, False, False], [False, False, True, False]])
        for call in measured.call_args_list[1:]:
            self.assertFalse(call.args[7].any())
        expected = .02/60
        torch.testing.assert_close(env.terms['song_finger_standby'], torch.full((2,), expected), atol=3e-11, rtol=0)

    def test_real_environment_current_events_and_near_allow_recovery(self):
        env, row = self.idle_environment(task(onset=1.5, end=2.5, press=1.5))
        snapshot = env._snapshot
        def inject_events(value):
            snapshot(value)
            # Isolate event/proximity attribution after normal source measure.
            env.candidate[0, 3] = True
            env.wrong[1, 0] = True
            env.surface_distance[0, 1] = .04
            env.surface_distance[1, 2] = .039
        with patch.object(env, '_snapshot', side_effect=inject_events), patch(
                'guitar_learning.gpu.environment.finger_preparation_reward', wraps=finger_preparation_reward) as measured:
            self.advance(env, row)
        for call in measured.call_args_list:
            self.assertEqual(call.args[7].tolist(), [[False, False, False, True], [True, False, False, False]])
            result = finger_preparation_reward(*call.args)
            self.assertEqual(result['gate'].tolist(), [[1.,1.,1.,1.]]*2)
        torch.testing.assert_close(env.terms['song_finger_standby'], torch.full((2,), .02/60), atol=3e-11, rtol=0)

    def test_real_environment_reordered_targets_keep_contact_information_without_recovery_veto(self):
        env, row = self.idle_environment(task((3, 1, 3), onset=1.5, end=2.5, press=1.5))
        snapshot = env._snapshot
        def inject_events(value):
            snapshot(value)
            env.candidate[0, 0] = True
            env.candidate[0, 2] = True
            env.wrong[1, 1] = True
        with patch.object(env, '_snapshot', side_effect=inject_events), patch(
                'guitar_learning.gpu.environment.finger_preparation_reward', wraps=finger_preparation_reward) as measured:
            self.advance(env, row)
        for call in measured.call_args_list:
            self.assertEqual(call.args[7].tolist(), [[False, False, True, False], [True, False, False, False]])
        torch.testing.assert_close(env.terms['song_finger_standby'], torch.full((2,), .02/60), atol=4e-11, rtol=0)

    def test_real_environment_stale_event_does_not_block_another_relevant_note_of_same_finger(self):
        base = task((1, 1, 2), onset=2.5, end=3.5, press=2.5)
        score = ScoreTask((replace(base.targets[0], onset_s=.1, end_s=.2, press_s=.1),
                           base.targets[1],
                           replace(base.targets[2], onset_s=10., end_s=11., press_s=10.)))
        env, row = self.idle_environment(score)
        env.clock[:] = 240  #1s: note0 expired, note1 relevant, note2 future.
        env.previous_candidate[:, 0] = True
        env.previous_wrong[:, 2] = True
        snapshot = env._snapshot
        def inject_events(value):
            snapshot(value)
            env.candidate[:, 0] = True
            env.wrong[:, 2] = True
            env.surface_distance[:, 0] = float('nan')
            env.surface_distance[:, 2] = .01
        with patch.object(env, '_snapshot', side_effect=inject_events), patch(
                'guitar_learning.gpu.environment.finger_preparation_reward', wraps=finger_preparation_reward) as measured:
            self.advance(env, row)
        for call in measured.call_args_list:
            self.assertFalse(call.args[7].any())
        torch.testing.assert_close(env.terms['song_finger_standby'],
                                   torch.full((2,), .02/60), atol=4e-11, rtol=0)
        diagnostics = env.episode_diagnostics.episode(0)['standby']
        self.assertEqual(diagnostics['contact_excluded_s'], [0.]*4)
        self.assertEqual(diagnostics['proximity_excluded_s'], [0.]*4)
        self.assertEqual(diagnostics['nonfinite_distance_excluded_s'], [0.]*4)
        self.assertEqual(diagnostics['eligible_s'], [1/60]*4)

    def test_v22_checkpoint_roundtrip_rejects_legacy_v20_without_state_mutation(self):
        env, _, _ = self.environment()
        pool = SimpleNamespace(environment=env, set_curriculum=env.set_curriculum)
        def make(contract):
            policy = SpecialistPolicy(contract['observation']['dimension'], size='small', role='left', contract=contract)
            coordinator = CurriculumCoordinator(policy, pool)
            return PPOTrainer(policy), coordinator
        current, coordinator = make(env.contract)
        self.assertEqual(tuple(current.policy.left_curriculum_state.shape), (3331,))
        self.assertEqual(current.policy.architecture['finger_actor']['schema'], 'guitar_learning.targeted_finger_actor.v1')
        self.assertEqual(current.policy.architecture['priority_slots'], tuple(env.contract['observation']['finger_targets']['slots']))
        evidence = dict(valid=True, reason='timeline_complete', left_curriculum=dict(full_safe=True,
            finger_metrics=[dict(target_count=n, near_fraction=1., contact_fraction=0., success_fraction=0.)
                            for n in env.finger_counts]))
        coordinator.advance([evidence]*256, env.observation())
        for optimizer in (current.actor_optimizer, current.value_optimizer):
            for group in optimizer.param_groups:
                for parameter in group['params']:
                    parameter.grad = torch.ones_like(parameter)
            optimizer.step(); optimizer.zero_grad()
        current.updates, current.cost_weight = 7, 1.25
        old = copy.deepcopy(env.contract)
        old['reward']['schema'] = 'guitar_learning.gpu_tensor_song_reward.v20'
        old['observation']['dimension'] = 544
        old['observation']['fields'] = old['observation']['fields'][:544]
        old['observation']['scales'] = old['observation']['scales'][:544]
        old['observation'].pop('thumb_support')
        previous, _ = make(old)
        self.assertEqual(tuple(current.policy.state_dict()), tuple(previous.policy.state_dict()))
        with tempfile.TemporaryDirectory() as folder, patch('torch.cuda.is_available', return_value=False):
            newpath, oldpath = Path(folder)/'v22.pt', Path(folder)/'v20.pt'
            current.save(newpath); previous.save(oldpath)
            resumed, restored_coordinator = make(env.contract)
            resumed.load(newpath); restored_coordinator.restore()
            self.tree_equal(current.policy.state_dict(), resumed.policy.state_dict())
            self.tree_equal(current.actor_optimizer.state_dict(), resumed.actor_optimizer.state_dict())
            self.tree_equal(current.value_optimizer.state_dict(), resumed.value_optimizer.state_dict())
            np.testing.assert_array_equal(coordinator.state.state_vector(), restored_coordinator.state.state_vector())
            self.assertEqual((resumed.updates, resumed.cost_weight), (7, 1.25))
            before = copy.deepcopy((resumed.policy.state_dict(), resumed.actor_optimizer.state_dict(),
                resumed.value_optimizer.state_dict(), resumed.updates, resumed.cost_weight,
                restored_coordinator.state.state_vector(), torch.get_rng_state(), np.random.get_state()))
            with self.assertRaisesRegex(ValueError, 'mismatch'):
                resumed.load(oldpath)
            self.tree_equal(before, (resumed.policy.state_dict(), resumed.actor_optimizer.state_dict(),
                resumed.value_optimizer.state_dict(), resumed.updates, resumed.cost_weight,
                restored_coordinator.state.state_vector(), torch.get_rng_state(), np.random.get_state()))
