"""완료된 native 시점별 보상만 CPU로 검증·집계한다. 학습/물리 변경 없음."""
import os
for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):
    os.environ[key]='1'
os.environ.setdefault('MPLCONFIGDIR','/tmp/discounted_reward_mpl')
from pathlib import Path
import argparse
import json
import hashlib
from datetime import datetime,timezone
import numpy as np
import analyze_all
import reward_trace_probe as probe

ROOT=Path(__file__).resolve().parent
LABELS=('full100','full200','full200_initial','index_A100_free','no_prior100')


def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_pins(pins):
    for name,expected in pins.items():
        path=Path(name)
        if not path.is_file() or sha(path)!=expected:
            raise ValueError('입력/출력 SHA 불일치: '+name)


def load_dataset(path,pins):
    summary_path=path/'summary.json'
    if not summary_path.exists():return dict(status='pending',path=str(path))
    summary=read(summary_path)
    if summary.get('completed') is not True:return dict(status='pending_or_failed',failure=summary.get('failure'),path=str(path))
    for key in ('strict_source_loaded','model_unchanged'):
        if summary.get(key) is not True:raise ValueError('완료 증거 누락: '+key)
    if summary.get('optimizer_updates_difference')!=0:raise ValueError('평가 optimizer 변경')
    if tuple(summary['term_names'])!=probe.TERMS:raise ValueError('9항 열 순서 불일치')
    if summary['reward_gamma']!=.99 or summary['cost_gamma']!=1.:raise ValueError('예상 PPO 할인 설정 불일치')
    verify_pins(summary['input_sha256']);verify_pins(summary['output_sha256'])
    pins.update(summary['input_sha256']);pins.update(summary['output_sha256']);pins[str(summary_path)]=sha(summary_path)
    report=read(path/'native/report.json')
    if report.get('completed') is not True or report.get('lifecycle_verified') is not True or any(
            report.get(k) for k in ('failure','changed_inputs','missing_import_pins','cleanup_errors')):
        raise ValueError('원본 native 수명주기 검증 실패')
    if report['checkpoint_sha256']!=summary['checkpoint_sha256']:raise ValueError('checkpoint SHA 출처 불일치')
    episodes=[row['episode'] for row in analyze_all.iter_episode_rows(path/'native')]
    trace=dict(np.load(path/'trace.npz',allow_pickle=False)); initial=dict(np.load(path/'initial.npz',allow_pickle=False))
    for k in ('q105','hold105'):
        if initial[k].shape!=(32,105) or not np.isfinite(initial[k]).all():raise ValueError('초기 q/hold shape/유한성')
        if hashlib.sha256(initial[k].tobytes()).hexdigest()!=summary['actual_initial_sha256'][k]:raise ValueError('실제 초기 SHA 불일치')
    if trace['terms'].shape[1:]!=(9,) or not np.isfinite(trace['terms']).all():raise ValueError('9항 shape/유한성')
    if set(trace['env'].tolist())!=set(range(32)):raise ValueError('trace 환경 분모 불일치')
    if any(len(v)!=len(trace['env']) for v in trace.values()):raise ValueError('trace 열 길이 불일치')
    for episode in episodes:
        mask=trace['env']==episode['env_id'];ticks=trace['tick'][mask]
        if not np.array_equal(ticks,np.arange(episode['steps'])) or trace['terminal'][mask].sum()!=1 or not trace['terminal'][mask][-1]:
            raise ValueError('최초 episode tick/종료 누락·중복')
    import torch
    rows=[dict((k,torch.from_numpy(trace[k][i]) if k=='terms' else trace[k][i]) for k in trace) for i in range(len(trace['env']))]
    checked=probe.reconcile(rows,episodes,reward_gamma=summary['reward_gamma'],cost_gamma=summary['cost_gamma'])
    if max(abs(row['discounted_shaping_terminal_zero_residual']) for row in checked)>2e-5:raise ValueError('potential 할인 등식 불일치')
    metrics=analyze_all.combine_episode_values(episodes,'index')
    metrics['discounted_terms_mean']={k:float(np.mean([row['discounted_terms'][k] for row in checked])) for k in probe.TERMS}
    metrics['discounted_reward_mean']=sum(metrics['discounted_terms_mean'].values())
    metrics['discounted_cost_mean']=float(np.mean([row['discounted_cost'] for row in checked]))
    metrics['max_shaping_residual']=max(abs(row['discounted_shaping_terminal_zero_residual']) for row in checked)
    metrics['episode_steps']=sorted(set(e['steps'] for e in episodes))
    metrics['actual_initial_diversity']={k:dict(unique_rows=int(np.unique(v,axis=0).shape[0]),
        maximum_axis_peak_to_peak_rad=float(np.ptp(v,axis=0).max())) for k,v in initial.items()}
    # 실제 조기종료 뒤에는 보상을 더하지 않고 누적값을 유지한다.
    curves=np.zeros((32,361,9))
    for i in range(32):
        mask=trace['env']==i;terms=trace['terms'][mask].astype(float)
        if len(terms)>360:raise ValueError('현재6초 진단의360tick 초과')
        cumulative=np.cumsum(terms*(summary['reward_gamma']**np.arange(len(terms)))[:,None],axis=0)
        curves[i,1:len(terms)+1]=cumulative
        curves[i,len(terms)+1:]=cumulative[-1]
    return dict(status='completed',path=str(path),metrics=metrics,initial=initial,
        curve_mean=curves.mean(0),checkpoint=report['checkpoint'],checkpoint_sha256=report['checkpoint_sha256'])


