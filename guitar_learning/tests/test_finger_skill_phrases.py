import copy
import json
from pathlib import Path
import unittest

from guitar_learning.music_task import ScoreTarget, ScoreTask
from guitar_learning.song.finger_phrases import (
    BalancedPhraseSampler, FingerPhraseCatalog, build_phrase_catalog)
from guitar_learning.song.task import make_task


BUNDLE = Path(__file__).resolve().parents[2] / 'data/song_bundles/05_BN2-131-B_solo'


def task_from_intervals(intervals):
    return ScoreTask(tuple(ScoreTarget(str(i), str(i), 0, 7, 1, 1,
                                      press, end, press, press - 3, end - 3)
                           for i, (press, end) in enumerate(intervals)),
                     provenance=dict(schema='test', song=dict(pre_roll_s=3.)))


class FingerPhraseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.task = make_task(BUNDLE)
        cls.catalog = build_phrase_catalog(cls.task)

    def test_original_67_ids_times_and_closed_groups_preserved(self):
        catalog = self.catalog
        self.assertEqual([len(group) for group in catalog.closed_groups],
                         [3, 2, 1, 1, 6, 3, 1, 6, 10, 1, 1, 1, 15, 2, 1, 2, 4, 5, 1, 1])
        self.assertEqual({i for phrase in catalog.phrases for i in phrase.target_indices}, set(range(67)))
        self.assertEqual(len({p.phrase_id for p in catalog.phrases}), len(catalog.phrases))
        for index, source in enumerate(catalog.source_targets):
            self.assertEqual(dict(source)['target_id'], self.task.targets[index].target_id)
            for name in ('press_s', 'onset_s', 'end_s', 'source_onset_s', 'source_end_s'):
                self.assertEqual(dict(source)[name], getattr(self.task.targets[index], name))
        for group in catalog.closed_groups:
            for phrase in catalog.phrases:
                selected = set(group) & set(phrase.target_indices)
                self.assertTrue(not selected or selected == set(group))
        for size in (10, 15):
            group = next(g for g in catalog.closed_groups if len(g) == size)
            self.assertTrue(any(set(group) <= set(p.target_indices) for p in catalog.phrases))
        ten = next(g for g in catalog.closed_groups if len(g) == 10)
        self.assertTrue(any(p.target_indices == ten for p in catalog.phrases))
        # The original15-note group has only a10ms following gap. A different
        # earlier start gives a safe16-note view; its own start needs17 notes.
        fifteen = next(g for g in catalog.closed_groups if len(g) == 15)
        self.assertEqual(min(len(p.target_indices) for p in catalog.phrases
                             if set(fifteen) <= set(p.target_indices)), 16)
        own_start = next(p for p in catalog.phrases if p.target_indices[0] == fifteen[0])
        self.assertEqual(len(own_start.target_indices), 17)

    def test_local_clock_single_preparation_and_safe_control_end(self):
        for phrase in self.catalog.phrases:
            end = phrase.duration_ticks / self.catalog.control_hz
            self.assertAlmostEqual(phrase.start_s - phrase.score_offset_s, 3.)
            self.assertGreater(end + phrase.score_offset_s, phrase.end_s)
            if phrase.next_press_s is not None:
                self.assertLessEqual(end + phrase.score_offset_s, phrase.next_press_s + 1e-12)
            for i in phrase.target_indices:
                target = self.task.targets[i]
                self.assertAlmostEqual(target.onset_s - phrase.score_offset_s,
                                       target.source_onset_s - (phrase.start_s - 3.) + 3.)
                self.assertGreaterEqual(target.press_s - phrase.score_offset_s, 3. - 1e-12)
        # The ordinary full-song task, including its original tail, is untouched.
        self.assertEqual(self.task.duration_s, 1969 / 60.)
        self.assertEqual(self.catalog.document()['source_provenance']['song']['manifest_sha256'],
                         self.task.provenance['song']['manifest_sha256'])
        for gap in self.catalog.recovery_gaps:
            self.assertGreater(gap['gap_s'], 0)
            self.assertEqual(gap['next_press_s'], self.task.targets[gap['next_index']].press_s)
            self.assertEqual(gap['end_s'], self.task.targets[gap['previous_index']].end_s)

    def test_tiny_gap_forces_group_extension_and_exact_end_not_cut(self):
        task = task_from_intervals([(3., 3.101), (3.102, 3.201),
                                    (3.3, 3.4), (4., 4.1)])
        catalog = build_phrase_catalog(task)
        # A 1ms source gap cannot hold a 60Hz terminal boundary.
        for phrase in catalog.phrases:
            if 0 in phrase.target_indices:
                self.assertIn(1, phrase.target_indices)
            self.assertGreater(phrase.duration_ticks / 60. + phrase.score_offset_s, phrase.end_s)
        exact = build_phrase_catalog(task_from_intervals([(3., 3.1), (3.1, 3.2)]))
        self.assertEqual(exact.closed_groups, ((0, 1),))
        self.assertEqual(len(exact.phrases), 1)

    def test_serialization_and_fingerprint_reject_mutations(self):
        document = json.loads(json.dumps(self.catalog.document()))
        restored = FingerPhraseCatalog.from_document(document)
        self.assertEqual(restored.fingerprint, self.catalog.fingerprint)
        self.assertEqual(restored.phrases, self.catalog.phrases)
        changed = copy.deepcopy(document)
        changed['phrases'][0]['duration_ticks'] += 1
        with self.assertRaisesRegex(ValueError, 'fingerprint'):
            FingerPhraseCatalog.from_document(changed)
        self.assertEqual(build_phrase_catalog(self.task).fingerprint, self.catalog.fingerprint)

    def test_balanced_round_robin_restore_and_opportunities(self):
        sampler = BalancedPhraseSampler(self.catalog)
        first = [sampler.next() for _ in range(9)]
        self.assertEqual(sampler.cursors, [3, 2, 2, 2])
        self.assertEqual(sampler.opportunities,
                         [sum(p.opportunities[f] for p in first) for f in range(4)])
        restored = BalancedPhraseSampler(self.catalog)
        restored.load_state_dict(json.loads(json.dumps(sampler.state_dict())))
        self.assertEqual([sampler.next() for _ in range(50)], [restored.next() for _ in range(50)])
        self.assertEqual(sampler.state_dict(), restored.state_dict())
        state = sampler.state_dict()
        state['cursors'][0] += 1
        with self.assertRaisesRegex(ValueError, 'counters'):
            restored.load_state_dict(state)
        other = BalancedPhraseSampler(build_phrase_catalog(self.task, tail_s=.25))
        with self.assertRaisesRegex(ValueError, 'contract'):
            other.load_state_dict(sampler.state_dict())

    def test_absent_fingers_do_not_create_empty_buckets(self):
        sampler = BalancedPhraseSampler(build_phrase_catalog(task_from_intervals([(3., 3.2)])))
        for _ in range(7):
            sampler.next()
        self.assertEqual(sampler.cursors, [7, 0, 0, 0])
        restored = BalancedPhraseSampler(sampler.catalog)
        restored.load_state_dict(sampler.state_dict())
        self.assertEqual(sampler.next(), restored.next())

    def test_bad_configuration(self):
        for kwargs in (dict(preparation_s=-1), dict(tail_s=0), dict(control_hz=True),
                       dict(preparation_s=float('nan'))):
            with self.assertRaises(ValueError):
                build_phrase_catalog(self.task, **kwargs)


if __name__ == '__main__':
    unittest.main()
