"""공유 목표각 역변환의 직접 제어·경계·비유한 입력 계약을 검사한다."""
import unittest

import torch

from guitar_learning.tool.validation.press_acquisition import trajectory_actions


class PressAcquisitionTests(unittest.TestCase):
    def codec(self):
        low = torch.linspace(-2., -.5, 39, dtype=torch.float64)
        high = torch.linspace(.5, 3., 39, dtype=torch.float64)
        reference = low*.4+high*.6
        return reference, low, high

    def test_direct_inverse_matches_requested_angles_on_every_channel(self):
        ref, low, high = self.codec()
        desired = (low*.2+high*.8).expand(3, -1).clone()
        action = trajectory_actions(desired, ref, low, high)
        decoded = ref+torch.where(action >= 0, high-ref, ref-low)*action
        torch.testing.assert_close(decoded, desired, atol=1e-12, rtol=0)
        torch.testing.assert_close(trajectory_actions(ref[None], ref, low, high), torch.zeros_like(ref[None]))

    def test_direct_inverse_has_no_previous_target_dependency(self):
        ref, low, high = self.codec()
        for desired in (high[None], low[None], ref[None]):
            first = trajectory_actions(desired, ref, low, high)
            for _ in range(10):
                torch.testing.assert_close(trajectory_actions(desired, ref, low, high), first, atol=0, rtol=0)

    def test_codec_rejects_out_of_bounds_and_nonfinite_requests(self):
        ref, low, high = self.codec()
        desired = ref[None].clone(); desired[0, 0] = high[0]+.01
        with self.assertRaises(ValueError):
            trajectory_actions(desired, ref, low, high)
        desired = ref[None].clone(); desired[0, 0] = float('nan')
        with self.assertRaises(ValueError):
            trajectory_actions(desired, ref, low, high)


if __name__ == '__main__':
    unittest.main()
