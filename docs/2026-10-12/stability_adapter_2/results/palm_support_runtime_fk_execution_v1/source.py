"""Saved actualq -> t0-calibrated FK with moving Chest; diagnostic, no native/control."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'docs/2026-10-12/stability_adapter_2/results';OLD=BASE/'torso_hold_native_collision_v1';PHASE=BASE/'palm_support_runtime_fk_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def main():
    PHASE.mkdir(exist_ok=False)
    previous=read(OLD/'analysis.json');inputs=dict(previous['input_sha256'])
    for p in [Path(__file__).resolve(),ROOT/'stability_adapter_2/PALM_RUNTIME_FK_EXECUTION.md',ROOT/'stability_adapter_2/PALM_SUPPORT_RESIDUAL_AT_BODY9_PLAN.md',OLD/'analysis.json',OLD/'proposal.json',ROOT/'tab2body/assets/smpl_mpl_hands_body.xml',ROOT/'stability_adapter_2/search_multi_face_grip.py']:inputs[str(p)]=sha(p)
    assert all(sha(p)==h for p,h in inputs.items())
    (PHASE/'attempt.json').write_text(json.dumps(dict(input_sha256=inputs,native_initializations=0,physics_steps=0),indent=2)+'\n')
    from .environment import np
    from .search_multi_face_grip import left_fk
    from .build_fixed_lower_asset import pose
    from scipy.spatial.transform import Rotation
    states=[json.loads(v) for v in (OLD/'native/states.jsonl').read_text().splitlines()];init=read(OLD/'native/initial_values.json');proposal=read(OLD/'proposal.json');row=proposal['rows'][0];names=init['human_joint_names'];bodies=init['human_body_names'];state0=states[0];q0=np.array([d['pos'] for d in state0['human_dof_states']]);arm=[i for i,n in enumerate(names) if n.startswith(('L_Thorax_','L_Shoulder_','L_Elbow_','L_Wrist_'))];assert len(arm)==12
    fk,_=left_fk(names,bodies,state0,q0);pc0,qc0=pose(state0['human_body_states'][bodies.index('Chest')]);rc0=Rotation.from_quat(qc0)
    anchor=np.array(row['source_anchors']['LH:palm']['source_point_local_m']);normal=np.array(row['source_anchors']['LH:palm']['source_normal_local']);lower=np.array(init['PD_properties']['lower']);upper=np.array(init['PD_properties']['upper']);base=np.array(init['preserved_absolute_targets_rad']);outward=np.array([1.,.01631590413943356,0.]);outward/=np.linalg.norm(outward);region=np.array(proposal['regions_G_m']['palm']);samples=[]
    for step in (0,24,120,1200):
        state=states[step];q=np.array([d['pos'] for d in state['human_dof_states']]);pc,qc=pose(state['human_body_states'][bodies.index('Chest')]);rc=Rotation.from_quat(qc);lift=rc*rc0.inv()
        def poses_at(angles):return {n:(pc+lift.apply(p-pc0),lift*r) for n,(p,r) in fk(angles).items()}
        predicted=poses_at(q);errors=[]
        for name,(p,r) in predicted.items():
            pa,qa=pose(state['human_body_states'][bodies.index(name)]);errors.append(dict(body=name,position_error_mm=float(np.linalg.norm(p-pa)*1000),rotation_error_rad=float((r*Rotation.from_quat(qa).inv()).magnitude())))
        def task(angles):
            p,r=poses_at(angles)['LH:palm'];return p+r.apply(anchor),r.apply(normal)
        p,n=task(q);pa,qa=pose(state['human_body_states'][bodies.index('LH:palm')]);ra=Rotation.from_quat(qa);actualp=pa+ra.apply(anchor);actualn=ra.apply(normal);gp,gq=pose(state['guitar_body_states'][0]);gr=Rotation.from_quat(gq);actualG=gr.inv().apply(actualp-gp)
        y=float(np.clip(actualG[1],region[:,1].min()+.0031,region[:,1].max()-.0031));z=float(np.clip(actualG[2],region[:,2].min()+.0031,region[:,2].max()-.0031));plane=np.array([.027908-.01631590413943356*(y+.241803),y,z]);goalG=plane+.0001*outward;goal=gp+gr.apply(goalG)
        Jp=np.zeros((3,12));Jn=np.zeros((3,12));methods=[]
        for k,i in enumerate(arm):
            plus,minus=q.copy(),q.copy();h=.0001
            if q[i]-h>=lower[i] and q[i]+h<=upper[i]:plus[i]+=h;minus[i]-=h;method='central'
            elif lower[i]<=q[i]<=upper[i] and q[i]+h<=upper[i]:plus[i]+=h;method='forward'
            elif lower[i]<=q[i]<=upper[i] and q[i]-h>=lower[i]:minus[i]-=h;method='backward'
            else:plus[i]+=h;minus[i]-=h;method='unconstrained_source_derivative_actual_q_outside_bounds'
            pp,np_=task(plus);pm,nm=task(minus);denom=plus[i]-minus[i];Jp[:,k]=(pp-pm)/denom;Jn[:,k]=(np_-nm)/denom;methods.append(method)
        error=goal-p;raw=Jp.T@np.linalg.solve(Jp@Jp.T+.01**2*np.eye(3),error);dq=np.clip(raw,np.maximum(-.05,lower[arm]-q[arm]),np.minimum(.05,upper[arm]-q[arm]));changed=q.copy();changed[arm]+=dq;pn,_=task(changed)
        target=base.copy();target[arm]+=dq;initial_offsets=target-q0;main=[names.index(n) for n in init['main_control_joint_names']]
        samples.append(dict(physics_step=step,time_s=step/240,body_prediction_errors=errors,max_body_position_error_mm=max(v['position_error_mm'] for v in errors),max_body_rotation_error_rad=max(v['rotation_error_rad'] for v in errors),palm_anchor_prediction_error_mm=float(np.linalg.norm(p-actualp)*1000),palm_normal_prediction_error=float(np.linalg.norm(n-actualn)),actual_palm_anchor_W_m=actualp.tolist(),predicted_palm_anchor_W_m=p.tolist(),actual_palm_anchor_G_m=actualG.tolist(),actual_palm_normal_W=actualn.tolist(),goal_G_m=goalG.tolist(),goal_W_m=goal.tolist(),derivative_methods=methods,position_J_W_m_per_rad=Jp.tolist(),normal_J_W_per_rad=Jn.tolist(),position_J_singular_values=np.linalg.svd(Jp,compute_uv=False).tolist(),source_point_error_before_mm=float(np.linalg.norm(error)*1000),actual_point_error_before_mm=float(np.linalg.norm(goal-actualp)*1000),source_point_error_after_geometric_dq_mm=float(np.linalg.norm(goal-pn)*1000),linear_predicted_point_delta_W_mm=(Jp@dq*1000).tolist(),nonlinear_predicted_point_delta_W_mm=((pn-p)*1000).tolist(),geometric_dq_rad=dict(zip([names[i] for i in arm],dq.tolist())),actual_q_native_bound_violations=[names[i] for i in range(81) if q[i]<lower[i] or q[i]>upper[i]],base_plus_dq_within_native_limits=bool(np.all(target>=lower)&np.all(target<=upper)),base_plus_dq_initial_main_offsets_within0p3=bool(np.all(abs(initial_offsets[main])<=.3)),base_plus_dq_float32_target_rad=target.astype(np.float32).astype(float).tolist(),FK_prediction_gate_passed=max(v['position_error_mm'] for v in errors)<=.1 and max(v['rotation_error_rad'] for v in errors)<=.001))
    checks=dict(t0_calibration_only_no_per_sample_refit=True,four_saved_actual_samples=True,finite_numeric_derivatives=all(np.isfinite(v['position_J_W_m_per_rad']).all() and np.isfinite(v['normal_J_W_per_rad']).all() for v in samples),inputs_unchanged=all(sha(p)==h for p,h in inputs.items()));assert all(checks.values())
    result=dict(checks=checks,input_sha256=inputs,samples=samples,arm_joint_names=[names[i] for i in arm],all_saved_prediction_gates_passed=all(v['FK_prediction_gate_passed'] for v in samples),native_initializations=0,physics_steps=0,goal_policy=dict(plane_normal_G=outward.tolist(),normal_clearance_m=.0001,tangential_margin_m=.0031),scope='actual q to source FK diagnostic with t0 calibrated relative transforms and measured Chest motion; geometry angle derivative not PD/contact response; bounded geometric dq not executed or collision-certified; only actual point uses native pose; full support/restore/playing unproven')
    (PHASE/'analysis.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps(dict(checks=checks,prediction_gate=result['all_saved_prediction_gates_passed'],samples=[{k:s[k] for k in ('physics_step','max_body_position_error_mm','max_body_rotation_error_rad','palm_anchor_prediction_error_mm','source_point_error_before_mm','source_point_error_after_geometric_dq_mm','base_plus_dq_within_native_limits','base_plus_dq_initial_main_offsets_within0p3')} for s in samples]),indent=2))
if __name__=='__main__':main()
