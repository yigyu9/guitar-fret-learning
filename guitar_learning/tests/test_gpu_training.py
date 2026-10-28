"""GPU dispatch and terminal bootstrap without loading native simulation."""
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch, Mock

import torch

from guitar_learning.tool.training import train_legacy as start
from guitar_learning.training.rollout import FIELDS
from guitar_learning.training.rollout import TensorCollector
from guitar_learning.training.rollout import GpuPool


class FakePolicy:
    def __call__(self, state, *unused):
        return dict(reward_value=state[:, 0].clone(), cost_value=state[:, 0].clone())

    def act(self, state, *unused):
        result = self(state)
        zeros = torch.zeros(len(state), 39)
        result.update(action=zeros, latent=zeros, mean=zeros, log_std=zeros,
                      logp=torch.zeros(len(state)))
        return result


class FakePool:
    num_envs = 2
    valid = True

    def __init__(self):
        self.reset_ids = []
        self.ticks = 0
        self.observation = dict(state=torch.tensor([[1.], [2.]]),
            events=torch.zeros(2, 1, 24), mask=torch.ones(2, 1, dtype=torch.bool),
            priority_events=torch.zeros(2, 2, 24), priority_mask=torch.ones(2, 2, dtype=torch.bool))

    def step(self, action):
        self.ticks += 1
        # Deliberately mutate the old tensor: collector must own pre-step inputs.
        self.observation['state'][:] = torch.tensor([[10.], [20.]])
        done = torch.tensor([self.ticks == 1, False])
        truncated = torch.tensor([False, self.ticks == 1])
        return (self.observation, torch.ones(2), torch.zeros(2), done, truncated, [])

    def reset(self, ids):
        self.reset_ids.append(ids.tolist())
        self.observation['state'][ids] = 0
        return self.observation, []


