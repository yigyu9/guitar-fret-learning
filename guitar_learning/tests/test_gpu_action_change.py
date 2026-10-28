"""CPU action-accounting checks; static source snapshots are not native physics."""
import copy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import torch

from guitar_learning.core.control import ACTIVE_NAMES, LEFT_HAND_NAMES
from guitar_learning.training.policy import SpecialistPolicy
from guitar_learning.song.curriculum_runtime import CurriculumCoordinator
from guitar_learning.tests import test_gpu_continuous_clean as clean_fixtures
from guitar_learning.tests import test_gpu_environment as fixtures
from guitar_learning.training.ppo import PPOTrainer


class ActionChangeTests(unittest.TestCase):
    environment = fixtures.TensorSongTests.environment
    advance = staticmethod(fixtures.TensorSongTests.advance)
    tree_equal = clean_fixtures.ContinuousCleanTests.tree_equal

    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def test_deadband_is_inclusive_symmetric_and_continuous_above_boundary(self):
        for magnitude in (.049, .05, .0501, .15):
            with self.subTest(magnitude=magnitude):
                env, snapshot, _ = self.environment()
                action = torch.zeros(2, 39)
                action[:, ACTIVE_NAMES.index('L_Elbow_x')] = torch.tensor([magnitude, -magnitude])
                self.advance(env, snapshot, action)
                expected = -.01*max(magnitude-.05, 0.)**2/39/60
                torch.testing.assert_close(env.terms['action_change'], torch.full((2,), expected),
                                           atol=1e-13, rtol=1e-5)
                if magnitude <= .05:
                    self.assertEqual(env.terms['action_change'].tolist(), [0., 0.])

    def test_wrist_three_axes_each_cost_one_quarter_of_arm_and_keep_39_denominator(self):
        for axis in 'xyz':
            with self.subTest(axis=axis):
                env, snapshot, _ = self.environment()
                action = torch.zeros(2, 39)
                action[0, ACTIVE_NAMES.index('L_Elbow_'+axis)] = .25
                action[1, ACTIVE_NAMES.index('L_Wrist_'+axis)] = .25
                self.advance(env, snapshot, action)
                arm = -.01*.2**2/39/60
                torch.testing.assert_close(env.terms['action_change'], torch.tensor([arm, arm/4]),
                                           atol=1e-13, rtol=1e-6)

    def test_all_21_finger_axes_including_thumb_are_free_on_first_and_reversed_commands(self):
        env, snapshot, _ = self.environment()
        action = torch.zeros(2, 39)
        columns = [ACTIVE_NAMES.index(name) for name in LEFT_HAND_NAMES]
        action[0, columns] = 1.
        action[1, columns] = -1.
        self.assertEqual(len(columns), 21)
        self.assertEqual(sum(name.startswith('LH:thumb') for name in LEFT_HAND_NAMES), 5)
        for command in (action, -action):
            self.advance(env, snapshot, command)
            self.assertEqual(env.terms['action_change'].tolist(), [0., 0.])
            torch.testing.assert_close(env.previous_action, command, atol=0, rtol=0)

    def test_command_change_is_charged_once_while_unchanged_actual_snapshot_is_not_modified(self):
        env, snapshot, _ = self.environment()
        saved = {key:value.clone() for key,value in snapshot.items()}
        action = torch.zeros(2, 39)
        action[:, ACTIVE_NAMES.index('L_Shoulder_y')] = .3
        original = action.clone()
        self.advance(env, snapshot, action)
        expected = -.01*.25**2/39/60
        torch.testing.assert_close(env.terms['action_change'], torch.full((2,), expected),
                                   atol=1e-13, rtol=1e-6)
        self.advance(env, snapshot, action)
        self.assertEqual(env.terms['action_change'].tolist(), [0., 0.])
        torch.testing.assert_close(action, original, atol=0, rtol=0)
        for key,value in snapshot.items():
            torch.testing.assert_close(value, saved[key], atol=0, rtol=0)
        # Later mutation by the caller must not rewrite stored previous commands.
        action.zero_()
        torch.testing.assert_close(env.previous_action, original, atol=0, rtol=0)

    def test_h32_boundary_keeps_previous_commands_and_reset_only_clears_selected_row(self):
        env, snapshot, _ = self.environment()
        action = torch.zeros(2, 39)
        action[:, ACTIVE_NAMES.index('L_Thorax_z')] = .2
        for _ in range(32):
            self.advance(env, snapshot, action)
        env.reset_reward_window()
        torch.testing.assert_close(env.previous_action, action, atol=0, rtol=0)
        self.advance(env, snapshot, action)
        self.assertEqual(env.terms['action_change'].tolist(), [0., 0.])
        env.reset([0], snapshot)
        torch.testing.assert_close(env.previous_action[0], torch.zeros(39), atol=0, rtol=0)
        torch.testing.assert_close(env.previous_action[1], action[1], atol=0, rtol=0)
        self.advance(env, snapshot, action)
        expected = -.01*.15**2/39/60
        torch.testing.assert_close(env.terms['action_change'], torch.tensor([expected, 0.]),
                                   atol=1e-13, rtol=1e-6)
        self.assertEqual(env.clock.tolist(), [4, 136])

    def test_one_second_of_changes_integrates_at_60hz_without_stage_scaling(self):
        for stage in (0., 2.):
            with self.subTest(stage=stage):
                env, snapshot, _ = self.environment()
                env.set_curriculum(stage)
                total = torch.zeros(2)
                for tick in range(60):
                    action = torch.zeros(2, 39)
                    action[:, ACTIVE_NAMES.index('L_Elbow_x')] = .1 if tick % 2 == 0 else -.1
                    self.advance(env, snapshot, action)
                    total += env.terms['action_change']
                # First command changes0->.1; subsequent commands change by.2.
                expected = -.01*(.05**2+59*.15**2)/39/60
                torch.testing.assert_close(total, torch.full((2,), expected), atol=1e-11, rtol=1e-6)
                torch.testing.assert_close(env.episode_reward_terms['action_change'], total, atol=0, rtol=0)
                self.assertEqual(env.clock.tolist(), [240, 240])

    def test_right_hand_retains_original_square_cost_without_deadband(self):
        env, snapshot, _ = self.environment(hand='right')
        action = torch.zeros(2, 39)
        action[0, ACTIVE_NAMES.index('R_Wrist_x')] = .05
        action[1, ACTIVE_NAMES.index('R_Elbow_z')] = .2
        self.advance(env, snapshot, action)
        expected = -.01*torch.tensor([.05**2, .2**2])/39/60
        torch.testing.assert_close(env.terms['action_change'], expected, atol=1e-13, rtol=1e-6)
        self.advance(env, snapshot, -action)
        torch.testing.assert_close(env.terms['action_change'], expected*4, atol=1e-13, rtol=1e-6)
        self.assertEqual(env.contract['reward']['schema'], 'guitar_learning.gpu_tensor_song_reward.v1')

    def test_contract_describes_every_joint_coefficient_in_action_order(self):
        env, _, _ = self.environment()
        contract = env.contract['reward']['action_change']
        self.assertEqual(env.contract['reward']['schema'], 'guitar_learning.gpu_tensor_song_reward.v22')
        self.assertEqual(contract['schema'], 'guitar_learning.gpu_action_change.v2')
        self.assertEqual(contract['coefficient_per_s'], .01)
        self.assertEqual(contract['wrist_coefficient_per_s'], .0025)
        self.assertEqual(contract['deadband'], .05)
        self.assertEqual(contract['normalization_dimensions'], 39)
        self.assertEqual(contract['excluded_joint_names'], list(LEFT_HAND_NAMES))
        self.assertEqual(contract['wrist_joint_names'], ['L_Wrist_'+axis for axis in 'xyz'])
        expected = [0. if name in LEFT_HAND_NAMES else
                    .0025 if name.startswith('L_Wrist_') else .01 for name in ACTIVE_NAMES]
        self.assertEqual(contract['joint_coefficients_per_s'], expected)

    def test_v22_full_checkpoint_roundtrip_and_legacy544_v15_resume_rejection(self):
        env, _, _ = self.environment()
        pool = SimpleNamespace(environment=env, set_curriculum=env.set_curriculum)
        def make(contract):
            policy = SpecialistPolicy(contract['observation']['dimension'], size='small', role='left', contract=contract)
            coordinator = CurriculumCoordinator(policy, pool)
            return policy, coordinator, PPOTrainer(policy)
        policy, coordinator, trainer = make(env.contract)
        self.assertEqual(tuple(policy.left_curriculum_state.shape), (3331,))
        for optimizer in (trainer.actor_optimizer, trainer.value_optimizer):
            for group in optimizer.param_groups:
                for parameter in group['params']:
                    parameter.grad = torch.ones_like(parameter)
            optimizer.step(); optimizer.zero_grad()
        trainer.updates, trainer.cost_weight = 9, 1.5
        previous = copy.deepcopy(env.contract)
        previous['observation']['dimension'] = 544
        previous['observation']['fields'] = previous['observation']['fields'][:544]
        previous['observation']['scales'] = previous['observation']['scales'][:544]
        previous['observation'].pop('thumb_support')
        previous['observation']['fields'] = [field.replace('.standby_gate', '.idle_weight')
                                         for field in previous['observation']['fields']]
        previous['reward']['schema'] = 'guitar_learning.gpu_tensor_song_reward.v15'
        previous['reward']['action_change'] = dict(coefficient_per_s=.01, normalization_dimensions=39,
            excluded_joint_names=list(LEFT_HAND_NAMES),
            scope='LH21 including thumb excluded; original per-axis coefficient for all remaining actions')
        old_policy, _, old_trainer = make(previous)
        self.assertEqual(tuple(policy.state_dict()), tuple(old_policy.state_dict()))
        with tempfile.TemporaryDirectory() as folder, patch('torch.cuda.is_available', return_value=False):
            current, old = Path(folder)/'v22.pt', Path(folder)/'v15.pt'
            trainer.save(current); old_trainer.save(old)
            restored, restored_coordinator, resumed = make(env.contract)
            resumed.load(current); restored_coordinator.restore()
            self.tree_equal(policy.state_dict(), restored.state_dict())
            self.tree_equal(trainer.actor_optimizer.state_dict(), resumed.actor_optimizer.state_dict())
            self.tree_equal(trainer.value_optimizer.state_dict(), resumed.value_optimizer.state_dict())
            self.assertEqual((resumed.updates, resumed.cost_weight), (9, 1.5))
            self.assertEqual(coordinator.state.state_vector().tolist(),
                             restored_coordinator.state.state_vector().tolist())
            before = copy.deepcopy((restored.state_dict(), resumed.actor_optimizer.state_dict(),
                resumed.value_optimizer.state_dict(), resumed.updates, resumed.cost_weight))
            with self.assertRaisesRegex(ValueError, 'mismatch'):
                resumed.load(old)
            self.tree_equal(before, (restored.state_dict(), resumed.actor_optimizer.state_dict(),
                resumed.value_optimizer.state_dict(), resumed.updates, resumed.cost_weight))


if __name__ == '__main__':
    unittest.main()
