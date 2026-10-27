"""Region integration on tensor fixtures; no physical pose/success claims."""
import copy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

import torch

from guitar_learning.gpu.environment import TensorSongEnvironment
from guitar_learning.gpu.geometry import apply, multiply
from guitar_learning.skills.specialist_policy import SpecialistPolicy
from guitar_learning.song.curriculum_runtime import CurriculumCoordinator
from guitar_learning.song.left_environment import LEFT_FIELDS
from guitar_learning.tests.test_gpu_environment import fixture, BUNDLE, SONG
from guitar_learning.training.ppo import PPOTrainer


class WristRegionEnvironmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def environment(self):
        metadata, snapshot = fixture()
        env = TensorSongEnvironment(metadata, bundle=BUNDLE, song=SONG, hand='left', device='cpu')
        env.reset([0, 1], snapshot)
        return env, snapshot

    def put_wrists(self, env, snapshot, local):
        snapshot['body_state'][:, env.wrist_index, :3] = env.guitar_body[:, :3]+apply(env.guitar_q, local)

    def tick(self, env, snapshot):
        env.begin_control(torch.zeros(2, 39))
        for _ in range(4):
            env.substep(snapshot)
        return env.end_control()

    def test_inside_has_zero_observed_error_and_reward_without_orientation_target(self):
        env, snapshot = self.environment()
        lo, hi = env.guide['lower_G_m'], env.guide['upper_G_m']
        points = lo+(hi-lo)*torch.tensor([[.25], [.75]])
        self.put_wrists(env, snapshot, points)
        snapshot['body_state'][1, env.wrist_index, 3:7] = torch.tensor([1., 0., 0., 0.])
        obs = env.reset([0, 1], snapshot)
        self.assertEqual(env.guide['ready'].tolist(), [True, True])
        self.assertTrue((env.guide['delta'] == 0).all())
        self.assertTrue((env.guide['rotation'] == 0).all())
        self.assertTrue((obs['state'][:, 500:506] == 0).all())
        self.assertTrue((env.guide['position'] == 0).all())
        self.assertFalse(hasattr(env, 'reference_wrist'))
        self.tick(env, snapshot)
        self.assertTrue((env.episode_reward_terms['song_wrist_position'] == 0).all())

    def test_outside_penalty_includes_preroll_and_uses_physics_dt_and_stage_weights(self):
        for stage, weight in [(0., .2), (1., .1), (2., .05)]:
            with self.subTest(stage=stage):
                env, snapshot = self.environment()
                lo, hi = env.guide['lower_G_m'], env.guide['upper_G_m']
                points = (lo+hi)/2
                points[:, 0] = hi[:, 0]+.01
                self.put_wrists(env, snapshot, points)
                env.reset([0, 1], snapshot)
                env.set_curriculum(stage)
                torch.testing.assert_close(env.guide['delta'][:, 0], torch.full((2,), -.01), atol=3e-8, rtol=0)
                self.assertEqual(env.guide['ready'].tolist(), [False, False])
                self.assertTrue((env.clock == 0).all())
                self.tick(env, snapshot)
                torch.testing.assert_close(env.terms['song_wrist_position'], torch.full((2,), -.2/60), atol=2e-8, rtol=0)
                torch.testing.assert_close(env.episode_reward_terms['song_wrist_position'], torch.full((2,), -weight*.2/60), atol=2e-8, rtol=0)

    def test_live_guitar_frame_and_partial_reset_preserve_other_rows(self):
        env, snapshot = self.environment()
        original = env.guide['delta'].clone()
        q = torch.tensor([0., 0., .7071067811865476, .7071067811865476]).expand(2, -1)
        body = snapshot['body_state']
        body[..., :3] = apply(q[:, None], body[..., :3])+torch.tensor([.2, -.3, .1])
        body[..., 3:7] = multiply(q[:, None], body[..., 3:7])
        env.reset([0, 1], snapshot)
        torch.testing.assert_close(env.guide['delta'], original, atol=1e-7, rtol=0)
        env.clock[1] = 821*4
        env._snapshot(snapshot)
        other = env.observation()['state'][1].clone()
        self.assertTrue(env.guide['ready'][1])
        env.reset([0], snapshot)
        self.assertEqual(env.clock.tolist(), [0, 821*4])
        torch.testing.assert_close(env.observation()['state'][1], other)
        self.assertFalse(env.guide['ready'][0])
        self.assertTrue(env.guide['ready'][1])

    def test_v22_preserves_finger_actor_3331_state_and_rejects_legacy544_v8(self):
        env, snapshot = self.environment()
        pool = SimpleNamespace(environment=env, set_curriculum=env.set_curriculum)
        def make(contract):
            policy = SpecialistPolicy(contract['observation']['dimension'], size='small', contract=contract)
            coordinator = CurriculumCoordinator(policy, pool)
            return PPOTrainer(policy), coordinator
        current, _ = make(env.contract)
        self.assertEqual(current.policy.actor_heads['left'].out_features, 17)
        self.assertEqual(len(current.policy.finger_heads), 4)
        self.assertEqual(tuple(current.policy.left_curriculum_state.shape), (3331,))
        old = copy.deepcopy(env.contract)
        old['observation']['dimension'] = 544
        old['observation']['fields'] = old['observation']['fields'][:544]
        old['observation']['scales'] = old['observation']['scales'][:544]
        old['observation'].pop('thumb_support')
        old['observation']['fields'] = [field.replace('.standby_gate', '.idle_weight')
                                         for field in old['observation']['fields']]
        old['reward']['schema'] = 'guitar_learning.gpu_tensor_song_reward.v8'
        del old['reward']['wrist_region']
        del old['observation']['wrist_region']
        old['observation']['fields'][500:506] = ['left_curriculum.'+field for field in LEFT_FIELDS[:6]]
        legacy, _ = make(old)
        self.assertEqual(tuple(current.policy.state_dict()), tuple(legacy.policy.state_dict()))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'v8.pt'
            legacy.save(path)
            before = {key:value.clone() for key, value in current.policy.state_dict().items()}
            rng = torch.get_rng_state().clone()
            with self.assertRaisesRegex(ValueError, 'mismatch'):
                current.load(path)
            self.assertTrue(all(torch.equal(value, current.policy.state_dict()[key]) for key, value in before.items()))
            self.assertTrue(torch.equal(rng, torch.get_rng_state()))
            self.assertEqual(current.updates, 0)
        self.assertEqual(env.contract['reward']['schema'], 'guitar_learning.gpu_tensor_song_reward.v22')
        self.assertEqual(len(env.contract['observation']['fields']), 552)


if __name__ == '__main__':
    unittest.main()
