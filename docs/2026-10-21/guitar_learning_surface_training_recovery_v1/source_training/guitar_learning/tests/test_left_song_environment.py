"""Recorded left curriculum interfaces; these are not native music evidence."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from guitar_learning.song import environment as original
from guitar_learning.song.left_environment import LeftSongEnvironment, LEFT_FIELDS, LEFT_SCALES
from guitar_learning.song.task import make_task
from guitar_learning.tests.test_skill_environment import LongRecordedSession
from guitar_learning.tests.test_song_environment import BUNDLE, SONG


class ReadyGuide:
    def __init__(self, *args, **kwargs):
        pass

    def metadata(self):
        return dict(schema='recorded.ready_guide')

    def measure(self, sample, now_s):
        return dict(delta_G_m=[.01, .02, .03], rotation_error_rad=[.1, .2, .3],
                    distance_m=.037, angle_rad=.374, ready=True, position_score=1.,
                    orientation_score=1., anchor_fret=5., target_G_m=[0., 0., 0.],
                    wrist_G_m=[0., 0., 0.])


class LeftSongEnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.environments = []
        self.guide_patch = patch('guitar_learning.song.left_environment.WristGuide', ReadyGuide)
        self.guide_patch.start()

    def tearDown(self):
        for env in self.environments:
            env.close()
        self.guide_patch.stop()
        self.folder.cleanup()

    def environment(self, **kwargs):
        sessions = []
        def factory(config, out):
            session = LongRecordedSession(config, out)
            sessions.append(session)
            return session
        def contacts(scene):
            return copy.deepcopy(sessions[-1].row()['native_contacts']['contacts'])
        with patch.object(original.training_environment, 'ContactEnvironment',
                          original.PersistentContactEnvironment):
            env = LeftSongEnvironment({}, Path(self.folder.name)/str(len(self.environments)),
                task=make_task(BUNDLE), bundle=BUNDLE, song=SONG, role='left',
                session_factory=factory, contact_reader=contacts, **kwargs)
        self.environments.append(env)
        return env, sessions

    def test_512_contract_progress_update_and_reset_preserve_training_progress(self):
        env, sessions = self.environment()
        observation, info = env.reset()
        self.assertEqual(observation['state'].shape, (512,))
        contract = copy.deepcopy(env.contract)
        self.assertEqual(contract['observation']['dimension'], 512)
        self.assertEqual(contract['observation']['fields'][-12:],
                         ['left_curriculum.'+name for name in LEFT_FIELDS])
        self.assertEqual(contract['observation']['scales'][-12:], list(LEFT_SCALES))
        self.assertEqual(info['left_curriculum']['progress'], 0.)
        self.assertFalse(info['left_curriculum']['full_safe'])
        env.step(np.zeros(39))
        steps, resets = sessions[0].scene.steps, sessions[0].reset_calls
        changed = env.set_curriculum(1.5)
        self.assertEqual(sessions[0].scene.steps, steps)
        self.assertEqual(sessions[0].reset_calls, resets)
        self.assertEqual(env.contract, contract)
        np.testing.assert_allclose(changed['state'][-3:], [.75, 1., .675])
        again, info = env.reset()
        self.assertEqual(env.curriculum.progress, 1.5)
        self.assertEqual(info['left_curriculum']['progress'], 1.5)
        self.assertEqual(info['left_curriculum']['contact_fraction'], 0.)
        self.assertEqual(info['left_curriculum']['reach_fraction'], 0.)
        self.assertEqual(env.contract, contract)
        self.assertEqual(again['state'].shape, (512,))
        self.assertEqual(len(sessions), 1)
        for invalid in (True, np.nan, -1., 2.01):
            with self.assertRaises(ValueError):
                env.set_curriculum(invalid)
        self.assertEqual(env.curriculum.progress, 1.5)

    def test_weighted_actual_rows_shared_terms_and_episode_total(self):
        env, _ = self.environment(time_limit_s=2/60.)
        env.reset()
        env.set_curriculum(.5)
        update = env.song_ledger.update
        def prescribed(*args, **kwargs):
            terms = update(*args, **kwargs)
            return {key: -2. if 'wrong' in key or 'missing' in key or 'missed' in key
                    else 1. for key in terms}
        total = 0.
        with patch.object(env.song_ledger, 'update', side_effect=prescribed), \
             patch.object(env, '_substep', return_value=dict(
                 song_wrist_position=.2, song_left_contact=.3)):
            for _ in range(2):
                _, reward, terminated, truncated, info = env.step(np.zeros(39))
                total += reward
                self.assertFalse(terminated)
                rows = info['physics_measurements']
                self.assertEqual(len(rows), 4)
                self.assertAlmostEqual(rows[0]['song_reward_terms']['song_wrist_position'], .2*.675)
                self.assertAlmostEqual(rows[0]['song_reward_terms']['song_left_contact'], .3*.575)
                self.assertAlmostEqual(rows[0]['song_reward_terms']['song_wrong_press'], -2.*.575)
                self.assertAlmostEqual(rows[0]['song_reward_terms']['song_left_success'], .225)
                self.assertAlmostEqual(rows[0]['song_reward_terms']['song_left_approach'], .15)
                expected = sum(sum(row['song_reward_terms'].values()) for row in rows)
                expected += info['reward_terms']['action_change']+info['reward_terms']['terminal_failure']
                self.assertAlmostEqual(reward, expected)
                self.assertAlmostEqual(reward, sum(info['reward_terms'].values()))
                self.assertAlmostEqual(info['left_curriculum']['raw_reward_terms']['song_left_contact'], 1.2)
                self.assertEqual(rows[0]['song_reward_terms_unweighted']['song_left_success'], 1.)
        self.assertTrue(truncated)
        self.assertFalse(info['left_curriculum']['full_safe'])
        self.assertAlmostEqual(env.total_reward, total)
        self.assertAlmostEqual(info['episode']['reward'], total)
        self.assertEqual(len(info['episode']['left_curriculum']['per_note']), 67)

    def test_failure_suppresses_all_new_positive_terms_and_cost_stays_once(self):
        env, sessions = self.environment()
        env.reset()
        sessions[0].unsafe_at = 4
        with patch.object(env, '_substep', return_value=dict(
                song_wrist_position=100., song_left_contact=100.)):
            _, reward, terminated, truncated, info = env.step(np.zeros(39))
        self.assertTrue(terminated)
        self.assertFalse(truncated)
        self.assertFalse(info['left_curriculum']['full_safe'])
        self.assertTrue(all(value <= 0. for value in info['reward_terms'].values()))
        self.assertTrue(all(value <= 0. for row in info['physics_measurements']
                            for value in row['song_reward_terms'].values()))
        cost = sum(row['stability']['cost'] for row in info['physics_measurements'])
        self.assertAlmostEqual(info['cost'], cost+env.safety_config.failure_cost)
        self.assertAlmostEqual(info['episode']['cost'], info['cost'])
        self.assertAlmostEqual(info['episode']['reward'], reward)

    def test_relaxed_contact_bonus_is_once_and_progress_is_observable(self):
        env, _ = self.environment()
        env.reset()
        target = env.task.targets[0]
        measured = copy.deepcopy(env.last_measured)
        measured['task_time_s'] = target.press_s
        measured['targets'][target.target_id]['candidate'] = True
        env._previous_measured = measured
        total = 0.
        for tick in range(1, 25):
            current = copy.deepcopy(measured)
            current['task_time_s'] = target.press_s+tick/240.
            terms = env._substep(current, env.last_sample)
            total += terms['song_left_contact']
            if tick == 11:
                self.assertFalse(env.curriculum_notes[target.target_id]['contact_achieved'])
        note = env.curriculum_notes[target.target_id]
        self.assertTrue(note['contact_achieved'])
        self.assertTrue(note['reach_achieved'])
        self.assertAlmostEqual(total, .5+.5*.1)
        env.last_measured = current
        observation = env._observation()
        np.testing.assert_allclose(observation['state'][-6:-3], [1., 1., 1/67.])
        self.assertFalse(env.song_ledger.notes[target.target_id]['left_achieved'])

    def test_wrist_metrics_do_not_replace_original_full_song_success(self):
        env, _ = self.environment()
        env.reset()
        for note in env.song_ledger.notes.values():
            note['left_achieved'] = True
        env.song_ledger.previous['task_time_s'] = env.task.duration_s
        info = dict(episode={}, termination_reason='timeline_complete')
        env._song_info(info, True)
        env._curriculum_info(info)
        self.assertTrue(info['song']['stage_success'])
        self.assertTrue(info['left_curriculum']['full_safe'])
        self.assertEqual(info['left_curriculum']['reach_fraction'], 0.)
        self.assertEqual(info['left_curriculum']['contact_fraction'], 0.)
        self.assertFalse(info['song']['joint_stage_success'])

    def test_post_integration_guide_error_blocks_retry(self):
        env, sessions = self.environment()
        env.reset()
        with patch.object(env, '_substep', side_effect=ValueError('guide fault')):
            with self.assertRaisesRegex(ValueError, 'guide fault'):
                env.step(np.zeros(39))
        self.assertTrue(env.finished)
        self.assertEqual(sessions[0].scene.steps, 4)
        with self.assertRaisesRegex(RuntimeError, 'reset required'):
            env.step(np.zeros(39))
        self.assertEqual(sessions[0].scene.steps, 4)


if __name__ == '__main__':
    unittest.main()
