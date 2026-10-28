"""Independent rotation/FK derivatives and compact actual16-snapshot regression."""
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

import numpy as np
import torch
from scipy.spatial.transform import Rotation

from guitar_learning.core.control import LEFT_ARM_NAMES
from guitar_learning.native.paths import HUMAN
from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract
from guitar_learning.tool.experiments.short_finger_learning.wrist import (
    _so3_left_jacobian, _wrist_position_groups, _wrist_position_jacobian, wrist_error_and_jacobian,
    bounded_wrist_target, WRIST_CONTROL)


def source_cache(columns=None):
    prepared = load_prepared_reset_contract()
    initial = prepared['initial']
    names = initial['joint_names']
    bodies = ['human/'+n for n in initial['human_body_names']]
    bodies += ['guitar/'+n for n in initial['guitar_body_names']]+['chair/box']
    xml = ET.parse(HUMAN)
    groups = {}
    for element in xml.iter('body'):
        if element.get('name') in ('L_Thorax', 'L_Shoulder', 'L_Elbow', 'L_Wrist'):
            joints = element.findall('joint')
            groups[element.get('name')] = (torch.tensor([names.index(j.get('name')) for j in joints]),
                torch.tensor([[float(v) for v in j.get('axis').split()] for j in joints], dtype=torch.float64).T)
    controller = SimpleNamespace(names=names, bodies=initial['human_body_names'], human_xml=xml, groups=groups)
    columns = torch.tensor([names.index(n) for n in LEFT_ARM_NAMES]) if columns is None else columns
    return prepared, bodies, controller, _wrist_position_groups(controller, bodies, columns)


def actual_snapshot():
    fixture = np.load(Path(__file__).parent/'fixtures/wrist_position_jacobian_native_v1.npz')
    assert str(fixture['raw_sha256']) == '9c76fd3674b64371f52ea43c82e22842b71c69208682a932712104a471f1db71'
    prepared, bodies, controller, cache = source_cache()
    assert fixture['joint_names'].tolist() == controller.names and fixture['body_names'].tolist() == bodies
    count = len(fixture['q'])
    body = torch.zeros(count, len(bodies), 13, dtype=torch.float64); body[:, :, 6] = 1
    native = torch.zeros(count, len(controller.bodies)-1, 6, 105, dtype=torch.float64)
    wrist = bodies.index('human/L_Wrist')
    for k, column in enumerate(cache['columns']):
        native[:, wrist-1, :, column] = torch.tensor(fixture['wrist_native'][:, :, k], dtype=torch.float64)
    for k, (parent, own, qids, _, _) in enumerate(cache['groups']):
        body[:, parent, 3:7] = torch.tensor(fixture['parent_quaternion'][:, k], dtype=torch.float64)
        for j, column in enumerate(qids):
            native[:, own-1, 3:, column] = torch.tensor(fixture['own_angular'][:, k, :, j], dtype=torch.float64)
    body[:, wrist] = torch.tensor(fixture['wrist_state'], dtype=torch.float64)
    snapshot = dict(q=torch.tensor(fixture['q'], dtype=torch.float64), body_state=body, jacobian=native,
        reset_body_snapshot=torch.zeros(count, dtype=torch.bool))
    return prepared, controller, bodies, cache, wrist, torch.tensor(fixture['wrist_com'], dtype=torch.float64), snapshot


class WristPositionJacobianTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def test_left_derivative_with_parent_axes_and_nonidentity_post_bind(self):
        parent = Rotation.from_rotvec([.4, -.3, .7])
        bind = Rotation.from_rotvec([-.5, .2, .6])
        basis = np.array([[0., -1., 0.], [0., 0., 1.], [1., 0., 0.]])
        for q in (np.zeros(3), np.array([1e-11, -2e-11, 3e-11]), np.array([1.7, -.6, .8])):
            analytic = parent.as_matrix()@_so3_left_jacobian(torch.tensor(basis@q)).numpy()@basis
            numeric = []
            for i in range(3):
                step = np.eye(3)[i]*1e-6
                rp = parent*Rotation.from_rotvec(basis@(q+step))*bind
                rm = parent*Rotation.from_rotvec(basis@(q-step))*bind
                numeric.append((rp*rm.inv()).as_rotvec()/2e-6)
            np.testing.assert_allclose(analytic, np.stack(numeric, 1), atol=3e-10, rtol=0)

    def test_named_source_groups_reject_wrong_row_or_axis_order(self):
        _, bodies, controller, cache = source_cache()
        self.assertEqual([controller.names[int(i)] for i in cache['columns']], list(LEFT_ARM_NAMES))
        changed = list(bodies); changed[1], changed[2] = changed[2], changed[1]
        with self.assertRaises(ValueError): _wrist_position_groups(controller, changed, cache['columns'])
        ids, basis = controller.groups['L_Shoulder']
        controller.groups['L_Shoulder'] = (ids.flip(0), basis.flip(1))
        with self.assertRaises(ValueError): _wrist_position_groups(controller, bodies, cache['columns'])

    def test_actual16_snapshots_match_independent_full_fk_position_derivatives(self):
        prepared, controller, bodies, cache, wrist, com, snapshot = actual_snapshot()
        original = {key: value.clone() for key, value in snapshot.items()}
        result = _wrist_position_jacobian(snapshot, wrist, com, cache).numpy()
        qref = np.array([r['pos'] for r in prepared['state']['human_dof_states']])
        fk = full_fk(SimpleNamespace(names=controller.names, human_bodies=controller.bodies, q_ref=qref), prepared['state'])
        derivatives = []
        for row, q in enumerate(snapshot['q'].numpy()):
            position, rotation = fk(q)['L_Wrist']
            actual = snapshot['body_state'][row, wrist].numpy()
            self.assertLess(np.linalg.norm(position-actual[:3]), 1e-6)
            self.assertLess((rotation.inv()*Rotation.from_quat(actual[3:7])).magnitude(), 2e-6)
            numeric = []
            for col in cache['columns']:
                qp, qm = q.copy(), q.copy(); qp[int(col)] += 1e-5; qm[int(col)] -= 1e-5
                pp, rp = fk(qp)['L_Wrist']; pm, rm = fk(qm)['L_Wrist']
                numeric.append(np.r_[(pp-pm)/2e-5, (rp*rm.inv()).as_rotvec()/2e-5])
            derivatives.append(np.stack(numeric, 1))
        derivatives = np.stack(derivatives)
        error = abs(result-derivatives)
        self.assertLess(float(error[:, :3].max()), 1e-6)
        self.assertLess(float(error[:, 3:].max()), 2e-6)
        float_snapshot = {key: value.float() if value.is_floating_point() else value for key, value in snapshot.items()}
        float_cache = dict(columns=cache['columns'], groups=tuple(
            (parent, own, qids, basis.float(), slots) for parent, own, qids, basis, slots in cache['groups']))
        float_result = _wrist_position_jacobian(float_snapshot, wrist, com.float(), float_cache).double().numpy()
        float_error = abs(float_result-derivatives)
        self.assertLess(float(float_error[:, :3].max()), 1e-6)
        self.assertLess(float(float_error[:, 3:].max()), 2e-6)
        for key, value in original.items():
            torch.testing.assert_close(snapshot[key], value)
        # Output column permutation follows named caller order, not fixed indices.
        _, _, _, permuted = source_cache(cache['columns'].flip(0))
        torch.testing.assert_close(_wrist_position_jacobian(snapshot, wrist, com, permuted), torch.tensor(result[:, :, ::-1].copy()))

    def test_reset_nan_rows_never_enter_basis_solve(self):
        _, _, bodies, cache, wrist, com, snapshot = actual_snapshot()
        snapshot = {k:v[:2].clone() for k, v in snapshot.items()}
        snapshot['reset_body_snapshot'][0] = True
        for key in ('q', 'body_state', 'jacobian'): snapshot[key][0] = float('nan')
        solve = torch.linalg.solve
        with patch('torch.linalg.solve', wraps=solve) as checked:
            error, result = wrist_error_and_jacobian(snapshot, wrist, bodies.index('guitar/guitar'), com,
                cache, torch.zeros(2, 3, dtype=torch.float64), torch.tensor([[0.,0.,0.,1.]]*2, dtype=torch.float64))
            self.assertEqual(checked.call_count, 4)
            for call in checked.call_args_list:
                self.assertEqual(call.args[0].shape, (1, 3, 3))
                self.assertTrue(all(torch.isfinite(v).all() for v in call.args))
        self.assertTrue(torch.isfinite(result).all() and torch.isfinite(error).all())
        torch.testing.assert_close(result[0], torch.zeros(6, 12, dtype=torch.float64))
        snapshot['reset_body_snapshot'][:] = True
        with patch('torch.linalg.solve', side_effect=AssertionError('reset solve')):
            torch.testing.assert_close(_wrist_position_jacobian(snapshot, wrist, com, cache), torch.zeros_like(result))

    def test_actual_candidate_reverses_overshoot_and_settles_without_accumulating(self):
        base = torch.zeros(1,12,dtype=torch.float64)
        actual = base.clone(); correction = base.clone(); correction[0,0] = .1
        previous = correction.clone()
        jacobian = torch.zeros(1,6,12,dtype=torch.float64); jacobian[:,:,:6] = torch.eye(6,dtype=torch.float64)
        error = torch.zeros(1,6,dtype=torch.float64); error[0,0] = .02
        active = torch.tensor([True]); lower = base.new_full((12,),-2.); upper = -lower; rate = upper*1.5
        inputs = (base,correction,previous,actual,jacobian,error,active,lower,upper,rate)
        saved = [value.clone() for value in inputs]
        requested, memory, delta, candidate = bounded_wrist_target(*inputs)
        self.assertAlmostEqual(float(delta[0,0]),-WRIST_CONTROL['correction_step_rad'])
        self.assertLess(float(requested[0,0]),float(previous[0,0]))
        for value, original in zip(inputs,saved):
            torch.testing.assert_close(value,original)
        for _ in range(40):
            requested, memory, delta, candidate = bounded_wrist_target(base,memory,requested,actual,jacobian,error,
                active,lower,upper,rate)
        expected = error[0,0]/(1+WRIST_CONTROL['damping'])
        self.assertAlmostEqual(float(candidate[0,0]),float(expected),places=14)
        self.assertAlmostEqual(float(requested[0,0]),float(expected),places=14)
        torch.testing.assert_close(delta,torch.zeros_like(delta),atol=1e-14,rtol=0)
        torch.testing.assert_close(memory,requested-base)

    def test_zero_pose_error_moves_lagging_request_toward_actual_and_holds_if_equal(self):
        base = torch.full((2,12),.3,dtype=torch.float64)
        memory = torch.full_like(base,.2); previous = base+memory
        actual = previous.clone(); actual[0] = .4
        jacobian = torch.zeros(2,6,12,dtype=torch.float64)
        error = torch.zeros(2,6,dtype=torch.float64)
        requested, _, delta, candidate = bounded_wrist_target(base,memory,previous,actual,jacobian,error,
            torch.tensor([True,True]),base.new_full((12,),-2.),base.new_full((12,),2.),base.new_full((12,),3.))
        torch.testing.assert_close(delta[0],base.new_full((12,),-WRIST_CONTROL['correction_step_rad']))
        torch.testing.assert_close(requested[1],previous[1])
        torch.testing.assert_close(delta[1],torch.zeros(12,dtype=torch.float64))
        torch.testing.assert_close(candidate,actual)

    def test_inactive_nan_preserves_feedforward_and_existing_rate_and_bounds(self):
        base = torch.zeros(2,12,dtype=torch.float64); base[0] = .04
        memory = torch.zeros_like(base); memory[1,1] = .002
        previous = memory.clone(); actual = torch.zeros_like(base); actual[0] = float('nan')
        jacobian = torch.zeros(2,6,12,dtype=torch.float64)
        jacobian[0] = float('nan'); jacobian[1,:,:6] = torch.eye(6,dtype=torch.float64)
        error = torch.ones(2,6,dtype=torch.float64); error[0] = float('nan')
        lower = base.new_full((12,),-1.); upper = -lower; upper[0] = .003
        rate = base.new_full((12,),3.); rate[1] = .006
        inputs = (base,memory,previous,actual,jacobian,error,torch.tensor([False,True]),lower,upper,rate)
        saved = [value.clone() for value in inputs]
        requested, correction, delta, candidate = bounded_wrist_target(*inputs)
        self.assertTrue(torch.isfinite(requested).all())
        torch.testing.assert_close(delta[0],torch.zeros(12,dtype=torch.float64))
        torch.testing.assert_close(candidate[0],base[0]+memory[0])
        self.assertTrue(torch.isfinite(candidate).all())
        torch.testing.assert_close(requested[0,2:],base[0,2:])
        self.assertGreater(float(requested[0,2]),WRIST_CONTROL['correction_step_rad'])
        self.assertAlmostEqual(float(requested[1,0]),.003)
        self.assertAlmostEqual(float(requested[1,1]),.0021)
        self.assertTrue(((requested >= lower) & (requested <= upper)).all())
        self.assertTrue(((requested-previous).abs() <= rate/60+1e-14).all())
        self.assertLessEqual(float(delta.abs().max()),WRIST_CONTROL['correction_step_rad'])
        torch.testing.assert_close(correction,requested-base)
        for value, original in zip(inputs,saved):
            torch.testing.assert_close(value,original,equal_nan=True)


if __name__ == '__main__':
    unittest.main()
