"""유한 과제의 PPO에서 행동 정책과 가치망을 별도로 갱신한다.

GAE 계산 → 우위값 정규화 → KL 제한을 둔 정책 갱신 → 가치망 갱신 순서이며, 실패 시 상태를 복원한다."""
import copy
import math
from dataclasses import dataclass,asdict
from pathlib import Path
import os
import random
import tempfile
import numpy as np
import torch


@torch.no_grad()
def rollout_evaluation(policy,inputs,batch_size=4096):
    """토큰 중간값의 메모리 사용을 제한하면서 수집 자료의 모든 출력을 원래 순서대로 유지한다."""
    if len(inputs[0])<=batch_size:
        return policy(*inputs)
    results=[policy(*(value[start:start+batch_size] for value in inputs))
             for start in range(0,len(inputs[0]),batch_size)]
    return {key:torch.cat([result[key] for result in results],dim=0)
            for key in ('mean','log_std','reward_value','cost_value')}


@torch.no_grad()
def tensor_summary(value):
    value=value.detach().reshape(-1).double()
    finite=value[torch.isfinite(value)]
    return dict(count=value.numel(),nonfinite_count=value.numel()-finite.numel(),
                mean=float(finite.mean()) if finite.numel() else None,
                std=float(finite.std(unbiased=False)) if finite.numel() else None,
                min=float(finite.min()) if finite.numel() else None,
                max=float(finite.max()) if finite.numel() else None)


class MinibatchSummary:
    """마지막 미니배치 값 대신 표본 수로 가중한 최적화 단계 통계를 모은다."""
    def __init__(self):
        self.steps=0
        self.samples=0
        self.sums={}
        self.maxima={}
        self.finite_samples={}
        self.nonfinite_steps={}

    @torch.no_grad()
    def add(self,samples,**values):
        self.steps+=1
        self.samples+=samples
        for key,value in values.items():
            number=float(value)
            if not math.isfinite(number):
                self.nonfinite_steps[key]=self.nonfinite_steps.get(key,0)+1
                continue
            self.finite_samples[key]=self.finite_samples.get(key,0)+samples
            self.sums[key]=self.sums.get(key,0.)+samples*number
            self.maxima[key]=max(self.maxima.get(key,-math.inf),number)

    def summary(self):
        return dict(steps=self.steps,sample_visits=self.samples,
                    sample_weighted_mean={k:v/self.finite_samples[k] for k,v in self.sums.items()},
                    max=dict(self.maxima),finite_sample_visits=dict(self.finite_samples),
                    nonfinite_steps=dict(self.nonfinite_steps))


@torch.no_grad()
def advantage_diagnostics(buffer,ar,ac,combined,normalized,weight,config,*,
                          reward_normalized=None,cost_normalized=None):
    result=dict(cost_weight_used=weight,reward_raw=tensor_summary(ar),cost_raw=tensor_summary(ac),
                weighted_cost_raw=tensor_summary(weight*ac),combined_raw=tensor_summary(combined),
                combined_normalized=tensor_summary(normalized))
    if reward_normalized is not None:
        result.update(normalization='separate',reward_normalized=tensor_summary(reward_normalized),
                      cost_normalized=tensor_summary(cost_normalized),
                      weighted_cost_normalized=tensor_summary(weight*cost_normalized),
                      raw_combined=tensor_summary(ar-weight*ac))
    for name,gamma in (('reward',config.gamma),('cost',config.cost_gamma)):
        td=(buffer[name]+gamma*(~buffer['terminated'])*buffer['next_'+name+'_value']-
            buffer[name+'_value'])
        result[name+'_td_residual']=tensor_summary(td)
    return result


