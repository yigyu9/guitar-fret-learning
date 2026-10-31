"""동일 후보 생성·strict load 뒤 재시드·첫 reset 캡처를 CPU 모의 환경에서 검사한다."""
import copy
import json
from pathlib import Path
import random
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import numpy as np
import torch
import fixed_reset_evaluate as tool


def fake_runtime(source_rng):
    names = ['joint'+str(i) for i in range(105)]
    candidates = [dict(candidate_valid=True, native_verified=True, q105=[.01*index]*105)
                  for index in range(4)]
    class Pool:
        def __init__(self):
            self.num_envs = 32
            q = torch.tensor([candidates[int(torch.randint(4, (1,)))]['q105'] for _ in range(32)])
            self.scene = SimpleNamespace(names=names, physics_steps=0, initial_hold=q.clone(),
                                         snapshot=lambda: dict(q=q))
            self.reset_count = 0
            self.reset()  # 공식 생성자도 load보다 앞서 reset한다.
        def reset(self):
            self.reset_count += 1
            return ({'q':self.scene.snapshot()['q']}, [])
    class Trainer:
        def load(self, checkpoint):
            torch.manual_seed(source_rng)
            self.loaded_checkpoint = checkpoint
            return dict(strict_identity_validated=True)
    sp = SimpleNamespace(StructuredPool=Pool, StructuredTrainer=Trainer, ACTIVE_NAMES=names[:39],
                         catalog_goal=lambda config: ({}, dict(perturbations=candidates)))
    official = SimpleNamespace(_pins=Mock(return_value={}))
    return sp, official


class FixedResetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def config(self):
        return dict(geometry_sha256='same_geometry', song='same_song')

    def paired_capture(self, source_rng):
        sp, official = fake_runtime(source_rng)
        originals = (sp.StructuredPool.__init__, sp.StructuredPool.reset, sp.StructuredTrainer.load, official._pins)
        with tool.fixed_reset_context(sp, official, 4242, self.config()) as record:
            pool = sp.StructuredPool()
            self.assertIsNone(record['initial_conditions'])
            trainer = sp.StructuredTrainer()
            returned = trainer.load('source_checkpoint')
            self.assertTrue(returned['strict_identity_validated'])
            self.assertEqual(trainer.loaded_checkpoint, 'source_checkpoint')
            pool.reset()
            before = copy.deepcopy(record['initial_conditions'])
            pool.reset()
            self.assertEqual(record['initial_conditions'], before)
            official._pins({}, Path('/tmp'), [])
            self.assertIn(Path(tool.__file__).resolve(), originals[3].call_args.args[2])
        self.assertEqual(originals, (sp.StructuredPool.__init__, sp.StructuredPool.reset, sp.StructuredTrainer.load, official._pins))
        return dict(reset_seed=4242, initial_conditions=record['initial_conditions']), record['events']

    def test_load_order_first_postload_capture_and_actual_pairing(self):
        first, events = self.paired_capture(100)
        second, _ = self.paired_capture(200)
        proof = tool.assert_same_initial_conditions(first, second)
        self.assertEqual(proof['count'], 32)
        self.assertEqual(events, ['seed_before_pool_creation', 'original_strict_load_completed',
                                 'seed_after_strict_load', 'captured_first_postload_reset'])
        second['initial_conditions']['environments'][0]['q105'][0] += .1
        with self.assertRaises(ValueError): tool.assert_same_initial_conditions(first, second)

    def test_seed_repeats_all_cpu_generators_and_propagates_cuda(self):
        tool.seed_all(4242)
        first = (random.random(), float(np.random.rand()), float(torch.rand(())))
        tool.seed_all(4242)
        second = (random.random(), float(np.random.rand()), float(torch.rand(())))
        self.assertEqual(first, second)
        with patch.object(torch.cuda, 'is_available', return_value=True):
            with patch.object(torch.cuda, 'manual_seed_all') as seeded:
                tool.seed_all(4242)
                seeded.assert_any_call(4242)
        for seed in (-1, 2**32, True, 4.2):
            with self.assertRaises(ValueError): tool.validate_seed(seed)

    def test_failed_original_load_does_not_reseed_or_capture_and_restores(self):
        sp, official = fake_runtime(0)
        def failing_load(self, checkpoint):
            raise ValueError('strict identity mismatch')
        sp.StructuredTrainer.load = failing_load
        originals = (sp.StructuredPool.__init__, sp.StructuredPool.reset, sp.StructuredTrainer.load, official._pins)
        with self.assertRaisesRegex(ValueError, 'strict identity'):
            with tool.fixed_reset_context(sp, official, 4242, self.config()) as record:
                sp.StructuredPool()
                sp.StructuredTrainer().load('invalid')
        self.assertFalse(record['strict_load_completed'])
        self.assertIsNone(record['initial_conditions'])
        self.assertEqual(record['events'], ['seed_before_pool_creation'])
        self.assertEqual(originals, (sp.StructuredPool.__init__, sp.StructuredPool.reset, sp.StructuredTrainer.load, official._pins))

    def test_real_source_preservation_with_mocked_gpu_evaluator(self):
        from guitar_learning.tool.experiments.structured_geometry import nested_input_paths
        with nested_input_paths():
            from guitar_learning.training import finger_skill_runner as official
            from guitar_learning.tool.experiments import structured_press as real_sp
            checkpoint = tool.ROOT/'index_B_seed7_v1/100/train/J/initial.pt'
            before = tool.digest(checkpoint)
            fake_sp, _ = fake_runtime(0)
            fake_config = self.config()
            def evaluate(checkpoint, out, **options):
                # 실제 native/collector를 생성하지 않고 wrapper 순서만 실행한다.
                pool = real_sp.StructuredPool()
                real_sp.StructuredTrainer().load(checkpoint)
                pool.reset()
                out.mkdir()
                report = dict(schema='official_mock', completed=True)
                (out/'report.json').write_text(json.dumps(report))
                return report, [dict(env_id=i) for i in range(32)]
            # source의 strict metadata/pin 검증은 실제 수행한다. runtime 객체만 모의로 치환한다.
            from guitar_learning.portability import localize
            payload = torch.load(checkpoint, map_location='cpu', weights_only=False)
            config = localize(payload['metadata']['settings'])['structured_press']
            fake_sp.catalog_goal = lambda config: ({}, dict(perturbations=[
                dict(candidate_valid=True, native_verified=True, q105=[.01*i]*105) for i in range(4)]))
            with tempfile.TemporaryDirectory(prefix='paired_reset_cpu_') as temporary:
                out = Path(temporary)/'eval'
                from contextlib import contextmanager
                @contextmanager
                def no_factory(config):
                    yield []
                with patch.object(real_sp, 'StructuredPool', fake_sp.StructuredPool), \
                     patch.object(real_sp, 'StructuredTrainer', fake_sp.StructuredTrainer), \
                     patch.object(real_sp, 'ACTIVE_NAMES', fake_sp.ACTIVE_NAMES), \
                     patch.object(real_sp, 'catalog_goal', fake_sp.catalog_goal), \
                     patch.object(real_sp, 'structured_runtime', no_factory), \
                     patch.object(official, 'evaluate_checkpoint', side_effect=evaluate):
                    report = tool.run(checkpoint, out)
                self.assertEqual(report['schema'], 'diagnostic_fixed_reset_evaluation.v1')
                self.assertEqual(report['initial_conditions']['count'], 32)
                self.assertTrue(report['original_strict_load_completed'])
                self.assertFalse(report['cross_model_pairing_verified'])
            self.assertEqual(before, tool.digest(checkpoint))


if __name__ == '__main__':
    unittest.main()
