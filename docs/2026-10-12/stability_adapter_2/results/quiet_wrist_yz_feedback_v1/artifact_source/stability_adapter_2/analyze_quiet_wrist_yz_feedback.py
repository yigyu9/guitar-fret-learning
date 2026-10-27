"""Verify current-guitar-error feedback OFF/ON from saved native data."""
from pathlib import Path
import hashlib
import json
import numpy as np
from scipy.spatial.transform import Rotation

R=Path(__file__).resolve().parents[1];D=R/'docs/2026-10-12/stability_adapter_2'
P=D/'results/quiet_wrist_yz_feedback_v1';OLD=D/'results/initial_middle3_alignment_v1/native'
FIXED=('Pelvis',)+tuple(s+'_'+n for s in ('L','R') for n in ('Hip','Knee','Ankle','Toe'))


def read(p):return json.loads(Path(p).read_text())
def rows(p):return [json.loads(s) for s in Path(p).read_text().splitlines()]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def angles(q,ref):return np.degrees((Rotation.from_quat(q)*Rotation.from_quat(ref).inv()).magnitude())


def main():
    assert not (P/'analysis.json').exists()
    folders=dict(baseline=OLD,off=P/'native/off',on=P/'native/on')
    paths={Path(__file__).resolve(),R/'stability_adapter_2/QUIET_WRIST_YZ_FEEDBACK_PLAN.md',R/'stability_adapter_2/QUIET_WRIST_YZ_FEEDBACK_EXECUTION.md'}
    comparison=R/'docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/comparison_v2.json'
    paths.update([comparison,comparison.parent/'artifact_inventory.json',P/'preflight.json'])
    paths.update(f/n for f in folders.values() for n in ['initial_values.json','states.jsonl','trace.jsonl','controls.jsonl','contacts.jsonl','report.json','initial_grip_audit.json','capture.json','videos.json'])
    paths.update(P/(c+'_execution.json') for c in ['off','on'])
    for condition in ['off','on']:
        paths.add(P/(condition+'.log'))
        paths.update(Path(p) for p in read(P/(condition+'_execution.json'))['input_sha256_before'])
    for f in folders.values():
        for frame in read(f/'capture.json')['frames']:
            paths.update(Path(p) for key in ['image_sha256','raw_image_sha256'] for p in frame[key])
        paths.update(Path(v['path']) for v in read(f/'videos.json').values())
    before={str(p):sha(p) for p in sorted(paths,key=str)}
    data={label:{'initial':read(f/'initial_values.json'),'states':rows(f/'states.jsonl'),'trace':rows(f/'trace.jsonl'),
        'controls':rows(f/'controls.jsonl'),'contacts':rows(f/'contacts.jsonl'),'report':read(f/'report.json'),
        'audit':read(f/'initial_grip_audit.json')} for label,f in folders.items()}
    base=data['baseline'];names=base['initial']['human_joint_names'];support=[names.index(n) for n in ['L_Wrist_y','L_Wrist_z']];other=[i for i in range(81) if i not in support]
    response=np.array(read(comparison)['response_matrix_world_6x2']);scale=np.r_[np.full(3,.03),np.full(3,np.deg2rad(5.))];kappa=.00242502989755426
    common=['motion_command','input_trial','effective_initial_settings','human_joint_names','human_body_names','main_control_joint_names',
        'actual_initial_angles_rad','initial_PD_target_rad','native_initial_state','guitar_goal_position_W_m','guitar_goal_quaternion_xyzw',
        'PD_properties','physics_parameters','absolute_strap_rest_length_m','initial_route_length_m','body9_gain_change',
        'strap_law_parameters','warmstart_alpha','preserved_absolute_targets_rad','left33_names']
    checks={};summary={};series={}
    for label,d in data.items():
        initial,states,trace,controls,report=(d[k] for k in ['initial','states','trace','controls','report'])
        checks[label+'_completed_1200_steps']=report['completed'] and report['failure'] is None and report['physics_steps']==1200 and report['simulation_elapsed_s']==5 and report['native_initialization_attempts']==report['native_initializations']==1 and all(report['checks'].values())
        checks[label+'_ordered_samples']=len(states)==len(trace)==1201 and len(controls)==len(d['contacts'])==1200 and [s['physics_step'] for s in states]==list(range(1201)) and all(t['time_s']==i/240 for i,t in enumerate(trace)) and [c['physics_step'] for c in controls]==list(range(1,1201)) and [c['physics_step'] for c in d['contacts']]==list(range(1,1201))
        fixed=[initial['human_body_names'].index(n) for n in FIXED]
        checks[label+'_root_lower_fixed']=all(all(s['human_body_states'][i]==states[0]['human_body_states'][i] for i in fixed) for s in states)
        checks[label+'_fixed_LA']=all(t['strap_rest_length_m']==base['initial']['absolute_strap_rest_length_m'] for t in trace)
        pos=np.array([t['guitar_position_m'] for t in trace]);q=np.array([t['guitar_quaternion_xyzw'] for t in trace])
        rawp=np.array([[s['guitar_body_states'][0]['pose']['p'][k] for k in 'xyz'] for s in states])
        rawq=np.array([[s['guitar_body_states'][0]['pose']['r'][k] for k in 'xyzw'] for s in states]);rawq/=np.linalg.norm(rawq,axis=1,keepdims=True)
        checks[label+'_trace_matches_native_pose']=bool(np.isfinite(pos).all() and np.isfinite(q).all() and np.array_equal(pos,rawp) and np.max(np.minimum(np.linalg.norm(q-rawq,axis=1),np.linalg.norm(q+rawq,axis=1)))<1e-12)
        dp=np.linalg.norm(pos-initial['guitar_goal_position_W_m'],axis=1)*1000;dr=angles(q,initial['guitar_goal_quaternion_xyzw'])
        checks[label+'_independent_pose_errors']=bool(np.max(abs(dp-np.array([t['position_error_m'] for t in trace])*1000))<1e-9 and np.max(abs(dr-np.array([t['rotation_error_deg'] for t in trace])))<1e-4)
        window=[(float(np.linalg.norm(pos[i:i+241]-pos[i],axis=1).max()*1000),float(angles(q[i:i+241],q[i]).max())) for i in range(480,961,4)]
        contacts={}
        for c in d['contacts']:
            positive=set()
            for v in c['contacts']:
                pair=(v['body0_name'],v['body1_name'])
                if v['lambda']>0 and any(n.startswith('guitar/') for n in pair):
                    positive.update(n.split('/',1)[1] for n in pair if n.startswith('human/'))
            for n in positive:contacts[n]=contacts.get(n,0)+1
        actual=np.array([[v['pos'] for v in s['human_dof_states']] for s in states])
        targets=np.array([c['final_target_rad'] for c in controls])
        lower=np.array(initial['PD_properties']['lower']);upper=np.array(initial['PD_properties']['upper'])
        torso=[names.index(b+'_'+axis) for b in ['Torso','Spine','Chest'] for axis in 'xyz'];body_change=abs(actual[:,torso]-actual[0,torso]);where=np.unravel_index(body_change.argmax(),body_change.shape)
        checks[label+'_body9_targets_held']=bool(np.array_equal(targets[:,torso],np.broadcast_to(np.array(initial['initial_PD_target_rad'])[torso],(1200,9))))
        excess=np.maximum(lower-actual,actual-upper)
        summary[label]=dict(max_initial_position_error_mm=float(dp.max()),max_initial_rotation_error_deg=float(dr.max()),
            end_position_error_mm=float(dp[-1]),end_rotation_error_deg=float(dr[-1]),
            max_late_1s_position_change_mm=max(w[0] for w in window),max_late_1s_rotation_change_deg=max(w[1] for w in window),late_window_count=len(window),
            support_actual_min_rad=actual[:,support].min(axis=0).tolist(),support_actual_max_rad=actual[:,support].max(axis=0).tolist(),
            support_late_PD_error_abs_max_rad=abs(targets[480:,support]-actual[481:,support]).max(axis=0).tolist(),
            body9_max_actual_coordinate_change_rad=float(body_change.max()),body9_max_change_joint=names[torso[where[1]]],body9_max_change_step=int(where[0]),
            max_actual_native_limit_excess_rad=float(max(0,excess.max())),positive_raw_lambda_contact_steps=contacts,
            peak_applied_strap_tension_N=max(t['last_applied_tension_n'] for t in trace),end_applied_strap_tension_N=trace[-1]['last_applied_tension_n'],
            palm_up_proxy_passed=report['palm_up_proxy_passed'],constraint_violations=report['constraint_violations'])
        capture=read(folders[label]/'capture.json');frames=capture['frames'];videos=read(folders[label]/'videos.json')
        checks[label+'_151_readonly_strap_frames']=len(frames)==151 and all(v['physics_step']==i*8 and v['time_s']==i/30 and v['render_preserves_states'] and v['strap_route_points_W_m']==trace[i*8]['route_points_m'] and v['strap_rest_length_m']==initial['absolute_strap_rest_length_m'] for i,v in enumerate(frames))
        checks[label+'_604_raw_and_overlay_PNG_exact']=sum(len(v[k]) for v in frames for k in ['image_sha256','raw_image_sha256'])==604 and all(sha(p)==h for v in frames for k in ['image_sha256','raw_image_sha256'] for p,h in v[k].items())
        checks[label+'_two151frame30fps_videos']=set(videos)=={'whole_body','hands'} and all(v['ffmpeg_exit_code']==v['ffprobe_exit_code']==0 and v['stream']['nb_read_frames']=='151' and v['stream']['avg_frame_rate']=='30/1' and abs(float(v['stream']['duration'])-151/30)<1e-6 and sha(v['path'])==v['sha256'] for v in videos.values())
        series[label]=dict(time_s=[t['time_s'] for t in trace],position_error_mm=dp.tolist(),rotation_error_deg=dr.tolist(),
            position_W_m=pos.tolist(),quaternion_xyzw=q.tolist(),support_actual_rad=actual[:,support].tolist(),support_target_rad=targets[:,support].tolist())
        if label=='baseline':continue
        execution=read(P/(label+'_execution.json'))
        checks[label+'_native_execution_inputs_current']=execution['exit_code']==0 and execution['terminal_state']=='completed' and execution['input_sha256_before']==execution['input_sha256_after'] and all(sha(p)==h for p,h in execution['input_sha256_before'].items()) and sha(P/(label+'.log'))==execution['log_sha256']
        checks[label+'_20_initial_fields_exact']=all(initial[k]==base['initial'][k] for k in common)
        checks[label+'_states_trace_prefix_to2s_exact']=states[:481]==base['states'][:481] and trace[:481]==base['trace'][:481]
        checks[label+'_all1200_other79_targets_exact']=all(all(c['final_target_rad'][i]==b['final_target_rad'][i] for i in other) for c,b in zip(controls,base['controls']))
        fingers=[i for i,n in enumerate(names) if n.startswith(('LH:','RH:'))]
        checks[label+'_all_finger_targets_exact']=bool(np.array_equal(targets[:,fingers],np.array([c['final_target_rad'] for c in base['controls']])[:,fingers]))
        checks[label+'_first484_all81_commands_exact']=all(c['final_target_rad']==b['final_target_rad'] for c,b in zip(controls[:484],base['controls'][:484]))
        checks[label+'_target_native_bounds_and_original_motion_exact']=bool(np.all(targets>=lower) and np.all(targets<=upper) and all(c['command_time_s']==b['command_time_s'] and c['wrist_motion_delta_rad']==b['wrist_motion_delta_rad'] and c['updated_before_step']==b['updated_before_step'] for c,b in zip(controls,base['controls'])))
        delta=np.zeros(2);feedback_ok=True;held_ok=True;rate_max=0.;angle_max=0.
        for k,c in enumerate(controls):
            rec=c['feedback']
            if k%4==0:
                gp=np.array([states[k]['guitar_body_states'][0]['pose']['p'][v] for v in 'xyz'])
                gq=np.array([states[k]['guitar_body_states'][0]['pose']['r'][v] for v in 'xyzw'])
                error=np.r_[np.array(initial['guitar_goal_position_W_m'])-gp,(Rotation.from_quat(initial['guitar_goal_quaternion_xyzw'])*Rotation.from_quat(gq).inv()).as_rotvec()]
                gradient=(response/scale[:,None]).T@(error/scale)
                active=label=='on' and k/240>2.;rate=np.clip(kappa*gradient,-.002,.002) if active else np.zeros(2)
                following=np.clip(delta+rate/60,-.005,.005) if active else np.zeros(2)
                effective=(following-delta)*60
                feedback_ok &= c['command_time_s']==k/240 and rec['feedback_active']==active and rec['guitar_position_at_update_W_m']==gp.tolist() and rec['guitar_quaternion_at_update_xyzw']==gq.tolist()
                for field,expected in [('guitar_error_at_update_world_m_rad',error),('gradient_per_rad',gradient),('delta_before_rad',delta),('requested_rate_rad_s',rate),('delta_after_rad',following),('effective_rate_rad_s',effective)]:
                    feedback_ok &= bool(np.allclose(rec[field],expected,rtol=0,atol=1e-14))
                rate_max=max(rate_max,float(abs(effective).max()));angle_max=max(angle_max,float(abs(following).max()));delta=following
                expected_target=np.array([float(initial['actual_initial_angles_rad'][names[i]])+(float(initial['input_trial']['main_target_offsets_rad'][names[i]])+delta[j]) for j,i in enumerate(support)],dtype=np.float32)
            elif rec!=controls[k-1]['feedback']:held_ok=False
            feedback_ok &= bool(np.array_equal(targets[k,support],expected_target))
        checks[label+'_live_error_gradient_rate_delta_target_recomputed']=bool(feedback_ok)
        checks[label+'_control_record_held_between60Hz_updates']=held_ok
        checks[label+'_bounded_angle_and_effective_rate']=angle_max<=.005 and rate_max<=.002+1e-14
        checks[label+'_offset66_within_point3']=bool(np.max(abs(targets[:,[names.index(n) for n in initial['main_control_joint_names']]]-np.array([initial['actual_initial_angles_rad'][n] for n in initial['main_control_joint_names']])))<=.3+1e-7)
        summary[label].update(final_delta_rad=delta.tolist(),max_abs_delta_rad=angle_max,max_abs_effective_rate_rad_s=rate_max)
        series[label]['delta_rad']=[c['feedback']['delta_after_rad'] for c in controls]
        if label=='off':
            checks['off_full_native_states_trace_and81targets_exact']=states==base['states'] and trace==base['trace'] and all(c['final_target_rad']==b['final_target_rad'] for c,b in zip(controls,base['controls']))
        checks[label+'_fresh15_direct_source_gate']=len(d['audit']['checks'])==15 and all(d['audit']['checks'].values()) and d['audit']['complete_source_self_screen']['pair_count']==1188
        first=next((i for i,(s,b) in enumerate(zip(states,base['states'])) if s!=b),None)
        summary[label]['first_nonidentical_native_state_step']=first
        summary[label]['t5_position_difference_from_baseline_W_m']=(pos[-1]-np.array(series['baseline']['position_W_m'][-1])).tolist()
        summary[label]['t5_rotation_log_from_baseline_W_rad']=(Rotation.from_quat(q[-1])*Rotation.from_quat(series['baseline']['quaternion_xyzw'][-1]).inv()).as_rotvec().tolist()
    checks['all_inputs_unchanged']=all(sha(p)==h for p,h in before.items())
    assert all(checks.values()),checks
    result=dict(checks=checks,summary=summary,compared_initial_fields=common,support_joints=['L_Wrist_y','L_Wrist_z'],feedback_response_source=str(comparison),
        input_sha256_before=before,input_sha256_after={p:sha(p) for p in before},physical_initializations=2,physical_steps=2400,actor_inference_calls=0,training_updates=0,
        scope='Saved current world guitar-error feedback OFF/ON; native invariants and target synthesis checked, not natural playing or global closed-loop stability certification; no simulation in this analyzer')
    (P/'analysis.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    (P/'series.json').write_text(json.dumps(series,allow_nan=False)+'\n')
    print(json.dumps(dict(checks=len(checks),summary=summary),indent=2))


if __name__=='__main__':main()
