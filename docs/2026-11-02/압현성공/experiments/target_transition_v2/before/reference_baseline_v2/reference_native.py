"""한 휴지 길이의 참조각 경로를 자유 기타 GPU 물리에서 재생한다.

새 프로세스로 한 gap만 실행한다. 최초 A-hover reset 이후 상태 쓰기 없이 기존
직접 위치 제어기의 smoothing/rate/PD를 통과한다. 정책·학습 성공과 구분한다.
"""
if __name__=='__main__':
    import isaacgym

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import numpy as np

ROOT=Path(__file__).resolve().parents[6]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(Path(__file__).parent))
from reference_motion import trajectory, quintic


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value): path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def reset_state_for_q(reference,q):
    """일치하는 q와 body를 최초 reset 입력에만 생성한다."""
    from guitar_learning.runtime.prepared_reset_v1 import load_gpu_prepared_reset_contract
    from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
    original=load_gpu_prepared_reset_contract('left')
    initial=original['initial']; state=copy.deepcopy(reference['initial_state'])
    fk=full_fk(SimpleNamespace(names=initial['joint_names'],human_bodies=initial['human_body_names'],
        q_ref=np.array(reference['initial_q105'])),state)
    poses=fk(q)
    for row,v in zip(state['human_dof_states'],q): row.update(pos=float(v),vel=0.)
    for name,row in zip(initial['human_body_names'],state['human_body_states']):
        p,r=poses[name]; row['pose']=dict(p=dict(zip('xyz',map(float,p))),r=dict(zip('xyzw',map(float,r.as_quat()))))
        row['vel']={kind:dict.fromkeys('xyz',0.) for kind in ('linear','angular')}
    return state


