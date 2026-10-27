"""Recorded pose geometry tests; these do not certify trained reachability."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
from scipy.spatial.transform import Rotation

from guitar_learning.core.geometry_v1 import frame, geometry_snapshot
from guitar_learning.song.wrist_guide import WristGuide, load_anchor_track


ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / 'data/song_bundles/05_BN2-131-B_solo'
PROBE = ROOT / 'docs/2026-10-12/stability_adapter_2/results/free_guitar_fretting_v1/native_probe_v1'


class WristGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.saved = json.loads((PROBE / 'prepared.json').read_text())['sample']
        initial = json.loads((PROBE / 'initial_values.json').read_text())
        cls.human_names, cls.guitar_names = initial['human_body_names'], initial['guitar_body_names']

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)

    def tearDown(self):
        self.folder.cleanup()

    def bundle(self, frames=None):
        document = dict(schema='tab2body.hand_position_targets.v1', coordinate_frame='guitar local',
            frames=frames if frames is not None else [dict(frame=0, t=0., anchor_fret=5.),
                                                      dict(frame=1, t=.0167, anchor_fret=6.)])
        self.write_document(document)
        return self.root

    def write_document(self, document):
        payload = json.dumps(document).encode()
        (self.root / 'training').mkdir(exist_ok=True)
        (self.root / 'training/hand_position_targets.json').write_bytes(payload)
        (self.root / 'manifest.json').write_text(json.dumps(dict(files={
            'training/hand_position_targets.json': dict(bytes=len(payload),
                sha256=hashlib.sha256(payload).hexdigest())})))

    def guide(self, bundle=None):
        return WristGuide(bundle or self.bundle(), self.saved, self.human_names, self.guitar_names)

    def test_actual_prepared_anchor5_targets_actual_wrist_not_legacy_offsets(self):
        guide = self.guide(BUNDLE)
        result = guide.measure(self.saved, 0.)
        self.assertEqual(result['anchor_fret'], 5.)
        np.testing.assert_allclose(result['target_G_m'], result['wrist_G_m'], atol=1e-15)
        self.assertAlmostEqual(result['distance_m'], 0.)
        self.assertAlmostEqual(result['angle_rad'], 0.)
        self.assertEqual(result['position_score'], 1.)
        self.assertEqual(result['orientation_score'], 1.)
        self.assertTrue(result['ready'])
        self.assertGreater(np.linalg.norm(np.array([.075, .084633, -.0227]) -
                                         np.array(result['target_G_m'])), .13)
        json.dumps(result, allow_nan=False)

    def test_anchor_interpolation_uses_exact_frame_clock_and_live_fret_displacement(self):
        guide = self.guide()
        baseline = guide.measure(self.saved, 0.)
        halfway = guide.measure(self.saved, 3. + 1/120.)
        self.assertAlmostEqual(halfway['anchor_fret'], 5.5)
        frets = np.asarray(self.saved['geometry']['fret_markers_G_m'])
        expected = np.array(baseline['target_G_m']) + [0., (frets[6, 1] - frets[5, 1]) / 2, 0.]
        np.testing.assert_allclose(halfway['target_G_m'], expected, atol=1e-14)
        self.assertEqual(guide.measure(self.saved, 100.)['anchor_fret'], 6.)
        self.assertEqual(guide.measure(self.saved, 2.)['anchor_fret'], 5.)

    def test_common_world_rotation_and_translation_preserve_current_guitar_errors(self):
        guide = self.guide()
        reference = guide.measure(self.saved, 3. + 1/120.)
        moved = copy.deepcopy(self.saved)
        transform = Rotation.from_euler('xyz', [.63, -.4, 1.1])
        translation = np.array([1.2, -3., .7])
        for key in ('human_body_states', 'guitar_body_states'):
            for body in moved['native'][key]:
                point, rotation = frame(body)
                body['pose']['p'] = dict(zip('xyz', translation + transform.apply(point)))
                body['pose']['r'] = dict(zip('xyzw', (transform * rotation).as_quat()))
        moved['geometry'] = geometry_snapshot(moved['native'], self.human_names, self.guitar_names)
        result = guide.measure(moved, 3. + 1/120.)
        for key in ('target_G_m', 'wrist_G_m', 'delta_G_m', 'rotation_error_rad',
                    'distance_m', 'angle_rad', 'position_score', 'orientation_score'):
            np.testing.assert_allclose(result[key], reference[key], atol=1e-14)
        self.assertEqual(result['ready'], reference['ready'])

    def test_wrist_motion_changes_errors_and_orientation_prior_without_guitar_motion(self):
        guide = self.guide()
        moved = copy.deepcopy(self.saved)
        guitar = moved['native']['guitar_body_states'][self.guitar_names.index('guitar')]
        wrist = moved['native']['human_body_states'][self.human_names.index('L_Wrist')]
        _, gr = frame(guitar)
        wp, wr = frame(wrist)
        wrist['pose']['p'] = dict(zip('xyz', wp + gr.apply([.06, 0., 0.])))
        wrist['pose']['r'] = dict(zip('xyzw', (wr * Rotation.from_rotvec([0., 0., .7])).as_quat()))
        result = guide.measure(moved, 0.)
        np.testing.assert_allclose(result['delta_G_m'], [-.06, 0., 0.], atol=1e-14)
        self.assertAlmostEqual(result['distance_m'], .06)
        self.assertAlmostEqual(result['angle_rad'], .7)
        self.assertAlmostEqual(result['position_score'], np.exp(-1.))
        self.assertAlmostEqual(result['orientation_score'], np.exp(-(.7/.6)**2))
        self.assertFalse(result['ready'])

    def test_changed_manifest_sha_or_bytes_rejected(self):
        self.bundle()
        manifest = json.loads((self.root / 'manifest.json').read_text())
        for field, value in (('bytes', 0), ('sha256', '0' * 64)):
            with self.subTest(field=field):
                damaged = copy.deepcopy(manifest)
                damaged['files']['training/hand_position_targets.json'][field] = value
                (self.root / 'manifest.json').write_text(json.dumps(damaged))
                with self.assertRaisesRegex(ValueError, 'fingerprint'):
                    load_anchor_track(self.root)

    def test_validly_hashed_invalid_schema_frame_time_or_anchor_rejected(self):
        self.bundle()
        valid = json.loads((self.root / 'training/hand_position_targets.json').read_text())
        cases = [('schema', 'other'), ('coordinate_frame', 'world'), ('frames', [])]
        for key, value in cases:
            with self.subTest(key=key):
                damaged = copy.deepcopy(valid)
                damaged[key] = value
                self.write_document(damaged)
                with self.assertRaises(ValueError):
                    load_anchor_track(self.root)
        for key, value in (('frame', True), ('frame', 3), ('t', .1), ('t', float('nan')),
                           ('anchor_fret', 0), ('anchor_fret', 23),
                           ('anchor_fret', float('inf')), ('anchor_fret', True)):
            with self.subTest(key=key, value=value):
                damaged = copy.deepcopy(valid)
                damaged['frames'][0][key] = value
                self.write_document(damaged)
                with self.assertRaises(ValueError):
                    load_anchor_track(self.root)

    def test_changed_local_geometry_or_stale_geometry_step_rejected(self):
        guide = self.guide()
        moved = copy.deepcopy(self.saved)
        moved['geometry']['fret_markers_G_m'][5][1] += .001
        with self.assertRaisesRegex(ValueError, 'geometry changed'):
            guide.measure(moved, 0.)
        moved = copy.deepcopy(self.saved)
        moved['geometry']['physics_step'] += 1
        with self.assertRaisesRegex(ValueError, 'physics steps'):
            guide.measure(moved, 0.)

    def test_supported_song_tracks_verified_and_metadata_has_no_floating_reset_pose(self):
        for name in ('02_Jazz1-200-B_solo', '03_Rock1-130-A_solo', '05_BN1-129-Eb_solo',
                     '05_BN2-131-B_solo', '05_Rock2-142-D_solo'):
            with self.subTest(song=name):
                track = load_anchor_track(BUNDLE.parent / name)
                self.assertTrue(track['anchors'])
                self.assertIn('wrist_pos_guitar', track['ignored_fields'])
        guide = self.guide()
        metadata = guide.metadata()
        self.assertTrue(metadata['ignored_legacy_wrist_offsets'])
        self.assertNotIn('reference_wrist', metadata)
        self.assertNotIn('reference_rotation', metadata)
        json.dumps(metadata, allow_nan=False)


if __name__ == '__main__':
    unittest.main()
