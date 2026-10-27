"""Read-only PPO diagnostics; never sample or change optimization state."""
import math

import torch


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
    """Sample-weighted optimizer-step metrics, not a last-minibatch proxy."""
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
def advantage_diagnostics(buffer,ar,ac,combined,normalized,weight,config):
    result=dict(cost_weight_used=weight,reward_raw=tensor_summary(ar),cost_raw=tensor_summary(ac),
                weighted_cost_raw=tensor_summary(weight*ac),combined_raw=tensor_summary(combined),
                combined_normalized=tensor_summary(normalized))
    for name,gamma in (('reward',config.gamma),('cost',config.cost_gamma)):
        td=(buffer[name]+gamma*(~buffer['terminated'])*buffer['next_'+name+'_value']-
            buffer[name+'_value'])
        result[name+'_td_residual']=tensor_summary(td)
    return result


@torch.no_grad()
def post_update_diagnostics(policy,inputs,latent,old_logp,rr,rc,clip_ratio):
    result=policy(*inputs)
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
