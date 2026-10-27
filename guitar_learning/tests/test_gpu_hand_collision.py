"""The native bitmask rule and the complete pinned pair matrix."""
import copy
import itertools
import json
from pathlib import Path
import unittest

from guitar_learning.gpu.hand_collision import (
    FINGER_MASKS, SEGMENT_FINGER, left_hand_collision_properties,
    verify_external_filter_preservation)
from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract


class HandCollisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = load_prepared_reset_contract()['initial']['actual_shape_properties']

    def test_exactly_distinct_finger_pairs_change(self):
        original = copy.deepcopy(self.source['human'])
        changed, contract = left_hand_collision_properties(original)
        self.assertEqual(original, self.source['human'])
        rows = [(n, i, v) for n, vs in original.items() for i, v in enumerate(vs)]
        count = 0
        for (a, ai, av), (b, bi, bv) in itertools.combinations(rows, 2):
            old = (av['filter'] & bv['filter']) == 0
            new = (changed[a][ai]['filter'] & changed[b][bi]['filter']) == 0
            distinct = (a in SEGMENT_FINGER and b in SEGMENT_FINGER and
                        SEGMENT_FINGER[a] != SEGMENT_FINGER[b])
            self.assertEqual(new, True if distinct else old, (a, b))
            count += old != new
        self.assertEqual(count, 90)
        self.assertEqual(contract['enabled_distinct_finger_pairs'], 90)

    def test_every_other_shape_property_is_preserved(self):
        changed, _ = left_hand_collision_properties(self.source['human'])
        for name, values in self.source['human'].items():
            for old, new in zip(values, changed[name]):
                self.assertEqual({k: v for k, v in old.items() if k != 'filter'},
                                 {k: v for k, v in new.items() if k != 'filter'})

    def test_palm_arm_proxy_same_finger_exclusions_remain(self):
        changed, _ = left_hand_collision_properties(self.source['human'])
        for name in ('L_Elbow', 'L_Wrist', 'LH:palm', 'LH:thumb_pad'):
            for segment in SEGMENT_FINGER:
                self.assertNotEqual(changed[name][0]['filter'] & changed[segment][0]['filter'], 0)
        self.assertEqual(len(set(FINGER_MASKS.values())), 5)
        for finger in FINGER_MASKS:
            masks = [changed['LH:'+finger+str(s)][0]['filter'] for s in (1, 2, 3)]
            self.assertTrue(all(a & b for a, b in itertools.combinations(masks, 2)))

    def test_guitar_chair_right_hand_pairs_preserved(self):
        original = self.source['human']
        changed, _ = left_hand_collision_properties(original)
        manifest = Path(__file__).resolve().parents[1]/'assets/gpu_rigid_guitar_v1/manifest.json'
        external = [0] + [r['filter'] for r in json.loads(manifest.read_text())['shape_properties']]
        verify_external_filter_preservation(original, changed, external)
        for name in original:
            if name.startswith('RH:') or name.startswith('R_'):
                self.assertEqual(original[name], changed[name])

    def test_unknown_source_masks_and_missing_segments_are_rejected(self):
        changed = copy.deepcopy(self.source['human'])
        changed['LH:index1'][0]['filter'] = 0
        with self.assertRaises(ValueError):
            left_hand_collision_properties(changed)
        changed = copy.deepcopy(self.source['human'])
        changed['Pelvis'][0]['filter'] = 1 << 20
        with self.assertRaises(ValueError):
            left_hand_collision_properties(changed)

    def test_external_new_bits_or_changed_truth_are_rejected(self):
        original = self.source['human']
        changed, _ = left_hand_collision_properties(original)
        with self.assertRaises(ValueError):
            verify_external_filter_preservation(original, changed, [1 << 20])
        changed['LH:thumb1'][0]['filter'] |= 4096
        with self.assertRaises(ValueError):
            verify_external_filter_preservation(original, changed, [4096])


if __name__ == '__main__':
    unittest.main()
