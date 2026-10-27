"""CPU diagnostics of predeclared0..7 saved poses; no native physics or policy."""
import argparse
import copy
import json
from pathlib import Path
import sys

import numpy as np
from scipy.spatial.transform import Rotation
import torch

PHASE=Path(__file__).resolve().parent
ROOT=PHASE.parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(PHASE))
from evaluate_checkpoints import (require,sha,write,validate_capture,validate_input_contract,
    posture_metadata,checkpoint_selection,CHECKPOINT_UPDATES,SOURCE_PHASE,SOURCE_SEAL_SHA)
from guitar_learning.gpu.finger_reward import (finger_posture_reward,finger_target_indices,
    FINGER_COORDINATION_CONTRACT)
from guitar_learning.training.recording import project_source_paths

FINGERS=('index','middle','ring','pinky')
DEG=180/np.pi


def scipy_angles(palm,segments):
    """Independent normalized parent/child matrix action oracle, xyzw."""
    parent=np.concatenate((np.broadcast_to(palm[:,None,None],(len(palm),4,1,4)),segments[:,:,:2]),axis=2)
    ok=np.isfinite(parent).all(-1)&np.isfinite(segments).all(-1)&(np.linalg.norm(parent,axis=-1)>1e-12)&(np.linalg.norm(segments,axis=-1)>1e-12)
    identity=np.array([0.,0.,0.,1.])
    p=np.where(ok[...,None],parent,identity);c=np.where(ok[...,None],segments,identity)
    relative=Rotation.from_quat(p.reshape(-1,4)).inv()*Rotation.from_quat(c.reshape(-1,4))
    direction=relative.apply(np.tile([0.,-1.,0.],(relative.as_quat().shape[0],1))).reshape(ok.shape+(3,))
    valid=ok&(np.linalg.norm(direction[...,1:],axis=-1)>=1e-6)
    return np.where(valid,np.arctan2(-direction[...,2],-direction[...,1]),0.),valid


def measure(now,targets,palm,segments):
    now=torch.as_tensor(now,dtype=torch.float64)
    columns=[torch.tensor([t[key] for t in targets],dtype=torch.float64) for key in ('onset_s','end_s','press_s')]
    finger=torch.tensor([t['finger'] for t in targets],dtype=torch.long)
    with torch.no_grad():
        posture=finger_posture_reward(now,*columns,finger,torch.as_tensor(palm,dtype=torch.float64),torch.as_tensor(segments,dtype=torch.float64))
        selection=finger_target_indices(now,*columns,finger)
    result={k:v.numpy() for k,v in posture.items()}
    independent,valid=scipy_angles(np.asarray(palm),np.asarray(segments))
    require(np.array_equal(valid,result['valid']), 'SciPy/helper geometric validity differs')
    error=float(np.max(np.abs(independent-result['angles']))*DEG) if independent.size else 0.
    require(error<1e-8,'SciPy/helper signed angles differ')
    indices=selection['indices'][:,:,0].numpy();tracking=selection['valid'][:,:,0].numpy()
    audible=np.zeros_like(tracking)
    if targets:
        onset=np.array([t['onset_s'] for t in targets]);end=np.array([t['end_s'] for t in targets])
        chosen=np.maximum(indices,0);clock=now.numpy()[:,None]
        audible=tracking&(onset[chosen]<=clock)&(clock<end[chosen])
    result.update(roles=np.where(audible,2,np.where(tracking,1,0)),
        next_valid=selection['valid'][:,:,1].numpy(),oracle_max_error_deg=error)
    return result


def describe(values):
    a=np.asarray(values,dtype=np.float64)
    return dict(n=int(a.size),mean=float(a.mean()),min=float(a.min()),max=float(a.max())) if a.size else dict(n=0,mean=None,min=None,max=None)


