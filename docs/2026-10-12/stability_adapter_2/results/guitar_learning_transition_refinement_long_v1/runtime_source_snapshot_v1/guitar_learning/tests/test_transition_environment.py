"""Persistent recorded-session contracts; playback is not dynamic validation."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from guitar_learning.transition.environment import build_environment, LEFT_TERMS
from guitar_learning.song_reward_v2.environment import build_environment as reward_environment
from guitar_learning.tests.test_song_environment import SONG
from guitar_learning.tests.test_transition_task import BUNDLE, config
from guitar_learning.tests.test_skill_environment import LongRecordedSession


class TransitionEnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.environments = []

    def tearDown(self):
        for env in self.environments: env.close()
        self.folder.cleanup()

    def environment(self, role='left', **kwargs):
        sessions = []
        def factory(cfg, out):
            session = LongRecordedSession(cfg, out); sessions.append(session)
            return session
        def contacts(scene): return copy.deepcopy(sessions[-1].row()['native_contacts']['contacts'])
        env = build_environment({}, Path(self.folder.name)/str(len(self.environments)),
            bundle=BUNDLE, transition=config('pair', role=role),
            session_factory=factory, contact_reader=contacts, **kwargs)
        self.environments.append(env)
        return env, sessions

    def test_exact500_state_and39_action_contract_unmodified(self):
        env, sessions = self.environment()
        observation, info = env.reset()
        old_sessions = []
        def factory(cfg, out):
            value = LongRecordedSession(cfg, out); old_sessions.append(value); return value
        old = reward_environment({}, Path(self.folder.name)/'baseline', bundle=BUNDLE, song=SONG,
            session_factory=factory,
            contact_reader=lambda scene: copy.deepcopy(old_sessions[-1].row()['native_contacts']['contacts']))
        self.environments.append(old)
        old.reset()
        self.assertEqual(env.contract['observation'], old.contract['observation'])
        self.assertEqual(env.contract['action'], old.contract['action'])
        self.assertEqual(env.contract['termination'], old.contract['termination'])
        self.assertEqual(env.contract['reward']['song'], old.contract['reward']['song'])
        remaining_index = env.builder.fields.index('music.remaining_s')
        self.assertAlmostEqual(float(observation['state'][remaining_index]),
                               env.task.duration_s/(1969/60.))
        self.assertEqual(observation['state'].shape, (500,))
        self.assertEqual(observation['events'].shape, (64, 24))
        self.assertEqual(info['training_contract']['task']['transition']['role'], 'left')
        self.assertEqual(info['transition']['physics_sample_count'], 0)
        self.assertEqual(sessions[0].scene.steps, 0)
        env.step(np.zeros(39))
        self.assertEqual(env.transition_ledger.sample_count, 4)
        env.reset()
        self.assertEqual(len(sessions), 1)
        self.assertEqual(env.transition_ledger.sample_count, 0)

    def test_left_rejects_nonzero_right_before_integration_and_projects_rewards(self):
        env, sessions = self.environment(time_limit_s=1/60.)
        env.reset()
        bad = np.zeros(39); bad[-1] = .001
        with self.assertRaisesRegex(ValueError, 'zero right'): env.step(bad)
        self.assertEqual(sessions[0].scene.steps, 0)
        _, reward, terminated, truncated, info = env.step(np.zeros(39))
        self.assertFalse(terminated); self.assertTrue(truncated)
        self.assertEqual(set(info['reward_terms']), LEFT_TERMS)
        self.assertAlmostEqual(reward, sum(info['reward_terms'].values()))
        self.assertAlmostEqual(reward, info['episode']['reward'])
        self.assertIn('song_right_progress', info['unprojected_reward_terms'])
        self.assertEqual(info['transition']['physics_sample_count'], 4)
        self.assertEqual(info['episode']['transition'], info['transition'])
        self.assertFalse(info['transition']['completed'])
        self.assertFalse(info['transition']['successful'])

    def test_failure_preserves_all_native_cost_and_blocks_success(self):
        env, sessions = self.environment()
        env.reset(); sessions[0].unsafe_at = 4
        _, reward, terminated, truncated, info = env.step(np.zeros(39))
        self.assertTrue(terminated); self.assertFalse(truncated)
        expected = sum(row['stability']['cost'] for row in info['physics_measurements'])+env.safety_config.failure_cost
        self.assertAlmostEqual(info['cost'], expected)
        self.assertAlmostEqual(info['episode']['cost'], expected)
        self.assertFalse(info['transition']['safety_valid'])
        self.assertFalse(info['transition']['stage_success'])
        self.assertTrue(all(v <= 0 for v in info['reward_terms'].values()))
        with self.assertRaisesRegex(RuntimeError, 'reset required'): env.step(np.zeros(39))
        self.assertEqual(sessions[0].scene.steps, 4)

    def test_joint_keeps_right_rewards_and_allows_both_actors(self):
        env, _ = self.environment(role='joint', time_limit_s=1/60.)
        env.reset()
        _, reward, _, _, info = env.step(np.full(39, .01))
        self.assertIn('song_right_progress', info['reward_terms'])
        self.assertNotIn('unprojected_reward_terms', info)
        self.assertAlmostEqual(reward, sum(info['reward_terms'].values()))
        self.assertIn('strict100', info['transition']['music_criterion'])

    def test_measurement_failure_blocks_later_integration(self):
        env, sessions = self.environment()
        env.reset()
        with patch.object(env.transition_ledger, 'update', side_effect=ValueError('diagnostic failure')):
            with self.assertRaisesRegex(ValueError, 'diagnostic failure'): env.step(np.zeros(39))
        with self.assertRaisesRegex(RuntimeError, 'reset required'): env.step(np.zeros(39))
        self.assertEqual(sessions[0].scene.steps, 4)

    def test_full_recorded_episode_complete_is_separate_from_success(self):
        env, sessions = self.environment()
        env.reset()
        for tick in range(round(env.task.duration_s*60)):
            _, _, terminated, truncated, info = env.step(np.zeros(39))
            self.assertFalse(truncated)
            self.assertEqual(terminated, tick == round(env.task.duration_s*60)-1)
        self.assertTrue(info['transition']['completed'])
        self.assertEqual(info['transition']['physics_sample_count'], round(env.task.duration_s*240))
        self.assertEqual(sessions[0].reset_calls, 0)
        self.assertFalse(info['transition']['successful'])
        self.assertEqual(info['episode']['transition'], info['transition'])


if __name__ == '__main__': unittest.main()
