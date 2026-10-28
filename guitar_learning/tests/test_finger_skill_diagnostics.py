import json
import math
import unittest

import torch

from guitar_learning.gpu.episode_diagnostics import PHASES
from guitar_learning.gpu.episode_diagnostics import SkillEpisodeDiagnostics
from guitar_learning.gpu.control import apply
from guitar_learning.song.task import ScoreTarget
from guitar_learning.song.task import SongTask


def task():
    return SongTask((ScoreTarget('a', 'a', 0, 7, 1, 1, 4.2, 4.5, 4., 1.2, 1.5),
                     ScoreTarget('b', 'b', 0, 7, 1, 1, 10.2, 10.5, 10., 7.2, 7.5)),
                    episode_duration_s=12.)


def pose(count, position=(0., 0., 0.), angle=0.):
    return torch.tensor([*position, 0., 0., math.sin(angle / 2), math.cos(angle / 2)],
                        dtype=torch.float64).expand(count, 7).clone()


def posture(count):
    return dict(valid=torch.ones(count, 4, 3, dtype=torch.bool),
                angles=torch.zeros(count, 4, 3, dtype=torch.float64),
                band_inside=torch.ones(count, 4, dtype=torch.bool),
                quality=torch.ones(count, 4, dtype=torch.float64),
                gate=torch.ones(count, 4, dtype=torch.float64))


