"""전축 fresh 학습의 목표4축 분산 비교를 완료된 원시 자료만으로 집계한다."""
import os
for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[key]='1'
from datetime import datetime,timezone
import json
from pathlib import Path
import compare_variance as c

ROOT=Path(__file__).resolve().parent
CONTROL=ROOT/'index_full33_seed7_v1'
VARIANT=ROOT/'fresh_variance_variant/runs'


def exact(a,b):
    import torch
    if torch.is_tensor(a):return torch.is_tensor(b) and torch.equal(a,b)
    if isinstance(a,dict):return isinstance(b,dict) and a.keys()==b.keys() and all(exact(x,b[k]) for k,x in a.items())
    if isinstance(a,(list,tuple)):return type(a)==type(b) and len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
    if hasattr(a,'shape'):return type(a)==type(b) and a.shape==b.shape and bool((a==b).all())
    return a==b


def run(path,evaluation,pins):
    row=c.collect_run(path,evaluation,pins)
    if row['status']=='completed':
        report=c.read(Path(path)/'report.json')
        if any(report.get(k) for k in ('changed_inputs','missing_import_pins','cleanup_errors')) or report.get('lifecycle_verified') is False:
            raise ValueError('완료 자료 lifecycle/입력 검증 실패: '+str(path))
        config=report['settings']['structured_press']
        if config['stage']!='free_v9' or config['finger']!='index' or config['song']!='virtual_finger_v9_index_s3_f4':
            raise ValueError('601열 자유 검지 목표 계약 불일치')
        row['updates_in_run']=report.get('updates_in_run')
    return row


def source_proof(pins):
    paths=dict(control_initial=CONTROL/'100/train/J/initial.pt',variant_initial=VARIANT/'100/train/J/initial.pt',
        source100=VARIANT/'100/train/J/final.pt',resume200=VARIANT/'200/train/J/initial.pt')
    missing=[str(path) for path in paths.values() if not path.exists()]
    if missing:return dict(status='pending',missing=missing)
    import torch
    torch.set_num_threads(1)
    for path in paths.values():pins[str(path)]=c.digest(path)
    saved={key:torch.load(path,map_location='cpu',weights_only=False) for key,path in paths.items()}
    initial_keys=('model','torch_rng','cuda_rng','numpy_rng','python_rng')
    resume_keys=initial_keys+('actor_optimizer','value_optimizer','updates')
    initial={key:exact(saved['control_initial'][key],saved['variant_initial'][key]) for key in initial_keys}
    resume={key:exact(saved['source100'][key],saved['resume200'][key]) for key in resume_keys}
    if not all(initial.values()) or not all(resume.values()):raise ValueError('실제 fresh/strictresume 대응 불일치')
    return dict(status='verified',initial_control_exact=initial,strict_resume_exact=resume,
        source_updates=saved['source100']['updates'],resume_initial_updates=saved['resume200']['updates'],
        no_A_weights_transferred=True)


def settings_proof(pins):
    result={}
    for updates in (100,200):
        paths=[base/str(updates)/'train/settings.json' for base in (CONTROL,VARIANT)]
        if not all(path.exists() for path in paths):return dict(status='pending')
        a,b=(c.read(path) for path in paths)
        for path in paths:pins[str(path)]=c.digest(path)
        if 'structured_transfer' in a or 'structured_transfer' in b:raise ValueError('fresh 조건에 A 가중치 이전 있음')
        for saved in (a,b):
            if tuple(saved.get(k) for k in ('num_envs','horizon','updates','seed','size'))!=(64,32,100,7,'large'):
                raise ValueError('계획된64/H32/100/seed7/large 불일치')
        baseline={k:v for k,v in b.items() if k not in ('variance_variant','fresh_variance')}
        if a!=baseline:raise ValueError('분산 외 fresh 설정 변경: '+str(updates))
        config=b.get('variance_variant',{})
        if config.get('factor')!=.1 or config.get('selected_axes')!=[17,18,19,20] or not b.get('fresh_variance'):
            raise ValueError('fresh factor/marker 불일치')
        result[str(updates)]=dict(only_sigma_variant_and_fresh_identity_fields_differ=True,
            same_initial_pose_physics_rewards_gamma_ppo=True,goal_axes=[17,18,19,20],factor=.1)
    return dict(status='verified',blocks=result)


