"""Verify actual near-contact native trials and compare finger targets; no new physics."""
import hashlib,json,math,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PHASE=ROOT/'docs/2026-10-12/stability_adapter_2/results/three_face_near_contact_diagnostic_v1'
KINDS=('states','trace','tasks','contacts','controls')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def lines(p):return [json.loads(v) for v in Path(p).read_text().splitlines()]
def finite(v):
    if isinstance(v,dict):return all(finite(x) for x in v.values())
    if isinstance(v,list):return all(finite(x) for x in v)
    return not isinstance(v,(int,float)) or math.isfinite(v)
def main():
    out=PHASE/'analysis_v2.json';assert not out.exists()
    inputs={str(p):sha(p) for p in (PHASE/'native').rglob('*') if p.is_file()}
    for name in ('proposal.json','root_native_preflight.json','native_execution_producer.py','original_targets_native_execution.json','initial_finger_targets_native_execution.json','completed_source_row_snapshot.json','source_snapshot_provenance.json'):
        inputs[str(PHASE/name)]=sha(PHASE/name)
    inputs.update({str(Path(__file__).resolve()):sha(__file__),str(ROOT/'stability_adapter_2/NEAR_CONTACT_RESULT_ANALYSIS_PLAN.md'):sha(ROOT/'stability_adapter_2/NEAR_CONTACT_RESULT_ANALYSIS_PLAN.md')})
    proposal=read(PHASE/'proposal.json');assert all(proposal['checks'].values())
    inputs.update(proposal['input_sha256']);assert all(sha(p)==h for p,h in inputs.items())
    from .environment import np
    from .build_fixed_lower_asset import pose,LOWER_BODIES
    from .strap import cable_forces
    from scipy.spatial.transform import Rotation
    summary=[];curves={};raw_by_label={};inits=[]
    for row in proposal['rows']:
        label=row['label'];folder=PHASE/'native'/label
        report=read(folder/'report.json');capture=read(folder/'capture.json');init=read(folder/'initial_values.json');audit=read(folder/'initial_grip_audit.json');execution=read(PHASE/f'{label}_native_execution.json')
        assert report['completed'] and report['diagnostic_only'] and report['source_support_search_passed'] is False and execution['exit_code']==0
        assert all(report['checks'].values()) and all(audit['checks'].values()) and all(sha(p)==h for p,h in report['input_sha256'].items())
        inputs.update(report['input_sha256']);raw={n:lines(folder/f'{n}.jsonl') for n in KINDS};assert finite([raw,init,report,audit])
        assert report['physics_steps']==1200 and report['simulation_elapsed_s']==5 and all(len(raw[n])==(1201 if n in ('states','trace','tasks') else 1200) for n in KINDS)
        names=init['human_joint_names'];q=np.array([d['pos'] for d in raw['states'][0]['human_dof_states']]);targets=np.array(row['expected_absolute_targets_rad']);left=[names.index(n) for n in proposal['left33_names']];other=np.setdiff1d(np.arange(81),left)
        assert np.array_equal(q,row['expected_initial_angles_rad']) and q.tolist()==init['initial_PD_target_rad'] and len(init['main_control_joint_names'])==66
        assert np.all(q>=init['PD_properties']['lower']) and np.all(q<=init['PD_properties']['upper']) and all(d['vel']==0 for d in raw['states'][0]['human_dof_states'])
        assert all(c['physics_step']==i+1 and c['updated_before_step']==(i%4==0) and c['other48_targets_held'] and c['final_target_rad']==targets.tolist() for i,c in enumerate(raw['controls']))
        assert np.array_equal(targets[other],q[other])
        ids=[init['human_body_names'].index(n) for n in ('Pelvis',)+LOWER_BODIES];initial=raw['states'][0]
        for i,(state,t) in enumerate(zip(raw['states'],raw['trace'])):
            assert state['physics_step']==i and abs(t['time_s']-i/240)<1e-9 and (not i or raw['contacts'][i-1]['physics_step']==i)
            assert all(state['human_body_states'][j]==initial['human_body_states'][j] for j in ids)
            gp,gq=pose(state['guitar_body_states'][0]);angle=np.degrees((Rotation.from_quat(gq)*Rotation.from_quat(init['guitar_goal_quaternion_xyzw']).inv()).magnitude())
            assert abs(np.linalg.norm(gp-init['guitar_goal_position_W_m'])-t['position_error_m'])<1e-12 and abs(angle-t['rotation_error_deg'])<1e-4
        law=init['strap_law_parameters'];assert (law['stiffness_n_per_m'],law['damping_n_s_per_m'],law['max_tension_n'])==(6000,120,300)
        predicted=[cable_forces(np.array(t['route_points_m']),np.array(t['route_point_velocities_mps']),init['absolute_strap_rest_length_m'],6000,120,300)[1] for t in raw['trace'][:-1]]
        applied=np.array([t['last_applied_tension_n'] for t in raw['trace'][1:]]);lawerror=float(np.max(np.abs(predicted-applied)));assert lawerror<1e-8
        assert all(t['strap_rest_length_m']==init['absolute_strap_rest_length_m'] for t in raw['trace'])
        frames=capture['frames'];assert len(frames)==151 and set(report['videos'])=={'hands','whole_body'}
        assert all(f['physics_step']==i*8 and abs(f['time_s']-i/30)<1e-9 and f['render_preserves_states'] and len(f['image_sha256'])==2 and all(sha(p)==h for p,h in f['image_sha256'].items()) for i,f in enumerate(frames))
        for video in report['videos'].values():
            stream=json.loads(subprocess.run(video['ffprobe_command'],capture_output=True,text=True,check=True).stdout)['streams'][0]
            assert stream==video['stream'] and int(stream['nb_read_frames'])==151 and stream['avg_frame_rate']=='30/1' and abs(float(stream['duration'])-151/30)<.002 and sha(video['path'])==video['sha256']
        groups={};crosshand_steps=set()
        for record in raw['contacts']:
            for c in record['contacts']:
                a,b=c['body0_name'],c['body1_name']
                if ('LH:' in a and 'RH:' in b) or ('RH:' in a and 'LH:' in b):crosshand_steps.add(record['physics_step'])
                body=a if b.startswith('guitar/') and not a.startswith('guitar/') else b if a.startswith('guitar/') and not b.startswith('guitar/') else None
                if body is None:continue
                g=groups.setdefault(body,dict(rows=0,positive_rows=0,positive_steps=set(),last_contact_step=None));g['rows']+=1;g['last_contact_step']=record['physics_step']
                if c['lambda']>0:g['positive_rows']+=1;g['positive_steps'].add(record['physics_step'])
        for g in groups.values():g.update(positive_step_count=len(g['positive_steps']),last_positive_step=max(g['positive_steps'],default=None),positive_steps=sorted(g['positive_steps']))
        drift=np.array([[d['pos'] for d in s['human_dof_states']] for s in raw['states']])-q
        def metrics(a,b):
            ts=raw['trace'][a:b+1]
            return dict(max_position_error_mm=max(t['position_error_m'] for t in ts)*1000,max_rotation_error_deg=max(t['rotation_error_deg'] for t in ts),end_position_error_mm=ts[-1]['position_error_m']*1000,end_rotation_error_deg=ts[-1]['rotation_error_deg'],max_torso_coordinate_drift_deg=float(np.max(np.abs([t['torso_drift_deg'] for t in ts]))),max_left33_coordinate_drift_deg=float(np.degrees(np.abs(drift[a:b+1,left]).max())))
        summary.append(dict(label=label,finger_target_policy=row['finger_target_policy'],first_0p1s=metrics(0,24),full_5s=metrics(0,1200),last1s=metrics(960,1200),initial_source_hull_patch_upper_mm={n:v['distance_m']*1000 for n,v in audit['source_hull_to_faces'].items()},initial_source_support_passed=False,contacts_by_human_body=groups,cross_hand_contact_step_count=len(crosshand_steps),palm_up_proxy_violations=len(report['constraint_violations']),strap=dict(absolute_rest_length_m=init['absolute_strap_rest_length_m'],initial_route_length_m=init['initial_route_length_m'],max_law_tension_n=float(applied.max()),end_law_tension_n=float(applied[-1]),law_reconstruction_max_error_n=lawerror),FK_max_position_error_mm=audit['max_FK_position_error_m']*1000,FK_max_rotation_error_rad=audit['max_FK_rotation_error_rad'],stability_success=False))
        curves[label]=dict(time_s=[t['time_s'] for t in raw['trace']],position_error_mm=[t['position_error_m']*1000 for t in raw['trace']],rotation_error_deg=[t['rotation_error_deg'] for t in raw['trace']])
        raw_by_label[label]=raw;inits.append(init)
    for field in ('human_joint_names','PD_properties','physics_parameters','guitar_goal_position_W_m','guitar_goal_quaternion_xyzw','absolute_strap_rest_length_m','native_initial_state','actual_initial_angles_rad'):
        assert inits[0][field]==inits[1][field],field
    finger=[i for i,n in enumerate(inits[0]['human_joint_names']) if n.startswith('LH:')];other=np.setdiff1d(np.arange(81),finger)
    ta,tb=(np.array(r['expected_absolute_targets_rad']) for r in proposal['rows']);q=np.array(proposal['rows'][0]['expected_initial_angles_rad'])
    assert len(finger)==21 and np.array_equal(ta[other],tb[other]) and np.array_equal(tb[finger],q[finger])
    checks=dict(actual_two_fresh5s_1200steps_151frames_both_cameras=True,same_initial81_G_LA_PD_only_finger21_targets_differ=True,absolute81_targets_300updates_other48_held=True,raw_world_G_error_root_lower_fixed_and_passive_law=True,source_support_failure_preserved=True,inputs_unchanged=all(sha(p)==h for p,h in inputs.items()))
    assert all(checks.values())
    out.write_text(json.dumps(dict(checks=checks,input_sha256=inputs,summary=summary,curves=curves,counts=dict(native_initializations=2,physics_steps=2400),independent_review=False,scope='root offline raw verification; source safety admission differs from unmet initial support; body names/raw lambda not face support/force N/cooked penetration certification; no successful grip or stability declared'),indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(checks=checks,summary=[{k:r[k] for k in ('label','full_5s','palm_up_proxy_violations','cross_hand_contact_step_count')} for r in summary]),indent=2))
if __name__=='__main__':main()
