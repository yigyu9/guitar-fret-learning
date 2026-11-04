"""CPU checks for admission, actual-arrival reads and right6 execution contracts."""
import math
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import torch

from guitar_learning.tests.test_gpu_environment import fixture
from guitar_learning.tool.experiments.right_strike import runtime
from guitar_learning.tool.experiments.right_strike.native_probe import actual_contract, close_capture, trajectory


class RuntimeTests(unittest.TestCase):
    def test_original_right_policy_and_strict_ppo_checkpoint_roundtrip(self):
        import copy
        from guitar_learning.tests.test_right_strike_environment import RightStrikeEnvironmentTests
        from guitar_learning.training.policy import SpecialistPolicy
        from guitar_learning.training.ppo import PPOTrainer
        env, _ = RightStrikeEnvironmentTests().make()
        observation = env.observation()
        policy = SpecialistPolicy(observation['state'].shape[-1], size='small', contract=env.contract, role='right')
        decision = policy.act(**observation, deterministic=True)
        self.assertEqual(tuple(decision['action'].shape), (2, 39))
        self.assertTrue(torch.equal(decision['action'][:, :33], torch.zeros(2, 33)))
        trainer = PPOTrainer(policy)
        with tempfile.TemporaryDirectory() as directory, patch('torch.cuda.is_available', return_value=False):
            path = Path(directory)/'checkpoint.pt'; trainer.save(path, metadata=dict(scope='CPU fixture'))
            trainer.load(path)
            changed = copy.deepcopy(env.contract)
            changed['diagnostics']['right_strike_quality']['target']['direction'] = -1
            other = SpecialistPolicy(observation['state'].shape[-1], size='small', contract=changed, role='right')
            with self.assertRaisesRegex(ValueError, 'mismatch'):
                PPOTrainer(other).load(path)

    def test_raw_save_failure_still_closes_native_scene(self):
        from unittest.mock import Mock
        pool = Mock()
        sample = dict(q=np.array([1.]))
        capture = SimpleNamespace(samples=[sample])
        fake_numpy = Mock(stack=np.stack, savez_compressed=Mock(side_effect=OSError('disk full')))
        codes, errors = close_capture(pool, capture, [sample], [sample], {}, None, fake_numpy, Path('/tmp'))
        pool.close.assert_called_once()
        self.assertEqual(len(errors), 3)
        self.assertTrue(all('disk full' in error for error in errors))

    def test_ppo_rejects_unprepared_or_failed_diagnostic(self):
        from guitar_learning.tool.experiments.right_strike.runner import validate_diagnostic
        manifest = dict(pins={'source': 'sha'})
        report = dict(completed=True, protocol_completed=True, mode='diagnostic', failure=None,
                      no_mid_episode_state_injection=True, pins=manifest['pins'],
                      episode=dict(right_strike_quality=dict(success=True, full_safe=True,
                          prepared_before_hit=True, native_expected_hit_count=1, accepted_count=1)))
        validate_diagnostic(report, manifest)
        report['episode']['right_strike_quality']['prepared_before_hit'] = False
        with self.assertRaises(ValueError):
            validate_diagnostic(report, manifest)
    def test_busy_gpu_cannot_be_admitted_even_with_free_memory(self):
        device = dict(uuid=runtime.GPU_UUID, name='fixture', **{'memory.free [MiB]': '9000 MiB'})
        job = dict(pid='123', gpu_uuid=runtime.GPU_UUID, process_name='another experiment')
        with patch.object(runtime, 'gpu_rows', side_effect=[[device], [job]]):
            ready, reason, _ = runtime.readiness()
        self.assertFalse(ready)
        self.assertEqual(reason, 'waiting_for_gpu_idle')
        with patch.object(runtime, 'gpu_rows', side_effect=[[device], []]):
            self.assertTrue(runtime.readiness()[0])

    def test_arrival_uses_actual_snapshot_and_does_not_write_it(self):
        metadata, snapshot = fixture(1)
        snapshot['physics_step'] = torch.tensor([120])
        snapshot['q'][0, 0] += .01
        before = {k: v.clone() for k, v in snapshot.items()}
        pool = SimpleNamespace(scene=SimpleNamespace(body_names=metadata['body_names'], snapshot=lambda: snapshot))
        result = actual_contract(pool)
        self.assertEqual(result['state']['physics_step'], 120)
        self.assertEqual(result['state']['human_dof_states'][0]['pos'], float(snapshot['q'][0, 0]))
        self.assertTrue(all(torch.equal(value, snapshot[key]) for key, value in before.items()))

    def test_path_prepares_crosses_once_then_remains_lifted(self):
        initial = np.zeros(6); pre = np.ones(6); post = 2*np.ones(6); lift = 3*np.ones(6)
        for time, expected in ((0, initial), (.5, initial), (2.6, pre), (2.9, pre),
                               (3.1, post), (3.3, post), (3.8, lift), (5., lift)):
            np.testing.assert_allclose(trajectory(time, initial, [pre, post, lift]), expected)
        path = np.array([trajectory(t, initial, [pre, post, lift]) for t in np.linspace(0, 5, 1001)])
        self.assertTrue((np.diff(path[:, 0]) >= -1e-12).all())
        for invalid in (math.nan, math.inf, -.1, 5.1):
            with self.assertRaises(ValueError):
                trajectory(invalid, initial, [pre, post, lift])

    def test_source_pin_corruption_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=runtime.ROOT/'data/diagnostic_inputs') as directory:
            path = Path(directory)/'source.py'; path.write_text('x=1\n')
            pins = {str(path): runtime.sha(path)}
            runtime.verify_pins(pins)
            path.write_text('x=2\n')
            with self.assertRaises(ValueError):
                runtime.verify_pins(pins)

    def test_queue_wait_does_not_create_a_native_process(self):
        from guitar_learning.tool.experiments.right_strike.queue import queue_probe
        with tempfile.TemporaryDirectory(dir=runtime.ROOT/'runs') as folder:
            folder = Path(folder)
            with patch('guitar_learning.tool.experiments.right_strike.queue.verify_manifest'), \
                 patch('guitar_learning.tool.experiments.right_strike.queue.sha', return_value='fixture'), \
                 patch('guitar_learning.tool.experiments.right_strike.queue.readiness',
                       return_value=(False, 'waiting_for_gpu_idle', {})), \
                 patch('guitar_learning.tool.experiments.right_strike.queue.time.sleep', side_effect=KeyboardInterrupt), \
                 patch('guitar_learning.tool.experiments.right_strike.queue.subprocess.Popen') as spawn:
                with self.assertRaises(KeyboardInterrupt):
                    queue_probe(runtime.ROOT/'data/diagnostic_inputs/fake.json', folder/'probe', folder/'queue')
                spawn.assert_not_called()


if __name__ == '__main__':
    unittest.main()
