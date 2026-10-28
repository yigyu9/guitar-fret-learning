"""Recorded interface evidence; these tests do not establish native song success."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import torch

from guitar_learning.training.policy import SpecialistPolicy
from guitar_learning.song import progress
from guitar_learning.song.hand_environment import build_environment, HAND_TERMS, SHARED_TERMS, SCHEMA
from guitar_learning.tests.test_training_environment import LongRecordedSession
from guitar_learning.tests.test_song_environment import BUNDLE, SONG
from guitar_learning.tool.validation.rollout import RolloutCollector


class HandSongEnvironmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.environments = []

    def tearDown(self):
        for env in self.environments:
            env.close()
        self.folder.cleanup()

    def environment(self, role, **kwargs):
        sessions = []
        def factory(config, out):
            session = LongRecordedSession(config, out)
            sessions.append(session)
            return session
        def contacts(scene):
            return copy.deepcopy(sessions[-1].row()['native_contacts']['contacts'])
        env = build_environment({}, Path(self.folder.name)/str(len(self.environments)),
            bundle=BUNDLE, song=SONG, role=role, session_factory=factory,
            contact_reader=contacts, **kwargs)
        self.environments.append(env)
        return env, sessions

    def test_full_score_500_contract_and_persistent_reset_for_each_hand(self):
        for role in HAND_TERMS:
            with self.subTest(role=role):
                env, sessions = self.environment(role)
                observation, info = env.reset()
                self.assertEqual(observation['state'].shape, (500,))
                self.assertEqual(observation['events'].shape, (64, 24))
                self.assertEqual(len(env.task.targets), 67)
                self.assertEqual(env.task.duration_s, 1969/60.)
                self.assertIsNone(env.time_limit_s)
                self.assertEqual(info['song']['denominator'], 67)
                self.assertEqual(info['training_contract']['task']['specialist'], dict(
                    schema=SCHEMA, role=role, frozen_partner=False,
                    inactive_action='zero_residual', scope='complete_score'))
                self.assertEqual(env.contract['reward']['hand_projection']['terms'], list(HAND_TERMS[role]))
                self.assertEqual(sessions[0].scene.steps, 0)
                self.assertEqual(sessions[0].preparation_calls, 0)
                env.step(np.zeros(39))
                again, _ = env.reset()
                for key in observation:
                    np.testing.assert_array_equal(observation[key], again[key])
                self.assertEqual(len(sessions), 1)
                self.assertEqual(sessions[0].reset_calls, 1)
                self.assertEqual(sessions[0].scene.steps, 0)

    def test_selected_success_does_not_require_the_other_hand_but_joint_stays_strict(self):
        for role in HAND_TERMS:
            with self.subTest(role=role):
                env, _ = self.environment(role)
                env.reset()
                for note in env.song_ledger.notes.values():
                    note['left_achieved'] = role == 'left'
                    note['right_crossing_id'] = 'crossing' if role == 'right' else None
                env.song_ledger.previous['task_time_s'] = env.task.duration_s
                info = {'episode': {}}
                env._song_info(info, True)
                self.assertTrue(info['song']['stage_success'])
                self.assertFalse(info['song']['joint_stage_success'])
                self.assertFalse(info['song']['joint_provisional_success'])
                self.assertEqual(info['song'][role+'_success_count'], 67)
                other = 'right' if role == 'left' else 'left'
                self.assertEqual(info['song'][other+'_success_count'], 0)
                self.assertEqual(len(info['song']['per_note']), 67)
                self.assertIn('strict_music', info['song'])
                self.assertEqual(info['episode']['song'], info['song'])
                self.assertEqual(info['episode']['musical_quality'], info['musical_quality'])
                env._song_info(info, False)
                self.assertFalse(info['song']['stage_success'])
                self.assertTrue(info['song']['provisional_success'])
                if role == 'right':
                    for field in ('wrong_crossings', 'repeat_crossings'):
                        setattr(env.song_ledger, field, 1)
                        env._song_info(info, True)
                        self.assertFalse(info['song']['stage_success'])
                        setattr(env.song_ledger, field, 0)
                env.song_ledger.invalidate(['guitar_displacement'])
                env._song_info(info, True)
                self.assertFalse(info['song']['stage_success'])

    def test_substep_projection_control_progress_and_episode_totals(self):
        for role in HAND_TERMS:
            with self.subTest(role=role):
                env, sessions = self.environment(role, time_limit_s=2/60.)
                env.reset()
                original_update = env.song_ledger.update
                def prescribed(*args, **kwargs):
                    terms = original_update(*args, **kwargs)
                    return {key: float(index+1) for index, key in enumerate(terms)}
                states = [dict(target_id='a', potential=v) for v in (.2, .8, .8, .4)]
                total = 0.
                with patch.object(env.song_ledger, 'update', side_effect=prescribed), \
                     patch.object(progress, 'snapshot', side_effect=states):
                    for tick in range(2):
                        _, reward, terminated, truncated, info = env.step(np.zeros(39))
                        total += reward
                        self.assertEqual(set(info['reward_terms']), set(HAND_TERMS[role]+SHARED_TERMS))
                        self.assertAlmostEqual(reward, sum(info['reward_terms'].values()))
                        self.assertEqual(len(info['physics_measurements']), 4)
                        for row in info['physics_measurements']:
                            self.assertEqual(set(row['song_reward_terms']), set(HAND_TERMS[role])-{'song_right_progress'})
                        substep_sum = sum(sum(row['song_reward_terms'].values()) for row in info['physics_measurements'])
                        expected_progress = .25*(.99*states[2*tick+1]['potential']-states[2*tick]['potential'])
                        expected = substep_sum + (expected_progress if role == 'right' else 0.)
                        expected += sum(info['reward_terms'][key] for key in SHARED_TERMS)
                        self.assertAlmostEqual(reward, expected)
                        self.assertEqual(info['reward_shaping']['included_in_reward'], role == 'right')
                        self.assertFalse(terminated)
                        self.assertEqual(truncated, tick == 1)
                self.assertEqual(sessions[0].policy_calls, 2)
                self.assertEqual(sessions[0].scene.steps, 8)
                self.assertAlmostEqual(env.total_reward, total)
                self.assertAlmostEqual(info['episode']['reward'], total)

    def test_inactive_nonzero_or_invalid_actions_fail_before_physics(self):
        for role in HAND_TERMS:
            for case in ('inactive', 'nan', 'shape'):
                with self.subTest(role=role, case=case):
                    env, sessions = self.environment(role)
                    env.reset()
                    action = np.zeros(39)
                    if case == 'inactive': action[33 if role == 'left' else 0] = 1e-12
                    elif case == 'nan': action[0] = np.nan
                    else: action = np.zeros(38)
                    with self.assertRaises(ValueError): env.step(action)
                    self.assertTrue(env.finished)
                    self.assertEqual(sessions[0].scene.steps, 0)
                    self.assertEqual(sessions[0].policy_calls, 0)
                    with self.assertRaisesRegex(RuntimeError, 'reset required'): env.step(np.zeros(39))

    def test_rollout_cuts_keep_native_object_and_score_clock(self):
        for role in HAND_TERMS:
            with self.subTest(role=role):
                env, sessions = self.environment(role)
                env.reset()
                policy = SpecialistPolicy(500, size='small', contract=env.contract, role=role)
                collector = RolloutCollector(policy, env)
                first, first_episodes = collector.collect(2)
                session = sessions[0]
                second, second_episodes = collector.collect(2)
                self.assertEqual(first_episodes+second_episodes, [])
                self.assertIs(env.control.session, session)
                self.assertEqual(len(sessions), 1)
                self.assertEqual(session.reset_calls, 1)
                self.assertEqual(session.scene.steps, 16)
                self.assertEqual(collector.episode_steps, 4)
                self.assertEqual(env.control_steps, 4)
                self.assertAlmostEqual(env.last_measured['task_time_s'], 4/60.)
                self.assertEqual(first['state'].shape, (2, 1, 500))
                self.assertEqual(second['state'].shape, (2, 1, 500))

    def test_failure_suppresses_positive_projection_and_cost_is_not_duplicated(self):
        for role in HAND_TERMS:
            with self.subTest(role=role):
                env, sessions = self.environment(role)
                env.reset()
                sessions[0].unsafe_at = 4
                original_update = env.song_ledger.update
                def positive(*args, **kwargs):
                    terms = original_update(*args, **kwargs)
                    return {key: value+100. for key, value in terms.items()}
                with patch.object(env.song_ledger, 'update', side_effect=positive):
                    _, reward, terminated, truncated, info = env.step(np.zeros(39))
                self.assertTrue(terminated)
                self.assertFalse(truncated)
                self.assertTrue(all(value <= 0. for value in info['reward_terms'].values()))
                self.assertTrue(all(value <= 0. for row in info['physics_measurements']
                    for value in row['song_reward_terms'].values()))
                expected_cost = sum(row['stability']['cost'] for row in info['physics_measurements'])+env.safety_config.failure_cost
                self.assertAlmostEqual(info['cost'], expected_cost)
                self.assertAlmostEqual(info['episode']['cost'], expected_cost)
                self.assertAlmostEqual(info['episode']['reward'], reward)
                self.assertFalse(info['song']['stage_success'])

    def test_progress_exception_after_integration_blocks_retry(self):
        env, sessions = self.environment('right')
        with self.assertRaisesRegex(RuntimeError, 'reset required'):
            env.step(np.zeros(39))
        self.assertEqual(sessions, [])
        env.reset()
        before = progress.snapshot(env.task, env.song_ledger.notes, env.last_measured,
                                   env.last_sample, env.song_ledger.window_s)
        with patch.object(progress, 'snapshot', side_effect=[before, ValueError('after sample')]):
            with self.assertRaisesRegex(ValueError, 'after sample'):
                env.step(np.zeros(39))
        self.assertTrue(env.finished)
        self.assertEqual(sessions[0].scene.steps, 4)
        with self.assertRaisesRegex(RuntimeError, 'reset required'):
            env.step(np.zeros(39))
        self.assertEqual(sessions[0].scene.steps, 4)


if __name__ == '__main__':
    unittest.main()
