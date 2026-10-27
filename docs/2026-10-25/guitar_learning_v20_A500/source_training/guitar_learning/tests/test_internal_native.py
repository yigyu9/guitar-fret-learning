"""Migration boundaries preserve physical inputs and historical gate identity."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from guitar_learning.native import paths
from guitar_learning.native.lower_body_release_v1 import common
from guitar_learning.core.dependency_inputs import parity_errors

ROOT = Path(__file__).resolve().parents[2]
PROBE = Path(__file__).with_name('native_input_probe.py')


class InternalNativeTests(unittest.TestCase):
    def test_current_cpu_inputs_work_with_legacy_open_and_import_forbidden(self):
        environment = dict(os.environ, PYTHONPATH=str(ROOT))
        result = subprocess.run([sys.executable, str(PROBE)], cwd=ROOT, env=environment,
                                capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report['legacy_open_and_import_guards'])
        self.assertGreater(report['baseline_parity_files'], 100)
        self.assertLess(report['fk_max_position_error_m'], 1e-12)
        self.assertGreater(report['solver_inputs'], 2)

    def test_known_models_resolve_internally_and_unknown_legacy_input_fails(self):
        original = ROOT/'tab2body/assets/smpl_mpl_hands_body.xml'
        self.assertEqual(paths.resolve_input_path(original), common.HUMAN)
        self.assertEqual(paths.original_input_path(common.HUMAN), original)
        unknown = ROOT/'tab2body/not_a_registered_runtime_input.xml'
        with self.assertRaisesRegex(FileNotFoundError, 'no internal copy'):
            paths.resolve_input_path(unknown)
        self.assertEqual(paths.rebase_paths({'historical_identity': str(unknown)}),
                         {'historical_identity': str(unknown)})

    def test_extra_historical_source_keeps_original_key_and_original_sha(self):
        original = ROOT/'stability_adapter_2/lower_body_release_v1/scene_v8.py'
        internal = paths.resolve_input_path(original)
        row = next(row for row in paths.provenance_records() if row['original'] == str(original))
        pins = common.pin(extra=[original])
        self.assertEqual(pins[str(original)], row['original_sha256'])
        self.assertEqual(pins[str(internal)], row['internal_sha256'])
        self.assertNotEqual(pins[str(original)], pins[str(internal)])
        self.assertNotIn(str(paths.A/'assets/humanoid_fixed_lower.xml'), pins)
        self.assertTrue(common.verify(pins))

    def test_provenance_rehashes_current_bytes_and_rejects_tampering(self):
        with tempfile.TemporaryDirectory() as folder:
            current = Path(folder)/'native.py'
            current.write_text('original bytes\n')
            manifest = Path(folder)/'manifest.json'
            manifest.write_text(json.dumps({'files': [], 'generated_files': [
                {'internal': str(current), 'internal_sha256': hashlib.sha256(current.read_bytes()).hexdigest()}]}))
            with patch.object(paths, 'PROVENANCE', manifest):
                self.assertEqual(paths.verify_provenance()['verified_files'], 1)
                current.write_text('changed bytes\n')
                with self.assertRaisesRegex(ValueError, 'provenance SHA mismatch'):
                    paths.verify_provenance()

    def test_original_model_sha_remains_required_after_path_migration(self):
        original = str(paths.original_input_path(common.HUMAN))
        self.assertEqual(parity_errors([str(common.HUMAN)], {original: common.sha(common.HUMAN)}), [])
        self.assertEqual(parity_errors([str(common.HUMAN)], {original: '0'*64}), [str(common.HUMAN)])


if __name__ == '__main__':
    unittest.main()
