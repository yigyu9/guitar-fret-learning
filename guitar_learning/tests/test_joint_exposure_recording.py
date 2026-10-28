import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

import torch

from guitar_learning.tests.test_finger_decisions import TinyDecisionPolicy, FakeDecisionPool
from guitar_learning.training import finger_skill_runner as runner
from guitar_learning.training.finger_skill_runner import ExposureSchedule
from guitar_learning.training.ppo import DecisionPPOTrainer
from guitar_learning.training.training_log_io import iter_gpu_transitions


class JointExposureRecordingTests(unittest.TestCase):
    def test_real_raw_scope_counts_and_committed_metadata_include_mixed_episodes(self):
        class Pool(FakeDecisionPool):
            def __init__(self, active, out):
                super().__init__()
                self.progress = 0
                self.focus = torch.tensor([[True, False], [True, False]])
                self.sampler_index = 0
                sampler = SimpleNamespace(state_dict=lambda: dict(index=self.sampler_index),
                    load_state_dict=lambda state: setattr(self, 'sampler_index', state['index']))
                self.environment = SimpleNamespace(approach_gamma=.99, focus_mask=self.focus,
                    sampler=sampler, reset_reward_window=lambda: None, reward_window_means=lambda count: {})
                self.scene = SimpleNamespace(diagnostics=dict(closed=False, physx_use_gpu=True,
                    use_gpu_pipeline=True, simulator_count=1, environment_count=2))
            def set_training_progress(self, committed):
                self.progress = committed
            def step(self, action):
                self.clock += 1
                done = torch.tensor([self.clock[0] == 2, self.clock[1] == 3])
                self.observation = self._obs()
                episodes = []
                for identity in done.nonzero().flatten().tolist():
                    full = bool(self.focus[identity].all())
                    count = int(self.focus[identity].sum())
                    episodes.append(dict(env_id=identity, steps=int(self.clock[identity]), valid=True,
                        reason='timeline_complete', reward=1., cost=0.,
                        finger_skill=dict(schema='guitar_learning.finger_skill.v3',
                            scope='full_song' if full else 'phrase', selected_mask=self.focus[identity].tolist()),
                        song=dict(stage_success=False, left_success_count=0, right_success_count=0),
                        left_curriculum=dict(finger_metrics=[dict(target_count=count, success_fraction=0.)])))
                return self.observation, torch.ones(2), torch.zeros(2), done, torch.zeros(2, dtype=torch.bool), episodes
            def reset(self, ids=None):
                ids = torch.arange(2) if ids is None else ids
                if self.progress >= 3:
                    self.focus[ids] = True
                self.sampler_index += len(ids)
                return super().reset(ids)
            def close(self):
                self.scene.diagnostics['closed'] = True
        class Monitor:
            def __init__(self, *args, **kwargs): pass
            def start(self): pass
            def check(self): pass
            def set_phase(self, *args, **kwargs): pass
            def progress(self, context): pass
            def close(self, reason): pass
        active = dict(device='cuda:0', seed=7, num_envs=2, horizon=3, updates=2,
            initial_std=.05, min_available_memory_gib=0., max_wall_seconds=None, checkpoint_every=250,
            finger_skill=dict(schema='guitar_learning.finger_skill.v3', phase='J', scope='scheduled',
                planned_transitions=12, full_song_after=3, hold_ticks=1, exploration='independent'),
            ppo=dict(epochs=1, target_kl=.1, advantage_normalization='joint', cost_weight=1.,
                episode_cost_budget=None, lambda_lr=0.))
        model = TinyDecisionPolicy()
        model.support_log_std = model.log_std[:17]
        model.finger_log_std = model.log_std[17:33]
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)/'run'
            def pins(settings, folder, extra):
                path = folder/'settings.json'
                return {str(path): runner.digest(path)}
            with patch('guitar_learning.training.rollout.GpuPool', Pool), \
                    patch('guitar_learning.training.training_log_io.Monitor', Monitor), \
                    patch('torch.cuda.mem_get_info', return_value=(2*1024**3, 4*1024**3)), \
                    patch('torch.cuda.synchronize'), patch('torch.cuda.is_available', return_value=False), \
                    patch.object(runner, '_policy', return_value=model), \
                    patch.object(runner, '_pins', side_effect=pins), \
                    patch.object(runner, 'project_source_paths', return_value=set()):
                result = runner._train_phase(active, out, ExposureSchedule(12), updates=2)
                resumed = dict(active, updates=1)
                resumed_result = runner._train_phase(resumed, Path(temp)/'resume', ExposureSchedule(12),
                    resume=out/'final.pt', updates=1)
                original_update = DecisionPPOTrainer.update
                calls = []
                def fail_second(trainer, *args):
                    calls.append(True)
                    if len(calls) == 2:
                        raise RuntimeError('injected second PPO failure')
                    return original_update(trainer, *args)
                with patch.object(DecisionPPOTrainer, 'update', fail_second), self.assertRaisesRegex(RuntimeError, 'second PPO'):
                    runner._train_phase(active, Path(temp)/'failed', ExposureSchedule(12), updates=2)
            failed = json.loads((Path(temp)/'failed/report.json').read_text())
            self.assertEqual(failed['exposure_transitions'], dict(phrases=6, full_song=0))
            self.assertEqual(failed['sampled_uncommitted_exposure_transitions'], dict(phrases=4, full_song=2))
            self.assertEqual(failed['discarded_from_learning_exposure_transitions'], dict(phrases=4, full_song=2))
            self.assertEqual(failed['journal']['committed'], 6)
            self.assertEqual(failed['journal']['discarded'], 6)
            self.assertEqual(resumed_result['report']['exposure_transitions'], dict(phrases=10, full_song=8))
            self.assertEqual(resumed_result['report']['curriculum']['committed_transitions'], 18)
            self.assertEqual(resumed_result['report']['curriculum']['config']['full_song_after'], 3)
            expected = dict(phrases=10, full_song=2)
            self.assertEqual(result['report']['exposure_transitions'], expected)
            self.assertEqual(result['report']['journal']['committed'], 12)
            self.assertIsNone(result['report']['sampled_uncommitted_exposure_transitions'])
            checkpoint = torch.load(out/'final.pt', map_location='cpu', weights_only=False)
            self.assertEqual(checkpoint['metadata']['schema'], runner.RESUME_SCHEMA)
            self.assertEqual(checkpoint['metadata']['exposure_transitions'], expected)
            self.assertEqual(checkpoint['metadata']['curriculum']['committed_transitions'], 12)
            metrics = [json.loads(row) for row in (out/'learning_metrics.jsonl').read_text().splitlines()]
            self.assertEqual(metrics[0]['exposure_transitions'], dict(phrases=6, full_song=0))
            self.assertEqual(metrics[1]['exposure_transitions'], dict(phrases=4, full_song=2))
            for raw in iter_gpu_transitions(out):
                for episode in raw['episodes']:
                    selected = episode['finger_skill']['selected_mask']
                    self.assertEqual(episode['left_curriculum']['finger_metrics'][0]['target_count'], sum(selected))
                    self.assertEqual(episode['finger_skill']['scope'], 'full_song' if all(selected) else 'phrase')


if __name__ == '__main__':
    unittest.main()
