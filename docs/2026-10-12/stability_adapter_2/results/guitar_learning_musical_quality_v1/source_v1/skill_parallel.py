"""Process-private hand-internal curriculum worker dispatch."""
import copy
import random
from pathlib import Path
from .parallel import Pool
from .specialist_parallel import specialist_compact
from .skill_settings import SKILLS


def skill_native_environment(spec, worker_id):
    import isaacgym  # Must precede NumPy/Torch in each spawned native worker.
    import numpy as np
    import torch
    from . import parallel
    from .skill_environment import build_skill_environment
    if not spec.get('headless', True):
        raise ValueError('skill training requires headless sessions')
    seed = int(spec.get('seed', 7))+worker_id
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    torch.set_num_threads(1)
    parallel._compact = specialist_compact
    return build_skill_environment(spec['config'], Path(spec['out'])/'environment',
        role=spec['specialist']['role'], skill=spec['skill'],
        bundle=spec['bundle'], stage=spec['stage'],
        start_event_index=spec.get('start_event_index', 0),
        phrase_events=spec.get('phrase_events', 8), tempo_scale=spec.get('tempo_scale', 1.),
        seed=int(spec.get('seed', 7)), worker_id=worker_id,
        music=spec.get('music'), **dict(spec.get('env_kwargs', {})))


class SkillPool(Pool):
    def __init__(self, specs, *, specialist, skill, timeout_s=120.,
                 worker_factory=None, wait_callback=None):
        role = specialist.get('role')
        if role not in SKILLS or skill not in SKILLS[role]:
            raise ValueError('valid hand-internal skill required')
        other = 'right' if role == 'left' else 'left'
        if specialist.get(other+'_checkpoint') is not None:
            raise ValueError('frozen partner is not part of hand-internal training')
        specs = copy.deepcopy(specs)
        for spec in specs:
            spec['specialist'] = copy.deepcopy(specialist)
            spec['skill'] = skill
        super().__init__(specs, timeout_s=timeout_s,
            worker_factory=worker_factory or skill_native_environment, wait_callback=wait_callback)
