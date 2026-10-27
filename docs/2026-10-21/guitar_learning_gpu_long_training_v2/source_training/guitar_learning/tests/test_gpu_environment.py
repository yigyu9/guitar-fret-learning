"""CPU tensor fixtures test GPU formulas, not native physics or audio success."""
import copy
from dataclasses import replace
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np
import torch
from scipy.spatial.transform import Rotation

from guitar_learning.gpu.environment import TensorSongEnvironment, CONTACT_CONTRACT, TERMS
from guitar_learning.gpu.geometry import apply, conjugate, multiply, rotvec
from guitar_learning.music_task import ScoreTask, ScoreTarget
from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract


BUNDLE = Path(__file__).resolve().parents[2]/'data/song_bundles/05_BN2-131-B_solo'
SONG = dict(pre_roll_s=3., tail_s=.5, window_s=.5, left_fraction=.4)


def fixture(count=2):
    contract = load_prepared_reset_contract()
    initial, state = contract['initial'], contract['state']
    names = ['human/'+name for name in initial['human_body_names']]
    names += ['guitar/'+name for name in initial['guitar_body_names']]+['chair/box']
    rows = [row for kind in ('human', 'guitar', 'chair') for row in state[kind+'_body_states']]
    bodies = torch.tensor([[*[row['pose']['p'][a] for a in 'xyz'],
        *[row['pose']['r'][a] for a in 'xyzw'], *[row['vel']['linear'][a] for a in 'xyz'],
        *[row['vel']['angular'][a] for a in 'xyz']] for row in rows])
    properties = initial['human_properties']+initial['guitar_properties']['applied']
    metadata = dict(joint_names=initial['joint_names'], body_names=names,
        body_com=[row['COM_body_m'] for row in properties]+[[0., 0., 0.]],
        reference105=contract['target105'].tolist(), action_contract=dict(schema='fixture.control'))
    q = torch.tensor([row['pos'] for row in state['human_dof_states']]).expand(count, -1).clone()
    snapshot = dict(q=q, qd=torch.zeros_like(q), target=torch.tensor(contract['target105']).float().expand(count, -1).clone(),
        body_state=bodies.expand(count, -1, -1).clone(), contact_force=torch.zeros(count, len(names), 3))
    snapshot['body_state'][..., 7:] = 0
    for name in ('human/Chest', 'human/L_Ankle', 'human/R_Ankle'):
        snapshot['contact_force'][:, names.index(name), 2] = 1.
    return metadata, snapshot


class TensorSongTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def environment(self, hand='left', task=None):
        metadata, snapshot = fixture()
        factory = patch('guitar_learning.gpu.environment.make_task', return_value=task) if task else None
        if factory:
            factory.start()
        try:
            env = TensorSongEnvironment(metadata, bundle=BUNDLE, song=SONG, hand=hand, device='cpu')
        finally:
            if factory:
                factory.stop()
        observation = env.reset([0, 1], snapshot)
        return env, snapshot, observation

    @staticmethod
    def advance(env, snapshot, action=None):
        action = torch.zeros(2, 39) if action is None else action
        env.begin_control(action)
        for _ in range(4):
            env.substep(snapshot)
        return env.end_control()

    def test_shapes_mask_scaling_and_new_contract_for_both_hands(self):
        for hand, dimension in (('left', 512), ('right', 500)):
            env, snapshot, obs = self.environment(hand)
            self.assertEqual(obs['state'].shape, (2, dimension))
            self.assertEqual(obs['events'].shape, (2, 64, 24))
            self.assertEqual(obs['priority_events'].shape, (2, 2, 24))
            self.assertEqual(obs['mask'].dtype, torch.bool)
            self.assertTrue(torch.isfinite(obs['state']).all())
            self.assertTrue((obs['events'][~obs['mask']] == 0).all())
            self.assertEqual(env.contract['native_backend']['pipeline'], 'gpu')
            self.assertEqual(env.contract['task']['contact_measurement'], CONTACT_CONTRACT)
            self.assertIn('not inherited', CONTACT_CONTRACT['compatibility'])
            result = self.advance(env, snapshot)
            self.assertEqual(result[0]['state'].shape, obs['state'].shape)
            self.assertTrue(torch.isfinite(result[1]).all())
            self.assertTrue((result[2] >= 0).all())
            self.assertFalse(result[3].any())

    def test_clock_partial_reset_and_curriculum_do_not_modify_physical_tensors(self):
        env, snapshot, _ = self.environment()
        saved = {key: value.clone() for key, value in snapshot.items()}
        self.advance(env, snapshot)
        self.advance(env, snapshot)
        self.assertEqual(env.clock.tolist(), [8, 8])
        old = env.observation()['state'][1].clone()
        env.reset([0], snapshot)
        self.assertEqual(env.clock.tolist(), [0, 8])
        torch.testing.assert_close(env.observation()['state'][1], old)
        obs = env.set_curriculum(1.5)
        torch.testing.assert_close(obs['state'][:, -3:], torch.tensor([[.75, 1., .675]]).expand(2, -1))
        self.assertEqual(env.clock.tolist(), [0, 8])
        for key, value in snapshot.items():
            torch.testing.assert_close(value, saved[key])

    def test_invalid_inactive_actions_and_incomplete_substeps_rejected(self):
        env, snapshot, _ = self.environment()
        action = torch.zeros(2, 39)
        action[1, 33] = 1e-9
        with self.assertRaisesRegex(ValueError, 'inactive'):
            env.begin_control(action)
        self.assertEqual(env.clock.tolist(), [0, 0])
        env.begin_control(torch.zeros(2, 39))
        env.substep(snapshot)
        with self.assertRaisesRegex(RuntimeError, 'four'):
            env.end_control()
        with self.assertRaisesRegex(RuntimeError, 'completed control'):
            env.reset([0], snapshot)

    def test_failure_at_240hz_suppresses_tick_positive_reward_and_counts_failure_once(self):
        env, snapshot, _ = self.environment()
        env.begin_control(torch.zeros(2, 39))
        for substep in range(4):
            row = {key: value.clone() for key, value in snapshot.items()}
            if substep == 1:
                row['body_state'][0, env.guitar_index, 0] += .1
            env.substep(row)
        _, reward, cost, done, truncated, completed = env.end_control()
        self.assertEqual(done.tolist(), [True, False])
        self.assertFalse(truncated.any())
        self.assertLessEqual(float(reward[0]), -2.)
        self.assertGreaterEqual(float(cost[0]), 5.)
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0]['reason'], 'terminal_failure')
        self.assertIn('guitar_displacement', completed[0]['failure_reasons'])
        self.assertFalse(completed[0]['left_curriculum']['full_safe'])
        self.assertFalse(completed[0]['song']['stage_success'])

    def test_invalid_support_control_is_latched_physical_failure_until_selective_reset(self):
        env, snapshot, _ = self.environment()
        with self.assertRaisesRegex(RuntimeError, 'active control'):
            env.invalidate_control(torch.tensor([True, False]))
        env.begin_control(torch.zeros(2, 39))
        with self.assertRaisesRegex(ValueError, 'boolean'):
            env.invalidate_control(torch.tensor([1., 0.]))
        env.invalidate_control(torch.tensor([True, False]))
        self.assertEqual(env.control_invalid.tolist(), [True, False])
        for _ in range(4):
            # A recovered normal does not remove the failure measured earlier.
            env.invalidate_control(torch.tensor([False, False]))
            env.substep(snapshot)
        env.terms['song_wrist_position'] += 100.
        _, reward, cost, terminated, _, completed = env.end_control()
        self.assertEqual(terminated.tolist(), [True, False])
        self.assertLessEqual(float(reward[0]), -2.)
        self.assertGreaterEqual(float(cost[0]), 5.)
        self.assertEqual(completed[0]['failure_reasons'], ['support_control_invalid'])
        self.assertFalse(completed[0]['left_curriculum']['full_safe'])
        self.assertFalse(completed[0]['song']['stage_success'])
        self.assertTrue(completed[0]['song']['safety_invalidated'])
        self.assertIn('support_control_invalid', env.contract['termination']['additional_failure_reasons'])
        env.reset([0], snapshot)
        self.assertFalse(env.failure[0].any())
        self.assertFalse(env.invalid[0])
        self.assertFalse(env.control_invalid[0])
        result = self.advance(env, snapshot)
        self.assertFalse(result[3].any())

    def test_surface_candidate_requires_real_source_surface_geometry_and_load(self):
        env, snapshot, _ = self.environment()
        target = env.task.targets[0]
        body_slot = (target.finger*2)+1  # thumb occupies slots0/1
        body_index = int(env.finger_indices[body_slot])
        source = env.surface_local[body_slot, 0]
        row = {key: value.clone() for key, value in snapshot.items()}
        guitar = row['body_state'][:, env.guitar_index]
        desired = env.goals[:, 0]
        point_world = guitar[:, :3]+apply(guitar[:, 3:7], desired)
        orientation = row['body_state'][:, body_index, 3:7]
        row['body_state'][:, body_index, :3] = point_world-apply(orientation, source)
        env._snapshot(row)
        self.assertFalse(env.candidate[:, 0].any())
        row['contact_force'][:, body_index, 2] = 1.
        env._snapshot(row)
        self.assertTrue(env.candidate[:, 0].all())
        row['body_state'][:, body_index, :3] += apply(guitar[:, 3:7], torch.tensor([0., 0., .04]).expand(2, -1))
        env._snapshot(row)
        self.assertFalse(env.candidate[:, 0].any())

    def test_token_overflow_is_rejected_before_any_notes_are_dropped(self):
        target = ScoreTarget('a', 'a', 0, 5, 1, 1, .1, .2, 0., .1, .2)
        with self.assertRaisesRegex(ValueError, 'capacity overflow'):
            self.environment(task=ScoreTask((target, replace(target, target_id='b', event_id='b')), capacity=1))

    def test_wrong_assignment_and_higher_surface_contact_are_distinct_from_other_strings(self):
        env, snapshot, _ = self.environment()
        target = env.task.targets[0]
        row = {key: value.clone() for key, value in snapshot.items()}
        guitar = row['body_state'][:, env.guitar_index]

        def place(finger, string, fret):
            slot = finger*2+1
            index = int(env.finger_indices[slot])
            y = (env.frets[:, fret-1, 1]+env.frets[:, fret, 1])*.5
            start = env.starts[:, string]
            line = env.ends[:, string]-start
            goal = start+((y-start[:, 1])/line[:, 1])[:, None]*line
            world = guitar[:, :3]+apply(guitar[:, 3:7], goal)
            row['body_state'][:, index, :3] = world-apply(row['body_state'][:, index, 3:7], env.surface_local[slot, 0])
            row['contact_force'][:, index, 2] = 1.

        other = 2 if target.finger != 2 else 3
        place(other, target.string, target.fret)
        env._snapshot(row)
        self.assertTrue(env.wrong[:, 0].all())
        self.assertFalse(env.candidate[:, 0].any())
        place(target.finger, target.string, target.fret)
        env._snapshot(row)
        self.assertTrue(env.candidate[:, 0].all())
        place(other, target.string, target.fret+2)
        env._snapshot(row)
        self.assertTrue(env.wrong[:, 0].all())
        self.assertFalse(env.candidate[:, 0].any())
        place(other, (target.string+3) % 6, target.fret+2)
        env._snapshot(row)
        self.assertTrue(env.candidate[:, 0].all())

    def test_strike_rearm_and_target_matching_follow_native_substep_order(self):
        targets = (ScoreTarget('down', 'down', 0, 5, 1, 1, 1/240., .03, 0., 1/240., .03),
                   ScoreTarget('up', 'up', 0, 5, 1, -1, 4/240., .04, 0., 4/240., .04))
        env, _, _ = self.environment('right', task=ScoreTask(targets))
        env.starts = torch.tensor([[[.02-i*.02, -.4, .01] for i in range(6)]]).expand(2, -1, -1).clone()
        env.ends = env.starts.clone()
        env.ends[:, :, 1] = .2
        env.previous_pick = torch.tensor([[.01, -.32, .006]]).expand(2, -1).clone()
        env.terms = {key: torch.zeros(2) for key in TERMS}
        both = torch.ones(2, 2, dtype=torch.bool)
        for step, x in ((1, .03), (2, .03), (3, .03), (4, .01)):
            env.pick = torch.tensor([[x, -.32, .006]]).expand(2, -1).clone()
            env.clock[:] = step
            before = torch.full((2,), (step-1)/240., dtype=torch.float64)
            env._strike(before, before+1/240., both)
            env.previous_pick = env.pick.clone()
        self.assertEqual(env.geometric_crossings.tolist(), [2, 2])
        self.assertTrue(env.note['right'].all())
        self.assertTrue(env.note['match50'].all())
        self.assertEqual(env.wrong_crossings.tolist(), [0, 0])
        self.assertEqual(env.repeat_crossings.tolist(), [0, 0])

    def test_native_clock_gaps_and_nonfinite_snapshots_are_rejected(self):
        env, snapshot, _ = self.environment()
        env.begin_control(torch.zeros(2, 39))
        snapshot['physics_step'] = 1
        env.substep(snapshot)
        snapshot['physics_step'] = 3
        with self.assertRaisesRegex(ValueError, 'consecutive'):
            env.substep(snapshot)
        snapshot['physics_step'] = 2
        snapshot['q'][0, 0] = torch.nan
        with self.assertRaisesRegex(RuntimeError, 'nonfinite'):
            env.substep(snapshot)

    def test_tensor_episode_clock_respects_selective_resets_and_rejects_gap(self):
        env, snapshot, _ = self.environment()
        self.advance(env, snapshot)
        env.reset([0], snapshot)
        env.begin_control(torch.zeros(2, 39))
        snapshot['physics_step'] = torch.tensor([1, 5])
        env.substep(snapshot)
        snapshot['physics_step'] = torch.tensor([3, 6])
        with self.assertRaisesRegex(RuntimeError, 'consecutive'):
            env.substep(snapshot)

    def test_fractional_note_dwell_bonus_and_completion_are_not_horizon_resets(self):
        target = ScoreTarget('a', 'a', 0, 5, 1, 1, .003, .023, 0., .003, .023)
        env, snapshot, _ = self.environment(task=ScoreTask((target,), capacity=64))
        with patch.object(env, '_contacts', return_value=(torch.ones(2, 1, dtype=torch.bool), torch.zeros(2, 1, dtype=torch.bool))):
            env.reset([0, 1], snapshot)
            self.advance(env, snapshot)
            self.advance(env, snapshot)
        torch.testing.assert_close(env.note['clean'], torch.full((2, 1), .02, dtype=torch.float64))
        self.assertTrue(env.note['left'].all())
        self.assertEqual(env.clock.tolist(), [8, 8])
        for _ in range(6):
            result = self.advance(env, snapshot)
        self.assertTrue(result[3].all())
        self.assertEqual(len(result[5]), 2)
        self.assertTrue(result[5][0]['song']['completed'])
        self.assertEqual(result[5][0]['song']['left_success_count'], 1)


class QuaternionTests(unittest.TestCase):
    def test_tensor_rotations_match_scipy_and_shortest_rotvec(self):
        rotation = Rotation.from_rotvec([.1, -.3, .7])
        q = torch.tensor(rotation.as_quat(), dtype=torch.float64)
        point = torch.tensor([.4, .2, -.1], dtype=torch.float64)
        np.testing.assert_allclose(apply(q, point), rotation.apply(point), atol=1e-12)
        torch.testing.assert_close(apply(conjugate(q), apply(q, point)), point)
        torch.testing.assert_close(rotvec(q), torch.tensor(rotation.as_rotvec()))
        torch.testing.assert_close(rotvec(-q), rotvec(q))
        torch.testing.assert_close(multiply(conjugate(q), q), torch.tensor([0., 0., 0., 1.], dtype=torch.float64))


if __name__ == '__main__':
    unittest.main()
