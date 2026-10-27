"""Best uninterrupted first-contact credit; CPU tensors, not reachability proof."""
import copy
import unittest

import torch

from guitar_learning.tests import test_gpu_continuous_contact as fixtures
from guitar_learning.tests import test_gpu_environment as snapshots
from guitar_learning.tests.test_gpu_surface_learning import task
from guitar_learning.music_task import ScoreTask, ScoreTarget


class ContactProgressTests(unittest.TestCase):
    environment = fixtures.ContinuousContactTests.environment
    placed = fixtures.ContinuousContactTests.placed
    tick = fixtures.ContinuousContactTests.tick
    assert_seconds = fixtures.ContinuousContactTests.assert_seconds

    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def test_partial_contact_pays_only_new_best_and_completion_adds_no_second_bonus(self):
        env, good, bad = self.placed()
        total = torch.zeros(2)
        for _ in range(4):
            credit, _ = self.tick(env, (good, good, bad, bad))
            total += credit
        torch.testing.assert_close(total, torch.full((2,), .5*(2/240)/.05))
        self.assertFalse(env.note['contact_done'].any())
        for _ in range(5):
            credit, _ = self.tick(env, (good,)*4)
            total += credit
        torch.testing.assert_close(total, torch.full((2,), .5))
        self.assertTrue(env.note['contact_done'].all())
        for _ in range(3):
            credit, _ = self.tick(env, (good,)*4)
            self.assert_seconds(credit, 0.)

    def test_reset_only_clears_selected_rows_budget(self):
        env, good, _ = self.placed()
        self.tick(env, (good,)*4)
        preserved = {k:v[1].clone() for k,v in env.note.items()}
        env.reset([0], good)
        self.assert_seconds(env.note['best_contact_streak'][0], 0.)
        self.assert_seconds(env.note['contact_progress'][0], 0.)
        for key, before in preserved.items():
            torch.testing.assert_close(env.note[key][1], before, rtol=0, atol=0)
        credit, _ = self.tick(env, (good,)*4)
        torch.testing.assert_close(credit, torch.full((2,), .5/3))

    def test_collection_boundary_preserves_best_and_budget(self):
        env, good, bad = self.placed()
        first, _ = self.tick(env, (good, good, bad, bad))
        before = copy.deepcopy(env.note)
        env.reward_window_means(1)
        env.reset_reward_window()
        for key in before:
            torch.testing.assert_close(env.note[key], before[key], rtol=0, atol=0)
        repeated, _ = self.tick(env, (good, good, bad, bad))
        self.assert_seconds(repeated, 0.)
        self.assertTrue((first > 0).all())

    def test_event_tokens_distinguish_current_and_previously_credited_streak(self):
        env, good, bad = self.placed()
        self.tick(env, (good,)*4)
        self.tick(env, (bad,)*4)
        obs = env.observation()
        for key in ('events', 'priority_events'):
            self.assert_seconds(obs[key][:, 0, 12], 0.)
            torch.testing.assert_close(obs[key][:, 0, 13], torch.full((2,), 1/3))
            self.assert_seconds(obs[key][:, 0, 11], 0.)
        self.assert_seconds(env.note['held'], 4/240.)
        self.assertEqual(env.contract['observation']['event_fields'][12:14],
            ['contact_streak_fraction', 'contact_progress'])
        self.assertEqual(env.event_scales[12:14].tolist(), [1., 1.])

    def test_short_window_and_clipped_press_window_preserve_cap(self):
        for press, end in ((0., .025), (.103, .128), (.103, .183), (.0045, .005)):
            with self.subTest(press=press, end=end):
                env, good, _ = self.placed(press=press, onset=press, end=end)
                total = torch.zeros(2)
                for _ in range(int(end*60)+2):
                    credit, _ = self.tick(env, (good,)*4)
                    total += credit
                torch.testing.assert_close(total, torch.full((2,), .5), atol=1e-6, rtol=0)
                self.assertTrue(env.note['contact_done'].all())
                self.assert_seconds(env.note['contact_streak'], 0.)
                self.assert_seconds(env.note['contact_progress'], 1.)

    def test_overlapping_notes_have_independent_budgets_in_both_token_streams(self):
        score = ScoreTask(tuple(ScoreTarget(name, name, 0, 5, 1, 1,
            onset, 1., onset, onset, 1.) for name, onset in (('a', 0.), ('b', .03))))
        env, initial, _ = self.environment(task=score)
        env.pad_valid[0] = False
        env.pad_valid[0, 0] = True
        good = snapshots.place_pad_sample(env, initial, 1, snapshots.press_goal(env))
        env.reset([0, 1], good)
        total = torch.zeros(2)
        credit, _ = self.tick(env, (good,)*4)
        total += credit
        expected = torch.tensor([1/3, 0.])
        obs = env.observation()
        for key in ('events', 'priority_events'):
            # The current and upcoming note use index1's two priority slots.
            torch.testing.assert_close(obs[key][:, :2, 12], expected.expand(2, -1), atol=1e-7, rtol=0)
            torch.testing.assert_close(obs[key][:, :2, 13], expected.expand(2, -1), atol=1e-7, rtol=0)
        credit, _ = self.tick(env, (good,)*4)
        total += credit
        expected = torch.tensor([2/3, (8/240.-.03)/.05])
        torch.testing.assert_close(env.note['contact_progress'], expected.expand(2, -1).double(), atol=1e-7, rtol=0)
        # Once both notes are audible the unchanged priority selector has one
        # slot for this finger; the general stream still exposes both budgets.
        torch.testing.assert_close(env.observation()['events'][:, :2, 13], expected.expand(2, -1), atol=1e-7, rtol=0)
        for _ in range(4):
            credit, _ = self.tick(env, (good,)*4)
            total += credit
        torch.testing.assert_close(total, torch.ones(2))
        self.assertTrue(env.note['contact_done'].all())

    def test_failure_tick_suppresses_positive_credit_without_repaying_it(self):
        env, good, _ = self.placed()
        env.begin_control(torch.zeros(2, 39))
        for _ in range(3):
            env.substep(good)
        env.invalidate_control(torch.tensor([True, False]))
        env.substep(good)
        env.end_control()
        self.assertEqual(float(env.episode_reward_terms['song_left_contact'][0]), 0.)
        self.assertGreater(float(env.episode_reward_terms['song_left_contact'][1]), 0.)
        torch.testing.assert_close(env.note['contact_progress'], torch.full_like(env.note['contact_progress'], 1/3))

    def test_random_contact_sequence_matches_scalar_oracle(self):
        env, good, bad = self.placed(press=.019, onset=.019, end=.931)
        rng = torch.Generator().manual_seed(249)
        candidate_before = True
        streak = best = progress = accumulated = 0.
        for tick in range(60):
            samples = []
            for substep in range(4):
                candidate = bool(torch.rand((), generator=rng) < .88)
                samples.append(good if candidate else bad)
                before = (tick*4+substep)/240
                now = before+1/240
                overlap = max(0., min(now, .931)-max(before, .019))
                streak = streak+overlap if candidate_before and candidate and overlap > 0 else 0.
                best = max(best, streak)
                updated = min(best/.05, 1.)
                accumulated += .5*(updated-progress)
                progress = updated
                candidate_before = candidate
            credit, _ = self.tick(env, samples)
            expected_increment = accumulated-getattr(self, '_last_credit', 0.)
            torch.testing.assert_close(credit, torch.full((2,), expected_increment), atol=1e-7, rtol=0)
            self._last_credit = accumulated
            self.assert_seconds(env.note['contact_streak'], streak)
            self.assert_seconds(env.note['best_contact_streak'], best)
            self.assert_seconds(env.note['contact_progress'], progress)
        self.assertLessEqual(accumulated, .5)

    def test_contract_and_ledger_version_and_budget_are_explicit(self):
        env, good, bad = self.placed()
        self.tick(env, (good, good, bad, bad))
        self.assertEqual(env.contract['reward']['schema'], 'guitar_learning.gpu_tensor_song_reward.v21')
        self.assertEqual(env.contract['observation']['surface_geometry']['schema'],
                         'guitar_learning.left_surface_events.v5')
        ledger = env._episode(0, False)['left_note_ledger']
        self.assertEqual(ledger['schema'], 'guitar_learning.surface_note_ledger.v7')
        self.assertAlmostEqual(ledger['values']['best_contact_streak'][0], 2/240., places=12)
        self.assertAlmostEqual(ledger['values']['contact_progress'][0], (2/240)/.05, places=12)
        self.assertIn('contact_done', ledger['values'])

    def test_right_hand_has_no_new_contact_state_or_event_semantics(self):
        env, _, _ = self.environment(hand='right', task=task((1,), end=1.))
        self.assertNotIn('best_contact_streak', env.note)
        self.assertNotIn('contact_progress', env.note)
        self.assertEqual(env.contract['reward']['schema'], 'guitar_learning.gpu_tensor_song_reward.v1')
        self.assertNotEqual(env.contract['observation']['event_fields'][12], 'contact_streak_fraction')


if __name__ == '__main__':
    unittest.main()
