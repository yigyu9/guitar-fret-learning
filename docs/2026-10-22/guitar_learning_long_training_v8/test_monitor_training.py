"""CPU fault injection only: synthetic proc tree, no real signals or GPU query."""
from contextlib import ExitStack
import errno
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

PHASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('monitor_v2_tested', PHASE/'monitor_training_v2.py')
monitor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)


class MonitorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.phase, self.run, self.proc = root/'phase', root/'base/train2000', root/'proc'
        for p in (self.phase, self.run, self.proc): p.mkdir(parents=True)
        self.command = ['/usr/bin/python', '-B', '-m', 'guitar_learning.train', '--out', str(self.run)]
        self.launch = dict(out=str(self.run), child_pid=20, started_utc='1970-01-01T00:17:30+00:00',
                           command=['gdb', '-batch', '--args']+self.command)
        (self.proc/'stat').write_text('btime 1000\n')
        self.process(20, 1, 5000, self.launch['command'])
        self.process(21, 20, 5050, self.command)
        child_path = self.proc/'20/task/20'
        child_path.mkdir(parents=True)
        (child_path/'children').write_text('21')
        (self.run/'status.json').write_text(json.dumps(dict(parent_pid=21, phase='collecting')))
        (self.run/'update_000012.json').write_text(json.dumps(dict(update_index=12, optimizer_updates=13,
                                                                  mean_reward=.1, mean_cost=.2)))
        src = root/'source.py'; src.write_text('source unchanged\n')
        self.source = {str(src): hashlib.sha256(src.read_bytes()).hexdigest()}
        self.state = dict(started=0., last_update=12, last_progress=100., count=0,
                          native=None, signal_attempted=False)
        self.stack = ExitStack(); self.addCleanup(self.stack.close)
        original_owner = monitor.owned_native
        self.owner = self.stack.enter_context(patch.object(monitor, 'owned_native', side_effect=lambda launch, run, cached=None, status=None:
            original_owner(launch, run, cached, status, self.proc)))
        self.stack.enter_context(patch.object(monitor.os, 'sysconf', return_value=100))
        self.stack.enter_context(patch.object(monitor.os, 'statvfs', return_value=SimpleNamespace(f_bavail=9*1024**3, f_frsize=1)))
        self.gpu = self.stack.enter_context(patch.object(monitor.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout='1024, 14336', stderr='')))
        self.kill = self.stack.enter_context(patch.object(monitor.os, 'kill'))
        self.clock = self.stack.enter_context(patch.object(monitor.time, 'monotonic', return_value=100.))
        self.stack.enter_context(patch.object(monitor.sys, 'stderr', io.StringIO()))

    def process(self, pid, ppid, start, command):
        folder = self.proc/str(pid); folder.mkdir(exist_ok=True)
        fields = ['S', str(ppid)]+['0']*17+[str(start)]
        (folder/'stat').write_text(str(pid)+' (name with ) spaces) '+' '.join(fields))
        (folder/'cmdline').write_bytes(b'\0'.join(x.encode() for x in command)+b'\0')

    def cycle(self):
        return monitor.cycle(self.launch, self.source, self.state, self.phase)

    def fail_status(self):
        original = monitor.read
        def read(path):
            if path == self.run/'status.json': raise OSError(errno.EIO, 'injected status EIO')
            return original(path)
        return patch.object(monitor, 'read', side_effect=read)

    def test_initial_status_eio_discovers_exact_gdb_child_and_interrupts_once(self):
        with self.fail_status():
            first = self.cycle(); self.cycle()
        self.assertIn('status storage error', first['guard_problem'])
        self.assertEqual(self.state['native']['starttime'], 5050)
        self.kill.assert_called_once_with(21, signal.SIGINT)

    def test_nvidia_timeout_and_command_error_are_warning_only(self):
        for error in (subprocess.TimeoutExpired('nvidia-smi', 10), OSError(errno.ENOENT, 'missing query')):
            self.gpu.side_effect = error
            row = self.cycle()
            self.assertIsNone(row['guard_problem'])
            self.assertIn('NVIDIA query unavailable', row['warnings'][0])
        self.kill.assert_not_called()

    def test_local_enospc_preserves_original_and_warns_on_external_log(self):
        local = self.phase/'progress.jsonl'; local.write_text('original monitor bytes\n')
        original = monitor.append
        def append(path, row):
            if path == local: raise OSError(errno.ENOSPC, 'injected local full')
            return original(path, row)
        with patch.object(monitor, 'append', side_effect=append): row = self.cycle()
        entries = [json.loads(s) for s in (self.run.parent/'monitor_v2_progress.jsonl').read_text().splitlines()]
        self.assertEqual(entries[-1]['event'], 'local_progress_write_failed')
        self.assertEqual(local.read_text(), 'original monitor bytes\n')
        self.assertIsNone(row['guard_problem']); self.kill.assert_not_called()

    def test_external_progress_enospc_triggers_owned_guard_once(self):
        original = monitor.append
        def append(path, row):
            if path.parent == self.run.parent: raise OSError(errno.ENOSPC, 'injected external full')
            return original(path, row)
        with patch.object(monitor, 'append', side_effect=append):
            row = self.cycle(); self.cycle()
        self.assertIn('external progress storage error', row['guard_problem'])
        self.kill.assert_called_once_with(21, signal.SIGINT)
        self.assertIn('guard_action', json.loads((self.phase/'progress.jsonl').read_text().splitlines()[0]))

    def test_pid_reuse_after_cache_and_foreign_status_never_receive_signal(self):
        self.state['native'] = monitor.owned_native(self.launch, self.run)
        self.process(21, 20, 5060, self.command)  # Same PID and args, different birth.
        with self.fail_status(): row = self.cycle()
        self.assertIn('No signal', row['guard_action']); self.kill.assert_not_called()
        self.state['native'] = None
        foreign = self.command[:-1]+['/another/run']
        self.process(21, 20, 5050, foreign)
        with self.fail_status(): row = self.cycle()
        self.assertIn('No signal', row['guard_action']); self.kill.assert_not_called()

    def test_initial_identity_requires_full_args_parent_and_launch_start(self):
        self.process(21, 20, 5050, self.command+['--hand', 'right'])
        self.assertIsNone(monitor.owned_native(self.launch, self.run))
        self.process(21, 999, 5050, self.command)
        self.assertIsNone(monitor.owned_native(self.launch, self.run))
        self.process(21, 20, 5050, self.command)
        self.process(20, 1, 12000, self.launch['command'])
        self.assertIsNone(monitor.owned_native(self.launch, self.run))

    def test_source_read_eio_is_guarded_with_verified_cached_pid(self):
        self.state['native'] = monitor.owned_native(self.launch, self.run)
        original = Path.read_bytes
        def read_bytes(path):
            if str(path) in self.source: raise OSError(errno.EIO, 'injected source EIO')
            return original(path)
        with patch.object(Path, 'read_bytes', read_bytes): row = self.cycle()
        self.assertIn('storage error', row['guard_problem'])
        self.kill.assert_called_once_with(21, signal.SIGINT)

    def test_initial_source_manifest_read_failure_still_guards_owned_native(self):
        self.state['startup_problem'] = 'source manifest storage error: injected EIO'
        row = monitor.cycle(self.launch, {}, self.state, self.phase)
        self.assertIn('source manifest storage error', row['guard_problem'])
        self.kill.assert_called_once_with(21, signal.SIGINT)

    def test_native_gone_closed_report_finishes_without_launcher_result(self):
        self.state['native'] = monitor.owned_native(self.launch, self.run)
        shutil.rmtree(self.proc/'21')
        (self.run/'report.json').write_text(json.dumps(dict(completed=True, gpu_scene=dict(closed=True))))
        row = self.cycle()
        self.assertTrue(row['finished'])
        self.assertEqual(row['finish_reason'], 'closed_report_native_gone')
        self.assertIsNone(row['launch_result']); self.kill.assert_not_called()

    def test_identity_io_error_is_not_native_gone_even_with_closed_report(self):
        (self.run/'report.json').write_text(json.dumps(dict(completed=True, gpu_scene=dict(closed=True))))
        with patch.object(monitor, 'owned_native', side_effect=OSError(errno.EIO, 'proc unreadable')):
            row = self.cycle()
        self.assertFalse(row['finished']); self.kill.assert_not_called()

    def test_600_second_stall_guards_alive_and_marks_missing_report_after_death(self):
        self.clock.return_value = 701.; self.state['last_progress'] = 0.
        row = self.cycle()
        self.assertEqual(row['guard_problem'], 'no committed update for600s')
        self.assertFalse(row['finished']); self.kill.assert_called_once_with(21, signal.SIGINT)
        shutil.rmtree(self.proc/'21')
        row = self.cycle()
        self.assertTrue(row['finished'])
        self.assertEqual(row['finish_reason'], 'native_gone_without_report_after600s')


if __name__ == '__main__':
    unittest.main()
