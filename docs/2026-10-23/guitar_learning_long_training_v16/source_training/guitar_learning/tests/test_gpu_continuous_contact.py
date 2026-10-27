"""Continuous left-pad contact timing on real source-mesh tensor snapshots.

These are integration checks of GPU-path formulas on CPU, not native pressure,
reachable poses, or musical performance measurements.
"""
import copy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import torch

from guitar_learning.gpu.geometry import apply
from guitar_learning.skills.specialist_policy import SpecialistPolicy
from guitar_learning.song.curriculum_runtime import CurriculumCoordinator
from guitar_learning.tests import test_gpu_environment as fixtures
from guitar_learning.tests.test_gpu_surface_learning import task
from guitar_learning.training.ppo import PPOTrainer


class ContinuousContactTests(unittest.TestCase):
    environment = fixtures.TensorSongTests.environment
    advance = staticmethod(fixtures.TensorSongTests.advance)

    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def placed(self, *, press=0., onset=0., end=1.):
        env, initial, _ = self.environment(task=task((1,), press=press, onset=onset, end=end))
        env.pad_valid[0] = False
        env.pad_valid[0, 0] = True
        good = fixtures.place_pad_sample(env, initial, 1, fixtures.press_goal(env))
        bad = {key:value.clone() for key, value in good.items()}
        bad['contact_force'][:, env.pad_indices[0]] = 0.
        env.reset([0, 1], good)
        self.assertTrue(env.candidate.all())
        return env, good, bad

    def tick(self, env, rows):
        """Four actual snapshots; return unweighted contact impulse per row."""
        env.begin_control(torch.zeros(2, 39))
        for row in rows:
            env.substep(row)
        result = env.end_control()
        return env.terms['song_left_contact'].clone(), result

    def assert_seconds(self, value, expected):
        torch.testing.assert_close(value, torch.full_like(value, expected), atol=1e-12, rtol=0)

    def test_zero_duration_press_window_is_rejected_before_left_measurement(self):
        zero = task((1,), press=.1, onset=.1, end=.1)
        # The shared task and the right backend retain their original input
        # contract; only GPU-left first-contact measurement requires time.
        with self.assertRaisesRegex(ValueError, 'positive press..end window'):
            self.environment(task=zero)
        right, _, _ = self.environment(hand='right', task=zero)
        self.assertEqual(right.task.targets[0].end_s, right.task.targets[0].press_s)
        self.assertNotIn('contact_streak', right.note)

    def test_intermittent_sum_over_50ms_does_not_earn_first_contact(self):
        env, good, bad = self.placed()
        total = torch.zeros(2)
        # Each2-on/2-off burst is shorter than50ms. Accumulated contact still
        # exceeds50ms, even with conservative both-endpoint qualification.
        for _ in range(16):
            impulse, _ = self.tick(env, (good, good, bad, bad))
            total += impulse
            self.assert_seconds(env.note['contact_streak'], 0.)
        self.assertTrue((env.note['contact_time'] > .05).all())
        self.assertFalse(env.note['contact_done'].any())
        self.assertEqual(total.tolist(), [0., 0.])
        self.assert_seconds(env.observation()['state'][:, 506], 0.)

    def test_exact_12_substeps_threshold_and_one_impulse(self):
        env, good, _ = self.placed()
        for _ in range(2):
            impulse, _ = self.tick(env, (good,)*4)
            self.assertEqual(impulse.tolist(), [0., 0.])
        env.begin_control(torch.zeros(2, 39))
        for _ in range(3):
            env.substep(good)
        self.assert_seconds(env.note['contact_streak'], 11/240.)
        self.assertFalse(env.note['contact_done'].any())
        self.assertEqual(env.terms['song_left_contact'].tolist(), [0., 0.])
        env.substep(good)
        self.assert_seconds(env.note['contact_streak'], .05)
        self.assertTrue(env.note['contact_done'].all())
        self.assertEqual(env.terms['song_left_contact'].tolist(), [.5, .5])
        env.end_control()
        impulse, _ = self.tick(env, (good,)*4)
        self.assertEqual(impulse.tolist(), [0., 0.])
        self.assert_seconds(env.note['contact_time'], 16/240.)

    def test_break_clears_streak_immediately_but_keeps_accumulated_diagnostic(self):
        env, good, bad = self.placed()
        self.tick(env, (good,)*4)
        self.tick(env, (good,)*4)
        before = env.note['contact_time'].clone()
        env.begin_control(torch.zeros(2, 39))
        env.substep(bad)
        self.assert_seconds(env.note['contact_streak'], 0.)
        torch.testing.assert_close(env.note['contact_time'], before, atol=1e-12, rtol=0)
        env.substep(good)  # Reentry endpoint is not a complete contact interval.
        self.assert_seconds(env.note['contact_streak'], 0.)
        env.substep(good)
        self.assert_seconds(env.note['contact_streak'], 1/240.)
        env.substep(good)
        env.end_control()
        self.assert_seconds(env.note['contact_streak'], 2/240.)
        self.assert_seconds(env.note['contact_time'], 10/240.)
        self.assertFalse(env.note['contact_done'].any())

    def test_achievement_stays_true_after_break_without_repeat_contact_bonus(self):
        env, good, bad = self.placed()
        impulses = []
        for _ in range(3):
            impulse, _ = self.tick(env, (good,)*4)
            impulses.append(impulse)
        self.tick(env, (bad,)*4)
        self.assert_seconds(env.note['contact_streak'], 0.)
        self.assertTrue(env.note['contact_done'].all())
        for _ in range(4):
            impulse, _ = self.tick(env, (good,)*4)
            impulses.append(impulse)
        self.assertTrue((env.note['contact_streak'] >= .05).all())
        torch.testing.assert_close(torch.stack(impulses).sum(0), torch.full((2,), .5))
        self.assertTrue(env.note['contact_done'].all())

    def test_partial_reset_and_batch_rows_keep_independent_streaks(self):
        env, good, bad = self.placed()
        mixed = {key:value.clone() for key, value in good.items()}
        mixed['contact_force'][0] = bad['contact_force'][0]
        self.tick(env, (good,)*4)
        self.tick(env, (mixed,)*4)
        self.assertAlmostEqual(float(env.note['contact_streak'][0, 0]), 0., places=12)
        self.assertAlmostEqual(float(env.note['contact_streak'][1, 0]), 8/240., places=12)
        before = {key:value[1].clone() for key,value in env.note.items()}
        other_clock = env.clock[1].clone()
        env.reset([0], good)
        self.assertEqual(int(env.clock[0]), 0)
        self.assertTrue(torch.equal(env.clock[1], other_clock))
        self.assert_seconds(env.note['contact_streak'][0], 0.)
        self.assert_seconds(env.note['contact_time'][0], 0.)
        for key, value in before.items():
            torch.testing.assert_close(env.note[key][1], value, atol=0, rtol=0)
        self.tick(env, (good,)*4)
        self.assertEqual(env.note['contact_done'][:, 0].tolist(), [False, True])
        self.assert_seconds(env.note['contact_streak'][0], 4/240.)

    def test_reward_collection_boundary_does_not_reset_contact_streak(self):
        env, good, _ = self.placed()
        self.tick(env, (good,)*4)
        self.tick(env, (good,)*4)
        before = env.note['contact_streak'].clone()
        env.reward_window_means(4)
        env.reset_reward_window()
        torch.testing.assert_close(env.note['contact_streak'], before, atol=0, rtol=0)
        impulse, _ = self.tick(env, (good,)*4)
        self.assertEqual(impulse.tolist(), [.5, .5])
        self.assertTrue(env.note['contact_done'].all())

    def test_press_window_clips_preroll_and_resets_after_end(self):
        env, good, _ = self.placed(press=.1, onset=.1, end=.18)
        for _ in range(6):
            impulse, _ = self.tick(env, (good,)*4)
            self.assertEqual(impulse.tolist(), [0., 0.])
        self.assert_seconds(env.note['contact_streak'], 0.)
        self.assert_seconds(env.note['contact_time'], 0.)
        for _ in range(2):
            self.tick(env, (good,)*4)
        self.assertFalse(env.note['contact_done'].any())
        impulse, _ = self.tick(env, (good,)*4)
        self.assertEqual(impulse.tolist(), [.5, .5])
        # Continue beyond end, before the task's0.1s tail finishes.
        for _ in range(3):
            self.tick(env, (good,)*4)
        self.assert_seconds(env.note['contact_streak'], 0.)
        self.assert_seconds(env.note['contact_time'], .08)
        self.assertTrue(env.note['contact_done'].all())

    def test_short_window_uses_its_duration_without_extra_post_end_contact(self):
        env, good, _ = self.placed(end=.025)
        self.tick(env, (good,)*4)
        self.assertFalse(env.note['contact_done'].any())
        env.begin_control(torch.zeros(2, 39))
        env.substep(good)
        self.assert_seconds(env.note['contact_streak'], 5/240.)
        self.assertFalse(env.note['contact_done'].any())
        env.substep(good)
        self.assert_seconds(env.note['contact_streak'], .025)
        self.assertTrue(env.note['contact_done'].all())
        self.assertEqual(env.terms['song_left_contact'].tolist(), [.5, .5])
        env.substep(good)
        self.assert_seconds(env.note['contact_streak'], 0.)
        env.substep(good)
        env.end_control()
        self.assert_seconds(env.note['contact_time'], .025)
        impulse, _ = self.tick(env, (good,)*4)
        self.assertEqual(impulse.tolist(), [0., 0.])
        self.assert_seconds(env.note['contact_streak'], 0.)

    def test_unloaded_or_wrong_contact_breaks_qualified_streak(self):
        for cause in ('unloaded', 'wrong'):
            with self.subTest(cause=cause):
                env, good, bad = self.placed()
                if cause == 'wrong':
                    bad = {key:value.clone() for key,value in good.items()}
                    slot = 4  # Other finger's full middle surface: original wrong detector.
                    index = int(env.finger_indices[slot])
                    target = env.task.targets[0]
                    fret = target.fret+2
                    start = env.starts[:, target.string]
                    line = env.ends[:, target.string]-start
                    y = (env.frets[:, fret-1, 1]+env.frets[:, fret, 1])*.5
                    goal = start+((y-start[:, 1])/line[:, 1])[:, None]*line
                    guitar = bad['body_state'][:, env.guitar_index]
                    world = guitar[:, :3]+apply(guitar[:, 3:7], goal)
                    body = bad['body_state'][:, index]
                    body[:, :3] = world-apply(body[:, 3:7], env.surface_local[slot, 0])
                    bad['contact_force'][:, index, 2] = 1.
                self.tick(env, (good,)*4)
                self.tick(env, (good,)*4)
                self.tick(env, (bad,)*4)
                self.assertFalse(env.candidate.any())
                if cause == 'wrong':
                    self.assertTrue(env.wrong.all())
                self.assert_seconds(env.note['contact_streak'], 0.)
                self.assert_seconds(env.note['contact_time'], 8/240.)
                self.assertFalse(env.note['contact_done'].any())

    def test_observation_and_ledger_expose_current_streak_not_accumulated_sum(self):
        env, good, bad = self.placed()
        self.tick(env, (good,)*4)
        torch.testing.assert_close(env.observation()['state'][:, 506],
                                   torch.full((2,), (4/240.)/.05), atol=1e-7, rtol=0)
        self.tick(env, (bad,)*4)
        self.assert_seconds(env.observation()['state'][:, 506], 0.)
        self.assert_seconds(env.note['contact_time'], 4/240.)
        self.assertEqual(env.contract['observation']['fields'][506],
                         'left_curriculum.focus_contact_streak_fraction')
        ledger = env._episode(0, False)['left_note_ledger']
        self.assertEqual(ledger['schema'], 'guitar_learning.surface_note_ledger.v6')
        self.assertEqual(ledger['values']['contact_streak'], [0.])
        self.assertAlmostEqual(ledger['values']['contact_time'][0], 4/240., places=12)

    def test_right_hand_keeps_original_cumulative_contact_semantics(self):
        env, initial, _ = self.environment(hand='right', task=task((1,), end=1.))
        good = {key:value.clone() for key,value in initial.items()}
        slot = 3  # Original index distal full-surface source sample.
        index = int(env.finger_indices[slot])
        guitar = good['body_state'][:, env.guitar_index]
        world = guitar[:, :3]+apply(guitar[:, 3:7], env.goals[:, 0])
        body = good['body_state'][:, index]
        body[:, :3] = world-apply(body[:, 3:7], env.surface_local[slot, 0])
        good['contact_force'][:, index, 2] = 1.
        bad = {key:value.clone() for key,value in good.items()}
        bad['contact_force'][:, index] = 0.
        env.reset([0, 1], good)
        self.assertTrue(env.candidate.all())
        for _ in range(16):
            self.tick(env, (good, good, bad, bad))
        self.assertTrue((env.note['contact_time'] > .05).all())
        self.assertTrue(env.note['contact_done'].all())
        self.assertNotIn('contact_streak', env.note)
        self.assertEqual(env.contract['reward']['schema'], 'guitar_learning.gpu_tensor_song_reward.v1')

    def test_v16_contract_roundtrip_and_same_shape_v10_rejected_without_mutation(self):
        env, _, _ = self.placed()
        pool = SimpleNamespace(environment=env, set_curriculum=env.set_curriculum)
        def make(contract):
            policy = SpecialistPolicy(544, size='small', role='left', contract=contract)
            coordinator = CurriculumCoordinator(policy, pool)
            return policy, coordinator, PPOTrainer(policy)
        policy, coordinator, trainer = make(env.contract)
        evidence = dict(valid=True, reason='timeline_complete', left_curriculum=dict(full_safe=True,
            finger_metrics=[dict(target_count=n, near_fraction=1., contact_fraction=0., success_fraction=0.)
                            for n in env.finger_counts]))
        coordinator.advance([evidence]*256, env.observation())
        self.assertEqual(env.contract['reward']['schema'], 'guitar_learning.gpu_tensor_song_reward.v16')
        self.assertEqual(env.contract['reward']['surface_learning']['schema'], 'guitar_learning.surface_fretting.v7')
        self.assertEqual(tuple(policy.left_curriculum_state.shape), (3331,))
        self.assertEqual((env.observation()['events'].shape[-1], env.observation()['priority_events'].shape[1]), (24, 8))
        for optimizer in (trainer.actor_optimizer, trainer.value_optimizer):
            for group in optimizer.param_groups:
                for parameter in group['params']:
                    parameter.grad = torch.ones_like(parameter)
            optimizer.step(); optimizer.zero_grad()
        trainer.updates, trainer.cost_weight = 5, 1.25
        old = copy.deepcopy(env.contract)
        old['reward']['schema'] = 'guitar_learning.gpu_tensor_song_reward.v10'
        old['reward']['surface_learning']['schema'] = 'guitar_learning.surface_fretting.v4'
        old['observation']['fields'][506] = 'left_curriculum.focus_contact_fraction'
        old_policy, _, old_trainer = make(old)
        self.assertEqual(tuple(policy.state_dict()), tuple(old_policy.state_dict()))
        with tempfile.TemporaryDirectory() as folder, patch('torch.cuda.is_available', return_value=False):
            current, previous = Path(folder)/'v16.pt', Path(folder)/'v10.pt'
            trainer.save(current); old_trainer.save(previous)
            restored, restored_coordinator, resumed = make(env.contract)
            resumed.load(current); restored_coordinator.restore()
            self.assert_tree_equal(policy.state_dict(), restored.state_dict())
            self.assert_tree_equal(trainer.actor_optimizer.state_dict(), resumed.actor_optimizer.state_dict())
            self.assert_tree_equal(trainer.value_optimizer.state_dict(), resumed.value_optimizer.state_dict())
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
            self.assert_tree_equal(before, after)

    def assert_tree_equal(self, left, right):
        if isinstance(left, torch.Tensor):
            torch.testing.assert_close(left, right, rtol=0, atol=0)
        elif isinstance(left, np.ndarray):
            np.testing.assert_array_equal(left, right)
        elif isinstance(left, dict):
            self.assertEqual(left.keys(), right.keys())
            for key in left:
                self.assert_tree_equal(left[key], right[key])
        elif isinstance(left, (list, tuple)):
            self.assertEqual(len(left), len(right))
            for a, b in zip(left, right):
                self.assert_tree_equal(a, b)
        else:
            self.assertEqual(left, right)


if __name__ == '__main__':
    unittest.main()
