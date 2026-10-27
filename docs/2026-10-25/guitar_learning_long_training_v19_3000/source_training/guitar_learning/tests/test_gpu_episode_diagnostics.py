"""Pure tensor diagnostics: denominators and geometry, not native success."""
import json
import math
import unittest

import torch

from guitar_learning.gpu.episode_diagnostics import (LeftEpisodeDiagnostics,
    load_thumb_rear_surface, thumb_rear_distance)
from guitar_learning.gpu.finger_reward import finger_preparation_reward
from guitar_learning.tests import test_gpu_environment as fixtures


class EpisodeDiagnosticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def inputs(self, count=2):
        p = dict(gate=torch.ones(count, 4, dtype=torch.float64),
            quality=torch.ones(count, 4, dtype=torch.float64),
            near_veto=torch.zeros(count, 4, dtype=torch.bool),
            nonfinite_veto=torch.zeros(count, 4, dtype=torch.bool),
            contact_veto=torch.zeros(count, 4, dtype=torch.bool),
            idle_weight=torch.ones(count, 4, dtype=torch.float64),
            angles=torch.ones(count, 4, 3, dtype=torch.float64),
            valid=torch.ones(count, 4, 3, dtype=torch.bool))
        return p, torch.zeros(count, 4, dtype=torch.bool), torch.zeros(count, 3, dtype=torch.float64)

    def test_weighted_reward_excludes_whole_failed_tick_and_has_fixed_four_denominator(self):
        d = LeftEpisodeDiagnostics(2, 'cpu')
        args = self.inputs()
        for _ in range(4):
            d.physics(*args)
        d.control(torch.tensor([False, True]), .3, torch.tensor([.002, .02]), torch.tensor([.002, .02]))
        good, failed = d.episode(0), d.episode(1)
        self.assertEqual(good['physics_endpoint_count'], 4)
        self.assertEqual(good['thumb']['endpoint_count'], 1)
        self.assertAlmostEqual(good['physics_sampled_s'], 1/60)
        self.assertAlmostEqual(sum(good['standby']['raw_standby_reward']), .01/60)
        self.assertAlmostEqual(sum(good['standby']['weighted_standby_reward']), .01/60*.3)
        self.assertEqual(failed['standby']['weighted_standby_reward'], [0.]*4)
        self.assertEqual(good['thumb']['rear_side_within3mm_fraction'], 1.)

    def test_exclusions_overlap_and_remain_finger_local_at_inclusive_distance_boundary(self):
        d = LeftEpisodeDiagnostics(2, 'cpu')
        p, pressing, wrist = self.inputs()
        p['idle_weight'][0] = torch.tensor([0., .5, 1., 1.])
        p['gate'][0] = torch.tensor([0., 0., 0., 1.])
        p['contact_veto'][0, :2] = True
        p['near_veto'][0] = torch.tensor([True, False, True, False])
        p['nonfinite_veto'][0, 1] = True
        d.physics(p, pressing, wrist)
        row = d.episode(0)['standby']
        self.assertEqual(row['time_blocked_s'], [1/240, 0., 0., 0.])
        self.assertEqual(row['time_faded_s'], [0., 1/240, 0., 0.])
        self.assertEqual(row['contact_excluded_s'], [1/240, 1/240, 0., 0.])
        self.assertEqual(row['proximity_excluded_s'], [1/240, 0., 1/240, 0.])
        self.assertEqual(row['nonfinite_distance_excluded_s'], [0., 1/240, 0., 0.])
        self.assertEqual(row['eligible_s'], [0., 0., 0., 1/240])

    def test_angles_use_per_joint_valid_and_gate_weighted_denominators(self):
        d = LeftEpisodeDiagnostics(2, 'cpu')
        args = self.inputs()
        p, pressing, _ = args
        p['gate'][0, 0] = .5
        pressing[0, 0] = True
        p['valid'][0, 0, 2] = False
        d.physics(*args)
        p['gate'][0, 0] = 1.
        p['angles'][0, 0] = 3.
        d.physics(*args)
        row = d.episode(0)
        idle, press = row['idle_angles'], row['press_angles']
        self.assertAlmostEqual(idle['mean_rad'][0][0], 7/3)
        self.assertAlmostEqual(idle['valid_weighted_s'][0][0], 1.5/240)
        self.assertAlmostEqual(press['mean_rad'][0][0], 2.)
        self.assertEqual(idle['min_rad'][0], [1., 1., 0.])
        self.assertEqual(idle['max_rad'][0], [3., 3., 0.])
        self.assertEqual(press['valid_weighted_s'][0][2], 0.)

    def test_wrist_axis_excess_and_inclusive_inside_fraction(self):
        d = LeftEpisodeDiagnostics(2, 'cpu')
        args = self.inputs()
        d.physics(*args)
        args[-1][0] = torch.tensor([-.02, .03, -.04])
        d.physics(*args)
        row = d.episode(0)['wrist']
        self.assertEqual(row['inside_fraction'], .5)
        torch.testing.assert_close(torch.tensor(row['mean_excess_G_xyz_m']), torch.tensor([.01, .015, .02]))
        torch.testing.assert_close(torch.tensor(row['max_excess_G_xyz_m']), torch.tensor([.02, .03, .04]))

    def test_selected_reset_preserves_other_row_and_bounded_storage(self):
        d = LeftEpisodeDiagnostics(2, 'cpu')
        pointers = {k: v.data_ptr() for k, v in d.values.items()}
        for _ in range(8):
            d.physics(*self.inputs())
        before = d.episode(1)
        d.reset([0])
        self.assertEqual(d.episode(1), before)
        self.assertEqual(d.episode(0)['physics_endpoint_count'], 0)
        self.assertEqual(d.episode(0)['idle_angles']['max_rad'], [[0.]*3]*4)
        self.assertEqual(pointers, {k: v.data_ptr() for k, v in d.values.items()})
        json.dumps(d.episode(0), allow_nan=False)

    def test_finite_triangle_distance_does_not_treat_infinite_plane_as_neck(self):
        triangles = torch.tensor([[[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]]], dtype=torch.float64)
        plane = torch.tensor([0., 0., -1., 0.], dtype=torch.float64)
        points = torch.tensor([[[.2, .2, -.002]], [[2., 0., -.002]], [[.2, .2, .002]]], dtype=torch.float64)
        distance, rear = thumb_rear_distance(points, torch.tensor([True]), triangles, plane)
        torch.testing.assert_close(distance, torch.tensor([.002, math.sqrt(1+.002**2), .002], dtype=torch.float64))
        self.assertEqual(rear[0], distance[0])
        self.assertTrue(torch.isinf(rear[2]))

    def test_invalid_surface_samples_are_excluded(self):
        triangles = torch.tensor([[[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]]])
        points = torch.tensor([[[.2, .2, 0.], [.2, .2, -.02]]])
        distance, rear = thumb_rear_distance(points, torch.tensor([False, True]), triangles, torch.tensor([0., 0., -1., 0.]))
        self.assertAlmostEqual(distance.item(), .02, places=7)
        self.assertEqual(distance, rear)

    def test_pinned_source_rear_is_finite_and_actual_source_plane(self):
        triangles, plane = load_thumb_rear_surface()
        self.assertEqual(triangles.shape, (4, 3, 3))
        self.assertLess(plane[2], -.5)
        self.assertLess(abs(triangles@plane[:3]+plane[3]).max(), 1e-10)

    def test_reward_helper_returns_its_same_measurement_without_new_rate_semantics(self):
        q = torch.tensor([[0., 0., 0., 1.]], dtype=torch.float64)
        p = finger_preparation_reward(torch.tensor([0.], dtype=torch.float64),
            torch.tensor([4.], dtype=torch.float64), torch.tensor([5.], dtype=torch.float64),
            torch.tensor([3.], dtype=torch.float64), torch.tensor([1]), q,
            q[:, None, None].expand(1, 4, 3, 4), torch.zeros(1, 4, dtype=torch.bool),
            torch.tensor([[.1]], dtype=torch.float64))
        self.assertEqual(p['angles'].shape, (1, 4, 3))
        self.assertTrue(p['valid'].all())
        torch.testing.assert_close(p['rate'], .01*(p['gate']*p['quality']).mean(-1))

    def test_environment_uses_physics_and_control_endpoints_and_preserves_partial_reset(self):
        env, snapshot, _ = fixtures.TensorSongTests.environment(self)
        fixtures.TensorSongTests.advance(env, snapshot, torch.zeros(2, 39))
        row = env._episode(0, False)['left_episode_diagnostics']
        self.assertEqual(row['physics_endpoint_count'], 4)
        self.assertEqual(row['thumb']['endpoint_count'], 1)
        self.assertAlmostEqual(sum(row['standby']['weighted_standby_reward']),
            env.episode_reward_terms['song_finger_standby'][0].item(), places=10)
        before = env.episode_diagnostics.episode(1)
        env.reset([0], snapshot)
        self.assertEqual(env.episode_diagnostics.episode(1), before)
        self.assertEqual(env.episode_diagnostics.episode(0)['physics_endpoint_count'], 0)
        json.dumps(row, allow_nan=False)


if __name__ == '__main__':
    unittest.main()
