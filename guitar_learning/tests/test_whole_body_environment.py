"""전신 학습의 CPU 계산 계약 검사. 물리 제어·학습 성능 검증은 아니다."""
import copy
import math
import unittest

import torch

from guitar_learning.gpu.whole_body import REWARD_TERMS, STATE_FIELDS, WholeBodyEnvironment
from guitar_learning.gpu.whole_body_control import ACTION_NAMES, SCHEMA
from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract
from guitar_learning.tests.test_gpu_environment import fixture


def body_fixture():
    metadata, snapshot = fixture()
    initial = load_prepared_reset_contract()['initial']
    properties = initial['human_properties'] + initial['guitar_properties']['applied']
    metadata['body_mass'] = [row['mass_kg'] for row in properties] + [100000.]
    metadata['action_contract'] = dict(schema=SCHEMA, action_order=list(ACTION_NAMES))
    snapshot['q'] = snapshot['target'].clone()
    return metadata, snapshot


class WholeBodyEnvironmentTests(unittest.TestCase):
    def environment(self, duration_s=10.):
        metadata, snapshot = body_fixture()
        env = WholeBodyEnvironment(metadata, duration_s=duration_s, device='cpu')
        env.reset([0, 1], snapshot)
        return env, snapshot

    @staticmethod
    def sample(env, snapshot):
        return dict(snapshot, physics_step=env.clock.clone()+1)

    def advance(self, env, snapshot, action=None):
        env.begin_control(torch.zeros(2, 37) if action is None else action)
        for _ in range(4):
            env.substep(self.sample(env, snapshot))
        return env.end_control()

    @staticmethod
    def raw_fields(env, prefix):
        indices = [i for i, name in enumerate(STATE_FIELDS) if name.startswith(prefix)]
        return env.observation()['state'][:, indices] * env.scales[indices]

    def test_state484_empty_goals_and_observation_does_not_advance_or_mutate(self):
        env, snapshot = self.environment()
        original = {name: value.clone() for name, value in snapshot.items()}
        first = env.observation()
        self.assertEqual(first['state'].shape, (2, 484))
        self.assertEqual(first['events'].shape, (2, 0, 0))
        self.assertEqual(first['priority_events'].shape, (2, 0, 0))
        self.assertEqual(first['mask'].shape, (2, 0))
        self.assertEqual(first['priority_mask'].dtype, torch.bool)
        self.assertTrue(torch.isfinite(first['state']).all())
        for _ in range(3):
            torch.testing.assert_close(env.observation()['state'], first['state'], rtol=0, atol=0)
        self.assertEqual(env.clock.tolist(), [0, 0])
        self.assertTrue((env.loss == 0).all())
        for name, value in snapshot.items():
            self.assertTrue(torch.equal(value, original[name]), name)

    def test_combined_com_uses_source_offsets_pelvis_frame_and_excludes_chair(self):
        metadata, snapshot = body_fixture()
        names = metadata['body_names']
        pelvis, chest, guitar = [names.index(name) for name in ('human/Pelvis', 'human/Chest', 'guitar/guitar')]
        metadata['body_mass'] = [0.]*len(names)
        metadata['body_mass'][chest], metadata['body_mass'][guitar] = 2., 1.
        metadata['body_mass'][-1] = 100000.
        metadata['body_com'] = [[0., 0., 0.] for _ in names]
        metadata['body_com'][chest], metadata['body_com'][guitar] = [1., 0., 0.], [0., 1., 0.]
        bodies = snapshot['body_state']
        bodies.zero_()
        bodies[..., 6] = 1.
        bodies[:, pelvis, :3] = torch.tensor([1., 2., 3.])
        bodies[:, pelvis, 3:7] = torch.tensor([0., 0., math.sqrt(.5), math.sqrt(.5)])
        bodies[:, pelvis, 7:10] = torch.tensor([1., 0., 0.])
        bodies[:, pelvis, 12] = 2.
        bodies[:, chest, :3] = torch.tensor([4., 2., 3.])
        bodies[:, guitar, :3] = torch.tensor([1., 5., 3.])
        bodies[:, chest, 7:10] = torch.tensor([1., 2., 0.])
        bodies[:, guitar, 7:10] = torch.tensor([4., 2., 0.])
        bodies[:, -1, :3] = 1000.
        env = WholeBodyEnvironment(metadata, device='cpu')
        env.reset([0, 1], snapshot)
        expected = torch.tensor([4/3, -8/3, 0., -10/3, -11/3, 0.]).expand(2, -1)
        torch.testing.assert_close(self.raw_fields(env, 'combined_com.'), expected)

    def test_support_forces_are_pelvis_relative_and_sum_ankle_and_toe(self):
        metadata, snapshot = body_fixture()
        names = metadata['body_names']
        pelvis = names.index('human/Pelvis')
        snapshot['body_state'][:, pelvis, 3:7] = torch.tensor([0., 0., math.sqrt(.5), math.sqrt(.5)])
        forces = snapshot['contact_force']
        forces.zero_()
        world = {'human/Chest': [3., 4., 5.], 'human/R_Shoulder': [-1., 2., 0.],
                 'human/R_Hip': [0., -2., 3.], 'human/L_Ankle': [1., 2., 3.],
                 'human/L_Toe': [4., 5., 6.], 'human/R_Ankle': [-2., 3., 4.],
                 'human/R_Toe': [1., -1., 2.]}
        for name, force in world.items():
            forces[:, names.index(name)] = torch.tensor(force)
        env = WholeBodyEnvironment(metadata, device='cpu')
        env.reset([0, 1], snapshot)
        expected = torch.tensor([4., -3., 5., 2., 1., 0., -2., 0., 3.,
                                 7., -5., 9., 2., 1., 6.]).expand(2, -1)
        torch.testing.assert_close(self.raw_fields(env, 'support_force.'), expected)

    def test_four_sequential_physics_samples_and_partial_reset(self):
        env, snapshot = self.environment()
        snapshot['contact_force'][1, env.flag_indices[-2]] = 0
        env.begin_control(torch.zeros(2, 37))
        with self.assertRaises(ValueError):
            env.substep(dict(snapshot, physics_step=torch.tensor([2, 1])))
        self.assertEqual(env.clock.tolist(), [0, 0])
        for _ in range(3):
            env.substep(self.sample(env, snapshot))
        with self.assertRaises(RuntimeError):
            env.end_control()
        with self.assertRaises(RuntimeError):
            env.reset([0], snapshot)
        env.substep(self.sample(env, snapshot))
        with self.assertRaises(RuntimeError):
            env.substep(self.sample(env, snapshot))
        env.end_control()
        before = env.observation()['state'][1].clone()
        loss = env.loss[1].clone()
        env.reset([0], snapshot)
        self.assertEqual(env.clock.tolist(), [0, 4])
        torch.testing.assert_close(env.loss[1], loss, rtol=0, atol=0)
        torch.testing.assert_close(env.observation()['state'][1], before, rtol=0, atol=0)
        self.advance(env, snapshot)
        self.assertEqual(env.clock.tolist(), [4, 8])

    def test_contact_loss_grace_is_continuous_and_strictly_exceeds_quarter_second(self):
        env, snapshot = self.environment()
        missing = copy.deepcopy(snapshot)
        missing['contact_force'][0, env.flag_indices[-2]] = 0
        for _ in range(14):
            self.assertFalse(self.advance(env, missing)[3].any())
        self.advance(env, snapshot)
        self.assertEqual(float(env.loss[0, 1]), 0.)
        for _ in range(15):
            self.assertFalse(self.advance(env, missing)[3].any())
        self.assertAlmostEqual(float(env.loss[0, 1]), .25, places=6)
        result = self.advance(env, missing)
        self.assertEqual(result[3].tolist(), [True, False])
        self.assertIn('ground_contact_lost', result[5][0]['failures'])

    def test_transient_failure_latches_suppresses_positive_reward_and_costs_once(self):
        env, snapshot = self.environment()
        env.begin_control(torch.zeros(2, 37))
        for i in range(4):
            sample = copy.deepcopy(self.sample(env, snapshot))
            if i == 1:
                sample['qd'][0, 0] = 51.
            env.substep(sample)
        _, reward, cost, done, truncated, episodes = env.end_control()
        self.assertEqual(done.tolist(), [True, False])
        self.assertFalse(truncated.any())
        self.assertEqual(float(reward[0]), 0.)
        self.assertGreater(float(reward[1]), 0.)
        self.assertAlmostEqual(float(cost[0]), 5.+2.*(10.-4/240.), places=5)
        self.assertAlmostEqual(float(cost[1]), 0., places=7)
        self.assertEqual(episodes[0]['failures'], ['joint_speed'])
        self.assertFalse(episodes[0]['safe_completion'])
        self.assertTrue(all(episodes[0]['reward_components'][key] == 0 for key in REWARD_TERMS))
        with self.assertRaises(RuntimeError):
            env.end_control()
        with self.assertRaises(RuntimeError):
            env.begin_control(torch.zeros(2, 37))
        torch.testing.assert_close(env.total_cost, cost)

    def test_safe_time_limit_completion_and_tracking_metrics(self):
        env, snapshot = self.environment(duration_s=2/60.)
        snapshot['target'][:, env.active_joints[0]] += .03
        first = self.advance(env, snapshot)
        self.assertFalse(first[3].any())
        result = self.advance(env, snapshot)
        self.assertTrue(result[3].all())
        self.assertFalse(result[4].any())
        self.assertEqual(len(result[5]), 2)
        for episode in result[5]:
            self.assertTrue(episode['safe_completion'])
            self.assertFalse(episode['failed'])
            self.assertAlmostEqual(episode['duration_s'], 2/60.)
            self.assertAlmostEqual(episode['tracking_rmse_rad'][0], .03, places=5)
            self.assertAlmostEqual(episode['tracking_max_rad'][0], .03, places=5)

    def test_invalid_actions_and_snapshots_rejected_before_state_changes(self):
        env, snapshot = self.environment()
        for action in (torch.zeros(2, 39), torch.full((2, 37), float('nan')),
                       torch.ones(2, 37)*1.01, torch.zeros(2, 37, dtype=torch.bool)):
            with self.assertRaises(ValueError):
                env.begin_control(action)
            self.assertIsNone(env._substeps)
        env.begin_control(torch.zeros(2, 37))
        malformed = copy.deepcopy(self.sample(env, snapshot))
        malformed['q'][0, 0] = float('nan')
        with self.assertRaises(ValueError):
            env.substep(malformed)
        self.assertEqual(env.clock.tolist(), [0, 0])
        self.assertEqual(env._substeps, 0)
        self.assertTrue((env.loss == 0).all())
        for _ in range(4):
            env.substep(self.sample(env, snapshot))
        env.end_control()
        before = env.observation()['state'].clone()
        malformed = copy.deepcopy(snapshot)
        malformed['body_state'][0, 0, 3:7] = 0.
        with self.assertRaises(ValueError):
            env.reset([0], malformed)
        torch.testing.assert_close(env.observation()['state'], before, rtol=0, atol=0)


if __name__ == '__main__':
    unittest.main()
