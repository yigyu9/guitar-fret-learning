import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location('pc1_inspection', Path(__file__).resolve().parents[1] / 'inspect_inputs.py')
inspection = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inspection)


class InspectionTests(unittest.TestCase):
    def test_committed_boundaries(self):
        self.assertTrue(inspection.check_boundary(128, 4194304)['resume_boundary'])
        self.assertFalse(inspection.check_boundary(512, 16777216)['resume_boundary'])
        self.assertTrue(inspection.check_boundary(512, 16777216)['evaluation_boundary'])
        self.assertFalse(inspection.check_boundary(129, 129 * 32768)['evaluation_boundary'])
        for updates, transitions in ((True, 32768), (513, 513 * 32768), (128, 4194305)):
            with self.assertRaises(ValueError):
                inspection.check_boundary(updates, transitions)

    def test_profile_difference_allowlist_is_exact(self):
        def settings(profile):
            preparation = profile == 'preparation'
            return dict(compact_press=dict(improvement_profile=profile), compact_press_v5=dict(
                profile=profile, preparation=dict(enabled=preparation, factor='P' if preparation else 'B')),
                ppo=dict(epochs=2))
        left, right = settings('corrected'), settings('preparation')
        self.assertEqual(set(inspection.check_profile_diff(left, right)), inspection.PROFILE_DIFFS)
        right['ppo']['epochs'] = 3
        with self.assertRaises(ValueError):
            inspection.check_profile_diff(left, right)
        with self.assertRaises(ValueError):
            inspection.check_profile_diff(left, left)


if __name__ == '__main__':
    unittest.main()
