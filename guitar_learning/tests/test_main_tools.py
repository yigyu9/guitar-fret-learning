"""Tool separation preserves runnable imports, shared evidence and core isolation."""
import ast
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT/'guitar_learning'


class MainToolsTests(unittest.TestCase):
    def test_every_internal_import_base_has_a_current_module(self):
        from guitar_learning.training.recording import active_source_paths
        files = active_source_paths(PACKAGE)
        modules = {}
        for path in files:
            parts = list(path.relative_to(ROOT).with_suffix('').parts)
            if parts[-1] == '__init__': parts.pop()
            modules['.'.join(parts)] = path
        for name, path in modules.items():
            package = name if path.name == '__init__.py' else name.rsplit('.', 1)[0]
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node, ast.ImportFrom):
                    base = importlib.util.resolve_name('.'*node.level+(node.module or ''), package) if node.level else node.module
                    names = [base]
                elif isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                else: continue
                for target in names:
                    if target and target.startswith('guitar_learning'):
                        self.assertIn(target, modules, (str(path), node.lineno, target))

    def test_source_census_never_enters_archive(self):
        from guitar_learning.training.recording import active_source_paths
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'main.py').write_text('')
            (root/'archive').mkdir()
            (root/'archive'/'old.py').write_text('')
            (root/'shared').mkdir()
            (root/'shared'/'core.py').write_text('')
            original = Path.iterdir
            def guarded(path):
                if 'archive' in path.parts:
                    raise OSError('archived storage unavailable')
                return original(path)
            with patch.object(Path, 'iterdir', guarded):
                self.assertEqual(active_source_paths(root),
                                 {root/'main.py', root/'shared'/'core.py'})

    def test_default_settings_and_worker_import_without_any_tool_package(self):
        script = '''
import importlib.abc, sys, types
class Guard(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'guitar_learning.tool' or fullname.startswith('guitar_learning.tool.'):
            raise AssertionError('default learning imported an auxiliary tool: '+fullname)
sys.meta_path.insert(0, Guard())
sys.modules['isaacgym'] = types.ModuleType('isaacgym')
from guitar_learning.training.start import settings_document
from guitar_learning.song.runtime import native_environment
from guitar_learning.skills.specialist_policy import SpecialistPolicy
settings = settings_document()
assert settings['specialist']['role'] == 'left'
assert settings['finger_skill']['schema'] == 'guitar_learning.finger_skill.v2'
from guitar_learning.training import finger_skill_runner
assert native_environment.__module__ == 'guitar_learning.song.runtime'
assert not any(n == 'guitar_learning.tool' or n.startswith('guitar_learning.tool.') for n in sys.modules)
'''
        result = subprocess.run([sys.executable, '-B', '-c', script], cwd='/tmp',
            env=dict(os.environ, PYTHONPATH=str(ROOT), PYTHONDONTWRITEBYTECODE='1'),
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)

    def test_fresh_case_census_includes_main_sources_after_nested_move(self):
        from guitar_learning.tool.experiments.contact_recovery.run import _fresh
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            settings, protocol = folder/'settings.json', folder/'protocol.json'
            settings.write_text('{}'); protocol.write_text('{}')
            out = folder/'out'
            result = _fresh({}, SimpleNamespace(out=out, settings=settings,
                protocol=protocol, checkpoint=None, mode='collect'), dict(cases=[]))
            pins = json.loads((out/'inputs_before.json').read_text())
            self.assertTrue(result['completed'])
            for path in ('train.py', 'training/runner.py', 'quality/runtime.py',
                         'native/paths.py', 'tool/experiments/contact_recovery/run.py'):
                self.assertIn(str(PACKAGE/path), pins)
            self.assertFalse(any('/archive/' in name for name in pins))


if __name__ == '__main__':
    unittest.main()