def comparison_gate(rows):
    reasons=[name+' 미완료' for name in LABELS if rows.get(name,{}).get('status')!='completed']
    if not reasons:
        baseline=rows['full100']['initial']
        for name in LABELS:
            for key in ('q105','hold105'):
                if not np.array_equal(baseline[key],rows[name]['initial'][key]):reasons.append(name+' actual '+key+' 불일치')
    return dict(ready=not reasons,reasons=reasons,definition='32환경 실제 q105/hold105 원소·행순서 정확 대응; 설정/seed 동일만으로 판정하지 않음')


def graphs(rows):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,1,figsize=(11,8),constrained_layout=True)
    musical=[1,2,3,4,5]
    for name in LABELS:
        curve=rows[name]['curve_mean'];axes[0].plot(np.arange(361)/60,curve[:,musical].sum(-1),label=name)
    axes[0].set(xlabel='Seconds',ylabel='Mean cumulative discounted music return',title='First 32 native episodes; reward gamma=.99; failures included')
    axes[0].legend();axes[0].axvspan(3,5.5,alpha=.1,color='green')
    x=np.arange(9);width=.16
    for j,name in enumerate(LABELS):axes[1].bar(x+(j-2)*width,[rows[name]['metrics']['discounted_terms_mean'][k] for k in probe.TERMS],width,label=name)
    axes[1].set_xticks(x);axes[1].set_xticklabels(['Approach','First contact','Clean hold','Achieve','Wrong','Deficit','Standby','Thumb','Action'],rotation=20)
    axes[1].set_ylabel('Mean discounted return per term');axes[1].axhline(0,color='black',linewidth=.5)
    path=ROOT/'DISCOUNTED_REWARD_ANALYSIS.png';fig.savefig(path,dpi=160);plt.close(fig);return path


def collect():
    pins={str(Path(__file__)):sha(Path(__file__)),str(Path(probe.__file__)):sha(Path(probe.__file__)),str(Path(analyze_all.__file__)):sha(Path(analyze_all.__file__))}
    rows={};errors=[]
    for name in LABELS:
        path=(ROOT/'no_alignment_prior_variant/runs/reward_trace_no_prior100_v2'
              if name=='no_prior100' else ROOT/'reward_trace'/name)
        try:rows[name]=load_dataset(path,pins)
        except (ValueError,KeyError,OSError) as error:rows[name]=dict(status='invalid',error=str(error));errors.append(name+': '+str(error))
    gate=comparison_gate(rows);proof=dict(status='pending')
    if all(rows[k]['status']=='completed' for k in ('full100','full200_initial')):
        import torch
        a,b=[torch.load(rows[k]['checkpoint'],map_location='cpu',weights_only=False) for k in ('full100','full200_initial')]
        same=set(a['model'])==set(b['model']) and all(torch.equal(v,b['model'][k]) for k,v in a['model'].items())
        proof=dict(status='verified' if same else 'mismatch',model_tensors_equal=same)
        if not same:
            gate['ready']=False;gate['reasons'].append('full100→full200_initial model 불일치')
    training={}
    for updates in ('100','200'):
        path=ROOT/'index_full33_seed7_v1'/updates/'train/J'
        training[updates]=analyze_all.aggregate(path,'index',False)
        for name in ('report.json','episodes.jsonl','episode_metadata.json'):
            if (path/name).exists():pins[str(path/name)]=sha(path/name)
    result=dict(training_stochastic_reference=training,schema='discounted_reward_analysis.v1',updated_utc=datetime.now(timezone.utc).isoformat(),datasets=rows,
        comparison_gate=gate,full100_vs_resume_initial_weights=proof,errors=errors,input_sha256=pins,
        interpretation='실제 완료·무결성·초기 대응 검증 전 효과 판단 보류')
    if gate['ready']:
        chart=graphs(rows);result['chart']=str(chart);result['chart_sha256']=sha(chart)
        result['interpretation']='실제 대응32환경 평균 정책 비교. raw 접근합은 할인 목적이 아니므로 직접 음악 성과로 읽지 않음.'
    for row in rows.values():row.pop('initial',None);row.pop('curve_mean',None)
    verify_pins(pins)
    return result


