"""CPU checks for the new evaluation's rejection and capture contracts."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

FILE = Path(__file__).with_name('evaluate.py')
spec = importlib.util.spec_from_file_location('v20_A500_evaluate', FILE)
evaluate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluate)


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads((evaluate.ROOT/'docs/2026-10-25/'
            'guitar_learning_finger_recovery_v20/gpu_A/training_contract.json').read_text())

    def test_default_A_contract_accepts_and_other_versions_reject(self):
        evaluate.validate_input_contract(self.contract)
        for key, value in [('schema', 'guitar_learning.gpu_tensor_song_reward.v19')]:
            altered = copy.deepcopy(self.contract)
            altered['reward'][key] = value
            with self.assertRaises(ValueError):
                evaluate.validate_input_contract(altered)
        for rate, shape in ((.04, 0.), (.02, .004)):
            altered = copy.deepcopy(self.contract)
            altered['reward']['finger_recovery'].update(standby_rate_per_s=rate, shape_rate_per_s=shape)
            with self.assertRaises(ValueError):
                evaluate.validate_input_contract(altered)

    def test_observation_gate_and_shape_flags_are_enforced(self):
        for change in ('gate', 'shape', 'posture'):
            altered = copy.deepcopy(self.contract)
            if change == 'gate':
                altered['observation']['fields'][-1] = 'finger_posture.pinky.idle_weight'
            elif change == 'shape':
                altered['reward']['finger_shape']['enabled'] = True
            else:
                altered['reward']['finger_posture']['standby_rate_per_s'] = .04
            with self.assertRaises(ValueError):
                evaluate.validate_input_contract(altered)

    def test_checkpoint_is_final500_only(self):
        self.assertEqual(evaluate.checkpoint_path(Path('/run'), 500), Path('/run/final.pt'))
        for update in (0, 499, 3000):
            with self.assertRaises(ValueError):
                evaluate.checkpoint_path(Path('/run'), update)

    def test_nested_exact_comparison_detects_optimizer_tensor_and_rng_changes(self):
        import numpy as np
        import torch
        left = dict(model={'weight': torch.tensor([1., 2.])}, optimizer={'state': {0: dict(
            exp_avg=torch.tensor([.1]), step=torch.tensor(3.))}}, rng=(1, np.array([1, 2], dtype=np.uint32)))
        self.assertTrue(evaluate.exact_equal(left, copy.deepcopy(left)))
        right = copy.deepcopy(left)
        right['optimizer']['state'][0]['exp_avg'][0] += .0001
        self.assertFalse(evaluate.exact_equal(left, right))
        right = copy.deepcopy(left)
        right['rng'][1][1] = 3
        self.assertFalse(evaluate.exact_equal(left, right))
        self.assertFalse(evaluate.exact_equal([1, 2], (1, 2)))
        self.assertFalse(evaluate.exact_equal(torch.tensor([1.]), torch.tensor([1.], dtype=torch.float64)))

    def test_restoration_checks_both_adams_model_and_each_rng(self):
        import random
        import numpy as np
        import torch
        model = {'weight':torch.tensor([1.])}
        actor = {'state':{0:{'exp_avg':torch.tensor([.1])}}}
        value = {'state':{0:{'exp_avg':torch.tensor([.2])}}}
        trainer = SimpleNamespace(policy=SimpleNamespace(state_dict=lambda:model),
            actor_optimizer=SimpleNamespace(state_dict=lambda:actor),
            value_optimizer=SimpleNamespace(state_dict=lambda:value), updates=500, cost_weight=1.)
        payload = copy.deepcopy(dict(model=model, actor_optimizer=actor, value_optimizer=value,
            updates=500, cost_weight=1., torch_rng=torch.get_rng_state(), numpy_rng=np.random.get_state(),
            python_rng=random.getstate(), cuda_rng=None))
        with patch.object(torch.cuda, 'is_available', return_value=False):
            evaluate.verify_trainer_restoration(trainer,payload)
            for key in ('model','actor_optimizer','value_optimizer','torch_rng','numpy_rng','python_rng','cuda_rng'):
                bad = copy.deepcopy(payload)
                bad[key] = None if key != 'cuda_rng' else [torch.zeros(1,dtype=torch.uint8)]
                with self.assertRaises(ValueError, msg=key):
                    evaluate.verify_trainer_restoration(trainer,bad)

    def test_capture_requires_contiguous_native_first_episode_and_ledger(self):
        import numpy as np
        episode = dict(steps=2, task_time_s=8/240, song=dict(left_success_count=1))
        shapes = dict(body_state=(3,2,13), q=(3,105), qd=(3,105), target=(3,105),
            action=(3,39), clock=(3,), left_count=(3,), near_count=(3,), contact_count=(3,), candidate_count=(3,))
        arrays = {k: np.zeros(shape) for k,shape in shapes.items()}
        arrays['body_state'][...,6] = 1
        arrays['clock'][:] = [0,4,8]
        arrays['left_count'][-1] = 1
        evaluate.validate_capture(arrays, 2, episode)
        for key, value in (('clock', 7), ('left_count', 0)):
            bad = copy.deepcopy(arrays)
            bad[key][-1] = value
            with self.assertRaises(ValueError):
                evaluate.validate_capture(bad, 2, episode)

    def test_video_selection_is_predeclared_and_not_best_score(self):
        rows = [dict(env_id=i, reason='timeline_complete' if i in (2,4) else 'terminal_failure',
            task_time_s=32 if i in (2,4) else 5+i,
            left_curriculum=dict(full_safe=i in (2,4)), song=dict(left_success_count=67 if i==4 else 0))
            for i in range(8)]
        self.assertEqual(evaluate.select_video_env(rows), 2)
        rows[2]['left_curriculum']['full_safe'] = False
        rows[4]['left_curriculum']['full_safe'] = False
        self.assertEqual(evaluate.select_video_env(rows), 2)
        with self.assertRaises(ValueError):
            evaluate.select_video_env(rows[:-1])

    def test_source_manifest_requires_exact_census_current_sha_and_complete_audit(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            phase = root/'phase'
            phase.mkdir()
            package = root/'guitar_learning'
            package.mkdir()
            sources = {}
            for i in range(462):
                path = package/('source%03d.py'%i)
                path.write_text('VALUE = %d\n'%i)
                sources[str(path.relative_to(root))] = evaluate.sha(path)
            (phase/'training_source_manifest.json').write_text(json.dumps(dict(python_count=462,source=sources)))
            audit = dict(verified=True, transitions=16_384_000, raw_crc=dict(complete=True,
                valid_prefix_rows=16000, completed_members=500, error=None, discarded_unverified_bytes=0))
            audit_file = phase/'log_inspection.json'
            audit_file.write_text(json.dumps(audit))
            pins = {str(root/p):h for p,h in sources.items()}
            with patch.object(evaluate, 'ROOT', root), patch.object(evaluate, 'PHASE', phase):
                evaluate.validate_source_pins(pins)
                extra = package/'unlisted.py'
                extra.write_text('')
                with self.assertRaises(ValueError):
                    evaluate.validate_source_pins(pins)
                extra.unlink()
                altered = package/'source000.py'
                altered.write_text('VALUE = 999\n')
                with self.assertRaises(ValueError):
                    evaluate.validate_source_pins(pins)
                altered.write_text('VALUE = 0\n')
                audit['raw_crc']['completed_members'] = 499
                audit_file.write_text(json.dumps(audit))
                with self.assertRaises(ValueError):
                    evaluate.validate_source_pins(pins)


if __name__ == '__main__':
    unittest.main(verbosity=2)
