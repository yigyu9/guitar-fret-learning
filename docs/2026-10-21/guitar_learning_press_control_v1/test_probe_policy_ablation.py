"""CPU mask/capture checks; no final checkpoint load or native execution."""
import ast
from pathlib import Path
import sys
import unittest

import numpy as np

PHASE = Path(__file__).resolve().parent
sys.path.insert(0, str(PHASE))
import probe_policy_ablation as probe


class PolicyAblationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Read the frozen source contract; no policy/native modules imported.
        import json
        cls.control = json.loads((PHASE/'contact_probe_n4/training_contract.json').read_text())['native_backend']['control']
        cls.order = cls.control['action_order']

    def fixture(self, index):
        n = 4
        arrays = dict(body_state=np.zeros((n,106,13)),q=np.zeros((n,105)),qd=np.zeros((n,105)),
            target=np.repeat(np.array(self.control['reference105_rad'])[None],n,axis=0),
            raw_action=np.zeros((n,39)),applied_action=np.zeros((n,39)),
            state=np.zeros((n,512)),policy_input_state=np.zeros((n,512)),
            clock=np.arange(n)*4,global_physics_step=np.arange(n)*4)
        arrays['body_state'][...,6] = 1
        arrays['raw_action'][1:] = np.arange(39)/50-.3
        mask = probe.action_masks(self.order)[index]
        arrays['applied_action'] = arrays['raw_action']*mask
        return arrays,mask,dict(steps=3)

    def test_masks_use_named_groups_and_keep_each_rows_own_actions(self):
        mask = probe.action_masks(self.order)
        hand = [i for i,n in enumerate(self.order) if n.startswith('LH:')]
        arm = [i for i,n in enumerate(self.order) if n.startswith('L_')]
        right = [i for i,n in enumerate(self.order) if n.startswith('R_')]
        self.assertEqual((len(hand),len(arm),len(right)),(21,12,6))
        raw = np.arange(156,dtype=np.float32).reshape(4,39)/200
        applied = raw*mask
        np.testing.assert_array_equal(applied[0],raw[0])
        np.testing.assert_array_equal(applied[1,arm+right],raw[1,arm+right])
        np.testing.assert_array_equal(applied[2,hand+right],raw[2,hand+right])
        self.assertTrue((applied[1,hand]==0).all() and (applied[2,arm]==0).all() and (applied[3]==0).all())
        reverse=list(reversed(self.order)); revmask=probe.action_masks(reverse)
        np.testing.assert_array_equal(revmask[:,::-1],mask)
        with self.assertRaises(ValueError):probe.action_masks(self.order[:-1])

    def test_all_4_cases_keep_exact_actions_reference_holds_and_left21_metrics(self):
        for index in range(4):
            arrays,mask,episode=self.fixture(index)
            proof=probe.audit_trace(arrays,mask,episode,self.control)
            self.assertEqual(len(proof['actual_left21_range_rad']),21)
            self.assertEqual(len(proof['target_left21_range_rad']),21)
            self.assertEqual(proof['control_steps'],3)
            self.assertEqual(proof['zeroed_channel_target_reference_max_error_rad'],None if index==0 else 0)

    def test_mask_changed_command_clock_nonfinite_and_reset_frame_rejected(self):
        for key,location,value in (('applied_action',(1,12),.3),('clock',1,8),
                ('q',(1,0),np.nan),('raw_action',(0,0),.1),('global_physics_step',2,0)):
            arrays,mask,episode=self.fixture(1);arrays[key][location]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                probe.audit_trace(arrays,mask,episode,self.control)
        arrays,mask,episode=self.fixture(3)
        native=self.control['joint_names'].index(next(n for n in self.order if n.startswith('LH:')))
        arrays['target'][1,native]+=.01
        with self.assertRaisesRegex(ValueError,'hold prepared'):
            probe.audit_trace(arrays,mask,episode,self.control)

    def test_entrypoint_is_native_lazy_and_strict_restore_no_ppo_update(self):
        self.assertNotIn('isaacgym',sys.modules)
        self.assertNotIn('torch',sys.modules)
        self.assertNotIn('mujoco',sys.modules)
        tree=ast.parse((PHASE/'probe_policy_ablation.py').read_text(),feature_version=(3,8))
        calls=[n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)]
        self.assertIn('load',calls);self.assertIn('restore',calls);self.assertIn('eval',calls)
        learning_calls=[n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call) and
            isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and
            n.func.value.id in ('trainer','coordinator')]
        self.assertNotIn('update',learning_calls);self.assertNotIn('advance',learning_calls)
        self.assertIn('no_grad',calls)


if __name__=='__main__':unittest.main(verbosity=2)
