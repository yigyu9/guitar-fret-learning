"""CPU 합성 표본 검사다. 관절 도달성·실제 물리·음향 성공을 뜻하지 않는다."""
import copy
import unittest
from unittest.mock import patch

import torch

from guitar_learning.gpu.compact_strike import (
    CompactStrikeEnvironment, GOAL_DIM, GOAL_FIELDS, STATE_DIM, STATE_FIELDS)
from guitar_learning.gpu.control import apply
from guitar_learning.song.strike_task import StrikeEvent, StrikeTask
from guitar_learning.tests.test_gpu_environment import fixture, BUNDLE, SONG
from guitar_learning.tool.experiments.right27.control import ACTION_NAMES, SCHEMA


def event(strings=(2,), onset=.1+1./480., offsets=None):
    strings = tuple(strings)
    offsets = tuple(offsets or (0.,)*len(strings))
    return StrikeEvent('event-0', 'single_pick' if len(strings) == 1 else 'strum',
        1, onset, strings, strings, (), offsets, offsets[-1]-offsets[0],
        (onset,)*len(strings), (.4,)*len(strings), tuple(range(len(strings))), ())


class CompactStrikeEnvironmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def make(self, events=None, duration=.5, count=2):
        events = tuple(events or (event(),))
        metadata, snapshot = fixture(count)
        metadata['action_contract'] = dict(schema=SCHEMA, action_order=list(ACTION_NAMES),
            action_lower_rad=[-3.]*39, action_upper_rad=[3.]*39)
        names = metadata['body_names']
        guitar = names.index('guitar/guitar')
        snapshot['body_state'][:, guitar, 3:7] = torch.tensor([0., 0., 0., 1.])
        origin = snapshot['body_state'][:, guitar, :3]
        # 각 현은 로컬 y축을 따르고 down은 x 증가 방향이다.
        for string in range(6):
            for suffix, y in (('', -.6), ('_end', 0.)):
                index = names.index('guitar/G:string%d%s'%(string+1, suffix))
                snapshot['body_state'][:, index, :3] = origin+torch.tensor([(5-string)*.01, y, 0.])
        snapshot['body_state'][:, names.index('human/Chest'), :3] = origin
        snapshot['q'][:] = torch.tensor(metadata['reference105'])
        snapshot['target'][:] = snapshot['q']
        first = events[0].traversal_strings[0]
        snapshot['body_state'][:, names.index('human/RH:pick'), :3] = origin+torch.tensor([(5-first)*.01-.008, -.32, -.008])
        with patch('guitar_learning.gpu.compact_strike.load_strike_task',
                   return_value=StrikeTask(events, duration, dict(schema='synthetic.cpu.only'))):
            env = CompactStrikeEnvironment(metadata, bundle=BUNDLE, song=SONG, device='cpu')
        observation = env.reset(range(count), snapshot)
        return env, snapshot, observation

    def pick(self, env, snapshot, x, z=-.008, y=-.32):
        result = {key: value.clone() for key, value in snapshot.items()}
        local = torch.tensor([x, y, z]).expand(env.N, -1)
        guitar = result['body_state'][:, env.guitar_index]
        result['body_state'][:, env.pick_index, :3] = guitar[:, :3]+apply(guitar[:, 3:7], local)
        return result

    def tick(self, env, snapshot, actions=None, samples=None):
        env.begin_control(torch.zeros(env.N, 39) if actions is None else actions)
        for index in range(4):
            source = snapshot if samples is None else samples[index]
            env.substep(dict(source, physics_step=env.clock+1))
        return env.end_control()

    def prepare(self, env, snapshot):
        for _ in range(6):
            self.tick(env, snapshot)
        self.assertTrue(env.ledger.history['ready'].all())

    def finish(self, env, snapshot):
        while not env.finished.all():
            result = self.tick(env, snapshot)
        return result

    def test_shapes_masks_contract_and_observation_does_not_change_history(self):
        env, _, obs = self.make(events=(event(onset=.5), event(onset=1.)), duration=1.5)
        self.assertEqual((STATE_DIM, GOAL_DIM), (450, 79))
        self.assertEqual(obs['state'].shape, (2, 450))
        self.assertEqual(obs['events'].shape, (2, 0, 79))
        self.assertEqual(obs['priority_events'].shape, (2, 2, 79))
        self.assertTrue(obs['priority_mask'].all())
        self.assertEqual(len(env.contract['observation']['fields']), 450)
        self.assertEqual(len(env.contract['observation']['event_scales']), 79)
        self.assertEqual(len(GOAL_FIELDS), GOAL_DIM)
        before = {key: value.clone() for key, value in env.ledger.history.items()}
        env.observation(); env.observation()
        for key, value in before.items():
            torch.testing.assert_close(env.ledger.history[key], value)
        one, _, observation = self.make()
        self.assertEqual(observation['priority_mask'].tolist(), [[True, False], [True, False]])
        self.assertTrue((observation['priority_events'][:, 1] == 0).all())
        self.assertTrue(torch.isfinite(observation['state']).all())
        self.assertEqual(one.contract['action']['active_indices'], list(range(12, 39)))

    def test_partial_reset_preserves_other_rows_and_never_writes_physical_inputs(self):
        env, snapshot, _ = self.make(events=(event(onset=.5),), duration=1.)
        original = {key: value.clone() for key, value in snapshot.items()}
        self.prepare(env, snapshot)
        env.ledger.history['wrong'][1, 0] = True
        env.ledger.history['accepted'][1, 0, 2] = True
        history = {key: value[1].clone() for key, value in env.ledger.history.items()}
        other_observation = env.observation()['state'][1].clone()
        env.reset([0], snapshot)
        self.assertEqual(env.clock.tolist(), [0, 24])
        self.assertFalse(env.ledger.history['ready'][0, 0])
        for key, value in history.items():
            torch.testing.assert_close(env.ledger.history[key][1], value)
        torch.testing.assert_close(env.observation()['state'][1], other_observation)
        for key, value in original.items():
            torch.testing.assert_close(snapshot[key], value)

    def test_27_actions_are_retained_and_inactive12_are_rejected(self):
        env, snapshot, _ = self.make()
        action = torch.zeros(2, 39)
        action[:, 12:] = torch.linspace(-1., 1., 27)
        obs, *_ = self.tick(env, snapshot, actions=action)
        torch.testing.assert_close(env.previous_action, action)
        first = STATE_FIELDS.index('previous_action.'+ACTION_NAMES[12])
        torch.testing.assert_close(obs['state'][:, first:first+27], action[:, 12:])
        action[:, 0] = 1e-9
        with self.assertRaisesRegex(ValueError, 'first12 zero'):
            env.begin_control(action)
        for invalid in (torch.zeros(2, 27), torch.full((2, 39), float('nan')), torch.ones(2, 39)*1.01):
            with self.assertRaises(ValueError):
                env.begin_control(invalid)

    def test_four_consecutive_actual_physics_samples_are_required(self):
        env, snapshot, _ = self.make()
        env.begin_control(torch.zeros(2, 39))
        with self.assertRaisesRegex(ValueError, 'physics_step'):
            env.substep(snapshot)
        with self.assertRaisesRegex(RuntimeError, 'consecutive'):
            env.substep(dict(snapshot, physics_step=env.clock+2))
        env.substep(dict(snapshot, physics_step=env.clock+1))
        with self.assertRaisesRegex(RuntimeError, 'four'):
            env.end_control()
        with self.assertRaisesRegex(RuntimeError, 'completed control'):
            env.reset([0], snapshot)
        for _ in range(3):
            env.substep(dict(snapshot, physics_step=env.clock+1))
        with self.assertRaisesRegex(RuntimeError, 'four'):
            env.substep(dict(snapshot, physics_step=env.clock+1))
        env.end_control()
        self.assertEqual(env.clock.tolist(), [4, 4])

    def test_readiness_requires_six_control_ticks_and_exact_hit_completes_once(self):
        env, snapshot, _ = self.make()
        for _ in range(5):
            self.tick(env, snapshot)
        self.assertFalse(env.ledger.history['ready'].any())
        self.tick(env, snapshot)
        self.assertTrue(env.ledger.history['ready'].all())
        after = self.pick(env, snapshot, .038)
        self.tick(env, after)
        h = env.ledger.history
        self.assertTrue(h['complete'].all())
        self.assertTrue(h['clean_complete'].all())
        self.assertEqual(env.geometric_crossings.tolist(), [1, 1])
        torch.testing.assert_close(h['times'][:, 0, 2], torch.full((2,), .1+1./480., dtype=torch.float64), atol=2e-8, rtol=0)
        _, _, _, done, _, episodes = self.finish(env, after)
        self.assertTrue(done.all())
        self.assertEqual(len(episodes), 2)
        self.assertTrue(all(row['song']['stage_success'] for row in episodes))
        self.assertEqual([row['song']['clean_complete'] for row in episodes], [1, 1])

    def test_strum_needs_entire_ordered_traversal_and_preserves_partial_progress(self):
        offsets = (-.001, 0., .001)
        env, snapshot, _ = self.make(events=(event((3, 2, 1), offsets=offsets),))
        self.prepare(env, snapshot)
        first = self.pick(env, snapshot, .025)
        self.tick(env, first)
        self.assertTrue(env.ledger.history['accepted'][:, 0, 3].all())
        self.assertFalse(env.ledger.history['complete'].any())
        second = self.pick(env, snapshot, .048)
        self.tick(env, second)
        self.assertTrue(env.ledger.history['clean_complete'].all())
        self.assertTrue(env.ledger.history['accepted'][:, 0, [3, 2, 1]].all())
        times = env.ledger.history['times'][:, 0, [3, 2, 1]]
        self.assertTrue((times[:, 1:] > times[:, :-1]).all())
        _, _, _, _, _, episodes = self.finish(env, second)
        self.assertTrue(all(row['song']['stage_success'] for row in episodes))

    def test_strum_out_of_order_hit_cannot_be_clean_complete(self):
        env, snapshot, _ = self.make(events=(event((3, 2, 1), offsets=(-.001, 0., .001)),))
        self.prepare(env, snapshot)
        above = self.pick(env, snapshot, .032, z=.02)
        below = self.pick(env, snapshot, .032)
        skipped = self.pick(env, snapshot, .048)
        self.tick(env, skipped, samples=(above, below, skipped, skipped))
        self.assertTrue(env.ledger.history['wrong'].all())
        self.assertEqual(env.ledger.history['order_violation'].sum().item(), 2.)
        self.assertFalse(env.ledger.history['complete'].any())
        self.assertFalse(env.ledger.history['clean_complete'].any())

    def test_blocked_immediate_recross_revokes_clean_reward_and_recovery_payment(self):
        env, snapshot, _ = self.make()
        self.prepare(env, snapshot)
        after = self.pick(env, snapshot, .038)
        # 실제 교차 다음 1/240초에 원래 쪽으로 돌아오지만 아직 재무장 전이다.
        self.tick(env, snapshot, samples=(after, snapshot, snapshot, snapshot))
        self.assertEqual(env.geometric_crossings.tolist(), [1, 1])
        self.assertEqual(env.blocked_crossings.tolist(), [1, 1])
        self.assertTrue(env.ledger.history['complete'].all())
        self.assertTrue(env.ledger.history['wrong'].all())
        self.assertEqual(env.ledger.history['unplanned'][:, 0].tolist(), [1., 1.])
        self.assertFalse(env.ledger.history['clean_complete'].any())
        torch.testing.assert_close(env.ledger.terms['wrong'], torch.ones(2))
        for term in ('crossing', 'timing', 'recovery_progress', 'recovery_complete'):
            torch.testing.assert_close(env.ledger.terms[term], torch.zeros(2))
        _, _, _, _, _, episodes = self.finish(env, snapshot)
        for row in episodes:
            self.assertFalse(row['song']['stage_success'])
            self.assertEqual(row['song']['wrong_crossings'], 1)
            self.assertEqual(row['rearm_blocked_crossings'], 1)
            self.assertEqual(row['reward_components']['crossing'], 0.)
            self.assertEqual(row['reward_components']['recovery_progress'], 0.)
            self.assertEqual(row['reward_components']['recovery_complete'], 0.)

    def test_two_armed_strings_in_one_physics_interval_keep_strum_time_order(self):
        env, snapshot, _ = self.make(events=(event((3, 2), offsets=(-.001, .001)),))
        self.prepare(env, snapshot)
        after = self.pick(env, snapshot, .038)
        env.begin_control(torch.zeros(2, 39))
        env.substep(dict(after, physics_step=env.clock+1))
        self.assertEqual(env.geometric_crossings.tolist(), [2, 2])
        self.assertEqual(env.blocked_crossings.tolist(), [0, 0])
        self.assertTrue(env.ledger.history['clean_complete'].all())
        self.assertFalse(env.ledger.history['wrong'].any())
        times = env.ledger.history['times'][:, 0, [3, 2]]
        self.assertTrue((times[:, 0] < times[:, 1]).all())
        self.assertTrue((times > .1).all())
        self.assertTrue((times < .1+1./240.).all())
        for _ in range(3):
            env.substep(dict(after, physics_step=env.clock+1))
        env.end_control()
        _, _, _, _, _, episodes = self.finish(env, after)
        self.assertTrue(all(row['song']['stage_success'] for row in episodes))

    def test_failure_overrides_positive_rewards_with_exact_minus10(self):
        env, snapshot, _ = self.make()
        self.prepare(env, snapshot)
        after = self.pick(env, snapshot, .038)
        failed = {key: value.clone() for key, value in after.items()}
        failed['qd'][0, 0] = 51.
        _, reward, cost, done, _, episodes = self.tick(env, after, samples=(after, failed, after, after))
        self.assertEqual(done.tolist(), [True, False])
        self.assertEqual(reward[0].item(), -10.)
        self.assertGreaterEqual(cost[0].item(), 5.)
        self.assertTrue(env.ledger.history['clean_complete'][0, 0])
        self.assertFalse(episodes[0]['song']['stage_success'])
        self.assertEqual(episodes[0]['reason'], 'terminal_failure')
        self.assertAlmostEqual(sum(episodes[0]['reward_components'].values()), episodes[0]['reward'], delta=2e-6)

    def test_readiness_streak_restarts_after_preparation_is_lost(self):
        env, snapshot, _ = self.make(events=(event(onset=.5),), duration=1.)
        for _ in range(5):
            self.tick(env, snapshot)
        far = self.pick(env, snapshot, .022, y=-.35)
        self.tick(env, far)
        torch.testing.assert_close(env.ledger.ready_elapsed, torch.zeros(2))
        for _ in range(5):
            self.tick(env, snapshot)
        self.assertFalse(env.ledger.history['ready'].any())
        self.tick(env, snapshot)
        self.assertTrue(env.ledger.history['ready'].all())

    def test_moving_guitar_relative_pick_velocity_cancels_rigid_motion(self):
        env, snapshot, _ = self.make()
        moving = {key: value.clone() for key, value in snapshot.items()}
        bodies = moving['body_state']
        omega = torch.tensor([0., 0., .7]).expand(env.N, -1)
        translation = torch.tensor([.2, -.1, .3]).expand(env.N, -1)
        center = bodies[:, env.guitar_index, :3].clone()
        bodies[..., 10:13] = omega[:, None]
        com = apply(bodies[..., 3:7], env.com[None].expand(env.N, -1, -1))
        bodies[..., 7:10] = translation[:, None]+torch.cross(omega[:, None].expand_as(com),
            bodies[..., :3]-center[:, None]+com, dim=-1)
        env._snapshot(moving)
        torch.testing.assert_close(env.pick_velocity, torch.zeros_like(env.pick_velocity), atol=1e-7, rtol=0)
        pick_state = env._relative_state(env.pick_index, env.guitar_index)
        torch.testing.assert_close(pick_state[:, 9:12], torch.zeros(2, 3), atol=1e-7, rtol=0)
        torch.testing.assert_close(pick_state[:, 12:15], torch.zeros(2, 3), atol=1e-7, rtol=0)

    def test_collection_boundary_and_observation_preserve_event_ledger(self):
        env, snapshot, _ = self.make()
        self.prepare(env, snapshot)
        after = self.pick(env, snapshot, .038)
        self.tick(env, after)
        clock = env.clock.clone()
        history = {key: value.clone() for key, value in env.ledger.history.items()}
        env.reset_reward_window()
        env.set_training_progress(2048)
        env.set_curriculum(1.)
        env.observation()
        torch.testing.assert_close(env.clock, clock)
        for key, value in history.items():
            torch.testing.assert_close(env.ledger.history[key], value)
        self.tick(env, after)
        self.assertTrue(env.ledger.history['complete'].all())

    def test_control_contract_and_native_snapshot_shape_are_validated(self):
        env, snapshot, _ = self.make()
        wrong = copy.deepcopy(env.contract['action']['target_contract'])
        wrong['action_order'][12:14] = reversed(wrong['action_order'][12:14])
        with self.assertRaisesRegex(ValueError, 'right27 controller'):
            env.bind_action_contract(wrong)
        wrong = copy.deepcopy(env.contract['action']['target_contract'])
        wrong['action_upper_rad'][12] = wrong['action_lower_rad'][12]
        with self.assertRaisesRegex(ValueError, 'ordered right27 bounds'):
            env.bind_action_contract(wrong)
        env.begin_control(torch.zeros(2, 39))
        malformed = dict(snapshot, q=torch.zeros(2, 104), physics_step=env.clock+1)
        with self.assertRaisesRegex(ValueError, 'shape mismatch: q'):
            env.substep(malformed)


if __name__ == '__main__':
    unittest.main()
