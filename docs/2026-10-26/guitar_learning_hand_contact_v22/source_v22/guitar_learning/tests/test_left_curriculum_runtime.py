"""CPU checkpoint and spawned IPC checks for the shared left song schedule."""
import copy
from pathlib import Path
import tempfile
import unittest

import numpy as np
import torch

from guitar_learning.skills.specialist_policy import SpecialistPolicy
from guitar_learning.song.curriculum_runtime import CurriculumCoordinator
from guitar_learning.song.left_curriculum import STATE_SIZE
from guitar_learning.tests.test_parallel import CONTRACT, observation
from guitar_learning.tests.test_policy import policy
from guitar_learning.tests.test_ppo import assert_tree, buffer
from guitar_learning.training.parallel import Collector, Pool
from guitar_learning.training.ppo import PPOConfig, PPOTrainer
from guitar_learning.training.start import settings_document


def completed(*, safe=True, reach=.9, contact=.8, valid=True, reason='timeline_complete'):
    return dict(valid=valid, reason=reason, cost=0., left_curriculum=dict(
        full_safe=safe, reach_fraction=reach, contact_fraction=contact))


class RecordingPool:
    def __init__(self):
        self.broadcasts = []

    def set_curriculum(self, progress):
        self.broadcasts.append(progress)
        return {'progress': progress}


class CurriculumWorker:
    """Expose native-like clock/reset counters directly in its observation."""
    def __init__(self, spec, worker_id):
        self.contract = copy.deepcopy(CONTRACT)
        self.worker_id, self.steps, self.resets, self.progress = worker_id, 0, 0, 0.

    def observation(self):
        result = observation(0.)
        result['state'][:] = [self.progress, self.steps, self.resets, self.worker_id, 0.]
        return result

    def reset(self):
        self.resets += 1
        self.steps = 0
        return self.observation(), {}

    def set_curriculum(self, progress):
        self.progress = progress
        return self.observation()

    def step(self, action):
        self.steps += 1
        done = self.steps == 2
        info = dict(cost=0., termination_reason='timeline_complete' if done else None)
        if done:
            info['episode'] = dict(valid=True, left_curriculum=completed()['left_curriculum'])
        return self.observation(), 0., done, False, info

    def close(self):
        pass


def curriculum_worker(spec, worker_id):
    return CurriculumWorker(spec, worker_id)


