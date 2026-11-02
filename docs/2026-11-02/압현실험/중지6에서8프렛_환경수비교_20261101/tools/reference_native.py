"""한 휴지 길이의 참조각 경로를 자유 기타 GPU 물리에서 재생한다.

새 프로세스로 한 gap만 실행한다. 학습과 같은 최초 catalog reset 이후 상태 쓰기 없이 기존
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

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'scripts/tab2body.py').is_file())
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(Path(__file__).parent))
from reference_motion import trajectory, quintic, keyframes, SETTLE_S


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value): path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def run(candidate_path,gap,out,device):
    import torch
    from guitar_learning.tool.experiments.natural_press import NaturalScene
    from guitar_learning.gpu.control import BatchedController
    from guitar_learning.gpu.environment import FAILURE_REASONS
    from guitar_learning.gpu.finger_skill_environment import FingerSkillEnvironment
    from guitar_learning.tool.validation.press_acquisition import trajectory_actions
    from guitar_learning.training.training_log_io import project_source_paths
    if gap != .75:
        raise ValueError('6 to 8 reference requires .75s gap')
    reference=json.loads(candidate_path.read_text())
    if reference['schema']!='middle_f6_f8.reference_motion.v1': raise ValueError('6 to 8 reference v1 required')
    if any(sha(p)!=value for p,value in reference['source_sha256'].items()):
        raise ValueError('CPU reference inputs changed; regenerate before replay')
    if not all(row['cpu_candidate_valid'] for row in reference['candidates'].values()):
        raise ValueError('All source geometry endpoints must pass before native replay')
    times,qs,frames=trajectory(reference['candidates'],gap)
    out.mkdir(parents=True,exist_ok=False)
    initial_catalog=candidate_path.parent.parent/'initial_catalog.json'
    initial_provenance=candidate_path.parent.parent/'initial_provenance.json'
    initial_data=json.loads(initial_catalog.read_text()); provenance=json.loads(initial_provenance.read_text())
    if sha(initial_catalog)!=provenance['catalog_sha256']:
        raise ValueError('Current training initial catalog hash differs')
    for path,value in provenance['active_physical_inputs'].items():
        if sha(ROOT/path)!=value:raise ValueError('Initial catalog physical input changed: '+path)
    row=initial_data['goals'][0];q_hover=np.array(row['q105']);state=copy.deepcopy(row['state'])
    initial_hold=np.array(row['hold_target105'])
    catalog=initial_catalog
    config=dict(geometry=str(catalog.resolve()),geometry_sha256=sha(catalog),song=row['song'],
        distribution='aligned',initial_distribution=dict(v9_fraction=0.))
    settings=dict(schema=reference['schema'],gap_s=gap,prepare_s=3.,hold_s=1.5,settle_s=SETTLE_S,
        diagnostic_only=True,policy_training=False,physics='unmodified GPU free gravity guitar',
        state_writes='current training initial_catalog unchanged at reset; no intermediate reset/state writes',
        initial_catalog=str(initial_catalog.resolve()),initial_catalog_sha256=sha(initial_catalog),
        initial_state_matches_training_catalog=True,
        preparation='0-.5s initial hold;.5-2.8s quintic A approach;2.8-3s settle;direct physical song clock',
        active_channels=reference['active_channels'],keyframes=frames,
        metric='native loaded assigned pad plus current wrong veto; no acoustic or pair-contact proof',
        candidate_path=str(candidate_path.resolve()),candidate_sha256=sha(candidate_path))
    write(out/'settings.json',settings)
    scene=None; fast=[]; slow=[]; report=None; readback=[]; cleanup_error=None
    try:
        scene=NaturalScene(1,'left',device=device,out=out,natural_press=config)
        control=BatchedController(scene,finger_action_mode='position')
        metadata=copy.deepcopy(scene.metadata);metadata['action_contract']=copy.deepcopy(control.contract)
        metadata['reset_body_source']=dict(schema='target_transition.reference_reset.v2',
            verified=False,native_verified=False,source='current training initial_catalog unchanged row',
            training_initial_catalog_sha256=sha(initial_catalog),
            candidate_sha256=sha(candidate_path),historical_verification_inherited=False)
        # 번들은 실제 동일 두 셀의 현/프렛 정의만 읽는다. 보상/학습 clock은 실행하지 않는다.
        bundle=ROOT/'data/song_bundles/virtual_middle_s3_f6_f8_AB_v1'
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
        for path in (initial_catalog,initial_provenance):pins[str(path.resolve())]=sha(path)
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
        raw_frames=keyframes(reference['candidates'],gap)
        native_indices=np.array(reference['native_indices'])
        peak=np.max([1.875*np.abs(b[2][native_indices]-a[2][native_indices])/(b[0]-a[0])
            for a,b in zip(raw_frames,raw_frames[1:])],axis=0)
        actual_rate=control.rate[torch.tensor(native_indices,device=device)].cpu().numpy()
        if not bool((peak<=actual_rate+1e-8).all()):
            raise ValueError('Continuous quintic request exceeds actual native controller rate')
        settings['continuous_peak_request_rad_s']=peak.tolist()
        settings['actual_controller_rate_rad_s']=actual_rate.tolist()
        write(out/'settings.json',settings)
        desired=scene.initial_hold[:,control.active].clone();initial=desired.clone()
        last_valid=scene.efforts.clone();failure=None
        windows=[(3.,4.5,0),(5.25,6.75,1)]
        note=[dict(goal_fret=6 if i==0 else 8,start_s=a,end_s=b,clean_s=0.,wrong_s=0.,
            best_streak_s=0.,first_clean_s=None,observed_s=0.) for i,(a,b,g) in enumerate(windows)]
        streak=np.zeros(2);prev=np.zeros(2,dtype=bool)
        maximum_guitar_distance=0.;maximum_guitar_rotation=0.
        total_ticks=round(times[-1]*60)
        reset_count_before=scene.reset_calls
        for tick in range(total_ticks):
            t=(tick+1)/60.
            requested=qs[min(tick+1,len(qs)-1)]
            req=torch.tensor(requested,device=device,dtype=control.reference.dtype)[control.active]
            desired=initial.clone();desired[:,active]=req[active]
            action=trajectory_actions(desired,control.reference[control.active],control.action_low,control.action_high)
            env.begin_control(action)
            target=control.targets(action,sample)
            for sub in range(4):
                efforts=control.efforts(sample);checks=control.diagnostics
                if not bool((checks['finite']&checks['chest_witness_certified']).all()):
                    raise RuntimeError('Native controller finite/support certificate failed')
                undefined=~checks['chest_normal_defined']
                env.invalidate_control(undefined)
                efforts=torch.where(env.control_invalid[:,None],last_valid,efforts)
                last_valid.copy_(efforts);sample=scene.step(target,efforts)
                now=(tick*4+sub+1)/240.
                previous_candidate=env.candidate[0,:2].cpu().numpy().copy()
                env.substep(sample)
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
                    clean=bool(previous_candidate[goal] and candidate[goal] and not wrong[goal] and alive and in_window)
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
            if env._substeps == 4:
                env.end_control()
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
            row['first_clean_delay_s']=(None if row['first_clean_s'] is None else
                max(0.,float(row['first_clean_s']-row['start_s'])))
            row['onset_compliant']=bool(row['first_clean_delay_s'] is not None and
                row['first_clean_delay_s']<=1/240.+1e-8)
        report=dict(schema=reference['schema'],completed=True,accepted=False,settings=settings,notes=note,failure=failure,
            native_verified=bool(failure is None and all(r['hold_90percent'] for r in note)),
            maximum_guitar_displacement_m=maximum_guitar_distance,maximum_guitar_rotation_rad=maximum_guitar_rotation,
            physics_steps=scene.physics_steps,reset_calls_before_physics=reset_count_before,
            reset_calls_after_physics=scene.reset_calls,no_intermediate_reset=scene.reset_calls==reset_count_before,
            source_unchanged=all(sha(p)==value for p,value in pins.items()),
            policy_valid=bool(failure is None),
            clock_matches_physics=bool(int(env.clock[0])==scene.physics_steps),
            controller_contract=control.contract,scene=scene.diagnostics,
            initial_hover_native_readback=readback[:2],
            source_fk_actual_readback_max_position_m=max(r['position_error_m'] for r in readback),
            source_fk_actual_readback_max_rotation_rad=max(r['rotation_error_rad'] for r in readback),
            limitation='Two held reference targets only; no trained policy, acoustic signal or exact contact pair guarantee.')
        write(out/'source_fk_readback.json',readback)
    except BaseException as error:
        report=dict(schema=reference['schema'],completed=False,accepted=False,
            native_verified=False,error=repr(error),physics_samples=len(fast),
            limitation='Execution failed; this is not evidence of physical infeasibility.',
            source_sha256=dict(reference['source_sha256']))
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
        if report is not None and not report['completed']:
            report.update(scene_destroyed=bool(scene is not None and scene.closed),
                cleanup_error=cleanup_error,
                source_unchanged=all(sha(p)==value for p,value in reference['source_sha256'].items()))
            write(out/'report.json',report)
    if report is not None:
        report['scene_destroyed']=bool(scene is not None and scene.closed)
        report['cleanup_error']=cleanup_error
        report['initial_hover_readback_consistent']=bool(readback and all(r['position_error_m']<=.002 and
            r['rotation_error_rad']<=.05 for r in readback[:2]))
        report['finite_trace']=bool(all(np.isfinite(row['q']).all() and np.isfinite(row['applied_target']).all() for row in fast) and all(np.isfinite(row['body_state']).all() for row in slow))
        report['native_verified']=bool(report['native_verified'] and report['source_unchanged'] and
            report['no_intermediate_reset'] and report['scene_destroyed'] and cleanup_error is None and
            report['initial_hover_readback_consistent'] and report['finite_trace'])
        common=bool(report['source_unchanged'] and report['no_intermediate_reset'] and
            report['scene_destroyed'] and cleanup_error is None and
            report['initial_hover_readback_consistent'] and report['finite_trace'])
        def section_verified(rows):
            safe=report['failure'] is None or report['failure']['time_s']>rows[-1]['end_s']+1e-8
            return bool(common and safe and all(r['onset_compliant'] and r['entire_hold_clean'] and
                r['full_hold_observed'] for r in rows))
        report['AB_on_time_full_hold_verified']=section_verified(note[:2])
        report['accepted']=bool(report['AB_on_time_full_hold_verified'] and report['clock_matches_physics'])
        report['verification_level']='accepted requires AB onset<=one240Hz tick, entire1.5s holds, source/finite/reset/cleanup and physical/wrist safety gates'
        write(out/'report.json',report)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate','--candidates',dest='candidates',type=Path,required=True)
    p.add_argument('--gap',type=float,choices=(.75,),required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--device',default='cuda:0');args=p.parse_args()
    report=run(args.candidates,args.gap,args.out,args.device)
    print(json.dumps(dict(native_verified=report['native_verified'],notes=report['notes']),indent=2))


if __name__=='__main__':main()
