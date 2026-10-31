"""CPU scope/clock accounting; synthetic snapshots are not native reachability."""
import copy
import unittest

import torch

from guitar_learning.gpu.environment import TensorSongEnvironment, TERMS
from guitar_learning.gpu.finger_skill_environment import FingerSkillEnvironment
from guitar_learning.tests.test_gpu_environment import fixture, SONG, BUNDLE


class FingerSkillEnvironmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def make(self, scope='phrases', count=4):
        metadata, snapshot = fixture(count)
        env = FingerSkillEnvironment(metadata, bundle=BUNDLE, song=SONG, device='cpu',
            skill=dict(schema='guitar_learning.finger_skill.v3', phase='J', scope='scheduled',
                hold_ticks=1, exploration='independent', planned_transitions=400, full_song_after=100))
        if scope == 'full_song': env.set_evaluation(True, full_song=True)
        observation = env.reset(range(count), snapshot)
        return env, snapshot, observation

    @staticmethod
    def advance(env, snapshot, failure=False):
        env.begin_control(torch.zeros(env.N, 39))
        for _ in range(4):
            sample = dict(snapshot, physics_step=env.clock+1)
            env.substep(sample)
        if failure:
            env.tick_failure[:, 0] = True
        return env.end_control()

    def test_view_preserves_original_ids_and_score_clock_and_balances_selected_fingers(self):
        env, _, obs = self.make()
        self.assertEqual(env.M, 67)
        self.assertEqual(obs['state'].shape, (4, 557))
        self.assertEqual(env.catalog.closed_groups[0], tuple(env.catalog.closed_groups[0]))
        torch.testing.assert_close(env._score_time(), env.score_offset)
        self.assertTrue((env.score_offset > 0).any())
        for row in range(4):
            selected = env.focus_mask[row]
            self.assertAlmostEqual(float(env.finger_weights[row].sum()), int(selected.sum()), places=5)
            own = [float(env.finger_weights[row, selected & (env.finger == f)].sum())
                   for f in range(1, 5) if bool((selected & (env.finger == f)).any())]
            self.assertLess(max(own)-min(own), 1e-5)
            self.assertAlmostEqual(float(env.view_first[row]-env.score_offset[row]), 3.)

    def test_unselected_past_and_future_notes_never_grade_or_make_tokens(self):
        env, snapshot, _ = self.make()
        for _ in range(3):
            obs, *_ = self.advance(env, snapshot)
        for key in ('left', 'left_missed', 'strict_missed', 'clean', 'wrong', 'missing',
                    'exposure_time', 'contact_time', 'ever'):
            self.assertFalse(bool(env.note[key][~env.focus_mask].any()), key)
        features = obs['events']*env.event_scales
        for row in range(env.N):
            target_ids = set()
            for token in features[row, obs['mask'][row]]:
                indices = ((env.string+1 == token[3].round()) &
                    (env.fret == token[4].round()) & (env.finger == token[5].round()) &
                    ((env.onset-env._score_time()[row]-token[0]).abs() < 1e-5))
                target_ids.update(indices.nonzero().flatten().tolist())
            self.assertTrue(target_ids <= set(env.focus_mask[row].nonzero().flatten().tolist()))

    def test_selected_reset_leaves_other_views_clocks_and_physical_arrays_untouched(self):
        env, snapshot, _ = self.make()
        self.advance(env, snapshot)
        before = [x.clone() for x in (env.clock, env.focus_mask, env.score_offset,
                  env.duration_ticks, env.finger_weights, env.skill_diagnostics.paths)]
        physical = {k: v.clone() for k, v in snapshot.items()}
        env.reset([0], snapshot)
        for old, current in zip(before, (env.clock, env.focus_mask, env.score_offset,
                env.duration_ticks, env.finger_weights, env.skill_diagnostics.paths)):
            torch.testing.assert_close(old[1:], current[1:], rtol=0, atol=0)
        for key, value in physical.items():
            torch.testing.assert_close(value, snapshot[key], rtol=0, atol=0)
        self.assertEqual(int(env.clock[0]), 0)

    def test_passive_pick_crossing_cannot_latch_an_unselected_note(self):
        env, _, _ = self.make(count=1)
        note = int((~env.focus_mask[0]).nonzero()[0])
        string, direction = int(env.string[note]), int(env.direction[note])
        x = .02-string*.02
        env.starts = torch.tensor([[[.02-i*.02, -.4, .01] for i in range(6)]])
        env.ends = env.starts.clone()
        env.ends[:, :, 1] = .2
        env.previous_pick = torch.tensor([[x-direction*.01, -.32, .006]])
        env.pick = torch.tensor([[x+direction*.01, -.32, .006]])
        env.terms = {key: torch.zeros(1) for key in TERMS}
        env.clock[:] = 4
        before = env.onset[note].expand(1)-1/480.
        env._strike(before, before+1/240., torch.zeros(1, env.M, dtype=torch.bool))
        self.assertFalse(bool(env.note['right'][0, note]))
        self.assertFalse(bool(env.note['coupled'][0, note]))




    def test_end_and_remaining_failure_cost_use_local_duration_not_source_offset(self):
        env, snapshot, _ = self.make()
        env.clock.copy_(env.duration_ticks*4-4)
        result = self.advance(env, snapshot)
        self.assertTrue(bool(result[3].all()))
        for episode in result[-1]:
            row = episode['env_id']
            self.assertTrue(episode['song']['completed'])
            self.assertEqual(episode['song']['denominator'], int(env.focus_mask[row].sum()))
            self.assertAlmostEqual(episode['task_time_s'], float(env.duration_ticks[row])/60)
            self.assertEqual(episode['left_curriculum']['finger_metrics'], env._finger_metrics(row))
        env.reset(range(4), snapshot)
        env.clock[:] = 236
        result = self.advance(env, snapshot, failure=True)
        expected = 2*(env._episode_duration()-1).clamp_min(0)+env.termination_note_budget.double()
        torch.testing.assert_close(env.failure_horizon_cost.double(), expected, rtol=1e-6, atol=1e-6)

    def test_evaluation_view_is_explicit_and_keeps_training_contract(self):
        env, snapshot, _ = self.make()
        before = copy.deepcopy(env.contract)
        env.set_evaluation(True, full_song=True)
        env.reset(range(4), snapshot)
        self.assertTrue(bool(env.focus_mask.all()))
        self.assertEqual(env.duration_ticks.tolist(), [1969]*4)
        self.assertFalse(bool(env.score_offset.any()))
        self.assertEqual(before, env.contract)
        result = self.advance(env, snapshot, failure=True)
        self.assertTrue(result[-1][0]['evaluation'])
        self.assertEqual(result[-1][0]['finger_skill_eval']['scope'], 'full_song')

    def test_full_song_retains_base_state_and_event_measurements(self):
        env, snapshot, observation = self.make(scope='full_song')
        metadata, _ = fixture(4)
        base = TensorSongEnvironment(metadata, bundle=BUNDLE, song=SONG, hand='left', device='cpu')
        original = base.reset(range(4), snapshot)
        for _ in range(4):
            for key, value in original.items():
                actual = observation[key][:, :552] if key == 'state' else observation[key]
                torch.testing.assert_close(actual, value, rtol=0, atol=0)
            observation = self.advance(env, snapshot)[0]
            original = self.advance(base, snapshot)[0]

    def test_removed_phases_schemas_and_hold_options_are_rejected(self):
        metadata, _ = fixture(2)
        skill = dict(schema='guitar_learning.finger_skill.v3', phase='J', scope='scheduled',
            hold_ticks=1, exploration='independent', planned_transitions=400, full_song_after=100)
        for key, value in (('schema', 'guitar_learning.finger_skill.v1'),
                ('schema', 'guitar_learning.finger_skill.v2'), ('phase', 'R'), ('phase', 'F'),
                ('phase', 'auto'), ('hold_ticks', 3), ('hold_ticks', 6), ('hold_ticks', True),
                ('exploration', 'correlated'), ('scope', 'phrases')):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                FingerSkillEnvironment(metadata, bundle=BUNDLE, song=SONG, device='cpu',
                    skill=dict(skill, **{key: value}))





if __name__ == '__main__':
    unittest.main()
