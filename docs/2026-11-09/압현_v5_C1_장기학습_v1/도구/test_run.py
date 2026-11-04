"""감독기의 예산·SHA·프로세스 감시를 GPU 없이 검사한다."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location('c1_supervisor', Path(__file__).with_name('run.py'))
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)


class SupervisorTests(unittest.TestCase):
    def test_budget_and_absolute_argv(self):
        argv = run.train_command(Path('/tmp/a b;$x'))
        self.assertIn('2000', argv)
        self.assertEqual(argv[argv.index('--size')+1], 'large')
        self.assertIn('/tmp/a b;$x', argv)
        self.assertEqual(argv[0], str(run.PYTHON))
        self.assertIn(str(run.RUNTIME_ROOT / 'scripts/tab2body.py'), argv)
        resumed = run.train_command(Path('/tmp/new'), Path('/tmp/old.pt'), 250)
        self.assertEqual(resumed[resumed.index('--updates')+1], '1750')
        self.assertNotIn('--num-envs', resumed)
        with self.assertRaises(ValueError):
            run.train_command(Path('/tmp/new'), committed=2000)

    def test_manifest_sha_blocks_corruption_and_escape(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            phase = base / 'J'
            phase.mkdir()
            model = phase / 'checkpoint.pt'
            model.write_bytes(b'valid')
            manifest = phase / 'checkpoint_manifest.jsonl'
            row = dict(path=model.name, optimizer_updates=250, sha256=run.sha(model))
            manifest.write_text(json.dumps(row)+'\n')
            self.assertEqual(run.manifest_candidates([base])[0][0], 250)
            model.write_bytes(b'changed')
            with self.assertRaises(ValueError):
                run.manifest_candidates([base])
            row['path'] = '../checkpoint.pt'
            manifest.write_text(json.dumps(row)+'\n')
            with self.assertRaises(ValueError):
                run.manifest_candidates([base])

    def test_finite_and_incomplete_lines(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'metrics'
            path.write_text('{"optimizer_updates":1}\n{"unfinished":')
            self.assertEqual(len(run.rows(path)), 1)
            path.write_text('{"reward":NaN}\n')
            with self.assertRaises(ValueError):
                run.rows(path)

    def test_strict_inspection_is_separate_cpu_process(self):
        completed = Mock(stdout='module notice\n{"updates":250}\n')
        with patch.object(run.subprocess, 'run', return_value=completed) as launch:
            self.assertEqual(run.strict_check(Path('/tmp/model.pt'), 'digest')['updates'], 250)
        argv = launch.call_args.args[0]
        self.assertEqual(argv[:2], [str(run.PYTHON), str(run.SELF)])
        self.assertIn('--inspect', argv)
        self.assertTrue(launch.call_args.kwargs['check'])

    def execute_fixture(self, temporary, poll_values, disk_free, clocks, training=False):
        process = Mock(pid=123, poll=Mock(side_effect=poll_values), wait=Mock(return_value=0))
        with patch.object(run, 'STUDY', Path(temporary)), \
             patch.object(run.subprocess, 'Popen', return_value=process) as popen, \
             patch.object(run.shutil, 'disk_usage', return_value=Mock(free=disk_free)), \
             patch.object(run.time, 'monotonic', side_effect=clocks), \
             patch.object(run.time, 'sleep'), patch.object(run, 'stop') as stop:
            result = run.execute(['/absolute/python', '/tmp/a b'], 'test', {},
                                 out=Path(temporary), training=training)
        self.assertTrue(popen.call_args.kwargs['start_new_session'])
        return result, stop

    def test_normal_exit(self):
        with tempfile.TemporaryDirectory() as temporary:
            result, _ = self.execute_fixture(temporary, [0], run.MIN_FREE, [0])
            self.assertEqual(result[:2], (0, None))

    def test_disk_budget_stops_child(self):
        with tempfile.TemporaryDirectory() as temporary:
            result, stop = self.execute_fixture(temporary, [None], run.MIN_FREE-1, [0, 1, 1])
            self.assertEqual(result[1], 'disk_below_8GiB')
            self.assertTrue(stop.called)

    def test_stall_stops_child(self):
        with tempfile.TemporaryDirectory() as temporary:
            result, stop = self.execute_fixture(temporary, [None, None], run.MIN_FREE,
                [0, 1, 1, 2, 2, 700, 701], training=True)
            self.assertEqual(result[1], 'stall')
            self.assertTrue(stop.called)

    def test_retry_never_changes_conditions(self):
        with tempfile.TemporaryDirectory() as temporary:
            log = Path(temporary) / 'log'
            log.write_text('external signal')
            self.assertTrue(run.retry_allowed(log, 'process_exit'))
            self.assertFalse(run.retry_allowed(log, 'disk_below_8GiB'))
            log.write_text('Traceback (most recent call last):\n  stopped\nKeyboardInterrupt\n')
            self.assertTrue(run.retry_allowed(log, 'stall'))
            self.assertFalse(run.retry_allowed(log, 'process_exit'))
            log.write_text('Traceback (most recent call last):\nValueError: bad\n'
                           'Traceback (most recent call last):\nKeyboardInterrupt\n')
            self.assertFalse(run.retry_allowed(log, 'stall'))
            for message in ('KL guard', 'non-finite', 'contract mismatch', 'Traceback'):
                log.write_text(message)
                self.assertFalse(run.retry_allowed(log, 'process_exit'))

    def test_sigint_then_kill_only_after_grace(self):
        process = Mock(pid=123, poll=Mock(return_value=None))
        process.wait.side_effect = [subprocess.TimeoutExpired('train', 90), 0]
        with patch.object(run.os, 'killpg') as kill:
            run.stop(process)
        self.assertEqual([c.args[1] for c in kill.call_args_list],
                         [run.signal.SIGINT, run.signal.SIGKILL])


if __name__ == '__main__':
    unittest.main()
