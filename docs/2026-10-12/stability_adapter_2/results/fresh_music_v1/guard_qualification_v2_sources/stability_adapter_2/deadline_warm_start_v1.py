"""Explicit 820 -> 825 policy initialization; never an exact PPO resume."""
import hashlib
from dataclasses import asdict
from pathlib import Path

import torch
from .joint_policy_v1 import JointActorCritic, digest

WARM_START_SHA256 = 'd4cdb7511aecc2927540fa6cc20835f0fc8dae4ec9d335a5cf8b9244fd5624d5'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def migrate(trainer, path, legacy_abi, initial_observation):
    """Validate the frozen source checkpoint, then install only its policy/RMS."""
    if sha(path) != WARM_START_SHA256:
        raise ValueError('registered warm-start checkpoint SHA mismatch')
    device = next(trainer.model.parameters()).device
    payload = torch.load(path, map_location=device, weights_only=True)
    if (payload['schema'] != 'deadline_pilot_ppo_v1' or
            digest(payload['abi']) != payload['abi_sha256']):
        raise ValueError('invalid source checkpoint ABI digest')
    old_abi = dict(payload['abi'])
    source_sha = old_abi.pop('source_sha256')
    if old_abi.pop('action_dimension') != 81 or old_abi != legacy_abi:
        raise ValueError('legacy physical/music/input-order ABI mismatch')
    if not source_sha or any(sha(p) != h for p, h in source_sha.items()):
        raise ValueError('a consumed source checkpoint input changed')
    if payload['ppo_config'] != asdict(trainer.config):
        raise ValueError('source PPO config mismatch')
    if trainer.model.obs_dim != 825 or trainer.updates or trainer.transitions or trainer.optimizer.state:
        raise ValueError('warm start requires a fresh 825D PPO/Adam')
    obs = torch.as_tensor(initial_observation, device=device, dtype=torch.float32)
    if obs.shape != (825,) or not torch.isfinite(obs).all():
        raise ValueError('finite actual initial 825D observation required')
    old_model = JointActorCritic(820, legacy_abi['groups']).to(device)
    old_model.load_state_dict(payload['model'], strict=True)
    state = expanded_state(payload['model'], trainer.model.state_dict())
    # Check a temporary model before mutating the learner, including actual t0.
    candidate = JointActorCritic(825, legacy_abi['groups']).to(device)
    candidate.load_state_dict(state, strict=True)
    evidence = equivalence(old_model, candidate, obs)
    trainer.model.load_state_dict(state, strict=True)
    return {'checkpoint': str(Path(path).resolve()), 'checkpoint_sha256': sha(path),
            'source_abi_sha256': payload['abi_sha256'],
            'source_updates': payload['updates'], 'source_transitions': payload['transitions'],
            'old_source_sha256_verified': source_sha,
            'new_optimizer_empty': not trainer.optimizer.state,
            'new_updates': 0, 'new_transitions': 0,
            'scope': 'policy/RMS warm start; new Adam, ABI and physical episode; not exact resume',
            'equivalence': evidence}


def expanded_state(old_state, template):
    if set(old_state) != set(template):
        raise ValueError('model state key mismatch')
    result = {}
    for key, target in template.items():
        source = old_state[key]
        if not torch.isfinite(source).all():
            raise ValueError('nonfinite source policy state')
        if key in ('actor.0.weight', 'critic.0.weight'):
            if source.shape != (512, 820) or target.shape != (512, 825):
                raise ValueError('input layer shape mismatch')
            value = torch.zeros_like(target)
            value[:, :820] = source
        elif key in ('obs_rms.mean', 'obs_rms.var'):
            if source.shape != (820,) or target.shape != (825,):
                raise ValueError('RMS shape mismatch')
            value = torch.ones_like(target) if key.endswith('var') else torch.zeros_like(target)
            value[:820] = source
        else:
            if source.shape != target.shape:
                raise ValueError('unchanged model layer shape mismatch')
            value = source.clone()
        if key == 'obs_rms.var' and torch.any(value < 0):
            raise ValueError('negative RMS variance')
        result[key] = value
    return result


@torch.no_grad()
def equivalence(old_model, candidate, actual_obs):
    device = actual_obs.device
    # Local generator keeps the learner's exploration RNG untouched.
    generator = torch.Generator(device=device).manual_seed(103)
    prefix = torch.randn(32, 820, generator=generator, device=device)
    extra = torch.randn(32, 5, generator=generator, device=device)*10
    new_obs = torch.cat((prefix, extra), -1)
    new_obs = torch.cat((actual_obs[None], new_obs), 0)
    prior, expanded = old_model.sample(new_obs[:, :820], True), candidate.sample(new_obs, True)
    errors = {}
    for key in ('action', 'latent', 'value', 'log_prob'):
        errors[key] = float((prior[key]-expanded[key]).abs().max())
        if not torch.allclose(prior[key], expanded[key], rtol=2e-5, atol=2e-5):
            raise ValueError('policy expansion equivalence failed: '+key)
    if not torch.equal(old_model.log_std, candidate.log_std):
        raise ValueError('exploration std changed')
    return {'initial_native_plus_random_samples': 33, 'max_absolute_errors': errors,
            'rtol': 2e-5, 'atol': 2e-5, 'log_std_exact': True,
            'first_820_RMS_exact': torch.equal(old_model.obs_rms.mean, candidate.obs_rms.mean[:820])
                and torch.equal(old_model.obs_rms.var, candidate.obs_rms.var[:820]),
            'RMS_count_exact': torch.equal(old_model.obs_rms.count, candidate.obs_rms.count)}
