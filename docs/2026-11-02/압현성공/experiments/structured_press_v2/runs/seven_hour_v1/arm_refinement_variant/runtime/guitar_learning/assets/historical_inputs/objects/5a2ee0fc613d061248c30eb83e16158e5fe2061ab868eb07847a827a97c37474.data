"""CPU reset lifecycle checks; recorded bodies do not model native dynamics."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from guitar_learning.core import training_environment
from guitar_learning.runtime.persistent_environment import PersistentContactEnvironment, build_persistent_environment
from guitar_learning.core.task_sampling import build_environment
from guitar_learning.tests.test_training_environment import RecordedSession

BUNDLE = 'data/song_bundles/05_BN2-131-B_solo'


class ReusableRecordedSession(RecordedSession):
    def __init__(self, config, out):
        super().__init__(config, out)
        self.initial_target = self.scene.target.copy()
        self.reset_calls = self.close_calls = 0
        self.fail_reset = self.fail_preparation = False

    def reset_episode(self, config, out):
        self.reset_calls += 1
        if self.fail_reset:
            raise RuntimeError('injected episode reset failure')
        self.scene.steps = 0
        self.scene.target[:] = self.initial_target
        self.scene.forbidden_calls.clear()
        self.preparation_calls = self.policy_calls = 0
        self.unsafe = False
        return self

    def integrate(self):
        if self.fail_preparation:
            raise RuntimeError('injected preparation failure')
        return super().integrate()

    def close(self):
        if not self.closed:
            self.close_calls += 1
        super().close()


class PersistentEnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.environments = []
        self.sessions = []

    def tearDown(self):
        for env in self.environments:
            env.close()
        self.folder.cleanup()

    def build(self, *, persistent=True, music=None, **kwargs):
        sessions = []
        def factory(config, out):
            session = ReusableRecordedSession(config, out)
            self.sessions.append(session)
            sessions.append(session)
            return session
        def contacts(scene):
            return copy.deepcopy(sessions[-1].row()['native_contacts']['contacts'])
        builder = build_persistent_environment if persistent else build_environment
        env = builder({}, Path(self.folder.name)/str(len(self.environments)),
            bundle=BUNDLE, stage='B', start_event_index=0, phrase_events=8,
            tempo_scale=1., seed=7, worker_id=0, music=music,
            session_factory=factory, contact_reader=contacts, time_limit_s=1/60,
            **kwargs)
        self.environments.append(env)
        return env

    def test_same_session_scene_and_contract_with_fresh_episode_histories(self):
        env = self.build(music={'reward_mode': 'dense_v2'})
        first, first_info = env.reset()
        session, scene = env.control.session, env.control.session.scene
        contract = copy.deepcopy(env.contract)
        _, _, _, truncated, _ = env.step(np.ones(39))
        self.assertTrue(truncated)
        self.assertEqual(scene.steps, 484)
        self.assertGreater(np.linalg.norm(env.previous_action), 0.)
        second, info = env.reset()
        self.assertIs(env.control.session, session)
        self.assertIs(session.scene, scene)
        self.assertEqual(len(self.sessions), 1)
        self.assertEqual(session.reset_calls, 1)
        self.assertEqual(session.close_calls, 0)
        self.assertEqual(scene.steps, 480)
        self.assertEqual(session.preparation_calls, 120)
        self.assertEqual(info['prepared_physics_step'], first_info['prepared_physics_step'])
        self.assertEqual(info['task_time_s'], 0.)
        self.assertEqual(env.control_steps, 0)
        self.assertEqual(env.total_reward, 0.)
        self.assertEqual(env.total_cost, 0.)
        self.assertFalse(env.finished)
        np.testing.assert_array_equal(env.previous_action, np.zeros(39))
        np.testing.assert_array_equal(env.control.codec_previous,
                                      env.control.contract.reset_targets())
        self.assertEqual(env._dense_previous_geometry['physics_step'], 480)
        self.assertEqual(env.contract, contract)
        for key in first:
            np.testing.assert_array_equal(first[key], second[key])
        env.close(); env.close()
        self.assertIsNone(env.control.session)
        self.assertFalse(env.control.ready)
        self.assertEqual(session.close_calls, 1)

    def test_legacy_dense_and_pool_keep_original_observation_and_contract(self):
        original_binding = training_environment.ContactEnvironment
        for music in ({'reward_mode':'legacy'}, {'reward_mode':'dense_v2'},
                      {'reward_mode':'dense_v2','goal_event_indices':[0,1,2]}):
            ordinary = self.build(persistent=False, music=music)
            reused = self.build(music=music)
            self.assertIsInstance(reused.control, PersistentContactEnvironment)
            self.assertIs(training_environment.ContactEnvironment, original_binding)
            contracts = []
            for _ in range(3):
                expected, expected_info = ordinary.reset()
                actual, actual_info = reused.reset()
                self.assertEqual(expected_info['training_contract'], actual_info['training_contract'])
                self.assertEqual(expected_info.get('episode_task'), actual_info.get('episode_task'))
                for key in expected:
                    np.testing.assert_array_equal(expected[key], actual[key])
                contracts.append(copy.deepcopy(reused.contract))
                ordinary.step(np.zeros(39)); reused.step(np.zeros(39))
            self.assertTrue(all(contract == contracts[0] for contract in contracts))
            self.assertEqual(reused.control.session.reset_calls, 2)

    def test_reset_and_preparation_failures_destroy_session_once(self):
        for flag, message in (('fail_reset','episode reset'), ('fail_preparation','preparation')):
            env = self.build()
            env.reset()
            session = env.control.session
            setattr(session, flag, True)
            with self.assertRaisesRegex(RuntimeError, message):
                env.reset()
            self.assertFalse(env.control.ready)
            self.assertTrue(env.finished)
            self.assertIsNone(env.control.session)
            self.assertEqual(session.close_calls, 1)
            env.close()
            self.assertEqual(session.close_calls, 1)
            env.reset()
            self.assertIsNot(env.control.session, session)

    def test_folder_failure_and_changed_configuration_close_cached_session(self):
        for mode in ('folder', 'config', 'closed', 'names'):
            env = self.build()
            env.reset()
            session = env.control.session
            if mode == 'folder':
                (env.control.out/'episode_0001').mkdir()
                error = FileExistsError
            elif mode == 'config':
                env.control.config['changed'] = True
                error = ValueError
            elif mode == 'closed':
                session.close()
                error = RuntimeError
            else:
                session.scene.names = ['invalid']*105
                error = ValueError
            with self.assertRaises(error): env.reset()
            self.assertTrue(session.closed)
            self.assertEqual(session.close_calls, 1)
            self.assertIsNone(env.control.session)
            self.assertFalse(env.control.ready)

    def test_snapshot_failure_during_preparation_is_not_suppressed(self):
        env = self.build()
        env.reset()
        session = env.control.session
        with patch.object(env.control, '_snapshot', side_effect=RuntimeError('snapshot failure')):
            with self.assertRaisesRegex(RuntimeError, 'snapshot failure'): env.reset()
        self.assertTrue(session.closed)
        self.assertEqual(session.close_calls, 1)
        self.assertIsNone(env.control.session)

    def test_construction_binding_restored_when_goal_validation_fails(self):
        original = training_environment.ContactEnvironment
        with self.assertRaisesRegex(ValueError, 'unsupported'):
            self.build(music={'goal_event_indices':[0,42]})
        self.assertIs(training_environment.ContactEnvironment, original)
        self.assertEqual(self.sessions, [])

    def test_factory_without_reset_or_returning_closed_session_is_cleaned(self):
        for mode in ('missing', 'closed'):
            env = self.build()
            def factory(config, out):
                session = ReusableRecordedSession(config, out)
                if mode == 'missing': session.reset_episode = None
                else: session.closed = True
                self.sessions.append(session)
                return session
            env.control._native_session_factory = factory
            with self.assertRaises((TypeError, RuntimeError)): env.reset()
            self.assertIsNone(env.control.session)
            self.assertTrue(self.sessions[-1].closed)


if __name__ == '__main__': unittest.main()
