"""Frozen Fret fingers, prepared arm targets and inherited passive strap on free guitar."""
from .underneck_pose_trial_v5 import initial_audit, read, save, sha, pose
from .environment import ROOT, np
from .run_joint_hold import native_state
from .fret_native_view_v2 import create_fret_view
from .strike_native_view import refresh_native
from .bounded_arm_hold import BoundedArmHold
from .fret_finger_target_ownership import compose_finger_play_targets
from .underneck_strap_environment import UnderneckStrapEnvironment
from .strap_trial_recording import StrapTrialRecording
from .underneck_initial_search import BASE
BASELINE_INITIAL = ROOT / "docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/native/data/initial_values.json"
from .native_contacts import read_contacts, body_names, plain
from pathlib import Path
import argparse
import traceback
import torch
from tab2body.learning.fret_v2_model import FretV2ActorCritic
from tab2body.tools.fret_rollout_contract import verify_rollout_model

CHECKPOINT = ROOT/'fret/training/runs/20260911_1710_02_Jazz1-200-B_solo/checkpoints/fret_035000.pt'
GOAL = ROOT/'data/song_bundles/02_Jazz1-200-B_solo/training/fret_training.json'
HAND_TARGETS = ROOT/'data/song_bundles/02_Jazz1-200-B_solo/training/hand_position_targets.json'


