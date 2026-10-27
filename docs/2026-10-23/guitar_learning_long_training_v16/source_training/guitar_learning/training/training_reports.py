"""Shared stream evidence for current reports and old single-gzip runs."""
import json
import sys
from collections import Counter
from pathlib import Path
from guitar_learning.training.training_log_io import iter_transitions


def run_evidence(out):
    out = Path(out)
    summary_path = out/'training_summary.json'
    if summary_path.is_file():
        summary = json.loads(summary_path.read_text())
        episodes=[]
        if summary.get('logging_detail','diagnostic')=='diagnostic':
            with (out/'episodes.jsonl').open() as stream:
                for line in stream:
                    record=json.loads(line)
                    if record['episode'] is not None:episodes.append(record['episode'])
        return dict(episodes=episodes, logged_transitions=summary['accounting']['logged_transitions'],
            reward_terms=summary['reward_terms'], preparation=summary['preparation'],
            last_quality_by_worker=summary['last_quality_by_worker'],
            episode_stats=summary,episode_records=summary.get('episode_records'),
            accounting=summary['accounting'], open_episodes=summary.get('open_episodes', []),
            evidence_source='streaming_summary_and_episode_records')
    episodes, rewards, last, prep_rewards = [], Counter(), {}, Counter()
    total = prep_steps = nonzero = 0
    for row in iter_transitions(out/'transitions.jsonl.gz'):
        for worker, info in enumerate(row['infos']):
            total += 1
            rewards.update(info.get('reward_terms', {}))
            if 'episode' in info:
                episodes.append(info['episode'])
            if 'musical_quality' in info:
                last[str(worker)] = info['musical_quality']
            if info.get('task_time_s', float('inf')) <= 2.+1e-9:
                prep_steps += 1
                nonzero += info.get('action_summary', {}).get('active_nonzero',
                    any(abs(float(v)) > 1e-8 for v in info.get('debug', {}).get('action', [])))
                prep_rewards.update(info.get('reward_terms', {}))
    valid=[e for e in episodes if e.get('valid',True)]
    stats=dict(completed_episodes=len(valid),
        physical_failure_episodes=sum(e.get('reason')=='terminal_failure' for e in valid))
    for label,key in (('quality','musical_quality'),('specialist','specialist'),('timing','timing')):
        stats[label+'_successful_episodes']=sum(e.get(key,{}).get('stage_success',False) for e in valid)
        stats[label+'_evaluated_episodes']=sum('stage_success' in e.get(key,{}) for e in valid)
    stats['timing_only_successful_episodes']=sum(e.get('timing',{}).get('timing_only_stage_success',
        e.get('timing',{}).get('stage_success',False)) for e in valid)
    return dict(episodes=episodes, logged_transitions=total, reward_terms=dict(rewards),
        episode_stats=stats,episode_records=None,
        preparation=dict(total_logged_transitions=total, first2s_logged_transitions=prep_steps,
            first2s_nonzero_action_transitions=nonzero, first2s_reward_terms=dict(prep_rewards)),
        last_quality_by_worker=last, accounting=None, open_episodes=[],
        evidence_source='legacy_transition_scan')


def finalize_summary(out, producer, label):
    """Do not replace the primary training exception with a summary failure."""
    original = sys.exc_info()[1]
    try:
        return producer(Path(out))
    except BaseException as error:
        if original is None:
            raise
        from guitar_learning.training.recording import write
        detail = dict(type=type(error).__name__, message=str(error),
            primary_exception=type(original).__name__)
        try:
            write(Path(out)/(label+'_summary_error.json'), detail)
        except BaseException:
            pass
        print('[%s] secondary summary error: %s' % (label, error), file=sys.stderr, flush=True)
