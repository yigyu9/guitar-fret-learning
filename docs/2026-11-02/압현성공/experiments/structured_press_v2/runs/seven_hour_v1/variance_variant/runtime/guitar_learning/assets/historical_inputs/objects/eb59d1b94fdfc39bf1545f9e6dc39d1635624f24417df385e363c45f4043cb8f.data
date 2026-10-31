"""Frozen BC mean bounds and entry-point identity; no new native run."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

import numpy as np
import torch
import torch._dynamo

from guitar_learning.imitation import dataset_manifest
from guitar_learning.parallel import FIELDS
from guitar_learning.ppo import PPOTrainer
from guitar_learning.transition import anchored_policy as anchored,anchored_run as runner
from guitar_learning.transition import learning,policy,transfer,train,probe,train_with_teacher_proof
from guitar_learning.transition.policy import SpecialistPolicy as OriginalPolicy

PHASE=Path(__file__).resolve().parents[2]/'docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_long_v1'


class AnchoredPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)
        cls.settings=runner.settings_document(json.loads((PHASE/'single_a_anchored_eval_settings_v1.json').read_text()))
        # Real archive validation includes the original successful native
        # teacher capture and its full source proof. Later tensor tests reuse
        # this validated immutable payload rather than replacing it with zeros.
        cls.evidence=learning.validate_initialization(cls.settings['initialization']['checkpoint'])
        cls.payload=cls.evidence['payload'];cls.contract=cls.payload['architecture']['contract']
        cls.original=OriginalPolicy(500,contract=cls.contract)
        cls.original.load_state_dict(cls.payload['model']);cls.original.eval()
        with np.load(PHASE/'single_a_bc_eval_v1/case_000/demonstration.npz') as archive:
            cls.inputs=[torch.as_tensor(archive[key][:8]) for key in FIELDS]

    def model(self,initialize=True):
        model=anchored.AnchoredPolicy(500,contract=self.contract,behavior_prior=self.settings['behavior_prior'])
        if initialize:
            with patch.object(learning,'validate_initialization',return_value=self.evidence):
                anchored.initialize_actor(model,self.settings)
        return model

    def test_initial_mean_actions_and_std_exactly_match_actual_BC(self):
        model=self.model()
        with torch.no_grad():before=self.original.act(*self.inputs,deterministic=True);after=model.act(*self.inputs,deterministic=True)
        for field in ('mean','log_std','action','logp'):
            torch.testing.assert_close(before[field],after[field],rtol=0,atol=0)
        self.assertTrue(bool(model.prior_initialized))
        self.assertIn('Gaussian',model.architecture['exploration'])

    def test_uninitialized_prior_is_fail_closed_and_critic_remains_fresh(self):
        model=self.model(False)
        with self.assertRaisesRegex(ValueError,'validated BC prior'):model(*self.inputs)
        before={key:value.clone() for key,value in model.state_dict().items()}
        with patch.object(learning,'validate_initialization',return_value=self.evidence):anchored.initialize_actor(model,self.settings)
        for key,value in model.state_dict().items():
            if key.startswith(('value_encoder.','reward_critic.','cost_critic.','actor_encoders.right.','actor_heads.right.')):
                torch.testing.assert_close(value,before[key],rtol=0,atol=0)

    def test_global_pointwise_bound_rhs_zero_and_original_std_clamp(self):
        model=self.model();limit=self.settings['behavior_prior']['latent_limit']
        with torch.no_grad():
            prior=self.original(*self.inputs)
            model.actor_heads['left'].bias.add_(1000.)
            model.log_std.fill_(-100.)
            output=model.act(*self.inputs,deterministic=True)
        self.assertLessEqual(float((output['mean'][:,:33]-prior['mean'][:,:33]).abs().max()),limit+1e-6)
        self.assertLessEqual(float((output['action'][:,:33]-prior['mean'][:,:33].tanh()).abs().max()),limit+1e-6)
        self.assertTrue(torch.equal(output['action'][:,33:],torch.zeros(8,6)))
        torch.testing.assert_close(output['log_std'][:,:33],torch.full((8,33),-5.),rtol=0,atol=0)
        # This deliberately does not assert Gaussian draws obey the mean bound.

    def test_initial_gradient_slope_one_and_prior_absent_from_optimizers(self):
        prior=torch.tensor([[1.,-2.,.3]],dtype=torch.float64)
        raw=prior.clone().requires_grad_(True)
        anchored.bounded_mean(raw,prior,.0002).sum().backward()
        torch.testing.assert_close(raw.grad,torch.ones_like(raw),rtol=0,atol=0)
        model=self.model();trainer=PPOTrainer(model)
        frozen=list(model.frozen_actor_encoders.parameters())+list(model.frozen_actor_heads.parameters())
        optimizer_ids={id(parameter) for optimizer in (trainer.actor_optimizer,trainer.value_optimizer)
            for group in optimizer.param_groups for parameter in group['params']}
        self.assertTrue(all(not parameter.requires_grad and id(parameter) not in optimizer_ids for parameter in frozen))
        model(*self.inputs)['mean'].sum().backward()
        self.assertTrue(all(parameter.grad is None for parameter in frozen))
        self.assertFalse(trainer.actor_optimizer.state);self.assertFalse(trainer.value_optimizer.state)

    def test_old_loader_and_old_PPO_cannot_silently_accept_new_identity(self):
        model=self.model()
        with self.assertRaises(ValueError):learning.apply_initialization(model,self.settings['initialization']['checkpoint'])
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'new.pt';PPOTrainer(model).save(path)
            restored=self.model(False);PPOTrainer(restored).load(path)
            self.assertTrue(bool(restored.prior_initialized))
            with torch.no_grad():
                torch.testing.assert_close(model(*self.inputs)['mean'],restored(*self.inputs)['mean'],rtol=0,atol=0)
            with self.assertRaises(ValueError):PPOTrainer(OriginalPolicy(500,contract=self.contract)).load(path)
            changed=copy.deepcopy(self.settings['behavior_prior']);changed['checkpoint_sha256']='0'*64
            other=anchored.AnchoredPolicy(500,contract=self.contract,behavior_prior=changed)
            with self.assertRaises(ValueError):PPOTrainer(other).load(path)
            with self.assertRaises(ValueError):anchored.initialize_actor(other,self.settings)

    def test_settings_require_exact_BC_scope_limit_and_sha(self):
        for key,value in (('latent_limit',.001),('checkpoint_sha256','0'*64),('formula','unnormalized')):
            settings=copy.deepcopy(self.settings);settings['behavior_prior'][key]=value
            with self.assertRaises(ValueError):runner.settings_document(settings)
        settings=copy.deepcopy(self.settings);settings['transition']['mode']='pair'
        with self.assertRaises(ValueError):runner.settings_document(settings)

    def test_new_gate_metadata_and_source_pins_are_required(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);settings=copy.deepcopy(self.settings);gates=[];pins=dict(self.evidence['source_pins'])
            sources=dataset_manifest(runner.source_paths())
            for index in range(4):
                case=root/str(index);case.mkdir();gates.append(str(case))
                (case/'settings.json').write_text(json.dumps(settings))
                (case/'inputs_before.json').write_text(json.dumps(sources))
                pins.update(dataset_manifest([case/'settings.json',case/'inputs_before.json']))
            settings['initialization']['gate_evaluations']=gates
            original=lambda value,require_gate:dict(source_pins=dict(pins))
            result=runner.initialization_evidence(original,settings,require_gate=True)
            self.assertTrue(set(sources).issubset(result['source_pins']))
            case=Path(gates[0]);old=json.loads((case/'settings.json').read_text());old.pop('behavior_prior')
            (case/'settings.json').write_text(json.dumps(old));pins.update(dataset_manifest([case/'settings.json']))
            with self.assertRaisesRegex(ValueError,'four new native gates'):
                runner.initialization_evidence(original,settings,require_gate=True)
            (case/'settings.json').write_text(json.dumps(self.settings));pins.update(dataset_manifest([case/'settings.json']))
            (case/'inputs_before.json').write_text('{}');pins.update(dataset_manifest([case/'inputs_before.json']))
            with self.assertRaisesRegex(ValueError,'actual anchored policy'):
                runner.initialization_evidence(original,settings,require_gate=True)

    def test_scoped_eval_and_teacher_proof_composition_preserve_original_loader(self):
        original_policy=policy.SpecialistPolicy;original_initializer=transfer.initialize_actor
        original_validator=train.initialization_evidence
        reached=[]
        def boundary(settings,args):
            model=policy.SpecialistPolicy(500,contract=self.contract)
            self.assertIsInstance(model,anchored.AnchoredPolicy)
            self.assertIs(learning.SpecialistPolicy,OriginalPolicy)
            transfer.initialize_actor(model,settings)
            proof=train.initialization_evidence(settings,require_gate=False)
            self.assertTrue(set(map(str,runner.source_paths())).issubset(proof['source_pins']))
            reached.append(args.mode)
            return {'completed':True}
        with patch.dict('sys.modules',{'isaacgym':types.ModuleType('isaacgym')}), \
                patch.object(learning,'validate_initialization',return_value=self.evidence), \
                patch.object(probe,'run',side_effect=boundary),patch.object(train_with_teacher_proof,'run',side_effect=boundary):
            for mode in ('eval','train'):
                args=types.SimpleNamespace(mode=mode,resume=None,checkpoint=None)
                self.assertTrue(runner.run(self.settings,args)['completed'])
        self.assertEqual(reached,['eval','train'])
        self.assertIs(policy.SpecialistPolicy,original_policy)
        self.assertIs(transfer.initialize_actor,original_initializer)
        self.assertIs(train.initialization_evidence,original_validator)

    def test_CLI_imports_Isaac_before_numpy_or_torch(self):
        script='''
import builtins,runpy,sys
original=builtins.__import__
def checked(name,*args,**kwargs):
    if name=='isaacgym':
        assert 'torch'not in sys.modules and 'numpy'not in sys.modules
        raise RuntimeError('ISAAC_FIRST')
    return original(name,*args,**kwargs)
builtins.__import__=checked
sys.argv=['anchored','eval','--settings','/tmp/unused.json','--out','/tmp/unused-out']
try:runpy.run_module('guitar_learning.transition.anchored_run',run_name='__main__')
except RuntimeError as error:assert str(error)=='ISAAC_FIRST'
else:raise AssertionError('Isaac never imported')
'''
        result=subprocess.run([sys.executable,'-c',script],cwd=PHASE.parents[4],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stderr)


if __name__=='__main__':unittest.main()
