"""Transfer a pinned old825 Actor/RMS; retain a fresh Critic and Adam."""
import hashlib
from dataclasses import asdict
from pathlib import Path

import torch
from .joint_policy_v1 import JointActorCritic, digest

SOURCE_SHA256 = {
    True: '0127e0807dc363fd6802dba6fb2053e5d4a9d11301002589c910db3f2838054d',
    False: '738e2ec6df28afbd5d05c1e76dc6dc0bfa53b23d1c55674a53a25c66fb3823ee',
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def migrate(trainer, path, prior_abi, initial_observation):
    if sha(path) != SOURCE_SHA256[prior_abi['strap_enabled']]:
        raise ValueError('registered same-mode source checkpoint SHA mismatch')
    device = next(trainer.model.parameters()).device
    payload = torch.load(path, map_location=device, weights_only=True)
    if payload['schema'] != 'deadline_pilot_ppo_v1' or digest(payload['abi']) != payload['abi_sha256']:
        raise ValueError('source ABI digest invalid')
    abi = dict(payload['abi']); sources = abi.pop('source_sha256')
    if abi != prior_abi:
        raise ValueError('old825 physical/music/observation/control ABI mismatch')
    if not sources or any(sha(p) != h for p, h in sources.items()):
        raise ValueError('consumed checkpoint source changed')
    if payload['ppo_config'] != asdict(trainer.config):
        raise ValueError('source PPO config mismatch')
    if trainer.model.obs_dim != 825 or trainer.updates or trainer.transitions or trainer.optimizer.state:
        raise ValueError('fresh825 learner/Adam required')
    obs = torch.as_tensor(initial_observation, device=device, dtype=torch.float32)
    if obs.shape != (825,) or not torch.isfinite(obs).all():
        raise ValueError('finite actual initial825 observation required')
    template = trainer.model.state_dict()
    source = payload['model']
    if set(template) != set(source) or any(source[k].shape != value.shape or
            not torch.isfinite(source[k]).all() for k, value in template.items()):
        raise ValueError('source model shape/finiteness invalid')
    if torch.any(source['obs_rms.var'] < 0):
        raise ValueError('source RMS variance invalid')
    prior = JointActorCritic(825, prior_abi['groups']).to(device)
    prior.load_state_dict(source, strict=True)
    candidate = JointActorCritic(825, prior_abi['groups']).to(device)
    state = {k: source[k].clone() if not k.startswith('critic.') else value.clone()
             for k, value in template.items()}
    candidate.load_state_dict(state, strict=True)
    with torch.no_grad():
        generator = torch.Generator(device=device).manual_seed(103)
        observations = torch.cat((obs[None], torch.randn(32, 825, generator=generator, device=device)))
        old, new = prior.sample(observations, True), candidate.sample(observations, True)
        errors = {k: float((old[k]-new[k]).abs().max()) for k in ('action', 'latent', 'log_prob')}
        if any(not torch.equal(old[k], new[k]) for k in errors):
            raise ValueError('Actor transfer changed native/random policy output')
    trainer.model.load_state_dict(state, strict=True)
    return {'checkpoint': str(Path(path).resolve()), 'checkpoint_sha256': sha(path),
        'source_abi_sha256': payload['abi_sha256'], 'source_updates': payload['updates'],
        'source_transitions': payload['transitions'], 'old_source_sha256_verified': sources,
        'initial_native_plus_random_samples': 33, 'actor_output_max_absolute_error': errors,
        'actor_log_std_RMS_exact': True, 'critic_retained_fresh': True,
        'new_optimizer_empty': not trainer.optimizer.state, 'new_updates': 0,
        'scope': 'Actor/log_std/RMS only; fresh Critic/Adam/ABI/physical episode; not exact resume'}
