"""요청각 기댓값 배포 진단을 실제 대응 초기값과 원시 할인 보상으로 집계한다."""
from datetime import datetime,timezone
import json
from pathlib import Path
import numpy as np
import DISCOUNTED_REWARD_ANALYSIS as audit
from FROZEN_SAMPLING_ANALYSIS import pair_gate

ROOT=Path(__file__).resolve().parent
CASES=dict(full200_latent_mean=('full200','latent_mean'),
    full200_normalized_action_mean=('full200','normalized_action_mean'),
    full200_requested_angle_mean=('full200','requested_angle_mean'),
    full100_normalized_action_mean=('full100','normalized_action_mean'),
    full100_requested_angle_mean=('full100','requested_angle_mean'),
    index_A100_free_normalized_action_mean=('index_A100_free','normalized_action_mean'),
    index_A100_free_requested_angle_mean=('index_A100_free','requested_angle_mean'))


def codec_proof(path,pins):
    import torch
    summary=audit.read(path/'summary.json');native=audit.read(path/'native/report.json')
    checkpoint=Path(native['checkpoint']);payload=torch.load(checkpoint,map_location='cpu',weights_only=False)
    contract=payload['identity']['architecture']['contract']['action']['target_contract']
    config=payload['metadata']['settings']['structured_press']
    if config['stage']!='free_v9' or config['active_axes']!=list(range(33)):raise ValueError('저장 free33 계약 누락')
    catalog_path=Path(summary['source_runtime'])/'guitar_learning/assets/structured_press_v2/catalog.json'
    catalog=audit.read(catalog_path);catalog_sha=audit.sha(catalog_path)
    if catalog_sha!=config['geometry_sha256']:raise ValueError('catalog SHA 계약 불일치')
    indices=[contract['joint_names'].index(name) for name in contract['action_order']]
    if len(indices)!=39 or indices!=catalog['action_indices']:raise ValueError('39축 순서 불일치')
    ref=np.asarray(contract['reference105_rad'])[indices];lo=np.asarray(contract['action_lower_rad']);hi=np.asarray(contract['action_upper_rad'])
    if not (np.allclose(ref,np.asarray(catalog['reference105'])[indices],atol=1e-6,rtol=0) and
        np.allclose(lo,catalog['action_lower'],atol=1e-6,rtol=0) and np.allclose(hi,catalog['action_upper'],atol=1e-6,rtol=0)):
        raise ValueError('저장codec/catalog bounds·reference 불일치')
    if not (np.isfinite(ref).all() and np.isfinite(lo).all() and np.isfinite(hi).all() and (hi>ref).all() and (lo<ref).all()):
        raise ValueError('39축 span 유한성/양수 실패')
    pins[str(catalog_path)]=catalog_sha;pins[str(checkpoint)]=audit.sha(checkpoint)
    return dict(verified=True,catalog_sha256=catalog_sha,action_indices=indices,action_order=contract['action_order'],
        reference39=ref.tolist(),positive_span39=(hi-ref).tolist(),negative_span39=(ref-lo).tolist(),
        asymmetric_axis_count=int(np.sum(np.abs((hi-ref)-(ref-lo))>1e-6)),
        goal4_axes=[i for i,name in enumerate(contract['action_order']) if name.startswith('LH:'+config['finger'])],
        arm12_axes=[i for i,name in enumerate(contract['action_order'][:33]) if not name.startswith('LH:')],
        scope='평활화/속도 제한 전 native piecewise 요청각 codec, 실제 물리 응답 기댓값 아님')


