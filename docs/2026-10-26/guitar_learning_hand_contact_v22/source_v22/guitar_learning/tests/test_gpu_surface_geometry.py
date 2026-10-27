"""CPU checks for designated real-surface geometry, without a simulator."""
import unittest

import torch

from guitar_learning.gpu.geometry import surface_target_geometry


class SurfaceTargetGeometryTests(unittest.TestCase):
    def fixture(self, count=1, fingers=(1,), strings=None, samples=3):
        dtype = torch.float64
        if strings is None:
            strings = tuple(0 for _ in fingers)
        points = torch.full((count, 10, samples, 3), 100., dtype=dtype)
        velocity = torch.zeros_like(points)
        valid = torch.ones((10, samples), dtype=torch.bool)
        starts = torch.zeros((count, 6, 3), dtype=dtype)
        starts[:, :, 0] = torch.arange(6, dtype=dtype)*.1
        ends = starts.clone()
        ends[:, :, 1] = 1.
        low = torch.full((count, len(fingers)), .3, dtype=dtype)
        high = torch.full_like(low, .7)
        return [points, velocity, valid, starts, ends, low, high,
                torch.tensor(strings), torch.tensor(fingers)]

    def test_rows_all_fingers_and_flat_sample_indices(self):
        args = self.fixture(2, (1, 2, 3, 4), (0, 1, 2, 3))
        for row in range(2):
            for finger in range(1, 5):
                args[0][row, 2*finger, 0] = torch.tensor(
                    [(finger-1)*.1, .5, .01*(finger+row)])
        args[0][1, 3, 2] = torch.tensor([0., .5, .001])
        delta, velocity, distance, index = surface_target_geometry(*args)
        expected = torch.tensor([[.01, .02, .03, .04], [.001, .03, .04, .05]],
                                dtype=torch.float64)
        torch.testing.assert_close(distance, expected)
        torch.testing.assert_close(delta[..., :2], torch.zeros_like(delta[..., :2]))
        torch.testing.assert_close(delta[..., 2], -expected)
        torch.testing.assert_close(velocity, torch.zeros_like(velocity))
        self.assertEqual(index.tolist(), [[6, 12, 18, 24], [11, 12, 18, 24]])

    def test_other_finger_and_invalid_padding_do_not_win(self):
        args = self.fixture(fingers=(2,))
        args[0][:, 2, 0] = torch.tensor([0., .5, 0.])  # Wrong finger, exact contact.
        args[0][:, 4, 0] = torch.tensor([0., .5, .02])
        args[0][:, 5, 0] = torch.tensor([0., .5, 0.])
        args[2][5, 0] = False
        args[0][:, 5, 1] = torch.nan  # Invalid padding need not have a position.
        args[2][5, 1] = False
        delta, _, distance, index = surface_target_geometry(*args)
        torch.testing.assert_close(distance, torch.tensor([[.02]], dtype=torch.float64))
        self.assertTrue(torch.isfinite(delta).all())
        self.assertEqual(index.item(), 12)

    def test_finite_string_intersection_and_slanted_3d_projection(self):
        args = self.fixture(fingers=(1, 1, 1), strings=(0, 1, 2))
        args[3][0, 1] = torch.tensor([0., 0., 0.])
        args[4][0, 1] = torch.tensor([1., 1., 0.])
        args[3][0, 2] = torch.tensor([0., 1., 0.])  # Reverse fret direction.
        args[4][0, 2] = torch.tensor([0., 0., 0.])
        args[0][0, 2, 0] = torch.tensor([0., 2., 0.])
        args[5][:] = torch.tensor([[-1., .2, .2]])
        args[6][:] = torch.tensor([[2., .8, .8]])
        delta, _, _, _ = surface_target_geometry(*args, margin=0.)
        # Target 0 clips at the finite string end, not y=2 of its wide cell.
        torch.testing.assert_close(delta[0, 0], torch.tensor([0., -1., 0.], dtype=torch.float64))
        # On slanted target 1, projection is t=1 then clipped to cell upper=.8.
        torch.testing.assert_close(delta[0, 1], torch.tensor([.8, -1.2, 0.], dtype=torch.float64))
        torch.testing.assert_close(delta[0, 2], torch.tensor([0., -1.2, 0.], dtype=torch.float64))

    def test_cell_margin_and_exact_tie_choose_first_flat_index(self):
        args = self.fixture()
        args[0][0, 2, 0] = torch.tensor([0., .701, .01])
        args[0][0, 3, 1] = args[0][0, 2, 0]
        delta, _, distance, index = surface_target_geometry(*args)
        torch.testing.assert_close(delta, torch.tensor([[[0., 0., -.01]]], dtype=torch.float64))
        torch.testing.assert_close(distance, torch.tensor([[.01]], dtype=torch.float64))
        self.assertEqual(index.item(), 6)

    def test_actual_velocity_not_argmin_switch_difference(self):
        args = self.fixture()
        args[0][0, 2, 0] = torch.tensor([0., .4, .01])
        args[0][0, 3, 0] = torch.tensor([0., .6, .02])
        args[1][0, 2, 0] = torch.tensor([.1, -.2, .3])
        args[1][0, 3, 0] = args[1][0, 2, 0]
        first = surface_target_geometry(*args)
        args[0][0, 2, 0, 2] = .03
        second = surface_target_geometry(*args)
        self.assertEqual(first[3].item(), 6)
        self.assertEqual(second[3].item(), 9)
        torch.testing.assert_close(first[1], second[1])
        torch.testing.assert_close(second[1], torch.tensor([[[-.1, .2, -.3]]], dtype=torch.float64))

    def test_rigid_frame_change_preserving_fret_y_axis(self):
        args = self.fixture()
        args[0][0, 2, 0] = torch.tensor([.02, .5, .03])
        args[1][0, 2, 0] = torch.tensor([.1, .2, .3])
        before = surface_target_geometry(*args)
        rotation = torch.tensor([[0., 0., 1.], [0., 1., 0.], [-1., 0., 0.]], dtype=torch.float64)
        shift = torch.tensor([1., .4, -2.], dtype=torch.float64)
        args[0] = args[0]@rotation.T+shift
        args[1] = args[1]@rotation.T
        args[3] = args[3]@rotation.T+shift
        args[4] = args[4]@rotation.T+shift
        args[5] += shift[1]
        args[6] += shift[1]
        after = surface_target_geometry(*args)
        torch.testing.assert_close(after[0], before[0]@rotation.T)
        torch.testing.assert_close(after[1], before[1]@rotation.T)
        torch.testing.assert_close(after[2], before[2])
        torch.testing.assert_close(after[3], before[3])

    def test_empty_designated_surface_and_disjoint_cell_rejected(self):
        args = self.fixture()
        args[2][2:4] = False
        with self.assertRaisesRegex(RuntimeError, 'no valid surface'):
            surface_target_geometry(*args)
        args[2][:] = True
        args[5][:], args[6][:] = 2., 3.
        with self.assertRaisesRegex(RuntimeError, 'intersect'):
            surface_target_geometry(*args)


if __name__ == '__main__':
    unittest.main()
