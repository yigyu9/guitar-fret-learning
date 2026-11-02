"""감시기는 mock 검사에서 GPU를 실행하지 않는다."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock, call

spec = importlib.util.spec_from_file_location('verify_gpu_when_idle', Path(__file__).with_name('verify_gpu_when_idle.py'))
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


class VerificationTests(unittest.TestCase):
    def test_pipeline_running_never_ready(self):
        self.assertFalse(v.ready({'status': 'running'}, []))
        self.assertFalse(v.ready({'status': 'completed'}, [123]))
        self.assertFalse(v.ready({}, []))
        self.assertTrue(v.ready({'status': 'completed'}, []))

    def trace(self, lines):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'trace'
            path.write_text(lines)
            return v.trace_access(path, Path('/tmp/fresh'), Path('/project'), [Path('/home/ajou/miniconda3/envs/rl38')])

    def test_successful_read_separate_from_failed_metadata_probe(self):
        result = self.trace('123 openat(AT_FDCWD</tmp/fresh>, "a", O_RDONLY) = 3</tmp/fresh/a>\n'
                            '123 newfstatat(AT_FDCWD, "/project/old", {}, 0) = -1 ENOENT\n'
                            '123 openat(AT_FDCWD, "/project/old", O_RDONLY) = -1 ENOENT\n')
        self.assertTrue(result['passed'])
        self.assertEqual(result['metadata_probes'], 1)

    def test_original_project_read_rejected(self):
        result = self.trace('123 openat(AT_FDCWD, "/project/old", O_RDONLY) = 3</project/old>\n')
        self.assertFalse(result['passed'])
        self.assertEqual(result['external_project_reads'][0]['path'], '/project/old')

    def test_resumed_read_not_silently_dropped(self):
        result = self.trace('123 openat(AT_FDCWD, "/project/old", O_RDONLY <unfinished ...>\n'
                            '123 <... openat resumed>) = 3</project/old>\n')
        self.assertFalse(result['passed'])
        self.assertEqual(len(result['external_project_reads']), 1)

    def test_no_reads_or_unresolved_read_not_pass(self):
        self.assertFalse(self.trace('')['passed'])
        self.assertFalse(self.trace('123 openat(AT_FDCWD, "x", O_RDONLY) = 3\n')['passed'])

    def test_installed_libraries_allowed(self):
        result = self.trace('123 openat(AT_FDCWD, "/usr/lib/a", O_RDONLY) = 3</usr/lib/a>\n'
                            '123 execve("/home/ajou/miniconda3/envs/rl38/bin/python", ["python"], []) = 0\n')
        self.assertTrue(result['passed'])

    def test_unknown_tmp_and_other_home_assets_rejected(self):
        for path in ('/tmp/old_project/model.pt', '/home/other/asset.xml'):
            result = self.trace('123 openat(AT_FDCWD, "%s", O_RDONLY) = 3<%s>\n' % (path, path))
            self.assertFalse(result['passed'])
            self.assertEqual(result['unknown_external_accesses'][0]['path'], path)

    def test_directory_open_is_metadata_not_file_read(self):
        result = self.trace('123 openat(AT_FDCWD, "/home/other", O_RDONLY|O_DIRECTORY) = 3</home/other>\n'
                            '123 openat(AT_FDCWD, "/tmp/fresh/a", O_RDONLY) = 3</tmp/fresh/a>\n')
        self.assertTrue(result['passed'])
        self.assertEqual(result['metadata_probes'], 1)
        self.assertEqual(result['successful_accesses'], 1)

    def test_dead_direct_child_does_not_skip_final_group_kill(self):
        child = Mock(pid=123)
        child.wait.return_value = 0
        with patch.object(v.os, 'killpg') as kill:
            v.cleanup_group(child)
        self.assertEqual(kill.call_args_list, [call(123, v.signal.SIGTERM), call(123, v.signal.SIGKILL)])

    def test_missing_group_cleanup_allowed(self):
        child = Mock(pid=123)
        with patch.object(v.os, 'killpg', side_effect=ProcessLookupError):
            v.cleanup_group(child)
        self.assertEqual(child.wait.call_count, 2)

    def test_cpu_claim_alone_insufficient_and_manifest_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            project = directory / 'fresh'
            project.mkdir()
            source = project / 'source.py'
            source.write_text('original')
            manifest = directory / 'manifest.json'
            manifest.write_text(json.dumps({'commit': v.COMMIT, 'project': str(project), 'files': [
                {'path': 'source.py', 'bytes': source.stat().st_size, 'sha256': v.digest(source)}]}))
            audit = {'completed': True, 'success': True, 'remote_sha': v.COMMIT, 'project': str(project),
                     'clean_tracked': True, 'lfs_verified': True}
            with self.assertRaises(KeyError):
                v.cpu_gate(audit, project, directory)
            for key in ('checkout_manifest', 'input_audit', 'lfs_report'):
                audit[key] = manifest.name
                audit[key + '_sha256'] = v.digest(manifest)
            v.cpu_gate(audit, project, directory)
            source.write_text('tampered')
            with self.assertRaises(ValueError):
                v.cpu_gate(audit, project, directory)

    def test_gpu_errors_not_idle(self):
        with patch.object(v, 'command', return_value='driver unavailable'):
            with self.assertRaises(ValueError):
                v.gpu_processes()
        with patch.object(v, 'command', side_effect=RuntimeError('driver error')):
            with self.assertRaises(RuntimeError):
                v.gpu_processes()


if __name__ == '__main__':
    unittest.main()
