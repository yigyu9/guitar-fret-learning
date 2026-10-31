"""Spawn-safe refinement factory; the native scene/controller are unchanged."""
import copy
from pathlib import Path
import random

from guitar_learning.tool.experiments.transition.worker import compact as original_compact


def compact(env, info, action):
    result = original_compact(env, info, action)
    result['refinement'] = copy.deepcopy(info['refinement'])
    result['legacy_reward_terms'] = copy.deepcopy(info['legacy_reward_terms'])
    return result


def native_environment(spec, worker_id):
    import isaacgym
    import numpy as np
    import torch
    from guitar_learning.training import parallel
    from guitar_learning.runtime.persistent_session import PersistentHeadlessPreparedSession
    from guitar_learning.tool.experiments.transition_refinement.environment import build_environment
    if not spec.get('headless', True):
        raise ValueError('refinement workers must be headless')
    seed = spec.get('seed', 7)+worker_id
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed); torch.set_num_threads(1)
    parallel._compact = compact
    kwargs = dict(spec.get('env_kwargs', {}))
    kwargs['session_factory'] = PersistentHeadlessPreparedSession
    return build_environment(spec['config'], Path(spec['out'])/'environment',
        bundle=spec['bundle'], transition=spec['transition'], **kwargs)
