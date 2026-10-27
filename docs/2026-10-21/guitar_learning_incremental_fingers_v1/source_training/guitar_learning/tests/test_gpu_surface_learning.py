"""CPU integration of surface observations/rewards; not native pressure/audio."""
import copy
import math
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import torch

from guitar_learning.gpu.geometry import apply, conjugate
from guitar_learning.music_task import EVENT_FIELDS, ScoreTask, ScoreTarget
from guitar_learning.skills.specialist_policy import SpecialistPolicy
from guitar_learning.song.curriculum_runtime import CurriculumCoordinator
from guitar_learning.tests import test_gpu_environment as fixtures
from guitar_learning.training.ppo import PPOTrainer


def task(fingers=(1, 2, 3, 4), onset=0., end=.2, press=0.):
    return ScoreTask(tuple(ScoreTarget('note-%d' % i, 'event-%d' % i,
        i, 5, finger, 1, onset, end, press, onset, end)
        for i, finger in enumerate(fingers)))


class SurfaceLearningTests(unittest.TestCase):
    # Reuse the fixtures without inheriting or collecting their existing tests.
    environment = fixtures.TensorSongTests.environment
    advance = staticmethod(fixtures.TensorSongTests.advance)

    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def place(self, env, snapshot, offset=(0., 0., 0.), loaded=True):
        row = {key: value.clone() for key, value in snapshot.items()}
        target = env.task.targets[0]
        slot = target.finger * 2 + 1
        index = int(env.finger_indices[slot])
        guitar = row['body_state'][:, env.guitar_index]
        goal = env.goals[:, 0] + torch.tensor(offset)
        world = guitar[:, :3] + apply(guitar[:, 3:7], goal)
        body = row['body_state'][:, index]
        body[:, :3] = world - apply(body[:, 3:7], env.surface_local[slot, 0])
        row['contact_force'][:, index, :] = 0
        if loaded:
            row['contact_force'][:, index, 2] = 1.
        return row

    def test_all_four_fingers_get_real_surface_candidates_and_positive_terms(self):
        for finger in range(1, 5):
            with self.subTest(finger=finger):
                env, snapshot, _ = self.environment(task=task((finger,)))
                row = self.place(env, snapshot)
                env.reset([0, 1], row)
                self.assertTrue(env.candidate.all())
                self.assertTrue((env.surface_distance < 1e-6).all())
                # One present finger has total weight1, independently of its ID.
                torch.testing.assert_close(env.finger_weights, torch.ones(1))
                contact, success = [], []
                for _ in range(6):
                    result = self.advance(env, row)
                    self.assertTrue((env.terms['song_clean_hold'] > 0).all())
                    self.assertTrue((result[1] > 0).all())
                    contact.append(float(env.terms['song_left_contact'][0]))
                    success.append(float(env.terms['song_left_success'][0]))
                self.assertAlmostEqual(sum(contact), .5, places=6)
                self.assertAlmostEqual(sum(success), .5, places=6)
                self.assertTrue(env.note['left'].all())

    def test_unloaded_surface_approach_improves_after_press_deadline(self):
        env, snapshot, _ = self.environment(task=task((2,), onset=.5, end=2., press=.4))
        far = self.place(env, snapshot, offset=(0., 0., .15), loaded=False)
        near = self.place(env, snapshot, loaded=False)
        env.reset([0, 1], far)
        env.clock[:] = 240  # A full0.6s after scheduled press, inside the note.
        before = env.surface_distance.clone()
        before_phi = torch.exp(-before[:, 0] / .03)
        self.assertFalse(env.candidate.any())
        self.advance(env, near)
        self.assertTrue((env.surface_distance < before).all())
        self.assertFalse(env.candidate.any())
        self.assertFalse(env.note['contact_done'].any())
        expected = .99 * torch.exp(-env.surface_distance[:, 0] / .03) - before_phi
        torch.testing.assert_close(env.terms['song_left_approach'], expected)
        self.assertTrue((expected > 0).all())

    def test_potential_uses_all_notes_time_window_and_present_finger_balance(self):
        targets = (ScoreTarget('a', 'a', 0, 5, 1, 1, 1., 1.5, .9, 1., 1.5),
                   ScoreTarget('b', 'b', 1, 5, 2, 1, 1.2, 1.7, 1.1, 1.2, 1.7),
                   ScoreTarget('c', 'c', 2, 5, 1, 1, 10., 10.2, 9.9, 10., 10.2))
        env, _, _ = self.environment(task=ScoreTask(targets))
        torch.testing.assert_close(env.finger_weights, torch.tensor([.75, 1.5, .75]))
        env.surface_distance[:] = torch.tensor([.03, .06, .09])
        for seconds, expected in ((0., .75*math.exp(-1)+1.5*math.exp(-2)),
                                  (1.5, 1.5*math.exp(-2)),
                                  (7.8, 0.), (7.95, .75*math.exp(-3)), (10.2, 0.)):
            env.clock[:] = round(seconds*240)
            torch.testing.assert_close(env._surface_potential(), torch.full((2,), expected))
        # Each present finger contributes M/F when all its target potentials=1.
        env.surface_distance.zero_()
        env.clock.zero_()
        self.assertAlmostEqual(float(env._surface_potential()[0]), .75+1.5)

    def test_potential_discount_once_per_control_and_true_terminal_zero(self):
        for ending in ('ongoing', 'physical', 'timeline'):
            with self.subTest(ending=ending):
                env, snapshot, _ = self.environment(task=task((1,), end=2.))
                if ending == 'physical':
                    snapshot['body_state'][0, env.guitar_index, 0] += .1
                if ending == 'timeline':
                    env.clock[:] = round(env.task.duration_s*240)-4
                with patch.object(env, '_surface_potential', side_effect=[torch.full((2,), 2.), torch.full((2,), 3.)]) as phi:
                    result = self.advance(env, snapshot)
                self.assertEqual(phi.call_count, 2)
                expected = torch.tensor([-2., .99*3.-2.]) if ending == 'physical' else torch.full((2,), -2. if ending == 'timeline' else .99*3.-2.)
                torch.testing.assert_close(env.terms['song_left_approach'], expected)
                self.assertEqual(result[3].tolist(), dict(ongoing=[False, False], physical=[True, False], timeline=[True, True])[ending])

    def test_h32_and_selected_reset_preserve_other_row_and_reward_window(self):
        env, snapshot, _ = self.environment(task=task((1,), end=2.))
        env.reset_reward_window()
        rewards = []
        for _ in range(32):
            result = self.advance(env, snapshot)
            self.assertFalse(result[3].any())
            rewards.append(result[1].clone())
        self.assertEqual(env.clock.tolist(), [128, 128])
        self.assertEqual(env.steps.tolist(), [32, 32])
        torch.testing.assert_close(env.note['exposure_time'], torch.full((2, 1), 32/60., dtype=torch.float64))
        before = {key: value[1].clone() for key, value in env.note.items()}
        other_terms = {key: value[1].clone() for key, value in env.episode_reward_terms.items()}
        old_clock = env.clock[1].clone()
        old_surface = env.previous_surface_distance[1].clone()
        means = env.reward_window_means(64)
        self.assertAlmostEqual(sum(means.values()), float(torch.stack(rewards).double().sum()/64), places=6)
        env.reset([0], snapshot)
        self.assertEqual(env.clock[0], 0)
        self.assertTrue(torch.equal(env.clock[1], old_clock))
        self.assertTrue(torch.equal(env.previous_surface_distance[1], old_surface))
        for key, saved in before.items():
            self.assertTrue(torch.equal(env.note[key][1], saved), key)
        for key, saved in other_terms.items():
            self.assertTrue(torch.equal(env.episode_reward_terms[key][1], saved), key)
        self.assertEqual(env.reward_window_means(64), means)

    def test_current_flags_surface_error_and_physical_velocity_in_24_tokens(self):
        env, snapshot, _ = self.environment(task=task((3,), end=2.))
        row = self.place(env, snapshot)
        slot = 3*2+1
        index = int(env.finger_indices[slot])
        row['body_state'][:, index, 7:10] = torch.tensor([.03, -.04, .05])
        row['body_state'][:, index, 10:13] = torch.tensor([.2, 0., .1])
        row['body_state'][:, env.guitar_index, 7:10] = torch.tensor([.02, .01, -.03])
        row['body_state'][:, env.guitar_index, 10:13] = torch.tensor([.1, -.15, .07])
        env.reset([0, 1], row)
        env.note['match50'].zero_()
        env.note['match100'].fill_(True)
        env.delta_velocity.fill_(99.)  # Old origin finite-difference semantics.
        events, mask, _, _ = env._events()
        self.assertEqual(events.shape, (2, 64, 24))
        self.assertTrue(mask[:, 0].all())
        torch.testing.assert_close(events[:, 0, 9:11], torch.tensor([[1., 0.]]).expand(2, -1))
        torch.testing.assert_close(events[:, 0, 16:19], torch.zeros(2, 3), atol=2e-5, rtol=0)
        expected = []
        for i in range(2):
            selected = int(env.surface_sample[i, 0])
            body_slot, sample = divmod(selected, env.surface_count)
            body_index = int(env.finger_indices[body_slot])
            body = row['body_state'][i, body_index]
            lever = apply(body[3:7], env.surface_local[body_slot, sample]-env.com[body_index])
            physical = body[7:10]+torch.cross(body[10:13], lever, dim=-1)
            guitar = row['body_state'][i, env.guitar_index]
            sample_world = body[:3]+apply(body[3:7], env.surface_local[body_slot, sample])
            guitar_com = guitar[:3]+apply(guitar[3:7], env.com[env.guitar_index])
            relative = physical-guitar[7:10]-torch.cross(guitar[10:13], sample_world-guitar_com, dim=-1)
            expected.append(-apply(conjugate(guitar[3:7]), relative))
        torch.testing.assert_close(events[:, 0, 19:22]*.5, torch.stack(expected), atol=1e-6, rtol=1e-5)
        self.assertGreater(float(env.delta.abs().max()), .001)
        self.assertEqual(env.contract['observation']['event_fields'][9:11], ['surface_candidate_now', 'surface_wrong_now'])
        self.assertEqual(env.contract['observation']['surface_geometry']['schema'], 'guitar_learning.left_surface_events.v1')
        # Moving sample selection with zero physical velocities must stay zero.
        moved = self.place(env, snapshot, offset=(0., 0., .02))
        env._snapshot(moved)
        env.delta_velocity.fill_(99.)
        torch.testing.assert_close(env._events()[0][:, 0, 19:22], torch.zeros(2, 3))

    def test_contact_once_normalized_hold_after_achievement_and_episode_ledgers(self):
        env, snapshot, _ = self.environment(task=task())
        candidate = torch.ones(2, 4, dtype=torch.bool)
        wrong = torch.zeros_like(candidate)
        # Controlled qualified measurements isolate integration from geometry;
        # real source-mesh geometry for every finger is exercised separately.
        with patch.object(env, '_contacts', return_value=(candidate, wrong)):
            env.reset([0, 1], snapshot)
            env.surface_distance.fill_(.005)
            env.previous_surface_distance.fill_(.005)
            env.contact_geometry = candidate.clone()
            env.contact_loaded_target = candidate.clone()
            env.surface_body_loaded = candidate.clone()
            env.contact_causes = (wrong.clone(), wrong.clone(), wrong.clone())
            env.reset_reward_window()
            rewards, contact, success, hold = [], [], [], []
            achieved_before = False
            held_after_achievement = False
            for _ in range(30):
                result = self.advance(env, snapshot)
                rewards.append(result[1].clone())
                contact.append(float(env.terms['song_left_contact'][0]))
                success.append(float(env.terms['song_left_success'][0]))
                hold.append(float(env.terms['song_clean_hold'][0]))
                if achieved_before and hold[-1] > 0:
                    held_after_achievement = True
                achieved_before |= bool(env.note['left'].all())
                if result[3].all():
                    break
        self.assertTrue(result[3].all())
        self.assertTrue(held_after_achievement)
        self.assertEqual(sum(value > 0 for value in contact), 1)
        self.assertAlmostEqual(sum(contact), .5*4, places=5)
        self.assertAlmostEqual(sum(success), .5*4, places=5)
        self.assertAlmostEqual(sum(hold), 2.*4, places=5)
        torch.testing.assert_close(env.required, torch.full((4,), .08, dtype=torch.float64))
        means = env.reward_window_means(len(rewards)*2)
        self.assertAlmostEqual(sum(means.values()), float(torch.stack(rewards).double().mean()), places=6)
        for episode in result[-1]:
            self.assertEqual(episode['reason'], 'timeline_complete')
            self.assertTrue(episode['song']['stage_success'])
            ledger = episode['left_note_ledger']
            self.assertEqual(ledger['target_ids'], ['note-%d' % i for i in range(4)])
            self.assertEqual(sum(ledger['values']['left']), episode['song']['left_success_count'])
            for field in ('clean', 'contact_time', 'near_time', 'geometry_time', 'loaded_target_time', 'body_load_time'):
                np.testing.assert_allclose(ledger['values'][field], [.2]*4, atol=1e-12)
            for metrics in episode['left_curriculum']['finger_metrics']:
                self.assertEqual(metrics['target_count'], 1)
                for field in ('near_fraction', 'contact_fraction', 'success_fraction', 'clean_fraction'):
                    self.assertAlmostEqual(metrics[field], 1.)
            self.assertAlmostEqual(sum(episode['reward_components'].values()), episode['reward'], places=5)
            for key, value in episode['reward_components'].items():
                self.assertAlmostEqual(value/len(rewards), means[key], places=6)

    def test_original_wrong_press_penalty_is_not_scaled_by_new_positive_weight(self):
        env, snapshot, _ = self.environment(task=task())
        with patch.object(env, '_contacts', return_value=(torch.zeros(2, 4, dtype=torch.bool), torch.ones(2, 4, dtype=torch.bool))):
            env.reset([0, 1], snapshot)
            self.advance(env, snapshot)
        expected = -(4/60.)*.15  # Legacy position-stage wrong penalty.
        torch.testing.assert_close(env.episode_reward_terms['song_wrong_press'], torch.full((2,), expected))

    def test_real_policy3331_roundtrip_and_old_same_dimension_contract_rejected(self):
        env, snapshot, observation = self.environment()
        def pool_for(environment):
            return SimpleNamespace(environment=environment, set_curriculum=environment.set_curriculum)
        def policy_for(contract):
            return SpecialistPolicy(512, size='small', role='left', contract=contract)
        policy = policy_for(env.contract)
        coordinator = CurriculumCoordinator(policy, pool_for(env))
        self.assertEqual(tuple(policy.left_curriculum_state.shape), (3331,))
        self.assertEqual(policy.left_curriculum_state.dtype, torch.float64)
        evidence = dict(valid=True, reason='timeline_complete', left_curriculum=dict(full_safe=True,
            finger_metrics=[dict(target_count=n, near_fraction=1., contact_fraction=0., success_fraction=0.) for n in env.finger_counts]))
        before_clock = env.clock.clone()
        coordinator.advance([evidence]*256, observation)
        self.assertEqual(env.progress, .1)
        self.assertTrue(torch.equal(env.clock, before_clock))
        trainer = PPOTrainer(policy)
        with tempfile.TemporaryDirectory() as folder, patch('torch.cuda.is_available', return_value=False):
            path = Path(folder)/'surface.pt'
            trainer.save(path)
            restored_env, _, _ = self.environment()
            restored_policy = policy_for(restored_env.contract)
            restored = CurriculumCoordinator(restored_policy, pool_for(restored_env))
            resumed = PPOTrainer(restored_policy)
            resumed.load(path)
            restored.restore()
            np.testing.assert_array_equal(restored.state.state_vector(), coordinator.state.state_vector())
            self.assertEqual(restored_env.progress, .1)
            for key, value in policy.state_dict().items():
                self.assertTrue(torch.equal(value, restored_policy.state_dict()[key]), key)
            old_contract = copy.deepcopy(env.contract)
            old_contract['reward']['schema'] = 'guitar_learning.gpu_tensor_song_reward.v2'
            old_contract['observation']['event_fields'] = list(EVENT_FIELDS)
            old_policy = policy_for(old_contract)
            CurriculumCoordinator(old_policy, pool_for(env))
            self.assertEqual(tuple(old_policy.left_curriculum_state.shape), (27,))
            old_path = Path(folder)/'old512.pt'
            PPOTrainer(old_policy).save(old_path)
            before = {key: value.clone() for key, value in restored_policy.state_dict().items()}
            rng = torch.get_rng_state()
            with self.assertRaisesRegex(ValueError, 'mismatch'):
                resumed.load(old_path)
            for key, value in before.items():
                self.assertTrue(torch.equal(value, restored_policy.state_dict()[key]), key)
            self.assertTrue(torch.equal(torch.get_rng_state(), rng))


if __name__ == '__main__':
    unittest.main()
