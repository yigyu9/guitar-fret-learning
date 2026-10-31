"""독립 seed17 fresh 분산 실험을 실제 완료 자료와 초기/재개 증거로 집계한다."""
from datetime import datetime,timezone
import json
from pathlib import Path
import FRESH_VARIANCE_ANALYSIS as f
import SEED17_FULL33_ANALYSIS as s

ROOT=Path(__file__).resolve().parent
CONTROL=ROOT/'full33_seed17'
VARIANT=ROOT/'fresh_variance_variant/runs/seed17'
c=f.c


def proof(pins):
    paths=dict(control=CONTROL/'100/train/J/initial.pt',variant=VARIANT/'100/train/J/initial.pt',
        final100=VARIANT/'100/train/J/final.pt',initial200=VARIANT/'200/train/J/initial.pt')
    if not all(p.exists() for p in paths.values()):return dict(status='pending')
    import torch
    torch.set_num_threads(1)
    saved={k:torch.load(p,map_location='cpu',weights_only=False) for k,p in paths.items()}
    for p in paths.values():pins[str(p)]=c.digest(p)
    keys=('model','torch_rng','cuda_rng','python_rng','numpy_rng')
    initial={k:f.exact(saved['control'][k],saved['variant'][k]) for k in keys}
    resume={k:f.exact(saved['final100'][k],saved['initial200'][k]) for k in keys+('actor_optimizer','value_optimizer','updates')}
    if not all(initial.values()) or not all(resume.values()):raise ValueError('seed17 실제 초기/재개 불일치')
    return dict(status='verified',initial_control_exact=initial,strict_resume_exact=resume,
        source_updates=saved['final100']['updates'],resume_initial_updates=saved['initial200']['updates'])


def settings_proof(pins):
    for n in (100,200):
        paths=[base/str(n)/'train/settings.json' for base in (CONTROL,VARIANT)]
        if not all(p.exists() for p in paths):return dict(status='pending')
        a,b=(c.read(p) for p in paths)
        for p in paths:pins[str(p)]=c.digest(p)
        for saved in (a,b):
            if 'structured_transfer' in saved or tuple(saved.get(k) for k in ('seed','num_envs','horizon','updates','size'))!=(17,64,32,100,'large'):
                raise ValueError('seed17 fresh64/H32/100 예산 불일치')
        if a!={k:v for k,v in b.items() if k not in ('variance_variant','fresh_variance')}:
            raise ValueError('분산 외 설정 변경')
        if b.get('variance_variant',{}).get('factor')!=.1 or b['variance_variant'].get('selected_axes')!=[17,18,19,20] or not b.get('fresh_variance'):
            raise ValueError('목표4축 factor.1/생성 계약 불일치')
    return dict(status='verified',only_goal4_sigma_and_identity_changed=True,no_A_transfer=True)


def gate(result):
    verdict=f.gate(result)
    for name,row in result['evaluations'].items():
        if name.endswith('initial'):continue
        if result['evaluation_source_proof'].get(name) is not True:verdict['reasons'].append(name+' 실제 checkpoint SHA 미검증')
    verdict['ready']=not verdict['reasons']
    return verdict


