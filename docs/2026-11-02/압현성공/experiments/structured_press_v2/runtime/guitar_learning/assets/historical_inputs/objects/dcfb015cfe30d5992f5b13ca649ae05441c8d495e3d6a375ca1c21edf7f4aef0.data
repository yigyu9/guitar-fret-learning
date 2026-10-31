"""CPU-only one-time reset ownership and explicit phase-clock contracts."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
from guitar_learning.runtime import prepared_reset_v1 as reset


def body(x=0.):
    return dict(pose=dict(p=dict(x=x, y=0., z=0.), r=dict(x=0., y=0., z=0., w=1.)),
                vel=dict(linear=dict(x=.02, y=0., z=0.), angular=dict(x=0., y=.03, z=0.)))


VEC = np.dtype([('x', 'f4'), ('y', 'f4'), ('z', 'f4')])
QUAT = np.dtype([('x', 'f4'), ('y', 'f4'), ('z', 'f4'), ('w', 'f4')])
RB = np.dtype([('pose', [('p', VEC), ('r', QUAT)]), ('vel', [('linear', VEC), ('angular', VEC)])])
DOF = np.dtype([('pos', 'f4'), ('vel', 'f4')])


class FakeGym:
    def __init__(self, scene):
        self.scene = scene
        self.calls = []
        self.dofs = np.zeros(105, dtype=DOF)
        self.guitar = np.zeros(1, dtype=RB)
        reset._assign(self.guitar[0], body())
        self.fail = False

    def get_actor_dof_states(self, env, actor, flags):
        return self.dofs.copy()

    def get_actor_rigid_body_states(self, env, actor, flags):
        return self.guitar.copy()

    def set_actor_dof_states(self, env, actor, values, flags):
        self.calls.append(('human_DOF', self.scene.initialization_complete))
        self.dofs[:] = values
        return not self.fail

    def set_actor_rigid_body_states(self, env, actor, values, flags):
        if actor != self.scene.guitar:
            raise AssertionError('Human articulated RB setter must never be called')
        self.calls.append(('guitar_RB', self.scene.initialization_complete))
        self.guitar[:] = values
        return True

    def set_actor_dof_position_targets(self, env, actor, target):
        self.calls.append(('native_POSITION', self.scene.initialization_complete))
        return True


def plain(value):
    if isinstance(value, np.void):
        return {name: plain(value[name]) for name in value.dtype.names}
    return value.item() if isinstance(value, np.generic) else value


def fixture():
    names = ['joint_' + str(i) for i in range(105)]
    props = np.ones(105, dtype=[('stiffness', 'f4'), ('effort', 'f4')])
    scene = SimpleNamespace(steps=0, initialization_complete=True, names=names,
        human_bodies=['Pelvis'], guitar_bodies=['guitar'], loaded_assets=[], chair_placement={},
        pd_properties=props, control_kp=np.ones(105), control_kd=np.ones(105),
        lower=np.full(105, -1.), upper=np.ones(105), human=0, guitar=1, env=0,
        target=np.zeros(105, dtype='f4'), last_target=np.zeros(105), jacobian_mode='COM')
    scene.gym = FakeGym(scene)
    scene.native = lambda: dict(physics_step=scene.steps, human_body_states=[body()],
        guitar_body_states=[plain(scene.gym.guitar[0])],
        human_dof_states=[plain(value) for value in scene.gym.dofs], chair_body_states=[body()])
    state = scene.native()
    state['physics_step'] = 5280
    state['human_dof_states'] = [dict(pos=float(np.float32(.2)), vel=float(np.float32(.03))) for _ in range(105)]
    state['guitar_body_states'] = [body(.15)]
    initial = dict(joint_names=names, human_body_names=['Pelvis'], guitar_body_names=['guitar'],
        loaded_assets=[], chair_initial_placement={}, native_PD_properties={key: props[key].tolist() for key in props.dtype.names},
        control_K105=np.ones(105).tolist(), control_D105=np.ones(105).tolist())
    return scene, dict(config={}, state=state, target105=np.full(105, .1), initial=initial, source_sha256={})


class PreparedResetTests(unittest.TestCase):
    def test_phase_only_clock_and_attribute_writes_forward(self):
        scene, _ = fixture()
        view = reset.ControlPhaseView(scene)
        self.assertEqual(view.steps, 5280)
        self.assertEqual(view.native()['physics_step'], 0)
        view.jacobian_mode = 'body_origin'
        self.assertEqual(scene.jacobian_mode, 'body_origin')
        scene.steps = 480
        self.assertEqual(view.steps, 5760)
        with self.assertRaises(AttributeError):
            view.steps = 100
        self.assertEqual(scene.steps, 480)

    def test_reset_restores_pos_vel_and_target_once_without_human_RB(self):
        scene, contract = fixture()
        original = copy.deepcopy(contract)
        description = reset._restore_once(scene, contract, 3)
        self.assertEqual(scene.gym.calls, [('human_DOF', False), ('guitar_RB', False), ('native_POSITION', False)])
        self.assertTrue(scene.initialization_complete)
        self.assertEqual(scene.steps, 0)
        self.assertLess(description['human_DOF_pos_vel_max_error'], 1e-7)
        self.assertFalse(description['human_body_exact_checkpoint_claim'])
        self.assertEqual(contract['state'], original['state'])
        np.testing.assert_array_equal(scene.target, np.full(105, .1, dtype='f4'))

    def test_reset_window_closes_on_failure_and_late_restore_rejected(self):
        scene, contract = fixture()
        scene.gym.fail = True
        with self.assertRaises(RuntimeError):
            reset._restore_once(scene, contract, 3)
        self.assertTrue(scene.initialization_complete)
        scene.steps = 1
        with self.assertRaises(ValueError):
            reset._restore_once(scene, contract, 3)

    def test_wrong_names_or_properties_fail_before_state_writes(self):
        for kind in ('names', 'properties'):
            scene, contract = fixture()
            if kind == 'names':
                scene.names[0] = 'wrong_joint'
                contract['initial']['joint_names'] = ['joint_' + str(i) for i in range(105)]
            else:
                scene.pd_properties['effort'][0] = 2.
            with self.assertRaises(ValueError):
                reset._restore_once(scene, contract, 3)
            self.assertEqual(scene.gym.calls, [])

    def test_cached_contract_returns_private_state_and_target_copies(self):
        _, contract = fixture()
        with patch.object(reset, '_load_prepared_reset_contract', return_value=contract):
            first = reset.load_prepared_reset_contract()
            first['state']['human_dof_states'][0]['pos'] = 999.
            first['target105'][0] = 999.
            second = reset.load_prepared_reset_contract()
        self.assertNotEqual(second['state']['human_dof_states'][0]['pos'], 999.)
        self.assertNotEqual(second['target105'][0], 999.)

    def test_real_source_contract_hashes_model_inputs_and_cache(self):
        first = reset.load_prepared_reset_contract()
        self.assertEqual(first['state']['physics_step'], 5280)
        self.assertEqual(len(first['target105']), 105)
        self.assertGreaterEqual(len(first['source_sha256']), 106)
        with patch.object(reset, '_verified_json', side_effect=AssertionError('must not reread source after cache')):
            second = reset.load_prepared_reset_contract()
        np.testing.assert_array_equal(first['target105'], second['target105'])

    def test_session_prepare_never_calls_original_targets(self):
        scene, contract = fixture()
        def initialize(session, config, out):
            session.scene = scene
            session.controller = SimpleNamespace(s=scene, targets=lambda: (_ for _ in ()).throw(AssertionError('forbidden original22s targets')))
        with patch.object(reset, 'load_prepared_reset_contract', return_value=contract), patch.object(reset.NativeSession, '__init__', initialize), patch.object(reset, '_state_all', return_value=3):
            session = reset.PreparedSession({}, Path('/tmp/unused_prepared_reset_test'))
        with patch.object(session, 'submit_policy_target', return_value={'submitted': True}) as submit:
            self.assertEqual(session.prepare_tick(), {'submitted': True})
            np.testing.assert_array_equal(submit.call_args[0][0], contract['target105'])
        self.assertEqual(scene.steps, 0)
        self.assertEqual(session.controller.s.steps, 5280)


if __name__ == '__main__':
    unittest.main()
