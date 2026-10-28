"""CPU native doubles check left21 PD ownership and the final target limiter."""
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

import numpy as np

from guitar_learning.core.control import LEFT_HAND_NAMES
from guitar_learning.core.control import default_profile
from guitar_learning.runtime import finger_session as finger
from guitar_learning.runtime import persistent_session as persistent
from guitar_learning.runtime.headless_session import HeadlessPreparedSession
from guitar_learning.runtime.prepared_reset_v1 import _restore_once
from guitar_learning.tests.test_persistent_session import ResetGym
from guitar_learning.tests.test_prepared_reset_v1 import fixture


ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / 'docs/2026-10-12/stability_adapter_2/results/free_guitar_fretting_v1/native_probe_v1'


class FingerGym(ResetGym):
    def __init__(self, scene):
        super().__init__(scene)
        self.pd_calls = []
        self.fail_pd = False
        self.corrupt_pd_readback = False
        self.corrupt_target_readback = False

    def set_actor_dof_properties(self, env, actor, values):
        self.pd_calls.append(dict(initialization_complete=self.scene.initialization_complete,
                                  physics_step=self.scene.steps, values=values.copy()))
        if self.scene.initialization_complete or actor != self.scene.human:
            self.scene.forbidden_calls.append('set_actor_dof_properties')
            raise RuntimeError('runtime property owner violation')
        self.properties = values.copy()
        if self.corrupt_pd_readback:
            self.properties['effort'][0] += 1.
        return not self.fail_pd

    def get_actor_dof_position_targets(self, env, actor):
        result = self.targets.copy()
        if self.corrupt_target_readback:
            result[self.scene.position_indices[0]] += .01
        return result

    def set_actor_dof_position_targets(self, env, actor, target):
        if self.scene.initialization_complete and not self.scene.submitting_targets:
            self.scene.forbidden_calls.append('set_actor_dof_position_targets')
            raise RuntimeError('runtime POSITION target owner violation')
        return super().set_actor_dof_position_targets(env, actor, target)


def finger_fixture():
    scene, contract = fixture()
    recorded = json.loads((PROBE / 'initial_values.json').read_text())
    prepared = json.loads((PROBE / 'prepared.json').read_text())
    scene.names = recorded['joint_names']
    fields = recorded['native_PD_properties']
    dtype = [(key, '?' if key == 'hasLimits' else 'i4' if key == 'driveMode' else 'f4')
             for key in fields]
    scene.pd_properties = np.zeros(105, dtype=dtype)
    for key in fields:
        scene.pd_properties[key] = fields[key]
    scene.lower, scene.upper = [scene.pd_properties[key].astype(float) for key in ('lower', 'upper')]
    scene.control_kp = np.array(recorded['control_K105'])
    scene.control_kd = np.array(recorded['control_D105'])
    scene.q_ref = np.array(prepared['metadata']['prepared_target105_rad'])
    scene.target = scene.q_ref.astype('f4')
    scene.last_target = scene.target.astype(float)
    scene.zero_indices = np.flatnonzero(scene.lower == scene.upper)
    scene.position_indices = np.flatnonzero(scene.pd_properties['driveMode'] == 1)
    prefixes = tuple(side + '_' + part + '_' for side in ('L', 'R')
                     for part in ('Hip', 'Knee', 'Ankle', 'Toe'))
    scene.lower_indices = np.array([index for index, name in enumerate(scene.names) if name.startswith(prefixes)])
    scene.cfg = {}
    scene.gym = FingerGym(scene)
    scene.sim, scene.env, scene.chair_actor = object(), object(), 2
    scene.controlling = scene.submitting_targets = False
    scene.human_root_fixed = True
    scene.guitar_root_fixed = scene.guitar_gravity_disabled = False
    scene.initial_state_calls, scene.forbidden_calls = [], []
    scene.persistent_native_calls = dict(create_sim=1, create_env=1, load_asset=3, destroy_sim=0)
    def close():
        scene.persistent_native_calls['destroy_sim'] += 1
        scene.sim = None
    scene.close = close
    contract['target105'] = scene.target.astype(float).copy()
    contract['state']['human_dof_states'] = copy.deepcopy(prepared['sample']['native']['human_dof_states'])
    contract['initial'].update(joint_names=list(scene.names), native_PD_properties=copy.deepcopy(fields),
        control_K105=scene.control_kp.tolist(), control_D105=scene.control_kd.tolist())
    return scene, contract


class FingerSessionTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        self.sessions = []

    def tearDown(self):
        for session in self.sessions:
            session.close()
        self.folder.cleanup()

    def session(self, *, fail_pd=False, corrupt_pd=False):
        scene, contract = finger_fixture()
        scene.gym.fail_pd, scene.gym.corrupt_pd_readback = fail_pd, corrupt_pd
        source = copy.deepcopy(contract)
        controller = NS(fk=object(), target_rows=[], right_target=np.arange(12.), right_info={},
                        apply=lambda named: (named, {'finite_lower': True}))
        def initialize(session, config, out, **kwargs):
            session.scene, session.controller = scene, controller
            session.prepared_reset_description = _restore_once(scene, contract, 3)
            session.seed_target105 = contract['target105'].copy()
        output = self.root / str(len(self.sessions)) / 'episode_0000'
        output.mkdir(parents=True)
        with patch.object(HeadlessPreparedSession, '__init__', initialize), \
             patch.object(persistent, 'load_prepared_reset_contract', return_value=contract), \
             patch.object(finger, 'load_prepared_reset_contract', return_value=contract):
            session = finger.FlexibleLeftFingerSession({}, output)
        self.sessions.append(session)
        return session, scene, contract, source, output

    def test_initial_native_pd_changes_only_left21_kd_and_keeps_pose_targets_and_caps(self):
        session, scene, contract, source, output = self.session()
        self.assertEqual(len(scene.gym.pd_calls), 1)
        self.assertFalse(scene.gym.pd_calls[0]['initialization_complete'])
        self.assertEqual(scene.gym.pd_calls[0]['physics_step'], 0)
        self.assertTrue(scene.initialization_complete)
        original = source['initial']['native_PD_properties']
        ix = np.array([scene.names.index(name) for name in LEFT_HAND_NAMES])
        others = np.array([index for index in range(105) if index not in ix])
        for field in scene.pd_properties.dtype.names:
            expected = np.asarray(original[field], dtype=scene.pd_properties[field].dtype)
            if field not in ('stiffness', 'damping'):
                np.testing.assert_array_equal(scene.pd_properties[field], expected)
            np.testing.assert_array_equal(scene.pd_properties[field][others], expected[others])
        for name in LEFT_HAND_NAMES:
            index = scene.names.index(name)
            thumb = name.startswith('LH:thumb')
            self.assertEqual(scene.pd_properties['stiffness'][index], 8. if thumb else 12.)
            self.assertEqual(scene.pd_properties['damping'][index], 1.25 if thumb else 1.5)
            self.assertEqual(scene.pd_properties['effort'][index], 4. if thumb else 20.)
        np.testing.assert_array_equal(scene.target, source['target105'].astype('f4'))
        self.assertEqual(scene.native()['human_dof_states'], source['state']['human_dof_states'])
        self.assertEqual(contract['initial'], source['initial'])
        self.assertEqual(contract['state'], source['state'])
        np.testing.assert_array_equal(contract['target105'], source['target105'])
        self.assertIsNot(session._prepared_contract, contract)
        self.assertEqual(session._prepared_contract['state'], source['state'])
        self.assertNotEqual(session._prepared_contract['initial']['native_PD_properties'], original)
        self.assertEqual(session.prepared_reset_description['finger_control']['profile'], default_profile())
        audit = json.loads((output / 'persistent_reset.json').read_text())
        self.assertTrue(audit['diagnostics']['native_properties_unchanged'])
        self.assertEqual(audit['diagnostics']['finger_control']['profile'], default_profile())
        self.assertEqual(scene.forbidden_calls, [])

    def test_pd_profile_cannot_be_reapplied_or_changed_after_physics(self):
        session, scene, *_ = self.session()
        for step in (0, 4):
            scene.steps = step
            with self.assertRaisesRegex(RuntimeError, 'initial-only'):
                session._apply_finger_profile_once()
        self.assertEqual(len(scene.gym.pd_calls), 1)
        with self.assertRaises(TypeError):
            session._finger_profile['finger_rate_rad_s'] = 9.
        session.finger_control_description['profile']['finger_rate_rad_s'] = 99.
        row = session.submit_policy_target(scene.target.copy())
        self.assertEqual(row['finger_control']['profile']['finger_rate_rad_s'], 4.)

    def test_failed_native_pd_call_or_corrupt_readback_closes_initialization_gate(self):
        for kind in ('setter', 'readback'):
            with self.subTest(kind=kind):
                scene, contract = finger_fixture()
                scene.gym.fail_pd = kind == 'setter'
                scene.gym.corrupt_pd_readback = kind == 'readback'
                controller = NS(fk=object(), target_rows=[])
                def initialize(session, config, out, **kwargs):
                    session.scene, session.controller = scene, controller
                    session.prepared_reset_description = _restore_once(scene, contract, 3)
                output = self.root / kind / 'episode_0000'
                output.mkdir(parents=True)
                with patch.object(HeadlessPreparedSession, '__init__', initialize), \
                     patch.object(persistent, 'load_prepared_reset_contract', return_value=contract), \
                     patch.object(finger, 'load_prepared_reset_contract', return_value=contract):
                    with self.assertRaisesRegex(RuntimeError, 'initialization failed|readback mismatch'):
                        finger.FlexibleLeftFingerSession({}, output)
                self.assertTrue(scene.initialization_complete)
                self.assertIsNone(scene.sim)

    def test_native_final_limiter_passes_four_rad_s_left_but_preserves_other_rates_and_zero8(self):
        session, scene, *_ = self.session()
        before = copy.deepcopy(scene.native())
        previous = scene.target.astype(float).copy()
        target = previous.copy()
        for name in ('LH:thumb1_y', 'LH:index2', 'L_Shoulder_x', 'RH:middle2'):
            target[scene.names.index(name)] += .3
        row = session.submit_policy_target(target)
        for name, rate in (('LH:thumb1_y', 4.), ('LH:index2', 4.),
                           ('L_Shoulder_x', 3.), ('RH:middle2', 1.5)):
            index = scene.names.index(name)
            self.assertAlmostEqual(scene.target[index] - previous[index], rate / 60., places=6)
        self.assertEqual(scene.native(), before)
        np.testing.assert_array_equal(scene.target[scene.zero_indices], scene.q_ref[scene.zero_indices])
        np.testing.assert_array_equal(scene.gym.targets[scene.position_indices], scene.target[scene.position_indices])
        self.assertTrue(row['position_readback_exact'])
        self.assertEqual(row['foot_world_target_IK'], {'finite_lower': True})
        self.assertEqual(row['stage'], 'policy_handoff')
        self.assertFalse(scene.submitting_targets)
        self.assertEqual(len(scene.gym.pd_calls), 1)
        self.assertEqual(len(session.controller.target_rows), 1)

    def test_persistent_reset_restores_original_pose_with_derived_pd_without_reapplying(self):
        session, scene, _, source, _ = self.session()
        baseline = scene.pd_properties.copy()
        identities = session._native_identities()
        for episode in (1, 2):
            scene.steps = 4
            scene.gym.dofs['pos'] = -.7
            scene.gym.dofs['vel'] = .9
            output = self.root / '0' / ('episode_%04d' % episode)
            output.mkdir()
            with patch.object(persistent, '_state_all', return_value=3):
                session.reset_episode({}, output)
            self.assertEqual(session._native_identities(), identities)
            self.assertEqual(scene.steps, 0)
            self.assertEqual(scene.native()['human_dof_states'], source['state']['human_dof_states'])
            np.testing.assert_array_equal(scene.pd_properties, baseline)
            np.testing.assert_array_equal(scene.gym.properties, baseline)
            self.assertEqual(len(scene.gym.pd_calls), 1)
            self.assertTrue(session.prepared_reset_description['finger_control']['applied'])
            self.assertTrue((output / 'persistent_reset.json').is_file())

    def test_runtime_property_mutation_or_upper_foot_ownership_error_fails_closed(self):
        session, scene, *_ = self.session()
        with self.assertRaisesRegex(RuntimeError, 'runtime property'):
            scene.gym.set_actor_dof_properties(scene.env, scene.human, scene.pd_properties)
        self.assertEqual(scene.forbidden_calls, ['set_actor_dof_properties'])
        def contaminate(named):
            named = dict(named)
            named['LH:index2'] += .01
            return named, {}
        session.controller.apply = contaminate
        with self.assertRaisesRegex(RuntimeError, 'Foot maintenance'):
            session.submit_policy_target(scene.target.copy())
        self.assertTrue(session.closed)
        self.assertIsNone(session.scene)


if __name__ == '__main__':
    unittest.main()
