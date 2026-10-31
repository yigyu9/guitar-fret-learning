"""연구 판정·시간 예산·고정 분모·안전 우선 선택을 GPU 없이 검사한다."""
from datetime import datetime, timedelta, timezone
import unittest
import signal
import subprocess
from unittest.mock import Mock
import research


def raw_episode(index, failed=False, success=True):
    return dict(episode=dict(env_id=index, valid=True, reward=.2,
        termination=dict(physical_failure=failed, wrist_failure=failed),
        song=dict(target_count=1, left_success_count=int(success)),
        left_note_ledger=dict(values=dict(clean=[2.], best_clean_streak=[1.5])),
        failure_reasons=['both_failure'] if failed else []))


def report(successes=32):
    return dict(completed=True, episodes=32, summary=dict(count=32, stage_success=successes),
                first_episode_per_env=True)


class ResearchTests(unittest.TestCase):
    def test_union_failures_and_failed_clean_zero(self):
        rows = [raw_episode(index, failed=index == 0) for index in range(32)]
        result = research.summarize_episodes(report(31), rows)
        self.assertEqual(result['safe_success'], 31)
        self.assertEqual(result['failure_episodes'], 1)
        self.assertEqual(result['physical_failure'], 1)
        self.assertEqual(result['wrist_failure'], 1)
        self.assertEqual(result['mean_safe_clean_s'], 62/32.)
        self.assertEqual(result['mean_safe_best_clean_s'], 46.5/32.)

    def test_unique_denominator_and_summary_mismatch_rejected(self):
        rows = [raw_episode(index) for index in range(32)]
        for bad in (rows[:-1], rows+[rows[-1]], rows[:-1]+[rows[0]]):
            with self.assertRaises(ValueError): research.summarize_episodes(report(), bad)
        with self.assertRaises(ValueError): research.summarize_episodes(report(31), rows)
        altered = report(); altered['completed'] = False
        with self.assertRaises(ValueError): research.summarize_episodes(altered, rows)

    def test_stage_thresholds_and_failure_limit(self):
        for stage, minimum in (('A', 24), ('B', 22), ('C50', 16), ('C75', 16), ('C100', 16)):
            result = dict(safe_success=minimum, failure_episodes=1)
            self.assertTrue(research.accepted(stage, result))
            result['safe_success'] -= 1
            self.assertFalse(research.accepted(stage, result))
            result.update(safe_success=minimum, failure_episodes=2)
            self.assertEqual(research.accepted(stage, result), stage == 'A')

    def test_budget_minimum_recent_cost_and_reserved_deadline(self):
        now = datetime(2026, 10, 31, tzinfo=timezone.utc)
        budget = dict(training_deadline_utc=(now+timedelta(seconds=901)).isoformat())
        self.assertTrue(research.training_budget(budget, now=now)['allowed'])
        self.assertFalse(research.training_budget(budget, 700, now=now)['allowed'])
        self.assertEqual(research.training_budget(budget, 700, now=now)['required_seconds'], 1030)
        self.assertFalse(research.training_budget(budget, now=now+timedelta(seconds=2))['allowed'])

    def test_running_deadline_keeps_training_reserve_and_caps_evaluation(self):
        now = datetime(2026, 10, 31, tzinfo=timezone.utc)
        budget = dict(training_deadline_utc=now.isoformat(),
                      deadline_utc=(now+timedelta(minutes=35)).isoformat())
        self.assertTrue(research.deadline_status(budget, 'train', now)['expired'])
        self.assertFalse(research.deadline_status(budget, 'evaluate', now)['expired'])
        self.assertFalse(research.deadline_status(budget, 'evaluate-free-v9', now)['expired'])
        final = research.deadline_status(budget, 'evaluate', now+timedelta(minutes=35))
        self.assertTrue(final['expired'])
        self.assertEqual(final['remaining_seconds'], 0)

    def test_timeout_requests_cleanup_before_forceful_stop(self):
        child = Mock()
        child.poll.return_value = None
        child.wait.side_effect = [subprocess.TimeoutExpired('test', 30),
                                  subprocess.TimeoutExpired('test', 10), 0]
        self.assertEqual(research.interrupt_child(child), ['SIGINT', 'SIGTERM', 'SIGKILL'])
        child.send_signal.assert_called_once_with(signal.SIGINT)
        self.assertEqual(child.wait.call_args_list[0].kwargs, dict(timeout=30))
        self.assertEqual(child.wait.call_args_list[1].kwargs, dict(timeout=10))
        child.terminate.assert_called_once_with()
        child.kill.assert_called_once_with()

    def test_selection_uses_safety_then_safe_clean_then_failures_then_latest(self):
        def row(success, clean, failures, updates):
            return dict(updates=updates, summary=dict(safe_success=success,
                mean_safe_clean_s=clean, failure_episodes=failures))
        candidates = [row(30, 2., 0, 300), row(31, 1., 1, 100), row(31, 1.1, 1, 200),
                      row(31, 1.1, 0, 100), row(31, 1.1, 0, 300)]
        self.assertIs(max(candidates, key=research.selection_key), candidates[-1])

    def test_actual_sealed_runtime_and_completed_reference_episode_reading(self):
        self.assertEqual(len(research.verify_seal()), 64)
        result = research.aggregate(research.STUDY/'runs/index_s3_f4_A_v1/eval_100')
        self.assertEqual(result['count'], 32)
        self.assertEqual(result['safe_success'], 32)
        self.assertEqual(result['failure_episodes'], 0)


if __name__ == '__main__':
    unittest.main()
