"""KL 보호만 독립 조건으로 넘기며 입력·정리 오류를 숨기지 않는지 검사한다."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
spec = importlib.util.spec_from_file_location('continuation', Path(__file__).with_name('continue_study.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class GuardTests(unittest.TestCase):
    def check(self, *, kind='KLGuardError', missing=(), lifecycle=True, cleanup=()):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            job = out/'jobs/H128_s7_u25_train'
            (job/'J').mkdir(parents=True)
            report = dict(failure=dict(type=kind), missing_import_pins=list(missing),
                          changed_inputs=[], cleanup_errors=list(cleanup),
                          lifecycle_verified=lifecycle, optimizer_updates=3)
            (job/'J/report.json').write_text(json.dumps(report))
            (job/'report.json').write_text(json.dumps(dict(failure=dict(type=kind))))
            state = dict(interpretations=[])
            with patch.object(module.study, 'check_sources'), patch.object(module.study, 'progress'):
                return module.expected_kl_failure(state, out, 'H128', 7, 25)

    def test_clean_kl_failure_is_condition_local(self):
        self.assertTrue(self.check())

    def test_kl_with_missing_source_is_not_swallowed(self):
        self.assertFalse(self.check(missing=['changed_module.py']))

    def test_kl_with_unverified_lifecycle_is_not_swallowed(self):
        self.assertFalse(self.check(lifecycle=False))

    def test_kl_with_cleanup_failure_is_not_swallowed(self):
        self.assertFalse(self.check(cleanup=['native_scene_not_closed']))

    def test_other_failure_is_not_swallowed(self):
        self.assertFalse(self.check(kind='FloatingPointError'))


if __name__ == '__main__':
    unittest.main()
