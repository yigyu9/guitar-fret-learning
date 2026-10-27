"""Summarize native exploratory LH rollouts without using legacy40% song flags."""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path


def rows(path, warnings):
    if not path.exists():
        return
    with path.open() as handle:
        for number, line in enumerate(handle, 1):
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                if not line.endswith('\n'):
                    warnings.append('%s: ignored unfinished final line%d' % (path.name, number))
                    break
                raise


def mean(values):
    values = [float(value) for value in values if value is not None and math.isfinite(value)]
    return sum(values)/len(values) if values else None


def episode(row):
    value, metrics = row.get('episode') or {}, row.get('metrics') or {}
    transition = value.get('transition', {})
    targets = list(transition.get('per_target', {}).values())
    valid = value.get('valid') is True and metrics.get('valid') is not False
    invalid = value.get('valid') is False or metrics.get('valid') is False
    physical = bool(metrics.get('physical_failure') or transition.get('safety_valid') is False
        or value.get('reason') == 'terminal_failure')
    complete = bool(valid and value.get('reason') == 'timeline_complete' and transition.get('completed') is True)
    ready = value.get('refinement', {}).get('per_target', {}).values()
    return dict(update_index=row['update_index'], valid=valid, complete=complete,
        physical_failure=physical, runtime_invalid=invalid,
        transition_present=bool(transition), success=transition.get('successful') is True,
        clean_hold_fraction=mean([t.get('clean_hold_fraction') for t in targets]),
        all_target_release_pass=all(t.get('release_pass') is True for t in targets) if targets else None,
        release_absent_fraction=mean([t.get('qualified_target_contact_absent_fraction') for t in targets]),
        release_latency_s=mean([t.get('qualified_contact_absent_latency_s') for t in targets]),
        prepare_ready_s=mean([t.get('prepare_ready_s') for t in ready]),
        actual_reward_terms=metrics.get('reward_terms', {}))


def aggregate(values):
    valid = [row for row in values if row['valid']]
    complete = [row for row in values if row['complete'] and row['transition_present']]
    release = [row for row in complete if row['all_target_release_pass'] is not None]
    count = sum(row['success'] for row in complete)
    terms = defaultdict(float)
    for row in values:
        for key, value in row['actual_reward_terms'].items():
            if key.startswith('refinement_'):
                terms[key] += value
    return dict(observed_closed_episodes=len(values), valid_closed_episodes=len(valid), valid_complete_episodes=len(complete),
        physical_failure_episodes=sum(row['physical_failure'] for row in values),
        runtime_invalid_episodes=sum(row['runtime_invalid'] for row in values),
        incomplete_valid_episodes=sum(row['valid'] and not row['complete'] for row in values),
        incomplete_or_unknown_validity_episodes=sum(not row['complete'] and not row['runtime_invalid'] for row in values),
        missing_current_transition=sum(not row['transition_present'] for row in values),
        lh_success_count=count, lh_success_rate_valid_complete=count/len(complete) if complete else None,
        lh_success_rate_valid_closed=count/len(valid) if valid else None,
        lh_success_rate_all_closed=count/len(values) if values else None,
        clean_hold_fraction_mean=mean([row['clean_hold_fraction'] for row in complete]),
        release_pass_rate=sum(row['all_target_release_pass'] for row in release)/len(release) if release else None,
        release_evaluated_episodes=len(release),
        release_absent_fraction_mean=mean([row['release_absent_fraction'] for row in complete]),
        release_latency_s_mean=mean([row['release_latency_s'] for row in complete]),
        prepare_ready_s_mean=mean([row['prepare_ready_s'] for row in complete]),
        actual_refinement_reward_terms_sum=dict(terms))


def nested(value, *keys):
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def sha(path):
    result = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda:handle.read(1024*1024), b''):
            result.update(block)
    return result.hexdigest()