@torch.no_grad()
def post_update_diagnostics(policy,inputs,latent,old_logp,rr,rc,clip_ratio):
    result=rollout_evaluation(policy,inputs)
    log_ratio=policy.log_probability(result['mean'],result['log_std'],latent)-old_logp
    ratio=log_ratio.double().exp()
    active=(policy._active_mask() if hasattr(policy,'_active_mask') else
            torch.ones(39,dtype=torch.bool,device=latent.device))
    std=result['log_std'][...,active].exp()
    entropy=(result['log_std'][...,active]+.5*math.log(2*math.pi*math.e)).sum(-1)
    critics={}
    for name,target in (('reward',rr.flatten()),('cost',rc.flatten())):
        value=result[name+'_value']
        error=target.double()-value.double()
        variance=target.double().var(unbiased=False)
        critics[name]=dict(value=tensor_summary(value),target=tensor_summary(target),
                           mse=float(error.square().mean()),
                           explained_variance=(float(1-error.var(unbiased=False)/variance)
                                               if variance>0 else None))
    return dict(scope='full_collected_rollout_after_actor_and_critic_updates',
                critic_target_scope='fixed GAE lambda-return targets from the collected rollout',
                ratio=tensor_summary(ratio),
                clip_fraction=float(((ratio<1-clip_ratio)|(ratio>1+clip_ratio)).float().mean()),
                active_distribution=dict(channels=int(active.sum()),latent_gaussian_entropy=tensor_summary(entropy),
                    std=tensor_summary(std),tanh_saturation_threshold=.98,
                    collected_action_saturation_fraction=float((latent[...,active].tanh().abs()>=.98).float().mean()),
                    post_update_mean_action_saturation_fraction=float((result['mean'][...,active].tanh().abs()>=.98).float().mean()),
                    entropy_scope='latent Gaussian, not entropy of tanh actions'),
                critics=critics)


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
    advantage_normalization: str='joint'


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


def policy_advantages(reward,cost,weight,mode):
    """수집 자료 전체에서 정규화하며, 값이 일정한 성분은 0으로 반영한다."""
    reward_normalized=cost_normalized=None
    if mode=='separate':
        reward_normalized=(reward-reward.mean())/reward.std(unbiased=False).clamp_min(1e-8)
        cost_normalized=(cost-cost.mean())/cost.std(unbiased=False).clamp_min(1e-8)
        combined=(reward_normalized-weight*cost_normalized).flatten()
    elif mode=='joint':
        combined=(reward-weight*cost).flatten()
    else:
        raise ValueError('advantage normalization must be joint or separate')
    normalized=(combined-combined.mean())/combined.std(unbiased=False).clamp_min(1e-8)
    return combined,normalized,reward_normalized,cost_normalized


class KLGuardError(RuntimeError):
    def __init__(self,diagnostic):
        super().__init__('actor KL budget exhausted; actor and Adam restored')
        self.diagnostic=diagnostic


