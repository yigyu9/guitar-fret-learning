"""Clock/history/reset integration using recorded states, not simulated dynamics."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from guitar_learning.core import training_environment
from guitar_learning.music_task import ScoreTask
from guitar_learning.runtime.persistent_environment import PersistentContactEnvironment
from guitar_learning.skills.skill_environment_v2 import HISTORY_FIELDS, TIME_FIELDS, COUNT_FIELDS
from guitar_learning.timing.timing_curriculum import TimingConfig, TIMING_HISTORY_FIELDS
from guitar_learning.timing.timing_environment import TimingEnvironment, execution_task
from guitar_learning.tests.test_skill_environment import LongRecordedSession


class TimingEnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.environments = []

    def tearDown(self):
        for env in self.environments:
            env.close()
        self.folder.cleanup()

    def environment(self, role='left', **kwargs):
        sessions = []
        def factory(config, out):
            session = LongRecordedSession(config, out)
            sessions.append(session)
            return session
        def contacts(scene):
            return copy.deepcopy(sessions[-1].row()['native_contacts']['contacts'])
        task = ScoreTask.from_bundle('data/song_bundles/05_BN2-131-B_solo')
        with patch.object(training_environment, 'ContactEnvironment', PersistentContactEnvironment):
            env = TimingEnvironment({}, Path(self.folder.name)/str(len(self.environments)),
                task=task, role=role, session_factory=factory, contact_reader=contacts, **kwargs)
        self.environments.append(env)
        return env

    def test_clock_translation_preserves_source_and_relative_score(self):
        original = ScoreTask.from_bundle('data/song_bundles/05_BN2-131-B_solo')
        old = copy.deepcopy(original)
        task = execution_task(original, TimingConfig())
        self.assertEqual(original, old)
        self.assertEqual(task.duration_s, 5.)
        self.assertEqual(task.provenance, original.provenance)
        for a, b in zip(task.targets, original.targets):
            for name in ('press_s', 'onset_s', 'end_s'):
                self.assertAlmostEqual(getattr(a, name)-1., getattr(b, name))
            self.assertEqual(a.source_onset_s, b.source_onset_s)
            self.assertEqual(a.source_end_s, b.source_end_s)

    def test_visible_preroll_policy_actions_and_unchanged_505_normalization(self):
        env = self.environment()
        observation, reset = env.reset()
        self.assertEqual(observation['state'].shape, (505+len(TIMING_HISTORY_FIELDS),))
        self.assertEqual(reset['score_time_s'], -1.)
        self.assertEqual(reset['task_time_s'], 0.)
        self.assertEqual(reset['preparation_seconds'], 2.)
        for name in ('music.elapsed_s', 'music.remaining_s', 'music.held_total_s'):
            self.assertEqual(env.builder.scales[env.builder.fields.index(name)], 4.)
        for name, scale in zip(HISTORY_FIELDS, env.builder.history_scales):
            self.assertEqual(scale, 4. if name in TIME_FIELDS else 960. if name in COUNT_FIELDS else 1.)
        before = env.control.session.scene.steps
        observation, reward, terminated, truncated, info = env.step(np.r_[np.ones(33)*.1, np.zeros(6)])
        self.assertEqual(env.control.session.scene.steps, before+4)
        self.assertFalse(terminated or truncated)
        self.assertAlmostEqual(info['score_time_s'], -1.+1/60.)
        self.assertEqual(len(info['physics_measurements']), 4)
        self.assertEqual(info['music']['matched50'], 0)
        self.assertNotIn('left_hold', info['reward_terms'])
        self.assertAlmostEqual(reward, sum(info['reward_terms'].values()))
        index = env.builder.fields.index('timing_history.policy_time_s')
        self.assertAlmostEqual(float(observation['state'][index]), 1/60./5., places=8)
        self.assertFalse(info['timing']['stage_success'])

    def test_reset_clears_both_history_ledgers_and_keeps_contract(self):
        env = self.environment()
        first, info = env.reset()
        contract = copy.deepcopy(info['training_contract'])
        env.step(np.zeros(39))
        again, reset = env.reset()
        self.assertEqual(reset['training_contract'], contract)
        for key in first:
            np.testing.assert_array_equal(first[key], again[key])
        self.assertEqual(env.timing_ledger.previous_time, 0.)
        self.assertEqual(env.skill_ledger.contacts, set())

    def test_safety_and_truncation_cannot_be_success(self):
        truncated = self.environment(time_limit_s=1/60.)
        truncated.reset()
        _, _, terminated, cut, info = truncated.step(np.zeros(39))
        self.assertFalse(terminated)
        self.assertTrue(cut)
        self.assertFalse(info['specialist']['stage_success'])
        self.assertFalse(info['timing']['completed'])
        unsafe = self.environment()
        unsafe.reset()
        unsafe.control.session.unsafe = True
        _, _, terminated, _, info = unsafe.step(np.zeros(39))
        self.assertTrue(terminated)
        self.assertEqual(info['termination_reason'], 'terminal_failure')
        self.assertTrue(info['timing']['safety_invalidated'])
        self.assertFalse(info['timing']['stage_success'])
        self.assertTrue(all(v <= 0 for k, v in info['reward_terms'].items() if k.startswith('timing_')))

    def test_timing_failure_blocks_further_physics_until_reset(self):
        env = self.environment()
        env.reset()
        with patch.object(env.timing_ledger, 'update', side_effect=ValueError('injected timing failure')):
            with self.assertRaisesRegex(ValueError, 'injected timing failure'):
                env.step(np.zeros(39))
        step = env.control.session.scene.steps
        self.assertTrue(env.finished)
        with self.assertRaisesRegex(RuntimeError, 'reset required'):
            env.step(np.zeros(39))
        self.assertEqual(env.control.session.scene.steps, step)
        env.reset()
        self.assertFalse(env.finished)


if __name__ == '__main__':
    unittest.main()
