"""GPU 없이 시간 진입과 복구 경계·확정 모델 선택을 검증한다."""
import importlib.util
from datetime import datetime
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('bp_supervisor', Path(__file__).resolve().parents[1]/'run.py')
supervisor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(supervisor)


class SupervisorTests(unittest.TestCase):
    def test_pair_admission_reserves_training_margin_and_postprocessing(self):
        early = datetime(2026, 11, 5, 0, tzinfo=supervisor.KST)
        late = datetime(2026, 11, 5, 2, tzinfo=supervisor.KST)
        self.assertTrue(supervisor.enough_time(1/2000, 3600, early))
        self.assertFalse(supervisor.enough_time(1/2000, 3600, late))
        self.assertFalse(supervisor.enough_time(1/2000, 3*3600, early))

    def test_resume_uses_remaining_updates_and_rejects_unaligned_state(self):
        with patch.object(supervisor, 'now', return_value=datetime(2026, 11, 5, 1, tzinfo=supervisor.KST)):
            argv = supervisor.train_argv('P', Path('/tmp/bp-output'), resume=Path('/tmp/checkpoint'), committed=128)
            self.assertEqual(argv[argv.index('--updates')+1], '384')
            self.assertEqual(argv[argv.index('--checkpoint-every')+1], '128')
            self.assertNotIn('--improvement-profile', argv)
            self.assertEqual(int(argv[argv.index('--max-wall-seconds')+1]), 6*3600-120)
            with self.assertRaises(ValueError):
                supervisor.train_argv('P', Path('/tmp/bp-output'), committed=129)

    def test_discarded_tail_does_not_supply_evaluation_model(self):
        records = {'first': [dict(optimizer_updates=u, checkpoint='first%d' % u)
                            for u in (0, 128, 256)],
                   'second': [dict(optimizer_updates=u, checkpoint='second%d' % u)
                             for u in (128, 256, 384, 512)]}
        inputs = dict(training_runs={'B': ['first', 'second']}, committed_prefix={'first': 128, 'second': 512})
        with patch.object(supervisor, 'manifest', side_effect=lambda path: records[str(path)]):
            models = supervisor.expected_models('B', inputs)
        self.assertEqual(models[128]['checkpoint'], 'first128')
        self.assertEqual(models[256]['checkpoint'], 'second256')
        self.assertEqual(set(models), {0, 128, 256, 384, 512})

    def test_transient_classifier_does_not_retry_invalid_learning(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'stderr.log'
            path.write_text('resource temporarily unavailable')
            self.assertTrue(supervisor.transient(path))
            path.write_text('nonfinite action; resource temporarily unavailable')
            self.assertFalse(supervisor.transient(path))
            path.write_text('identity mismatch')
            self.assertFalse(supervisor.transient(path))


if __name__ == '__main__':
    unittest.main()
