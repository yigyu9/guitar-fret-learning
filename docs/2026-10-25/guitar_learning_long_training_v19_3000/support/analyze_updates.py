"""Read-only update/checkpoint analysis; no inference or physics execution."""
import gc
import hashlib
import json
from pathlib import Path

import torch

PHASE = Path(__file__).resolve().parents[1]
RUN = PHASE/'train3000'


def finite(value):
    if isinstance(value, torch.Tensor):
        assert torch.isfinite(value).all()
    elif isinstance(value, dict):
        for child in value.values():
            finite(child)
    elif isinstance(value, (tuple, list)):
        for child in value:
            finite(child)


def main():
    torch.set_num_threads(1)
    rows = [json.loads(line) for line in (RUN/'learning_metrics.jsonl').open()]
    assert [r['update_index'] for r in rows] == list(range(3000))
    assert sum(r['transitions'] for r in rows) == 98_304_000
    groups = {}
    for label, start, stop in [('first100', 0, 100), ('last100', 2900, 3000),
            ('last250', 2750, 3000), ('last500', 2500, 3000)]+[
            ('bin100_%04d'%i, i, i+100) for i in range(0, 3000, 100)]+[
            ('bin250_%04d'%i, i, i+250) for i in range(0, 3000, 250)]:
        subset = rows[start:stop]
        count = sum(r['episode_summary']['count'] for r in subset)
        safe = sum(r['episode_summary']['timeline_complete'] for r in subset)
        achieved = sum(r['episode_summary']['count']*(r['episode_summary']['mean_left_success_count'] or 0)
                       for r in subset)
        groups[label] = dict(start=start, stop_exclusive=stop, episodes=count,
            safe=safe, safe_fraction=safe/count if count else None,
            mean_achieved=achieved/count if count else None)
    changes, previous = [], 0.
    for row in rows:
        value = row['left_curriculum']['progress']
        if value != previous:
            changes.append(dict(update=row['optimizer_updates'], before=previous, after=value))
            previous = value
    checkpoints = []
    contract = json.loads((RUN/'training_contract.json').read_text())
    for entry in map(json.loads, (RUN/'checkpoint_manifest.jsonl').open()):
        payload = torch.load(RUN/entry['path'], map_location='cpu', weights_only=False)
        finite(payload)
        assert payload['updates'] == entry['optimizer_updates']
        assert payload['identity']['architecture']['contract'] == contract
        assert payload['model']['left_curriculum_state'].shape == (3331,)
        checkpoints.append(dict(path=entry['path'], updates=payload['updates'],
            all_tensors_finite=True, progress=float(payload['model']['left_curriculum_state'][0]),
            sha256=entry['sha256']))
        del payload
        gc.collect()
    assert [c['updates'] for c in checkpoints] == list(range(0, 3001, 250))
    manifest = json.loads((PHASE/'training_source_manifest.json').read_text())['source']
    root = PHASE.parents[2]
    assert all(hashlib.sha256((root/k).read_bytes()).hexdigest() == v for k, v in manifest.items())
    result = dict(scope='Online training completed episodes, including failures; no fixed-policy evaluation',
        groups=groups, curriculum_changes=changes, final_curriculum=rows[-1]['left_curriculum'],
        kl_retries=[dict(update=r['optimizer_updates'], retries=r['kl_retries'], actor_lr=r['actor_lr'],
            max_attempted_kl=r['max_attempted_kl']) for r in rows if r['kl_retries']],
        maximum_accepted_kl=max(r['analytic_kl'] for r in rows),
        final_actor_lr=rows[-1]['actor_lr'],
        final_distribution=rows[-1]['diagnostics']['post_update']['active_distribution'],
        checkpoints=checkpoints, current_source_sha_verified=len(manifest))
    (PHASE/'analysis/updates.json').write_text(json.dumps(result, indent=2)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    bins = [groups['bin100_%04d'%i] for i in range(0, 3000, 100)]
    x = [(r['start']+r['stop_exclusive'])/2 for r in bins]
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    axes[0].plot(x, [r['mean_achieved'] for r in bins], marker='o', markersize=3)
    axes[0].set(ylabel='Achieved notes / 67', ylim=(0, 67),
        title='v19: online training episodes (100-update bins; failures included)')
    axes[1].plot(x, [100*r['safe_fraction'] for r in bins], color='tab:green')
    axes[1].axhline(90, color='gray', linestyle='--', label='Curriculum safety threshold')
    axes[1].set(ylabel='Safe timeline completion (%)', ylim=(0, 100))
    axes[1].legend(loc='lower left', fontsize=8)
    axes[2].plot([r['optimizer_updates'] for r in rows],
                 [r['left_curriculum']['progress'] for r in rows], color='tab:orange')
    axes[2].set(ylabel='Curriculum progress', xlabel='PPO update', ylim=(0, 2.05))
    for ax in axes:
        ax.grid(alpha=.25)
    fig.tight_layout()
    fig.savefig(PHASE/'analysis/learning_curve.png', dpi=150)
    plt.close(fig)
    print(json.dumps({k: groups[k] for k in ('first100', 'last100', 'last250')}, indent=2))


if __name__ == '__main__':
    main()
