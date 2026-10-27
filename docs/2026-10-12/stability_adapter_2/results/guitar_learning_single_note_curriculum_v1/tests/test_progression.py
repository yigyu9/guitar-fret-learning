import copy
import json
import tempfile
import io
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch
import signal

PATH = Path(__file__).resolve().parents[1] / 'watch_and_expand_v1.py'
spec = importlib.util.spec_from_file_location('single_note_progression', PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def row(success=True):
    return dict(episode=dict(valid=True, reason='timeline_complete', steps=420,
                            task_time_s=7., musical_quality=dict(stage_success=success)),
                metrics=dict(role='left', complete=True, valid=True,
                             physical_failure=False, quality_stage_success=success))


class ProgressionGateTests(unittest.TestCase):
    def test_success_requires_full_window(self):
        self.assertFalse(module.recent_gate([row()] * 63, 'left')['passed'])
        self.assertTrue(module.recent_gate([row()] * 64, 'left')['passed'])

    def test_ninety_percent_and_recent_window(self):
        self.assertTrue(module.recent_gate([row(False)] * 10 + [row()] * 58 + [row(False)] * 6, 'left')['passed'])
        self.assertFalse(module.recent_gate([row()] * 57 + [row(False)] * 7, 'left')['passed'])

    def test_physical_failure_blocks_even_high_success(self):
        rows = [row() for _ in range(64)]
        rows[-1]['metrics']['physical_failure'] = True
        self.assertFalse(module.recent_gate(rows, 'left')['passed'])

    def test_invalid_terminal_stays_in_denominator(self):
        rows = [row() for _ in range(64)]
        rows[-1]['episode']['reason'] = 'terminal_failure'
        result = module.recent_gate(rows, 'left')
        self.assertEqual(result['evaluated_episodes'], 64)
        self.assertEqual(result['unsafe_episodes'], 1)
        self.assertFalse(result['passed'])

    def test_open_prefix_not_counted(self):
        self.assertFalse(module.recent_gate([row()] * 63 + [dict(episode=None)], 'left')['passed'])

    def test_role_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            module.recent_gate([row()], 'right')

    def test_deterministic_gate_requires_quality_and_safety(self):
        result = dict(completed=True, source_unchanged=True, episodes=[row()['episode'] for _ in range(4)])
        self.assertTrue(module.evaluation_gate(result, 4)['passed'])
        result['episodes'][0]['musical_quality']['stage_success'] = False
        self.assertFalse(module.evaluation_gate(result, 4)['passed'])
        result['episodes'][0] = row()['episode']
        result['episodes'][0]['reason'] = 'terminal_failure'
        self.assertFalse(module.evaluation_gate(result, 4)['passed'])

    def test_evaluation_requires_complete_unchanged_evidence(self):
        good = dict(completed=True, source_unchanged=True, episodes=[row()['episode'] for _ in range(4)])
        for key in ('completed', 'source_unchanged'):
            bad = copy.deepcopy(good)
            bad[key] = False
            self.assertFalse(module.evaluation_gate(bad, 4)['passed'])
        good['episodes'].pop()
        self.assertFalse(module.evaluation_gate(good, 4)['passed'])


class CleanupTests(unittest.TestCase):
    def runner(self):
        runner = module.Progression({}, Path('/tmp/unused_progression_test'))
        runner.save = Mock()
        return runner

    def child(self, pid):
        process = Mock(pid=pid)
        process.poll.return_value = None
        return dict(process=process, stream=Mock(), label='test')

    def test_exit_race_does_not_skip_other_child_or_close(self):
        runner = self.runner()
        one, two = self.child(1001), self.child(1002)
        runner.children = [one, two]
        def send(pid, sig):
            if pid == 1001:
                one['process'].poll.return_value = 0
                raise ProcessLookupError()
            two['process'].poll.return_value = 0
        with patch.object(module.os, 'getpgid', side_effect=lambda pid: pid), \
                patch.object(module.os, 'killpg', side_effect=send) as kill:
            runner.cleanup()
        self.assertEqual(kill.call_count, 2)
        one['stream'].close.assert_called_once()
        two['stream'].close.assert_called_once()
        self.assertEqual(runner.state['surviving_owned_children'], [])

    def test_only_owned_session_gets_escalation(self):
        runner = self.runner()
        child = self.child(1001)
        runner.children = [child]
        def send(pid, sig):
            if sig == signal.SIGKILL:
                child['process'].poll.return_value = -9
        with patch.object(module.os, 'getpgid', return_value=1001), \
                patch.object(module.os, 'killpg', side_effect=send) as kill, \
                patch.object(module.time, 'monotonic', side_effect=range(0, 100000, 1000)):
            runner.cleanup()
        self.assertEqual([c.args[1] for c in kill.call_args_list],
                         [signal.SIGINT, signal.SIGTERM, signal.SIGKILL])
        self.assertEqual(runner.state['surviving_owned_children'], [])

    def test_status_io_failure_does_not_interrupt_cleanup(self):
        runner = self.runner()
        child = self.child(1001)
        runner.children = [child]
        runner.save.side_effect = OSError('status disk failure')
        def send(pid, sig):
            if sig == signal.SIGKILL:
                child['process'].poll.return_value = -9
        # Each signal receives one cleanup loop iteration before its grace expires.
        ticks = [0, 0, 400, 400, 400, 800, 800]
        with patch.object(module.os, 'getpgid', return_value=1001), \
                patch.object(module.os, 'killpg', side_effect=send) as kill, \
                patch.object(module.time, 'monotonic', side_effect=ticks), \
                patch.object(module.time, 'sleep'):
            runner.cleanup()
        self.assertEqual([c.args[1] for c in kill.call_args_list],
                         [signal.SIGINT, signal.SIGTERM, signal.SIGKILL])
        child['stream'].close.assert_called_once()
        self.assertTrue(any(x.get('component') == 'cleanup_status' for x in runner.state['cleanup']))

    def test_changed_session_identity_is_never_signalled(self):
        runner = self.runner()
        runner.children = [self.child(1001)]
        with patch.object(module.os, 'getpgid', return_value=9999), \
                patch.object(module.os, 'killpg') as kill, \
                patch.object(module.time, 'monotonic', side_effect=range(0, 100000, 1000)):
            runner.cleanup()
        kill.assert_not_called()
        self.assertEqual(runner.state['surviving_owned_children'], [1001])


class ProgressionOutcomeTests(unittest.TestCase):
    def prepare(self, root, mastered):
        original, single, out = root/'original', root/'single', root/'watch'
        for path in (original, single, out):
            path.mkdir()
        (original/'result.json').write_text('{}')
        (single/'report.json').write_text(json.dumps(dict(completed=True, failure=None)))
        (single/'episodes.jsonl').write_text(''.join(json.dumps(row(mastered))+'\n' for _ in range(64)))
        evaluation = out/'single_left_evaluation_v1'
        evaluation.mkdir()
        (evaluation/'musical_quality_result.json').write_text(json.dumps(dict(completed=True,
            source_unchanged=True, episodes=[row(mastered)['episode'] for _ in range(4)])))
        preflight = out/'pool_left_preflight_v1'
        preflight.mkdir()
        (preflight/'result.json').write_text(json.dumps(dict(completed=True, source_unchanged=True,
            covered_event_indices=[0, 2], episodes=[row()['episode'] for _ in range(2)])))
        plan = dict(original_supervisor=str(original), original_deadline_utc='2030-01-01T00:00:00+00:00',
                    pin_manifests=[], training_window=64, minimum_training_rate=.9,
                    evaluation_episodes=4, goal_event_indices=[0, 2], jobs=[dict(role='left',
                    single_run=str(single), single_settings='unused.json', expanded_settings='unused2.json',
                    expanded_run=str(root/'expanded'))])
        runner = module.Progression(plan, out)
        runner.start = Mock(return_value=dict(process=Mock(returncode=2)))
        return runner

    def test_nonzero_expanded_exit_and_missing_report_are_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            runner = self.prepare(Path(directory), True)
            runner.wait = Mock(side_effect=[True, True, False])
            self.assertEqual(runner.run(), 2)
            self.assertEqual(runner.state['phase'], 'expanded_execution_failed')
            self.assertFalse(runner.state['execution_ok'])
            self.assertTrue(runner.state['hands']['left']['advanced'])

    def test_quality_miss_is_recorded_without_launching_expansion(self):
        with tempfile.TemporaryDirectory() as directory:
            runner = self.prepare(Path(directory), False)
            runner.wait = Mock(return_value=True)
            self.assertEqual(runner.run(), 0)
            self.assertEqual(runner.state['phase'], 'single_note_not_mastered')
            self.assertEqual(runner.start.call_count, 1)
            self.assertFalse(runner.state['hands']['left']['advanced'])


class PrimaryFailureTests(unittest.TestCase):
    def test_secondary_persistence_failure_preserves_primary_exception(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = root/'plan.json'
            plan.write_text('{}')
            with patch.object(module.sys, 'argv', ['watch', '--plan', str(plan), '--out', str(root/'watch')]), \
                    patch.object(module.Progression, 'run', side_effect=RuntimeError('primary failure')), \
                    patch.object(module.Progression, 'cleanup'), \
                    patch.object(module.Progression, 'save', side_effect=OSError('secondary save')), \
                    patch.object(module, 'write', side_effect=OSError('secondary write')), \
                    patch.object(module.sys, 'stderr', new=io.StringIO()):
                with self.assertRaisesRegex(RuntimeError, 'primary failure'):
                    module.main()


if __name__ == '__main__':
    unittest.main()
