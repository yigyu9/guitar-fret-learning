"""v25 wrong-fretting acceptance cases; synthetic poses do not certify native pressure."""
import unittest
from unittest.mock import patch

import torch

from guitar_learning.gpu.control import apply
from guitar_learning.gpu.finger_skill_environment import FingerSkillEnvironment
from guitar_learning.gpu.contact import pad_contact_cells
from guitar_learning.gpu.contact import wrong_press_sources
from guitar_learning.tests.test_gpu_environment import fixture, SONG, BUNDLE, place_pad_sample, press_goal
from guitar_learning.tests.test_gpu_surface_learning import task
from guitar_learning.tests.test_simplified_finger_environment import advance


class WrongPressRuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def inputs(self, targets=1):
        return dict(qualifies=torch.zeros(1, 10, dtype=torch.bool),
            assigned=torch.zeros(1, 10, dtype=torch.long), nearest=torch.zeros(1, 10, dtype=torch.long),
            source_fingers=torch.arange(5).repeat_interleave(2), surface_count=1,
            pad_cells=(torch.zeros(1, 4, 1, dtype=torch.bool), torch.zeros(1, 4, 1, dtype=torch.long),
                       torch.zeros(1, 4, 1, dtype=torch.long)),
            positive=torch.zeros(1, targets, dtype=torch.bool), now=torch.tensor([.5]),
            onset=torch.zeros(targets), end=torch.ones(targets), press=torch.zeros(targets),
            scope=torch.ones(1, targets, dtype=torch.bool), strings=torch.zeros(targets, dtype=torch.long),
            frets=torch.full((targets,), 5, dtype=torch.long), fingers=torch.ones(targets, dtype=torch.long),
            fret_count=23)

    def test_own_other_fret_and_other_string_even_same_fret(self):
        for string, fret, cause in ((0, 3, 1), (0, 7, 1), (1, 5, 2), (1, 7, 2)):
            with self.subTest(string=string, fret=fret):
                values = self.inputs()
                valid, frets, strings = values['pad_cells']
                valid[:, 0] = True; frets[:, 0] = fret; strings[:, 0] = string
                result = wrong_press_sources(**values)
                self.assertTrue(result['wrong'].item())
                self.assertTrue(result['flags'][0, 0, 3, cause])
                self.assertEqual(result['fret_min'][0, 0, 3], fret)
                self.assertEqual(int(result['flags'].sum()), 1)

    def test_other_finger_only_higher_on_same_string(self):
        for string, fret, expected in ((0, 3, False), (0, 5, False), (0, 7, True), (1, 7, False)):
            for positive in (False, True):
                values = self.inputs()
                values['qualifies'][0, 4] = True
                values['assigned'][0, 4] = fret; values['nearest'][0, 4] = string
                values['positive'].fill_(positive)
                result = wrong_press_sources(**values)
                self.assertEqual(result['wrong'].item(), expected)

    def test_own_middle_surface_does_not_replace_pad_evidence(self):
        values = self.inputs()
        values['qualifies'][0, 2] = True; values['assigned'][0, 2] = 7
        self.assertFalse(wrong_press_sources(**values)['wrong'].item())

    def test_positive_pad_wins_over_incidental_own_samples_but_not_other_higher(self):
        values = self.inputs()
        values['pad_cells'][0][:, 0] = True; values['pad_cells'][1][:, 0] = 3
        values['positive'].fill_(True)
        self.assertFalse(wrong_press_sources(**values)['wrong'].item())
        values['qualifies'][0, 0] = True; values['assigned'][0, 0] = 7  # thumb
        self.assertTrue(wrong_press_sources(**values)['wrong'].item())

    def test_no_target_or_unselected_has_no_wrong(self):
        values = self.inputs()
        values['qualifies'][0, 4] = True; values['assigned'][0, 4] = 7
        values['pad_cells'][0][:, 0] = True; values['pad_cells'][1][:, 0] = 3
        values['scope'].fill_(False)
        self.assertFalse(wrong_press_sources(**values)['wrong'].item())
        values = self.inputs()
        values['pad_cells'][0][:, 3] = True; values['pad_cells'][1][:, 3] = 3
        self.assertFalse(wrong_press_sources(**values)['wrong'].item())  # idle pinky

    def test_future_preparation_does_not_exempt_current_interference(self):
        values = self.inputs(2)
        values['fingers'][1] = 2; values['frets'][1] = 7
        values['onset'][1] = 1.; values['end'][1] = 2.
        values['qualifies'][0, 4] = True; values['assigned'][0, 4] = 7
        result = wrong_press_sources(**values)
        self.assertEqual(result['wrong'].tolist(), [[True, False]])
        self.assertEqual(result['next_preparation'].tolist(), [[True, False]])

    def test_simultaneous_assigned_cell_is_allowed_but_future_cell_is_not(self):
        values = self.inputs(2)
        values['strings'][1] = 1
        values['pad_cells'][0][:, 0] = True; values['pad_cells'][1][:, 0] = 5
        values['pad_cells'][2][:, 0] = 1
        self.assertFalse(wrong_press_sources(**values)['wrong'].any())
        values['onset'][1] = .8
        result = wrong_press_sources(**values)
        self.assertEqual(result['wrong'].tolist(), [[True, False]])
        self.assertTrue(result['next_preparation'][0, 0])

    def test_pad_requires_same_sample_position_facing_load_and_clear_cell(self):
        points = torch.tensor([[[[0., .5, .001]]]*4])
        normals = torch.tensor([[[[0., 0., -1.]]]*4])
        starts = torch.tensor([[[i*.01, 0., 0.] for i in range(6)]])
        ends = starts.clone(); ends[..., 1] = 2.
        frets = torch.tensor([[[0., y, 0.] for y in (0., 1., 2.)]])
        valid = torch.ones(4, 1, dtype=torch.bool); loaded = torch.ones(1, 4, dtype=torch.bool)
        plane = torch.tensor([0., 0., 1., 0.])
        def verdict(p=points, n=normals, load=loaded):
            return pad_contact_cells(p, n, valid, load, starts, ends, frets, plane)[0]
        self.assertTrue(verdict().all())
        self.assertFalse(verdict(n=-normals).any())
        self.assertFalse(verdict(load=~loaded).any())
        for axis, value in ((0, .005), (1, 1.), (1, -.1), (2, .004), (2, -.002)):
            changed = points.clone(); changed[..., axis] = value
            self.assertFalse(verdict(p=changed).any())


class WrongPressEnvironmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def setup(self, score=None):
        metadata, row = fixture()
        skill = dict(schema='guitar_learning.finger_skill.v3', phase='J', exploration='independent',
            hold_ticks=1, scope='scheduled', planned_transitions=400, full_song_after=100)
        with patch('guitar_learning.gpu.environment.make_task', return_value=score or task((1,), end=.5)):
            env = FingerSkillEnvironment(metadata, bundle=BUNDLE, song=SONG, skill=skill, device='cpu')
        env.set_evaluation(True, full_song=True)
        env.reset([0, 1], row)
        env.surface_valid.zero_()  # Isolate intentional full-surface witnesses.
        env.pad_valid.zero_(); env.pad_valid[:, 0] = True
        return env, row

    def other(self, env, row, fret=7, body=4):
        start, line = env.starts[:, 0], env.ends[:, 0]-env.starts[:, 0]
        y = .5*(env.frets[:, fret-1, 1]+env.frets[:, fret, 1])
        goal = start+((y-start[:, 1])/line[:, 1])[:, None]*line
        guitar = row['body_state'][:, env.guitar_index]
        index = int(env.finger_indices[body])
        row['body_state'][:, index, :3] = guitar[:, :3]+apply(guitar[:, 3:7], goal)-apply(
            row['body_state'][:, index, 3:7], env.surface_local[body, 0])
        row['contact_force'][:, index, 2] = 1.
        env.surface_valid[body*env.surface_count] = True

    def test_replacement_finger_neither_wrong_nor_assigned_success(self):
        env, row = self.setup()
        row = place_pad_sample(env, row, 2, press_goal(env))
        self.other(env, row, fret=5)
        env.reset([0, 1], row)
        self.assertFalse(env.wrong.any()); self.assertFalse(env.candidate.any())
        advance(env, row)
        self.assertTrue((env.note['missing'] > 0).all())
        self.assertFalse(env.note['clean'].any())

    def test_wrong_own_pad_on_other_string_is_logged_on_distal_body(self):
        env, row = self.setup()
        goal = press_goal(env); goal[:, 0] = env.starts[:, 1, 0]
        row = place_pad_sample(env, row, 1, goal)
        env.reset([0, 1], row)
        self.assertTrue(env.wrong.all()); self.assertFalse(env.candidate.any())
        self.assertTrue(env.wrong_source_flags[:, 0, 3, 2].all())
        advance(env, row)
        ledger = env._episode(0, False)['left_note_ledger']
        self.assertGreater(ledger['values']['own_wrong_string_time'][0], 0)
        self.assertNotIn('assignment_time', ledger['values'])
        self.assertEqual(ledger['wrong_press_sources']['contract']['causes'],
                         ['other_higher', 'own_wrong_fret', 'own_wrong_string'])
        self.assertEqual(env.contract['task']['contact_measurement'], env.contact_contract)

    def test_penalty_budget_multiple_sources_and_release_trapezoid(self):
        env, row = self.setup()
        row = place_pad_sample(env, row, 1, press_goal(env))
        self.other(env, row, body=4); self.other(env, row, body=6)
        env.reset([0, 1], row)
        self.assertTrue(env.wrong.all()); self.assertFalse(env.candidate.any())
        advance(env, row)
        torch.testing.assert_close(env.note['wrong'], torch.full((2, 1), 1/60, dtype=torch.float64))
        torch.testing.assert_close(env.episode_reward_terms['song_wrong_press'], torch.full((2,), -.15/60/.5))
        previous = env.note['wrong'].clone()
        row['contact_force'][:, env.finger_indices[[4, 6]]] = 0.
        advance(env, row)
        torch.testing.assert_close(env.note['wrong']-previous, torch.full((2, 1), .5/240, dtype=torch.float64))
        self.assertTrue(env.candidate.all())

    def test_preparation_and_note_end_do_not_charge_outside_audible_window(self):
        env, row = self.setup(score=task((1,), onset=1/60, end=2/60))
        self.other(env, row)
        env.reset([0, 1], row)
        advance(env, row)
        self.assertFalse(env.note['wrong'].any())
        advance(env, row)
        torch.testing.assert_close(env.note['wrong'], torch.full((2, 1), 1/60, dtype=torch.float64))
        torch.testing.assert_close(env.episode_reward_terms['song_wrong_press'], torch.full((2,), -.15))
        previous = env.note['wrong'].clone()
        advance(env, row)
        torch.testing.assert_close(env.note['wrong'], previous)

    def test_partial_reset_preserves_other_environment_history(self):
        env, row = self.setup(); self.other(env, row)
        env.reset([0, 1], row); advance(env, row)
        previous = env.note['wrong_source_time'][1].clone()
        env.reset([0], row)
        self.assertFalse(env.note['wrong_source_time'][0].any())
        torch.testing.assert_close(env.note['wrong_source_time'][1], previous)

    def test_fractional_physics_boundaries_charge_exact_audible_overlap(self):
        # Both musical boundaries lie strictly between physics samples. A
        # time-gated verdict would incorrectly lose half of each edge overlap.
        onset, end = .001, .029
        env, row = self.setup(score=task((1,), onset=onset, end=end))
        self.other(env, row)
        env.reset([0, 1], row)
        advance(env, row); advance(env, row)
        torch.testing.assert_close(env.note['wrong'], torch.full((2, 1), end-onset, dtype=torch.float64))
        torch.testing.assert_close(env.episode_reward_terms['song_wrong_press'], torch.full((2,), -.15))


if __name__ == '__main__':
    unittest.main()
