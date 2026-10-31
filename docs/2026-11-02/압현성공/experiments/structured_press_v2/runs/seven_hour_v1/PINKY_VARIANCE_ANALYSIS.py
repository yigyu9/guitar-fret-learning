"""소지 A200→B100의 단일 분산 요인 비교를 완료 증거에 한해 CPU에서 집계한다."""
import os
for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[key]='1'
from datetime import datetime,timezone
import json
from pathlib import Path
import compare_variance as c
from fixed_reset_evaluate import assert_same_initial_conditions

ROOT=Path(__file__).resolve().parent
CONTROL=ROOT/'pinky_B_seed7_v1/100'
VARIANT=ROOT/'pinky_variance_variant/runs'
SOURCE=ROOT/'pinky_A_seed7_v1/200/train/J/final.pt'
SOURCE_SHA='009d7f0f4a9c3380e1c6d630e4fb444e7d4ee6c9229df7de4789a8f68f4ca2ea'
GOAL=dict(finger='pinky',song='virtual_finger_v9_pinky_s3_f9',physical_string=3,fret=9)


def run(path,evaluation,pins):
    row=c.collect_run(path,evaluation,pins)
    if row['status']=='completed':
        # 공통 helper의 검지 진단 선택만 소지에 맞게 다시 집계한다.
        row['metrics']=c.analysis.aggregate(path,'pinky',evaluation)
        report=c.read(Path(path)/'report.json')
        if any(report.get(k) for k in ('changed_inputs','missing_import_pins','cleanup_errors')):
            raise ValueError('완료 run 입력/정리 검증 실패: '+str(path))
        if report.get('lifecycle_verified') is False:raise ValueError('lifecycle 미검증')
        settings=c.read(Path(path)/'settings.json')
        if settings['structured_press']['finger']!='pinky' or settings['structured_press']['song']!=GOAL['song']:
            raise ValueError('소지 목표 계약 불일치')
    return row


def checkpoint_proof(pins):
    paths=dict(source=SOURCE,control=CONTROL/'train/J/initial.pt',
        variant=VARIANT/'pinky_B_factor010_seed7/J/initial.pt')
    if c.digest(SOURCE)!=SOURCE_SHA:raise ValueError('원본 A200 SHA 불일치')
    pins[str(SOURCE)]=SOURCE_SHA
    missing=[str(p) for p in paths.values() if not p.exists()]
    if missing:return dict(status='pending',missing=missing)
    import torch
    torch.set_num_threads(1)
    for path in paths.values():pins[str(path)]=c.digest(path)
    saved={key:torch.load(path,map_location='cpu',weights_only=False) for key,path in paths.items()}
    s,a,b=(saved[key] for key in ('source','control','variant'))
    initial_same=set(a['model'])==set(b['model']) and all(torch.equal(value,b['model'][key]) for key,value in a['model'].items())
    source_same=all(set(x['model'])==set(s['model']) and all(key=='active_mask' or torch.equal(value,x['model'][key])
        for key,value in s['model'].items()) for x in (a,b))
    cpu=torch.equal(a['torch_rng'],b['torch_rng'])
    cuda=len(a['cuda_rng'])==len(b['cuda_rng']) and all(torch.equal(x,y) for x,y in zip(a['cuda_rng'],b['cuda_rng']))
    if not all((initial_same,source_same,cpu,cuda)):raise ValueError('실제 소지 초기 가중치/RNG 불일치')
    return dict(status='verified',source_sha256=SOURCE_SHA,source_model_exact_except_active_mask=source_same,
        initial_models_exact_equal=initial_same,cpu_rng_exact_equal=cpu,cuda_rng_exact_equal=cuda)


