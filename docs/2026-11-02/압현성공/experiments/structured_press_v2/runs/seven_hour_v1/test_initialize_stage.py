"""0업데이트 이전의 설정·가중치·생성 계보·공식 API 호출을 GPU 없이 검사한다."""
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import torch
import initialize_stage as tool


class InitializeStageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)
        from guitar_learning.tool.experiments.structured_geometry import nested_input_paths
        cls.paths = nested_input_paths(); cls.paths.__enter__()
        from guitar_learning.portability import localize
        from guitar_learning.tool.experiments import structured_press
        from guitar_learning.training import finger_skill_runner
        cls.sp, cls.official = structured_press, finger_skill_runner
        cls.source = tool.ROOT/'middle_A_seed7_v1/100/train/J/final.pt'
        cls.payload = torch.load(cls.source, map_location='cpu', weights_only=False)
        cls.saved = localize(cls.payload['metadata']['settings'])
        cls.architecture = localize(cls.payload['identity']['architecture'])

    @classmethod
    def tearDownClass(cls):
        cls.paths.__exit__(None, None, None)

    def settings(self, stage='B', distribution='saved'):
        return tool.make_settings(self.saved, self.source, stage, distribution, self.sp)

    def policy(self, settings):
        contract = copy.deepcopy(self.architecture['contract'])
        contract['structured_press'] = settings['structured_press']
        return self.sp.StructuredPolicy(self.architecture['state_dim'], size='large',
            contract=contract, structured=settings['structured_press'])

    def test_settings_free_distribution_and_override_restrictions(self):
        stage = self.settings()
        self.assertEqual(stage['num_envs'], 64)
        self.assertEqual(stage['updates'], 100)  # 설정 예산은 양수, 실제 API updates=0은 별도다.
        self.assertEqual(stage['seed'], self.saved['seed'])
        self.assertEqual(stage['structured_press']['initial_distribution']['v9_fraction'], 0.)
        for distribution, fraction in (('saved', 1.), ('aligned', 0.), ('v9', 1.)):
            settings = self.settings('free_v9', distribution)
            self.assertEqual(settings['structured_press']['initial_distribution']['v9_fraction'], fraction)
            self.assertEqual(settings['structured_press']['active_axes'], list(range(33)))
            self.assertIn('no_support_J33', settings['simple_start']['initial_pose'])
        with self.assertRaises(ValueError): self.settings('B', 'aligned')
        with self.assertRaises(ValueError): self.settings('C50', 'v9')

    def test_original_transfer_exact_weights_except_active_mask_and_fresh_optimizer(self):
        from guitar_learning.training.ppo import PPOConfig
        settings = self.settings(); policy = self.policy(settings)
        before = tool.digest(self.source)
        policy.initialize_from(self.source, expected_sha256=before)
        for name, expected in self.payload['model'].items():
            if name != 'active_mask':
                self.assertTrue(torch.equal(expected, policy.state_dict()[name]), name)
        trainer = self.sp.StructuredTrainer(policy, PPOConfig(**settings['ppo']))
        self.assertEqual(trainer.updates, 0)
        with tempfile.TemporaryDirectory(prefix='stage_export_weights_') as temporary:
            path = Path(temporary)/'final.pt'
            trainer.save(path, metadata=dict(no_training=True, curriculum=dict(committed_transitions=0)))
            verified = tool.verify_export(self.payload, path, settings['structured_press'], torch)
            self.assertTrue(verified['exact_source_model_except_active_mask'])
        self.assertEqual(before, tool.digest(self.source))
        with self.assertRaisesRegex(ValueError, 'adjacent'):
            self.policy(self.settings('C50')).initialize_from(self.source, expected_sha256=before)

    def test_creation_external_inputs_are_lineage_not_required_runtime(self):
        from guitar_learning.portability import portable, validate_checkpoint_inputs
        settings = self.settings(); spec = settings['finger_skill']
        schedule = self.official.ExposureSchedule(spec['planned_transitions'], spec['full_song_after'])
        pool = SimpleNamespace(environment=SimpleNamespace(sampler=SimpleNamespace(state_dict=lambda: {})))
        original = (self.official._pins, self.official.checkpoint_metadata)
        with tempfile.TemporaryDirectory(prefix='stage_export_lineage_') as temporary:
            out = Path(temporary)
            (out/'settings.json').write_text(json.dumps(portable(settings)))
            with tool.creation_provenance(self.official, self.source, {'no_training': True}):
                pins = self.official._pins(settings, out)
                metadata = self.official.checkpoint_metadata(settings, schedule, pool,
                    input_pins=pins, settings_path=out/'settings.json')
            validate_checkpoint_inputs(metadata)
            lineage = metadata['input_contract']['lineage']
            identifiers = {row['original_identifier'] for row in lineage}
            self.assertIn(str(self.source.resolve()), identifiers)
            self.assertIn(str(Path(tool.__file__).resolve()), identifiers)
            self.assertFalse(any('initialize_stage.py' in name for name in metadata['input_contract']['required']))
            self.assertTrue(metadata['no_training'])
            self.assertTrue(metadata['not_formal_stage_pass'])
            self.assertEqual(metadata['optimizer_updates'], 0)
        self.assertEqual(original, (self.official._pins, self.official.checkpoint_metadata))

    def test_zero_api_override_and_partial_outer_report_with_mocked_phase(self):
        class StopBeforeGPU(RuntimeError): pass
        original = (self.official._pins, self.official.checkpoint_metadata)
        with tempfile.TemporaryDirectory(prefix='stage_export_no_gpu_') as temporary:
            out = Path(temporary)/'export'
            with patch.object(self.official, '_train_phase', side_effect=StopBeforeGPU('no GPU in CPU test')) as phase:
                with self.assertRaises(StopBeforeGPU):
                    tool.run(self.source, 'free_v9', 'aligned', out)
            self.assertEqual(phase.call_args.kwargs, dict(updates=0))
            report = json.loads((out/'report.json').read_text())
            self.assertFalse(report['completed'])
            self.assertTrue(report['no_training'])
            self.assertTrue(report['not_formal_stage_pass'])
            self.assertEqual(report['optimizer_updates'], 0)
            self.assertEqual(report['committed_transitions'], 0)
        self.assertEqual(original, (self.official._pins, self.official.checkpoint_metadata))


if __name__ == '__main__':
    unittest.main()
