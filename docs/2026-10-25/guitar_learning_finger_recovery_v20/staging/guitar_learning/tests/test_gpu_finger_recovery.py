"""CPU analytic contracts for B recovery and optional tracking shape rates."""
import copy
import math
import unittest

import torch

from guitar_learning.gpu.finger_reward import (
    B_PREPARATION_ANGLES_DEGREES, FINGER_PREPARATION_CONTRACT,
    FINGER_SHAPE_CONTRACT, finger_preparation_gate, finger_preparation_reward,
    finger_recovery_config, finger_shape_reward, finger_target_indices)


def inputs(times=(0.,)):
    n = len(times)
    angles = torch.tensor(B_PREPARATION_ANGLES_DEGREES, dtype=torch.float64)
    return dict(now=torch.tensor(times, dtype=torch.float64),
        onset=torch.tensor([4.], dtype=torch.float64), end=torch.tensor([5.], dtype=torch.float64),
        press=torch.tensor([3.], dtype=torch.float64), finger=torch.tensor([1]),
        palm_quaternion=torch.tensor([0., 0., 0., 1.], dtype=torch.float64).expand(n, -1).clone(),
        segment_quaternion=segments(angles).expand(n, -1, -1, -1).clone(),
        contact=torch.zeros(n, 4, dtype=torch.bool),
        distance=torch.ones(n, 1, dtype=torch.float64))


def segments(degrees):
    """Independent x-axis forward kinematics for actual geometric flexion."""
    half = degrees.cumsum(-1)*math.pi/360.
    q = torch.zeros(*half.shape, 4, dtype=degrees.dtype)
    q[..., 0] = half.sin()
    q[..., 3] = half.cos()
    return q


def gate_data(data):
    return {k:data[k] for k in ('now', 'onset', 'end', 'press', 'finger', 'contact', 'distance')}


class FingerRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def test_config_exact_keys_and_supported_experiments(self):
        expected = dict(schema='guitar_learning.left_finger_recovery.v1',
                        standby_rate_per_s=.02, shape_rate_per_s=0.)
        self.assertEqual(finger_recovery_config(), expected)
        for standby in (.02, .04):
            for shape in (0., .004):
                value = dict(expected, standby_rate_per_s=standby, shape_rate_per_s=shape)
                before = value.copy()
                self.assertEqual(finger_recovery_config(value), value)
                self.assertEqual(value, before)
        for bad in (True, False, float('nan'), float('inf'), -.02, .01, '.02', None):
            for key in ('standby_rate_per_s', 'shape_rate_per_s'):
                with self.assertRaises(ValueError):
                    finger_recovery_config(dict(expected, **{key:bad}))
        for bad in ({}, dict(expected, extra=1), dict(expected, schema='old'), []):
            with self.assertRaises(ValueError):
                finger_recovery_config(bad)
        config = finger_recovery_config(); config['standby_rate_per_s'] = 100
        self.assertEqual(finger_recovery_config(), expected)

    def test_B_inside_band_flat_outside_monotone_inverse_quadratic(self):
        observed = []
        for offset in (0., 10., 15., 20., 30., 45., 60.):
            data = inputs()
            degrees = torch.tensor(B_PREPARATION_ANGLES_DEGREES, dtype=torch.float64)+offset
            data['segment_quaternion'] = segments(degrees)[None]
            result = finger_preparation_reward(**data)
            q = 1/(1+3*(max(offset-15., 0.)/30.)**2)
            self.assertAlmostEqual(float(result['rate']), .02*q, places=14)
            torch.testing.assert_close(result['per_finger_rate'], torch.full((1, 4), .005*q, dtype=torch.float64))
            observed.append(float(result['rate']))
        self.assertAlmostEqual(observed[0], observed[2], places=14)
        self.assertTrue(all(a>b for a,b in zip(observed[2:], observed[3:])))
        self.assertEqual(FINGER_PREPARATION_CONTRACT['schema'], 'guitar_learning.gpu_finger_preparation_rate.v4')

    def test_B_large_error_has_nonvanishing_tail_and_actual_rate_breakdown(self):
        data = inputs(); data['segment_quaternion'] = segments(torch.tensor([[0., 0., 90.]]*4, dtype=torch.float64))[None]
        result = finger_preparation_reward(**data)
        ref = B_PREPARATION_ANGLES_DEGREES[0]
        s = sum((max(abs(a-b)-15., 0.)/30.)**2 for a,b in zip((0.,0.,90.),ref))
        self.assertAlmostEqual(float(result['quality'][0, 0]), 1/(1+s), places=14)
        self.assertGreater(float(result['quality'][0, 0]), math.exp(-s))
        self.assertFalse(result['band_inside'].any())
        torch.testing.assert_close(result['rate'], result['per_finger_rate'].sum(-1), rtol=0, atol=0)
        stronger = finger_preparation_reward(**data, rate_per_s=.04)
        torch.testing.assert_close(stronger['per_finger_rate'], 2*result['per_finger_rate'], rtol=0, atol=0)

    def test_gate_preserves_boundaries_fades_and_independence(self):
        data = inputs((2.5, 2.575, 2.65, 5., 5.075, 5.15))
        measured = finger_preparation_reward(**data)
        gate = finger_preparation_gate(**gate_data(data))
        torch.testing.assert_close(gate['gate'][:,0], torch.tensor([1.,.5,0.,0.,.5,1.], dtype=torch.float64))
        self.assertTrue((gate['gate'][:,1:] == 1).all())
        for key in gate:
            torch.testing.assert_close(gate[key], measured[key], rtol=0, atol=0)
        self.assertTrue(measured['band_inside'].all())
        torch.testing.assert_close(measured['per_finger_rate'][:,1:], torch.full((6,3), .005, dtype=torch.float64))

    def test_gate_stale_future_contact_and_nan_are_ignored_only_outside_relevance(self):
        data = inputs((.999, 1., 2., 5., 5.001))
        data['contact'][:] = True; data['distance'][:] = float('nan')
        result = finger_preparation_gate(**gate_data(data))
        self.assertEqual(result['relevant_targets'][:,0].tolist(), [False, True, True, True, False])
        self.assertEqual(result['nonfinite_veto'][:,0].tolist(), [False, True, True, True, False])
        self.assertEqual(result['contact_veto'][:,0].tolist(), [False, True, True, True, False])
        self.assertFalse(result['nonfinite_veto'][:,1:].any())
        self.assertTrue((result['gate'][:,1:] == 1).all())
        torch.testing.assert_close(result['gate'][:,0], torch.tensor([1.,0.,0.,0.,.001/.15],dtype=torch.float64))

    def test_gate_inclusive_near_distance_overlaps_and_absent_fingers(self):
        data = inputs((2.,)*4)
        data['distance'][:,0] = torch.tensor([.04,.040001,float('inf'),1.])
        self.assertEqual(finger_preparation_gate(**gate_data(data))['gate'][:,0].tolist(), [0.,1.,0.,1.])
        data.update(onset=torch.tensor([4.,4.]), end=torch.tensor([5.,6.]),
            press=torch.tensor([3.,3.]), finger=torch.tensor([1,1]), distance=torch.ones(4,2))
        self.assertTrue((finger_preparation_gate(**gate_data(data))['gate'] == 1).all())
        data['now'][:] = 3.
        self.assertEqual(finger_preparation_gate(**gate_data(data))['gate'].tolist(), [[0.,1.,1.,1.]]*4)

    def test_empty_score_invalid_angle_and_input_purity(self):
        data = inputs(); saved = copy.deepcopy(data)
        finger_preparation_reward(**data)
        for key in data:
            torch.testing.assert_close(data[key], saved[key], rtol=0, atol=0)
        for invalid in (0., float('nan')):
            bad = copy.deepcopy(data); bad['segment_quaternion'][:,0] = invalid
            result = finger_preparation_reward(**bad)
            self.assertFalse(result['valid'][:,0].all())
            self.assertFalse(result['band_inside'][:,0].any())
            self.assertEqual(float(result['per_finger_rate'][0,0]),0.)
            self.assertAlmostEqual(float(result['rate']), .015, places=14)
        for key in ('onset','end','press','finger'): data[key] = data[key][:0]
        data['distance'] = data['distance'][:,:0]
        result = finger_preparation_reward(**data)
        self.assertEqual(float(result['rate']),0.)
        self.assertFalse(result['gate'].any())

    def test_gate_and_preparation_reject_misaligned_inputs_and_rates(self):
        for key,bad in (('now',torch.zeros(1,1)),('finger',torch.ones(1)),
                        ('contact',torch.zeros(1,4)),('distance',torch.ones(1,2))):
            data = inputs(); data[key] = bad
            with self.assertRaises(ValueError):
                finger_preparation_gate(**gate_data(data))
        for bad in (True, float('nan'), 0., .03):
            with self.assertRaises(ValueError):
                finger_preparation_reward(**inputs(),rate_per_s=bad)


