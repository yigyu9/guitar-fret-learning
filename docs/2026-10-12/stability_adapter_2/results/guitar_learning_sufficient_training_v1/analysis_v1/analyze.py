"""Stream saved summaries; never load transition gzip or mutate execution inputs."""
import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path


def read(path):
    return json.loads(path.read_text()) if path.is_file() else None


def lines(path):
    if not path.is_file():
        return
    with path.open() as stream:
        for index, line in enumerate(stream, 1):
            if not line.endswith('\n'):
                break  # A live writer may not have completed the final row.
            try:
                yield json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError('%s:%s: invalid complete row' % (path, index)) from error


def mean(values):
    values = [v for v in values if isinstance(v, (int, float)) and math.isfinite(v)]
    return sum(values) / len(values) if values else None


def bounds(values):
    values = [v for v in values if isinstance(v, (int, float)) and math.isfinite(v)]
    return {'min': min(values), 'max': max(values), 'mean': mean(values)} if values else None


def episode_row(episode, metrics=None):
    metrics = metrics or {}
    transition = episode.get('transition', {})
    targets = list(transition.get('per_target', {}).values())
    refinement = episode.get('refinement', {})
    prepared = list(refinement.get('per_target', {}).values())
    song = episode.get('song', {})
    return {
        'success': transition.get('successful') is True,
        'physical_failure': metrics.get('physical_failure') is True or
                            transition.get('safety_valid') is False,
        'hold_pass': bool(targets) and all(t.get('hold_pass') is True for t in targets),
        'release_pass': bool(targets) and all(t.get('release_pass') is True for t in targets),
        'hold_fraction': mean([t.get('clean_hold_fraction') for t in targets]),
        'release_absent_fraction': mean([t.get('qualified_target_contact_absent_fraction') for t in targets]),
        'ready_s': sum(t.get('prepare_ready_s', 0) for t in prepared),
        'wrong_press_s': song.get('wrong_press_s'),
        'missing_press_s': song.get('missing_press_s'),
        'first_clean_s': metrics.get('first_clean_actual_policy_s'),
        'reward': episode.get('reward'), 'cost': episode.get('cost'),
        'complete': metrics.get('complete', episode.get('reason') == 'timeline_complete'),
    }


def summarize(rows):
    if not rows:
        return {'episodes': 0}
    result = {'episodes': len(rows)}
    for key in ('success', 'hold_pass', 'release_pass', 'physical_failure', 'complete'):
        result[key + '_count'] = sum(row[key] for row in rows)
        result[key + '_fraction'] = result[key + '_count'] / len(rows)
    for key in ('hold_fraction', 'release_absent_fraction', 'ready_s', 'wrong_press_s',
                'missing_press_s', 'first_clean_s', 'reward', 'cost'):
        result[key] = bounds([row[key] for row in rows])
    return result


def runtime_evidence(path):
    data = read(path)
    return {
        'path': str(path), 'present': data is not None,
        'recorded_pass': bool(data and data.get('completed') is True and
                              data.get('anomaly') is None and
                              data.get('state_mutations') is False and
                              data.get('failure') is None and data.get('checks', 0) > 0),
        'record': data,
    }


def report_evidence(path):
    data = read(path)
    if data is None:
        return {'path': str(path), 'present': False, 'recorded_pass': False}
    blockers = {key: data[key] for key in ('failure', 'cleanup_errors', 'missing_import_pins',
                'original_source_parity_errors', 'changed_inputs', 'missing_worker_audits',
                'worker_audit_read_errors', 'guard_violations', 'worker_failures',
                'physical_flags_errors') if data.get(key)}
    return {'path': str(path), 'present': True,
            'recorded_pass': data.get('completed') is True and not blockers,
            'completed': data.get('completed'), 'stopped': data.get('stopped'), 'blockers': blockers}


