"""Finite-task PPO with independent actor/value optimization and transactional KL guard."""
import copy
from dataclasses import dataclass,asdict
from pathlib import Path
import os
import random
import tempfile
import numpy as np
import torch
from .ppo_diagnostics import MinibatchSummary,advantage_diagnostics,post_update_diagnostics


@dataclass(frozen=True)
class PPOConfig:
    actor_lr: float=3e-5
    value_lr: float=3e-4
    gamma: float=.99
    cost_gamma: float=1.
    gae_lambda: float=.95
    clip_ratio: float=.2
    cost_weight: float=1.
    epochs: int=2
    minibatch_size: int=256
    max_grad_norm: float=.5
    target_kl: float=.02
    kl_retries: int=3
    retry_lr_factor: float=.25
    episode_cost_budget: float=None
    lambda_lr: float=.01


def compute_gae(reward,value,next_value,terminated,truncated,gamma,gae_lambda):
    if reward.ndim!=2 or any(x.shape!=reward.shape for x in (value,next_value,terminated,truncated)):
        raise ValueError('GAE fields must share [T,N] shape')
    if terminated.dtype!=torch.bool or truncated.dtype!=torch.bool:
        raise ValueError('GAE flags must be bool')
    if not all(torch.isfinite(x).all() for x in (reward,value,next_value)):
        raise ValueError('nonfinite GAE input')
    if reward.shape[0] < 1 or reward.shape[1] < 1:
        raise ValueError('nonempty GAE trajectory required')
    advantage=torch.zeros_like(reward)
    carry=torch.zeros_like(reward[0])
    for t in reversed(range(len(reward))):
        delta=reward[t]+gamma*(~terminated[t])*next_value[t]-value[t]
        carry=delta+gamma*gae_lambda*(~(terminated[t]|truncated[t]))*carry
        advantage[t]=carry
    return advantage,advantage+value


def gaussian_kl(old_mean,old_log_std,mean,log_std):
    return (log_std-old_log_std+(old_log_std.mul(2).exp()+(old_mean-mean).square())/
            (2*log_std.mul(2).exp())-.5).sum(-1).mean()


class KLGuardError(RuntimeError):
    def __init__(self,diagnostic):
        super().__init__('actor KL budget exhausted; actor and Adam restored')
        self.diagnostic=diagnostic


