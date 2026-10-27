"""Recompute initial-arm target contracts, coordinate errors and native motion; no new physics."""
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PHASE=ROOT/'docs/2026-10-12/stability_adapter_2/results/three_face_arm_initial_target_v1'
OLD=PHASE.parent/'three_face_support_loss_v1'
KINDS=('states','trace','tasks','contacts','controls')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def lines(p):return [json.loads(s) for s in Path(p).read_text().splitlines()]
def finite(v):
    if isinstance(v,dict):return all(finite(x) for x in v.values())
    if isinstance(v,list):return all(finite(x) for x in v)
    return not isinstance(v,(float,int)) or math.isfinite(v)


def main():
    output=PHASE/'analysis.json'
    if output.exists():raise FileExistsError('preserve previous analysis')
    hashes={}
    def sealed_read(path):
        hashes[str(path)]=sha(path)
        return read(path)
    proposal=sealed_read(PHASE/'proposal.json');execution=sealed_read(PHASE/'execution.json');oldinit=sealed_read(OLD/'native/saved_finger_targets/initial_values.json')
    oldreport=sealed_read(OLD/'native/saved_finger_targets/report.json')
    hashes.update({str(p):sha(p) for p in (Path(__file__).resolve(),PHASE/'environment.json',OLD/'analysis.json')})
    if not all(proposal['checks'].values()) or any(sha(p)!=h for p,h in proposal['input_sha256'].items()):raise AssertionError('proposal original input closure')
    hashes.update(proposal['input_sha256'])
    folders={r['label']:PHASE/'native'/r['label'] for r in proposal['rows']};reports={};captures={}
    for label,folder in folders.items():
        hashes.update({str(p):sha(p) for p in folder.rglob('*') if p.is_file()})
        reports[label]=read(folder/'report.json');captures[label]=read(folder/'capture.json')
        if any(sha(p)!=h for p,h in reports[label]['input_sha256'].items()):raise AssertionError('native original input closure')
        hashes.update(reports[label]['input_sha256'])
    hashes.update({str(OLD/'native/saved_finger_targets'/(n+'.jsonl')):sha(OLD/'native/saved_finger_targets'/(n+'.jsonl')) for n in KINDS})
    oldraw={n:lines(OLD/'native/saved_finger_targets'/(n+'.jsonl')) for n in KINDS}
    from .environment import np
    from .strap import cable_forces
    from .build_fixed_lower_asset import pose,LOWER_BODIES
    from scipy.spatial.transform import Rotation
    import subprocess
    summary=[];curves={};repeat={};qold=np.array(proposal['old_initial_angles_rad'])
    for row in proposal['rows']:
        label=row['label'];targets=np.array(row['expected_absolute_targets_rad']);folder=folders[label];report=reports[label];capture=captures[label];init=read(folder/'initial_values.json');audit=read(folder/'initial_grip_audit.json');raw={n:lines(folder/(n+'.jsonl')) for n in KINDS}
        if not finite([raw,init,report,audit,capture]) or not report['completed'] or not all(report['checks'].values()) or not all(audit['checks'].values()):raise AssertionError('completion/finite/fresh native source FK')
        if report['physics_steps']!=1200 or any(len(raw[n])!=(1201 if n in ('states','trace','tasks') else 1200) for n in KINDS):raise AssertionError('raw 5s coverage')
        names=init['human_joint_names'];left=[names.index(n) for n in proposal['left33_names']];other=np.setdiff1d(np.arange(81),left)
        q=np.array([d['pos'] for d in raw['states'][0]['human_dof_states']]);expected=np.array(row['expected_initial_angles_rad'])
        if len(left)!=33 or len(init['main_control_joint_names'])!=66 or not np.array_equal(q,expected) or not np.array_equal(q[other],qold[other]) or q.tolist()!=init['initial_PD_target_rad']:raise AssertionError('same initial81/left33/other48/final66 contract')
        if not np.all((q>=init['PD_properties']['lower'])&(q<=init['PD_properties']['upper'])):raise AssertionError('native initial bounds')
        for field in ('human_joint_names','PD_properties','physics_parameters','guitar_goal_position_W_m','guitar_goal_quaternion_xyzw','absolute_strap_rest_length_m'):
            if init[field]!=oldinit[field]:raise AssertionError('held field '+field)
        if raw['states'][0]['guitar_body_states']!=oldinit['native_initial_state']['guitar_body_states']:raise AssertionError('same initial G state')
        if any(d['vel']!=0 for d in raw['states'][0]['human_dof_states']):raise AssertionError('initial velocities')
        for i,c in enumerate(raw['controls']):
            if c['physics_step']!=i+1 or c['updated_before_step']!=(i%4==0) or not c['other48_targets_held'] or c['final_target_rad']!=targets.tolist():raise AssertionError('same absolute81 targets 300updates')
        bodyids=[init['human_body_names'].index(n) for n in ('Pelvis',)+LOWER_BODIES]
        for i,(state,trace) in enumerate(zip(raw['states'],raw['trace'])):
            if state['physics_step']!=i or abs(trace['time_s']-i/240)>1e-9 or (i and raw['contacts'][i-1]['physics_step']!=i):raise AssertionError('continuous sequence')
            if any(state['human_body_states'][j]!=raw['states'][0]['human_body_states'][j] for j in bodyids):raise AssertionError('root/lower physical fixation')
            gp,gq=pose(state['guitar_body_states'][0]);rot=(Rotation.from_quat(gq)*Rotation.from_quat(init['guitar_goal_quaternion_xyzw']).inv()).magnitude()
            if abs(np.linalg.norm(gp-init['guitar_goal_position_W_m'])-trace['position_error_m'])>1e-12 or abs(np.degrees(rot)-trace['rotation_error_deg'])>1e-4:raise AssertionError('raw world G error')
        law=init['strap_law_parameters']
        if (law['stiffness_n_per_m'],law['damping_n_s_per_m'],law['max_tension_n'])!=(6000,120,300):raise AssertionError('same passive strap law')
        predicted=[cable_forces(np.array(t['route_points_m']),np.array(t['route_point_velocities_mps']),init['absolute_strap_rest_length_m'],6000,120,300)[1] for t in raw['trace'][:-1]]
        applied=[t['last_applied_tension_n'] for t in raw['trace'][1:]];lawerror=float(np.max(np.abs(np.array(predicted)-applied)))
        if lawerror>1e-8 or any(t['strap_rest_length_m']!=init['absolute_strap_rest_length_m'] for t in raw['trace']):raise AssertionError('prestep strap law / LA')
        frames=capture['frames']
        if len(frames)!=151 or set(report['videos'])!={'hands','whole_body'} or any(f['physics_step']!=i*8 or abs(f['time_s']-i/30)>1e-9 or not f['render_preserves_states'] or len(f['image_sha256'])!=2 or {Path(p).parent.name for p in f['image_sha256']}!={'hands','whole_body'} or any(sha(p)!=h for p,h in f['image_sha256'].items()) for i,f in enumerate(frames)):raise AssertionError('actual cameras 0..5s')
        for video in report['videos'].values():
            proc=subprocess.run(video['ffprobe_command'],capture_output=True,text=True,check=True);stream=json.loads(proc.stdout)['streams'][0]
            if stream!=video['stream'] or int(stream['nb_read_frames'])!=151 or stream['avg_frame_rate']!='30/1' or abs(float(stream['duration'])-151/30)>.002 or sha(video['path'])!=video['sha256']:raise AssertionError('video hash/metadata')
        groups={}
        for record in raw['contacts']:
            for c in record['contacts']:
                a,b=c['body0_name'],c['body1_name'];body=a if b.startswith('guitar/') and not a.startswith('guitar/') else b if a.startswith('guitar/') and not b.startswith('guitar/') else None
                if not body:continue
                g=groups.setdefault(body,{'rows':0,'positive_rows':0,'positive_steps':set(),'last_contact_step':None});g['rows']+=1;g['last_contact_step']=record['physics_step']
                if c['lambda']>0:g['positive_rows']+=1;g['positive_steps'].add(record['physics_step'])
        for g in groups.values():g['positive_step_count']=len(g['positive_steps']);g['last_positive_step']=max(g['positive_steps'],default=None);g['positive_steps']=sorted(g['positive_steps'])
        coords=np.array([[d['pos'] for d in state['human_dof_states']] for state in raw['states']]);drift=coords[:,left]-q[left];target_error=coords-targets
        groups_by_indices={'arm12':[names.index(n) for n in proposal['arm12_names']],'finger21':[names.index(n) for n in proposal['finger21_names']],'torso9':[i for i,n in enumerate(names) if any(n.startswith(k+'_') for k in ('Torso','Spine','Chest'))]}
        def metrics(start,end):
            ts=raw['trace'][start:end+1]
            return {'max_guitar_position_error_mm':max(t['position_error_m'] for t in ts)*1000,'max_guitar_rotation_error_deg':max(t['rotation_error_deg'] for t in ts),'end_guitar_position_error_mm':ts[-1]['position_error_m']*1000,'end_guitar_rotation_error_deg':ts[-1]['rotation_error_deg'],'max_actual_torso_coordinate_drift_deg':float(np.abs([t['torso_drift_deg'] for t in ts]).max()),'max_actual_left33_coordinate_drift_deg':float(np.max(np.abs(drift[start:end+1]))*180/np.pi),'max_abs_target_coordinate_error_deg':{k:float(np.max(np.abs(target_error[start:end+1,ids]))*180/np.pi) for k,ids in groups_by_indices.items()},'end_abs_target_coordinate_error_deg':{k:float(np.max(np.abs(target_error[end,ids]))*180/np.pi) for k,ids in groups_by_indices.items()}}
        summary.append({'label':label,'alpha':row['alpha'],'first_0p1s':metrics(0,24),'full_5s':metrics(0,1200),'last1s':metrics(960,1200),'initial_hull_gap_mm':{n:g['distance_m']*1000 for n,g in audit['source_hull_to_faces'].items()},'three_face_initial_source_approach_satisfied':audit['three_face_source_approach_satisfied'],'contacts_by_any_other_body':groups,'strap':{'absolute_rest_length_m':init['absolute_strap_rest_length_m'],'initial_route_length_m':init['initial_route_length_m'],'law_reconstruction_max_error_n':lawerror,'max_submitted_law_tension_n':max(applied)},'palm_up_proxy_violations':len(report['constraint_violations']),'max_FK_position_error_mm':audit['max_FK_position_error_m']*1000,'max_FK_rotation_error_rad':audit['max_FK_rotation_error_rad'],'stability_success':False})
        curves[label]={'time_s':[t['time_s'] for t in raw['trace']],'guitar_position_error_mm':[t['position_error_m']*1000 for t in raw['trace']],'guitar_rotation_error_deg':[t['rotation_error_deg'] for t in raw['trace']],'max_actual_left33_coordinate_drift_deg':(np.max(np.abs(drift),axis=1)*180/np.pi).tolist(),'max_abs_target_coordinate_error_deg':{k:(np.max(np.abs(target_error[:,ids]),axis=1)*180/np.pi).tolist() for k,ids in groups_by_indices.items()}}
        repeat[label]={'raw_arrays_exact':{n:raw[n]==oldraw[n] for n in KINDS},'video_exact':{view:report['videos'][view]['sha256']==oldreport['videos'][view]['sha256'] for view in report['videos']},'controls_schema_changed':False,'scope':'comparison with stored reference; equality flags are observations, not admission/performance gates'}
    before=np.array(proposal['rows'][0]['expected_absolute_targets_rad']);after=np.array(proposal['rows'][1]['expected_absolute_targets_rad']);finger=[oldinit['human_joint_names'].index(n) for n in proposal['finger21_names']];nonfinger=np.setdiff1d(np.arange(81),finger)
    arm=[oldinit['human_joint_names'].index(n) for n in proposal['arm12_names']]
    if len(finger)!=21 or len(arm)!=12 or not np.array_equal(before[nonfinger],after[nonfinger]) or not np.array_equal(after[finger],qold[finger]) or not np.array_equal(before[arm],qold[arm]) or not np.array_equal(after[arm],qold[arm]):raise AssertionError('both arm12 match actualinitial and only finger21 changes between new rows')
    reference_metrics={key:{'max_guitar_position_error_mm':max(t['position_error_m'] for t in oldraw['trace'][start:end+1])*1000,'max_guitar_rotation_error_deg':max(t['rotation_error_deg'] for t in oldraw['trace'][start:end+1]),'end_guitar_position_error_mm':oldraw['trace'][end]['position_error_m']*1000,'end_guitar_rotation_error_deg':oldraw['trace'][end]['rotation_error_deg']} for key,start,end in [('first_0p1s',0,24),('full_5s',0,1200),('last1s',960,1200)]}
    checks={'source_and_fresh_native_admission':True,'same_native_initial81_and_final66':True,'row_targets300updates_both_arm12_match_initial_only_finger21_differ':True,'raw_G_errors_root_lower_PD_LA_and_passive_law':True,'actual_5s_both_cameras':True,'executions_exit_zero':len(execution)==len(folders) and all(e['exit_code']==0 for e in execution),'inputs_unchanged':all(sha(p)==h for p,h in hashes.items())}
    if not all(checks.values()):raise AssertionError(checks)
    output.write_text(json.dumps({'checks':checks,'input_sha256':hashes,'summary':summary,'curves':curves,'stored_reference_comparisons':repeat,'stored_reference_metrics':reference_metrics,'stored_reference_curves':{'time_s':[t['time_s'] for t in oldraw['trace']],'guitar_position_error_mm':[t['position_error_m']*1000 for t in oldraw['trace']],'guitar_rotation_error_deg':[t['rotation_error_deg'] for t in oldraw['trace']]},'source_rejected_candidates':proposal['rejected'],'counts':{'native_initializations':len(folders),'physics_steps':1200*len(folders)},'scope':'same initial81 and PD/G/LA; both new arm12 targets match initial; onlyfinger21 differ; prior completed reference is not new native count; target errors at t0 use planned first submission and afterstep1 logged constant targets, scalar notSO3; source gap is not cooked clearance; body contact and raw lambda do not certify neck face or continuous support; no stability success'},indent=2,allow_nan=False)+'\n');print(json.dumps({'checks':checks,'summary':[{k:r[k] for k in ('label','alpha','first_0p1s','full_5s')} for r in summary],'stored_reference_comparisons':repeat},indent=2),flush=True)


if __name__=='__main__':main()
