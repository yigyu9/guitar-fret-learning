"""Regression for the actual contract's NumPy reset-reference serialization."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from guitar_learning.runtime.prepared_reset_v1 import load_gpu_prepared_reset_contract
from guitar_learning.tool.experiments.right_strike_io_v2 import write


class SnapshotIOTests(unittest.TestCase):
    def test_io_override_is_restored_when_probe_raises(self):
        import os
        from guitar_learning.tool.experiments.right_strike import native_probe
        from guitar_learning.tool.experiments.right_strike_io_v2.__main__ import main
        original = native_probe.write
        def fail(*args):
            self.assertIs(native_probe.write, write)
            raise RuntimeError('fixture native failure')
        with patch.dict(os.environ), patch('sys.argv', ['io-v2', 'probe', '--manifest', '/tmp/m.json', '--out', '/tmp/out']), \
             patch('guitar_learning.tool.experiments.right_strike_io_v2.__main__.verify_manifest'), \
             patch.object(native_probe, 'run', side_effect=fail):
            with self.assertRaisesRegex(RuntimeError, 'fixture native failure'):
                main()
        self.assertIs(native_probe.write, original)

    def test_actual_prepared_contract_roundtrip_preserves_numeric_values(self):
        value = load_gpu_prepared_reset_contract('right')
        value['test_scalar'] = np.float32(.125)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'arrival.json'
            write(path, value)
            result = json.loads(path.read_text())
            np.testing.assert_array_equal(result['target105'], value['target105'])
            self.assertEqual(result['state'], value['state'])
            self.assertEqual(result['test_scalar'], .125)
            with self.assertRaises(FileExistsError):
                write(path, value)

    def test_invalid_numbers_rejected_before_creating_output(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'invalid.json'
            with self.assertRaises(ValueError):
                write(path, dict(q=np.array([float('nan')])))
            self.assertFalse(path.exists())


if __name__ == '__main__':
    unittest.main()
