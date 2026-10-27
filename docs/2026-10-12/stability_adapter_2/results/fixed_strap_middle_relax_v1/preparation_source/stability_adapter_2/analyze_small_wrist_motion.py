"""Compare one recorded wrist-motion trial with the preserved quiet-hold baseline."""
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'docs/2026-10-12/stability_adapter_2/results'
PHASE=BASE/'small_wrist_motion_v1'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def lines(path):return [json.loads(v) for v in Path(path).read_text().splitlines()]
def rotation_difference(q,reference):
    q=np.asarray(q);q=q/np.linalg.norm(q,axis=1)[:,None]
    reference=np.asarray(reference);reference=reference/np.linalg.norm(reference,axis=-1,keepdims=True)
    return np.degrees(2*np.arccos(np.clip(abs(np.sum(q*reference,axis=1)),0,1)))
def quaternion(body):return [body['pose']['r'][v] for v in 'xyzw']
def position(body):return [body['pose']['p'][v] for v in 'xyz']
def metrics(trace):
    late=trace[480:];p=np.array([r['guitar_position_m'] for r in late]);q=[r['guitar_quaternion_xyzw'] for r in late]
    return dict(max_initial_position_error_mm=max(r['position_error_m'] for r in trace)*1000,max_initial_rotation_error_deg=max(r['rotation_error_deg'] for r in trace),end_initial_position_error_mm=trace[-1]['position_error_m']*1000,end_initial_rotation_error_deg=trace[-1]['rotation_error_deg'],max_position_change_from_2s_mm=float(np.linalg.norm(p-p[0],axis=1).max()*1000),max_rotation_change_from_2s_deg=float(rotation_difference(q,q[0]).max()))


