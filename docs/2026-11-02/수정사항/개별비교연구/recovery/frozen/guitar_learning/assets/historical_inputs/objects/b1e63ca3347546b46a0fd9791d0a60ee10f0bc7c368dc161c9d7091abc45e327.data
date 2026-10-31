"""Pinned825 RMS only; failed Actor, Critic and optimizer are not inherited."""
import hashlib
from pathlib import Path
import torch
from .joint_policy_v1 import digest

SOURCE_SHA256 = '5f2c6b055c2b268311870a3cf84e49e22887343010b7030cc264484a7a29131b'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def initialize(trainer, path, prior_abi):
    if sha(path) != SOURCE_SHA256 or not prior_abi['strap_enabled']:
        raise ValueError('registered ON initial checkpoint required')
    payload = torch.load(path, map_location=next(trainer.model.parameters()).device, weights_only=True)
    if payload['schema'] != 'deadline_pilot_ppo_v1' or digest(payload['abi']) != payload['abi_sha256']:
        raise ValueError('source ABI digest invalid')
    abi = dict(payload['abi']); sources = abi.pop('source_sha256')
    if abi != prior_abi or not sources or any(sha(p) != h for p, h in sources.items()):
        raise ValueError('source physical/music/observation ABI or source bytes mismatch')
    if trainer.model.obs_dim != 825 or trainer.updates or trainer.transitions or trainer.optimizer.state:
        raise ValueError('fresh825 learner required')
    template = trainer.model.state_dict()
    keys = [k for k in template if k.startswith('obs_rms.')]
    source = payload['model']
    if (set(keys) != {'obs_rms.mean', 'obs_rms.var', 'obs_rms.count'}
            or any(source[k].shape != template[k].shape or not torch.isfinite(source[k]).all() for k in keys)
            or torch.any(source['obs_rms.var'] < 0) or source['obs_rms.count'] <= 0):
        raise ValueError('source RMS invalid')
    if torch.count_nonzero(trainer.model.actor[-1].weight) or torch.count_nonzero(trainer.model.actor[-1].bias):
        raise ValueError('neutral output layer required before initialization')
    state = {k: source[k].clone() if k in keys else v.clone() for k, v in template.items()}
    trainer.model.load_state_dict(state, strict=True)
    return {'checkpoint': str(Path(path).resolve()), 'checkpoint_sha256': sha(path),
            'source_abi_sha256': payload['abi_sha256'], 'source_sha256_verified': sources,
            'RMS_exact_frozen': True, 'actor_mean_zero': True, 'critic_and_Adam_fresh': True,
            'scope': 'RMS only; new policy/control ABI and physical episode; not exact resume'}