def impact_proof(summary):
    impact=summary.get('observed_request_impact')
    if not impact or impact.get('policy_act_calls',0)<=0 or impact.get('env_action_samples',0)<=0:
        raise ValueError('실제 평가관측 영향 통계 누락')
    for key in ('observed_latent_mean_min','observed_latent_mean_max','observed_sigma_min','observed_sigma_max'):
        if impact.get(key) is None or not np.isfinite(impact[key]):raise ValueError('실제 μ/σ 통계 누락')
    if impact['observed_sigma_min']<=0:raise ValueError('sigma 양수 계약 실패')
    if impact.get('active_action_latent_verified_calls')!=impact['policy_act_calls']:raise ValueError('실제 act action/latent 연결 검증 누락')
    adjustment=impact.get('finite_latent_adjustment',{})
    for key in ('saturated_active_count','max_normalized_action_change','max_requested_angle_change_degrees'):
        if adjustment.get(key) is None or not np.isfinite(adjustment[key]) or adjustment[key]<0:raise ValueError('포화 경계 수치보정 통계 누락')
    groups=impact.get('requested_angle_difference_degrees',{})
    for key,n in (('goal4',4),('arm12',12),('other17',17)):
        item=groups.get(key,{})
        if len(item.get('axes',[]))!=n or item.get('count')!=impact['env_action_samples']*n:raise ValueError('그룹 표본 분모 불일치')
        if any(item.get(k) is None or not np.isfinite(item[k]) for k in ('mean_absolute','mean_signed','max_absolute')):
            raise ValueError('요청각 통계 유한성 실패')
    if sorted(sum([groups[key]['axes'] for key in ('goal4','arm12','other17')],[]))!=list(range(33)):
        raise ValueError('33축 그룹 중복/누락')
    return impact


def expected_dataset(path,mode,pins):
    item=audit.load_dataset(path,pins)
    if item['status']!='completed':return item
    summary=audit.read(path/'summary.json');native=audit.read(path/'native/report.json')
    for report in (summary,native):
        if (report.get('deployment_rule')!=mode or report.get('policy_mode')!='deterministic_expectation_deployment_diagnostic' or
            report.get('saved_gaussian_mean_std_unchanged') is not True or report.get('optimizer_updates_difference')!=0 or
            report.get('quadrature',{}).get('nodes')!=64 or not report.get('finite_latent_boundary')):raise ValueError('명시 배포 규칙/분포 불변 provenance 누락')
    item['codec']=codec_proof(path,pins);item['observed_request_impact']=impact_proof(summary)
    groups=item['observed_request_impact']['requested_angle_difference_degrees']
    if groups['goal4']['axes']!=item['codec']['goal4_axes'] or groups['arm12']['axes']!=item['codec']['arm12_axes']:
        raise ValueError('actual codec와 영향 그룹의 축 선택 불일치')
    item['deployment_rule']=mode
    item['likelihood_interpretation']=summary['likelihood']
    item['inactive_axes_preservation']='원본 핀 helper의 torch.where(active, transformed, mean.tanh())와 CPU bitwise검사로 보존; 전체 실행action journal의 독립 감사는 아님'
    return item


def baseline_metrics_equal(first,second):
    """실행 전체 저널 동등성 대신 현재 기록된 원시 성과/9항/할인 보상만 검사한다."""
    fields=('count','safe_success','failure_episodes','complete_episode_control_transitions','mean_reward','mean_cost',
        'mean_clean_s','mean_safe_clean_s','mean_best_clean_s','reward_components_mean','cost_components_mean',
        'discounted_terms_mean','discounted_reward_mean','discounted_cost_mean','episode_steps')
    mismatch=[key for key in fields if first.get(key)!=second.get(key)]
    return dict(verified=not mismatch,mismatched_fields=mismatch,scope='기록된32episode 성과·9항·할인reward/cost exact equality; 전체각/실행action journal 동등성 아님')


def gate(result):
    reasons=[]
    for group in ('references','experiments'):
        for name,row in result[group].items():
            if row.get('status')!='completed':reasons.append(group+'/'+name+' 미완료 또는 invalid')
    for name in ('full100','full200','index_A100_free'):
        if result['reference_pairing'].get(name,{}).get('verified') is not True:reasons.append(name+' 원래 mean/stochastic 실제 대응 미검증')
    for name in CASES:
        if result['actual_pairing'].get(name,{}).get('verified') is not True:reasons.append(name+' 실제 q/hold/source 대응 미검증')
    if result['full200_latent_baseline_reproduction'].get('verified') is not True:reasons.append('full200 latent_mean 기준 재현 미검증')
    return dict(ready=not reasons,reasons=reasons)