def main():
    out=PHASE/'analysis.json';assert not out.exists();current=PHASE/'native';old=BASE/'torso_hold_native_collision_v1/native'
    inputs={str(Path(__file__).resolve()):sha(__file__)}
    for folder in (old,current):
        for name in ('states.jsonl','trace.jsonl','controls.jsonl','contacts.jsonl','initial_values.json','capture.json','report.json','videos.json'):
            p=folder/name;inputs[str(p)]=sha(p)
    for p in (PHASE/'native_execution.json',PHASE/'preflight.json',PHASE/'native_source.py',ROOT/'stability_adapter_2/SMALL_WRIST_MOTION_PLAN.md'):
        inputs[str(p)]=sha(p)
    i0=read(old/'initial_values.json');i1=read(current/'initial_values.json');s0=lines(old/'states.jsonl');s1=lines(current/'states.jsonl');t0=lines(old/'trace.jsonl');t1=lines(current/'trace.jsonl');controls=lines(current/'controls.jsonl');cap=read(current/'capture.json');report=read(current/'report.json')
    names=i1['human_joint_names'];k=names.index('L_Wrist_x');main=[names.index(n) for n in i1['main_control_joint_names']];base=np.array(i0['preserved_absolute_targets_rad'],dtype=np.float32);other=[j for j in range(81) if j!=k];lo=np.array(i1['PD_properties']['lower']);hi=np.array(i1['PD_properties']['upper']);q0=np.array(i1['initial_PD_target_rad']);pre=read(PHASE/'preflight.json')['commands'];updates=[r for r in controls if r['updated_before_step']]
    fields=('native_initial_state','initial_PD_target_rad','preserved_absolute_targets_rad','PD_properties','physics_parameters','absolute_strap_rest_length_m','initial_route_length_m','guitar_goal_position_W_m','guitar_goal_quaternion_xyzw','main_control_joint_names','strap_law_parameters')
    initial_checks={f:i0[f]==i1[f] for f in fields}
    checks=dict(completed_1200step_two151frame=report['completed'] and report['failure'] is None and report['physics_steps']==1200 and len(s1)==len(t1)==1201 and len(cap['frames'])==151 and len(report['videos'])==2,all_native_checks=all(report['checks'].values()),same_initial_and_PD=all(initial_checks.values()),first_four_physics_steps_exact=s0[:5]==s1[:5],all300_commands_match_preflight=len(updates)==300 and all(r['command_time_s']==p['command_time_s'] and abs(r['wrist_motion_delta_rad']-p['delta_rad'])<1e-15 and r['final_target_rad'][k]==p['wrist_target_rad'] for r,p in zip(updates,pre)),other80_targets_exact=all(np.array_equal(np.array(r['final_target_rad'])[other],base[other]) for r in controls),all_targets_model_and_offset_bounds=all(np.all(np.array(r['final_target_rad'])>=lo) and np.all(np.array(r['final_target_rad'])<=hi) and np.all(abs((np.array(r['final_target_rad'])-q0)[main])<=.3) for r in controls),all_render_preserves_states=all(f['render_preserves_states'] for f in cap['frames']),capture_steps_complete=all(f['physics_step']==j*8 and f['time_s']==j/30 for j,f in enumerate(cap['frames'])))
    actual=np.array([s['human_dof_states'][k]['pos'] for s in s1]);static=np.array([s['human_dof_states'][k]['pos'] for s in s0]);difference=actual-static;times=np.array([r['time_s'] for r in t1]);late=times>=2;design=np.column_stack((np.ones(late.sum()),times[late]-2,np.sin(2*np.pi*times[late]),np.cos(2*np.pi*times[late])));fit=np.linalg.lstsq(design,difference[late],rcond=None)[0];amplitude=float(np.hypot(fit[2],fit[3]));residual=difference[late]-design@fit
    body=i1['human_body_names'].index('LH:palm');p0=np.array([position(s['human_body_states'][body]) for s in s0]);p1=np.array([position(s['human_body_states'][body]) for s in s1]);r0=np.array([quaternion(s['human_body_states'][body]) for s in s0]);r1=np.array([quaternion(s['human_body_states'][body]) for s in s1]);g0=np.array([r['guitar_position_m'] for r in t0]);g1=np.array([r['guitar_position_m'] for r in t1]);motion=dict(command_amplitude_rad=.005,actual_coordinate_response_1Hz_amplitude_rad=amplitude,actual_coordinate_response_1Hz_amplitude_deg=float(np.degrees(amplitude)),actual_minus_static_coordinate_peak_to_peak_rad=float(np.ptp(difference[late])),fit_rms_residual_rad=float(np.sqrt(np.mean(residual**2))),max_palm_origin_difference_from_static_mm=float(np.linalg.norm(p1[late]-p0[late],axis=1).max()*1000),max_palm_world_rotation_difference_from_static_deg=float(rotation_difference(r1[late],r0[late]).max()),max_guitar_position_difference_from_static_mm=float(np.linalg.norm(g1[late]-g0[late],axis=1).max()*1000))
    contacts=lines(current/'contacts.jsonl');palm=[];human_self=[]
    for row in contacts:
        for c in row['contacts']:
            pair=(c['body0_name'],c['body1_name'])
            if 'human/LH:palm' in pair and any(n.startswith('guitar/') for n in pair) and c['lambda']>0:palm.append(row['physics_step'])
            if all(n.startswith('human/') for n in pair):human_self.append(row['physics_step'])
    motion['palm_guitar_positive_raw_lambda_steps']=len(set(palm));motion['human_self_contact_steps']=len(set(human_self))
    checks['actual_wrist_response_nonzero']=amplitude>1e-6
    for f in cap['frames']:
        for key in ('image_sha256','raw_image_sha256'):
            for path,value in f[key].items():assert sha(path)==value
    checks['all604_recorded_image_SHA_exact']=True
    checks['inputs_unchanged']=all(sha(p)==h for p,h in inputs.items());assert all(checks.values()),checks
    out.write_text(json.dumps(dict(checks=checks,input_sha256=inputs,initial_exact_fields=initial_checks,baseline=metrics(t0),motion_trial=metrics(t1),motion_response=motion,new_native_initializations=1,new_physics_steps=1200,scope='native small single-wrist motion, no guitar residual; coordinate response and actual palm poses kept distinct; practical quiet baseline comparison, not full playing robustness/initial-G restoration or whole-hand grip certification'),indent=2)+'\n')
    print(json.dumps(dict(checks=checks,baseline=metrics(t0),motion_trial=metrics(t1),motion_response=motion),indent=2))


if __name__=='__main__':main()
