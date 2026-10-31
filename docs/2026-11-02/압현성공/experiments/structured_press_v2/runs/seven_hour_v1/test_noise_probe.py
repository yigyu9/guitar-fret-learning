"""저장 정책을 바꾸지 않는 잡음 배율과 평가 컨텍스트 복구를 CPU에서 검사한다."""
import copy
import json
import tempfile
from pathlib import Path
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
import torch
import noise_probe as probe


class NoiseProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def test_mean_and_inactive_std_unchanged_active_four_scaled(self):
        active = torch.zeros(39, dtype=torch.bool); active[21:25] = True
        result = dict(mean=torch.randn(3, 39), log_std=torch.randn(3, 39)-2,
                      reward_value=torch.randn(3), cost_value=torch.randn(3))
        before = {key:value.clone() for key,value in result.items()}
        for scale in probe.SCALES:
            out = probe.scaled_result(result, active, scale)
            self.assertIs(out['mean'], result['mean'])
            self.assertTrue(torch.equal(out['log_std'][:, ~active], result['log_std'][:, ~active]))
            if scale > 0:
                self.assertTrue(torch.allclose(out['log_std'][:, active].exp(), result['log_std'][:, active].exp()*scale))
            for name, value in before.items():
                self.assertTrue(torch.equal(result[name], value))

    def test_scale_zero_selects_deterministic_and_positive_selects_sampling(self):
        model = Mock(); model.phase = 'J'
        probe.SamplingPolicy(model, 0).act('input')
        model.act.assert_called_once_with('input', deterministic=True)
        for scale in (.25, .5, 1.):
            model.reset_mock()
            probe.SamplingPolicy(model, scale).act('input')
            model.act.assert_called_once_with('input', deterministic=False)
        for scale in (-1, .1, 2, float('inf'), float('nan'), True, None):
            with self.assertRaises(ValueError): probe.validate_scale(scale)

    def test_parameter_bytes_and_architecture_unchanged_factory_restored(self):
        class FakePolicy(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.weight = torch.nn.Parameter(torch.randn(39))
                self.active_mask = torch.zeros(39, dtype=torch.bool); self.active_mask[17:21] = True
                self.architecture = {'schema':'unchanged'}
            def forward(self):
                return dict(mean=self.weight[None], log_std=self.weight[None]*0-2)
        sp = SimpleNamespace(StructuredPolicy=FakePolicy)
        official = SimpleNamespace(_DeterministicPolicy=object, _pins=Mock(return_value={'pinned':True}))
        original = (FakePolicy.forward, official._DeterministicPolicy, official._pins)
        model = FakePolicy(); before = model.weight.detach().numpy().tobytes()
        identity = copy.deepcopy(model.architecture)
        with self.assertRaises(RuntimeError):
            with probe.sampling_override(sp, official, .5):
                result = model()
                self.assertTrue(torch.equal(result['mean'], model.weight[None]))
                official._pins({}, probe.ROOT, [])
                self.assertIn(probe.ROOT/'noise_probe.py', original[2].call_args[0][2])
                raise RuntimeError('test cleanup')
        self.assertEqual(original, (FakePolicy.forward, official._DeterministicPolicy, official._pins))
        self.assertEqual(before, model.weight.detach().numpy().tobytes())
        self.assertEqual(identity, model.architecture)

    def test_report_override_with_mocked_evaluator_never_runs_gpu(self):
        from guitar_learning.tool.experiments.structured_geometry import nested_input_paths
        with nested_input_paths():
            from guitar_learning.training import finger_skill_runner as official
            from guitar_learning.training.training_log_io import iter_episode_rows
            evaluation = probe.ROOT/'middle_A_seed7_v1/100/evaluate_final'
            saved = json.loads((evaluation/'report.json').read_text())
            rows = [row['episode'] for row in iter_episode_rows(evaluation)]
            def fake_evaluate(checkpoint, out, **options):
                self.assertEqual(options['num_envs'], 32)
                out.mkdir()
                (out/'report.json').write_text(json.dumps(saved))
                return copy.deepcopy(saved), rows
            with tempfile.TemporaryDirectory(prefix='noise_probe_report_') as temporary:
                out = Path(temporary)/'evaluation'
                with patch.object(official, 'evaluate_checkpoint', side_effect=fake_evaluate):
                    result = probe.run(probe.ROOT/'middle_A_seed7_v1/100/train/J/final.pt', .5, out)
                self.assertEqual(result['schema'], 'diagnostic_sampling_override.v1')
                self.assertEqual(result['original_report_schema'], saved['schema'])
                self.assertFalse(result['original_saved_distribution'])
                self.assertTrue(result['policy_mean_unchanged'])
                self.assertTrue(result['first_episode_per_env'])
                self.assertEqual(result['failure_episode_count'], 0)
                self.assertIn('RNG', result['sampling_rng'])

    def test_actual_A_checkpoint_strict_cpu_preflight(self):
        from guitar_learning.tool.experiments.structured_geometry import nested_input_paths
        with nested_input_paths():
            from guitar_learning.tool.experiments import structured_press as sp
            from guitar_learning.training import finger_skill_runner as official
            checkpoint = probe.ROOT/'middle_A_seed7_v1/100/train/J/final.pt'
            before = probe.digest(checkpoint)
            payload = torch.load(checkpoint, map_location='cpu', weights_only=False)
            settings, config = probe.validate_payload(payload, sp, official)
            self.assertEqual(config['stage'], 'A')
            self.assertEqual(config['active_axes'], [21, 22, 23, 24])
            self.assertEqual(before, probe.digest(checkpoint))
            self.assertEqual(len(probe.verify_source_seal()), 64)


if __name__ == '__main__':
    unittest.main()