def analyze(training, out):
    warnings, groups, learning, inputs = [], defaultdict(list), {}, []
    settings_path = training/'settings.json'
    if settings_path.exists():
        settings = json.loads(settings_path.read_text())
        if nested(settings, 'transition', 'mode') != 'single_a' or nested(settings, 'transition', 'role') != 'left':
            raise ValueError('this analysis is explicitly for left single_a training')
        inputs.append(settings_path)
    sizes_before = {str(path):path.stat().st_size for path in training.glob('*.jsonl')}
    for row in rows(training/'episodes.jsonl', warnings):
        groups[row['update_index']].append(episode(row))
    for row in rows(training/'learning_metrics.jsonl', warnings):
        learning[row['update_index']] = row
    updates = []
    for path in sorted(training.glob('update_*.json')):
        try:
            value = json.loads(path.read_text())
        except json.JSONDecodeError:
            warnings.append('%s: not yet a complete update JSON' % path.name)
            continue
        index = value['update_index']
        window = learning.get(index, {}).get('learning_window', value.get('learning_window', {}))
        stats = aggregate(groups[index])
        stats.update(update_index=index, optimizer_update=index+1,
            active_std_mean=nested(value, 'diagnostics', 'post_update', 'active_distribution', 'std', 'mean'),
            bc_mse=value.get('bc_mse', nested(value, 'diagnostics', 'rehearsal', 'bc_mse')),
            actor_lr=value.get('actor_lr'), std_lr=value.get('std_lr'),
            analytic_kl=value.get('analytic_kl'), kl_retries=value.get('kl_retries'),
            collection_s=value.get('collection_s'), update_s=value.get('update_s'),
            transitions_in_update=value.get('transitions'),
            first2s_preparation=window.get('preparation'),
            actual_window_reward_terms=window.get('reward_terms'),
            journal=value.get('journal'))
        updates.append(stats)
        inputs.append(path)
    indices = sorted(row['update_index'] for row in updates)
    first, last = set(indices[:8]), set(indices[-8:])
    observed = [row for batch in groups.values() for row in batch]
    report_path = training/'report.json'
    report = json.loads(report_path.read_text()) if report_path.exists() else {}
    latest_journal = report.get('journal') or (updates[-1]['journal'] if updates else None)
    result = dict(schema='guitar_learning.refinement_training_analysis.v1', training=str(training),
        created_utc=datetime.now(timezone.utc).isoformat(),
        scope='exploratory native training episodes, singleA at fixed initial condition, Root fixed; not deterministic evaluation, audio or generalization evidence',
        criteria='episode.transition.successful and native per_target clean hold/release; legacy40% song flags and RHS strict_music excluded',
        completed=report.get('completed'), stopped=report.get('stopped'), failure=report.get('failure'),
        optimizer_updates=report.get('optimizer_updates', len(updates)),
        recorded_update_count=len(updates), observed_episode_update_indices=sorted(groups),
        accounting=report.get('accounting'), latest_journal=latest_journal,
        overall=aggregate(observed),
        first8=dict(update_indices=sorted(first), **aggregate([r for r in observed if r['update_index'] in first])),
        last8=dict(update_indices=sorted(last), **aggregate([r for r in observed if r['update_index'] in last])),
        first_last_windows_overlap=bool(first & last), per_update=updates, warnings=warnings,
        uncommitted_episode_update_indices=sorted(set(groups)-set(indices)))
    for name in ('episodes.jsonl', 'learning_metrics.jsonl', 'report.json'):
        if (training/name).exists():
            inputs.append(training/name)
    result['inputs'] = [dict(path=str(path), sha256=sha(path), bytes=path.stat().st_size) for path in inputs]
    result['live_inputs_advanced_during_analysis'] = any(
        row['path'] in sizes_before and row['bytes'] != sizes_before[row['path']] for row in result['inputs'])
    out.mkdir(parents=True, exist_ok=False)
    (out/'summary.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    plot(updates, out/'learning_curves.png', training.name)
    print(json.dumps(dict(out=str(out), updates=len(updates), **result['overall']), indent=2))


def plot(updates, path, title):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    figure, axes = plt.subplots(3, 1, figsize=(10, 10), sharex=True, constrained_layout=True)
    x = [row['optimizer_update'] for row in updates]
    for key, label in (('lh_success_rate_valid_complete', 'LH episode success'),
                       ('clean_hold_fraction_mean', 'Mean clean hold'), ('release_pass_rate', 'Release pass')):
        axes[0].plot(x, [None if row[key] is None else 100*row[key] for row in updates], marker='.', label=label)
    axes[0].set(ylabel='Complete valid episodes (%)', ylim=(-3, 103))
    axes[0].legend(loc='best')
    for axis, key, label in ((axes[1], 'active_std_mean', 'Active latent Gaussian std'),
                              (axes[2], 'bc_mse', 'Full demonstration BC MSE')):
        axis.plot(x, [row[key] for row in updates], marker='.')
        axis.set_ylabel(label)
        present = [row[key] for row in updates if row[key] is not None]
        if not present:
            axis.text(.5, .5, 'Not present in these logs', transform=axis.transAxes, ha='center')
        elif key == 'bc_mse' and min(present) > 0:
            axis.set_yscale('log')
    for axis in axes:
        axis.grid(alpha=.25)
    axes[-1].set_xlabel('Completed PPO optimizer update (1-based)')
    figure.suptitle(title+'\nExploratory singleA rollouts; fixed initial condition, Root fixed')
    figure.savefig(path, dpi=150)
    plt.close(figure)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--training', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    if not args.training.is_absolute() or not args.out.is_absolute():
        parser.error('--training and --out must be absolute paths')
    analyze(args.training, args.out)
