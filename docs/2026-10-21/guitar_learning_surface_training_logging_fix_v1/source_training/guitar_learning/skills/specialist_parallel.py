"""Spawn workers with independent-hand rewards and unchanged native support."""
import copy
import random
from pathlib import Path
from guitar_learning.training.parallel import Pool, _compact as base_compact
from guitar_learning.skills.specialist_settings import frozen_partner


def specialist_compact(env, info, action):
    result = base_compact(env, info, action)
    # Preserve the independent evidence alongside the original joint music log.
    result['specialist'] = copy.deepcopy(info['specialist'])
    return result


def specialist_native_environment(spec, worker_id):
    import isaacgym  # Must precede numpy/torch in every spawned native process.
    import numpy as np
    import torch
    from guitar_learning.training import parallel
    from guitar_learning.skills.specialist_environment import build_specialist_environment
    if not spec.get('headless', True):
        raise ValueError('specialist training requires headless sessions')
    seed = int(spec.get('seed', 7)) + worker_id
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    torch.set_num_threads(1)
    # One environment per process; this binding is private to this worker.
    parallel._compact = specialist_compact
    stage = spec['specialist']
    return build_specialist_environment(spec['config'], Path(spec['out']) / 'environment',
        role=stage['role'], frozen_partner=frozen_partner(stage),
        bundle=spec['bundle'], stage=spec['stage'],
        start_event_index=spec.get('start_event_index', 0), phrase_events=spec.get('phrase_events', 8),
        tempo_scale=spec.get('tempo_scale', 1.), seed=int(spec.get('seed', 7)), worker_id=worker_id,
        music=spec.get('music'), **dict(spec.get('env_kwargs', {})))


class SpecialistPool(Pool):
    def __init__(self, specs, *, specialist, timeout_s=120., worker_factory=None, wait_callback=None):
        specs = copy.deepcopy(specs)
        for spec in specs:
            spec['specialist'] = copy.deepcopy(specialist)
        super().__init__(specs, timeout_s=timeout_s,
            worker_factory=worker_factory or specialist_native_environment, wait_callback=wait_callback)
