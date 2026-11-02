"""CPU synthetic accounting tests; these do not demonstrate physical reachability."""
import copy
from dataclasses import replace
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

import torch

from guitar_learning.gpu.finger_skill_environment import FingerSkillEnvironment
from guitar_learning.song.task import make_task
from guitar_learning.tests.test_gpu_environment import fixture, BUNDLE, SONG


SPEC = importlib.util.spec_from_file_location('adjacent_pair_environment',
    Path(__file__).resolve().parents[1]/'pair_environment.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
PairEnvironment = MODULE.PairEnvironment
SKILL = dict(schema='guitar_learning.finger_skill.v3', phase='J', scope='scheduled',
    hold_ticks=1, exploration='independent', planned_transitions=400, full_song_after=100)


class PairEnvironmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)
        source = make_task(BUNDLE, **dict(pre_roll_s=3., tail_s=.5))
        targets = tuple(replace(source.targets[i], target_id='pair-%d'%i,
            event_id='pair-chord', finger=i+1, string=i, fret=12+i,
            press_s=3.25, onset_s=3.25+i*.01, end_s=4.85,
            source_onset_s=.25+i*.01, source_end_s=1.85) for i in range(2))
        cls.task = replace(source, targets=targets, episode_duration_s=5.35)

    def make(self, count=2, task=None):
        metadata, snapshot = fixture(count)
        with patch('guitar_learning.gpu.environment.make_task', return_value=task or self.task):
            env = PairEnvironment(metadata, bundle=BUNDLE, song=SONG,
                device='cpu', skill=SKILL)
        env.reset(range(count), snapshot)
        return env, snapshot

    def integrate(self, env, selector, wrong_at=None, unsafe_at=None):
        # The subclass still observes the parent's before/after native-step
        # boundary. Only the expensive physical update is replaced by a
        # deterministic CPU fixture, never used in a real run.
        env.clock[:] = 0
        env.score_offset[:] = 3.30
        env.tick_failure = torch.zeros(env.N, 7, dtype=torch.bool)
        env.candidate[:] = torch.as_tensor(selector(0), dtype=torch.bool)
        env.wrong[:] = False

        def native_step(snapshot):
            torch.testing.assert_close(snapshot['physics_step'], env.clock+1)
            env.clock += 1
            tick = int(env.clock[0])
            env.candidate[:] = torch.as_tensor(selector(tick), dtype=torch.bool)
            env.wrong[:] = False
            if wrong_at is not None and tick == wrong_at:
                env.wrong[:, 0] = True
            if unsafe_at is not None and tick == unsafe_at:
                env.tick_failure[:, 0] = True

        with patch.object(FingerSkillEnvironment, 'substep', side_effect=native_step):
            for _ in range(360):
                env.substep(dict(physics_step=env.clock+1))

    def result(self, env, index=0):
        return env._pair_episode(index, dict(left_curriculum=dict(full_safe=True)), False)

    def test_both_clean_for_whole_window_and_score_offset_pass(self):
        env, _ = self.make()
        self.integrate(env, lambda tick: [True, True])
        env.note['left'][:] = True
        result = self.result(env)
        self.assertTrue(result['success'])
        self.assertAlmostEqual(result['clean_s'], 1.5)
        self.assertAlmostEqual(result['longest_clean_s'], 1.5)
        self.assertEqual(result['individual_achievements'], [True, True])
        self.assertEqual(result['integration_hz'], 240)

    def test_sequential_individual_latches_do_not_imply_joint_success(self):
        env, _ = self.make()
        self.integrate(env, lambda tick: [tick <= 180, tick > 180])
        env.note['left'][:] = True
        env.clock[:] = env.duration_ticks*4
        result = env._episode(0, False)
        self.assertTrue(result['song']['stage_success'])
        self.assertEqual(result['simultaneous_press']['individual_achievements'], [True, True])
        self.assertFalse(result['simultaneous_press']['success'])
        self.assertEqual(result['simultaneous_press']['clean_s'], 0.)

    def test_one_clean_is_never_pair_success(self):
        env, _ = self.make()
        self.integrate(env, lambda tick: [True, False])
        result = self.result(env)
        self.assertFalse(result['success'])
        self.assertEqual(result['individual_clean_s'], [1.5, 0.])

    def test_single_wrong_endpoint_breaks_both_adjacent_intervals(self):
        env, _ = self.make()
        self.integrate(env, lambda tick: [True, True], wrong_at=180)
        result = self.result(env)
        self.assertFalse(result['success'])
        self.assertAlmostEqual(result['wrong_union_s'], 2/240.)
        self.assertAlmostEqual(result['clean_s'], 1.5-2/240.)
        self.assertLess(result['longest_clean_s'], .76)

    def test_unsafe_native_substep_is_not_hidden_by_clean_endpoints(self):
        env, _ = self.make()
        self.integrate(env, lambda tick: [True, True], unsafe_at=179)
        result = self.result(env)
        self.assertFalse(result['success'])
        self.assertFalse(result['full_safe'])
        self.assertGreater(result['unsafe_s'], 0.)

    def test_partial_reset_preserves_other_row_and_selected_pair(self):
        env, snapshot = self.make()
        self.integrate(env, lambda tick: [True, True])
        before = {key: value[1].clone() for key, value in env.pair_values.items()}
        individual = env.pair_individual_clean[1].clone()
        env.pair_unsafe_seen[:] = True
        env.reset([0], snapshot)
        for name, value in env.pair_values.items():
            self.assertEqual(float(value[0]), 0.)
            torch.testing.assert_close(value[1], before[name])
        torch.testing.assert_close(env.pair_individual_clean[1], individual)
        self.assertFalse(bool(env.pair_unsafe_seen[0]))
        self.assertTrue(bool(env.pair_unsafe_seen[1]))
        self.assertTrue(bool(env.focus_mask.all()))

    def test_quarter_exposure_and_full_exposure_retain_both_targets(self):
        env, snapshot = self.make()
        self.assertEqual(env.catalog.closed_groups, ((0, 1),))
        self.assertTrue(all(set(p.target_indices) == {0, 1} for p in env.catalog.phrases))
        for committed in (0, 99, 100, 400):
            env.set_training_progress(committed)
            env.reset(range(env.N), snapshot)
            self.assertTrue(bool(env.focus_mask.all()))

    def test_bad_scope_or_pair_mapping_rejects(self):
        targets = self.task.targets
        with self.assertRaises(ValueError):
            self.make(task=replace(self.task, targets=targets[:1]))
        for change in (dict(finger=1), dict(finger=4), dict(string=0),
                       dict(string=3), dict(fret=15), dict(onset_s=3.31), dict(end_s=4.79)):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.make(task=replace(self.task,
                    targets=(targets[0], replace(targets[1], **change))))

    def test_diagnostic_addition_keeps_parent_control_observation_reward_contract(self):
        env, snapshot = self.make()
        metadata, _ = fixture(2)
        with patch('guitar_learning.gpu.environment.make_task', return_value=self.task):
            parent = FingerSkillEnvironment(metadata, bundle=BUNDLE, song=SONG,
                device='cpu', skill=SKILL)
        parent.reset(range(2), snapshot)
        expected = copy.deepcopy(env.contract)
        expected['diagnostics'].pop('simultaneous_press')
        self.assertEqual(expected, parent.contract)
        for key, value in env.observation().items():
            torch.testing.assert_close(value, parent.observation()[key], rtol=0, atol=0)
        for instance in (env, parent):
            instance.begin_control(torch.zeros(2, 39))
            for _ in range(4):
                instance.substep(dict(snapshot, physics_step=instance.clock+1))
        actual, original = env.end_control(), parent.end_control()
        for a, b in zip(actual[1:4], original[1:4]):
            torch.testing.assert_close(a, b, rtol=0, atol=0)
        for name in env.terms:
            torch.testing.assert_close(env.terms[name], parent.terms[name], rtol=0, atol=0)


if __name__ == '__main__':
    unittest.main()
