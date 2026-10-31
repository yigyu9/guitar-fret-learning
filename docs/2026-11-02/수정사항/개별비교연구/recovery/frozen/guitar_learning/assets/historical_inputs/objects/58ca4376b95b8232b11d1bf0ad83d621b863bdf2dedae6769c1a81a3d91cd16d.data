"""Shared hand-quality worker construction, compact logs and run summary."""
import copy
import json
from pathlib import Path
from guitar_learning.timing.recording import timing_compact as base_compact


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
    from guitar_learning.skills.specialist_parallel import specialist_compact
    from guitar_learning.training import parallel
    from guitar_learning.quality.musical_quality_environment import build_environment
    from guitar_learning.timing.timing_curriculum import TimingConfig
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



def summarize_run(out):
    from guitar_learning.training.recording import write
    from guitar_learning.training.training_reports import run_evidence
    data = run_evidence(out)
    report = json.loads((out/'report.json').read_text())
    episodes = [episode['musical_quality'] for episode in data['episodes']]
    stats=data['episode_stats']
    successes=stats['quality_successful_episodes']
    evaluated=stats['quality_evaluated_episodes']
    last = data['last_quality_by_worker']
    result = dict(schema='guitar_learning.musical_quality_run.v2',
        completed=report['completed'], failure=report['failure'], stopped=report['stopped'],
        episodes=episodes,episode_records=data['episode_records'],completed_episodes=stats['completed_episodes'],
        successful_episodes=successes,success_rate=successes/evaluated if evaluated else None,
        evaluated_episodes=evaluated,timing_only_successful_episodes=stats['timing_only_successful_episodes'],
        last_quality_by_worker=last, last_measured_quality=next(iter(last.values())) if len(last)==1 else None,
        reward_terms=data['reward_terms'], accounting=data['accounting'], open_episodes=data['open_episodes'],
        evidence_source=data['evidence_source'],
        scope='measured prefix may include transitions discarded before PPO; current role quality, not timing-only or acoustic success')
    write(out/'musical_quality_report.json', result)
    return result

