"""Frozen Strike with incremental current-guitar recovery priority over right-arm goals."""
from .underneck_pose_trial_v5 import UnderneckEnvironment, initial_audit, read, save, sha, pose, calibrated_fk
from .environment import ROOT, np
from .run_strike_live_probe import CHECKPOINT, GOAL, GRIP, tensor_plain
from .run_joint_hold import native_state
from .strike_native_view import create_view, refresh_native
from .guitar_relative_readiness_v2 import evaluate_readiness, pick_behind_body
from .strike_preparation_handoff import seed_source_history
from .prepared_strike_start import guitar_in_playable_region
import xml.etree.ElementTree as ET
from .bounded_arm_hold import BoundedArmHold
from .gym_trial_recording import GymTrialRecording
from .native_contacts import read_contacts, body_names, plain
from .underneck_initial_search import FACETS
from scipy.spatial.transform import Rotation
from scipy.optimize import least_squares
from pathlib import Path
import argparse
import traceback
import torch
from tab2body.learning.strike_v2_model import StrikeV2ActorCritic


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--right-rate',type=float,choices=(.8,3.2),default=.8)
    parser.add_argument('--right-gain',type=float,choices=(1.,4.),default=1.)
    parser.add_argument('--prepare-radius',type=float,choices=(.3,.6),default=.3)
    parser.add_argument('--prepare-error-gain',type=float,choices=(0.,.5),default=0.)
    args=parser.parse_args()
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    env=recorder=model=None;failure=None;records=[];trace=[];video={};checks={}
    phase='PREPARE';play_start=None;stop_reason=None;terminal_reasons={}
    try:
        candidate=read(args.candidate);env=UnderneckEnvironment(candidate)
        right_arm_pd=np.array([i for i,n in enumerate(env.names) if n.startswith(('R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))])
        initial_props=env.gym.get_actor_dof_properties(env.env,env.human).copy()
        initial_props['stiffness'][right_arm_pd]*=args.right_gain
        initial_props['damping'][right_arm_pd]*=np.sqrt(args.right_gain)
        if not env.gym.set_actor_dof_properties(env.env,env.human,initial_props):raise RuntimeError('right PD initialization failed')
        audit=initial_audit(env,candidate);save(out/'initial_audit.json',audit)
        state0=native_state(env);props=env.gym.get_actor_dof_properties(env.env,env.human).copy()
        save(out/'initial_values.json',{'candidate_path':str(args.candidate.resolve()),'joint_names':env.names,
            'human_body_names':env.human_bodies,'guitar_body_names':env.guitar_bodies,'native_initial_state':state0,
            'initial_angles_rad':env.initial_q.tolist(),'PD_properties':plain(props),'native_lower_rad':env.lower.tolist(),
            'native_upper_rad':env.upper.tolist(),'self_collision_policy':env.self_collision_policy,'strap_force_enabled':False,'right_policy_rate_rad_s':args.right_rate,'right_arm_PD_scale':args.right_gain})
        recorder=GymTrialRecording(env,out/'images');recorder.capture()
        if not all(audit['checks'].values()) or not audit['source_clear']:raise ValueError('fresh native initial audit failed')
        checkpoint=torch.load(CHECKPOINT,map_location='cpu',weights_only=True);payload=checkpoint['checkpoint_contract']['payload']
        assert sha(GOAL)==payload['inputs']['goal_sha256'] and sha(GRIP)==payload['inputs']['grip_reference_sha256']
        view=create_view(env,checkpoint,str(GOAL),str(GRIP))
        assert list(view.controlled_dof_names)==payload['control']['controlled_dof_names']
        assert list(view.observation_manifest)==payload['config']['observation_manifest']
        model=StrikeV2ActorCritic(303,30,value_dim=1,init_std=payload['model']['policy_init_std'])
        model.load_state_dict(checkpoint['model'],strict=True);model.eval();model.requires_grad_(False)
        frozen={k:v.clone() for k,v in model.state_dict().items()}
        view._reset_task_state(torch.tensor([0]));view.progress_buf.zero_()
        before=native_state(env)
        checks['handoff_target_geometry_exact']=seed_source_history(view,env.target)
        checks['handoff_preflight_readonly']=native_state(env)==before
        expected=view.actions_for_pd_targets(torch.tensor(env.target[view.ctrl_idx.numpy()].copy())[None])
        checks['handoff_preflight_history_exact']=torch.equal(view.prev_action,expected)
        initial_song_time=float(view.song_time_s[0])
        indices=lambda prefixes:np.array([i for i,n in enumerate(env.names) if n.startswith(prefixes)])
        arm=indices(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist','R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))
        left=indices(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist'));right_arm=indices(('R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))
        source_right=view.ctrl_idx.numpy();right_fingers=indices(('RH:',));other=np.setdiff1d(np.arange(81),np.r_[left,right_arm,right_fingers])
        left_in_arm=np.array([j for j,i in enumerate(arm) if i in left]);dummy_right=np.array([j for j,i in enumerate(arm) if i not in left])
        assert (len(left),len(right_arm),len(right_fingers),len(other))==(12,12,21,36)
        hold=BoundedArmHold(env.initial_q[arm],env.lower[arm],env.upper[arm])
        fk,_=calibrated_fk(env.names,env.human_bodies,state0,env.initial_q)
        chest0=pose(state0['human_body_states'][env.human_bodies.index('Chest')])
        lo=np.maximum(env.lower[right_arm],env.initial_q[right_arm]-args.prepare_radius)
        hi=np.minimum(env.upper[right_arm],env.initial_q[right_arm]+args.prepare_radius)
        normal=read(FACETS)['facets']['LH:palm']['normal_local'];names=body_names(env.gym,env.env)
        relative_r=Rotation.from_quat(candidate['preparation']['soft_reference_pick_rotation_G_xyzw'])
        gp0,gr0=pose(state0['guitar_body_states'][0]);play_thorax=None
        chest_z=float(chest0[0][2])
        guitar_xml=ET.parse(ROOT/env.config['guitar_asset']).getroot()
        body_geom=next(b for b in guitar_xml.iter('body') if b.get('name')=='G:body').find('geom')
        assert body_geom.get('type')=='box'
        body_half_thickness=float(body_geom.get('size').split()[2])
        checks.update(target_bounds=True,target_rates=True,held_other36=True,commands_preserve_state=True,
                      ready_residual_bounds=True,root_lower_fixed=True,prepare_clock_frozen=True,prepare_has_no_actor=True,
                      hold_goals_clock_history_frozen=True)
        def sample():
            s=native_state(env);gp,gr=pose(s['guitar_body_states'][0])
            trace.append({'physics_step':env.steps,'time_s':env.steps/240,'phase':phase,'position_W_m':gp.tolist(),
                'quaternion_xyzw':gr.as_quat().tolist(),'position_change_m':float(np.linalg.norm(gp-gp0)),
                'rotation_change_deg':float(np.degrees((gr*gr0.inv()).magnitude())),'native_state':s})
        sample()
        def integrate():
            for _ in range(4):
                env.step_physics()
                s=native_state(env)
                values=[v for row in s['human_dof_states'] for v in (row['pos'],row['vel'])]
                for row in s['human_body_states']+s['guitar_body_states']:
                    for block in (row['pose']['p'],row['pose']['r'],row['vel']['linear'],row['vel']['angular']):values.extend(block.values())
                if not np.isfinite(values).all() or max(abs(r['vel']) for r in s['human_dof_states'])>50:raise ValueError('unsafe native state')
                if env.steps%8==0:
                    sample();recorder.capture()
                    checks['root_lower_fixed'] &= all(s['human_body_states'][i]==state0['human_body_states'][i] for i,n in enumerate(env.human_bodies) if i==0 or any(k in n for k in ('Hip','Knee','Ankle','Toe')))
        def submit(desired):
            before=native_state(env);previous=env.target.copy()
            records[-1]['requested_targets_rad']=np.asarray(desired).tolist()
            rate=np.full(81,.8,dtype=np.float32)
            if phase=='PLAY':rate[source_right]=args.right_rate
            env.target=np.clip(np.clip(desired,previous-rate/60,previous+rate/60),env.lower,env.upper).astype(np.float32)
            env._submit_targets();view.pd_target.copy_(torch.tensor(env.target.copy()))
            view.prev_action.copy_(view.actions_for_pd_targets(view.pd_target[source_right][None]))
            checks['commands_preserve_state'] &= native_state(env)==before
            checks['target_rates'] &= bool(np.all(abs(env.target-previous)<=rate/60+2e-7))
            checks['target_bounds'] &= bool(((env.target>=env.lower)&(env.target<=env.upper)).all())
            checks['held_other36'] &= bool(np.array_equal(env.target[other],env.initial_q[other]))
            records[-1]['final_targets_rad']=env.target.tolist();records[-1]['source_history']=tensor_plain(view.prev_action)
        def left_target(actual):
            measured=actual[arm].copy();measured[dummy_right]=env.initial_q[arm][dummy_right]
            target,_=hold.update(measured,1/60)
            return target[left_in_arm]
        ready_integral=np.zeros(9);adapter_entry_reached=False;adapter_event_key=None
        def advance(task):
            nonlocal ready_integral,adapter_entry_reached,adapter_event_key
            actual=np.array([r['pos'] for r in native_state(env)['human_dof_states']]);desired=env.target.copy()
            desired[left]=left_target(actual);desired[source_right]=tensor_plain(task.pd_target[source_right])
            desired[indices(('R_Thorax',))]=play_thorax
            if int(task.motor_phase[0]) in (0,1,2):
                state=native_state(env);gp,gr=pose(state['guitar_body_states'][0])
                _,cr=pose(state['human_body_states'][env.human_bodies.index('Chest')]);_,rr=chest0
                delta_chest=cr*rr.inv()
                actual_pick_W,_=pose(state['human_body_states'][env.human_bodies.index('RH:pick')])
                base_pick_fk,_=fk(actual)['RH:pick']
                geometry=task._current_target_geometry();source_phase=int(task.motor_phase[0])
                event_key=(int(task.event_index[0]),int(geometry[0][0]),int(task._current_target_direction()[0]))
                if event_key!=adapter_event_key or source_phase!=1:adapter_entry_reached=False
                adapter_event_key=event_key
                pick_G=gr.inv().apply(actual_pick_W-gp)
                entry_G=geometry[4][0].numpy()
                entry_distance=float(np.linalg.norm(pick_G-entry_G))
                if source_phase==1 and entry_distance<=task.entry_distance:adapter_entry_reached=True
                waypoint_index=3 if source_phase==0 else (5 if source_phase==2 or adapter_entry_reached else 4)
                ready_g=geometry[waypoint_index][0].numpy()
                target_W=gp+gr.apply(ready_g)
                controlled_arm=np.array([i for i in right_arm if i in source_right])
                low=np.maximum(env.lower[controlled_arm],actual[controlled_arm]-.15)
                high=np.minimum(env.upper[controlled_arm],actual[controlled_arm]+.15)
                assert np.all(high>low)
                def residual(v):
                    q=actual.copy();q[controlled_arm]=v
                    p,_=fk(q)['RH:pick'];predicted=actual_pick_W+delta_chest.apply(p-base_pick_fk)
                    return np.r_[1000*(predicted-target_W),3*(v-actual[controlled_arm])]
                fit=least_squares(residual,np.clip(actual[controlled_arm],low+1e-8,high-1e-8),bounds=(low,high),max_nfev=12)
                correction=np.clip(fit.x-actual[controlled_arm],-.15,.15)
                policy=desired[controlled_arm].copy()
                if source_phase==2:
                    # Retain the current actuator goal and increment toward the actual
                    # original clearance waypoint; no new policy arm target during recovery.
                    old_integral=ready_integral.copy();blocked=np.zeros(9,dtype=bool)
                    applied_correction=2.0*correction
                    desired[controlled_arm]=np.clip(env.target[controlled_arm]+applied_correction,
                        env.lower[controlled_arm],env.upper[controlled_arm])
                else:
                    old_integral=ready_integral.copy()
                    proposed=np.clip(old_integral+.2*correction,-.3,.3)
                    raw_correction=np.clip(correction+proposed,-.3,.3)
                    raw_goal=(policy+raw_correction).astype(np.float32)
                    bounded_goal=np.clip(raw_goal,env.lower[controlled_arm],env.upper[controlled_arm])
                    preview_rate=np.full(len(controlled_arm),args.right_rate,dtype=np.float32)
                    final_preview=np.clip(np.clip(bounded_goal,env.target[controlled_arm]-preview_rate/60,
                        env.target[controlled_arm]+preview_rate/60),env.lower[controlled_arm],env.upper[controlled_arm]).astype(np.float32)
                    blocked=correction*(raw_goal-final_preview)>1e-12
                    ready_integral=np.where(blocked,old_integral,proposed)
                    applied_correction=np.clip(correction+ready_integral,-.3,.3)
                    desired[controlled_arm]=np.clip(policy+applied_correction,env.lower[controlled_arm],env.upper[controlled_arm])
                records[-1]['phase_target_residual']={'joint_indices':controlled_arm.tolist(),'policy_targets_rad':policy.tolist(),
                    'actual_angles_rad':actual[controlled_arm].tolist(),'correction_rad':correction.tolist(),'fit_success':bool(fit.success),
                    'fit_cost':float(fit.cost),'target_W_m':target_W.tolist(),'target_G_m':ready_g.tolist(),
                    'actual_pick_W_m':actual_pick_W.tolist(),'actual_dofs_rad':actual.tolist(),'base_pick_fk_W_m':base_pick_fk.tolist(),
                    'current_chest_delta_xyzw':delta_chest.as_quat().tolist(),
                    'integral_rad':ready_integral.tolist(),'integral_blocked':blocked.tolist(),'applied_correction_rad':applied_correction.tolist(),
                    'recovery_priority_active':source_phase==2,'recovery_increment_gain':2.0 if source_phase==2 else 0.,
                    'previous_actuator_targets_rad':env.target[controlled_arm].tolist(),'source_motor_phase':source_phase,'adapter_event_key':list(event_key),'adapter_entry_reached':adapter_entry_reached,
                    'native_pick_to_entry_m':entry_distance,'source_entry_distance_m':task.entry_distance,'target_geometry_index':waypoint_index,
                    'scope':'measured pick/current G phase waypoint PI residual; source phase/detector unchanged'}
                checks['ready_residual_bounds'] &= bool(np.isfinite(np.r_[correction,ready_integral,applied_correction]).all() and max(abs(correction))<=.15+1e-12 and max(abs(ready_integral))<=.3+1e-12 and max(abs(applied_correction))<=.3+1e-12)
            submit(desired);integrate()
        view.advance_native=advance
        ready_streak=0
        for tick in range(300):
            refresh_native(view,env);state=native_state(env);gp,gr=pose(state['guitar_body_states'][0])
            _,_,center,ready,*_=view._current_target_geometry()
            actual=np.array([r['pos'] for r in state['human_dof_states']]);grip=view.grip_reference.measure(view.dof_state[:,0][None])
            contacts=read_contacts(env.gym,env.env,names)
            readiness=evaluate_readiness(state,env.human_bodies,env.guitar_bodies,contacts,ready[0].numpy(),center[0].numpy(),normal,bool(grip['grip_success'][0]))
            readiness['prep_target_W_m']=list(readiness['ready_W_m'])
            region_ok=guitar_in_playable_region(gp,gr.as_quat(),chest_z)
            behind,rear_plane=pick_behind_body(state,env.guitar_bodies,readiness['pick_G_m'],body_half_thickness)
            records.append({'guitar_in_playable_region':region_ok,'strict_preparation_met':readiness['ready_now'],
                'pick_behind_guitar_body':behind,'rear_plane_G_z_m':rear_plane,'before_physics_step':env.steps,'time_s':env.steps/240,'phase':phase,'readiness':readiness,
                'contacts':contacts,'song_time_s':float(view.song_time_s[0]),'actor_used':False,
                'grip_pinch_rms_rad':float(grip['grip_pinch_rms_rad'][0]),'grip_free_rms_rad':float(grip['grip_free_rms_rad'][0])})
            eligible=region_ok and readiness['conditions']['finite'] and readiness['conditions']['left_palm_up'] and readiness['conditions']['right_front_side'] and readiness['conditions']['right_grip'] and readiness['pick_to_ready_m']<=.01
            ready_streak=ready_streak+1 if eligible else 0
            records[-1]['native_ready_streak']=ready_streak
            start_conditions=('finite','left_finger_neck_contact','left_palm_up','right_front_side','right_grip','right_noncontact')
            start_ready=region_ok and readiness['pick_to_ready_m']<=.025 and all(readiness['conditions'][k] for k in start_conditions)
            records[-1]['automatic_start_ready']=bool(start_ready)
            if phase=='PREPARE' and start_ready:
                handoff_before=native_state(env)
                checks['handoff_target_geometry_exact'] &= seed_source_history(view,env.target)
                checks['handoff_preflight_readonly'] &= native_state(env)==handoff_before
                phase='PLAY';play_start=env.steps/240
                play_thorax=env.target[indices(('R_Thorax',))].copy()
                records[-1]['handoff']=True;records[-1]['phase']='PLAY'
            elif phase=='PLAY' and behind:
                phase='HOLD';stop_reason='pick_behind_guitar';records[-1]['phase']='HOLD'
            if phase=='PREPARE':
                checks['prepare_clock_frozen'] &= float(view.song_time_s[0])==initial_song_time and int(view.progress_buf[0])==0
                cp,cr=pose(state['human_body_states'][env.human_bodies.index('Chest')]);rp,rr=chest0
                delta=cr*rr.inv();target=gp+gr.apply(ready[0].numpy());target_r=gr*relative_r
                def residual(v):
                    q=actual.copy();q[right_arm]=v;p,r=fk(q)['RH:pick']
                    predicted=cp+delta.apply(p-rp);predicted_r=delta*r
                    return np.r_[1000*(predicted-target),5*(target_r.inv()*predicted_r).as_rotvec(),.2*(v-env.target[right_arm])]
                fit=least_squares(residual,np.clip(env.target[right_arm],lo+1e-8,hi-1e-8),bounds=(lo,hi),max_nfev=12)
                desired=env.initial_q.copy();desired[left]=left_target(actual);desired[right_arm]=np.clip(fit.x+args.prepare_error_gain*(fit.x-actual[right_arm]),lo,hi)
                submit(desired);records[-1]['prep_IK_goal_rad']=fit.x.tolist();records[-1]['prep_IK_actual_error_rad']=(fit.x-actual[right_arm]).tolist();records[-1]['prep_IK_cost']=float(fit.cost);records[-1]['prep_IK_success']=bool(fit.success)
                integrate()
            elif phase=='PLAY':
                obs=view.strict_observation()
                with torch.no_grad():action=model.act(obs,deterministic=True)[0]
                if not torch.isfinite(action).all():raise ValueError('nonfinite actor action')
                records[-1].update(actor_used=True,observation=tensor_plain(obs),action=tensor_plain(action))
                _,reward,done,info=view.step(action)
                records[-1].update(done=bool(done.any()),after_physics_step=env.steps,source_progress=int(view.progress_buf[0]),
                    source_song_time_after_s=float(view.song_time_s[0]),reward=tensor_plain(reward),info={k:tensor_plain(v) for k,v in info.items() if isinstance(v,torch.Tensor)})
                if bool(done.any()):
                    terminal_reasons={k:tensor_plain(v) for k,v in info.items() if isinstance(v,torch.Tensor) and
                        ('termination' in k or k in ('timeout','nonfinite','velocity_blowup','goal_finished'))}
                    phase='HOLD';stop_reason='source_terminal';sample()
            else:
                held=env.target.copy();song=float(view.song_time_s[0]);progress=int(view.progress_buf[0]);history=view.prev_action.clone()
                records[-1]['final_targets_rad']=held.tolist();records[-1]['source_history']=tensor_plain(history)
                integrate()
                checks['hold_goals_clock_history_frozen'] &= bool(np.array_equal(env.target,held) and
                    float(view.song_time_s[0])==song and int(view.progress_buf[0])==progress and torch.equal(view.prev_action,history))
            if env.steps%240==0:print('native seconds',env.steps/240,'phase',phase,'ready',readiness['conditions'],flush=True)
        checks['prepare_has_no_actor']=all(not r['actor_used'] for r in records if r['phase']=='PREPARE')
        checks['source_weights_RMS_frozen']=all(torch.equal(v,frozen[k]) for k,v in model.state_dict().items())
        checks['PD_unchanged']=bool(np.array_equal(props,env.gym.get_actor_dof_properties(env.env,env.human)))
        checks['no_forbidden_calls']=not env.forbidden_calls
        checks['render_readonly']=all(f['render_preserves_states'] for f in recorder.frames)
        save(out/'checkpoint_connection.json',{'checkpoint':str(CHECKPOINT),'official_G0_qualification':False,
            'model_obs_dim':303,'model_action_dim':30,'diagnostic_start_after_s':0,'time_wait_gate_used':False,
            'diagnostic_ready_distance_m':.025,'native_ready_hold_frames_gate':False,'source_ready_distance_m':.01,'source_ready_hold_frames':6,'prepare_stand_off_m':0.,'prepare_radius_rad':args.prepare_radius,'prepare_error_gain':args.prepare_error_gain,'strict_contact_gate_used':False,'playable_upper_z_m':chest_z,'right_policy_rate_rad_s':args.right_rate,'right_arm_PD_scale':args.right_gain,'actuator_difference':'native implicitPD/rate cap vs source explicit stiffness torque',
            'prepared_source_handoff_preflight':checks['handoff_preflight_history_exact'],'learning_updates':0,'ready_proportional_max_rad':.15,'ready_integral_max_rad':.3,'ready_combined_max_rad':.3,'ready_integral_step_gain':.2,'integral_update_source_phases':[0,1],'phase_target_geometry':'READY ready, APPROACH entry then exit after measured entry, RECOVER original exit/clearance','source_phase_or_detector_override':False,'recovery_arm_owner':'adapter incremental position targets; frozen policy still owns fingers','recovery_increment_gain':2.0})
    except BaseException as exc:
        failure={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()};print(failure['traceback'],flush=True)
    finally:
        if env:env.close()
        if recorder and len(recorder.frames)>1:video=recorder.encode()
        save(out/'controls.json',records);save(out/'trace.json',trace)
        save(out/'report.json',{'failure':failure,'checks':checks,'physics_steps':env.steps if env else 0,'phase_end':phase,
            'play_start_time_s':play_start,'stop_reason':stop_reason,'terminal_reasons':terminal_reasons,
            'diagnostic_only':True,'strict_contact_gate_used':False,'actor_steps':sum(r['actor_used'] for r in records),
            'completed_5s':bool(env and env.steps==1200 and failure is None and all(checks.values())),
            'frame_count':len(recorder.frames) if recorder else 0,'videos':video,'music_success':False,'learning_updates':0,'ready_proportional_max_rad':.15,'ready_integral_max_rad':.3,'ready_combined_max_rad':.3,'ready_integral_step_gain':.2,'integral_update_source_phases':[0,1],'phase_target_geometry':'READY ready, APPROACH entry then exit after measured entry, RECOVER original exit/clearance','source_phase_or_detector_override':False,'recovery_arm_owner':'adapter incremental position targets; frozen policy still owns fingers','recovery_increment_gain':2.0})
    if failure or not all(checks.values()):raise RuntimeError(failure or checks)


if __name__=='__main__':main()
