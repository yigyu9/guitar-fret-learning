"""Tool separation preserves runnable imports, shared evidence and core isolation."""
import ast
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT/'guitar_learning'


class MainToolsTests(unittest.TestCase):
    def test_every_internal_import_base_has_a_current_module(self):
        from guitar_learning.training.training_log_io import active_source_paths
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
        from guitar_learning.training.training_log_io import active_source_paths
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

    def test_default_settings_resolve_v5_without_retired_compact_modules(self):
        script = """
import importlib.abc, sys, types
class Guard(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in ('guitar_learning.tool.experiments.compact_press',
                        'guitar_learning.tool.experiments.compact_press_v3',
                        'guitar_learning.tool.experiments.compact_press_v4'):
            raise AssertionError('default learning imported retired CLI: '+fullname)
sys.meta_path.insert(0, Guard())
sys.modules['isaacgym'] = types.ModuleType('isaacgym')
from guitar_learning.training.launch import settings_document
from guitar_learning.song.runtime import native_environment
settings = settings_document()
assert settings['specialist']['role'] == 'left'
assert settings['compact_press']['schema'] == 'guitar_learning.compact_press.v5'
assert settings['song_training']['observation_dimension'] == 464
assert native_environment.__module__ == 'guitar_learning.song.runtime'
"""
        result = subprocess.run([sys.executable, '-B', '-c', script], cwd='/tmp',
            env=dict(os.environ, PYTHONPATH=str(ROOT), PYTHONDONTWRITEBYTECODE='1'),
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)


if __name__ == '__main__':
    unittest.main()