def summarize_finger(measured,finger,q,target,actions,low,high):
    angles=measured['angles'][:,finger]*DEG;valid=measured['valid'][:,finger]
    roles=measured['roles'][:,finger];idle=measured['idle_weight'][:,finger]
    groups=dict(all=np.ones(len(q),bool),audible=roles==2,preparation=roles==1,
        no_tracking=roles==0,idle_full=idle>=1-1e-12,idle_fade=(idle>1e-12)&(idle<1-1e-12))
    result={}
    for name,mask in groups.items():
        usable=mask&valid.all(-1);a=angles[usable]
        mcp,pip,dip=a.T if len(a) else (np.array([]),)*3
        violation=np.stack((np.maximum(dip-pip-20,0),np.maximum(dip-mcp-60,0),
            np.maximum(-mcp-20,0)*np.clip((dip-30)/15,0,1)),axis=-1)
        positive=np.maximum(a,0);total=positive.sum(-1);bent=total>1e-8
        qvalues=q[mask];tvalues=target[mask]
        native=[]
        for j in range(4):
            diff=qvalues[:,j]-tvalues[:,j]
            native.append(dict(q_deg=describe(qvalues[:,j]*DEG),target_deg=describe(tvalues[:,j]*DEG),
                requested_velocity_rad_s=describe(4*actions[mask,j]),
                near_lower_2deg_count=int((qvalues[:,j]<=low[j]+2/DEG).sum()),
                near_upper_2deg_count=int((qvalues[:,j]>=high[j]-2/DEG).sum()),
                q_target_rms_deg=float(np.sqrt(np.mean(diff**2))*DEG) if len(diff) else None))
        difference=(angles-q[:,[0,2,3]]*DEG+180)%360-180
        counts=dict(distal_over_pip20=(violation[:,0]>1e-8),distal_over_mcp60=(violation[:,1]>1e-8),
            base_back_with_distal=(violation[:,2]>1e-8),
            pip_straight_distal_bent=(np.abs(pip)<10)&(dip>60),fully_straight=(np.abs(a)<10).all(-1),distal_above60=dip>60)
        result[name]=dict(endpoint_samples=int(mask.sum()),usable_triplets=int(usable.sum()),
            valid_joint_counts=valid[mask].sum(0).tolist(),
            valid_joint_fraction=valid[mask].mean(0).tolist() if mask.any() else [None]*3,
            usable_fraction=float(valid[mask].all(-1).mean()) if mask.any() else None,
            angles_deg=[describe(angles[mask&valid[:,j],j]) for j in range(3)],
            violation_counts={k:int(v.sum()) for k,v in counts.items()},
            violation_fraction={k:float(v.mean()) if v.size else None for k,v in counts.items()},
            violation_mean_deg=[float(v.mean()) if len(v) else None for v in violation.T],
            coordination_quality=describe(measured['coordination_quality'][mask,finger]),
            standby_quality=describe(measured['standby_quality'][mask,finger]),idle_weight=describe(idle[mask]),
            idle_weighted_standby_quality=describe((idle*measured['standby_quality'][:,finger])[mask]),
            mean_positive_flexion_share=(positive[bent]/total[bent,None]).mean(0).tolist() if bent.any() else None,
            flexion_share_samples=int(bent.sum()),native_axes=native,
            geometric_minus_native_q_rms_deg=[float(np.sqrt(np.mean(difference[mask&valid[:,j],j]**2))) if (mask&valid[:,j]).any() else None for j in range(3)])
    return result


def pooled(captures):
    """Endpoint-weighted capture summary, with explicit safety and role counts."""
    result={}
    for group,rows in (('all',captures),('safe',[r for r in captures if r['full_safe']]),('failed',[r for r in captures if not r['full_safe']])):
        fingers={}
        for f in FINGERS:
            fingers[f]={}
            for role in ('all','audible','preparation','idle_full'):
                samples=[r['fingers'][f]['roles'][role] for r in rows]
                n=sum(r['endpoint_samples'] for r in samples);usable=sum(r['usable_triplets'] for r in samples)
                pip=[r['angles_deg'][1] for r in samples if r['angles_deg'][1]['n']]
                pn=sum(r['n'] for r in pip)
                fingers[f][role]=dict(endpoint_samples=n,usable_triplets=usable,
                    pip_mean_deg=sum(r['mean']*r['n'] for r in pip)/pn if pn else None,
                    pip_min_deg=min(r['min'] for r in pip) if pn else None,pip_max_deg=max(r['max'] for r in pip) if pn else None,
                    violation_fraction={key:sum(r['violation_counts'][key] for r in samples)/usable if usable else None
                        for key in ('distal_over_pip20','distal_over_mcp60','base_back_with_distal','pip_straight_distal_bent','fully_straight','distal_above60')},
                    coordination_quality_mean=sum(r['coordination_quality']['mean']*r['endpoint_samples'] for r in samples if r['endpoint_samples'])/n if n else None,
                    standby_quality_mean=sum(r['standby_quality']['mean']*r['endpoint_samples'] for r in samples if r['endpoint_samples'])/n if n else None)
        result[group]=dict(captures=len(rows),endpoint_samples=sum(r['endpoint_samples'] for r in rows),fingers=fingers)
    return result


