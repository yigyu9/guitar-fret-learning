"""Compare the -4mm strap trial with identical wrist motion and the original quiet hold."""
import hashlib,json
from pathlib import Path
import numpy as np
from .analyze_small_wrist_motion import metrics
from .strap import cable_forces
ROOT=Path(__file__).resolve().parents[1];B=ROOT/'docs/2026-10-12/stability_adapter_2/results';P=B/'body9_strap_minus4mm_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def lines(p):return [json.loads(v) for v in Path(p).read_text().splitlines()]
def strap_metrics(trace,initial):
    law=initial['strap_law_parameters'];rest=initial['absolute_strap_rest_length_m'];values=[cable_forces(np.array(r['route_points_m']),np.array(r['route_point_velocities_mps']),rest,law['stiffness_n_per_m'],law['damping_n_s_per_m'],law['max_tension_n'])[1] for r in trace[:-1]];applied=[r['last_applied_tension_n'] for r in trace[1:]];error=max(abs(a-b) for a,b in zip(values,applied));assert error<1e-8
    return dict(rest_length_m=rest,initial_route_length_m=initial['initial_route_length_m'],initial_slack_mm=(rest-initial['initial_route_length_m'])*1000,first_positive_step=next((i+1 for i,v in enumerate(applied) if v>0),None),max_law_tension_n=max(applied),end_law_tension_n=applied[-1],law_reconstruction_max_error_n=error)
def wrist_response(states,static,k):
    times=np.arange(480,1201)/240.;difference=np.array([a['human_dof_states'][k]['pos']-b['human_dof_states'][k]['pos'] for a,b in zip(states[480:],static[480:])]);X=np.column_stack((np.ones(len(times)),times-2,np.sin(2*np.pi*times),np.cos(2*np.pi*times)));fit=np.linalg.lstsq(X,difference,rcond=None)[0];return dict(amplitude_rad=float(np.hypot(fit[2],fit[3])),amplitude_deg=float(np.degrees(np.hypot(fit[2],fit[3]))),scope='actual scalar q minus original static baseline, constant/trend/1Hz fit on2..5s; not bone rotation')
