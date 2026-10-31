"""Current code pins and historical proof pins retain separate SHA contracts."""
import hashlib
from pathlib import Path
import tempfile
import unittest

from guitar_learning.native import paths as common
from guitar_learning.runtime import prepared_reset_v1
from guitar_learning.training.training_log_io import digest
from guitar_learning.core.dependency_inputs import pin_evidence
from guitar_learning.historical_inputs import fingerprint_paths


class EvidencePinTests(unittest.TestCase):
    def test_changed_evidence_between_validation_and_pin_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder)/'evidence.json'
            source.write_text('original')
            expected = fingerprint_paths([source])
            def change_at_pin(config, extra):
                source.write_text('changed after proof validation')
                return fingerprint_paths(extra)
            with self.assertRaisesRegex(RuntimeError, 'physical evidence changed'):
                pin_evidence(change_at_pin, None, (), expected)

    def test_wrong_physical_pin_is_rejected_even_if_original_bytes_are_restored(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder)/'evidence.json'
            source.write_text('original')
            expected = fingerprint_paths([source])
            def pin(config, extra):
                source.write_text('temporary change')
                pins = fingerprint_paths(extra)
                source.write_text('original')
                return pins
            with self.assertRaisesRegex(RuntimeError, 'physical evidence changed'):
                pin_evidence(pin, None, (), expected)
            self.assertEqual(fingerprint_paths(expected), expected)

    def test_original_config_proof_pins_the_identical_internal_copy(self):
        from guitar_learning.native.paths import original_input_path
        original = str(original_input_path(prepared_reset_v1.BASELINE_CONFIG))
        expected = {original: digest(prepared_reset_v1.BASELINE_CONFIG)}
        result = pin_evidence(common.pin, None, (), expected)
        self.assertEqual(result[str(prepared_reset_v1.BASELINE_CONFIG)], expected[original])
        self.assertNotIn(original, result)

    def test_live_input_audit_rejects_historical_sha_for_changed_current_code(self):
        root = Path(__file__).resolve().parents[2]
        source = root/'guitar_learning/music_task.py'
        backup = root/'guitar_learning/archive/20261019_before_dependency_internalization/music_task.py'
        expected = {str(source): hashlib.sha256(backup.read_bytes()).hexdigest()}
        self.assertEqual(fingerprint_paths(expected), expected)
        with self.assertRaisesRegex(RuntimeError, 'live input SHA mismatch'):
            common.verify({str(root/'guitar_learning/song/task.py'): expected[str(source)]})


if __name__ == '__main__':
    unittest.main()
