"""Spawn-safe joint environment factory and training evidence adapter."""
import copy
import random
from pathlib import Path

from guitar_learning.training.parallel import _compact as base_compact


def compact(env, info, action):
    result = base_compact(env, info, action)
    for key in ('musical_quality', 'timing', 'specialist', 'joint'):
        if key in info: result[key] = copy.deepcopy(info[key])
    if 'episode' not in info:
        quality = result.get('musical_quality', {})
        for hand in ('left', 'right'):
            value = quality.get(hand, {})
            value.get('fretting_state', {}).pop('feature_diagnostics', None)
            value.get('strike', {}).pop('preparation', None)
    return result


def native_environment(spec, worker_id):
    import isaacgym
    import numpy as np
    import torch
    from guitar_learning.training import parallel
    from guitar_learning.runtime.persistent_session import PersistentHeadlessPreparedSession
    from guitar_learning.timing.timing_curriculum import TimingConfig
    from guitar_learning.tool.experiments.joint.environment import build_environment
    if not spec.get('headless', True): raise ValueError('joint training requires headless native scenes')
    seed = int(spec.get('seed', 7))+worker_id
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed); torch.set_num_threads(1)
    parallel._compact = compact
    kwargs = dict(spec.get('env_kwargs', {})); kwargs['session_factory'] = PersistentHeadlessPreparedSession
    return build_environment(spec['config'], Path(spec['out'])/'environment', bundle=spec['bundle'],
        timing=TimingConfig(**spec['timing']), stage=spec['stage'],
        start_event_index=spec.get('start_event_index', 0), phrase_events=spec.get('phrase_events', 8),
        tempo_scale=spec.get('tempo_scale', 1.), seed=int(spec.get('seed', 7)),
        worker_id=worker_id, music=spec.get('music'), **kwargs)
