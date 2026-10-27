"""Measure current-condition signed shoulder PD-goal to guitar world-pose response."""
from pathlib import Path
import hashlib,json
import numpy as np
from scipy.spatial.transform import Rotation
from .analyze_small_wrist_motion import metrics
from .analyze_body9_strap_minus4mm import strap_metrics
from .warmstart_targets import compose
from .build_fixed_lower_asset import LOWER_BODIES
R=Path(__file__).resolve().parents[1];A=R/'stability_adapter_2';B=R/'docs/2026-10-12/stability_adapter_2/results';P=B/'fixed_strap_shoulder_response_v1';BASE=B/'joint_only_fixed_strap_v1/native'
def read(p):return json.loads(Path(p).read_text())
def lines(p):return [json.loads(s) for s in Path(p).read_text().splitlines()]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def error_vectors(states,initial):
    ref=Rotation.from_quat(initial['guitar_goal_quaternion_xyzw']);p0=np.array(initial['guitar_goal_position_W_m']);result=[]
    for state in states:
        body=state['guitar_body_states'][0];p=np.array([body['pose']['p'][k] for k in 'xyz']);q=[body['pose']['r'][k] for k in 'xyzw']
        result.append(np.r_[p-p0,(Rotation.from_quat(q)*ref.inv()).as_rotvec()])
    return np.array(result)
