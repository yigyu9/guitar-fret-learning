"""손가락 함수 보존 실험의 완료 결과와 실제 체크포인트를 CPU에서 검증한다."""
import os
for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):
    os.environ[key]='1'
from datetime import datetime,timezone
import json
from pathlib import Path
import compare_variance as comparison
from fixed_reset_evaluate import assert_same_initial_conditions

ROOT=Path(__file__).resolve().parent
ARM=ROOT/'arm_refinement_variant/runs'
VAR=ROOT/'variance_variant/runs'
FROZEN=('core.finger_encoder.','core.finger_heads.','core.finger_log_std','actor_extra.')
SUPPORT=('core.support_encoder.','core.support_head.','core.support_log_std')
VALUE=('core.value_encoder.','core.reward_critic.','core.cost_critic.','value_extra.')


def checkpoint_proof(pins):
    """저장된 감사 플래그 대신 실제 텐서·RNG도 정확하게 비교한다."""
    paths=dict(arm_initial=ARM/'index_B_arm_refinement_seed7/J/initial.pt',
        arm_final=ARM/'index_B_arm_refinement_seed7/J/final.pt',
        variance_initial=VAR/'index_B_factor010_seed7/J/initial.pt',
        source=ROOT/'arm_refinement_variant/runtime/transfer_inputs/index_A100.pt')
    missing=[str(path) for path in paths.values() if not path.is_file()]
    if missing:return dict(status='pending',missing=missing)
    import torch
    torch.set_num_threads(1)
    for path in paths.values():pins[str(path)]=comparison.digest(path)
    saved={key:torch.load(path,map_location='cpu',weights_only=False) for key,path in paths.items()}
    a,b,c,s=(saved[k] for k in ('arm_initial','arm_final','variance_initial','source'))
    if set(a['model'])!=set(b['model']) or set(a['model'])!=set(c['model']):
        raise ValueError('모델 tensor key 불일치')
    same=lambda x,y:all(torch.equal(value,y[key]) for key,value in x.items())
    frozen=[key for key in a['model'] if key.startswith(FROZEN)]
    if not frozen:raise ValueError('동결 tensor가 없음')
    frozen_changed=[key for key in frozen if not torch.equal(a['model'][key],b['model'][key])]
    source_changed=[key for key,value in s['model'].items() if key!='active_mask' and not torch.equal(value,a['model'][key])]
    cpu_equal=torch.equal(a['torch_rng'],c['torch_rng'])
    cuda_equal=len(a['cuda_rng'])==len(c['cuda_rng']) and all(torch.equal(x,y) for x,y in zip(a['cuda_rng'],c['cuda_rng']))
    same_initial=same(a['model'],c['model'])
    if frozen_changed or source_changed or not (same_initial and cpu_equal and cuda_equal):
        raise ValueError('함수 보존 또는 초기 대응 증거 불일치: '+str(frozen_changed+source_changed))
    changed=lambda prefix:[key for key,value in a['model'].items() if key.startswith(prefix) and not torch.equal(value,b['model'][key])]
    return dict(status='verified',source_sha256=pins[str(paths['source'])],frozen_tensor_count=len(frozen),
        all_frozen_tensors_exact_equal=True,source_model_exact_except_active_mask=True,
        variance_initial_model_exact_equal=same_initial,variance_initial_cpu_rng_equal=cpu_equal,
        variance_initial_cuda_rng_equal=cuda_equal,support_changed_tensor_names=changed(SUPPORT),
        value_changed_tensor_names=changed(VALUE),initial_optimizer_updates=a['updates'],final_optimizer_updates=b['updates'],
        angles_locked=False,same_observation_function_preservation='고정된 가중치·정규화이며 실제 관측 변화에 따른 출력 변화는 허용')


def completed_evaluation(path,pins):
    row=comparison.collect_run(path,True,pins)
    if row['status']=='completed':
        report=comparison.read(Path(path)/'report.json')
        for key in ('changed_inputs','missing_import_pins','cleanup_errors'):
            if report.get(key):raise ValueError('완료 평가 무결성 실패: '+key)
        if report.get('lifecycle_verified') is False:raise ValueError('lifecycle 검증 실패')
    return row


