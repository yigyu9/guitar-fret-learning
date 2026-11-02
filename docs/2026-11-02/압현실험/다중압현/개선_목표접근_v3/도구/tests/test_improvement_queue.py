import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
spec = importlib.util.spec_from_file_location('tested_improvement_queue', TOOLS/'improvement_queue.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ImprovementQueueTests(unittest.TestCase):
    def test_waiting_or_failed_baseline_never_creates_native_child(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); manifest = root/'manifest.json'; manifest.write_text('{}')
            document = dict(jobs=[dict(job_id='new_train',out=str(root/'native_output'))])
            states = [(False, 'waiting_for_original_six_case_queue', dict(baseline_status='running')),
                      (False, 'waiting_for_original_six_case_queue', dict(baseline_status='error'))]
            with patch.object(module, 'STUDY', root), patch.object(module, 'inside', lambda p:Path(p).resolve()), \
                    patch.object(module, 'verify_manifest', return_value=document), \
                    patch.object(module, 'readiness', side_effect=states), \
                    patch.object(module.time, 'sleep'), patch.object(module.subprocess, 'Popen') as launch:
                module.run(manifest)
                launch.assert_not_called()
            state = json.loads((root/'로그/B2_queue/state.json').read_text())
            self.assertEqual(state['status'], 'blocked_by_baseline_error')
            self.assertFalse(state['completed'])
            self.assertEqual(state['jobs'], {})

    def test_manifest_replacement_while_waiting_fails_before_spawn(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); manifest = root/'manifest.json'; manifest.write_text('{}')
            document = dict(jobs=[dict(job_id='new_train',out=str(root/'native_output'))])
            with patch.object(module, 'STUDY', root), patch.object(module, 'inside', lambda p:Path(p).resolve()), \
                    patch.object(module, 'verify_manifest', return_value=document), \
                    patch.object(module, 'digest', side_effect=['first', 'changed']), \
                    patch.object(module.subprocess, 'Popen') as launch:
                with self.assertRaisesRegex(ValueError, 'manifest identity'):
                    module.run(manifest)
                launch.assert_not_called()


if __name__ == '__main__':
    unittest.main()
