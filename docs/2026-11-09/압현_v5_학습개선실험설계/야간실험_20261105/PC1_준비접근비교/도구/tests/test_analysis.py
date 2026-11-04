"""CPU-only arithmetic and provenance regressions; no native scene or training."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('pc1_analysis', Path(__file__).resolve().parents[1]/'analyze.py')
analysis = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(analysis)


def fixture():
    schedule = [dict(target_id='n'+str(i), onset_s=4.+2*i, end_s=5.+2*i) for i in range(20)]
    sections = [dict(case_id='P1', first_note=1., last_note=39., end=40., note_indices=list(range(20)))]
    values = dict(exposure_time=[0.]*20, left=[False]*20, contact_done=[False]*20,
                  loaded_target_time=[0.]*20, clean=[0.]*20, wrong=[0.]*20,
                  missing=[0.]*20, surface_min=[0.]*20)
    notes = [dict(target, duration_s=1., best_clean_streak_s=0., strict_success=False) for target in schedule]
    release = [dict(target_id=n['target_id'], release_required=True, release_status='aborted') for n in schedule]
    episode = dict(env_id=0, finger_skill=dict(scope='full_song', source_task_time_s=3.5),
        left_note_ledger=dict(target_ids=[n['target_id'] for n in schedule],
            selected_target_ids=[n['target_id'] for n in schedule], values=values),
        press_coordination=dict(notes=notes, groups=[]),
        press_completion=dict(notes=release, safe=False, completion_success=False),
        termination=dict(physical_failure=True, wrist_failure=False))
    episodes = [dict(copy.deepcopy(episode), env_id=i) for i in range(32)]
    return schedule, sections, episodes


class AnalysisTests(unittest.TestCase):
    def test_failed_unreached_notes_stay_in_total_denominator(self):
        schedule, sections, episodes = fixture()
        result, rows, sr = analysis.aggregate(episodes, schedule, sections, 3.)
        self.assertEqual(result['note_denominator'], 640)
        self.assertEqual(result['unstarted_notes'], 640)
        self.assertEqual(result['hold_release_rate'], 0.)
        self.assertIsNone(result['exposed_hold_release_rate'])
        self.assertEqual(result['failure_rate'], 1.)
        self.assertEqual(sr[0]['note_denominator'], 640)
        self.assertTrue(all(r['surface_min_m'] is None for r in rows))
        self.assertTrue(all(r['preparation_goal_observation_exposed'] is None for r in rows))

    def test_full_hold_requires_release_and_completed_audible_window(self):
        schedule, sections, episodes = fixture()
        episode = episodes[0]
        episode['finger_skill']['source_task_time_s'] = 5.
        episode['left_note_ledger']['values']['exposure_time'][0] = 1.
        episode['left_note_ledger']['values']['left'][0] = True
        note = episode['press_coordination']['notes'][0]
        note.update(best_clean_streak_s=1., strict_success=True)
        row = analysis.episode_notes(episode, schedule, sections, 3.)[0]
        self.assertTrue(row['strict_hold']); self.assertTrue(row['legacy_40pct'])
        self.assertFalse(row['hold_release'])
        episode['press_completion']['notes'][0]['release_status'] = 'released'
        row = analysis.episode_notes(episode, schedule, sections, 3.)[0]
        self.assertTrue(row['hold_release']); self.assertFalse(row['safe_hold_release'])
        episode['finger_skill']['source_task_time_s'] = 4.9
        self.assertFalse(analysis.episode_notes(episode, schedule, sections, 3.)[0]['hold_release'])

    def test_selected_target_cannot_disappear_after_early_failure(self):
        schedule, sections, episodes = fixture()
        episodes[0]['left_note_ledger']['selected_target_ids'].pop()
        with self.assertRaisesRegex(ValueError, '20 scheduled'):
            analysis.aggregate(episodes, schedule, sections, 3.)

    def test_coordination_overlap_must_be_present_and_strict(self):
        schedule, sections, episodes = fixture()
        schedule[1].update(onset_s=4., end_s=5.)
        for episode in episodes:
            episode['press_coordination']['notes'][1].update(onset_s=4., end_s=5.)
        with self.assertRaisesRegex(ValueError, 'coordination groups'):
            analysis.aggregate(episodes, schedule, sections, 3.)
        group = dict(target_ids=['n0', 'n1'], start_s=4., end_s=5., duration_s=1.,
                     observed_s=1., longest_clean_s=.5, strict_success=False)
        for episode in episodes:
            episode['press_coordination']['groups'] = [copy.deepcopy(group)]
            episode['finger_skill']['source_task_time_s'] = 44.
            for n, r in zip(episode['press_coordination']['notes'], episode['press_completion']['notes']):
                n.update(best_clean_streak_s=1., strict_success=True)
                r['release_status'] = 'released'
        result, _, sr = analysis.aggregate(episodes, schedule, sections, 3.)
        self.assertEqual(result['hold_release_notes'], 640)
        self.assertEqual(sr[0]['section_completed'], 0)

    def test_recovery_discards_uncommitted_tail_and_deduplicates_updates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); a = root/'attempt01'; b = root/'attempt02'
            a.mkdir(); b.mkdir()
            def metric(u, marker):
                return dict(optimizer_updates=u, update_index=u-1, transitions=analysis.BATCH,
                    curriculum=dict(committed_transitions=u*analysis.BATCH), marker=marker)
            (a/'learning_metrics.jsonl').write_text(''.join(json.dumps(metric(u, 'old'))+'\n' for u in range(1, 4)))
            (b/'learning_metrics.jsonl').write_text(json.dumps(metric(2, 'new'))+'\n'+json.dumps(metric(3, 'new'))+'\n'+json.dumps(metric(4, 'tail')))
            chosen = analysis.metric_selection([a, b], {str(a): 2, str(b): 3})
            self.assertEqual(sorted(chosen), [1, 2, 3])
            self.assertEqual(chosen[2][1]['marker'], 'new')
            self.assertNotIn(4, chosen)
            with self.assertRaisesRegex(ValueError, 'committed_prefix'):
                analysis.metric_selection([a], {})

    def test_evaluation_rejects_different_model_and_cross_profile_contract(self):
        info = dict(checkpoint_sha256='model-a', transitions=0)
        settings = dict(compact_press=dict(improvement_profile='corrected'))
        report = dict(completed=True, lifecycle_verified=True, scope='full_song', episodes=32,
            checkpoint_sha256='model-b', first_episode_per_env_per_batch=True,
            failed_episodes_in_denominator=True, training_contract={'profile': 'corrected'},
            settings=dict(num_envs=32, compact_press=dict(improvement_profile='corrected'),
                          simple_start=dict(initial_pose='left_standby_v9')))
        with self.assertRaisesRegex(ValueError, 'different model'):
            analysis.validate_evaluation(report, info, settings, {'profile': 'corrected'}, lambda x: x, 'B')
        report['checkpoint_sha256'] = 'model-a'
        with self.assertRaisesRegex(ValueError, 'own checkpoint'):
            analysis.validate_evaluation(report, info, settings, {'profile': 'preparation'}, lambda x: x, 'B')
        analysis.validate_evaluation(report, info, settings, report['training_contract'], lambda x: x, 'B')


if __name__ == '__main__':
    unittest.main()
