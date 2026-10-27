"""Distance tracking independent of contact; original contact rewards retained.

CPU formula/integration checks use source mesh snapshots and synthetic rigid
poses, not native pressure or training-performance measurements.
"""
import copy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import torch

from guitar_learning.gpu.finger_reward import finger_tracking_reward, FINGER_REWARD_CONTRACT
from guitar_learning.gpu.fingertip_pad import pad_tracking_reward, FINGERTIP_TRACKING_CONTRACT
from guitar_learning.skills.specialist_policy import SpecialistPolicy
from guitar_learning.song.curriculum_runtime import CurriculumCoordinator
from guitar_learning.tests import test_gpu_environment as fixtures
from guitar_learning.tests.test_gpu_surface_learning import task
from guitar_learning.training.ppo import PPOTrainer


def inputs(n=1, m=1):
    return dict(now=torch.ones(n), onset=torch.full((m,), .5), end=torch.full((m,), 2.),
                press=torch.full((m,), .4), finger=torch.ones(m, dtype=torch.long),
                delta=torch.zeros(n, m, 3), velocity=torch.zeros(n, m, 3),
                candidate=torch.zeros(n, m, dtype=torch.bool), actions=torch.zeros(n, 21),
                alignment=torch.ones(n, m))


class TrackingContactIndependenceTests(unittest.TestCase):
    environment = fixtures.TensorSongTests.environment
    advance = staticmethod(fixtures.TensorSongTests.advance)

    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def test_candidate_toggle_is_exactly_equal_for_rate_quality_and_selection(self):
        data = inputs(n=3, m=4)
        data['finger'] = torch.arange(1, 5)
        data['delta'][:, :, 0] = torch.tensor([0., .01, .04, .12])
        data['alignment'][:] = torch.tensor([-1., .5, 0., 1.])
        off = pad_tracking_reward(**data)
        data['candidate'].fill_(True)
        on = pad_tracking_reward(**data)
        for key in ('rate', 'quality', 'indices', 'valid'):
            self.assertTrue(torch.equal(on[key], off[key]), key)
        # At alignment1, the new term matches the historical no-contact rate
        # and is half the historical loaded-candidate rate.
        data['alignment'].fill_(1.)
        new = pad_tracking_reward(**data)
        legacy_args = {key:value for key,value in data.items() if key != 'alignment'}
        old_on = finger_tracking_reward(**legacy_args)
        legacy_args['candidate'] = torch.zeros_like(data['candidate'])
        old_off = finger_tracking_reward(**legacy_args)
        torch.testing.assert_close(new['rate'], old_off['rate'], atol=0, rtol=0)
        torch.testing.assert_close(new['quality'], old_off['quality'], atol=0, rtol=0)
        torch.testing.assert_close(new['rate']*2, old_on['rate'], atol=0, rtol=0)
        self.assertEqual(FINGER_REWARD_CONTRACT['schema'], 'guitar_learning.gpu_finger_tracking_rate.v5')
        self.assertEqual(FINGER_REWARD_CONTRACT['candidate_multiplier'], 2.)

    def test_independent_scalar_distance_and_near_alignment_formula_and_bound(self):
        data = inputs(n=7)
        distances = [0., .005, .01, .019, .02, .04, .2]
        cosines = [-1., 0., .5, 2., -1., .3, -1.]
        data['delta'][:, 0, 2] = torch.tensor(distances)
        data['alignment'][:, 0] = torch.tensor(cosines)
        data['candidate'][::2] = True
        result = pad_tracking_reward(**data)
        expected = []
        for distance, cosine in zip(distances, cosines):
            near = min(max(1-distance/.02, 0.), 1.)
            facing = min(max(cosine, 0.), 1.)
            expected.append(2/(1+distance/.04)**2*(1-.2*near*(1-facing)))
        torch.testing.assert_close(result['rate'], torch.tensor(expected), atol=2e-7, rtol=0)
        self.assertTrue(((result['rate'] >= 0) & (result['rate'] <= 2.)).all())
        perfect = inputs(n=2, m=4)
        perfect['finger'] = torch.arange(1, 5)
        perfect['candidate'][1] = True
        torch.testing.assert_close(pad_tracking_reward(**perfect)['rate'], torch.full((2,), 2.), atol=0, rtol=0)
        self.assertEqual(FINGERTIP_TRACKING_CONTRACT['schema'], 'guitar_learning.gpu_finger_tracking_rate.v7')
        self.assertEqual(FINGERTIP_TRACKING_CONTRACT['candidate_multiplier'], 1.)
        self.assertEqual(FINGERTIP_TRACKING_CONTRACT['rate_bounds_per_s'], [0., 2.])
        self.assertNotIn('(1+candidate)', FINGERTIP_TRACKING_CONTRACT['quality'])

    def test_far_alignment_motion_and_actions_have_no_effect_or_input_mutation(self):
        data = inputs(n=3)
        data['delta'][:, 0, 0] = torch.tensor([.02, .04, 1.])
        saved = {key:value.clone() for key,value in data.items()}
        reference = pad_tracking_reward(**data)
        for key,value in saved.items():
            torch.testing.assert_close(data[key], value, atol=0, rtol=0)
        data['alignment'].fill_(-1.)
        data['velocity'].fill_(1000.)
        data['actions'][:] = torch.linspace(-1., 1., 21)
        data['candidate'].fill_(True)
        changed = pad_tracking_reward(**data)
        for key in reference:
            torch.testing.assert_close(changed[key], reference[key], atol=0, rtol=0)

    def test_selector_present_finger_denominator_and_mixed_valid_windows(self):
        data = inputs(n=4, m=3)
        data.update(now=torch.tensor([1., 3.5, 8.5, 20.]), onset=torch.tensor([.5, 3., 8.]),
            end=torch.tensor([2., 4., 9.]), press=torch.tensor([.4, 2.8, 7.8]),
            finger=torch.tensor([1, 1, 3]))
        data['delta'][:, :, 0] = torch.tensor([0., .04, .12])
        data['candidate'][:] = torch.tensor([True, False, True])
        result = pad_tracking_reward(**data)
        self.assertEqual(result['indices'].tolist(), [[0, -1, -1, -1], [1, -1, -1, -1],
                                                     [-1, -1, 2, -1], [-1, -1, -1, -1]])
        self.assertEqual(result['valid'].tolist(), [[True, False, False, False], [True, False, False, False],
                                                   [False, False, True, False], [False]*4])
        # Two song-present fingers remain in the denominator, including when
        # only one has a target now. No normalization by candidate count.
        torch.testing.assert_close(result['rate'], torch.tensor([1., .25, .0625, 0.]), atol=1e-7, rtol=0)
        data['candidate'].logical_not_()
        for key,value in result.items():
            torch.testing.assert_close(pad_tracking_reward(**data)[key], value, atol=0, rtol=0)

    def test_empty_nonassigned_and_candidate_shape_dtype_validation(self):
        empty = inputs(n=2, m=0)
        result = pad_tracking_reward(**empty)
        self.assertEqual(result['rate'].tolist(), [0., 0.])
        self.assertFalse(result['valid'].any())
        self.assertEqual(result['indices'].tolist(), [[-1]*4]*2)
        data = inputs(n=2)
        data['finger'].zero_()  # No index/middle/ring/pinky target is assigned.
        self.assertEqual(pad_tracking_reward(**data)['rate'].tolist(), [0., 0.])
        for value in (torch.zeros(2, 1), torch.zeros(2, 2, dtype=torch.bool)):
            with self.subTest(candidate_shape=value.shape, candidate_dtype=value.dtype):
                invalid = inputs(n=2)
                invalid['candidate'] = value
                with self.assertRaises(ValueError):
                    pad_tracking_reward(**invalid)

    def test_real_pad_force_only_toggle_preserves_tracking_and_original_contact_rewards(self):
        env, initial, _ = self.environment(task=task((1,), end=.2))
        env.pad_valid[0] = False
        env.pad_valid[0, 0] = True
        row = fixtures.place_pad_sample(env, initial, 1, fixtures.press_goal(env))
        row['contact_force'][0, env.pad_indices[0]] = 0.
        env.reset([0, 1], row)
        self.assertEqual(env.candidate[:, 0].tolist(), [False, True])
        contact, success, hold = torch.zeros(2), torch.zeros(2), torch.zeros(2)
        saved = {key:value.clone() for key,value in row.items()}
        for _ in range(6):
            result = self.advance(env, row)
            self.assertFalse(result[3].any())
            torch.testing.assert_close(env.terms['song_finger_tracking'][0],
                env.terms['song_finger_tracking'][1], atol=0, rtol=0)
            self.assertAlmostEqual(float(env.terms['song_finger_tracking'][0]), 2/60., places=7)
            self.assertEqual(env.terms['action_change'].tolist(), [0., 0.])
            self.assertEqual(env.terms['terminal_failure'].tolist(), [0., 0.])
            contact += env.terms['song_left_contact']
            success += env.terms['song_left_success']
            hold += env.terms['song_clean_hold']
        self.assertEqual(contact.tolist(), [0., .5])
        self.assertEqual(success.tolist(), [0., .5])
        torch.testing.assert_close(hold, torch.tensor([0., 1.]), atol=2e-7, rtol=0)
        self.assertEqual(env.note['contact_done'][:, 0].tolist(), [False, True])
        self.assertEqual(env.note['left'][:, 0].tolist(), [False, True])
        self.assertAlmostEqual(float(env.note['contact_streak'][1, 0]), .1, places=12)
        self.assertAlmostEqual(float(env.note['clean_streak'][1, 0]), .1, places=12)
        for key,value in saved.items():
            torch.testing.assert_close(row[key], value, atol=0, rtol=0)
        self.assertEqual(env.observation()['state'].shape, (2, 544))
        self.assertEqual(env.observation()['events'].shape, (2, 64, 24))
        self.assertEqual(env.observation()['priority_events'].shape, (2, 8, 24))
        self.assertEqual(env.contract['observation']['surface_geometry']['schema'], 'guitar_learning.left_surface_events.v5')
        self.assertEqual(env._episode(0, False)['left_note_ledger']['schema'], 'guitar_learning.surface_note_ledger.v7')

    def test_v16_policy_optimizers3331_roundtrip_and_v12_strict_rejection(self):
        env, _, observation = self.environment()
        pool = SimpleNamespace(environment=env, set_curriculum=env.set_curriculum)
        def make(contract):
            policy = SpecialistPolicy(544, size='small', role='left', contract=contract)
            coordinator = CurriculumCoordinator(policy, pool)
            return policy, coordinator, PPOTrainer(policy)
        policy, coordinator, trainer = make(env.contract)
        evidence = dict(valid=True, reason='timeline_complete', left_curriculum=dict(full_safe=True,
            finger_metrics=[dict(target_count=n, near_fraction=1., contact_fraction=0., success_fraction=0.)
                            for n in env.finger_counts]))
        coordinator.advance([evidence]*256, observation)
        self.assertEqual(tuple(policy.left_curriculum_state.shape), (3331,))
        self.assertEqual(env.contract['reward']['schema'], 'guitar_learning.gpu_tensor_song_reward.v20')
        self.assertEqual(env.contract['reward']['surface_learning']['schema'], 'guitar_learning.surface_fretting.v8')
        for optimizer in (trainer.actor_optimizer, trainer.value_optimizer):
            for group in optimizer.param_groups:
                for parameter in group['params']:
                    parameter.grad = torch.ones_like(parameter)
            optimizer.step(); optimizer.zero_grad()
        trainer.updates, trainer.cost_weight = 5, 1.25
        old = copy.deepcopy(env.contract)
        old['observation']['fields'] = [field.replace('.standby_gate', '.idle_weight')
                                         for field in old['observation']['fields']]
        old['reward']['schema'] = 'guitar_learning.gpu_tensor_song_reward.v12'
        old['reward']['finger_tracking'].update(schema='guitar_learning.gpu_finger_tracking_rate.v6',
            candidate_multiplier=2., rate_bounds_per_s=[0., 4.],
            quality='(1+distance/0.04)^-2*(1+candidate)*alignment_factor')
        old_policy, _, old_trainer = make(old)
        self.assertEqual(tuple(policy.state_dict()), tuple(old_policy.state_dict()))
        with tempfile.TemporaryDirectory() as folder, patch('torch.cuda.is_available', return_value=False):
            current, previous = Path(folder)/'v16.pt', Path(folder)/'v12.pt'
            trainer.save(current); old_trainer.save(previous)
            restored, restored_coordinator, resumed = make(env.contract)
            resumed.load(current); restored_coordinator.restore()
            self.tree_equal(policy.state_dict(), restored.state_dict())
            self.tree_equal(trainer.actor_optimizer.state_dict(), resumed.actor_optimizer.state_dict())
            self.tree_equal(trainer.value_optimizer.state_dict(), resumed.value_optimizer.state_dict())
            np.testing.assert_array_equal(coordinator.state.state_vector(), restored_coordinator.state.state_vector())
            self.assertEqual((resumed.updates, resumed.cost_weight), (5, 1.25))
            before = copy.deepcopy((restored.state_dict(), resumed.actor_optimizer.state_dict(),
                resumed.value_optimizer.state_dict(), resumed.updates, resumed.cost_weight,
                torch.get_rng_state(), np.random.get_state()))
            with self.assertRaisesRegex(ValueError, 'mismatch'):
                resumed.load(previous)
            after = (restored.state_dict(), resumed.actor_optimizer.state_dict(),
                resumed.value_optimizer.state_dict(), resumed.updates, resumed.cost_weight,
                torch.get_rng_state(), np.random.get_state())
            self.tree_equal(before, after)

    def tree_equal(self, left, right):
        if isinstance(left, torch.Tensor):
            torch.testing.assert_close(left, right, rtol=0, atol=0)
        elif isinstance(left, np.ndarray):
            np.testing.assert_array_equal(left, right)
        elif isinstance(left, dict):
            self.assertEqual(left.keys(), right.keys())
            for key in left:
                self.tree_equal(left[key], right[key])
        elif isinstance(left, (list, tuple)):
            self.assertEqual(len(left), len(right))
            for a,b in zip(left, right):
                self.tree_equal(a,b)
        else:
            self.assertEqual(left, right)


if __name__ == '__main__':
    unittest.main()