def gate(result):
    """자료·동일 요인·예산·실제 대응 증거 모두 있어야 효과를 해석한다."""
    reasons=[]
    proof=result['checkpoint_proof']
    if (proof.get('status')!='verified' or proof.get('source_sha256')!=SOURCE_SHA or any(proof.get(k) is not True for k in
        ('source_model_exact_except_active_mask','initial_models_exact_equal','cpu_rng_exact_equal','cuda_rng_exact_equal'))):
        reasons.append('실제 초기 체크포인트 증거 미완료')
    for name,row in result['evaluations'].items():
        if row['status']!='completed' or row.get('metrics',{}).get('count')!=32:reasons.append(name+' raw32 평가 미완료')
    for name in ('control_final','variant_initial','variant_final'):
        if result['paired_conditions'].get(name,{}).get('verified') is not True:reasons.append(name+' 실제 q/hold 대응 미검증')
    for name,row in result['training'].items():
        if row['status']!='completed' or row.get('optimizer_updates')!=100 or row.get('committed_transitions')!=204800:
            reasons.append(name+' 100회/204800전이 학습 미완료')
    if result['settings_proof'].get('status')!='verified':reasons.append('단일 요인 설정 증거 미완료')
    audit=result['training']['variant'].get('initial_transfer_audit') or {}
    if audit.get('control_status')!='verified' or any(audit.get(k) is not True for k in
        ('all_initial_model_tensors_equal_source_except_active_mask','control_model_exact_equal','control_cpu_torch_rng_equal','control_cuda_rng_equal')):
        reasons.append('실제 실행의 native 초기 감사 미검증')
    return dict(ready=not reasons,reasons=reasons)


def settings_proof(pins):
    paths=[CONTROL/'train/settings.json',VARIANT/'pinky_B_factor010_seed7/settings.json']
    if not all(path.exists() for path in paths):return dict(status='pending')
    values=[c.read(path) for path in paths]
    for path in paths:pins[str(path)]=c.digest(path)
    for settings in values:
        if tuple(settings.get(k) for k in ('num_envs','horizon','updates','seed','size'))!=(64,32,100,7,'large'):
            raise ValueError('계획된64/H32/100/seed7/large 불일치')
        if settings.get('structured_transfer',{}).get('sha256')!=SOURCE_SHA:raise ValueError('A200 source 불일치')
    keys=('ppo','initial_std','structured_press','simple_start','finger_skill','song','song_training','physics_backend')
    unequal=[key for key in keys if values[0].get(key)!=values[1].get(key)]
    if unequal:raise ValueError('분산 외 설정 불일치: '+str(unequal))
    variant=values[1].get('variance_variant',{})
    if variant.get('factor')!=.1 or variant.get('selected_axes')!=[29,30,31,32]:raise ValueError('소지 sigma factor 불일치')
    return dict(status='verified',matching_settings_keys=list(keys),factor=.1,selected_axes=[29,30,31,32],
        learning_rate_rule_same=True,realized_learning_rates_may_differ=True)


def collect():
    pins={str(Path(c.__file__)):c.digest(c.__file__)}
    result=dict(schema='structured_press.pinky_variance_analysis.v1',updated_utc=datetime.now(timezone.utc).isoformat(),
        goal=GOAL,source_sha256=SOURCE_SHA,evaluations={},training={},paired_conditions={},input_sha256=pins,
        production_unchanged=True,formal_stage_promotion=False)
    for name,path in dict(control_initial=CONTROL/'evaluate_initial_fixed4242',control_final=CONTROL/'evaluate_final_fixed4242',
        control_free_v9=CONTROL/'evaluate_final_free_v9',variant_initial=VARIANT/'eval_initial_fixed4242',
        variant_final=VARIANT/'eval_final_fixed4242',variant_free_v9=VARIANT/'eval_final_free_v9').items():
        result['evaluations'][name]=run(path,True,pins)
    for name,path in dict(control=CONTROL/'train/J',variant=VARIANT/'pinky_B_factor010_seed7/J').items():
        result['training'][name]=run(path,False,pins)
    for name in ('control_final','variant_initial','variant_final'):
        a,b=result['evaluations']['control_initial'],result['evaluations'][name]
        if a['status']==b['status']=='completed':result['paired_conditions'][name]=assert_same_initial_conditions(a,b)
    result['checkpoint_proof']=checkpoint_proof(pins)
    result['settings_proof']=settings_proof(pins)
    result['gate']=gate(result)
    result['interpretation']='자료 또는 대응 증거 대기 중이며 효과를 추정하지 않음'
    if result['gate']['ready']:
        e=result['evaluations'];score=lambda name:(e[name]['metrics']['safe_success'],e[name]['metrics']['mean_safe_clean_s'])
        better_control=score('variant_final')>score('control_final');better_B0=score('variant_final')>score('control_initial')
        free_safe=e['variant_free_v9']['metrics']['failure_episodes']==0
        result['interpretation']=dict(better_than_control_B100=better_control,better_than_B0=better_B0,
            variant_free_v9_failure_zero=free_safe,eligible_for_further_experiment=better_control and better_B0 and free_safe,
            production_unchanged=True,scope='단일 소지 목표·seed7이며 formal B 승급 실험 아님')
    for path,sha in pins.items():
        if c.digest(path)!=sha:raise ValueError('분석 중 입력 변경: '+path)
    result['analysis_script_sha256']=c.digest(__file__)
    return result


