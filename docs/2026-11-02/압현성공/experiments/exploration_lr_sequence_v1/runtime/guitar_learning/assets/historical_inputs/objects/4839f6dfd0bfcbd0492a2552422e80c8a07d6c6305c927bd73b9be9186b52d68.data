"""Batched policy collection with per-environment bootstrap/reset boundaries."""
import time
import numpy as np
import torch
from stability_adapter_2.deadline_guarded_ppo_v3 import GuardedPPO

class ParallelPPO(GuardedPPO):
    def collect(self,env,steps):
        if type(steps) is not int or steps<=0:raise ValueError('positive rollout length')
        env.require_training_ready()
        if env is not self._collection_env:self._collection_env,self._collection_obs=env,env.reset()
        started=time.monotonic()
        obs=np.array(self._collection_obs,copy=True)
        fields={k:[] for k in ('obs','latent','action','log_prob','value','reward','next_value','terminated','truncated')}
        device=next(self.model.parameters()).device
        for _ in range(steps):
            tensor=torch.as_tensor(obs,device=device,dtype=torch.float32)
            sample=self.model.sample(tensor)
            final_obs,reward,terminated,truncated,info=env.step(sample['action'].cpu().numpy())
            if not np.isfinite(reward).all() or np.asarray(reward).shape!=(env.num_envs,):raise ValueError('finite N rewards required')
            with torch.no_grad():
                nv=self.model.value(torch.as_tensor(final_obs,device=device,dtype=torch.float32)).squeeze(-1)
            fields['obs'].append(tensor.clone())
            for key in ('latent','action','log_prob','value'):fields[key].append(sample[key].clone())
            for key,value,dtype in (('reward',reward,torch.float32),('next_value',nv,torch.float32),
                    ('terminated',terminated,torch.bool),('truncated',truncated,torch.bool)):
                fields[key].append(torch.as_tensor(value,device=device,dtype=dtype).clone())
            # Critic above sees final states, including time-limit endpoints, before any reset.
            obs=np.array(final_obs,copy=True)
            for index,reset_obs in env.reset_done(terminated|truncated).items():obs[index]=reset_obs
            self._collection_obs=np.array(obs,copy=True)
        elapsed=time.monotonic()-started
        self.last_collection_stats={'seconds':elapsed,'transitions':steps*env.num_envs,
            'transitions_per_second':steps*env.num_envs/elapsed,'shape_T_N':[steps,env.num_envs],'policy_batch_size':env.num_envs}
        return {key:torch.stack(value) for key,value in fields.items()}