class PPOTrainer:
    schema='guitar_learning_ppo_v1'

    def __init__(self,policy,config=None):
        self.policy=policy
        self.config=config or PPOConfig()
        c=self.config
        if not all(np.isfinite(value) for value in asdict(c).values() if value is not None):
            raise ValueError('finite PPO config required')
        if any(isinstance(v,bool) or not isinstance(v,int) for v in (c.epochs,c.minibatch_size,c.kl_retries)):
            raise ValueError('integer optimization loop fields required')
        if c.clip_ratio<=0:
            raise ValueError('positive PPO clip ratio required')
        if c.episode_cost_budget is not None and c.cost_gamma!=1.:
            raise ValueError('finite episode budget requires undiscounted cost_gamma=1')
        if min(c.actor_lr,c.value_lr,c.target_kl,c.max_grad_norm)<=0 or min(c.epochs,c.minibatch_size)<1 or c.kl_retries<0 or not 0<c.retry_lr_factor<1:
            raise ValueError('invalid PPO optimization config')
        if not 0<=c.gamma<=1 or not 0<=c.cost_gamma<=1 or not 0<=c.gae_lambda<=1 or c.cost_weight<0 or c.lambda_lr<0:
            raise ValueError('invalid PPO return/budget config')
        if c.episode_cost_budget is not None and c.episode_cost_budget<0:
            raise ValueError('episode budget must be nonnegative')
        self.actor_optimizer=torch.optim.Adam(policy.actor_parameters(),lr=c.actor_lr)
        self.value_optimizer=torch.optim.Adam(policy.value_parameters(),lr=c.value_lr)
        self.cost_weight=c.cost_weight
        self.updates=0

    def _actor_snapshot(self):
        return [p.detach().clone() for p in self.policy.actor_parameters()],copy.deepcopy(self.actor_optimizer.state_dict())

    def _actor_restore(self,snapshot):
        with torch.no_grad():
            for parameter,value in zip(self.policy.actor_parameters(),snapshot[0]):
                parameter.copy_(value)
        self.actor_optimizer.load_state_dict(snapshot[1])

    def update(self,buffer,completed_episodes=()):
        # A failed critic step must not leave a partially updated checkpoint.
        snapshot = (copy.deepcopy(self.policy.state_dict()),
                    copy.deepcopy(self.actor_optimizer.state_dict()),
                    copy.deepcopy(self.value_optimizer.state_dict()),
                    self.cost_weight, self.updates, torch.get_rng_state(),
                    torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None)
        try:
            return self._update(buffer,completed_episodes)
        except BaseException:
            self.policy.load_state_dict(snapshot[0])
            self.actor_optimizer.load_state_dict(snapshot[1])
            self.value_optimizer.load_state_dict(snapshot[2])
            self.cost_weight,self.updates = snapshot[3:5]
            torch.set_rng_state(snapshot[5])
            if snapshot[6] is not None: torch.cuda.set_rng_state_all(snapshot[6])
            raise

    def _update(self,buffer,completed_episodes):
        """Episode rows: {cost, valid:True, reason:'terminal'|'terminal_failure'|'timeline_complete'}.

        Incomplete/guard-fault episodes never update the optional multiplier.
        Reward and cost advantages retain their units until jointly normalized.
        """
        c=self.config
        eligible=[]
        for row in completed_episodes:
            if row.get('valid') is True and row.get('reason') in ('terminal','terminal_failure','timeline_complete'):
                cost=float(row['cost'])
                if not np.isfinite(cost) or cost<0: raise ValueError('invalid completed episode cost')
                eligible.append(cost)
        b={k:v.detach() for k,v in buffer.items()}
        ar,rr=compute_gae(b['reward'],b['reward_value'],b['next_reward_value'],b['terminated'],b['truncated'],c.gamma,c.gae_lambda)
        ac,rc=compute_gae(b['cost'],b['cost_value'],b['next_cost_value'],b['terminated'],b['truncated'],c.cost_gamma,c.gae_lambda)
        t,n=b['reward'].shape
        if t*n<2: raise ValueError('at least two transitions required')
        for key in ('state','events','mask','priority_events','priority_mask','latent','logp','old_mean','old_log_std'):
            if b[key].shape[:2]!=(t,n): raise ValueError('rollout shape mismatch: '+key)
        state=b['state'].flatten(0,1)
        events=b['events'].flatten(0,1)
        mask=b['mask'].flatten(0,1)
        priority=b['priority_events'].flatten(0,1)
        priority_mask=b['priority_mask'].flatten(0,1)
        if any(b[key].shape!=(t,n,39) for key in ('latent','old_mean','old_log_std')) or b['logp'].shape!=(t,n):
            raise ValueError('39D Gaussian and scalar logp rollout shapes required')
        latent=b['latent'].reshape(-1,39)
        old_mean=b['old_mean'].reshape(-1,39)
        old_std=b['old_log_std'].reshape(-1,39)
        old_logp=b['logp'].flatten()
        if not all(torch.isfinite(x).all() for x in (old_mean,old_std,old_logp,latent)):
            raise ValueError('nonfinite old distribution')
        advantage=(ar-self.cost_weight*ac).flatten()
        combined=advantage
        advantage=(advantage-advantage.mean())/advantage.std(unbiased=False).clamp_min(1e-8)
        diagnostics=dict(schema='guitar_learning_ppo_diagnostics_v1',
                         legacy_scalar_scope='last optimizer minibatch; actor metrics refer to last accepted attempt',
                         advantages=advantage_diagnostics(b,ar,ac,combined,advantage,self.cost_weight,c))
        actor_accepted,actor_rejected,value_steps=(MinibatchSummary() for _ in range(3))
        original=self._actor_snapshot()
        retries=0
        max_kl=0.
        try:
            for epoch in range(c.epochs):
                for index in torch.randperm(t*n,device=state.device).split(c.minibatch_size):
                    before=self._actor_snapshot()
                    for retry in range(c.kl_retries+1):
                        result=self.policy.evaluate(state[index],events[index],mask[index],priority[index],priority_mask[index],latent[index])
                        ratio=(result['logp']-old_logp[index]).exp()
                        loss=-torch.minimum(ratio*advantage[index],ratio.clamp(1-c.clip_ratio,1+c.clip_ratio)*advantage[index]).mean()
                        if not torch.isfinite(loss): raise FloatingPointError('nonfinite actor loss')
                        self.actor_optimizer.zero_grad()
                        loss.backward()
                        norm=torch.nn.utils.clip_grad_norm_(self.policy.actor_parameters(),c.max_grad_norm,error_if_nonfinite=True)
                        self.actor_optimizer.step()
                        with torch.no_grad():
                            full=self.policy(state,events,mask,priority,priority_mask)
                            kl=gaussian_kl(old_mean,old_std,full['mean'],full['log_std'])
                        max_kl=max(max_kl,float(kl))
                        if torch.isfinite(kl) and kl<=c.target_kl:
                            actor_accepted.add(len(index),loss=loss,grad_norm_pre_clip=norm,full_rollout_kl=kl)
                            break
                        actor_rejected.add(len(index),loss=loss,grad_norm_pre_clip=norm,full_rollout_kl=kl)
                        self._actor_restore(before)
                        retries+=1
                        if retry==c.kl_retries:
                            raise KLGuardError(dict(epoch=epoch,retries=retries,attempted_kl=float(kl),target_kl=c.target_kl))
                        for group in self.actor_optimizer.param_groups:
                            group['lr']*=c.retry_lr_factor**(retry+1)
        except BaseException:
            self._actor_restore(original)
            raise
        for _ in range(c.epochs):
            for index in torch.randperm(t*n,device=state.device).split(c.minibatch_size):
                result=self.policy(state[index],events[index],mask[index],priority[index],priority_mask[index])
                reward_loss=(result['reward_value']-rr.flatten()[index]).square().mean()
                cost_loss=(result['cost_value']-rc.flatten()[index]).square().mean()
                value_loss=.5*(reward_loss+cost_loss)
                if not torch.isfinite(value_loss): raise FloatingPointError('nonfinite value loss')
                self.value_optimizer.zero_grad()
                value_loss.backward()
                value_norm=torch.nn.utils.clip_grad_norm_(self.policy.value_parameters(),c.max_grad_norm,error_if_nonfinite=True)
                self.value_optimizer.step()
                value_steps.add(len(index),reward_loss=reward_loss,cost_loss=cost_loss,grad_norm_pre_clip=value_norm)
        if not all(torch.isfinite(p).all() for p in self.policy.parameters()):
            raise FloatingPointError('nonfinite optimized parameters')
        if c.episode_cost_budget is not None and eligible:
            self.cost_weight=max(0.,self.cost_weight+c.lambda_lr*(float(np.mean(eligible))-c.episode_cost_budget))
        self.updates+=1
        diagnostics['minibatches']=dict(actor_accepted=actor_accepted.summary(),actor_rejected=actor_rejected.summary(),
                                       value=value_steps.summary())
        diagnostics['post_update']=post_update_diagnostics(self.policy,(state,events,mask,priority,priority_mask),
                                                          latent,old_logp,rr,rc,c.clip_ratio)
        return dict(actor_loss=float(loss),reward_value_loss=float(reward_loss),cost_value_loss=float(cost_loss),
                    actor_grad_norm=float(norm),analytic_kl=float(kl),max_attempted_kl=max_kl,
                    kl_retries=retries,actor_lr=self.actor_optimizer.param_groups[0]['lr'],cost_weight=self.cost_weight,
                    actor_loss_last=float(loss),reward_value_loss_last=float(reward_loss),cost_value_loss_last=float(cost_loss),
                    actor_grad_norm_last=float(norm),diagnostics=diagnostics)

    def _identity(self):
        return dict(schema=self.schema,architecture=self.policy.architecture,config=asdict(self.config),
                    resume_scope='PPO_optimizer_RNG_only_new_environment_episode')

    def save(self,path,metadata=None):
        path=Path(path)
        path.parent.mkdir(parents=True,exist_ok=True)
        payload=dict(identity=self._identity(),model=self.policy.state_dict(),actor_optimizer=self.actor_optimizer.state_dict(),
            value_optimizer=self.value_optimizer.state_dict(),cost_weight=self.cost_weight,updates=self.updates,metadata=metadata,
            torch_rng=torch.get_rng_state(),numpy_rng=np.random.get_state(),python_rng=random.getstate(),
            cuda_rng=torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None)
        descriptor,temporary=tempfile.mkstemp(prefix='checkpoint-',suffix='.pt',dir=str(path.parent))
        os.close(descriptor)
        try:
            torch.save(payload,temporary)
            os.link(temporary,path)
        finally:
            os.unlink(temporary)

    def load(self,path):
        payload=torch.load(path,map_location=next(self.policy.parameters()).device,weights_only=False)
        if not isinstance(payload,dict) or payload.get('identity')!=self._identity():
            raise ValueError('own schema/architecture/input/control/config mismatch')
        if not all(torch.isfinite(v).all() for v in payload['model'].values()): raise ValueError('nonfinite checkpoint model')
        cuda=payload['cuda_rng']
        if cuda is not None and (not torch.cuda.is_available() or len(cuda)!=torch.cuda.device_count()):
            raise ValueError('CUDA RNG topology mismatch')
        self.policy.load_state_dict(payload['model'],strict=True)
        self.actor_optimizer.load_state_dict(payload['actor_optimizer'])
        self.value_optimizer.load_state_dict(payload['value_optimizer'])
        self.cost_weight=payload['cost_weight']
        self.updates=payload['updates']
        torch.set_rng_state(payload['torch_rng'].cpu())
        np.random.set_state(payload['numpy_rng'])
        random.setstate(payload['python_rng'])
        if cuda is not None: torch.cuda.set_rng_state_all([v.cpu() for v in cuda])
        return payload['metadata']
