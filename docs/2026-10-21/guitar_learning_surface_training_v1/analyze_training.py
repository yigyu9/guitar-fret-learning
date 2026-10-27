"""Stream committed training logs into fresh final or --prefix N analysis outputs.

No simulation, CUDA inference, optimizer, or fixed-policy evaluation is run.
One logged update is retained at a time; persistent summaries contain no episode
ledgers. Prefix outputs never claim final completion or fixed-policy improvement.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import math
from pathlib import Path
import json

import numpy as np
from verify_training import read, lines, require, finite, digest, torch

FINGERS = ('index', 'middle', 'ring', 'pinky')
CAUSES = ('geometry_time', 'loaded_target_time', 'body_load_time', 'higher_time', 'lower_time', 'assignment_time')


class Summary:
    def __init__(self, notes=False):
        self.count = 0
        self.total, self.reasons, self.failure_times = Counter(), Counter(), Counter()
        self.environments = set()
        self.first = self.last = self.failure_min = self.failure_max = None
        self.notes = {key: np.zeros(67) for key in ('left', 'near_done', 'contact_done', 'clean_fraction',
            'exposed', 'surface_min_sum', *CAUSES)} if notes else None

    def add(self, episode, features, update, note_values):
        self.count += 1
        self.total.update(features)
        self.environments.add(episode['env_id'])
        self.first = update if self.first is None else min(self.first, update)
        self.last = update if self.last is None else max(self.last, update)
        if episode['reason'] == 'terminal_failure':
            time = episode['task_time_s']
            self.failure_times[str(math.floor(time))] += 1
            self.reasons.update(episode['failure_reasons'])
            self.failure_min = time if self.failure_min is None else min(self.failure_min, time)
            self.failure_max = time if self.failure_max is None else max(self.failure_max, time)
        if self.notes is not None:
            for key, value in note_values.items():
                self.notes[key] += value

    def result(self, schedule):
        mean = {key: value/self.count for key, value in self.total.items()} if self.count else {}
        failures = self.total['physical_failure']
        result = dict(episodes=self.count, distinct_environments=len(self.environments),
            update_first=self.first, update_last=self.last, mean=mean,
            failure_time_s=dict(mean=self.total['failure_time_sum_s']/failures if failures else None,
                minimum=self.failure_min, maximum=self.failure_max, histogram_1s=dict(self.failure_times)),
            failure_reason_occurrences=dict(self.reasons),
            mean_surface_min_m_when_exposed=self.total['surface_min_sum']/self.total['exposed_notes'] if self.total['exposed_notes'] else None)
        if self.notes is not None:
            result['notes'] = [dict(target_id=target['target_id'], finger=target['finger'],
                string_1based=target['string']+1, fret=target['fret'], ended_episode_denominator=self.count,
                exposed_episode_count=int(self.notes['exposed'][index]),
                surface_min_mean_m=self.notes['surface_min_sum'][index]/self.notes['exposed'][index] if self.notes['exposed'][index] else None,
                means={key: float(value[index]/self.count) for key, value in self.notes.items()
                       if key not in ('surface_min_sum', 'exposed')}) for index, target in enumerate(schedule)]
        return result


def episode_features(episode, lengths):
    ledger = episode['left_note_ledger']['values']
    require(all(len(value) == 67 for value in ledger.values()), 'Expected67-note ledger')
    exposed = np.asarray(ledger['exposure_time']) > 0
    clean = np.minimum(np.asarray(ledger['clean'])/lengths, 1.)
    safe = episode['reason'] == 'timeline_complete' and episode['left_curriculum']['full_safe']
    failed = episode['reason'] == 'terminal_failure'
    values = dict(full_safe=float(safe), physical_failure=float(failed),
        failure_time_sum_s=episode['task_time_s'] if failed else 0.,
        task_time_s=episode['task_time_s'], achieved_notes=episode['song']['left_success_count'],
        clean_fraction=float(clean.mean()), reward=episode['reward'], cost=episode['cost'],
        original_cost=episode['cost_components']['original_physics_and_terminal'],
        remaining_failure_cost=episode['cost_components']['remaining_song_failure'],
        end_progress=episode['left_curriculum']['progress'], wrist_reach=episode['left_curriculum']['reach_fraction'],
        exposed_notes=int(exposed.sum()), surface_min_sum=float(np.asarray(ledger['surface_min'])[exposed].sum()))
    for name, metrics in zip(FINGERS, episode['left_curriculum']['finger_metrics']):
        for key in ('near_fraction', 'contact_fraction', 'success_fraction', 'clean_fraction'):
            values[name+'.'+key] = metrics[key]
    for key in CAUSES:
        values[key+'.mean_s_per_note'] = math.fsum(ledger[key])/67.
        values[key+'.positive_note_fraction'] = float((np.asarray(ledger[key]) > 0).mean())
    for key, value in episode['reward_components'].items():
        values['reward_component.'+key] = value
    note_values = {key: np.asarray(ledger[key], dtype=float) for key in ('left', 'near_done', 'contact_done', *CAUSES)}
    note_values.update(clean_fraction=clean, exposed=exposed.astype(float),
                       surface_min_sum=np.where(exposed, ledger['surface_min'], 0.))
    return values, note_values, safe


def update_features(row):
    diagnostics = row['diagnostics']
    actor = diagnostics['minibatches']['actor_accepted']['sample_weighted_mean']
    value = diagnostics['minibatches']['value']['sample_weighted_mean']
    std = diagnostics['post_update']['active_distribution']['std']
    return dict(update_index=row['update_index'], mean_reward=row['mean_reward'], mean_cost=row['mean_cost'],
        actor_lr=row['actor_lr'], cost_weight=row['cost_weight'], analytic_kl=row['analytic_kl'],
        max_attempted_kl=row['max_attempted_kl'], kl_retries=row['kl_retries'],
        actor_grad_preclip_mean=actor.get('grad_norm_pre_clip'), value_grad_preclip_mean=value.get('grad_norm_pre_clip'),
        std_min=std['min'], std_mean=std['mean'], std_max=std['max'],
        action_saturation=diagnostics['post_update']['active_distribution']['collected_action_saturation_fraction'],
        collection_s=row['collection_s'], update_s=row['update_s'],
        progress=row['left_curriculum']['progress'], recent_safe_fraction=row['left_curriculum']['recent_safe_fraction'],
        reward_components=row['reward_component_means'])


def checkpoint_summary(path):
    payload = torch.load(path, map_location='cpu', weights_only=False)
    std = payload['model']['log_std'][:33].clamp(-5, 2).exp()
    require(bool(torch.isfinite(std).all()), 'Nonfinite checkpoint exploration std')
    return dict(path=str(path.resolve()), sha256=digest(path), optimizer_updates=payload['updates'],
        reward_schema=payload['identity']['architecture']['contract']['reward']['schema'],
        active_latent_std=dict(minimum=float(std.min()), mean=float(std.mean()), maximum=float(std.max())),
        curriculum_progress=float(payload['model']['left_curriculum_state'][0]),
        scope='Checkpoint parameters only; no policy inference or song evaluation')


def complete_memory_lines(path):
    # Live memory telemetry can have an unfinished tail after the committed prefix.
    with path.open() as stream:
        for line in stream:
            if not line.endswith('\n'):
                break
            yield json.loads(line)


def memory_summary(run, limit):
    caches, releases = [], Counter()
    for row in complete_memory_lines(run/'events.jsonl'):
        index = row.get('update_index')
        if index is not None and index >= limit:
            break
        if row.get('event') == 'cuda_cache_release':
            releases[row['reason']] += 1
            if row['reason'] == 'optimizer_boundary':
                after = row['after']
                caches.append(dict(update_index=index, free_GiB=after['free_bytes']/1024**3,
                    reserved_GiB=after['reserved_bytes']/1024**3, allocated_GiB=after['allocated_bytes']/1024**3))
    ram = []
    for row in complete_memory_lines(run/'resources.jsonl'):
        index = row.get('update_index')
        if index is not None and index >= limit:
            break
        ram.append(dict(update_index=index, elapsed_s=row['elapsed_s'], free_GiB=row['available_memory_bytes']/1024**3,
                        parent_RSS_GiB=row['parent_memory']['rss_current_bytes']/1024**3))
    base = caches[0]['free_GiB']+caches[0]['reserved_GiB'] if caches else None
    for row in caches:
        row['estimated_nonTorch_growth_GiB'] = base-row['free_GiB']-row['reserved_GiB']
    return dict(cache_boundaries=caches, RAM_samples=ram, cache_release_reasons=dict(releases),
        minimum_post_cache_free_GiB=min((r['free_GiB'] for r in caches), default=None),
        minimum_RAM_free_GiB=min((r['free_GiB'] for r in ram), default=None),
        scope='Logged samples only; free+reserved residual does not identify native allocation ownership or prove an SDK leak')


def analyze(run, phase, prefix=None):
    settings, contract = read(run/'settings.json'), read(run/'training_contract.json')
    report = read(run/'report.json') if (run/'report.json').is_file() else None
    if prefix is None:
        require(report is not None, 'Final report missing; use --prefix N for a committed live snapshot')
        limit = len(report['updates'])
        mode = 'final_completed' if report.get('completed') is True else 'final_failed_or_stopped'
        if mode == 'final_completed':
            require(report['failure'] is None and report['optimizer_updates'] == limit == settings['updates'], 'Final report budget/completion mismatch')
    else:
        require(0 < prefix <= settings['updates'], 'Prefix must be a positive committed update count within the budget')
        limit, mode = prefix, 'committed_prefix'
    require(limit > 0, 'No committed updates to analyze')
    schedule = contract['task']['provenance']['song']['schedule']
    require(len(schedule) == 67, 'Expected67-note schedule')
    lengths = np.asarray([t['end_s']-t['onset_s'] for t in schedule])
    groups, update_buckets, curve, changes = {}, defaultdict(list), [], []
    previous = None
    metrics = iter(lines(run/'learning_metrics.jsonl'))
    for index in range(limit):
        row = next(metrics, None)
        require(row is not None and row['update_index'] == index, 'Requested committed prefix is not fully available')
        require(row['journal']['committed'] == (index+1)*settings['horizon']*settings['num_envs'], 'Uncommitted update')
        finite(row)
        point = update_features(row)
        curve.append(point)
        if point['progress'] != previous:
            changes.append(dict(update_index=index, committed_updates=index+1,
                committed_transitions=(index+1)*settings['horizon']*settings['num_envs'],
                **{key: row['left_curriculum'][key] for key in ('progress', 'stage', 'weights', 'recent_safe_fraction', 'recent_fingers')}))
            previous = point['progress']
        for width in (100, 250):
            update_buckets[(width, index//width)].append(point)
        for episode in row['completed_episodes']:
            features, note_values, safe = episode_features(episode, lengths)
            cohorts = ('all_ended', 'full_safe' if safe else 'physical_failure')
            for cohort in cohorts:
                names = ['overall/'+cohort] + ['updates_%d/%04d_%04d/%s' % (width, index//width*width,
                    min((index//width+1)*width, limit)-1, cohort) for width in (100, 250)]
                for name in names:
                    if name not in groups:
                        groups[name] = Summary(notes=name.startswith('overall/'))
                    groups[name].add(episode, features, index, note_values)
    compact_updates = {}
    scalar_keys = [key for key in curve[0] if key not in ('update_index', 'reward_components')]
    for (width, group), points in update_buckets.items():
        key = '%d/%04d_%04d' % (width, group*width, min((group+1)*width, limit)-1)
        mean = {name: float(np.mean([p[name] for p in points if p[name] is not None]))
                if any(p[name] is not None for p in points) else None for name in scalar_keys}
        compact_updates[key] = dict(updates=len(points), mean=mean,
            actor_lr_min=min(p['actor_lr'] for p in points), actor_lr_max=max(p['actor_lr'] for p in points),
            max_attempted_kl=max(p['max_attempted_kl'] for p in points),
            reward_component_means={k: math.fsum(p['reward_components'][k] for p in points)/len(points)
                                    for k in points[0]['reward_components']})
    checkpoints = [run/'initial.pt']
    candidates = sorted((int(p.stem.split('_')[-1])+1, p) for p in run.glob('checkpoint_*.pt')
                        if int(p.stem.split('_')[-1])+1 <= limit)
    if mode == 'final_completed':
        checkpoints.append(run/'final.pt')
    elif candidates:
        checkpoints.append(candidates[-1][1])
    model_summaries = [checkpoint_summary(path) for path in checkpoints]
    require(all(row['optimizer_updates'] <= limit for row in model_summaries), 'Checkpoint is beyond the selected snapshot')
    require(all(row['reward_schema'] == contract['reward']['schema'] for row in model_summaries), 'Checkpoint reward contract mismatch')
    if mode == 'final_completed':
        require(model_summaries[-1]['optimizer_updates'] == limit, 'Final checkpoint update count differs from the completed run')
    verification_path = phase/'training_verification.json'
    verification = read(verification_path) if prefix is None and verification_path.is_file() else None
    if verification is not None:
        require(verification['completed'] is True and verification['committed_updates'] == limit and
                verification['final_checkpoint_sha256'] == model_summaries[-1]['sha256'], 'Verification/checkpoint mismatch')
    summaries = {}
    for name, group in sorted(groups.items()):
        summaries[name] = group.result(schedule)
        if name.startswith('updates_'):
            first, last = (int(v) for v in name.split('/')[1].split('_'))
            summaries[name].update(bucket_first=first, bucket_last=last)
    return dict(schema='guitar_learning.surface_training_analysis.v1', generated_at_utc=datetime.now(timezone.utc).isoformat(),
        mode=mode, run=str(run.resolve()), selected_committed_updates=limit, last_update_index=limit-1,
        committed_transitions=limit*settings['horizon']*settings['num_envs'],
        final_completed=mode == 'final_completed', final_execution_verified=verification is not None,
        execution_verification=verification,
        settings=settings, training_contract_sha256=digest(run/'training_contract.json'),
        source_manifest_sha256=digest(phase/'training_source_manifest.json'),
        curriculum_changes=changes, update_buckets=compact_updates, update_curve=curve,
        episode_groups=summaries,
        checkpoint_parameters=model_summaries, memory=memory_summary(run, limit),
        limitations=[
            'These are on-policy training collections. Fixed initial/final1024-policy evaluations are separate outputs and are not mixed into these cohorts.',
            'All-ended/failed cohorts keep the fixed67-note denominator, including future notes not reached before a failure. Full-safe cohorts contain all1969 ticks.',
            'Episode progress is its end progress; curriculum may change during the song. Reward means across stages are not a common fixed-weight performance score.',
            '256 recent songs and repeated environments are not independent seeds, generalization, or a controlled causal comparison.',
            'Geometry/body-load/target-load and competing-fret/finger times can overlap; their sums are not disjoint failure probabilities.',
            'Surface-min statistics exclude exposure_time=0;10mm near is approach only, not contact, calibrated pressure or acoustic success.',
            'Gradients are sample-weighted accepted-minibatch pre-clip norms. Std is latent Gaussian std, not joint radians.',
            'Prefix snapshots only use their requested committed update rows; they do not establish final success, whole-file CRC, or final GPU cleanup.',
            'Per-update curves and bounded aggregates are retained; whole-run episode ledgers are streamed, not accumulated.'
        ])


def plot(value, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    curve = value['update_curve']
    x = [row['update_index']+1 for row in curve]
    subtitle = '%s: %d committed updates; training collections' % (value['mode'], value['selected_committed_updates'])
    groups = value['episode_groups']
    def centers(rows):
        return [(g['bucket_first']+g['bucket_last'])/2+1 for g in rows]
    fig, axes = plt.subplots(2, 3, figsize=(16, 8))
    for cohort in ('all_ended', 'full_safe', 'physical_failure'):
        selected = [g for name, g in groups.items() if name.startswith('updates_100/') and name.endswith('/'+cohort)]
        selected.sort(key=lambda g: g['update_first'])
        axes[0, 0].plot(centers(selected),
                        [g['mean']['achieved_notes'] for g in selected], marker='.', label=cohort)
        axes[0, 1].plot(centers(selected),
                        [100*g['mean']['clean_fraction'] for g in selected], marker='.', label=cohort)
    axes[0, 0].set(title='Achieved notes /67,100-update ended-song cohorts', ylim=(0, 67))
    axes[0, 1].set(title='Mean clean-time fraction /67 notes', ylabel='Percent', ylim=(0, 100))
    ended = [g for name, g in groups.items() if name.startswith('updates_100/') and name.endswith('/all_ended')]
    ended.sort(key=lambda g: g['update_first'])
    for key in ('full_safe', 'physical_failure'):
        axes[0, 2].plot(centers(ended),
                        [100*g['mean'][key] for g in ended], marker='.', label=key)
    axes[0, 2].set(title='Outcome / all ended songs', ylabel='Percent', ylim=(0, 100))
    safe = [g for name, g in groups.items() if name.startswith('updates_100/') and name.endswith('/full_safe')]
    safe.sort(key=lambda g: g['update_first'])
    for ax, field, title in ((axes[1, 0], 'near_fraction', 'Near10mm achievement: full-safe songs'),
                              (axes[1, 1], 'contact_fraction', 'Contact achievement: full-safe songs'),
                              (axes[1, 2], 'success_fraction', 'Note achievement: full-safe songs')):
        for name in FINGERS:
            ax.plot(centers(safe),
                    [100*g['mean'][name+'.'+field] for g in safe], marker='.', label=name)
        ax.set(title=title, ylabel='Percent', ylim=(0, 100))
        if not safe:
            ax.text(.5, .5, 'No full-safe ended songs in this snapshot', transform=ax.transAxes, ha='center')
    for ax in axes.flat:
        ax.set_xlabel('Optimizer update'); ax.grid(alpha=.25); ax.legend(fontsize=8)
    fig.suptitle(subtitle); fig.tight_layout()
    for suffix in ('png', 'svg'):
        fig.savefig(output/('training.'+suffix), dpi=150)
    plt.close(fig)
    fig, axes = plt.subplots(3, 2, figsize=(12, 11))
    for key in ('mean_reward', 'mean_cost'):
        axes[0, 0].plot(x, [p[key] for p in curve], label=key)
    axes[0, 0].set_title('Per-transition collection means')
    for key in ('progress', 'recent_safe_fraction'):
        axes[0, 1].plot(x, [p[key] for p in curve], label=key)
    axes[0, 1].set_title('Curriculum and recent256-song safety')
    for key in ('actor_grad_preclip_mean', 'value_grad_preclip_mean'):
        axes[1, 0].plot(x, [p[key] for p in curve], label=key)
    axes[1, 0].set_yscale('log'); axes[1, 0].axhline(value['settings']['ppo']['max_grad_norm'], color='gray', ls='--', label='clip threshold')
    for key in ('analytic_kl', 'max_attempted_kl'):
        axes[1, 1].plot(x, [p[key] for p in curve], label=key)
    axes[1, 1].axhline(value['settings']['ppo']['target_kl'], color='gray', ls='--', label='target KL')
    axes[2, 0].plot(x, [p['actor_lr'] for p in curve], label='actor LR'); axes[2, 0].set_yscale('log')
    twin = axes[2, 0].twinx(); twin.plot(x, [p['cost_weight'] for p in curve], color='tab:red', label='cost weight'); twin.set_ylabel('Cost weight')
    for key in ('std_min', 'std_mean', 'std_max'):
        axes[2, 1].plot(x, [p[key] for p in curve], label=key)
    axes[2, 1].set_title('Active33 latent Gaussian std')
    for ax in axes.flat:
        ax.set_xlabel('Optimizer update'); ax.grid(alpha=.25); ax.legend(fontsize=8)
    handles, labels = axes[2, 0].get_legend_handles_labels()
    extra_handles, extra_labels = twin.get_legend_handles_labels()
    axes[2, 0].legend(handles+extra_handles, labels+extra_labels, fontsize=8)
    fig.suptitle(subtitle); fig.tight_layout()
    for suffix in ('png', 'svg'):
        fig.savefig(output/('ppo.'+suffix), dpi=150)
    plt.close(fig)
    fig, axes = plt.subplots(3, 1, figsize=(12, 9))
    caches, ram = value['memory']['cache_boundaries'], value['memory']['RAM_samples']
    for key in ('free_GiB', 'reserved_GiB', 'allocated_GiB'):
        axes[0].plot([r['update_index']+1 for r in caches], [r[key] for r in caches], label=key)
    axes[0].set_title('GPU after optimizer-boundary cache release')
    axes[1].plot([r['update_index']+1 for r in caches], [r['estimated_nonTorch_growth_GiB'] for r in caches], label='free+reserved residual growth estimate')
    axes[1].set_title('Not an attribution of SDK/native allocation ownership')
    for key in ('free_GiB', 'parent_RSS_GiB'):
        axes[2].plot([r['elapsed_s'] for r in ram], [r[key] for r in ram], label=key)
    axes[2].set_xlabel('Elapsed wall seconds')
    for ax in axes:
        ax.set_ylabel('GiB'); ax.grid(alpha=.25); ax.legend(fontsize=8)
    for ax in axes[:2]:
        ax.set_xlabel('Optimizer update')
    fig.suptitle(subtitle); fig.tight_layout()
    for suffix in ('png', 'svg'):
        fig.savefig(output/('memory.'+suffix), dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--prefix', type=int, help='Read exactly N committed updates; never claim final completion')
    parser.add_argument('--out', type=Path, help='New output directory; existing outputs are never overwritten')
    args = parser.parse_args()
    phase = args.phase.resolve()
    output = args.out or phase/('analysis_final' if args.prefix is None else 'analysis_prefix_%06d' % args.prefix)
    require(not output.exists(), 'Use a new analysis output directory')
    torch.set_num_threads(1)
    result = analyze(phase/'train1024_large_2000', phase, args.prefix)
    output.mkdir(parents=True, exist_ok=False)
    plot(result, output)
    with (output/'analysis.json').open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps(dict(mode=result['mode'], updates=result['selected_committed_updates'], output=str(output))))


if __name__ == '__main__':
    main()
