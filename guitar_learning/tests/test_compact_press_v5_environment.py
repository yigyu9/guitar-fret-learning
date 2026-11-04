"""압현 v5의 관측 교정·단독 보상·해제 평가를 CPU 텐서로 검사한다."""
import json
from contextlib import nullcontext
import unittest
from unittest.mock import patch

import torch

from guitar_learning.gpu.compact_press_v5 import (CompactPressV5Environment, IMPROVEMENT_PROFILES,
    OBSERVATION_SCHEMA, improvement_configuration, reward_configuration,
    ADDED_GOAL_SCALES, actual_reward_posture, geometric_posture_flags, standby_posture_quality)
from guitar_learning.song.task import ScoreTask, ScoreTarget
from guitar_learning.tests.test_gpu_environment import fixture, SONG, BUNDLE
from guitar_learning.gpu.finger_skill_environment import FingerSkillEnvironment, remaining_negative_budget
from guitar_learning.gpu.press_coordination import audible_sections, validate_assignments
from guitar_learning.gpu.control import apply, conjugate, exp_rotation, origin_velocity
import copy
import math

SKILL = dict(schema='guitar_learning.finger_skill.v3', phase='J', scope='scheduled',
             hold_ticks=1, exploration='independent', planned_transitions=400, full_song_after=100)


def target(name, finger=1, string=2, fret=6, onset=3., end=3.5, press=2.9):
    return ScoreTarget(name, name, string, fret, finger, 1, onset, end, press, onset, end)


def coordination_target(identity, string, finger, onset=0., end=.02, press=None):
    return ScoreTarget(identity, identity, string, 6, finger, 1, onset, end,
                       onset if press is None else press, onset, end)


