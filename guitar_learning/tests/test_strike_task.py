"""실제 CPU compiler 입력으로 타현 시계·스트럼·오염 거부를 확인한다."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import wave

from guitar_learning.score.canonical import load_music_task
from guitar_learning.song.strike_task import load_strike_task, SCHEMA
from guitar_learning.tool import build_fret_training_data, build_strike_training_data
from guitar_learning.tool import build_strike_plan, register_song_bundle


ROOT = Path(__file__).resolve().parents[2]
SINGLE = ROOT/'data/diagnostic_inputs/right_strike_v1'


class StrikeTaskTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='strike_task_')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def bundle(self, strikes, *, technique=None, fret=0, tail_off=.8, audio_s=1.):
        """strikes는 실제 builder에 넣을 (원시각,runtime현) 목록이다."""
        root = self.root/'bundle'
        root.mkdir()
        (root/'mapping').mkdir()
        (root/'source').mkdir()
        (root/'training').mkdir()
        notes = [dict(t_on=at, t_off=tail_off, string=5-string, fret=fret,
                      midi=60, finger=0 if fret == 0 else 1, barre=False)
                 for at, string in strikes]
        if technique:
            notes[0]['technique'] = technique
        mapping = dict(convention='string 0 = low-E; 5 = high-e', notes=notes,
                       presses=[], hand=[dict(t=0., P=6, grip=None)],
                       stats=dict(dropped_invalid_fret=0), diagnostics=[], violations=[])
        source = root/'mapping/fingering.json'
        source.write_text(json.dumps(mapping))
        audio = root/'source/audio.wav'
        with wave.open(str(audio), 'wb') as stream:
            stream.setnchannels(1)
            stream.setsampwidth(2)
            stream.setframerate(16000)
            stream.writeframes(b'\0\0'*int(audio_s*16000))
        with contextlib.redirect_stdout(io.StringIO()):
            build_fret_training_data.main(['--fingering', str(source), '--audio', str(audio),
                '--out', str(root/'training/fret_training.json')])
            build_strike_training_data.main([str(source), '--out', str(root/'training/strike_training.json')])
            build_strike_plan.main([str(root/'training/strike_training.json'),
                '--out', str(root/'training/strike_plan.json')])
            register_song_bundle.write_manifest(root.name, root)
        return root

    def mutate(self, root, relative, change, *, rehash=True):
        path = root/relative
        value = json.loads(path.read_text())
        change(value)
        path.write_text(json.dumps(value))
        if rehash:
            manifest_path = root/'manifest.json'
            manifest = json.loads(manifest_path.read_text())
            manifest['files'][relative] = dict(bytes=path.stat().st_size,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            manifest_path.write_text(json.dumps(manifest))

    def test_actual_single_identity_clock_direction_and_provenance(self):
        task = load_strike_task(SINGLE)
        self.assertEqual(len(task.events), 1)
        event = task.events[0]
        self.assertEqual((event.event_id, event.gesture, event.direction),
                         ('event-000000', 'single_pick', 1))
        self.assertEqual((event.traversal_strings, event.audible_strings,
                          event.protected_strings, event.mapping_note_indices), ((2,), (2,), (), (0,)))
        self.assertEqual((event.onset_s, event.crossing_times_s, event.start_s,
                          event.deadline_s), (3., (3.,), 2.95, 3.05))
        self.assertEqual((event.source_note_on_s, event.source_note_off_s), ((0.,), (1.2,)))
        self.assertEqual((task.duration_s, task.provenance['control_ticks']), (5., 300))
        self.assertEqual(task.provenance['schema'], SCHEMA)
        pins = {row['path']: row for row in task.provenance['files']}
        for name in ('manifest.json', 'source/audio.wav', 'mapping/fingering.json',
                     'training/fret_training.json', 'training/strike_plan.json',
                     'training/strike_training.json'):
            path = SINGLE/name
            self.assertEqual(pins[str(path)]['sha256'], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_strum_only_bundle_bypasses_no_curriculum_checks_and_preserves_protected(self):
        root = self.bundle([(.25, 5), (.25, 3)])
        with self.assertRaisesRegex(ValueError, 'curriculum segment'):
            load_music_task(root, stage='B')
        task = load_strike_task(root)
        event = task.events[0]
        self.assertEqual((event.gesture, event.direction, event.onset_s), ('strum', 1, 3.25))
        self.assertEqual(event.traversal_strings, (5, 4, 3))
        self.assertEqual(event.audible_strings, (5, 3))
        self.assertEqual(event.protected_strings, (4,))
        self.assertEqual(event.traversal_offsets_s, (-.007, 0., .007))
        self.assertEqual(event.sweep_duration_s, .014)
        self.assertEqual(event.mapping_note_indices, (0, 1))
        self.assertEqual(event.source_note_on_s, (.25, .25))
        self.assertEqual(event.crossing_times_s, (3.243, 3.25, 3.257))

    def test_upstroke_has_increasing_runtime_traversal(self):
        task = load_strike_task(self.bundle([(.25, 1), (.27, 4)]))
        event = task.events[0]
        self.assertEqual((event.gesture, event.direction), ('strum', -1))
        self.assertEqual(event.traversal_strings, (1, 2, 3, 4))
        self.assertEqual(event.protected_strings, (2, 3))
        self.assertTrue(all(a < b for a, b in zip(event.crossing_times_s, event.crossing_times_s[1:])))

    def test_actual_comp_preserves_original_strum_and_complete_note_coverage(self):
        task = load_strike_task(ROOT/'data/song_bundles/00_SS1-68-E_comp')
        self.assertEqual((len(task.events), sum(event.gesture == 'strum' for event in task.events)), (104, 43))
        event = task.events[2]
        self.assertEqual((event.event_id, event.onset_s, event.mapping_note_indices),
                         ('event-000002', 3.9172, (2, 3, 4)))
        self.assertEqual(event.traversal_offsets_s, (-.012, 0., .012))
        self.assertEqual(event.source_note_on_s, (.894, .9172, .9404))
        self.assertEqual(task.provenance['source_note_count'],
                         sum(len(event.mapping_note_indices) for event in task.events))

    def test_overlapping_acceptance_windows_of_ordered_events_are_allowed(self):
        task = load_strike_task(self.bundle([(.25, 2), (.33, 3)]))
        first, second = task.events
        self.assertLess(second.start_s, first.deadline_s)
        self.assertLess(first.crossing_times_s[-1], second.crossing_times_s[0])
        self.assertIn('sequential event approval', task.provenance['event_order'])

    def test_left_only_missing_press_is_preserved_without_success_claim(self):
        task = load_strike_task(self.bundle([(.25, 2)], fret=6))
        self.assertEqual(task.events[0].unsupported_reasons, ('missing_fret_event_link',))
        self.assertIn('no left pressure, pitch or acoustic success', task.provenance['scope'])

    def test_ambiguous_attack_technique_and_alternate_restrike_are_rejected(self):
        root = self.bundle([(.25, 2)], technique='hammer_on')
        with self.assertRaisesRegex(ValueError, 'unsupported right strike semantics'):
            load_strike_task(root)
        # 기본곡의 실제 재타격 묶음을 임의로 단음으로 펼치지 않는다.
        with self.assertRaisesRegex(ValueError, 'alternate_restrike'):
            load_strike_task(ROOT/'data/song_bundles/05_BN2-131-B_solo')

    def test_manifest_audio_and_plan_contamination_are_rejected(self):
        root = self.bundle([(.25, 2)])
        path = root/'source/audio.wav'
        original = path.read_bytes()
        path.write_bytes(original+b' ')
        with self.assertRaisesRegex(ValueError, 'SHA/size mismatch'):
            load_strike_task(root)
        path.write_bytes(original)
        self.mutate(root, 'training/strike_plan.json',
                    lambda doc: doc['events'][0].update(direction='sideways'))
        with self.assertRaisesRegex(ValueError, 'invalid compiled strike plan'):
            load_strike_task(root)

    def test_rehashed_raw_identity_and_plan_partition_are_still_verified(self):
        root = self.bundle([(.25, 2)])
        self.mutate(root, 'training/strike_plan.json',
                    lambda doc: doc['events'][0].update(source_event_ids=[99]))
        with self.assertRaisesRegex(ValueError, 'partition'):
            load_strike_task(root)

    def test_rehashed_raw_string_identity_is_not_bypassed(self):
        root = self.bundle([(.25, 2)])
        self.mutate(root, 'training/strike_training.json',
                    lambda doc: doc['events'][0].update(string=3))
        raw_hash = hashlib.sha256((root/'training/strike_training.json').read_bytes()).hexdigest()
        self.mutate(root, 'training/strike_plan.json',
                    lambda doc: doc['metadata'].update(source_sha256=raw_hash))
        with self.assertRaisesRegex(ValueError, 'incorrect string conversion'):
            load_strike_task(root)

    def test_rehashed_gesture_cannot_relabel_multistring_strum_as_single(self):
        root = self.bundle([(.25, 5), (.25, 3)])
        self.mutate(root, 'training/strike_plan.json',
                    lambda doc: doc['events'][0].update(gesture='single_pick'))
        with self.assertRaisesRegex(ValueError, 'cardinality mismatch'):
            load_strike_task(root)

    def test_deadline_audio_boundaries_and_fractional_tick_ceiling(self):
        root = self.bundle([(.99, 2)], tail_off=1.)
        with self.assertRaisesRegex(ValueError, 'last strike deadline'):
            load_strike_task(root, pre_roll_s=0., tail_s=.001)
        task = load_strike_task(root, pre_roll_s=.001, tail_s=.051)
        self.assertEqual(task.duration_s, 64/60.)
        self.assertGreaterEqual(task.duration_s, task.events[-1].deadline_s)

    def test_raw_off_is_metadata_and_not_a_right_hand_hold_requirement(self):
        task = load_strike_task(self.bundle([(.25, 2)], tail_off=1.1))
        self.assertEqual(task.events[0].source_note_off_s, (1.1,))
        self.assertEqual(task.duration_s, 4.5)

    def test_path_and_clock_inputs_are_strict(self):
        for value in ({'events': []}, None, 3):
            with self.assertRaisesRegex(ValueError, 'bundle path'):
                load_strike_task(value)
        for key, value in (('pre_roll_s', True), ('pre_roll_s', float('nan')),
                           ('pre_roll_s', -.1), ('tail_s', 0), ('tail_s', float('inf'))):
            with self.assertRaises(ValueError):
                load_strike_task(SINGLE, **{key: value})


if __name__ == '__main__':
    unittest.main()
