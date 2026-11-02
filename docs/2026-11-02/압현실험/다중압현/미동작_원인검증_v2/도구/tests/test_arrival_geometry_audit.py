import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import arrival_geometry_audit as audit
import numpy as np


class ActualArrivalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.arrival = json.loads((audit.STUDY/'입력/arrival_native_t3p30.json').read_text())
        cls.case = json.loads((audit.STUDY/'입력/arrival_case.json').read_text())
        cls.contract = audit.load_gpu_prepared_reset_contract('left')
        cls.metadata = json.loads((audit.CAPTURE/'capture_metadata.json').read_text())
        cls.training = json.loads((audit.CAPTURE/'training_contract.json').read_text())
        cls.raw = np.load(str(audit.CAPTURE/'poses_env0000.npz'), allow_pickle=False)
        cls.planner = audit.CommonPose(cls.case, cls.arrival)
        cls.report = json.loads((audit.STUDY/'로그/arrival_geometry/report.json').read_text())

    @classmethod
    def tearDownClass(cls):
        cls.raw.close()

    def test_actual_endpoint_identity_and_fk_reproduction(self):
        arrival, case, endpoint = audit.make_arrival(self.raw, self.metadata, self.training,
            self.contract, self.arrival['source_sha256'])
        self.assertEqual(endpoint, 197)
        self.assertEqual(arrival['physics_step'], 792)
        self.assertEqual(arrival['source_time_s'], 3.3)
        self.assertEqual(arrival['q105'], self.raw['q'][197].astype(float).tolist())
        self.assertEqual(case, self.case)
        result = audit.native_reproduction(self.planner, arrival)
        self.assertLess(result['max_position_error_m'], 1e-12)
        self.assertLess(result['max_rotation_error_rad'], 1e-12)

    def test_swapped_names_and_nonunit_quaternion_are_rejected(self):
        metadata = copy.deepcopy(self.metadata)
        metadata['body_names'][0:2] = reversed(metadata['body_names'][0:2])
        with self.assertRaises(ValueError):
            audit.make_arrival(self.raw, metadata, self.training,
                               self.contract, self.arrival['source_sha256'])
        arrival = copy.deepcopy(self.arrival)
        arrival['state']['guitar_body_states'][0]['pose']['r']['w'] = 2.
        with self.assertRaises(ValueError):
            audit.validate_arrival(arrival, self.case, self.contract)

    def test_q_state_mismatch_and_reset_clock_are_rejected(self):
        arrival = copy.deepcopy(self.arrival)
        arrival['q105'][56] += .01
        with self.assertRaises(ValueError):
            audit.validate_arrival(arrival, self.case, self.contract)
        raw = {key: self.raw[key].copy() for key in self.raw.files}
        raw['physics_step'][100] = 4
        with self.assertRaises(ValueError):
            audit.make_arrival(raw, self.metadata, self.training,
                               self.contract, self.arrival['source_sha256'])

    def test_wrong_target_pair_and_nonrecorded_endpoint_are_rejected(self):
        training = copy.deepcopy(self.training)
        training['task']['provenance']['song']['schedule'][1]['fret'] = 7
        with self.assertRaises(ValueError):
            audit.make_arrival(self.raw, self.metadata, training,
                               self.contract, self.arrival['source_sha256'])
        with self.assertRaises(ValueError):
            audit.make_arrival(self.raw, self.metadata, self.training,
                               self.contract, self.arrival['source_sha256'], target_time=3.301)

    def test_numpy_distance_matches_unmodified_contact_function(self):
        import torch
        from guitar_learning.gpu.contact import pad_target_geometry
        planner = self.planner
        for q in (planner.q0, np.asarray(self.report['attempts'][0]['fit']['q105'])):
            count = planner.pad['points_local'].shape[1]
            points = np.zeros((1, 4, count, 3))
            for k, (surface, _) in enumerate(planner.samples(q)):
                finger = planner.rows[k]['finger_id']-1
                points[0, finger, planner.pad['valid'][finger]] = surface
            values = pad_target_geometry(torch.tensor(points), torch.zeros_like(torch.tensor(points)),
                torch.zeros_like(torch.tensor(points)), torch.tensor(planner.pad['valid']),
                torch.tensor(planner.starts[None]), torch.tensor((planner.starts+planner.lines)[None]),
                torch.tensor((planner.low-.002)[None]), torch.tensor((planner.high+.002)[None]),
                torch.tensor([2, 1]), torch.tensor([1, 2]), torch.zeros(1, 4, dtype=torch.bool),
                torch.tensor(np.r_[planner.normal, planner.d]))
            expected = np.array([row['minimum_distance_m'] for row in audit.finite_distances(planner, q)])
            np.testing.assert_allclose(values['distance'].numpy()[0], expected, rtol=0, atol=1e-12)
        self.assertFalse(torch.cuda.is_initialized())

    def test_fixed_arm_candidate_preserves_other_axes_and_is_geometric_only(self):
        candidate = np.asarray(self.report['attempts'][0]['fit']['q105'])
        fixed = sorted(set(range(105))-set(self.planner.finger))
        np.testing.assert_array_equal(candidate[fixed], self.planner.q0[fixed])
        self.assertTrue(all(row['geometry_candidate']
                            for row in self.planner.measure(candidate, -.0005)))
        self.assertFalse(self.report['attempts'][0]['fit']['native_verified'])
        self.assertEqual(self.report['physics_steps_executed'], 0)

    def test_source_pins_match_and_both_distances_exceed_53mm(self):
        audit.verify(self.report['source_sha256'])
        for row in audit.finite_distances(self.planner, self.planner.q0):
            self.assertGreater(row['minimum_distance_m'], .053)
            self.assertLess(row['minimum_distance_m'], .054)


if __name__ == '__main__':
    unittest.main()
