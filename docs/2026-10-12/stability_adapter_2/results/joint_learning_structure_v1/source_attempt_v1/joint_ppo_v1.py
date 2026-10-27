"""Task-neutral PPO with explicit bootstrap/reset boundaries; no native reward fiction."""
from dataclasses import asdict, dataclass
import math
import os
from pathlib import Path
import random
import tempfile
import numpy as np
import torch
from .joint_policy_v1 import digest


@dataclass(frozen=True)
class PPOConfig:
    control_hz: int = 60
    discount_half_life_s: float = 10.
    trace_half_life_s: float = 1.
    learning_rate: float = 3e-4
    clip_ratio: float = .2
    value_clip: float = .2
    value_weight: float = .5
    entropy_weight: float = .001
    max_grad_norm: float = 1.
    target_kl: float = .02
    epochs: int = 4
    minibatch_size: int = 128

    def __post_init__(self):
        for key, value in asdict(self).items():
            if not math.isfinite(value) or value <= 0:
                raise ValueError('positive finite PPO setting required: '+key)
        if self.control_hz != 60 or self.clip_ratio >= 1:
            raise ValueError('60Hz and clip ratio below one required')
        if any(type(getattr(self,k)) is not int for k in ('epochs','minibatch_size')):
            raise ValueError('integer epochs/minibatch size required')

    @property
    def gamma(self): return 2**(-1/(self.control_hz*self.discount_half_life_s))

    @property
    def lam(self): return 2**(-1/(self.control_hz*self.trace_half_life_s))


def gae(reward, value, next_value, terminated, truncated, gamma, lam):
    """next_value must use the transition's final observation, never a reset state."""
    if reward.ndim != 2 or any(x.shape != reward.shape for x in
                              (value,next_value,terminated,truncated)):
        raise ValueError('matching [T,N] GAE tensors required')
    if terminated.dtype != torch.bool or truncated.dtype != torch.bool:
        raise ValueError('boolean episode boundaries required')
    if any(not torch.isfinite(x).all() for x in (reward,value,next_value)):
        raise ValueError('non-finite GAE input')
    if not 0 < gamma <= 1 or not 0 < lam <= 1:
        raise ValueError('invalid discount/trace factor')
    advantage = torch.zeros_like(reward)
    carry = torch.zeros_like(reward[0])
    for t in reversed(range(len(reward))):
        delta = reward[t] + gamma*next_value[t]*(~terminated[t]) - value[t]
        carry = delta + gamma*lam*carry*(~(terminated[t] | truncated[t]))
        advantage[t] = carry
    return advantage, advantage+value