def json_plain(value):
    if isinstance(value,torch.Tensor):return value.detach().cpu().tolist()
    if isinstance(value,dict):return {k:json_plain(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)):return [json_plain(v) for v in value]
    return plain(value)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--candidate',type=Path,required=True)
    args=parser.parse_args(); out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    env=recorder=view=model=None; records=[];trace=[];checks={};failure=None;video={}
    phase='PREPARE';stop_reason=None;terminal_info={};play_start=None;prepared_left=None
    try:
        candidate=read(args.candidate);env=UnderneckStrapEnvironment(candidate)
        audit=initial_audit(env,candidate);save(out/'initial_audit.json',audit)
        if not all(audit['checks'].values()) or not audit['source_clear']:raise ValueError('native initial audit failed')
        state0=native_state(env);gp0,gr0=pose(state0['guitar_body_states'][0])
        assert state0 == read(BASELINE_INITIAL)['native_initial_state'], 'strap ON changed t=0 state'
        recorder=StrapTrialRecording(env,out/'images');recorder.capture()
        checkpoint=torch.load(CHECKPOINT,map_location='cpu',weights_only=True)
        if sha(CHECKPOINT)!='a6f0c303f69686eb02ebed5f7dce743fdc223fd89c8a8fb2b40303d0abeab5ca':raise ValueError('checkpoint changed')
        before=native_state(env);view,payload=create_fret_view(env,checkpoint,GOAL,HAND_TARGETS)
        model=FretV2ActorCritic(420,30,value_dim=6,init_std=payload['model']['policy_init_std'])
        verify_rollout_model(view,model,payload)
        model.load_state_dict(checkpoint['model'],strict=True);model.eval();model.requires_grad_(False)
        frozen={k:v.clone() for k,v in model.state_dict().items()}
        policy=view.ctrl_idx.numpy(); arm=np.array([i for i,n in enumerate(env.names) if n.startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist','R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))])
        fingers=np.array([i for i,n in enumerate(env.names) if n.startswith('LH:')])
        left_arm=np.array([i for i in policy if i not in fingers])
        support=np.array([i for i in arm if i not in policy]);other=np.setdiff1d(np.arange(len(env.names)),np.r_[policy,support])
        assert (len(fingers),len(left_arm),len(support),len(other))==(21,9,15,36)
        assert len(set(np.r_[fingers,left_arm,support,other]))==len(env.names)==81
        hold=BoundedArmHold(env.initial_q[arm],env.lower[arm],env.upper[arm])
        checks.update(constructor_readonly=native_state(env)==before,contract_verified=True,
            single_target_owner=True,target_rates=True,target_bounds=True,held_other36=True,
            commands_preserve_states=True,prepare_no_actor=True,prepare_clock_frozen=True,
            root_lower_fixed=True,frozen_actor=True,source_terminal_stops_actor=True,prepared_left9_target_held=True,finger21_source_requests_exact=True)
        save(out/'initial_values.json',{'candidate_path':str(args.candidate.resolve()),'checkpoint_path':str(CHECKPOINT),
            'checkpoint_sha256':sha(CHECKPOINT),'goal_path':str(GOAL),'hand_targets_path':str(HAND_TARGETS),
            'joint_names':env.names,'native_initial_state':state0,'initial_angles_rad':env.initial_q.tolist(),
            'native_lower_rad':env.lower.tolist(),'native_upper_rad':env.upper.tolist(),
            'source_lower_rad':view.dof_lower.tolist(),'source_upper_rad':view.dof_upper.tolist(),
            'source_profile_audit':view.human_hard_limit_audit,'native_hard_limit_mode':'authored XML; source profile targets only',
            'self_collision_policy':env.self_collision_policy,'strap_enabled':True,'strap_rest_length_m':env.rest_length,'initial_route_length_m':env.initial_route_length,
            'strap_law_parameters':env.config['strap'],'strap_rest_length_source':str(BASE),'human_body_names':env.human_bodies,
            'control_owners':{'Fret21':[env.names[i] for i in fingers], 'prepared_left9':[env.names[i] for i in left_arm], 'bounded_hold15':[env.names[i] for i in support],
                'initial_hold36':[env.names[i] for i in other]},'minimum_preparation_s':2.,
            'left_arm_policy_requests_applied':False,'left_arm_hold_mode':'last submitted target at t=2; actual state remains free',
            'source_preparation_frames_replaced':view.preparation_frames,'source_goal_frames':view.goals.n_frames,
            'checkpoint_asset_changes':[e['path'] for e in payload['fingerprints']['asset']['manifest']
                if not (ROOT/'tab2body'/e['path']).is_file() or sha(ROOT/'tab2body'/e['path'])!=e['sha256']],
            'checkpoint_implementation_changes':[e['path'] for e in payload['fingerprints']['implementation']['manifest']
                if not (ROOT/'tab2body'/e['path']).is_file() or sha(ROOT/'tab2body'/e['path'])!=e['sha256']]})
        names=body_names(env.gym,env.env)
        def sample():
            s=native_state(env);gp,gr=pose(s['guitar_body_states'][0])
            trace.append({'physics_step':env.steps,'time_s':env.steps/240,'phase':phase,
                'position_W_m':gp.tolist(),'quaternion_xyzw':gr.as_quat().tolist(),
                'position_change_m':float(np.linalg.norm(gp-gp0)),
                'rotation_change_deg':float(np.degrees((gr*gr0.inv()).magnitude())),'native_state':s})
        sample()
        checks['initial_state_exact_baseline']=True
        def integrate():
            for _ in range(4):
                env.step_physics();s=native_state(env)
                values=[v for row in s['human_dof_states'] for v in (row['pos'],row['vel'])]
                for row in s['human_body_states']+s['guitar_body_states']:
                    for block in (row['pose']['p'],row['pose']['r'],row['vel']['linear'],row['vel']['angular']):values.extend(block.values())
                if not np.isfinite(values).all() or max(abs(r['vel']) for r in s['human_dof_states'])>50:raise ValueError('unsafe native state')
                checks['root_lower_fixed'] &= all(s['human_body_states'][i]==state0['human_body_states'][i] for i,n in enumerate(env.human_bodies) if i==0 or any(k in n for k in ('Hip','Knee','Ankle','Toe')))
                if env.steps%8==0:sample();recorder.capture()
        for tick in range(120+int(view.max_episode_length)+1):
            time=env.steps/240; refresh_native(view,env)
            actual=view.dof_state[:,0].numpy().copy()
            held,hold_record=hold.update(actual[arm],1/60)
            desired=env.initial_q.copy()
            if tick<120:
                desired[arm]=held
                desired[policy]=np.clip(desired[policy],view.ctrl_lo.numpy()[0],view.ctrl_hi.numpy()[0])
            else:
                if phase=='PREPARE':
                    phase='PLAY';play_start=time;prepared_left=env.target[left_arm].copy()
                    save(out/'handoff_values.json',{'time_s':time,'left_arm_names':[env.names[i] for i in left_arm],
                        'prepared_left_targets_rad':prepared_left.tolist(),'native_state':native_state(env)})
                    view.preparation_remaining.zero_();view.progress_buf.zero_()
                    view.prev_action.copy_(view.actions_for_pd_targets(torch.tensor(env.target[policy])[None]))
                    checks['handoff_history_exact']=torch.equal(view.prev_action,view.actions_for_pd_targets(torch.tensor(env.target[policy])[None]))
                    checks['two_second_handoff']=time==2.
                observation=view.strict_observation()
                with torch.no_grad():actor_action=model.act(observation,deterministic=True)[0]
                if not torch.isfinite(actor_action).all():raise ValueError('nonfinite Fret action')
                view.cache_policy_actions(actor_action)
                source_requested=view.pd_target.numpy()[policy].copy()
                desired=compose_finger_play_targets(env.initial_q,source_requested,held,policy,fingers,left_arm,support,arm,prepared_left)
                checks['finger21_source_requests_exact'] &= np.array_equal(desired[fingers],source_requested[[j for j,i in enumerate(policy) if i in fingers]])
            before=native_state(env);previous=env.target.copy()
            rate=np.full(len(env.names),.8,dtype=np.float32)
            if phase=='PLAY':rate[fingers]=3.2
            env.target=np.clip(np.clip(desired,previous-rate/60,previous+rate/60),env.lower,env.upper).astype(np.float32)
            env._submit_targets();view.pd_target.copy_(torch.tensor(env.target.copy()))
            view.prev_action.copy_(view.actions_for_pd_targets(view.pd_target[policy][None]))
            checks['commands_preserve_states'] &= native_state(env)==before
            if phase=='PLAY':checks['prepared_left9_target_held'] &= np.array_equal(env.target[left_arm],prepared_left)
            checks['held_other36'] &= bool(np.array_equal(env.target[other],env.initial_q[other]))
            checks['target_rates'] &= bool(np.all(abs(env.target-previous)<=rate/60+2e-7))
            checks['target_bounds'] &= bool(np.all((env.target>=env.lower)&(env.target<=env.upper)))
            row={'time_s':time,'phase':phase,'actor_used':phase=='PLAY','requested_targets_rad':desired.tolist(),
                'submitted_targets_rad':env.target.tolist(),'source_frame_before':view.goals.frame_idx.tolist(),
                'actual_profile_excess_rad':np.maximum(np.maximum(view.ctrl_lo.numpy()[0]-actual[policy],actual[policy]-view.ctrl_hi.numpy()[0]),0).tolist(),
                'hold_diagnostic':hold_record,'native_contacts':read_contacts(env.gym,env.env,names)}
            if phase=='PLAY':row.update(observation=observation.tolist(),actor_action=actor_action.tolist(),executed_history=view.prev_action.tolist(),source_requested_policy_targets_rad=source_requested.tolist())
            records.append(row);integrate();refresh_native(view,env)
            if phase=='PLAY':
                view.progress_buf+=1
                obs,reward,done,info=view.evaluate_after_physics()
                row.update(reward=reward.tolist(),source_info=json_plain(info),source_done=done.tolist())
                if bool(done[0]):
                    terminal_info=json_plain(info);stop_reason='source_terminal';phase='TERMINATED';break
            else:
                checks['prepare_clock_frozen'] &= int(view.goals.frame_idx[0])==0 and int(view.progress_buf[0])==0
        if stop_reason is None:raise RuntimeError('recording budget exhausted before source done')
        if trace[-1]['physics_step']!=env.steps:sample();recorder.capture()
        checks['frozen_actor']=all(torch.equal(v,frozen[k]) for k,v in model.state_dict().items())
        checks['no_forbidden_writes']=not env.forbidden_calls
        save(out/'terminal_info.json',terminal_info)
    except BaseException as exc:
        failure={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()};print(failure['traceback'],flush=True)
    finally:
        if env and recorder and trace and trace[-1]['physics_step']!=env.steps:
            try:sample();recorder.capture()
            except BaseException:pass
        save(out/'controls.json',records);save(out/'trace.json',trace)
        if env:
            save(out/'strap_forces.json',env.strap_records)
            checks.update({'strap_'+k:v for k,v in env.strap_checks.items()})
            checks['strap_once_per_physics_step']=len(env.strap_records)==env.steps
            checks['strap_inherited_fixed_length']=env.rest_length==read(BASE)['input_trial']['initial_settings']['strap_rest_length_m']
        errors=[]
        try:
            if env:env.close()
        except BaseException as exc:errors.append({'stage':'close','message':str(exc)})
        try:
            if recorder and len(recorder.frames)>1:video=recorder.encode()
        except BaseException as exc:errors.append({'stage':'encode','message':str(exc)})
        if errors and failure is None:failure={'type':'FinalizationError','errors':errors}
        save(out/'report.json',{'failure':failure,'checks':checks,'phase_end':phase,'stop_reason':stop_reason,
            'play_start_time_s':play_start,'actor_steps':sum(r['actor_used'] for r in records),
            'physics_steps':env.steps if env else 0,'recorded_physics_duration_s':env.steps/240 if env else 0,
            'frame_count':len(recorder.frames) if recorder else 0,'videos':video,'finalization_errors':errors,
            'completed_recording':failure is None and bool(checks) and all(checks.values()) and stop_reason=='source_terminal',
            'strap_enabled':True,'strap_rest_length_m':env.rest_length if env else None,
            'learning_updates':0,'Strike_actor_enabled':False,'music_success':False})
    if failure or not all(checks.values()):raise RuntimeError(failure or checks)


if __name__=='__main__':main()
