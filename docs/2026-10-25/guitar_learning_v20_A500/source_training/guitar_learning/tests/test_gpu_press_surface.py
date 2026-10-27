"""CPU source geometry and tensor projection; no simulator or cooked claims."""
import hashlib
from pathlib import Path
import tempfile
import unittest

import numpy as np
from scipy.spatial.transform import Rotation
import torch

from guitar_learning.gpu.press_surface import (
    load_press_surface, project_press_strings, _extract_plane, _validate_targets)
from guitar_learning.gpu.geometry import surface_target_geometry
from guitar_learning.song.task import make_task


class PressSurfaceTests(unittest.TestCase):
    def synthetic(self, directory, vertices=None, angle=0.):
        directory = Path(directory)
        if vertices is None:
            vertices = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
        pins = {}
        for i in (1, 2):
            path = directory/('neck%d.obj'%i)
            path.write_text(''.join('v %s %s %s\n'%tuple(v) for v in vertices))
            pins[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        rotation = Rotation.from_euler('x', angle).as_quat()
        quat = ' '.join(str(v) for v in np.r_[rotation[3:], rotation[:3]])
        path = directory/'asset.xml'
        path.write_text('<mujoco><asset>'+''.join(
            '<mesh name="guitar_neck%d" file="neck%d.obj"/>'%(i, i) for i in (1, 2))+
            '</asset><worldbody><body>'+''.join(
            '<geom type="mesh" mesh="guitar_neck%d" quat="%s"/>'%(i, quat) for i in (1, 2))+
            '</body></worldbody></mujoco>')
        pins[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        return path, pins

    @staticmethod
    def targets():
        starts = np.zeros((6, 3)); starts[:, 1] = -.5
        ends = starts.copy(); ends[:, 1] = .5
        return starts, ends, np.array([-.2]), np.array([.2]), np.array([0])

    def test_current_67_notes_extract_9_3mm_plane_and_134_endpoints(self):
        bundle = Path(__file__).resolve().parents[2]/'data/song_bundles/05_BN2-131-B_solo'
        task = make_task(bundle)
        contract = load_press_surface([t.string for t in task.targets], [t.fret for t in task.targets])
        self.assertEqual(len(task.targets), 67)
        np.testing.assert_allclose(contract['plane_G'], [0, 0, 1, -.0093], rtol=0, atol=1e-12)
        self.assertEqual(contract['target_validation']['endpoint_count'], 134)
        self.assertEqual(contract['target_validation']['covered_endpoint_count'], 134)
        self.assertLess(contract['target_validation']['maximum_plane_residual_m'], 1e-12)
        self.assertEqual(contract['inward_margin_m'], .002)
        self.assertEqual(len(contract['source_sha256']), 4)  # XML, two OBJ, manifest.
        for name, expected in contract['source_sha256'].items():
            self.assertTrue(Path(name).is_absolute())
            self.assertEqual(hashlib.sha256(Path(name).read_bytes()).hexdigest(), expected)

    def test_tilted_source_plane_matches_projection_without_changing_xy_or_input(self):
        with tempfile.TemporaryDirectory() as folder:
            path, pins = self.synthetic(folder, angle=.2)
            plane, hulls, _ = _extract_plane(path, pins)
        expected = Rotation.from_euler('x', .2).apply([0., 0., 1.])
        np.testing.assert_allclose(plane[:3], expected, atol=1e-12)
        self.assertAlmostEqual(plane[3], -1.)
        proof = _validate_targets(plane, hulls, *self.targets())
        self.assertEqual(proof['endpoint_count'], 2)
        starts = torch.tensor(np.repeat(self.targets()[0][None], 2, axis=0))
        ends = torch.tensor(np.repeat(self.targets()[1][None], 2, axis=0))
        before = starts.clone(), ends.clone()
        projected = project_press_strings(starts, ends, torch.tensor(plane))
        for original, output in zip(before, projected):
            torch.testing.assert_close(output[..., :2], original[..., :2], rtol=0, atol=0)
            torch.testing.assert_close(output@torch.tensor(plane[:3])+plane[3], torch.zeros((2, 6), dtype=starts.dtype), atol=1e-12, rtol=0)
        torch.testing.assert_close(starts, before[0], rtol=0, atol=0)
        torch.testing.assert_close(ends, before[1], rtol=0, atol=0)

    def test_source_sha_and_nonplanar_top_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path, pins = self.synthetic(folder)
            (Path(folder)/'neck1.obj').write_text('changed')
            with self.assertRaisesRegex(ValueError, 'mesh SHA'):
                _extract_plane(path, pins)
            ridge = [(x, y, -1) for x in (-1, 1) for y in (-1, 1)]
            ridge += [(x, y, 0) for x in (-1, 1) for y in (-1, 1)]+[(0, -1, 1), (0, 1, 1)]
            path, pins = self.synthetic(folder, ridge)
            with self.assertRaisesRegex(ValueError, 'Single upward'):
                _extract_plane(path, pins)

    def test_outside_empty_and_disjoint_targets_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path, pins = self.synthetic(folder)
            plane, hulls, _ = _extract_plane(path, pins)
        args = list(self.targets()); args[0][:, 0] = 2; args[1][:, 0] = 2
        with self.assertRaisesRegex(ValueError, 'outside'):
            _validate_targets(plane, hulls, *args)
        args = list(self.targets()); args[3][:] = args[2]+.003
        with self.assertRaisesRegex(ValueError, 'Nonempty'):
            _validate_targets(plane, hulls, *args)
        args = list(self.targets()); args[2][:], args[3][:] = 2, 3
        with self.assertRaisesRegex(ValueError, 'intersect'):
            _validate_targets(plane, hulls, *args)
        for strings, frets in (([6], [1]), ([0], [0]), ([0.], [1]), ([], [])):
            with self.assertRaises(ValueError):
                load_press_surface(strings, frets)

    def test_projected_surface_geometry_uses_inward_cell_and_existing_velocity(self):
        starts = torch.zeros((1, 6, 3), dtype=torch.float64); starts[..., 2] = .0123
        ends = starts.clone(); ends[..., 1] = 1
        press = project_press_strings(starts, ends, torch.tensor([0., 0., 1., -.0093], dtype=starts.dtype))
        points = torch.full((1, 10, 1, 3), 10., dtype=starts.dtype)
        points[:, 2, 0] = torch.tensor([0., .2, .0093])
        velocity = torch.ones_like(points)*.01
        delta, speed, distance, index = surface_target_geometry(points, velocity,
            torch.ones((10, 1), dtype=torch.bool), *press,
            torch.tensor([[.2]], dtype=starts.dtype), torch.tensor([[.8]], dtype=starts.dtype),
            torch.tensor([0]), torch.tensor([1]), margin=-.002)
        torch.testing.assert_close(delta, torch.tensor([[[0., .002, 0.]]], dtype=starts.dtype), atol=1e-8, rtol=0)
        torch.testing.assert_close(speed, torch.full_like(speed, -.01))
        self.assertAlmostEqual(distance.item(), .002, places=7)
        self.assertEqual(index.item(), 2)
        with self.assertRaises(ValueError):
            project_press_strings(starts, ends, torch.ones(3, dtype=starts.dtype))


if __name__ == '__main__':
    unittest.main()