def gate(result):
    reasons=[]
    for key in ('source_proof','settings_proof'):
        if result[key].get('status')!='verified':reasons.append(key+' 미검증')
    proof=result['source_proof']
    for key in ('initial_control_exact','strict_resume_exact'):
        if not proof.get(key) or any(x is not True for x in proof[key].values()):reasons.append(key+' 미검증')
    if proof.get('status')=='verified' and (proof.get('source_updates')!=100 or proof.get('resume_initial_updates')!=100):
        reasons.append('100회 checkpoint 재개 업데이트 불일치')
    for name,row in result['training'].items():
        if (row['status']!='completed' or row.get('updates_in_run')!=100 or row.get('committed_transitions')!=204800 or
                row.get('optimizer_updates')!=int(name.rsplit('_',1)[1])):
            reasons.append(name+' 100회/204800전이 블록 미완료')
    for name,row in result['evaluations'].items():
        if row['status']!='completed' or row.get('metrics',{}).get('count')!=32:reasons.append(name+' raw32 미완료')
    for updates in (100,200):
        audit=result['native_audits'].get(str(updates),{})
        required={'model','torch_rng','cuda_rng','numpy_rng','python_rng'}
        if updates==200:required|={'actor_optimizer','value_optimizer','updates'}
        if set(audit.get('exact_equal',{}))!=required or any(x is not True for x in audit.get('exact_equal',{}).values()):
            reasons.append(str(updates)+' native 감사 미검증')
        if updates==200 and audit.get('strict_resume') is not True:reasons.append('200회 strictresume 미검증')
    return dict(ready=not reasons,reasons=reasons)


def collect():
    pins={str(Path(c.__file__)):c.digest(c.__file__)}
    result=dict(schema='structured_press.fresh_variance_analysis.v1',updated_utc=datetime.now(timezone.utc).isoformat(),
        training={},evaluations={},native_audits={},input_sha256=pins,production_unchanged=True,
        goal=dict(finger='index',physical_string=3,fret=4),formal_stage_promotion=False)
    for name,base in (('control',CONTROL),('variant',VARIANT)):
        for updates in (100,200):
            result['training'][name+'_'+str(updates)]=run(base/str(updates)/'train/J',False,pins)
            result['evaluations'][name+'_'+str(updates)]=run(base/str(updates)/'evaluate_final',True,pins)
            if updates==100:result['evaluations'][name+'_initial']=run(base/'100/evaluate_initial',True,pins)
            if name=='variant':
                path=base/str(updates)/'train/report.json'
                if path.exists():result['native_audits'][str(updates)]=c.read(path).get('initial_native_audit',{})
    result['source_proof']=source_proof(pins);result['settings_proof']=settings_proof(pins)
    result['gate']=gate(result);result['interpretation']='완료 자료 또는 실제 초기화/재개 증거 대기 중이며 효과를 추정하지 않음'
    if result['gate']['ready']:
        metrics=result['evaluations'];score=lambda key:(metrics[key]['metrics']['safe_success'],metrics[key]['metrics']['mean_safe_clean_s'])
        result['interpretation']={str(updates):dict(better_deterministic_than_control=score('variant_'+str(updates))>score('control_'+str(updates)),
            variant_failure_zero=metrics['variant_'+str(updates)]['metrics']['failure_episodes']==0) for updates in (100,200)}
    result['selection']=dict(status='pending',replace_existing_best=False)
    if result['gate']['ready']:
        evaluations=result['evaluations']
        rank=lambda name:(evaluations[name]['metrics']['safe_success'],evaluations[name]['metrics']['mean_safe_clean_s'])
        best_control=max(('control_100','control_200'),key=rank)
        best_variant=max(('variant_100','variant_200'),key=rank)
        result['selection']=dict(status='verified',best_control=best_control,best_variant=best_variant,
            better_than_existing_full33_best=rank(best_variant)>rank(best_control),
            replace_existing_best=False,production_unchanged=True,
            reason='동일 예산 비교와 기존 최고 모델 대체 여부를 구분하며 단일 목표 실험으로 자동 교체하지 않음')
    for path,sha in pins.items():
        if c.digest(path)!=sha:raise ValueError('분석 중 입력 변경: '+path)
    result['analysis_script_sha256']=c.digest(__file__)
    return result


