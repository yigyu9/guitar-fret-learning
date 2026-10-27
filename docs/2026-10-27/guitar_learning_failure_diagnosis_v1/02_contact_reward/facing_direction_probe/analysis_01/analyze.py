"""Independent CPU audit of the actual16-environment finite direction capture."""
import csv
import hashlib
import json
import math
import os
from pathlib import Path

os.environ.setdefault('MPLCONFIGDIR','/tmp/facing_direction_analysis_mpl')
import numpy as np
from scipy.spatial.transform import Rotation
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
RUN=BASE/'run_01'
ROOT=HERE.parents[5]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(name,value):
    (HERE/name).write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')


def main():
    raw={str(p):sha(p) for p in RUN.iterdir() if p.is_file()}
    report=read(RUN/'report.json');protocol=report['conditions']
    episodes=read(RUN/'first_attempt_episodes.json');contract=read(RUN/'original_training_contract.json')
    launcher=read(BASE/'run_01_launcher.json')
    assert launcher['returncode']==0 and launcher['precommit_sha256']==sha(BASE/'precommit.json')
    assert report['completed'] and all(report['checks'].values()) and len(episodes)==16
    assert report['scene']['closed'] and report['scene']['environment_count']==16
    p=np.load(RUN/'physics240.npz');a={k:p[k] for k in p.files};p.close()
    p=np.load(RUN/'control60.npz');c={k:p[k] for k in p.files};p.close()
    assert len(a['clock'])==872==4*len(c['clock'])
    assert all(np.isfinite(v).all() for v in [*a.values(),*c.values()])
    assert [e['env_id'] for e in episodes]==list(range(16))
    assert not np.any(~a['first_attempt'][:-1]&a['first_attempt'][1:])
    for i in range(16):
        assert np.array_equal(a['clock'][a['first_attempt'][:,i],i],np.arange(1,int(a['first_attempt'][:,i].sum())+1))
    failure_flags=a['physical_failure']|a['wrist_failure']
    failed=np.maximum.accumulate(failure_flags&a['first_attempt'],axis=0)
    assert np.array_equal(failed,a['failed'])
    live=a['first_attempt']&~failed
    force=np.linalg.norm(a['distal_force_n'],axis=-1)
    # Recompute SAME-point gates from captured points/normals and original markers;
    # do not call the driver, protocol.summarize or original mask helper.
    rigid_path=ROOT/'guitar_learning/assets/gpu_rigid_guitar_v1/manifest.json'
    rigid=read(rigid_path);names=rigid['logical_body_names'];offset=np.asarray(rigid['logical_position_root_m'],np.float32)
    target=protocol['view']['source_target'];s=target['string']+1;fret=target['fret']
    plane=np.asarray(contract['reward']['surface_learning']['press_surface']['plane_G'],np.float32)
    normal=plane[:3]/np.linalg.norm(plane[:3])
    start=offset[names.index('G:string%d'%s)].copy();end=offset[names.index('G:string%d_end'%s)].copy()
    for point in (start,end):point[2]=-(point[:2]@plane[:2]+plane[3])/plane[2]
    fy=[offset[names.index('G:nut' if n==0 else 'G:fret%d'%n),1] for n in (fret-1,fret)]
    low,high=min(fy)+.002,max(fy)-.002;line=end-start
    points=a['points_G'];height=points@normal+plane[3]/np.linalg.norm(plane[:3])
    projection=np.sum((points-start)*line,axis=-1)/np.sum(line*line)
    lateral=np.linalg.norm(points-height[...,None]*normal-start-projection[...,None]*line,axis=-1)
    cosine=-np.sum(a['normals_G']*normal,axis=-1)
    position=a['valid_mask']&(points[...,1]>=low)&(points[...,1]<=high)&(height>=-.001)&(height<=.003)&(lateral<=.003)
    facing=position&(cosine>=.1)
    geometry_errors=dict(position_mask_mismatches=int((position!=a['position_mask']).sum()),
        facing_mask_mismatches=int((facing!=a['facing_mask']).sum()),
        max_height_error_m=float(np.abs(height-a['signed_height_m']).max()),
        max_cosine_error=float(np.abs(cosine-a['normal_cos']).max()),
        max_lateral_error_m=float(np.abs(lateral-a['lateral_m']).max()))
    assert not geometry_errors['position_mask_mismatches'] and not geometry_errors['facing_mask_mismatches']
    assert np.array_equal(facing.any(-1)&(force>=.01),a['positive'])
    assert np.array_equal(a['candidate'],a['positive']&~a['wrong'])
    # Independent pose reconstruction of stored registered palmar samples.
    from guitar_learning.gpu.fingertip_pad import load_fingertip_pad
    pad=load_fingertip_pad();assert pad['contract']==contract['reward']['surface_learning']['pad']
    local=pad['points_local'][1].astype(float);local_normal=pad['normals_local'][1].astype(float)
    maximum_pose_point_error=0.;maximum_pose_normal_error=0.
    for tick in range(872):
        d,g=a['distal_pose'][tick],a['guitar_pose'][tick]
        rd=Rotation.from_quat(d[:,3:7]).as_matrix();rg=Rotation.from_quat(g[:,3:7]).as_matrix()
        world=d[:,None,:3]+np.einsum('nij,pj->npi',rd,local)
        rebuilt=np.einsum('nji,npj->npi',rg,world-g[:,None,:3])
        rebuilt_normal=np.einsum('nji,npj->npi',rg,np.einsum('nij,pj->npi',rd,local_normal))
        maximum_pose_point_error=max(maximum_pose_point_error,float(np.abs(rebuilt-a['points_G'][tick]).max()))
        maximum_pose_normal_error=max(maximum_pose_normal_error,float(np.abs(rebuilt_normal-a['normals_G'][tick]).max()))
    assert maximum_pose_point_error<1e-6 and maximum_pose_normal_error<1e-5
    wrist_local=Rotation.from_quat(a['guitar_pose'][...,3:7].reshape(-1,4)).inv()*Rotation.from_quat(a['wrist_pose'][...,3:7].reshape(-1,4))
    angular=(Rotation.from_quat(a['wrist_goal_G_xyzw'].reshape(-1,4))*wrist_local.inv()).magnitude().reshape(872,16)
    orientation_error=float(np.abs(angular-a['orientation_error_rad']).max())
    assert orientation_error<1e-5
    loaded=live&position.any(-1)&~facing.any(-1)&(force>=.01)
    geometric=live&position.any(-1)&~facing.any(-1)
    view=protocol['view'];press,onset,finish=[view[k] for k in ('local_press_s','local_onset_s','local_end_s')]
    duration=finish-onset
    cases=[];reward_errors=[];report_mismatches=[]
    for i,episode in enumerate(episodes):
        # Independent streaming span count, rather than the driver's split/index code.
        current=best=0;start=best_start=best_end=None;previous=None
        for k in range(872):
            clock=int(a['clock'][k,i])
            if loaded[k,i]:
                current=current+1 if previous is not None and clock==previous+1 else 1
                if current==1:start=clock
                if current>best:best,best_start,best_end=current,start,clock
                previous=clock
            else:current=0;previous=None
        span=(best_end-best_start)/240 if best else 0.
        post=live[:,i]&(a['local_time_s'][:,i]>=2.8)
        saved=report['episodes'][i]
        native_min=float(a['orientation_error_rad'][post,i].min()) if post.any() else None
        cause=('loaded_negative_observed' if loaded[:,i].any() else 'negative_geometry_unloaded' if geometric[:,i].any()
            else 'position_not_observed' if not np.any(live[:,i]&position[:,i].any(-1)) else 'same_sample_facing_remained')
        checks=dict(loaded_negative_samples=int(loaded[:,i].sum()),loaded_negative_witness=bool(loaded[:,i].any()),
            stable50ms=span>=.05,max_contiguous_samples=best,max_contiguous_span_s=span,
            position_samples=int((live[:,i]&position[:,i].any(-1)).sum()),
            facing_samples=int((live[:,i]&facing[:,i].any(-1)).sum()),
            negative_geometry_unloaded_samples=int((geometric[:,i]&(force[:,i]<.01)).sum()),cause=cause,
            orientation_error_min_after2p8_rad=native_min,
            orientation_within10deg_after2p8=bool(np.any(post&(a['orientation_error_rad'][:,i]<=math.radians(10)))))
        for name,value in checks.items():
            if value!=saved[name]:report_mismatches.append(dict(env_id=i,field=name,saved=saved[name],recomputed=value))
        note=episode['selected_raw_note'];terms=episode['reward_components'];required=episode['left_note_ledger']['required_clean_s'][view['source_index']]
        expected=[.25*note['contact_progress'],note['clean']/duration,.25*bool(note['left']),-.15*note['wrong']/duration,
            -.1*max(note['missing']/duration,max(0,1-note['best_clean_streak']/required))]
        keys=['song_left_contact','song_clean_hold','song_left_success','song_wrong_press','song_performance_deficit']
        reward_errors.extend(abs(terms[k]-v) for k,v in zip(keys,expected))
        reward_errors.append(abs(sum(terms.values())-episode['reward']))
        reward_errors.append(abs(c['reward'][:,i].astype(float).sum()-episode['reward']))
        for key,value in terms.items():
            reward_errors.append(abs(c['reward_increment_'+key][:,i].astype(float).sum()-value))
            reward_errors.append(abs(float(c['reward_cumulative_'+key][-1,i])-value))
        timing=live[:,i]&(a['local_time_s'][:,i]>=onset)&(a['local_time_s'][:,i]<=finish)
        selected=np.flatnonzero(live[:,i]&position[:,i].any(-1))
        actual_position_max_cosine=float(cosine[:,i][live[:,i,None]&position[:,i]].max()) if len(selected) else None
        cases.append(dict(env_id=i,condition=i%8,repetition=i//8,**checks,
            independently_rebuilt_min_orientation_error_rad=float(angular[post,i].min()),
            max_distal_resultant_n=float(force[live[:,i],i].max()),
            loaded_samples=int((live[:,i]&(force[:,i]>=.01)).sum()),
            position_audible_samples=int((timing&position[:,i].any(-1)).sum()),
            arm_clip_control_ticks=int(c['wrist_arm_clipped'][:,i].any(-1).sum()),
            clean_fraction=note['clean']/duration,wrong_fraction=note['wrong']/duration,achieved=bool(note['left']),
            physical_failure=episode['termination']['physical_failure'],wrist_failure=episode['termination']['wrist_failure'],
            maximum_cosine_of_position_samples=actual_position_max_cosine,
            reward_components=terms,reason=episode['reason']))
    assert not report_mismatches
    assert max(reward_errors)<5e-6
    conditions=[]
    for condition in range(8):
        group=[r for r in cases if r['condition']==condition]
        assert len(group)==2
        conditions.append(dict(condition=condition,assigned=2,completed=len(group),
            loaded_negative_witnesses=sum(r['loaded_negative_witness'] for r in group),stable50ms=sum(r['stable50ms'] for r in group),
            orientation_within10deg=sum(r['orientation_within10deg_after2p8'] for r in group),
            min_orientation_errors_rad=[r['orientation_error_min_after2p8_rad'] for r in group],
            position_exposed=sum(r['position_samples']>0 for r in group),position_sample_count=sum(r['position_samples'] for r in group),
            facing_sample_count=sum(r['facing_samples'] for r in group),
            geometric_negative_samples=sum(r['negative_geometry_unloaded_samples']+r['loaded_negative_samples'] for r in group),
            achieved=sum(r['achieved'] for r in group),physical_failure=sum(r['physical_failure'] for r in group),wrist_failure=sum(r['wrist_failure'] for r in group),
            max_distal_resultant_n=max(r['max_distal_resultant_n'] for r in group),
            mean_arm_clip_control_fraction=sum(r['arm_clip_control_ticks'] for r in group)/(2*218)))
    pins=read(RUN/'inputs_after.json');assert pins['verified']
    assert all(Path(p).is_file() and sha(Path(p))==v for p,v in pins['input_pins'].items())
    assert raw=={str(p):sha(p) for p in RUN.iterdir() if p.is_file()}
    verification=dict(completed=True,cpu_only=True,gpu_executed_by_analysis=False,independent_cases=16,
        samepoint_gate_recomputation=geometry_errors,maximum_pose_point_error_m=maximum_pose_point_error,
        maximum_pose_normal_error=maximum_pose_normal_error,maximum_orientation_error_rad=orientation_error,
        report_mismatches=report_mismatches,maximum_reward_check_error=max(reward_errors),failure_censor_matches=True,
        observed_physical_or_wrist_failure_samples=int(failure_flags.sum()),
        original_audits_passed=sum(report['checks'].values()),source_pins_still_valid=True,pinned_files=len(pins['input_pins']),
        raw_sha_unchanged=True,launcher_exit=launcher['returncode'],launcher_wall_s=launcher['wall_s'],
        scene_closed=report['scene']['closed'],physics_steps=872,control_ticks=218,loaded_negative_total=int(loaded.sum()),
        first_attempt_endpoint_samples=int(a['first_attempt'].sum()),eligible_before_failure_samples=int(live.sum()),
        scope='new16-env finite direction diagnostic only; not native impossibility proof, same-task policy performance or contact-pair/string pressure certification',
        raw_sha256=raw,launcher_sha256=sha(BASE/'run_01_launcher.json'),
        supplemental_inputs_sha256={str(rigid_path):sha(rigid_path),str(Path(__file__)):sha(Path(__file__))})
    write('verification.json',verification);write('cases.json',cases);write('conditions.json',conditions)
    with (HERE/'conditions.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(conditions[0]));writer.writeheader();writer.writerows(conditions)
    plot(conditions,a,c,angular)
    results(conditions,cases,verification,protocol)


def plot(rows,a,c,angular):
    fig,axes=plt.subplots(2,2,figsize=(11,7),constrained_layout=True)
    x=np.arange(8);colors=['#2878b5']*4+['#c65b37']*4
    means=[np.degrees(np.mean(r['min_orientation_errors_rad'])) for r in rows]
    axes[0,0].bar(x,means,color=colors)
    axes[0,0].axhline(10,color='#555555',ls=':',label='Reporting threshold 10 deg')
    axes[0,0].set(title='Wrist orientation: mean of each attempt minimum after2.8s',ylabel='Remaining error (degrees)',xticks=x)
    axes[0,0].legend(fontsize=8)
    axes[0,1].bar(x,[r['position_exposed'] for r in rows],color='#15976b',label='Any position geometry /2')
    axes[0,1].bar(x,[r['loaded_negative_witnesses'] for r in rows],color='#e69f00',label='Loaded facing negative /2')
    axes[0,1].set(title='All assigned attempts retained',xticks=x,ylim=(0,2.5),yticks=[0,1,2],ylabel='Attempts /2')
    axes[0,1].legend(fontsize=8)
    for i,color in zip((4,5,6,7),('#2878b5','#e69f00','#15976b','#9954a0')):
        axes[1,0].plot(a['local_time_s'][:,i],np.degrees(angular[:,i]),label=f'Condition {i}, rep0',color=color)
    axes[1,0].axvline(2.8,ls=':',color='#777777')
    axes[1,0].set(title='Actual remaining direction error (one declared rep/condition)',xlabel='Actual local time (s)',ylabel='Error (degrees)')
    axes[1,0].legend(fontsize=8)
    axes[1,1].bar(x,[100*r['mean_arm_clip_control_fraction'] for r in rows],color=colors)
    axes[1,1].set(title='Bounded arm request differed from preclip request',xlabel='Condition',xticks=x,ylabel='Control endpoints (%)',ylim=(0,105))
    for ax in axes.flat:ax.grid(alpha=.2)
    fig.suptitle('Fixed-guitar middle row8 /8 finite variants x2 first attempts / no loaded facing-negative witness')
    fig.savefig(HERE/'summary.png',dpi=160);plt.close(fig)


def results(rows,cases,v,protocol):
    labels=['원래 reference','clearance 대조','x/PIP/DIP 하한','DIP 상한','u +90°','u −90°','v +90°','v −90°']
    table='\n'.join('| '+' | '.join(map(str,[r['condition'],labels[r['condition']],f"{r['loaded_negative_witnesses']}/2",f"{r['stable50ms']}/2",f"{r['orientation_within10deg']}/2",
        '/'.join(f'{x:.3f}' for x in r['min_orientation_errors_rad']),f"{r['position_exposed']}/2",r['position_sample_count'],r['facing_sample_count']]))+' |' for r in rows)
    failures=sum(r['physical_failure']+r['wrist_failure'] for r in rows)
    text=f'''# 유한 방향 진단 실제 결과

사전 지정8조건×2개 첫 시도, **loaded back-facing witness0/16, 연속50ms witness0/16**이다. 물리·손목 실패는 각각0/16이고16개 모두 원래3.633333초를 끝냈다. 결과는 새 finite direction 조건의 관측이며, native 기하의 불가능 증명이나 학습·정책 성과가 아니다.

큰 방향 요청 조건4~7은 두 반복 모두2.8초 뒤에도 원래 선언한 방향오차10° 표시 범위에 도달하지 못했다. 최선의 잔여 오차가 약0.917/1.152/0.963/1.560rad(약53/66/55/89°)다. 조건6은 위치 기하가 있어도 같은 유효 표본의 facing이 남았고, 조건4·5·7은 위치 기하도 없었다. 따라서 ‘원하는 방향·위치·하중을 실제로 만들었는데 판정만 거부했다’는 사례를 확보한 것이 아니다.

## 실패 포함 고정 분모

| 조건 | 유한 목표 | loaded 음성 | ≥50ms | 방향≤10° | 반복별 최소 오차(rad) | 위치 노출 | 위치 endpoint 수 | facing endpoint 수 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
{table}

방향 오차는2.8초 이후 각 첫 시도의 최소값이고10°는 사전 선언한 설명용 표시 문턱이다. native contact·성공·실패 기준을 완화하지 않았다. 위치/facing endpoint 수는16개 첫 시도의240Hz 시점 수이며 준비 구간을 포함한다.128개 pad 표본 수나 episode 수와 혼동하지 않는다. 모든 조건의 배정 분모2를 유지했으며, 실패 뒤 표본은 같은 실패240Hz 시점부터 제외한다. 이번에는 실패가 없어 제외 표본도0개다.

![방향 추종·기하 노출과 bounded arm 요청](summary.png)

## 원인 구분

- 방향: 원래 방향을 유지한 조건0~3은8개 모두10° 이내였으나 ±90° 요청 조건4~7은8개 모두 미도달이었다. 요청이 실제90° 회전으로 실행되었다고 간주하지 않는다.
- 위치: 조건2는 방향 추종과 별개로 위치 노출0/2였다. clearance 대조 조건1도 위치 노출이1/2에 그쳤다. 이 유한 접근/선택 관절 자세에서 목표 cell에 닿지 않은 사례가 있으며, 원래 cell/높이 문턱을 바꿔 보완하지 않았다.
- same-point facing: 위치 기하가 나온 모든 시점은 원래 facing도 남았다. 전체13,952개 실제 첫 시도 endpoint에서 `position=true & facing=false`가0개다. 따라서 geometric-negative-but-unloaded 역시0개이며, 이번 음성 미확보를 단순히0.01N 하중 부족 탓으로 분류하지 않는다.
- bounded control: 큰 방향 요청의 arm request는 preclip 요청과 약90~100%의 control endpoint에서 달랐다. 이는 원래 보정 누적·변화율·action 범위 제약을 적용한 흔적이며, PD/힘을 바꿔 회전을 강제하지 않았다. 이 clip 표시만으로 native 관절 한계 하나나 solver 오류를 원인으로 확정하지 않는다.

원래 대조 조건0의 음악 달성은1/2, 조건6은2/2였지만, 후자는 요청 방향을 달성하지 못한 상태에서 facing positive를 유지한 결과다. 이를 facing-negative 시험의 성공으로 재분류하지 않는다. 원래 note ledger·clean·9항 보상은 [cases.json](cases.json)에 모두 보존했다.

## 독립 검산·실행 종료

기존 driver의 summary/helper를 호출하지 않고 저장 point/normal과 원래 줄·프렛·press plane에서 same-sample 위치/facing을 다시 계산했다. 모든 point-level mask가 일치했다. 할당 distal force는 성분 부호가 아닌 벡터 norm으로 다시 계산했고, `first_attempt & ~failed & position & ~facing & norm≥0.01`을 적용했다. 별도 순차 알고리즘으로 clock+1·인접 표본을 요구하는 최대 연속 span을 계산해16개 원 보고서와 일치했다.13개 endpoint의 `(last−first)/240≥0.05초` 조건은 그대로다.

저장 distal/guitar pose와 봉인한 등록 palmar sample에서 point/normal도 독립 재구성했다. point 최대오차{v['maximum_pose_point_error_m']:.3g}m, normal 최대오차{v['maximum_pose_normal_error']:.3g}, 실제 wrist pose의 quaternion geodesic 방향오차 차이는 최대{v['maximum_orientation_error_rad']:.3g}rad다. 저장된 실패 mask는 원래 physical/wrist flag를 동일240Hz 시점부터 latch하는 연산과 일치했다. 다만 이번 실제 실패는0개여서 실제 실패 발생 시의 차단 사례가 추가로 확보된 것은 아니며, 그 경계 동작은 기존 CPU 검사로 확인한 범위다. 유효 witness 뒤의 늦은 episode 실패가 이전 witness를 없애지는 않으며 무실패 episode 부분집합은 별도다.

실제9항 보상은60Hz 증분·누적·episode 원장 합과 비교했고, contact/hold/achievement/wrong/performance의 원래 ledger 기반 예산식을 검산했다. 최대오차{v['maximum_reward_check_error']:.3g}로5×10⁻⁶ 이내다. 물리872endpoint/제어218tick,4substeps/control·finite·연속 clock·16첫시도·원 실행14audit와 현재 입력 pin{v['pinned_files']}개·raw SHA가 통과했다. 모델/버퍼 동일과 updates0은 원 실행 audit에 있으며 CPU 분석에서 GPU 모델을 다시 실행하지 않았다.

launcher exit **0**, wall **{v['launcher_wall_s']:.3f}초**가 [run_01_launcher.json](../run_01_launcher.json)에 보존되어 있다. 원래 GPU scene final은 closed=true,1simulator/16환경이다. raw·precommit·driver·활성 소스는 변경하지 않았고 GPU를 재실행하지 않았다. 검산 값과 파일 SHA는 [verification.json](verification.json), 조건별 기계 판독 표는 [conditions.csv](conditions.csv)에 있다.

## 해석 범위

이8개 유한 목표·2개 반복·원래 시간창에서 loaded 음성을 확보하지 못했다. 방향 요청 미도달과 위치 미도달을 분리할 근거가 생겼지만, 모든 native 가동범위·가능한 접근 궤적에서 그런 음성이 불가능하다는 뜻은 아니다. 회전이 더 가능한지, 반대편 mesh가 넥과 가까워지는지, 실제 접촉 상대가 기타인지도 별도의 문제다. 등록 palmar 표본의 facing 음성과 실제 피부 뒷면 접촉을 동일시하지 않는다.

할당 중지 distal의 관측 resultant 최대는{max(r['max_distal_resultant_n'] for r in rows):.3f}N이었다. 이는 이번16환경의 해당 몸체240Hz resultant에 한정되며 actuator force cap·접촉 pair·실제 현 압력을 뜻하지 않는다. 전체 몸체 force가 없으므로 이전212N 문제의 해결이나 전체 몸체 최대값을 주장하지 않는다. 문턱·PD·힘·원자료를 바꾸지 않고 미확보 상태를 유지한다.
'''
    (HERE/'RESULTS.md').write_text(text)


if __name__=='__main__':main()