def training_summary(folder):
    updates = []
    for path in sorted(folder.glob('update_*.json')):
        data = read(path)
        diag = data.get('diagnostics', {})
        post = diag.get('post_update', {})
        advantages = diag.get('advantages', {})
        rw = advantages.get('reward_raw', {}).get('std')
        cw = advantages.get('weighted_cost_raw', {}).get('std')
        window = data.get('learning_window', {})
        updates.append({
            'update_index': data['update_index'], 'transitions': data['transitions'],
            'actor_lr': data.get('actor_lr'), 'std_lr': data.get('std_lr'),
            'analytic_kl': data.get('analytic_kl'), 'kl_retries': data.get('kl_retries'),
            'bc_mse': data.get('bc_mse'), 'collection_s': data.get('collection_s'),
            'update_s': data.get('update_s'), 'journal': data.get('journal'),
            'std_mean': post.get('active_distribution', {}).get('std', {}).get('mean'),
            'cost_reward_advantage_std_ratio': cw / rw if rw else None,
            'reward_value_loss': data.get('reward_value_loss'),
            'cost_value_loss': data.get('cost_value_loss'),
            'reward_explained_variance': post.get('critics', {}).get('reward', {}).get('explained_variance'),
            'cost_explained_variance': post.get('critics', {}).get('cost', {}).get('explained_variance'),
            'episodes': window.get('completed_episodes', 0),
            'successes': window.get('quality_successful_episodes', 0),
            'reward_terms': window.get('reward_terms'),
        })
    workers, by_update = defaultdict(list), defaultdict(list)
    all_rows = []
    for item in lines(folder / 'episodes.jsonl'):
        row = episode_row(item['episode'], item.get('metrics'))
        row['worker_id'] = item['worker_id']
        row['update_index'] = item['update_index']
        all_rows.append(row)
        workers[item['worker_id']].append(row)
        by_update[item['update_index']].append(row)
    for update in updates:
        update['episode_summary'] = summarize(by_update[update['update_index']])
    count = min(16, len(updates) // 2)
    windows = {}
    if count:
        for name, subset in [('first', updates[:count]), ('last', updates[-count:])]:
            ids = {u['update_index'] for u in subset}
            windows[name] = {'updates': sorted(ids),
                             **summarize([row for row in all_rows if row['update_index'] in ids])}
    resource_values = defaultdict(list)
    for item in lines(folder / 'resources.jsonl'):
        for key in ('available_memory_bytes', 'elapsed_s'):
            if item.get(key) is not None:
                resource_values[key].append(item[key])
        for key in ('rss_current_bytes', 'pss_current_bytes', 'rss_peak_bytes'):
            value = item.get('parent_memory', {}).get(key)
            if value is not None:
                resource_values['parent_' + key].append(value)
    report = read(folder / 'report.json') or {}
    last = updates[-1] if updates else {}
    journal = last.get('journal') or {}
    accounting = report.get('accounting') or {
        key + '_transitions': journal.get(key) for key in ('sampled', 'logged', 'durable', 'committed', 'discarded')}
    diagnostics = {key: bounds([u.get(key) for u in updates]) for key in (
        'actor_lr', 'analytic_kl', 'kl_retries', 'std_mean', 'bc_mse',
        'reward_value_loss', 'cost_value_loss', 'reward_explained_variance',
        'cost_explained_variance', 'cost_reward_advantage_std_ratio', 'collection_s', 'update_s')}
    return {
        'folder': str(folder), 'finalized_report': report_evidence(folder / 'report.json'),
        'runtime': runtime_evidence(folder.with_name(folder.name + '_runtime_json_audit.json')),
        'status': 'finalized' if report else 'progress_only',
        'accounting': accounting, 'recorded_updates': len(updates),
        'global_optimizer_updates': report.get('optimizer_updates'),
        'recorded_update_transition_sum': sum(u['transitions'] for u in updates),
        'all_episodes': summarize(all_rows), 'per_worker': {str(k): summarize(v) for k, v in workers.items()},
        'nonoverlap_windows': windows, 'diagnostic_ranges': diagnostics,
        'resource_stream_extrema': {k: bounds(v) for k, v in resource_values.items()},
        'final_resource_summary': report.get('resources'), 'wall_s': report.get('wall_s'),
        'updates': updates,
        'scope': 'Saved summaries only; no transition gzip replay. Live last rows are provisional.',
    }


def evaluation_summary(folder):
    result = read(folder / 'result.json')
    runtime = runtime_evidence(folder.with_name(folder.name + '_runtime_json_audit.json'))
    rows, invalid = [], []
    for path in sorted(folder.glob('case_*/result.json')):
        data = read(path)
        blockers = {k: data.get(k) for k in ('failure', 'cleanup_error', 'forbidden_calls', 'missing_import_pins') if data.get(k)}
        valid = all(data.get(k) is True for k in ('completed', 'source_unchanged', 'physical_flags_ok')) and not blockers
        if not valid:
            invalid.append({'case': path.parent.name, 'blockers': blockers})
        row = episode_row(data.get('episode', {}))
        spec = read(path.parent / 'case_spec.json') or {}
        row.update(case=path.parent.name, seed=spec.get('seed'), recorded_case_valid=valid)
        rows.append(row)
    parent_pass = bool(result and all(result.get(k) is True for k in
                       ('completed', 'source_unchanged', 'physical_flags_ok')) and
                       not any(result.get(k) for k in ('failure', 'cleanup_error', 'forbidden_calls', 'missing_import_pins')))
    return {'folder': str(folder), 'finalized_recorded_pass': parent_pass and runtime['recorded_pass'] and not invalid,
            'runtime': runtime, 'parent': result, 'invalid_cases': invalid,
            'summary': summarize(rows), 'cases': rows,
            'scope': 'Seeds vary policy RNG; same prepared pose. No initial-pose diversity or generalization claim.'}


def plot_training(training, path):
    if not training['updates']:
        return
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    updates = training['updates']
    x = [u['update_index'] + 1 for u in updates]
    fig, axes = plt.subplots(3, 2, figsize=(12, 9), sharex=True)
    def plot(axis, key, label, scale=None):
        axis.plot(x, [u.get(key) for u in updates], label=label, linewidth=1.5)
        if scale:
            axis.set_yscale(scale)
        axis.grid(alpha=.25)
        axis.legend(loc='best')
    rates = [u['successes'] / u['episodes'] if u['episodes'] else None for u in updates]
    axes[0, 0].plot(x, rates, alpha=.3, label='Per update (8 episodes)')
    width = min(8, len(updates))
    axes[0, 0].plot(x, [mean(rates[max(0, i-width+1):i+1]) for i in range(len(rates))], label='%s-update mean' % width)
    axes[0, 0].set_ylim(-.02, 1.02)
    axes[0, 0].set_ylabel('LH single-note success fraction')
    axes[0, 0].legend()
    plot(axes[0, 1], 'analytic_kl', 'Accepted analytic KL', 'log')
    plot(axes[1, 0], 'actor_lr', 'Actor learning rate', 'log')
    plot(axes[1, 1], 'std_mean', 'Mean latent action std')
    plot(axes[2, 0], 'bc_mse', 'BC rehearsal MSE', 'log')
    plot(axes[2, 1], 'cost_reward_advantage_std_ratio', 'Weighted cost / reward advantage std')
    for axis in axes[-1]:
        axis.set_xlabel('Additional update in this run')
    fig.suptitle('Single-note refinement: saved update summaries (%s)' % training['status'])
    fig.tight_layout()
    fig.savefig(str(path), dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--training', type=Path)
    parser.add_argument('--evaluation', action='append', default=[], help='label=absolute_folder')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = {'schema': 'guitar_learning.sufficient_training_analysis.v1',
              'helper_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'evidence_limit': 'Checks recorded final reports, not a repeat of native raw auditing.',
              'training': training_summary(args.training) if args.training else None,
              'evaluations': {key: evaluation_summary(Path(value)) for key, value in
                              [item.split('=', 1) for item in args.evaluation]}}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    if result['training']:
        plot_training(result['training'], args.out.with_suffix('.png'))


if __name__ == '__main__':
    main()