class JointPPO:
    def __init__(self, model, abi, config=PPOConfig()):
        if abi['observation']['dimension'] != model.obs_dim or abi['action_dimension'] != 81:
            raise ValueError('model/ABI dimension mismatch')
        self.model, self.abi, self.config = model, abi, config
        if next(model.parameters()).device.type != 'cpu':
            raise ValueError('v1 supports CPU training/checkpoint RNG only')
        self.abi_sha256 = digest(abi)
        self.optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
        self.updates, self.transitions = 0, 0
        self._collection_env, self._collection_obs = None, None

    def update(self, batch):
        keys = ('obs','latent','action','log_prob','value','reward','next_value','terminated','truncated')
        if set(batch) != set(keys): raise ValueError('complete rollout fields required')
        b = {k:v.detach().clone() for k,v in batch.items()}
        shape = b['reward'].shape
        if len(shape) != 2 or min(shape) < 1: raise ValueError('nonempty [T,N] rollout required')
        for k in keys:
            expected = shape+(self.model.obs_dim,) if k=='obs' else shape+(81,) if k in ('latent','action') else shape
            if b[k].shape != expected: raise ValueError('rollout shape mismatch: '+k)
            if k not in ('terminated','truncated') and not torch.isfinite(b[k]).all():
                raise ValueError('non-finite rollout field: '+k)
        if not torch.equal(torch.tanh(b['latent']), b['action']):
            raise ValueError('stored action must be sampled tanh(latent), not executed PD inverse')
        adv, returns = gae(b['reward'],b['value'],b['next_value'],b['terminated'],b['truncated'],
                           self.config.gamma,self.config.lam)
        flat = {k:v.flatten(0,1) for k,v in b.items()}
        adv, returns = adv.flatten(), returns.flatten()
        adv = (adv-adv.mean())/(adv.std(unbiased=False)+1e-8)
        c, count = self.config, len(adv)
        with torch.no_grad():
            initial_lp, _, _ = self.model.evaluate_latent(flat['obs'],flat['latent'])
            if not torch.allclose(initial_lp,flat['log_prob'],atol=2e-4,rtol=1e-5):
                raise ValueError('stale/off-policy rollout or normalization changed')
        metrics, stopped = [], False
        for _ in range(c.epochs):
            for indices in torch.randperm(count,device=adv.device).split(c.minibatch_size):
                lp, entropy, value = self.model.evaluate_latent(flat['obs'][indices],flat['latent'][indices])
                log_ratio = lp-flat['log_prob'][indices]
                ratio = log_ratio.exp()
                kl = ((ratio-1)-log_ratio).mean()
                if not torch.isfinite(kl): raise FloatingPointError('non-finite PPO KL')
                if float(kl.detach()) > c.target_kl:
                    stopped = True
                    break
                policy = -torch.minimum(ratio*adv[indices],ratio.clamp(1-c.clip_ratio,1+c.clip_ratio)*adv[indices]).mean()
                clipped = flat['value'][indices]+(value-flat['value'][indices]).clamp(-c.value_clip,c.value_clip)
                value_loss = .5*torch.maximum((value-returns[indices]).square(),(clipped-returns[indices]).square()).mean()
                loss = policy+c.value_weight*value_loss-c.entropy_weight*entropy.mean()
                if not torch.isfinite(loss): raise FloatingPointError('non-finite PPO loss')
                self.optimizer.zero_grad()
                loss.backward()
                norm = torch.nn.utils.clip_grad_norm_(self.model.parameters(),c.max_grad_norm,error_if_nonfinite=True)
                self.optimizer.step()
                metrics.append({'policy_loss':float(policy.detach()),'value_loss':float(value_loss.detach()),
                                'entropy_per_joint':float(entropy.mean().detach()),'kl':float(kl.detach()),
                                'gradient_norm':float(norm)})
            if stopped: break
        # Frozen throughout collection and every likelihood reevaluation; changed only here.
        self.model.obs_rms.update(flat['obs'])
        self.updates += 1
        self.transitions += count
        return {'optimizer_steps':len(metrics),'early_kl_stop':stopped,'minibatches':metrics,
                'transitions':count,'gamma':c.gamma,'lambda':c.lam}

    def collect(self, env, steps):
        """Single-scene collection. Native env must certify the complete reward contract."""
        if type(steps) is not int or steps <= 0: raise ValueError('positive rollout length required')
        env.require_training_ready()
        if env is not self._collection_env:
            self._collection_env, self._collection_obs = env, env.reset()
        obs = self._collection_obs
        fields = {k:[] for k in ('obs','latent','action','log_prob','value','reward','next_value','terminated','truncated')}
        device = next(self.model.parameters()).device
        for _ in range(steps):
            tensor = torch.as_tensor(np.array(obs,copy=True),dtype=torch.float32,device=device)[None]
            sample = self.model.sample(tensor)
            final_obs,reward,terminated,truncated,info = env.step(sample['action'][0].cpu().numpy())
            if type(terminated) is not bool or type(truncated) is not bool or not math.isfinite(reward):
                raise ValueError('finite scalar reward and explicit boolean boundaries required')
            with torch.no_grad():
                nv = self.model.value(torch.as_tensor(np.array(final_obs,copy=True),dtype=torch.float32,device=device)[None]).squeeze(-1)
            fields['obs'].append(tensor.clone())
            for k in ('latent','action','log_prob','value'): fields[k].append(sample[k].clone())
            for k,v,dtype in (('reward',reward,torch.float32),('next_value',float(nv[0]),torch.float32),
                              ('terminated',terminated,torch.bool),('truncated',truncated,torch.bool)):
                fields[k].append(torch.tensor([v],dtype=dtype,device=device))
            obs = env.reset() if terminated or truncated else final_obs
            self._collection_obs = np.array(obs,copy=True)
        return {k:torch.stack(v) for k,v in fields.items()}

    def save(self, path):
        path = Path(path)
        if path.exists(): raise FileExistsError(path)
        payload = {'schema':'upper81_ppo_v1','abi':self.abi,'abi_sha256':self.abi_sha256,
                   'ppo_config':asdict(self.config),'model':self.model.state_dict(),
                   'optimizer':self.optimizer.state_dict(),'updates':self.updates,'transitions':self.transitions,
                   'rng_torch':torch.get_rng_state(),'rng_python':random.getstate(),
                   'rng_numpy':(np.random.get_state()[0],np.random.get_state()[1].tolist(),
                                *np.random.get_state()[2:]),
                   'resume_scope':'optimizer/RNG/model; new physical scene, not mid-episode continuation'}
        path.parent.mkdir(parents=True,exist_ok=True)
        fd,temp = tempfile.mkstemp(prefix='.'+path.name+'.',dir=path.parent)
        try:
            with os.fdopen(fd,'wb') as stream:
                torch.save(payload,stream);stream.flush();os.fsync(stream.fileno())
            os.link(temp,path)  # Atomic create, never replace an existing checkpoint.
            directory = os.open(path.parent,os.O_RDONLY)
            try: os.fsync(directory)
            finally: os.close(directory)
        finally:
            os.unlink(temp)

    def load(self, path):
        payload = torch.load(path,map_location=next(self.model.parameters()).device,weights_only=True)
        if payload['schema'] != 'upper81_ppo_v1' or digest(payload['abi']) != payload['abi_sha256'] or payload['abi_sha256'] != self.abi_sha256:
            raise ValueError('checkpoint ABI mismatch before state restore')
        if payload['ppo_config'] != asdict(self.config): raise ValueError('PPO config mismatch')
        self.model.load_state_dict(payload['model'],strict=True)
        self.optimizer.load_state_dict(payload['optimizer'])
        self.updates,self.transitions = payload['updates'],payload['transitions']
        torch.set_rng_state(payload['rng_torch'].cpu())
        random.setstate(payload['rng_python'])
        name,keys,pos,gaussian,cached = payload['rng_numpy']
        np.random.set_state((name,np.array(keys,dtype=np.uint32),pos,gaussian,cached))
        self._collection_env, self._collection_obs = None, None
