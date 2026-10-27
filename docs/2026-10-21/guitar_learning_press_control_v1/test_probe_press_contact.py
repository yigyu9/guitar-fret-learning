"""CPU fixtures for raw-contact audit only; no native simulator or GL."""
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import probe_press_contact as probe


class PressContactProbeTests(unittest.TestCase):
    def fixture(self):
        buffer = probe.allocate(8, 2)
        for value in buffer.values():
            value.fill(0)
        arrays = {key: value[0] for key, value in buffer.items()}
        arrays['clock'][:] = np.arange(1, 9)
        arrays['global_physics_step'][:] = np.arange(101, 109)
        arrays['surface_sample'][:] = [6, 12]
        arrays['selected_body'][:] = [12, 14]
        arrays['selected_surface_G'][..., 1] = .5
        arrays['selected_surface_G'][..., 2] = .0103
        arrays['surface_delta'][..., 2] = -.001
        arrays['surface_distance'][:] = .001
        arrays['string_starts_G'][..., 2] = .0123
        arrays['string_ends_G'][..., 1] = 1
        arrays['string_ends_G'][..., 2] = .0123
        arrays['native_contact_force'][:, 2, 2] = .02
        arrays['body_loaded'][:, 0] = True
        arrays['candidate'][2:5, 0] = True
        arrays['contact_geometry'][:, 0] = True
        metadata = dict(surface_samples_per_body=3, finger_body_indices=list(range(10, 20)),
            target_fingers=[1, 2], target_strings=[0, 1], force_threshold_n=.01,
            press_surface=dict(plane_G=[0, 0, 1, -.0093]))
        return arrays, metadata

    def test_true_240hz_clock_selected_body_load_and_virtual_wire_are_distinct(self):
        arrays, metadata = self.fixture()
        result = probe.audit(arrays, metadata, dict(steps=2))
        self.assertEqual(result['samples'], 8)
        self.assertEqual(result['candidate_frames_per_note'], [3, 0])
        self.assertEqual(result['geometry_frames_per_note'], [8, 0])
        self.assertEqual(result['selected_body_loaded_frames_per_note'], [8, 0])
        np.testing.assert_allclose(result['virtual_wire_minus_press_goal_z_range_m'], [.003, .003], atol=1e-9)
        self.assertTrue(result['body_mapping_passed'])

    def test_clock_missing_frame_wrong_finger_and_wrong_body_rejected(self):
        for key, replacement in (('clock', 77), ('surface_sample', 0), ('selected_body', 19)):
            arrays, metadata = self.fixture()
            arrays[key][0] = replacement
            with self.subTest(key=key), self.assertRaises(ValueError):
                probe.audit(arrays, metadata, dict(steps=2))
        arrays, metadata = self.fixture()
        with self.assertRaisesRegex(ValueError, 'length'):
            probe.audit(arrays, metadata, dict(steps=1))

    def test_no_contact_is_valid_measurement_and_mismatched_load_is_not(self):
        arrays, metadata = self.fixture()
        arrays['native_contact_force'][:] = 0
        arrays['body_loaded'][:] = False
        arrays['candidate'][:] = False
        result = probe.audit(arrays, metadata, dict(steps=2))
        self.assertEqual(result['selected_body_loaded_frames_per_note'], [0, 0])
        arrays['body_loaded'][:, 0] = True
        with self.assertRaisesRegex(ValueError, 'load flag'):
            probe.audit(arrays, metadata, None)

    def test_wrong_press_goal_and_nonfinite_data_are_rejected(self):
        arrays, metadata = self.fixture()
        arrays['surface_delta'][..., 2] = .002  # Targets virtual wire, not press plane.
        with self.assertRaisesRegex(ValueError, 'press plane'):
            probe.audit(arrays, metadata, None)
        arrays, metadata = self.fixture()
        arrays['q_left21'][0, 0] = np.nan
        with self.assertRaisesRegex(ValueError, 'Nonfinite'):
            probe.audit(arrays, metadata, None)

    def test_capture_allocation_is_bounded_and_import_has_no_native_backend(self):
        buffers = probe.allocate(1969*4, 67)
        self.assertLess(sum(value.nbytes for value in buffers.values()), 110*1024**2)
        self.assertEqual(buffers['native_contact_force'].shape, (4, 7876, 11, 3))
        self.assertNotIn('isaacgym', sys.modules)
        self.assertNotIn('torch', sys.modules)
        self.assertNotIn('mujoco', sys.modules)


if __name__ == '__main__':
    unittest.main(verbosity=2)
