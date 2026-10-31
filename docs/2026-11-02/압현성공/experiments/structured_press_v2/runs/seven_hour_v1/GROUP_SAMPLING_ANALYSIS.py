"""그룹별 고정 표본 진단을 최초32/9항/실제 초기 상태·원본 재현 후 비교한다."""
from datetime import datetime,timezone
import json
from pathlib import Path
import numpy as np
import DISCOUNTED_REWARD_ANALYSIS as audit
from FROZEN_SAMPLING_ANALYSIS import pair_gate
import group_sampling_probe as probe

ROOT=Path(__file__).resolve().parent
REFERENCES=dict(seed7=ROOT/'frozen_sampling/full200',seed17=ROOT/'full33_seed17/evaluate/200_stochastic')


def same_trace(a,b,pins):
    if a['status']!='completed' or b['status']!='completed':return dict(verified=False,reason='자료 대기')
    flags={}
    for filename in ('trace.npz','initial.npz'):
        paths=[Path(x['path'])/filename for x in (a,b)]
        values=[dict(np.load(p,allow_pickle=False)) for p in paths]
        for p in paths:pins[str(p)]=audit.sha(p)
        flags[filename]=values[0].keys()==values[1].keys() and all(np.array_equal(v,values[1][k]) for k,v in values[0].items())
    return dict(verified=all(flags.values()),exact=flags,scope='trace8열 전체 및 initial q/hold 행별 exact; 저장되지 않은 전체 관측·몸 root journal까지 동등하다는 주장은 아님')


def load(path,group,pins):
    row=audit.load_dataset(path,pins)
    if row['status']!='completed':return row
    report=audit.read(path/'summary.json')
    expected=probe.groups(dict(finger='index'))
    if (report.get('sampling_group')!=group or report.get('selected_axes')!=expected[group] or
        report.get('group_partition')!=expected or report.get('native_draw_axes')!=33 or
        report.get('all_groups_same_native_rng_consumption') is not True or
        report.get('source_distribution_unchanged') is not True or report.get('diagnostic_group_record',{}).get('act_calls',0)<1 or
        report.get('policy_mode')!=('original_stochastic_all33' if group=='all' else 'hybrid_group_sampling')):
        raise ValueError('실제 그룹/분포/실행 계약 누락')
    # 저장 계약과 catalog의 실제39축 codec도 별도 검증한다.
    from EXPECTED_ANGLE_ANALYSIS import codec_proof
    row['codec']=codec_proof(path,pins)
    return row


def collect():
    pins={str(Path(p)):audit.sha(Path(p)) for p in (__file__,audit.__file__,probe.__file__)}
    result=dict(schema='structured_press.group_sampling_analysis.v1',updated_utc=datetime.now(timezone.utc).isoformat(),seeds={},errors=[],input_sha256=pins,production_unchanged=True)
    for seed,path in REFERENCES.items():
        reference=audit.load_dataset(path,pins);rows={};pairs={}
        for group in ('all','goal','arm','other'):
            try:rows[group]=load(ROOT/'group_sampling'/(seed+'_'+group),group,pins)
            except (ValueError,KeyError,OSError) as error:
                rows[group]=dict(status='invalid',error=str(error));result['errors'].append(seed+'_'+group+': '+str(error))
            pairs[group]=pair_gate(reference,rows[group])
        reproduction=same_trace(reference,rows['all'],pins)
        reasons=[g+' 자료/source/qhold 미완료' for g in rows if pairs[g].get('verified') is not True]
        if not reproduction['verified']:reasons.append('원래 stochastic all trace8열 재현 미검증')
        gate=dict(ready=not reasons,reasons=reasons)
        interpretation='실제 대응·all 재현 증거 대기; 그룹별 영향 판단 보류'
        if gate['ready']:
            interpretation={g:dict(safe_success=rows[g]['metrics']['safe_success'],safe_clean_s=rows[g]['metrics']['mean_safe_clean_s'],failure_episodes=rows[g]['metrics']['failure_episodes']) for g in rows}
        for row in [reference]+list(rows.values()):
            row.pop('initial',None);row.pop('curve_mean',None)
        result['seeds'][seed]=dict(reference=reference,groups=rows,actual_pairing=pairs,all_baseline_reproduction=reproduction,gate=gate,interpretation=interpretation)
    audit.verify_pins(pins)
    return result


def write(result):
    lines=['# 그룹별 고정 표본 실행 진단','','원본 full200의 Gaussian·가중치·물리·보상은 유지한다. 매 호출에서 원래 활성33축을 한 번 모두 draw한 후 선택 그룹 외 활성축만 latent mean으로 되돌린다. 출력은39축이고 inactive6은 원본 그대로다. all은 원래 stochastic 정책, 나머지는 hybrid 진단이며 새 학습이 아니다.']
    for seed,data in result['seeds'].items():
        lines+=['','## '+seed+' 실행 결과','','| seed | 실행 그룹 | 상태 | 안전성공/분모 | safe clean초 | 실패 |','|---|---|---|---:|---:|---:|']
        for group,row in data['groups'].items():
            m=row.get('metrics',{});lines.append('| {} | {} | {} | {}/{} | {} | {} |'.format(seed,group,row['status'],m.get('safe_success'),m.get('count'),m.get('mean_safe_clean_s'),m.get('failure_episodes')))
        for key in ('actual_pairing','all_baseline_reproduction','gate','interpretation'):lines+=['','## '+seed+' '+key,'','`'+json.dumps(data[key],ensure_ascii=False)+'`']
    lines+=['','원시 최초32 episode에서 실패를 분모에 포함하며9항 시점별 trace와 gamma0.99/cost gamma1을 검증한다. 실제 q105/hold105가 원본과 대응하고 all의 trace8열이 exact 재현되어야 효과를 해석한다. 전체 몸 root와 모든 관측 journal은 저장되지 않아 동등성을 과장하지 않는다. '
        '같은 단일 검지 목표·한 고정 난수 궤적에서 어느 그룹의 표본 실행이 결과를 바꾸는지 검사하며 독립적인 원인 분해나 새 목표 일반화는 아니다. '
        'logp는 선택 latent의 원래 Gaussian 밀도 기록일 뿐 hybrid 분포의 밀도가 아니고 PPO에 사용하지 않는다. 학습·생산 정책을 교체하지 않는다.']
    (ROOT/'GROUP_SAMPLING_ANALYSIS.md').write_text('\n'.join(lines)+'\n')
    (ROOT/'GROUP_SAMPLING_ANALYSIS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    result=collect();write(result);print(json.dumps({k:v['gate'] for k,v in result['seeds'].items()},ensure_ascii=False))
