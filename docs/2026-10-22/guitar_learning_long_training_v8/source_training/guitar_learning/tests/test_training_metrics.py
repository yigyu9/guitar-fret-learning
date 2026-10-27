import copy
import gzip
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

from guitar_learning.training.training_metrics import LearningMetrics, quality_tick_summary, safety_tick_summary


def physics(step, *, absent=False, displacement=0.):
    flags = [1.]*10
    if absent:
        flags[-1] = 0.
    return dict(physics_step=step, stability=dict(flags=flags,
        guitar_delta_m=[displacement, 0., 0.], guitar_rotation_vector_rad=[0., 0., .1],
        foot_delta_m=[[0., 0., 0.], [.01, 0., 0.]], max_joint_speed_rad_s=2.))


def info(time, role='left', *, done=False, late=0.):
    q = dict(role=role, stage_success=False, timing_achievement=True,
        clean_audible_fraction=1., wrong_press_s=0., missing_press_s=0., audible_wrong_s=0.,
        dropouts=0, release_complete=False, release_clear_dwell_s=0., release_late_s=late,
        strike=dict(accepted_crossing_ids=['a'], extra_crossing_ids=['b'],
            unprepared_crossing_ids=['c'], blocked_event_ids=['b', 'c', 'd'],
            extra_count=1, unprepared_count=1, recovered=True, ready=True,
            ready_dwell_s=.2, recovery_dwell_s=.1))
    result = dict(task_time_s=time, cost=.1, reward_terms={'held': .2}, failure_reasons=[],
        musical_quality=q, action_summary={'active_nonzero': True},
        specialist=dict(role=role, left={'targets': {'goal': {}}}),
        timing=dict(config={'stage_index': 1}, window_s=.5,
            timing_only_stage_success=True, stage_success=False, best_abs_error_s=.02,
            wrong_crossings=1, crossings=[dict(crossing_id='a', error_s=-.02)]),
        music=dict(target_count=1, matched50=0, matched100=0, missed_strict=1))
    if done:
        result.update(termination_reason='timeline_complete', episode=dict(valid=True))
    return result


def row(infos, dones=None):
    return dict(infos=infos, reward=[.2]*len(infos), terminated=dones or [False]*len(infos),
                truncated=[False]*len(infos))


class SafetyTickTests(unittest.TestCase):
    def test_substep_peak_and_contact_gap_are_not_endpoint(self):
        result = safety_tick_summary([physics(1, absent=True, displacement=.09),
            physics(2, absent=True), physics(3), physics(4)])
        self.assertEqual(result['maxima']['guitar_displacement_m'], .09)
        self.assertEqual(result['sample_count'], 4)
        right = result['contacts']['right_foot']
        self.assertEqual(right['absent_s'], 2/240.)
        self.assertEqual(right['prefix_absent_s'], 2/240.)
        self.assertEqual(right['suffix_absent_s'], 0.)

    def test_run_crosses_tick_boundary_and_episode_resets(self):
        metrics = LearningMetrics()
        a = info(4/240.); a['safety240'] = safety_tick_summary(
            [physics(1), physics(2), physics(3, absent=True), physics(4, absent=True)])
        b = info(8/240., done=True); b['safety240'] = safety_tick_summary(
            [physics(5, absent=True), physics(6, absent=True), physics(7, absent=True), physics(8)])
        metrics.observe(row([a]))
        final = metrics.observe(row([b], [True]))[0]
        self.assertAlmostEqual(final['safety240']['contacts']['right_foot']['longest_absent_s'], 5/240.)
        self.assertTrue(final['safety240_complete'])
        c = info(4/240., done=True); c['safety240'] = safety_tick_summary([physics(n) for n in range(101, 105)])
        second = metrics.observe(row([c], [True]))[0]
        self.assertEqual(second['episode_id'], 1)
        self.assertEqual(second['safety240']['contacts']['right_foot']['longest_absent_s'], 0.)

    def test_reject_nonconsecutive_or_nonfinite_physics(self):
        with self.assertRaises(ValueError):
            safety_tick_summary([physics(1), physics(3)])
        bad = physics(1, displacement=float('nan'))
        with self.assertRaises(ValueError):
            safety_tick_summary([bad])

    def test_actual_quality_stamp_not_tick_end_or_release_completion(self):
        target = SimpleNamespace(target_id='goal', end_s=1.)
        samples = []
        for n, clear, clean in [(239, True, False), (240, False, True), (241, True, False), (242, True, False)]:
            samples.append(dict(music=dict(task_time_s=n/240., targets={'goal': {
                'fretting_quality': dict(clean_target_candidate=clean,
                    target_string_contact_evidence_ids=[] if clear else ['id'])}})))
        result = quality_tick_summary(samples, target)
        self.assertEqual(result['first_clean_policy_s'], 1.)
        self.assertEqual(result['first_post_note_clear_policy_s'], 241/240.)
        metrics = LearningMetrics()
        end = info(242/240., done=True); end['quality240'] = result
        episode = metrics.observe(row([end], [True]))[0]
        self.assertAlmostEqual(episode['first_post_note_clear_delay_ms'], 1000/240.)
        self.assertFalse(episode['left']['release_complete'])