class FingerSkillDiagnosticsTests(unittest.TestCase):
    def make(self, count=1, offset=5., duration=7.):
        diagnostic = SkillEpisodeDiagnostics(task(), count, 'cpu')
        points = torch.zeros(count, 4, 128, 3, dtype=torch.float64)
        offset = torch.full((count,), offset, dtype=torch.float64)
        duration = torch.full((count,), int(duration * 60), dtype=torch.long)
        focus = torch.ones(count, 2, dtype=torch.bool)
        diagnostic.reset(torch.arange(count), offset, duration, points, pose(count), pose(count), focus)
        return diagnostic, points, offset, duration, focus

    def physics_until(self, diagnostic, start_tick, end_tick, offset):
        state = posture(diagnostic.count)
        for tick in range(start_tick, end_tick + 1):
            now = torch.full((diagnostic.count,), tick / 240., dtype=torch.float64)
            diagnostic.physics(now, now + offset, state,
                               torch.zeros(diagnostic.count, 4, dtype=torch.bool))

    def test_initial_preparation_cannot_fill_original_score_gap(self):
        diagnostic, _, offset, _, _ = self.make()
        # Original index gap5.55..9.65 overlaps synthetic score5..8, but that
        # overlap belongs to the three-second policy preparation, not music.
        self.physics_until(diagnostic, 1, 720, offset)
        result = diagnostic.episode(0)
        self.assertEqual(result['source_recovery']['by_finger'][0]['observed_s'], 0.)
        self.assertAlmostEqual(result['source_recovery']['by_finger'][0]['planned_s'], 1.65)
        self.assertAlmostEqual(result['initial_preparation']['in_band_s'][0], 3.)
        self.assertEqual(result['source_recovery']['by_finger'][0]['occupancy80_windows'], 0)

    def test_fixed_planned_denominator_retains_failure_tail(self):
        diagnostic, _, offset, _, _ = self.make()
        self.physics_until(diagnostic, 1, 840, offset)  # failure after3.5 local seconds
        result = diagnostic.episode(0)['source_recovery']['by_finger'][0]
        self.assertAlmostEqual(result['planned_s'], 1.65)
        self.assertAlmostEqual(result['observed_s'], .5)
        self.assertAlmostEqual(result['in_band_s'], .5)
        self.assertAlmostEqual(result['credited_in_band_fraction'], .5 / 1.65)
        self.assertEqual(result['occupancy80_windows'], 0)
        self.assertEqual(result['incomplete_or_unobserved_windows'], 1)

    def test_complete_window_credits_80_percent_and_invalid_posture_does_not(self):
        diagnostic, _, offset, _, _ = self.make()
        self.physics_until(diagnostic, 1, 1116, offset)
        result = diagnostic.episode(0)['source_recovery']['by_finger'][0]
        self.assertAlmostEqual(result['planned_s'], 1.65)
        self.assertAlmostEqual(result['observed_s'], 1.65)
        self.assertEqual(result['complete_windows'], 1)
        self.assertEqual(result['occupancy80_windows'], 1)
        invalid, _, offset, _, _ = self.make()
        state = posture(1)
        state['valid'][:] = False
        for tick in range(1, 1117):
            now = torch.tensor([tick / 240.], dtype=torch.float64)
            invalid.physics(now, now + offset, state, torch.zeros(1, 4, dtype=torch.bool))
        result = invalid.episode(0)['source_recovery']['by_finger'][0]
        self.assertEqual(result['in_band_s'], 0.)
        self.assertEqual(result['valid_s'], 0.)
        self.assertEqual(result['occupancy80_windows'], 0)

    def test_partial_reset_preserves_other_environment(self):
        diagnostic, points, offset, duration, focus = self.make(count=2)
        self.physics_until(diagnostic, 1, 840, offset)
        moved = points + .001
        now = torch.tensor([3.5, 3.5], dtype=torch.float64)
        diagnostic.control(now, now + offset, moved, pose(2), pose(2))
        before = diagnostic.episode(1)
        previous = diagnostic.previous_points[1].clone()
        diagnostic.reset(torch.tensor([0]), offset, duration, points, pose(2), pose(2), focus)
        self.assertEqual(diagnostic.episode(1), before)
        torch.testing.assert_close(diagnostic.previous_points[1], previous)
        self.assertEqual(diagnostic.episode(0)['initial_preparation']['in_band_s'], [0.] * 4)
        self.assertEqual(diagnostic.episode(0)['source_recovery']['by_finger'][0]['observed_s'], 0.)

    def test_endpoint_phase_paths_and_focus_mask(self):
        diagnostic, points, offset, duration, focus = self.make(offset=0., duration=12.)
        focus[:, 1] = False
        diagnostic.reset(torch.tensor([0]), offset, duration, points, pose(1), pose(1), focus)
        for i, endpoint in enumerate((1., 3.5, 4.1, 4.3, 4.55, 8.5)):
            now = torch.tensor([endpoint], dtype=torch.float64)
            shifted = points.clone()
            shifted[..., 0] += (i + 1) * .001
            diagnostic.control(now, now, shifted, pose(1), pose(1))
        result = diagnostic.episode(0)['motion']
        for phase in PHASES:
            row = result['path_m'][PHASES.index(phase)][0]
            self.assertAlmostEqual(row[0], .001)
            self.assertEqual(row[1], 0.)
            self.assertAlmostEqual(row[2], .001)
        self.assertLessEqual(result['vector_sum_max_error_m'], 1e-18)
        # The unselected next note must not turn8.5s into finger preparation.
        self.assertAlmostEqual(result['path_m'][PHASES.index('idle')][0][2], .001)
        json.dumps(diagnostic.episode(0), allow_nan=False)

    def test_common_world_motion_and_guitar_relative_translation(self):
        diagnostic, points, offset, _, _ = self.make()
        points[..., 0] = .02
        diagnostic.previous_points.copy_(points)
        rigid = pose(1, (.1, .2, -.03), .4)
        current = apply(rigid[:, None, None, 3:], points) + rigid[:, None, None, :3]
        now = torch.tensor([1 / 60.], dtype=torch.float64)
        diagnostic.control(now, now + offset, current, rigid, rigid)
        self.assertLess(diagnostic.paths.abs().max(), 1e-15)
        guitar = rigid.clone()
        guitar[:, 0] += .01
        now *= 2
        diagnostic.control(now, now + offset, current, rigid, guitar)
        result = diagnostic.episode(0)['motion']['path_m'][0]
        for finger in result:
            self.assertAlmostEqual(finger[0], .01)
            self.assertAlmostEqual(finger[1], .01)
            self.assertAlmostEqual(finger[2], 0.)

    def test_invalid_samples_excluded_without_nan_and_repeated_endpoint_not_counted(self):
        diagnostic, points, offset, _, _ = self.make()
        current = points.clone()
        current[..., 0, :] = float('inf')
        now = torch.tensor([1 / 60.], dtype=torch.float64)
        diagnostic.control(now, now + offset, current, pose(1), pose(1))
        before = diagnostic.episode(0)
        json.dumps(before, allow_nan=False)
        diagnostic.control(now, now + offset, current, pose(1), pose(1))
        self.assertEqual(diagnostic.episode(0), before)
        self.assertAlmostEqual(before['motion']['valid_sample_s'][0][0], 127 / 128 / 60.)


if __name__ == '__main__':
    unittest.main()
