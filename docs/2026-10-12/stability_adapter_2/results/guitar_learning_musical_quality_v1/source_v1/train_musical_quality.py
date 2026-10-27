"""Train measured fretting/strike quality with unchanged native support."""
import argparse
import copy
import json
import gzip
import os
from pathlib import Path
from unittest.mock import patch
from . import train_actionable_preparation as previous
from .train_timing import timing_compact as base_compact


def settings_document(raw):
    from .musical_quality import metadata
    value = copy.deepcopy(raw)
    declared = value.pop('musical_quality', None)
    if declared is not None and declared != metadata():
        raise ValueError('known musical quality contract required')
    result = previous.settings_document(value)
    if result['actor_initialization_kind'] != 'ppo':
        raise ValueError('musical quality requires own actionable PPO actor initialization')
    result['musical_quality'] = metadata()
    return result


def compact(env, info, action):
    result = base_compact(env, info, action)
    result['musical_quality'] = copy.deepcopy(info['musical_quality'])
    return result


def native_environment(spec, worker_id):
    import isaacgym
    import numpy as np
    import torch
    import random
    # Bind the original logger before the worker installs our compact function.
    from .specialist_parallel import specialist_compact
    from . import parallel
    from .musical_quality_environment import build_environment
    from .timing_curriculum import TimingConfig
    if not spec.get('headless', True):
        raise ValueError('headless quality training required')
    seed = int(spec.get('seed', 7))+worker_id
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed); torch.set_num_threads(1)
    parallel._compact = compact
    return build_environment(spec['config'], Path(spec['out'])/'environment',
        role=spec['specialist']['role'], bundle=spec['bundle'], timing=TimingConfig(**spec['timing']),
        stage=spec['stage'], start_event_index=spec.get('start_event_index', 0),
        phrase_events=spec.get('phrase_events', 8), tempo_scale=spec.get('tempo_scale', 1.),
        seed=int(spec.get('seed', 7)), worker_id=worker_id, music=spec.get('music'),
        **dict(spec.get('env_kwargs', {})))


def run(settings, args):
    from . import actionable_preparation_transfer
    from .musical_quality_transfer import apply_actor_initialization
    existed = args.out.exists()
    with patch.object(previous, 'native_environment', native_environment), \
            patch.object(actionable_preparation_transfer, 'apply_actor_initialization', apply_actor_initialization):
        result = previous.run(settings, args)
    if not existed and (args.out/'transitions.jsonl.gz').is_file():
        from .recording import write
        episodes, rewards, last = [], {}, None
        with gzip.open(args.out/'transitions.jsonl.gz', 'rt') as stream:
            for line in stream:
                for info in json.loads(line)['infos']:
                    last = info['musical_quality']
                    for key, value in info['reward_terms'].items(): rewards[key] = rewards.get(key, 0.)+value
                    if 'episode' in info: episodes.append(info['musical_quality'])
        write(args.out/'musical_quality_report.json', dict(schema='guitar_learning.musical_quality_run.v1',
            episodes=episodes, successful_episodes=sum(row['stage_success'] for row in episodes),
            last_measured_quality=last, reward_terms=rewards,
            scope='new clean contact/prepared crossing criteria; prior success is not inherited'))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--settings', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--resume', type=Path)
    args = parser.parse_args()
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'): os.environ[name] = '1'
    import isaacgym
    run(settings_document(json.loads(args.settings.read_text())), args)


if __name__ == '__main__': main()
