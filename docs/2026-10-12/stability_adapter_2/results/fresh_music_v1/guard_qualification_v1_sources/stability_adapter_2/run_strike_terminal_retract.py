"""Frozen finger policy/current-guitar incremental arm, with native terminal retraction."""
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
from tab2body.env.strike_events import strike_timed_approach_open


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--right-rate',type=float,choices=(.8,3.2),default=.8)
    parser.add_argument('--right-gain',type=float,choices=(1.,),default=1.)
    parser.add_argument('--prepare-radius',type=float,choices=(.3,.6),default=.3)
    parser.add_argument('--prepare-error-gain',type=float,choices=(0.,.5),default=0.)
    args=parser.parse_args()
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    env=recorder=model=None;failure=None;records=[];trace=[];video={};checks={}
    phase='PREPARE';play_start=None;pd_switch_time=None;pd_switch_records=[];stop_reason=None;terminal_reasons={}
    hold_frozen_goals=None;hold_target_G=None;hold_PD_restored=False
    try:
        candidate=read(args.candidate);env=UnderneckEnvironment(candidate)
        right_arm_pd=np.array([i for i,n in enumerate(env.names) if n.startswith(('R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))])
        initial_props=env.gym.get_actor_dof_properties(env.env,env.human).copy()
        initial_props['stiffness'][right_arm_pd]*=args.right_gain
        initial_props['damping'][right_arm_pd]*=np.sqrt(args.right_gain)
        if not env.gym.set_actor_dof_properties(env.env,env.human,initial_props):raise RuntimeError('right PD initialization failed')
        audit=initial_audit(env,candidate);save(out/'initial_audit.json',audit)
        state0=native_state(env);props=env.gym.get_actor_dof_properties(env.env,env.human).copy()
        expected_props=props.copy()
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
        source_right=view.ctrl_idx.numpy();right_fingers=indices(('RH:',));curl_joints=np.array([env.names.index(n) for n in ('RH:middle2','RH:middle3','RH:ring2','RH:ring3')]);pinch_joints=np.array([env.names.index(n) for n in read(GRIP)['groups']['pinch']]);other=np.setdiff1d(np.arange(81),np.r_[left,right_arm,right_fingers])
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
                      ready_residual_bounds=True,velocity_feedback_finite_and_bounded=True,pinch9_requested_policy_exact=True,free4_requested_residual_exact=True,PD_expected_prepare=True,PD_expected_schedule=True,approach_PD_native_readback_exact=True,PD_set_preserves_state=True,adapter_exit_respects_source_time=True,adapter_entry_respects_source_time=True,root_lower_fixed=True,prepare_clock_frozen=True,prepare_has_no_actor=True,
                      hold_clock_history_frozen=True,hold_other72_goals_frozen=True,hold_target_finite_and_bounds=True)
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
        def submit(desired,update_source_history=True):
            before=native_state(env);previous=env.target.copy()
            records[-1]['requested_targets_rad']=np.asarray(desired).tolist()
            rate=np.full(81,.8,dtype=np.float32)
            if phase in ('PLAY','HOLD'):rate[source_right]=args.right_rate
            env.target=np.clip(np.clip(desired,previous-rate/60,previous+rate/60),env.lower,env.upper).astype(np.float32)
            env._submit_targets();view.pd_target.copy_(torch.tensor(env.target.copy()))
            if update_source_history:view.prev_action.copy_(view.actions_for_pd_targets(view.pd_target[source_right][None]))
            checks['commands_preserve_state'] &= native_state(env)==before
            checks['target_rates'] &= bool(np.all(abs(env.target-previous)<=rate/60+2e-7))
            checks['target_bounds'] &= bool(((env.target>=env.lower)&(env.target<=env.upper)).all())
            checks['held_other36'] &= bool(np.array_equal(env.target[other],env.initial_q[other]))
            records[-1]['final_targets_rad']=env.target.tolist();records[-1]['source_history']=tensor_plain(view.prev_action)
        def left_target(actual):
            measured=actual[arm].copy();measured[dummy_right]=env.initial_q[arm][dummy_right]
            target,_=hold.update(measured,1/60)
            return target[left_in_arm]
        ready_integral=np.zeros(9);adapter_entry_reached=False;adapter_event_key=None;previous_pick_G=None;previous_pick_time=None
        def advance(task):
            nonlocal ready_integral,adapter_entry_reached,adapter_event_key,pd_switch_time,previous_pick_G,previous_pick_time
            source_pd_phase=int(task.motor_phase[0])
            play_arm=np.array([i for i in right_arm if i in source_right]);assert len(play_arm)==9
            requested_props=props.copy()
            if source_pd_phase==1:requested_props['damping'][play_arm]*=.25
            if not np.array_equal(expected_props,requested_props):
                switch_before=native_state(env)
                if not env.gym.set_actor_dof_properties(env.env,env.human,requested_props):raise RuntimeError('phase damping submission failed')
                readback=env.gym.get_actor_dof_properties(env.env,env.human).copy()
                checks['approach_PD_native_readback_exact'] &= bool(np.array_equal(requested_props,readback))
                checks['PD_set_preserves_state'] &= native_state(env)==switch_before
                if not checks['approach_PD_native_readback_exact'] or not checks['PD_set_preserves_state']:raise ValueError('phase PD switch audit failed')
                expected_props[:]=requested_props
                if source_pd_phase==1 and pd_switch_time is None:pd_switch_time=env.steps/240
                pd_switch_records.append({'before_physics_step':env.steps,'time_s':env.steps/240,'source_motor_phase':source_pd_phase,
                    'joint_indices':play_arm.tolist(),'joint_names':[env.names[i] for i in play_arm],
                    'damping_scale':.25 if source_pd_phase==1 else 1.,'initial_PD_properties':plain(props),'requested_PD_properties':plain(requested_props),
                    'native_PD_properties':plain(readback),'state_preserved':native_state(env)==switch_before,
                    'scope':'POSITION R9 damping .25 only source APPROACH; baseline READY/RECOVER; no EFFORT command'})
                save(out/'PD_phase_properties.json',pd_switch_records)
            checks['PD_expected_schedule'] &= bool(np.array_equal(requested_props,env.gym.get_actor_dof_properties(env.env,env.human)))
            actual=np.array([r['pos'] for r in native_state(env)['human_dof_states']]);desired=env.target.copy()
            desired[left]=left_target(actual);desired[source_right]=tensor_plain(task.pd_target[source_right])
            source_finger_targets=desired[right_fingers].copy();source_pinch_targets=desired[pinch_joints].copy();source_curl_targets=desired[curl_joints].copy()
            desired[curl_joints]+=.2
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
                mask=task._current_target_masks();offsets=task._current_target_offsets()
                first_offset=torch.where(mask,offsets,torch.full_like(offsets,float('inf'))).amin(dim=1)
                timing=strike_timed_approach_open(task.song_time_s,task._effective_target_time(),first_offset,task.approach_lead_s)
                approach_open=bool(timing['approach_open'][0].item())
                adapter_exit_active=source_phase==1 and adapter_entry_reached and approach_open
                waypoint_index=3 if source_phase==0 or (source_phase==1 and not approach_open) else (5 if source_phase==2 or adapter_exit_active else 4)
                checks['adapter_exit_respects_source_time'] &= not adapter_exit_active or approach_open
                checks['adapter_entry_respects_source_time'] &= source_phase!=1 or approach_open or waypoint_index==3
                source_waypoint_G=geometry[waypoint_index][0].numpy().copy()
                measured_time=env.steps/240
                velocity_G=np.zeros(3) if previous_pick_G is None else (pick_G-previous_pick_G)/(measured_time-previous_pick_time)
                previous_pick_G=pick_G.copy();previous_pick_time=measured_time
                velocity_feedback_active=source_phase in (0,2) or (source_phase==1 and not approach_open)
                velocity_feedback_G=-.1*velocity_G if velocity_feedback_active else np.zeros(3)
                feedback_norm=float(np.linalg.norm(velocity_feedback_G))
                if feedback_norm>.005:velocity_feedback_G*=.005/feedback_norm
                ready_g=source_waypoint_G+velocity_feedback_G
                target_W=gp+gr.apply(ready_g)
                checks['velocity_feedback_finite_and_bounded'] &= bool(np.isfinite(np.r_[velocity_G,velocity_feedback_G,ready_g]).all() and np.linalg.norm(velocity_feedback_G)<=.005+1e-12)
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
                waiting_priority=source_phase==1 and not approach_open
                ready_priority=source_phase==0 or waiting_priority
                # Arm9 uses measured current-guitar geometry in every source phase.
                # Frozen policy arm requests are logged; policy finger requests remain active.
                blocked=np.zeros(9,dtype=bool)
                applied_correction=2.0*correction
                base_goal=env.target[controlled_arm]
                desired[controlled_arm]=np.clip(base_goal+applied_correction,
                    env.lower[controlled_arm],env.upper[controlled_arm])
                records[-1]['phase_target_residual']={'joint_indices':controlled_arm.tolist(),'policy_targets_rad':policy.tolist(),
                    'actual_angles_rad':actual[controlled_arm].tolist(),'correction_rad':correction.tolist(),'fit_success':bool(fit.success),
                    'fit_cost':float(fit.cost),'target_W_m':target_W.tolist(),'target_G_m':ready_g.tolist(),
                    'source_waypoint_G_m':source_waypoint_G.tolist(),'measured_pick_G_m':pick_G.tolist(),'measured_pick_time_s':measured_time,
                    'measured_pick_velocity_G_m_s':velocity_G.tolist(),'velocity_feedback_G_m':velocity_feedback_G.tolist(),'velocity_feedback_active':velocity_feedback_active,
                    'actual_pick_W_m':actual_pick_W.tolist(),'actual_dofs_rad':actual.tolist(),'base_pick_fk_W_m':base_pick_fk.tolist(),
                    'current_chest_delta_xyzw':delta_chest.as_quat().tolist(),
                    'integral_rad':ready_integral.tolist(),'integral_blocked':blocked.tolist(),'applied_correction_rad':applied_correction.tolist(),
                    'geometry_arm_priority_active':True,'open_approach_increment_gain':2.0 if source_phase==1 and approach_open else 0.,'recovery_priority_active':source_phase==2,'waiting_priority_active':waiting_priority,'ready_priority_active':ready_priority,'ready_increment_gain':2.0 if ready_priority else 0.,'waiting_increment_gain':2.0 if waiting_priority else 0.,'waiting_goal_base_rad':env.target[controlled_arm].tolist() if waiting_priority else None,'recovery_increment_gain':2.0 if source_phase==2 else 0.,
                    'previous_actuator_targets_rad':env.target[controlled_arm].tolist(),'source_motor_phase':source_phase,'adapter_event_key':list(event_key),'adapter_entry_reached':adapter_entry_reached,
                    'adapter_approach_open':approach_open,'adapter_exit_active':adapter_exit_active,'source_approach_lead_s':float(task.approach_lead_s),
                    'source_song_time_at_command_s':float(task.song_time_s[0]),'source_effective_target_time_s':float(task._effective_target_time()[0]),'source_first_offset_s':float(first_offset[0]),
                    'native_pick_to_entry_m':entry_distance,'source_entry_distance_m':task.entry_distance,'target_geometry_index':waypoint_index,
                    'scope':'nominal source waypoint plus bounded measured G-frame finite-difference velocity damping for READY/closed APPROACH/RECOVER; source geometry/phase/detector unchanged'}
                checks['ready_residual_bounds'] &= bool(np.isfinite(np.r_[correction,ready_integral,applied_correction]).all() and max(abs(correction))<=.15+1e-12 and max(abs(ready_integral))<=.3+1e-12 and max(abs(applied_correction))<=.3+1e-12)
            checks['pinch9_requested_policy_exact'] &= bool(np.array_equal(desired[pinch_joints],source_pinch_targets))
            checks['free4_requested_residual_exact'] &= bool(np.allclose(desired[curl_joints]-source_curl_targets,.2,atol=2e-7,rtol=0))
            records[-1]['free_finger_curl']={'joint_indices':curl_joints.tolist(),'source_finger_joint_indices':right_fingers.tolist(),
                'source_finger_targets_rad':source_finger_targets.tolist(),'requested_curl_goals_rad':desired[curl_joints].tolist(),
                'nominal_additive_residual_rad':.2,'pinch_requested_policy_exact':bool(np.array_equal(desired[pinch_joints],source_pinch_targets))}
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
                checks['PD_expected_prepare'] &= bool(np.array_equal(props,env.gym.get_actor_dof_properties(env.env,env.human)))
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
                song=float(view.song_time_s[0]);progress=int(view.progress_buf[0]);history=view.prev_action.clone()
                controlled_arm=np.array([i for i in right_arm if i in source_right])
                outside=np.setdiff1d(np.arange(81),controlled_arm)
                if hold_frozen_goals is None:hold_frozen_goals=env.target.copy()
                if not hold_PD_restored:
                    pd_before=native_state(env)
                    if not env.gym.set_actor_dof_properties(env.env,env.human,props):raise RuntimeError('terminal baseline PD restoration failed')
                    terminal_readback=env.gym.get_actor_dof_properties(env.env,env.human).copy()
                    restored_state_exact=native_state(env)==pd_before
                    restored_props_exact=bool(np.array_equal(terminal_readback,props))
                    checks['PD_set_preserves_state'] &= restored_state_exact
                    checks['PD_expected_schedule'] &= restored_props_exact
                    if not restored_state_exact or not restored_props_exact:raise RuntimeError('terminal PD restoration native state/readback mismatch')
                    expected_props[:]=props
                    pd_switch_records.append({'physics_step':env.steps,'time_s':env.steps/240,'source_motor_phase':int(view.motor_phase[0]),
                        'trigger':'terminal_retraction','damping_scale':1.,'native_readback_properties':plain(terminal_readback)})
                    save(out/'PD_phase_properties.json',pd_switch_records)
                    hold_PD_restored=True
                actual_pick_W,_=pose(state['human_body_states'][env.human_bodies.index('RH:pick')])
                pick_G=gr.inv().apply(actual_pick_W-gp)
                if hold_target_G is None:
                    hold_target_G=pick_G.copy();hold_target_G[2]=max(float(pick_G[2]),float(ready[0,2]))+.03
                measured_time=env.steps/240
                velocity_G=np.zeros(3) if previous_pick_G is None else (pick_G-previous_pick_G)/(measured_time-previous_pick_time)
                previous_pick_G=pick_G.copy();previous_pick_time=measured_time
                feedback=-.1*velocity_G;feedback_norm=float(np.linalg.norm(feedback))
                if feedback_norm>.005:feedback*=.005/feedback_norm
                servo_G=hold_target_G+feedback;target_W=gp+gr.apply(servo_G)
                cp,cr=pose(state['human_body_states'][env.human_bodies.index('Chest')]);rp,rr=chest0;delta_chest=cr*rr.inv()
                base_pick_fk,_=fk(actual)['RH:pick']
                low=np.maximum(env.lower[controlled_arm],actual[controlled_arm]-.15)
                high=np.minimum(env.upper[controlled_arm],actual[controlled_arm]+.15)
                def hold_residual(v):
                    q=actual.copy();q[controlled_arm]=v;p,_=fk(q)['RH:pick']
                    return np.r_[1000*(actual_pick_W+delta_chest.apply(p-base_pick_fk)-target_W),3*(v-actual[controlled_arm])]
                fit=least_squares(hold_residual,np.clip(actual[controlled_arm],low+1e-8,high-1e-8),bounds=(low,high),max_nfev=12)
                correction=np.clip(fit.x-actual[controlled_arm],-.15,.15)
                desired=hold_frozen_goals.copy();previous_goal=env.target[controlled_arm].copy()
                desired[controlled_arm]=np.clip(previous_goal+2*correction,env.lower[controlled_arm],env.upper[controlled_arm])
                records[-1]['terminal_retraction']={'joint_indices':controlled_arm.tolist(),'anchor_G_m':hold_target_G.tolist(),
                    'servo_G_m':servo_G.tolist(),'measured_pick_G_m':pick_G.tolist(),'measured_pick_time_s':measured_time,
                    'measured_pick_velocity_G_m_s':velocity_G.tolist(),'feedback_G_m':feedback.tolist(),
                    'previous_actuator_targets_rad':previous_goal.tolist(),'correction_rad':correction.tolist(),
                    'target_W_m':target_W.tolist(),'actual_pick_W_m':actual_pick_W.tolist(),'actual_dofs_rad':actual.tolist(),
                    'fit_success':bool(fit.success),'fit_cost':float(fit.cost),'scope':'human arm9 bounded retraction; fingers/other72 goals and source clock/history frozen; no guitar state or force write'}
                checks['hold_target_finite_and_bounds'] &= bool(np.isfinite(np.r_[hold_target_G,velocity_G,feedback,correction]).all() and
                    np.linalg.norm(feedback)<=.005+1e-12 and max(abs(correction))<=.15+1e-12)
                submit(desired,update_source_history=False);integrate()
                checks['hold_other72_goals_frozen'] &= bool(np.array_equal(env.target[outside],hold_frozen_goals[outside]))
                checks['hold_clock_history_frozen'] &= bool(float(view.song_time_s[0])==song and int(view.progress_buf[0])==progress and torch.equal(view.prev_action,history))
            if env.steps%240==0:print('native seconds',env.steps/240,'phase',phase,'ready',readiness['conditions'],flush=True)
        checks['prepare_has_no_actor']=all(not r['actor_used'] for r in records if r['phase']=='PREPARE')
        checks['source_weights_RMS_frozen']=all(torch.equal(v,frozen[k]) for k,v in model.state_dict().items())
        checks['PD_expected_schedule'] &= bool(np.array_equal(expected_props,env.gym.get_actor_dof_properties(env.env,env.human)))
        checks['no_forbidden_calls']=not env.forbidden_calls
        checks['render_readonly']=all(f['render_preserves_states'] for f in recorder.frames)
        save(out/'checkpoint_connection.json',{'checkpoint':str(CHECKPOINT),'official_G0_qualification':False,
            'model_obs_dim':303,'model_action_dim':30,'diagnostic_start_after_s':0,'time_wait_gate_used':False,
            'diagnostic_ready_distance_m':.025,'native_ready_hold_frames_gate':False,'source_ready_distance_m':.01,'source_ready_hold_frames':6,'prepare_stand_off_m':0.,'prepare_radius_rad':args.prepare_radius,'prepare_error_gain':args.prepare_error_gain,'strict_contact_gate_used':False,'playable_upper_z_m':chest_z,'right_policy_rate_rad_s':args.right_rate,'right_arm_PD_scale':args.right_gain,'free_finger_residual_rad':.2,'free_finger_residual_joint_names':[env.names[i] for i in curl_joints],'pinch_policy_requested_targets_unchanged':True,'actuator_difference':'native implicitPD/rate cap vs source explicit stiffness torque',
            'prepared_source_handoff_preflight':checks['handoff_preflight_history_exact'],'learning_updates':0,'ready_proportional_max_rad':.15,'ready_integral_max_rad':.3,'ready_combined_max_rad':.3,'ready_integral_step_gain':.2,'integral_update_source_phases':[],'integral_update_gate':'held in all source phases; no PI update','approach_arm_owner':'adapter previous actuator target plus 2*current-guitar local IK correction; source arm9 requests logged only','policy_arm_requested_targets_used':False,'ready_arm_owner':'adapter previous actuator target plus 2*local IK correction during phase0 and closedphase1','ready_increment_gain':2.0,'waypoint_velocity_feedback_time_s':.1,'waypoint_velocity_feedback_max_m':.005,'waypoint_velocity_feedback_gate':'phase0/closedphase1/phase2 only; source waypoint unchanged, adapter IK servo target offset','waypoint_velocity_measurement':'consecutive PLAY control samples of native pick origin in current guitar frame; first sample zero','waiting_arm_owner':'adapter incremental READY targets during actual phase1 closed window; frozen policy owns fingers','phase_target_geometry':'READY ready, APPROACH entry then exit after measured entry, RECOVER original exit/clearance','source_phase_or_detector_override':False,'recovery_arm_owner':'adapter incremental position targets; frozen policy still owns fingers','recovery_increment_gain':2.0,'adapter_exit_time_gate':'original strike_timed_approach_open; source song time read-only, no added dt','adapter_exit_early_before_source_open':False,'adapter_entry_before_source_open':'source READY geometry3; originalapproach helper unchanged','native_PLAY_damping_scale':.25,'native_PLAY_damping_joint_names':[env.names[i] for i in right_arm if i in source_right],'native_mode':'POSITION; no human EFFORT command','terminal_retraction':{'R9_increment_gain':2.,'lift_from_max_actual_or_source_ready_m':.03,'velocity_time_s':.1,'velocity_max_m':.005,'other72_goals_frozen':True,'source_clock_history_frozen':True,'PD_baseline_restore':True},'PD_switch_time_s':pd_switch_time,'PD_switch_gate':'actual source phase1 damping quarter during PLAY; other phases baseline; terminal retraction restores baseline','PD_switch_count':len(pd_switch_records),'PD_damping_schedule':{'0':1.,'1':.25,'2':1.}})
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
            'terminal_retraction_enabled':True,'terminal_retraction_anchor_G_m':hold_target_G.tolist() if hold_target_G is not None else None,'terminal_PD_baseline_restored':hold_PD_restored,'frame_count':len(recorder.frames) if recorder else 0,'videos':video,'music_success':False,'learning_updates':0,'free_finger_residual_rad':.2,'ready_proportional_max_rad':.15,'ready_integral_max_rad':.3,'ready_combined_max_rad':.3,'ready_integral_step_gain':.2,'integral_update_source_phases':[],'integral_update_gate':'held in all source phases; no PI update','approach_arm_owner':'adapter previous actuator target plus 2*current-guitar local IK correction; source arm9 requests logged only','policy_arm_requested_targets_used':False,'ready_arm_owner':'adapter previous actuator target plus 2*local IK correction during phase0 and closedphase1','ready_increment_gain':2.0,'waypoint_velocity_feedback_time_s':.1,'waypoint_velocity_feedback_max_m':.005,'waypoint_velocity_feedback_gate':'phase0/closedphase1/phase2 only; source waypoint unchanged, adapter IK servo target offset','waypoint_velocity_measurement':'consecutive PLAY control samples of native pick origin in current guitar frame; first sample zero','waiting_arm_owner':'adapter incremental READY targets during actual phase1 closed window; frozen policy owns fingers','phase_target_geometry':'READY ready, APPROACH entry then exit after measured entry, RECOVER original exit/clearance','source_phase_or_detector_override':False,'recovery_arm_owner':'adapter incremental position targets; frozen policy still owns fingers','recovery_increment_gain':2.0,'adapter_exit_time_gate':'original strike_timed_approach_open; source song time read-only, no added dt','adapter_exit_early_before_source_open':False,'adapter_entry_before_source_open':'source READY geometry3; originalapproach helper unchanged','native_PLAY_damping_scale':.25,'native_PLAY_damping_joint_names':[env.names[i] for i in right_arm if i in source_right],'native_mode':'POSITION; no human EFFORT command','terminal_retraction':{'R9_increment_gain':2.,'lift_from_max_actual_or_source_ready_m':.03,'velocity_time_s':.1,'velocity_max_m':.005,'other72_goals_frozen':True,'source_clock_history_frozen':True,'PD_baseline_restore':True},'PD_switch_time_s':pd_switch_time,'PD_switch_gate':'actual source phase1 damping quarter during PLAY; other phases baseline; terminal retraction restores baseline','PD_switch_count':len(pd_switch_records),'PD_damping_schedule':{'0':1.,'1':.25,'2':1.}})
    if failure or not all(checks.values()):raise RuntimeError(failure or checks)


if __name__=='__main__':main()
