"""Fresh-interpreter regression for spawn's lazy logger import order."""
import subprocess
import sys
import unittest
from unittest.mock import patch
from guitar_learning.tool.training import train_timing, train_timing_v2


class TimingWorkerTests(unittest.TestCase):
    def test_fresh_worker_captures_original_logger_before_installing_wrapper(self):
        code = """
import sys
from types import SimpleNamespace
sys.modules['isaacgym'] = SimpleNamespace()
from guitar_learning.training import parallel
from guitar_learning.tool.training import train_timing
from guitar_learning.tool.training import train_timing_v2
assert 'guitar_learning.skills.specialist_parallel' not in sys.modules
parallel._compact = lambda env, info, action: {'original_base': True}
def fake_native(spec, worker_id):
    parallel._compact = train_timing.timing_compact
    return worker_id
train_timing_v2._BASE_WORKER = fake_native
assert train_timing_v2.timing_native_environment({}, 7) == 7
info = {'specialist': {'stage_success': False}, 'timing': {'stage_success': False}, 'score_time_s': -1.}
result = parallel._compact(None, info, None)
assert result == dict(original_base=True, **info), result
"""
        subprocess.run([sys.executable, '-c', code], check=True, capture_output=True, text=True, timeout=30)

    def test_dispatch_restored_on_interrupt(self):
        original = train_timing.timing_native_environment
        def interrupt(settings, args):
            self.assertIs(train_timing.timing_native_environment, train_timing_v2.timing_native_environment)
            raise KeyboardInterrupt()
        with patch.object(train_timing, 'run', interrupt):
            with self.assertRaises(KeyboardInterrupt):
                train_timing_v2.run({}, None)
        self.assertIs(train_timing.timing_native_environment, original)


if __name__ == '__main__':
    unittest.main()
