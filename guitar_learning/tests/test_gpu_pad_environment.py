"""CPU pad integration and resume semantics; no native contact certification."""
import copy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import torch

from guitar_learning.gpu.control import apply, multiply
from guitar_learning.training.policy import SpecialistPolicy
from guitar_learning.song.curriculum_runtime import CurriculumCoordinator
from guitar_learning.tests import test_gpu_environment as fixtures
from guitar_learning.tests.test_gpu_surface_learning import task
from guitar_learning.training.ppo import PPOTrainer


class PadEnvironmentTests(unittest.TestCase):
    environment = fixtures.TensorSongTests.environment
    advance = staticmethod(fixtures.TensorSongTests.advance)

    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def placed(self, facing=True, loaded=True, offset=0.):
        env, initial, _ = self.environment(task=task((1,), end=.2))
        env.pad_valid[0] = False
        env.pad_valid[0, 0] = True
        goal = fixtures.press_goal(env)+torch.tensor([0., 0., offset])
        row = fixtures.place_pad_sample(env, initial, 1, goal, loaded, facing)
        env.reset([0, 1], row)
        return env, row

    def test_pad_facing_load_and_signed_height_are_independent_requirements(self):
        for facing, loaded, height, expected in ((True, True, 0., True),
                (True, False, 0., False), (False, True, 0., False),
                (True, True, -.002, False), (True, True, .004, False)):
            with self.subTest(facing=facing, loaded=loaded, height=height):
                env, row = self.placed(facing, loaded, height)
                self.assertEqual(env.candidate[:, 0].tolist(), [expected]*2)
                torch.testing.assert_close(env.surface_alignment[:, 0],
                    torch.full((2,), 1. if facing else -1.), atol=1e-6, rtol=0)
                torch.testing.assert_close(env.surface_height[:, 0],
                    torch.full((2,), height), atol=1e-7, rtol=0)
                self.assertTrue(torch.isfinite(env.surface_delta).all())
                self.assertTrue(torch.isfinite(env.surface_velocity).all())
                self.assertTrue(torch.isfinite(env.surface_distance).all())
                if not expected:
                    self.advance(env, row)
                    self.assertFalse(env.note['contact_done'].any())

    def test_backface_keeps_finite_approach_signal_and_distance_improvement(self):
        env, far = self.placed(facing=False, loaded=False, offset=.08)
        before = env._surface_potential().clone()
        near = fixtures.place_pad_sample(env, far, 1, fixtures.press_goal(env), False, False)
        self.advance(env, near)
        self.assertFalse(env.candidate.any())
        self.assertTrue((env.surface_alignment < -.99).all())
        self.assertTrue((env.terms['song_left_approach'] > 0).all())
        torch.testing.assert_close(env.terms['song_left_approach'],
            .99*env._surface_potential()-before)
        self.assertTrue((env.terms['song_finger_tracking'] > 0).all())

    def test_middle_surface_load_cannot_replace_distal_pad(self):
        env, initial, _ = self.environment(task=task((1,)))
        row = {key:value.clone() for key, value in initial.items()}
        # All positive distal bodies far away; a real middle-mesh point is at
        # target and is the only loaded finger body.
        row['body_state'][:, env.pad_indices, :3] += 1.
        row['contact_force'][:, env.finger_indices] = 0.
        middle_slot = 2
        index = int(env.finger_indices[middle_slot])
        guitar = row['body_state'][:, env.guitar_index]
        goal = env.goals[:, 0]
        world = guitar[:, :3]+apply(guitar[:, 3:7], goal)
        row['body_state'][:, index, :3] = world-apply(
            row['body_state'][:, index, 3:7], env.surface_local[middle_slot, 0])
        row['contact_force'][:, index, 2] = 1.
        env.reset([0, 1], row)
        self.assertFalse(env.candidate.any())
        self.advance(env, row)
        self.assertFalse(env.note['contact_done'].any())
        self.assertTrue((env.note['middle_target_time'] > 0).all())
        self.assertTrue((env.note['rejected_target_time'] > 0).all())
        self.assertEqual(env.terms['song_left_contact'].tolist(), [0., 0.])
        self.assertEqual(env.terms['song_left_success'].tolist(), [0., 0.])

    def test_dorsal_surface_at_goal_is_not_a_positive_pad_sample(self):
        env, initial, _ = self.environment(task=task((1,)))
        row = {key:value.clone() for key, value in initial.items()}
        slot = 3  # index distal in the preserved full-surface buffer
        index = int(env.finger_indices[slot])
        valid = env.surface_valid.reshape(10, -1)[slot]
        points = env.surface_local[slot]
        dorsal = points[torch.where(valid, points[:, 2], -torch.inf).argmax()]
        self.assertGreater(float(dorsal[2]), 0.)
        guitar = row['body_state'][:, env.guitar_index]
        goal = fixtures.press_goal(env)
        row['body_state'][:, index, 3:7] = guitar[:, 3:7]
        row['body_state'][:, index, :3] = guitar[:, :3]+apply(guitar[:, 3:7], goal-dorsal)
        row['contact_force'][:, index, 2] = 1.
        env.reset([0, 1], row)
        self.assertFalse(env.candidate.any())
        self.assertTrue((env.surface_distance > .003).all())
        self.advance(env, row)
        self.assertFalse(env.note['contact_done'].any())
        self.assertEqual(env.terms['song_left_contact'].tolist(), [0., 0.])
        # Keeping a nonzero approach value is intentional: the real palmar pad
        # can still move toward the goal; the dorsal point itself is not used.
        self.assertTrue(torch.isfinite(env._surface_potential()).all())

    def test_full_surface_wrong_contact_still_blocks_clean_success(self):
        env, row = self.placed()
        # The assigned pad remains valid; a different finger's full middle
        # surface touches the same wire two frets higher.
        slot = 4
        index = int(env.finger_indices[slot])
        fret = env.task.targets[0].fret+2
        string = env.task.targets[0].string
        start = env.starts[:, string]
        line = env.ends[:, string]-start
        y = (env.frets[:, fret-1, 1]+env.frets[:, fret, 1])*.5
        goal = start+((y-start[:, 1])/line[:, 1])[:, None]*line
        guitar = row['body_state'][:, env.guitar_index]
        world = guitar[:, :3]+apply(guitar[:, 3:7], goal)
        row['body_state'][:, index, :3] = world-apply(
            row['body_state'][:, index, 3:7], env.surface_local[slot, 0])
        row['contact_force'][:, index, 2] = 1.
        env._snapshot(row)
        self.assertTrue(env.contact_geometry.all())
        self.assertTrue(env.wrong.all())
        self.assertFalse(env.candidate.any())
        self.advance(env, row)
        self.assertTrue((env.note['higher_time'] > 0).all())
        self.assertFalse(env.note['left'].any())

    def test_pad_normal_events_and_geometry_rotate_with_live_guitar(self):
        env, row = self.placed()
        events = env._events()[0]
        torch.testing.assert_close(events[:, 0, 22], env.surface_alignment[:, 0])
        torch.testing.assert_close(events[:, 0, 23]*env.event_scales[23], env.surface_height[:, 0])
        before = (env.surface_delta.clone(), env.surface_alignment.clone(), env.surface_height.clone())
        q = torch.tensor([.3, -.4, .5, .7]); q /= q.norm()
        row['body_state'][..., :3] = apply(q, row['body_state'][..., :3])+torch.tensor([.2, .1, -.3])
        row['body_state'][..., 3:7] = multiply(q[None, None], row['body_state'][..., 3:7])
        env._snapshot(row)
        for actual, expected in zip((env.surface_delta, env.surface_alignment, env.surface_height), before):
            torch.testing.assert_close(actual, expected, atol=4e-7, rtol=0)
        self.assertTrue(env.candidate.all())
        self.assertEqual(env.contract['observation']['surface_geometry']['schema'], 'guitar_learning.left_surface_events.v5')
        self.assertEqual(env.observation()['state'].shape, (2, 552))
        self.assertEqual(env.observation()['priority_events'].shape, (2, 8, 24))

    def test_valid_pad_achieves_and_backface_fails_with_ledger_fields(self):
        env, row = self.placed()
        # Two batch rows exercise valid and backfacing samples simultaneously.
        back = fixtures.place_pad_sample(env, row, 1, fixtures.press_goal(env), True, False)
        row['body_state'][1] = back['body_state'][1]
        env.reset([0, 1], row)
        for _ in range(6):
            self.advance(env, row)
        self.assertEqual(env.note['left'][:, 0].tolist(), [True, False])
        self.assertGreater(float(env.note['facing_time'][0, 0]), 0.)
        self.assertEqual(float(env.note['facing_time'][1, 0]), 0.)
        self.assertEqual(float(env.note['loaded_target_time'][1, 0]), 0.)
        ledger = env._episode(1, False)['left_note_ledger']
        self.assertEqual(ledger['schema'], 'guitar_learning.surface_note_ledger.v7')
        for key in ('facing_time', 'middle_target_time', 'distal_target_time', 'rejected_target_time'):
            self.assertIn(key, ledger['values'])

    def test_v22_preserved3331_roundtrip_and_v9_strict_resume_rejection(self):
        env, _, observation = self.environment()
        pool = SimpleNamespace(environment=env, set_curriculum=env.set_curriculum)
        def make(contract):
            policy = SpecialistPolicy(contract['observation']['dimension'], size='small', role='left', contract=contract)
            coordinator = CurriculumCoordinator(policy, pool)
            return policy, coordinator, PPOTrainer(policy)
        policy, coordinator, trainer = make(env.contract)
        evidence = dict(valid=True, reason='timeline_complete', left_curriculum=dict(full_safe=True,
            finger_metrics=[dict(target_count=n, near_fraction=1., contact_fraction=0., success_fraction=0.)
                            for n in env.finger_counts]))
        coordinator.advance([evidence]*256, observation)
        self.assertEqual(tuple(policy.left_curriculum_state.shape), (3331,))
        self.assertEqual(env.contract['reward']['schema'], 'guitar_learning.gpu_tensor_song_reward.v22')
        old = copy.deepcopy(env.contract)
        old['observation']['dimension'] = 544
        old['observation']['fields'] = old['observation']['fields'][:544]
        old['observation']['scales'] = old['observation']['scales'][:544]
        old['observation'].pop('thumb_support')
        old['observation']['fields'] = [field.replace('.standby_gate', '.idle_weight')
                                         for field in old['observation']['fields']]
        old['reward']['schema'] = 'guitar_learning.gpu_tensor_song_reward.v9'
        # Legacy544 checkpoints must not restore policy/optimizer/curriculum
        # under the current552 observation and reward contract.
        legacy, _, previous = make(old)
        self.assertEqual(tuple(legacy.state_dict()), tuple(policy.state_dict()))
        with tempfile.TemporaryDirectory() as folder, patch('torch.cuda.is_available', return_value=False):
            current, historical = Path(folder)/'v22.pt', Path(folder)/'v9.pt'
            trainer.save(current); previous.save(historical)
            restored, resumed_coordinator, resumed = make(env.contract)
            resumed.load(current); resumed_coordinator.restore()
            np.testing.assert_array_equal(coordinator.state.state_vector(), resumed_coordinator.state.state_vector())
            for key, value in policy.state_dict().items():
                torch.testing.assert_close(restored.state_dict()[key], value, rtol=0, atol=0)
            before = {key:value.clone() for key,value in restored.state_dict().items()}
            rng = torch.get_rng_state().clone()
            with self.assertRaisesRegex(ValueError, 'mismatch'):
                resumed.load(historical)
            for key, value in before.items():
                torch.testing.assert_close(restored.state_dict()[key], value, rtol=0, atol=0)
            self.assertTrue(torch.equal(torch.get_rng_state(), rng))


if __name__ == '__main__':
    unittest.main()
