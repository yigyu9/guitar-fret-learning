"""Transactional PPO steps with frozen RMS and complete-rollout analytic KL."""
import copy
import torch
from .deadline_ppo_v1 import DeadlinePPO
from .joint_ppo_v1 import PPOConfig, gae


class GuardedPPO(DeadlinePPO):
    def __init__(self, model, abi, config=PPOConfig(learning_rate=3e-5)):
        super().__init__(model, abi, config)

    @torch.no_grad()
    def _kl(self, observations, old_mean, old_std):
        new = self.model.distribution(observations)
        # Bijective tanh preserves KL; sum joints, mean rollout states.
        value = torch.distributions.kl_divergence(
            torch.distributions.Normal(old_mean, old_std), new).sum(-1).mean()
        return float(value)

    def _guarded_step(self, observations, old_mean, old_std):
        model_before = copy.deepcopy(self.model.state_dict())
        adam_before = copy.deepcopy(self.optimizer.state_dict())
        candidates = []
        for attempt in range(8):
            if attempt:
                self.model.load_state_dict(model_before, strict=True)
                self.optimizer.load_state_dict(adam_before)
            lr = self.config.learning_rate*2**(-attempt)
            for group in self.optimizer.param_groups: group['lr'] = lr
            self.optimizer.step()
            kl = self._kl(observations, old_mean, old_std)
            finite = all(torch.isfinite(p).all() for p in self.model.parameters())
            accepted = bool(finite and 0 <= kl <= self.config.target_kl)
            candidates.append({'attempt': attempt, 'learning_rate': lr,
                               'analytic_kl': kl if torch.isfinite(torch.tensor(kl)) else None,
                               'accepted': accepted})
            if accepted:
                for group in self.optimizer.param_groups: group['lr'] = self.config.learning_rate
                return True, candidates
        self.model.load_state_dict(model_before, strict=True)
        self.optimizer.load_state_dict(adam_before)
        return False, candidates

    def update(self, batch):
        keys = ('obs', 'latent', 'action', 'log_prob', 'value', 'reward',
                'next_value', 'terminated', 'truncated')
        if set(batch) != set(keys): raise ValueError('complete rollout required')
        b = {k: v.detach().clone() for k, v in batch.items()}
        shape = b['reward'].shape
        if len(shape) != 2 or min(shape) < 1: raise ValueError('nonempty [T,N] required')
        for k in keys:
            expected = shape+(self.model.obs_dim,) if k == 'obs' else shape+(81,) if k in ('latent', 'action') else shape
            if b[k].shape != expected: raise ValueError('rollout shape mismatch: '+k)
            if k not in ('terminated', 'truncated') and not torch.isfinite(b[k]).all():
                raise ValueError('nonfinite rollout: '+k)
        if not torch.equal(torch.tanh(b['latent']), b['action']):
            raise ValueError('stored action must equal tanh(latent)')
        c = self.config
        adv, returns = gae(b['reward'], b['value'], b['next_value'], b['terminated'],
                           b['truncated'], c.gamma, c.lam)
        flat = {k: v.flatten(0, 1) for k, v in b.items()}
        adv, returns = adv.flatten(), returns.flatten()
        adv = (adv-adv.mean())/(adv.std(unbiased=False)+1e-8)
        rms_before = copy.deepcopy(self.model.obs_rms.state_dict())
        with torch.no_grad():
            initial_lp, _, _ = self.model.evaluate_latent(flat['obs'], flat['latent'])
            if not torch.allclose(initial_lp, flat['log_prob'], atol=2e-4, rtol=1e-5):
                raise ValueError('stale/off-policy rollout or normalization changed')
            distribution = self.model.distribution(flat['obs'])
            old_mean, old_std = distribution.mean.clone(), distribution.stddev.clone()
        metrics, rejected, stopped = [], [], False
        for _ in range(c.epochs):
            for indices in torch.randperm(len(adv), device=adv.device).split(c.minibatch_size):
                lp, entropy, value = self.model.evaluate_latent(flat['obs'][indices], flat['latent'][indices])
                ratio = (lp-flat['log_prob'][indices]).exp()
                policy = -torch.minimum(ratio*adv[indices], ratio.clamp(1-c.clip_ratio, 1+c.clip_ratio)*adv[indices]).mean()
                clipped = flat['value'][indices]+(value-flat['value'][indices]).clamp(-c.value_clip, c.value_clip)
                value_loss = .5*torch.maximum((value-returns[indices]).square(), (clipped-returns[indices]).square()).mean()
                loss = policy+c.value_weight*value_loss-c.entropy_weight*entropy.mean()
                if not torch.isfinite(loss): raise FloatingPointError('nonfinite PPO loss')
                self.optimizer.zero_grad()
                loss.backward()
                norm = torch.nn.utils.clip_grad_norm_(self.model.parameters(), c.max_grad_norm, error_if_nonfinite=True)
                accepted, candidates = self._guarded_step(flat['obs'], old_mean, old_std)
                if not accepted:
                    rejected = candidates; stopped = True
                    break
                metrics.append({'policy_loss': float(policy.detach()), 'value_loss': float(value_loss.detach()),
                                'entropy_per_joint': float(entropy.mean().detach()),
                                'gradient_norm': float(norm), 'kl': candidates[-1]['analytic_kl'],
                                'step_candidates': candidates})
            if stopped: break
        if any(not torch.equal(v, rms_before[k]) for k, v in self.model.obs_rms.state_dict().items()):
            raise AssertionError('frozen RMS changed')
        final_kl = self._kl(flat['obs'], old_mean, old_std)
        if not 0 <= final_kl <= c.target_kl: raise AssertionError('final policy exceeds rollout KL budget')
        self.updates += 1; self.transitions += len(adv)
        return {'optimizer_steps': len(metrics), 'early_kl_stop': stopped, 'minibatches': metrics,
                'rejected_final_candidates': rejected, 'final_analytic_kl': final_kl,
                'RMS_updated': False, 'transitions': len(adv), 'gamma': c.gamma, 'lambda': c.lam}
