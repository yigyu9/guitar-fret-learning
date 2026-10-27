import math
import unittest

import torch

from guitar_learning.gpu.finger_motion_attribution import decompose_pad_motion
from guitar_learning.gpu.geometry import apply, multiply


def pose(position=(0., 0., 0.), angle=0.):
    return torch.tensor([*position, 0., 0., math.sin(angle / 2), math.cos(angle / 2)],
                        dtype=torch.float64)


class FingerMotionAttributionTests(unittest.TestCase):
    def setUp(self):
        generator = torch.Generator().manual_seed(13)
        self.points = torch.randn(2, 4, 128, 3, generator=generator, dtype=torch.float64) * .02
        self.zero = pose().expand(2, 7)

    def test_finger_only_and_palm_only(self):
        changed = self.points + torch.tensor([.001, -.002, .003])
        result = decompose_pad_motion(self.points, changed, self.zero,
                                      self.zero, self.zero, self.zero)
        torch.testing.assert_close(result.support, torch.zeros_like(self.points))
        torch.testing.assert_close(result.finger, changed - self.points)
        moved = pose((.01, .02, -.03)).expand(2, 7)
        current = self.points + moved[:, None, None, :3]
        result = decompose_pad_motion(self.points, current, self.zero, moved, self.zero, self.zero)
        torch.testing.assert_close(result.finger, torch.zeros_like(self.points))
        torch.testing.assert_close(result.support, current - self.points)

    def test_guitar_motion_and_combined_vector_identity(self):
        new_palm = pose((.01, -.03, .02), .4).expand(2, 7)
        new_guitar = pose((-.02, .01, .03), -.2).expand(2, 7)
        carried = apply(new_palm[:, None, None, 3:], self.points) + new_palm[:, None, None, :3]
        changed = carried + torch.tensor([.001, -.002, .004])
        result = decompose_pad_motion(self.points, changed, self.zero, new_palm, self.zero, new_guitar)
        torch.testing.assert_close(result.support + result.finger, result.total)
        expected_finger = apply(pose(angle=.2)[3:], changed - carried)
        torch.testing.assert_close(result.finger, expected_finger)
        expected_total = apply(pose(angle=.2)[3:], changed - new_guitar[:, None, None, :3]) - self.points
        torch.testing.assert_close(result.total, expected_total)

    def test_common_rigid_world_motion_is_zero_in_guitar_coordinates(self):
        rigid = pose((.2, -.1, .05), .6).expand(2, 7)
        current = apply(rigid[:, None, None, 3:], self.points) + rigid[:, None, None, :3]
        result = decompose_pad_motion(self.points, current, self.zero, rigid, self.zero, rigid)
        for value in (result.total, result.support, result.finger):
            torch.testing.assert_close(value, torch.zeros_like(value), atol=1e-15, rtol=0)

    def test_fixed_sample_identity_not_nearest_point(self):
        current = self.points.clone()
        current[..., 0, :] += .01
        result = decompose_pad_motion(self.points, current, self.zero, self.zero, self.zero, self.zero)
        self.assertEqual(result.finger.shape, (2, 4, 128, 3))
        torch.testing.assert_close(result.finger[..., 1:, :], torch.zeros_like(result.finger[..., 1:, :]))
        self.assertTrue((result.finger[..., 0, :].abs() > 0).all())

    def test_nonidentity_previous_frames_and_common_world_transform(self):
        old_palm = pose((.1, -.2, .03), .7).expand(2, 7)
        old_guitar = pose((-.1, .3, .2), -.4).expand(2, 7)
        rigid = pose((.2, .1, -.03), .6)
        previous = apply(old_palm[:, None, None, 3:], self.points) + old_palm[:, None, None, :3]

        def transform_pose(old):
            return torch.cat((apply(rigid[3:], old[..., :3]) + rigid[:3],
                              multiply(rigid[3:].expand_as(old[..., 3:]), old[..., 3:])), -1)

        current = apply(rigid[3:], previous) + rigid[:3]
        result = decompose_pad_motion(previous, current, old_palm, transform_pose(old_palm),
                                      old_guitar, transform_pose(old_guitar))
        for value in (result.total, result.support, result.finger):
            torch.testing.assert_close(value, torch.zeros_like(value), atol=5e-16, rtol=0)

    def test_body_specific_pose_broadcast_and_invalid_shape(self):
        old = pose().expand(2, 4, 7)
        result = decompose_pad_motion(self.points, self.points, old, old, self.zero, self.zero)
        torch.testing.assert_close(result.total, torch.zeros_like(self.points))
        with self.assertRaisesRegex(ValueError, 'aligned'):
            decompose_pad_motion(self.points, self.points[:, :, :127], old, old, self.zero, self.zero)


if __name__ == '__main__':
    unittest.main()