class LearningMetricsTests(unittest.TestCase):
    def test_two_workers_cumulative_once_and_update_boundary(self):
        metrics = LearningMetrics()
        metrics.observe(row([info(1., late=1.), info(1., 'right')]))
        first_window = metrics.update_summary()
        self.assertEqual(first_window['completed_episodes'], 0)
        self.assertEqual(len(first_window['open_episodes']), 2)
        finals = metrics.observe(row([info(2., done=True, late=2.), info(2., 'right', done=True)], [True, True]))
        report = metrics.update_summary()
        self.assertEqual(report['transitions'], 2)
        self.assertEqual(report['completed_episodes'], 2)
        self.assertEqual(finals[0]['left']['release_late_s'], 2.)
        self.assertEqual(finals[0]['reward_terms']['held'], .4)
        self.assertIsNone(finals[0]['right'])
        self.assertIsNone(finals[1]['left'])
        self.assertEqual(finals[1]['right']['other_blocked_count'], 1)
        self.assertEqual(finals[1]['right']['first_accepted_signed_error_s'], -.02)
        self.assertEqual(metrics.summary()['transitions'], 4)
        self.assertNotIn('episodes', metrics.summary())
        self.assertEqual(metrics.update_summary()['completed_episodes'], 0)

    def test_safety_completion_timing_quality_and_joint_are_separate(self):
        metrics = LearningMetrics()
        final = metrics.observe(row([info(7., done=True)], [True]))[0]
        self.assertTrue(final['timing_only_success'])
        self.assertFalse(final['quality_stage_success'])
        self.assertEqual(final['joint_music']['matched100'], 0)
        self.assertFalse(final['safety240_complete'])
        group = metrics.summary()['groups'][0]
        self.assertEqual(group['episodes'], 1)
        self.assertEqual(group['timing_only_successes'], 1)
        self.assertEqual(group['quality_successes'], 0)

    def test_done_without_episode_and_explicit_timeout_never_fake_success(self):
        metrics = LearningMetrics()
        closed = metrics.observe(row([info(1.)], [True]))[0]
        self.assertFalse(closed['complete'])
        self.assertIsNone(closed['timing_only_success'])
        metrics.observe(row([info(1.)]))
        timeout = metrics.close_incomplete('worker_timeout')[0]
        self.assertFalse(timeout['complete'])
        self.assertEqual(metrics.summary()['completed_episodes'], 0)
        self.assertEqual(metrics.summary()['timeout_episodes'], 1)

    def test_unreported_reset_closes_old_episode_without_history_leak(self):
        metrics = LearningMetrics()
        metrics.observe(row([info(2., late=9.)]))
        abandoned = metrics.observe(row([info(.1)]))[0]
        self.assertEqual(abandoned['reason'], 'reset_without_terminal')
        final = metrics.observe(row([info(.2, done=True, late=.01)], [True]))[0]
        self.assertEqual(final['episode_id'], 1)
        self.assertEqual(final['left']['release_late_s'], .01)

    def test_invalid_terminal_is_not_success_denominator(self):
        metrics = LearningMetrics()
        value = info(7., done=True); value['episode']['valid'] = False
        metrics.observe(row([value], [True]))
        self.assertEqual(metrics.summary()['invalid_episodes'], 1)
        self.assertEqual(metrics.summary()['completed_episodes'], 0)

    def test_preparation_boundary_and_old_action_fallback_use_active_hand(self):
        metrics = LearningMetrics()
        a = info(2., 'right'); a.pop('action_summary'); a['debug'] = {'action': [1.]*33+[0.]*6}
        metrics.observe(row([a]))
        metrics.observe(row([info(2.01, 'right')]))
        prep = metrics.summary()['preparation']
        self.assertEqual(prep['total_logged_transitions'], 2)
        self.assertEqual(prep['first2s_logged_transitions'], 1)
        self.assertEqual(prep['first2s_action_observed_transitions'], 1)
        self.assertEqual(prep['first2s_nonzero_action_transitions'], 0)
        self.assertEqual(prep['first2s_reward_terms'], {'held': .2})

    def test_input_not_mutated_and_summary_is_independent(self):
        metrics = LearningMetrics()
        value = row([info(7., done=True)], [True]); original = copy.deepcopy(value)
        closed = metrics.observe(value)
        closed[0]['left']['release_late_s'] = 100.
        self.assertEqual(value, original)
        self.assertEqual(metrics.update_summary()['episodes'][0]['left']['release_late_s'], 0.)

    def test_success_sources_and_missing_measurement_denominators_are_separate(self):
        metrics = LearningMetrics()
        first = info(7., done=True)
        first['specialist']['stage_success'] = True
        records = metrics.observe(row([first], [True]))
        self.assertTrue(records[0]['specialist_stage_success'])
        self.assertFalse(records[0]['timing_stage_success'])
        second = info(7., done=True)
        second.pop('musical_quality')
        second['timing'].pop('stage_success')
        metrics.observe(row([second], [True]))
        summary = metrics.summary()
        self.assertEqual(summary['completed_episodes'], 2)
        self.assertEqual(summary['specialist_successful_episodes'], 1)
        self.assertEqual(summary['specialist_evaluated_episodes'], 1)
        self.assertEqual(summary['specialist_success_rate'], 1.)
        self.assertEqual(summary['timing_successful_episodes'], 0)
        self.assertEqual(summary['timing_stage_evaluated_episodes'], 1)
        self.assertEqual(summary['timing_evaluated_episodes'], 2)
        self.assertEqual(summary['quality_evaluated_episodes'], 1)
        group = summary['groups'][0]
        self.assertEqual(group['episodes'], 2)
        self.assertEqual(group['specialist_evaluated_episodes'], 1)
        self.assertEqual(group['timing_stage_evaluated_episodes'], 1)
        self.assertEqual(group['quality_evaluated_episodes'], 1)
        window = metrics.update_summary()
        self.assertEqual(window['specialist_successful_episodes'], summary['specialist_successful_episodes'])
        self.assertEqual(window['groups'], summary['groups'])

    def test_global_state_does_not_keep_closed_episode_history(self):
        metrics = LearningMetrics()
        final = row([info(7., done=True)], [True])
        for index in range(1000):
            metrics.observe(final)
            metrics.update_summary()
        self.assertFalse(hasattr(metrics, 'episodes'))
        self.assertEqual(metrics.active, {})
        self.assertEqual(metrics.window_episodes, [])
        self.assertEqual(len(metrics.groups), 1)
        self.assertEqual(metrics.summary()['completed_episodes'], 1000)
        self.assertNotIn('episodes', metrics.summary())

    def test_goal_fallback_preserved_when_compact_omits_legacy_targets(self):
        metrics = LearningMetrics()
        final = info(7., 'right', done=True)
        final['specialist'].pop('left')
        final['musical_quality']['strike']['target_id'] = 'actual-goal'
        metrics.observe(row([final], [True]))
        self.assertEqual(metrics.summary()['groups'][0]['goal_ids'], ['actual-goal'])