def run(candidate_path,gap,out,device):
    import torch
    from guitar_learning.tool.experiments.natural_press import NaturalScene
    from guitar_learning.gpu.control import BatchedController
    from guitar_learning.gpu.environment import FAILURE_REASONS
    from guitar_learning.gpu.finger_skill_environment import FingerSkillEnvironment
    from guitar_learning.tool.validation.press_acquisition import trajectory_actions
    from guitar_learning.training.training_log_io import project_source_paths
    reference=json.loads(candidate_path.read_text())
    if reference['schema']!='target_transition.reference_motion.v2': raise ValueError('reference v2 required')
    if any(sha(p)!=value for p,value in reference['source_sha256'].items()):
        raise ValueError('CPU reference inputs changed; regenerate before replay')
    if not all(row['cpu_candidate_valid'] for row in reference['candidates'].values()):
        raise ValueError('All source geometry endpoints must pass before native replay')
    times,qs,keyframes=trajectory(reference['candidates'],gap)
    out.mkdir(parents=True,exist_ok=False)
    q_hover=np.array(reference['candidates']['A_hover']['q105'])
    state=reset_state_for_q(reference,q_hover)
    row=dict(song='reference_motion_v2',state=state,q105=q_hover.tolist(),
        hold_target105=reference['candidates']['A_hover']['hold_target105'])
    catalog=out/'reset_catalog.json'; write(catalog,dict(goals=[row]))
    config=dict(geometry=str(catalog.resolve()),geometry_sha256=sha(catalog),song='reference_motion_v2',
        distribution='aligned',initial_distribution=dict(v9_fraction=0.))
    settings=dict(schema=reference['schema'],gap_s=gap,prepare_s=1.5,hold_s=1.5,
        diagnostic_only=True,policy_training=False,physics='unmodified GPU free gravity guitar',
        state_writes='one initial A_hover reset before any physics; no intermediate reset/state writes',
        active_channels=reference['active_channels'],keyframes=keyframes,
        metric='native loaded assigned pad plus current wrong veto; no acoustic or pair-contact proof',
        candidate_path=str(candidate_path.resolve()),candidate_sha256=sha(candidate_path))
    write(out/'settings.json',settings)
    scene=None; fast=[]; slow=[]; report=None; readback=[]; cleanup_error=None
    try:
        scene=NaturalScene(1,'left',device=device,out=out,natural_press=config)
        control=BatchedController(scene,finger_action_mode='position')
        metadata=copy.deepcopy(scene.metadata);metadata['action_contract']=copy.deepcopy(control.contract)
        metadata['reset_body_source']=dict(schema='target_transition.reference_reset.v2',
            verified=False,native_verified=False,source='fresh source-FK A_hover candidate',
            candidate_sha256=sha(candidate_path),historical_verification_inherited=False)
        # 번들은 실제 동일 두 셀의 현/프렛 정의만 읽는다. 보상/학습 clock은 실행하지 않는다.
        bundle=ROOT/'data/song_bundles/virtual_middle_s3_f6_f7_ABAB_v1'
        env=FingerSkillEnvironment(metadata,bundle=bundle,
            song=dict(pre_roll_s=3.,tail_s=.5,left_fraction=.4,window_s=.1),
            skill=dict(schema='guitar_learning.finger_skill.v3',phase='J',exploration='independent',
                hold_ticks=1,scope='scheduled',planned_transitions=4,full_song_after=1),
            hand='left',device=device)
        sample=scene.snapshot();ids=torch.arange(1,device=device)
        from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
        from scipy.spatial.transform import Rotation
        fk=full_fk(SimpleNamespace(names=scene.names,human_bodies=scene.human_bodies,q_ref=q_hover),state)
        control.reset(ids,sample);control.target[:]=scene.initial_hold
        env.set_evaluation(True,full_song=True);env.reset(ids,sample)
        env.tick_failure=torch.zeros(1,len(FAILURE_REASONS),dtype=torch.bool,device=device)
        env.tick_cost=torch.zeros(1,device=device)
        pins=dict(reference['source_sha256']);pins[str(candidate_path.resolve())]=sha(candidate_path)
        pins.update({str(Path(p).resolve()):sha(p) for p in project_source_paths(sys.modules.items())})
        pins[str(Path(__file__).resolve())]=sha(__file__)
        for p in bundle.rglob('*'):
            if p.is_file():pins[str(p.resolve())]=sha(p)
        write(out/'inputs_before.json',pins);write(out/'metadata.json',metadata)
        if not np.allclose(control.action_low.cpu(),reference['action_lower'],atol=1e-6,rtol=0):
            raise ValueError('CPU/action lower bounds differ')
        if not np.allclose(control.action_high.cpu(),reference['action_upper'],atol=1e-6,rtol=0):
            raise ValueError('CPU/action upper bounds differ')
        active=torch.tensor(reference['active_channels'],device=device)
        desired=scene.initial_hold[:,control.active].clone();initial=desired.clone()
        last_valid=scene.efforts.clone();failure=None
        windows=[(1.5,3.,0),(3.+gap,4.5+gap,1),(4.5+2*gap,6.+2*gap,0)]
        note=[dict(goal_fret=6 if i!=1 else 7,start_s=a,end_s=b,clean_s=0.,wrong_s=0.,
            best_streak_s=0.,first_clean_s=None,observed_s=0.) for i,(a,b,g) in enumerate(windows)]
        streak=np.zeros(3);prev=np.zeros(3,dtype=bool)
        maximum_guitar_distance=0.;maximum_guitar_rotation=0.
        total_ticks=round((1.5+times[-1])*60)
        reset_count_before=scene.reset_calls
        for tick in range(total_ticks):
            t=(tick+1)/60.
            if t<=.5: requested=q_hover
            elif t<1.5:
                requested=q_hover+quintic((t-.5)/1.)*(np.array(reference['candidates']['A_press']['q105'])-q_hover)
            else: requested=qs[min(round((t-1.5)*60),len(qs)-1)]
            req=torch.tensor(requested,device=device,dtype=control.reference.dtype)[control.active]
            desired=initial.clone();desired[:,active]=req[active]
            action=trajectory_actions(desired,control.reference[control.active],control.action_low,control.action_high)
            target=control.targets(action,sample)
            for sub in range(4):
                efforts=control.efforts(sample);checks=control.diagnostics
                if not bool((checks['finite']&checks['chest_witness_certified']).all()):
                    raise RuntimeError('Native controller finite/support certificate failed')
                undefined=~checks['chest_normal_defined'];efforts=torch.where(undefined[:,None],last_valid,efforts)
                last_valid.copy_(efforts);sample=scene.step(target,efforts)
                now=(tick*4+sub+1)/240.
                # 이전 bundle의 음 시각에 정렬하여 wrong 출처의 허가 창만 평가한다.
                # 실제 유지/휴지는 아래 물리 시각 windows로만 채점한다.
                score_time=float(np.interp(now,[0.,1.5,3.,3.+gap,4.5+gap,4.5+2*gap,6.+2*gap],
                    [0.,3.,4.5,5.,6.5,7.,8.5]))
                env.clock[:]=round(score_time*240)
                env._snapshot(sample);env._safety();env.tick_failure[:,-1]|=undefined
                candidate=env.candidate[0,:2].cpu().numpy().copy()
                wrong=env.wrong[0,:2].cpu().numpy().copy()
                if bool(env.tick_failure.any() | env.wrist_failure.any() | env.wrist_severe_failure.any()):
                    reasons=[v for j,v in enumerate(FAILURE_REASONS) if bool(env.tick_failure[0,j])]
                    if bool(env.wrist_failure.any()):reasons.append('wrist_outside')
                    if bool(env.wrist_severe_failure.any()):reasons.append('wrist_severe')
                    failure=dict(time_s=now,reasons=reasons)
                alive=failure is None
                for i,(a,b,goal) in enumerate(windows):
                    in_window=a<now<=b
                    clean=bool(candidate[goal] and alive and in_window)
                    if alive and in_window:
                        note[i]['observed_s']+=1/240.
                        note[i]['clean_s']+=int(clean)/240.
                        note[i]['wrong_s']+=int(wrong[goal])/240.
                    streak[i]=streak[i]+1/240. if clean and prev[i] else (1/240. if clean else 0.)
                    note[i]['best_streak_s']=float(max(note[i]['best_streak_s'],streak[i]));prev[i]=clean
                    if clean and note[i]['first_clean_s'] is None:note[i]['first_clean_s']=now
                gd=float(torch.linalg.vector_norm(env.guitar_delta[0]).cpu())
                ga=float(torch.linalg.vector_norm(env.guitar_rotation[0]).cpu())
                maximum_guitar_distance=max(maximum_guitar_distance,gd);maximum_guitar_rotation=max(maximum_guitar_rotation,ga)
                fast.append(dict(time_s=now,q=scene.q[0].cpu().numpy().copy(),
                    requested_target=desired[0].cpu().numpy().copy(),applied_target=target[0].cpu().numpy().copy(),
                    candidate=candidate,wrong=wrong,position_geometry=env.contact_geometry[0,:2].cpu().numpy().copy(),
                    facing_geometry=env.contact_facing[0,:2].cpu().numpy().copy(),
                    pad_loaded=env.surface_body_loaded[0,:2].cpu().numpy().copy(),
                    wrong_source_flags=env.wrong_source_flags[0,:2].cpu().numpy().copy(),
                    pad_load_n=float(torch.linalg.vector_norm(sample['contact_force'][0,env.pad_indices[1]]).cpu()),
                    distance_m=env.surface_distance[0,:2].cpu().numpy().copy(),
                    signed_height_m=env.surface_height[0,:2].cpu().numpy().copy(),
                    guitar_displacement_m=gd,guitar_rotation_rad=ga,alive=alive))
                if failure is not None:break
            slow.append(dict(time_s=now,body_state=scene.body_state[0].cpu().numpy().copy(),q=scene.q[0].cpu().numpy().copy()))
            if tick<2 or tick%60==0:
                predicted=fk(slow[-1]['q'].astype(float))
                for name in ('L_Wrist','LH:middle3'):
                    actual=slow[-1]['body_state'][scene.body_names.index('human/'+name)]
                    pos,rot=predicted[name]
                    readback.append(dict(time_s=now,body=name,position_error_m=float(np.linalg.norm(pos-actual[:3])),
                        rotation_error_rad=float((rot.inv()*Rotation.from_quat(actual[3:7])).magnitude())))
            if tick%60==0:print('reference',gap,round(now,3),candidate.tolist(),flush=True)
            if failure is not None:break
        for row in note:
            row['best_streak_s']=float(row['best_streak_s'])
            row['diagnostic_hold_100ms']=bool(row['best_streak_s']>=.1-1e-8)
            row['hold_90percent']=bool(row['clean_s']>=1.35-1e-8)
            row['full_hold_observed']=bool(row['observed_s']>=1.5-1e-8)
            row['entire_hold_clean']=bool(row['clean_s']>=1.5-1e-8)
        report=dict(schema=reference['schema'],settings=settings,notes=note,failure=failure,
            native_verified=bool(failure is None and all(r['hold_90percent'] for r in note)),
            maximum_guitar_displacement_m=maximum_guitar_distance,maximum_guitar_rotation_rad=maximum_guitar_rotation,
            physics_steps=scene.physics_steps,reset_calls_before_physics=reset_count_before,
            reset_calls_after_physics=scene.reset_calls,no_intermediate_reset=scene.reset_calls==reset_count_before,
            source_unchanged=all(sha(p)==value for p,value in pins.items()),
            controller_contract=control.contract,scene=scene.diagnostics,
            initial_hover_native_readback=readback[:2],
            source_fk_actual_readback_max_position_m=max(r['position_error_m'] for r in readback),
            source_fk_actual_readback_max_rotation_rad=max(r['rotation_error_rad'] for r in readback),
            limitation='Three held references only; no trained policy, acoustic signal or exact contact pair guarantee.')
        write(out/'source_fk_readback.json',readback)
    except BaseException as error:
        write(out/'failure.json',dict(error=repr(error),physics_samples=len(fast)))
        raise
    finally:
        for filename,rows in (('trace240.npz',fast),('poses60.npz',slow)):
            if rows:np.savez_compressed(out/filename,**{k:np.stack([r[k] for r in rows]) for k in rows[0]})
        if scene is not None:
            try:scene.close()
            except BaseException as error:
                cleanup_error=repr(error)
                write(out/'cleanup_failure.json',dict(error=cleanup_error))
    if report is not None:
        report['scene_destroyed']=bool(scene is not None and scene.closed)
        report['cleanup_error']=cleanup_error
        report['initial_hover_readback_consistent']=bool(readback and all(r['position_error_m']<=.002 and
            r['rotation_error_rad']<=.05 for r in readback[:2]))
        report['finite_trace']=bool(all(np.isfinite(row['q']).all() and np.isfinite(row['applied_target']).all() for row in fast))
        report['native_verified']=bool(report['native_verified'] and report['source_unchanged'] and
            report['no_intermediate_reset'] and report['scene_destroyed'] and cleanup_error is None and
            report['initial_hover_readback_consistent'] and report['finite_trace'])
        report['verification_level']='90percent-of-each-1.5s-hold plus safety/readback/source/cleanup; entire_hold_clean separately reported'
        write(out/'report.json',report)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidates',type=Path,required=True)
    p.add_argument('--gap',type=float,choices=(.5,.75,1.),required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--device',default='cuda:0');args=p.parse_args()
    report=run(args.candidates,args.gap,args.out,args.device)
    print(json.dumps(dict(native_verified=report['native_verified'],notes=report['notes']),indent=2))


if __name__=='__main__':main()
