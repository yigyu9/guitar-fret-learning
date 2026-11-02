"""평가 분모·실패 원장과 모순된 두 프렛 성공의 분석 회귀 검사."""
import gzip
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('study', Path(__file__).with_name('study.py'))
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


def fixture(path):
    report = dict(episodes=2, completed=True, lifecycle_verified=True,
                  failed_episodes_in_denominator=True, first_episode_per_env_per_batch=True)
    (path/'report.json').write_text(json.dumps(report))
    (path/'episode_metadata.json').write_text(json.dumps(dict(fields=[])))
    rows = []
    for env in range(2):
        row = dict(env_id=env, valid=env == 0, reward=1., reward_components=dict(hold=1.),
                   left_note_ledger=dict(values=dict(left=[True, True], clean=[1.5, 1.5], wrong=[0., 0.])),
                   termination=dict(physical_failure=env == 1, wrist_failure=False),
                   finger_control_diagnostics=dict(episode_id=1),
                   left_episode_diagnostics=dict(thumb_support=dict(contact_candidate_s=0., mean_signed_gap_m=.05, normal_load_mean_N=0.)))
        rows.append(json.dumps(dict(episode=row)))
    (path/'episodes.jsonl').write_text('\n'.join(rows)+'\n')
    extra = dict(all_env_episode_ids=[1, 1], all_env_episode_time_s=[5.25, 5.25],
                 all_env_candidate=[[False, True], [False, False]], all_env_wrong=[[False, False], [False, False]],
                 all_env_position_geometry=[[False, True], [False, False]],
                 all_env_facing_geometry=[[False, True], [False, False]],
                 all_env_assigned_loaded=[[True, True], [True, True]])
    with gzip.open(path/'finger_control_trace.jsonl.gz', 'wt') as stream:
        stream.write(json.dumps(dict(natural_preparation=dict(transition=extra)))+'\n')
    return extra


class AnalysisTests(unittest.TestCase):
    def test_failed_episode_remains_in_denominator_but_not_full_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            fixture(path)
            result = study.analyze(path, 2)
            self.assertEqual(result['episodes'], 2)
            self.assertEqual(result['physical'], 1)
            self.assertEqual(result['AB'], 1)
            self.assertEqual(result['full_duration_pair'], 1)
            self.assertEqual(result['B_rejection_partition']['position'], 1)
            self.assertEqual(result['B_rejection_partition']['clean'], 1)

    def test_simultaneous_adjacent_frets_stop_analysis(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            extra = fixture(path)
            extra['all_env_candidate'][0] = [True, True]
            with gzip.open(path/'finger_control_trace.jsonl.gz', 'wt') as stream:
                stream.write(json.dumps(dict(natural_preparation=dict(transition=extra)))+'\n')
            with self.assertRaisesRegex(ValueError, '동시'):
                study.analyze(path, 2)

    def test_missing_first_episode_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            fixture(path)
            rows = (path/'episodes.jsonl').read_text().splitlines()
            (path/'episodes.jsonl').write_text(rows[0]+'\n')
            with self.assertRaisesRegex(ValueError, '분모'):
                study.analyze(path, 2)

    def test_incomplete_lifecycle_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            fixture(path)
            report = json.loads((path/'report.json').read_text())
            report['completed'] = False
            (path/'report.json').write_text(json.dumps(report))
            with self.assertRaises(ValueError):
                study.analyze(path, 2)


if __name__ == '__main__':
    unittest.main()
