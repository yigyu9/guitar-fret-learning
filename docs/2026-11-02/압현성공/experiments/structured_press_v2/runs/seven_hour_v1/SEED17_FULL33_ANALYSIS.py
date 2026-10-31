"""seed17 전축 fresh 재현을 원본 seed7과 CPU에서 검증·집계한다. GPU 실행은 없다."""
from datetime import datetime,timezone
import json
from pathlib import Path
import numpy as np
import DISCOUNTED_REWARD_ANALYSIS as audit
import EXPECTED_ANGLE_ANALYSIS as expected
from FROZEN_SAMPLING_ANALYSIS import pair_gate
from FRESH_VARIANCE_ANALYSIS import exact

ROOT=Path(__file__).resolve().parent
BASE=ROOT/'full33_seed17'
LABELS=('initial_latent_mean','100_latent_mean','100_requested_angle_mean','100_stochastic',
    '200_latent_mean','200_requested_angle_mean','200_stochastic')


def load(path,mode,pins):
    if mode=='stochastic':
        item=audit.load_dataset(path,pins)
        if item['status']=='completed':
            summary=audit.read(path/'summary.json');native=audit.read(path/'native/report.json')
            for report in (summary,native):
                if (report.get('policy_mode')!='stochastic_frozen_checkpoint' or report.get('sampling_scale')!=1. or
                    report.get('saved_mean_and_std_unchanged') is not True):raise ValueError('원래 Gaussian stochastic provenance 누락')
            item['codec']=expected.codec_proof(path,pins)
        return item
    return expected.expected_dataset(path,mode,pins)


def qhold_equal(a,b):
    if a.get('status')!='completed' or b.get('status')!='completed':return dict(verified=False,reason='자료 대기')
    same=all(np.array_equal(a['initial'][key],b['initial'][key]) for key in ('q105','hold105')) and a.get('codec')==b.get('codec')
    return dict(verified=same,scope='32행 실제 q105/hold105만 exact; body/root 전체 상태 동등성 아님')


def settings_proof(pins):
    pairs={}
    for updates in (100,200):
        paths=[ROOT/'index_full33_seed7_v1'/str(updates)/'train/settings.json',BASE/str(updates)/'train/settings.json']
        if not all(p.exists() for p in paths):return dict(status='pending')
        a,b=(audit.read(p) for p in paths)
        for path in paths:pins[str(path)]=audit.sha(path)
        if a['seed']!=7 or b['seed']!=17 or any('structured_transfer' in x for x in (a,b)):
            raise ValueError('fresh seed7→17 외 source 이전/seed 불일치')
        aa,bb=dict(a),dict(b);aa.pop('seed');bb.pop('seed')
        if aa!=bb:raise ValueError('seed 외 설정 변경: '+str(updates))
        if tuple(b.get(k) for k in ('num_envs','horizon','updates','size'))!=(64,32,100,'large'):
            raise ValueError('large64/H32/100 블록 예산 불일치')
        config=b['structured_press']
        if config['stage']!='free_v9' or config['active_axes']!=list(range(33)) or config['song']!='virtual_finger_v9_index_s3_f4':
            raise ValueError('동일 검지 자유33 목표 불일치')
        pairs[str(updates)]=dict(only_seed_changed=True,from_seed=7,to_seed=17,no_A_transfer=True)
    return dict(status='verified',blocks=pairs)


def resume_proof(pins):
    paths=[BASE/'100/train/J/final.pt',BASE/'200/train/J/initial.pt']
    if not all(p.exists() for p in paths):return dict(status='pending')
    import torch
    torch.set_num_threads(1)
    for path in paths:pins[str(path)]=audit.sha(path)
    a,b=(torch.load(path,map_location='cpu',weights_only=False) for path in paths)
    fields=('model','actor_optimizer','value_optimizer','updates','torch_rng','cuda_rng','python_rng','numpy_rng')
    flags={key:exact(a[key],b[key]) for key in fields}
    if not all(flags.values()) or a['updates']!=100 or b['updates']!=100:raise ValueError('seed17 strict resume 실물 불일치')
    return dict(status='verified',exact_equal=flags,source_updates=100,resume_initial_updates=100,
        source_sha256=pins[str(paths[0])],note='seed7과 초기 가중치가 같다는 주장이 아님; seed17 안의 strict100→200 복원 검증')


