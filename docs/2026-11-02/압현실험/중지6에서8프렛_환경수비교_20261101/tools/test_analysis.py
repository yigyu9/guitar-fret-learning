"""평가 분모·시간표·후보 중복을 작은 합성 원장으로 검사한다."""
import copy
import gzip
import json
from pathlib import Path
import tempfile
import unittest
import analyze_results as analysis


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name)
        self.report = dict(episodes=2, failed_episodes_in_denominator=True,
                           completed=True, lifecycle_verified=True,
                           first_episode_per_env_per_batch=True)
        self.rows = [dict(env_id=i, valid=i == 0,
            termination=dict(physical_failure=i == 1, wrist_failure=False),
            left_note_ledger=dict(values=dict(left=[True, True], clean=[1.5, 1.5], wrong=[0., 0.])),
            finger_control_diagnostics=dict(episode_id=10+i), reward_components=dict(a=1., b=-.5), reward=.5)
            for i in range(2)]
        self.extra = dict(schema='guitar_learning.middle_f6_f8_environment_scale.v1',
            goals=[dict(fret=f, string_index=2, onset_s=a, end_s=b)
                   for f, a, b in ((6, 3., 4.5), (8, 5.25, 6.75))],
            all_env_episode_ids=[10, 11], all_env_candidate=[[True, True]]*2,
            all_env_wrong=[[False, False]]*2,
            all_env_position_geometry=[[True, True]]*2,
            all_env_facing_geometry=[[True, True]]*2,
            all_env_assigned_loaded=[[True, True]]*2)

    def save(self):
        (self.out/'report.json').write_text(json.dumps(self.report))
        (self.out/'episode_metadata.json').write_text(json.dumps(dict(fields=[])))
        (self.out/'episodes.jsonl').write_text('\n'.join(json.dumps(dict(episode=x)) for x in self.rows))
        with gzip.open(self.out/'finger_control_trace.jsonl.gz', 'wt') as stream:
            for t in [4.45+i/240 for i in range(12)]+[5.25, 5.3]:
                extra = copy.deepcopy(self.extra)
                extra['all_env_episode_time_s'] = [t, t]
                stream.write(json.dumps(dict(natural_preparation=dict(transition=extra)))+'\n')

    def test_failure_stays_in_denominator_and_candidate_overlap_is_recorded(self):
        self.save()
        result = analysis.analyze(self.out, 2)
        self.assertEqual((result['episodes'], result['AB'], result['full_duration_pair']), (2, 1, 1))
        self.assertEqual(result['physical'], 1)
        self.assertEqual(result['on_time_pair'], 1)
        self.assertEqual(result['A_audible_candidate_warning_samples'], 24)
        self.assertGreater(result['candidate_overlap_samples'], 0)
        self.assertEqual(result['B_rejection_partition']['clean'], 4)
        self.assertEqual(result['clean_fraction'], [1., 1.])

    def test_missing_environment_is_rejected(self):
        self.rows.pop()
        self.save()
        with self.assertRaisesRegex(ValueError, '분모 누락'):
            analysis.analyze(self.out, 2)

    def test_wrong_goal_or_time_contract_is_rejected(self):
        self.extra['goals'][1]['fret'] = 7
        self.save()
        with self.assertRaisesRegex(ValueError, '시간표 불일치'):
            analysis.analyze(self.out, 2)

    def test_reward_sum_is_checked(self):
        self.rows[0]['reward'] = 9.
        self.save()
        with self.assertRaisesRegex(ValueError, '합계 불일치'):
            analysis.analyze(self.out, 2)


if __name__ == '__main__':
    unittest.main()