def write(result):
    lines=['# 전축 fresh 목표 손가락 분산 비교','','집계 시각: '+result['updated_utc'],'',
        '동일601열·33활성축·원래v9·검지 줄3/프렛4·seed7에서 처음부터100+100회 학습한다. '
        '변경 요인은 목표4축 sigma0.1배뿐이다. A 가중치 이전이 없고 기존 IK 팔 출력 bias와 초기 물리 자세를 유지한다. '
        '같은 적응 LR 규칙이지만 실제 사용 LR은 KL 재시도에 따라 달라질 수 있다.','',
        '## 고정 모델 결정적 최초32환경 평가','','| 조건 | 분모 | 안전 성공 | 평균 safe clean(초) | 실패 |','|---|---:|---:|---:|---:|']
    for name,row in result['evaluations'].items():lines.append('| {} | {} | {} | {} | {} |'.format(name,*c.display(row)))
    lines+=['','## 학습 중 변화하는 확률 정책','','| 블록 | 완료 episode | 안전 성공 | 평균 safe clean(초) | 실패 |','|---|---:|---:|---:|---:|']
    for name,row in result['training'].items():lines.append('| {} | {} | {} | {} | {} |'.format(name,*c.display(row)))
    lines+=['','학습 완료 episode와 고정 정책 평가를 구분한다. 실패를 분모에서 빼지 않으며 미완료 episode는 성공이 아니다. '
        '100회와200회 학습 표는 각100회 블록에서 완료된 episode이고,200회 평가는 누적200회 모델이다.','',
        '## 학습 블록별9항 보상 평균','','| 항목 | 기본100 | 분산0.1 100 | 기본200블록 | 분산0.1 200블록 |','|---|---:|---:|---:|---:|']
    for key,label in c.analysis.TERMS.items():
        values=[]
        for name in ('control_100','variant_100','control_200','variant_200'):
            value=result['training'][name].get('metrics',{}).get('reward_components_mean',{}).get(key)
            values.append('—' if value is None else '{:.6f}'.format(value))
        lines.append('| {} | {} | {} | {} | {} |'.format(label,*values))
    for name,row in result['training'].items():
        lr=row.get('lr',{});lines+=['',name+' 비용(물리 실패 포함): `'+json.dumps(row.get('metrics',{}).get('cost_components_mean'),ensure_ascii=False)+'`',
            '{} 실제 LR 최소/최대 {}/{}; KL 재시도 {}.'.format(name,lr.get('minimum_used_actor_lr'),lr.get('maximum_used_actor_lr'),lr.get('total_retries'))]
    for title,key in (('실제 초기 전체 모델/RNG 및 strict 재개','source_proof'),('단일 요인 설정','settings_proof'),
        ('실제 실행의 native 감사','native_audits'),('완료 증거 gate','gate'),('판단','interpretation')):
        lines+=['','## '+title,'','`'+json.dumps(result[key],ensure_ascii=False)+'`']
    if result['gate']['ready']:
        e=result['evaluations']
        lines+=['','## 동일 예산 개선과 기존 최고 보존','',
            '분산0.1은200회 동일 예산에서 기존200회 {}/32 대비 {}/32로 개선되었다. 그러나 기존 full33 최고100회 모델의 {}/32·평균 safe clean {:.4f}초보다 '
            '새200회 모델의 {}/32·{:.4f}초가 낮으므로 대체하지 않는다.'.format(
                e['control_200']['metrics']['safe_success'],e['variant_200']['metrics']['safe_success'],
                e['control_100']['metrics']['safe_success'],e['control_100']['metrics']['mean_safe_clean_s'],
                e['variant_200']['metrics']['safe_success'],e['variant_200']['metrics']['mean_safe_clean_s']),
            '', '선택 판단: `'+json.dumps(result['selection'],ensure_ascii=False)+'`']
    lines+=['','B 후보 전용 fixed-reset 보정은 사용하지 않고 원래 full33 공식 평가를 유지한다. '
        '전체 초기 모델/RNG와 동일 초기화 코드·설정의 증거를 기록하며, 환경별 실제 q/hold를 별도 캡처해 정확 비교한 실험으로 표현하지 않는다. '
        '단일 검지 목표·seed7·동일 기하의 비교이고 새 목표 일반화나 과거557열 production 재현이 아니다. '
        '이 full33 실험에서는 원래 full33 최고100회 체크포인트를 보존한다. 별도 절차에서 확보한 A/B0 후보도 함께 보존하며, 서로 다른 절차의 최고 성과를 이번 동일 예산 비교와 혼동하지 않는다. 생산 코드는 자동 변경하지 않는다. '
        '입력 SHA·원시 분모·보상·비용·실패·LR 전체는 동명 JSON에 기록한다.']
    (ROOT/'FRESH_VARIANCE_ANALYSIS.md').write_text('\n'.join(lines)+'\n')
    (ROOT/'FRESH_VARIANCE_ANALYSIS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    result=collect();write(result);print(json.dumps(result['gate'],ensure_ascii=False))
