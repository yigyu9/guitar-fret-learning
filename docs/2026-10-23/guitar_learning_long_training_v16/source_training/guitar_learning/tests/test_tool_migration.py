"""Migrated offline tools produce current song inputs without historical code."""
import contextlib
import hashlib
import importlib.abc
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ('register_song_bundle', 'build_fret_training_data',
         'build_strike_training_data', 'build_strike_plan',
         'audit_strike_goal_quality', 'render_timeline')

if os.environ.get('GL_TOOL_BLOCK_OLD'):
    blocked = tuple(str(ROOT / name) + os.sep for name in
                    ('fret', 'full', 'stability_adapter', 'stability_adapter_2',
                     'strike', 'tab2body', 'archive'))

    class BlockHistoricalImports(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if fullname.split('.')[0] in {
                    'fret', 'full', 'stability_adapter', 'stability_adapter_2',
                    'strike', 'tab2body', 'torch', 'isaacgym'}:
                raise ImportError('forbidden tool import: ' + fullname)

    sys.meta_path.insert(0, BlockHistoricalImports())

    def block_historical_reads(event, args):
        if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
            filename = str(Path(os.fsdecode(args[0])).absolute())
            if filename.startswith(blocked):
                raise RuntimeError('forbidden tool input: ' + filename)

    sys.addaudithook(block_historical_reads)

from guitar_learning.tool import (
    register_song_bundle, build_fret_training_data, build_strike_training_data,
    build_strike_plan, audit_strike_goal_quality,
)
from guitar_learning.score.canonical import compile_song_bundle_events
from guitar_learning.score.strike_goal_compiler import compiled_strike_goal_from_plan_document
from guitar_learning.tool._strike_goal_compiler import strike_plan_document


class ToolMigrationTests(unittest.TestCase):
    def test_reviewed_stage1_to_current_canonical_input(self):
        with tempfile.TemporaryDirectory(prefix='guitar_tools_') as temporary:
            base = Path(temporary)
            stage1 = base / 'stage1'
            stage1.mkdir()
            notes = [dict(t_on=1., t_off=1.4, string=0, fret=3, midi=43,
                          finger=1, barre=False, grip=None),
                     dict(t_on=2., t_off=2.4, string=1, fret=3, midi=48,
                          finger=1, barre=False, grip=None)]
            fingering = dict(
                notes=notes, convention='string 0 = low-E (CSV/모델 관례)',
                presses=[dict(finger=1, string=n['string'], fret=3,
                              barre=False, t_press=n['t_on']-.1,
                              t_release=n['t_off'], strikes=[n['t_on']])
                         for n in notes],
                hand=[dict(t=0., P=3, grip=None)],
                stats=dict(dropped_invalid_fret=0), diagnostics=[], violations=[])
            (stage1 / 'fixture.fingering.json').write_text(json.dumps(fingering))
            for name in ('fixture.chords.json', 'fixture.notes.json'):
                (stage1 / name).write_text('{}')
            (stage1 / 'fixture.notes.csv').write_text(
                'string,start,end,pitch\n0,1.0,1.4,43\n1,2.0,2.4,48\n')
            (stage1 / 'fixture_mic.wav').write_bytes(b'reviewed-audio-fixture')
            (stage1 / 'fixture.fingering.png').write_bytes(b'preview-fixture')
            bundle = base / 'song_bundles' / 'fixture-120-E_solo'
            with contextlib.redirect_stdout(io.StringIO()):
                with patch.object(register_song_bundle, 'bundle_path', return_value=bundle):
                    register_song_bundle.main(['fixture-120-E_solo', '--stage1', str(stage1)])
                mapping = bundle / 'mapping/fingering.json'
                fret = bundle / 'training/fret_training.json'
                raw = bundle / 'training/strike_training.json'
                plan = bundle / 'training/strike_plan.json'
                build_fret_training_data.main([
                    '--fingering', str(mapping), '--audio',
                    str(bundle / 'source/audio.wav'), '--out', str(fret)])
                build_strike_training_data.main([str(mapping), '--out', str(raw)])
                build_strike_plan.main([str(raw), '--out', str(plan)])
                register_song_bundle.write_manifest('fixture-120-E_solo', bundle)
                audit_path = base / 'audit.json'
                result = audit_strike_goal_quality.main([
                    '--bundle', str(bundle), '--format', 'json', '--out', str(audit_path)])
            self.assertEqual(result, 0)
            self.assertTrue(audit_path.is_file())
            self.assertEqual(len(compile_song_bundle_events(bundle).events), 2)
            doc = json.loads(raw.read_text())
            self.assertEqual([e['string'] for e in doc['events']], [5, 4])
            self.assertEqual(json.loads(fret.read_text())['frames'][60]['fret_goal'][5], 3)
            self.assertTrue((fret.parent / 'hand_position_targets.json').is_file())

    def test_compiler_matches_seven_original_complete_plan_documents(self):
        golden = GOLDEN
        for song_id, expected in golden.items():
            with self.subTest(song_id=song_id):
                source = json.loads((ROOT / 'data/song_bundles' / song_id /
                                     'training/strike_training.json').read_text())
                result = build_strike_plan.build_strike_plan(source)
                digest = hashlib.sha256(json.dumps(
                    result, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
                self.assertIn(digest, expected if isinstance(expected, tuple) else (expected,))
                # A generated offline plan must roundtrip through the exact
                # reader used by training without changing its JSON contract.
                metadata = result['metadata']
                restored = strike_plan_document(
                    compiled_strike_goal_from_plan_document(result),
                    fps=metadata['fps'], source=metadata['source'],
                    source_sha256=metadata['source_sha256'])
                self.assertEqual(restored, result)

    def test_timeline_preserves_strum_overlay(self):
        from guitar_learning.tool import render_timeline
        with tempfile.TemporaryDirectory(prefix='guitar_timeline_') as temporary:
            base = Path(temporary)
            fingering = dict(notes=[dict(
                t_on=1., t_off=1.4, string=string, fret=0, midi=40,
                finger=0, barre=False) for string in (0, 1, 2)], hand=[])
            source = base / 'fingering.json'
            raw = base / 'strike_training.json'
            out = base / 'timeline.png'
            source.write_text(json.dumps(fingering))
            raw.write_text(json.dumps(
                build_strike_training_data.build_strike_training_data(fingering)))
            with contextlib.redirect_stdout(io.StringIO()):
                with patch.object(render_timeline.plt, 'close') as close:
                    render_timeline.main([str(source), str(out), str(raw)])
                figure = close.call_args[0][0]
                self.assertIn('1개 strum 그룹', figure._suptitle.get_text())
                self.assertEqual(sum(patch.get_zorder() in (4.6, 6)
                                     for patch in figure.axes[0].patches), 2)
                render_timeline.plt.close(figure)
            self.assertGreater(out.stat().st_size, 1000)

    def test_contract_validation_rejects_bad_clock_and_duplicate_ids(self):
        from guitar_learning.tool._strike_goals import validate_strike_training_data
        source = dict(schema='tab2body.strike_training.v3', metadata=dict(fps=30),
                      events=[dict(time=1., frame=60, string=0)])
        with self.assertRaisesRegex(ValueError, 'clock mismatch'):
            validate_strike_training_data(source)
        source['metadata']['fps'] = 60
        source['events'] = [dict(time=1., frame=60, string=0, event_id='same'),
                            dict(time=2., frame=120, string=1, event_id='same')]
        with self.assertRaisesRegex(ValueError, 'duplicate event_id'):
            validate_strike_training_data(source)

    def test_all_cli_entrypoints_support_help(self):
        for name in TOOLS:
            for entry in (['-m', 'guitar_learning.tool.' + name],
                          [str(ROOT / 'guitar_learning/tool' / (name + '.py'))]):
                with self.subTest(tool=name, entry=entry):
                    result = subprocess.run([sys.executable] + entry + ['--help'],
                                            cwd=ROOT, text=True, capture_output=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn('usage:', result.stdout)

    def test_build_pipeline_with_historical_roots_and_gpu_libraries_blocked(self):
        environment = dict(os.environ, GL_TOOL_BLOCK_OLD='1')
        result = subprocess.run([
            sys.executable, '-m', 'unittest',
            __name__ + '.ToolMigrationTests.test_reviewed_stage1_to_current_canonical_input',
            __name__ + '.ToolMigrationTests.test_compiler_matches_seven_original_complete_plan_documents',
            __name__ + '.ToolMigrationTests.test_timeline_preserves_strum_overlay'],
            cwd=ROOT, env=environment, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


GOLDEN = {
  # Python 3.8 and 3.13 sum floating costs differently; both original baselines
  # were compared with the migrated compiler in the same interpreter.
  "00_SS1-68-E_comp": ("0104a6b98263ee2696a41e585b0bd374c8707a02927614abf54f036b4c132dec",
                        "a9c11befd58eb7b57c9e5ea28caa40b55206229fb13bae5bbe9b3e27dfb9f109"),
  "02_Jazz1-200-B_solo": "ce030abd4dda85241337d76aaa4a1d983f49cac0453edf483ee23799fc1516d1",
  "03_Rock1-130-A_solo": "75167e9eb5cc791b1b419be65874f191b382fcd65e6c0e5749a39165a3f7b659",
  "05_BN1-129-Eb_solo": "7a7c578c9102388c23f0b9925019d49e819196d5b02ad65469b7d8d96e933089",
  "05_BN2-131-B_solo": "ed00902363e38e43873b4122145a8e424bca7e729d0bc2e460ba13612910afd7",
  "05_Jazz1-200-B_solo": "85c24dafcdd422104495c7e0fcc4f81436a60f5d656b15f1d618bdd1dd28c569",
  "05_Rock2-142-D_solo": "157a46b7c7d08831e338246fda649220d3b2cbd89e9ff37f1c7741726b6faefb"
}

if __name__ == '__main__':
    unittest.main()
