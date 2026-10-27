"""CPU checks of source witnesses, finite region, and weak thumb reward."""
import hashlib
import json
from pathlib import Path
import unittest

import numpy as np
from scipy.spatial.transform import Rotation
import torch

from guitar_learning.gpu.thumb_support import load_thumb_support, thumb_support_geometry, THUMB_SUPPORT_CONTRACT


class ThumbSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = load_thumb_support()

    def test_actual_source_barycentrics_and_outward_normal_are_same_face(self):
        row = self.source['contract']['patch_diagnostics']
        payload = Path(row['mesh']).read_bytes()
        layout = np.dtype([('normal', '<f4', (3,)), ('vertices', '<f4', (3, 3)), ('attribute', '<u2')])
        triangles = np.frombuffer(payload, dtype=layout, count=row['source_triangle_count'], offset=84)['vertices'].astype(np.float64)
        triangles *= row['mesh_scale']
        quat = row['geom_quaternion_wxyz']
        triangles = Rotation.from_quat(quat[1:]+quat[:1]).apply(triangles.reshape(-1, 3)).reshape(-1, 3, 3)
        triangles += row['geom_position_m']
        source = triangles[row['source_triangle_indices']]
        barycentric = np.asarray(row['source_barycentric'])
        self.assertTrue((barycentric >= -1e-10).all())
        np.testing.assert_allclose(barycentric.sum(-1), 1., atol=1e-12)
        np.testing.assert_allclose(self.source['points_local'], np.einsum('si,sij->sj', barycentric, source), atol=2e-9)
        normal = np.cross(source[:, 1]-source[:, 0], source[:, 2]-source[:, 0])
        normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
        np.testing.assert_allclose(self.source['normals_local'], normal, atol=6e-8)

    def test_only_actual_distal_flexion_patch_is_used(self):
        points, normal = self.source['points_local'], self.source['normals_local']
        row = self.source['contract']['patch_diagnostics']
        xmin, xmax = row['canonical_mesh_y_bounds_m']
        u = (xmax-points[:, 0])/(xmax-xmin)
        self.assertEqual(points.shape, (128, 3))
        self.assertTrue(self.source['valid'].all())
        self.assertTrue((points[:, 1] <= 0).all())
        self.assertTrue((u >= .25).all())
        self.assertTrue(((normal[:, 1] <= -.25) | ((u >= .75) & (normal[:, 0] <= -.4) & (normal[:, 1] <= 0))).all())
        self.assertGreater(row['sampled_source_triangle_count'], 30)

    def test_rear_is_finite_source_trapezoid_and_every_source_pin_matches(self):
        rear, plane = self.source['rear_vertices'], self.source['plane']
        np.testing.assert_allclose(rear@plane[:3]+plane[3], 0., atol=1e-10)
        self.assertLess(plane[2], -.9)
        self.assertLess(rear[0, 1], rear[2, 1])
        self.assertLess(rear[0, 0], rear[1, 0])
        self.assertLess(rear[3, 0], rear[2, 0])
        for path, sha in self.source['contract']['source_sha256'].items():
            self.assertEqual(hashlib.sha256(Path(path).read_bytes()).hexdigest(), sha)
        json.dumps(self.source['contract'], allow_nan=False)
        second = load_thumb_support()
        for key in ('points_local', 'normals_local', 'valid', 'rear_vertices', 'plane'):
            np.testing.assert_array_equal(self.source[key], second[key])


class ThumbGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    @staticmethod
    def inputs(n=1, samples=1):
        points = torch.zeros(n, samples, 3, dtype=torch.float64)
        points[..., 2] = -.001
        normals = torch.zeros_like(points)
        normals[..., 2] = 1.
        return dict(points=points, normals=normals, valid=torch.ones(samples, dtype=torch.bool),
            center_y=torch.zeros(n, dtype=torch.float64),
            rear_vertices=torch.tensor([[-.04, -.2, 0], [.04, -.2, 0],
                [.08, .2, 0], [-.08, .2, 0]], dtype=torch.float64),
            plane=torch.tensor([0., 0., -1., 0.], dtype=torch.float64))

    def test_signed_gap_plateau_bounded_rate_and_no_force_input(self):
        x = self.inputs(5)
        x['points'][:, 0, 2] = -torch.tensor([0., .001, .003, .013, .023], dtype=torch.float64)
        r = thumb_support_geometry(**x)
        torch.testing.assert_close(r['signed_gap'], torch.tensor([0., .001, .003, .013, .023], dtype=torch.float64))
        torch.testing.assert_close(r['quality'][:3], torch.ones(3, dtype=torch.float64))
        self.assertTrue((r['quality'][3:] < 1).all())
        self.assertGreater(r['quality'][3], r['quality'][4])
        self.assertEqual(r['near_geometry'].tolist(), [True, True, True, False, False])
        torch.testing.assert_close(r['rate'], .02*r['quality'])
        self.assertEqual(THUMB_SUPPORT_CONTRACT['rate_per_s'], .02)

    def test_orientation_and_signed_penetration_gate(self):
        x = self.inputs(7)
        x['points'][:, 0, 2] = torch.tensor([-.001, -.001, .0005, .001, .004, -.001, -.001], dtype=torch.float64)
        x['normals'][1, 0, 2] = -1.
        x['normals'][5, 0] = torch.tensor([1., 0., 0.])
        x['normals'][6, 0] = torch.tensor([np.sqrt(.84), 0., .4])
        r = thumb_support_geometry(**x)
        torch.testing.assert_close(r['quality'], torch.tensor([1., 0., .5, 0., 0., 0., .5], dtype=torch.float64))
        self.assertFalse(r['near_geometry'][2])

    def test_finite_region_central_half_taper_and_moving_work_center(self):
        x = self.inputs(5)
        x['points'][:, 0] = torch.tensor([[.03, 0., -.001], [.04, 0., -.001],
            [0., .1, -.001], [0., .1, -.001], [0., .3, -.001]], dtype=torch.float64)
        x['center_y'][:] = torch.tensor([0., 0., 0., .1, .19], dtype=torch.float64)
        r = thumb_support_geometry(**x)
        torch.testing.assert_close(r['region_excess'], torch.tensor([0., .01/np.sqrt(1.0025), .06, 0., .1], dtype=torch.float64), atol=1e-12, rtol=1e-10)
        self.assertEqual(r['near_geometry'].tolist(), [True, False, False, True, False])
        target = r['selected_point']+r['delta']
        torch.testing.assert_close(target[-1, 1], torch.tensor(.2, dtype=torch.float64))

    def test_one_sample_must_supply_position_and_facing(self):
        x = self.inputs(samples=2)
        x['normals'][0, 0, 2] = -1.
        x['points'][0, 1, 2] = -.023
        r = thumb_support_geometry(**x)
        self.assertEqual(r['sample_index'].item(), 1)
        self.assertAlmostEqual(r['signed_gap'].item(), .023)
        self.assertAlmostEqual(r['normal_cos'].item(), 1.)
        self.assertAlmostEqual(r['quality'].item(), .25)
        self.assertFalse(r['near_geometry'].item())
        torch.testing.assert_close(r['selected_point'], x['points'][:, 1])
        torch.testing.assert_close(r['selected_normal'], x['normals'][:, 1])

    def test_nearest_fallback_when_all_faces_wrong_and_first_tie(self):
        x = self.inputs(samples=3)
        x['normals'][..., 2] = -1.
        x['points'][0, :, 2] = torch.tensor([-.02, -.001, -.001], dtype=torch.float64)
        r = thumb_support_geometry(**x)
        self.assertEqual(r['sample_index'].item(), 1)
        self.assertEqual(r['quality'].item(), 0.)
        self.assertTrue(r['valid'].item())

    def test_invalid_inputs_and_outside_work_region_return_finite_zero(self):
        x = self.inputs(5, 2)
        x['points'][0] = torch.nan
        x['normals'][1] = torch.inf
        x['normals'][2] = 0.
        x['center_y'][3] = torch.nan
        x['center_y'][4] = 1.
        r = thumb_support_geometry(**x)
        self.assertFalse(r['valid'].any())
        self.assertEqual(r['sample_index'].tolist(), [-1]*5)
        for key, value in r.items():
            self.assertTrue(torch.isfinite(value).all(), key)
        self.assertTrue((r['quality'] == 0).all())

    def test_masking_plane_scale_and_no_input_mutation(self):
        x = self.inputs(samples=2)
        x['valid'][0] = False
        old = {k: v.clone() for k, v in x.items()}
        r = thumb_support_geometry(**x)
        self.assertEqual(r['sample_index'].item(), 1)
        for key, value in x.items():
            torch.testing.assert_close(value, old[key])
        x['plane'] *= 3
        scaled = thumb_support_geometry(**x)
        for key in r:
            torch.testing.assert_close(r[key], scaled[key])
        x['valid'][:] = False
        self.assertFalse(thumb_support_geometry(**x)['valid'].item())

    def test_rotated_rear_plane_distance(self):
        x = self.inputs()
        # A source-like rear plane slants along guitar Gy.
        x['rear_vertices'][:, 2] = -.02*x['rear_vertices'][:, 1]
        x['plane'] = torch.tensor([0., -.02, -1., 0.], dtype=torch.float64)
        unit = x['plane'][:3]/torch.linalg.vector_norm(x['plane'][:3])
        x['points'][0, 0] = .002*unit
        x['normals'][0, 0] = -unit
        r = thumb_support_geometry(**x)
        self.assertAlmostEqual(r['signed_gap'].item(), .002)
        self.assertAlmostEqual(r['quality'].item(), 1.)
        torch.testing.assert_close(r['delta'][0], -.002*unit)

    def test_shape_validation(self):
        x = self.inputs()
        x['valid'] = x['valid'].float()
        with self.assertRaises(ValueError):
            thumb_support_geometry(**x)


if __name__ == '__main__':
    unittest.main()
