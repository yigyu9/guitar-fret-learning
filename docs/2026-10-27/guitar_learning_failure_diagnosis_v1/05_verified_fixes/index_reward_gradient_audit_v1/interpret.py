"""동결된 기울기 결과와 실제 전곡 반환값을 비교해 후속 단일 가설을 기록한다."""
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    analysis = json.loads((HERE/'analysis/analysis.json').read_text())
    verification = json.loads((HERE/'analysis/verification.json').read_text())
    assert verification['completed'] and not verification['changed_inputs'] and not verification['failure']
    pins = dict(analysis['input_pins'])
    for p in (Path(__file__).resolve(), HERE/'analysis/analysis.json', HERE/'analysis/verification.json',
              HERE/'report/summary.json', HERE/'report/verification.json'):
        pins[str(p)] = sha(p)
    assert all(sha(p) == h for p, h in pins.items())
    stats = {}
    for case, result in analysis['reports'].items():
        pieces = []
        for p in sorted((HERE/'runs'/case).glob('buffer_*.npz')):
            assert sha(p) == pins[str(p.resolve())]
            with np.load(p, allow_pickle=False) as z:
                pieces.append({k: z[k].copy() for k in
                               ('reward', 'reward_value', 'terminated', 'truncated', 'audit_phase')})
        data = {k: np.concatenate([p[k] for p in pieces]) for k in pieces[0]}
        assert data['reward'].shape == (354, 128)
        assert not data['terminated'][:-1].any() and data['terminated'][-1].all()
        assert not data['truncated'].any()
        returns = np.zeros_like(data['reward'], dtype=np.float64)
        carry = np.zeros(128)
        for t in range(353, -1, -1):
            carry = data['reward'][t]+.99*(~data['terminated'][t])*carry
            returns[t] = carry
        error = data['reward_value']-returns
        phase0 = error[data['audit_phase'] == 0]
        agg = result['weighted_chunk_gradient']
        norms = {v['term']: v['norm'] for v in agg['components']}
        stats[case] = dict(
            value_minus_realized_MC_mean=float(error.mean()),
            realized_MC_RMSE=float(np.sqrt(np.mean(error**2))),
            pre_A_value_minus_MC_mean=float(phase0.mean()),
            pre_A_MC_RMSE=float(np.sqrt(np.mean(phase0**2))),
            contact_hold_cosine=agg['component_cosines'][1][2],
            pre_A_A_prep_cosine=agg['phase_cosines'][0][1],
            pre_A_A_release_cosine=agg['phase_cosines'][0][3],
            total_gradient_norm=agg['total_norm'], component_norms=norms,
            last_H2_weighted_gradient_norm=result['chunks'][-1]['total_norm']*2/354,
            saved_CPU_GPU_logp_max_difference=max(c['saved_logp_max_difference'] for c in result['chunks']),
        )
    out = HERE/'interpretation'
    out.mkdir(exist_ok=False)
    lines = ['# 진단 결론과 다음 단일 비교', '',
             '모델 고정·새 확률 수행의 측정 결과다. 과거 학습에서 실제 수락된 미니배치나 Adam 변화의 인과 분석은 아니다. '
             '보상9항·기존 종료·물리·정책·저장본은 바꾸지 않았다.', '',
             '|모델|접촉/유지 cosine|초기준비/첫음준비 cosine|V−실현MC 평균|실현MC RMSE|',
             '|---|---:|---:|---:|---:|']
    for c, s in stats.items():
        lines.append('|%s|%.6f|%.6f|%.6f|%.6f|' % (c, s['contact_hold_cosine'], s['pre_A_A_prep_cosine'],
                     s['value_minus_realized_MC_mean'], s['realized_MC_RMSE']))
    s = stats['300']
    lines += ['', '마지막 모델의 최초 접촉과 압현 유지 방향은 cosine %.6f, 초기준비와 첫음준비는 %.6f다. '
              '동일 정책 매개변수에서 상반된 방향이 관찰된다. 각 norm은 기여율이 아니고, 이를 곧바로 보상 중복·불필요 또는 삭제 근거로 해석하지 않는다.'
              % (s['contact_hold_cosine'], s['pre_A_A_prep_cosine']), '',
              '마지막 접근 stream norm %.6f, 공통 reward critic/bootstrap 잔차 %.6f, 압현 유지 %.6f다. '
              'critic 잔차는 별도 보상항이 아니다. 접근 potential과 가치 예측의 상쇄도 포함하므로 큰 norm만으로 critic 오류를 확정하지 않는다.'
              % (s['component_norms']['song_left_approach'], s['component_norms']['common_reward_critic_bootstrap'],
                 s['component_norms']['song_clean_hold']), '',
              '354tick의 실제 보상을 gamma=.99로 역합산해 관측된 반환값을 계산했다. 모든 환경은 마지막 tick에서 실제 terminated=True이며 조기 종료나 truncated가 없었다. '
              '이 MC 값은 한 확률 궤적의 실현값으로 조건부 기대가치의 정답 자체는 아니다. 따라서 RMSE에는 수행의 확률적 변동도 들어간다.', '',
              '초기 fit 모델의 초기준비 구간 V−MC 평균은 %.6f, RMSE %.6f였다. 마지막 모델은 각각 %.6f, %.6f다. '
              '가치 예측 오차가 줄어드는 동안에도 압현은 퇴행했다. 초기의 미보정 가치 예측이 학습 초반에 영향을 줬을 가능성을 별도 비교하되 단독 원인으로 확정하지 않는다.'
              % (stats['fit']['pre_A_value_minus_MC_mean'], stats['fit']['pre_A_MC_RMSE'],
                 s['pre_A_value_minus_MC_mean'], s['pre_A_MC_RMSE']), '',
              '마지막2tick은 별도 H2 정규화이므로 원 학습의 H32 연속 수행과 같다고 하지 않는다. 마지막 모델에서 이 H2 기여 norm은 %.6f이고 전체 가중 기울기 norm은 %.6f다. '
              'CPU/GPU logp 차이도 기록했으며 같은 CPU forward를 기준으로 ratio1을 정의했다.'
              % (s['last_H2_weighted_gradient_norm'], s['total_gradient_norm']), '',
              '다음 단일 가설은 **정책을 그대로 둔 reward critic 사전 보정**이다. 초기 fit 수행 자료만 사용해 실제 할인 반환값을 학습하고, '
              'actor·표준편차·비용 head·물리·9보상·종료·PPO 설정은 보존한다. 동일 장면의 환경별 train/holdout을 사전에 나누고 '
              '초기 행동/원장 동일성, holdout 가치 오차, 동일 예산 후의 압현·해제·실패를 비교한다. 아직 구현·수행하거나 효과를 입증한 변경은 아니다.', '',
              '[보상·구간·오압현 그림과 실제 점수](../report/RESULTS.md). 다른 seed·손가락·자유 기타/J33·67음은 미완료다.']
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n')
    (out/'values.json').write_text(json.dumps(stats, indent=2)+'\n')
    assert all(sha(p) == h for p, h in pins.items())
    (out/'verification.json').write_text(json.dumps(dict(completed=True, input_pins=pins,
        new_GPU_runs=0, new_NN_runs=0, output_sha256={p.name: sha(p) for p in out.iterdir()}), indent=2)+'\n')


if __name__ == '__main__':
    main()
