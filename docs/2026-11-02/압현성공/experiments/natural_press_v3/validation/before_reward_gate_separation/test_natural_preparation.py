"""준비 보상의 시계·기하·정산 검사. CPU 결과는 실제 압현 성공의 증거가 아니다."""
import math
import unittest
from dataclasses import replace
from unittest.mock import patch

import torch

from guitar_learning.gpu.finger_reward import finger_target_indices
from guitar_learning.gpu.finger_skill_environment import FingerSkillEnvironment
from guitar_learning.song.task import ScoreTarget, SongTask
from guitar_learning.tests.test_gpu_environment import fixture, BUNDLE, SONG
from guitar_learning.tests import test_finger_skill_environment as skill_fixtures


def note(name='first', finger=2, onset=3., end=5.5):
    return ScoreTarget(name, name, 2, 6, finger, 1, onset, end, onset, onset-3., end-3.)


class NaturalPreparationTests(unittest.TestCase):
    advance = staticmethod(skill_fixtures.FingerSkillEnvironmentTests.advance)

    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def make(self, condition='E4', targets=None):
        metadata, snapshot = fixture(2)
        config = None if condition is None else dict(
            schema='guitar_learning.natural_preparation.v3', condition=condition)

        class Environment(FingerSkillEnvironment):
            natural_preparation = config

        task = SongTask(tuple(targets or (note(),)), lookahead_s=4.,
                        episode_duration_s=max(t.end_s for t in targets or (note(),))+.5)
        with patch('guitar_learning.gpu.environment.make_task', return_value=task):
            env = Environment(metadata, bundle=BUNDLE, song=SONG, device='cpu',
                skill=dict(schema='guitar_learning.finger_skill.v3', phase='J', scope='scheduled',
                    hold_ticks=1, exploration='independent', planned_transitions=400, full_song_after=100))
        env.set_evaluation(True, full_song=True)
        env.reset(range(2), snapshot)
        return env, snapshot

    def geometry(self, env, height=.006, lateral=0., along=0., alignment=1.):
        # 압현면 +Z, 목표 줄 +Y인 독립 해석 가능한 합성 기하다.
        env.press_plane = torch.tensor([0., 0., 1., 0.])
        env.starts = torch.zeros(2, 6, 3)
        env.ends = env.starts.clone()
        env.ends[..., 1] = 1
        env.surface_height.fill_(height)
        env.surface_alignment.fill_(alignment)
        env.surface_delta[:] = torch.tensor([lateral, along, -height])
        env.surface_distance.fill_(math.sqrt(height**2+lateral**2+along**2))

    def test_e0_is_identical_to_unchanged_environment(self):
        baseline, snap = self.make(None)
        control, _ = self.make('E0')
        for tick in (0, 239, 240, 624, 672, 720, 1319, 1320):
            baseline.clock.fill_(tick)
            control.clock.fill_(tick)
            torch.testing.assert_close(control._surface_potential(), baseline._surface_potential(), rtol=0, atol=0)
            for key in ('gate', 'tracking_weight', 'per_finger_rate'):
                torch.testing.assert_close(control._finger_preparation(control._score_time())[key],
                    baseline._finger_preparation(baseline._score_time())[key], rtol=0, atol=0)
            for key in ('events', 'priority_events', 'state'):
                torch.testing.assert_close(control.observation()[key], baseline.observation()[key], rtol=0, atol=0)

    def test_observation_standby_and_hover_factors_are_independent(self):
        for condition in ('E0', 'E1', 'E2', 'E3', 'E4'):
            env, _ = self.make(condition)
            exposed = bool(env._finger_targets(env._score_time())['valid'][0, 1, 0])
            self.assertEqual(exposed, condition in ('E1', 'E4'), condition)
            posture = env._finger_preparation(env._score_time())
            self.assertEqual(float(posture['gate'][0, 1]), 0. if condition in ('E2', 'E4') else 1.)
            # E2는 대기 보상만 제거하며 접근 가중치를 앞당기지 않는다.
            self.assertEqual(float(posture['tracking_weight'][0, 1]), 0.)
            self.geometry(env)
            self.assertEqual(float(env._surface_potential()[0]), 1. if condition in ('E3', 'E4') else 0.)
            self.assertEqual(env.observation()['state'].shape[-1], 557)
            spec = env.contract['reward']['natural_preparation']
            self.assertEqual(spec['condition'], condition)

    def test_hover_band_same_witness_and_facing_quality(self):
        env, _ = self.make()
        for height in (.004, .006, .008):
            self.geometry(env, height=height, lateral=.002)
            state = env._natural_state(env._score_time())
            self.assertTrue(bool(state['ready'][0, 1]))
            self.assertAlmostEqual(float(env._surface_potential()[0]), 1., places=6)
        for values in (dict(height=0.), dict(height=.009), dict(lateral=.004),
                       dict(along=.002), dict(alignment=0.)):
            self.geometry(env, **values)
            self.assertFalse(bool(env._natural_state(env._score_time())['ready'][0, 1]))
            self.assertLess(float(env._surface_potential()[0]), 1.)
        self.geometry(env, height=.006, alignment=-1.)
        self.assertAlmostEqual(float(env._surface_potential()[0]), .8, places=6)

    def test_descent_has_exact_unchanged_surface_endpoint(self):
        env, _ = self.make()
        self.geometry(env, height=.006, alignment=.5)
        values = []
        for seconds, blend in ((2.8, 0.), (2.9, .5), (3., 1.)):
            env.clock.fill_(round(seconds*240))
            state = env._natural_state(env._score_time())
            self.assertAlmostEqual(float(state['blend'][0, 1]), blend, places=6)
            values.append(float(env._surface_potential()[0]))
        self.assertAlmostEqual(values[1], (values[0]+values[2])/2, places=6)
        expected = math.exp(-.006/.03)*(1-.2*(1-.006/.02)*.5)
        self.assertAlmostEqual(values[2], expected, places=6)
        env.natural_preparation['condition'] = 'E0'
        self.assertAlmostEqual(float(env._surface_potential()[0]), expected, places=6)

    def test_first_goal_does_not_expose_arbitrary_later_fingers(self):
        env, _ = self.make(targets=(note(), note('later', finger=1, onset=10., end=11.)))
        selected = env._finger_targets(env._score_time())
        self.assertEqual(selected['valid'][0, :, 0].tolist(), [False, True, False, False])
        env.clock.fill_(8*240)
        self.assertTrue(bool(env._finger_targets(env._score_time())['valid'][0, 0, 0]))

    def test_sustain_has_priority_and_ties_preserve_source_event_order(self):
        now = torch.tensor([3.5, 5.])
        onset = torch.tensor([3., 4., 4.])
        end = torch.tensor([5., 6., 6.])
        press = onset.clone()
        finger = torch.tensor([2, 2, 2])
        result = finger_target_indices(now, onset, end, press, finger,
            preparation_mask=torch.ones(2, 3, dtype=torch.bool))
        self.assertEqual(result['indices'][:, 1, 0].tolist(), [0, 1])
        self.assertEqual(result['indices'][0, 1, 1].item(), 1)
        with self.assertRaises(ValueError):
            finger_target_indices(now, onset, end, press, finger, preparation_mask=torch.ones(2, 3))

    def test_focus_preserves_existing_target_id_ties_for_chords(self):
        targets = (note('z', finger=4), replace(note('a', finger=1), string=1))
        control, _ = self.make('E0', targets)
        early, _ = self.make('E1', targets)
        for tick in (240, 720, 960):
            control.clock.fill_(tick)
            early.clock.fill_(tick)
            for prepare in (False, True):
                old_index, old_valid = control._focus(prepare)
                new_index, new_valid = early._focus(prepare)
                torch.testing.assert_close(new_index, old_index, rtol=0, atol=0)
                torch.testing.assert_close(new_valid, old_valid, rtol=0, atol=0)

    def test_no_wrist_gate_and_terminal_discount_telescope(self):
        env, _ = self.make()
        self.geometry(env)
        env.guide['delta'].fill_(1.)
        self.assertEqual(float(env._surface_potential()[0]), 1.)
        phis = []
        for tick in range(0, 1441, 4):
            env.clock.fill_(tick)
            phis.append(float(env._surface_potential()[0]) if tick < 1440 else 0.)
        gamma = env.approach_gamma
        total = sum(gamma**i*(gamma*phis[i+1]-phis[i]) for i in range(len(phis)-1))
        self.assertAlmostEqual(total, -phis[0], places=10)

    def test_collection_boundary_keeps_potential_and_failure_clears_next(self):
        env, snapshot = self.make()
        env.begin_control(torch.zeros(2, 39))
        before = env.before_surface_potential.clone()
        for _ in range(4):
            env.substep(dict(snapshot, physics_step=env.clock+1))
        after = env._surface_potential().clone()
        env.end_control()
        torch.testing.assert_close(env.terms['song_left_approach'], env.approach_gamma*after-before)
        env.begin_control(torch.zeros(2, 39))
        before = env.before_surface_potential.clone()
        for _ in range(4):
            env.substep(dict(snapshot, physics_step=env.clock+1))
        env.tick_failure[:, 0] = True
        result = env.end_control()
        torch.testing.assert_close(env.terms['song_left_approach'], -before)
        self.assertTrue(bool(result[3].all()))
        self.assertIn('natural_preparation', result[-1][0])

    def test_pre_onset_contact_cannot_pay_first_contact_reward(self):
        env, snapshot = self.make()
        env.clock.fill_(600)
        original = env._contacts
        def contact():
            original()
            return torch.ones_like(env.candidate), torch.zeros_like(env.wrong)
        env._contacts = contact
        env.previous_candidate.fill_(True)
        self.advance(env, snapshot)
        self.assertTrue(bool(env.candidate.all()))
        self.assertFalse(bool(env.note['contact_progress'].any()))
        self.assertEqual(float(env.terms['song_left_contact'].sum()), 0.)
        contact_paid = hold_paid = success_paid = 0.
        while not bool(env.finished.all()):
            self.advance(env, snapshot)
            contact_paid += .5*float(env.terms['song_left_contact'][0])
            hold_paid += .5*float(env.terms['song_clean_hold'][0])
            success_paid += .5*float(env.terms['song_left_success'][0])
        self.assertAlmostEqual(contact_paid, .25, places=6)
        self.assertAlmostEqual(hold_paid, 1., places=6)
        self.assertAlmostEqual(success_paid, .25, places=6)

    def test_partial_reset_preserves_other_diagnostics_and_ledger(self):
        env, snapshot = self.make()
        self.advance(env, snapshot)
        saved = env.natural_seconds[1].clone()
        env.reset([0], snapshot)
        self.assertFalse(bool(env.natural_seconds[0].any()))
        torch.testing.assert_close(env.natural_seconds[1], saved, rtol=0, atol=0)
        trace = env.natural_preparation_trace()
        self.assertEqual(trace['fingers'][1]['target_id'], 'first')
        self.assertEqual(trace['fingers'][1]['observation_exposed'], True)
        self.assertTrue('sample_index' in trace['fingers'][1])


if __name__ == '__main__':
    unittest.main()
