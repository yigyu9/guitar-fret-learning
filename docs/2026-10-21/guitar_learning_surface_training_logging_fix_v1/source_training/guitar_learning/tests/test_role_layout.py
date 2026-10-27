"""Relocated entry points retain project roots and exact historical inputs."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from guitar_learning import historical_inputs
from guitar_learning.imitation import imitation_io
from guitar_learning.runtime import prepared_reset_v1

ROOT = Path(__file__).resolve().parents[2]


class RoleLayoutTests(unittest.TestCase):
    def test_nested_input_resolvers_keep_real_project_and_asset_roots(self):
        self.assertEqual(imitation_io.ROOT, ROOT)
        self.assertEqual(prepared_reset_v1.ROOT, ROOT)
        self.assertTrue(imitation_io.BUNDLE.is_dir())
        self.assertEqual(imitation_io.CONFIG, prepared_reset_v1.BASELINE_CONFIG)
        self.assertTrue(imitation_io.CONFIG.is_file())
        paths = prepared_reset_v1.prepared_input_paths()
        self.assertTrue(paths)
        self.assertTrue(all(p.is_file() for p in paths))
        self.assertTrue(any('/guitar_learning/assets/' in str(p) for p in paths))

    def test_before_move_inputs_verify_without_reading_removed_paths_or_archive(self):
        backup = ROOT/'guitar_learning/archive/20261020_before_role_layout'
        records = json.loads((backup/'manifest.json').read_text())['files']
        expected = {row['original']: row['sha256'] for row in records}
        original_open = Path.open

        def deny_original(path, *args, **kwargs):
            if ((str(path) in expected and path != historical_inputs._STORE/'index.json')
                    or '/guitar_learning/archive/' in str(path)):
                raise AssertionError('old proof read a live or archived implementation')
            return original_open(path, *args, **kwargs)

        with patch.object(Path, 'open', deny_original):
            self.assertEqual(historical_inputs.fingerprint_paths(expected), expected)
        current = Path(imitation_io.__file__).resolve()
        sha = hashlib.sha256(current.read_bytes()).hexdigest()
        self.assertEqual(historical_inputs.fingerprint_paths([current]), {str(current): sha})
        self.assertFalse((ROOT/'guitar_learning/imitation_io.py').exists())

    def test_role_cli_modules_work_outside_project_working_directory(self):
        environment = dict(os.environ, PYTHONPATH=str(ROOT), PYTHONDONTWRITEBYTECODE='1')
        for module in ('guitar_learning.tool.demonstration.capture_imitation',
                       'guitar_learning.tool.training.train_imitation_ppo_v2',
                       'guitar_learning.tool.training.train_timing',
                       'guitar_learning.tool.training.train_specialists',
                       'guitar_learning.tool.evaluation.evaluate_musical_quality'):
            with self.subTest(module=module):
                result = subprocess.run([sys.executable, '-B', '-m', module, '--help'],
                                        cwd='/tmp', env=environment, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('usage:', result.stdout)


if __name__ == '__main__':
    unittest.main()
