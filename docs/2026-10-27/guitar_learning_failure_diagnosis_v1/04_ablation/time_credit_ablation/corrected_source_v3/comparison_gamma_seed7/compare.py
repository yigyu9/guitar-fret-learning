"""Compare the two completed, same-geometry seed7 experiments."""
import csv
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
BASE = HERE.parent
RUNS = {
    'baseline': 'baseline_original_gamma_seed7',
    'A': 'A_time_discount_30s_seed7',
}


def read(path):
    return json.loads(path.read_text())


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.font_manager import FontProperties

    if (HERE/'comparison.json').exists():
        raise FileExistsError('Completed comparison already exists')
    rows, acceptance, inputs = [], {}, {}
    for label, name in RUNS.items():
        run = BASE/name
        completed = read(run/'comparison_completed.json')
        assert completed['completed'] and len(completed['stages']) == 11
        assert read(BASE/(name+'_launcher.json'))['returncode'] == 0
        acceptance[label] = read(run/'analysis/acceptance.json')
        for update in (0, 50, 100, 150, 200, 250, 300):
            folder = 'evaluation_initial_policy' if update == 0 else 'evaluation_%06d' % update
            result = read(run/folder/'evaluation.json')
            assert result['assigned_quotas'] == [1]*128 and len(result['episodes']) == 128
            s = result['summary']
            rows.append(dict(condition=label, update=update,
                achieved=sum(bool(e['achieved']) for e in result['episodes']), **s))
        for control in ('policy', 'zero', 'random', 'reference'):
            inputs.setdefault(control, {})[label] = read(
                run/('evaluation_initial_'+control)/'evaluation.json')['summary']
    assert all(v['baseline'] == v['A'] for v in inputs.values())
    comparability = read(HERE/'initial_comparability.json')
    assert comparability['all_initial_tensors_exact']
    result = dict(rows=rows, acceptance=acceptance, initial_control_summaries=inputs,
        initial_comparability=comparability,
        scope='one seed, fixed guitar, teacher-supported middle finger single note; no free-guitar/full-song or naturalness claim')
    with (HERE/'comparison.json').open('x') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
    with (HERE/'performance.csv').open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    font = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    plt.rcParams['font.family'] = font.get_name()
    plt.rcParams['axes.unicode_minus'] = False
    fig, axes = plt.subplots(1, 3, figsize=(14, 4), sharey=True)
    for label, caption in (('baseline', '기준 할인 .99'), ('A', '시간 할인 변경 A')):
        subset = [r for r in rows if r['condition'] == label]
        for ax, key, title in zip(axes,
                ('achieved_fraction', 'mean_clean_fraction', 'mean_audible_wrong_fraction'),
                ('압현 달성', '압현 유지', '오압현')):
            ax.plot([r['update'] for r in subset], [100*r[key] for r in subset], marker='o', label=caption)
            ax.set_title(title)
            ax.set_xlabel('학습 반복')
            ax.grid(alpha=.25)
            ax.set_ylim(-3, 103)
    axes[0].set_ylabel('비율 (%) — 실패 포함 128시도')
    axes[0].legend()
    fig.tight_layout()
    fig.savefig(HERE/'comparison.png', dpi=140)
    plt.close(fig)
    text = ['# 같은 기하에서 시간 할인만 변경한 비교', '',
        '고정 기타·팔 안내·중지1음·large128/H32/300·seed7이다. 각 평가는 실패를 포함한128환경 첫시도다.', '',
        '| 반복 | 기준 달성/128 | A 달성/128 | 기준 유지 / 오압현 | A 유지 / 오압현 |',
        '|---:|---:|---:|---:|---:|']
    for update in (0, 50, 100, 150, 200, 250, 300):
        a, b = [next(r for r in rows if r['condition'] == label and r['update'] == update)
                for label in ('baseline', 'A')]
        text.append('| %d | %d | %d | %.2f%% / %.2f%% | %.2f%% / %.2f%% |' %
            (update, a['achieved'], b['achieved'], 100*a['mean_clean_fraction'],
             100*a['mean_audible_wrong_fraction'], 100*b['mean_clean_fraction'],
             100*b['mean_audible_wrong_fraction']))
    text += ['', '연속 통과 평가쌍: 기준 %s / A %s.' %
        (acceptance['baseline']['passing_pairs'], acceptance['A']['passing_pairs']), '',
        '실제 초기 모델73개 텐서가 동일했고 설정은 gamma/PBRS gamma 및 실험 표기만 달랐다. 초기 policy/zero/random/reference 네 조건의 성과 요약도 동일하다. 비용 할인·비용 계수·관절 제어·물리·음 일정은 유지했다.', '',
        '단일 seed의 비교이며 기본 채택·자유 기타·전곡·적절한 접촉 힘을 입증하지 않는다. 기준선에서 확인된 높은 접촉 합력은 별도 제어 진단으로 계속 조사한다. 전체 실패율과 수용 판정은 comparison.json에 보존했다.']
    with (HERE/'RESULTS.md').open('x') as stream:
        stream.write('\n'.join(text)+'\n')


if __name__ == '__main__':
    main()
