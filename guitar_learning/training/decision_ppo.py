"""PPO over variable-duration decisions, with padding excluded before optimization."""
import numpy as np
import torch

from guitar_learning.training.ppo import PPOTrainer, KLGuardError, policy_advantages
from guitar_learning.training.ppo_diagnostics import MinibatchSummary, rollout_evaluation, tensor_summary


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
    # Every environment's ragged trajectory must occupy a contiguous prefix.
    if bool((valid[1:] & ~valid[:-1]).any()):
        raise ValueError('valid decisions must form a prefix in each environment')
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
    schema = 'guitar_learning_decision_ppo_v1'

    def _update(self, buffer, completed_episodes):
        c = self.config
        b = {key: value.detach() for key, value in buffer.items()}
        valid = b['valid']
        ar, rr = compute_decision_gae(b['reward'], b['reward_value'], b['next_reward_value'],
            b['terminated'], b['truncated'], b['duration'], valid, c.gamma, c.gae_lambda)
        ac, rc = compute_decision_gae(b['cost'], b['cost_value'], b['next_cost_value'],
            b['terminated'], b['truncated'], b['duration'], valid, c.cost_gamma, c.gae_lambda)
        count = int(valid.sum())
        if count < 2:
            raise ValueError('at least two valid decisions required')
        selected = {}
        for key in ('state', 'events', 'mask', 'priority_events', 'priority_mask',
                    'latent', 'logp', 'old_mean', 'old_log_std'):
            if b[key].shape[:2] != valid.shape:
                raise ValueError('rollout shape mismatch: '+key)
            selected[key] = b[key][valid]
        if (any(selected[key].shape != (count, 39) for key in ('latent', 'old_mean', 'old_log_std'))
                or selected['logp'].shape != (count,)):
            raise ValueError('39D Gaussian and scalar logp required')
        if not all(torch.isfinite(selected[key]).all() for key in ('latent', 'logp', 'old_mean', 'old_log_std')):
            raise ValueError('nonfinite valid old distribution')
        inputs = tuple(selected[key] for key in ('state', 'events', 'mask', 'priority_events', 'priority_mask'))
        latent, old_mean, old_std, old_logp = (selected[key] for key in ('latent', 'old_mean', 'old_log_std', 'logp'))
        ar, ac, rr, rc = (x[valid] for x in (ar, ac, rr, rc))
        combined, advantage, _, _ = policy_advantages(ar, ac, self.cost_weight, c.advantage_normalization)
        eligible = []
        for row in completed_episodes:
            if row.get('valid') is True and row.get('reason') in ('terminal', 'terminal_failure', 'timeline_complete'):
                cost = float(row['cost'])
                if not np.isfinite(cost) or cost < 0:
                    raise ValueError('invalid completed episode cost')
                eligible.append(cost)
        accepted, rejected, values = (MinibatchSummary() for _ in range(3))
        retries, max_kl = 0, 0.
        for epoch in range(c.epochs):
            for index in torch.randperm(count, device=inputs[0].device).split(c.minibatch_size):
                before = self._actor_snapshot()
                for retry in range(c.kl_retries+1):
                    result = self.policy.evaluate(*(x[index] for x in inputs), latent[index])
                    ratio = (result['logp']-old_logp[index]).exp()
                    loss = -torch.minimum(ratio*advantage[index], ratio.clamp(
                        1-c.clip_ratio, 1+c.clip_ratio)*advantage[index]).mean()
                    if not torch.isfinite(loss):
                        raise FloatingPointError('nonfinite actor loss')
                    self.actor_optimizer.zero_grad()
                    loss.backward()
                    norm = torch.nn.utils.clip_grad_norm_(self.policy.actor_parameters(), c.max_grad_norm,
                                                          error_if_nonfinite=True)
                    self.actor_optimizer.step()
                    with torch.no_grad():
                        full = rollout_evaluation(self.policy, inputs)
                        per_row_kl = self.policy.analytic_kl(old_mean, old_std, full['mean'], full['log_std'])
                        if per_row_kl.shape != (count,):
                            raise ValueError('policy analytic KL must have one value per valid decision')
                        kl = per_row_kl.mean()
                    max_kl = max(max_kl, float(kl))
                    if torch.isfinite(kl) and kl <= c.target_kl:
                        accepted.add(len(index), loss=loss, grad_norm_pre_clip=norm, full_rollout_kl=kl)
                        break
                    rejected.add(len(index), loss=loss, grad_norm_pre_clip=norm, full_rollout_kl=kl)
                    self._actor_restore(before)
                    retries += 1
                    if retry == c.kl_retries:
                        raise KLGuardError(dict(epoch=epoch, retries=retries, attempted_kl=float(kl),
                                                target_kl=c.target_kl))
                    for group in self.actor_optimizer.param_groups:
                        group['lr'] *= c.retry_lr_factor**(retry+1)
        for _ in range(c.epochs):
            for index in torch.randperm(count, device=inputs[0].device).split(c.minibatch_size):
                result = self.policy(*(x[index] for x in inputs))
                reward_loss = (result['reward_value']-rr[index]).square().mean()
                cost_loss = (result['cost_value']-rc[index]).square().mean()
                value_loss = .5*(reward_loss+cost_loss)
                if not torch.isfinite(value_loss):
                    raise FloatingPointError('nonfinite value loss')
                self.value_optimizer.zero_grad()
                value_loss.backward()
                value_norm = torch.nn.utils.clip_grad_norm_(self.policy.value_parameters(), c.max_grad_norm,
                                                            error_if_nonfinite=True)
                self.value_optimizer.step()
                values.add(len(index), reward_loss=reward_loss, cost_loss=cost_loss, grad_norm_pre_clip=value_norm)
        if not all(torch.isfinite(p).all() for p in self.policy.parameters()):
            raise FloatingPointError('nonfinite optimized parameters')
        weight_used = self.cost_weight
        if c.episode_cost_budget is not None and eligible:
            self.cost_weight = max(0., self.cost_weight+c.lambda_lr*(float(np.mean(eligible))-c.episode_cost_budget))
        self.updates += 1
        with torch.no_grad():
            parts = [self.policy.evaluate(*(value[start:start+4096] for value in inputs),
                                          latent[start:start+4096])
                     for start in range(0, count, 4096)]
            final = {key: torch.cat([part[key] for part in parts])
                     for key in ('logp', 'entropy', 'reward_value', 'cost_value')}
            ratio = (final['logp']-old_logp).double().exp()
            critics = {}
            for name, target in (('reward', rr), ('cost', rc)):
                error = target.double()-final[name+'_value'].double()
                variance = target.double().var(unbiased=False)
                critics[name] = dict(value=tensor_summary(final[name+'_value']), target=tensor_summary(target),
                    mse=float(error.square().mean()), explained_variance=(
                        float(1-error.var(unbiased=False)/variance) if variance > 0 else None))
        diagnostics = dict(schema='guitar_learning_decision_ppo_diagnostics_v1',
            scope='valid decisions only; no padded observations evaluated', valid_decisions=count,
            physical_transitions=int(b['duration'][valid].sum()), duration=tensor_summary(b['duration'][valid]),
            advantages=dict(cost_weight_used=weight_used, reward_raw=tensor_summary(ar), cost_raw=tensor_summary(ac),
                combined_raw=tensor_summary(combined), combined_normalized=tensor_summary(advantage)),
            minibatches=dict(actor_accepted=accepted.summary(), actor_rejected=rejected.summary(), value=values.summary()),
            post_update=dict(scope='all valid decisions', ratio=tensor_summary(ratio),
                clip_fraction=float(((ratio < 1-c.clip_ratio) | (ratio > 1+c.clip_ratio)).float().mean()),
                latent_gaussian_entropy=tensor_summary(final['entropy']), critics=critics))
        return dict(actor_loss=float(loss.detach()), reward_value_loss=float(reward_loss.detach()), cost_value_loss=float(cost_loss.detach()),
            actor_grad_norm=float(norm.detach()), analytic_kl=float(kl), max_attempted_kl=max_kl, kl_retries=retries,
            actor_lr=self.actor_optimizer.param_groups[0]['lr'], cost_weight=self.cost_weight,
            actor_loss_last=float(loss.detach()), reward_value_loss_last=float(reward_loss.detach()), cost_value_loss_last=float(cost_loss.detach()),
            actor_grad_norm_last=float(norm.detach()), diagnostics=diagnostics)