class CompactPressV5Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def make(self, profile='corrected', targets=None, pelvis=False):
        class Environment(CompactPressV5Environment):
            improvement_profile = profile
            include_pelvis = pelvis
        song = dict(SONG, left_fraction=1. if profile in ('full_hold', 'combined') else .4)
        metadata, snapshot = fixture(2)
        context = patch('guitar_learning.gpu.environment.make_task', return_value=ScoreTask(tuple(targets))) if targets else nullcontext()
        with context:
            env = Environment(metadata, bundle=BUNDLE, song=song, skill=SKILL, device='cpu')
        env.set_evaluation(True, full_song=True)
        return env, snapshot, env.reset(range(2), snapshot)

    def tick(self, env, snapshot, failure=False):
        env.begin_control(torch.zeros(2, 39))
        for _ in range(4):
            env.substep(dict(snapshot, physics_step=env.clock+1))
        if failure:
            env.tick_failure[:, 0] = True
        return env.end_control()

    def context(self, env, observation):
        first, last = env.contract['observation']['compact_press']['blocks']['v5_preparation_context']
        return observation['state'][:, first:last]*env.scales[first:last]

    def seed_hold(self, env):
        env.note['best_clean_streak'][:] = env.end-env.onset
        env.note['left'][:] = True
        env.note['ever'][:] = True

    def finish_clock(self, env):
        env.clock[:] = env.duration_ticks*4

    def test_configuration_is_independent_json_and_profiles_are_explicit(self):
        for name in IMPROVEMENT_PROFILES:
            value = improvement_configuration(name)
            self.assertEqual(json.loads(json.dumps(value)), value)
            self.assertEqual(value['full_hold']['enabled'], name in ('full_hold', 'combined'))
            self.assertEqual(value['preparation']['enabled'], name in ('preparation', 'combined'))
            value['observation']['fret_range'][0] = 99
            self.assertEqual(improvement_configuration(name)['observation']['fret_range'][0], 1)
        with self.assertRaises(ValueError):
            improvement_configuration('baseline')

    def test_dimensions_contract_and_velocity_definition_all_profiles(self):
        for name in IMPROVEMENT_PROFILES:
            for pelvis in (False, True):
                env, _, obs = self.make(name, pelvis=pelvis)
                width = 473 if pelvis else 464
                self.assertEqual(obs['state'].shape, (2, width))
                self.assertEqual(obs['priority_events'].shape, (2, 8, 26))
                self.assertEqual(env.contract['compact_press']['schema'], OBSERVATION_SCHEMA)
                self.assertEqual(env.contract['reward']['compact_press_v5'], improvement_configuration(name))
                self.assertEqual(env.contract['reward']['compact_press_v4'], reward_configuration())
                self.assertTrue(env.contract['observation']['event_fields'][9].startswith('negative_pad'))
                description = env.contract['observation']['compact_press']['strict_success']
                self.assertNotIn('legacy40%', description)
                self.assertIn(improvement_configuration(name)['full_hold']['required'], description)
                self.assertTrue(torch.isfinite(obs['state']).all())
                self.assertFalse(obs['priority_events'][~obs['priority_mask']].any())

    def test_common_physics_and_termination_contracts_are_preserved(self):
        env, _, _ = self.make()
        metadata, _ = fixture(2)
        parent = FingerSkillEnvironment(metadata, bundle=BUNDLE, song=SONG, skill=SKILL, device='cpu')
        self.assertEqual(env.contract['action'], parent.contract['action'])
        self.assertEqual(env.contract['termination'], parent.contract['termination'])
        self.assertEqual(env.contact_contract, parent.contact_contract)

    def test_hidden_boundary_changes_are_now_visible_without_changing_goals(self):
        env, _, _ = self.make(targets=[target('a'), target('b', finger=2, string=1,
            onset=3.2, end=3.7, press=3.1)])
        env.focus_mask[:, 1] = False
        env.clock[:] = round(2.95*240)
        original = env.observation()
        before = self.context(env, original)
        self.assertFalse(original['priority_mask'][:, 2].any())
        env.recovery_mask[:, 1] = False
        after = env.observation()
        current = self.context(env, after)
        torch.testing.assert_close(original['priority_events'], after['priority_events'], rtol=0, atol=0)
        torch.testing.assert_close(original['state'][:, :452], after['state'][:, :452], rtol=0, atol=0)
        self.assertTrue((before[:, 1] == 0).all())
        self.assertTrue((current[:, 1] == 1).all())
        self.assertTrue((before[:, 9] == 1).all())
        self.assertFalse(current[:, 9].any())
        self.assertFalse(torch.equal(original['state'], after['state']))

    def test_full_task_budget_normalization_and_long_future_time_do_not_saturate(self):
        env, _, obs = self.make()
        index = env.contract['observation']['fields'].index('episode.remaining_negative_note_budget')
        self.assertAlmostEqual(float(env.scales[index]), .25*67)
        torch.testing.assert_close(obs['state'][:, index], torch.ones(2))
        env, _, obs = self.make(targets=[target('late', onset=80., end=81., press=79.9)])
        raw = self.context(env, obs)
        self.assertTrue((raw[:, 4] > 79).all())
        self.assertTrue((raw[:, 8] == 1).all())
        self.assertTrue((obs['state'].abs() < 10).all())

    def test_fret_range_rejects_fifteen_and_accepts_boundaries(self):
        with self.assertRaisesRegex(ValueError, '1~14'):
            self.make(targets=[target('invalid', fret=15)])
        for fret in (1, 14):
            env, _, _ = self.make(targets=[target('valid', fret=fret)])
            self.assertEqual(int(env.fret[0]), fret)

    def test_left_fraction_is_validated_and_required_is_full_duration(self):
        for name in IMPROVEMENT_PROFILES:
            env, _, _ = self.make(name, targets=[target('one')])
            duration = env.end-env.onset
            expected = duration if name in ('full_hold', 'combined') else duration*.4
            torch.testing.assert_close(env.required, expected)
        metadata, _ = fixture(2)
        class Environment(CompactPressV5Environment):
            improvement_profile = 'full_hold'
        with self.assertRaisesRegex(ValueError, 'left_fraction'):
            Environment(metadata, bundle=BUNDLE, song=SONG, skill=SKILL, device='cpu')

    def test_preparation_factor_retains_ten_percent_at_full_standby(self):
        env, _, _ = self.make('preparation')
        base, _, _ = self.make('corrected')
        state = dict(selected=torch.zeros(2,4,dtype=torch.long),
            valid=torch.ones(2,4,dtype=torch.bool), distance=torch.full((2,4),.02),
            alignment=torch.ones(2,4), blend=torch.zeros(2,4),
            lateral_tolerance=torch.full((2,4),.002), lateral=torch.zeros(2,4))
        for model in (env, base):
            model._natural_state = lambda now: state
            model.surface_distance[:] = .02
        for gate in (0., .5, 1.):
            for model in (env, base):
                model._finger_preparation = lambda now: dict(standby_reward_gate=torch.full((2,4),gate))
            full = env._selected_finger_weights(state['selected']).sum(-1)*(.5*torch.exp(torch.tensor(-.02/.08))+.5*torch.exp(torch.tensor(-.02/.03)))
            torch.testing.assert_close(env._surface_potential(), full*(1-.9*gate))
            torch.testing.assert_close(base._surface_potential(), full*(1-gate))

    def test_new_preparation_potential_masks_nonfinite_geometry(self):
        for name in ('preparation', 'combined'):
            env, _, _ = self.make(name)
            env.surface_distance[:] = float('nan')
            potential = env._surface_potential()
            self.assertTrue(torch.isfinite(potential).all())
            self.assertFalse(potential.any())

    def test_bonus_and_deficit_use_forty_percent_or_full_duration(self):
        note = [target('one', onset=0., end=.5, press=0.)]
        for profile, achieved in (('corrected', True), ('full_hold', False)):
            env, snapshot, _ = self.make(profile, targets=note)
            env.candidate[:] = True
            env.previous_candidate[:] = True
            env._contacts = lambda: (torch.ones(2,1,dtype=torch.bool), torch.zeros(2,1,dtype=torch.bool))
            for _ in range(12):
                self.tick(env, snapshot)
            self.assertEqual(bool(env.note['left'].all()), achieved)
            # 음 종료 정산에서 missing0이어도 최장 streak의 부족률을 반영한다.
            env.note['best_clean_streak'][:] = .2
            env.note['missing'][:] = 0
            env.note['performance_paid'][:] = 0
            env.note['performance_settled'][:] = False
            env.clock[:] = round(.5*240)
            env._prepare_control_end(torch.zeros(2,dtype=torch.bool))
            expected = 0. if achieved else .06
            torch.testing.assert_close(env.note['performance_paid'], torch.full((2,1),expected,dtype=torch.float64))

    def test_pbrs_terminal_and_failure_paid_suppression_preserved(self):
        for name in IMPROVEMENT_PROFILES:
            env, snapshot, _ = self.make(name)
            env._surface_potential = lambda: torch.ones(2)
            env.clock[:] = (env.duration_ticks-1)*4
            self.tick(env, snapshot)
            torch.testing.assert_close(env.terms['song_left_approach'], -torch.ones(2))
        env, snapshot, _ = self.make('combined')
        self.tick(env, snapshot, failure=True)
        episode = env._episode(0, True)
        self.assertEqual(sum(episode['compact_press_v4']['actual_paid_standby']), 0.)
        self.assertFalse(episode['press_completion']['completion_success'])

    def test_release_success_pending_missed_and_abort_are_separate(self):
        env, _, _ = self.make(targets=[target('one')])
        self.seed_hold(env)
        env.clock[:] = round(3.55*240)
        pending = env._episode(0, False)['press_completion']
        self.assertEqual(pending['notes'][0]['release_status'], 'pending')
        self.assertFalse(pending['completion_success'])
        self.finish_clock(env)
        missed = env._episode(0, False)['press_completion']
        self.assertTrue(missed['full_hold_success'])
        self.assertEqual(missed['notes'][0]['release_status'], 'missed')
        self.assertFalse(missed['completion_success'])
        env.v5_released[:] = True
        env.v5_release_s[:] = 3.55
        completed = env._episode(0, False)['press_completion']
        self.assertTrue(completed['completion_success'])
        env.v5_released[:] = False
        aborted = env._episode(0, True)['press_completion']
        self.assertEqual(aborted['notes'][0]['release_status'], 'aborted')
        self.assertTrue(aborted['timeline_complete'])
        self.assertFalse(aborted['safe'])
        self.assertFalse(aborted['completion_success'])

    def test_continuous_identical_target_does_not_require_intermediate_release(self):
        notes = [target('a'), target('b', onset=3.5, end=4., press=3.5)]
        env, _, _ = self.make(targets=notes)
        self.assertFalse(env.release_required[0])
        self.assertTrue(env.release_required[1])
        self.seed_hold(env)
        self.finish_clock(env)
        env.v5_released[:,1] = True
        env.v5_release_s[:,1] = 4.05
        result = env._episode(0, False)['press_completion']
        self.assertEqual(result['notes'][0]['release_status'], 'not_required')
        self.assertTrue(result['completion_success'])

    def test_wrong_only_drop_is_not_new_release_but_raw_pad_loss_is(self):
        env, snapshot, _ = self.make(targets=[target('one')])
        env.clock[:] = round(3.5*240)-1
        env.contact_loaded_target[:] = True
        env.candidate[:] = True
        env.previous_candidate[:] = True
        env.note['ever'][:] = True

        def wrong_only():
            env.contact_loaded_target[:] = True
            return torch.zeros(2,1,dtype=torch.bool), torch.ones(2,1,dtype=torch.bool)

        env._contacts = wrong_only
        env.begin_control(torch.zeros(2,39))
        env.substep(dict(snapshot, physics_step=env.clock+1))
        self.assertTrue(env.note['released'].all())  # 기존 원장은 원문대로 남는다.
        self.assertFalse(env.v5_released.any())

        def raw_loss():
            env.contact_loaded_target[:] = False
            return torch.zeros(2,1,dtype=torch.bool), torch.ones(2,1,dtype=torch.bool)

        env._contacts = raw_loss
        env.substep(dict(snapshot, physics_step=env.clock+1))
        self.assertTrue(env.v5_released.all())
        torch.testing.assert_close(env.v5_release_s, torch.full((2,1),3.5+1/240,dtype=torch.float64))
        for _ in range(2):
            env.substep(dict(snapshot, physics_step=env.clock+1))
        env.end_control()

    def test_h32_window_and_partial_reset_keep_other_rows_context_and_ledgers(self):
        env, snapshot, _ = self.make('combined')
        self.tick(env, snapshot)
        env.note['best_clean_streak'][:,0] = .1
        env.v5_released[:,0] = True
        env.v5_release_s[:,0] = .05
        before = env.observation()
        stats = {name:value.clone() for name,value in env.v4_stats.items()}
        note = env.note['best_clean_streak'].clone()
        env.reset_reward_window()
        torch.testing.assert_close(env.note['best_clean_streak'], note)
        self.assertTrue(env.v5_released[:,0].all())
        env.reset([0], snapshot)
        after = env.observation()
        torch.testing.assert_close(after['state'][1],before['state'][1],rtol=0,atol=0)
        torch.testing.assert_close(env.note['best_clean_streak'][1],note[1])
        self.assertFalse(env.note['best_clean_streak'][0].any())
        self.assertFalse(env.v5_released[0].any())
        self.assertTrue(env.v5_released[1,0])
        self.assertAlmostEqual(float(env.v5_release_s[1,0]), .05)
        for name,value in stats.items():
            torch.testing.assert_close(env.v4_stats[name][1],value[1])


    def contacts(self, env, candidate, wrong=None):
        valid = torch.as_tensor(candidate, dtype=torch.bool).expand(env.N, -1).clone()
        wrong = torch.zeros_like(valid) if wrong is None else torch.as_tensor(wrong, dtype=torch.bool).expand_as(valid).clone()
        env.candidate = valid & ~wrong
        env.wrong = wrong
        env.previous_candidate = env.candidate.clone()
        env.previous_wrong = wrong.clone()
        env._contacts = lambda: (valid & ~wrong, wrong)

    def raw_block(self, env, observation, name):
        first, last = env.contract['observation']['compact_press']['blocks'][name]
        return observation['state'][:, first:last]*env.scales[first:last]

    def test_nine_state_values_use_actual_loss_remaining_budget_and_no_single_group(self):
        env, _, _ = self.make(targets=[coordination_target('a', 2, 1)])
        env.loss[:] = torch.tensor([.1, .2, .3])
        obs = env.observation()
        values = self.raw_block(env, obs, 'v3_state')
        torch.testing.assert_close(values[:, :3], env.loss)
        torch.testing.assert_close(values[:, 3], env._episode_duration().float())
        expected = remaining_negative_budget(env._score_time(), env.onset, env.end,
            env.finger_weights, env.focus_mask, env.note['performance_paid'], env.note['performance_settled'])
        torch.testing.assert_close(values[:, 4], expected.float())
        self.assertFalse(values[:, 5:].any())

    def test_goal_progress_scaling_exact_selected_indices_and_invalid_zero(self):
        env, _, _ = self.make(targets=[coordination_target('a', 2, 1), coordination_target('b', 1, 2)])
        env.note['contact_streak'][:] = .012
        env.note['contact_progress'][:] = .3
        env.note['left'][:] = True
        env.note['best_clean_streak'][:] = .014
        env.note['missing'][:] = .006
        env.note['performance_paid'][:] = .03
        env.note['performance_settled'][:] = True
        obs = env.observation()
        selection = env._finger_targets(env._score_time())
        indices = selection['indices'].flatten(1).clamp_min(0)
        extras = obs['priority_events'][..., 16:]*torch.tensor(ADDED_GOAL_SCALES)
        for row in range(env.N):
            for slot in range(8):
                if bool(obs['priority_mask'][row, slot]):
                    i = indices[row, slot]
                    expected = torch.tensor([.012, .3, 1., .014, .006, .03, 1.,
                                             float(env.required[i]), .02, float(env.finger_weights[row, i])])
                    torch.testing.assert_close(extras[row, slot], expected)
                else:
                    self.assertFalse(extras[row, slot].any())

    def test_observation_does_not_mutate_ledgers_or_group_history(self):
        env, _, _ = self.make(targets=[coordination_target('a', 2, 1), coordination_target('b', 1, 2)])
        before = {name: value.clone() for name, value in env.note.items()}
        groups = {name: value.clone() for name, value in env.coordination_values.items()}
        contract = copy.deepcopy(env.contract)
        for _ in range(3): env.observation()
        self.assertTrue(all(torch.equal(value, env.note[name]) for name, value in before.items()))
        self.assertTrue(all(torch.equal(value, env.coordination_values[name]) for name, value in groups.items()))
        self.assertEqual(contract, env.contract)

    def test_partial_clean_has_half_reward_only_over_exact_overlap(self):
        targets = [coordination_target('a', 2, 1, .001, .020), coordination_target('b', 1, 2, .003, .013)]
        env, snapshot, _ = self.make(targets=targets)
        self.contacts(env, [True, False])
        self.tick(env, snapshot)
        expected = ((1/60.-.001)-.5*(.013-.003))/.019
        torch.testing.assert_close(env.episode_reward_terms['song_clean_hold'], torch.full((2,), expected))
        self.assertAlmostEqual(float(env.coordination_values['observed'][0, 0]), .010, places=12)
        self.assertEqual(float(env.coordination_values['clean'][0, 0]), 0.)

    def test_current_and_previous_wrong_break_both_adjacent_intervals(self):
        env, snapshot, _ = self.make(targets=[coordination_target('a', 2, 1), coordination_target('b', 1, 2)])
        self.contacts(env, [True, True])
        env.begin_control(torch.zeros(2, 39))
        for step in range(4):
            wrong = torch.tensor([[False, step == 1]]).expand(2, -1)
            env._contacts = lambda wrong=wrong: (~wrong, wrong)
            env.substep(dict(snapshot, physics_step=env.clock+1))
        env.end_control()
        self.assertAlmostEqual(float(env.coordination_values['clean'][0, 0]), 2/240., places=12)
        self.assertAlmostEqual(float(env.coordination_values['best'][0, 0]), 1/240., places=12)

    def test_changing_active_set_splits_streak_at_non_aligned_boundary(self):
        targets = [coordination_target('long', 2, 1, 0., .020), coordination_target('short1', 1, 2, 0., .005),
                   coordination_target('short2', 0, 3, .005, .012)]
        env, snapshot, _ = self.make(targets=targets)
        self.contacts(env, [True]*3)
        self.tick(env, snapshot)
        self.assertEqual([row['target_indices'] for row in env.coordination_groups[0]], [(0, 1), (0, 2)])
        self.assertAlmostEqual(float(env.coordination_values['best'][0, 0]), .005, places=12)
        self.assertAlmostEqual(float(env.coordination_values['best'][0, 1]), .007, places=12)
        self.assertFalse(self.raw_block(env, env.observation(), 'v3_state')[:, 5:].any())

    def test_partial_reset_and_collection_window_leave_other_group_history(self):
        env, snapshot, _ = self.make(targets=[coordination_target('a', 2, 1), coordination_target('b', 1, 2)])
        self.contacts(env, [True, True])
        self.tick(env, snapshot)
        before = env.coordination_values['clean'][1].clone()
        env.reset_reward_window()
        torch.testing.assert_close(before, env.coordination_values['clean'][1])
        env.reset([0], snapshot)
        self.assertFalse(env.coordination_values['clean'][0].any())
        torch.testing.assert_close(before, env.coordination_values['clean'][1])
        self.assertTrue(torch.isfinite(env.observation()['state']).all())

    def test_failure_tick_suppresses_positive_hold_using_original_parent_rule(self):
        env, snapshot, _ = self.make(targets=[coordination_target('a', 2, 1), coordination_target('b', 1, 2)])
        self.contacts(env, [True, True])
        env.begin_control(torch.zeros(2, 39))
        for _ in range(4): env.substep(dict(snapshot, physics_step=env.clock+1))
        env.control_invalid[:] = True
        env.tick_failure[:, 0] = True
        env.end_control()
        self.assertFalse(env.episode_reward_terms['song_clean_hold'].any())

    def test_full_note_and_full_overlap_are_required_in_all_summary_locations(self):
        env, _, _ = self.make(targets=[coordination_target('a', 2, 1, 0., 1.5), coordination_target('b', 1, 2, 0., 1.5)])
        env.clock[:] = round(float(env._episode_duration()[0])*240)
        env.note['left'][:] = True
        env.note['best_clean_streak'][:] = .6
        env.coordination_values['observed'][:] = 1.5
        env.coordination_values['clean'][:] = 0.
        env.coordination_values['best'][:] = 0.
        result = env._episode(0, False)
        self.assertTrue(result['song']['legacy_stage_success'])
        self.assertFalse(result['song']['stage_success'])
        self.assertFalse(result['press_coordination']['strict_groups_success'])
        self.assertEqual(result['press_coordination']['simultaneous_clean_s'], 0.)
        self.assertFalse(result['musical_quality']['stage_success'])
        self.assertEqual(result['musical_quality']['song'], result['song'])
        env.note['best_clean_streak'][:] = 1.5
        env.coordination_values['clean'][:] = 1.5
        env.coordination_values['best'][:] = 1.5
        result = env._episode(0, False)
        self.assertTrue(result['song']['stage_success'])
        self.assertTrue(result['press_coordination']['success'])
        self.assertEqual(result['press_coordination']['simultaneous_clean_s'], 1.5)
        self.assertFalse(env._episode(0, True)['song']['stage_success'])

    def test_same_finger_or_string_overlap_rejected_but_preparation_overlap_allowed(self):
        with self.assertRaisesRegex(ValueError, 'distinct strings and fingers'):
            validate_assignments([coordination_target('a', 2, 1), coordination_target('b', 1, 1)])
        with self.assertRaisesRegex(ValueError, 'distinct strings and fingers'):
            validate_assignments([coordination_target('a', 2, 1), coordination_target('b', 2, 2)])
        validate_assignments([coordination_target('a', 2, 1, 0., 1.), coordination_target('b', 2, 1, 1., 2., press=.5)])
        self.assertEqual(audible_sections([coordination_target('a', 2, 1)], [True]), [])

    def block(self, env, observation, name):
        first, last = env.contract['observation']['compact_press']['blocks'][name]
        return observation['state'][:, first:last]*env.scales[first:last]

    def test_previous_action_only_left_and_real_flexion_zero_for_invalid(self):
        env, _, _ = self.make()
        env.previous_action[:, :33] = .2
        env.previous_action[:, 33:] = .9
        observation = env.observation()
        torch.testing.assert_close(self.block(env, observation, 'previous_left_action'),
                                   torch.full((2, 33), .2))
        first, last = env.contract['observation']['compact_press']['blocks']['finger_flexion']
        angles = observation['state'][:, first:first+12]
        self.assertTrue(torch.isfinite(angles).all())
        self.assertEqual(last-first, 16)

    def test_performance_is_interleaved_and_only_audible_selected_clean(self):
        env, _, _ = self.make()
        target = 0
        env.clock[:] = int(float(env.onset[target])*240)+1
        env.candidate[:] = False
        env.wrong[:] = False
        env.candidate[:, target] = True
        env.note['clean_streak'][:, target] = .2
        observation = env.observation()
        performance = self.block(env, observation, 'finger_performance').reshape(2, 4, 2)
        finger = int(env.finger[target])-1
        torch.testing.assert_close(performance[:, finger], torch.tensor([[1., .2]]).expand(2, -1))
        env.wrong[:, target] = True
        self.assertFalse(self.block(env, env.observation(), 'finger_performance').any())

    def test_pelvis_uses_rotating_frame_and_origin_velocity_not_com_velocity(self):
        env, snapshot, _ = self.make(pelvis=True)
        row = {key: value.clone() for key, value in snapshot.items()}
        pelvis = row['body_state'][:, env.pelvis_index].clone()
        pelvis[:, 3:7] = exp_rotation(torch.tensor([[.2, -.3, .4]]).expand(2, -1))
        pelvis[:, 7:10] = torch.tensor([.3, -.2, .1])
        pelvis[:, 10:13] = torch.tensor([.4, .5, -.2])
        row['body_state'][:, env.pelvis_index] = pelvis
        observation = env.reset(range(2), row)
        inverse = conjugate(pelvis[:, 3:7])
        expected = torch.cat((apply(inverse, torch.tensor([0., 0., -1.])),
            apply(inverse, origin_velocity(pelvis, env.com[env.pelvis_index])),
            apply(inverse, pelvis[:, 10:13])), -1)
        torch.testing.assert_close(self.block(env, observation, 'pelvis'), expected)

    def test_combined_reward_metadata_is_independent_and_fixed(self):
        first = reward_configuration()
        self.assertEqual(json.loads(json.dumps(first)), first)
        self.assertTrue(all(first['enabled'].values()))
        first['posture']['half_band_degrees'][0] = 999
        self.assertEqual(reward_configuration()['posture']['half_band_degrees'], [30., 10., 10.])
        env, _, _ = self.make()
        for path in reward_configuration()['authority']['overrides']:
            section, field = path.split('.')
            self.assertEqual(env.contract[section][field]['v4_authoritative_contract'],
                             'reward.compact_press_v4')

    def test_first_press_group_protects_all_assigned_fingers_from_standby(self):
        notes = [target('index', finger=1), target('middle', finger=2, string=1),
                 target('later', finger=3, string=0, onset=5., end=5.5, press=4.9)]
        env, _, _ = self.make(targets=notes)
        posture = env._finger_preparation(torch.zeros(2, dtype=torch.float64))
        self.assertFalse(posture['standby_reward_gate'][:, :2].any())
        self.assertTrue((posture['standby_reward_gate'][:, 2:] == 1).all())
        self.assertTrue((posture['per_finger_rate'] <= .005).all())

    def test_posture_quality_and_geometric_flags_never_issue_joint_commands(self):
        from guitar_learning.gpu.finger_reward import B_PREPARATION_ANGLES_DEGREES
        angles = torch.tensor(B_PREPARATION_ANGLES_DEGREES)*math.pi/180.
        angles = angles.expand(2, 4, 3).clone()
        valid = torch.ones_like(angles, dtype=torch.bool)
        values = standby_posture_quality(angles, valid)
        torch.testing.assert_close(values['quality'], torch.ones(2, 4))
        angles[:, 0] = torch.tensor([-25., 0., 0.])*math.pi/180.
        angles[:, 1] = torch.tensor([70., 20., 10.])*math.pi/180.
        angles[:, 2] = torch.tensor([0., 10., 70.])*math.pi/180.
        flags = geometric_posture_flags(angles, valid)
        self.assertTrue(flags[:, 0, 0].all())
        self.assertTrue(flags[:, 1, 1].all())
        self.assertTrue(flags[:, 2, 2].all())
        angles[:, 3] = float('nan')
        self.assertFalse(standby_posture_quality(angles, valid)['quality'][:, 3].any())
        self.assertFalse(geometric_posture_flags(angles, valid)[:, 3].any())

    def test_alignment_tolerance_uses_actual_adjacent_string_spacing(self):
        env, _, _ = self.make()
        selected = env._natural_state(env._score_time())['selected']
        initial = env._lateral_tolerance(selected)
        self.assertTrue((initial > 0).all())
        self.assertTrue((initial <= .003).all())
        # 가로 간격만 절반으로 줄이면 허용폭도 늘어나지 않는다.
        env.starts[:, :, 0] *= .5
        env.ends[:, :, 0] *= .5
        smaller = env._lateral_tolerance(selected)
        self.assertTrue((smaller <= initial+1e-8).all())


if __name__=='__main__':
    unittest.main()
