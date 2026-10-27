"""CPU geometry/penalty checks for the free GPU wrist-region contract."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
from scipy.spatial.transform import Rotation
import torch

from guitar_learning.gpu.press_surface import load_press_surface
from guitar_learning.gpu.wrist_region import load_wrist_region_track, measure_wrist_region


ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT/'data/song_bundles/05_BN2-131-B_solo'


class WristRegionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.surface = load_press_surface([0], [5])
        cls.track = load_wrist_region_track(BUNDLE, cls.surface)

    @staticmethod
    def measure(points, times=None, lower=None, upper=None, track_times=None):
        points = torch.tensor(points, dtype=torch.float64)
        if times is None:
            times = [0.]*len(points)
        if lower is None:
            lower, upper = [[0., 0., 0.]], [[.07, .12, .09]]
        if track_times is None:
            track_times = [0.]
        return measure_wrist_region(points, torch.tensor(times, dtype=points.dtype),
            torch.tensor(track_times, dtype=points.dtype),
            torch.tensor(lower, dtype=points.dtype), torch.tensor(upper, dtype=points.dtype))

    def test_current_source_bounds_match_agreed_f5_f9_visuals(self):
        # Frozen visual frame219/F5 and821/F9 include policy pre-roll3s;
        # the song track is frame39 and641 respectively. Values are in metres.
        expected = {
            39: ([.032747671176728485, -.018879490202489746, -.1007],
                 [.10274767117672848, .10112050979751025, -.0107]),
            641: ([.034361110076170646, -.11088699403158089, -.1007],
                  [.10436111007617065, .00911300596841911, -.0107])}
        for frame, (lower, upper) in expected.items():
            np.testing.assert_allclose(self.track['lower_G_m'][frame], lower, rtol=0, atol=1e-8)
            np.testing.assert_allclose(self.track['upper_G_m'][frame], upper, rtol=0, atol=1e-8)
        np.testing.assert_allclose(np.array(self.track['upper_G_m'])-self.track['lower_G_m'],
                                   np.tile([.07, .12, .09], (1622, 1)), rtol=0, atol=1e-12)
        self.assertEqual(self.track['times_s'], [i/60. for i in range(1622)])
        contract = self.track['contract']
        self.assertEqual(contract['stage_weights'], [.2, .1, .05])
        self.assertEqual(contract['integration_dt_s'], 1/240.)
        self.assertEqual(contract['excess_scales_G_xyz_m'], [.02, .03, .03])
        json.dumps(self.track, allow_nan=False)
        for name, sha in contract['source_sha256'].items():
            self.assertEqual(hashlib.sha256(Path(name).read_bytes()).hexdigest(), sha)

    def test_all_interior_faces_corners_have_zero_penalty_and_free_rotation(self):
        points = [[x, y, z] for x in (0, .035, .07) for y in (0, .06, .12) for z in (0, .045, .09)]
        result = self.measure(points)
        self.assertTrue(result['ready'].all())
        torch.testing.assert_close(result['position'], torch.zeros(27, dtype=torch.float64), atol=0, rtol=0)
        torch.testing.assert_close(result['delta'], torch.zeros((27, 3), dtype=torch.float64), atol=0, rtol=0)
        torch.testing.assert_close(result['rotation'], torch.zeros((27, 3), dtype=torch.float64), atol=0, rtol=0)
        torch.testing.assert_close(result['orientation'], torch.ones(27, dtype=torch.float64), atol=0, rtol=0)

    def test_all_six_exits_point_back_to_nearest_face_and_penalty_is_monotone(self):
        center = np.array([.035, .06, .045])
        lo, hi = np.zeros(3), np.array([.07, .12, .09])
        scales = [.02, .03, .03]
        for axis in range(3):
            for side in (-1, 1):
                points = np.repeat(center[None], 2, axis=0)
                edge = lo[axis] if side == -1 else hi[axis]
                points[:, axis] = edge+side*np.array([scales[axis], scales[axis]*2])
                result = self.measure(points)
                self.assertFalse(result['ready'].any())
                torch.testing.assert_close(result['position'], torch.tensor([-.5, -.8], dtype=torch.float64))
                nearest = np.clip(points, lo, hi)
                torch.testing.assert_close(result['delta'], torch.tensor(nearest-points))
                torch.testing.assert_close(result['distance_m'], torch.tensor([scales[axis], 2*scales[axis]], dtype=torch.float64))
                self.assertTrue(((result['position'] < 0) & (result['position'] > -1)).all())

    def test_corner_penalty_and_stage_rate_examples_integrate_once_at_240hz(self):
        result = self.measure([[-.01, .06, .045], [.035, -.03, .045], [-.02, -.03, -.03]])
        torch.testing.assert_close(result['position'], torch.tensor([-.2, -.5, -.75], dtype=torch.float64))
        rates = .2*result['position']
        torch.testing.assert_close(rates[:2], torch.tensor([-.04, -.1], dtype=torch.float64))
        torch.testing.assert_close((rates/240.).repeat(240, 1).sum(0), rates)

    def test_bounds_interpolate_and_clamp_before_pre_roll_and_after_track(self):
        lower = [[0, 0, 0], [1, 2, 3]]
        upper = [[.07, .12, .09], [1.07, 2.12, 3.09]]
        result = self.measure([[.01, .01, .01]]*5, times=[-3., 0., .5, 1., 99.],
                              lower=lower, upper=upper, track_times=[0., 1.])
        torch.testing.assert_close(result['lower_G_m'], torch.tensor(
            [[0, 0, 0], [0, 0, 0], [.5, 1, 1.5], [1, 2, 3], [1, 2, 3]], dtype=torch.float64))
        widths = torch.tensor([.07, .12, .09], dtype=torch.float64).expand(5, -1)
        torch.testing.assert_close(result['upper_G_m']-result['lower_G_m'], widths)

    def test_guitar_local_measurement_is_covariant_under_rigid_world_motion(self):
        points_G = np.array([[-.02, .06, .045], [.035, .06, .045]])
        rotation = Rotation.from_euler('xyz', [1.2, -.6, 2.1])
        translation = np.array([3.1, -2., .8])
        points_W = rotation.apply(points_G)+translation
        recovered_G = rotation.inv().apply(points_W-translation)
        result, moved = self.measure(points_G), self.measure(recovered_G)
        for key in ('delta', 'position', 'orientation', 'rotation', 'distance_m'):
            torch.testing.assert_close(result[key], moved[key], atol=1e-12, rtol=0)
        self.assertEqual(result['ready'].tolist(), moved['ready'].tolist())

    def _write_track(self, folder, document, valid_pin=True):
        folder = Path(folder)
        (folder/'training').mkdir(exist_ok=True)
        payload = json.dumps(document).encode()
        (folder/'training/hand_position_targets.json').write_bytes(payload)
        pin = hashlib.sha256(payload).hexdigest() if valid_pin else '0'*64
        (folder/'manifest.json').write_text(json.dumps({'files': {
            'training/hand_position_targets.json': {'bytes': len(payload), 'sha256': pin}}}))

    def test_invalid_track_structure_values_and_manifest_are_rejected(self):
        original = dict(schema='tab2body.hand_position_targets.v1', coordinate_frame='guitar local',
            frames=[dict(frame=0, t=0., anchor_fret=5., allowed_fret_range=[4, 9])])
        mutations = [lambda d: d.update(schema='wrong'), lambda d: d.update(coordinate_frame='world'),
                     lambda d: d.update(frames=[])]
        for key, value in [('frame', True), ('frame', 1), ('t', .1), ('t', float('nan')),
                           ('anchor_fret', True), ('anchor_fret', 0), ('anchor_fret', 23),
                           ('allowed_fret_range', [9, 4]), ('allowed_fret_range', [4., 9]),
                           ('allowed_fret_range', [0, 9]), ('allowed_fret_range', [4, 23]),
                           ('allowed_fret_range', [6, 9]), ('allowed_fret_range', [4])]:
            mutations.append(lambda d, k=key, v=value: d['frames'][0].update({k: v}))
        with tempfile.TemporaryDirectory() as folder:
            self._write_track(folder, original, valid_pin=False)
            with self.assertRaisesRegex(ValueError, 'fingerprint'):
                load_wrist_region_track(folder, self.surface)
            for mutation in mutations:
                document = copy.deepcopy(original)
                mutation(document)
                self._write_track(folder, document)
                with self.assertRaises(ValueError):
                    load_wrist_region_track(folder, self.surface)

    def test_press_plane_and_source_fingerprints_cannot_be_substituted(self):
        for field, value in [('plane_G', [0., 0., 1., 0.]), ('schema', 'wrong'), ('source_sha256', {})]:
            surface = copy.deepcopy(self.surface)
            surface[field] = value
            with self.assertRaises(ValueError):
                load_wrist_region_track(BUNDLE, surface)
        surface = copy.deepcopy(self.surface)
        key = next(path for path in surface['source_sha256'] if path.endswith('.obj'))
        surface['source_sha256'][key] = '0'*64
        with self.assertRaisesRegex(ValueError, 'pins mismatch'):
            load_wrist_region_track(BUNDLE, surface)


if __name__ == '__main__':
    unittest.main()
