"""Diagnostics must describe PPO without changing its numerical trajectory."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import torch

from guitar_learning.training.ppo import PPOConfig, PPOTrainer, compute_gae, gaussian_kl
from guitar_learning.training.ppo_diagnostics import MinibatchSummary, post_update_diagnostics, rollout_evaluation
from guitar_learning.tests.test_policy import policy
from guitar_learning.tests.test_ppo import buffer,assert_tree
from guitar_learning.tests.test_specialist_policy import specialist


def original_module():
    path=(Path(__file__).resolve().parents[1]/'archive'/'20261019_before_logging_improvements'/
          'guitar_learning'/'ppo.py')
    name='ppo_before_logging_diagnostics_test'
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module
    spec.loader.exec_module(module)
    return module


class PPOLoggingTests(unittest.TestCase):
    def test_chunked_rollout_preserves_outputs_KL_state_and_RNG(self):
        for role in ('shared','left','right'):
            model=policy() if role=='shared' else specialist(role)
            data=buffer(model)
            inputs=tuple(data[k].flatten(0,1) for k in
                         ('state','events','mask','priority_events','priority_mask'))
            saved=copy.deepcopy(model.state_dict())
            rng=torch.get_rng_state().clone()
            with torch.no_grad():
                expected=model(*inputs)
            for batch_size in (3,4,16):
                visits=[]
                def limited(*values):
                    visits.append(len(values[0]))
                    self.assertLessEqual(len(values[0]),batch_size)
                    return model(*values)
                with self.subTest(role=role,batch_size=batch_size):
                    actual=rollout_evaluation(limited,inputs,batch_size)
                    self.assertEqual(sum(visits),8)
                    for key in expected:
                        torch.testing.assert_close(actual[key],expected[key])
                        self.assertFalse(actual[key].requires_grad)
                    old_mean=data['old_mean'].flatten(0,1)+.01
                    old_std=data['old_log_std'].flatten(0,1)
                    torch.testing.assert_close(
                        gaussian_kl(old_mean,old_std,actual['mean'],actual['log_std']),
                        gaussian_kl(old_mean,old_std,expected['mean'],expected['log_std']))
            self.assertTrue(torch.equal(rng,torch.get_rng_state()))
            assert_tree(self,saved,model.state_dict())

    def test_post_update_chunking_preserves_global_diagnostics(self):
        model=specialist('left')
        data=buffer(model)
        inputs=tuple(data[k].flatten(0,1) for k in
                     ('state','events','mask','priority_events','priority_mask'))
        args=(model,inputs,data['latent'].flatten(0,1),data['logp'].flatten(),
              torch.arange(8).float(),torch.ones(8),.2)
        expected=post_update_diagnostics(*args)
        with patch('guitar_learning.training.ppo_diagnostics.rollout_evaluation',
                   side_effect=lambda policy,inputs: rollout_evaluation(policy,inputs,3)):
            actual=post_update_diagnostics(*args)
        def close(left,right):
            if isinstance(left,dict):
                self.assertEqual(left.keys(),right.keys())
                for key in left:close(left[key],right[key])
            elif isinstance(left,float):
                self.assertAlmostEqual(left,right,places=5)
            else:self.assertEqual(left,right)
        close(expected,actual)

    def test_sample_weighted_aggregation_separates_nonfinite_attempts(self):
        stats=MinibatchSummary()
        stats.add(3,loss=2.,kl=float('inf'))
        stats.add(1,loss=6.,kl=.2)
        result=stats.summary()
        self.assertEqual(result['sample_weighted_mean']['loss'],3.)
        self.assertEqual(result['max']['loss'],6.)
        self.assertEqual(result['nonfinite_steps'],{'kl':1})
        self.assertEqual(result['finite_sample_visits']['kl'],1)
        json.dumps(result,allow_nan=False)

    def test_update_matches_archived_weights_optimizers_rng_and_legacy_metrics(self):
        original=original_module()
        for role in ('shared','left','right'):
            with self.subTest(role=role):
                torch.manual_seed(19)
                model=policy() if role=='shared' else specialist(role)
                config=PPOConfig(actor_lr=1e-4,epochs=2,minibatch_size=3,target_kl=.02)
                current=PPOTrainer(model,config)
                old=original.PPOTrainer(copy.deepcopy(model),original.PPOConfig(**config.__dict__))
                data=buffer(model)
                rng=torch.get_rng_state()
                expected=old.update(data)
                expected_rng=torch.get_rng_state()
                torch.set_rng_state(rng)
                actual=current.update(data)
                self.assertTrue(torch.equal(expected_rng,torch.get_rng_state()))
                assert_tree(self,old.policy.state_dict(),current.policy.state_dict())
                assert_tree(self,old.actor_optimizer.state_dict(),current.actor_optimizer.state_dict())
                assert_tree(self,old.value_optimizer.state_dict(),current.value_optimizer.state_dict())
                self.assertEqual(old._identity(),current._identity())
                self.assertEqual(expected,{k:actual[k] for k in expected})
                self.assertEqual(current.updates,old.updates)
                json.dumps(actual,allow_nan=False)
                diag=actual['diagnostics']
                self.assertEqual(diag['minibatches']['actor_accepted']['sample_visits'],16)
                self.assertEqual(diag['minibatches']['actor_rejected']['steps'],actual['kl_retries'])
                self.assertEqual(diag['minibatches']['value']['sample_visits'],16)
                self.assertEqual(actual['actor_loss'],actual['actor_loss_last'])
                expected_channels={'shared':39,'left':33,'right':6}[role]
                self.assertEqual(diag['post_update']['active_distribution']['channels'],expected_channels)
                ar,_=compute_gae(data['reward'],data['reward_value'],data['next_reward_value'],
                                 data['terminated'],data['truncated'],config.gamma,config.gae_lambda)
                self.assertAlmostEqual(diag['advantages']['reward_raw']['mean'],float(ar.double().mean()))
                self.assertAlmostEqual(diag['advantages']['combined_normalized']['std'],1.,places=6)

    def test_post_update_metrics_active_only_and_zero_target_variance(self):
        for role,channels in (('left',33),('right',6)):
            model=specialist(role)
            data=buffer(model)
            inputs=tuple(data[k].flatten(0,1) for k in
                         ('state','events','mask','priority_events','priority_mask'))
            latent=data['latent'].flatten(0,1)
            inactive=~model._active_mask()
            latent[:,inactive]=10.
            rng=torch.get_rng_state()
            result=post_update_diagnostics(model,inputs,latent,data['logp'].flatten(),
                                            torch.zeros(8),torch.zeros(8),.2)
            self.assertTrue(torch.equal(rng,torch.get_rng_state()))
            self.assertEqual(result['critics']['reward']['explained_variance'],None)
            self.assertEqual(result['critics']['cost']['explained_variance'],None)
            self.assertEqual(result['active_distribution']['channels'],channels)
            self.assertEqual(result['active_distribution']['collected_action_saturation_fraction'],0.)
            expected=channels*(-3.+.5*torch.log(torch.tensor(2.*torch.pi*torch.e)).item())
            self.assertAlmostEqual(result['active_distribution']['latent_gaussian_entropy']['mean'],expected,places=4)
            self.assertEqual(result['clip_fraction'],0.)
            json.dumps(result,allow_nan=False)


if __name__=='__main__':
    unittest.main()
