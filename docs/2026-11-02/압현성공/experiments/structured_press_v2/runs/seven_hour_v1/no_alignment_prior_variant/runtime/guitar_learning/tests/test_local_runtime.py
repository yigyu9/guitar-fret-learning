"""Local runtime integrity checks independent of Isaac Gym/GPU availability."""
import importlib.util
import json
import multiprocessing
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    'tab2body_runtime', Path(__file__).resolve().parents[2] / 'scripts/tab2body.py')
RUNTIME = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNTIME)


def prepare_in_process(source, cache, queue):
    try:
        path, digest = RUNTIME.prepare_runtime(Path(source), Path(cache))
        queue.put((str(path), digest))
    except Exception as error:
        queue.put(('error', str(error)))


class LocalRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.root / 'setup.py').write_text("setup(version='1.0.preview4')\n")
        (self.source / '__init__.py').write_text('VERSION = 1\n')
        (self.source / 'library.so').write_bytes(b'library bytes')
        (self.source / 'library_alias.so').symlink_to('library.so')
        self.cache = self.root / 'cache'

    def test_reuse_invalidation_and_tamper(self):
        first, sha = RUNTIME.prepare_runtime(self.source, self.cache)
        second, sha2 = RUNTIME.prepare_runtime(self.source, self.cache)
        self.assertEqual((first, sha), (second, sha2))
        self.assertTrue((first / 'isaacgym/library_alias.so').is_symlink())
        (self.source / '__init__.py').write_text('VERSION = 2\n')
        third, sha3 = RUNTIME.prepare_runtime(self.source, self.cache)
        self.assertNotEqual(sha, sha3)
        self.assertNotEqual(first, third)
        (third / 'isaacgym/library.so').write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError, 'failed SHA verification'):
            RUNTIME.prepare_runtime(self.source, self.cache)

    def test_distribution_version_is_part_of_cache_identity(self):
        first, sha = RUNTIME.prepare_runtime(self.source, self.cache)
        manifest = json.loads((first / 'manifest.json').read_text())
        self.assertEqual(manifest['release']['version'], '1.0.preview4')
        (self.root / 'setup.py').write_text("setup(version='1.0.preview5')\n")
        _, changed_sha = RUNTIME.prepare_runtime(self.source, self.cache)
        self.assertNotEqual(sha, changed_sha)

    def test_injected_bytecode_not_ignored_in_cache(self):
        target, _ = RUNTIME.prepare_runtime(self.source, self.cache)
        bytecode = target / 'isaacgym/__pycache__'
        bytecode.mkdir()
        (bytecode / 'unverified.pyc').write_bytes(b'unknown bytes')
        with self.assertRaisesRegex(ValueError, 'failed SHA verification'):
            RUNTIME.prepare_runtime(self.source, self.cache)

    def test_escaping_and_absolute_links_rejected(self):
        outside = self.root / 'outside'
        outside.write_text('not runtime')
        link = self.source / 'external'
        link.symlink_to('../outside')
        with self.assertRaisesRegex(ValueError, 'escapes package'):
            RUNTIME.prepare_runtime(self.source, self.cache)
        link.unlink()
        link.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'absolute symlink'):
            RUNTIME.prepare_runtime(self.source, self.cache)

    def test_concurrent_atomic_creation(self):
        context = multiprocessing.get_context('fork')
        queue = context.Queue()
        children = [context.Process(target=prepare_in_process,
                    args=(str(self.source), str(self.cache), queue)) for _ in range(3)]
        for child in children:
            child.start()
        results = [queue.get(timeout=20) for child in children]
        for child in children:
            child.join(timeout=20)
            self.assertEqual(child.exitcode, 0)
        self.assertEqual(len(set(results)), 1)
        self.assertNotEqual(results[0][0], 'error')
        target = Path(results[0][0])
        self.assertEqual(json.loads((target / 'manifest.json').read_text())['sha256'], results[0][1])

    def test_shared_filesystem_rejected_before_creation(self):
        with patch.object(RUNTIME, 'mount_type', return_value='fuse.sshfs'):
            with self.assertRaisesRegex(ValueError, 'local filesystem'):
                RUNTIME.prepare_runtime(self.source, self.cache)
        self.assertFalse(self.cache.exists())

    def test_environment_replaces_shared_runtime_and_build_paths(self):
        target, sha = RUNTIME.prepare_runtime(self.source, self.cache)
        with patch.dict(os.environ, {'PYTHONPATH': '/remote/isaacgym',
                                   'TORCH_EXTENSIONS_DIR': '/remote/cache'}):
            env = RUNTIME.execution_environment(target, sha, self.cache)
        self.assertEqual(env['PYTHONPATH'].split(os.pathsep), [str(target), str(RUNTIME.PROJECT)])
        self.assertIn(self.cache, Path(env['TORCH_EXTENSIONS_DIR']).parents)
        self.assertEqual(env['PYTHONDONTWRITEBYTECODE'], '1')

    def test_child_reads_utf8_after_native_locale_change_without_environment_flag(self):
        target, sha = RUNTIME.prepare_runtime(self.source, self.cache)
        text = self.root / 'korean.json'
        text.write_text('{"name": "기타"}', encoding='utf-8')
        code = ('import json, locale, sys; from pathlib import Path; '
                'locale.setlocale(locale.LC_CTYPE, "C"); '
                'assert sys.flags.utf8_mode == 1; '
                'assert json.loads(Path(sys.argv[1]).read_text())["name"] == "기타"')
        # Exercise main's actual child argv and environment. Explicit 0 also
        # verifies that a caller cannot accidentally restore locale-based I/O.
        for inherited in (None, '0'):
            with self.subTest(PYTHONUTF8=inherited):
                environment = os.environ.copy()
                environment.pop('PYTHONUTF8', None)
                if inherited is not None:
                    environment['PYTHONUTF8'] = inherited
                def execute(executable, argv, env):
                    child = subprocess.run(argv, env=env, capture_output=True,
                                           encoding='utf-8', timeout=20)
                    self.assertEqual(child.returncode, 0, child.stderr)
                with patch.dict(os.environ, environment, clear=True), \
                     patch.object(sys, 'argv', ['tab2body.py', '--cache-root', str(self.cache),
                                                'run', '-c', code, str(text)]), \
                     patch.object(RUNTIME, 'prepare_runtime', return_value=(target, sha)), \
                     patch.object(RUNTIME.os, 'execvpe', side_effect=execute), \
                     patch.object(RUNTIME.resource, 'setrlimit'):
                    RUNTIME.main()


if __name__ == '__main__':
    unittest.main()