def main():
    out=P/'analysis.json';assert not out.exists();old=B/'small_wrist_motion_v1/native';new=P/'native';static=B/'torso_hold_native_collision_v1/native';mid=B/'body9_strap_minus2mm_v1/native';inputs={}
    for folder in (old,mid,new):
        for name in ('initial_values.json','states.jsonl','trace.jsonl','controls.jsonl','contacts.jsonl','capture.json','report.json','videos.json'):
            p=folder/name;inputs[str(p)]=sha(p)
    for p in (static/'states.jsonl',Path(__file__).resolve(),ROOT/'stability_adapter_2/analyze_small_wrist_motion.py',ROOT/'stability_adapter_2/strap.py',P/'native_execution.json',P/'preparation.json',ROOT/'stability_adapter_2/BODY9_STRAP_MINUS4MM_EXECUTION.md'):
        inputs[str(p)]=sha(p)
    i0=read(old/'initial_values.json');i1=read(new/'initial_values.json');s0=lines(old/'states.jsonl');s1=lines(new/'states.jsonl');t0=lines(old/'trace.jsonl');t1=lines(new/'trace.jsonl');c0=lines(old/'controls.jsonl');c1=lines(new/'controls.jsonl');report=read(new/'report.json');cap=read(new/'capture.json');fields=('native_initial_state','initial_PD_target_rad','preserved_absolute_targets_rad','PD_properties','physics_parameters','initial_route_length_m','guitar_goal_position_W_m','guitar_goal_quaternion_xyzw','main_control_joint_names','strap_law_parameters','motion_command');equal={f:i0[f]==i1[f] for f in fields}
    restored=json.loads(json.dumps(i1['input_trial']));restored['initial_settings']['strap_rest_length_m']=i0['input_trial']['initial_settings']['strap_rest_length_m'];baseline_controls=[(r['physics_step'],r['updated_before_step'],r['command_time_s'],r['wrist_motion_delta_rad'],r['final_target_rad']) for r in c0];new_controls=[(r['physics_step'],r['updated_before_step'],r['command_time_s'],r['wrist_motion_delta_rad'],r['final_target_rad']) for r in c1]
    checks=dict(completed_one1200step_two151frame=report['completed'] and report['failure'] is None and report['native_initializations']==1 and report['physics_steps']==1200 and len(s1)==len(t1)==1201 and len(cap['frames'])==151 and len(report['videos'])==2,all_native_checks=all(report['checks'].values()),all11_common_initial_fields_exact=all(equal.values()),only_trial_rest_length_changed=restored==i0['input_trial'],declared_LA_minus4mm=i1['absolute_strap_rest_length_m']==i0['absolute_strap_rest_length_m']-.004,all1200_submitted_commands_exact=baseline_controls==new_controls,capture_steps_complete=all(f['physics_step']==j*8 and f['time_s']==j/30 and f['render_preserves_states'] for j,f in enumerate(cap['frames'])))
    i2=read(mid/'initial_values.json');c2=lines(mid/'controls.jsonl')
    checks['mid11_initial_fields_and_names_exact']=all(i2[f]==i0[f] for f in fields) and i2['human_joint_names']==i0['human_joint_names']==i1['human_joint_names']
    checks['mid1200_commands_exact']=baseline_controls==[(r['physics_step'],r['updated_before_step'],r['command_time_s'],r['wrist_motion_delta_rad'],r['final_target_rad']) for r in c2]
    restored_mid=json.loads(json.dumps(i2['input_trial']));restored_mid['initial_settings']['strap_rest_length_m']=i0['input_trial']['initial_settings']['strap_rest_length_m']
    checks['mid_only_rest_minus2mm']=restored_mid==i0['input_trial'] and i2['absolute_strap_rest_length_m']==i0['absolute_strap_rest_length_m']-.002
    static_states=lines(static/'states.jsonl');k=i1['human_joint_names'].index('L_Wrist_x');summary=[]
    for label,folder,trace,states,initial in [('baseline',old,t0,s0,i0),('minus2mm',mid,lines(mid/'trace.jsonl'),lines(mid/'states.jsonl'),read(mid/'initial_values.json')),('minus4mm',new,t1,s1,i1)]:
        palm=set();self_steps=set();human_guitar={}
        for row in lines(folder/'contacts.jsonl'):
            for c in row['contacts']:
                pair=(c['body0_name'],c['body1_name'])
                if 'human/LH:palm' in pair and any(n.startswith('guitar/') for n in pair) and c['lambda']>0:palm.add(row['physics_step'])
                if all(n.startswith('human/') for n in pair):self_steps.add(row['physics_step'])
                if c['lambda']>0 and any(n.startswith('guitar/') for n in pair) and any(n.startswith('human/') for n in pair):
                    body=next(n for n in pair if n.startswith('human/'));human_guitar.setdefault(body,set()).add(row['physics_step'])
        summary.append(dict(label=label,guitar=metrics(trace),strap=strap_metrics(trace,initial),wrist=wrist_response(states,static_states,k),palm_guitar_positive_raw_lambda_steps=len(palm),human_self_contact_steps=len(self_steps),human_guitar_positive_raw_lambda_by_body={body:dict(steps=len(steps),first_step=min(steps),last_step=max(steps)) for body,steps in sorted(human_guitar.items())}))
    checks['law_reconstructed_same6000_120_300']=all(r['strap']['law_reconstruction_max_error_n']<1e-8 for r in summary)
    for f in cap['frames']:
        for key in ('image_sha256','raw_image_sha256'):
            for path,value in f[key].items():assert sha(path)==value
    checks['all604_recorded_image_SHA_exact']=True;checks['inputs_unchanged']=all(sha(p)==h for p,h in inputs.items());assert all(checks.values()),checks
    out.write_text(json.dumps(dict(checks=checks,input_sha256=inputs,common_initial_exact_fields=equal,summary=summary,new_native_initializations=1,new_physics_steps=1200,scope='constant LA change only, same wrist goal waveform and full native initial state/PD; physical response comparison, not success threshold/final66 playing/initial-G restoration controller completion'),indent=2)+'\n');print(json.dumps(dict(checks=checks,summary=summary),indent=2))
if __name__=='__main__':main()
