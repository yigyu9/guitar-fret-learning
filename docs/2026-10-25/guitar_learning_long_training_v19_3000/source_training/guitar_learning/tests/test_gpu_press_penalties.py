"""CPU accounting regressions; synthetic mesh poses do not certify physics."""
import copy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import torch

from guitar_learning.gpu.geometry import apply
from guitar_learning.music_task import ScoreTask
from guitar_learning.skills.specialist_policy import SpecialistPolicy
from guitar_learning.song.curriculum_runtime import CurriculumCoordinator
from guitar_learning.tests import test_gpu_continuous_clean as clean_fixtures
from guitar_learning.training.ppo import PPOTrainer


class PressPenaltyTests(unittest.TestCase):
    environment = clean_fixtures.ContinuousCleanTests.environment
    placed = clean_fixtures.ContinuousCleanTests.placed
    tick = clean_fixtures.ContinuousCleanTests.tick
    seconds = clean_fixtures.ContinuousCleanTests.seconds
    tree_equal = clean_fixtures.ContinuousCleanTests.tree_equal

    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def wrong_snapshot(self, env, snapshot):
        # A different finger's original full-surface point on the target cell.
        # This fixture isolates accounting, without claiming joint reachability.
        row = {key:value.clone() for key,value in snapshot.items()}
        slot = 5  # middle distal, while these fixtures request index finger
        index = int(env.finger_indices[slot])
        guitar = row['body_state'][:, env.guitar_index]
        goal = env.goals[:, 0]
        row['body_state'][:, index, :3] = (guitar[:, :3]+apply(guitar[:, 3:7], goal)-
            apply(row['body_state'][:, index, 3:7], env.surface_local[slot, 0]))
        row['contact_force'][:, index, 2] = 1.
        env.reset([0, 1], row)
        self.assertTrue(env.wrong[:, 0].all())
        self.assertFalse(env.candidate[:, 0].any())
        return row

    def test_equal_wrong_and_missing_fractions_cost_the_same_for_different_lengths(self):
        for kind, coefficient in (('wrong', 1.), ('missing', .5)):
            totals = []
            for duration in (.2, .8):
                with self.subTest(kind=kind, duration=duration):
                    env, _, bad = self.placed(end=duration)
                    row = self.wrong_snapshot(env, bad) if kind == 'wrong' else bad
                    env.reset([0, 1], row)
                    self.assertFalse(env.candidate.any())
                    self.assertEqual(bool(env.wrong.any()), kind == 'wrong')
                    total = torch.zeros(2)
                    for _ in range(round(duration*.25*60)):
                        terms, _ = self.tick(env, (row,)*4)
                        total += terms['song_%s_press' % kind]
                        other = 'missing' if kind == 'wrong' else 'wrong'
                        self.assertEqual(terms['song_%s_press' % other].tolist(), [0., 0.])
                    torch.testing.assert_close(total, torch.full((2,), -.25*coefficient),
                                               atol=1e-7, rtol=0)
                    totals.append(total)
            torch.testing.assert_close(totals[0], totals[1], atol=1e-7, rtol=0)

    def test_same_absolute_missing_time_is_costlier_for_a_short_note(self):
        totals = []
        for duration in (.2, .8):
            env, _, bad = self.placed(end=duration)
            env.reset([0, 1], bad)
            total = torch.zeros(2)
            for _ in range(3):
                terms, _ = self.tick(env, (bad,)*4)
                total += terms['song_missing_press']
            totals.append(total)
        torch.testing.assert_close(totals[0], totals[1]*4, atol=1e-7, rtol=0)

    def test_wrong_balance_and_existing_stage_multipliers_apply_after_normalization(self):
        score = ScoreTask((clean_fixtures.note('a', onset=0., end=.1),
                           clean_fixtures.note('b', onset=1., end=1.1, press=1.),
                           clean_fixtures.note('c', onset=1., end=1.1, press=1., finger=2, string=1)))
        for stage, contact_weight, timing_weight in ((0., .15, .1), (1., 1., .35), (2., 1., 1.)):
            for kind, coefficient, weight in (('wrong', 1., contact_weight),
                                                ('missing', .5, timing_weight)):
                with self.subTest(stage=stage, kind=kind):
                    env, _, bad = self.placed(score=score)
                    row = self.wrong_snapshot(env, bad) if kind == 'wrong' else bad
                    env.reset([0, 1], row)
                    env.set_curriculum(stage)
                    terms, _ = self.tick(env, (row,)*4)
                    key = 'song_%s_press' % kind
                    # This note carries .75 weight and one tick spans 1/6 of it.
                    raw = -.75*coefficient/6
                    torch.testing.assert_close(terms[key], torch.full((2,), raw), atol=1e-8, rtol=0)
                    torch.testing.assert_close(env.episode_reward_terms[key],
                        torch.full((2,), raw*weight), atol=1e-8, rtol=0)

    def test_missing_and_missed_balance_total_contribution_per_present_finger(self):
        score = ScoreTask((clean_fixtures.note('a', onset=0., end=.1),
                           clean_fixtures.note('b', onset=.2, end=.3, press=.2),
                           clean_fixtures.note('c', onset=.4, end=.5, press=.4, finger=2, string=1)))
        env, _, bad = self.placed(score=score)
        env.reset([0, 1], bad)
        self.assertFalse(env.candidate.any())
        self.assertFalse(env.wrong.any())
        torch.testing.assert_close(env.finger_weights, torch.tensor([.75, .75, 1.5]))
        missing, missed = torch.zeros(2), torch.zeros(2)
        per_note = []
        for control in range(31):
            terms, _ = self.tick(env, (bad,)*4)
            missing += terms['song_missing_press']
            missed += terms['song_left_missed']
            if control in (6, 18, 30):
                per_note.append(missing.clone())
        first, second, third = per_note[0], per_note[1]-per_note[0], per_note[2]-per_note[1]
        torch.testing.assert_close(first, torch.full((2,), -.375), atol=1e-7, rtol=0)
        torch.testing.assert_close(first, second, atol=1e-7, rtol=0)
        torch.testing.assert_close(first+second, third, atol=1e-7, rtol=0)
        torch.testing.assert_close(missed, missing, atol=1e-7, rtol=0)
        self.assertEqual(env.note['left_missed'].sum(-1).tolist(), [3, 3])

    def test_preparation_contact_or_wrong_cannot_add_audible_penalties_or_best_clean(self):
        for kind in ('good', 'missing', 'wrong'):
            with self.subTest(kind=kind):
                env, good, bad = self.placed(press=0., onset=.1, end=.3)
                row = good if kind == 'good' else bad
                if kind == 'wrong':
                    row = self.wrong_snapshot(env, bad)
                env.reset([0, 1], row)
                for _ in range(6):
                    terms, _ = self.tick(env, (row,)*4)
                    for key in ('song_wrong_press', 'song_missing_press', 'song_left_missed'):
                        self.assertEqual(terms[key].tolist(), [0., 0.])
                self.seconds(env.note['best_clean_streak'], 0.)
                self.seconds(env.note['clean'], 0.)
                self.assertFalse(env.note['left_missed'].any())

    def test_nearly_achieved_note_has_small_missed_cost_but_still_counts_as_missed(self):
        env, good, bad = self.placed()
        # 95/240s is exactly one physical sample below the unchanged 0.4s goal.
        for _ in range(23):
            self.tick(env, (good,)*4)
        self.tick(env, (good, good, good, bad))
        self.seconds(env.note['best_clean_streak'], 95/240.)
        self.seconds(env.note['clean_streak'], 0.)
        missed = torch.zeros(2)
        while int(env.clock[0]) <= 240:
            terms, _ = self.tick(env, (bad,)*4)
            missed += terms['song_left_missed']
        self.assertFalse(env.note['left'].any())
        self.assertTrue(env.note['left_missed'].all())
        torch.testing.assert_close(missed, torch.full((2,), -1/192.), atol=1e-8, rtol=0)
        terms, _ = self.tick(env, (bad,)*4)
        self.assertEqual(terms['song_left_missed'].tolist(), [0., 0.])

    def test_best_continuous_run_not_total_clean_controls_missed_relief(self):
        env, good, bad = self.placed(end=.5)
        missed = torch.zeros(2)
        for _ in range(30):
            terms, _ = self.tick(env, (good, good, good, bad))
            missed += terms['song_left_missed']
        self.assertTrue((env.note['clean'] > env.required).all())
        self.seconds(env.note['best_clean_streak'], 3/240.)
        self.assertFalse(env.note['left'].any())
        terms, _ = self.tick(env, (bad,)*4)
        missed += terms['song_left_missed']
        # Best run12.5ms against required200ms: 6.25% relief, despite >40% total.
        torch.testing.assert_close(missed, torch.full((2,), -.46875), atol=1e-8, rtol=0)
        self.assertTrue(env.note['left_missed'].all())

    def test_achievement_threshold_and_once_only_bonus_remain_unchanged(self):
        env, good, bad = self.placed()
        bonus, missed = torch.zeros(2), torch.zeros(2)
        for _ in range(24):
            terms, _ = self.tick(env, (good,)*4)
            bonus += terms['song_left_success']
        self.assertTrue(env.note['left'].all())
        self.seconds(env.note['best_clean_streak'], .4)
        while int(env.clock[0]) <= 240:
            terms, _ = self.tick(env, (bad,)*4)
            bonus += terms['song_left_success']
            missed += terms['song_left_missed']
        torch.testing.assert_close(bonus, torch.full((2,), .5), atol=0, rtol=0)
        self.assertEqual(missed.tolist(), [0., 0.])
        self.assertFalse(env.note['left_missed'].any())
        self.seconds(env.note['best_clean_streak'], .4)

    def test_h32_reward_boundary_and_selected_reset_preserve_other_best_runs(self):
        env, good, bad = self.placed(end=2.)
        for _ in range(32):
            self.tick(env, (good,)*4)
        self.tick(env, (bad,)*4)
        self.seconds(env.note['best_clean_streak'], 128/240.)
        self.seconds(env.note['clean_streak'], 0.)
        before = {key:value[1].clone() for key,value in env.note.items()}
        env.reset_reward_window()
        self.seconds(env.note['best_clean_streak'], 128/240.)
        env.reset([0], good)
        self.seconds(env.note['best_clean_streak'][0], 0.)
        for key,value in before.items():
            torch.testing.assert_close(env.note[key][1], value, atol=0, rtol=0)
        self.assertEqual(env.clock.tolist(), [0, 132])
        ledger = env._episode(1, False)['left_note_ledger']
        self.assertEqual(ledger['schema'], 'guitar_learning.surface_note_ledger.v7')
        self.assertAlmostEqual(ledger['values']['best_clean_streak'][0], 128/240., places=12)

    def test_v16_checkpoint_roundtrip_and_same_shape_v14_rejection(self):
        env, _, _ = self.placed()
        pool = SimpleNamespace(environment=env, set_curriculum=env.set_curriculum)
        def make(contract):
            policy = SpecialistPolicy(544, size='small', role='left', contract=contract)
            coordinator = CurriculumCoordinator(policy, pool)
            return policy, coordinator, PPOTrainer(policy)
        policy, coordinator, trainer = make(env.contract)
        self.assertEqual(env.contract['reward']['schema'], 'guitar_learning.gpu_tensor_song_reward.v19')
        self.assertEqual(env.contract['reward']['surface_learning']['schema'], 'guitar_learning.surface_fretting.v8')
        self.assertEqual(tuple(policy.left_curriculum_state.shape), (3331,))
        for optimizer in (trainer.actor_optimizer, trainer.value_optimizer):
            for group in optimizer.param_groups:
                for parameter in group['params']:
                    parameter.grad = torch.ones_like(parameter)
            optimizer.step(); optimizer.zero_grad()
        trainer.updates, trainer.cost_weight = 7, 1.25
        previous = copy.deepcopy(env.contract)
        previous['reward']['schema'] = 'guitar_learning.gpu_tensor_song_reward.v14'
        previous['reward']['surface_learning']['schema'] = 'guitar_learning.surface_fretting.v6'
        old_policy, _, old_trainer = make(previous)
        self.assertEqual(tuple(policy.state_dict()), tuple(old_policy.state_dict()))
        with tempfile.TemporaryDirectory() as folder, patch('torch.cuda.is_available', return_value=False):
            current, old = Path(folder)/'v16.pt', Path(folder)/'v14.pt'
            trainer.save(current); old_trainer.save(old)
            restored, restored_coordinator, resumed = make(env.contract)
            resumed.load(current); restored_coordinator.restore()
            self.tree_equal(policy.state_dict(), restored.state_dict())
            self.tree_equal(trainer.actor_optimizer.state_dict(), resumed.actor_optimizer.state_dict())
            self.tree_equal(trainer.value_optimizer.state_dict(), resumed.value_optimizer.state_dict())
            self.assertEqual((resumed.updates, resumed.cost_weight), (7, 1.25))
            self.assertEqual(coordinator.state.state_vector().tolist(),
                             restored_coordinator.state.state_vector().tolist())
            before = copy.deepcopy((restored.state_dict(), resumed.actor_optimizer.state_dict(),
                resumed.value_optimizer.state_dict(), resumed.updates, resumed.cost_weight))
            with self.assertRaisesRegex(ValueError, 'mismatch'):
                resumed.load(old)
            after = (restored.state_dict(), resumed.actor_optimizer.state_dict(),
                resumed.value_optimizer.state_dict(), resumed.updates, resumed.cost_weight)
            self.tree_equal(before, after)


if __name__ == '__main__':
    unittest.main()
