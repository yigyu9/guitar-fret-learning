"""CPU source-surface and contact/reward semantics; no native simulation."""
import hashlib
import json
from pathlib import Path
import unittest

import numpy as np
import torch
from scipy.spatial.transform import Rotation

from guitar_learning.gpu.fingertip_pad import (load_fingertip_pad, _sample_patch,
    pad_target_geometry, pad_tracking_reward, FINGERTIP_TRACKING_CONTRACT)
from guitar_learning.gpu.finger_reward import finger_tracking_reward


class SourcePadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pad = load_fingertip_pad()

    def test_source_samples_and_normals_match_original_triangles(self):
        for index, row in enumerate(self.pad['contract']['fingers_diagnostics']):
            payload = Path(row['mesh']).read_bytes()
            layout = np.dtype([('normal', '<f4', (3,)), ('vertices', '<f4', (3, 3)), ('attribute', '<u2')])
            source = np.frombuffer(payload, dtype=layout, count=row['source_triangle_count'], offset=84)['vertices'].astype(np.float64)
            source *= row['mesh_scale']
            quat = row['geom_quaternion_wxyz']
            source = Rotation.from_quat(quat[1:]+quat[:1]).apply(source.reshape(-1, 3)).reshape(-1, 3, 3)
            source += row['geom_position_m']
            selected = source[row['source_triangle_indices']]
            barycentric = np.array(row['source_barycentric'])
            self.assertTrue((barycentric >= -1e-10).all())
            np.testing.assert_allclose(barycentric.sum(-1), 1., atol=1e-12)
            expected = np.einsum('si,sij->sj', barycentric, selected)
            np.testing.assert_allclose(self.pad['points_local'][index], expected, atol=2e-9)
            normal = np.cross(selected[:, 1]-selected[:, 0], selected[:, 2]-selected[:, 0])
            normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
            np.testing.assert_allclose(self.pad['normals_local'][index], normal, atol=6e-8)

    def test_every_final_sample_passes_local_patch_definition(self):
        self.assertEqual(self.pad['points_local'].shape, (4, 128, 3))
        self.assertTrue(self.pad['valid'].all())
        for index, row in enumerate(self.pad['contract']['fingers_diagnostics']):
            p, n = self.pad['points_local'][index], self.pad['normals_local'][index]
            ymin, ymax = row['mesh_y_bounds_m']
            u = (ymax-p[:, 1])/(ymax-ymin)
            self.assertTrue((p[:, 2] <= 0).all())
            self.assertTrue((u >= .25).all())
            self.assertTrue(((n[:, 2] <= -.25) | ((u >= .75) & (n[:, 1] <= -.4) & (n[:, 2] <= 0))).all())
            np.testing.assert_allclose(np.linalg.norm(n, axis=-1), 1., atol=1e-7)
            self.assertGreater(row['distal_quarter_sample_count'], 20)
            self.assertLess(row['nearest_sample_spacing_m']['max'], .003)
            self.assertGreater(row['sampled_source_triangle_count'], 50)

    def test_deterministic_json_safe_and_source_pins(self):
        second = load_fingertip_pad()
        for key in ('points_local', 'normals_local', 'valid'):
            np.testing.assert_array_equal(second[key], self.pad[key])
        self.assertEqual(second['contract'], self.pad['contract'])
        json.dumps(self.pad['contract'], allow_nan=False)
        for path, sha in self.pad['contract']['source_sha256'].items():
            self.assertEqual(hashlib.sha256(Path(path).read_bytes()).hexdigest(), sha)
        self.assertIn('engineering patch', self.pad['contract']['limitation'])

    def test_clips_final_points_instead_of_accepting_whole_centroid_triangle(self):
        # Down-facing triangles include a proximal half and a part above z=0.
        triangles = np.array([[[-1., -1., -.2], [1., -1., -.2], [1., 1., -.2]],
                              [[-1., -1., -.2], [1., 1., -.2], [-1., 1., -.2]]])[:, ::-1]
        points, normals, row = _sample_patch(triangles)
        self.assertTrue((points[:, 1] <= .5).all())  # ymax1 - .25*length2
        self.assertTrue((normals[:, 2] < -.99).all())
        self.assertAlmostEqual(row['patch_area_m2'], 3.)
        # Equal-area sampling covers left/right and proximal/distal interiors.
        self.assertLess(abs(float((points[:, 0] < 0).mean())-.5), .08)
        self.assertLess(abs(float((points[:, 1] < -.25).mean())-.5), .08)
        self.assertLess(points[:, 0].min(), -.8)
        self.assertGreater(points[:, 0].max(), .8)
        crossing = np.array([[[-1., -1., -.5], [1., 1., .5], [1., -1., -.5]]])
        p, _, _ = _sample_patch(crossing)
        self.assertTrue((p[:, 2] <= 0).all())

    def test_dorsal_and_proximal_cap_rejected(self):
        dorsal = np.array([[[-1., -1., .2], [1., -1., .2], [1., 1., .2]]])
        with self.assertRaises(ValueError):
            _sample_patch(dorsal)


class PadGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    @staticmethod
    def inputs(n=1, p=2):
        starts = torch.zeros(n, 6, 3)
        ends = starts.clone(); ends[..., 1] = 1.
        points = torch.zeros(n, 4, p, 3); points[..., 1] = .5; points[..., 2] = .001
        normals = torch.zeros_like(points); normals[..., 2] = -1
        return dict(points=points, normals=normals, velocities=torch.zeros_like(points),
                    valid=torch.ones(4, p, dtype=torch.bool), starts=starts, ends=ends,
                    low=torch.zeros(n, 4), high=torch.ones(n, 4), strings=torch.arange(4),
                    fingers=torch.arange(1, 5), loaded=torch.ones(n, 4, dtype=torch.bool),
                    plane=torch.tensor([0., 0., 1., 0.]))

    def test_pad_position_facing_loaded_and_flat_sample_indices(self):
        x = self.inputs()
        result = pad_target_geometry(**x)
        self.assertTrue(result['positive'].all())
        self.assertEqual(result['sample_index'].tolist(), [[0, 2, 4, 6]])
        torch.testing.assert_close(result['distance'], torch.full((1, 4), .001))
        torch.testing.assert_close(result['delta'][..., 2], torch.full((1, 4), -.001))
        torch.testing.assert_close(result['normal_cos'], torch.ones(1, 4))
        torch.testing.assert_close(result['signed_height'], torch.full((1, 4), .001))
        x['loaded'][0, 2] = False
        result = pad_target_geometry(**x)
        self.assertEqual(result['positive'].tolist(), [[True, True, False, True]])
        self.assertTrue(result['facing_geometry'].all())

    def test_backface_still_has_finite_approach_without_positive_contact(self):
        x = self.inputs()
        x['normals'][..., 2] = 1.
        result = pad_target_geometry(**x)
        self.assertTrue(result['position_geometry'].all())
        self.assertFalse(result['facing_geometry'].any())
        self.assertFalse(result['positive'].any())
        self.assertTrue(torch.isfinite(result['distance']).all())
        torch.testing.assert_close(result['normal_cos'], -torch.ones(1, 4))

    def test_position_and_facing_must_hold_for_same_sample(self):
        x = self.inputs()
        x['normals'][:, :, 0, 2] = 1.
        x['points'][:, :, 1, 0] = .004
        result = pad_target_geometry(**x)
        self.assertTrue(result['position_geometry'].all())
        self.assertFalse(result['facing_geometry'].any())

    def test_eligible_facing_sample_need_not_be_nearest_sample(self):
        x = self.inputs()
        x['normals'][:, :, 0, 2] = 1.
        x['points'][:, :, 1, 2] = .002
        result = pad_target_geometry(**x)
        self.assertTrue(result['positive'].all())
        self.assertTrue((result['normal_cos'] == -1).all())
        self.assertTrue((result['sample_index'] % 2 == 0).all())

    def test_invalid_sample_and_other_finger_cannot_create_candidate(self):
        x = self.inputs()
        x['points'][:, 1, :, 2] = .01
        x['points'][:, 1, 1, 2] = 0.
        x['valid'][1, 1] = False
        result = pad_target_geometry(**x)
        self.assertFalse(result['positive'][0, 1])
        self.assertEqual(int(result['sample_index'][0, 1]), 2)
        self.assertAlmostEqual(float(result['distance'][0, 1]), .01)
        # Contract accepts only distal[N,4,P,3], never old middle/distal[N,10,P,3].
        x['points'] = torch.zeros(1, 10, 2, 3)
        with self.assertRaises(ValueError):
            pad_target_geometry(**x)

    def test_lateral_and_height_boundaries(self):
        x = self.inputs(n=6)
        x['points'][..., 2] = torch.tensor([-.001, -.00101, .003, .00301, 0., 0.])[:, None, None]
        x['points'][4, :, :, 0] = .003
        x['points'][5, :, :, 0] = .00301
        actual = pad_target_geometry(**x)['positive'][:, 0]
        self.assertEqual(actual.tolist(), [True, False, True, False, True, False])

    def test_real_cell_is_inset_not_expanded_and_nearest_is_clamped(self):
        x = self.inputs(n=4)
        x['low'].fill_(.4); x['high'].fill_(.6)
        x['points'][..., 1] = torch.tensor([.401, .403, .597, .599])[:, None, None]
        x['points'][..., 2] = 0.
        result = pad_target_geometry(**x)
        self.assertEqual(result['positive'][:, 0].tolist(), [False, True, True, False])
        torch.testing.assert_close(result['delta'][:, 0, 1], torch.tensor([.001, 0., 0., -.001]), atol=1e-7, rtol=0)
        # Flipping finite-string endpoint order leaves identical geometry.
        x['starts'], x['ends'] = x['ends'], x['starts']
        flipped = pad_target_geometry(**x)
        for key in result:
            torch.testing.assert_close(flipped[key], result[key], atol=1e-7, rtol=0)

    def test_far_approach_is_finite_and_velocity_is_actual_selected_point(self):
        x = self.inputs()
        x['points'][:, :, 0, 0] = .2
        x['points'][:, :, 1, 0] = .3
        x['loaded'].fill_(False)
        x['velocities'][:, :, 0] = torch.tensor([1., -2., 3.])
        result = pad_target_geometry(**x)
        self.assertFalse(result['positive'].any())
        self.assertTrue(torch.isfinite(result['distance']).all())
        torch.testing.assert_close(result['velocity'], torch.tensor([[[-1., 2., -3.]]]).expand(1, 4, 3))

    def test_plane_normalization_and_oblique_plane_geometry(self):
        x = self.inputs()
        # Rotate plane, strings, points and normals together around y.
        angle = .3
        rotation = torch.tensor([[np.cos(angle), 0., np.sin(angle)], [0., 1., 0.],
                                 [-np.sin(angle), 0., np.cos(angle)]], dtype=torch.float32)
        reference = pad_target_geometry(**x)
        for key in ('points', 'normals', 'velocities', 'starts', 'ends'):
            x[key] = x[key]@rotation.T
        x['plane'][:3] = rotation[:, 2]*2
        result = pad_target_geometry(**x)
        for key in ('distance', 'normal_cos', 'signed_height', 'positive'):
            torch.testing.assert_close(result[key], reference[key])

    def test_empty_targets_shapes_and_no_input_mutation(self):
        x = self.inputs()
        copies = {key: value.clone() for key, value in x.items()}
        pad_target_geometry(**x)
        for key in x:
            torch.testing.assert_close(x[key], copies[key], rtol=0, atol=0)
        x.update(strings=torch.empty(0, dtype=torch.long), fingers=torch.empty(0, dtype=torch.long),
                 low=torch.empty(1, 0), high=torch.empty(1, 0))
        result = pad_target_geometry(**x)
        self.assertEqual(result['delta'].shape, (1, 0, 3))
        self.assertEqual(result['positive'].shape, (1, 0))

    def test_rejects_invalid_source_and_target_contracts(self):
        x = self.inputs()
        x['valid'][0] = False
        with self.assertRaises(RuntimeError):
            pad_target_geometry(**x)
        x = self.inputs(); x['low'].fill_(.499); x['high'].fill_(.501)
        with self.assertRaises(RuntimeError):
            pad_target_geometry(**x)
        x = self.inputs(); x['fingers'][0] = 0
        with self.assertRaises(RuntimeError):
            pad_target_geometry(**x)