def write(result):
    lines=['# 실제 할인 보상 비교','','집계: '+result['updated_utc'],'',
        '원본 strict 평균 정책의 최초32 episode를 검증한다. 보상γ=.99, 비용γ=1이다. '
        '접근은 potential shaping이므로 비할인 합의 큰 음수를 곧바로 나쁜 정책이라고 읽으면 안 된다.','',
        '| 조건 | 상태 | 성공/분모 | clean초 | 비할인 reward | 할인 reward | 할인 cost |','|---|---|---|---|---|---|---|']
    for name,row in result['datasets'].items():
        m=row.get('metrics',{});lines.append('| {} | {} | {}/{} | {} | {} | {} | {} |'.format(name,row['status'],*[m.get(k) for k in ('safe_success','count','mean_safe_clean_s','mean_reward','discounted_reward_mean','discounted_cost_mean')]))
    lines+=['','실제 초기 대응/무결성 gate: `'+json.dumps(result['comparison_gate'],ensure_ascii=False)+'`','',result['interpretation'],'',
        '과거 학습 중 확률 정책의 성과(원본100회{}/{},200회{}/{})와 고정 평균 평가32/32→0/32는 서로 다른 지표다. '.format(
            result['training_stochastic_reference']['100']['safe_success'],result['training_stochastic_reference']['100']['count'],
            result['training_stochastic_reference']['200']['safe_success'],result['training_stochastic_reference']['200']['count'])+
        '학습 블록에서는 매 update 가중치와 확률 행동이 변한다. 이번 probe는 해당 지표를 재학습하거나 동일한 정책으로 간주하지 않는다. '
        '기존 FULL33_COLLAPSE_ANALYSIS 자료와 구별하여 원시 probe를 집계한다.','',
        '각9항 할인합·비용·Phi residual·native 원시 합 대조는 JSON에 기록한다. 누락/핀/실제 q 대응 실패 상태에서 효과 비교는 열지 않는다.', '',
        '초기 자세 다양성은 JSON의 actual_initial_diversity에 실제 q105/hold105의 고유 행 수와 축별 최대 범위를 기록한다. '
        '32환경의 q/hold가 같은 경우 동일한 명목 v9 DOF 자세의 반복 평가이며, 서로 다른32개 시작 자세의 일반화 검사가 아니다. '
        'q105/hold105의 일치는 body/root pose와 전체 물리 상태의 대응·다양성을 증명하지 않는다. 해당 전체 상태는 이번 기록으로 감사하지 않았다.']
    lines+=['']
    for name,row in result['datasets'].items():
        diversity=row.get('metrics',{}).get('actual_initial_diversity')
        if diversity:
            lines+=['- {}: q105 고유 {}개 / hold105 고유 {}개; 최대 축 범위 {} / {} rad.'.format(name,
                diversity['q105']['unique_rows'],diversity['hold105']['unique_rows'],
                diversity['q105']['maximum_axis_peak_to_peak_rad'],diversity['hold105']['maximum_axis_peak_to_peak_rad'])]
    if result.get('chart'):lines+=['','![할인 보상 비교]('+result['chart']+')']
    (ROOT/'DISCOUNTED_REWARD_ANALYSIS.md').write_text('\n'.join(lines)+'\n')
    (ROOT/'DISCOUNTED_REWARD_ANALYSIS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    result=collect();write(result);print(json.dumps(result['comparison_gate'],ensure_ascii=False))
