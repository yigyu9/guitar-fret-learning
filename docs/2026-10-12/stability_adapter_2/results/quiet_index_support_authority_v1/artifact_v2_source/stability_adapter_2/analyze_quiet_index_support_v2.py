"""Measure completed index responses and preserve the terminal failed first minus."""
from pathlib import Path
import hashlib
import json
import numpy as np
from scipy.spatial.transform import Rotation

R=Path(__file__).resolve().parents[1];D=R/'docs/2026-10-12/stability_adapter_2'
P=D/'results/quiet_index_support_authority_v1';OLD=D/'results/initial_middle3_alignment_v1/native'
FIXED=('Pelvis',)+tuple(s+'_'+n for s in ('L','R') for n in ('Hip','Knee','Ankle','Toe'))


def read(p):return json.loads(Path(p).read_text())
def rows(p):return [json.loads(s) for s in Path(p).read_text().splitlines()]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def angles(q,ref):return np.degrees((Rotation.from_quat(q)*Rotation.from_quat(ref).inv()).magnitude())


def main():
    assert not (P/'analysis.json').exists()
    folders=dict(baseline=OLD,plus=P/'native/plus',minus=P/'native/minus_retry_v2')
    paths={Path(__file__).resolve(),R/'stability_adapter_2/QUIET_INDEX_SUPPORT_AUTHORITY_PLAN.md',R/'stability_adapter_2/QUIET_INDEX_SUPPORT_EXECUTION.md'}
    paths.update(f/n for f in folders.values() for n in ['initial_values.json','states.jsonl','trace.jsonl','controls.jsonl','contacts.jsonl','report.json','initial_grip_audit.json','capture.json','videos.json'])
    paths.update(P/(c+'_execution.json') for c in ['plus','minus','minus_retry_v2'])
    paths.add(R/'stability_adapter_2/QUIET_INDEX_NATIVE_RETRY_V2.md');paths.add(P/'minus_native_crash.json');paths.add(P/'minus.log')
    crash=read(P/'minus_native_crash.json');paths.update(Path(p) for p in crash['output_inventory'])
    paths.add(OLD/'tasks.jsonl')
    for condition in ['plus','minus','minus_retry_v2']:
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
    base=data['baseline'];names=base['initial']['human_joint_names'];idx=names.index('LH:index3');other=[i for i in range(81) if i!=idx]
    common=['motion_command','input_trial','effective_initial_settings','human_joint_names','human_body_names','main_control_joint_names',
        'actual_initial_angles_rad','initial_PD_target_rad','native_initial_state','guitar_goal_position_W_m','guitar_goal_quaternion_xyzw',
        'PD_properties','physics_parameters','absolute_strap_rest_length_m','initial_route_length_m','body9_gain_change',
        'strap_law_parameters','warmstart_alpha','preserved_absolute_targets_rad','left33_names']
    checks={};summary={};series={}
    failed=read(P/'minus_execution.json')
    checks['first_minus_terminal_crash_preserved']=failed['exit_code']==-11 and failed['terminal_state']=='error' and crash['completed'] is False and all(crash['checks'].values()) and all(Path(p).stat().st_size==v['size'] and sha(p)==v['sha256'] for p,v in crash['output_inventory'].items())
    checks['first_minus_execution_provenance_exact']=sha(P/'minus_execution.json')==crash['execution_sha256'] and sha(P/'minus.log')==failed['log_sha256'] and failed['input_sha256_before']==failed['input_sha256_after'] and all(sha(p)==h for p,h in failed['input_sha256_before'].items())
    checks['failed_first_minus_prefix_before_pulse_exact']=all(rows(P/'native/minus'/n)==base['states' if n=='states.jsonl' else 'trace' if n=='trace.jsonl' else 'contacts'][:len(rows(P/'native/minus'/n))] for n in ['states.jsonl','trace.jsonl','contacts.jsonl'])
    failed_controls=rows(P/'native/minus/controls.jsonl');failed_tasks=rows(P/'native/minus/tasks.jsonl')
    checks['failed_first_minus_commands_tasks_prefix_exact']=len(failed_controls)==152 and len(failed_tasks)==153 and failed_tasks==rows(OLD/'tasks.jsonl')[:153] and all(c['index_support_delta_rad']==0 and all(c[k]==b[k] for k in ['physics_step','final_target_rad','command_time_s','updated_before_step','wrist_motion_delta_rad','wrist_actual_at_update_rad','task_error_m_scaled_rad','other48_targets_held']) for c,b in zip(failed_controls,base['controls']))
    assert crash['physics_steps_observed']==152 and crash['frame_count']==19 and crash['simulation_elapsed_s_observed']<2
    for label,d in data.items():
        initial,states,trace,controls,report=(d[k] for k in ['initial','states','trace','controls','report'])
        checks[label+'_completed_1200_steps']=report['completed'] and report['failure'] is None and report['physics_steps']==1200 and report['simulation_elapsed_s']==5 and all(report['checks'].values())
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
        targets=np.array([c['final_target_rad'] for c in controls]);index_error=targets[:,idx]-actual[1:,idx]
        lower=np.array(initial['PD_properties']['lower']);upper=np.array(initial['PD_properties']['upper'])
        excess=np.maximum(lower-actual,actual-upper)
        summary[label]=dict(max_initial_position_error_mm=float(dp.max()),max_initial_rotation_error_deg=float(dr.max()),
            end_position_error_mm=float(dp[-1]),end_rotation_error_deg=float(dr[-1]),
            max_late_1s_position_change_mm=max(w[0] for w in window),max_late_1s_rotation_change_deg=max(w[1] for w in window),late_window_count=len(window),
            index3_actual_range_rad=[float(actual[:,idx].min()),float(actual[:,idx].max())],index3_late_PD_error_abs_max_rad=float(abs(index_error[480:]).max()),
            max_actual_native_limit_excess_rad=float(max(0,excess.max())),positive_raw_lambda_contact_steps=contacts,
            peak_applied_strap_tension_N=max(t['last_applied_tension_n'] for t in trace),end_applied_strap_tension_N=trace[-1]['last_applied_tension_n'],
            palm_up_proxy_passed=report['palm_up_proxy_passed'],constraint_violations=report['constraint_violations'])
        capture=read(folders[label]/'capture.json');frames=capture['frames'];videos=read(folders[label]/'videos.json')
        checks[label+'_151_readonly_strap_frames']=len(frames)==151 and all(v['physics_step']==i*8 and v['time_s']==i/30 and v['render_preserves_states'] and v['strap_route_points_W_m']==trace[i*8]['route_points_m'] and v['strap_rest_length_m']==initial['absolute_strap_rest_length_m'] for i,v in enumerate(frames))
        checks[label+'_604_raw_and_overlay_PNG_exact']=sum(len(v[k]) for v in frames for k in ['image_sha256','raw_image_sha256'])==604 and all(sha(p)==h for v in frames for k in ['image_sha256','raw_image_sha256'] for p,h in v[k].items())
        checks[label+'_two151frame30fps_videos']=set(videos)=={'whole_body','hands'} and all(v['ffmpeg_exit_code']==v['ffprobe_exit_code']==0 and v['stream']['nb_read_frames']=='151' and v['stream']['avg_frame_rate']=='30/1' and abs(float(v['stream']['duration'])-151/30)<1e-6 and sha(v['path'])==v['sha256'] for v in videos.values())
        series[label]=dict(time_s=[t['time_s'] for t in trace],position_error_mm=dp.tolist(),rotation_error_deg=dr.tolist(),
            position_W_m=pos.tolist(),quaternion_xyzw=q.tolist(),index3_actual_rad=actual[:,idx].tolist(),index3_target_rad=targets[:,idx].tolist())
        if label=='baseline':continue
        execution=read(P/(('plus' if label=='plus' else 'minus_retry_v2')+'_execution.json'))
        checks[label+'_native_execution_inputs_current']=execution['exit_code']==0 and execution['terminal_state']=='completed' and execution['input_sha256_before']==execution['input_sha256_after'] and all(sha(p)==h for p,h in execution['input_sha256_before'].items()) and sha(P/(('plus' if label=='plus' else 'minus_retry_v2')+'.log'))==execution['log_sha256']
        if label=='minus':checks['retry_preserved_original_failed_output']=execution['prior_partial_outputs_unchanged'] is True
        checks[label+'_20_initial_fields_exact']=all(initial[k]==base['initial'][k] for k in common)
        checks[label+'_states_trace_prefix_to2s_exact']=states[:481]==base['states'][:481] and trace[:481]==base['trace'][:481]
        checks[label+'_all1200_other80_targets_exact']=all(all(c['final_target_rad'][i]==b['final_target_rad'][i] for i in other) for c,b in zip(controls,base['controls']))
        checks[label+'_first484_all81_commands_exact']=all(c['final_target_rad']==b['final_target_rad'] for c,b in zip(controls[:484],base['controls'][:484]))
        sign=1 if label=='plus' else -1
        desired=np.array([np.float32(float(base['initial']['actual_initial_angles_rad']['LH:index3'])+float(initial['input_trial']['main_target_offsets_rad']['LH:index3'])+sign*.005*min(1.,max(0.,(c['command_time_s']-2)/.5))) for c in controls])
        checks[label+'_index3_ramp_exact_bounds_other_commands']=bool(np.array_equal(desired,targets[:,idx]) and np.all(targets>=lower) and np.all(targets<=upper) and all(c['command_time_s']==b['command_time_s'] and c['wrist_motion_delta_rad']==b['wrist_motion_delta_rad'] and c['updated_before_step']==b['updated_before_step'] for c,b in zip(controls,base['controls'])))
        checks[label+'_fresh15_direct_source_gate']=len(d['audit']['checks'])==15 and all(d['audit']['checks'].values()) and d['audit']['complete_source_self_screen']['pair_count']==1188
        first=next((i for i,(s,b) in enumerate(zip(states,base['states'])) if s!=b),None)
        summary[label]['first_nonidentical_native_state_step']=first
        summary[label]['t5_position_difference_from_baseline_W_m']=(pos[-1]-np.array(series['baseline']['position_W_m'][-1])).tolist()
        summary[label]['t5_rotation_log_from_baseline_W_rad']=(Rotation.from_quat(q[-1])*Rotation.from_quat(series['baseline']['quaternion_xyzw'][-1]).inv()).as_rotvec().tolist()
    plus,minus=(summary[n] for n in ['plus','minus'])
    response=np.r_[np.array(plus['t5_position_difference_from_baseline_W_m'])-minus['t5_position_difference_from_baseline_W_m'],
        np.array(plus['t5_rotation_log_from_baseline_W_rad'])-minus['t5_rotation_log_from_baseline_W_rad']]/.01
    checks['all_inputs_unchanged']=all(sha(p)==h for p,h in before.items())
    assert all(checks.values()),checks
    result=dict(checks=checks,summary=summary,compared_initial_fields=common,central_t5_response_6x1=response[:,None].tolist(),
        response_row_units=['m/rad']*3+['rad/rad']*3,response_frame='world XYZ position; world rotation logs relative to same t5 baseline, central subtraction divided by0.01rad',
        input_sha256_before=before,input_sha256_after={p:sha(p) for p in before},physical_initializations=3,completed_trial_physics_steps=2400,failed_trial_steps_observed=crash['physics_steps_observed'],total_physics_steps_observed=2400+crash['physics_steps_observed'],failed_first_minus=dict(exit_code=-11,simulation_elapsed_s_observed=crash['simulation_elapsed_s_observed'],frame_count=19,last_captured_simulation_s=crash['last_captured_simulation_s']),actor_inference_calls=0,training_updates=0,
        scope='Two completed physical index3 target-ramp responses plus preserved first-minus terminal crash; total step count includes observed failed trial steps; local contact-dependent finite response, not global Jacobian or feedback-gain certificate; no simulation in this analyzer')
    (P/'analysis.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    (P/'series.json').write_text(json.dumps(series,allow_nan=False)+'\n')
    print(json.dumps(dict(checks=len(checks),summary=summary,central_t5_response_6x1=result['central_t5_response_6x1']),indent=2))


if __name__=='__main__':main()
