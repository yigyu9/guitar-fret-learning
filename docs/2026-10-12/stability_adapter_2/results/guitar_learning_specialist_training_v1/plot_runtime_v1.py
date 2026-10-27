"""Worker process memory and shared host availability on their observed clocks."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

PHASE = Path(__file__).resolve().parent


def main():
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.5))
    for hand, color in (('left', '#246caa'), ('right', '#c26324')):
        rows = [json.loads(line) for line in (PHASE/(hand+'_run_v1')/'resources.jsonl').read_text().splitlines()]
        usable = [row for row in rows if len(row.get('workers', [])) == 4 and
                  all(w['alive'] and all(w['memory'][k] is not None for k in ('rss_current_bytes', 'pss_current_bytes')) for w in row['workers'])]
        times = [row['elapsed_s']/60 for row in usable]
        for field, style, label in (('rss_current_bytes', '-', 'RSS'), ('pss_current_bytes', '--', 'PSS')):
            values = [sum(w['memory'][field] for w in row['workers'])/2**30 for row in usable]
            axes[0].plot(times, values, style, color=color, label=hand.capitalize()+' '+label, linewidth=1.5)
        if hand == 'left':
            axes[1].plot([row['elapsed_s']/60 for row in rows], [row['available_memory_bytes']/2**30 for row in rows], color='#337a4a', label='Host MemAvailable (one series)')
    axes[0].set_title('Sum of four worker processes per hand')
    axes[0].set_ylabel('Current process memory (GiB)')
    axes[0].set_ylim(bottom=0)
    axes[1].set_title('Shared host memory; hand runs overlap')
    axes[1].set_ylabel('Available host memory (GiB)')
    axes[1].axhline(4, color='#aa3333', linestyle='--', label='Protection floor: 4 GiB')
    axes[1].set_ylim(bottom=0)
    for ax in axes:
        ax.set_xlabel('Elapsed run time (minutes)')
        ax.grid(alpha=.22)
        ax.legend(loc='best', fontsize=8)
    fig.suptitle('Specialist training resource observations', fontsize=13)
    fig.text(.5, .015, 'RSS includes shared pages; PSS apportions them. Native startup is included. Host availability is shared and must not be summed across runs.', ha='center', fontsize=8)
    fig.tight_layout(rect=(0, .045, 1, .92))
    for suffix in ('png', 'pdf'):
        target = PHASE/('runtime_progress_v1.'+suffix)
        if target.exists():
            raise FileExistsError(str(target))
        fig.savefig(target, dpi=170)
    plt.close(fig)


if __name__ == '__main__':
    main()