def other_lineage(finger,pins):
    import torch
    source=ROOT/(finger+'_A_seed7_v1')/'200/train/J/final.pt'
    exported=ROOT/'model_only'/(finger+'_free_v9')/'J/final.pt'
    report_path=exported.parent.parent/'report.json'
    if not all(path.exists() for path in (source,exported,report_path)):return dict(status='pending')
    report=audit.read(report_path);transition=report['model_only_transition']
    if (not report.get('completed') or report.get('no_training') is not True or report.get('optimizer_updates')!=0 or
        report.get('committed_transitions')!=0 or report.get('physics_steps')!=0 or
        Path(transition['source']).resolve()!=source.resolve() or transition['source_sha256']!=audit.sha(source)):
        raise ValueError('A200 model-only 계보/0update 불일치')
    a,b=(torch.load(path,map_location='cpu',weights_only=False) for path in (source,exported))
    x,y=(value['metadata']['settings']['structured_press'] for value in (a,b))
    if a['updates']!=200 or b['updates']!=0 or x['stage']!='A' or y['stage']!='free_v9' or x['finger']!=finger or y['finger']!=finger or x['song']!=y['song']:
        raise ValueError('A200/손가락/목표/free export 불일치')
    if set(a['model'])!=set(b['model']) or not all(key=='active_mask' or torch.equal(value,b['model'][key]) for key,value in a['model'].items()):
        raise ValueError('A200→free 모델 가중치 불일치')
    catalog=ROOT.parents[1]/'runtime/guitar_learning/assets/structured_press_v2/catalog.json'
    goal=next(row for row in audit.read(catalog)['goals'] if row['finger']==finger and row['song']==y['song'])
    for path in (source,exported,report_path,catalog):pins[str(path)]=audit.sha(path)
    return dict(status='verified',source_A200=str(source),source_sha256=audit.sha(source),exported_checkpoint=str(exported),
        exported_sha256=audit.sha(exported),all_weights_exact_except_active_mask=True,no_training=True,
        goal={key:goal[key] for key in ('finger','song','physical_string','fret')})


def collect_other_fingers(pins):
    section=dict(cases={},errors=[],gate=dict(ready=False,reasons=[]),universal_no_harm_adoption='추가3쌍 완료 전 보류; 완료 후에도 기존 저장모델 비교이며 일반 보장 아님')
    for finger in ('middle','ring','pinky'):
        row=dict(modes={},actual_pairing=dict(verified=False,reason='자료 대기'),lineage=dict(status='pending'))
        section['cases'][finger]=row
        try:
            row['lineage']=other_lineage(finger,pins)
            for mode in ('latent_mean','requested_angle_mean'):
                path=ROOT/'expected_angle'/(finger+'_A200_'+mode)
                item=expected_dataset(path,mode,pins);row['modes'][mode]=item
                if item['status']=='completed':
                    if row['lineage']['status']!='verified' or item['checkpoint_sha256']!=row['lineage']['exported_sha256']:
                        raise ValueError('추가 손가락 평가 source export 불일치')
                    episodes=[e['episode'] for e in audit.analyze_all.iter_episode_rows(path/'native')]
                    correct=audit.analyze_all.combine_episode_values(episodes,finger)
                    for key in ('target_finger_joint_means','finger_control_240hz_mean'):item['metrics'][key]=correct[key]
            a,b=(row['modes'][mode] for mode in ('latent_mean','requested_angle_mean'))
            row['actual_pairing']=pair_gate(a,b)
            if row['actual_pairing']['verified'] and a['codec']!=b['codec']:raise ValueError('추가 pair 39codec 불일치')
            if row['actual_pairing']['verified']:
                x,y=a['metrics'],b['metrics']
                row['comparison']=dict(requested_minus_latent_success=y['safe_success']-x['safe_success'],
                    requested_minus_latent_safe_clean_s=y['mean_safe_clean_s']-x['mean_safe_clean_s'],
                    requested_minus_latent_discounted_reward=y['discounted_reward_mean']-x['discounted_reward_mean'],
                    requested_minus_latent_cost=y['discounted_cost_mean']-x['discounted_cost_mean'],
                    requested_minus_latent_failure_episodes=y['failure_episodes']-x['failure_episodes'])
        except (ValueError,KeyError,OSError) as error:
            row['error']=str(error);row['actual_pairing']=dict(verified=False,reason=str(error));section['errors'].append(finger+': '+str(error))
        if row['lineage']['status']!='verified' or row['actual_pairing']['verified'] is not True:
            section['gate']['reasons'].append(finger+' A200계보 또는 새baseline 실제pair 미검증')
    section['gate']['ready']=not section['gate']['reasons']
    if section['gate']['ready']:
        section['additional_no_harm_observed']=all(row['comparison']['requested_minus_latent_success']>=0 and
            row['comparison']['requested_minus_latent_safe_clean_s']>=-1e-12 and row['comparison']['requested_minus_latent_cost']<=1e-12 and
            row['comparison']['requested_minus_latent_failure_episodes']<=0 for row in section['cases'].values())
        section['universal_no_harm_adoption']='추가3pair 비교 완료; 제한된 기존 A200 모델의 진단이며 일반 무손상 보장/자동 채택은 아님'
    return section


