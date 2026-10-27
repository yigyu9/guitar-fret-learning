"""Plot recorded native data; no simulation or generated pose frames."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from analyze_body_rotation import relative_rotvec


def main():
    phase = Path(__file__).resolve().parent
    fig, axes = plt.subplots(3, 1, figsize=(10, 10), constrained_layout=True)
    analyses = []
    for folder, label, color in (('native_baseline', '4 iterations (current)', '#2563eb'),
                                  ('native_solver16', '16 iterations (diagnostic)', '#ea580c')):
        root = phase/folder
        metadata = json.loads((root/'capture_metadata.json').read_text())
        with np.load(str(root/'case_005.npz')) as capture:
            z = metadata['joint_names'].index('LH:pinky1_z')
            t = np.arange(241)/60
            axes[0].plot(t, capture['q'][285:, z], label=label, color=color)
            if folder == 'native_baseline':
                axes[0].plot(t, capture['target'][285:, z], '--', color='#111827', label='Command target')
            y = relative_rotvec(capture['body_state'], metadata['body_names'], 'pinky')[:, 1]
            axes[1].plot(t, y[285:], label=label, color=color)
        filename = 'baseline_analysis.json' if folder == 'native_baseline' else 'solver16_analysis.json'
        analyses.append(json.loads((phase/filename).read_text()))
    axes[0].set_title('Pinky base z response with x target = 1.56 rad; no finger contact')
    axes[0].set_ylabel('Native z angle (rad)')
    axes[0].legend(loc='upper right')
    axes[1].set_ylabel('Palm-relative log y (rad)')
    axes[1].set_xlabel('Seconds from z pulse start')
    for ax in axes[:2]:
        for t in (1, 2, 3):
            ax.axvline(t, color='#9ca3af', linewidth=.7)
        ax.grid(alpha=.2)
    free = [0, 1, 3, 4, 5]
    x = np.arange(len(free))
    for i, (analysis, color, label) in enumerate(zip(analyses, ('#2563eb', '#ea580c'), ('4 iterations', '16 iterations'))):
        axes[2].bar(x+(i-.5)*.35, [analysis['cases'][j]['z_response_fraction'] for j in free], .35, color=color, label=label)
    axes[2].axhline(1, color='#111827', linestyle='--', linewidth=.8)
    axes[2].set_xticks(x)
    axes[2].set_xticklabels(['Ring x=0', 'Ring x=.8', 'Pinky x=0', 'Pinky x=.8', 'Pinky x=1.56'])
    axes[2].set_ylabel('Actual / allowed z movement')
    axes[2].set_ylim(0, 1.12)
    axes[2].legend()
    axes[2].set_title('Contact-free cases only; distinct conditioning histories')
    fig.suptitle('Native N6 diagnostic: more solver iterations did not remove the tracking residual', fontsize=13)
    path = phase/'tracking_comparison.png'
    if path.exists():
        raise FileExistsError(path)
    fig.savefig(str(path), dpi=160)
    plt.close(fig)
    print('Saved', path.name)


if __name__ == '__main__':
    main()