class SavedTraceRegressionTests(unittest.TestCase):
    def test_saved_native_training_ledgers_and_interval_rewards(self):
        phase = Path(__file__).resolve().parents[2]/'docs/2026-10-12/stability_adapter_2/results/guitar_learning_musical_quality_v1'
        if not phase.is_dir():
            self.skipTest('saved native audit data unavailable')
        for folder, role in [('left_native_train_v2', 'left'), ('right_native_train_v1', 'right')]:
            with self.subTest(role=role):
                metrics = LearningMetrics()
                with gzip.open(phase/folder/'transitions.jsonl.gz', 'rt') as stream:
                    for line in stream:
                        closed = metrics.observe(json.loads(line))
                old = json.loads((phase/folder/'musical_quality_report.json').read_text())
                report = metrics.summary()
                self.assertEqual(report['transitions'], 420)
                self.assertEqual(report['completed_episodes'], 1)
                self.assertEqual(report['quality_successful_episodes'], 0)
                self.assertEqual(report['timing_only_successful_episodes'], 1)
                for key, value in old['reward_terms'].items():
                    self.assertAlmostEqual(report['reward_terms'][key], value, places=10)
                self.assertEqual(report['preparation']['first2s_logged_transitions'], 120)
                self.assertFalse(closed[0]['safety240_complete'])
                if role == 'left':
                    self.assertAlmostEqual(closed[0]['left']['release_late_s'], 2.5478)
                    self.assertEqual(closed[0]['left']['clean_audible_fraction'], 1.)
                else:
                    self.assertAlmostEqual(closed[0]['right']['first_accepted_signed_error_s'], .177248588182378)
                    self.assertEqual(closed[0]['right']['extra_count'], 1)


if __name__ == '__main__':
    unittest.main()
