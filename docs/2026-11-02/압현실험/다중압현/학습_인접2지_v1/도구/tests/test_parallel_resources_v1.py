"""CPU mocks: resource identities must fail closed without importing physics."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import parallel_resources_v1 as resources


class ParallelResourceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.source = self.folder / 'frozen.py'
        self.source.write_text('untouched source\n')
        self.manifest = self.folder / 'manifest.json'
        self.manifest.write_text(json.dumps({'pins': {str(self.source): resources.digest(self.source)}}))
        self.manifest_sha = resources.digest(self.manifest)
        self.state = dict(schema='guitar_learning.range336.state.v1', total=336,
                          status='running', completed=False, finished=80, remaining=256,
                          manifest_sha256=self.manifest_sha,
                          current=dict(case='index_s6_f6', out='/single/index_s6_f6/attempt01'))
        self.state_file = self.folder / 'state.json'
        self.state_file.write_text(json.dumps(self.state))
        for name, value in [('SINGLE_STATE', self.state_file), ('SINGLE_MANIFEST', self.manifest),
                            ('SINGLE_MANIFEST_SHA256', self.manifest_sha)]:
            p = patch.object(resources, name, value)
            p.start(); self.addCleanup(p.stop)
        self.gpu = [dict(uuid=resources.GPU_UUID, **{'memory.free [MiB]': '10970 MiB'})]
        self.processes = [dict(pid='123', gpu_uuid=resources.GPU_UUID, process_name='python')]
        self.identity = dict(pid=123, start_ticks='777', argv=[
            '/env/bin/python', '-X', 'utf8', str(resources.SINGLE_SCRIPT),
            '--geometry', str(resources.SINGLE_GEOMETRY), '--case', 'index_s6_f6',
            '--seed', '7', '--out', self.state['current']['out']])

    def ready(self, compute=None, gpu=None, identity=None, recheck=None):
        compute = self.processes if compute is None else compute
        gpu = self.gpu if gpu is None else gpu
        identity = self.identity if identity is None else identity
        with patch.object(resources, 'gpu_query', side_effect=[gpu, compute,
                         compute if recheck is None else recheck]), \
             patch.object(resources, 'read_process_identity', return_value=identity):
            return resources.readiness()

    def test_existing_single_and_idle_are_ready(self):
        self.assertEqual(self.ready()[:2], (True, 'ready_parallel'))
        self.assertEqual(self.ready(compute=[])[:2], (True, 'ready_idle'))
        self.assertEqual(self.source.read_text(), 'untouched source\n')

    def test_units_supported_and_low_memory_blocks(self):
        for value in ['4096', '4096 MiB', '10970.5 MiB']:
            self.gpu[0]['memory.free [MiB]'] = value
            self.assertTrue(self.ready()[0])
        self.gpu[0]['memory.free [MiB]'] = '4095 MiB'
        self.assertEqual(self.ready()[:2], (False, 'waiting_for_gpu_memory'))

    def test_invalid_and_nonfinite_memory_never_ready(self):
        for value in ['NaN MiB', 'Inf', '-Inf MiB', '-1 MiB', '12 GiB', 'N/A', '', None]:
            with self.subTest(value=value):
                self.gpu[0]['memory.free [MiB]'] = value
                self.assertFalse(self.ready()[0])

    def test_gpu_uuid_missing_wrong_or_duplicated_blocks(self):
        for rows in [[], [dict(uuid='GPU-other', **{'memory.free [MiB]': '12000 MiB'})],
                     self.gpu * 2]:
            self.assertEqual(self.ready(gpu=rows)[:2], (False, 'waiting_for_verified_gpu'))

    def test_unknown_process_or_additional_process_blocks(self):
        identity = copy.deepcopy(self.identity)
        identity['argv'][3] = '/other/train.py'
        self.assertEqual(self.ready(identity=identity)[:2], (False, 'waiting_for_unknown_gpu_process'))
        self.assertFalse(self.ready(compute=self.processes * 2)[0])

    def test_native_script_as_argument_to_another_script_is_not_allowed(self):
        identity = copy.deepcopy(self.identity)
        identity['argv'].insert(3, '/other/train.py')
        self.assertFalse(self.ready(identity=identity)[0])
        identity['argv'] = ['/bin/sh', str(resources.SINGLE_SCRIPT)] + self.identity['argv'][4:]
        self.assertFalse(self.ready(identity=identity)[0])

    def test_geometry_out_case_and_duplicate_option_are_verified(self):
        for flag in ['--geometry', '--out', '--case']:
            identity = copy.deepcopy(self.identity)
            identity['argv'][identity['argv'].index(flag) + 1] = '/wrong/value'
            self.assertFalse(self.ready(identity=identity)[0])
        identity = copy.deepcopy(self.identity)
        identity['argv'].extend(['--out', self.state['current']['out']])
        self.assertFalse(self.ready(identity=identity)[0])

    def test_other_gpu_process_does_not_block_target(self):
        self.assertTrue(self.ready(compute=self.processes + [dict(pid='456', gpu_uuid='GPU-other')])[0])

    def test_compute_process_replaced_or_exited_blocks(self):
        self.assertEqual(self.ready(recheck=[])[:2], (False, 'waiting_for_process_race'))
        changed = copy.deepcopy(self.processes); changed[0]['pid'] = '456'
        self.assertEqual(self.ready(recheck=changed)[:2], (False, 'waiting_for_process_race'))

    def test_pid_reused_or_proc_disappears_blocks(self):
        changed = copy.deepcopy(self.identity); changed['start_ticks'] = '888'
        with patch.object(resources, 'gpu_query', side_effect=[self.gpu, self.processes, self.processes]), \
             patch.object(resources, 'read_process_identity', side_effect=[self.identity, changed]):
            self.assertEqual(resources.readiness()[:2], (False, 'waiting_for_process_race'))
        with patch.object(resources, 'gpu_query', side_effect=[self.gpu, self.processes]), \
             patch.object(resources, 'read_process_identity', side_effect=FileNotFoundError('/proc/123')):
            self.assertFalse(resources.readiness()[0])

    def test_single_manifest_or_pinned_source_changed_blocks(self):
        self.source.write_text('changed source\n')
        self.assertFalse(self.ready()[0])
        self.source.write_text('untouched source\n')
        self.manifest.write_text(self.manifest.read_text() + '\n')
        # Even coordinated state digest changes cannot replace the original pin.
        self.state['manifest_sha256'] = resources.digest(self.manifest)
        self.state_file.write_text(json.dumps(self.state))
        self.assertFalse(self.ready()[0])

    def test_state_manifest_digest_mismatch_blocks(self):
        self.state['manifest_sha256'] = '0' * 64
        self.state_file.write_text(json.dumps(self.state))
        self.assertFalse(self.ready()[0])

    def test_state_turnover_blocks(self):
        changed = copy.deepcopy(self.state); changed['current']['case'] = 'next'
        with patch.object(resources, '_state', side_effect=[self.state, changed]):
            self.assertEqual(self.ready()[:2], (False, 'waiting_for_single_state_race'))

    def test_invalid_pid_and_missing_state_block(self):
        for value in ['N/A', '0', '-1', 'NaN']:
            rows = copy.deepcopy(self.processes); rows[0]['pid'] = value
            self.assertFalse(self.ready(compute=rows)[0])
        self.state_file.unlink()
        self.assertFalse(self.ready()[0])

    def test_missing_process_gpu_identity_blocks(self):
        self.assertFalse(self.ready(compute=[dict(pid='123')])[0])

    def test_proc_stat_start_ticks_and_exit_race(self):
        def stat(ticks):
            return '123 (python (worker)) S ' + ' '.join(['0'] * 18 + [ticks])
        with patch.object(Path, 'read_text', side_effect=[stat('777'), stat('777')]), \
             patch.object(Path, 'read_bytes', return_value=b'/env/bin/python\0script.py\0'):
            identity = resources.read_process_identity(123)
            self.assertEqual(identity['start_ticks'], '777')
            self.assertEqual(identity['argv'], ['/env/bin/python', 'script.py'])
        with patch.object(Path, 'read_text', side_effect=[stat('777'), stat('888')]), \
             patch.object(Path, 'read_bytes', return_value=b'/env/bin/python\0'):
            with self.assertRaises(ValueError):
                resources.read_process_identity(123)

    def test_oom_and_query_timeout_fail_closed(self):
        for error in [RuntimeError('GPU query unavailable: Out of memory'),
                      subprocess.TimeoutExpired('nvidia-smi', 20)]:
            with patch.object(resources, 'gpu_query', side_effect=error):
                ready, _, evidence = resources.readiness()
                self.assertFalse(ready)
                self.assertIn('error', evidence)

    def test_gpu_csv_actual_mib_header(self):
        result = subprocess.CompletedProcess([], 0,
            'uuid, name, memory.free [MiB]\n%s, GeForce RTX, 10970 MiB\n' % resources.GPU_UUID, '')
        with patch.object(resources.subprocess, 'run', return_value=result) as run:
            rows = resources.gpu_query('uuid,name,memory.free', 'gpu')
        self.assertEqual(rows[0]['memory.free [MiB]'], '10970 MiB')
        self.assertEqual(run.call_args[0][0][-1], '--format=csv')


if __name__ == '__main__':
    unittest.main()
