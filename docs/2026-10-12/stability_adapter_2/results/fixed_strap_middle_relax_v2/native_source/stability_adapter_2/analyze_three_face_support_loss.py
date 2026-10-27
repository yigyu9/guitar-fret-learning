"""Analyze recorded actual poses and one read-only shape-property repeat; no native init."""
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'docs/2026-10-12/stability_adapter_2/results'
OLD=BASE/'three_face_finger_target_hold_v1'
PHASE=BASE/'three_face_support_loss_v1'
STEPS=(0,24,60,120,240,1200)
KINDS=('states','trace','tasks','contacts','controls')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def lines(p):return [json.loads(s) for s in Path(p).read_text().splitlines()]
def save(p,v):Path(p).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def finite(v):
    if isinstance(v,dict):return all(finite(x) for x in v.values())
    if isinstance(v,list):return all(finite(x) for x in v)
    return not isinstance(v,(float,int)) or math.isfinite(v)


def main():
    output=PHASE/'analysis.json'
    if output.exists():raise FileExistsError('preserve previous analysis')
    hashes={}
    def sealed(path):
        hashes[str(path)]=sha(path)
        return read(path)
    previous=sealed(OLD/'analysis.json');proposal=sealed(OLD/'proposal.json');sealed(OLD/'final_verification.json')
    if not all(previous['checks'].values()) or any(sha(p)!=h for p,h in previous['input_sha256'].items()):raise AssertionError('previous input closure')
    hashes.update(previous['input_sha256'])
    folder=PHASE/'native/saved_finger_targets'
    hashes.update({str(p):sha(p) for p in folder.rglob('*') if p.is_file()})
    report=read(folder/'report.json');init=read(folder/'initial_values.json');shapes=read(folder/'shape_properties.json');execution=sealed(PHASE/'execution.json')
    if not report['completed'] or not all(report['checks'].values()) or not all(read(folder/'initial_grip_audit.json')['checks'].values()):raise AssertionError('completed native readback/admission')
    if any(sha(p)!=h for p,h in report['input_sha256'].items()):raise AssertionError('native original input closure')
    hashes.update(report['input_sha256'])
    proxy_path=BASE/'palm_neck_side_v1/initial_audit_v2/audit.json';proxy_data=sealed(proxy_path)
    helpers=('face_referenced_geometry.py','plot_neck_palm.py','initial_overlap.py','audit_palm_side_target.py','search_multi_face_grip.py','build_fixed_lower_asset.py','strap.py','config.json','THREE_FACE_SUPPORT_LOSS_DIAGNOSTIC_PLAN.md')
    hashes.update({str(ROOT/'stability_adapter_2'/n):sha(ROOT/'stability_adapter_2'/n) for n in helpers})
    hashes[str(Path(__file__).resolve())]=sha(__file__)
    from .environment import np
    from .build_fixed_lower_asset import ASSET,pose,LOWER_BODIES
    from .initial_overlap import build_probe
    from .face_referenced_geometry import face_geometry
    from .audit_palm_side_target import closest_polygon
    from .search_multi_face_grip import nearest_face
    from .strap import cable_forces
    from scipy.spatial.transform import Rotation
    import subprocess
    config=read(ROOT/'stability_adapter_2/config.json');config['humanoid_asset']=str(ASSET)
    if str(ASSET) not in hashes:raise AssertionError('fixed lower source asset not sealed')
    raw={n:lines(folder/(n+'.jsonl')) for n in KINDS}
    if not finite([raw,init,report,shapes]):raise AssertionError('finite fresh raw/metadata')
    baseline={n:lines(OLD/'native/saved_finger_targets'/(n+'.jsonl')) for n in KINDS}
    if report['physics_steps']!=1200 or any(len(raw[n])!=(1201 if n in ('states','trace','tasks') else 1200) for n in KINDS):raise AssertionError('full 5s coverage')
    oldinit=read(OLD/'native/saved_finger_targets/initial_values.json')
    held_fields=('human_joint_names','human_body_names','main_control_joint_names','initial_PD_target_rad','native_initial_state','preserved_absolute_targets_rad','PD_properties','physics_parameters','guitar_goal_position_W_m','guitar_goal_quaternion_xyzw','absolute_strap_rest_length_m','initial_route_length_m','input_trial')
    if any(init[k]!=oldinit[k] for k in held_fields):raise AssertionError('same initial state and control/physics settings')
    targets=init['preserved_absolute_targets_rad'];fixed=[init['human_body_names'].index(n) for n in ('Pelvis',)+LOWER_BODIES]
    for i,state in enumerate(raw['states']):
        if state['physics_step']!=i or any(state['human_body_states'][j]!=raw['states'][0]['human_body_states'][j] for j in fixed):raise AssertionError('fixed root/lower/sequence')
        gp,gq=pose(state['guitar_body_states'][0]);trace=raw['trace'][i]
        if abs(np.linalg.norm(gp-init['guitar_goal_position_W_m'])-trace['position_error_m'])>1e-12 or abs(np.degrees((Rotation.from_quat(gq)*Rotation.from_quat(init['guitar_goal_quaternion_xyzw']).inv()).magnitude())-trace['rotation_error_deg'])>1e-4:raise AssertionError('raw G p/q error')
    for i,c in enumerate(raw['controls']):
        if c['physics_step']!=i+1 or c['final_target_rad']!=targets or c['updated_before_step']!=(i%4==0):raise AssertionError('absolute targets/300updates')
    law=init['strap_law_parameters'];predicted=[cable_forces(np.array(t['route_points_m']),np.array(t['route_point_velocities_mps']),init['absolute_strap_rest_length_m'],law['stiffness_n_per_m'],law['damping_n_s_per_m'],law['max_tension_n'])[1] for t in raw['trace'][:-1]]
    lawerror=float(np.max(np.abs(np.array(predicted)-[t['last_applied_tension_n'] for t in raw['trace'][1:]])))
    if lawerror>1e-8 or any(t['strap_rest_length_m']!=init['absolute_strap_rest_length_m'] for t in raw['trace']):raise AssertionError('passive strap law')
    capture=read(folder/'capture.json')
    if len(capture['frames'])!=151 or any(f['physics_step']!=i*8 or not f['render_preserves_states'] or any(sha(p)!=h for p,h in f['image_sha256'].items()) for i,f in enumerate(capture['frames'])):raise AssertionError('actual frame coverage/hash')
    for video in report['videos'].values():
        stream=json.loads(subprocess.check_output(video['ffprobe_command'],text=True))['streams'][0]
        if stream!=video['stream'] or int(stream['nb_read_frames'])!=151 or stream['avg_frame_rate']!='30/1' or abs(float(stream['duration'])-151/30)>.002 or sha(video['path'])!=video['sha256']:raise AssertionError('video metadata/hash')
    guitar_names=[r['body'] for r in shapes['actors']['guitar']['body_ranges']]
    rows=[];geometry=[];proxy=np.array(proxy_data['palmar_normal_proxy_local'])
    for row in proposal['rows']:
        label=row['label'];run=OLD/'native'/label;initial=read(run/'initial_values.json');states=lines(run/'states.jsonl');controls=lines(run/'controls.jsonl');names=initial['human_joint_names'];body_names=initial['human_body_names']
        finger=[i for i,n in enumerate(names) if n.startswith('LH:')];arm=[names.index(n) for n in initial['left33_names'] if not n.startswith('LH:')];torso=[i for i,n in enumerate(names) if any(n.startswith(k+'_') for k in ('Torso','Spine','Chest'))]
        if (len(finger),len(arm),len(torso))!=(21,12,9):raise AssertionError('finger/arm/torso groups')
        for step in STEPS:
            state=states[step];target=np.array(initial['preserved_absolute_targets_rad'] if step==0 else controls[step-1]['final_target_rad']);q=np.array([d['pos'] for d in state['human_dof_states']]);gp,gq=pose(state['guitar_body_states'][0]);gr=Rotation.from_quat(gq)
            scene=SimpleNamespace(config=config,human=0,guitar=1,env=None,gym=SimpleNamespace(get_actor_rigid_body_names=lambda env,actor:body_names if actor==0 else guitar_names),bodies=lambda actor:state['human_body_states'] if actor==0 else state['guitar_body_states'])
            model,data,source_shapes=build_probe(scene);metrics={};meshes={}
            for name,facet in proposal['facets'].items():
                shape=next(s for s in source_shapes if s['actor']=='human' and s['body']==name);mesh=face_geometry(model,data,shape);face='palm' if name=='LH:palm' else 'thumb' if name=='LH:thumb3' else 'front';poly=np.array(proposal['regions_G_m'][face]);poly[:,2]=proposal['front_outer_source_z_G_m'] if face=='front' else poly[:,2]
                gap=closest_polygon(mesh,gr.apply(poly)+gp);p,bq=pose(state['human_body_states'][body_names.index(name)]);br=Rotation.from_quat(bq);point=gr.inv().apply(p+br.apply(facet['point_local_m'])-gp);nearest,normal=nearest_face(point,face,proposal['front_outer_source_z_G_m'],row['target_clearance_m'],proposal['regions_G_m']);direction=gr.inv().apply(br.apply(facet['normal_local']))
                metrics[name]={'face':face,'hull_gap_m':gap['distance_m'],'QP_feasibility_error_m':gap['feasibility_error_m'],'facet_point_G_m':point.tolist(),'facet_distance_to_offset_patch_m':float(np.linalg.norm(point-nearest)),'inward_alignment_dot':float(direction@-normal),'hull_witness_G_m':gr.inv().apply(np.array(gap['palm_witness_world_m'])-gp).tolist(),'patch_witness_G_m':gr.inv().apply(np.array(gap['target_witness_world_m'])-gp).tolist()}
                meshes[name]={'vertices_G_m':gr.inv().apply(mesh.vertices-gp).tolist(),'faces':mesh.faces.tolist()}
                if step==0 and abs(gap['distance_m']-read(run/'initial_grip_audit.json')['source_hull_to_faces'][name]['distance_m'])>1e-6:raise AssertionError('t0 QP matches initial audit within1um')
            palm_q=pose(state['human_body_states'][body_names.index('LH:palm')])[1];error=q-target
            rows.append({'label':label,'physics_step':step,'time_s':step/240,'metrics':metrics,'palm_up_proxy_z':float(Rotation.from_quat(palm_q).apply(proxy)[2]),'coordinate_error_rad':{n:float(error[i]) for i,n in enumerate(names)},'max_abs_coordinate_error_rad':{key:float(np.abs(error[ids]).max()) for key,ids in [('finger21',finger),('left_arm12',arm),('torso9',torso)]},'target_scope':'planned first target before step1 submission' if step==0 else 'actual logged target submitted before this step'})
            geometry.append({'label':label,'physics_step':step,'hand_hulls':meshes})
    materials={}
    for actor,data in shapes['actors'].items():
        ranges=data['body_ranges'];properties=data['shape_properties'];ids=[i for r in ranges for i in r['shape_indices']]
        if sorted(ids)!=list(range(data['shape_count'])) or any(not math.isfinite(v) for p in properties for v in p.values()):raise AssertionError('shape map/finite properties')
        materials[actor]={field:sorted(set(p[field] for p in properties)) for field in properties[0]}
    repeat={'raw_arrays_exact':{n:raw[n]==baseline[n] for n in KINDS},'video_SHA_exact':{view:report['videos'][view]['sha256']==read(OLD/'native/saved_finger_targets/report.json')['videos'][view]['sha256'] for view in report['videos']},'scope':'observed reproducibility, not an admission or performance gate'}
    checks={'saved_actual_pose_geometry12_samples6_bodies':len(rows)==12 and all(len(r['metrics'])==6 for r in rows),'initial_QP_matches_saved_audit':True,'native_same_initial81_targets_PD_physics_and_LA':True,'fresh5s_root_lower_targets_strap_and_video_contract':True,'shape_queries_preserve_state_PD_and_Python_target':shapes['queries_preserve_state_target_and_PD'],'execution_exit_zero_source_unchanged':execution['exit_code']==0 and execution['runner_sha256_before']==execution['runner_sha256_after']==sha(ROOT/'stability_adapter_2/run_three_face_shape_readback.py'),'inputs_unchanged':all(sha(p)==h for p,h in hashes.items())}
    if not all(checks.values()):raise AssertionError(checks)
    save(output,{'checks':checks,'input_sha256':hashes,'rows':rows,'geometry':geometry,'regions_G_m':proposal['regions_G_m'],'front_outer_source_z_G_m':proposal['front_outer_source_z_G_m'],'native_shape_properties':shapes,'material_unique_values':materials,'fresh_repeat':repeat,'fresh_strap_law_max_error_n':lawerror,'counts':{'native_initializations':1,'physics_steps':1200,'offline_actual_pose_samples':12},'scope':'saved actual poses placed in CPU source geometry, not a native replay; hull distances/facets are not cooked clearance, anatomical pads or rear/front/side contact certification; scalar coordinate errors are not SO3; readback9fields includes backend-specific fields; no changed gains/angles/materials/strap or stability success'})
    print(json.dumps({'checks':checks,'material_unique_values':materials,'fresh_repeat':repeat,'selected_palm_gaps_mm':[dict(label=r['label'],time_s=r['time_s'],palm_gap_mm=r['metrics']['LH:palm']['hull_gap_m']*1000) for r in rows]},indent=2),flush=True)


if __name__=='__main__':main()
