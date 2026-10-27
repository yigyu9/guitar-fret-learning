"""Verify completed GPU logs and summarize episodes with bounded memory.

Accepts compact v2 and historical v1 records. Full gzip CRC/EOF and raw rollout
accounting are checked; a missing/deleted log is not reconstructed or certified.
Checkpoint hashes verify stored bytes, not optimizer payload compatibility.
"""
import argparse
import json
import math
from pathlib import Path

from guitar_learning.training.gpu_log_records import (
    METRICS_SCHEMA, iter_learning_metrics, iter_gpu_transitions, episode_summary)
from guitar_learning.training.recording import digest


def require(condition, message):
    if not condition:
        raise ValueError(message)


def _numbers(row, key, count):
    values = row[key]
    require(len(values) == count, key+' batch size')
    require(all(type(x) in (int, float) and math.isfinite(x) for x in values), key+' finite numbers')
    return values


def inspect(run):
    run = Path(run)
    report = json.loads((run/'report.json').read_text())
    settings = report['settings']
    require(report['completed'] and report['failure'] is None and report['lifecycle_verified'],
        'Only completed, lifecycle-verified runs can be certified')
    require(not any(report[k] for k in ('changed_inputs', 'missing_import_pins', 'cleanup_errors')),
        'Input or cleanup audit failed')
    raw_status = {}
    raw = iter(iter_gpu_transitions(run, diagnostics=raw_status))
    count = completed = safe = success = 0
    reward_sum = cost_sum = left_sum = right_sum = 0.
    finger_success = [0., 0., 0., 0.]
    finger_targets = [0, 0, 0, 0]
    for index, metrics in enumerate(iter_learning_metrics(run)):
        require(metrics['update_index'] == index, 'Nonsequential update index')
        require(metrics['transitions'] == settings['horizon']*settings['num_envs'], 'Update transition count')
        episodes, rewards, costs = [], [], []
        for tick in range(settings['horizon']):
            row = next(raw, None)
            require(row is not None and row['update_index'] == index and row['tick_in_update'] == tick,
                'Missing/misordered raw rollout row')
            rewards.append(math.fsum(_numbers(row, 'reward', settings['num_envs'])))
            cost = _numbers(row, 'cost', settings['num_envs'])
            require(all(x >= 0 for x in cost), 'Negative raw cost')
            costs.append(math.fsum(cost))
            for key in ('terminated', 'truncated'):
                require(len(row[key]) == settings['num_envs'] and all(type(x) is bool for x in row[key]),
                    'Invalid '+key+' batch')
            ids = [episode['env_id'] for episode in row['episodes']]
            done = [i for i, flags in enumerate(zip(row['terminated'], row['truncated'])) if any(flags)]
            require(sorted(ids) == done, 'Episode count/IDs differ from terminal flags')
            for episode in row['episodes']:
                env = episode['env_id']
                # Both physical failure and the end of the finite song are
                # true MDP terminals in the GPU environment.
                require(episode['reason'] in ('terminal_failure', 'timeline_complete') and
                    row['terminated'][env] and not row['truncated'][env],
                    'Episode reason differs from termination flag')
            episodes.extend(row['episodes'])
        require(episodes == metrics['completed_episodes'], 'Update and raw canonical episode mismatch')
        if 'episode_summary' in metrics:
            require(metrics['episode_summary'] == episode_summary(episodes), 'Episode aggregate mismatch')
        transitions = metrics['transitions']
        for key, values in (('reward', rewards), ('cost', costs)):
            require(math.isclose(math.fsum(values)/transitions, metrics['mean_'+key], rel_tol=1e-5, abs_tol=1e-6),
                'Raw '+key+' differs from rollout mean')
        require(index < len(report['updates']) and report['updates'][index]['update_index'] == index,
            'Report update mismatch')
        require(metrics['optimizer_updates'] == report['updates'][index]['optimizer_updates'],
            'Optimizer update mismatch')
        count += transitions
        reward_sum += math.fsum(rewards)
        cost_sum += math.fsum(costs)
        for episode in episodes:
            completed += 1
            song = episode['song']
            safe += not song['safety_invalidated']
            success += bool(song['stage_success'])
            left_sum += song['left_success_count']
            right_sum += song['right_success_count']
            for i, finger in enumerate(episode.get('left_curriculum', {}).get('finger_metrics', [])):
                finger_success[i] += finger['success_fraction']*finger['target_count']
                finger_targets[i] += finger['target_count']
    require(next(raw, None) is None and raw_status['complete'], 'Unexpected raw tail or incomplete gzip')
    require((index+1 if 'index' in locals() else 0) == len(report['updates']), 'Report update count')
    require(count == report['transitions'] == report['journal']['committed'], 'Committed transition count')
    require(all(report['journal'][k] == count for k in ('sampled', 'logged', 'durable')), 'Journal accounting')
    require(report['journal']['discarded'] == report['journal']['unresolved_sampled'] == 0 and
        report['journal']['closed'] and not report['journal']['failed'], 'Journal close/discard audit')
    require(completed == report['completed_episodes'], 'Completed episode count')
    manifest = run/'checkpoint_manifest.jsonl'
    if report.get('logging_schema') == METRICS_SCHEMA or 'checkpoints' in report:
        require(manifest.is_file(), 'Missing checkpoint manifest for compact GPU run')
    checkpoint_count = checkpoint_bytes = 0
    if manifest.is_file():
        from guitar_learning.training.gpu_log_records import iter_json_lines
        names = set()
        for entry in iter_json_lines(manifest):
            name = entry['path']
            require(Path(name).name == name and name not in names, 'Invalid/duplicate checkpoint name')
            names.add(name)
            path = run/name
            require(path.stat().st_size == entry['bytes'] and digest(path) == entry['sha256'],
                'Checkpoint hash/bytes mismatch: '+name)
            checkpoint_count += 1
            checkpoint_bytes += entry['bytes']
        require({'initial.pt', 'final.pt'} <= names, 'Missing initial/final checkpoint')
        require(checkpoint_count == report['checkpoints']['count'] and
            checkpoint_bytes == report['checkpoints']['bytes'], 'Checkpoint manifest totals')
    return dict(schema='guitar_learning.gpu_log_inspection.v1', verified=True,
        transitions=count, completed_episodes=completed, safe_episodes=safe, successful_episodes=success,
        mean_reward=reward_sum/count if count else None, mean_cost=cost_sum/count if count else None,
        mean_left_success_count=left_sum/completed if completed else None,
        mean_right_success_count=right_sum/completed if completed else None,
        finger_success_fraction=[s/n if n else None for s, n in zip(finger_success, finger_targets)],
        checkpoints=dict(count=checkpoint_count, bytes=checkpoint_bytes) if manifest.is_file() else None,
        raw_crc=raw_status, scope='ended training episodes, including failures; not fixed-policy evaluation or acoustic success')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.run), indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
