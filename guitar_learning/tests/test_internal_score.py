"""Score contracts survive removal of the former runtime packages."""
import copy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

from guitar_learning.score.canonical import (
    CanonicalEventTimeline, SongBundleValidationError, compile_song_bundle_events,
)
from guitar_learning.score.events import load_music_task
from guitar_learning.score.strike_goal_compiler import compiled_strike_goal_from_plan_document
from guitar_learning.song.task import make_task

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / 'data/song_bundles/05_BN2-131-B_solo'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


class InternalScoreTests(unittest.TestCase):
    def test_source_timeline_and_full_song_preserve_reviewed_baseline(self):
        source = load_music_task(BUNDLE)
        self.assertEqual(source.timeline.content_sha256,
                         'fcff20c56500424b9e55c28b61ccd98fcde7c3591824806e0fe3a76fcae3f0b4')
        self.assertEqual(len(source.timeline.events), 66)
        task = make_task(BUNDLE)
        self.assertEqual(len(task.targets), 67)
        self.assertEqual(digest([asdict(target) for target in task.targets]),
                         '23e380c889e695d93735c4925bea9cfbb675231f3c1d3856e3f49b3f1d749ebd')
        self.assertEqual(digest(task.provenance['song']['schedule']),
                         '5a7af20887779256ae4d105b582bdfe6db52e4ea0129e590dff98b8891ff2bee')
        self.assertEqual(task.provenance['song']['expanded_event_ids'], ['event-000042'])
        self.assertEqual(task.duration_s, 1969 / 60)

    def test_comp_bundle_has_identical_polyphonic_timeline(self):
        timeline = compile_song_bundle_events(
            ROOT / 'data/song_bundles/00_SS1-68-E_comp', fail_on_unsupported=False)
        self.assertEqual(timeline.content_sha256,
                         'ae00d3b14a693702bb6d15e235e1b06ce1861fa745b38bb09cccc4656ce6256e')
        self.assertEqual(len(timeline.events), 104)

    def test_provenance_records_internal_compilers_and_every_bundle_input(self):
        task = load_music_task(BUNDLE)
        files = {Path(row['path']): row for row in task.provenance}
        for name in ('events.py', 'canonical.py', 'strike_goal_compiler.py'):
            path = ROOT / 'guitar_learning/score' / name
            self.assertEqual(files[path]['sha256'], hashlib.sha256(path.read_bytes()).hexdigest())
        for name in ('manifest.json', 'mapping/fingering.json', 'training/fret_training.json',
                     'training/strike_plan.json', 'training/strike_training.json', 'source/audio.wav'):
            self.assertIn(BUNDLE / name, files)
        self.assertFalse(any((ROOT / old) in path.parents
                             for path in files for old in ('tab2body', 'stability_adapter_2')))

    def test_strict_roundtrip_and_plan_validation_are_preserved(self):
        timeline = compile_song_bundle_events(BUNDLE, fail_on_unsupported=False)
        doc = timeline.to_document()
        self.assertEqual(CanonicalEventTimeline.from_document(doc).to_document(), doc)
        tampered = copy.deepcopy(doc)
        tampered['events'][0]['string_targets'][0]['source_string'] = 99
        with self.assertRaises(SongBundleValidationError):
            CanonicalEventTimeline.from_document(tampered)
        plan = json.loads((BUNDLE / 'training/strike_plan.json').read_text())
        plan['timeline']['original_times_s'][0] += .1
        with self.assertRaisesRegex(ValueError, 'does not match events'):
            compiled_strike_goal_from_plan_document(plan)
        comp_plan = json.loads((ROOT / 'data/song_bundles/00_SS1-68-E_comp/training/strike_plan.json').read_text())
        comp_plan['transitions'][0]['edge_gap_s'] += .1
        with self.assertRaisesRegex(ValueError, 'does not match events'):
            compiled_strike_goal_from_plan_document(comp_plan)

    def test_import_and_score_build_with_old_packages_and_gpu_imports_blocked(self):
        script = r'''
import importlib.abc
import sys
class BlockFormerRuntime(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'tab2body', 'stability_adapter_2', 'torch', 'isaacgym'}:
            raise ImportError('forbidden runtime import: ' + fullname)
sys.meta_path.insert(0, BlockFormerRuntime())
from guitar_learning.music_task import ScoreTask
from guitar_learning.song.task import make_task
for stage in ('B', 'C', 'D'):
    assert ScoreTask.from_bundle(sys.argv[1], stage=stage).targets
assert len(make_task(sys.argv[1]).targets) == 67
assert not any(name.split('.')[0] in {'tab2body', 'stability_adapter_2', 'torch', 'isaacgym'}
               for name in sys.modules)
'''
        result = subprocess.run([sys.executable, '-c', script, str(BUNDLE)], cwd=ROOT,
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