class GpuTrainingTests(unittest.TestCase):
    def test_gpu_count_and_short_collection_preserve_whole_song(self):
        settings = start.settings_document('left', device='cuda:0', num_envs=1024)
        self.assertEqual(settings['num_envs'], 1024)
        self.assertEqual(settings['horizon'], 32)
        self.assertEqual(settings['song_training']['control_ticks'], 1969)
        self.assertEqual(settings['song_training']['target_count'], 67)
        self.assertEqual(settings['physics_backend']['tensor_pipeline'], 'cuda')
        self.assertEqual(settings['physics_backend']['schema'], 'guitar_learning.gpu_batch.v3')
        self.assertEqual(start.settings_document('right', device='cuda:0', num_envs=32, horizon=1)['horizon'], 1)
        for count in (0, 1025, True):
            with self.subTest(count=count), self.assertRaises(ValueError):
                start.settings_document('left', device='cuda:0', num_envs=count)

    def test_cpu_reference_mode_stays_explicit_and_unchanged(self):
        settings = start.settings_document('left', device='cuda:0', physics='cpu', num_envs=8)
        self.assertNotIn('physics_backend', settings)
        self.assertEqual(settings['horizon'], 1969)
        with self.assertRaises(ValueError):
            start.settings_document('left', device='cpu', physics='gpu')
        with self.assertRaises(ValueError):
            start.settings_document('left', device='cpu', physics='cpu', num_envs=32)

    def test_checkpoint_interval_is_explicit_and_validated(self):
        self.assertEqual(start.settings_document('left', checkpoint_every=50)['checkpoint_every'], 50)
        self.assertEqual(start.settings_document('left')['checkpoint_every'], 250)
        for interval in (0, -1, True, 1.5):
            with self.subTest(interval=interval), self.assertRaises(ValueError):
                start.settings_document('left', checkpoint_every=interval)

    def test_only_gpu_left_uses_separate_advantages_and_longer_gae(self):
        settings=start.settings_document('left',device='cuda:0')
        self.assertEqual(settings['ppo']['advantage_normalization'],'separate')
        self.assertEqual(settings['ppo']['gae_lambda'],.98)
        self.assertEqual(settings['ppo']['gamma'],.99)
        self.assertEqual(settings['song']['surface_approach_gamma'],.99)
        self.assertEqual(settings['ppo']['cost_gamma'],1.)
        self.assertEqual(settings['ppo']['cost_weight'],1.)
        self.assertIsNone(settings['ppo']['episode_cost_budget'])
        self.assertEqual(settings['horizon'],32)
        for hand,physics in (('right','gpu'),('left','cpu'),('right','cpu')):
            with self.subTest(hand=hand,physics=physics):
                legacy=start.settings_document(hand,device='cuda:0',physics=physics)
                self.assertNotIn('advantage_normalization',legacy['ppo'])
                self.assertEqual(legacy['ppo']['gae_lambda'],.95)

    def test_gpu_dispatch_does_not_enter_old_spawn_runner(self):
        from guitar_learning.tool.training import legacy_gpu_runner as gpu_runner
        settings = start.settings_document('left', device='cuda:0', num_envs=2)
        args = SimpleNamespace(out=Path('/tmp/new-gpu-test'), resume=None)
        with patch.dict('sys.modules', {'isaacgym': SimpleNamespace()}), \
                patch.object(gpu_runner, 'run', return_value='gpu') as run:
            self.assertEqual(start.run(settings, args), 'gpu')
            run.assert_called_once_with(settings, args)

    def test_uncertified_support_aborts_before_physics(self):
        pool = GpuPool.__new__(GpuPool)
        pool.closed, pool.valid = False, True
        pool.scene = SimpleNamespace(snapshot=lambda: {}, step=Mock())
        pool.controller = SimpleNamespace(targets=lambda *args: torch.zeros(2, 105),
            efforts=lambda *args: torch.zeros(2, 105), diagnostics={'finite': torch.tensor([True, True]),
                'chest_witness_certified': torch.tensor([True, False]),
                'chest_normal_defined': torch.tensor([True, True])})
        pool.environment = SimpleNamespace(begin_control=lambda action: None)
        with self.assertRaisesRegex(RuntimeError, 'uncertified'):
            pool.step(torch.zeros(2, 39))
        pool.scene.step.assert_not_called()
        self.assertFalse(pool.valid)

    def test_degenerate_normal_holds_only_failed_row_until_terminal_boundary(self):
        pool = GpuPool.__new__(GpuPool)
        pool.closed, pool.valid = False, True
        pool.last_valid_efforts = torch.full((2, 105), 3.)
        outputs = []
        pool.scene = SimpleNamespace(snapshot=lambda: {},
            step=lambda target, efforts: outputs.append(efforts.clone()) or {})
        controller = SimpleNamespace(targets=lambda *args: torch.zeros(2, 105))
        ticks = [0]
        def efforts(sample):
            ticks[0] += 1
            controller.diagnostics = dict(finite=torch.ones(2, dtype=torch.bool),
                chest_witness_certified=torch.ones(2, dtype=torch.bool),
                chest_normal_defined=torch.tensor([ticks[0] != 2, True]))
            return torch.full((2, 105), float(ticks[0]))
        controller.efforts = efforts
        pool.controller = controller
        environment = SimpleNamespace(control_invalid=torch.zeros(2, dtype=torch.bool),
            begin_control=lambda action: None, substep=lambda sample: None,
            end_control=lambda: ('terminal_observation',))
        environment.invalidate_control = lambda mask: environment.control_invalid.logical_or_(mask)
        pool.environment = environment
        self.assertEqual(pool.step(torch.zeros(2, 39)), ('terminal_observation',))
        self.assertEqual([value[:, 0].tolist() for value in outputs],
                         [[1., 1.], [1., 2.], [1., 3.], [1., 4.]])
        self.assertTrue(pool.valid)

    def test_terminal_observation_bootstrap_before_selective_reset(self):
        pool = FakePool()
        collector = TensorCollector(FakePolicy(), pool)
        buffer, _ = collector.collect(1)
        self.assertEqual(pool.reset_ids, [[0, 1]])
        torch.testing.assert_close(buffer['state'][0, :, 0], torch.tensor([1., 2.]))
        torch.testing.assert_close(buffer['next_reward_value'][0], torch.tensor([0., 20.]))
        self.assertEqual(buffer['terminated'].tolist(), [[True, False]])
        self.assertEqual(buffer['truncated'].tolist(), [[False, True]])

    def test_horizon_cut_keeps_live_episode_and_rollout_tensors_owned(self):
        pool = FakePool()
        collector = TensorCollector(FakePolicy(), pool)
        collector.collect(1)
        buffer, _ = collector.collect(2)
        self.assertEqual(pool.reset_ids, [[0, 1]])
        self.assertEqual(pool.ticks, 3)
        self.assertEqual(buffer['state'][:, :, 0].tolist(), [[0., 0.], [10., 20.]])
        for key in FIELDS:
            self.assertEqual(buffer[key].device.type, 'cpu')


if __name__ == '__main__':
    unittest.main()
