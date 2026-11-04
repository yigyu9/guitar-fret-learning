"""오른손27축 분포·39칸 버퍼·공용 PPO 재개 identity를 CPU에서 검사한다."""
import copy
import tempfile
from pathlib import Path
import unittest
import torch
from guitar_learning.training.policy import Policy
from guitar_learning.training.ppo import PPOConfig, PPOTrainer, gaussian_kl
from guitar_learning.tool.experiments.right27.policy import Right27Policy

torch.set_num_threads(1)


def model():
    contract=dict(schema='guitar_learning.training.v1',observation=dict(dimension=5),
        action=dict(dimension=39),task=dict(source='right24_cpu_fixture'),reward={},termination={})
    return Right27Policy(5,size='small',contract=contract)


def inputs(batch=8):
    return (torch.randn(batch,5),torch.randn(batch,2,24),torch.ones(batch,2,dtype=torch.bool),
        torch.randn(batch,2,24),torch.ones(batch,2,dtype=torch.bool))


def buffer(policy):
    values=inputs()
    with torch.no_grad():out=policy.act(*values)
    result={k:v[:,None] for k,v in zip(('state','events','mask','priority_events','priority_mask'),values)}
    result.update({k:out[v][:,None].clone() for k,v in (('latent','latent'),('logp','logp'),('old_mean','mean'),
        ('old_log_std','log_std'),('reward_value','reward_value'),('cost_value','cost_value'))})
    result.update(next_reward_value=torch.zeros(8,1),next_cost_value=torch.zeros(8,1),
        reward=torch.arange(8.).reshape(8,1)/10,cost=torch.zeros(8,1),
        terminated=torch.zeros(8,1,dtype=torch.bool),truncated=torch.zeros(8,1,dtype=torch.bool))
    return result


class Right27PolicyTests(unittest.TestCase):
    def test_layout_and_inert_channels_for_sample_and_mean(self):
        policy=model();values=inputs()
        self.assertEqual(policy.role_sizes,(12,27));self.assertEqual(policy.log_std.shape,(27,))
        self.assertEqual(policy.architecture['active_action_indices'],list(range(12,39)))
        self.assertEqual(policy.architecture['action_layout']['right_hand21'],[12,33])
        for deterministic in (False,True):
            out=policy.act(*values,deterministic=deterministic)
            for name in ('mean','log_std','latent','action'):
                self.assertEqual(out[name].shape,(8,39));self.assertTrue(torch.equal(out[name][:,:12],torch.zeros(8,12)))
            self.assertTrue(torch.isfinite(out['logp']).all())
        self.assertFalse(policy.actor_heads[0].weight.requires_grad)
        with self.assertRaises(ValueError):Right27Policy(5,contract=policy.architecture['contract'],role='left')
        with self.assertRaises(ValueError):Right27Policy(5,contract=policy.architecture['contract'],frozen_partner=True)

    def test_logp_entropy_and_kl_ignore_inert_container(self):
        policy=model();values=inputs();out=policy.act(*values);evaluated=policy.evaluate(*values,out['latent'])
        self.assertTrue(torch.allclose(out['logp'],evaluated['logp']))
        expected=torch.distributions.Normal(out['mean'][:,12:],out['log_std'][:,12:].exp()).entropy().sum(-1)
        self.assertTrue(torch.allclose(expected,evaluated['entropy']))
        latent=out['latent'].clone();latent[:,:12]=100
        self.assertTrue(torch.equal(policy.evaluate(*values,latent)['logp'],out['logp']))
        changed_mean=out['mean'].clone();changed_std=out['log_std'].clone();changed_mean[:,:12]=100;changed_std[:,:12]=1
        self.assertTrue(torch.equal(policy.analytic_kl(out['mean'],out['log_std'],changed_mean,changed_std),torch.zeros(8)))
        changed_mean[:,12:]+=.1
        expected=policy.analytic_kl(out['mean'],out['log_std'],changed_mean,changed_std)
        self.assertTrue((expected>0).all())
        # 공용 PPO의 전체39칸 KL도 실제 forward의 고정 빈칸에서는 추가 기여가 없다.
        changed_mean[:,:12]=0;changed_std[:,:12]=0
        self.assertTrue(torch.allclose(gaussian_kl(out['mean'],out['log_std'],changed_mean,changed_std),expected.mean()))

    def test_ppo_update39_and_strict_checkpoint_identity(self):
        torch.manual_seed(7);policy=model();config=PPOConfig(actor_lr=1e-5,target_kl=.1,epochs=1)
        trainer=PPOTrainer(policy,config);data=buffer(policy);before=policy.actor_heads[1].weight.detach().clone()
        result=trainer.update(data)
        self.assertEqual(result['diagnostics']['post_update']['active_distribution']['channels'],27)
        self.assertFalse(torch.equal(before,policy.actor_heads[1].weight));self.assertEqual(trainer.updates,1)
        with tempfile.TemporaryDirectory() as name:
            path=Path(name)/'right27.pt';trainer.save(path,dict(scope='CPU'))
            restored=PPOTrainer(model(),config);self.assertEqual(restored.load(path),dict(scope='CPU'))
            for key,value in policy.state_dict().items():self.assertTrue(torch.equal(value,restored.policy.state_dict()[key]))
            old=Policy(5,size='small',contract=copy.deepcopy(policy.architecture['contract']));old_trainer=PPOTrainer(old,config)
            old_path=Path(name)/'old39.pt';old_trainer.save(old_path)
            with self.assertRaises(ValueError):restored.load(old_path)
            with self.assertRaises(ValueError):old_trainer.load(path)
            bad=Path(name)/'bad.pt';payload=torch.load(path,weights_only=False);payload['identity']['architecture']['action_layout']['right_hand21']=[0,21];torch.save(payload,bad)
            with self.assertRaises(ValueError):restored.load(bad)


if __name__=='__main__':unittest.main()
