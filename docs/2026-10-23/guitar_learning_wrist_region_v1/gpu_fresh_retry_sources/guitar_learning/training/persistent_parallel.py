"""Persistent native worker factory; existing collection/PPO remains unchanged."""
import random
from pathlib import Path
from guitar_learning.training.parallel import Pool


def persistent_native_environment(spec,worker_id):
    import isaacgym  # Must precede numpy/torch in each spawned native worker.
    import numpy as np
    import torch
    from guitar_learning.runtime.persistent_environment import build_persistent_environment
    if not spec.get('headless',True):
        raise ValueError('persistent training currently requires headless sessions')
    seed=int(spec.get('seed',7))+worker_id
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    torch.set_num_threads(1)
    return build_persistent_environment(spec['config'],Path(spec['out'])/'environment',
        bundle=spec['bundle'],stage=spec['stage'],
        start_event_index=spec.get('start_event_index',0),phrase_events=spec.get('phrase_events',8),
        tempo_scale=spec.get('tempo_scale',1.),seed=int(spec.get('seed',7)),worker_id=worker_id,
        music=spec.get('music'),**dict(spec.get('env_kwargs',{})))


class PersistentPool(Pool):
    def __init__(self,specs,timeout_s=120.,worker_factory=None,wait_callback=None):
        super().__init__(specs,timeout_s=timeout_s,
            worker_factory=worker_factory or persistent_native_environment,wait_callback=wait_callback)