class FingerShapeTests(unittest.TestCase):
    def shape_data(self, times=(1.,)):
        data = inputs(times)
        for key in ('palm_quaternion','segment_quaternion','contact','distance'): data.pop(key)
        data.update(angles=torch.zeros(len(times),4,3,dtype=torch.float64),
                    valid=torch.ones(len(times),4,3,dtype=torch.bool))
        return data

    def test_shape_disabled_by_default_and_one_finger_fixed_denominator(self):
        data = self.shape_data()
        self.assertEqual(float(finger_shape_reward(**data)['rate']),0.)
        enabled = finger_shape_reward(**data,rate_per_s=.004)
        self.assertAlmostEqual(float(enabled['rate']),.001,places=14)
        self.assertEqual(enabled['active'].tolist(),[[True,False,False,False]])
        self.assertEqual(FINGER_SHAPE_CONTRACT['default_rate_per_s'],0.)

    def test_shape_flat_band_scalar_formula_and_MCP_independence(self):
        data = self.shape_data()
        for pip,dip in ((0.,0.), (0.,50.), (30.,80.), (0.,90.), (20.,90.)):
            data['angles'][...,1] = math.radians(pip); data['angles'][...,2] = math.radians(dip)
            q = 1/(1+(max(dip-pip-50.,0.)/30.)**2)
            first = finger_shape_reward(**data,rate_per_s=.004)
            self.assertAlmostEqual(float(first['rate']),.001*q,places=14)
            for mcp in (-90.,0.,90.):
                data['angles'][...,0] = math.radians(mcp)
                second = finger_shape_reward(**data,rate_per_s=.004)
                torch.testing.assert_close(first['rate'],second['rate'],rtol=0,atol=0)

    def test_shape_selector_boundaries_no_double_credit_and_inputs_unchanged(self):
        data = self.shape_data((.999,1.,4.,5.))
        expected = finger_target_indices(**{k:data[k] for k in ('now','onset','end','press','finger')})
        saved=copy.deepcopy(data)
        result = finger_shape_reward(**data,rate_per_s=.004)
        torch.testing.assert_close(result['active'],expected['valid'][...,0],rtol=0,atol=0)
        self.assertEqual(result['active'][:,0].tolist(),[False,True,True,False])
        for key in data: torch.testing.assert_close(data[key],saved[key],rtol=0,atol=0)
        data.update(onset=torch.tensor([4.,4.]),end=torch.tensor([5.,5.]),press=torch.tensor([3.,3.]),finger=torch.tensor([1,1]))
        torch.testing.assert_close(result['rate'],finger_shape_reward(**data,rate_per_s=.004)['rate'])

    def test_shape_all_four_max_invalid_nonfinite_and_empty_score(self):
        data=self.shape_data()
        for key in ('onset','end','press'): data[key]=data[key].expand(4)
        data['finger']=torch.arange(1,5)
        result=finger_shape_reward(**data,rate_per_s=.004)
        self.assertAlmostEqual(float(result['rate']),.004,places=14)
        data['valid'][:,0,0]=False
        data['angles'][:,1,1]=float('nan')
        result=finger_shape_reward(**data,rate_per_s=.004)
        self.assertTrue(torch.isfinite(result['rate']).all())
        self.assertEqual(result['per_finger_rate'].tolist(),[[0.,0.,.001,.001]])
        for key in ('onset','end','press','finger'):data[key]=data[key][:0]
        self.assertEqual(float(finger_shape_reward(**data,rate_per_s=.004)['rate']),0.)

    def test_shape_bad_inputs_and_unsupported_rates(self):
        for key,bad in (('angles',torch.zeros(1,4,2)),('valid',torch.ones(1,4,3))):
            data=self.shape_data();data[key]=bad
            with self.assertRaises(ValueError):finger_shape_reward(**data)
        for bad in (True,float('inf'),.001):
            with self.assertRaises(ValueError):finger_shape_reward(**self.shape_data(),rate_per_s=bad)


if __name__ == '__main__':
    unittest.main()
