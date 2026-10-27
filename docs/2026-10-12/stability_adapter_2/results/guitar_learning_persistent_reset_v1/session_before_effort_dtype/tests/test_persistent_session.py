"""CPU native doubles verify persistent episode reset ownership and lifecycle."""
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
import numpy as np
from guitar_learning import persistent_session as persistent
from guitar_learning.headless_session import HeadlessPreparedSession
from guitar_learning.prepared_reset_v1 import _restore_once
from guitar_learning.tests.test_headless_session import OriginalGuard, RawGym, parameters
from guitar_learning.tests.test_prepared_reset_v1 import FakeGym, fixture


class ResetGym(FakeGym):
    def __init__(self, scene):
        super().__init__(scene)
        self.properties = scene.pd_properties.copy()
        self.params = parameters()
        self.time = 0.
        self.efforts = []
        self.targets = np.zeros(105)
        matrix = NS(x=NS(x=1.,y=0.,z=0.),y=NS(x=0.,y=1.,z=0.),z=NS(x=0.,y=0.,z=1.))
        self.bodies = [NS(mass=1.,com=NS(x=0.,y=0.,z=0.),inertia=matrix,flags=0)]
        self.shapes = [NS(filter=1,friction=.5,contact_offset=.002,rest_offset=0.)]

    def get_actor_dof_properties(self, *args): return self.properties.copy()
    def get_actor_rigid_body_properties(self, *args): return copy.deepcopy(self.bodies)
    def get_actor_rigid_shape_properties(self, *args): return copy.deepcopy(self.shapes)
    def get_sim_params(self, sim): return self.params
    def get_sim_time(self, sim): return self.time

    def apply_actor_dof_efforts(self, env, actor, values):
        if not self.scene.controlling or actor != self.scene.human:
            raise AssertionError('Original human effort owner required')
        self.efforts.append(np.asarray(values).copy())
        return True

    def set_actor_dof_states(self, *args):
        if self.scene.initialization_complete: raise AssertionError('Runtime state setter')
        self.scene.initial_state_calls.append('set_actor_dof_states')
        return super().set_actor_dof_states(*args)

    def set_actor_rigid_body_states(self, *args):
        if self.scene.initialization_complete: raise AssertionError('Runtime state setter')
        self.scene.initial_state_calls.append('set_actor_rigid_body_states')
        return super().set_actor_rigid_body_states(*args)

    def set_actor_dof_position_targets(self, env, actor, target):
        self.targets = target.copy()
        return super().set_actor_dof_position_targets(env, actor, target)