def gate(result):
    reasons=[]
    for key in ('settings_proof','resume_proof'):
        if result[key].get('status')!='verified':reasons.append(key+' 미완료')
    if (set(result['resume_proof'].get('exact_equal',{}))!={'model','actor_optimizer','value_optimizer','updates','torch_rng','cuda_rng','python_rng','numpy_rng'} or
        any(x is not True for x in result['resume_proof'].get('exact_equal',{}).values())):
        reasons.append('실제 model/Adam/전체RNG 복원 미검증')
    for name,row in result['training'].items():
        if row.get('status')!='completed' or row.get('updates_in_run')!=100 or row.get('optimizer_updates')!=int(name) or row.get('committed')!=204800:
            reasons.append(name+' 학습 블록 미완료')
    for name in LABELS:
        if result['seed17'][name].get('status')!='completed':reasons.append(name+' 평가 미완료/invalid')
        if result['source_checkpoint_proof'].get(name,{}).get('verified') is not True:reasons.append(name+' source checkpoint SHA 미검증')
    required_pairs=['initial_vs100']+[str(n)+'_'+mode for n in (100,200) for mode in ('requested_angle_mean','stochastic')]+['seed7_vs17_'+str(n) for n in (100,200)]
    for key in required_pairs:
        if result['pairing'].get(key,{}).get('verified') is not True:reasons.append(key+' 실제 초기 대응 미검증')
    for name,row in result['seed7_reference'].items():
        if row.get('status')!='completed':reasons.append('seed7 '+name+' 참조 미완료')
    return dict(ready=not reasons,reasons=reasons)


def collect():
    pins={str(Path(__file__)):audit.sha(Path(__file__)),str(Path(audit.__file__)):audit.sha(Path(audit.__file__)),
        str(Path(expected.__file__)):audit.sha(Path(expected.__file__))}
    result=dict(schema='structured_press.seed17_full33_analysis.v1',updated_utc=datetime.now(timezone.utc).isoformat(),
        seed17={},seed7_reference={},training={},pairing={},source_checkpoint_proof={},errors=[],input_sha256=pins,
        production_unchanged=True,scope='동일 검지 줄3/프렛4·동일 기하에서 seed만 변경한 독립 학습 재현; 새 목표 일반화 아님')
    labels=list(LABELS)
    if (BASE/'evaluate/200_normalized_action_mean').exists():labels.append('200_normalized_action_mean')
    for name in labels:
        mode='latent_mean' if name.endswith('latent_mean') else 'requested_angle_mean' if name.endswith('requested_angle_mean') else 'normalized_action_mean' if name.endswith('normalized_action_mean') else 'stochastic'
        path=BASE/'evaluate'/name
        try:
            item=load(path,mode,pins);result['seed17'][name]=item
            if item['status']=='completed':
                update='100' if name.startswith(('initial_','100_')) else '200'
                checkpoint=BASE/update/'train/J'/('initial.pt' if name.startswith('initial_') else 'final.pt')
                verified=checkpoint.exists() and audit.sha(checkpoint)==item['checkpoint_sha256']
                result['source_checkpoint_proof'][name]=dict(verified=verified,path=str(checkpoint),sha256=item['checkpoint_sha256'])
                if not verified:raise ValueError('평가 모델이 지정 학습 체크포인트와 다름')
        except (ValueError,KeyError,OSError) as error:
            result['seed17'][name]=dict(status='invalid',error=str(error));result['errors'].append(name+': '+str(error))
    for updates in (100,200):
        for mode,path in (('latent_mean',ROOT/'reward_trace'/('full'+str(updates))),
            ('requested_angle_mean',ROOT/'expected_angle'/('full'+str(updates)+'_requested_angle_mean')),
            ('stochastic',ROOT/'frozen_sampling'/('full100_v2' if updates==100 else 'full200'))):
            name=str(updates)+'_'+mode
            try:
                if mode=='latent_mean':
                    item=audit.load_dataset(path,pins)
                    if item['status']=='completed':item['codec']=expected.codec_proof(path,pins)
                else:item=load(path,mode,pins)
                result['seed7_reference'][name]=item
            except (ValueError,KeyError,OSError) as error:
                result['seed7_reference'][name]=dict(status='invalid',error=str(error));result['errors'].append('seed7 '+name+': '+str(error))
        path=BASE/str(updates)/'train/J';report_path=path/'report.json'
        row=dict(status='pending',path=str(path))
        if report_path.exists():
            report=audit.read(report_path);pins[str(report_path)]=audit.sha(report_path)
            row.update(status='completed' if report.get('completed') else 'failed_or_running',updates_in_run=report.get('updates_in_run'),
                optimizer_updates=report.get('optimizer_updates'),committed=report.get('journal',{}).get('committed'),failure=report.get('failure'))
            if row['status']=='completed':
                if report.get('lifecycle_verified') is not True or any(report.get(k) for k in ('failure','changed_inputs','missing_import_pins','cleanup_errors')):
                    raise ValueError('seed17 train lifecycle 불완전')
                row['metrics']=audit.analyze_all.aggregate(path,'index',False)
                for name in ('episodes.jsonl','episode_metadata.json'):pins[str(path/name)]=audit.sha(path/name)
        result['training'][str(updates)]=row
    result['settings_proof']=settings_proof(pins);result['resume_proof']=resume_proof(pins)
    for updates in (100,200):
        mean=result['seed17'][str(updates)+'_latent_mean']
        for mode in ('requested_angle_mean','stochastic'):
            other=result['seed17'][str(updates)+'_'+mode]
            pair=pair_gate(mean,other)
            if pair['verified'] and mean['codec']!=other['codec']:pair=dict(verified=False,reason='동일39축 codec 아님')
            result['pairing'][str(updates)+'_'+mode]=pair
        result['pairing']['seed7_vs17_'+str(updates)]=qhold_equal(result['seed7_reference'][str(updates)+'_latent_mean'],mean)
    if '200_normalized_action_mean' in result['seed17']:
        result['pairing']['optional_200_normalized_action_mean']=pair_gate(result['seed17']['200_latent_mean'],result['seed17']['200_normalized_action_mean'])
    result['pairing']['initial_vs100']=qhold_equal(result['seed17']['initial_latent_mean'],result['seed17']['100_latent_mean'])
    result['gate']=gate(result);result['interpretation']='시간 부족/미실행/부분 결과는 미완료로 남기며 재현 효과 판단 보류'
    if result['gate']['ready']:
        result['interpretation']={str(updates):{mode:dict(seed7_success=result['seed7_reference'][str(updates)+'_'+mode]['metrics']['safe_success'],
            seed17_success=result['seed17'][str(updates)+'_'+mode]['metrics']['safe_success'],
            seed17_safe_clean_s=result['seed17'][str(updates)+'_'+mode]['metrics']['mean_safe_clean_s'])
            for mode in ('latent_mean','requested_angle_mean','stochastic')} for updates in (100,200)}
    for group in ('seed17','seed7_reference'):
        for row in result[group].values():row.pop('initial',None);row.pop('curve_mean',None)
    audit.verify_pins(pins)
    return result


