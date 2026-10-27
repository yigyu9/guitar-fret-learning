"""Spawn v2 skill workers with objective history exposed to the policy."""
import random
from pathlib import Path
from guitar_learning.skills.skill_parallel import SkillPool as BaseSkillPool
from guitar_learning.skills.specialist_parallel import specialist_compact


def skill_native_environment(spec, worker_id):
    import isaacgym  # Must precede NumPy/Torch in every spawned native process.
    import numpy as np
    import torch
    from guitar_learning.training import parallel
    from guitar_learning.skills.skill_environment_v2 import build_skill_environment
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


class SkillPool(BaseSkillPool):
    def __init__(self, *args, worker_factory=None, **kwargs):
        super().__init__(*args, worker_factory=worker_factory or skill_native_environment, **kwargs)