def collect():
    pins={str(Path(comparison.__file__)):comparison.digest(comparison.__file__)}
    result=dict(schema='structured_press.arm_refinement_analysis.v1',updated_utc=datetime.now(timezone.utc).isoformat(),
        evaluations={},training={},paired_conditions={},pending=[],input_sha256=pins,
        production_unchanged=True,same_learning_rate_rule_not_same_realized_lr=True)
    paths=dict(B0=ROOT/'paired_B_initial_seed4242',old_B100=ROOT/'paired_B_100_seed4242',
        variance_initial=VAR/'eval_factor010_initial_fixed4242',variance_final=VAR/'eval_factor010_final_fixed4242',
        variance_free_v9=VAR/'eval_factor010_final_free_v9',arm_initial=ARM/'eval_initial_fixed4242',
        arm_final=ARM/'eval_final_fixed4242',arm_free_v9=ARM/'eval_final_free_v9')
    for name,path in paths.items():result['evaluations'][name]=completed_evaluation(path,pins)
    for name,path in dict(variance=VAR/'index_B_factor010_seed7/J',arm=ARM/'index_B_arm_refinement_seed7/J').items():
        result['training'][name]=comparison.collect_run(path,False,pins)
    for name in ('variance_initial','variance_final','arm_initial','arm_final'):
        a,b=result['evaluations']['B0'],result['evaluations'][name]
        if a['status']==b['status']=='completed':result['paired_conditions'][name]=assert_same_initial_conditions(a,b)
    result['checkpoint_proof']=checkpoint_proof(pins)
    for group in ('training','evaluations'):
        result['pending'] += [group+'/'+name for name,row in result[group].items() if row['status']!='completed']
    if result['checkpoint_proof'].get('status')!='verified':
        result['pending'].append('checkpoint_proof')
    for name in ('variance_initial','variance_final','arm_initial','arm_final'):
        if result['paired_conditions'].get(name,{}).get('verified') is not True:
            result['pending'].append('paired_conditions/'+name)
    result['interpretation']='결과 또는 대응 증거 대기 중이며 실험 효과를 추정하지 않음'
    if not result['pending']:
        e=result['evaluations'];safe=lambda name:(e[name]['metrics']['safe_success'],e[name]['metrics']['mean_safe_clean_s'])
        result['interpretation']=dict(better_than_variance_B100=safe('arm_final')>safe('variance_final'),
            better_than_B0=safe('arm_final')>safe('B0'),
            free_v9_failure_zero=e['arm_free_v9']['metrics']['failure_episodes']==0,
            scope='단일 목표·seed7; B0 최고 기준과 비교하며 생산 자동 반영 없음')
    for path,expected in pins.items():
        if comparison.digest(path)!=expected:raise ValueError('분석 중 입력 변경: '+path)
    result['analysis_script_sha256']=comparison.digest(__file__)
    return result


def write(result):
    lines=['# 손가락 함수 보존형 팔 세부 학습 분석','','집계 시각: '+result['updated_utc'],'',
        '같은 A100·factor0.1·seed7·large/64/H32/B100에서 actor의 학습 가능한 가중치 범위만 바꾼다. '
        '손가락 encoder/heads/std와 actor_extra 가중치를 고정하며 팔·지지 actor와 독립 가치망을 학습한다. '
        '**관절 각도나 실행 행동을 고정하는 실험이 아니다.** 관측 변화에 따라 손가락 출력은 계속 변할 수 있다.','',
        '## 고정 정책 평가','','| 조건 | 완료 분모 | 안전 성공 | 평균 safe clean(초) | 실패 |','|---|---:|---:|---:|---:|']
    for name,row in result['evaluations'].items():lines.append('| {} | {} | {} | {} | {} |'.format(name,*comparison.display(row)))
    lines+=['','B0는 추가 학습 전 기준이다. 기존 분석에서 가장 높았던 B0를 계속 보존하며, '
        '학습 후 성과가 다른100회 모델보다 높다는 사실을 B0 개선으로 해석하지 않는다. '
        'B와 free-v9는 초기 분포·지원·활성축이 달라 합산하지 않는다.','',
        '실제32환경 q/initial_hold 대응: `'+json.dumps(result['paired_conditions'],ensure_ascii=False)+'`','',
        '## 실제 체크포인트 증거','','`'+json.dumps(result['checkpoint_proof'],ensure_ascii=False)+'`','',
        '## 학습 중 확률 정책','','| 조건 | 완료 episode | 안전 성공 | 평균 safe clean(초) | 실패 |','|---|---:|---:|---:|---:|']
    for name,row in result['training'].items():lines.append('| {} | {} | {} | {} | {} |'.format(name,*comparison.display(row)))
    lines+=['','학습 집계는 변화하는 확률 정책의 완료 episode만 포함한다. 고정 정책 최초32 episode 평가와 구별하며 '
        '미완료 episode를 성공으로 세지 않는다. 같은 학습률 규칙이라도 KL 재시도로 실제 사용 LR은 달라질 수 있다.','',
        '| 조건 | 완료 update | 실제 사용 LR 최소/최대 | KL 재시도 합계 |','|---|---:|---:|---:|']
    for name,row in result['training'].items():
        lr=row.get('lr',{});lines.append('| {} | {} | {} / {} | {} |'.format(name,lr.get('updates'),lr.get('minimum_used_actor_lr'),lr.get('maximum_used_actor_lr'),lr.get('total_retries')))
    lines+=['','## 학습 episode별 보상 평균과 비용','','| 항목 | 분산0.1 B100 | 손가락 함수 보존 B100 |','|---|---:|---:|']
    for key,label in comparison.analysis.TERMS.items():
        values=[]
        for name in ('variance','arm'):
            value=result['training'][name].get('metrics',{}).get('reward_components_mean',{}).get(key)
            values.append('—' if value is None else '{:.6f}'.format(value))
        lines.append('| {} | {} | {} |'.format(label,*values))
    for name,row in result['training'].items():
        lines+=['',name+' 세부 비용(물리 실패 포함): `'+json.dumps(row.get('metrics',{}).get('cost_components_mean'),ensure_ascii=False)+'`']
    lines+=['','## 판단','','`'+json.dumps(result['interpretation'],ensure_ascii=False)+'`','',
        '대기 입력: '+(', '.join(result['pending']) or '없음'),'',
        '단일 검지·동일 기하·단일 seed의 실험이다. 새 목표 일반화 검증이 아니며 생산 코드는 변경하지 않는다. '
        '원시32환경 분모·9항 보상·비용·실패·초기 가중치/RNG·동결 tensor·LR·입력 SHA는 동명 JSON에 기록한다.']
    (ROOT/'ARM_REFINEMENT_ANALYSIS.md').write_text('\n'.join(lines)+'\n')
    (ROOT/'ARM_REFINEMENT_ANALYSIS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    result=collect();write(result);print(json.dumps(dict(pending=result['pending'],input_files=len(result['input_sha256']))))
