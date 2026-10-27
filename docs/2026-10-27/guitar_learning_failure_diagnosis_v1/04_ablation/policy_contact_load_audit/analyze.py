"""CPU-only, saved env0/60Hz load and joint audit. No model or scene replay."""
import csv
import hashlib
import json
import math
import os
from pathlib import Path

os.environ.setdefault('MPLCONFIGDIR','/tmp/policy_contact_load_mpl')
import numpy as np
from scipy.spatial.transform import Rotation
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]
SHORT=BASE/'03_short_learning'
FINGERS=('thumb','index','middle','ring','pinky')
JOINTS=('LH:thumb1_x','LH:thumb1_y','LH:thumb1_z','LH:thumb2','LH:thumb3',
    'LH:middle1_x','LH:middle1_z','LH:middle2','LH:middle3','LH:index3','LH:ring3','LH:pinky3')
THRESHOLDS=(1.,10.,25.,50.)
BAND=math.radians(.25)


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())
def write(name,value):
    (HERE/name).write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')


def selection():
    rows=[]
    for seed in (7,17):
        for mode in ('incremental','position'):
            folder=SHORT/(f'pilot_{mode}_seed{seed}_v2'+('_retry2' if mode=='incremental' and seed==7 else ''))
            names=['evaluation_initial_reference','evaluation_000300']
            if mode=='incremental':names+=['evaluation_initial_zero','evaluation_000050','evaluation_000100','evaluation_000150']
            for name in names:
                rows.append(dict(label=f'{mode}_s{seed}_{name.replace("evaluation_","")}',kind='short',path=str(folder/name),seed=seed,mode=mode))
    rows.append(dict(label='stage2_live_reference_env0',kind='short',
        path=str(BASE/'02_contact_reward/live_release_probe/run_01'),seed=7,mode='incremental',supplement=True))
    rows.append(dict(label='stage2_direction_original_env0',kind='direction',
        path=str(BASE/'02_contact_reward/facing_direction_probe/run_01'),seed=7,mode='incremental',supplement=True))
    return rows


def max_span(mask,t):
    best=0.;start=last=None
    for on,at in zip(mask,t):
        if on:
            if last is None or abs(at-last-1/60)>1e-8:start=at
            last=at;best=max(best,float(at-start))
        else:start=last=None
    return best


def stats(values,t,mask):
    x=values[mask]
    return dict(endpoint_count=len(x),minimum=float(x.min()) if len(x) else None,
        maximum=float(x.max()) if len(x) else None,p95=float(np.percentile(x,95)) if len(x) else None,
        mean=float(x.mean()) if len(x) else None,
        threshold_exposure={str(level):dict(endpoint_count=int(np.sum(mask&(values>=level))),
            endpoint_fraction=float(np.mean(x>=level)) if len(x) else None,
            max_consecutive_endpoint_span_s=max_span(mask&(values>=level),t)) for level in THRESHOLDS})


