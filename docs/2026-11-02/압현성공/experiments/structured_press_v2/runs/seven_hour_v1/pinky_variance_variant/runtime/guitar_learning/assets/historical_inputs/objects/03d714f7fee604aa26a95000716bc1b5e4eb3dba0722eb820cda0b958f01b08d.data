"""Verify a fresh five-second heldout and compare it with sealed probe predictions."""
import hashlib
import json
import math
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PHASE=ROOT/'docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def finite_numbers(value):
    if isinstance(value,dict):return all(finite_numbers(v) for v in value.values())
    if isinstance(value,list):return all(finite_numbers(v) for v in value)
    return not isinstance(value,(int,float)) or math.isfinite(value)


def main():
    output=PHASE/'heldout_analysis.json'
    if output.exists():raise FileExistsError('preserve earlier heldout analysis')
    folder=PHASE/'native/heldout'; hashes={}
    metadata={}
    for n in ('report','capture','initial_values','initial_grip_audit'):
        p=folder/(n+'.json');hashes[str(p)]=sha(p);metadata[n]=read(p)
    report=metadata['report']; capture=metadata['capture']; init=metadata['initial_values']; admission=metadata['initial_grip_audit']
    paths=[Path(__file__).resolve(),ROOT/'stability_adapter_2/analyze_seed2_guitar_response.py',PHASE/'heldout_execution.json',PHASE/'environment.json',PHASE/'probe_analysis.json',PHASE/'heldout_selection.json',PHASE/'heldout_proposal.json',folder/'videos.json']
    paths += [Path(p) for p in report['input_sha256']]+[folder/(n+'.jsonl') for n in ('states','trace','tasks','contacts','controls')]
    paths += [Path(p) for f in capture['frames'] for p in f['image_sha256']]+[Path(v['path']) for v in report['videos'].values()]
    hashes.update({str(p):sha(p) for p in paths})
    probe=read(PHASE/'probe_analysis.json'); selection=read(PHASE/'heldout_selection.json'); proposal=read(PHASE/'heldout_proposal.json')
    for source in (report,probe,selection,proposal):
        if not all(source['checks'].values()) or any(sha(p)!=h for p,h in source['input_sha256'].items()):raise AssertionError('source checks/closure')
    from .environment import np
    from .build_fixed_lower_asset import pose
    from .strap import cable_forces
    from scipy.spatial.transform import Rotation
    base_init=read(PHASE/'native/base/initial_values.json')
    raw={n:[json.loads(line) for line in (folder/(n+'.jsonl')).read_text().splitlines()] for n in ('states','trace','tasks','contacts','controls')}
    if not all(finite_numbers(v) for v in (raw,metadata,selection)) or not report['completed'] or report['physics_steps']!=1200 or not all(admission['checks'].values()):raise AssertionError('finite completed heldout/admission')
    if any(len(raw[n])!=1201 for n in ('states','trace','tasks')) or any(len(raw[n])!=1200 for n in ('contacts','controls')):raise AssertionError('continuous raw coverage')
    if raw['states'][0]!=base_init['native_initial_state'] or raw['states'][0]!=init['native_initial_state']:raise AssertionError('same actual initial81q/G/body state')
    for field in ('human_joint_names','PD_properties','physics_parameters','guitar_goal_position_W_m','guitar_goal_quaternion_xyzw','absolute_strap_rest_length_m','initial_route_length_m','strap_law_parameters','initial_PD_target_rad'):
        if init[field]!=base_init[field]:raise AssertionError('same initial '+field)
    bias=proposal['support_bias_rad']; residual=selection['requested_residual_rad']; row=proposal['rows'][0]
    if row['target_residual_rad']!=residual or init['declared_target_residual_rad']!=residual or init['declared_support_bias_rad']!=bias or init['input_trial']['main_target_offsets_rad']!={n:v+residual.get(n,0.) for n,v in bias.items()}:raise AssertionError('declared exact heldout target')
    if {**init['input_trial'],'main_target_offsets_rad':bias}!=base_init['input_trial']:raise AssertionError('only residual input changes')
    axes=selection['axes'];names=init['human_joint_names'];arm=[i for i,n in enumerate(names) if n in bias]
    if axes!=[f'L_{joint}_{a}' for joint in ('Shoulder','Wrist') for a in 'xyz'] or len(arm)!=12 or any(abs(v)>.001 for v in residual.values()):raise AssertionError('sixaxis residual bounds/order')
    q=np.array(init['initial_PD_target_rad'],dtype=np.float32);off=np.array([init['input_trial']['main_target_offsets_rad'].get(n,0.) for n in names],dtype=np.float32)
    expected=q+off;lower=np.array(init['PD_properties']['lower']);upper=np.array(init['PD_properties']['upper'])
    if not np.all((expected>=lower)&(expected<=upper)):raise AssertionError('heldout native clipping')
    submitted=np.array(raw['controls'][0]['final_target_rad'])
    if not np.array_equal(submitted,expected[arm]):raise AssertionError('actual composed target')
    base_control=json.loads((PHASE/'native/base/controls.jsonl').read_text().splitlines()[0]);base_target=np.array(base_control['final_target_rad'])
    actual_delta=[float(submitted[[names[i] for i in arm].index(n)]-base_target[[names[i] for i in arm].index(n)]) for n in axes]
    if actual_delta!=selection['actual_float32_submitted_target_difference_rad']:raise AssertionError('prediction used actual float32 delta')
    if any(s['physics_step']!=i for i,s in enumerate(raw['states'])) or any(t['time_s']!=i/240 for i,t in enumerate(raw['trace'])):raise AssertionError('raw time sequence')
    if any(c['physics_step']!=i+1 or c['updated_before_step']!=(i%4==0) or c['final_target_rad']!=submitted.tolist() for i,c in enumerate(raw['controls'])) or any(c['physics_step']!=i+1 for i,c in enumerate(raw['contacts'])):raise AssertionError('constant controls/contact sequence')
    frames=capture['frames']
    if len(frames)!=151 or set(report['videos'])!={'whole_body','hands'} or any(f['physics_step']!=i*8 or abs(f['time_s']-i/30)>1e-9 or not f['render_preserves_states'] or len(f['image_sha256'])!=2 or {Path(p).parent.name for p in f['image_sha256']}!={'whole_body','hands'} for i,f in enumerate(frames)):raise AssertionError('actual two-view camera coverage')
    if any(sha(p)!=h for f in frames for p,h in f['image_sha256'].items()):raise AssertionError('actual camera hash')
    for v in report['videos'].values():
        proc=subprocess.run(v['ffprobe_command'],capture_output=True,text=True)
        if proc.returncode:raise RuntimeError('ffprobe failed')
        stream=json.loads(proc.stdout)['streams'][0]
        if stream!=v['stream'] or int(stream['nb_read_frames'])!=151 or stream['avg_frame_rate']!='30/1' or abs(float(stream['duration'])-151/30)>.002 or sha(v['path'])!=v['sha256']:raise AssertionError('video bytes/metadata')
    goal_p=np.array(init['guitar_goal_position_W_m']);goal_R=Rotation.from_quat(init['guitar_goal_quaternion_xyzw']);errors=[]
    for state,t in zip(raw['states'],raw['trace']):
        p,gq=pose(state['guitar_body_states'][0]);rot=(Rotation.from_quat(gq)*goal_R.inv()).as_rotvec()
        if not np.array_equal(p,np.array(t['guitar_position_m'])) or not np.allclose(gq/np.linalg.norm(gq),t['guitar_quaternion_xyzw'],rtol=0,atol=1e-15) or abs(np.linalg.norm(p-goal_p)-t['position_error_m'])>1e-12 or abs(np.degrees(np.linalg.norm(rot))-t['rotation_error_deg'])>1e-4:raise AssertionError('state/trace world error')
        errors.append(np.concatenate((p-goal_p,rot)))
    predicted=[cable_forces(np.array(t['route_points_m']),np.array(t['route_point_velocities_mps']),init['absolute_strap_rest_length_m'],6000,120,300)[1] for t in raw['trace'][:-1]]
    applied=[t['last_applied_tension_n'] for t in raw['trace'][1:]]
    law_error=float(np.max(np.abs(np.array(predicted)-applied)))
    if law_error>1e-8 or any(t['strap_rest_length_m']!=init['absolute_strap_rest_length_m'] for t in raw['trace']):raise AssertionError('passive strap law/fixed LA')
    windows={'t0p1':slice(24,25),'t1':slice(240,241),'t5':slice(1200,1201),'last1s_mean':slice(960,1201)};comparisons={}
    for name,w in windows.items():
        actual=np.array(errors)[w].mean(axis=0); pred=np.array(selection['predictions'][name]['predicted_error_W_m_rad']);base=np.array(probe['response_identification']['windows'][name]['baseline_error_W_m_rad']);difference=actual-pred
        comparisons[name]={'actual_error_W_m_rad':actual.tolist(),'predicted_error_W_m_rad':pred.tolist(),'actual_minus_baseline_W_m_rad':(actual-base).tolist(),'prediction_residual_W_m_rad':difference.tolist(),'prediction_residual_position_mm':float(np.linalg.norm(difference[:3])*1000),'prediction_residual_rotation_vector_deg':float(np.degrees(np.linalg.norm(difference[3:]))),'actual_mean_vector_norm_position_mm':float(np.linalg.norm(actual[:3])*1000),'actual_mean_vector_norm_rotation_deg':float(np.degrees(np.linalg.norm(actual[3:])))}
    groups={}
    for contact_row in raw['contacts']:
        for c in contact_row['contacts']:
            a,b=c['body0_name'],c['body1_name'];body=a if a.startswith(('human/LH:','human/RH:')) and b.startswith('guitar/') else b if b.startswith(('human/LH:','human/RH:')) and a.startswith('guitar/') else None
            if body:
                group=groups.setdefault(body,{'rows':0,'positive_rows':0,'last_contact_step':None,'last_positive_step':None});group['rows']+=1;group['last_contact_step']=contact_row['physics_step']
                if c['lambda']>0:group['positive_rows']+=1;group['last_positive_step']=contact_row['physics_step']
    def metrics(end):
        trace=raw['trace'][:end+1];return {'max_guitar_position_error_mm':max(t['position_error_m'] for t in trace)*1000,'max_guitar_rotation_error_deg':max(t['rotation_error_deg'] for t in trace),'end_guitar_position_error_mm':trace[-1]['position_error_m']*1000,'end_guitar_rotation_error_deg':trace[-1]['rotation_error_deg'],'max_actual_torso_coordinate_drift_deg':float(np.max(np.abs([t['torso_drift_deg'] for t in trace])))}
    execution=read(PHASE/'heldout_execution.json')
    checks={'fresh_native_5s_source_FK_contract':True,'same_initial81q_G_LA_PD_only_residual':True,'actual_float32_target_matches_prediction':True,'continuous_raw_two_view_videos':True,'world_SO3_error_matches_trace':True,'previous_state_passive_strap_law':True,'one_exit_zero':execution['exit_code']==0,'inputs_unchanged':all(sha(p)==h for p,h in hashes.items())}
    if not all(checks.values()):raise AssertionError(checks)
    result={'checks':checks,'input_sha256':hashes,'requested_residual_rad':residual,'actual_float32_target_difference_rad':actual_delta,'comparisons':comparisons,'first_0p1s':metrics(24),'full_5s':metrics(1200),'contacts_by_hand_body':groups,'palm_up_proxy_violations':len(report['constraint_violations']),'strap_law_reconstruction_max_error_n':law_error,'curves':{'time_s':[t['time_s'] for t in raw['trace']],'guitar_position_error_mm':[t['position_error_m']*1000 for t in raw['trace']],'guitar_rotation_error_deg':[t['rotation_error_deg'] for t in raw['trace']],'guitar_error_vector_W_m_rad':[e.tolist() for e in errors]},'counts':{'heldout_native_initializations':1,'heldout_physics_steps':1200,'phase_native_initializations':8,'phase_physics_steps':9600},'stability_success':False,'scope':'fresh constant-target heldout; prediction residual is difference of world error vectors, not quaternion distance or mean scalar norm; named-body contact not plane support certification; no runtime feedback or learning'}
    output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('input_sha256','curves')},indent=2))


if __name__=='__main__':main()
