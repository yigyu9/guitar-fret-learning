"""Find bounded forward-bent starts with exact source capsule/body clearances."""
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from .initial_pose_noise_v1 import read,save,sha,pose
from .upper_arm_static_geometry_v1 import ROOT,ASSET,calibrated_upper_fk,state_from_fk
from .realistic_guitar_geometry_v1 import source_scene,source_audit
from .om_axilla_source_geometry_v3 import CapsuleBodyDistance

P=ROOT/'docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1'
BASE=ROOT/'docs/2026-10-12/stability_adapter_2/results/visual_strings_v1/native_v1/initial_values.json'
CONFIG=ROOT/'docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1/search_v2/selected/config.json'
GEOMETRY=ROOT/'stability_adapter_2/assets/om_body_geometry_v3/manifest.json'


def main():
    from .environment_contract_v1 import EnvironmentContract
    from .underneck_initial_search import source_scene as transformed_scene
    c=EnvironmentContract(CONFIG);base=read(BASE);state=base['native_initial_state'];names=base['joint_names'];bodies=base['human_body_names'];q0=np.array(base['q_ref_rad'])
    fk,parents=calibrated_upper_fk(names,bodies,state,q0);original=fk(q0);gp,gr=pose(state['guitar_body_states'][0]);geometry=read(GEOMETRY);distance=CapsuleBodyDistance(geometry['asset'],ASSET)
    forward=original['Pelvis'][1].apply([0.,-1,0]);forward[2]=0;forward/=np.linalg.norm(forward);axis=np.cross([0,0,1.],forward)
    group=lambda prefixes:np.array([i for i,n in enumerate(names) if n.startswith(prefixes)])
    body=c.body;left=group(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist'));right=group(('R_Thorax','R_Shoulder','R_Elbow','R_Wrist'));head=group(('Neck_','Head_'))
    out=P/'search_v2';out.mkdir(exist_ok=False);selected=[];rows=[]
    inputs={str(p):sha(p) for p in [BASE,CONFIG,GEOMETRY,ASSET,Path(__file__).resolve(),ROOT/'stability_adapter_2/om_axilla_source_geometry_v3.py',ROOT/'stability_adapter_2/OM_AXILLA_INITIAL_POSE_PLAN_V3.md']}
    inputs.update(c.inputs);inputs[geometry['asset']]=geometry['asset_sha256']
    inputs.update({str(p):sha(p) for p in Path(__file__).resolve().parent.glob('*.py')})
    for m in geometry['meshes']:inputs[m['path']]=m['sha256']
    gp_reference=gp.copy()
    for back_mm in (30,35,40):
        lean=18;delta=-back_mm/1000*forward;gp=gp_reference+delta
        q=q0.copy();targets={n:Rotation.from_rotvec(axis*np.deg2rad(lean*f))*original[n][1] for n,f in zip(('Torso','Spine','Chest'),(.25,.625,1))}
        lo=np.maximum(c.lower[body],q0[body]-np.deg2rad(8));hi=np.minimum(c.upper[body],q0[body]+np.deg2rad(8))
        def body_res(v):
            z=q.copy();z[body]=v;poses=fk(z)
            return np.r_[np.concatenate([100*(targets[n].inv()*poses[n][1]).as_rotvec() for n in targets]),.01*(v-q0[body])]
        fit=least_squares(body_res,np.clip(q[body],lo+1e-9,hi-1e-9),bounds=(lo,hi),max_nfev=80);q[body]=fit.x
        for idx,name in [(head,'Head'),(left,'LH:palm')]:
            width=.3 if name=='Head' else .45
            lo=np.maximum(c.lower[idx],q0[idx]-width);hi=np.minimum(c.upper[idx],q0[idx]+width)
            def res(v):
                z=q.copy();z[idx]=v;pp,rr=fk(z)[name]
                parts=[100*(original[name][1].inv()*rr).as_rotvec(),.01*(v-q0[idx])]
                if name=='LH:palm':parts.insert(0,1000*(pp-(original[name][0]+delta)))
                return np.concatenate(parts)
            fit=least_squares(res,np.clip(q[idx],lo+1e-9,hi-1e-9),bounds=(lo,hi),max_nfev=100);q[idx]=fit.x
        lo=np.maximum(c.lower[right],q0[right]-.45);hi=np.minimum(c.upper[right],q0[right]+.45)
        def right_res(v):
            z=q.copy();z[right]=v;poses=fk(z);m=distance.measure(poses,'R_Shoulder',gp,gr);prox=distance.measure(poses,'R_Shoulder',gp,gr,.55);point=np.array(prox['guitar_surface_G_m'])
            return np.r_[500*(m['gap_m']-.003),1000*(prox['gap_m']-.003),100*max(point[0]+.05,0),100*max(-.44-point[1],0),100*max(point[1]+.25,0),
                100*(poses['R_Wrist'][0]-original['R_Wrist'][0]),5*(original['R_Wrist'][1].inv()*poses['R_Wrist'][1]).as_rotvec(),.1*(v-q0[right])]
        fit=least_squares(right_res,np.clip(q[right],lo+1e-9,hi-1e-9),bounds=(lo,hi),max_nfev=80,diff_step=1e-4);q[right]=fit.x;q=q.astype(np.float32).astype(float);poses=fk(q)
        support={n:distance.measure(poses,n,gp,gr) for n in ('Torso','Spine','Chest','R_Thorax','R_Shoulder','R_Elbow')}
        _,predicted=transformed_scene(state_from_fk(state,bodies,q,fk),{'human_body_names':bodies},gp,gr)
        audit=source_audit(source_scene(predicted,bodies,geometry['asset']),parents)
        prox=distance.measure(poses,'R_Shoulder',gp,gr,.55)
        errors={n:float(np.rad2deg((targets[n].inv()*poses[n][1]).magnitude())) for n in targets};lp,lr=poses['LH:palm'];label='lean18_back%d'%back_mm
        row={'label':label,'additional_chest_world_lean_deg':lean,'guitar_initial_delta_W_m':delta.tolist(),'guitar_back_mm':back_mm,'proximal_support':prox,'body_goal_orientation_errors_deg':errors,'left_palm_position_error_m':float(np.linalg.norm(lp-(original['LH:palm'][0]+delta))),
             'left_palm_orientation_error_deg':float(np.rad2deg((original['LH:palm'][1].inv()*lr).magnitude())),'head_orientation_error_deg':float(np.rad2deg((original['Head'][1].inv()*poses['Head'][1]).magnitude())),
             'body_max_initial_scalar_change_deg':float(np.rad2deg(abs(q[body]-q0[body])).max()),'arm_max_initial_scalar_change_rad':float(abs(q[np.r_[left,right]]-q0[np.r_[left,right]]).max()),
             'right_wrist_position_change_m':float(np.linalg.norm(poses['R_Wrist'][0]-original['R_Wrist'][0])),'capsule_body':support,'source_audit':audit}
        row['accepted_for_native']=bool(audit['source_clear'] and min(m['gap_m'] for m in support.values())>=.0002 and support['R_Shoulder']['gap_m']<.005 and .0002<=prox['gap_m']<.006 and prox['guitar_surface_G_m'][0]<-.05 and -.44<=prox['guitar_surface_G_m'][1]<=-.25 and support['Chest']['gap_m']<.005 and row['right_wrist_position_change_m']<.05 and row['left_palm_position_error_m']<.002 and row['left_palm_orientation_error_deg']<1 and max(errors.values())<.1 and row['head_orientation_error_deg']<.1)
        rows.append(row);save(out/(label+'_audit.json'),row)
        print(label,'accepted',row['accepted_for_native'],'body_gap_mm',round(support['Chest']['gap_m']*1000,3),'arm_gap_mm',round(support['R_Shoulder']['gap_m']*1000,3),'clear',audit['source_clear'],flush=True)
        if row['accepted_for_native']:
            folder=out/label;folder.mkdir();candidate={'joint_names':names,'joint_angles_rad':q.tolist(),'position_W_m':gp.tolist(),'quaternion_xyzw':gr.as_quat().tolist(),
                'predicted_human_poses':{n:{'p':p.tolist(),'q':r.as_quat().tolist()} for n,(p,r) in poses.items()},'om_axilla_proposal':row}
            save(folder/'candidate.json',candidate);cfg=read(CONFIG);cfg.update(initial_candidate=str(folder/'candidate.json'),initial_candidate_sha256=sha(folder/'candidate.json'))
            save(folder/'config.json',cfg);selected.append({'label':label,'config':str(folder/'config.json'),'Chest_gap_m':support['Chest']['gap_m']})
    assert all(sha(p)==h for p,h in inputs.items())
    save(out/'search.json',{'input_sha256':inputs,'rows':rows,'selected':selected,'native_runs':0,'scope':'static source search with analytic capsule/body extra check; not cooked clearance certification'})

if __name__=='__main__':main()
