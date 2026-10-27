"""CPU checks only: selection, frame coverage and saved poses; never import GL."""
import copy
import json
from pathlib import Path
import sys
import unittest

import numpy as np

PHASE = Path(__file__).resolve().parent
sys.path.insert(0, str(PHASE))
import render_probe as render


class RenderProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = PHASE/'probe_n4_retry02'
        cls.report = json.loads((cls.source/'report.json').read_text())
        cls.control = json.loads((cls.source/'control_contract.json').read_text())
        cls.metadata = json.loads((cls.source/'capture_metadata.json').read_text())
        cls.initial = json.loads((cls.source/'visual_initial.json').read_text())

    def test_selection_is_native_reference_room_only_and_tie_is_positive(self):
        selected = render.select_trials(self.report, self.control)
        self.assertEqual([r['trial']['joint'] for r in selected], list(render.JOINTS))
        paths = [r['trial']['path'] for r in selected]
        mutated = copy.deepcopy(self.report)
        for i, row in enumerate(mutated['trials']):
            row['audit']['actual_range_rad'] = 1000-i
        self.assertEqual([r['trial']['path'] for r in render.select_trials(mutated, self.control)], paths)
        tied = copy.deepcopy(self.control)
        for choice in selected:
            native, action = choice['native_joint_index'], choice['action_index']
            tied['reference105_rad'][native] = 0.
            tied['action_lower_rad'][action], tied['action_upper_rad'][action] = -.1, .1
        self.assertTrue(all(r['trial']['amplitude'] == .2 for r in render.select_trials(self.report, tied)))

    def test_frame_segments_and_exact350_endpoints_exclude_initial_sentinels(self):
        stages = [render.segment(i) for i in range(1, 71)]
        self.assertEqual([stages.count(key) for key in ('push30', 'zero10', 'reverse30')], [30, 10, 30])
        self.assertEqual([stages[i] for i in (0, 29, 30, 39, 40, 69)],
                         ['push30', 'push30', 'zero10', 'zero10', 'reverse30', 'reverse30'])
        self.assertEqual(5*len(stages), 350)
        self.assertAlmostEqual(350/60., 5.833333333333333)
        for frame in (0, 71):
            with self.assertRaises(ValueError):
                render.segment(frame)

    def test_actual_selected_npz_audit_pose_order_and_string_endpoints_without_gl(self):
        self.assertNotIn('mujoco', sys.modules)
        for choice in render.select_trials(self.report, self.control):
            row = choice['trial']; path = self.source/row['path']
            self.assertEqual(render.sha(path), row['sha256'])
            with np.load(str(path), allow_pickle=False) as archive:
                arrays = {key: archive[key] for key in archive.files}
            self.assertEqual(render.audit_trace(arrays, self.control, row['joint'], row['amplitude']), row['audit'])
            self.assertEqual(arrays['body_state'].shape, (71, 106, 13))
            self.assertEqual(arrays['q'].shape, (71, 105))
            frame = arrays['body_state'][70]; before = frame.copy()
            state = render.pose_state(self.metadata['body_names'], frame, self.initial)
            flattened = [r for actor in ('human', 'guitar', 'chair') for r in state[actor+'_body_states']]
            restored = np.array([[r['pose']['p'][k] for k in 'xyz']+
                                 [r['pose']['r'][k] for k in 'xyzw'] for r in flattened])
            np.testing.assert_array_equal(restored, frame[:, :7])
            endpoints = render.string_endpoints(self.metadata['body_names'], frame)
            for i, pair in enumerate(endpoints, 1):
                for j, suffix in enumerate(('', '_end')):
                    np.testing.assert_array_equal(pair[j], frame[self.metadata['body_names'].index('guitar/G:string%d%s' % (i, suffix)), :3])
            np.testing.assert_array_equal(frame, before)
        self.assertNotIn('mujoco', sys.modules)

    def test_source_pins_and_all84_npz_sha_are_intact(self):
        pins = json.loads((self.source/'inputs_before.json').read_text())
        self.assertFalse([name for name, sha in pins.items() if render.sha(name) != sha])
        for row in self.report['trials']:
            self.assertEqual(render.sha(self.source/row['path']), row['sha256'])

    def test_incomplete_or_failed_probe_is_rejected(self):
        for field, value in (('passed', False), ('completed', False), ('physical_terminal_rows', 1)):
            report = copy.deepcopy(self.report); report[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                render.select_trials(report, self.control)
        report = copy.deepcopy(self.report); report['trials'].pop()
        with self.assertRaises(ValueError):
            render.select_trials(report, self.control)


if __name__ == '__main__':
    unittest.main(verbosity=2)
