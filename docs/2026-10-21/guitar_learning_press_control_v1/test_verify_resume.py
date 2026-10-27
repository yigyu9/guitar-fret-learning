"""Controlled CPU fixtures for verifier boundaries; not synthetic GPU evidence."""
import copy
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

import numpy as np
import torch
from torch import nn

PHASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('verify_resume', PHASE/'verify_resume.py')
v = importlib.util.module_from_spec(spec);spec.loader.exec_module(v)


def payload():
    moments = dict(step=torch.tensor(100.), exp_avg=torch.zeros(39), exp_avg_sq=torch.zeros(39))
    return dict(identity={'fixture_control': 'new'}, updates=100, cost_weight=1., metadata='selected',
        model={'actor_encoders.left.weight':torch.tensor([1.]), 'actor_heads.left.weight':torch.tensor([2.]),
               'actor_encoders.right.weight':torch.tensor([3.]), 'actor_heads.right.weight':torch.tensor([4.]),
               'value_encoder.weight':torch.tensor([5.]), 'log_std':torch.zeros(39),
               'partner_initialized':torch.zeros(2,dtype=torch.bool)},
        actor_optimizer=dict(state={0:copy.deepcopy(moments)},param_groups=[dict(params=[0])]),
        value_optimizer=dict(state={0:dict(step=torch.tensor(100.))},param_groups=[dict(params=[0])]),
        torch_rng=torch.tensor([1,2],dtype=torch.uint8),numpy_rng=('fixture',np.array([3,4],dtype=np.uint32)),
        python_rng=('fixture',5),cuda_rng=[torch.tensor([6,7],dtype=torch.uint8)])


def chain():
    selected=payload();initial=copy.deepcopy(selected);initial['metadata']='actual resumed initial'
    final=copy.deepcopy(initial);final['updates']=101
    final['model']['actor_heads.left.weight'] += .1
    final['model']['value_encoder.weight'] += .1
    final['actor_optimizer']['state'][0]['step'] += 1
    final['actor_optimizer']['state'][0]['exp_avg'][:33] += .1
    final['value_optimizer']['state'][0]['step'] += 1
    return selected,initial,final


class TinyPolicy(nn.Module):
    def __init__(self, contract):
        super().__init__()
        self.actor=nn.Linear(2,2);self.value=nn.Linear(2,1)
        self.architecture=dict(schema='CPU-test-only',contract=contract)
    def actor_parameters(self):return self.actor.parameters()
    def value_parameters(self):return self.value.parameters()


class ResumeVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):torch.set_num_threads(1)

    def test_exact_full_boundary_includes_cuda_rng_and_ignores_metadata_only(self):
        selected,initial,final=chain()
        result=v.check_resume_payloads(selected,initial,final)
        self.assertTrue(result['exact_nonmetadata_100_to_initial'])
        self.assertEqual(result['left_changed_tensors'],1)
        initial['cuda_rng'][0][0] += 1
        with self.assertRaisesRegex(ValueError,'outside metadata'):
            v.check_resume_payloads(selected,initial,final)

    def test_bit_exact_scalar_tensor_array_signed_zero_and_structure(self):
        self.assertFalse(v.same_tree(0.,-0.))
        self.assertFalse(v.same_tree(torch.tensor([0.]),torch.tensor([-0.])))
        self.assertFalse(v.same_tree(np.array([0.]),np.array([-0.])))
        self.assertFalse(v.same_tree([1],(1,)))
        self.assertFalse(v.same_tree(torch.tensor(1.),torch.tensor(1.,dtype=torch.float64)))
        self.assertTrue(v.same_tree(torch.tensor(1.),torch.tensor(1.)))

    def test_every_training_input_pin_is_checked_against_actual_file(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'source.py';source.write_text('fixed source')
            pins={str(source):hashlib.sha256(source.read_bytes()).hexdigest()}
            self.assertEqual(v.verify_input_pins(pins),1)
            source.write_text('changed source')
            with self.assertRaisesRegex(ValueError,'changed or missing'):v.verify_input_pins(pins)
            source.unlink()
            with self.assertRaisesRegex(ValueError,'changed or missing'):v.verify_input_pins(pins)
            with self.assertRaisesRegex(ValueError,'Nonempty'):v.verify_input_pins({})

    def test_missing_actual_updates_nonfinite_and_inactive_right_changes_fail(self):
        for case in ('no_left','no_value','no_optimizer','nan','right','right_std','right_moment'):
            a,b,c=chain()
            if case=='no_left':c['model']['actor_heads.left.weight']=b['model']['actor_heads.left.weight'].clone()
            elif case=='no_value':c['model']['value_encoder.weight']=b['model']['value_encoder.weight'].clone()
            elif case=='no_optimizer':c['actor_optimizer']=copy.deepcopy(b['actor_optimizer'])
            elif case=='nan':c['model']['actor_heads.left.weight'][0]=float('nan')
            elif case=='right':c['model']['actor_heads.right.weight'][0] += .1
            elif case=='right_std':c['model']['log_std'][33] += .1
            elif case=='right_moment':c['actor_optimizer']['state'][0]['exp_avg'][33] += .1
            with self.subTest(case=case),self.assertRaises(ValueError):v.check_resume_payloads(a,b,c)

    def test_old_control_rejected_before_cuda_checks_with_populated_adam_and_rng_unchanged(self):
        from guitar_learning.training.ppo import PPOTrainer
        with tempfile.TemporaryDirectory() as folder:
            old=PPOTrainer(TinyPolicy({'action_codec':'old'}));path=Path(folder)/'old.pt'
            old.save(path)
            trainer=PPOTrainer(TinyPolicy({'action_codec':'new','diagnostics':'new'}))
            for optimizer,parameters in ((trainer.actor_optimizer,trainer.policy.actor_parameters()),
                                         (trainer.value_optimizer,trainer.policy.value_parameters())):
                for parameter in parameters:parameter.grad=torch.ones_like(parameter)
                optimizer.step()
            trainer.updates=100
            result=v.reject_old_without_mutation(trainer,path)
            self.assertTrue(result['rejected']);self.assertTrue(result['host_state_and_rng_unchanged'])
            # Compatible identity must never be reported as old-control rejection.
            old.policy.architecture=trainer.policy.architecture
            wrong=Path(folder)/'wrong-reason.pt';old.save(wrong)
            with self.assertRaisesRegex(ValueError,'unexpectedly accepted'):
                v.reject_old_without_mutation(trainer,wrong)


if __name__=='__main__':unittest.main()
