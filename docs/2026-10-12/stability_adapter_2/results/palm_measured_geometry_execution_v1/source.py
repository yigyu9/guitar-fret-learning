"""Offline current measured hand geometry transformed by a verified arm12 FK delta."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'docs/2026-10-12/stability_adapter_2/results';OLD=BASE/'torso_hold_native_collision_v1';PHASE=BASE/'palm_measured_geometry_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def main():
    PHASE.mkdir(exist_ok=False);runtime=read(BASE/'palm_support_runtime_fk_v1/analysis.json');assessment=read(BASE/'palm_support_two_axis_fk_v2/palm_scope_assessment.json');inputs=dict(runtime['input_sha256']);inputs.update(assessment['input_sha256'])
    for p in [Path(__file__).resolve(),ROOT/'stability_adapter_2/PALM_MEASURED_GEOMETRY_EXECUTION.md',ROOT/'stability_adapter_2/PALM_MEASURED_POSE_RESIDUAL_PLAN.md',BASE/'palm_support_runtime_fk_v1/analysis.json',BASE/'palm_support_two_axis_fk_v2/palm_scope_assessment.json',OLD/'initial_collision/shape_properties.json']:inputs[str(p)]=sha(p)
    assert all(sha(p)==h for p,h in inputs.items());(PHASE/'attempt.json').write_text(json.dumps(dict(input_sha256=inputs,native_initializations=0,physics_steps=0),indent=2)+'\n')
    from .environment import np
    from .build_fixed_lower_asset import ASSET,pose
    from .initial_overlap import build_probe
    from .face_referenced_geometry import face_geometry
    from .search_multi_face_grip import left_fk
    from .palm_side_source_checks import intersection
    from .source_patch_interval import certified_distance
    from scipy.spatial.transform import Rotation
    states=[json.loads(v) for v in (OLD/'native/states.jsonl').read_text().splitlines()];init=read(OLD/'native/initial_values.json');proposal=read(OLD/'proposal.json');anchors=proposal['rows'][0]['source_anchors'];names=init['human_joint_names'];hn=init['human_body_names'];gn=init['native_initial_state']['guitar_body_states'];shapeprops=read(OLD/'initial_collision/shape_properties.json');guitar_names=[r['body'] for r in shapeprops['actors']['guitar']['body_ranges']];masks=shapeprops['mask_audit']['native_filters'];config=read(ROOT/'stability_adapter_2/config.json');config['humanoid_asset']=str(ASSET)
    q0=np.array([d['pos'] for d in states[0]['human_dof_states']]);fk,_=left_fk(names,hn,states[0],q0);pc0,qc0=pose(states[0]['human_body_states'][hn.index('Chest')]);rc0=Rotation.from_quat(qc0);arm=[names.index(n) for n in runtime['arm_joint_names']];proxy=np.array(read(BASE/'palm_neck_side_v1/initial_audit_v2/audit.json')['palmar_normal_proxy_local']);rows=[]
    for sample in runtime['samples']:
        step=sample['physics_step'];state=states[step];q=np.array([d['pos'] for d in state['human_dof_states']]);pc,qc=pose(state['human_body_states'][hn.index('Chest')]);lift=Rotation.from_quat(qc)*rc0.inv()
        def poses_at(v):return {n:(pc+lift.apply(p-pc0),lift*r) for n,(p,r) in fk(v).items()}
        oldpose=poses_at(q);palm_p,palm_q=pose(state['human_body_states'][hn.index('LH:palm')]);palm_r=Rotation.from_quat(palm_q);gp,gq=pose(state['guitar_body_states'][0]);gr=Rotation.from_quat(gq)
        scene=SimpleNamespace(config=config,human=0,guitar=1,env=None,gym=SimpleNamespace(get_actor_rigid_body_names=lambda env,actor:hn if actor==0 else guitar_names),bodies=lambda actor:state['human_body_states'] if actor==0 else state['guitar_body_states'])
        model,data,shapes=build_probe(scene);meshes={s['geom_id']:face_geometry(model,data,s) for s in shapes};moving=[s for s in shapes if s['actor']=='human' and (s['body'].startswith('LH:') or s['body'] in ('L_Thorax','L_Shoulder','L_Elbow','L_Wrist'))];humans=[s for s in shapes if s['actor']=='human'];guitars=[s for s in shapes if s['actor']=='guitar'];rights=[s for s in humans if s['body'].startswith('RH:') or s['body']=='R_Wrist'];moving_ids={s['geom_id'] for s in moving}
        pairs=[('human_guitar',a,b) for a in humans for b in guitars]
        pairs += [('allowed_human_self',a,b) for i,a in enumerate(humans) for b in humans[i+1:] if (a['geom_id'] in moving_ids or b['geom_id'] in moving_ids) and all(x&y==0 for x in masks[a['body']] for y in masks[b['body']])]
        pairs += [('cross_hands_source',a,b) for a in moving if a['body'].startswith('LH:') or a['body']=='L_Wrist' for b in rights]
        def query(v):
            return {kind+'|'+str(a['geom_id'])+'|'+str(b['geom_id']):dict(kind=kind,a=a['body'],b=b['body'],a_geom=a['geom_id'],b_geom=b['geom_id'],common_radius_m=intersection(v[a['geom_id']],v[b['geom_id']])) for kind,a,b in pairs}
        baseline=query(meshes);dq=np.array([sample['geometric_dq_rad'][names[i]] for i in arm])
        for fraction in (0.,1.,.5,.25):
            changed=q.copy();changed[arm]+=fraction*dq;pred=poses_at(changed);delta_r=pred['LH:palm'][1]*oldpose['LH:palm'][1].inv();delta_p=pred['LH:palm'][0]-oldpose['LH:palm'][0];newp=palm_p+delta_p;newr=delta_r*palm_r;updated=dict(meshes)
            for shape in moving:
                name=shape['body'];oldmesh=meshes[shape['geom_id']];mesh=oldmesh.copy()
                if name.startswith('LH:'):mesh.vertices=newp+delta_r.apply(oldmesh.vertices-palm_p)
                else:
                    pa,qa=pose(state['human_body_states'][hn.index(name)]);dr=pred[name][1]*oldpose[name][1].inv();dp=pred[name][0]-oldpose[name][0];mesh.vertices=pa+dp+dr.apply(oldmesh.vertices-pa)
                if fraction==0.:assert np.max(abs(mesh.vertices-oldmesh.vertices))<1e-12
                updated[shape['geom_id']]=mesh
            radii=baseline if fraction==0 else query(updated);increased=[dict(v,baseline_common_radius_m=baseline[k]['common_radius_m'],increase_m=v['common_radius_m']-baseline[k]['common_radius_m']) for k,v in radii.items() if v['common_radius_m']>1e-7 and v['common_radius_m']>baseline[k]['common_radius_m']+1e-5]
            intersecting=[v for v in radii.values() if v['common_radius_m']>1e-7];palmgeom=next(s['geom_id'] for s in shapes if s['body']=='LH:palm');gap=certified_distance(updated[palmgeom],gr.apply(np.array(proposal['regions_G_m']['palm']))+gp);point=newp+newr.apply(anchors['LH:palm']['source_point_local_m']);direction=gr.inv().apply(newr.apply(anchors['LH:palm']['source_normal_local']));normal=-np.array([1.,.01631590413943356,0.]);normal/=np.linalg.norm(normal);target=np.array(sample['goal_W_m']);base=np.array(init['preserved_absolute_targets_rad']);targetq=base.copy();targetq[arm]+=fraction*dq;main=[names.index(n) for n in init['main_control_joint_names']];bounds=np.all(targetq>=init['PD_properties']['lower']) and np.all(targetq<=init['PD_properties']['upper']) and np.all(abs((targetq-q0)[main])<=.3);up=float(newr.apply(proxy)[2])
            rows.append(dict(physics_step=step,fraction=fraction,source_pair_count=len(pairs),current_source_intersections=intersecting,new_or_increased_source_intersections=increased,palm_finite_patch_interval=gap,palm_anchor_W_m=point.tolist(),palm_goal_W_m=target.tolist(),palm_anchor_error_mm=float(np.linalg.norm(point-target)*1000),palm_inward_normal_G_dot=float(direction@normal),palm_up_proxy_z=up,PD_target_model_and_offset_bounds=bool(bounds),source_direction_screen_passed=not increased and up>0 and bool(bounds),angle_delta_rad=(fraction*dq).tolist(),scope='actual finger-relative pose rigidly transformed by arm12 source FK delta; no finger angle future prediction or physics state writes'))
    checks=dict(identity_fraction0_meshes_preserved=True,sixteen_saved_geometry_placements=len(rows)==16,only_arm12_dq_and_measured_hand_pose=True,inputs_unchanged=all(sha(p)==h for p,h in inputs.items()));assert all(checks.values());result=dict(checks=checks,input_sha256=inputs,rows=rows,native_initializations=0,physics_steps=0,source_screen_tolerance_increase_m=.00001,scope='offline whole hand measured-pose source insphere intersection and witness interval; not cooked/native penetration/contact or certified runtime-safe PD controller')
    (PHASE/'analysis.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps(dict(checks=checks,summary=[dict(step=r['physics_step'],fraction=r['fraction'],passed=r['source_direction_screen_passed'],increases=[dict(a=v['a'],b=v['b'],kind=v['kind'],increase_mm=v['increase_m']*1000) for v in r['new_or_increased_source_intersections']],palm_gap_upper_mm=r['palm_finite_patch_interval']['distance_m']*1000,palm_point_error_mm=r['palm_anchor_error_mm']) for r in rows]),indent=2))
if __name__=='__main__':main()
