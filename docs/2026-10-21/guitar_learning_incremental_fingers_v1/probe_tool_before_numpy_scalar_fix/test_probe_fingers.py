"""CPU recurrence/coverage tests; never construct native GPU scenes."""
import copy
import importlib.util
from pathlib import Path
import unittest

import numpy as np

spec = importlib.util.spec_from_file_location('probe_fingers',Path(__file__).with_name('probe_fingers.py'))
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def fixture(amplitude=.2,frames=71):
    names = ['LH:axis%d'%i for i in range(21)]+['other%d'%i for i in range(84)]
    order = names[:21]+names[21:39]
    contract = dict(schema='guitar_learning.gpu_finite_control.v3',joint_names=names,action_order=order,
        physics_hz=240,position_indices=list(range(48)),rate_rad_s=[4.]*105,smoothing_alpha=[1.]*39,
        reference105_rad=[0.]*105,action_lower_rad=[-.1]*39,action_upper_rad=[.15]*39,
        action_codec=dict(schema='guitar_learning.gpu_left_incremental_fingers.v1',velocity_scale_rad_s=4.,
            control_hz=60,incremental_joint_names=names[:21],incremental_action_indices=list(range(21))))
    arrays = dict(q=np.zeros((frames,105)),qd=np.zeros((frames,105)),target=np.zeros((frames,105)),
        body_state=np.zeros((frames,106,13)),action=np.zeros((frames,39)),clock=np.arange(frames)*4,
        global_physics_step=np.arange(frames)*4+280)
    arrays['body_state'][...,6] = 1.
    for t in range(1,frames):
        arrays['action'][t,0] = probe.command_at(t-1,amplitude)
        arrays['target'][t] = arrays['target'][t-1]
        arrays['target'][t,0] = np.clip(arrays['target'][t-1,0]+arrays['action'][t,0]*4/60,-.1,.15)
        arrays['q'][t] = arrays['target'][t]*.8
    return contract,arrays


class ProbeTests(unittest.TestCase):
    def test_four_sign_size_cases_covered_for_each_batch_size(self):
        for n in range(1,9):
            batches = probe.command_batches(n)
            self.assertTrue(all(len(v)==n for v in batches))
            self.assertEqual(set(x for row in batches for x in row),set(probe.AMPLITUDES))
        for n in (0,9,True):
            with self.assertRaises(ValueError): probe.command_batches(n)

    def test_both_signs_clamp_hold_reverse_and_real_q_are_distinct(self):
        for value in probe.AMPLITUDES:
            contract,arrays = fixture(value)
            row = probe.audit_trace(arrays,contract,'LH:axis0',value)
            self.assertTrue(row['complete_schedule'])
            self.assertTrue(row['no_windup_observed'])
            self.assertEqual(row['target_hold_delta_rad'],0.)
            self.assertTrue(row['first_reverse_target_delta_rad']*value<0)
            self.assertTrue(row['actual_motion_observed'])
            self.assertGreater(row['endpoint_tracking_rms_rad'],0.)

    def test_no_saturation_and_aborted_trace_do_not_claim_no_windup(self):
        contract,arrays = fixture(frames=21)
        row = probe.audit_trace(arrays,contract,'LH:axis0',.2)
        self.assertFalse(row['complete_schedule'])
        self.assertFalse(row['no_windup_observed'])
        self.assertIsNone(row['first_reverse_target_delta_rad'])
        contract,arrays = fixture()
        contract['action_upper_rad']=[10.]*39
        contract['action_lower_rad']=[-10.]*39
        for t in range(1,71):
            arrays['target'][t,0]=arrays['target'][t-1,0]+arrays['action'][t,0]*4/60
        self.assertFalse(probe.audit_trace(arrays,contract,'LH:axis0',.2)['no_windup_observed'])

    def test_old_absolute_zero_recentering_and_hidden_windup_are_rejected(self):
        for tick in (31,41):
            contract,arrays=fixture()
            arrays['target'][tick,0]+=.01
            with self.assertRaisesRegex(ValueError,'recurrence'):
                probe.audit_trace(arrays,contract,'LH:axis0',.2)

    def test_mapping_clock_finiteness_and_uncommanded_axis_are_checked(self):
        contract,arrays=fixture()
        wrong=copy.deepcopy(contract)
        wrong['action_codec']['incremental_action_indices'][0]=1
        with self.assertRaises(ValueError):probe.mapping(wrong)
        for key,index,value in (('clock',1,5),('global_physics_step',1,999),('q',(1,0),np.nan),
                                ('target',(5,1),.1),('action',(5,1),.1)):
            broken={k:v.copy() for k,v in arrays.items()}
            broken[key][index]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                probe.audit_trace(broken,contract,'LH:axis0',.2)


if __name__=='__main__':
    unittest.main()
