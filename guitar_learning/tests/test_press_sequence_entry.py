"""목표 선택·원래 CLI 옵션 전달·재개 제한을 CPU에서 검사한다."""
import contextlib
import builtins
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from guitar_learning.tool.experiments import press_sequence as entry


def saved_settings(case='C1'):
    bundle = entry.BUNDLES[case]
    return dict(song_training=dict(song_id=bundle, bundle=str(entry.ROOT / 'data/song_bundles' / bundle)))


class PressSequenceEntryTests(unittest.TestCase):
    def test_all_six_cases_forward_existing_v5_options_as_argv(self):
        for case in entry.CASES:
            args = entry.parser().parse_args(['train', case, '--out', 'unused', '--num-envs', '64',
                '--horizon', '128', '--updates', '20', '--initial-finger-std', '.4',
                '--initial-support-std', '.2', '--improvement-profile', 'full_hold', '--include-pelvis'])
            with patch.object(entry, 'checked_target', return_value=dict(case_id=case)) as check:
                command = entry.native_command(args)
            check.assert_called_once_with(case)
            self.assertEqual(command[1:4], ['-m', entry.WRAPPER_MODULE, '_native'])
            start = command.index('train')
            native = entry.native_entry().parser().parse_args(command[start:])
            self.assertEqual(native.song, entry.BUNDLES[case])
            self.assertEqual(native.num_envs, 64)
            self.assertEqual(native.horizon, 128)
            self.assertEqual(native.updates, 20)
            self.assertEqual(native.initial_finger_std, .4)
            self.assertEqual(native.initial_support_std, .2)
            self.assertEqual(native.improvement_profile, 'full_hold')
            self.assertTrue(native.include_pelvis)
            self.assertEqual(native.out, (Path.cwd() / 'unused').resolve())
            self.assertIsNone(args.song)

    def test_no_shell_and_native_return_code_preserved(self):
        suspicious = 'output;$(touch SHOULD_NOT_EXIST)'
        with patch.object(entry, 'checked_target', return_value={}), \
                patch.object(entry.subprocess, 'run', return_value=SimpleNamespace(returncode=7)) as run:
            self.assertEqual(entry.main(['train', 'C1', '--out', suspicious]), 7)
        argv = run.call_args[0][0]
        self.assertIn(str((Path.cwd() / suspicious).resolve()), argv)
        self.assertFalse(run.call_args.kwargs['shell'])
        self.assertEqual(run.call_args.kwargs['cwd'], entry.ROOT)
        self.assertFalse((Path.cwd() / 'SHOULD_NOT_EXIST').exists())

    def test_missing_target_song_bypass_and_unknown_all_are_rejected(self):
        for argv in (['train', '--out', 'unused'],
                ['train', 'C1', '--out', 'unused', '--song', entry.BUNDLES['C1']],
                ['train', 'C1', '--out', 'unused', '--all'],
                ['check'], ['check', 'C1', '--all'], ['list', '--all']):
            with self.subTest(argv=argv), patch.object(entry.subprocess, 'run') as run, \
                    contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                entry.main(argv)
            run.assert_not_called()

    def test_resume_keeps_saved_target_and_rejects_other_target_or_bundle_path(self):
        for case in entry.CASES:
            args = entry.parser().parse_args(['train', '--resume', 'saved.pt', '--out', 'unused'])
            with patch.object(entry.native_entry(), 'read_checkpoint', return_value=saved_settings(case)) as reader, \
                    patch.object(entry, 'checked_target', return_value={}) as check, \
                    patch.object(entry, 'verify_checkpoint_clock') as clock:
                command = entry.native_command(args)
            reader.assert_called_once_with(Path('saved.pt'))
            check.assert_called_once_with(case)
            clock.assert_called_once_with(Path('saved.pt'), {})
            native = entry.native_entry().parser().parse_args(command[command.index('train'):])
            self.assertIsNone(native.song)
            self.assertEqual(native.resume, Path('saved.pt').resolve())
        args = entry.parser().parse_args(['train', 'C2', '--resume', 'saved.pt', '--out', 'unused'])
        with patch.object(entry.native_entry(), 'read_checkpoint', return_value=saved_settings()), self.assertRaises(ValueError):
            entry.native_command(args)
        for saved in (dict(song_training=dict(song_id='other', bundle='/tmp/other')),
                dict(song_training=dict(song_id=entry.BUNDLES['C1'], bundle='/tmp/other'))):
            args = entry.parser().parse_args(['train', '--resume', 'saved.pt', '--out', 'unused'])
            with patch.object(entry.native_entry(), 'read_checkpoint', return_value=saved), self.assertRaises(ValueError):
                entry.native_command(args)

    def test_evaluate_render_always_call_strict_reader_and_keep_checkpoint(self):
        for command in ('evaluate', 'render'):
            args = entry.parser().parse_args([command, 'saved.pt', '--out', 'unused', '--num-envs', '2'])
            with patch.object(entry.native_entry(), 'read_checkpoint', return_value=saved_settings('C6')) as reader, \
                    patch.object(entry, 'checked_target', return_value={}), \
                    patch.object(entry, 'verify_checkpoint_clock') as clock:
                argv = entry.native_command(args)
            reader.assert_called_once_with(Path('saved.pt'))
            clock.assert_called_once_with(Path('saved.pt'), {})
            native = entry.native_entry().parser().parse_args(argv[argv.index(command):])
            self.assertEqual(native.checkpoint, Path('saved.pt').resolve())
            self.assertEqual(native.num_envs, 2)
            self.assertEqual(native.scope, 'full_song')
        for command in ('train', 'evaluate', 'render'):
            argv = ['train', '--resume', 'saved.pt', '--out', 'unused'] if command == 'train' else [command, 'saved.pt', '--out', 'unused']
            with patch.object(entry.native_entry(), 'read_checkpoint', side_effect=ValueError('input sources changed')), \
                    patch.object(entry.subprocess, 'run') as run, contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                entry.main(argv)
            run.assert_not_called()

    def test_check_all_is_cpu_only_and_validates_all_cases(self):
        with patch.object(entry, 'checked_target', side_effect=lambda case: dict(case_id=case)) as check, \
                patch.object(entry.subprocess, 'run') as run, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(entry.main(['check', '--all']), 0)
        self.assertEqual([call.args[0] for call in check.call_args_list], list(entry.CASES))
        run.assert_not_called()

    def test_preparation_api_result_and_missing_bundle_errors_are_preserved(self):
        report = dict(case_id='C1', bundle_id=entry.BUNDLES['C1'], completed=True)
        prepare = SimpleNamespace(check_target=lambda target: report)
        with patch.dict(sys.modules, {'guitar_learning.tool.prepare_press_targets': prepare}):
            self.assertEqual(entry.checked_target('C1'), report)
            report['completed'] = False
            with self.assertRaises(ValueError):
                entry.checked_target('C1')
        with patch.object(entry, 'checked_target', side_effect=FileNotFoundError('등록 번들 없음')), \
                patch.object(entry.subprocess, 'run') as run, contextlib.redirect_stderr(io.StringIO()), \
                self.assertRaises(SystemExit):
            entry.main(['train', 'C1', '--out', 'unused'])
        run.assert_not_called()

    def test_help_requires_neither_target_preparation_nor_native_execution(self):
        for argv in (['--help'], ['train', '--help'], ['check', '--help']):
            with patch.object(entry, 'checked_target') as check, patch.object(entry.subprocess, 'run') as run, \
                    contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as error:
                entry.main(argv)
            self.assertEqual(error.exception.code, 0)
            check.assert_not_called()
            run.assert_not_called()

    def test_native_child_import_order_adapter_and_success_exit_code(self):
        events = []
        original_import = builtins.__import__
        original_entry = entry.native_entry()
        original_argv = sys.argv
        @contextlib.contextmanager
        def adapter():
            events.append('adapter enter')
            try:
                yield
            finally:
                events.append('adapter exit')
        def tracking_import(name, *args, **kwargs):
            if name == 'isaacgym':
                events.append('isaacgym')
            return original_import(name, *args, **kwargs)
        def existing_entry():
            events.append('v5 entry')
            return original_entry
        def original_main():
            self.assertIn('--song', sys.argv)
            events.append('v5 main')
            return dict(completed=True)
        prepare = SimpleNamespace(source_clock_runtime=adapter)
        with patch.dict(sys.modules, {'isaacgym': SimpleNamespace(),
                'guitar_learning.tool.prepare_press_targets': prepare}), \
                patch('builtins.__import__', side_effect=tracking_import), \
                patch.object(entry, 'native_entry', side_effect=existing_entry), \
                patch.object(entry, 'checked_target', return_value={}), \
                patch.object(original_entry, 'main', side_effect=original_main):
            self.assertEqual(entry.native_main(['train', '--song', entry.BUNDLES['C1'], '--out', 'unused']), 0)
        self.assertIs(sys.argv, original_argv)
        self.assertEqual(events, ['isaacgym', 'v5 entry', 'adapter enter', 'v5 main', 'adapter exit'])

    def test_native_child_restores_argv_and_adapter_on_error(self):
        events = []
        original_argv = sys.argv
        @contextlib.contextmanager
        def adapter():
            try:
                yield
            finally:
                events.append('adapter exit')
        with patch.dict(sys.modules, {'isaacgym': SimpleNamespace(),
                'guitar_learning.tool.prepare_press_targets': SimpleNamespace(source_clock_runtime=adapter)}), \
                patch.object(entry, 'checked_target', return_value={}), \
                patch.object(entry.native_entry(), 'main', side_effect=RuntimeError('native failure')):
            with self.assertRaisesRegex(RuntimeError, 'native failure'):
                entry.native_main(['train', '--song', entry.BUNDLES['C1'], '--out', 'unused'])
            with self.assertRaisesRegex(ValueError, '등록된'):
                entry.native_main(['train', '--song', 'other_song', '--out', 'unused'])
        self.assertIs(sys.argv, original_argv)
        self.assertEqual(events, ['adapter exit'])

    def test_checkpoint_exact_clock_required_after_original_strict_reader(self):
        import copy
        import torch
        schema = 'guitar_learning.press_sequence_source_clock.v1'
        clock = dict(schema=schema, bundle_id=entry.BUNDLES['C1'],
            clock_contract_sha256='a' * 64, onset_mapping_sha256='b' * 64)
        report = dict(clock_schema=schema, **{key: value for key, value in clock.items() if key != 'schema'})
        payload = dict(identity=dict(architecture=dict(contract=dict(task=dict(provenance=dict(left_press_clock=clock))))))
        with tempfile.TemporaryDirectory() as folder, patch.dict(sys.modules, {
                'guitar_learning.tool.prepare_press_targets': SimpleNamespace(SCHEMA=schema)}):
            path = Path(folder) / 'saved.pt'
            torch.save(payload, path)
            entry.verify_checkpoint_clock(path, report)
            for key in clock:
                bad = copy.deepcopy(payload)
                bad['identity']['architecture']['contract']['task']['provenance']['left_press_clock'][key] = 'wrong'
                torch.save(bad, path)
                with self.subTest(key=key), self.assertRaises(ValueError):
                    entry.verify_checkpoint_clock(path, report)
            torch.save(dict(identity={}), path)
            with self.assertRaises(ValueError):
                entry.verify_checkpoint_clock(path, report)
        events = []
        def strict(checkpoint):
            events.append('strict')
            return saved_settings()
        def checked(target):
            events.append('check')
            return report
        def verified(checkpoint, current):
            events.append('clock')
        args = entry.parser().parse_args(['train', '--resume', 'saved.pt', '--out', 'unused'])
        with patch.object(entry.native_entry(), 'read_checkpoint', side_effect=strict), \
                patch.object(entry, 'checked_target', side_effect=checked), \
                patch.object(entry, 'verify_checkpoint_clock', side_effect=verified):
            entry.native_command(args)
        self.assertEqual(events, ['strict', 'check', 'clock'])

    def test_registered_six_cases_check_and_catalog_without_native_execution(self):
        with patch.object(entry.subprocess, 'run') as run, contextlib.redirect_stdout(io.StringIO()) as stream:
            self.assertEqual(entry.main(['list']), 0)
        rows = json.loads(stream.getvalue())
        self.assertEqual([row['case_id'] for row in rows], list(entry.CASES))
        self.assertTrue(all(row['ready'] for row in rows))
        run.assert_not_called()
        with patch.object(entry.subprocess, 'run') as run, contextlib.redirect_stdout(io.StringIO()) as stream:
            self.assertEqual(entry.main(['check', '--all']), 0)
        reports = json.loads(stream.getvalue())
        for case, report in zip(entry.CASES, reports):
            self.assertEqual(report['case_id'], case)
            self.assertEqual(report['bundle_id'], entry.BUNDLES[case])
            self.assertTrue(report['completed'])
            self.assertEqual(report['source_note_count'], 20)
            self.assertEqual(report['target_count'], 20)
            self.assertEqual(report['policy_duration_s'], 47.25)
            self.assertEqual(report['control_ticks'], 2835)
        run.assert_not_called()

    def test_original_pins_cover_wrapper_preparer_and_every_bundle_file(self):
        from guitar_learning.tool.prepare_press_targets import source_clock_runtime
        from guitar_learning.training.finger_skill_runner import _pins
        from guitar_learning.training.training_log_io import write
        from guitar_learning.portability import portable
        with source_clock_runtime():
            settings = entry.native_entry().build_settings(song=entry.BUNDLES['C1'], num_envs=2, updates=1)
        with tempfile.TemporaryDirectory(dir=entry.ROOT / 'runs') as folder:
            folder = Path(folder)
            write(folder / 'settings.json', portable(settings))
            pins = _pins(settings, folder)
        required = [entry.ROOT / 'guitar_learning/tool/experiments/press_sequence.py',
            entry.ROOT / 'guitar_learning/tool/prepare_press_targets.py']
        bundle = entry.ROOT / 'data/song_bundles' / entry.BUNDLES['C1']
        required.extend(path for path in bundle.rglob('*') if path.is_file())
        self.assertTrue(all(str(path.resolve()) in pins for path in required))


if __name__ == '__main__':
    unittest.main()
