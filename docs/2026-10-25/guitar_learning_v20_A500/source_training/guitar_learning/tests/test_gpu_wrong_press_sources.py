"""Actual source-sample provenance; synthetic poses do not certify reachability."""
from dataclasses import replace
import unittest

import torch

from guitar_learning.gpu.geometry import apply
from guitar_learning.music_task import ScoreTask
from guitar_learning.tests import test_gpu_environment as fixtures
from guitar_learning.tests.test_gpu_surface_learning import task


class WrongPressSourceTests(unittest.TestCase):
    environment = fixtures.TensorSongTests.environment
    advance = staticmethod(fixtures.TensorSongTests.advance)

    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def setup(self, *, onset=0., end=.5, score=None):
        env, row, _ = self.environment(task=score or task((1,), onset=onset, end=end))
        row = fixtures.place_pad_sample(env, row, 1, fixtures.press_goal(env))
        # Isolate full-surface witnesses independently of the assigned pad.
        env.surface_valid.zero_()
        return env, row

    def probe(self, env, row, *, slot=4, fret=7, boundary=False):
        index = int(env.finger_indices[slot])
        start = env.starts[:, 0]
        line = env.ends[:, 0]-start
        y = env.frets[:, fret-1, 1] if boundary else .5*(env.frets[:, fret-1, 1]+env.frets[:, fret, 1])
        goal = start+((y-start[:, 1])/line[:, 1])[:, None]*line
        guitar = row['body_state'][:, env.guitar_index]
        world = guitar[:, :3]+apply(guitar[:, 3:7], goal)
        row['body_state'][:, index, :3] = world-apply(row['body_state'][:, index, 3:7], env.surface_local[slot, 0])
        row['contact_force'][:, index, 2] = 1.
        env.surface_valid[slot*env.surface_count] = True

    def test_higher_witness_body_string_fret_and_supported_audible_time(self):
        env, row = self.setup(); self.probe(env, row)
        env.reset([0, 1], row)
        self.assertTrue(env.wrong.all()); self.assertFalse(env.candidate.any())
        self.advance(env, row)
        torch.testing.assert_close(env.note['wrong_source_time'][:, 0, 4, 0], torch.full((2,), 1/60., dtype=torch.float64))
        torch.testing.assert_close(env.note['wrong_supported_time'], env.note['wrong'])
        self.assertFalse(env.note['wrong_ambiguous_time'].any())
        self.assertEqual(env.note['wrong_source_fret_min'][:, 0, 4].tolist(), [7, 7])
        ledger = env._episode(0, False)['left_note_ledger']
        sources = ledger['wrong_press_sources']
        self.assertEqual(sources['body_names'][4], 'human/LH:middle2')
        self.assertEqual(sources['target_strings_1based'], [1])
        self.assertEqual(sources['contract']['causes'], ['higher', 'lower', 'assignment'])

    def test_lower_and_assignment_only_contribute_without_positive_pad(self):
        for fret, cause in ((3, 1), (5, 2)):
            env, row = self.setup(); self.probe(env, row, fret=fret)
            env.reset([0, 1], row)
            self.assertTrue(env.candidate.all()); self.assertFalse(env.wrong.any())
            self.assertFalse(env.wrong_source_flags.any())
            row['contact_force'][:, env.pad_indices[0]] = 0.
            env.reset([0, 1], row)
            self.assertTrue(env.wrong.all())
            self.assertTrue(env.wrong_source_flags[:, 0, 4, cause].all())
            self.advance(env, row)
            self.assertTrue((env.note['wrong_supported_time'] > 0).all())

    def test_assignment_on_boundary_is_recorded_as_ambiguous_without_new_verdict(self):
        env, row = self.setup(); self.probe(env, row, fret=5, boundary=True)
        row['contact_force'][:, env.pad_indices[0]] = 0.
        env.reset([0, 1], row)
        self.assertTrue(env.wrong.all())  # Original assignment predicate.
        self.assertTrue(env.wrong_ambiguous.all()); self.assertFalse(env.wrong_supported.any())
        self.advance(env, row)
        torch.testing.assert_close(env.note['wrong_ambiguous_time'], env.note['wrong'])
        self.assertEqual(env.note['wrong_source_fret_min'][:, 0, 4].tolist(), [0, 0])

    def test_future_note_preparation_is_identified_but_not_exempted(self):
        current = task((1,), end=.5).targets[0]
        future = replace(current, target_id='next', event_id='next', fret=7, finger=2,
                         onset_s=1., end_s=1.5, press_s=.8)
        env, row = self.setup(score=ScoreTask((current, future)))
        self.probe(env, row)
        env.reset([0, 1], row)
        self.assertTrue(env.wrong[:, 0].all())
        self.assertTrue(env.wrong_next_preparation[:, 0].all())
        self.advance(env, row)
        torch.testing.assert_close(env.note['wrong_next_preparation_time'][:, 0], env.note['wrong'][:, 0])
        self.assertTrue((env.terms['song_wrong_press'] < 0).all())
        self.assertFalse(env.note['wrong_next_preparation_time'][:, 1].any())

    def test_preparation_diagnostics_do_not_leak_into_audible_sources(self):
        env, row = self.setup(onset=1., end=1.5); self.probe(env, row)
        env.reset([0, 1], row); self.advance(env, row)
        self.assertTrue((env.note['higher_time'] > 0).all())  # Existing press-window diagnostic.
        for name in ('wrong_source_time', 'wrong_supported_time', 'wrong_ambiguous_time', 'wrong'):
            self.assertFalse(env.note[name].any())
        self.assertFalse(env.terms['song_wrong_press'].any())

    def test_multiple_bodies_do_not_duplicate_wrong_penalty(self):
        env, row = self.setup()
        for slot in (4, 6): self.probe(env, row, slot=slot)
        env.reset([0, 1], row); self.advance(env, row)
        for slot in (4, 6):
            torch.testing.assert_close(env.note['wrong_source_time'][:, 0, slot, 0], env.note['wrong'][:, 0])
        torch.testing.assert_close(env.note['wrong'][:, 0], torch.full((2,), 1/60., dtype=torch.float64))
        torch.testing.assert_close(env.terms['song_wrong_press'], torch.full((2,), -1/60./.5))

    def test_endpoint_trapezoid_and_fret_range_preserve_collection_boundaries(self):
        env, row = self.setup(); self.probe(env, row, fret=7)
        env.reset([0, 1], row); self.advance(env, row)
        self.probe(env, row, fret=8)
        env.reset_reward_window(); self.advance(env, row)
        self.assertEqual(env.note['wrong_source_fret_min'][:, 0, 4].tolist(), [7, 7])
        self.assertEqual(env.note['wrong_source_fret_max'][:, 0, 4].tolist(), [8, 8])
        # Release the witness. First substep contributes the previous endpoint
        # half-interval, subsequent endpoints contribute zero.
        saved = env.note['wrong_source_time'].clone()
        row['contact_force'][:, env.finger_indices[4]] = 0.
        self.advance(env, row)
        delta = env.note['wrong_source_time']-saved
        self.assertAlmostEqual(float(delta[0, 0, 4, 0]), .5/240., places=12)
        torch.testing.assert_close(env.note['wrong_supported_time'], env.note['wrong'])

    def test_selective_reset_preserves_other_row_provenance(self):
        env, row = self.setup(); self.probe(env, row)
        env.reset([0, 1], row); self.advance(env, row)
        saved = {name:value[1].clone() for name,value in env.note.items() if name.startswith('wrong_')}
        env.reset([0], row)
        for name,value in saved.items():
            self.assertFalse(env.note[name][0].any())
            torch.testing.assert_close(env.note[name][1], value, atol=0, rtol=0)
