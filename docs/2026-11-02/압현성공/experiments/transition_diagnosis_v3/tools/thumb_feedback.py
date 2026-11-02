"""자유 기타 이동과 FK 오차를 분리하고 엄지 5축의 유한 재조준을 진단한다.

최초 동일 학습 초기화 뒤 상태를 쓰지 않는다. 원본 후보를 먼저 재생하고,
최대 두 번 실제 관측에 기준을 둔 CPU 기하 탐색·유한 PD 재생만 수행한다.
정책 학습이나 보상·제어기·물리 변경은 없다.
"""
import argparse
import copy
import json
from pathlib import Path
import sys
from types import SimpleNamespace

BASE=Path(__file__).resolve().parents[1]
ROOT=next(p for p in BASE.parents if (p/'scripts/tab2body.py').is_file())
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(Path(__file__).parent))
from thumb_reachability import sha, write


def run(candidate,out,device,corrections):
    import numpy as np
    import torch
    from scipy.optimize import minimize
    from scipy.spatial.transform import Rotation
    from guitar_learning.tool.experiments.natural_press import NaturalScene
    from guitar_learning.gpu.control import BatchedController
    from guitar_learning.gpu.contact import load_thumb_support,thumb_support_geometry
    from guitar_learning.gpu.finger_skill_environment import FingerSkillEnvironment
    from guitar_learning.gpu.environment import FAILURE_REASONS
    from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
    from guitar_learning.tool.validation.press_acquisition import trajectory_actions
    torch.set_num_threads(1)
    data=json.loads(Path(candidate).read_text())
    if not data['cpu_candidate_valid'] or any(sha(p)!=value for p,value in data['source_sha256'].items()):
        raise ValueError('Unchanged successful CPU candidate required')
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    initial=json.loads(Path(data['initial_catalog']).read_text())
    row=next(r for r in initial['goals'] if r['song']=='virtual_finger_v9_middle_s3_f6')
    config=dict(geometry=data['initial_catalog'],geometry_sha256=sha(data['initial_catalog']),
        song=row['song'],distribution='aligned',initial_distribution=dict(v9_fraction=0.))
    patch=load_thumb_support();valid=torch.as_tensor(patch['valid'],dtype=torch.bool)
    def tensor(x):return torch.as_tensor(x,dtype=torch.float64)
    rear,plane=tensor(patch['rear_vertices']),tensor(patch['plane'])
    center=tensor([data['center_Gy_m']])
    def measure(position,rotation,guitar):
        gp,gr=guitar[:3],Rotation.from_quat(guitar[3:7])
        points=gr.inv().apply(position+rotation.apply(patch['points_local'])-gp)
        normals=gr.inv().apply(rotation.apply(patch['normals_local']))
        with torch.no_grad():
            v=thumb_support_geometry(tensor(points[None]),tensor(normals[None]),valid,center,rear,plane)
        return {k:x[0].tolist() for k,x in v.items()}
    scene=None;trace=[];snapshots=[];fits=[];segments=[];failure=None;report=None
    try:
        scene=NaturalScene(1,'left',device=device,out=out,natural_press=config)
        controller=BatchedController(scene,finger_action_mode='position')
        metadata=copy.deepcopy(scene.metadata);metadata['action_contract']=copy.deepcopy(controller.contract)
        env=FingerSkillEnvironment(metadata,bundle=ROOT/'data/song_bundles/virtual_middle_s3_f6_f7_AB_v2',
            song=dict(pre_roll_s=3.,tail_s=.5,left_fraction=.4,window_s=.1),
            skill=dict(schema='guitar_learning.finger_skill.v3',phase='J',exploration='independent',
                hold_ticks=1,scope='scheduled',planned_transitions=4,full_song_after=1),hand='left',device=device)
        sample=scene.snapshot();ids=torch.arange(1,device=device)
        controller.reset(ids,sample);controller.target[:]=scene.initial_hold
        env.set_evaluation(True,full_song=True);env.reset(ids,sample)
        native=np.asarray(data['native_indices']);channels=np.asarray(data['active_channels'])
        gi=env.guitar_index;ti=env.thumb_support_index
        initial_guitar=sample['body_state'][0,gi,:7].cpu().numpy().copy()
        initial_fk=full_fk(SimpleNamespace(names=scene.names,human_bodies=scene.human_bodies,
            q_ref=np.asarray(data['initial_q105'])),row['state'])
        last=scene.efforts.clone();reset_count=scene.reset_calls
        fixed=scene.initial_hold[:,controller.active].clone()
        # 관측한 실제 몸체 자세와 DOF를 같은 시점에 저장한다.
        def snapshot(label):
            q=sample['q'][0].cpu().numpy().astype(float).copy()
            bodies=sample['body_state'][0].cpu().numpy().copy()
            guitar=bodies[gi,:7].copy();thumb=bodies[ti,:7].copy()
            p,r=initial_fk(q)['LH:thumb3']
            old_g=measure(p,r,initial_guitar)
            live_g=measure(p,r,guitar)
            actual=measure(thumb[:3],Rotation.from_quat(thumb[3:7]),guitar)
            original_guitar=row['state']['guitar_body_states'][0]['pose']
            source_guitar=np.r_[[original_guitar['p'][k] for k in 'xyz'],
                                [original_guitar['r'][k] for k in 'xyzw']]
            source=measure(p,r,source_guitar)
            value=dict(label=label,time_s=len(trace)/240.,q105=q.tolist(),
                body_names=scene.body_names,body_state=bodies.tolist(),guitar_pose=guitar.tolist(),
                original_fk_initial_guitar=old_g,original_fk_live_guitar=live_g,
                original_fk_catalog_guitar=source,native_thumb_live_guitar=actual,
                guitar_gap_effect_m=live_g['signed_gap']-old_g['signed_gap'],
                original_fk_native_gap_residual_m=actual['signed_gap']-live_g['signed_gap'],
                original_fk_native_thumb_position_error_m=float(np.linalg.norm(p-thumb[:3])),
                original_fk_native_thumb_rotation_error_rad=float((r.inv()*Rotation.from_quat(thumb[3:7])).magnitude()),
                guitar_translation_since_reset_m=float(np.linalg.norm(guitar[:3]-initial_guitar[:3])),
                guitar_rotation_since_reset_rad=float((Rotation.from_quat(initial_guitar[3:7]).inv()*Rotation.from_quat(guitar[3:7])).magnitude()))
            snapshots.append(value)
            return q,bodies,guitar
        def playback(label,goal,duration=2.,hold=2.):
            nonlocal sample,last,failure
            start=controller.target[:,controller.active].clone()
            goal=torch.tensor(goal,device=device,dtype=start.dtype)
            rates=controller.rate[torch.tensor(native,device=device)]
            duration=max(duration,float((1.875*(goal-start[0,channels]).abs()/rates.clamp_min(1e-9)).max())+.1)
            begin=len(trace)
            for tick in range(round((duration+hold)*60)):
                t=(tick+1)/60.;u=min(1.,t/duration);blend=u*u*u*(10+u*(-15+6*u))
                desired=fixed.clone();desired[:,channels]=start[:,channels]+blend*(goal-start[:,channels])
                action=trajectory_actions(desired,controller.reference[controller.active],controller.action_low,controller.action_high)
                target=controller.targets(action,sample)
                for sub in range(4):
                    efforts=controller.efforts(sample);checks=controller.diagnostics
                    if not bool((checks['finite']&checks['chest_witness_certified']).all()):
                        raise RuntimeError('Finite/support controller certificate failed')
                    undefined=~checks['chest_normal_defined']
                    efforts=torch.where(undefined[:,None],last,efforts);last.copy_(efforts)
                    sample=scene.step(target,efforts)
                    env.clock[:]=len(trace)+1
                    env.tick_failure=torch.zeros(1,len(FAILURE_REASONS),dtype=torch.bool,device=device)
                    env.tick_cost=torch.zeros(1,device=device)
                    env._snapshot(sample);env._safety()
                    trace.append(dict(segment=label,time_s=(len(trace)+1)/240.,hold=t>duration,
                        **{k:v[0].cpu().tolist() for k,v in env.thumb_support.items()},
                        actual_q105=sample['q'][0].cpu().tolist(),
                        guitar_pose=sample['body_state'][0,gi,:7].cpu().tolist(),
                        thumb_pose=sample['body_state'][0,ti,:7].cpu().tolist()))
                    if bool(env.tick_failure.any()) or bool(undefined.any()):
                        failure=dict(time_s=trace[-1]['time_s'],reason='physical/support failure');break
                if failure:break
            held=[r for r in trace[begin:] if r['hold']]
            segments.append(dict(label=label,ramp_s=duration,hold_observed_s=len(held)/240.,
                contact_candidate_s=sum(bool(r['contact_candidate']) for r in held)/240.,
                near_geometry_s=sum(bool(r['near_geometry']) for r in held)/240.,
                min_gap_m=min((r['signed_gap'] for r in held),default=None),
                max_normal_load_N=max((r['normal_load'] for r in held),default=None)))
            snapshot(label+'_end')
        snapshot('reset')
        playback('original_cpu_candidate',data['best']['x'])
        for attempt in range(corrections):
            if failure:break
            q,bodies,guitar=snapshot('feedback_'+str(attempt)+'_start')
            state=copy.deepcopy(row['state'])
            for name,body in zip(scene.human_bodies,bodies[:len(scene.human_bodies)]):
                old=state['human_body_states'][scene.human_bodies.index(name)]
                old['pose']['p']=dict(zip('xyz',body[:3].tolist()))
                old['pose']['r']=dict(zip('xyzw',body[3:7].tolist()))
            anchored=full_fk(SimpleNamespace(names=scene.names,human_bodies=scene.human_bodies,q_ref=q),state)
            lo=np.asarray(data['action_lower'])[channels];hi=np.asarray(data['action_upper'])[channels]
            seed=q[native].copy()
            def evaluate(x):
                candidate_q=q.copy();candidate_q[native]=x
                p,r=anchored(candidate_q)['LH:thumb3']
                return measure(p,r,guitar)
            def objective(x):
                v=evaluate(x)
                return ((v['signed_gap']+.0002)/.003)**2+(v['region_excess']/.003)**2+.1*(1-v['quality'])+1e-5*float(np.square(x-seed).sum())
            fit=minimize(objective,np.clip(seed,lo+1e-8,hi-1e-8),method='Powell',bounds=list(zip(lo,hi)),
                options={'maxiter':80,'maxfev':2200,'xtol':1e-6,'ftol':1e-8})
            v=evaluate(fit.x)
            fits.append(dict(attempt=attempt,q105_anchor=q.tolist(),guitar_pose_anchor=guitar.tolist(),
                thumb_target_rad=fit.x.tolist(),measurement=v,nfev=int(fit.nfev),optimizer_success=bool(fit.success),
                instantaneous_anchored_residual=evaluate(seed)))
            if not (v['valid'] and -.001<v['signed_gap']<.003 and v['region_excess']<.001 and v['normal_cos']>=.1):
                fits[-1]['not_replayed']='CPU same-point geometry failed';break
            playback('feedback_'+str(attempt),fit.x)
        report=dict(schema='guitar_learning.thumb_feedback.v1',failure=failure,segments=segments,
            corrections=corrections,correction_fits=len(fits),no_intermediate_reset=scene.reset_calls==reset_count,
            native_verified=bool(not failure and any(s['contact_candidate_s']>=.1 for s in segments)),
            limitation='Finite source geometry and thumb3 native resultant load proxies; no contact-pair/pressure or collision-free anatomy certification',
            candidate_sha256=sha(candidate),script_sha256=sha(__file__))
    finally:
        if scene is not None:scene.close()
        write(out/'trace240.json',trace);write(out/'snapshots.json',snapshots);write(out/'fits.json',fits)
        if report is not None:write(out/'report.json',report)
    print(json.dumps(report,ensure_ascii=False),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--candidate',type=Path,default=BASE/'geometry/thumb_candidate.json')
    parser.add_argument('--out',type=Path,required=True);parser.add_argument('--device',default='cuda:0')
    parser.add_argument('--corrections',type=int,choices=(1,2),default=2);args=parser.parse_args()
    import isaacgym  # torch보다 먼저 native를 초기화한다.
    run(args.candidate,args.out,args.device,args.corrections)
