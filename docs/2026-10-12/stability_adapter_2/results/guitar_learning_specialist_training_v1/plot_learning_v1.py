"""Static scientific plot of observed training, not a held-out policy test."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

PHASE = Path(__file__).resolve().parent
COLORS = dict(left='#246caa', right='#c26324')


def metric(rows, name):
    return [np.nan if row['metrics'][name]['mean'] is None else 1000*row['metrics'][name]['mean'] for row in rows]


def main():
    analysis = json.loads((PHASE/'learning_analysis_v1.json').read_text())
    fig, axes = plt.subplots(2, 3, figsize=(14, 8.6))
    for hand in ('left', 'right'):
        role = analysis['roles'][hand]
        rows = [row for row in role['per_update'] if row['committed']]
        x = np.array([row['update_index']+1 for row in rows])
        color = COLORS[hand]
        ax = axes[0, 0 if hand == 'left' else 1]
        key = 'left_press_to_onset_m' if hand == 'left' else 'right_sweep_m'
        y = metric(rows, key)
        ax.plot(x, y, '-o', color=color, markersize=3, linewidth=1.4)
        ax.set_title('Left: distal-origin target distance' if hand == 'left' else 'Right: pick-to-guide distance')
        ax.set_ylabel('Distance (mm)')
        ax.text(.02, .97, '[press, onset] samples' if hand == 'left' else 'onset +/-80 ms sweep samples',
                transform=ax.transAxes, va='top', fontsize=9)
        axes[0, 2].plot(x, np.cumsum([row['episode_stage_successes'] for row in rows]), '-o',
                       label=hand.capitalize(), color=color, markersize=3)
        axes[1, 0].plot(x, [row['episode_reward_mean'] for row in rows], '-o',
                       label=hand.capitalize()+' (own objective)', color=color, markersize=3)
        axes[1, 1].plot(x, [row['mean_cost_per_transition'] for row in rows], '-o',
                       label=hand.capitalize(), color=color, markersize=3)
        updates = [json.loads(p.read_text()) for p in sorted((PHASE/(hand+'_run_v1')).glob('update_*.json'))]
        axes[1, 2].plot(x, [row['analytic_kl'] for row in updates], '-o',
                       label=hand.capitalize(), color=color, markersize=3)
    axes[0, 2].set_title('Cumulative safe stage successes')
    axes[0, 2].set_ylabel('Completed successful episodes')
    axes[0, 2].set_ylim(bottom=-.1)
    axes[1, 0].set_title('Return of episodes ending in each update')
    axes[1, 0].set_ylabel('Episode reward (different objectives)')
    axes[1, 1].set_title('Mean stability cost per control tick')
    axes[1, 1].set_ylabel('Integrated cost / tick')
    axes[1, 1].set_ylim(bottom=0.)
    axes[1, 2].set_title('Accepted policy KL')
    axes[1, 2].set_ylabel('Analytic Gaussian KL')
    axes[1, 2].axhline(.02, color='#666666', linestyle='--', linewidth=1, label='KL limit 0.02')
    axes[1, 2].set_ylim(bottom=0.)
    for ax in axes.flat:
        ax.set_xlabel('Completed PPO updates')
        ax.grid(alpha=.22)
    for ax in (axes[0, 2], *axes[1]):
        ax.legend(fontsize=8, loc='best')
    fig.suptitle('Separate left/right specialist training: one fixed note\nOn-policy observations; distance proxies are not physical contact or acoustic success', fontsize=13)
    fig.text(.5, .012, 'N=4 per hand, H=128, seed=7; reward scales differ between hands. Full-episode stage success requires safe timeline completion.',
             ha='center', fontsize=9)
    fig.tight_layout(rect=(0, .035, 1, .93))
    for suffix in ('png', 'pdf'):
        target = PHASE/('training_progress_v1.'+suffix)
        if target.exists():
            raise FileExistsError(str(target))
        fig.savefig(target, dpi=170)
    plt.close(fig)


if __name__ == '__main__':
    main()
