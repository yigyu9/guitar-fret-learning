"""Move only the initial right arm slightly to clear the revised OM upper bout."""
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from .initial_pose_noise_v1 import read,save,sha,pose
from .upper_arm_static_geometry_v1 import ROOT,calibrated_upper_fk,state_from_fk,capsule_witness
from .realistic_guitar_geometry_v1 import source_scene,source_audit


def main():
    from .environment_contract_v1 import EnvironmentContract
    result=ROOT/'docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1/search_v1';result.mkdir(exist_ok=False)
    base=ROOT/'docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/native_realistic_v2/initial_values.json'
    original_cfg=ROOT/'docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/search_v1/front35_up80/config.json'
    manifest=ROOT/'stability_adapter_2/assets/om_body_geometry_v2/manifest.json';geometry=read(manifest);saved=read(base)
    c=EnvironmentContract(original_cfg);state=saved['native_initial_state'];names=saved['joint_names'];bodies=saved['human_body_names'];q0=np.asarray(saved['q_ref_rad'])
    fk,parents=calibrated_upper_fk(names,bodies,state,q0);poses0=fk(q0);gp,gr=pose(state['guitar_body_states'][0]);normal=gr.apply([-1.,0,0])
    index=np.array([i for i,n in enumerate(names) if n.startswith(tuple('R_'+part for part in ('Thorax','Shoulder','Elbow','Wrist')))])
    lo=np.maximum(c.lower[index],q0[index]-.15);hi=np.minimum(c.upper[index],q0[index]+.15)
    inputs={str(p):sha(p) for p in [Path(__file__).resolve(),base,original_cfg,manifest]};inputs.update(geometry['input_sha256']);inputs[geometry['asset']]=geometry['asset_sha256']
    for entry in geometry['meshes']:inputs[entry['path']]=entry['sha256']
    rows=[];selected=None
    for distance in [.006,.010,.015,.020]:
        target=capsule_witness(poses0,normal)+distance*normal
        def residual(v):
            q=q0.copy();q[index]=v;poses=fk(q)
            return np.r_[1000*(capsule_witness(poses,normal)-target),
                300*(poses['R_Wrist'][0]-poses0['R_Wrist'][0]),
                10*(poses0['R_Wrist'][1].inv()*poses['R_Wrist'][1]).as_rotvec(),.1*(v-q0[index])]
        fit=least_squares(residual,np.clip(q0[index],lo+1e-9,hi-1e-9),bounds=(lo,hi),max_nfev=200)
        q=q0.copy();q[index]=fit.x;q=q.astype(np.float32).astype(float);poses=fk(q);predicted=state_from_fk(state,bodies,q,fk)
        audit=source_audit(source_scene(predicted,bodies,geometry['asset']),parents)
        row={'distance_requested_m':distance,'max_right_arm_delta_rad':float(abs(q[index]-q0[index]).max()),
            'right_wrist_position_change_m':float(np.linalg.norm(poses['R_Wrist'][0]-poses0['R_Wrist'][0])),
            'witness_fit_error_m':float(np.linalg.norm(capsule_witness(poses,normal)-target)),'audit':audit}
        rows.append(row);print(distance,audit['source_clear'],row['max_right_arm_delta_rad'],flush=True)
        if audit['source_clear'] and row['witness_fit_error_m']<.002 and row['right_wrist_position_change_m']<.003:
            folder=result/'selected';folder.mkdir();candidate={'joint_names':names,'joint_angles_rad':q.tolist(),'position_W_m':gp.tolist(),
                'quaternion_xyzw':gr.as_quat().tolist(),'predicted_human_poses':{n:{'p':p.tolist(),'q':r.as_quat().tolist()} for n,(p,r) in poses.items()},'OM_right_clearance':row}
            save(folder/'candidate.json',candidate);cfg=read(original_cfg);cfg.update(initial_candidate=str(folder/'candidate.json'),initial_candidate_sha256=sha(folder/'candidate.json'))
            save(folder/'config.json',cfg);selected=str(folder/'config.json');break
    assert all(sha(path)==value for path,value in inputs.items())
    save(result/'search.json',{'input_sha256':inputs,'rows':rows,'selected_config':selected,'native_runs':0,
        'scope':'right arm initial targets only; guitar p/q, left hand, torso/head/finger/lower targets unchanged'})
    assert selected,'no clear small-right-arm candidate'


if __name__=='__main__':main()
