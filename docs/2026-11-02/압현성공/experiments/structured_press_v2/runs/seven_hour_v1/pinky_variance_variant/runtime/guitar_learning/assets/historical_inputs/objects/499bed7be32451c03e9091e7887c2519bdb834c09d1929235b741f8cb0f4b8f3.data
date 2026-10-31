"""Smoothing composes with the existing observed final-target/rate contract."""
import unittest
import numpy as np
from ..environment_contract_v1 import EnvironmentContract
from .environment_v5 import POSE_CONFIG,action_groups,action_targets,smooth_target


class SmoothedContractTests(unittest.TestCase):
    def test_neutral_is_exact_and_original_rate_cap_retained(self):
        contract = EnvironmentContract(POSE_CONFIG)
        previous = contract.q_ref.astype(np.float32)
        np.testing.assert_array_equal(smooth_target(contract.q_ref,previous,.2),contract.q_ref)
        indices = np.concatenate(action_groups(contract.names))
        lower = np.maximum(contract.lower[indices],contract.q_ref[indices]-.08)
        upper = np.minimum(contract.upper[indices],contract.q_ref[indices]+.08)
        # Respect the existing body effective limits in this isolated codec test.
        lower = np.maximum(lower,contract.effective_lower[indices])
        upper = np.minimum(upper,contract.effective_upper[indices])
        for sign in (-1,1):
            requested = action_targets(np.full(54,sign),contract.q_ref,indices,lower,upper)
            filtered = smooth_target(requested,previous,.2)
            native_action = np.clip((filtered-contract.mid)/contract.half,-1,1)
            _,final = contract.targets(native_action,previous)
            self.assertTrue(np.all(abs(final.astype(float)-previous)<=contract.rates/60+2e-7))
            others = np.setdiff1d(np.arange(81),indices)
            np.testing.assert_array_equal(final[others],previous[others])


if __name__=='__main__': unittest.main()
