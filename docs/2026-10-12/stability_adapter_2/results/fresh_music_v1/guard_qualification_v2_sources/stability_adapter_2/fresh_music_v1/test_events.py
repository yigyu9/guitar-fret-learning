"""Real-bundle CPU contract checks; no simulator dependencies."""
from dataclasses import replace
from pathlib import Path
import subprocess
import sys
import unittest

from .events import OBSERVATION_DIM, ROOT, _compiler, load_music_task, validate_timeline

BUNDLE = ROOT / 'data/song_bundles/00_SS1-68-E_comp'


class MusicEventsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.task = load_music_task(BUNDLE)

    def altered(self, target=None, **changes):
        timeline = self.task.timeline
        events = list(timeline.events)
        events[0] = replace(events[0], **changes, **({'string_targets': (target,)} if target is not None else {}))
        timeline = replace(timeline, events=tuple(events))
        return replace(timeline, content_sha256=_compiler().canonical_content_sha256(timeline))

    def test_fixed_encoding_release_and_numbering(self):
        task = self.task
        target = task.events[0].string_targets[0]
        self.assertGreater(target.fret, 0)
        self.assertEqual(target.string + target.source_string, 5)
        self.assertEqual(len(task.encode(0)), OBSERVATION_DIM)
        self.assertEqual(task.encode(task.duration_s)[:30], (0.0,) * 30)
        self.assertEqual(task.encode(0), task.encode(0))
        self.assertTrue(all(len(p['sha256']) == 64 for p in task.provenance))

    def test_invalid_string_finger_timing_and_order(self):
        t = self.task.events[0].string_targets[0]
        for altered in (replace(t, string=6), replace(t, finger=9),
                        replace(t, release_s=-1), replace(t, source_string=t.string),
                        replace(t, sustain_until_s=-1)):
            with self.subTest(target=altered), self.assertRaises(ValueError):
                validate_timeline(self.altered(altered))
        with self.assertRaises(ValueError):
            validate_timeline(self.altered(score_time_s=999))

    def test_paired_and_phrase_keep_consecutive_real_events(self):
        for stage, count in [('C', 2), ('D', 8)]:
            task = load_music_task(BUNDLE, stage=stage, tempo_scale=0.5)
            self.assertEqual(len(task.events), count)
            self.assertEqual(task.timing_mode, 'tempo_scaled')
            self.assertEqual([e.event_index for e in task.events], list(range(task.events[0].event_index, task.events[0].event_index + count)))
            for event in task.events:
                self.assertEqual(len(task.encode(task.task_time(event.score_time_s))), OBSERVATION_DIM)
        # Canonical source fret holds can overlap many onsets. Encoding must
        # preserve the deterministic single clock and fixed dimensionality.
        self.assertGreater(self.task.events[0].string_targets[0].release_s, self.task.events[0].string_targets[0].sustain_until_s)

    def test_real_phrase_future_hold_does_not_mask_current_note(self):
        task = load_music_task(BUNDLE, stage='D')
        now = 1.001
        event, target, release, sounding = task.active_targets(now)[2]
        self.assertEqual(event.event_index, 0)
        self.assertTrue(sounding)
        self.assertAlmostEqual(release, 1.5689)
        self.assertEqual(task.encode(now)[2 * 5 + 3], 1.0)
        self.assertAlmostEqual(task.encode(now)[2 * 5 + 4], 0.5679)

    def test_constructed_overlap_and_conflict(self):
        task = self.task
        event = task.events[0]
        target = event.string_targets[0]
        future_target = replace(target, sustain_until_s=2.0)
        future = replace(event, event_id='future', score_time_s=1.0,
                         string_targets=(future_target,))
        paired = replace(task, events=(event, future))
        # Future shared preparation cannot change current sounding or release.
        self.assertEqual(paired.active_targets(1.001)[target.string][0].event_id, event.event_id)
        self.assertAlmostEqual(paired.active_targets(1.001)[target.string][2], 1.5689)
        # Same-identity audible overlap composes without dropping sounding.
        overlap = replace(future, score_time_s=0.2)
        overlapping = replace(task, events=(event, overlap))
        self.assertTrue(overlapping.active_targets(1.3)[target.string][3])
        self.assertAlmostEqual(overlapping.active_targets(1.3)[target.string][2], 3.0)
        conflict = replace(overlap, string_targets=(replace(future_target, fret=target.fret + 1),))
        with self.assertRaisesRegex(ValueError, 'conflicting audible targets'):
            replace(task, events=(event, conflict))
        # At a release/onset boundary adjacent different targets are valid.
        adjacent = replace(conflict, score_time_s=target.sustain_until_s)
        replace(task, events=(event, adjacent))

    def test_import_stays_cpu_only(self):
        script = 'from stability_adapter_2.fresh_music_v1.events import load_music_task; import sys; assert "torch" not in sys.modules; assert "isaacgym" not in sys.modules'
        subprocess.run([sys.executable, '-c', script], cwd=ROOT, check=True)

    def test_invalid_task_parameters(self):
        for kwargs in ({'tempo_scale': 0}, {'preroll_s': float('nan')}, {'phrase_events': True}, {'stage': 'A'}):
            with self.assertRaises(ValueError):
                load_music_task(BUNDLE, **kwargs)


if __name__ == '__main__':
    unittest.main()
