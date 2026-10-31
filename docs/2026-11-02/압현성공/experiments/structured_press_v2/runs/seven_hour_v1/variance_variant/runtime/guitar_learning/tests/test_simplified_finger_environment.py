"""v25 reward budgets and termination boundaries on CPU synthetic measurements."""
import math
import unittest
from unittest.mock import patch

import torch

from guitar_learning.gpu.environment import TensorSongEnvironment
from guitar_learning.gpu.finger_skill_environment import FingerSkillEnvironment
from guitar_learning.gpu.finger_skill_environment import performance_settlement
from guitar_learning.gpu.finger_skill_environment import remaining_negative_budget
from guitar_learning.gpu.finger_skill_environment import REWARD_TERMS
from guitar_learning.gpu.finger_skill_environment import WRIST_FIELDS
from guitar_learning.tests.test_gpu_environment import fixture, SONG, BUNDLE


def make(count=2):
    metadata, snapshot = fixture(count)
    skill = dict(schema='guitar_learning.finger_skill.v3', phase='J', exploration='independent',
                 hold_ticks=1, scope='scheduled', planned_transitions=400, full_song_after=100)
    env = FingerSkillEnvironment(metadata, bundle=BUNDLE, song=SONG, skill=skill, device='cpu')
    return env, snapshot, env.reset(range(count), snapshot)


def advance(env, snapshot, *, physical=False, wrist=False):
    env.begin_control(torch.zeros(env.N, 39))
    for _ in range(4):
        env.substep(dict(snapshot, physics_step=env.clock+1))
    if physical: env.tick_failure[:, 0] = True
    if wrist: env.wrist_failure[:] = True
    return env.end_control()


class FingerSkillEnvironmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def test_named_observation_and_k1_does_not_overwrite_wrist_timers(self):
        env, _, obs = make()
        self.assertEqual(obs['state'].shape, (2, 557))
        self.assertEqual(env.contract['observation']['fields'][-4:], list(WRIST_FIELDS))
        self.assertEqual(env.contract['observation']['scales'][-4:], [1., 1.5, 3., .1])
        self.assertEqual(env.contract['termination']['wrist']['schema'], 'guitar_learning.wrist_termination.v2')
        torch.testing.assert_close(obs['state'][:, -2], torch.ones(2))
        self.assertNotIn('finger_skill.planned_ticks', env.contract['observation']['fields'])
        self.assertFalse(hasattr(env, 'decision_observation'))
        self.assertFalse(hasattr(env, 'plan_decisions'))

    def test_nine_effective_coefficients_no_group_or_double_balance(self):
        env, _, _ = make()
        env.terms = {key: torch.ones(2) for key in REWARD_TERMS}
        env.control_performance_penalty = torch.full((2,), -.03)
        components = env._reward_components({})
        self.assertEqual(tuple(components), REWARD_TERMS)
        for name, scale in (('song_left_contact', .5), ('song_clean_hold', .5),
                            ('song_left_success', .5), ('song_wrong_press', .15)):
            torch.testing.assert_close(components[name], torch.full((2,), scale))
        self.assertNotIn('song_wrist_position', components)
        self.assertNotIn('terminal_failure', components)
        self.assertEqual(set(env.reward_window), set(REWARD_TERMS))
        self.assertNotIn('finger_tracking', env.contract['reward'])
        self.assertNotIn('wrist_region', env.contract['reward'])
        self.assertNotIn('missed once', env.contract['reward']['surface_learning']['penalty_window'])

    def test_monotone_deficit_one_budget_scope_and_single_settlement(self):
        missing = torch.tensor([[1., .2, .3]], dtype=torch.float64)
        best = torch.tensor([[0., .95, 0.]], dtype=torch.float64)
        weights = torch.tensor([[2., 1., 8.]], dtype=torch.float64)
        scope = torch.tensor([[True, True, False]])
        paid = torch.zeros_like(missing); settled = torch.zeros_like(scope)
        args = dict(required=torch.ones(3), duration=torch.ones(3), weights=weights,
                    scope=scope, end=torch.ones(3))
        paid, settled, increment = performance_settlement(missing, best, now=torch.tensor([.8]),
            paid=paid, settled=settled, **args)
        torch.testing.assert_close(increment, torch.tensor([[.2, .02, 0.]], dtype=torch.float64))
        paid, settled, increment = performance_settlement(missing, best, now=torch.tensor([1.]),
            paid=paid, settled=settled, **args)
        self.assertTrue(torch.equal(settled, scope))
        self.assertEqual(float(increment.sum()), 0.)
        _, _, again = performance_settlement(missing, best, now=torch.tensor([2.]),
            paid=paid, settled=settled, **args)
        self.assertEqual(float(again.sum()), 0.)
        # Missing .1 first, then final longest clean .4 -> max deficit .6,
        # paying .06 total, not .01+.06.
        values = dict(required=torch.ones(1), duration=torch.ones(1), weights=torch.ones(1, 1),
                      scope=torch.ones(1, 1, dtype=torch.bool), end=torch.ones(1))
        paid, settled, first = performance_settlement(torch.tensor([[.1]]), torch.tensor([[.4]]),
            now=torch.tensor([.5]), paid=torch.zeros(1, 1), settled=torch.zeros(1, 1, dtype=torch.bool), **values)
        paid, settled, final = performance_settlement(torch.tensor([[.1]]), torch.tensor([[.4]]),
            now=torch.tensor([1.]), paid=paid, settled=settled, **values)
        self.assertAlmostEqual(float(first+final), .06, places=7)

    def test_remaining_negative_budget_excludes_settled_and_unselected(self):
        result = remaining_negative_budget(torch.tensor([1.]), torch.tensor([0., 1., 2., 2.]),
            torch.tensor([1., 2., 3., 3.]), torch.ones(1, 4),
            torch.tensor([[True, True, True, False]]), torch.tensor([[.1, .03, 0., 0.]]),
            torch.tensor([[True, False, False, False]]))
        # Completed/settled0, active full remaining .15+.07, future .25.
        self.assertAlmostEqual(float(result), .47, places=7)

    def test_potential_uses_distance_near_alignment_scheduled_weight_and_no_load_gate(self):
        env, _, _ = make()
        selected = torch.arange(4).expand(2, -1)
        indices = torch.stack((selected, selected), -1)
        valid = torch.ones(2, 4, 2, dtype=torch.bool)
        env.surface_distance[:, :4] = .01
        env.surface_alignment[:, :4] = 0.
        env.finger_weights[:, :4] = 2.
        tracking = torch.tensor([[1., .5, 0., 1.], [1., .5, 0., 1.]])
        with patch.object(env, '_finger_targets', return_value=dict(indices=indices, valid=valid)), \
                patch.object(env, '_finger_preparation', return_value=dict(tracking_weight=tracking)):
            expected = 2*2.5*math.exp(-.01/.03)*.9
            torch.testing.assert_close(env._surface_potential(), torch.full((2,), expected))
            env.candidate.fill_(False)
            torch.testing.assert_close(env._surface_potential(), torch.full((2,), expected))

    def test_potential_target_switch_and_terminal_follow_one_telescoping_difference(self):
        env, snapshot, _ = make()
        with patch.object(env, '_surface_potential', side_effect=[torch.full((2,), .8), torch.full((2,), .2)]):
            advance(env, snapshot)
        torch.testing.assert_close(env.episode_reward_terms['song_left_approach'], torch.full((2,), .99*.2-.8))
        env, snapshot, _ = make()
        with patch.object(env, '_surface_potential', side_effect=[torch.full((2,), .8), torch.full((2,), .9)]):
            _, reward, _, terminated, _, rows = advance(env, snapshot, physical=True)
        torch.testing.assert_close(env.episode_reward_terms['song_left_approach'], torch.full((2,), -.8))
        self.assertTrue(terminated.all())
        for key in ('song_left_contact', 'song_clean_hold', 'song_left_success', 'song_finger_standby', 'song_thumb_support'):
            self.assertTrue((env.episode_reward_terms[key] <= 0).all())

    def test_single_failure_cost_physical_wrist_combined_and_no_running_cost(self):
        env, snapshot, _ = make()
        _, _, cost, done, _, _ = advance(env, snapshot)
        self.assertTrue((cost == 0).all()); self.assertFalse(done.any())
        _, _, cost, done, _, rows = advance(env, snapshot, physical=True, wrist=True)
        expected = 5+2*(env._episode_duration()-env._local_time())+remaining_negative_budget(
            env._score_time(), env.onset, env.end, env.finger_weights, env.focus_mask,
            env.note['performance_paid'], env.note['performance_settled'])
        torch.testing.assert_close(cost.double(), expected, rtol=1e-6, atol=1e-6)
        before = env.tick_cost.clone(); env._apply_failure_cost(torch.ones(2, dtype=torch.bool))
        torch.testing.assert_close(env.tick_cost, before, rtol=0, atol=0)
        for row in rows:
            self.assertTrue(row['termination']['physical_failure'])
            self.assertTrue(row['termination']['wrist_failure'])
            self.assertEqual(row['termination']['primary_reason'], 'physical_failure')
            self.assertEqual(row['reason'], 'terminal_failure')
            self.assertAlmostEqual(sum(row['cost_components'].values()), row['cost'], places=5)
            self.assertEqual(set(row['reward_components']), set(REWARD_TERMS))
        env, snapshot, _ = make()
        _, _, _, _, _, rows = advance(env, snapshot, wrist=True)
        self.assertFalse(rows[0]['termination']['physical_failure'])
        self.assertEqual(rows[0]['termination']['primary_reason'], 'wrist_failure')

    def test_normal_timers_grace_hysteresis_target_change_and_partial_reset(self):
        env, snapshot, _ = make()
        # Isolate the new timer from independent physical support checks.
        with patch.object(TensorSongEnvironment, '_safety'):
            env.guide['delta'][:] = .04
            env.clock[:] = 719
            env._safety()
            self.assertFalse(env.wrist_active.any())
            self.assertTrue((env.wrist_elapsed == 0).all())
            env.clock[:] = 720
            for _ in range(100): env._safety()
            self.assertTrue(env.wrist_active.all())
            env.guide['delta'][:] = .025
            env._safety()  # Recovery band remains active but reduces the timer.
            torch.testing.assert_close(env.wrist_elapsed, torch.full((2,), 99/240, dtype=torch.float64))
            env.score_offset += 5.  # A new source target does not reset the timer.
            env.guide['delta'][:] = .04
            for _ in range(260): env._safety()
            self.assertFalse(env.wrist_failure.any())
            env._safety()
            self.assertTrue(env.wrist_failure.all())
            env.guide['delta'][:] = .02
            env._safety()
            self.assertFalse(env.wrist_active.any())
            self.assertTrue((env.wrist_elapsed == 0).all())
        env.wrist_elapsed[:] = .5
        env.reset([0], snapshot)
        self.assertEqual(float(env.wrist_elapsed[0]), 0.)
        self.assertEqual(float(env.wrist_elapsed[1]), .5)
        self.assertTrue(env.wrist_failure[1])

    def test_recovery_reduces_time_without_instant_reset_or_negative_timer(self):
        env, _, _ = make()
        with patch.object(TensorSongEnvironment, '_safety'):
            env.clock[:] = 720
            env.guide['delta'][:] = .04
            for _ in range(180): env._safety()
            self.assertFalse(env.wrist_failure.any())  # Former .75s deadline.
            env.guide['delta'][:] = .03
            for _ in range(60): env._safety()
            torch.testing.assert_close(env.wrist_elapsed, torch.full((2,), .5, dtype=torch.float64))
            self.assertTrue(env.wrist_active.all())
            for _ in range(240): env._safety()
            self.assertTrue((env.wrist_elapsed == 0).all())
            self.assertFalse(env.wrist_failure.any())
            env.guide['delta'][:] = .04
            for _ in range(359): env._safety()
            self.assertFalse(env.wrist_failure.any())
            env._safety()
            self.assertTrue(env.wrist_failure.all())

    def test_episode_wrist_diagnostics_match_final_measurement(self):
        env, snapshot, _ = make()
        _, _, _, _, _, rows = advance(env, snapshot, wrist=True)
        for i, row in enumerate(rows):
            detail = row['wrist_termination']
            self.assertEqual(detail['schema'], 'guitar_learning.wrist_termination_diagnostics.v2')
            self.assertEqual(detail['delta_G_m'], env.guide['delta'][i].tolist())
            self.assertEqual(detail['lower_G_m'], env.guide['lower_G_m'][i].tolist())
            self.assertEqual(detail['upper_G_m'], env.guide['upper_G_m'][i].tolist())
            self.assertEqual(len(detail['audible_target_indices']), len(detail['audible_clean_candidate']))

    def test_severe_timer_applies_during_preparation_and_is_continuous(self):
        env, _, _ = make()
        with patch.object(TensorSongEnvironment, '_safety'):
            env.clock[:] = 1
            env.guide['delta'][:] = .10
            for _ in range(23): env._safety()
            self.assertFalse(env.wrist_severe_failure.any())
            env.guide['delta'][:] = .09; env._safety()
            self.assertTrue((env.wrist_severe_elapsed == 0).all())
            env.guide['delta'][:] = .10
            for _ in range(24): env._safety()
            self.assertTrue(env.wrist_severe_failure.all())
            self.assertTrue((env.wrist_elapsed == 0).all())

    def test_scheduled_scope_changes_only_next_reset_and_evaluation_can_override(self):
        env, snapshot, _ = make()
        before = [value.clone() for value in (env.focus_mask, env.clock, env.score_offset)]
        env.set_training_progress(100)
        for old, value in zip(before, (env.focus_mask, env.clock, env.score_offset)):
            torch.testing.assert_close(old, value, rtol=0, atol=0)
        env.reset([0], snapshot)
        self.assertTrue(env.focus_mask[0].all())
        self.assertFalse(env.focus_mask[1].all())
        self.assertEqual(float(env.score_offset[0]), 0.)
        env.set_evaluation(True, full_song=False); env.reset([0], snapshot)
        self.assertFalse(env.focus_mask[0].all())
        env.set_evaluation(True, full_song=True); env.reset([1], snapshot)
        self.assertTrue(env.focus_mask[1].all())
        with self.assertRaises(ValueError): env.set_training_progress(99)

    def test_failure_at_note_end_settles_before_remaining_budget_and_normal_end_cost_zero(self):
        env, _, _ = make()
        selected = int(env.focus_mask[0].nonzero()[0])
        env.clock[:] = math.ceil(float(env.end[selected]-env.score_offset[0])*240)
        env.note['missing'][0, selected] = (env.end-env.onset)[selected]
        env._prepare_control_end(torch.ones(2, dtype=torch.bool))
        self.assertTrue(env.note['performance_settled'][0, selected])
        self.assertAlmostEqual(float(env.note['performance_paid'][0, selected]), .1*float(env.finger_weights[0, selected]), places=7)
        expected = remaining_negative_budget(env._score_time(), env.onset, env.end,
            env.finger_weights, env.focus_mask, env.note['performance_paid'], env.note['performance_settled'])
        env.tick_cost = torch.zeros(2)
        env._apply_failure_cost(torch.zeros(2, dtype=torch.bool))
        self.assertTrue((env.tick_cost == 0).all())
        self.assertGreaterEqual(float(expected[0]), 0.)

    def test_natural_view_terminal_settles_selected_notes_without_failure_cost(self):
        env, snapshot, _ = make()
        env.clock[:] = env.duration_ticks*4-4
        _, _, cost, done, _, rows = advance(env, snapshot)
        self.assertTrue(done.all())
        self.assertTrue((cost == 0).all())
        self.assertTrue(env.note['performance_settled'][env.focus_mask].all())
        for row in rows:
            self.assertEqual(row['reason'], 'timeline_complete')
            self.assertNotIn('progress', row['left_curriculum'])
            self.assertNotIn('weights', row['left_curriculum'])
            self.assertIn('diagnostic', row['left_curriculum']['scope'])
            self.assertFalse(row['termination']['physical_failure'])
            self.assertFalse(row['termination']['wrist_failure'])
            self.assertEqual(row['cost'], 0.)


if __name__ == '__main__':
    unittest.main()
