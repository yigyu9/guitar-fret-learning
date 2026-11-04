"""전용 설정·factory 복원·portable strict checkpoint를 CPU에서 검사한다."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import torch

from guitar_learning.portability import ROOT, portable
from guitar_learning.training.compact_strike import CompactStrikePolicy
from guitar_learning.training.ppo import PPOConfig
from guitar_learning.training.training_log_io import write, digest
from guitar_learning.tool.experiments import compact_strike as entry
from guitar_learning.tests.test_compact_strike_policy import contract


class CompactStrikeEntryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def settings(self):
        return entry.build_settings(updates=1, num_envs=2, size='small')

    def test_strum_task_settings_and_fixed_pressure_ppo_without_left_schema(self):
        settings = self.settings()
        entry.validate_settings(settings)
        self.assertNotIn('finger_skill', settings)
        self.assertEqual(settings['specialist']['role'], 'right')
        self.assertEqual(settings['song_training']['song_id'], '00_SS1-68-E_comp')
        self.assertEqual(settings['song_training']['target_count'], 104)
        self.assertEqual(settings['compact_strike']['priority_slots'], 2)
        self.assertEqual(settings['compact_strike']['fusion_input'], 384)
        self.assertEqual(settings['ppo']['gae_lambda'], .98)
        self.assertEqual(settings['ppo']['lambda_lr'], 0.)
        args = entry.parser().parse_args(['train', '--out', 'unused'])
        self.assertIsNone(args.song)
        self.assertIsNone(args.num_envs)
        self.assertIn('폭은 고정', entry.parser().format_help())
        with self.assertRaisesRegex(ValueError, 'unsupported right strike gesture'):
            entry.build_settings(song='05_BN2-131-B_solo', updates=1, num_envs=2)

    def test_runtime_restores_four_factories_even_on_failure(self):
        from guitar_learning.training import rollout, policy, ppo
        from guitar_learning.gpu.compact_strike import CompactStrikeEnvironment
        def current():
            return rollout.GpuPool, rollout.TensorCollector, policy.SpecialistPolicy, ppo.PPOTrainer
        original = current()
        with self.assertRaisesRegex(RuntimeError, 'fixture failure'):
            with entry.runtime() as factories:
                self.assertIs(factories.pool.environment_class_override, CompactStrikeEnvironment)
                self.assertIs(rollout.TensorCollector, entry.CompactStrikeCollector)
                self.assertIs(policy.SpecialistPolicy, CompactStrikePolicy)
                self.assertTrue(issubclass(ppo.PPOTrainer, entry.CompactStrikeTrainer))
                self.assertNotEqual(current(), original)
                raise RuntimeError('fixture failure')
        self.assertEqual(current(), original)

    def test_resume_omitted_settings_preserved_and_conflicting_options_rejected(self):
        saved = self.settings()
        args = entry.parser().parse_args(['train', '--out', 'unused', '--resume', 'model.pt', '--updates', '3'])
        with patch.object(entry, 'read_checkpoint', return_value=copy.deepcopy(saved)), \
                patch('guitar_learning.tool.training.legacy_gpu_runner.run', return_value='fixture') as run:
            self.assertEqual(entry.train(args), 'fixture')
        self.assertEqual(run.call_args.args[0]['updates'], 3)
        self.assertEqual(run.call_args.args[0]['num_envs'], 2)
        for option in ('--size large', '--num-envs 8', '--song another_song'):
            args = entry.parser().parse_args(['train', '--out', 'unused', '--resume', 'model.pt']+option.split())
            with patch.object(entry, 'read_checkpoint', return_value=copy.deepcopy(saved)), self.assertRaises(ValueError):
                entry.train(args)

    def test_pool_factory_binds_right27_and_collects_four_cpu_snapshot_substeps(self):
        from guitar_learning.training.rollout import GpuPool
        from guitar_learning.tests.test_gpu_control import fake_scene
        from guitar_learning.tests.test_gpu_environment import fixture
        from guitar_learning.gpu import compact_strike as environment_module
        scene, sample = fake_scene(hand='right', dtype=torch.float32)
        metadata, safe = fixture()
        sample.update(contact_force=safe['contact_force'], target=safe['target'],
                      physics_step=torch.zeros(2, dtype=torch.long))
        scene.metadata = dict(metadata, guitar_representation={}, environment_aggregate={}, reset_body_source='CPU fixture')
        scene.efforts = torch.zeros(2, 105)
        scene.physics_steps = 0
        def snapshot():
            return {key: value.clone() for key, value in sample.items()}
        def reset(ids):
            sample['physics_step'][ids] = 0
            return snapshot()
        def step(target, efforts):
            sample['target'].copy_(target)
            sample['physics_step'] += 1
            scene.physics_steps += 1
            return snapshot()
        scene.snapshot, scene.reset, scene.step, scene.close = snapshot, reset, step, lambda: None
        class CpuEnvironment(environment_module.CompactStrikeEnvironment):
            def __init__(self, metadata, **options):
                options['device'] = 'cpu'
                super().__init__(metadata, **options)
        with patch.object(GpuPool, '_create_scene', return_value=scene), \
                patch.object(environment_module, 'CompactStrikeEnvironment', CpuEnvironment), entry.runtime() as factories:
            pool = factories.pool(self.settings(), None)
            try:
                model = CompactStrikePolicy(entry.configuration()['state_dim'], size='small', contract=pool.contract)
                collector = entry.CompactStrikeCollector(model, pool)
                buffer, _ = collector.collect(2)
                self.assertEqual(scene.physics_steps, 8)
                self.assertEqual(buffer['latent'].shape, (2, 2, 39))
                self.assertEqual(pool.contract['native_backend']['control']['schema'],
                                 'guitar_learning.right27_control.v1')
                self.assertIsNotNone(pool.environment.action_bounds)
                self.assertTrue(bool(torch.isfinite(buffer['reward']).all()))
                self.assertTrue(bool((buffer['latent'][..., 33:] != 0).any()))
            finally:
                pool.close()

    def test_strict_save_roundtrip_rejects_changed_inputs_architecture_and_old_metadata(self):
        settings = self.settings()
        spec = settings['compact_strike']
        native_contract = contract(spec['state_dim'], spec['event_dim'])
        config = PPOConfig(**settings['ppo'])
        with tempfile.TemporaryDirectory(dir=ROOT/'runs') as folder:
            out = Path(folder)
            source = out/'source.txt'; source.write_text('original')
            write(out/'settings.json', portable(settings))
            context = dict(settings=settings, out=out, lineage=[], pool=None,
                pins={str(source): digest(source), str(out/'settings.json'): digest(out/'settings.json')})
            model = CompactStrikePolicy(spec['state_dim'], size='small', contract=native_contract)
            trainer = entry.CompactStrikeTrainer(model, config, context=context)
            path = out/'strike.pt'; trainer.save(path, dict(test=True))
            self.assertEqual(entry.read_checkpoint(path), settings)
            before_rng = torch.get_rng_state().clone()
            entry.read_checkpoint(path)
            self.assertTrue(torch.equal(before_rng, torch.get_rng_state()))
            restored = entry.CompactStrikeTrainer(
                CompactStrikePolicy(spec['state_dim'], size='small', contract=native_contract), config)
            self.assertEqual(restored.load(path)['schema'], entry.RESUME_SCHEMA)
            for key, value in model.state_dict().items():
                torch.testing.assert_close(value, restored.policy.state_dict()[key], rtol=0, atol=0)
            original = torch.load(path, weights_only=False)
            bad = copy.deepcopy(original); bad['identity']['architecture']['fusion'] = [256, 256]
            wrong = out/'wrong.pt'; torch.save(bad, wrong)
            with self.assertRaisesRegex(ValueError, 'architecture'):
                entry.read_checkpoint(wrong)
            bad = copy.deepcopy(original); bad['metadata']['schema'] = 'guitar_learning.compact_press_resume.v3'
            old = out/'old.pt'; torch.save(bad, old)
            with self.assertRaisesRegex(ValueError, 'Compact strike checkpoint'):
                entry.read_checkpoint(old)
            source.write_text('changed')
            with self.assertRaisesRegex(ValueError, 'input sources changed'):
                restored.load(path)


if __name__ == '__main__':
    unittest.main()
