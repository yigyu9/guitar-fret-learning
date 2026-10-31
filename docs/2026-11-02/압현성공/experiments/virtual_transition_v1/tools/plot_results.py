"""원본 평가 집계에서 음별 달성과 유지 시간을 그린다. 대표 궤적과 혼합하지 않는다."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True, type=Path)
    args = parser.parse_args()
    rows = list(json.loads((args.run/'summary.json').read_text()).values())
    if not rows:
        return
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.font_manager import FontProperties
    font = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    rows.sort(key=lambda r: (r['seed'], r['updates'], r['condition']))
    labels = [f"{r['condition']} / seed{r['seed']} / {r['updates']}" for r in rows]
    counts = np.asarray([[n['success_count'] for n in r['metrics']['notes']] for r in rows])
    clean = np.asarray([[n['mean_clean_s'] for n in r['metrics']['notes']] for r in rows])
    fig, axes = plt.subplots(1, 3, figsize=(15, max(4.5, .4*len(rows)+1.5)),
        gridspec_kw={'width_ratios': [1.4, 1, 1]}, constrained_layout=True)
    for ax, data, title, maximum in ((axes[0], counts, '음별 달성 수 / 32 (실패 포함)', 32),
        (axes[1], clean, '음별 평균 압현 유지 (초)', 1.5)):
        im = ax.imshow(data, vmin=0, vmax=maximum, cmap='YlGnBu', aspect='auto')
        ax.set_xticks(range(4)); ax.set_xticklabels(['A1 / F6', 'B1 / F7', 'A2 / F6', 'B2 / F7'])
        ax.set_yticks(range(len(rows))); ax.set_yticklabels(labels if ax is axes[0] else ['']*len(rows))
        ax.set_title(title, fontproperties=font)
        for i in range(len(rows)):
            for j in range(4):
                value = f'{int(data[i,j])}' if maximum == 32 else f'{data[i,j]:.2f}'
                ax.text(j, i, value, ha='center', va='center', color='white' if data[i,j]>.65*maximum else 'black')
        fig.colorbar(im, ax=ax, shrink=.65)
    all_counts = [r['metrics']['full_sequence_success_count'] for r in rows]
    y = np.arange(len(rows))
    axes[2].barh(y, all_counts, color=['#527ab5' if r['condition']=='E0' else '#d58b3b' for r in rows])
    axes[2].set_ylim(len(rows)-.5, -.5); axes[2].set_xlim(0, 36)
    axes[2].set_yticks(y); axes[2].set_yticklabels(['']*len(rows))
    axes[2].set_title('전체 ABAB 달성 / 32', fontproperties=font)
    for i, value in enumerate(all_counts): axes[2].text(value+.4, i, str(value), va='center')
    fig.suptitle('중지 두 프렛 전환: 동일 초기 분포 최초 32에피소드 평가', fontproperties=font)
    fig.savefig(args.run/'comparison.png', dpi=150)
    plt.close(fig)
    evidence = {r['checkpoint']: r['metrics']['input_sha256'] for r in rows}
    (args.run/'figure_provenance.json').write_text(json.dumps(dict(
        input_evidence=evidence, scope='32 first episodes per block; no env0-only measures',
        note_order=['A1 F6', 'B1 F7', 'A2 F6', 'B2 F7']), ensure_ascii=False, indent=2)+'\n')


if __name__ == '__main__':
    main()
