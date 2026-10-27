"""Four saved-pose, bounded 18D support proposals and whole-source pair screening."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import xml.etree.ElementTree as ET

from scipy.optimize import Bounds, LinearConstraint, minimize
from .coupled_support_source import (CONTACT_BODIES, CoupledSnapshot, anchor_catalog,
                                     features, np, Rotation, pose)
from .initial_overlap import build_probe
from .face_referenced_geometry import face_geometry
from .palm_side_source_checks import intersection
from .source_patch_interval import certified_distance
from .search_multi_face_grip import nearest_face
from .build_fixed_lower_asset import ASSET

ROOT=Path(__file__).resolve().parents[1]; B=ROOT/'docs/2026-10-12/stability_adapter_2/results'
OLD=B/'body9_strap_minus2mm_v1'; P=B/'coupled_support_source_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def main():
    out=P/'search_v3.json';assert not out.exists()
    model=read(P/'model.json');assert all(model['checks'].values())
    inputs=dict(model['input_sha256'])
    paths=[P/'model.json',Path(__file__).resolve(),ASSET,OLD/'native/controls.jsonl',
           B/'torso_hold_native_collision_v1/initial_collision/shape_properties.json',
           B/'palm_neck_side_v1/initial_audit_v2/audit.json',
           ROOT/'docs/2026-08-19/fret_joint_limits/joint_limit_ranges.json',
           ROOT/'stability_adapter_2/config.json']
    paths += [ROOT/'stability_adapter_2'/s for s in ('initial_overlap.py','face_referenced_geometry.py','palm_side_source_checks.py','source_patch_interval.py')]
    paths.extend([ROOT/'stability_adapter_2/COUPLED_SUPPORT_SOURCE_CORRECTION.md', ROOT/'stability_adapter_2/COUPLED_SUPPORT_SELF_SCREEN.md'])
    for p in paths:inputs[str(p)]=sha(p)
    assert all(sha(p)==h for p,h in inputs.items())
    init=read(OLD/'native/initial_values.json');proposal=read(OLD/'proposal.json')
    states=[json.loads(v) for v in (OLD/'native/states.jsonl').read_text().splitlines()]
    controls=[json.loads(v) for v in (OLD/'native/controls.jsonl').read_text().splitlines()]
    names=init['human_joint_names'];bodies=init['human_body_names'];anchors=anchor_catalog(proposal)
    q0=np.array([d['pos'] for d in states[0]['human_dof_states']])
    hand_limits={r['dof']:r for r in read(ROOT/'docs/2026-08-19/fret_joint_limits/joint_limit_ranges.json')['rows']}
    props=read(paths[4]);guitar_names=[r['body'] for r in props['actors']['guitar']['body_ranges']];masks=props['mask_audit']['native_filters']
    proxy=np.array(read(paths[5])['palmar_normal_proxy_local'])
    config=read(ROOT/'stability_adapter_2/config.json');config['humanoid_asset']=str(ASSET)
    xml=ET.parse(ASSET).getroot();parents={c.get('name'):p.get('name') for p in xml.iter('body') for c in p.findall('body')}
    def distance(a,b):
        chain=[];current=a
        while current in parents:chain.append(current);current=parents[current]
        chain.append(current);steps=0;current=b
        while current not in chain and current in parents:steps+=1;current=parents[current]
        return steps+chain.index(current) if current in chain else 99
    rows=[];solves=[];identity=[]
    for sample in model['samples']:
        step=sample['step'];state=states[step];snap=CoupledSnapshot(names,bodies,states[0],state);indices=snap.indices
        scene=SimpleNamespace(config=config,human=0,guitar=1,env=None,gym=SimpleNamespace(get_actor_rigid_body_names=lambda env,actor:bodies if actor==0 else guitar_names),bodies=lambda actor:state['human_body_states'] if actor==0 else state['guitar_body_states'])
        mj,md,shapes=build_probe(scene);meshes={s['geom_id']:face_geometry(mj,md,s) for s in shapes}
        moving=[s for s in shapes if s['actor']=='human' and s['body'] in snap.poses(np.zeros(18))]
        moving_ids={s['geom_id'] for s in moving};humans=[s for s in shapes if s['actor']=='human'];guitars=[s for s in shapes if s['actor']=='guitar'];rights=[s for s in humans if s['body'].startswith('RH:') or s['body']=='R_Wrist']
        zero=snap.meshes(meshes,moving,np.zeros(18));identity.append(all(np.array_equal(meshes[k].vertices,zero[k].vertices) for k in meshes))
        pairs=[('human_guitar',a,b) for a in humans for b in guitars]
        for i,a in enumerate(humans):
            for b in humans[i+1:]:
                if a['geom_id'] not in moving_ids and b['geom_id'] not in moving_ids:continue
                if not all(x&y==0 for x in masks[a['body']] for y in masks[b['body']]):continue
                kind='connected_source_diagnostic' if distance(a['body'],b['body'])<=2 else 'allowed_nonadjacent_self'
                pairs.append((kind,a,b))
        pairs += [('cross_hands_source',a,b) for a in moving if a['body'].startswith('LH:') or a['body']=='L_Wrist' for b in rights]
        left_shapes=[s for s in moving if s['body'].startswith('LH:') or s['body'] in ('L_Wrist','L_Elbow')]
        seen={tuple(sorted((a['geom_id'],b['geom_id']))) for kind,a,b in pairs if a['actor']==b['actor']=='human'}
        left_nonadjacent=set()
        for i,a in enumerate(left_shapes):
            for b in left_shapes[i+1:]:
                key=tuple(sorted((a['geom_id'],b['geom_id'])))
                nonadjacent=distance(a['body'],b['body'])>2
                if nonadjacent:left_nonadjacent.add(key)
                if key not in seen:
                    pairs.append(('same_left_nonadjacent_source' if nonadjacent else 'connected_source_diagnostic',a,b));seen.add(key)
        assert left_nonadjacent<=seen
        def query(vertices,baseline=None):
            output={}
            for kind,a,b in pairs:
                key=(kind,a['geom_id'],b['geom_id'])
                if baseline is not None and not {a['geom_id'],b['geom_id']}&moving_ids:output[key]=baseline[key];continue
                output[key]=dict(kind=kind,a=a['body'],b=b['body'],a_geom=a['geom_id'],b_geom=b['geom_id'],common_radius_m=intersection(vertices[a['geom_id']],vertices[b['geom_id']]))
            return output
        baseline=query(meshes);gp,gq=pose(state['guitar_body_states'][0]);gr=Rotation.from_quat(gq)
        goal_points=[];goal_normals=[];planes={}
        current=np.array(sample['features_W']);base=np.array(controls[0 if step==0 else step-1]['final_target_rad'])
        assert step!=0 or base.tolist()==init['preserved_absolute_targets_rad']
        held=np.array([j for j in range(len(names)) if j not in indices])
        lower=np.array(init['PD_properties']['lower']);upper=np.array(init['PD_properties']['upper'])
        for name in snap.selected[12:]:
            j=names.index(name);lower[j]=max(lower[j],hand_limits[name]['lower_rad']);upper[j]=min(upper[j],hand_limits[name]['upper_rad'])
        widths=np.r_[np.full(12,.05),np.full(6,.10)]
        lo=np.maximum.reduce((-widths,lower[indices]-snap.q[indices],lower[indices]-base[indices],q0[indices]-.3-base[indices]))
        hi=np.minimum.reduce((widths,upper[indices]-snap.q[indices],upper[indices]-base[indices],q0[indices]+.3-base[indices]))
        assert np.all(lo<=0) and np.all(hi>=0)
        plane_J=[];plane_lower=[]
        for k,name in enumerate(CONTACT_BODIES):
            face='palm' if name=='LH:palm' else 'thumb' if name=='LH:thumb3' else 'front'
            point=gr.inv().apply(current[k*3:k*3+3]-gp);region=np.array(proposal['regions_G_m'][face])
            point[1]=np.clip(point[1],region[:,1].min()+.0031,region[:,1].max()-.0031)
            target,outward=nearest_face(point,face,proposal['front_outer_source_z_G_m'],.0001,proposal['regions_G_m'])
            goal_points.append(gp+gr.apply(target));normal=gr.apply(outward);goal_normals.append(-normal)
            plane=gp+gr.apply(target-.0001*outward);planes[name]=(plane,normal,face)
            for shape in [s for s in moving if s['body']==name]:
                vertices=meshes[shape['geom_id']].vertices;gaps=(vertices-plane)@normal;j=int(gaps.argmin())
                oldp,oldr=snap.actual[name];local=oldr.inv().apply(vertices[j]-oldp);derivative=[]
                for axis in range(18):
                    d=np.zeros(18);d[axis]=.0001
                    pp,rp=snap.poses(d)[name];pm,rm=snap.poses(-d)[name]
                    derivative.append(float(((pp+rp.apply(local))-(pm+rm.apply(local)))@normal/.0002))
                plane_J.append(derivative);plane_lower.append(-max(float(gaps[j]),0)-.00001)
        goal=np.r_[np.array(goal_points).reshape(-1),np.array(goal_normals).reshape(-1)]
        J=np.array(sample['feature_J_W_per_rad']);weights=np.r_[np.ones(12),np.repeat([.04,.02,.02,.02],3)]
        matrix=np.vstack((J*weights[:,None],.003*np.eye(18)));rhs=np.r_[(goal-current)*weights,np.zeros(18)]
        C=np.array(plane_J);cl=np.array(plane_lower)
        def objective(d):
            error=matrix@d-rhs;return float(error@error),2*matrix.T@error
        result=minimize(objective,np.zeros(18),jac=True,method='SLSQP',bounds=Bounds(lo,hi),constraints=[LinearConstraint(C,cl,np.inf)],options={'ftol':1e-13,'maxiter':300})
        dq=result.x;assert np.isfinite(dq).all()
        feasible=bool(np.all(dq>=lo-1e-10) and np.all(dq<=hi+1e-10) and np.all(C@dq>=cl-1e-10))
        solves.append(dict(step=step,optimizer_success=bool(result.success),message=str(result.message),feasible=feasible,selected_names=snap.selected,lower_delta_rad=lo.tolist(),upper_delta_rad=hi.tolist(),delta_rad=dq.tolist(),goal_features_W=goal.tolist(),linear_plane_matrix_m_per_rad=C.tolist(),linear_plane_lower_m=cl.tolist(),linear_weighted_error_before=float(np.linalg.norm(rhs)),linear_weighted_error_after=float(np.linalg.norm(matrix@dq-rhs))))
        for fraction in (0.,1.,.5,.25):
            delta=fraction*dq;updated=snap.meshes(meshes,moving,delta);candidate=baseline if fraction==0 else query(updated,baseline)
            increased=[dict(v,baseline_common_radius_m=baseline[k]['common_radius_m'],increase_m=v['common_radius_m']-baseline[k]['common_radius_m']) for k,v in candidate.items() if v['common_radius_m']>1e-7 and v['common_radius_m']>baseline[k]['common_radius_m']+.00001]
            blocking=[v for v in increased if v['kind']!='connected_source_diagnostic']
            feature=features(snap,delta,anchors);newposes=snap.poses(delta);gaps={};face_min={}
            for name,(plane,normal,face) in planes.items():
                poly=np.array(proposal['regions_G_m'][face])
                if face=='front':poly[:,2]=proposal['front_outer_source_z_G_m']
                bodyshapes=[s for s in moving if s['body']==name]
                gaps[name]=[certified_distance(updated[s['geom_id']],gp+gr.apply(poly)) for s in bodyshapes]
                face_min[name]=min(float(((updated[s['geom_id']].vertices-plane)@normal).min()) for s in bodyshapes)
            palm_upper=min(v['distance_m'] for v in gaps['LH:palm'])
            if fraction==0:baseline_palm_lower=min(v['distance_lower_bound_m'] for v in gaps['LH:palm'])
            palm_patch_improves=bool(palm_upper<baseline_palm_lower-1e-9)
            target=base.copy();target[indices]+=delta;assert np.array_equal(target[held],base[held]);main=[names.index(n) for n in init['main_control_joint_names']]
            bounds=bool(np.all(target>=lower-1e-12) and np.all(target<=upper+1e-12) and np.all(abs((target-q0)[main])<=.3+1e-12) and np.all(snap.q[indices]+delta>=lower[indices]-1e-12) and np.all(snap.q[indices]+delta<=upper[indices]+1e-12))
            up=float(newposes['LH:palm'][1].apply(proxy)[2]);palm_error=float(np.linalg.norm(goal[:3]-feature[:3])*1000)
            rows.append(dict(step=step,time_s=step/240,fraction=fraction,delta_rad=delta.tolist(),source_pair_count=len(pairs),same_left_nonadjacent_pair_count=len(left_nonadjacent),current_source_intersections=[v for v in candidate.values() if v['common_radius_m']>1e-7],new_or_increased_intersections=increased,blocking_increases=blocking,patch_distance_intervals=gaps,minimum_infinite_face_gap_m=face_min,palm_anchor_error_mm=palm_error,features_W=feature.tolist(),goal_features_W=goal.tolist(),palm_inward_alignment_dot=float(feature[12:15]@goal[12:15]),palm_up_proxy_z=up,palm_patch_approach_certified=palm_patch_improves,baseline_palm_patch_lower_m=baseline_palm_lower,PD_and_actual_delta_bounds=bounds,base_target_rad=base.tolist(),final_target_rad=target.tolist(),source_direction_screen_passed=bool(feasible and not blocking and up>0 and bounds and palm_patch_improves and palm_error<float(np.linalg.norm(goal[:3]-current[:3])*1000)-1e-6 and fraction>0)))
    checks=dict(model_five_checks_pass=all(model['checks'].values()),submitted_PD_base_and_other63_held=True,same_left_nonadjacent_source_pairs_evaluated=all(r['same_left_nonadjacent_pair_count']>0 for r in rows),four_exact_zero_mesh_identities=all(identity) and len(identity)==4,sixteen_source_placements=len(rows)==16,all_four_solve_results_feasible=all(r['feasible'] for r in solves),all_inputs_preserved=all(sha(p)==h for p,h in inputs.items()))
    output=dict(checks=checks,input_sha256=inputs,solves=solves,rows=rows,selected_names=model['selected_names'],native_initializations=0,physics_steps=0,scope='conditional measured-pose source geometry only; 18D is temporary support proposal scope, final66 control authority retained; source LP radius is not cooked penetration/contact or future PD response')
    out.write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(checks=checks,summary=[dict(step=r['step'],fraction=r['fraction'],palm_gap_upper_mm=min(v['distance_m'] for v in r['patch_distance_intervals']['LH:palm'])*1000,palm_anchor_error_mm=r['palm_anchor_error_mm'],passed=r['source_direction_screen_passed'],blocking_pairs=[dict(a=v['a'],b=v['b'],increase_mm=v['increase_m']*1000) for v in r['blocking_increases']]) for r in rows]),indent=2))
    assert all(checks.values()),checks
if __name__=='__main__':main()