def collect():
    pins={str(Path(__file__)):c.digest(__file__),str(Path(f.__file__)):c.digest(f.__file__),
        str(Path(s.__file__)):c.digest(s.__file__),str(Path(c.__file__)):c.digest(c.__file__)}
    result=dict(schema='structured_press.fresh_variance_seed17.v1',updated_utc=datetime.now(timezone.utc).isoformat(),
        training={},evaluations={},native_audits={},evaluation_source_proof={},input_sha256=pins,production_unchanged=True)
    failed=ROOT/'fresh_variance_variant/seed17/100/train/report.json'
    result['preserved_setup_attempt']=dict(status='not_present',model_failure=False)
    if failed.exists():
        report=c.read(failed);pins[str(failed)]=c.digest(failed)
        trace=str(report.get('failure',{}))
        setup=(report.get('completed') is False and report.get('training_transitions')==0 and
            'FileNotFoundError' in trace and '_pins' in trace and 'settings.json' in trace)
        result['preserved_setup_attempt']=dict(status='input_pin_setup_failure' if setup else 'unclassified_failure',
            path=str(failed),completed=report.get('completed'),training_transitions=report.get('training_transitions'),
            failure=report.get('failure'),model_failure=False if setup else None,
            included_in_model_performance=False,original_attempt_preserved=True)
        for p in (failed.parents[2]/'bootstrap.py',failed.parents[2]/'train100.console.log'):
            if p.exists():pins[str(p)]=c.digest(p)
    for name,base in (('control',CONTROL),('variant',VARIANT)):
        for n in (100,200):
            key=name+'_'+str(n)
            result['training'][key]=f.run(base/str(n)/'train/J',False,pins)
            if name=='control':
                row=s.load(base/'evaluate'/(str(n)+'_latent_mean'),'latent_mean',pins)
                for field in ('initial','curve_mean'):row.pop(field,None)
            else:
                row=f.run(base/str(n)/'evaluate_final',True,pins)
                report=base/str(n)/'train/report.json'
                if report.exists():
                    native=c.read(report);result['native_audits'][str(n)]=native.get('initial_native_audit',{})
                    bootstrap=native.get('seed17_bootstrap',{})
                    if bootstrap:
                        for p,expected in bootstrap['input_sha256'].items():
                            if c.digest(p)!=expected:raise ValueError('bootstrap 감사 입력 변경')
                            pins[p]=expected
            result['evaluations'][key]=row
            cp=base/str(n)/'train/J/final.pt'
            sha=row.get('checkpoint_sha256',row.get('source_checkpoint_sha256'))
            result['evaluation_source_proof'][key]=bool(cp.exists() and sha==c.digest(cp))
        optional=base/'100/evaluate_initial'
        if name=='variant' and optional.exists():result['optional_initial']=f.run(optional,True,pins)
    result['source_proof']=proof(pins);result['settings_proof']=settings_proof(pins)
    result['gate']=gate(result)
    result['interpretation']='자료·실제 초기 전체 모델/RNG·재개·원시32 분모 검증 전 효과 판단 보류'
    if result['gate']['ready']:
        result['interpretation']={str(n):dict(success_delta=result['evaluations']['variant_'+str(n)]['metrics']['safe_success']-result['evaluations']['control_'+str(n)]['metrics']['safe_success'],
            safe_clean_delta=result['evaluations']['variant_'+str(n)]['metrics']['mean_safe_clean_s']-result['evaluations']['control_'+str(n)]['metrics']['mean_safe_clean_s']) for n in (100,200)}
    for p,value in pins.items():
        if c.digest(p)!=value:raise ValueError('집계 중 입력 SHA 변경: '+p)
    return result


def write(result):
    lines=['# 독립 seed17 fresh 분산 비교','',
        '원본 seed17 fresh full33와 목표4축 sigma0.1배만 변경한100+100회를 비교한다. A 가중치 이전이 없다. '
        '동일 적응 LR 규칙이며 실제 LR은 KL 재시도에 따라 달라질 수 있다. 초기 전체 모델과 Python/numpy/CPU/CUDA RNG, '
        '100→200의 모델·두 Adam·업데이트·전체 RNG를 실제 파일에서 비교한다.','',
        '| 구분 | 조건 | 상태 | 분모 | 안전성공 | safe clean초 | 실패 |','|---|---|---|---:|---:|---:|---:|']
    for group in ('training','evaluations'):
        for name,row in result[group].items():lines.append('| {} | {} | {} | {} | {} | {} | {} |'.format(group,name,row['status'],*c.display(row)))
    for key in ('preserved_setup_attempt','source_proof','settings_proof','native_audits','evaluation_source_proof','gate','interpretation'):
        lines+=['','## '+key,'','`'+json.dumps(result[key],ensure_ascii=False)+'`']
    lines+=['','학습 완료 episode는 변화하는 확률 정책의 결과이고 평가는 저장 모델의 latent-mean 결정 실행 최초32환경이다. '
        '실패를 분모에서 제외하지 않는다. 보상9항·물리 비용·LR과 원시 분모는 JSON에 있다. '
        '원본 진단에는 시점별 trace가 있으나 variant 공식 평가에는 없으므로 공통 비교는 비할인 episode 합계이다. '
        'variant 평가에서 환경별 q/hold를 별도 저장하지 않으므로 실제32행 물리 초기상태 exact 대응을 주장하지 않는다. '
        '동일 초기 모델/전체 RNG와 봉인된 초기화 설정 검증 범위로 한정한다. 요청각 기댓값 진단과 혼합하지 않으며 '
        '단일 검지 줄3/프렛4·seed17의 독립 재현이지 새 목표 일반화가 아니다. 생산 기본값이나 기존 최고 모델은 자동 교체하지 않는다.']
    for suffix,text in (('md','\n'.join(lines)+'\n'),('json',json.dumps(result,ensure_ascii=False,indent=2)+'\n')):
        (ROOT/('FRESH_VARIANCE_SEED17_ANALYSIS.'+suffix)).write_text(text)


if __name__=='__main__':
    result=collect();write(result);print(json.dumps(result['gate'],ensure_ascii=False))
