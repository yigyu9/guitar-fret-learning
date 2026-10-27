"""CPU independent matched A/B audit; no scene, model, or raw evidence writes."""
import csv
import hashlib
import json
import os
from pathlib import Path

os.environ.setdefault('MPLCONFIGDIR','/tmp/thumb_native_comparison_mpl')
import numpy as np
from scipy.spatial.transform import Rotation
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
RUN=BASE/'run_v1'
ROOT=HERE.parents[6]
CONDITIONS=('current_all_vertices','face_only_playing_neck1')


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(name,value):
    (HERE/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def nearest_triangle(points,triangle):
    # Independent plane projection + barycentric inclusion + nearest edge.
    a,b,c=triangle;u=b-a;v=c-a;n=np.cross(u,v);n/=np.linalg.norm(n)
    p=points-np.einsum('ij,j->i',points-a,n)[:,None]*n
    d=p-a;uu=u@u;uv=u@v;vv=v@v
    beta=(vv*(d@u)-uv*(d@v))/(uu*vv-uv*uv)
    gamma=(uu*(d@v)-uv*(d@u))/(uu*vv-uv*uv)
    inside=(beta>=0)&(gamma>=0)&(beta+gamma<=1)
    candidates=[]
    for x,y in ((a,b),(b,c),(c,a)):
        edge=y-x;f=np.clip(((points-x)@edge)/(edge@edge),0,1)
        candidates.append(x+f[:,None]*edge)
    stack=np.stack(candidates,axis=1);index=np.sum((stack-points[:,None])**2,axis=-1).argmin(-1)
    closest=stack[np.arange(len(points)),index]
    return np.where(inside[:,None],p,closest)


def geometry(point,normal,force,valid,center,surface):
    plane=np.asarray(surface['plane'],float);rear=np.asarray(surface['rear_vertices'],float)
    unit=plane[:3]/np.linalg.norm(plane[:3]);offset=plane[3]/np.linalg.norm(plane[:3])
    yl=max(center-.04,rear[0,1]);yh=min(center+.04,rear[2,1])
    assert yh>yl
    corners=[]
    for y,right_side in ((yl,False),(yl,True),(yh,True),(yh,False)):
        f=np.clip((y-rear[0,1])/(rear[2,1]-rear[0,1]),0,1)
        left=rear[0,0]+f*(rear[3,0]-rear[0,0]);right=rear[1,0]+f*(rear[2,0]-rear[1,0])
        middle=(left+right)/2;half=(right-left)/4;x=middle+half if right_side else middle-half
        corners.append([x,y,-(unit[0]*x+unit[1]*y+offset)/unit[2]])
    corners=np.asarray(corners)
    choices=np.stack([nearest_triangle(point,corners[[0,1,2]]),nearest_triangle(point,corners[[0,2,3]])],axis=1)
    index=np.sum((choices-point[:,None])**2,axis=-1).argmin(-1)
    closest=choices[np.arange(len(point)),index]
    gap=point@unit+offset;projected=point-gap[:,None]*unit
    excess=np.linalg.norm(closest-projected,axis=-1)
    cosine=-np.sum(normal/np.linalg.norm(normal,axis=-1)[:,None]*unit,axis=-1)
    load=np.maximum(force@unit,0)
    smooth=lambda x:np.clip(x,0,1)**2*(3-2*np.clip(x,0,1))
    quality=(1+np.maximum(gap-.003,0)/.02)**-2*smooth((gap+.001)/.001)*smooth(cosine/.8)*(1+excess/.02)**-2
    candidate=valid&(gap>=-.001)&(gap<=.0005)&(excess<=1e-6)&(cosine>=.1)&(load>=.01)
    return dict(signed_gap=gap,region_excess=excess,normal_cos=cosine,normal_load=load,
        contact_candidate=candidate,quality=quality,rate=.01*quality*(1+candidate))


def transitions(candidate):
    stage='initial_hold';start=0.;streak=0;events=[];stages=[]
    for tick in range(900):
        now=tick/60.;next_stage=None
        if stage=='initial_hold' and now>=1:next_stage='approach'
        elif stage in ('approach','reapproach') and streak>=24:next_stage='contact_hold' if stage=='approach' else 'final_hold'
        elif stage=='contact_hold' and now-start>=1.5:next_stage='release'
        elif stage=='release' and now-start>=1.5:next_stage='reapproach'
        elif stage=='final_hold' and now-start>=1.5:next_stage='completed_hold'
        if next_stage:
            events.append(dict(time_s=now,previous=stage,next=next_stage));stage=next_stage;start=now;streak=0
        for value in candidate[tick*4:tick*4+4]:
            stages.append(stage);streak=streak+1 if value else 0
    return events,np.asarray(stages)


def reference_data():
    fixture=HERE/'old_source_reference.npz'
    if fixture.exists():return dict(np.load(fixture))
    # CPU source reads only. Freeze this small reference before production edits.
    from guitar_learning.gpu.thumb_support import load_thumb_support
    from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract
    from guitar_learning.core.control import ACTIVE_NAMES
    patch=load_thumb_support();prepared=load_prepared_reset_contract()
    names=prepared['initial']['joint_names'];qnames=['LH:'+x for x in ('thumb1_x','thumb1_y','thumb1_z','thumb2','thumb3')]
    values=dict(points=patch['points_local'],normals=patch['normals_local'],valid=patch['valid'],
        lower=np.asarray(prepared['initial']['native_PD_properties']['lower']),upper=np.asarray(prepared['initial']['native_PD_properties']['upper']),
        reference105=np.asarray(prepared['target105']),thumb_ids=np.array([names.index(n) for n in qnames]),
        thumb_actions=np.array([ACTIVE_NAMES.index(n) for n in qnames]))
    np.savez_compressed(fixture,**values)
    snapshot=HERE/'old_source';snapshot.mkdir(exist_ok=False)
    paths=['guitar_learning/gpu/thumb_support.py','guitar_learning/gpu/episode_diagnostics.py',
        'guitar_learning/gpu/fingertip_pad.py','guitar_learning/tool/validation/thumb_contact_probe.py',
        str((BASE/'support/surfaces.py').relative_to(ROOT))]
    manifest={}
    for i,name in enumerate(paths):
        source=ROOT/name;dest=snapshot/(str(i)+'_'+source.name);dest.write_bytes(source.read_bytes())
        manifest[str(source)]=dict(sha256=sha(source),snapshot=str(dest))
    write('old_source_snapshot.json',manifest)
    return values


def main():
    reports={name:read(RUN/name/'report.json') for name in CONDITIONS};ref=reference_data()
    raw_paths=[RUN/'comparison.json',RUN/'plan.json',BASE/'run_v1_launcher.json',BASE/'frozen_sources.json',HERE/'old_source_reference.npz',HERE/'old_source_snapshot.json',Path(__file__)]
    for name in CONDITIONS:
        raw_paths += [RUN/name/file for file in ('physics_env0000.npz','report.json','base_probe_report.json','inputs_before.json','scene/gpu_scene_initial.json','scene/gpu_scene_final.json')]
    pins={str(p):sha(p) for p in raw_paths};source_pins={}
    for name,report in reports.items():
        assert report['completed'] and report['scene_closed'] and report['failure'] is None
        source_pins.update(report['source_pins']);source_pins.update(read(RUN/name/'inputs_before.json'))
    assert all(Path(p).is_file() and sha(Path(p))==v for p,v in source_pins.items())
    launcher=read(BASE/'run_v1_launcher.json');assert launcher['returncode']==0
    assert launcher['frozen_sources_sha256']==sha(BASE/'frozen_sources.json')
    a,b=(reports[n] for n in CONDITIONS)
    common={}
    for key in ('asset_sha256','requested_fix_base_link','requested_disable_gravity','shape_readback_sha256'):
        va=a['scene']['diagnostic_guitar_asset'][key];vb=b['scene']['diagnostic_guitar_asset'][key]
        assert va==vb;common[key]=va
    for key in ('gravity','position_iterations','velocity_iterations','environment_aggregate','hand_collision'):
        assert a['scene'][key]==b['scene'][key]
    assert a['native_PD_sha256']==b['native_PD_sha256'];common['native_PD_sha256']=a['native_PD_sha256']
    outcomes={};phase_rows=[];arrays={};verification={};plot_data={}
    for name in CONDITIONS:
        report=reports[name];base=report['base_probe'];p=np.load(RUN/name/'physics_env0000.npz');d={k:p[k] for k in p.files};p.close()
        assert len(d['time_s'])==3600 and np.allclose(d['time_s'],np.arange(1,3601)/240,rtol=0,atol=1e-12)
        assert all(np.isfinite(v).all() for v in d.values() if v.dtype.kind not in 'US')
        point=d['thumb_selected_point'];normal=d['thumb_selected_normal'];force=d['thumb_force_G'];valid=d['thumb_valid']
        metrics={surface:geometry(point,normal,force,valid,base['fixed_work_center_y_m'],data) for surface,data in report['source_geometries'].items()}
        errors={}
        for surface,result in metrics.items():
            errors[surface]={}
            for key,value in result.items():
                if key=='rate':continue
                stored=d['thumb_comparison_'+surface+'_'+key]
                error=int(np.sum(value!=stored)) if key=='contact_candidate' else float(np.max(np.abs(value-stored)))
                errors[surface][key]=error
                assert error==0 if key=='contact_candidate' else error<3e-5,(surface,key,error)
        primary=metrics[name]
        assert np.array_equal(primary['contact_candidate'],d['thumb_contact_candidate'])
        assert float(np.abs(primary['rate']-d['thumb_rate']).max())<3e-7
        events,stages=transitions(primary['contact_candidate'])
        assert np.array_equal(stages,d['stage'])
        assert events==[{k:event[k] for k in ('time_s','previous','next')} for event in base['transitions']]
        names=base['body_names'];thumb=names.index('human/LH:thumb3');guitar=names.index('guitar/guitar')
        body=d['body_state'];rt=Rotation.from_quat(body[:,thumb,3:7]);rg=Rotation.from_quat(body[:,guitar,3:7])
        selected=ref['points'][d['thumb_sample_index']];selected_normal=ref['normals'][d['thumb_sample_index']]
        rebuilt=rg.inv().apply(body[:,thumb,:3]+rt.apply(selected)-body[:,guitar,:3])
        rebuilt_normal=rg.inv().apply(rt.apply(selected_normal));rebuilt_normal/=np.linalg.norm(rebuilt_normal,axis=-1)[:,None]
        rebuilt_force=rg.inv().apply(d['contact_force'][:,thumb])
        pose_errors=dict(point_max_m=float(np.abs(rebuilt-point).max()),normal_max=float(np.abs(rebuilt_normal-normal).max()),force_max_n=float(np.abs(rebuilt_force-force).max()))
        assert pose_errors['point_max_m']<1e-6 and pose_errors['normal_max']<1e-5 and pose_errors['force_max_n']<2e-5
        witness=ref['points'][d['control_witness_index']];witness=rg.inv().apply(body[:,thumb,:3]+rt.apply(witness)-body[:,guitar,:3])
        plane=np.asarray(report['source_geometries'][name]['plane']);witness_gap=witness@plane[:3]+plane[3]
        assert float(np.abs(witness_gap-d['control_witness_gap']).max())<1e-6
        ids=ref['thumb_ids'];action_ids=ref['thumb_actions'];target=d['target'][:,ids];controls=target[3::4]
        initial=ref['reference105'][ids]
        before=np.vstack((initial,controls[:-1]));action=d['action'][3::4][:,action_ids]
        expected=np.clip(before+action*4/60,ref['lower'][ids],ref['upper'][ids])
        codec=float(np.abs(expected-controls).max());assert codec<2e-6
        assert np.array_equal(d['target'].reshape(900,4,105),np.repeat(d['target'][::4,None],4,axis=1))
        other=np.ones(39,bool);other[action_ids]=False;assert not d['action'][:,other].any()
        excursion=float(np.degrees(np.abs(target-initial).max()));change=float(np.degrees(np.abs(controls-before).max()))
        excess=float(np.maximum(np.maximum(ref['lower'][ids]-target,target-ref['upper'][ids]),0).max())
        assert excursion<=15.0001 and change<=.5001 and excess<2e-6
        assert abs(excursion-report['raw_capture']['max_target_excursion_deg'])<2e-5
        phase_summary={}
        for phase in dict.fromkeys(stages):
            mask=stages==phase;load=primary['normal_load'][mask];gap=primary['signed_gap'][mask];candidate=primary['contact_candidate'][mask]
            result=dict(endpoints=int(mask.sum()),seconds=float(mask.sum()/240),candidate_fraction=float(candidate.mean()),
                rear_normal_load_mean_n=float(load.mean()),rear_normal_load_max_n=float(load.max()),rear_normal_load_p95_n=float(np.percentile(load,95)),
                thumb3_resultant_mean_n=float(np.linalg.norm(force[mask],axis=-1).mean()),thumb3_resultant_max_n=float(np.linalg.norm(force[mask],axis=-1).max()),
                gap_min_m=float(gap.min()),gap_max_m=float(gap.max()),gap_final_m=float(gap[-1]),fixed_witness_final_gap_m=float(witness_gap[mask][-1]))
            phase_summary[phase]=result;phase_rows.append(dict(condition=name,phase=phase,**result))
            original=base['measured_stages'][phase]
            assert abs(result['candidate_fraction']-original['candidate_fraction'])<1e-12
            assert abs(result['rear_normal_load_mean_n']-original['normal_load_mean_N'])<2e-5
            assert abs(result['rear_normal_load_max_n']-original['normal_load_max_N'])<2e-5
        protocol=dict(first_contact='contact_hold' in phase_summary,
            first_hold=phase_summary.get('contact_hold',{}).get('seconds',0)>=1.49 and phase_summary.get('contact_hold',{}).get('candidate_fraction',0)>=.9,
            release=phase_summary.get('release',{}).get('seconds',0)>=1.49 and phase_summary.get('release',{}).get('candidate_fraction',1)<.1 and phase_summary.get('release',{}).get('gap_final_m',0)>=.002,
            recontact='final_hold' in phase_summary,
            final_hold=phase_summary.get('final_hold',{}).get('seconds',0)>=1.49 and phase_summary.get('final_hold',{}).get('candidate_fraction',0)>=.9)
        assert protocol==base['protocol_passed']
        fixed_release=phase_summary.get('release',{}).get('fixed_witness_final_gap_m',0)>=.002
        assert fixed_release==base['fixed_witness_release_2mm_passed']
        samepoint={surface:dict(candidate_endpoints=int(m['contact_candidate'].sum()),gap_min_m=float(m['signed_gap'].min()),gap_max_m=float(m['signed_gap'].max()),normal_load_max_n=float(m['normal_load'].max()),quality_mean=float(m['quality'].mean())) for surface,m in metrics.items()}
        velocity_error=float(np.sqrt(np.mean((d['thumb_point_velocity_predicted']-d['thumb_point_velocity_measured'])**2)))
        outcomes[name]=dict(phases=phase_summary,transitions=events,protocol_passed=protocol,fixed_witness_release_2mm=fixed_release,
            same_actual_point_dual_surfaces=samepoint,target_excursion_max_deg=excursion,target_change_max_deg=change,native_target_limit_excess_rad=excess,
            codec_error_rad=codec,max_abs_qd_rad_s=float(np.abs(d['qd']).max()),velocity_check_rms_m_s=velocity_error,
            thumb_joint_names=[base['native_joint_names'][i] for i in ids],thumb_target_change_range_deg=np.degrees(np.ptp(target,axis=0)).tolist(),
            thumb1_resultant_max_n=float(np.linalg.norm(d['contact_force'][:,names.index('human/LH:thumb1')],axis=-1).max()),
            thumb2_resultant_max_n=float(np.linalg.norm(d['contact_force'][:,names.index('human/LH:thumb2')],axis=-1).max()))
        verification[name]=dict(geometry_errors=errors,pose_reconstruction_errors=pose_errors,transitions_match=True,protocol_matches=True,
            native_bounds_and_codec_pass=True,actual_physics=3600,actual_controls=900,scene_closed=report['scene']['closed'])
        plot_data[name]=dict(t=d['time_s'],metrics=metrics,force=force,stages=stages,target=target,reference=initial)
        for key,value in dict(time_s=d['time_s'],point=point,normal=normal,force_G=force,stage=stages,
            thumb_q=d['q'][:,ids],thumb_target=target,primary_candidate=primary['contact_candidate'],fixed_witness_gap=witness_gap).items():arrays[name+'__'+key]=value
        for surface,m in metrics.items():
            for key,value in m.items():arrays[name+'__'+surface+'__'+key]=value
    assert all(Path(p).is_file() and sha(Path(p))==v for p,v in pins.items())
    assert all(Path(p).is_file() and sha(Path(p))==v for p,v in source_pins.items())
    write('results.json',outcomes)
    with (HERE/'phase_summary.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(phase_rows[0]));writer.writeheader();writer.writerows(phase_rows)
    np.savez_compressed(HERE/'recomputed.npz',**arrays)
    write('verification.json',dict(completed=True,cpu_only=True,gpu_executed=False,conditions=verification,
        matched_physics=common,source_pins_unchanged=True,source_pin_count=len(source_pins),source_pins=source_pins,
        raw_and_analysis_inputs_unchanged=True,input_sha256=pins,launcher_exit=0,launcher_wall_s=launcher['wall_s'],
        scope='old-source matched fixed-guitar native diagnostic; actual same selected point on two surfaces, no pair-pressure or policy performance',
        source_freeze_status='all old-source calculations and current pin checks complete; old_source snapshots and old_source_reference preserve arithmetic reference'))
    plot(plot_data);write_results(outcomes,launcher,common)


def plot(data):
    fig,axes=plt.subplots(2,2,figsize=(12,7),constrained_layout=True)
    for row,(condition,d) in enumerate(data.items()):
        for surface,color in zip(CONDITIONS,('#c65b37','#2878b5')):
            m=d['metrics'][surface];axes[row,0].plot(d['t'],1000*m['signed_gap'],color=color,label=surface)
        axes[row,0].axhspan(-1,.5,color='#15976b',alpha=.12)
        axes[row,0].set(title=('A old guidance' if row==0 else 'B face-only guidance')+': both planes at SAME selected point',ylabel='Signed gap (mm)',xlabel='Actual time (s)')
        axes[row,0].legend(fontsize=7)
        primary=d['metrics'][condition]
        axes[row,1].plot(d['t'],primary['normal_load'],color='#555555',label='Rear-normal resultant')
        candidate_axis=axes[row,1].twinx();candidate_axis.step(d['t'],primary['contact_candidate'].astype(int),color='#15976b',alpha=.5,where='post')
        candidate_axis.set(yticks=[0,1],ylim=(-.05,1.15),ylabel='Candidate')
        axes[row,1].set(title=('A: no contact protocol' if row==0 else 'B: transient and stable holds separated'),xlabel='Actual time (s)',ylabel='Normal load (N)')
        for k in range(1,len(d['stages'])):
            if d['stages'][k]!=d['stages'][k-1]:
                for ax in axes[row]:ax.axvline(d['t'][k]-1/240,color='#777777',ls=':',lw=.8)
    for ax in axes.flat:ax.grid(alpha=.2)
    fig.suptitle('Matched physical asset / PD / fixed guitar / original15s finite thumb5 protocol')
    fig.savefig(HERE/'comparison.png',dpi=150);plt.close(fig)


def write_results(outcomes,launcher,common):
    a,b=(outcomes[n] for n in CONDITIONS)
    table='\n'.join('| '+' | '.join([phase,f"{v['seconds']:.3f}",f"{100*v['candidate_fraction']:.2f}",f"{v['rear_normal_load_mean_n']:.3f}",f"{v['rear_normal_load_max_n']:.3f}",f"{1000*v['gap_final_m']:.3f}"])+' |' for phase,v in b['phases'].items())
    text=f'''# 엄지 후면 안내면 native matched A/B 결과

같은 물리 자산·PD·fixed guitar에서 **기존 all-vertex 안내면 A는 접촉 프로토콜 미달, face-only playing-neck1 안내면 B는 접촉→유지→해제→재접촉→최종 유지 통과**였다. 두 실행 모두3600physics endpoint/900control·15초를 완료했다. 이는 새 안내면 입력/판정의 native 진단이며 정책 학습 성과나 contact-pair 압력 인증이 아니다.

## 같은 실제 점에서 안내면 차이

A가 선택한 실제 엄지 점은 A면 gap을 거의0으로 줄였지만 face-only 실제 neck1 후면에는 약5.4~5.9mm 떨어져 있었고 thumb3 rear-normal load는0N이었다. A면 자체 candidate도0/3600이었다. A는1초 initial hold 뒤14초 approach에서 머물러, hold/release/recontact에 진입하지 못했다.

B의 실제 궤적에서는 새 면 candidate가{b['same_actual_point_dual_surfaces']['face_only_playing_neck1']['candidate_endpoints']}/3600endpoint였지만, 그 **동일 actual selected point·normal·force**를 A면으로 판독한 candidate는0개였다. B면에 닿은 점의 A면 gap은 최대 약−5.37mm로 원래−1mm penetration 창을 벗어났다. 별도의 가상 표본·접촉을 만들거나, 상대 면마다 더 유리한 점을 새로 선택하지 않았다.

![동일 실제 선택점의 두 면 gap과240Hz rear-normal load](comparison.png)

두 실행에서 같은 point-selection 알고리즘을 사용해도 안내면이 달라 실제 selected point·제어 witness·궤적이 달라질 수 있다. 따라서 서로 다른 A/B native 궤적의 차이와, 한 궤적의 동일 점을 두 면으로 읽은 차이를 분리했다. 각각의 source sample ID와 fixed control-witness gap을 그대로 재계산했다.

## B 단계별 실제 하중

| 단계 | 적분 시간(s) | candidate(%) | normal load 평균(N) | 최대(N) | 끝 gap(mm) |
| --- | --- | --- | --- | --- | --- |
{table}

재접근 transient 최대는약11.225N이고, 처음 접근도약10.150N까지 올랐다. **안정 유지의 약2.4N과 transient peak를 섞지 않는다.** 첫 hold 평균2.422/최대2.511N, 최종 hold 평균2.373/최대2.460N, 그 뒤 completed hold 평균2.385/최대2.392N이다.2N 접근 보호는 다음 유한 보정 요청을 제한하는 조건이지 실제 contact resultant를2N에 clamp하는 물리 cap이 아니다.

원래 contact 확인은24개 연속240Hz candidate endpoint다. 독립 상태기계가 원래 transition 시각과 일치했다. B는1.983333초 first hold,3.483333초 release,4.983333초 reapproach,5.633333초 final hold,7.133333초 completed hold로 넘어갔다. release1.5초의 candidate 비율8.33%는 원래<10% 기준을 통과했고, 끝 selected gap은약2.997mm였다. fixed witness의2mm 이격도 통과했다. release가 시작된 순간부터 전체1.5초 내내 candidate=false였다고 확대하지 않는다.

## 목표·native 제어·무결성

최대 엄지 target 변화는 A약{a['target_excursion_max_deg']:.3f}°, B약{b['target_excursion_max_deg']:.3f}°로±15° 요청 범위 안이었다. control당 최대변화는 A약{a['target_change_max_deg']:.3f}°, B약{b['target_change_max_deg']:.6f}°로 원래0.5° 보정을 유지했다. 두 조건 모두 native target 초과0, 기존4rad/s incremental codec 재계산 오차2×10⁻⁶rad 이내였으며 다른 policy 채널은0이었다. 별도 solver·힘 보조·실행 중 상태 덮어쓰기는 없었다.

같은 point의 gap/finite-region excess/facing/load/candidate/quality를 독립 NumPy 삼각형/edge 투영으로 재계산했다. body/guitar pose와 동결한 원래128개 thumb patch에서 selected point·normal·force를 별도로 복원했고, phase 통계·상태 전이·원래 protocol flags가 일치했다. 정상 force는 thumb3 resultant만 사용하며 thumb1/2를 candidate 하중에 더하지 않았다. 원 source·README·원 raw를 수정하지 않았다.

양쪽 compound asset SHA는 `{common['asset_sha256']}`, shape readback SHA와native PD fields SHA도 같았다. fixed=true·gravity ON·원 collision/solver 옵션과1환경 scene closed를 확인했다. wrapper 내부 base report의 ‘free guitar’ 문구는 원래 helper의 일반 문구이며, 이번 실제 scene readback은 양쪽 fixed다. launcher exit0·전체 wall {launcher['wall_s']:.3f}초가 보존되어 있고 영상 인코더도 양쪽0이다.

구체적인 phase 표·두 면별 candidate/gap은 [results.json](results.json), [phase_summary.csv](phase_summary.csv), 재계산 배열은 [recomputed.npz](recomputed.npz), 원자료/source SHA와오차는 [verification.json](verification.json)에 있다. 바뀌기 전 함수 원문과 원래 patch/native bounds fixture도 이 분석 폴더 안에 봉인해 두었다. 생산 안내면을 나중에 수정하더라도 이 old-source 결과를 새 소스에서 평가한 결과처럼 재분류하지 않는다.

## 남는 범위

이 한 쌍은 이번 고정 기타·엄지5축 유한 진단에서 source 안내면 선택이 실제 접촉 후보/프로토콜 도달에 영향을 준다는 근거다. force resultant와 same-point 기하는 실제 thumb-neck pair·분포 압력·줄 진동·음향을 인증하지 못한다. 자유 기타·양손 학습·thumb 목표035 고정 시의 큰 부하·전곡 성공을 해결했다는 결론도 아니다. 생산 변경은 별도 버전·계약·검증과 새 checkpoint 정체성을 따라야 한다.
'''
    (HERE/'RESULTS.md').write_text(text)


if __name__=='__main__':main()
