"""CPU contracts; native ownership is separately checked against PhysX readback."""
import unittest
import numpy as np
from ..environment_contract_v1 import EnvironmentContract
from .environment_v2 import POSE_CONFIG, action_groups, action_targets


class ActionOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.contract = EnvironmentContract(POSE_CONFIG)
        self.groups = action_groups(self.contract.names)
        self.indices = np.concatenate(self.groups)
        q = self.contract.q_ref[self.indices]
        self.lower = np.maximum(self.contract.lower[self.indices],q-.035)
        self.upper = np.minimum(self.contract.upper[self.indices],q+.035)

    def test_partition_and_neutral(self):
        self.assertEqual([len(g) for g in self.groups],[15,33,6])
        self.assertEqual(len(set(self.indices)),54)
        result = action_targets(np.zeros(54),self.contract.q_ref,self.indices,self.lower,self.upper)
        np.testing.assert_array_equal(result,self.contract.q_ref)

    def test_endpoints_keep_other27_and_move_each_owned_channel(self):
        for sign,bound in [(-1,self.lower),(1,self.upper)]:
            result = action_targets(np.full(54,sign),self.contract.q_ref,self.indices,self.lower,self.upper)
            np.testing.assert_allclose(result[self.indices],bound,atol=1e-15)
            others = np.setdiff1d(np.arange(81),self.indices)
            np.testing.assert_array_equal(result[others],self.contract.q_ref[others])
            self.assertTrue(np.all(result[self.indices]!=self.contract.q_ref[self.indices]))

    def test_invalid_action_rejected(self):
        for action in [np.zeros(53),np.full(54,np.nan),np.full(54,np.inf),np.full(54,1.001)]:
            with self.assertRaises(ValueError):
                action_targets(action,self.contract.q_ref,self.indices,self.lower,self.upper)


if __name__=='__main__': unittest.main()
