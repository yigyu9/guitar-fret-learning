"""원본 자료를 보존하며 시간·오압현 후보 검사의 정정을 검증한다."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('corrected_analyzer', Path(__file__).with_name('analyzer.py'))
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


class AnalyzerTests(unittest.TestCase):
    def synthetic(self, time, wrong):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            (out/'report.json').write_text(json.dumps(dict(episodes=1,
                failed_episodes_in_denominator=True, completed=True, lifecycle_verified=True,
                first_episode_per_env_per_batch=True)))
            row = dict(finger_control_diagnostics={'episode_id': 5},
                left_note_ledger={'values': dict(left=[False, False], clean=[0., 0.], wrong=[0., 0.])},
                termination=dict(physical_failure=False, wrist_failure=False), valid=True,
                reward_components={'test': 0.}, reward=0.)
            extra = dict(all_env_episode_ids=[5], all_env_candidate=[[True, True]],
                all_env_wrong=[wrong], all_env_episode_time_s=[time],
                all_env_position_geometry=[[True, True]], all_env_facing_geometry=[[True, True]],
                all_env_assigned_loaded=[[True, True]])
            with gzip.open(out/'finger_control_trace.jsonl.gz', 'wt') as stream:
                stream.write(json.dumps({'natural_preparation': {'transition': extra}})+'\n')
            with patch.object(a, 'first_episodes', return_value=[row]):
                return a.analyze(out, 1, result_path=out/'corrected.json')

    def test_inside_A_clean_dual_is_rejected(self):
        for time in (3., 4., 4.499):
            with self.subTest(time=time), self.assertRaisesRegex(ValueError, 'A 발음'):
                self.synthetic(time, [False, False])

    def test_inside_A_wrong_dual_is_allowed(self):
        self.assertEqual(self.synthetic(3.5, [True, False])['episodes'], 1)

    def test_inside_B_lower_fret_incidental_contact_is_allowed(self):
        for time in (5.25, 6., 6.749):
            with self.subTest(time=time):
                self.assertEqual(self.synthetic(time, [False, False])['B_endpoint_count'], 1)

    def test_outside_audible_dual_is_allowed(self):
        for time in (2.99, 4.5, 5., 6.75, 6.775, 7.2041667):
            with self.subTest(time=time):
                self.assertEqual(self.synthetic(time, [False, False])['B_endpoint_count'], 0)

    def test_actual_trace_reanalysis_preserves_all_original_files(self):
        out = a.ROOT/'docs/2026-11-02/압현성공/experiments/transition_diagnosis_v3/runs/continuation_v1/jobs/H128_s7_u250_mean_std1.0_n32'
        if not out.is_dir():
            self.skipTest('검증할 원본 평가 자료 없음')
        def hashes():
            return {str(path.relative_to(out)): hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in out.rglob('*') if path.is_file()}
        before = hashes()
        with tempfile.TemporaryDirectory() as directory:
            result_path = Path(directory)/'analysis.json'
            result = a.analyze(out, 32, result_path=result_path)
            self.assertEqual(json.loads(result_path.read_text()), result)
        self.assertEqual(result['episodes'], 32)
        self.assertEqual(result['AB'], 0)
        self.assertAlmostEqual(result['clean_s'][1], .607421875, places=10)
        self.assertEqual(before, hashes())

    def test_original_denominator_and_lifecycle_checks_remain(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            (out/'report.json').write_text(json.dumps(dict(episodes=32,
                failed_episodes_in_denominator=True, completed=True, lifecycle_verified=False,
                first_episode_per_env_per_batch=True)))
            with self.assertRaisesRegex(ValueError, '분모'):
                a.analyze(out, 32)


if __name__ == '__main__':
    unittest.main()