class PersistentTests(unittest.TestCase):
    def make_session(self, directory):
        scene, contract = fixture()
        scene.cfg = dict(attempt_out=str(directory))
        scene.gym = ResetGym(scene)
        scene.sim = object(); scene.env = object(); scene.chair_actor = 2
        scene.controlling = scene.submitting_targets = False
        scene.human_root_fixed = True
        scene.guitar_root_fixed = scene.guitar_gravity_disabled = False
        scene.initial_state_calls = []
        scene.forbidden_calls = ['earlier-audit-record']
        scene.persistent_native_calls = dict(create_sim=1,create_env=1,load_asset=3,destroy_sim=0)
        scene.play_logic = NS(started=False,phase=None,cycle=None,info={},stage='prepared',fk=object())
        controller = NS(fk=object(), target_rows=[], right_target=np.arange(12.),
                        right_info={},play_latch=None,anchor=object())
        def scene_close():
            scene.persistent_native_calls['destroy_sim'] += 1
            scene.sim = None
        scene.close = scene_close
        def initialize(session, config, out, **kwargs):
            session.scene = scene
            session.controller = controller
            session.prepared_reset_description = _restore_once(scene, contract, 3)
            session.prepared_reset_description['retained_metadata'] = True
            session.seed_target105 = contract['target105'].copy()
        with patch.object(HeadlessPreparedSession, '__init__', initialize), \
             patch.object(persistent, 'load_prepared_reset_contract', return_value=contract):
            session = persistent.PersistentHeadlessPreparedSession({}, directory)
        return session, scene, contract

    def test_same_scene_restores_state_velocity_targets_and_histories(self):
        with tempfile.TemporaryDirectory() as tmp:
            initial = Path(tmp)/'episode_0000'; initial.mkdir()
            session, scene, contract = self.make_session(initial)
            ids = session.persistent_reset_description['native_identities']
            controller, anchor, fk = session.controller, session.controller.anchor, session.controller.fk
            scene.steps = 832; scene.gym.time = 832/240
            scene.gym.dofs['pos'] = -.7; scene.gym.dofs['vel'] = .9
            scene.gym.guitar['pose']['p']['x'] = 10.
            scene.gym.guitar['vel']['linear']['x'] = 9.
            scene.target[:] = -.5; scene.last_target[:] = -.6
            scene.jacobian_mode = 'body_origin'
            controller.target_rows.append({'old': True})
            controller.right_target[:] = 99.; controller.right_info['old'] = True
            controller.play_latch = {'old': True}; controller.release_origin_W = np.ones(3)
            folder = Path(tmp)/'episode_0001'; folder.mkdir()
            with patch.object(persistent, '_state_all', return_value=3):
                self.assertIs(session.reset_episode({}, folder), session)
            self.assertEqual(session.persistent_reset_description['native_identities'], ids)
            self.assertIs(session.controller, controller)
            self.assertIs(session.controller.anchor, anchor); self.assertIs(session.controller.fk, fk)
            np.testing.assert_allclose(scene.gym.dofs['pos'], .2)
            np.testing.assert_allclose(scene.gym.dofs['vel'], .03)
            np.testing.assert_allclose(scene.gym.guitar['pose']['p']['x'], .15)
            np.testing.assert_allclose(scene.gym.guitar['vel']['linear']['x'], .02)
            np.testing.assert_allclose(scene.gym.targets, .1)
            np.testing.assert_allclose(scene.last_target, .1)
            self.assertEqual(scene.steps, 0); self.assertEqual(scene.jacobian_mode, 'COM')
            self.assertEqual(scene.cfg['attempt_out'], str(folder))
            self.assertEqual(controller.target_rows, []); self.assertEqual(controller.right_info, {})
            np.testing.assert_array_equal(controller.right_target, np.arange(12.))
            self.assertIsNone(controller.play_latch); self.assertFalse(hasattr(controller, 'release_origin_W'))
            self.assertEqual(scene.initial_state_calls, ['set_actor_dof_states','set_actor_rigid_body_states']*2)
            self.assertEqual(scene.forbidden_calls, ['earlier-audit-record'])
            self.assertTrue(scene.initialization_complete)
            self.assertEqual(len(scene.gym.efforts), 1)
            np.testing.assert_array_equal(scene.gym.efforts[0], np.zeros(105))
            audit = json.loads((folder/'persistent_reset.json').read_text())
            self.assertEqual(audit['diagnostics']['native_calls']['create_sim'], 1)
            self.assertEqual(audit['diagnostics']['episode_initial_state_offset'], 2)
            self.assertEqual(audit['diagnostics']['native_sim_time_s'], 832/240)
            self.assertEqual(audit['diagnostics']['episode_local_physics_steps'], 0)
            self.assertEqual(audit['diagnostics']['controller_target_history_length'], 0)
            self.assertTrue(session.prepared_reset_description['retained_metadata'])
            session.close(); session.close()
            lifecycle = json.loads((Path(tmp)/'persistent_lifecycle.json').read_text())
            self.assertTrue(session.closed)
            self.assertEqual(lifecycle['native_calls'], dict(create_sim=1,create_env=1,load_asset=3,destroy_sim=1))

    def test_properties_or_config_change_rejected_before_any_state_write(self):
        for kind in ('PD', 'mass', 'collision', 'sim', 'config'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                folder = Path(tmp)/'episode_0000'; folder.mkdir()
                session, scene, _ = self.make_session(folder)
                previous_calls = len(scene.gym.calls)
                if kind == 'PD': scene.gym.properties['effort'][0] += 1.
                if kind == 'mass': scene.gym.bodies[0].mass += 1.
                if kind == 'collision': scene.gym.shapes[0].filter += 1
                if kind == 'sim': scene.gym.params.gravity.z = 0.
                config = {'changed':True} if kind == 'config' else {}
                with self.assertRaisesRegex((RuntimeError,ValueError), 'properties|config'):
                    session.reset_episode(config, Path(tmp)/'episode_0001')
                self.assertEqual(len(scene.gym.calls), previous_calls)
                self.assertTrue(session.closed); self.assertIsNone(session.scene)

    def test_reset_failure_closes_partial_state_and_closes_initializer_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/'episode_0000'; folder.mkdir()
            session, scene, _ = self.make_session(folder)
            scene.gym.fail = True
            with patch.object(persistent, '_state_all', return_value=3):
                with self.assertRaisesRegex(RuntimeError, 'DOF reset failed'):
                    session.reset_episode({}, Path(tmp)/'episode_0001')
            self.assertTrue(scene.initialization_complete)
            self.assertTrue(session.closed); self.assertIsNone(session.scene)
            self.assertEqual(scene.persistent_native_calls['destroy_sim'], 1)
            with self.assertRaisesRegex(RuntimeError, 'closed'):
                session.reset_episode({}, Path(tmp)/'episode_0002')
            self.assertEqual(scene.persistent_native_calls['destroy_sim'], 1)

    def test_normal_integrate_performs_no_state_write_and_requires_fetch_completion(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/'episode_0000'; folder.mkdir()
            session, scene, _ = self.make_session(folder)
            writes = list(scene.initial_state_calls)
            def integrate(session):
                self.assertTrue(session._physics_inflight)
                session.scene.steps += 1
                return {'fetched':True}
            with patch.object(HeadlessPreparedSession, 'integrate', integrate):
                self.assertEqual(session.integrate(), {'fetched':True})
            self.assertFalse(session._physics_inflight)
            self.assertEqual(scene.initial_state_calls, writes)
            session._physics_inflight = True
            with self.assertRaisesRegex(RuntimeError,'completed, fetched'):
                session.reset_episode({}, Path(tmp)/'episode_0001')
            self.assertTrue(session.closed)

    def test_lifecycle_guard_counts_actual_calls_and_retains_native_restrictions(self):
        raw=RawGym(); owner=NS(forbidden_calls=[])
        raw.create_env=lambda *args:'env'
        raw.load_asset=lambda *args:'asset'
        raw.destroy_sim=lambda *args:None
        guard=persistent._counting_guard_type(OriginalGuard,1)(raw,owner)
        self.assertEqual(guard.create_sim(0,4,'physx',parameters()),'native-sim')
        self.assertEqual(guard.create_env('native-sim'),'env')
        self.assertEqual(guard.load_asset('native-sim'),'asset')
        guard.destroy_sim('native-sim')
        self.assertEqual(owner.persistent_native_calls,dict.fromkeys(persistent._COUNTED_APIS,1))
        with self.assertRaisesRegex(RuntimeError,'original restriction'):
            guard.set_actor_rigid_body_states()
        self.assertEqual(owner.forbidden_calls,['set_actor_rigid_body_states'])


if __name__ == '__main__': unittest.main()