class LeftCurriculumRuntimeTests(unittest.TestCase):
    def setUp(self):
        torch.set_num_threads(1)
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)

    def tearDown(self):
        self.folder.cleanup()

    def coordinator(self):
        model, pool = policy(), RecordingPool()
        return CurriculumCoordinator(model, pool), pool

    def test_real_ppo_checkpoint_restores_exact_ring_and_subsequent_progress(self):
        torch.manual_seed(19)
        original, pool = self.coordinator()
        config = PPOConfig(actor_lr=1e-6, target_kl=.1, epochs=1)
        trainer = PPOTrainer(original.policy, config)
        data = buffer(original.policy)
        trainer.update(data)
        original.advance([completed()] * 11, None)
        original.advance([completed(reach=.8, contact=.4)] * 2, None)
        expected = original.state.state_vector().copy()
        self.assertEqual(expected.shape, (STATE_SIZE,))
        self.assertEqual(original.policy.left_curriculum_state.dtype, torch.float64)
        self.assertEqual(original.state.cursor, 5)
        path = self.root / 'left.pt'
        trainer.save(path, {'test': 'actual PPO and curriculum continuation'})

        restored, restored_pool = self.coordinator()
        resumed = PPOTrainer(restored.policy, config)
        resumed.load(path)
        np.testing.assert_array_equal(restored.policy.left_curriculum_state.numpy(), expected)
        observation = restored.restore()
        np.testing.assert_array_equal(restored.state.state_vector(), expected)
        self.assertEqual(observation, {'progress': original.state.progress})
        self.assertEqual(restored_pool.broadcasts, [original.state.progress])
        assert_tree(self, trainer.policy.state_dict(), resumed.policy.state_dict())
        assert_tree(self, trainer.actor_optimizer.state_dict(), resumed.actor_optimizer.state_dict())
        assert_tree(self, trainer.value_optimizer.state_dict(), resumed.value_optimizer.state_dict())

        for episodes in ([completed(safe=False, reason='terminal_failure')],
                         [completed()] * 2, [], [completed()] * 5):
            left, _ = original.advance(episodes, None)
            right, _ = restored.advance(episodes, None)
            self.assertEqual(left, right)
            np.testing.assert_array_equal(original.state.state_vector(), restored.state.state_vector())
            self.assertTrue(torch.equal(original.policy.left_curriculum_state,
                                        restored.policy.left_curriculum_state))
        rng = torch.get_rng_state()
        expected_metrics = trainer.update(data)
        torch.set_rng_state(rng)
        self.assertEqual(resumed.update(data), expected_metrics)
        assert_tree(self, trainer.policy.state_dict(), resumed.policy.state_dict())
        assert_tree(self, trainer.actor_optimizer.state_dict(), resumed.actor_optimizer.state_dict())
        assert_tree(self, trainer.value_optimizer.state_dict(), resumed.value_optimizer.state_dict())

    def test_invalid_truncated_partial_and_failed_only_history_cannot_advance(self):
        coordinator, pool = self.coordinator()
        marker = object()
        ignored = [completed(valid=False), completed(reason='time_limit'),
                   completed(reason='truncated'), dict(valid=False, reason='guard_fault')]
        summary, observation = coordinator.advance(ignored, marker)
        self.assertIs(observation, marker)
        self.assertEqual(summary['completed_episodes_in_update'], 0)
        self.assertEqual(coordinator.state.count, 0)
        for rows in ([], [completed(safe=False, reason='terminal_failure')] * 8, []):
            summary, observation = coordinator.advance(rows, marker)
            self.assertEqual(summary['progress'], 0.)
            self.assertIs(observation, marker)
        self.assertEqual(pool.broadcasts, [])
        self.assertEqual(coordinator.state.summary()['recent_safe_fraction'], 0.)

    def test_new_failures_do_not_advance_prior_good_window(self):
        coordinator, pool = self.coordinator()
        coordinator.advance([completed()] * 4, None)
        before = coordinator.state.progress
        calls = list(pool.broadcasts)
        coordinator.advance([completed(safe=False, reason='terminal_failure')], None)
        self.assertEqual(coordinator.state.progress, before)
        self.assertEqual(pool.broadcasts, calls)
        self.assertEqual(coordinator.state.count, 5)

    def test_malformed_saved_state_rejected_before_worker_broadcast(self):
        coordinator, pool = self.coordinator()
        before = coordinator.state.state_vector().copy()
        malformed = []
        for index, value in ((0, 3.), (1, 1.5), (2, 8.), (3, .5), (4, .8)):
            damaged = torch.zeros(STATE_SIZE, dtype=torch.float64)
            damaged[index] = value
            malformed.append(damaged)
        for damaged in malformed:
            with self.subTest(state=damaged.tolist()):
                coordinator.policy.left_curriculum_state.copy_(damaged)
                with self.assertRaises(ValueError):
                    coordinator.restore()
                np.testing.assert_array_equal(coordinator.state.state_vector(), before)
                self.assertEqual(pool.broadcasts, [])
        coordinator.policy.left_curriculum_state.zero_()
        path = self.root / 'valid.pt'
        trainer = PPOTrainer(coordinator.policy)
        trainer.save(path)
        payload = torch.load(path, weights_only=False)
        payload['model']['left_curriculum_state'][0] = 2.1
        damaged_path = self.root / 'invalid_progress.pt'
        torch.save(payload, damaged_path)
        trainer.load(damaged_path)  # Finite tensors pass the generic PPO reader.
        with self.assertRaises(ValueError):
            coordinator.restore()  # The schedule rejects its semantic state before IPC.
        self.assertEqual(pool.broadcasts, [])
        np.testing.assert_array_equal(coordinator.state.state_vector(), before)

    def test_real_spawn_broadcast_refreshes_observations_without_scene_reset(self):
        specs = [dict(out=str(self.root / str(index))) for index in range(2)]
        with Pool(specs, timeout_s=20, worker_factory=curriculum_worker) as pool:
            observation, _ = pool.reset()
            observation, *_ = pool.step(np.zeros((2, 39)))
            before = observation['state'].copy()
            coordinator = CurriculumCoordinator(policy(), pool)
            summary, observation = coordinator.advance([completed()] * 4, observation)
            self.assertEqual(summary['progress'], .1)
            np.testing.assert_allclose(observation['state'][:, 0], .1)
            np.testing.assert_array_equal(observation['state'][:, 1:], before[:, 1:])
            np.testing.assert_array_equal(observation['state'][:, 1:3], [[1., 1.], [1., 1.]])
            marker = observation
            summary, observation = coordinator.advance([], marker)
            self.assertIs(observation, marker)

    def test_collector_preserves_two_worker_episode_evidence_for_one_global_schedule(self):
        specs = [dict(out=str(self.root / str(index))) for index in range(2)]
        with Pool(specs, timeout_s=20, worker_factory=curriculum_worker) as pool:
            model = policy()
            coordinator = CurriculumCoordinator(model, pool)
            collector = Collector(model, pool)
            for expected_count in (2, 4):
                _, episodes = collector.collect(2)
                self.assertEqual([row['worker_id'] for row in episodes], [0, 1])
                self.assertEqual([row['left_curriculum'] for row in episodes],
                                 [completed()['left_curriculum']] * 2)
                summary, collector.observation = coordinator.advance(episodes, collector.observation)
                self.assertEqual(summary['completed_episodes_in_update'], 2)
                self.assertEqual(coordinator.state.count, expected_count)
            self.assertEqual(summary['progress'], .1)
            np.testing.assert_allclose(collector.observation['state'][:, 0], .1)

    def test_left512_rejects_legacy500_before_mutation_and_right500_stays_compatible(self):
        left, right = settings_document('left', size='small', physics='cpu'), settings_document('right', size='small', physics='cpu')
        self.assertEqual(left['song_training']['observation_dimension'], 512)
        self.assertEqual(right['song_training']['observation_dimension'], 500)
        self.assertNotIn('left_curriculum', right['song'])
        def specialist(dimension, role):
            contract = copy.deepcopy(CONTRACT)
            contract['observation']['dimension'] = dimension
            return SpecialistPolicy(dimension, size='small', role=role, contract=contract)
        old = PPOTrainer(specialist(500, 'left'))
        path = self.root / 'old_left.pt'
        old.save(path)
        current = specialist(512, 'left')
        coordinator = CurriculumCoordinator(current, RecordingPool())
        trainer = PPOTrainer(current)
        before = copy.deepcopy(current.state_dict())
        actor = copy.deepcopy(trainer.actor_optimizer.state_dict())
        value = copy.deepcopy(trainer.value_optimizer.state_dict())
        rng = torch.get_rng_state()
        with self.assertRaisesRegex(ValueError, 'mismatch'):
            trainer.load(path)
        assert_tree(self, current.state_dict(), before)
        assert_tree(self, trainer.actor_optimizer.state_dict(), actor)
        assert_tree(self, trainer.value_optimizer.state_dict(), value)
        self.assertTrue(torch.equal(torch.get_rng_state(), rng))
        np.testing.assert_array_equal(coordinator.state.state_vector(), np.zeros(STATE_SIZE))
        right_trainer = PPOTrainer(specialist(500, 'right'))
        right_path = self.root / 'right.pt'
        right_trainer.save(right_path)
        right_resumed = PPOTrainer(specialist(500, 'right'))
        right_resumed.load(right_path)
        self.assertNotIn('left_curriculum_state', right_resumed.policy.state_dict())
        assert_tree(self, right_trainer.policy.state_dict(), right_resumed.policy.state_dict())


if __name__ == '__main__':
    unittest.main()
