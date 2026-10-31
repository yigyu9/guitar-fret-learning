"""Explicit reward, exploration and rehearsal settings; legacy parsers stay intact."""
import copy
from dataclasses import asdict
import math

SCHEMA = 'guitar_learning.transition_refinement.v1'


def settings_document(raw):
    from ..transition.train import settings_document as original
    from .policy import ExplorationConfig
    from .ppo import RefinementConfig
    value = copy.deepcopy(raw)
    config = value.pop('refinement', None)
    if (not isinstance(config, dict)
            or set(config) != {'schema', 'exploration', 'learning', 'evaluation_mode'}
            or config['schema'] != SCHEMA
            or config['evaluation_mode'] not in ('deterministic', 'stochastic')):
        raise ValueError('explicit refinement schema/exploration/learning/evaluation mode required')
    if (not isinstance(config['exploration'], dict)
            or set(config['exploration']) != {'min_std', 'max_std', 'initial_std'}
            or not isinstance(config['learning'], dict)
            or set(config['learning']) != {'bc_weight', 'bc_batch_size', 'std_lr'}):
        raise ValueError('complete explicit exploration and rehearsal configuration required')
    exploration = ExplorationConfig(**config['exploration'])
    learning = RefinementConfig(**config['learning'])
    if value.get('initial_std') != exploration.initial_std:
        raise ValueError('initial_std must explicitly match the new exploration contract')
    # Validate all legacy run fields without inheriting the old policy's floor.
    value['initial_std'] = max(math.exp(-5), exploration.initial_std)
    parsed = original(value)
    parsed['initial_std'] = exploration.initial_std
    parsed['min_available_memory_gib'] = max(6., parsed['min_available_memory_gib'])
    if (parsed['transition']['role'] != 'left'
            or parsed['initialization']['mode'] != 'bc'
            or parsed['initial_std'] != exploration.initial_std):
        raise ValueError('BC-initialized left-hand refinement with matching initial_std required')
    parsed['refinement'] = dict(schema=SCHEMA, exploration=asdict(exploration),
        learning=asdict(learning), evaluation_mode=config['evaluation_mode'])
    return parsed