def write(result):
    lines=['# seed17 전축 fresh 독립 재현','','집계: '+result['updated_utc'],'',result['scope'],'',
        'A 가중치를 이전하지 않고 원래 Gaussian·large64/H32·100+100을 유지한다. '
        '학습 seed7→17만 변경한다. 평가는 고정reset4242의 실제 q/hold 대응으로 조건을 확인하며 서로 다른 seed의 학습 가중치가 같다고 주장하지 않는다.','',
        '| 자료 | 상태 | 안전성공/분모 | 평균safe clean초 | 최장연속clean초 | 할인reward(.99) | 할인cost(1) |','|---|---|---:|---:|---:|---:|---:|']
    for group in ('seed7_reference','seed17'):
        for name,row in result[group].items():
            m=row.get('metrics',{});lines.append('| {} {} | {} | {}/{} | {} | {} | {} | {} |'.format(group,name,row['status'],*[m.get(k) for k in ('safe_success','count','mean_safe_clean_s','mean_best_clean_s','discounted_reward_mean','discounted_cost_mean')]))
    lines+=['','## 학습','','| 블록 | 상태 | 완료episode | 안전성공 | 실패 |','|---|---|---:|---:|---:|']
    for name,row in result['training'].items():
        m=row.get('metrics',{});lines.append('| {} | {} | {} | {} | {} |'.format(name,row['status'],m.get('count'),m.get('safe_success'),m.get('failure_episodes')))
    for title,key in (('단일 요인 설정','settings_proof'),('100→200 strict 모델/두Adam/전체RNG','resume_proof'),
        ('실제 초기 q105/hold105와 source 대응','pairing'),('완료 gate','gate'),('재현 판단','interpretation')):
        lines+=['','## '+title,'','`'+json.dumps(result[key],ensure_ascii=False)+'`']
    lines+=['','같은 checkpoint의 Gaussian과 가중치는 유지하되 요청각 기댓값은 별도의 진단 배포 규칙이다. '
        '원래 latent 평균·확률 실행과 구분한다. 물리 응답의 기댓값이나 새 학습 성공이라고 표현하지 않는다. '
        'q/hold 일치는 body/root 전체 초기 상태 대응의 증거가 아니다. 단일 명목 자세의 반복32환경이며 새 곡/목표 일반화가 아니다. '
        '실패 포함 최초32·원시9항·보상γ.99/비용γ1·native lifecycle·source SHA를 검증한 자료만 판단한다. '
        '미실행/미완료 조건을0점 성과로 만들지 않는다. 남은 시간 때문에 실행하지 못한 경우도 pending으로 정직하게 남긴다. '
        '생산 코드와 기존 최고 모델을 자동 교체하지 않는다. 세부 보상/비용·source/model·입력 SHA는 JSON에 있다.']
    (ROOT/'SEED17_FULL33_ANALYSIS.md').write_text('\n'.join(lines)+'\n')
    (ROOT/'SEED17_FULL33_ANALYSIS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    result=collect();write(result);print(json.dumps(dict(gate=result['gate'],errors=result['errors']),ensure_ascii=False))
