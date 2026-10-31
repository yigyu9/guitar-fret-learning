"""검산 완료된 기울기와 원래 오압현 원장을 그림·한글 설명으로 정리한다."""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
CASES = ('fit', '50', '100', '300')
TERM_LABELS = ('Approach', 'Contact', 'Hold', 'Success', 'Wrong', 'Deficit',
               'Standby', 'Thumb', 'Act change', 'Reward V', 'Cost A')
PHASE_LABELS = ('pre-A', 'A prep', 'A audible', 'A release', 'post-A',
                'B prep', 'B7 audible', 'B gap', 'B8 audible', 'tail')
BODY_LABELS = ('thumb2', 'thumb3', 'index2', 'index3', 'middle2', 'middle3',
               'ring2', 'ring3', 'pinky2', 'pinky3')
CAUSES = ('other_higher', 'own_wrong_fret', 'own_wrong_string')


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def make_report(runs, analysis, out):
    verification = read(analysis/'verification.json')
    assert verification['completed'], 'Require successful frozen-buffer analysis'
    data = read(analysis/'analysis.json')
    settings = read(HERE.parent/'index_cost_prior_zero_v6/inputs/settings.json')
    targets = settings['song']['short_learning']['view']['source_targets']
    durations = np.asarray([n['end_s']-n['onset_s'] for n in targets])
    pins = {str(Path(__file__).resolve()): sha(__file__), **data['input_pins']}
    for path in (analysis/'verification.json', analysis/'analysis.json'):
        pins[str(path.resolve())] = sha(path)
    out.mkdir(parents=True, exist_ok=False)
    summaries = {}
    for case in CASES:
        folder = runs/case
        wrong_contract = read(folder/'training_contract.json')['diagnostics']['wrong_press']
        assert wrong_contract['schema'] == 'guitar_learning.wrong_press_sources.v2'
        assert tuple(wrong_contract['causes']) == CAUSES
        expected_boundaries = sorted({n[k] for n in targets for k in ('press_s', 'onset_s', 'end_s')} |
                                     {targets[0]['end_s']+.1})
        np.testing.assert_allclose(read(folder/'collection.json')['phase_boundaries_score_s'],
                                   expected_boundaries, rtol=0, atol=1e-9)
        first = read(folder/'first_attempts.json')
        assert first['completed_attempts'] == 128
        episodes = first['episodes']
        assert len(episodes) == 128 and {e['env_id'] for e in episodes} == set(range(128))
        maxima = {}
        std_sum, std_count = np.zeros(4), 0
        fret_min, fret_max = np.full(10, np.inf), np.zeros(10)
        for path in sorted(folder.glob('buffer_*.npz')):
            assert pins[str(path.resolve())] == sha(path)
            with np.load(path, allow_pickle=False) as z:
                first_episode = z['episode_id'] == 0
                std = np.exp(z['old_log_std'][..., 17:21])
                std_sum += std.sum(axis=(0, 1), dtype=np.float64)
                std_count += std.shape[0]*std.shape[1]
                audible = (first_episode & (z['audit_score_time']+1/60 >= targets[0]['onset_s']) &
                           (z['audit_score_time'] < targets[0]['end_s']))
                source = z['audit_endpoint_wrong_source_flags'][:, :, 0].any(-1) & audible[..., None]
                low = z['audit_endpoint_wrong_source_fret_min'][:, :, 0]
                high = z['audit_endpoint_wrong_source_fret_max'][:, :, 0]
                fret_min = np.minimum(fret_min, np.where(source, low, np.inf).min(axis=(0, 1)))
                fret_max = np.maximum(fret_max, np.where(source, high, 0).max(axis=(0, 1)))
                for key in ('wrong_source_time', 'wrong_supported_time',
                            'wrong_ambiguous_time', 'wrong_next_preparation_time'):
                    values = z['audit_note_'+key]
                    mask = first_episode.reshape(*first_episode.shape, *([1]*(values.ndim-2)))
                    value = np.where(mask, values, 0.).max(axis=0)
                    maxima[key] = np.maximum(maxima.get(key, np.zeros_like(value)), value)
        source_fraction = maxima['wrong_source_time'].mean(axis=0)/durations[:, None, None]
        assert source_fraction.shape == (3, 10, 3)
        notes = [[next(n for n in e['notes'] if n['source_index'] == i)
                  for e in episodes] for i in (4, 7, 8)]
        summaries[case] = dict(
            attempts=128, note_opportunities=384,
            reward_mean=float(np.mean([e['reward'] for e in episodes])),
            reward_components_mean={k: float(np.mean([e['reward_components'][k] for e in episodes]))
                                    for k in episodes[0]['reward_components']},
            latent_std4_mean=(std_sum/std_count).tolist(),
            A_endpoint_source_fret_ranges=[dict(body=BODY_LABELS[i], low=int(fret_min[i]), high=int(fret_max[i]))
                                           for i in range(10) if np.isfinite(fret_min[i])],
            per_note_achieved=[sum(n['achieved'] for n in group) for group in notes],
            all3=sum(all(n['achieved'] for n in e['notes']) for e in episodes),
            per_note_wrong=[float(np.mean([n['audible_wrong_fraction'] for n in group])) for group in notes],
            per_note_clean=[float(np.mean([n['clean_fraction'] for n in group])) for group in notes],
            source_fraction=source_fraction.tolist(),
            supported_fraction=(maxima['wrong_supported_time'].mean(axis=0)/durations).tolist(),
            ambiguous_fraction=(maxima['wrong_ambiguous_time'].mean(axis=0)/durations).tolist(),
            next_preparation_fraction=(maxima['wrong_next_preparation_time'].mean(axis=0)/durations).tolist(),
        )
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), constrained_layout=True)
    for ax, case in zip(axes.flat, CASES):
        agg = data['reports'][case]['weighted_chunk_gradient']
        norms = [n['norm'] for n in agg['components']]
        ax.barh(np.arange(11), norms)
        ax.set_yticks(np.arange(11)); ax.set_yticklabels(TERM_LABELS)
        ax.invert_yaxis(); ax.set_xscale('symlog', linthresh=1e-6)
        ax.set_title('V6 '+case); ax.set_xlabel('Actor gradient norm (not a percentage)')
    fig.savefig(out/'component_norms.png', dpi=150); plt.close(fig)
    for kind, labels, name in (('component', TERM_LABELS, 'component_cosines.png'),
                               ('phase', PHASE_LABELS, 'phase_cosines.png')):
        fig, axes = plt.subplots(2, 2, figsize=(15, 12), constrained_layout=True)
        cmap = plt.get_cmap('coolwarm').copy()
        cmap.set_bad('lightgray')
        for ax, case in zip(axes.flat, CASES):
            agg = data['reports'][case]['weighted_chunk_gradient']
            matrix = np.asarray(agg[kind+'_cosines'], dtype=float)
            shown = labels if kind == 'component' else [labels[n['phase']] for n in agg['phases']]
            assert matrix.shape == (len(shown), len(shown))
            im = ax.imshow(np.ma.masked_invalid(matrix), vmin=-1, vmax=1, cmap=cmap)
            ax.set_xticks(np.arange(len(shown))); ax.set_xticklabels(shown, rotation=65, ha='right')
            ax.set_yticks(np.arange(len(shown))); ax.set_yticklabels(shown); ax.set_title('V6 '+case)
        fig.colorbar(im, ax=axes.ravel().tolist(), label='Cosine; negative = opposing directions; gray = zero norm')
        fig.savefig(out/name, dpi=150); plt.close(fig)
    fig, axes = plt.subplots(2, 2, figsize=(11, 11), constrained_layout=True)
    for ax, case in zip(axes.flat, CASES):
        values = np.asarray(summaries[case]['source_fraction'])[0]
        im = ax.imshow(values, vmin=0, vmax=1, cmap='magma')
        ax.set_xticks((0, 1, 2)); ax.set_xticklabels(('other higher', 'own wrong fret', 'own wrong string'),
                                                  rotation=20, ha='right')
        ax.set_yticks(np.arange(10)); ax.set_yticklabels(BODY_LABELS); ax.set_title('V6 '+case+' / A')
    fig.colorbar(im, ax=axes.ravel().tolist(), label='A audible-time fraction; sources can overlap')
    fig.savefig(out/'wrong_sources.png', dpi=150); plt.close(fig)
    lines = ['# 보상·구간별 초기 정책 기울기와 오압현 출처', '',
             '고정 V6 저장본마다 새 확률 수행128시도·384음을 분석했다. 모델·보상·물리는 바꾸지 않았다. '
             '과거 학습 미니배치나 Adam 갱신을 재현한 결과가 아니다.', '',
             '|모델|A/B7/B8 달성|세 음 달성|A 오압현 비율|A clean 비율|평균 총보상|',
             '|---|---|---:|---:|---:|---:|']
    for case in CASES:
        s = summaries[case]
        lines.append('|%s|%s|%d/128|%.4f|%.4f|%.6f|' % (case, '/'.join(map(str, s['per_note_achieved'])),
                     s['all3'], s['per_note_wrong'][0], s['per_note_clean'][0], s['reward_mean']))
    lines += ['', '|보상항|fit|50|100|300|', '|---|---:|---:|---:|---:|']
    for key in summaries['fit']['reward_components_mean']:
        lines.append('|%s|%s|' % (key, '|'.join('%.6f' % summaries[c]['reward_components_mean'][key] for c in CASES)))
    lines += ['', '각 기울기는 원H32(마지막H2)의 GAE·공통 정규화를 유지하고 전이 수로 가중합했다. '
              '354tick 통합GAE가 아니다. 9개 보상 stream 외에 공통 reward critic/bootstrap 잔차와 비용 advantage를 별도로 분해했다. '
              'CPU의 동일 forward logp를 고정 기준으로 삼았으며 GPU에서 저장한 logp와의 차이는 원 analysis.json에 별도 기록했다. '
              '구간별 기울기는 보상이 지급된 시간이 아니라 행동의 출발시점 구간으로 묶었다.', '',
              '기울기 norm은 기여율이 아니며 합산되는 비율도 아니다. 음수 cosine은 해당 모델·수행에서 방향이 상반된다는 뜻이다. '
              '이것만으로 학습 실패의 단독 원인이나 어떤 보상항을 삭제할 근거가 되지는 않는다.', '',
              '![보상별 기울기 크기](component_norms.png)', '',
              '![보상 사이 방향](component_cosines.png)', '',
              '![구간 사이 방향](phase_cosines.png)', '',
              '오압현 출처는 기존 원장의240Hz 끝점 적분값이다. 같은 발음 시간에 여러 몸체·원인이 겹칠 수 있어 합이1일 필요는 없다. '
              'other_higher는 다른 손가락의 높은 프렛 경합, own_wrong_fret는 담당 패드의 잘못된 프렛, '
              'own_wrong_string은 담당 패드의 잘못된 현이다. 현재 finger-skill v2 계약을 확인해 해석했다. '
              '몸체 합력이나 판정 출처를 실제 현 압력·음향의 증거로 확대하지 않는다.', '',
              '![첫 음 오압현 출처](wrong_sources.png)', '',
              '|모델|A 주요 출처(시간 비율)|60Hz 끝점의 출처 프렛 범위|', '|---|---|---|']
    for case in CASES:
        a = np.asarray(summaries[case]['source_fraction'])[0]
        order = np.argsort(a.reshape(-1))[::-1][:3]
        sources = ['%s/%s %.4f' % (BODY_LABELS[i//3], CAUSES[i%3], a.reshape(-1)[i])
                   for i in order if a.reshape(-1)[i] > 0]
        ranges = ', '.join('%s %d..%d' % (v['body'], v['low'], v['high'])
                           for v in summaries[case]['A_endpoint_source_fret_ranges'])
        lines.append('|%s|%s|%s|' % (case, ', '.join(sources) or '없음', ranges or '없음'))
    lines += ['', '|모델|검지4축 latent 표준편차 평균|', '|---|---|']
    for case in CASES:
        lines.append('|%s|%s|' % (case, ', '.join('%.8f' % s for s in summaries[case]['latent_std4_mean'])))
    lines += ['', '표준편차는 정규화된 latent 단위이며 관절 각도나 실제 움직임의 표준편차가 아니다. '
              '실제 자세 변동은 목표 평균·tanh/관절 변환·접촉과 물리 제어의 영향을 함께 받는다.']
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n')
    (out/'summary.json').write_text(json.dumps(summaries, indent=2)+'\n')
    assert all(sha(path) == value for path, value in pins.items())
    (out/'verification.json').write_text(json.dumps(dict(completed=True, input_pins=pins,
        new_GPU_runs=0, new_NN_runs=0, output_sha256={p.name: sha(p) for p in out.iterdir()}), indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs', type=Path, required=True)
    parser.add_argument('--analysis', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    make_report(args.runs.resolve(), args.analysis.resolve(), args.out.resolve())