class PPOTrainer:
    """song 공용 PPO 기반. 기본 J 학습은 DecisionPPOTrainer의 유효 결정 갱신을 쓴다."""
    schema='guitar_learning_ppo_v1'

    def __init__(self,policy,config=None):
        self.policy=policy
        self.config=config or PPOConfig()
        c=self.config
        if c.advantage_normalization not in ('joint','separate'):
            raise ValueError('advantage normalization must be joint or separate')
        if not all(np.isfinite(value) for key,value in asdict(c).items()
                   if key!='advantage_normalization' and value is not None):
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
        # 가치망 갱신 실패 시 일부만 갱신된 상태가 체크포인트로 남아서는 안 된다.
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
            if snapshot[6] is not None:
                torch.cuda.set_rng_state_all(snapshot[6])
            raise

    def _update(self,buffer,completed_episodes):
        """에피소드 행 형식: {cost, valid:True, reason:'terminal'|'terminal_failure'|'timeline_complete'}.

        미완료 또는 보호 검사 오류 에피소드는 선택적인 비용 승수를 갱신하지 않는다.
        정규화 설정은 행동 정책의 우위값만 바꾸며, 가치망의 학습 목표는 바꾸지 않는다.
        """
        c=self.config
        eligible=[]
        for row in completed_episodes:
            if row.get('valid') is True and row.get('reason') in ('terminal','terminal_failure','timeline_complete'):
                cost=float(row['cost'])
                if not np.isfinite(cost) or cost<0:
                    raise ValueError('invalid completed episode cost')
                eligible.append(cost)
        b={k:v.detach() for k,v in buffer.items()}
        ar,rr=compute_gae(b['reward'],b['reward_value'],b['next_reward_value'],b['terminated'],b['truncated'],c.gamma,c.gae_lambda)
        ac,rc=compute_gae(b['cost'],b['cost_value'],b['next_cost_value'],b['terminated'],b['truncated'],c.cost_gamma,c.gae_lambda)
        t,n=b['reward'].shape
        if t*n<2:
            raise ValueError('at least two transitions required')
        for key in ('state','events','mask','priority_events','priority_mask','latent','logp','old_mean','old_log_std'):
            if b[key].shape[:2]!=(t,n):
                raise ValueError('rollout shape mismatch: '+key)
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
        combined,advantage,reward_normalized,cost_normalized=policy_advantages(
            ar,ac,self.cost_weight,c.advantage_normalization)
        diagnostics=dict(schema='guitar_learning_ppo_diagnostics_v1',
                         legacy_scalar_scope='last optimizer minibatch; actor metrics refer to last accepted attempt',
                         advantages=advantage_diagnostics(b,ar,ac,combined,advantage,self.cost_weight,c,
                             reward_normalized=reward_normalized,cost_normalized=cost_normalized))
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
                        if not torch.isfinite(loss):
                            raise FloatingPointError('nonfinite actor loss')
                        self.actor_optimizer.zero_grad()
                        loss.backward()
                        norm=torch.nn.utils.clip_grad_norm_(self.policy.actor_parameters(),c.max_grad_norm,error_if_nonfinite=True)
                        self.actor_optimizer.step()
                        with torch.no_grad():
                            full=rollout_evaluation(self.policy,(state,events,mask,priority,priority_mask))
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
                if not torch.isfinite(value_loss):
                    raise FloatingPointError('nonfinite value loss')
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
        config=asdict(self.config)
        if self.config.advantage_normalization=='joint':
            config.pop('advantage_normalization')
        return dict(schema=self.schema,architecture=self.policy.architecture,config=config,
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
        if not all(torch.isfinite(v).all() for v in payload['model'].values()):
            raise ValueError('nonfinite checkpoint model')
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
        if cuda is not None:
            torch.cuda.set_rng_state_all([v.cpu() for v in cuda])
        return payload['metadata']


def compute_decision_gae(reward, value, next_value, terminated, truncated, duration, valid,
                         gamma, gae_lambda):
    fields = (value, next_value, terminated, truncated, duration, valid)
    if reward.ndim != 2 or min(reward.shape) < 1 or any(x.shape != reward.shape for x in fields):
        raise ValueError('decision GAE fields must share nonempty [D,N] shape')
    if any(x.dtype != torch.bool for x in (terminated, truncated, valid)):
        raise ValueError('decision masks must be bool')
    if duration.dtype != torch.long or bool((duration[valid] < 1).any()):
        raise ValueError('positive integer valid durations required')
    if not 0 <= gamma <= 1 or not 0 <= gae_lambda <= 1:
        raise ValueError('discounts must be in [0,1]')
    if not all(torch.isfinite(x[valid]).all() for x in (reward, value, next_value)):
        raise ValueError('nonfinite valid decision GAE input')
    # 환경별 길이가 다른 궤적은 각 환경 배열의 앞부분부터 빈틈없이 배치해야 한다.
    if bool((valid[1:] & ~valid[:-1]).any()):
        raise ValueError('valid decisions must form a prefix in each environment')
    # valid는 환경별 유효 결정의 앞부분이다. 패딩은 역전파·목표 계산에서 제외한다.
    # terminated는 bootstrap도 끊고, truncated는 bootstrap을 허용하되 GAE 연결은 끊는다.
    advantage = torch.zeros_like(reward)
    carry = torch.zeros_like(reward[0])
    for row in reversed(range(len(reward))):
        ids = valid[row]
        delta = (reward[row, ids] + gamma**duration[row, ids] * (~terminated[row, ids]) *
                 next_value[row, ids] - value[row, ids])
        next_carry = torch.zeros_like(carry)
        next_carry[ids] = delta + (gamma*gae_lambda)**duration[row, ids] * (
            ~(terminated[row, ids] | truncated[row, ids])) * carry[ids]
        carry = next_carry
        advantage[row, ids] = carry[ids]
    returns = torch.zeros_like(value)
    returns[valid] = advantage[valid] + value[valid]
    return advantage, returns


class DecisionPPOTrainer(PPOTrainer):
    """기본 J 경로: 유효 결정만 모아 actor를 갱신한 뒤 고정 GAE 목표로 critic을 갱신한다."""
    schema = 'guitar_learning_decision_ppo_v1'

    def _update(self, buffer, completed_episodes):
        config = self.config
        batch = {key: value.detach() for key, value in buffer.items()}
        valid = batch['valid']
        reward_advantage, reward_return = compute_decision_gae(
            batch['reward'], batch['reward_value'], batch['next_reward_value'],
            batch['terminated'], batch['truncated'], batch['duration'], valid,
            config.gamma, config.gae_lambda,
        )
        cost_advantage, cost_return = compute_decision_gae(
            batch['cost'], batch['cost_value'], batch['next_cost_value'],
            batch['terminated'], batch['truncated'], batch['duration'], valid,
            config.cost_gamma, config.gae_lambda,
        )
        count = int(valid.sum())
        if count < 2:
            raise ValueError('at least two valid decisions required')
        selected = {}
        for key in ('state', 'events', 'mask', 'priority_events', 'priority_mask',
                    'latent', 'logp', 'old_mean', 'old_log_std'):
            if batch[key].shape[:2] != valid.shape:
                raise ValueError('rollout shape mismatch: '+key)
            selected[key] = batch[key][valid]
        if (any(selected[key].shape != (count, 39) for key in ('latent', 'old_mean', 'old_log_std'))
                or selected['logp'].shape != (count,)):
            raise ValueError('39D Gaussian and scalar logp required')
        if not all(torch.isfinite(selected[key]).all() for key in ('latent', 'logp', 'old_mean', 'old_log_std')):
            raise ValueError('nonfinite valid old distribution')
        inputs = tuple(selected[key] for key in (
            'state', 'events', 'mask', 'priority_events', 'priority_mask',
        ))
        latent, old_mean, old_log_std, old_logp = (
            selected[key] for key in ('latent', 'old_mean', 'old_log_std', 'logp')
        )
        reward_advantage, cost_advantage, reward_return, cost_return = (
            x[valid] for x in (reward_advantage, cost_advantage, reward_return, cost_return)
        )
        combined, advantage, _, _ = policy_advantages(
            reward_advantage, cost_advantage, self.cost_weight, config.advantage_normalization,
        )
        eligible = []
        for row in completed_episodes:
            if row.get('valid') is True and row.get('reason') in ('terminal', 'terminal_failure', 'timeline_complete'):
                cost = float(row['cost'])
                if not np.isfinite(cost) or cost < 0:
                    raise ValueError('invalid completed episode cost')
                eligible.append(cost)
        accepted, rejected, values = (MinibatchSummary() for _ in range(3))
        retries, max_kl = 0, 0.
        # actor를 먼저 갱신한다. KL은 이번 수집분의 유효 결정 전체에서 판정한다.
        for epoch in range(config.epochs):
            for index in torch.randperm(count, device=inputs[0].device).split(config.minibatch_size):
                before = self._actor_snapshot()
                for retry in range(config.kl_retries+1):
                    result = self.policy.evaluate(*(x[index] for x in inputs), latent[index])
                    ratio = (result['logp']-old_logp[index]).exp()
                    loss = -torch.minimum(
                        ratio*advantage[index],
                        ratio.clamp(1-config.clip_ratio, 1+config.clip_ratio)*advantage[index],
                    ).mean()
                    if not torch.isfinite(loss):
                        raise FloatingPointError('nonfinite actor loss')
                    self.actor_optimizer.zero_grad()
                    loss.backward()
                    norm = torch.nn.utils.clip_grad_norm_(self.policy.actor_parameters(), config.max_grad_norm,
                                                          error_if_nonfinite=True)
                    self.actor_optimizer.step()
                    with torch.no_grad():
                        full = rollout_evaluation(self.policy, inputs)
                        per_row_kl = self.policy.analytic_kl(old_mean, old_log_std, full['mean'], full['log_std'])
                        if per_row_kl.shape != (count,):
                            raise ValueError('policy analytic KL must have one value per valid decision')
                        kl = per_row_kl.mean()
                    max_kl = max(max_kl, float(kl))
                    if torch.isfinite(kl) and kl <= config.target_kl:
                        accepted.add(len(index), loss=loss, grad_norm_pre_clip=norm, full_rollout_kl=kl)
                        break
                    rejected.add(len(index), loss=loss, grad_norm_pre_clip=norm, full_rollout_kl=kl)
                    # 가중치와 Adam 상태를 함께 복원한 뒤 학습률을 낮춰 재시도한다.
                    self._actor_restore(before)
                    retries += 1
                    if retry == config.kl_retries:
                        raise KLGuardError(dict(epoch=epoch, retries=retries, attempted_kl=float(kl),
                                                target_kl=config.target_kl))
                    for group in self.actor_optimizer.param_groups:
                        group['lr'] *= config.retry_lr_factor**(retry+1)
        # actor 갱신을 모두 통과한 뒤 수집 시 고정한 GAE 목표로 critic을 갱신한다.
        # 이 과정의 실패까지 포함한 전체 상태 복원은 상속한 update()가 담당한다.
        for _ in range(config.epochs):
            for index in torch.randperm(count, device=inputs[0].device).split(config.minibatch_size):
                result = self.policy(*(x[index] for x in inputs))
                reward_loss = (result['reward_value']-reward_return[index]).square().mean()
                cost_loss = (result['cost_value']-cost_return[index]).square().mean()
                value_loss = .5*(reward_loss+cost_loss)
                if not torch.isfinite(value_loss):
                    raise FloatingPointError('nonfinite value loss')
                self.value_optimizer.zero_grad()
                value_loss.backward()
                value_norm = torch.nn.utils.clip_grad_norm_(self.policy.value_parameters(), config.max_grad_norm,
                                                            error_if_nonfinite=True)
                self.value_optimizer.step()
                values.add(len(index), reward_loss=reward_loss, cost_loss=cost_loss, grad_norm_pre_clip=value_norm)
        if not all(torch.isfinite(p).all() for p in self.policy.parameters()):
            raise FloatingPointError('nonfinite optimized parameters')
        weight_used = self.cost_weight
        if config.episode_cost_budget is not None and eligible:
            self.cost_weight = max(0., self.cost_weight+config.lambda_lr*(float(np.mean(eligible))-config.episode_cost_budget))
        self.updates += 1
        with torch.no_grad():
            parts = [self.policy.evaluate(*(value[start:start+4096] for value in inputs),
                                          latent[start:start+4096])
                     for start in range(0, count, 4096)]
            final = {key: torch.cat([part[key] for part in parts])
                     for key in ('logp', 'entropy', 'reward_value', 'cost_value')}
            ratio = (final['logp']-old_logp).double().exp()
            critics = {}
            for name, target in (('reward', reward_return), ('cost', cost_return)):
                error = target.double()-final[name+'_value'].double()
                variance = target.double().var(unbiased=False)
                critics[name] = dict(value=tensor_summary(final[name+'_value']), target=tensor_summary(target),
                    mse=float(error.square().mean()), explained_variance=(
                        float(1-error.var(unbiased=False)/variance) if variance > 0 else None))
        diagnostics = dict(
            schema='guitar_learning_decision_ppo_diagnostics_v1',
            scope='valid decisions only; no padded observations evaluated',
            valid_decisions=count,
            physical_transitions=int(batch['duration'][valid].sum()),
            duration=tensor_summary(batch['duration'][valid]),
            advantages=dict(
                cost_weight_used=weight_used,
                reward_raw=tensor_summary(reward_advantage),
                cost_raw=tensor_summary(cost_advantage),
                combined_raw=tensor_summary(combined),
                combined_normalized=tensor_summary(advantage),
            ),
            minibatches=dict(
                actor_accepted=accepted.summary(), actor_rejected=rejected.summary(), value=values.summary(),
            ),
            post_update=dict(
                scope='all valid decisions', ratio=tensor_summary(ratio),
                clip_fraction=float(((ratio < 1-config.clip_ratio) | (ratio > 1+config.clip_ratio)).float().mean()),
                latent_gaussian_entropy=tensor_summary(final['entropy']), critics=critics,
            ),
        )
        return dict(
            actor_loss=float(loss.detach()),
            reward_value_loss=float(reward_loss.detach()),
            cost_value_loss=float(cost_loss.detach()),
            actor_grad_norm=float(norm.detach()), analytic_kl=float(kl),
            max_attempted_kl=max_kl, kl_retries=retries,
            actor_lr=self.actor_optimizer.param_groups[0]['lr'], cost_weight=self.cost_weight,
            actor_loss_last=float(loss.detach()),
            reward_value_loss_last=float(reward_loss.detach()),
            cost_value_loss_last=float(cost_loss.detach()),
            actor_grad_norm_last=float(norm.detach()), diagnostics=diagnostics,
        )
