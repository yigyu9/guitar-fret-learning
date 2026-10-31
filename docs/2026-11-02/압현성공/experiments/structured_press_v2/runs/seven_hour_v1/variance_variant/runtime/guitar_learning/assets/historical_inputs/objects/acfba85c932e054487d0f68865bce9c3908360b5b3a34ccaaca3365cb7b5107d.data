"""Deadline pilot PPO: existing latent objective with CUDA-aware RNG checkpoints."""
from dataclasses import asdict
import math
import os
from pathlib import Path
import random
import tempfile
import numpy as np
import torch
from .joint_ppo_v1 import JointPPO, PPOConfig
from .joint_policy_v1 import digest


class DeadlinePPO(JointPPO):
    def __init__(self, model, abi, config=PPOConfig()):
        if abi['observation']['dimension'] != model.obs_dim or abi['action_dimension'] != 81:
            raise ValueError('model/ABI dimension mismatch')
        self.model, self.abi, self.config = model, abi, config
        device = next(model.parameters()).device
        if device.type not in ('cpu', 'cuda'):
            raise ValueError('CPU/CUDA only')
        self.abi_sha256 = digest(abi)
        self.optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
        self.updates, self.transitions = 0, 0
        self._collection_env, self._collection_obs = None, None

    def save(self, path):
        path = Path(path)
        if path.exists(): raise FileExistsError(path)
        cuda = next(self.model.parameters()).device.type == 'cuda'
        numpy_rng = np.random.get_state()
        payload = {'schema': 'deadline_pilot_ppo_v1', 'abi': self.abi,
                   'abi_sha256': self.abi_sha256, 'ppo_config': asdict(self.config),
                   'model': self.model.state_dict(), 'optimizer': self.optimizer.state_dict(),
                   'updates': self.updates, 'transitions': self.transitions,
                   'rng_torch': torch.get_rng_state(), 'rng_python': random.getstate(),
                   'rng_numpy': (numpy_rng[0], numpy_rng[1].tolist(), *numpy_rng[2:]),
                   'rng_cuda': torch.cuda.get_rng_state_all() if cuda else [],
                   'saved_device_type': 'cuda' if cuda else 'cpu',
                   'resume_scope': 'model/Adam/RNG; fresh physical episode, not mid-episode replay'}
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp = tempfile.mkstemp(prefix='.'+path.name+'.', dir=path.parent)
        try:
            with os.fdopen(fd, 'wb') as stream:
                torch.save(payload, stream); stream.flush(); os.fsync(stream.fileno())
            os.link(temp, path)
            directory = os.open(path.parent, os.O_RDONLY)
            try: os.fsync(directory)
            finally: os.close(directory)
        finally:
            os.unlink(temp)

    def load(self, path, restore_rng=True):
        device = next(self.model.parameters()).device
        payload = torch.load(path, map_location=device, weights_only=True)
        if (payload['schema'] != 'deadline_pilot_ppo_v1' or
            digest(payload['abi']) != payload['abi_sha256'] or
            payload['abi_sha256'] != self.abi_sha256):
            raise ValueError('checkpoint ABI mismatch before restore')
        if payload['ppo_config'] != asdict(self.config):
            raise ValueError('PPO config mismatch')
        if restore_rng and payload['saved_device_type'] != device.type:
            raise ValueError('exact RNG resume requires same device type; use restore_rng=False for evaluation')
        if restore_rng and device.type == 'cuda' and len(payload['rng_cuda']) != torch.cuda.device_count():
            raise ValueError('CUDA RNG device count mismatch')
        self.model.load_state_dict(payload['model'], strict=True)
        self.optimizer.load_state_dict(payload['optimizer'])
        self.updates, self.transitions = payload['updates'], payload['transitions']
        if restore_rng:
            torch.set_rng_state(payload['rng_torch'].cpu())
            if device.type == 'cuda':
                torch.cuda.set_rng_state_all([v.cpu() for v in payload['rng_cuda']])
            random.setstate(payload['rng_python'])
            name, keys, pos, gaussian, cached = payload['rng_numpy']
            np.random.set_state((name, np.array(keys, dtype=np.uint32), pos, gaussian, cached))
        self._collection_env, self._collection_obs = None, None

