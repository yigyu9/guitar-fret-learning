import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import live_geometry as live
import numpy as np


class LiveGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.capture = live.MULTI/'로그/실제시뮬영상_v1/capture'
        cls.raw = np.load(str(cls.capture/'poses_env0000.npz'), allow_pickle=False)
        cls.metadata = json.loads((cls.capture/'capture_metadata.json').read_text())
        cls.training = json.loads((cls.capture/'training_contract.json').read_text())
        cls.pins = json.loads((cls.capture/'inputs_before.json').read_text())
        cls.kwargs = dict(q105=cls.raw['q'][197].copy(), qd105=cls.raw['qd'][197].copy(),
            body_state=cls.raw['body_state'][197].copy(), joint_names=cls.metadata['joint_names'],
            body_names=cls.metadata['body_names'], training_contract=cls.training,
            physics_step=np.int64(792), pins=cls.pins)
        with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': 'cpu-test-marker',
                                    'OMP_NUM_THREADS': '7', 'MKL_NUM_THREADS': '5'}):
            before = {key: os.environ.get(key) for key in live._ENV_KEYS}
            cls.arrival, cls.case, cls.report = live.fit_snapshot(**cls.kwargs)
            cls.environment_restored = before == {key: os.environ.get(key) for key in live._ENV_KEYS}

    @classmethod
    def tearDownClass(cls):
        cls.raw.close()

    def test_import_is_lazy_and_does_not_change_visibility(self):
        program = "import os,sys;sys.path.insert(0,sys.argv[1]);os.environ['CUDA_VISIBLE_DEVICES']='visible-marker';import live_geometry;assert os.environ['CUDA_VISIBLE_DEVICES']=='visible-marker';assert 'torch' not in sys.modules;assert 'isaacgym' not in sys.modules;assert 'numpy' not in sys.modules"
        subprocess.run([sys.executable, '-c', program, str(TOOLS)], check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertTrue(self.environment_restored)

    def test_actual_fixture_has_same_positive_finger8_candidate(self):
        self.assertEqual(self.report['classification'], 'geometry_candidate')
        self.assertTrue(self.report['both_geometry'])
        self.assertFalse(self.report['native_verified'])
        self.assertEqual(self.report['actual_physics_step'], 792)
        self.assertLess(self.report['fk_reproduction']['max_position_error_m'], 1e-12)
        self.assertLess(self.report['fk_reproduction']['max_rotation_error_rad'], 1e-12)
        old = json.loads((live.MULTI/'미동작_원인검증_v2/로그/arrival_geometry/report.json').read_text())
        np.testing.assert_allclose(self.report['q105'], old['attempts'][0]['fit']['q105'], atol=1e-10, rtol=0)
        self.assertLessEqual(self.report['nfev'], 60)

    def test_nonassigned_97_axes_and_caller_input_are_unchanged(self):
        fixed = sorted(set(range(105))-set(self.report['assigned_indices']))
        np.testing.assert_array_equal(np.array(self.report['q105'])[fixed], self.kwargs['q105'][fixed])
        np.testing.assert_array_equal(self.kwargs['q105'], self.raw['q'][197])
        np.testing.assert_array_equal(self.kwargs['body_state'], self.raw['body_state'][197])
        self.assertEqual(self.pins, self.kwargs['pins'])
        self.assertTrue(self.report['nonassigned_q_preserved'])

    def test_wrong_order_and_nonunit_body_pose_are_rejected(self):
        for key in ('joint_names', 'body_names'):
            kwargs = copy.deepcopy(self.kwargs)
            kwargs[key][0:2] = reversed(kwargs[key][0:2])
            with self.assertRaises(ValueError):
                live.fit_snapshot(**kwargs)
        kwargs = copy.deepcopy(self.kwargs)
        kwargs['body_state'][66, 6] = 2.
        with self.assertRaises(ValueError):
            live.fit_snapshot(**kwargs)

    def test_wrong_task_and_source_sha_are_rejected(self):
        kwargs = copy.deepcopy(self.kwargs)
        kwargs['training_contract']['task']['provenance']['song']['schedule'][1]['fret'] = 7
        with self.assertRaises(ValueError):
            live.fit_snapshot(**kwargs)
        kwargs = copy.deepcopy(self.kwargs)
        first = next(iter(kwargs['pins']))
        kwargs['pins'][first] = '0'*64
        with self.assertRaises(ValueError):
            live.fit_snapshot(**kwargs)

    def test_nonfinite_missing_shapes_and_unbounded_budget_are_rejected(self):
        for key, value in [('q105', [0.]*104), ('physics_step', True), ('physics_step', -1),
                           ('max_nfev', 61), ('max_nfev', True), ('height', -.0011),
                           ('height', float('nan')), ('pins', {})]:
            kwargs = dict(self.kwargs)
            kwargs[key] = value
            with self.assertRaises(ValueError):
                live.fit_snapshot(**kwargs)
        kwargs = copy.deepcopy(self.kwargs)
        kwargs['qd105'][0] = np.nan
        with self.assertRaises(ValueError):
            live.fit_snapshot(**kwargs)

    def test_small_budget_is_classified_without_physical_impossibility_claim(self):
        kwargs = dict(self.kwargs)
        kwargs['max_nfev'] = 1
        _, _, report = live.fit_snapshot(**kwargs)
        self.assertEqual(report['classification'], 'no_candidate')
        self.assertFalse(report['both_geometry'])
        self.assertFalse(report['native_verified'])
        self.assertEqual(report['physical_steps_executed'], 0)

    def test_positive_hover_height_is_rejected_by_press_helper(self):
        for height in (.000001, .001, .003):
            kwargs = dict(self.kwargs)
            kwargs['height'] = height
            with self.assertRaisesRegex(ValueError, 'press height'):
                live.fit_snapshot(**kwargs)

    def test_json_output_and_raw_snapshot_fingerprint(self):
        json.dumps([self.arrival, self.case, self.report], allow_nan=False)
        payload = dict(joint_names=self.kwargs['joint_names'], body_names=self.kwargs['body_names'],
            q105=self.kwargs['q105'].astype(float).tolist(),
            qd105=self.kwargs['qd105'].astype(float).tolist(),
            body_state=self.kwargs['body_state'].astype(float).tolist(), physics_step=792)
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True,
            separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()
        self.assertEqual(digest, self.arrival['snapshot_content_sha256'])
        self.assertEqual(digest, self.report['snapshot_content_sha256'])


if __name__ == '__main__':
    unittest.main()