def write(result):
    lines=['# 소지 탐색 분산 비교','','집계 시각: '+result['updated_utc'],'',
        '목표는 소지·물리 줄3·프렛9이다. 같은 A200에서 B100으로 이전하고 목표 소지4축 sigma만0.1배로 변경한다. '
        '기본 잡음 대조군과 초기 모델·CPU/CUDA RNG·64/H32/100·seed7·물리·보상·학습률 규칙을 확인한다. '
        '실제 사용 LR은 KL 재시도에 따라 달라질 수 있다.','',
        '## 고정 정책 최초32환경 평가','','| 조건 | 분모 | 안전 성공 | 평균 safe clean(초) | 실패 |','|---|---:|---:|---:|---:|']
    for name,row in result['evaluations'].items():lines.append('| {} | {} | {} | {} | {} |'.format(name,*c.display(row)))
    lines+=['','B0는 control_initial이다. B0보다 낮으면 다른100회 모델보다 높아도 개선 채택 후보로 올리지 않는다. '
        'B와 free-v9는 지원·초기 분포·활성축이 달라 별도로 해석한다. 동일 기하 반복32환경은 새 목표 일반화가 아니다.','',
        '## 학습 중 변화하는 확률 정책','','| 조건 | 완료 episode | 안전 성공 | 평균 safe clean(초) | 실패 |','|---|---:|---:|---:|---:|']
    for name,row in result['training'].items():lines.append('| {} | {} | {} | {} | {} |'.format(name,*c.display(row)))
    lines+=['','학습은 확률 표본화와 정책 갱신이 계속되는 완료 episode 집계이고, 평가는 고정 모델의 결정적 최초32 episode이다. '
        '실패 episode를 분모에 포함하며 미완료 episode를 성공으로 세지 않는다. 잠재 Gaussian μ 불변이 tanh 이후 기대 행동 평균 불변을 뜻하지 않는다.','',
        '## 완료 episode별 평균 보상과 비용','','| 항목 | 기본 잡음 B100 | 소지 sigma0.1 B100 |','|---|---:|---:|']
    for key,label in c.analysis.TERMS.items():
        values=[]
        for name in ('control','variant'):
            value=result['training'][name].get('metrics',{}).get('reward_components_mean',{}).get(key)
            values.append('—' if value is None else '{:.6f}'.format(value))
        lines.append('| {} | {} | {} |'.format(label,*values))
    for name,row in result['training'].items():
        lr=row.get('lr',{});lines+=['',name+' 비용(물리 실패 포함): `'+json.dumps(row.get('metrics',{}).get('cost_components_mean'),ensure_ascii=False)+'`',
            '{} 실제 LR 최소/최대 {}/{}; KL 재시도 합계 {}.'.format(name,lr.get('minimum_used_actor_lr'),lr.get('maximum_used_actor_lr'),lr.get('total_retries'))]
    for title,key in (('초기 모델/RNG','checkpoint_proof'),('단일 요인 설정','settings_proof'),('실제 q/hold 대응','paired_conditions'),('완료 증거 gate','gate'),('판단','interpretation')):
        lines+=['','## '+title,'','`'+json.dumps(result[key],ensure_ascii=False)+'`']
    lines+=['','학습 완료·실제 초기 가중치/RNG·설정·모든 평가 raw32·실제 q/hold·native 감사가 모두 검증되기 전에는 효과를 판단하지 않는다. '
        '생산 코드와 기존 최고 체크포인트를 유지한다. 이100회 비교를 formal B 단계 승급으로 취급하지 않는다. '
        '입력 SHA·원시 분모·9보상·비용·실패·LR 세부 내역은 동명 JSON에 저장한다.']
    (ROOT/'PINKY_VARIANCE_ANALYSIS.md').write_text('\n'.join(lines)+'\n')
    (ROOT/'PINKY_VARIANCE_ANALYSIS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    result=collect();write(result);print(json.dumps(result['gate'],ensure_ascii=False))