def main():
    assert max_span(np.array([True]),np.array([1/60]))==0
    assert abs(max_span(np.array([True,True,True]),np.array([1,1+1/60,1+2/60]))-2/60)<1e-12
    assert max_span(np.array([True,True]),np.array([1,2]))==0
    chosen=selection();input_paths=[Path(__file__)];source_pins={};source_conflicts=[];summaries=[];samples={};tables=[]
    for item in chosen:
        p=Path(item['path'])
        trace=p/('physics240.npz' if item['kind']=='direction' else 'trace_env0_episode0.npz')
        contract_path=p/('original_training_contract.json' if item['kind']=='direction' else 'training_contract.json')
        metadata_path=p/('report.json' if item['kind']=='direction' else 'trace_metadata.json')
        input_paths += [trace,contract_path,metadata_path,p/'settings.json',p/'inputs_before.json']
        if (p/'evaluation.json').is_file():input_paths.append(p/'evaluation.json')
        if item['kind']=='direction':input_paths.append(p/'first_attempt_episodes.json')
        stored=read(p/'inputs_before.json')
        for name,value in stored.items():
            if '/guitar_learning/' in name and Path(name).suffix in ('.py','.xml','.json','.obj','.stl'):
                if name in source_pins and source_pins[name]!=value:source_conflicts.append(name)
                source_pins[name]=value
    paths=sorted(set(input_paths));pins={str(p):sha(p) for p in paths}
    write('selection.json',dict(post_capture_cpu_audit=True,selection='all saved env0 traces in fixed requested seed/mode/checkpoint list; no result-based omission',datasets=chosen,
        phases=dict(preparation='0<t<press',settled_preparation='2<=t<press',press_window='press<=t<=end',audible='onset<=t<=end',late='t>end'),
        sampling='60Hz native endpoints only; direction240 trace selects clocks4,8,... for declared env0, no new replay',
        force_thresholds_n=list(THRESHOLDS),threshold_role='descriptive bins only, not physical safety/pressure limits',
        actual_joint_near_limit_band_rad=BAND,target_boundary_tolerance_rad=1e-5,
        exposure='consecutive recorded endpoint span last-first; no guarantee between endpoints; never count/60 as actual duration',
        source_sha_conflicts=source_conflicts,input_sha256=pins))
    assert not source_conflicts
    for item in chosen:
        p=Path(item['path']);label=item['label'];contract=read(p/('original_training_contract.json' if item['kind']=='direction' else 'training_contract.json'))
        settings=read(p/'settings.json');view=settings['song']['short_learning']['view'];ctrl=contract['native_backend']['control']
        plane=np.asarray(contract['reward']['surface_learning']['press_surface']['plane_G'],float);unit=plane[:3]/np.linalg.norm(plane[:3])
        if item['kind']=='short':
            meta=read(p/'trace_metadata.json');a=np.load(p/'trace_env0_episode0.npz')
            t=a['time_s'];q=a['q'];target=a['target'];body=a['body_state'];force_all=a['net_body_force_n']
            names=meta['joint_names'];body_names=meta['body_names'];g=body[:,body_names.index('guitar/guitar')]
            force=np.stack([force_all[:,body_names.index('human/LH:'+f+'3')] for f in FINGERS],axis=1)
            normal_world=Rotation.from_quat(g[:,3:7]).apply(np.tile(unit,(len(t),1)))
            normal_force=np.einsum('tfc,tc->tf',force,normal_world)
            resultant=np.linalg.norm(force,axis=-1)
            inverse=np.stack([Rotation.from_quat(g[:,3:7]).inv().apply(force[:,f])@unit for f in range(5)],axis=-1)
            np.testing.assert_allclose(normal_force,inverse,atol=1e-10,rtol=0)
            joint_indices=[names.index(name) for name in JOINTS];selected_q=q[:,joint_indices];selected_target=target[:,joint_indices]
            candidate=a['candidate'];wrong=a['wrong'];distance=a['surface_distance_m'];height=a['surface_height_m']
            executed=a['executed_action'];raw_q=selected_q.copy();raw_target=selected_target.copy()
            raw_body=body[:,[body_names.index('guitar/guitar')]+[body_names.index('human/LH:'+f+'3') for f in FINGERS]].copy()
            evaluation=read(p/'evaluation.json');episode=next(r for r in evaluation['episodes'] if r['env_id']==0)
            outcome=dict(achieved=episode['achieved'],clean_fraction=episode['clean_fraction'],wrong_fraction=episode['audible_wrong_fraction'],reason=episode['reason'])
            a.close();available=list(FINGERS)
        else:
            a=np.load(p/'physics240.npz');pick=(a['clock'][:,0]%4==0)&a['first_attempt'][:,0]
            t=a['local_time_s'][pick,0];g=a['guitar_pose'][pick,0]
            force=np.full((len(t),5,3),np.nan);force[:,2]=a['distal_force_n'][pick,0]
            normal_world=Rotation.from_quat(g[:,3:7]).apply(np.tile(unit,(len(t),1)))
            resultant=np.linalg.norm(force,axis=-1);normal_force=np.einsum('tfc,tc->tf',force,normal_world)
            selected_q=np.full((len(t),len(JOINTS)),np.nan);selected_target=selected_q.copy()
            for k,name in enumerate(('LH:middle1_x','LH:middle1_z','LH:middle2','LH:middle3')):
                j=JOINTS.index(name);selected_q[:,j]=a['q4'][pick,0,k];selected_target[:,j]=a['target4'][pick,0,k]
            candidate=a['candidate'][pick,0];wrong=a['wrong'][pick,0]
            raw_q=a['q4'][pick,0].copy();raw_target=a['target4'][pick,0].copy();raw_body=np.stack([a['distal_pose'][pick,0],g],axis=1)
            distance=np.full(len(t),np.nan);height=np.full(len(t),np.nan);executed=None
            episode=next(r for r in read(p/'first_attempt_episodes.json') if r['env_id']==0);note=episode['selected_raw_note']
            outcome=dict(achieved=note['left'],clean_fraction=note['clean']/(view['local_end_s']-view['local_onset_s']),wrong_fraction=note['wrong']/(view['local_end_s']-view['local_onset_s']),reason=episode['reason'])
            a.close();available=['middle']
        assert len(t)==218 and np.allclose(t,np.arange(1,219)/60,rtol=0,atol=1e-12)
        press,onset,end=(view[k] for k in ('local_press_s','local_onset_s','local_end_s'))
        phases=dict(preparation=(t<press),settled_preparation=(t>=2)&(t<press),press_window=(t>=press)&(t<=end),audible=(t>=onset)&(t<=end),late=(t>end))
        row=dict(**item,environment=0,attempt=0,source_target_id=settings['song']['short_learning']['teacher']['source_target_id'],
            num_envs=settings['num_envs'],outcome=outcome,force_available_fingers=available,phases={},joints={},
            at3seconds={},teacher_wrist=settings['song']['short_learning']['teacher']['wrist_quaternion_G_xyzw'])
        if 'thumb' in available:
            ref=np.asarray(ctrl['reference105_rad'])[[ctrl['joint_names'].index(name) for name in JOINTS[:5]]]
            row['thumb_target_max_deviation_from_035_rad']=float(np.max(np.abs(selected_target[:,:5]-ref)))
            assert row['thumb_target_max_deviation_from_035_rad']<1e-6
        for phase,mask in phases.items():
            row['phases'][phase]={}
            for finger in available:
                f=FINGERS.index(finger)
                info=dict(resultant_n=stats(resultant[:,f],t,mask),signed_neck_normal_n=stats(normal_force[:,f],t,mask),
                    absolute_neck_normal_n=stats(np.abs(normal_force[:,f]),t,mask))
                row['phases'][phase][finger]=info
                tables.append(dict(dataset=label,phase=phase,finger=finger,resultant_peak_n=info['resultant_n']['maximum'],resultant_p95_n=info['resultant_n']['p95'],normal_signed_min_n=info['signed_neck_normal_n']['minimum'],normal_signed_max_n=info['signed_neck_normal_n']['maximum'],normal_abs_p95_n=info['absolute_neck_normal_n']['p95'],
                    count_ge25=info['resultant_n']['threshold_exposure']['25.0']['endpoint_count'],span_ge25_s=info['resultant_n']['threshold_exposure']['25.0']['max_consecutive_endpoint_span_s'],count_ge50=info['resultant_n']['threshold_exposure']['50.0']['endpoint_count'],span_ge50_s=info['resultant_n']['threshold_exposure']['50.0']['max_consecutive_endpoint_span_s']))
        for j,name in enumerate(JOINTS):
            if not np.isfinite(selected_q[:,j]).all():continue
            k=ctrl['action_order'].index(name);low=ctrl['action_lower_rad'][k];high=ctrl['action_upper_rad'][k]
            x,goal=selected_q[:,j],selected_target[:,j];error=goal-x
            exact_low=np.abs(goal-low)<=1e-5;exact_high=np.abs(goal-high)<=1e-5
            near_low=np.abs(x-low)<=BAND;near_high=np.abs(x-high)<=BAND
            joint=dict(lower_rad=low,upper_rad=high,phases={})
            for phase,mask in phases.items():
                out=dict(error_rms_deg=float(np.degrees(np.sqrt(np.mean(error[mask]**2)))),error_abs_p95_deg=float(np.percentile(np.abs(np.degrees(error[mask])),95)),
                    error_signed_min_deg=float(np.degrees(error[mask].min())),error_signed_max_deg=float(np.degrees(error[mask].max())),
                    target_lower_fraction=float(exact_low[mask].mean()),target_upper_fraction=float(exact_high[mask].mean()),
                    target_max_boundary_span_s=max(max_span(mask&exact_low,t),max_span(mask&exact_high,t)),
                    actual_near_lower_fraction=float(near_low[mask].mean()),actual_near_upper_fraction=float(near_high[mask].mean()),
                    actual_max_near_boundary_span_s=max(max_span(mask&near_low,t),max_span(mask&near_high,t)),
                    actual_below_lower_max_deg=float(np.degrees(np.maximum(low-x[mask],0).max())),actual_above_upper_max_deg=float(np.degrees(np.maximum(x[mask]-high,0).max())))
                if executed is not None and item['mode']=='incremental':
                    outward=(exact_low&(executed[:,k]<0))|(exact_high&(executed[:,k]>0))
                    out['incremental_outward_at_target_boundary_fraction']=float(outward[mask].mean())
                    out['incremental_outward_at_target_boundary_span_s']=max_span(mask&outward,t)
                joint['phases'][phase]=out
            row['joints'][name]=joint
        at=int(np.argmin(np.abs(t-3)))
        for finger in available:
            f=FINGERS.index(finger);row['at3seconds'][finger]=dict(resultant_n=float(resultant[at,f]),normal_projection_n=float(normal_force[at,f]))
        row['at3seconds']['middle_q_deg']=np.degrees(selected_q[at,5:9]).tolist();row['at3seconds']['middle_target_deg']=np.degrees(selected_target[at,5:9]).tolist()
        row['middle_geometry']=dict(audible_candidate_fraction=float(candidate[phases['audible']].mean()),audible_wrong_fraction=float(wrong[phases['audible']].mean()),
            audible_surface_distance_min_m=float(distance[phases['audible']].min()) if np.isfinite(distance).all() else None,
            audible_surface_height_min_m=float(height[phases['audible']].min()) if np.isfinite(height).all() else None)
        summaries.append(row)
        # Only selected joints and six selected body poses; no full raw replay.
        prefix=label+'__'
        for key,value in dict(time_s=t,resultant_n=resultant,neck_normal_n=normal_force,q_rad=selected_q,target_rad=selected_target,
            original_q=raw_q,original_target=raw_target,original_body_state=raw_body,original_force_vectors=force,
            guitar_normal_world=normal_world,candidate=candidate,wrong=wrong,surface_distance_m=distance,surface_height_m=height).items():samples[prefix+key]=value
    unchanged=[p for p,v in pins.items() if not Path(p).is_file() or sha(Path(p))!=v]
    changed_source=[p for p,v in source_pins.items() if not Path(p).is_file() or sha(Path(p))!=v]
    assert not unchanged and not changed_source
    np.savez_compressed(HERE/'selected_samples.npz',**samples)
    write('results.json',summaries)
    with (HERE/'body_phase_stats.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(tables[0]));writer.writeheader();writer.writerows(tables)
    write('verification.json',dict(completed=True,cpu_only=True,gpu_executed=False,datasets=len(chosen),primary_env0_traces=16,supplemental_stage2_controls=2,
        sampled_hz=60,endpoint_span_cpu_edge_checks=True,normal_projection_inverse_rotation_crosscheck=True,
        source_pin_files=len(source_pins),source_sha_conflicts=source_conflicts,changed_source_paths=changed_source,changed_inputs=unchanged,
        input_sha256=pins,measurement_source_sha256=source_pins,scope='saved env0 first attempts only; no all-environment load distribution or240Hz extrema/continuous force/pair-pressure certification',
        limitations='direction supplement has only middle3 vector and q4/distal+guitar poses; otherbody forces/full105 q unavailable there'))
    plots(summaries,samples)
    report(summaries)


def plots(rows,samples):
    selected=[r for r in rows if r['label'].endswith('_000300') or r['label']=='incremental_s17_initial_reference']
    fig,axes=plt.subplots(2,2,figsize=(12,7.5),constrained_layout=True)
    for row in selected:
        prefix=row['label']+'__';t=samples[prefix+'time_s'];f=samples[prefix+'resultant_n'];n=samples[prefix+'neck_normal_n']
        axes[0,0].plot(t,f[:,2],label=row['label'].replace('incremental','inc').replace('position','pos'),lw=1.3)
        axes[0,1].plot(t,f[:,0],lw=1.3)
    for ax,title in zip(axes[0],('Middle3 body resultant','Thumb3 body resultant')):
        ax.set(title=title,xlabel='Actual local time (s)',ylabel='60Hz resultant (N)');ax.axvspan(3,3.1174,color='#2878b5',alpha=.1)
    axes[0,0].legend(fontsize=7)
    name='incremental_s17_000300';t=samples[name+'__time_s'];q=np.degrees(samples[name+'__q_rad'][:,5:9]);goal=np.degrees(samples[name+'__target_rad'][:,5:9])
    for j,color in enumerate(('#2878b5','#e69f00','#15976b','#9954a0')):
        axes[1,0].plot(t,q[:,j],color=color,label=f'q{j+1}');axes[1,0].plot(t,goal[:,j],color=color,ls='--',alpha=.6)
    axes[1,0].set(title='Incremental seed17 final: q solid / target dashed',xlabel='Actual local time (s)',ylabel='Middle4 angle (degrees)');axes[1,0].legend(fontsize=8,ncol=4)
    for seed,color in ((7,'#2878b5'),(17,'#c65b37')):
        group=[r for r in rows if r['mode']=='incremental' and r['seed']==seed and not r.get('supplement') and r['label'].split('_')[-1] in ('000050','000100','000150','000300')]
        group.sort(key=lambda r:int(r['label'].split('_')[-1]))
        axes[1,1].plot([int(r['label'].split('_')[-1]) for r in group],[r['phases']['audible']['middle']['resultant_n']['p95'] for r in group],'o-',color=color,label=f'Seed {seed}')
    axes[1,1].set(title='Incremental checkpoint comparison, env0 audible p95',xlabel='Training update',ylabel='Middle3 resultant p95 (N)');axes[1,1].legend(fontsize=8)
    for ax in axes.flat:ax.grid(alpha=.2)
    fig.suptitle('Saved env0 only / body resultants, not contact-pair string pressure /60Hz endpoints')
    fig.savefig(HERE/'load_comparison.png',dpi=150);plt.close(fig)


def report(rows):
    table='\n'.join('| '+' | '.join([r['label'],str(r['outcome']['achieved']),f"{r['phases']['audible']['middle']['resultant_n']['maximum']:.2f}",f"{r['phases']['audible']['middle']['resultant_n']['p95']:.2f}",
        f"{r['phases']['audible']['middle']['absolute_neck_normal_n']['p95']:.2f}",f"{r['phases']['audible']['thumb']['resultant_n']['p95']:.2f}" if 'thumb' in r['force_available_fingers'] else '미기록',
        f"{r['phases']['preparation']['middle']['resultant_n']['maximum']:.2f}",f"{r['phases']['late']['middle']['resultant_n']['p95']:.2f}"])+' |' for r in rows)
    r=next(x for x in rows if x['label']=='incremental_s17_000300')
    mid=r['phases']['audible']['middle'];thumb=r['phases']['audible']['thumb'];mcp=r['joints']['LH:middle1_x']['phases']['audible'];spread=r['joints']['LH:middle1_z']['phases']['audible']
    text=f'''# 정책 성공 이후 하중·관절 명령 감사

저장된 env0 자료는 **달성률100%가 저부하 압현이나 제어 한계 해결을 뜻하지 않는다**는 점을 보여 준다. incremental seed17 최종 env0의 audible 중지3 resultant는{mid['resultant_n']['minimum']:.2f}~{mid['resultant_n']['maximum']:.2f}N, p95={mid['resultant_n']['p95']:.2f}N이다. 같은 음을 달성했지만3초 시점 실제 중지4각과 목표각 사이에 큰 차이가 남았다. 생체학적 ‘자연스러움’이나 실제 줄 압력을 이 측정으로 판정하지 않는다.

## 선정과 공통 정의

seed7/17·incremental/position 최종 및 초기reference4쌍, incremental 두 seed의cp50/100/150과초기zero를 포함한 **저장 env0 첫 시도16개**를 선정했다. stage2 live reference와 direction-original 조건의 env0 두 개를 보조로 더했다. 결과에 따라 env를 고르지 않았고, 실패 사례도 생략하지 않았다. 전체 평가128환경의 하중 분포를 재구성한 것은 아니다. 원래 평가의 성공률과 이 한 환경의 하중 통계는 분모가 다르다.

공통 물리 기록은60Hz endpoint218개다. 원래 note press2.9787/onset3.0/end3.1174초를 유지했다. 준비는press 전, settled 준비는2초~press, press 창은press..end, audible은onset..end, 후반은end 뒤다. 준비/settled와press/audible은 겹치는 정의이므로 합산하지 않는다. p95·peak는 저장된 endpoint의 값이며240Hz 물리 최대나 실제 연속 접촉 시간을 뜻하지 않는다.

force는 thumb3/index3/middle3/ring3/pinky3 각각의 **net rigid-body contact force 벡터 norm**이다. 실제 guitar quaternion으로 원래 neck-plane 법선을 world로 회전한 뒤 signed `F·n`과그 절댓값을 따로 계산했다. normal projection도 몸체 모든 접촉의 순합이지 기타/줄 pair의 압력이 아니다.1/10/25/50N은 사후 분석용 고정 구간이며 안전·음악 성공 기준이 아니다.

## 조건별60Hz 하중

| 저장 trace | env0 달성 | 중지 audible peak(N) | 중지 p95(N) | 중지 abs(normal) p95(N) | 엄지 p95(N) | 중지 준비 peak(N) | 중지 후반 p95(N) |
| --- | --- | --- | --- | --- | --- | --- | --- |
{table}

![저장 env0 하중·관절 비교](load_comparison.png)

stage2 보조 결과는 배치 크기/진단 제어가 다르다. `stage2_live_reference_env0`은128환경의 원래 finite reference/무회수 조건이고, `stage2_direction_original_env0`은16환경 direction 진단의 원래 reference 대조다. 후자는 중지 force벡터·q4·distal/guitar pose만 저장되어 있어 엄지/다른 손가락을 채워 만들지 않았다. 이 차이 때문에 두 실행의 차이를 정책 효과로 빼지 않는다. 기존 reference도 몸체 부하를 만들 수 있으므로 ‘모든 부하는 학습 정책이 만들었다’고 결론내릴 수 없다.

표의 준비 peak와audible p95는 서로 다른 시간 범위다. stage2의 준비 도중 큰 부하를 원음의 유지 부하로 바꾸어 인용하지 않았다. 반대로 audible에서 중지 부하가0인 실패 trace도 준비 peak나 엄지 부하가0이라는 뜻은 아니다.

## seed17 incremental 최종 관절과 노출

3초 실제 중지4각={np.round(r['at3seconds']['middle_q_deg'],2).tolist()}°, 목표={np.round(r['at3seconds']['middle_target_deg'],2).tolist()}°다. audible middle1_x의 target-upper 경계 점유는{100*mcp['target_upper_fraction']:.1f}%, 절대 추종 오차 p95는{mcp['error_abs_p95_deg']:.2f}°다. middle1_z target-lower 점유는{100*spread['target_lower_fraction']:.1f}%, 추종 오차 p95는{spread['error_abs_p95_deg']:.2f}°다. 목표가 native 끝에 있어도 실제각이 그 끝에 도달했다는 뜻은 아니다.

목표 경계는 원래 native/action bounds와1e−5rad 이내, 실제 near-bound는0.25° 이내로 별도 측정했다. 실제각은 물리 상태이며 target처럼 수학적으로 clamp됐다고 표현하지 않는다. 범위 밖의 작은 실제 readback도 크기를 그대로 남겼다. incremental에서는 경계 목표에서 같은 바깥 부호 action이 이어지는 비율/최대 endpoint span을 추가했다. position 행동의 절대목표 의미와 같은 부호 분석으로 섞지 않았다. 기존 incremental은 이미 clamp된 목표만 기억하므로 이 관측을 무한한 적분 windup의 증명으로 부르지 않는다.

audible 중지50N 이상 endpoint 수={mid['resultant_n']['threshold_exposure']['50.0']['endpoint_count']}, 최대 연속 endpoint span={mid['resultant_n']['threshold_exposure']['50.0']['max_consecutive_endpoint_span_s']:.6f}s다. 엄지도3초{r['at3seconds']['thumb']['resultant_n']:.2f}N이며 audible p95={thumb['resultant_n']['p95']:.2f}N이다. 이 span은 **저장된 연속 endpoint의 마지막−첫 시각**이며, 사이16.7ms에도 계속 문턱 이상이었다는 보장은 없다. count/60을 실제 노출시간으로 환산하지 않았다. 정확한240Hz peak·지속/충격은 이 원자료로 새로 주장하지 않는다.

press..end 창까지 포함하면 중지 범위는{r['phases']['press_window']['middle']['resultant_n']['minimum']:.2f}~{r['phases']['press_window']['middle']['resultant_n']['maximum']:.2f}N이다. audible에서 중지의 signed neck-normal 성분은{mid['signed_neck_normal_n']['minimum']:.2f}~{mid['signed_neck_normal_n']['maximum']:.2f}N이고, 엄지는{thumb['signed_neck_normal_n']['minimum']:.2f}~{thumb['signed_neck_normal_n']['maximum']:.2f}N으로 부호가 반대다. 엄지 norm57N을 neck-normal 압력57N으로 바꾸어 부르지 않는다. 원음 뒤에는 중지 p95={r['phases']['late']['middle']['resultant_n']['p95']:.2f}N, peak={r['phases']['late']['middle']['resultant_n']['maximum']:.2f}N이고50N 이상31개 endpoint의 span이0.5초다. 음 달성이 후반 부하 해소를 보장하지 않았다.

다른 말단도 별도로 계산했다. 선정 자료의 audible index3 최대23.62N은 incremental seed17 cp100에서 관측됐고, ring3/pinky3는 이 자료의 audible endpoint에서0N이었다.0이라는 결과도 접촉 상대나 표본 사이의 무접촉을 인증하지 않는다.

각 몸체의 signed normal 최소/최대, norm·|normal| peak/p95,1/10/25/50N endpoint 수/점유/span은 [body_phase_stats.csv](body_phase_stats.csv)와 [results.json](results.json)에 있다. 원래 선택 관절 q/target·기타와선택5개 말단 pose·선택5개 force벡터 및 geometry의 변경 없는 사본과 파생 배열은 [selected_samples.npz](selected_samples.npz)에 보관했다. 전체 몸체/학습 raw를 재생성하지 않았다. 보조 direction 자료는 중지4축과중지/기타 pose만 원자료에서 복사했으며 미기록 필드는 NaN으로 표시하고 관측 통계에는 넣지 않았다.

## 해석과 최소 후속 계획

관측은 ‘달성/clean’ 외에 부하와 추종·경계 체류를 함께 봐야 한다는 근거다. 엄지는035 목표를 유지하고 wrist는teacher가 안내하며 다른 손가락 B도 함께 제어된다. thumb3의 큰 resultant는 고정 목표·팔 안내·자기충돌/넥 지지 중 하나 이상과 관련될 수 있다. 접촉 상대가 분리되지 않아 정책 중지 명령만의 인과 효과로 귀속하지 않는다. 외부 contact resultant와 actuator effort cap도 같지 않다.

엄지5축의 기록된 target은 모든 기본 비교 trace에서035 reference와1e−6rad 안에서 같았다. 그럼에도 thumb3 부하는 서로 달랐다. 예를 들어 seed7 incremental 최종은 audible 중지 resultant0N인 미달성 사례인데도 엄지 p95가약45.85N이다. 이는 엄지 목표 고정만으로 낮은 하중이 보장되지 않음을 보여 주며, 중지·팔·기타·자기 접촉의 실제 분담은 아직 분리하지 못했다.

1. 먼저 같은 초기 상태/범위/PD에서 thumb035·teacher wrist를 유지한 reference/zero/학습중지 명령을 나란히 기록하고, 실제 native contact pair·finger/guitar/기타 몸체 반력과240Hz extreme을 확인하는 좁은 진단이 필요하다. 새 실행이 아직 수행되었다는 뜻은 아니다.
2. 실제로 finger의 목표−실제 lag와 loaded 구간의 계속 안쪽 명령이 함께 확인되면 **contact-aware 목표 누적 억제/anti-windup 가설**을 별도 조건으로 시험할 수 있다. 단순 native clamp는 이미 존재한다. 부하를 측정하는 pair/방향과 바깥으로 빠져나오는 명령 보존을 먼저 정의하고, 원래 제어를 고친 뒤 성공을 소급하지 않는다.
3. 별도의 물리 failure 기준이 필요한지는 원래 결과와독립적으로 검토할 수 있다. 현재50N 같은 분석 bin을 곧바로 종료 문턱으로 채택하거나 reward·force cap·범위·PD를 동시에 바꾸지 않는다. 먼저 실제 pair·힘 상한의 의미·수치 안정성과 연속 노출을 확인하고, 비용/종료 후보는 명시한 새 계약으로 비교해야 한다.

이번 감사는 새 GPU·원자료 재생성·기존 결과/활성 소스 수정 없이 CPU에서 수행했다. 실행 입력·원래 소스 SHA와선정 목록은 [selection.json](selection.json), 원자료/소스 불변 확인은 [verification.json](verification.json)에 남겼다. 과거212N 전체 몸체 문제나 실제 현 압력 인증을 해결했다고 주장하지 않는다.
'''
    (HERE/'RESULTS.md').write_text(text)


if __name__=='__main__':main()
