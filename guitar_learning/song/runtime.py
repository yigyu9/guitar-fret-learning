"""Spawn-safe whole-song hand worker, compact evidence and streaming summary."""
import copy
import json
from pathlib import Path
import random
from guitar_learning.training.parallel import _compact as base_compact


def compact(env, info, action):
    result = base_compact(env, info, action)
    for key in ('song', 'musical_quality', 'reward_shaping', 'left_curriculum'):
        if key in info: result[key] = copy.deepcopy(info[key])
    if 'episode' not in info:
        for key in ('per_note', 'targets', 'events'): result.get('song', {}).pop(key, None)
        result.get('left_curriculum', {}).pop('per_note', None)
    return result


def native_environment(spec, worker_id):
    import isaacgym
    import numpy as np
    import torch
    from guitar_learning.training import parallel
    from guitar_learning.runtime.persistent_session import PersistentHeadlessPreparedSession
    from guitar_learning.song.hand_environment import build_environment
    if not spec.get('headless', True):
        raise ValueError('song training requires headless native workers')
    seed = int(spec.get('seed', 7))+worker_id
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed); torch.set_num_threads(1)
    parallel._compact = compact
    kwargs = dict(spec.get('env_kwargs', {}))
    kwargs['session_factory'] = PersistentHeadlessPreparedSession
    if 'finger_control' in spec['song']:
        from guitar_learning.core.control import validate_profile
        from guitar_learning.runtime.finger_session import FlexibleLeftFingerSession
        if spec['specialist']['role'] != 'left':
            raise ValueError('flexible finger workers require the left hand')
        validate_profile(spec['song']['finger_control'])
        kwargs['session_factory'] = FlexibleLeftFingerSession
    return build_environment(spec['config'], Path(spec['out'])/'environment',
        bundle=spec['bundle'], song=spec['song'], role=spec['specialist']['role'], **kwargs)


def summarize_run(out):
    from guitar_learning.training.training_log_io import write
    from guitar_learning.training.training_log_io import run_evidence
    out = Path(out)
    report = json.loads((out/'report.json').read_text())
    data = run_evidence(out); stats = data['episode_stats']
    successes, evaluated = stats['quality_successful_episodes'], stats['quality_evaluated_episodes']
    full_safe = 0
    path = out/'episodes.jsonl'
    if path.is_file():
        with path.open() as stream:
            for line in stream:
                episode = json.loads(line).get('episode')
                if episode and episode.get('valid') is True:
                    song = episode.get('song', {})
                    full_safe += int(episode['reason'] == 'timeline_complete'
                        and song.get('completed') is True and song.get('safety_invalidated') is False)
    result = dict(schema='guitar_learning.hand_song_run.v1', completed=report['completed'],
        failure=report['failure'], stopped=report['stopped'],
        role=report['settings']['specialist']['role'], song=report['settings']['song_training'],
        completed_episodes=stats['completed_episodes'],
        full_safe_episodes=full_safe,
        whole_song_successful_episodes=successes, evaluated_episodes=evaluated,
        success_rate=successes/evaluated if evaluated else None,
        physical_failure_episodes=stats['physical_failure_episodes'],
        episode_records=data['episode_records'], last_quality_by_worker=data['last_quality_by_worker'],
        reward_terms=data['reward_terms'], accounting=data['accounting'], open_episodes=data['open_episodes'],
        evidence_source=data['evidence_source'],
        scope='selected-hand full-song contact/geometric timing; joint/strict music remain separate diagnostics; partial trajectories are not whole-song successes')
    if 'left_curriculum' in report['settings'].get('song', {}):
        updates=sorted(out.glob('update_*.json'))
        result['left_curriculum'] = (json.loads(updates[-1].read_text())['left_curriculum']
            if updates else dict(schema=report['settings']['song']['left_curriculum']['schema'],
                                 state='no completed PPO update'))
    write(out/'song_report.json', result)
    return result
