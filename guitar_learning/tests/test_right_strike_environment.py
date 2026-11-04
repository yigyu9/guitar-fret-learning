"""CPU geometry/accounting fixtures, not evidence of native striking ability."""
import copy
from dataclasses import replace
import unittest
from unittest.mock import patch

import torch

from guitar_learning.gpu.environment import TensorSongEnvironment, TERMS
from guitar_learning.gpu.right_strike_environment import RightStrikeEnvironment
from guitar_learning.song.task import ScoreTarget, SongTask
from guitar_learning.quality.strike_quality import StrikeQualityDetector
from guitar_learning.tests.test_gpu_environment import fixture, BUNDLE, SONG


TARGET = ScoreTarget('single-down', 'single-down', 2, 6, 1, 1, 3., 4.2, 3., 0., 1.2)
TASK = SongTask((TARGET,), episode_duration_s=5.)


class RightStrikeEnvironmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def make(self, cls=RightStrikeEnvironment, task=TASK):
        metadata, snapshot = fixture(2)
        with patch('guitar_learning.gpu.environment.make_task', return_value=task):
            env = cls(metadata, bundle=BUNDLE, song=SONG, hand='right', device='cpu')
        env.reset([0, 1], snapshot)
        return env, snapshot

    def geometry(self, env, pick=(-.004, -.32, .006)):
        env.starts = torch.tensor([[[.04-i*.02, -.4, .01] for i in range(6)]]).expand(2, -1, -1).clone()
        env.ends = env.starts.clone(); env.ends[:, :, 1] = .2
        env.pick = torch.tensor([pick]).expand(2, -1).clone()
        env.previous_pick = env.pick.clone()
        env.clock[:] = 716
        env.terms = {key: torch.zeros(2) for key in TERMS}
        env._reset_quality(torch.arange(2))

    def step(self, env, x, z=.006):
        env.clock += 1
        before = (env.clock-1).double()/240.
        env.pick = torch.tensor([[x, -.32, z]]).expand(2, -1).clone()
        env._strike(before, env.clock.double()/240., torch.zeros(2, 1, dtype=torch.bool))
        env.previous_pick = env.pick.clone()

    def prepared_hit(self, env):
        self.geometry(env)
        self.step(env, -.004)  # reset observation + this endpoint establish readiness
        self.step(env, -.002)
        self.step(env, .002)   # eligible crossing interpolates inside this interval

    def summary(self, env, index=0, failed=False):
        env.clock[:] = 1200
        return env._episode(index, failed)

    def test_prepared_native_hit_then_two_strictly_later_observations_recovers(self):
        env, _ = self.make()
        self.prepared_hit(env)
        self.assertTrue(bool(env.note['right'].all()))
        self.assertEqual(env.strike_quality['accepted'].tolist(), [1, 1])
        self.assertEqual(env.strike_quality['recovery_samples'].tolist(), [0, 0])
        self.step(env, .004)
        self.assertFalse(bool(env.strike_quality['recovered'].any()))
        self.step(env, .004)
        result = self.summary(env)
        quality = result['right_strike_quality']
        self.assertTrue(result['song']['stage_success'])
        self.assertTrue(quality['success'])
        self.assertAlmostEqual(quality['preparation_dwell_s'], 1/240.)
        self.assertAlmostEqual(quality['recovery_dwell_s'], 1/240.)
        self.assertAlmostEqual(quality['first_hit_time_error_s'], -1.5/240.)
        self.assertFalse(quality['strict_matched50'])  # no left clean in this fixture
        self.assertEqual(quality['native_eligible_crossings'], 1)

    def test_unprepared_parent_success_does_not_become_quality_success(self):
        env, _ = self.make()
        self.geometry(env)  # one qualifying previous sample is insufficient
        self.step(env, .002)
        self.step(env, .004); self.step(env, .004)
        result = self.summary(env)
        self.assertTrue(result['song']['stage_success'])
        quality = result['right_strike_quality']
        self.assertFalse(quality['prepared_before_hit'])
        self.assertFalse(quality['recovered'])
        self.assertEqual(quality['native_expected_hit_count'], 1)
        self.assertEqual(quality['accepted_count'], 0)
        self.assertEqual(quality['unprepared_hit_count'], 1)
        self.assertFalse(quality['success'])

    def test_separation_before_acceptance_does_not_count_and_current_recovery_can_be_lost(self):
        env, _ = self.make()
        self.geometry(env)
        self.step(env, -.004); self.step(env, -.004)
        self.assertFalse(bool(env.strike_quality['recovered'].any()))
        self.step(env, -.002); self.step(env, .002)
        self.step(env, .004); self.step(env, .004)
        self.assertTrue(bool(env.strike_quality['ever_recovered'].all()))
        self.step(env, .001, z=.009)  # 3D distance less than3mm, without crossing
        quality = self.summary(env)['right_strike_quality']
        self.assertTrue(quality['ever_recovered'])
        self.assertFalse(quality['recovered'])
        self.assertEqual(quality['recovery_dwell_s'], 0.)
        self.assertFalse(quality['success'])

    def test_raw_lifted_xy_passage_is_not_native_accepted_or_wrong(self):
        env, _ = self.make()
        self.geometry(env, pick=(-.004, -.32, .04))
        self.step(env, .004, z=.04)
        quality = self.summary(env)['right_strike_quality']
        self.assertEqual(quality['raw_xy_crossings'], 1)
        self.assertEqual(quality['raw_target_xy_crossings'], 1)
        self.assertEqual(quality['native_eligible_crossings'], 0)
        self.assertEqual(quality['wrong_count'], 0)
        self.assertFalse(quality['prepared'])

    def test_preparation_requires_finite_target_segment_depth_zone_and_departure_side(self):
        env, _ = self.make()
        for point in ((-.004, -.39, .006), (-.004, -.5, .006),
                      (-.004, -.32, .04), (-.004, -.32, -.02), (.004, -.32, .006)):
            self.geometry(env, pick=point)
            preparation, _ = env._quality_geometry()
            self.assertFalse(bool(preparation.any()), point)

    def test_readiness_and_current_recovery_match_cpu_quality_semantics(self):
        env, _ = self.make(); self.geometry(env)
        detector = StrikeQualityDetector(TARGET)
        def sample():
            return dict(physics_step=int(env.clock[0]), pick_G_m=env.pick[0].numpy().copy(),
                starts_G_m=env.starts[0].numpy().copy(), ends_G_m=env.ends[0].numpy().copy())
        previous = sample()
        for x, z in ((-.004, .006), (-.002, .006), (.002, .006),
                     (.004, .006), (.004, .006), (.001, .009)):
            self.step(env, x, z=z)
            current = sample(); cpu = detector.update(previous, current)['quality']; previous = current
            q = env.strike_quality
            self.assertEqual(bool(q['ready'][0]), cpu['ready'])
            self.assertEqual(bool(q['recovered'][0]), cpu['recovered'])
            self.assertEqual(bool(q['ever_recovered'][0]), cpu['ever_recovered'])
            self.assertAlmostEqual(float(q['preparation_longest_s'][0]), cpu['ready_dwell_s'])
            self.assertAlmostEqual(float(q['recovery_dwell_s'][0]), cpu['recovery_dwell_s'])
            self.assertEqual(int(q['accepted'][0]), cpu['counts']['accepted'])

    def test_wrong_native_crossing_and_repeat_are_preserved(self):
        env, _ = self.make()
        self.geometry(env, pick=(-.024, -.32, .006))
        self.step(env, -.016)  # adjacent wrong string at-.02
        quality = self.summary(env)['right_strike_quality']
        self.assertEqual(quality['wrong_count'], 1)
        self.assertFalse(quality['success'])
        env, _ = self.make()
        self.prepared_hit(env)
        self.step(env, .004); self.step(env, .004)  # original two-step rearm
        self.step(env, -.004, z=.05)  # lifted return is diagnostic only
        self.step(env, -.004)
        self.step(env, .004)  # matching eligible repeat, original ledger already latched
        quality = self.summary(env)['right_strike_quality']
        self.assertEqual(quality['repeat_count'], 1)
        self.assertEqual(quality['accepted_count'], 1)
        self.assertFalse(quality['success'])

    def test_safety_failure_and_incomplete_timeline_prevent_quality_success(self):
        env, _ = self.make(); self.prepared_hit(env)
        self.step(env, .004); self.step(env, .004)
        env.clock[:] = 1199
        self.assertFalse(env._episode(0, False)['right_strike_quality']['success'])
        env.invalid[0] = True
        self.assertFalse(self.summary(env)['right_strike_quality']['full_safe'])
        self.assertFalse(self.summary(env)['right_strike_quality']['success'])
        env.invalid[0] = False
        env.strike_quality['unsafe_seen'][0] = True
        self.assertFalse(self.summary(env)['right_strike_quality']['success'])

    def test_transient_physical_and_control_failures_are_latched_at_native_substeps(self):
        env, snapshot = self.make()
        env.begin_control(torch.zeros(2, 39))
        for substep in range(4):
            row = {k: v.clone() for k, v in snapshot.items()}
            if substep == 1:
                row['body_state'][0, env.guitar_index, 0] += .1
                env.control_invalid[1] = True
            if substep == 2:
                env.control_invalid[1] = False
            env.substep(dict(row, physics_step=env.clock+1))
        self.assertEqual(env.strike_quality['unsafe_seen'].tolist(), [True, True])

    def test_partial_reset_only_clears_selected_quality_row(self):
        env, snapshot = self.make(); self.prepared_hit(env)
        self.step(env, .004); self.step(env, .004)
        before = {k: v[1].clone() for k, v in env.strike_quality.items()}
        env.reset([0], snapshot)
        for name, value in env.strike_quality.items():
            torch.testing.assert_close(value[1], before[name], equal_nan=True, rtol=0, atol=0)
        self.assertEqual(int(env.strike_quality['accepted'][0]), 0)
        self.assertFalse(bool(env.strike_quality['ever_recovered'][0]))

    def test_original_control_reward_observation_contract_and_240hz_clock_are_preserved(self):
        env, snapshot = self.make()
        parent, _ = self.make(TensorSongEnvironment)
        geometry = env.contract['diagnostics']['right_strike_quality']['geometry']
        self.assertNotIn('extra', geometry)
        self.assertNotIn('wait_rearm', geometry)
        contract = copy.deepcopy(env.contract); contract.pop('diagnostics')
        self.assertEqual(contract, parent.contract)
        for name, value in env.observation().items():
            torch.testing.assert_close(value, parent.observation()[name], rtol=0, atol=0)
        for instance in (env, parent):
            instance.begin_control(torch.zeros(2, 39))
            for _ in range(4):
                instance.substep(dict(snapshot, physics_step=instance.clock+1))
        actual, expected = env.end_control(), parent.end_control()
        for a, b in zip(actual[1:4], expected[1:4]):
            torch.testing.assert_close(a, b, rtol=0, atol=0)
        for name in env.terms:
            torch.testing.assert_close(env.terms[name], parent.terms[name], rtol=0, atol=0)
        env.begin_control(torch.zeros(2, 39))
        with self.assertRaises(ValueError):
            env.substep(snapshot)
        with self.assertRaises(RuntimeError):
            env.substep(dict(snapshot, physics_step=env.clock+2))
        self.assertEqual(env.strike_quality['physics_samples'].tolist(), [4, 4])

    def test_other_task_scopes_are_rejected(self):
        invalid = [replace(TASK, targets=(replace(TARGET, string=1),)),
            replace(TASK, targets=(replace(TARGET, direction=-1),)),
            replace(TASK, targets=(replace(TARGET, onset_s=3.01),)),
            replace(TASK, episode_duration_s=5.1)]
        for task in invalid:
            with self.subTest(task=task), self.assertRaises(ValueError):
                self.make(task=task)


if __name__ == '__main__':
    unittest.main()
