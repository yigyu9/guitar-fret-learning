"""Pure CPU regression checks of diagnostic requests, no native scene."""
import unittest
import torch

from guitar_learning.tool.validation import thumb_contact_probe as probe


class ThumbDiagnosticTests(unittest.TestCase):
    def test_contact_gap_search_is_small_monotone_and_bounded(self):
        gaps = [probe.approach_gap(t) for t in (0., 1., 1.5, 3., 4.5, 15.)]
        for actual, expected in zip(gaps, [0., 0., -.0001, -.0002, -.0003, -.0003]):
            self.assertAlmostEqual(actual, expected, places=12)

    def test_point_jacobian_offset_uses_omega_cross_r_sign_and_meters(self):
        native = torch.zeros(1, 6, 1)
        native[0, 5, 0] = 1.
        point = probe.point_jacobian(native, torch.tensor([[.01, 0., 0.]]))
        torch.testing.assert_close(point[0, :, 0], torch.tensor([0., .01, 0.]))

    def test_codec_zero_hold_and_bounded_increment(self):
        current = torch.tensor([[.1, -.2, .3, .4, .5]])
        torch.testing.assert_close(probe.incremental_request(current, current), torch.zeros_like(current))
        desired = current+torch.tensor([[1., -1., .01, -.01, 0.]])
        request = probe.incremental_request(current, desired)
        self.assertTrue((request.abs() <= 1).all())
        torch.testing.assert_close(request[0, :2], torch.tensor([1., -1.]))
        torch.testing.assert_close((current+request*4/60)[0, 2:], desired[0, 2:])

    def test_damped_adjustment_moves_in_requested_direction_without_state_change(self):
        jacobian = torch.zeros(1, 3, 5, dtype=torch.float64)
        jacobian[0, :3, :3] = torch.eye(3, dtype=torch.float64)*.04
        error = torch.tensor([[.001, -.001, 0.]], dtype=torch.float64)
        current = torch.zeros(1, 5, dtype=torch.float64)
        original = current.clone()
        value = probe.bounded_point_adjustment(jacobian, error, current, current,
                                               current[0]-1, current[0]+1)
        self.assertGreater(value[0, 0].item(), 0)
        self.assertLess(value[0, 1].item(), 0)
        self.assertLessEqual(value.abs().max().item(), .008726647)
        torch.testing.assert_close(current, original)

    def test_native_and_diagnostic_excursion_bounds_hold_with_singular_jacobian(self):
        reference = torch.zeros(1, 5)
        current = torch.full_like(reference, .261799388)
        jacobian = torch.ones(1, 3, 5)*.01
        desired = probe.bounded_point_adjustment(jacobian, torch.ones(1, 3), current,
            reference, torch.full((5,), -.2), torch.full((5,), .2))
        self.assertTrue(torch.isfinite(desired).all())
        self.assertTrue((desired <= .2).all())
        self.assertTrue((desired >= -.2).all())
        zero = probe.bounded_point_adjustment(torch.zeros_like(jacobian), torch.ones(1, 3),
            reference, reference, torch.full((5,), -.2), torch.full((5,), .2))
        torch.testing.assert_close(zero, reference)


if __name__ == '__main__':
    unittest.main()
