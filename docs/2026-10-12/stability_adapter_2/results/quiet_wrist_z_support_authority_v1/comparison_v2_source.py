"""Compare saved endpoint responses; the bounded prediction is not a simulation."""
from pathlib import Path
import hashlib
import json
import shutil
import numpy as np
from scipy.optimize import lsq_linear
from scipy.spatial.transform import Rotation

R=Path(__file__).resolve().parents[1];A=R/'stability_adapter_2';B=R/'docs/2026-10-12/stability_adapter_2/results'
Y=B/'quiet_wrist_support_authority_v1';P=B/'quiet_wrist_z_support_authority_v1'
BASE=B/'initial_middle3_alignment_v1/native/initial_values.json'


def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def main():
    output=P/'comparison_v2.json';invocation=P/'comparison_v2_invocation.json';copy=P/'comparison_v2_source.py'
    assert not any(p.exists() for p in [output,invocation,copy])
    paths={Path(__file__).resolve(),A/'WRIST_YZ_RESPONSE_COMPARISON.md',A/'WRIST_YZ_COMPARISON_V2.md',P/'comparison_failure.json',BASE,BASE.parent.parent/'artifact_inventory.json',Y/'artifact_inventory.json',Y/'analysis.json',Y/'series.json',P/'analysis.json',P/'series.json'}
    before={str(p):sha(p) for p in sorted(paths,key=str)}
    shutil.copy2(Path(__file__).resolve(),copy);assert sha(copy)==sha(Path(__file__).resolve())
    save(invocation,dict(input_sha256_before=before,source_snapshot=str(copy),scope='Direct saved-data calculation; stdout goes to tool, no open leaf log'))
    before[str(invocation)]=sha(invocation)
    ya,za=read(Y/'analysis.json'),read(P/'analysis.json');ys,zs=read(Y/'series.json'),read(P/'series.json');initial=read(BASE);inventory=read(Y/'artifact_inventory.json');baseline_inventory=read(BASE.parent.parent/'artifact_inventory.json')
    checks={}
    checks['sealed_Y_and_baseline_inputs_exact']=all(sha(p)==inventory[str(p)]['sha256'] for p in [Y/'analysis.json',Y/'series.json']) and sha(BASE)==baseline_inventory[str(BASE)]['sha256']
    checks['both_saved_analyses_passed']=all(all(a['checks'].values()) and a['physical_initializations']==2 and a['physical_steps']==2400 and a['actor_inference_calls']==a['training_updates']==0 for a in [ya,za])
    common=['time_s','position_W_m','quaternion_xyzw','position_error_mm','rotation_error_deg']
    checks['baseline_pose_time_and_error_series_exact']=all(ys['baseline'][k]==zs['baseline'][k] for k in common)
    response=np.column_stack([np.array(a['central_t5_response_6x1'])[:,0] for a in [ya,za]])
    checks['finite_world_6x2_matching_units']=response.shape==(6,2) and bool(np.isfinite(response).all()) and ya['response_row_units']==za['response_row_units']==['m/rad']*3+['rad/rad']*3 and ya['response_frame']==za['response_frame']
    base_p=np.array(zs['baseline']['position_W_m'][-1]);base_r=Rotation.from_quat(zs['baseline']['quaternion_xyzw'][-1]);goal_p=np.array(initial['guitar_goal_position_W_m']);goal_r=Rotation.from_quat(initial['guitar_goal_quaternion_xyzw'])
    error=np.r_[goal_p-base_p,(goal_r*base_r.inv()).as_rotvec()]
    scale=np.r_[np.full(3,.03),np.full(3,np.deg2rad(5.))];matrix=response/scale[:,None];desired=error/scale
    singular=np.linalg.svd(matrix,compute_uv=False);rank=int(np.linalg.matrix_rank(matrix));norms=np.linalg.norm(matrix,axis=0)
    cosine=float(np.dot(matrix[:,0],matrix[:,1])/np.prod(norms)) if np.all(norms>0) else None
    condition=float(singular[0]/singular[-1]) if rank==2 else None
    fit=lsq_linear(matrix,desired,bounds=(-.005,.005));delta=fit.x
    predicted_p=base_p+response[:3]@delta;predicted_r=Rotation.from_rotvec(response[3:]@delta)*base_r
    checks['bounded_fit_finite_and_successful']=bool(fit.success and np.isfinite(delta).all() and np.all(abs(delta)<=.005))
    after={p:sha(p) for p in before};checks['inputs_unchanged']=before==after;assert all(checks.values()),checks
    save(output,dict(checks=checks,input_sha256_before=before,input_sha256_after=after,response_matrix_world_6x2=response.tolist(),columns=['L_Wrist_y','L_Wrist_z'],row_units=['m/rad']*3+['rad/rad']*3,
        position_scale_m=.03,rotation_scale_rad=float(np.deg2rad(5.)),scaled_singular_values=singular.tolist(),scaled_rank=rank,scaled_column_cosine=cosine,scaled_condition_number=condition,
        desired_correction_world_m_rad=error.tolist(),bounded_candidate_delta_rad=delta.tolist(),baseline_position_error_mm=float(np.linalg.norm(error[:3])*1000),baseline_rotation_error_deg=float(np.degrees(np.linalg.norm(error[3:]))),
        predicted_position_error_mm=float(np.linalg.norm(goal_p-predicted_p)*1000),predicted_rotation_error_deg=float(np.degrees((goal_r*predicted_r.inv()).magnitude())),native_calls=0,physics_steps=0,
        scope='Local endpoint response model and unmeasured combined candidate; no gain certificate, global Jacobian, combined-physics result, or success gate'))
    print(json.dumps(dict(checks=len(checks),scaled_rank=rank,scaled_column_cosine=cosine,delta_rad=delta.tolist())))


if __name__=='__main__':main()
