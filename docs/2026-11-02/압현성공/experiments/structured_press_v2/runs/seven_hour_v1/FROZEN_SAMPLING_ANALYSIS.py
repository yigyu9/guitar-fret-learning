"""동일 저장본의 고정 확률 정책과 평균 정책을 실제 초기 q/hold 대응 후 비교한다."""
from pathlib import Path
import json
from datetime import datetime,timezone
import numpy as np
import DISCOUNTED_REWARD_ANALYSIS as audit

ROOT=Path(__file__).resolve().parent
CASES=('full100','full200','index_A100_free')


def pair_gate(mean, sampled):
    if mean['status']!='completed' or sampled['status']!='completed':return dict(verified=False,reason='자료 미완료')
    if mean['checkpoint_sha256']!=sampled['checkpoint_sha256']:return dict(verified=False,reason='동일 저장본 SHA 아님')
    if any(not np.array_equal(mean['initial'][k],sampled['initial'][k]) for k in ('q105','hold105')):
        return dict(verified=False,reason='actual q105/hold105 정확 대응 실패')
    return dict(verified=True,scope='32환경 q/hold 행별 동일; body/root 전체 초기 상태는 미감사')


def collect():
    pins={str(Path(__file__)):audit.sha(Path(__file__)),str(Path(audit.__file__)):audit.sha(Path(audit.__file__))}
    cases={};errors=[]
    for name in CASES:
        row={}
        sampled_path=ROOT/'frozen_sampling'/('full100_v2' if name=='full100' else name)
        for mode,path in (('mean',ROOT/'reward_trace'/name),('stochastic',sampled_path)):
            try:
                item=audit.load_dataset(path,pins)
                if mode=='stochastic' and item['status']=='completed':
                    summary=audit.read(path/'summary.json');native=audit.read(path/'native/report.json')
                    for report in (summary,native):
                        if report.get('policy_mode')!='stochastic_frozen_checkpoint' or report.get('sampling_scale')!=1. or not report.get('saved_mean_and_std_unchanged'):
                            raise ValueError('고정 확률 정책 provenance 누락')
                if item['status']=='completed':
                    episodes=[e['episode'] for e in audit.analyze_all.iter_episode_rows(path/'native')]
                    fields=('clean','best_clean_streak','wrong','missing','own_wrong_string_time',
                            'own_wrong_fret_time','other_higher_time','geometry_time','loaded_target_time','body_load_time','facing_time')
                    item['metrics']['raw_note_means_s']={k:float(np.mean([e['left_note_ledger']['values'][k][0] for e in episodes])) for k in fields}
                    item['metrics']['fixed_note_duration_s']=2.5
                    settings_path=path/'native/settings.json';pins[str(settings_path)]=audit.sha(settings_path)
                    fraction=audit.read(settings_path)['song']['left_fraction']
                    required=min(2.5,max(.05,2.5*fraction))
                    item['metrics']['required_clean_streak_s']=required
                    item['metrics']['qualifying_streak_episode_count']=sum(e['left_note_ledger']['values']['best_clean_streak'][0]+1e-12>=required for e in episodes)
                    item['metrics']['mean_nonclean_audible_s']=2.5-item['metrics']['mean_clean_s']
                    item['metrics']['clean_wrong_missing_residual_s']=2.5-sum(item['metrics']['raw_note_means_s'][k] for k in ('clean','wrong','missing'))
                row[mode]=item
            except (OSError,KeyError,ValueError) as error:row[mode]=dict(status='invalid',error=str(error));errors.append(name+'/'+mode+': '+str(error))
        row['actual_pairing']=pair_gate(row['mean'],row['stochastic']);cases[name]=row
    ready=all(row['actual_pairing']['verified'] for row in cases.values())
    cross_path=ROOT/'probes/noise_index_scale100/report.json'
    cross=audit.read(cross_path)
    if cross.get('completed') is not True:raise ValueError('A4 noise 교차근거 미완료')
    pins[str(cross_path)]=audit.sha(cross_path)
    cross_reference=dict(path=str(cross_path),summary=cross['summary'],scale=cross['scale'],
        scope='source A supported aligned 4 active finger axes; different from exported free33 Gaussian')
    for row in cases.values():
        for mode in ('mean','stochastic'):row[mode].pop('initial',None);row[mode].pop('curve_mean',None)
    audit.verify_pins(pins)
    return dict(schema='frozen_sampling_analysis.v1',updated_utc=datetime.now(timezone.utc).isoformat(),
        comparison_ready=ready,cases=cases,errors=errors,input_sha256=pins,A4_noise_cross_reference=cross_reference,
        A_export_limitation='A target4 trained; exported free33 without retraining, so arm/non-target Gaussian noise was not trained in A',
        scope='한 고정 checkpoint의 평균 실행 vs 원래 Gaussian scale1 표본; 학습 블록의 변화하는 확률 정책과 구별',
        interpretation='완료/원시32/모델·source/실제초기대응 검증 전 효과 판단 보류' if not ready else
            '세 고정 저장본의 대응 비교 가능; 단일 목표·단일 명목 초기 DOF 자세 반복이며 무작위 자세 일반화 아님')


