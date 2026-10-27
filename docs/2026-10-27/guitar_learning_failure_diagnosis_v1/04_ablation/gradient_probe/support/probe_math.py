"""Frozen-batch GAE and pre-clip actor-gradient decomposition; no updates."""
import torch

from guitar_learning.training.decision_ppo import compute_decision_gae
from guitar_learning.training.ppo import policy_advantages
from guitar_learning.training.gpu_pool import FIELDS


def check_close(actual, expected, *, atol=2e-4, rtol=2e-4):
    torch.testing.assert_close(actual, expected, atol=atol, rtol=rtol)
    error = (actual-expected).double()
    denominator = expected.double().norm().clamp_min(1e-12)
    return dict(max_abs=float(error.abs().max()), relative_l2=float(error.norm()/denominator),
                atol=atol, rtol=rtol)


def decompose(buffer, components, config, cost_weight):
    b, valid = buffer, buffer['valid']
    if config.advantage_normalization != 'joint':
        raise ValueError('Exact joint normalization required')
    if components.shape[:2] != valid.shape or components.shape[-1] != 9:
        raise ValueError('Nine final reward components per decision required')
    reward_check = check_close(components.sum(-1)[valid], b['reward'][valid], atol=2e-6, rtol=2e-6)
    zero = torch.zeros_like(b['reward'])
    def gae(reward, value, next_value, gamma):
        return compute_decision_gae(reward, value, next_value, b['terminated'], b['truncated'],
            b['duration'], valid, gamma, config.gae_lambda)[0]
    ar = gae(b['reward'], b['reward_value'], b['next_reward_value'], config.gamma)
    ac = gae(b['cost'], b['cost_value'], b['next_cost_value'], config.cost_gamma)
    terms = [gae(components[..., i], zero, zero, config.gamma) for i in range(9)]
    residual = gae(zero, b['reward_value'], b['next_reward_value'], config.gamma)
    pieces = torch.stack([*terms, residual, -cost_weight*ac], -1)[valid].detach()
    combined, normalized, _, _ = policy_advantages(ar[valid], ac[valid], cost_weight, 'joint')
    sigma = combined.std(unbiased=False).clamp_min(1e-8).detach()
    normalized_pieces = (pieces-pieces.mean(0))/sigma
    checks = dict(reward_sum=reward_check,
        reward_gae=check_close(pieces[:, :10].sum(-1), ar[valid]),
        combined=check_close(pieces.sum(-1), combined),
        normalized=check_close(normalized_pieces.sum(-1), normalized))
    return dict(raw=pieces, normalized_pieces=normalized_pieces.detach(), reward_gae=ar[valid],
        cost_gae=ac[valid], combined=combined, normalized=normalized, sigma=sigma, checks=checks)


def gradient_probe(policy, buffer, decomposition, groups, *, clip_ratio, chunk_size=256):
    """Chunked sum equals the whole-batch mean; denominator is never chunk-local."""
    valid = buffer['valid']
    inputs = tuple(buffer[key][valid].detach() for key in FIELDS)
    latent, old_logp = buffer['latent'][valid].detach(), buffer['logp'][valid].detach()
    parameters = list(policy.actor_parameters())
    count = len(latent)
    width = sum(p.numel() for p in parameters)
    gradients = latent.new_zeros((12, width))  # eleven pieces plus production surrogate
    max_logp_error, max_ratio_error = 0., 0.
    for start in range(0, count, chunk_size):
        stop = min(count, start+chunk_size)
        result = policy.evaluate(*(x[start:stop] for x in inputs), latent[start:stop])
        logp = result['logp']
        ratio = (logp-old_logp[start:stop]).exp()
        max_logp_error = max(max_logp_error, float((logp.detach()-old_logp[start:stop]).abs().max()))
        max_ratio_error = max(max_ratio_error, float((ratio.detach()-1).abs().max()))
        if max_ratio_error > 2e-5:
            raise AssertionError('Frozen on-policy ratio differs from one')
        z = decomposition['normalized_pieces'][start:stop]
        objectives = [-(logp*z[:, i]).sum()/count for i in range(11)]
        advantage = decomposition['normalized'][start:stop].detach()
        objectives.append(-torch.minimum(ratio*advantage,
            ratio.clamp(1-clip_ratio, 1+clip_ratio)*advantage).sum()/count)
        for i, objective in enumerate(objectives):
            grad = torch.autograd.grad(objective, parameters, retain_graph=i < 11, allow_unused=True)
            flat = torch.cat([torch.zeros_like(p).flatten() if g is None else g.detach().flatten()
                              for p, g in zip(parameters, grad)])
            gradients[i].add_(flat)
    check = check_close(gradients[:11].sum(0), gradients[11], atol=2e-5, rtol=5e-4)
    gradients = gradients.cpu()
    output = {}
    for group, indices in groups.items():
        values = gradients[:, indices.cpu()].double()
        total = values[-1]
        norms = values.norm(dim=1)
        dots = values @ total
        total_norm = float(norms[-1])
        output[group] = dict(total_norm=total_norm, component_norm=norms[:11].tolist(),
            signed_dot_total=dots[:11].tolist(),
            cosine_total=[float(dots[i]/(norms[i]*norms[-1]))
                          if float(norms[i]) > 1e-12 and total_norm > 1e-12 else None for i in range(11)],
            sum_component_norm=float(norms[:11].sum()),
            cancellation_norm_gap=float(norms[:11].sum()-norms[-1]))
    return dict(check=check, groups=output, max_logp_error=max_logp_error,
                max_ratio_error=max_ratio_error, gradient_chunk_size=chunk_size,
                parameters=width, valid_decisions=count)


def actor_groups(policy):
    parameters = list(policy.actor_parameters())
    names = {id(p): name for name, p in policy.named_parameters()}
    groups = {name: [] for name in ('all', 'finger_encoder', 'selected_head', 'active_std', 'inactive_std')}
    rows, offset = [], 0
    active = policy._active_mask()[17:33]
    for p in parameters:
        name = names[id(p)]
        ids = torch.arange(offset, offset+p.numel(), device=p.device)
        groups['all'].append(ids)
        if name.startswith('finger_encoder.'):
            groups['finger_encoder'].append(ids)
        elif name.startswith('finger_heads.'+('index', 'middle', 'ring', 'pinky')[policy.finger-1]+'.'):
            groups['selected_head'].append(ids)
        elif name == 'finger_log_std':
            groups['active_std'].append(ids[active])
            groups['inactive_std'].append(ids[~active])
        else:
            raise ValueError('Unexpected trainable short-task actor parameter: '+name)
        rows.append(dict(name=name, shape=list(p.shape), start=offset, stop=offset+p.numel()))
        offset += p.numel()
    if int(active.sum()) != 4:
        raise ValueError('Exactly four selected std entries required')
    return {key: torch.cat(parts) for key, parts in groups.items()}, rows