class PadRewardTests(unittest.TestCase):
    @staticmethod
    def inputs(n=1):
        return dict(now=torch.ones(n), onset=torch.tensor([.5]), end=torch.tensor([2.]),
                    press=torch.tensor([.4]), finger=torch.tensor([1]),
                    delta=torch.zeros(n, 1, 3), velocity=torch.zeros(n, 1, 3),
                    candidate=torch.zeros(n, 1, dtype=torch.bool), actions=torch.zeros(n, 21),
                    alignment=torch.ones(n, 1))

    def test_alignment_is_weak_near_only_clamped_and_preserves_rate_units(self):
        x = self.inputs(n=5)
        x['delta'][:, 0, 0] = torch.tensor([0., .01, .02, .1, 1.])
        reference = finger_tracking_reward(**{key: value for key, value in x.items() if key != 'alignment'})
        x['alignment'].fill_(-1.)
        result = pad_tracking_reward(**x)
        torch.testing.assert_close(result['rate'], reference['rate']*torch.tensor([.8, .9, 1., 1., 1.]))
        self.assertTrue((result['rate'] > 0).all())
        x['alignment'].fill_(2.)
        torch.testing.assert_close(pad_tracking_reward(**x)['rate'], reference['rate'])
        self.assertEqual(FINGERTIP_TRACKING_CONTRACT['base_rate_per_s'], 2.)
        self.assertEqual(FINGERTIP_TRACKING_CONTRACT['rate_bounds_per_s'], [0., 2.])
        self.assertIn('none', FINGERTIP_TRACKING_CONTRACT['motion_cost'])

    def test_motion_has_zero_cost_inputs_unchanged_and_candidate_is_independent(self):
        x = self.inputs()
        x['alignment'].fill_(.5)
        before = {key: value.clone() for key, value in x.items()}
        rate = pad_tracking_reward(**x)['rate']
        for key in x:
            torch.testing.assert_close(x[key], before[key], rtol=0, atol=0)
        x['velocity'].fill_(100.)
        x['actions'].fill_(-1.)
        torch.testing.assert_close(pad_tracking_reward(**x)['rate'], rate)
        x['candidate'].fill_(True)
        torch.testing.assert_close(pad_tracking_reward(**x)['rate'], rate)

    def test_existing_selector_denominator_and_empty_window_are_preserved(self):
        x = self.inputs()
        x.update(onset=torch.tensor([3., 8.]), end=torch.tensor([4., 9.]),
                 press=torch.tensor([2.5, 7.5]), finger=torch.tensor([1, 3]),
                 delta=torch.zeros(1, 2, 3), velocity=torch.zeros(1, 2, 3),
                 candidate=torch.zeros(1, 2, dtype=torch.bool), alignment=torch.ones(1, 2))
        self.assertEqual(float(pad_tracking_reward(**x)['rate']), 1.)
        x['now'].fill_(-1.)
        result = pad_tracking_reward(**x)
        self.assertEqual(float(result['rate']), 0.)
        self.assertFalse(result['valid'].any())
        self.assertEqual(result['indices'].tolist(), [[-1, -1, -1, -1]])

    def test_shared_recovery_weight_removes_competing_tracking_credit_per_finger(self):
        x = self.inputs(n=3)
        weight = torch.ones(3, 4)
        weight[:, 0] = torch.tensor([0., .5, 1.])
        result = pad_tracking_reward(**x, tracking_weight=weight)
        torch.testing.assert_close(result['rate'], torch.tensor([0., 1., 2.]))
        self.assertTrue(result['valid'][:, 0].all())  # Selection remains observable.
        self.assertEqual(result['indices'][:, 0].tolist(), [0, 0, 0])
        with self.assertRaises(ValueError):
            pad_tracking_reward(**x, tracking_weight=torch.ones(3, 1))

    def test_empty_score_and_shape_validation(self):
        x = self.inputs()
        for key in ('onset', 'end', 'press', 'finger'):
            x[key] = x[key][:0]
        for key in ('delta', 'velocity', 'candidate', 'alignment'):
            x[key] = x[key][:, :0]
        self.assertEqual(float(pad_tracking_reward(**x)['rate']), 0.)
        x['alignment'] = torch.zeros(1, 1)
        with self.assertRaises(ValueError):
            pad_tracking_reward(**x)


if __name__ == '__main__':
    unittest.main()