def write(result):
    lines=['# 고정 체크포인트 확률 표본과 평균 실행 비교','','집계: '+result['updated_utc'],'',result['scope'],'',
        '| 저장본 | 실행 | 상태 | 안전 성공/분모 | 총clean초 | 최장연속clean초 | 할인 reward | cost |','|---|---|---|---|---|---|---|---|']
    for name,row in result['cases'].items():
        for mode in ('mean','stochastic'):
            item=row[mode];m=item.get('metrics',{})
            lines.append('| {} | {} | {} | {}/{} | {} | {} | {} | {} |'.format(name,mode,item['status'],*[m.get(k) for k in ('safe_success','count','mean_safe_clean_s','mean_best_clean_s','discounted_reward_mean','discounted_cost_mean')]))
    lines+=['','전체 비교 준비: '+str(result['comparison_ready']),'',result['interpretation'],'',
        '실제 q/hold 대응 결과: `'+json.dumps({k:v['actual_pairing'] for k,v in result['cases'].items()},ensure_ascii=False)+'`','',
        '실패도 최초32 episode 분모에 포함한다. 조기 종료는 실제 기록 길이로 유지한다. 보상9항/비용은 별도 할인율(.99/1)로 집계한다. '
        '학습 중4/512→133/513은 다른100개 update에 걸친 지표이므로 마지막 체크포인트의 확률 정책 성능을 대신하지 않는다. '
        '9항·안전성·raw/SHA/모델 불변 증거는 JSON에 기록하며 아직 실행되지 않은 조건의 효과를 추정하지 않는다.']
    lines+=['','총clean은 음 구간에서 clean 조건을 만족한 시간을 합산한 값이고 최장연속clean은 끊기지 않은 가장 긴 구간이다. 이 과제의 연속 달성 기준은1초이며 JSON에 실제 저장 left_fraction으로 계산한 기준을 기록했다. '
        '원본은1/240초 양 끝 candidate가 모두 참일 때만 clean을 적분하고 streak를 유지한다. wrong/missing은 끝점 trapezoid 적분이므로 '
        'clean+wrong+missing이 항상2.5초로 정확히 분할되지는 않는다. 그 잔여를 추가 missing이나 힘 이탈 시간이라고 단정하지 않는다.','']
    for name,row in result['cases'].items():
        if row['actual_pairing']['verified']:
            m=row['stochastic']['metrics'];raw=m['raw_note_means_s']
            lines+=['- {} 고정 확률 정책: 총clean {:.6f}초, 최장연속 {:.6f}초, non-clean 합 {:.6f}초; wrong {:.6f}초, missing {:.6f}초, target geometry {:.6f}초, loaded target {:.6f}초.'.format(
                name,m['mean_clean_s'],m['mean_best_clean_s'],m['mean_nonclean_audible_s'],raw['wrong'],raw['missing'],raw['geometry_time'],raw['loaded_target_time'])]
    lines+=['','A100free는 A에서 목표 손가락4축으로 학습한 후 가중치 재학습 없이 free33으로 전환한 모델이다. '
        '이번 표본은 저장된 free33 Gaussian의 정확한 실행이지만 A학습 때 팔과 비목표 손가락의 잡음은 학습되지 않았다. '
        '별도의 원본 A4축-only noise 진단에서 scale1은0/32였으며, 활성축·초기 분포·지원 조건이 달라 이번 free33 결과와 합산하지 않는다.','',
        '현재 세 자료가 모두 검증되었다면 full200의 고정 확률 정책 성공 상승은 능력 전체 상실이라는 설명에 반대되는 실제 근거다. '
        '그러나 실행 분포 차이가 관측되었다는 사실만으로 비대칭 decoder 하나가 원인이라고 확정하지 않는다. '
        '확률 접촉의 반복적인 짧은 끊김은 총clean이 높아도 연속 달성을 낮출 수 있다.']
    if result['comparison_ready']:
        x=result['cases'];lines+=['','고정 체크포인트의 실제 결과: full100은 평균32/32에서 확률7/32로, full200은 평균0/32에서 확률31/32로 바뀌었다. '
            '이는 변화하는 학습블록의 성공수 대용치가 아니라 같은 최종 저장본을 고정해 확인한 실행 결과다. '
            '따라서 full200의 능력 전체 상실이라고 요약하면 틀리며 평균/확률 실행 분포 차이를 따로 설명해야 한다. '
            '비대칭 요청각 변환·rate/smoothing·접촉 동역학 중 어느 요인 때문인지는 이번 비교만으로 분리하지 못했다.']
    (ROOT/'FROZEN_SAMPLING_ANALYSIS.md').write_text('\n'.join(lines)+'\n')
    (ROOT/'FROZEN_SAMPLING_ANALYSIS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    result=collect();write(result);print(json.dumps(dict(comparison_ready=result['comparison_ready'],errors=result['errors'])))
