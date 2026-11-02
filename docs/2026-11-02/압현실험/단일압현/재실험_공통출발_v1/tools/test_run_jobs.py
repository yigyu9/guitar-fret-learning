"""재시도 소진의 허위 완료와 대표 종료 후 남은 자식 프로세스를 검사한다."""
import importlib.util
import json
from pathlib import Path
import signal
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

SCRIPT = Path(__file__).with_name('run_jobs.py')
spec = importlib.util.spec_from_file_location('transport_run_jobs', SCRIPT)
jobs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jobs)


class RunnerSafetyTests(unittest.TestCase):
    def test_exhausted_attempts_cannot_complete_on_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            queue = root/'queue.json'
            queue.write_text(json.dumps(dict(pins={}, jobs=[dict(key='failed_case', argv=[])])))
            out = root/'out'
            pins = {str(queue.resolve()): jobs.sha(queue), str(SCRIPT): jobs.sha(SCRIPT)}
            jobs.write(out/'state.json', dict(pins=pins, jobs={'failed_case':
                [dict(status='failed'), dict(status='failed')]}))
            handlers = {s: signal.getsignal(s) for s in (signal.SIGINT, signal.SIGTERM)}
            try:
                with patch.object(sys, 'argv', ['run_jobs', '--queue', str(queue), '--out', str(out)]):
                    with self.assertRaisesRegex(RuntimeError, '실패 시도 상한'):
                        jobs.main()
            finally:
                for signum, handler in handlers.items():
                    signal.signal(signum, handler)
            self.assertEqual(json.loads((out/'state.json').read_text())['status'], 'failed')

    def test_cleanup_signals_group_even_after_leader_exits(self):
        child = Mock(pid=43210)
        child.poll.return_value = 0
        with patch.object(jobs.os, 'killpg') as kill:
            jobs.stop(child)
        self.assertEqual(kill.call_args_list[0].args, (43210, signal.SIGTERM))
        self.assertEqual(kill.call_args_list[1].args, (43210, signal.SIGKILL))


if __name__ == '__main__':
    unittest.main()
