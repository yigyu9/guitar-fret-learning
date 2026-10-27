"""Continuous audible left-pad achievement, independently of cumulative hold.

CPU tensor integration with source-mesh snapshots; no native contact, pressure,
reachable-pose, learning-run, or musical-performance claim.
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
from guitar_learning.music_task import ScoreTask, ScoreTarget
from guitar_learning.skills.specialist_policy import SpecialistPolicy
from guitar_learning.song.curriculum_runtime import CurriculumCoordinator
from guitar_learning.tests import test_gpu_environment as fixtures
from guitar_learning.tests.test_gpu_surface_learning import task
from guitar_learning.training.ppo import PPOTrainer


def note(identity, *, onset, end, press=0., finger=1, string=0):
    return ScoreTarget(identity, identity, string, 5, finger, 1,
                       onset, end, press, onset, end)


class ContinuousCleanTests(unittest.TestCase):
    environment = fixtures.TensorSongTests.environment

    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def placed(self, *, onset=0., end=1., press=0., score=None):
        env, initial, _ = self.environment(task=score or task((1,), onset=onset, end=end, press=press))
        env.pad_valid[0] = False
        env.pad_valid[0, 0] = True
        good = fixtures.place_pad_sample(env, initial, 1, fixtures.press_goal(env))
        bad = {key:value.clone() for key,value in good.items()}
        bad['contact_force'][:, env.pad_indices[0]] = 0.
        env.reset([0, 1], good)
        self.assertTrue(env.candidate[:, 0].all())
        return env, good, bad

    def tick(self, env, rows):
        env.begin_control(torch.zeros(2, 39))
        for row in rows:
            env.substep(row)
        result = env.end_control()
        return {key:value.clone() for key,value in env.terms.items()}, result

    def seconds(self, actual, expected):
        torch.testing.assert_close(actual, torch.full_like(actual, expected), atol=1e-12, rtol=0)

    def test_zero_audible_window_is_rejected_only_by_gpu_left(self):
        zero = task((1,), press=0., onset=.1, end=.1)
        # A positive press window bypasses the separate first-contact guard.
        # Shared ScoreTask and right backend retain their historical contract.
        self.assertGreater(zero.targets[0].end_s-zero.targets[0].press_s, 0.)
        with self.assertRaisesRegex(ValueError, 'positive onset..end window'):
            self.environment(task=zero)
        right, _, _ = self.environment(hand='right', task=zero)
        self.assertEqual(right.task.targets[0].onset_s, right.task.targets[0].end_s)
        self.assertNotIn('clean_streak', right.note)

    def test_intermittent_sum_over_40percent_does_not_achieve_but_keeps_hold_reward(self):
        env, good, bad = self.placed()
        hold, bonus = torch.zeros(2), torch.zeros(2)
        for _ in range(60):
            terms, _ = self.tick(env, (good, good, good, bad))
            hold += terms['song_clean_hold']
            bonus += terms['song_left_success']
            self.seconds(env.note['clean_streak'], 0.)
        self.assertTrue((env.note['clean'] > env.required).all())
        self.assertFalse(env.note['left'].any())
        self.assertEqual(bonus.tolist(), [0., 0.])
        expected = (2*env.note['clean'][:, 0]/(env.end[0]-env.onset[0])).float()
        torch.testing.assert_close(hold, expected, atol=1e-6, rtol=0)
        torch.testing.assert_close(env.note['held'], env.note['clean'], atol=0, rtol=0)

    def test_exact_continuous_40percent_threshold_awards_once(self):
        env, good, _ = self.placed()
        self.seconds(env.required, .4)
        bonus = torch.zeros(2)
        for _ in range(23):
            terms, _ = self.tick(env, (good,)*4)
            bonus += terms['song_left_success']
        env.begin_control(torch.zeros(2, 39))
        for _ in range(3):
            env.substep(good)
        self.seconds(env.note['clean_streak'], 95/240.)
        self.assertFalse(env.note['left'].any())
        self.assertEqual(env.terms['song_left_success'].tolist(), [0., 0.])
        env.substep(good)
        self.seconds(env.note['clean_streak'], .4)
        self.assertTrue(env.note['left'].all())
        self.assertEqual(env.terms['song_left_success'].tolist(), [.5, .5])
        env.end_control()
        bonus += env.terms['song_left_success']
        terms, _ = self.tick(env, (good,)*4)
        bonus += terms['song_left_success']
        self.assertEqual(bonus.tolist(), [.5, .5])
        self.assertTrue((terms['song_clean_hold'] > 0).all())

    def test_press_contact_before_onset_cannot_count_as_audible_clean_streak(self):
        env, good, _ = self.placed(press=0., onset=.1, end=.3)
        for _ in range(6):
            self.tick(env, (good,)*4)
        self.seconds(env.note['clean_streak'], 0.)
        self.seconds(env.note['clean'], 0.)
        self.assertTrue(env.note['contact_done'].all())
        self.assertTrue((env.note['contact_streak'] >= .05).all())
        self.assertFalse(env.note['left'].any())
        obs = env.observation()
        self.assertGreater(float(env.note['dwell'][0, 0]), 0.)
        # This catches accidentally retaining old dwell semantics in either
        # token stream: contact before onset cannot appear as clean streak.
        for key in ('events', 'priority_events'):
            torch.testing.assert_close(obs[key][:, 0, 11], torch.zeros(2), atol=0, rtol=0)
        for _ in range(3):
            self.tick(env, (good,)*4)
        self.seconds(env.note['clean_streak'], .05)
        self.assertFalse(env.note['left'].any())
        for _ in range(2):
            self.tick(env, (good,)*4)
        self.assertTrue(env.note['left'].all())

    def test_break_clears_immediately_and_reentry_needs_two_qualified_endpoints(self):
        env, good, bad = self.placed()
        for _ in range(3):
            self.tick(env, (good,)*4)
        clean = env.note['clean'].clone()
        env.begin_control(torch.zeros(2, 39))
        env.substep(bad)
        self.seconds(env.note['clean_streak'], 0.)
        torch.testing.assert_close(env.note['clean'], clean, atol=0, rtol=0)
        env.substep(good)
        self.seconds(env.note['clean_streak'], 0.)
        env.substep(good)
        self.seconds(env.note['clean_streak'], 1/240.)
        env.substep(good)
        env.end_control()
        self.seconds(env.note['clean_streak'], 2/240.)
        self.seconds(env.note['clean'], 14/240.)
        self.assertFalse(env.note['left'].any())

    def test_after_achievement_drop_preserves_latch_and_recontact_hold_without_repeat_bonus(self):
        env, good, bad = self.placed(end=.5)
        bonuses = []
        for _ in range(12):
            terms, _ = self.tick(env, (good,)*4)
            bonuses.append(terms['song_left_success'])
        self.assertTrue(env.note['left'].all())
        self.tick(env, (bad,)*4)
        self.seconds(env.note['clean_streak'], 0.)
        self.assertTrue(env.note['left'].all())
        for _ in range(13):
            terms, _ = self.tick(env, (good,)*4)
            bonuses.append(terms['song_left_success'])
            self.assertTrue((terms['song_clean_hold'] > 0).all())
        self.assertTrue((env.note['clean_streak'] >= .2).all())
        torch.testing.assert_close(torch.stack(bonuses).sum(0), torch.full((2,), .5))
        self.assertTrue((env.note['clean'] > env.note['clean_streak']).all())

    def test_short_note_50ms_floor_and_duration_cap(self):
        for duration, required, threshold in ((.1, .05, 12), (.025, .025, 6)):
            with self.subTest(duration=duration):
                env, good, _ = self.placed(end=duration)
                self.seconds(env.required, required)
                while int(env.clock[0])+4 < threshold:
                    self.tick(env, (good,)*4)
                env.begin_control(torch.zeros(2, 39))
                for _ in range(4):
                    env.substep(good)
                    at = int(env.clock[0])
                    self.assertEqual(env.note['left'][:, 0].tolist(), [at >= threshold]*2)
                    if at == threshold:
                        self.seconds(env.note['clean_streak'], required)
                env.end_control()

    def test_non_grid_onset_end_overlap_exactly_and_outside_resets(self):
        env, good, _ = self.placed(onset=.011, end=.037, press=0.)
        #26ms note is capped at its full duration. Both fractional endpoint
        # intervals must count; dwell before onset must not count.
        for _ in range(2):
            self.tick(env, (good,)*4)
        self.seconds(env.note['clean_streak'], 8/240.-.011)
        self.assertFalse(env.note['left'].any())
        env.begin_control(torch.zeros(2, 39))
        env.substep(good)  # At37.5ms the final overlap ends at37ms.
        self.seconds(env.note['clean_streak'], .026)
        self.assertTrue(env.note['left'].all())
        self.assertEqual(env.terms['song_left_success'].tolist(), [.5, .5])
        env.substep(good)
        self.seconds(env.note['clean_streak'], 0.)
        env.substep(good); env.substep(good)
        env.end_control()
        self.seconds(env.note['clean'], .026)
        self.seconds(env.note['held'], .026)

    def test_rows_and_repeated_notes_on_same_finger_have_independent_streaks_and_latches(self):
        score = ScoreTask((note('a', onset=0., end=.25),
                           note('b', onset=.3, end=.55, press=.28)))
        env, good, bad = self.placed(score=score)
        mixed = {key:value.clone() for key,value in good.items()}
        mixed['contact_force'][0] = bad['contact_force'][0]
        for _ in range(3):
            self.tick(env, (good,)*4)
        self.tick(env, (mixed,)*4)
        self.seconds(env.note['clean_streak'][0], 0.)
        self.assertAlmostEqual(float(env.note['clean_streak'][1, 0]), 16/240., places=12)
        self.assertAlmostEqual(float(env.note['clean_streak'][1, 1]), 0., places=12)
        for _ in range(2):
            self.tick(env, (good,)*4)
        self.assertEqual(env.note['left'].tolist(), [[False, False], [True, False]])
        while int(env.clock[0]) < 72:
            self.tick(env, (good,)*4)
        self.seconds(env.note['clean_streak'][:, 1], 0.)
        self.assertFalse(env.note['left'][:, 1].any())
        for _ in range(6):
            self.tick(env, (good,)*4)
        self.assertTrue(env.note['left'].all())
        self.seconds(env.note['clean_streak'][:, 0], 0.)
        self.seconds(env.note['clean_streak'][:, 1], .1)

    def test_collection_and_partial_reset_preserve_other_rows_and_note_clocks(self):
        env, good, _ = self.placed(end=.5)
        for _ in range(3):
            self.tick(env, (good,)*4)
        before = {key:value[1].clone() for key,value in env.note.items()}
        env.reset_reward_window()
        self.seconds(env.note['clean_streak'], .05)
        env.reset([0], good)
        self.seconds(env.note['clean_streak'][0], 0.)
        self.seconds(env.note['clean'][0], 0.)
        for key,value in before.items():
            torch.testing.assert_close(env.note[key][1], value, atol=0, rtol=0)
        self.assertEqual(env.clock.tolist(), [0, 12])
        self.tick(env, (good,)*4)
        self.seconds(env.note['clean_streak'][0], 4/240.)
        self.seconds(env.note['clean_streak'][1], 16/240.)

    def test_token11_and_ledger_distinguish_current_clean_streak_from_cumulative_hold(self):
        env, good, bad = self.placed()
        self.tick(env, (good,)*4)
        self.tick(env, (bad,)*4)
        obs = env.observation()
        events = obs['events'][:, 0]*env.event_scales
        priority = obs['priority_events'][:, 0]*env.event_scales
        torch.testing.assert_close(events[:, 11], torch.zeros(2), atol=0, rtol=0)
        torch.testing.assert_close(priority[:, 11], torch.zeros(2), atol=0, rtol=0)
        torch.testing.assert_close(events[:, 12], torch.full((2,), 4/240.), atol=1e-8, rtol=0)
        torch.testing.assert_close(events[:, 13], torch.full((2,), 4/240.), atol=1e-8, rtol=0)
        self.assertEqual(env.contract['observation']['event_fields'][11], 'clean_streak_s')
        self.assertEqual(env.contract['observation']['surface_geometry']['schema'], 'guitar_learning.left_surface_events.v4')
        self.assertEqual(float(env.event_scales[11]), float(env.event_scales[12]))
        ledger = env._episode(0, False)['left_note_ledger']
        self.assertEqual(ledger['schema'], 'guitar_learning.surface_note_ledger.v6')
        self.assertEqual(ledger['values']['clean_streak'], [0.])
        self.assertAlmostEqual(ledger['values']['clean'][0], 4/240., places=12)
        self.seconds(env.note['held'], 4/240.)
        self.assertEqual(obs['state'].shape, (2, 544))
        self.assertEqual(obs['events'].shape, (2, 64, 24))
        self.assertEqual(obs['priority_events'].shape, (2, 8, 24))

    def test_hold_rate_coefficient_stage_and_finger_balance_are_preserved(self):
        score = ScoreTask((note('a', onset=0., end=1.),
                           note('b', onset=2., end=3., press=1.9),
                           note('c', onset=2., end=3., press=1.9, finger=2, string=1)))
        for stage in (0., 1., 2.):
            with self.subTest(stage=stage):
                env, good, _ = self.placed(score=score)
                env.set_curriculum(stage)
                torch.testing.assert_close(env.finger_weights, torch.tensor([.75, .75, 1.5]))
                terms, _ = self.tick(env, (good,)*4)
                expected = 2*(4/240.)*.75
                torch.testing.assert_close(terms['song_clean_hold'], torch.full((2,), expected), atol=1e-8, rtol=0)
                torch.testing.assert_close(env.episode_reward_terms['song_clean_hold'],
                    torch.full((2,), expected*env._weights()['timing']), atol=1e-8, rtol=0)
                self.seconds(env.required, .4)

    def test_right_hand_keeps_original_cumulative_clean_achievement(self):
        env, initial, _ = self.environment(hand='right', task=task((1,), end=1.))
        good = {key:value.clone() for key,value in initial.items()}
        slot = 3
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
        for _ in range(60):
            self.tick(env, (good, good, good, bad))
        self.assertTrue((env.note['clean'] > env.required).all())
        self.assertTrue(env.note['left'].all())
        self.assertNotIn('clean_streak', env.note)
        self.assertEqual(env.contract['observation']['event_fields'][11], 'continuous_dwell_s')
        self.assertEqual(env.contract['reward']['schema'], 'guitar_learning.gpu_tensor_song_reward.v1')

    def test_v16_full_roundtrip_and_v11_same_shape_resume_rejected(self):
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
        self.assertEqual(tuple(policy.left_curriculum_state.shape), (3331,))
        self.assertEqual(env.contract['reward']['schema'], 'guitar_learning.gpu_tensor_song_reward.v16')
        self.assertEqual(env.contract['reward']['surface_learning']['schema'], 'guitar_learning.surface_fretting.v7')
        for optimizer in (trainer.actor_optimizer, trainer.value_optimizer):
            for group in optimizer.param_groups:
                for parameter in group['params']:
                    parameter.grad = torch.ones_like(parameter)
            optimizer.step(); optimizer.zero_grad()
        trainer.updates, trainer.cost_weight = 5, 1.25
        old = copy.deepcopy(env.contract)
        old['reward']['schema'] = 'guitar_learning.gpu_tensor_song_reward.v11'
        old['reward']['surface_learning']['schema'] = 'guitar_learning.surface_fretting.v5'
        old['observation']['surface_geometry']['schema'] = 'guitar_learning.left_surface_events.v3'
        old['observation']['event_fields'][11] = 'continuous_dwell_s'
        old_policy, _, old_trainer = make(old)
        self.assertEqual(tuple(policy.state_dict()), tuple(old_policy.state_dict()))
        with tempfile.TemporaryDirectory() as folder, patch('torch.cuda.is_available', return_value=False):
            current, previous = Path(folder)/'v16.pt', Path(folder)/'v11.pt'
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
