"""CPU reconstruction from the existing final seed17 env0 trace; no physics."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy as np
from scipy.spatial.transform import Rotation
import torch

from guitar_learning.gpu.fingertip_pad import load_fingertip_pad


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def movement(points):
    distance = np.linalg.norm(points-points[0],axis=-1)*1000
    return dict(max_from_first_mm=float(distance.max()),net_mm=float(distance[-1]),
                sampled_path_mm=float(np.linalg.norm(np.diff(points,axis=0),axis=-1).sum()*1000))


def main():
    base = Path(__file__).resolve().parents[1]
    run = base/'pilot_incremental_seed17_v2'
    folder = run/'evaluation_000300'
    metadata = read(folder/'trace_metadata.json')
    settings = read(folder/'settings.json')
    spec = settings['song']['short_learning']
    pins = read(folder/'inputs_before.json')
    trace = np.load(folder/'trace_env0_episode0.npz')
    t = trace['time_s'];assert len(t)==218 and np.allclose(np.diff(t),1/60)
    pad = load_fingertip_pad()
    assert pad['contract']['body_names'][1]=='LH:middle3'
    assert not torch.cuda.is_initialized()
    inputs = {str(folder/n):sha(folder/n) for n in ('trace_metadata.json','trace_env0_episode0.npz','settings.json','inputs_before.json')}
    inputs[str(Path(__file__).resolve())] = sha(__file__)
    for path,digest in pad['contract']['source_sha256'].items():
        assert sha(path)==digest and pins.get(str(Path(path).resolve()))==digest
        inputs[str(Path(path).resolve())]=digest
    points = pad['points_local'][1].astype(float)
    chosen = int(np.linalg.norm(points-points.mean(0),axis=-1).argmin())
    bodies = trace['body_state']
    wrist = bodies[:,metadata['body_names'].index('human/L_Wrist')]
    distal = bodies[:,metadata['body_names'].index('human/LH:middle3')]
    rw = Rotation.from_quat(wrist[:,3:7]).as_matrix()
    rd = Rotation.from_quat(distal[:,3:7]).as_matrix()
    world = distal[:,None,:3]+np.einsum('tij,sj->tsi',rd,points)
    local = np.einsum('tji,tsj->tsi',rw,world-wrist[:,None,:3])
    joint_names = spec['learned_action_names']
    selected = [metadata['joint_names'].index(n) for n in joint_names]
    q,target = np.degrees(trace['q'][:,selected]),np.degrees(trace['target'][:,selected])
    press,end = spec['view']['local_press_s'],spec['view']['local_end_s']
    masks = dict(ramp_0_to_2=t<=2+1e-9,settle_2_to_press=(t>2+1e-9)&(t<press),
                 press_to_end=(t>=press)&(t<=end),after_end=t>end)
    assert np.all(np.stack(list(masks.values())).sum(0)==1)
    phases = {}
    for name,mask in masks.items():
        times=t[mask];first=int(np.flatnonzero(mask)[0])
        rotation=Rotation.from_matrix(rw[mask]@rw[first].T).magnitude()*180/np.pi
        phases[name]=dict(endpoint_count=int(mask.sum()),first_endpoint_s=float(times[0]),last_endpoint_s=float(times[-1]),
            actual_range_deg=np.ptp(q[mask],axis=0).tolist(),target_range_deg=np.ptp(target[mask],axis=0).tolist(),
            actual_net_change_deg=(q[mask][-1]-q[mask][0]).tolist(),
            candidate_endpoints=int(trace['candidate'][mask].sum()),
            fixed_pad_world=movement(world[mask,chosen]),fixed_pad_wrist_local=movement(local[mask,chosen]),
            wrist_world=movement(wrist[mask,:3]),wrist_max_rotation_from_first_deg=float(rotation.max()))
    anchor=int(np.flatnonzero(np.isclose(t,2,atol=1e-9))[0]);after=np.arange(len(t))>=anchor
    relative_shift=np.linalg.norm(local[after]-local[anchor],axis=-1)*1000
    after_two=dict(anchor_s=float(t[anchor]),endpoint_count=int(after.sum()),
        actual_range_deg=np.ptp(q[after],axis=0).tolist(),target_range_deg=np.ptp(target[after],axis=0).tolist(),
        fixed_pad_wrist_local=movement(local[after,chosen]),fixed_pad_world=movement(world[after,chosen]),
        wrist_world=movement(wrist[after,:3]),
        wrist_rotation_max_deg=float(np.degrees(Rotation.from_matrix(rw[after]@rw[anchor].T).magnitude()).max()),
        all128_patch_max_displacement_mm=float(relative_shift.max()),
        all128_patch_max_rms_displacement_mm=float(np.sqrt(np.mean(relative_shift**2,axis=1)).max()))
    candidate=np.asarray(trace['candidate'],dtype=bool);runs=[]
    starts=np.flatnonzero(candidate&~np.r_[False,candidate[:-1]])
    stops=np.flatnonzero(candidate&~np.r_[candidate[1:],False])
    for start,stop in zip(starts,stops):
        runs.append(dict(first_endpoint_s=float(t[start]),last_endpoint_s=float(t[stop]),
                         endpoints=int(stop-start+1),adjacent_endpoint_span_s=float(t[stop]-t[start]),
                         preceding_false_endpoint_s=float(t[start-1]) if start else None,
                         following_false_endpoint_s=float(t[stop+1]) if stop+1<len(t) else None))
    result=dict(schema='short_final17_phase_motion.v1',input_sha256=inputs,
        scope='existing env0 first episode only;218 native60Hz endpoints; no warmup/replay/additionalGPU',
        selected_joint_names=joint_names,pad_definition=pad['contract'],fixed_sample_index=chosen,
        fixed_sample_local_m=points[chosen].tolist(),sample_selection='existing mesh sample nearest patch centroid; independent of trajectory/target',
        frame_formula='p_world = p_distal + R_distal*p_sample; p_wristlocal = transpose(R_wrist)*(p_world-p_wrist)',
        phases=phases,after_two_seconds=after_two,candidate_endpoint_runs=runs,
        limitations=['first endpoint1/60s; actual reset t0 not recorded',
            'phase ranges use included endpoints only; no interpolation at press/end boundaries',
            'candidate true endpoints are not native240Hz contact-start/hold measurements or paired pressure',
            'relative pad and wrist motions are independent geometric descriptions, not causal contribution shares',
            'sampled path is60Hz polyline length; not continuous path or work/effort',
            'one prespecified successful env0; not representative of128 attempts or naturalness'])
    output=run/'analysis/final_env0_phases';output.mkdir(exist_ok=False)
    (output/'analysis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    np.savez_compressed(output/'reconstructed_points.npz',time_s=t,pad_world_m=world,pad_wrist_local_m=local,
                        wrist_world_m=wrist[:,:3],fixed_sample_index=chosen)
    font=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    plt.rcParams['font.family']=font.get_name();plt.rcParams['axes.unicode_minus']=False
    fig,axes=plt.subplots(3,1,figsize=(12,10),sharex=True)
    for i,name in enumerate(joint_names):axes[0].plot(t,q[:,i],label=name.replace('LH:',''))
    axes[0].set_ylabel('실제각(°)');axes[0].legend(ncol=4)
    axes[1].plot(t[after],np.linalg.norm(local[after,chosen]-local[anchor,chosen],axis=-1)*1000,label='손목 기준 고정 패드점')
    axes[1].plot(t[after],np.linalg.norm(wrist[after,:3]-wrist[anchor,:3],axis=-1)*1000,label='손목 원점(world)')
    axes[1].set_ylabel('2초 기준 변위(mm)');axes[1].legend()
    axes[2].step(t,candidate.astype(int),where='post',label='candidate 끝점값')
    axes[2].set_ylim(-.05,1.1);axes[2].set_ylabel('candidate');axes[2].set_xlabel('로컬 시간(s)');axes[2].legend()
    for ax in axes:
        ax.axvline(2,color='gray',ls='--');ax.axvline(press,color='purple',ls=':');ax.axvspan(3,end,color='green',alpha=.15);ax.grid(alpha=.2)
    fig.suptitle('증분seed17 최종 env0 · 실제 움직임 분해(60Hz) · 인과 기여율 아님')
    fig.tight_layout();fig.savefig(output/'motion.png',dpi=140);plt.close(fig)
    lines=['# 증분 seed17 최종 env0의 움직임 시점','',
        '기존218개60Hz 끝점만 분석했다. 새 물리 실행·warmup·상태 변경은 없다. q/target 범위와 패드 상대운동은 사전 지정env0 한 시도의 기하 기록이며 자연스러움이나 인과 기여율을 뜻하지 않는다.','',
        '선정축 순서: '+', '.join(joint_names)+'.','',
        '| 구간 | 끝점 수 | 실제각 범위4축(°) | 명령각 범위4축(°) | candidate 끝점 수 |','|---|---:|---|---|---:|']
    for name,row in phases.items():
        lines.append('| %s | %d | %s | %s | %d |'%(name,row['endpoint_count'],', '.join('%.3f'%v for v in row['actual_range_deg']),', '.join('%.3f'%v for v in row['target_range_deg']),row['candidate_endpoints']))
    lines += ['', '구간은 (0,2], (2,press), [press,end], (end,마지막]이며 press=2.9787s/end=3.1174s다. 실제 첫 표본은1/60s이므로 reset t0의 움직임을 직접 포함하지 않는다.','',
        '2초부터 마지막 표본까지 고정 패드점의 wrist-local 최대 변위는%.3fmm, 손목 원점 world 최대 변위는%.3fmm, 손목 최대 회전은%.3f°다. 기존128개 pad sample 전체의 상대변위 RMS 최댓값은%.3fmm다.'%(after_two['fixed_pad_wrist_local']['max_from_first_mm'],after_two['wrist_world']['max_from_first_mm'],after_two['wrist_rotation_max_deg'],after_two['all128_patch_max_rms_displacement_mm']), '',
        '고정 패드점은 기존 mesh sample 중 patch centroid와 가장 가까운 점으로 선택했다. 시점마다 최근접점을 바꾸지 않았으며, 결과에 유리한 점을 고른 것이 아니다. world 위치와 wrist-local 위치의 차이를 비율로 합산하거나 손가락/팔의 인과 기여율로 해석하지 않는다.','',
        'candidate 끝점 연속 구간: '+json.dumps(runs,ensure_ascii=False)+'.', '',
        '60Hz candidate의 첫 true 끝점은 실제240Hz 접촉 시작 시점이 아니다. 연속 true 끝점의 시간 범위 역시 원래 접촉 원장의 정밀 유지시간을 대체하지 않는다. 상세 입력 SHA·sample정의·구간별 손목/패드 이동은 analysis.json에 있다.','',
        '![구간별 움직임](motion.png)','']
    (output/'RESULTS.md').write_text('\n'.join(lines))
    print(json.dumps(dict(output=str(output),phases=phases,after_two=after_two,candidate_runs=runs),ensure_ascii=False))


if __name__=='__main__':main()
