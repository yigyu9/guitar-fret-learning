"""Place a broad convex palmar facet next to the blue neck side, with positive gap."""
import json
from pathlib import Path
from types import SimpleNamespace

from .audit_palm_side_target import PHASE,BASE,PROPOSAL,closest_polygon
from .search_palm_neck_side import REFERENCE,arm_fk
from .environment import ROOT,np
from .build_fixed_lower_asset import read,sha,pose
from .replay_contact_geometry import recorded_probe
from .render_best_run_video import set_saved_pose
from .plot_neck_palm import geometry
from .pose_strap_inputs import pose_metrics
from .palm_side_source_checks import source_checks
from scipy.spatial.transform import Rotation
from scipy.optimize import least_squares
import mujoco


def main():
    out=PHASE/'facet_search';out.mkdir(exist_ok=False)
    trials=ROOT/'stability_adapter_2/trials/palm_neck_side_v1/facet';trials.mkdir(exist_ok=False)
    audit_path=PHASE/'initial_audit_v2/audit.json';audit=read(audit_path)
    reference=read(REFERENCE/'report.json');base=read(BASE)
    files=[Path(__file__).resolve(),audit_path,BASE,PROPOSAL,REFERENCE/'report.json',REFERENCE/'states.json']
    files += [Path(p) for p in audit['input_sha256']]
    files += [Path(__file__).with_name(n) for n in ('search_palm_neck_side.py','thigh_palm_support.py',
        'replay_contact_geometry.py','render_best_run_video.py','face_referenced_geometry.py','palm_side_source_checks.py')]
    hashes={str(p):sha(p) for p in files}
    model,data,shapes=recorded_probe(REFERENCE,0)
    palm_shape=next(s for s in shapes if s['body']=='LH:palm');mesh=geometry(model,data,palm_shape)
    direction=np.array(audit['hand']['palm_normal_world'])
    eligible=np.where(mesh.facets_normal@direction>.8)[0]
    if not len(eligible):raise ValueError('no palmar-side broad convex facet')
    facet=max(eligible,key=lambda i:mesh.facets_area[i])
    triangles=mesh.triangles[mesh.facets[facet]];areas=mesh.area_faces[mesh.facets[facet]]
    point=np.average(triangles.mean(1),weights=areas,axis=0);face_normal=mesh.facets_normal[facet]
    p,q=pose(audit['initial_state']['human_body_states'][reference['human_body_names'].index('LH:palm')])
    rotation=Rotation.from_quat(q);local=rotation.inv().apply(point-p);local_normal=rotation.inv().apply(face_normal)
    normal=np.array(audit['target_outward_normal_W']);center=np.array(audit['target_center_W_m']);polygon=np.array(audit['target_polygon_W_m'])
    q0=np.array(audit['initial_joint_targets_rad']);indices=np.array(reference['arm_indices'][:12])
    names=reference['human_joint_names'];bodies=reference['human_body_names']
    low=np.array(reference['diagnostic_lower_rad'][:12]);high=np.array(reference['diagnostic_upper_rad'][:12])
    fk=arm_fk(reference,q0,audit['initial_state']);rows=[]
    for clear in (.0002,.00005,.00001):
        target=center+normal*clear
        def residual(values):
            q=q0.copy();q[indices]=values;state=fk(q)
            p,r=pose(state['human_body_states'][bodies.index('LH:palm')]);rr=Rotation.from_quat(r)
            return np.r_[1000*(p+rr.apply(local)-target),60*(rr.apply(local_normal)+normal),.02*(values-q0[indices])]
        fit=least_squares(residual,np.clip(q0[indices],low+1e-10,high-1e-10),bounds=(low,high),
                          xtol=1e-11,ftol=1e-11,gtol=1e-11,max_nfev=1000)
        q=q0.copy();q[indices]=fit.x;state=fk(q)
        set_saved_pose(model,mujoco,reference,state);mujoco.mj_forward(model,data)
        probe=(model,data,shapes);meshes,overlaps,crosshands=source_checks(probe)
        scene=SimpleNamespace(human=0,guitar=1,human_bodies=bodies,guitar_bodies=reference['guitar_body_names'],
                              bodies=lambda actor:state['human_body_states'] if actor==0 else state['guitar_body_states'])
        hand=pose_metrics(scene,probe)
        gap=closest_polygon(meshes[palm_shape['geom_id']],polygon)
        p,r=pose(state['human_body_states'][bodies.index('LH:palm')]);rr=Rotation.from_quat(r)
        name='facet_'+str(round(clear*1e6))+'um'
        settings=dict(base,joint_angles_rad=dict(base['joint_angles_rad']),strap_rest_length_m=audit['absolute_rest_length_m'])
        settings['joint_angles_rad'].update({names[i]:float(q[i]) for i in indices})
        path=trials/(name+'.json');path.write_text(json.dumps(settings,indent=2)+'\n')
        rows.append({'name':name,'settings_path':str(path),'settings_sha256':sha(path),'source_state':state,
            'clearance_m':clear,'point_fit_error_m':float(np.linalg.norm(p+rr.apply(local)-target)),
            'facet_normal_to_inward_target_dot':float(rr.apply(local_normal)@(-normal)),
            'source_hull_to_blue_polygon':gap,'source_intersections':overlaps,'cross_hand_intersections':crosshands,
            'hand':hand,'left_arm_delta_rad':dict(zip([names[i] for i in indices],(q[indices]-q0[indices]).tolist())),
            'accepted_for_fresh_native':bool(fit.success and not overlaps and not crosshands and hand['palm_normal_valid'] and
                hand['palm_up_dot']>=0 and hand['neck_projection_in_range'] and hand['palm_height_vs_local_lower_m']<=0)})
        (out/'search.json').write_text(json.dumps({'rows':rows,'facet_area_m2':float(mesh.facets_area[facet]),
            'palmar_facet_point_local_m':local.tolist(),'palmar_facet_normal_local':local_normal.tolist(),
            'input_sha256':hashes,'native_initializations':0,'physics_steps':0,
            'scope':'broad source convex facet aligned with face-used neck side; fresh native proof required'},indent=2,allow_nan=False)+'\n')
        print(json.dumps({k:rows[-1][k] for k in ('name','point_fit_error_m','source_hull_to_blue_polygon','source_intersections','cross_hand_intersections','accepted_for_fresh_native')},indent=2),flush=True)
    if not all(sha(Path(p))==h for p,h in hashes.items()):raise AssertionError('facet search inputs changed')


if __name__=='__main__':main()
