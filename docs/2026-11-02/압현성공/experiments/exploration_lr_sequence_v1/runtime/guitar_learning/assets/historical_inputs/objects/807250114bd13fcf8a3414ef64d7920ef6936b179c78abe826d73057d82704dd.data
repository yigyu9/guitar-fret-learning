"""Spawn logger and CLI dispatch must keep the new zero-settling path explicit."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from guitar_learning import train_actionable_preparation as train
from guitar_learning import train_timing, timing_transfer


class PreparationWorkerTests(unittest.TestCase):
    def test_fresh_spawn_logger_does_not_capture_itself(self):
        script = '''
import sys
from types import SimpleNamespace
sys.modules['isaacgym'] = SimpleNamespace()
from guitar_learning import parallel, train_actionable_preparation as train
assert 'guitar_learning.specialist_parallel' not in sys.modules
parallel._compact = lambda env, info, action: {'base': True}
import guitar_learning.actionable_preparation_environment as environment
environment.build_environment = lambda *a, **kw: kw
spec = dict(config='unused',out='/tmp/unused',specialist={'role':'left'},bundle='unused',
            stage='B',timing={'pre_roll_s':3.})
result = train.native_environment(spec, 0)
assert result['timing'].pre_roll_s == 3.
info = dict(specialist={},timing={},score_time_s=-3.,actionable_preparation={'active':True})
assert parallel._compact(None,info,None) == dict(base=True, **info)
'''
        subprocess.run([sys.executable, '-c', script], check=True, capture_output=True, text=True, timeout=30)

    def test_dispatch_is_restored_on_interrupt(self):
        from guitar_learning.actionable_preparation_transfer import apply_actor_initialization
        previous_worker = train_timing.timing_native_environment
        previous_transfer = timing_transfer.apply_actor_initialization
        with tempfile.TemporaryDirectory() as folder:
            args = type('Args', (), {'out':Path(folder)/'new'})()
            def interrupt(settings, args):
                self.assertIs(train_timing.timing_native_environment, train.native_environment)
                self.assertIs(timing_transfer.apply_actor_initialization, apply_actor_initialization)
                raise KeyboardInterrupt()
            with patch.dict(sys.modules, {'isaacgym':type('Isaac', (), {})()}), \
                    patch.object(train_timing, 'run', interrupt):
                with self.assertRaises(KeyboardInterrupt): train.run({}, args)
        self.assertIs(train_timing.timing_native_environment, previous_worker)
        self.assertIs(timing_transfer.apply_actor_initialization, previous_transfer)

    def test_settings_require_new_clock(self):
        settings = json.loads((Path(__file__).resolve().parents[1]/'configs/left_timing_stage0_v1.json').read_text())
        with self.assertRaisesRegex(ValueError, 'pre_roll_s3'): train.settings_document(settings)
        settings['timing']['pre_roll_s'] = 3.
        self.assertEqual(train.settings_document(settings)['timing']['pre_roll_s'], 3.)


if __name__ == '__main__': unittest.main()