def main():
    assert not (P/'analysis.json').exists();folders={'baseline':BASE,'minus008':P/'minus008','plus008':P/'plus008'};hashes={}
    for folder in folders.values():
        for n in ['initial_values.json','states.jsonl','trace.jsonl','controls.jsonl','contacts.jsonl','capture.json','report.json','videos.json']:hashes[str(folder/n)]=sha(folder/n)
    for p in [Path(__file__).resolve(),P/'preparation.json',P/'proposal.json',P/'minus008_execution.json',P/'plus008_execution.json']+[A/n for n in ['FIXED_STRAP_SHOULDER_RESPONSE_PLAN.md','analyze_small_wrist_motion.py','analyze_body9_strap_minus4mm.py','analyze_body9_strap_fine.py','warmstart_targets.py','strap.py','build_fixed_lower_asset.py']]:hashes[str(p)]=sha(p)
    data={label:dict(initial=read(folder/'initial_values.json'),states=lines(folder/'states.jsonl'),trace=lines(folder/'trace.jsonl'),controls=lines(folder/'controls.jsonl'),contacts=lines(folder/'contacts.jsonl'),report=read(folder/'report.json'),capture=read(folder/'capture.json')) for label,folder in folders.items()}
    base=data['baseline'];i0=base['initial'];names=i0['human_joint_names'];axis=names.index('L_Shoulder_y');other=[j for j in range(81) if j!=axis];main=[names.index(n) for n in i0['main_control_joint_names']];wrist=main.index(names.index('L_Wrist_x'));checks={};summary=[];means={};deltas={'baseline':0.}
    windows={'0_to_0p1':(0,.1),'0p1_to_0p5':(.1,.5),'2_to_5':(2,5),'4_to_5':(4,5)}
    common=['native_initial_state','initial_PD_target_rad','PD_properties','physics_parameters','guitar_goal_position_W_m','guitar_goal_quaternion_xyzw','main_control_joint_names','human_joint_names','human_body_names','strap_law_parameters','absolute_strap_rest_length_m','initial_route_length_m','motion_command']
    for label,d in data.items():
        i=d['initial'];states=d['states'];controls=d['controls'];report=d['report'];cap=d['capture'];trace=d['trace']
        checks[label+'_complete_1200_rows']=report['completed'] and report['failure'] is None and report['native_initializations']==1 and report['physics_steps']==1200 and len(states)==len(trace)==1201 and len(controls)==len(d['contacts'])==1200 and [s['physics_step'] for s in states]==list(range(1201)) and all(t['time_s']==j/240 for j,t in enumerate(trace)) and [c['physics_step'] for c in controls]==list(range(1,1201)) and [c['physics_step'] for c in d['contacts']]==list(range(1,1201))
        checks[label+'_native_checks']=all(report['checks'].values()) and i['absolute_strap_rest_length_m']==1.1018469719600776
        if label!='baseline':
            checks[label+'_all_common_initial_fields_exact']=all(i[k]==i0[k] for k in common)
            restored=json.loads(json.dumps(i['input_trial']));restored['main_target_offsets_rad']['L_Shoulder_y']=i0['input_trial']['main_target_offsets_rad']['L_Shoulder_y']
            checks[label+'_only_Shoulder_y_trial_offset_changed']=restored==i0['input_trial']
            checks[label+'_other80_all1200targets_clock_exact']=all(all(c['final_target_rad'][j]==b['final_target_rad'][j] for j in other) and all(c[k]==b[k] for k in ['physics_step','updated_before_step','command_time_s','wrist_motion_delta_rad']) for c,b in zip(controls,base['controls']))
            deltas[label]=float(i['preserved_absolute_targets_rad'][axis])-float(i0['preserved_absolute_targets_rad'][axis])
            checks[label+'_constant_Shoulder_y_delta']=all(float(c['final_target_rad'][axis])-float(b['final_target_rad'][axis])==deltas[label] for c,b in zip(controls,base['controls']))
            offsets=np.array([i['input_trial']['main_target_offsets_rad'].get(names[j],0.) for j in main]);q=np.array(i['initial_PD_target_rad'],dtype=np.float32);lo=np.array(i['PD_properties']['lower']);hi=np.array(i['PD_properties']['upper'])
            for c in controls:
                command=offsets.copy();command[wrist]+=c['wrist_motion_delta_rad'];assert np.array_equal(compose(q,main,command,lo,hi),np.array(c['final_target_rad'],dtype=np.float32))
            checks[label+'_1200_unclipped_targets_reconstructed']=True
            audit=read(folders[label]/'initial_grip_audit.json');hashes[str(folders[label]/'initial_grip_audit.json')]=sha(folders[label]/'initial_grip_audit.json')
            checks[label+'_fresh14_and1188self_clear']=len(audit['checks'])==14 and all(audit['checks'].values()) and audit['complete_source_self_screen']['pair_count']==1188 and not audit['complete_source_self_screen']['intersections']
            for f in cap['frames']:
                for k in ['image_sha256','raw_image_sha256']:assert all(sha(p)==h for p,h in f[k].items())
            checks[label+'_604PNG_exact']=True
        checks[label+'_fixed_root_lower_allstates']=all(all(s['human_body_states'][i['human_body_names'].index(n)]==states[0]['human_body_states'][i['human_body_names'].index(n)] for n in ('Pelvis',)+LOWER_BODIES) for s in states)
        checks[label+'_151frame_steps_readonly']=len(cap['frames'])==151 and len(report['videos'])==2 and all(f['physics_step']==j*8 and f['time_s']==j/30 and f['render_preserves_states'] for j,f in enumerate(cap['frames']))
        e=error_vectors(states,i);times=np.arange(1201)/240.;means[label]={n:e[(times>=bounds[0])&(times<=bounds[1])].mean(axis=0).tolist() for n,bounds in windows.items()}
        contacts={};self_steps=set()
        for row in d['contacts']:
            for c in row['contacts']:
                pair=(c['body0_name'],c['body1_name'])
                if all(n.startswith('human/') for n in pair):self_steps.add(row['physics_step'])
                if c['lambda']>0 and any(n.startswith('guitar/') for n in pair) and any(n.startswith('human/') for n in pair):contacts.setdefault(next(n for n in pair if n.startswith('human/')),set()).add(row['physics_step'])
        qactual=np.array([[s['pos'] for s in state['human_dof_states']] for state in states]);excess=np.maximum(np.array(i['PD_properties']['lower'])-qactual,qactual-np.array(i['PD_properties']['upper']));body9=[names.index(n+'_'+k) for n in ['Torso','Spine','Chest'] for k in 'xyz']
        summary.append(dict(label=label,guitar=metrics(trace),strap=strap_metrics(trace,i),actual_target_delta_rad=deltas[label],mean_world_error_m_rad=means[label],human_self_contact_steps=len(self_steps),human_guitar_positive_raw_lambda_steps={n:len(v) for n,v in sorted(contacts.items())},body9_max_coordinate_drift_deg=float(np.degrees(abs(qactual[:,body9]-qactual[0,body9]).max())),max_actual_native_bound_excess_rad=float(max(0,excess.max()))))
    checks['actual_float32_delta_signs']=deltas['minus008']<0<deltas['plus008'];weights=np.array([1,1,1,.1,.1,.1]);secants={}
    for window in windows:
        zero=np.array(means['baseline'][window]);minus=np.array(means['minus008'][window]);plus=np.array(means['plus008'][window]);jm=(minus-zero)/deltas['minus008'];jp=(plus-zero)/deltas['plus008'];jc=(plus-minus)/(deltas['plus008']-deltas['minus008']);wj=weights*jc;den=float(wj@wj)
        secants[window]=dict(sampled_column_rank=int(den>0),sampled_column_rank_upper_bound=1,central_W_m_per_rad_rad_per_rad=jc.tolist(),backward=jm.tolist(),forward=jp.tolist(),weighted_central_norm_m_per_rad=float(np.linalg.norm(wj)),weighted_forward_backward_difference_m_per_rad=float(np.linalg.norm(weights*(jp-jm))),weighted_baseline_linear_prediction_residual_m={label:float(np.linalg.norm(weights*(np.array(means[label][window])-zero-jc*deltas[label]))) for label in ['minus008','plus008']},unbounded_1D_least_squares_delta_rad=float(-wj@(weights*zero)/den) if den>0 else None)
    checks['all_secant_values_finite']=all(np.isfinite(np.array(v['central_W_m_per_rad_rad_per_rad'])).all() for v in secants.values());checks['all_inputs_preserved']=all(sha(p)==h for p,h in hashes.items());assert all(checks.values()),checks
    result=dict(checks=checks,input_sha256=hashes,summary=summary,actual_target_deltas_rad=deltas,secants=secants,world_error_definition='p-p_goal; Log(R_current R_goal^-1), world m/rad; average windows include both endpoints',analysis_rotation_lever_m=.1,new_native_initializations=2,new_physics_steps=2400,scope='two static Shoulder_y target probes at current fixed-LA pose; secants of mean error, not instantaneous/native Jacobian or final66 controllability; no feedback/actor/training')
    (P/'analysis.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps(dict(checks=checks,summary=summary,secants=secants),indent=2))
if __name__=='__main__':main()
