"""Prepared reset and native evidence work with the original tree inaccessible."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from guitar_learning.native import paths
from guitar_learning.runtime import prepared_reset_v1

ROOT = Path(__file__).resolve().parents[2]


class PortableNativeInputTests(unittest.TestCase):
    def test_prepared_snapshots_are_internal_regular_files_with_original_sha(self):
        for path, expected in prepared_reset_v1.SOURCE_SHA256.items():
            self.assertTrue(paths.ASSETS in path.parents)
            self.assertFalse(path.is_symlink())
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected)
        manifest = json.loads(paths.PROVENANCE.read_text())
        self.assertTrue(all(not Path(row['internal']).is_absolute()
                            for row in manifest['files'] + manifest['generated_files']))

    def test_relocated_inputs_keep_historical_identity_without_original_tree_access(self):
        with tempfile.TemporaryDirectory(prefix='Tab2Body moved ') as folder:
            moved = Path(folder)
            shutil.copytree(ROOT / 'guitar_learning', moved / 'guitar_learning',
                            ignore=lambda directory, names: [name for name in names
                                if name == '__pycache__' or (name == 'archive'
                                    and Path(directory) == ROOT / 'guitar_learning')])
            code = r'''
import json, os, sys
from pathlib import Path
origin = '/home/ajou/yigyu/3/'

def deny_external(event, args):
    if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
        path = os.path.abspath(os.fsdecode(args[0]))
        if path.startswith((origin, '/media/ajou/')):
            raise AssertionError('read external original: ' + path)

sys.addaudithook(deny_external)
from guitar_learning.native import paths
from guitar_learning.runtime import prepared_reset_v1 as reset
from guitar_learning import historical_inputs
from guitar_learning.core.dependency_inputs import parity_errors
root = Path(sys.argv[1])
assert paths.ROOT == root
assert not (root / 'docs').exists()
contract = reset.load_prepared_reset_contract()
inputs = reset.prepared_input_paths()
assert all(root in path.parents and path.is_file() for path in inputs)
assert len(contract['target105']) == 105
for asset in contract['initial']['loaded_assets']:
    assert root in Path(asset['path']).parents
original = paths.HISTORICAL_ROOT / 'tab2body/assets/smpl_mpl_hands_body.xml'
assert paths.resolve_input_path(original) == paths.HUMAN
assert paths.original_input_path(paths.HUMAN) == original
assert parity_errors([paths.HUMAN], {str(original): paths.sha(paths.HUMAN)}) == []
source = str(paths.HISTORICAL_ROOT / 'tab2body/full/events.py')
sha = historical_inputs._index()[source]['default_sha256']
assert historical_inputs.fingerprint_paths({source: sha}) == {source: sha}
assert historical_inputs.fingerprint_paths([root / 'tab2body/full/events.py']) == {source: sha}
unknown = root / 'tab2body/no_internal_copy.xml'
try:
    paths.resolve_input_path(unknown)
except FileNotFoundError:
    pass
else:
    raise AssertionError('unregistered legacy path accepted')
pins = paths.pin(reset.BASELINE_CONFIG, extra=inputs)
assert paths.verify(pins)
assert paths.verify_provenance()['verified_files'] > 180
# Preserved SHA checks must still reject changed bytes after relocation.
reset.INITIAL_VALUES.write_bytes(b'tampered')
try:
    paths.verify_provenance()
except ValueError as error:
    assert 'SHA mismatch' in str(error)
else:
    raise AssertionError('changed prepared input accepted')
print(json.dumps({'prepared_inputs': len(inputs), 'original_tree_denied': True}))
'''
            env = dict(os.environ, PYTHONPATH=str(moved), PYTHONDONTWRITEBYTECODE='1')
            result = subprocess.run([sys.executable, '-B', '-c', code, str(moved)],
                                    cwd='/tmp', env=env, capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)['original_tree_denied'])


if __name__ == '__main__':
    unittest.main()
