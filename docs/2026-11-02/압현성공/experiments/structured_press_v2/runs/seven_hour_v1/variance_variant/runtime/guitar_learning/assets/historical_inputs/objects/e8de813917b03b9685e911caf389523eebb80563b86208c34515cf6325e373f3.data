"""New500-state demonstrations and selected-role BC retain native identity."""
import copy
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

import numpy as np
import torch
import torch._dynamo

from guitar_learning.training.parallel import FIELDS
from guitar_learning.tool.experiments.transition import learning
from guitar_learning.tool.experiments.transition.policy import SpecialistPolicy
from guitar_learning.tests.test_transition_transfer import contract,SOURCE


def dataset(mode='single_a'):
    arrays={key:np.zeros((4,)+shape,dtype=np.bool_ if 'mask' in key else np.float32)
        for key,shape in learning.SHAPES.items()}
    arrays['state'][:,-32:]=np.arange(32,dtype=np.float32)
    arrays['action'][:,:33]=.1
    return dict(arrays,role='left',contract=contract(mode=mode),dataset_contracts=[contract(mode=mode)],
        captures=['/capture/a'],source_pins={})


class TransitionLearningTests(unittest.TestCase):
    def setUp(self):torch.set_num_threads(1)

    def test_inactive_actions_likelihood_entropy_and_gradient(self):
        model=SpecialistPolicy(contract=contract());data=dataset()
        inputs=[torch.as_tensor(data[key]) for key in FIELDS]
        prediction=model.act(*inputs)
        self.assertTrue(torch.equal(prediction['action'][:,33:],torch.zeros(4,6)))
        modified=prediction['latent'].clone();modified[:,33:]=123
        alternative=model.evaluate(*inputs,modified)
        torch.testing.assert_close(prediction['logp'],alternative['logp'],rtol=0,atol=0)
        (-alternative['logp'].mean()).backward()
        self.assertTrue(all(p.grad is None for p in model.actor_encoders['right'].parameters()))
        self.assertTrue(all(p.grad is None for p in model.actor_heads['right'].parameters()))
        self.assertTrue(torch.equal(model.log_std.grad[33:],torch.zeros(6)))
        self.assertEqual(model.architecture['state_dim'],500)
        with self.assertRaises(ValueError):SpecialistPolicy(563,contract=contract())

    def test_BC_fits_selected_actor_and_does_not_change_critic_partner_std(self):
        model=SpecialistPolicy(contract=contract());data=dataset()
        before={key:value.clone() for key,value in model.state_dict().items()}
        fit=learning.fit_actor(model,data,steps=5,batch_size=4,tolerance=0.)
        self.assertLess(fit['training_mse'],fit['initial_training_mse'])
        for key,value in model.state_dict().items():
            if not key.startswith(('actor_encoders.left.','actor_heads.left.')):
                torch.testing.assert_close(value,before[key],rtol=0,atol=0)
        self.assertFalse(fit['converged'])

    def test_real_capture_auditor_required_and_failed_capture_not_accepted(self):
        fake=types.ModuleType('guitar_learning.tool.experiments.transition.capture')
        fake.audit_capture=lambda path:(_ for _ in ()).throw(ValueError('failed native capture'))
        with patch.dict('sys.modules',{'guitar_learning.tool.experiments.transition.capture':fake}),self.assertRaisesRegex(ValueError,'failed native'):
            learning.load_dataset(['/capture/a'])

    def test_two_task_datasets_preserve32_history_and_only_task_difference(self):
        a,b=dataset(),dataset('single_b')
        audited=[dict(contract=d['contract'],arrays={key:d[key] for key in learning.SHAPES},source_pins={},report={}) for d in (a,b)]
        fake=types.ModuleType('guitar_learning.tool.experiments.transition.capture')
        fake.audit_capture=lambda path:audited[0 if str(path).endswith('a') else 1]
        with patch.dict('sys.modules',{'guitar_learning.tool.experiments.transition.capture':fake}):
            data=learning.load_dataset(['/capture/a','/capture/b'],contract(mode='pair'))
            self.assertEqual(data['state'].shape,(8,500))
            np.testing.assert_array_equal(data['state'][4,-32:],np.arange(32))
            audited[1]['contract']['action']['smoothing_alpha']=.4
            with self.assertRaisesRegex(ValueError,'exact physical'):learning.load_dataset(['/capture/a','/capture/b'])

    def test_invalid_arrays_cannot_fit(self):
        model=SpecialistPolicy(contract=contract())
        for mutation in ('wrong_state','inactive_action','nan','mask'):
            data=dataset()
            if mutation=='wrong_state':data['state']=np.zeros((4,563),np.float32)
            if mutation=='inactive_action':data['action'][0,34]=.1
            if mutation=='nan':data['state'][0,0]=np.nan
            if mutation=='mask':data['mask']=data['mask'].astype(np.float32)
            with self.assertRaises(ValueError):learning.fit_actor(model,data,steps=1)

    def test_save_apply_contract_bound_archive_and_fresh_other_tensors(self):
        model=SpecialistPolicy(contract=contract());data=dataset()
        data['source_pins']={str(SOURCE/'final.pt'):'source-sha'};data['source_checkpoint']=str(SOURCE/'final.pt')
        fit=learning.fit_actor(model,data,steps=2)
        fake=types.ModuleType('guitar_learning.tool.experiments.transition.capture')
        fake.audit_capture=lambda path:dict(contract=data['contract'],arrays={key:data[key] for key in learning.SHAPES},
            source_pins={},report={})
        original_manifest=learning.dataset_manifest
        def manifest(paths):
            if isinstance(paths,dict) and str(SOURCE/'final.pt') in paths:return dict(paths)
            return original_manifest(paths)
        with tempfile.TemporaryDirectory() as folder,patch.dict('sys.modules',{'guitar_learning.tool.experiments.transition.capture':fake}), \
                patch.object(learning,'dataset_manifest',manifest), \
                patch.object(learning,'validate_source',return_value=dict(source_pins=data['source_pins'])):
            path=Path(folder)/'bc.pt';learning.save_initialization(model,path,data=data,fit_result=fit)
            fresh=SpecialistPolicy(contract=contract());before={key:value.clone() for key,value in fresh.state_dict().items()}
            learning.apply_initialization(fresh,path)
            for key,value in fresh.state_dict().items():
                expected=model.state_dict()[key] if key.startswith(('actor_encoders.left.','actor_heads.left.')) else before[key]
                torch.testing.assert_close(value,expected,rtol=0,atol=0)
            with self.assertRaisesRegex(ValueError,'exact transition BC'):
                learning.apply_initialization(SpecialistPolicy(contract=contract(mode='single_b')),path)


if __name__=='__main__':unittest.main()