def plot_selected(out,trace):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    paths=[];now,measured,actions=trace['time_s'],trace['measured'],trace['actions']
    for kind in ('angles_idle','requested_velocity'):
        fig,axes=plt.subplots(4,1,figsize=(12,10),sharex=True)
        for f,ax in enumerate(axes):
            if kind=='angles_idle':
                for j,label in enumerate(('MCP','PIP','DIP')):
                    ax.plot(now,np.where(measured['valid'][:,f,j],measured['angles'][:,f,j]*DEG,np.nan),label=label,linewidth=1)
                other=ax.twinx();other.fill_between(now,0,measured['idle_weight'][:,f],alpha=.12,color='black');other.set_ylim(0,1);other.set_ylabel('idle')
                ax.set_ylabel(FINGERS[f]+' deg')
            else:
                for j,label in enumerate(('1_x','1_z','2','3')):ax.plot(now,4*actions[:,f,j],label=label,linewidth=1)
                ax.set_ylabel(FINGERS[f]+' rad/s')
            ax.legend(loc='upper right',ncol=4);ax.grid(alpha=.25)
        axes[-1].set_xlabel('Recorded song time (s)');fig.suptitle('Fixed checkpoint %d, preselected env%d; 60Hz endpoints only'%(trace['updates'],trace['env_id']))
        fig.tight_layout();path=out/('selected_best_'+kind+'.png');fig.savefig(path,dpi=150);plt.close(fig)
        paths.append(dict(path=str(path),sha256=sha(path)))
    return paths


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evaluations',type=Path,default=PHASE/'checkpoint_evaluation.json')
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();out=args.out.resolve();pins={str(Path(__file__).resolve()):sha(Path(__file__).resolve())}
    def read(path):
        path=Path(path).resolve();pins[str(path)]=sha(path)
        return json.loads(path.read_text())
    combined=read(args.evaluations)
    require(combined['completed'] and combined['requested_evaluations_completed'] and
        set(combined['evaluated_updates'])==set(CHECKPOINT_UPDATES) and combined['selection']==checkpoint_selection(combined['results']), 'All five actual fixed evaluations required')
    source=read(combined['training_chain']['source_manifest'])
    require(source['active_python_count']==len(source['source'])==436,'Frozen436 source required')
    require(all(Path(p).is_file() and sha(p)==h for p,h in source['source'].items()),'Current source changed')
    pins.update(source['source'])
    seal_path=SOURCE_PHASE/'result_manifest.json';require(sha(seal_path)==SOURCE_SEAL_SHA,'Finger-input baseline seal changed');pins[str(seal_path)]=SOURCE_SEAL_SHA
    torch.set_num_threads(1)
    models=[];selected_trace=None;best=combined['selection']['best']['updates']
    for item in sorted(combined['results'],key=lambda r:r['source_optimizer_updates']):
        folder=Path(item['evaluation_directory']);report=read(folder/'report.json')
        require(report==item and report['training_chain']==combined['training_chain'] and report['gpu_scene']['closed'] and report['gpu_scene']['physx_use_gpu'] and
            report['gpu_scene']['use_gpu_pipeline'] and report['gpu_scene']['environment_count']==1024 and
            report['gpu_scene']['physics_steps']==report['ticks']*4,'Actual closed evaluation differs')
        original=read(folder/'inputs_before.json')
        require(all(Path(p).is_file() and sha(p)==h for p,h in original.items()),'Evaluation input pins changed');pins.update(original)
        require(all(original.get(p)==h for p,h in source['source'].items()),'Evaluation source436 differs')
        contract=read(Path(report['training_chain']['run'])/'training_contract.json');validate_input_contract(contract)
        targets=read(folder/'targets.json');require(len(targets)==67,'Original67 target schedule required')
        rows=[];missing=None
        if not report.get('capture_metadata_path'):
            require(item['source_optimizer_updates']==0,'Trained checkpoint capture missing')
            missing='Actual pose trajectory not captured; prepared t0 in other checkpoints is not the initial-policy trajectory'
        else:
            meta=read(folder/report['capture_metadata_path'])
            require(meta['checkpoint']==report['checkpoint'] and
                meta['checkpoint_sha256']==original[report['checkpoint']] and
                meta['source_optimizer_updates']==item['source_optimizer_updates'] and meta['training_chain']==report['training_chain'],
                'Pose checkpoint/chain identity differs')
            require(meta['posture_reconstruction']==posture_metadata(contract,meta['body_names']) and
                meta['capture_envs']==list(range(8)) and {r['env_id'] for r in meta['captures']}==set(range(8)) and len(meta['captures'])==8,
                'Exact predeclared0..7 capture/posture metadata required')
            require(meta['posture_reconstruction']['source_function_sha256']==pins[str(ROOT/'guitar_learning/gpu/finger_reward.py')], 'Actual helper SHA differs')
            expected=copy.deepcopy(meta['posture_reconstruction']['contract']);expected.pop('frame_source')
            require(expected==FINGER_COORDINATION_CONTRACT,'Posture helper contract changed')
            ctl=contract['action']['target_contract'];names=meta['joint_names'];palm_id=meta['posture_reconstruction']['palm_body_index'];segment_ids=np.array(meta['posture_reconstruction']['segment_body_indices'])
            selected=meta['selected_env_id']
            for capture in sorted(meta['captures'],key=lambda r:r['env_id']):
                env_id=capture['env_id'];path=folder/capture['path'];require(sha(path)==capture['sha256'],'Capture SHA mismatch');pins[str(path)]=sha(path)
                with np.load(path,allow_pickle=False) as archive:arrays={k:archive[k].copy() for k in archive.files}
                episode=next(r for r in report['episodes'] if r['env_id']==env_id);validate_capture(arrays,len(meta['body_names']),episode)
                require(capture['full_safe']==episode['left_curriculum']['full_safe'] and capture['reason']==episode['reason'],'Capture safety identity differs')
                b=arrays['body_state'];m=measure(arrays['clock']/240.,targets,b[:,palm_id,3:7],b[:,segment_ids,3:7])
                prepared_angles=m['angles'][0]*DEG;prepared_valid=m['valid'][0]
                m={k:(v[1:] if isinstance(v,np.ndarray) else v) for k,v in m.items()}
                fingers={};request=[]
                for f,finger in enumerate(FINGERS):
                    joint_names=['LH:'+finger+s for s in ('1_x','1_z','2','3')]
                    ji=[names.index(n) for n in joint_names];ai=[ctl['action_order'].index(n) for n in joint_names]
                    low=np.array(ctl['action_lower_rad'])[ai];high=np.array(ctl['action_upper_rad'])[ai]
                    q=arrays['q'][1:,ji];target=arrays['target'][1:,ji];action=arrays['action'][1:,ai];request.append(action)
                    fingers[finger]=dict(target_count=sum(t['finger']==f+1 for t in targets),native_bounds_deg=(np.stack((low,high),-1)*DEG).tolist(),
                        prepared_angles_deg=prepared_angles[f].tolist(),prepared_valid=prepared_valid[f].tolist(),
                        roles=summarize_finger(m,f,q,target,action,low,high))
                row=dict(env_id=env_id,full_safe=capture['full_safe'],reason=capture['reason'],endpoint_samples=len(arrays['clock'])-1,
                    duration_s=episode['task_time_s'],achieved_notes=episode['song']['left_success_count'],fingers=fingers,oracle_max_error_deg=m['oracle_max_error_deg'])
                rows.append(row)
                if item['source_optimizer_updates']==best and env_id==selected:
                    selected_trace=dict(updates=best,env_id=env_id,time_s=arrays['clock'][1:]/240.,measured=m,actions=np.stack(request,1))
        models.append(dict(updates=item['source_optimizer_updates'],capture_status='missing' if missing else 'available',missing_reason=missing,
            captures=rows,groups=pooled(rows)))
    require(not(project_source_paths(list(sys.modules.items()))-set(pins)),'Unpinned helper imports')
    require(all(Path(p).is_file() and sha(p)==h for p,h in pins.items()),'Analysis inputs changed')
    out.mkdir(parents=True,exist_ok=False)
    media=plot_selected(out,selected_trace) if selected_trace is not None else []
    initial=next(model for model in models if model['updates']==0)
    comparisons=[]
    for model in models:
        if not model['updates'] or not initial['captures'] or not model['captures']:
            continue
        common=sorted({r['env_id'] for r in initial['captures'] if r['full_safe']} &
            {r['env_id'] for r in model['captures'] if r['full_safe']})
        comparisons.append(dict(updates=model['updates'],matched_safe_env_ids=common,
            initial=pooled([r for r in initial['captures'] if r['env_id'] in common])['all'],
            candidate=pooled([r for r in model['captures'] if r['env_id'] in common])['all']))
    require(all(Path(p).is_file() and sha(p)==h for p,h in pins.items()),'Plotting inputs changed')
    write(out/'analysis.json',dict(completed=True,schema='guitar_learning.saved_pose_posture_analysis.v1',models=models,plots=media,inputs_sha256=pins,
        selection=combined['selection'],matched_safe_comparisons_to_initial=comparisons,thresholds=dict(native_limit_proximity_deg=2,pip_straight_abs_deg=10,distal_bent_deg=60,fully_straight_abs_deg=10,violation_numerical_tolerance_deg=1e-8),
        scope='Float64 CPU reconstruction of saved float32 poses, not bit-exact GPU reward replay. Only predeclared0..7 first-episode captures, never all1024. Endpoint-weighted role/safety groups; t0 only a separate prepared-pose reference. Current endpoint clock/240 roles are score assignments, not physical contact. Raw helper qualities are not earned240Hz GPU reward. Native q1_x and full geometric MCP are different definitions; angle difference is not control error. No velocity/jerk or pressure/acoustic certification.'))
    lines=['# 저장 자세의 손가락 협응 진단','',
        '사전 지정 환경0..7의 첫 곡만 분석했다. 안전/실패·모델·악보 역할을 분리하며, 전체1024환경이나 다른 seed/곡으로 일반화하지 않는다. t0를 제외한60Hz끝점이 분모다.','',
        '|모델|캡처|안전/실패|검지 PIP 평균|중지 PIP 평균|약지 PIP 평균|소지 PIP 평균|','|---|---:|---:|---:|---:|---:|---:|']
    for model in models:
        groups=model['groups'];values=[groups['all']['fingers'][f]['all']['pip_mean_deg'] for f in FINGERS]
        lines.append('|%d|%d|%d/%d|%s|'%(model['updates'],groups['all']['captures'],groups['safe']['captures'],groups['failed']['captures'],
            '|'.join('자료 없음' if v is None else '%.3f°'%v for v in values)))
    def fmt(value, percent=False):
        return '자료 없음' if value is None else ('%.1f%%'%(100*value) if percent else '%.3f'%value)
    for model in models:
        lines+=['','## %d회: 안전·실패 캡처 분리'%model['updates'],'',
            '|구분·손가락|유효 끝점|PIP 평균/범위°|DIP−PIP>20°|DIP−MCP>60°|기저 반대굽힘 조건|완전대기 끝점|대기 완전펴짐|대기 DIP>60°|대기 품질|',
            '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
        for group,label in (('safe','안전'),('failed','실패')):
            for finger in FINGERS:
                allrow=model['groups'][group]['fingers'][finger]['all'];idle=model['groups'][group]['fingers'][finger]['idle_full']
                v=allrow['violation_fraction'];iv=idle['violation_fraction']
                lines.append('|%s·%s|%d|%s / %s..%s|%s|%s|%s|%d|%s|%s|%s|'%(label,finger,allrow['usable_triplets'],
                    fmt(allrow['pip_mean_deg']),fmt(allrow['pip_min_deg']),fmt(allrow['pip_max_deg']),
                    fmt(v['distal_over_pip20'],True),fmt(v['distal_over_mcp60'],True),fmt(v['base_back_with_distal'],True),
                    idle['usable_triplets'],fmt(iv['fully_straight'],True),fmt(iv['distal_above60'],True),fmt(idle['standby_quality_mean'])))
    lines+=['','PIP 평균만으로 개선을 판정하지 않는다. analysis.json의 안전/실패·현재음/준비음/완전대기 분모, 실제 MCP/PIP/DIP 범위와 끝관절 편중·soft prior 위반, 실제 각도와 native q의 차이를 함께 확인해야 한다.',
        '','실제 전체 몸체 quaternion의 부모-자식 상대회전에서 각도를 구했고 각 끝점을 독립 SciPy 수식으로 대조했다. 대기에는0.25초 fade가 있어 선택 목표 없음과 완전대기는 다르다. helper 품질은 단계/실패 마스크 이전의 끝점 진단이며 실제 누적 학습 보상이 아니다.',
        '','초기와 비교 모델 양쪽에서 안전한 동일 envID의 통계도 analysis.json matched_safe_comparisons_to_initial에 별도로 보존했다. 공통 안전 표본이0이면 분모0/자료 없음이며 다른 환경으로 대신하지 않는다.',
        '','기록이 없는 초기 정책은 missing으로 표시한다. 다른 모델의 준비 t0로 초기 정책의 전체 움직임을 추정하지 않는다. 비교는 동일 곡·준비 자세의 서로 다른 고정 정책이며, 변화 원인의 인과를 확정하지 않는다. 속도·jerk를 측정하지 않아 급가속 개선을 주장하지 않는다.','']
    (out/'report.md').write_text('\n'.join(lines))
    print(json.dumps(dict(completed=True,models=len(models),plots=len(media))))


if __name__=='__main__':main()
