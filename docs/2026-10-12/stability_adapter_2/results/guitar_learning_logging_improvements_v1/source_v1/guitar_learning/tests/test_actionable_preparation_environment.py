"""CPU control/clock/reward contracts; recorded fixtures do not certify dynamics."""
import copy
import hashlib
import json
from pathlib import Path
from unittest.mock import patch
import tempfile
import unittest
import numpy as np
from guitar_learning import training_environment
from guitar_learning.environment_v4 import FreeGuitarEnvironment as PreviousEnvironment
from guitar_learning.environment_v5 import FreeGuitarEnvironment
from guitar_learning.actionable_preparation_environment import (
    build_environment, TASK_METADATA, REWARD_METADATA, PersistentContactEnvironment)
from guitar_learning.control import ACTIVE_NAMES
from guitar_learning.music_task import ScoreTask
from guitar_learning.task_measurement import TaskMeasurement
from guitar_learning.skill_environment_v2 import HISTORY_FIELDS, TIME_FIELDS, COUNT_FIELDS
from guitar_learning.timing_curriculum import TimingConfig
from guitar_learning.tests.test_environment_v4 import FakeSession
from guitar_learning.tests.test_skill_environment import LongRecordedSession

BUNDLE = 'data/song_bundles/05_BN2-131-B_solo'


class ZeroPreparationTests(unittest.TestCase):
    def test_zero_handoff_has_no_hidden_physics_and_first_action_owns39(self):
        with tempfile.TemporaryDirectory() as folder:
            phases = []
            env = FreeGuitarEnvironment({}, folder, action_half_range_rad=.002,
                preparation_seconds=0., session_factory=FakeSession,
                geometry_fn=lambda state, h, g: {},
                sample_callback=lambda scene, phase: phases.append((scene.steps, phase)))
            try:
                _, info = env.reset()
                session = env.session
                reference = session.scene.target.copy()
                self.assertEqual(session.scene.steps, 0)
                self.assertEqual(session.preparation_calls, 0)
                self.assertEqual(session.policy_calls, 0)
                self.assertEqual(info['prepared_physics_step'], 0)
                self.assertEqual(info['preparation_seconds'], 0.)
                self.assertEqual(info['preparation_mode'], 'prepared_state_then_immediate_policy_handoff')
                self.assertEqual(phases, [(0, 'preparation')])  # initial read only
                _, step = env.step(np.ones(39))
                self.assertEqual(session.policy_calls, 1)
                self.assertEqual(session.physics_calls, 4)
                self.assertEqual([s['native']['physics_step'] for s in step['physics_samples240']], [1,2,3,4])
                active = [session.scene.names.index(name) for name in ACTIVE_NAMES]
                held = sorted(set(range(81))-set(active))
                self.assertTrue(np.all(session.scene.target[active] > reference[active]))
                np.testing.assert_array_equal(session.scene.target[held], reference[held])
                np.testing.assert_array_equal(session.scene.target[session.scene.zero_indices], 0)
                for action in (np.zeros(38), np.full(39, np.nan), np.full(39, 1.01)):
                    with self.assertRaises(ValueError): env.step(action)
                self.assertEqual(session.physics_calls, 4)
            finally:
                env.close()

    def test_supported_settling_is_identical_and_bad_durations_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            for duration in (1., 1.5, 2.):
                environments = []
                try:
                    for index, cls in enumerate((PreviousEnvironment, FreeGuitarEnvironment)):
                        env = cls({}, Path(folder)/str(duration)/str(index), action_half_range_rad=.002,
                            preparation_seconds=duration, session_factory=FakeSession,
                            geometry_fn=lambda state, h, g: {})
                        environments.append(env)
                        _, info = env.reset()
                        self.assertEqual(env.session.physics_calls, round(duration*240))
                        self.assertEqual(env.session.preparation_calls, round(duration*60))
                    self.assertEqual(environments[0].reference105.tolist(), environments[1].reference105.tolist())
                finally:
                    for env in environments: env.close()
            for duration in (True, False, -.1, .5, 2.1, 1.001, float('nan'), float('inf')):
                with self.assertRaises(ValueError):
                    FreeGuitarEnvironment({}, folder, action_half_range_rad=.002, preparation_seconds=duration)
            with self.assertRaises(ValueError):
                PreviousEnvironment({}, folder, action_half_range_rad=.002, preparation_seconds=0.)


class ActionablePreparationTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.environments = []

    def tearDown(self):
        for env in self.environments: env.close()
        self.folder.cleanup()

    def environment(self, role='left', **kwargs):
        sessions = []
        def factory(config, out):
            session = LongRecordedSession(config, out)
            sessions.append(session)
            return session
        def contacts(scene):
            return copy.deepcopy(sessions[-1].row()['native_contacts']['contacts'])
        original = training_environment.ContactEnvironment
        env = build_environment({}, Path(self.folder.name)/str(len(self.environments)),
            role=role, bundle=BUNDLE, session_factory=factory, contact_reader=contacts, **kwargs)
        self.assertIs(training_environment.ContactEnvironment, original)
        self.assertIsInstance(env.control, PersistentContactEnvironment)
        self.environments.append(env)
        return env

    def test_all_stages_roles_have_unchanged_shape_zero_native_and_absolute_score(self):
        source = ScoreTask.from_bundle(BUNDLE)
        for role in ('left', 'right'):
            for stage in range(5):
                env = self.environment(role, timing=TimingConfig(stage_index=stage, pre_roll_s=3.))
                observation, info = env.reset()
                self.assertEqual(observation['state'].shape, (536,))
                self.assertEqual(info['score_time_s'], -3.)
                self.assertEqual(info['task_time_s'], 0.)
                self.assertEqual(info['preparation_seconds'], 0.)
                self.assertEqual(env.control.session.scene.steps, 0)
                self.assertEqual(env.task.duration_s, 7.)
                self.assertEqual(env.task.provenance, source.provenance)
                self.assertAlmostEqual(env.task.targets[0].onset_s, 4.12)
                self.assertAlmostEqual(env.task.targets[0].onset_s, 2.+source.targets[0].onset_s+1.)
                self.assertEqual(env.contract['task']['actionable_preparation'], TASK_METADATA)
                self.assertEqual(env.contract['reward']['actionable_preparation'], REWARD_METADATA)
                for name in ('music.remaining_s', 'music.elapsed_s', 'music.held_total_s'):
                    self.assertEqual(env.builder.scales[env.builder.fields.index(name)], 4.)
                for name, scale in zip(HISTORY_FIELDS, env.builder.history_scales):
                    self.assertEqual(scale, 4. if name in TIME_FIELDS else 960. if name in COUNT_FIELDS else 1.)
                index = env.builder.fields.index('timing_history.policy_time_s')
                self.assertEqual(env.builder.scales[index], 7.)

    def test_first_tick_all_measurements_costs_actions_and_lh_reward_accounted(self):
        env = self.environment(time_limit_s=1/60.)
        action = np.r_[np.full(33, .1), np.zeros(6)]
        def contacts(measurement, sample):
            valid = sample['native']['physics_step'] in (1, 2, 4)
            identities = {target.target_id for target in measurement.task.targets}
            return ({identity: dict(fretting_contact_candidate=valid) for identity in identities},
                    identities if valid else set())
        with patch.object(TaskMeasurement, '_contacts', contacts):
            env.reset()
            _, reward, terminated, truncated, info = env.step(action)
        self.assertFalse(terminated)
        self.assertTrue(truncated)
        self.assertEqual(env.control.session.preparation_calls, 0)
        self.assertEqual(env.control.session.policy_calls, 1)
        self.assertEqual([row['physics_step'] for row in info['physics_measurements']], [1,2,3,4])
        expected = .2/240.  # only the interval between consecutive positive samples1 and2
        for row, value in zip(info['physics_measurements'], (0., expected, 0., 0.)):
            self.assertAlmostEqual(row['preparation_contact_reward'], value)
            self.assertIn('stability', row)
        self.assertGreater(expected, 0.)
        self.assertAlmostEqual(info['reward_terms']['preparation_contact'], expected)
        self.assertAlmostEqual(reward, sum(info['reward_terms'].values()))
        self.assertAlmostEqual(info['episode']['reward'], reward)
        self.assertAlmostEqual(env.total_reward, reward)
        self.assertFalse(info['timing']['stage_success'])
        self.assertEqual(info['music']['matched50'], 0)

    def test_right_guide_starts_at_first_tick_without_left_shaping(self):
        env = self.environment('right')
        env.reset()
        _, reward, _, _, info = env.step(np.r_[np.zeros(33), np.full(6, .1)])
        self.assertEqual(env.control.session.scene.steps, 4)
        self.assertEqual(env.control.session.preparation_calls, 0)
        self.assertEqual(info['reward_terms']['preparation_contact'], 0.)
        self.assertTrue(all(row['preparation_contact_reward'] == 0. for row in info['physics_measurements']))
        self.assertGreater(info['reward_terms']['timing_right_guide'], 0.)
        self.assertAlmostEqual(reward, sum(info['reward_terms'].values()))

    def test_transient_first_tick_failure_suppresses_whole_tick_bonus(self):
        env = self.environment()
        with patch.object(TaskMeasurement, '_contacts', self.positive_contacts):
            env.reset()
            env.control.session.unsafe_at = 1
            _, reward, terminated, _, info = env.step(np.zeros(39))
        self.assertTrue(terminated)
        self.assertEqual(env.control.session.scene.steps, 4)
        self.assertEqual(info['termination_reason'], 'terminal_failure')
        self.assertTrue(info['failure_reasons'])
        self.assertFalse(info['physics_measurements'][-1]['stability']['failure_reasons'])
        self.assertEqual(info['reward_terms']['preparation_contact'], 0.)
        self.assertTrue(all(row['preparation_contact_reward'] == 0. for row in info['physics_measurements']))
        self.assertAlmostEqual(reward, sum(info['reward_terms'].values()))
        self.assertAlmostEqual(info['episode']['reward'], reward)
        self.assertFalse(info['timing']['stage_success'])

    def test_exact_two_second_boundary_and_persistent_fresh_reset(self):
        env = self.environment()
        with patch.object(TaskMeasurement, '_contacts', self.positive_contacts):
            self.check_contact_boundary_and_reset(env)

    @staticmethod
    def positive_contacts(measurement, sample):
        identities = {target.target_id for target in measurement.task.targets}
        return ({identity: dict(fretting_contact_candidate=True) for identity in identities}, identities)

    def check_contact_boundary_and_reset(self, env):
        first, reset = env.reset()
        session, scene = env.control.session, env.control.session.scene
        contract = copy.deepcopy(env.contract)
        for _ in range(120):
            _, _, terminated, truncated, info = env.step(np.zeros(39))
            self.assertFalse(terminated or truncated)
        self.assertAlmostEqual(info['task_time_s'], 2.)
        self.assertGreater(info['reward_terms']['preparation_contact'], 0.)
        self.assertAlmostEqual(sum(row['preparation_contact_reward'] for row in info['physics_measurements']), .2/60.)
        _, _, _, _, info = env.step(np.zeros(39))
        self.assertEqual(info['reward_terms']['preparation_contact'], 0.)
        again, reset = env.reset()
        self.assertIs(env.control.session, session)
        self.assertIs(session.scene, scene)
        self.assertEqual(session.reset_calls, 1)
        self.assertEqual(session.close_calls, 0)
        self.assertEqual(scene.steps, 0)
        self.assertEqual(session.preparation_calls, 0)
        self.assertEqual(env.total_reward, 0.)
        self.assertEqual(env.total_cost, 0.)
        self.assertEqual(env.contract, contract)
        for key in first: np.testing.assert_array_equal(first[key], again[key])
        env.close()
        self.assertEqual(session.close_calls, 1)

    def test_invalid_clock_and_goal_rejected_without_leaking_constructor_patch(self):
        original = training_environment.ContactEnvironment
        for kwargs in (dict(timing=TimingConfig()), dict(preparation_seconds=2.),
                       dict(start_event_index=1), dict(tempo_scale=.5), dict(role='joint')):
            with self.assertRaises(ValueError):
                build_environment({}, self.folder.name, role=kwargs.pop('role', 'left'), bundle=BUNDLE, **kwargs)
            self.assertIs(training_environment.ContactEnvironment, original)

    def test_archived_originals_remain_exact(self):
        manifest = Path('guitar_learning/archive/20261018_before_actionable_preparation/manifest_actionable_environment.json')
        for row in json.loads(manifest.read_text())['files']:
            for key in ('original', 'archive'):
                self.assertEqual(hashlib.sha256(Path(row[key]).read_bytes()).hexdigest(), row['sha256'])


if __name__ == '__main__': unittest.main()
