"""CPU checks for explicit actor advantage units and legacy checkpoint identity."""
import copy
from dataclasses import asdict
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import torch

from guitar_learning.tests.test_policy import policy
from guitar_learning.tests.test_ppo import assert_tree, buffer
from guitar_learning.training.ppo import PPOConfig, PPOTrainer, KLGuardError, policy_advantages


class SignalBalanceTests(unittest.TestCase):
    def signals(self):
        return torch.tensor([[1., 3.], [-2., 5.]]), torch.tensor([[4., -1.], [2., 0.]])

    def test_separate_cost_scale_nineteen_preserves_actor_signal(self):
        reward,cost=self.signals()
        original=[x.clone() for x in (reward,cost)]
        rng=torch.get_rng_state()
        combined,normalized,rn,cn=policy_advantages(reward,cost,1.,'separate')
        scaled=policy_advantages(7*reward+2,19*cost-3,1.,'separate')
        for expected,actual in zip((combined,normalized,rn,cn),scaled):
            torch.testing.assert_close(expected,actual)
        self.assertTrue(torch.equal(rng,torch.get_rng_state()))
        for a,b in zip(original,(reward,cost)): self.assertTrue(torch.equal(a,b))
        for component in (rn,cn,normalized):
            self.assertAlmostEqual(float(component.mean()),0.,places=6)
            self.assertAlmostEqual(float(component.std(unbiased=False)),1.,places=6)
        self.assertFalse(torch.allclose(policy_advantages(reward,cost,1.,'joint')[1],
                                        policy_advantages(reward,19*cost,1.,'joint')[1]))

    def test_constant_zero_and_cancelling_components_are_finite(self):
        reward,cost=self.signals()
        for r,c in ((reward,torch.zeros_like(cost)),(torch.zeros_like(reward),cost),
                    (torch.full_like(reward,7.),torch.full_like(cost,3.)),(reward,reward)):
            result=policy_advantages(r,c,1.,'separate')
            self.assertTrue(all(torch.isfinite(x).all() for x in result))
            if torch.equal(r,c) or (r.std()==0 and c.std()==0):
                self.assertTrue(torch.equal(result[1],torch.zeros_like(result[1])))
        tiny=torch.tensor([0.,1e-10])
        result=policy_advantages(tiny,torch.zeros_like(tiny),1.,'separate')
        torch.testing.assert_close(result[2],torch.tensor([-.005,.005]))

    def test_zero_cost_weight_ignores_cost(self):
        reward,cost=self.signals()
        a=policy_advantages(reward,cost,0.,'separate')
        b=policy_advantages(reward,19*cost,0.,'separate')
        self.assertTrue(torch.equal(a[0],b[0]))
        self.assertTrue(torch.equal(a[1],b[1]))
        torch.testing.assert_close(a[1],a[2].flatten())

    def test_joint_is_bitexact_old_formula_and_legacy_identity(self):
        reward,cost=self.signals()
        old=(reward-.7*cost).flatten()
        normalized=(old-old.mean())/old.std(unbiased=False).clamp_min(1e-8)
        actual=policy_advantages(reward,cost,.7,'joint')
        self.assertTrue(torch.equal(actual[0],old))
        self.assertTrue(torch.equal(actual[1],normalized))
        self.assertEqual(actual[2:],(None,None))
        config=PPOConfig()
        expected=asdict(config)
        expected.pop('advantage_normalization')
        trainer=PPOTrainer(policy(),config)
        self.assertEqual(trainer._identity()['config'],expected)
        self.assertNotIn('advantage_normalization',trainer._identity()['config'])
        with self.assertRaisesRegex(ValueError,'normalization'):
            PPOTrainer(policy(),PPOConfig(advantage_normalization='invalid'))

    def test_joint_update_output_model_optimizers_rng_equal_old_calculation(self):
        torch.manual_seed(71)
        config=PPOConfig(actor_lr=1e-6,target_kl=.1,epochs=1)
        current=PPOTrainer(policy(),config)
        data=buffer(current.policy)
        other=PPOTrainer(copy.deepcopy(current.policy),config)
        rng=torch.get_rng_state()
        result=current.update(data)
        final_rng=torch.get_rng_state()
        def legacy(reward,cost,weight,mode):
            combined=(reward-weight*cost).flatten()
            normalized=(combined-combined.mean())/combined.std(unbiased=False).clamp_min(1e-8)
            return combined,normalized,None,None
        torch.set_rng_state(rng)
        with patch('guitar_learning.training.ppo.policy_advantages',legacy):
            self.assertEqual(other.update(data),result)
        self.assertTrue(torch.equal(final_rng,torch.get_rng_state()))
        assert_tree(self,current.policy.state_dict(),other.policy.state_dict())
        assert_tree(self,current.actor_optimizer.state_dict(),other.actor_optimizer.state_dict())
        assert_tree(self,current.value_optimizer.state_dict(),other.value_optimizer.state_dict())

    def test_separate_real_update_diagnostics_and_strict_resume(self):
        torch.manual_seed(72)
        config=PPOConfig(actor_lr=1e-6,target_kl=.1,epochs=1,advantage_normalization='separate')
        trainer=PPOTrainer(policy(),config)
        data=buffer(trainer.policy)
        data['cost']=torch.tensor([2.,0.,3.,1.,0.,2.,0.,1.])[:,None]
        before=copy.deepcopy(trainer.policy.state_dict())
        result=trainer.update(data)
        self.assertTrue(any(not torch.equal(before[k],v) for k,v in trainer.policy.state_dict().items()))
        diagnostic=result['diagnostics']['advantages']
        self.assertEqual(diagnostic['normalization'],'separate')
        for key in ('reward_raw','cost_raw','reward_normalized','cost_normalized',
                    'weighted_cost_normalized','raw_combined','combined_raw','combined_normalized'):
            self.assertEqual(diagnostic[key]['count'],8)
            self.assertEqual(diagnostic[key]['nonfinite_count'],0)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'separate.pt'
            trainer.save(path)
            expected=trainer.update(data)
            restored=PPOTrainer(policy(),config)
            restored.load(path)
            self.assertEqual(restored.update(data),expected)
            assert_tree(self,trainer.policy.state_dict(),restored.policy.state_dict())
            assert_tree(self,trainer.actor_optimizer.state_dict(),restored.actor_optimizer.state_dict())
            assert_tree(self,trainer.value_optimizer.state_dict(),restored.value_optimizer.state_dict())
            joint=PPOTrainer(policy(),PPOConfig(actor_lr=1e-6,target_kl=.1,epochs=1))
            with self.assertRaisesRegex(ValueError,'mismatch'): joint.load(path)
            old=Path(directory)/'joint.pt'
            joint.save(old)
            # Legacy joint identity still loads in joint mode, not separate mode.
            joint.load(old)
            with self.assertRaisesRegex(ValueError,'mismatch'): restored.load(old)

    def test_separate_preserves_critic_targets_and_updates(self):
        torch.manual_seed(74)
        joint=PPOTrainer(policy(),PPOConfig(actor_lr=1e-6,target_kl=.1,epochs=1))
        separate=PPOTrainer(copy.deepcopy(joint.policy),PPOConfig(actor_lr=1e-6,
            target_kl=.1,epochs=1,advantage_normalization='separate'))
        data=buffer(joint.policy)
        data['cost']=torch.arange(8.).flip(0)[:,None]
        rng=torch.get_rng_state()
        a=joint.update(data)
        torch.set_rng_state(rng)
        b=separate.update(data)
        for key in ('reward_value_loss','cost_value_loss'):
            self.assertEqual(a[key],b[key])
        for x,y in zip(joint.policy.value_parameters(),separate.policy.value_parameters()):
            self.assertTrue(torch.equal(x,y))
        assert_tree(self,joint.value_optimizer.state_dict(),separate.value_optimizer.state_dict())
        self.assertEqual(joint.cost_weight,separate.cost_weight)

    def test_separate_kl_and_critic_failure_restore_all_state(self):
        for failure in ('kl','critic'):
            with self.subTest(failure=failure):
                torch.manual_seed(73)
                trainer=PPOTrainer(policy(),PPOConfig(actor_lr=.1 if failure=='kl' else 1e-6,
                    target_kl=1e-12 if failure=='kl' else .1,kl_retries=1,epochs=1,
                    advantage_normalization='separate'))
                data=buffer(trainer.policy)
                before=copy.deepcopy(trainer.policy.state_dict())
                actor=copy.deepcopy(trainer.actor_optimizer.state_dict())
                value=copy.deepcopy(trainer.value_optimizer.state_dict())
                rng=torch.get_rng_state()
                if failure=='kl':
                    with self.assertRaises(KLGuardError): trainer.update(data)
                else:
                    step=trainer.value_optimizer.step
                    def fail():
                        step()
                        raise RuntimeError('critic failure')
                    with patch.object(trainer.value_optimizer,'step',fail):
                        with self.assertRaisesRegex(RuntimeError,'critic failure'): trainer.update(data)
                assert_tree(self,before,trainer.policy.state_dict())
                assert_tree(self,actor,trainer.actor_optimizer.state_dict())
                assert_tree(self,value,trainer.value_optimizer.state_dict())
                self.assertTrue(torch.equal(rng,torch.get_rng_state()))
                self.assertEqual(trainer.updates,0)
                self.assertEqual(trainer.cost_weight,1.)


if __name__=='__main__':
    unittest.main()