def collect():
    pins={str(Path(__file__)):audit.sha(Path(__file__)),str(Path(audit.__file__)):audit.sha(Path(audit.__file__))}
    result=dict(schema='expected_angle_analysis.v1',updated_utc=datetime.now(timezone.utc).isoformat(),
        references={},experiments={},actual_pairing={},reference_pairing={},errors=[],input_sha256=pins,
        full200_latent_baseline_reproduction=dict(verified=False,reason='자료 대기'),production_unchanged=True)
    for name in ('full100','full200','index_A100_free'):
        for mode,path in (('mean',ROOT/'reward_trace'/name),('stochastic',ROOT/'frozen_sampling'/('full100_v2' if name=='full100' else name))):
            key=name+'_'+mode
            try:
                item=audit.load_dataset(path,pins)
                if item['status']=='completed':
                    item['codec']=codec_proof(path,pins)
                    if mode=='stochastic':
                        summary=audit.read(path/'summary.json')
                        if summary.get('policy_mode')!='stochastic_frozen_checkpoint' or summary.get('sampling_scale')!=1. or not summary.get('saved_mean_and_std_unchanged'):
                            raise ValueError('원래 고정 Gaussian provenance 실패')
                result['references'][key]=item
            except (ValueError,KeyError,OSError) as error:
                result['references'][key]=dict(status='invalid',error=str(error));result['errors'].append(key+': '+str(error))
    for name in ('full100','full200','index_A100_free'):
        a,b=result['references'][name+'_mean'],result['references'][name+'_stochastic']
        pair=pair_gate(a,b)
        if pair['verified'] and a['codec']!=b['codec']:pair=dict(verified=False,reason='원래 mean/stochastic codec 불일치')
        result['reference_pairing'][name]=pair
    for name,(source,mode) in CASES.items():
        try:
            item=expected_dataset(ROOT/'expected_angle'/name,mode,pins)
            result['experiments'][name]=item
            result['actual_pairing'][name]=pair_gate(result['references'][source+'_mean'],item)
            if item['status']=='completed' and result['actual_pairing'][name]['verified']:
                reference=result['references'][source+'_mean']
                if item['codec']!=reference['codec']:raise ValueError('같은39축 실제 spans/catalog 아님')
        except (ValueError,KeyError,OSError) as error:
            result['experiments'][name]=dict(status='invalid',error=str(error));result['errors'].append(name+': '+str(error))
            result['actual_pairing'][name]=dict(verified=False,reason=str(error))
    baseline=result['experiments']['full200_latent_mean'];original=result['references']['full200_mean']
    if baseline['status']==original['status']=='completed' and result['actual_pairing']['full200_latent_mean']['verified']:
        result['full200_latent_baseline_reproduction']=baseline_metrics_equal(original['metrics'],baseline['metrics'])
    result['gate']=gate(result);result['interpretation']='완료/provenance/실제 대응/기준 재현 검증 전 배포 규칙의 효과 판단 보류'
    if result['gate']['ready']:
        effects={}
        for source in ('full100','full200','index_A100_free'):
            a=result['experiments'][source+'_normalized_action_mean']['metrics'];b=result['experiments'][source+'_requested_angle_mean']['metrics']
            effects[source]=dict(angle_minus_normalized_success=b['safe_success']-a['safe_success'],
                angle_minus_normalized_safe_clean_s=b['mean_safe_clean_s']-a['mean_safe_clean_s'],
                angle_minus_normalized_discounted_reward=b['discounted_reward_mean']-a['discounted_reward_mean'],
                angle_minus_normalized_cost=b['discounted_cost_mean']-a['discounted_cost_mean'])
        result['interpretation']=dict(deployment_rule_contrasts=effects,
            limitation='같은 checkpoint·실제 q/hold·물리·분포에서 요청 변환 규칙을 바꾼 실행 차이; 물리 기댓값/단독 실패 원인/새 학습 성공 아님')
    result['other_fingers']=collect_other_fingers(pins)
    for group in ('references','experiments'):
        for item in result[group].values():item.pop('initial',None);item.pop('curve_mean',None)
    for row in result['other_fingers']['cases'].values():
        for item in row['modes'].values():item.pop('initial',None);item.pop('curve_mean',None)
    audit.verify_pins(pins)
    return result


