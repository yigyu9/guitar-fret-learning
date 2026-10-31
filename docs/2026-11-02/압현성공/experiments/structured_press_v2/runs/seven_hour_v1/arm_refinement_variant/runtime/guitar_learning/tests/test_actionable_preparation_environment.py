"""CPU control/clock/reward contracts; recorded fixtures do not certify dynamics."""
import copy
from pathlib import Path
import tempfile
import unittest
import numpy as np
from guitar_learning.core.environment_v4 import FreeGuitarEnvironment as PreviousEnvironment
from guitar_learning.runtime.persistent_environment import PreparedFreeGuitarEnvironment as FreeGuitarEnvironment
from guitar_learning.runtime.persistent_environment import PreparedPersistentContactEnvironment
from guitar_learning.tests.test_training_environment import LongRecordedSession
from guitar_learning.core.control import ACTIVE_NAMES
from guitar_learning.tests.test_environment_v4 import FakeSession

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


class PreparedPersistentTests(unittest.TestCase):
    def environment(self, folder):
        sessions = []
        def factory(config, out):
            session = LongRecordedSession(config, out)
            sessions.append(session)
            return session
        return PreparedPersistentContactEnvironment({}, folder, action_half_range_rad=.002,
            preparation_seconds=0., session_factory=factory,
            contact_reader=lambda scene: copy.deepcopy(sessions[-1].row()['native_contacts']['contacts']))

    def test_zero_contact_reset_reuses_session_and_preserves_snapshot_order(self):
        with tempfile.TemporaryDirectory() as folder:
            env = self.environment(folder)
            try:
                first, info = env.reset()
                session, scene = env.session, env.session.scene
                self.assertEqual(info['prepared_physics_step'], 0)
                self.assertEqual(first['native_contacts']['physics_step'], 0)
                env.step(np.zeros(39))
                again, info = env.reset()
                self.assertIs(env.session, session)
                self.assertIs(session.scene, scene)
                self.assertEqual(session.reset_calls, 1)
                self.assertEqual(session.close_calls, 0)
                self.assertEqual(session.preparation_calls, 0)
                self.assertEqual(scene.steps, 0)
                np.testing.assert_equal(first, again)
            finally:
                env.close()
            self.assertEqual(session.close_calls, 1)

    def test_zero_contact_reset_failure_destroys_owned_session_once(self):
        with tempfile.TemporaryDirectory() as folder:
            env = self.environment(folder)
            env.reset()
            session = env.session
            session.fail_reset = True
            with self.assertRaisesRegex(RuntimeError, 'episode reset failure'):
                env.reset()
            self.assertIsNone(env.session)
            self.assertFalse(env.ready)
            self.assertEqual(session.close_calls, 1)
            env.close()
            self.assertEqual(session.close_calls, 1)


if __name__ == '__main__': unittest.main()
