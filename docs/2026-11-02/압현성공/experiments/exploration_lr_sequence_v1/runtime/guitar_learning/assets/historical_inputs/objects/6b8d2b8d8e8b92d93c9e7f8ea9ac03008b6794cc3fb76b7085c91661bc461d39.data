import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from guitar_learning.music_task import MusicLedger, ScoreTask
from guitar_learning.song.task import SongTask, make_task


BUNDLE = Path(__file__).resolve().parents[2] / 'data/song_bundles/05_BN2-131-B_solo'


class SongTaskTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in BUNDLE.rglob('*') if p.is_file()}
        cls.task = make_task(BUNDLE)

    def test_all_notes_once_and_source_clock(self):
        task = self.task
        self.assertIsInstance(task, ScoreTask)
        self.assertIsInstance(task, SongTask)
        self.assertEqual(len(task.targets), 67)
        self.assertEqual(len({t.target_id for t in task.targets}), 67)
        song = task.provenance['song']
        self.assertEqual(song['source_mapping_indices'], list(range(67)))
        self.assertEqual(song['source_event_count'], 66)
        self.assertEqual(song['source_note_count'], 67)
        self.assertTrue(song['coverage']['complete'])
        self.assertAlmostEqual(task.targets[0].onset_s, 3.6385)
        self.assertAlmostEqual(task.targets[-1].end_s, 30.0048)
        self.assertEqual(task.provenance['source_origin_s'], 0.)
        self.assertEqual(task.lookahead_s, 4.)
        self.assertEqual(task.provenance['lookahead_s'], 4.)
        notes = json.loads((BUNDLE / 'mapping/fingering.json').read_text())['notes']
        for target, row, note in zip(task.targets, song['schedule'], notes):
            self.assertAlmostEqual(target.source_onset_s, note['t_on'])
            self.assertAlmostEqual(target.onset_s, note['t_on'] + 3.)
            self.assertEqual(target.string, 5 - note['string'])
            self.assertEqual((target.fret, target.finger), (note['fret'], note['finger']))
            self.assertAlmostEqual(target.end_s, row['source_end_s'] + 3.)

    def test_audio_tail_and_control_boundary(self):
        song = self.task.provenance['song']
        self.assertAlmostEqual(song['audio_duration_s'], 29.30639455782313)
        self.assertEqual(song['control_ticks'], 1969)
        self.assertEqual(self.task.duration_s, 1969 / 60.)
        requested = song['audio_duration_s'] + song['pre_roll_s'] + song['tail_s']
        self.assertGreaterEqual(self.task.duration_s, requested)
        self.assertLess(self.task.duration_s - requested, 1 / 60.)
        changed = make_task(BUNDLE, pre_roll_s=1., tail_s=.25)
        self.assertAlmostEqual(changed.targets[0].onset_s, 1.6385)
        self.assertEqual(changed.duration_s, 1834 / 60.)

    def test_explicit_restrike_split_and_release_caps(self):
        left, right = self.task.targets[42:44]
        self.assertAlmostEqual(left.onset_s, 18.7547)
        self.assertAlmostEqual(right.onset_s, 18.778)
        self.assertAlmostEqual(right.onset_s - left.onset_s, .0233)
        self.assertEqual(left.end_s, right.onset_s)
        self.assertEqual((left.fret, left.finger, right.fret, right.finger), (11, 4, 9, 3))
        self.assertEqual((left.direction, right.direction), (1, 1))
        self.assertEqual(self.task.provenance['song']['expanded_event_ids'], ['event-000042'])
        self.assertAlmostEqual(self.task.targets[45].source_end_s, 16.5919)
        capped = [r for r in self.task.provenance['song']['schedule']
                  if r['source_end_s'] < r['source_note_off_s'] - 1e-10]
        self.assertEqual(len(capped), 11)
        self.assertAlmostEqual(sum(r['source_note_off_s'] - r['source_end_s'] for r in capped), .8044)

    def test_overlap_and_token_capacity(self):
        targets = self.task.targets
        times = sorted({t.onset_s for t in targets})
        self.assertEqual(max(sum(t.onset_s <= now < t.end_s for t in targets) for now in times), 2)
        for i, target in enumerate(targets):
            for other in targets[i + 1:]:
                if max(target.onset_s, other.onset_s) < min(target.end_s, other.end_s):
                    self.assertNotEqual(target.string, other.string)
                    self.assertNotEqual(target.finger, other.finger)
        times = {t.onset_s - 2 for t in targets} | {t.end_s + .1 for t in targets}
        self.assertEqual(max(sum(t.onset_s <= now + 2 and now <= t.end_s + .1
                                 for t in targets) for now in times), 12)
        geometry = {t.target_id: dict(delta=(0., 0., 0.), velocity=(0., 0., 0.)) for t in targets}
        ledger = MusicLedger(self.task)
        rows, mask, identities = self.task.tokens(0., geometry, ledger)
        self.assertTrue(mask[0])
        self.assertEqual(identities[0], targets[0].target_id)
        self.assertAlmostEqual(rows[0][0], 3.6385)
        actual_window_times = {max(0., t.onset_s - self.task.lookahead_s) for t in targets}
        actual_window_times.update(t.end_s + .1 for t in targets)
        maximum_visible = max(sum(t.onset_s <= now + self.task.lookahead_s and now <= t.end_s + .1
                                  for t in targets) for now in actual_window_times)
        self.assertLess(maximum_visible, self.task.capacity)
        for now in actual_window_times:
            self.task.tokens(now, geometry, ledger)
        for now in sorted(times):
            rows, mask, ids = self.task.tokens(max(0., now), geometry, ledger)
            self.assertEqual(len(rows), 64)
            priority, priority_mask, priority_ids = self.task.priority_tokens(rows, mask, ids)
            self.assertEqual(len(priority), 2)

    def test_provenance_stable_and_originals_remain_strict(self):
        self.assertEqual(json.dumps(self.task.provenance, sort_keys=True, allow_nan=False),
                         json.dumps(make_task(BUNDLE).provenance, sort_keys=True, allow_nan=False))
        for item in self.task.provenance['provenance']:
            self.assertEqual(hashlib.sha256(Path(item['path']).read_bytes()).hexdigest(), item['sha256'])
        with self.assertRaisesRegex(ValueError, 'unsupported.*event-000042'):
            ScoreTask.from_bundle(BUNDLE, stage='full')
        self.assertEqual(self.before, {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                                      for p in BUNDLE.rglob('*') if p.is_file()})

    def test_invalid_horizon_and_changed_audio_fail(self):
        for kwargs in (dict(pre_roll_s=-1), dict(pre_roll_s=True), dict(tail_s=0), dict(tail_s=float('nan'))):
            with self.assertRaises(ValueError):
                make_task(BUNDLE, **kwargs)
        with tempfile.TemporaryDirectory() as temp:
            copied = Path(temp) / BUNDLE.name
            shutil.copytree(BUNDLE, copied)
            audio = copied / 'source/audio.wav'
            data = audio.read_bytes()
            audio.write_bytes(data[:-1] + bytes((data[-1] ^ 1,)))
            with self.assertRaisesRegex(ValueError, 'audio manifest fingerprint'):
                make_task(copied)


if __name__ == '__main__':
    unittest.main()