def write(result):
    lines=['# 요청각 기댓값 배포 규칙 분석','','집계: '+result['updated_utc'],'',
        '같은 저장 Gaussian의 원래 latent 평균 실행, E[tanh Z] 실행, piecewise 요청각 E[θ(Z)]의 역변환 실행을 비교한다. '
        '이는 새 학습이나 물리 응답의 기댓값이 아니라 **평활화·속도 제한 전 요청의 배포 규칙 진단**이다.','',
        '| 자료 | 상태 | 안전성공/분모 | 평균 safe clean초 | 최장연속clean초 | 할인reward(.99) | 할인cost(1) |',
        '|---|---|---:|---:|---:|---:|---:|']
    for group in ('references','experiments'):
        for name,row in result[group].items():
            m=row.get('metrics',{});lines.append('| {} | {} | {}/{} | {} | {} | {} | {} |'.format(name,row['status'],*[m.get(k) for k in ('safe_success','count','mean_safe_clean_s','mean_best_clean_s','discounted_reward_mean','discounted_cost_mean')]))
    lines+=['','실제32환경 q105/hold105와 source checkpoint SHA가 같아야 비교한다. 실패 포함 최초32 episode의9항과 할인 보상/비용을 원시 trace·episode 합에 대조했다. '
        'q/hold 대응은 body/root 전체 물리 상태의 exact 대응을 증명하지 않는다.','',
        '## 검증 상태','','`'+json.dumps(result['gate'],ensure_ascii=False)+'`','',
        'full200 latent_mean 기준 재현: `'+json.dumps(result['full200_latent_baseline_reproduction'],ensure_ascii=False)+'`','',
        '## 실제 관측에서 요청각 차이','','| 자료 | 그룹 | 평균절댓값차이(deg) | 최대절댓값차이(deg) | 축×환경 표본수 |','|---|---|---:|---:|---:|']
    for name,row in result['experiments'].items():
        for group,stats in row.get('observed_request_impact',{}).get('requested_angle_difference_degrees',{}).items():
            lines.append('| {} | {} | {} | {} | {} |'.format(name,group,stats['mean_absolute'],stats['max_absolute'],stats['count']))
    lines+=['','요청각 차이는 원래 latent-mean 요청각을 기준으로 한다. 실제 몸/관절 이동 차이가 아니다. '
        '영향 통계는 평가 중 모든 batch act 관측을 집계하므로 일부 환경이 첫 episode를 마친 뒤의 act도 포함할 수 있다. '
        '최초32 episode 성과 분모와 별개다. 실제 μ/σ minmax,3개 축 그룹과 분모,39축 실제 span·catalog 출처는 JSON에 기록한다.','',
        '## 해석','','`'+json.dumps(result['interpretation'],ensure_ascii=False)+'`','',
        'E[tanh Z]와 E[θ(Z)]의 차이는 비대칭 span을 포함하는 요청각 평균을 실제로 실행했을 때의 결과를 분리한다. '
        '이 비교만으로 전체 실패의 단독 원인이나 접촉·평활화·rate 제한의 독립 기여를 확정하지 않는다. '
        '포화 시에는 active action을 ±(1−dtype eps)로 제한하고 latent를 계산한 뒤 반환action=tanh(latent)로 맞춘다. 보정량은 JSON의 finite_latent_adjustment에 기록한다. '
        'inactive6축은 원본 pin helper의 보존 로직과 CPU bitwise 검사 근거이며 전체 실행각 journal을 새로 감사한 주장은 아니다. '
        'latent_mean 기준 재현도 현재 기록된 episode 성과/9항/할인값 exact equality 범위에 한정한다. '
        '단일 목표/명목 초기 자세의 반복이며 일반화 검증이나 생산 자동 채택이 아니다.','',
        'GH64는 analytic E|Z| 보정으로 절댓값 kink를 분리했다. CPU에서 검증한 σ≈.049787/.15, μ∈[−8,8]의64↔128 오차와 MC 검증은 helper 검사 근거다. '
        '실제 관측 범위를 JSON에 남기며 그 밖의 범위를 검증한 것으로 확대하지 않는다.']
    lines+=['','## 다른 기존 A200 모델의 별도 진단','',
        '이 추가6조건은 기존 핵심7조건 gate와 분리한다. 중지·약지·소지 각각의 별도 A200 모델을0학습 free-v9로 내보내 새 latent baseline과 요청각 기댓값을 비교한다. '
        '과거 free probe32/32와 새 baseline의 q/hold가 직접 같다고 주장하지 않는다. 새 pair 자체의 source SHA·q/hold·39codec를 검증한다. '
        '이는 새 학습이나 한 정책의 새 목표 일반화 검증이 아니다.','',
        '| 손가락 | 실행 | 상태 | 안전성공/분모 | 평균safe clean초 | 할인reward | cost |','|---|---|---|---:|---:|---:|---:|']
    for finger,row in result['other_fingers']['cases'].items():
        for mode,item in row['modes'].items():
            m=item.get('metrics',{});lines.append('| {} | {} | {} | {}/{} | {} | {} | {} |'.format(finger,mode,item['status'],*[m.get(key) for key in ('safe_success','count','mean_safe_clean_s','discounted_reward_mean','discounted_cost_mean')]))
    lines+=['','추가 진단 gate: `'+json.dumps(result['other_fingers']['gate'],ensure_ascii=False)+'`','',
        result['other_fingers']['universal_no_harm_adoption'], '',
        '기존 핵심 결론의 준비 여부는 main gate로 판단하고, 손가락 전반의 무손상 적용 판단은 추가3pair가 완료되기 전에는 보류한다. '
        '세 pair가 완료되어도 제한된 기존 저장 모델의 진단이며 일반적인 무손상 보장은 아니다.']
    (ROOT/'EXPECTED_ANGLE_ANALYSIS.md').write_text('\n'.join(lines)+'\n')
    (ROOT/'EXPECTED_ANGLE_ANALYSIS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    result=collect();write(result);print(json.dumps(dict(gate=result['gate'],errors=result['errors']),ensure_ascii=False))
