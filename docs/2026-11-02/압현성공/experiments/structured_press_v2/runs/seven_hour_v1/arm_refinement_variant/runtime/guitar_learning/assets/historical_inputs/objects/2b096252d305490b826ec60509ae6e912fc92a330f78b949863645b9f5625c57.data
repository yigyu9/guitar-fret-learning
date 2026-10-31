"""Operational CLI moves preserve paths, source pins and replay helpers."""
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ('audit_musical_quality_v2', 'recover_training_log',
         'render_pick_grip_v1', 'render_timing_video_v1',
         'run_fretting_probe_v3', 'validate')


class OperationalToolCleanupTests(unittest.TestCase):
    def test_module_and_direct_cli_help(self):
        for name in TOOLS:
            for arguments, directory in (
                    (['-m', 'guitar_learning.tool.' + name], ROOT),
                    ([str(ROOT / 'guitar_learning/tool' / (name + '.py'))], '/tmp')):
                with self.subTest(tool=name, arguments=arguments):
                    result = subprocess.run([sys.executable, '-B'] + arguments + ['--help'],
                                            cwd=directory, text=True, capture_output=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn('usage:', result.stdout)

    def test_project_paths_and_shared_replay_helpers(self):
        from guitar_learning.tool import _rendering, render_timing_video_v1, render_pick_grip_v1
        from guitar_learning.tool.experiments.local_skills import render
        for name in ('audit_musical_quality_v2', 'render_pick_grip_v1', 'render_timing_video_v1'):
            self.assertEqual(importlib.import_module('guitar_learning.tool.' + name).ROOT, ROOT)
        self.assertIs(render.encoder, _rendering.encoder)
        self.assertIs(render.probe, _rendering.probe)
        self.assertIs(render_timing_video_v1.encoder, _rendering.encoder)
        self.assertEqual(render.INITIAL, render_pick_grip_v1.INITIAL)
        self.assertTrue(_rendering.INITIAL.is_file())

    def test_audit_pins_current_tool_and_classifier_sources(self):
        from guitar_learning.tool import audit_musical_quality_v2 as audit
        inputs = audit.Inputs()
        with tempfile.TemporaryDirectory() as output, \
                patch.object(audit, 'Inputs', return_value=inputs), \
                patch.object(audit, 'analyze_left', side_effect=InterruptedError('stop after pins')):
            with self.assertRaisesRegex(InterruptedError, 'stop after pins'):
                audit.audit(output)
        self.assertEqual(set(inputs.files), {
            str(ROOT / 'guitar_learning/tool/audit_musical_quality_v2.py'),
            *(str(ROOT / 'guitar_learning' / name) for name in (
                'quality/fretting_quality.py', 'core/fretting_v1.py', 'core/geometry_v1.py',
                'music_task.py', 'core/strike.py', 'quality/strike_quality.py'))})
        self.assertEqual(inputs.verify(), [])

    def test_fixed_rate_encoder_and_probe(self):
        from guitar_learning.tool import _rendering
        with patch.object(_rendering.subprocess, 'Popen') as encoder:
            _rendering.encoder(Path('/tmp/movie.mp4'))
        command = encoder.call_args.args[0]
        self.assertEqual(command[command.index('-s') + 1], '1280x720')
        self.assertEqual(command[command.index('-r') + 1], '60')
        self.assertEqual(command[command.index('-pix_fmt') + 1], 'rgb24')
        self.assertIn('-n', command)
        with tempfile.NamedTemporaryFile() as movie:
            metadata = dict(width=1280, height=720, avg_frame_rate='60/1',
                            nb_read_frames='120', duration='2.000000')
            with patch.object(_rendering.subprocess, 'run') as probe:
                probe.return_value.stdout = json.dumps(dict(streams=[metadata]))
                result = _rendering.probe(Path(movie.name), 120)
                self.assertEqual(result['stream'], metadata)
                with self.assertRaisesRegex(ValueError, 'video coverage mismatch'):
                    _rendering.probe(Path(movie.name), 121)


if __name__ == '__main__':
    unittest.main()
