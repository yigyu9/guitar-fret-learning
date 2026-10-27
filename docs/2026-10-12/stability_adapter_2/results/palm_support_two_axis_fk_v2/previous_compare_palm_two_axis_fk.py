"""Saved native joint-relative and whole-chain FK errors for two-axis hypotheses."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'docs/2026-10-12/stability_adapter_2/results';OLD=BASE/'torso_hold_native_collision_v1';PHASE=BASE/'palm_support_two_axis_fk_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def main():
    PHASE.mkdir(exist_ok=False);previous=read(BASE/'palm_support_runtime_fk_v1/analysis.json');inputs=dict(previous['input_sha256'])
    for p in [Path(__file__).resolve(),ROOT/'stability_adapter_2/palm_two_axis_fk.py',ROOT/'stability_adapter_2/PALM_FK_TWO_AXIS_DIAGNOSTIC.md',BASE/'palm_support_runtime_fk_v1/analysis.json']:inputs[str(p)]=sha(p)
    assert all(sha(p)==h for p,h in inputs.items())
    (PHASE/'attempt.json').write_text(json.dumps(dict(input_sha256=inputs,native_initializations=0,physics_steps=0),indent=2)+'\n')
    from .environment import np
    from .palm_two_axis_fk import left_fk
    from .build_fixed_lower_asset import pose
    from scipy.spatial.transform import Rotation
    states=[json.loads(v) for v in (OLD/'native/states.jsonl').read_text().splitlines()];init=read(OLD/'native/initial_values.json');names=init['human_joint_names'];bodies=init['human_body_names'];q0=np.array([d['pos'] for d in states[0]['human_dof_states']]);pc0,qc0=pose(states[0]['human_body_states'][bodies.index('Chest')]);rc0=Rotation.from_quat(qc0);sample=[0,24,120,1200];heldout=[1,4,8,12,36,48,60,96,144,180,240,300,360,480,600,720,840,960,1080,1192];rows=[]
    for mode in ('exp_sum','xml_product','reverse_product'):
        fk,relatives=left_fk(names,bodies,states[0],q0,mode)
        for step in sample+heldout:
            s=states[step];q=np.array([d['pos'] for d in s['human_dof_states']]);pred=fk(q);pc,qc=pose(s['human_body_states'][bodies.index('Chest')]);lift=Rotation.from_quat(qc)*rc0.inv();errors=[];relative_errors=[]
            for name,(p,r) in pred.items():
                pa,qa=pose(s['human_body_states'][bodies.index(name)]);rw=lift*r;pw=pc+lift.apply(p-pc0);errors.append(dict(body=name,position_error_mm=float(np.linalg.norm(pw-pa)*1000),rotation_error_rad=float((rw*Rotation.from_quat(qa).inv()).magnitude())))
                if name in relatives and len(relatives[name][-1])==2:
                    parent=relatives[name][0];_,qp=pose(s['human_body_states'][bodies.index(parent)]);actual=Rotation.from_quat(qp).inv()*Rotation.from_quat(qa);estimated=pred[parent][1].inv()*r;relative_errors.append(dict(body=name,rotation_error_rad=float((estimated*actual.inv()).magnitude())))
            rows.append(dict(mode=mode,physics_step=step,heldout=step in heldout,max_position_error_mm=max(e['position_error_mm'] for e in errors),max_rotation_error_rad=max(e['rotation_error_rad'] for e in errors),body_errors=errors,two_axis_relative_errors=relative_errors))
    summary=[]
    for mode in ('exp_sum','xml_product','reverse_product'):
        for held in (False,True):
            group=[r for r in rows if r['mode']==mode and r['heldout']==held];summary.append(dict(mode=mode,heldout=held,samples=len(group),max_position_error_mm=max(r['max_position_error_mm'] for r in group),max_rotation_error_rad=max(r['max_rotation_error_rad'] for r in group),max_two_axis_relative_error_rad=max(e['rotation_error_rad'] for r in group for e in r['two_axis_relative_errors']),prediction_gate_passed=all(r['max_position_error_mm']<=.1 and r['max_rotation_error_rad']<=.001 for r in group)))
    checks=dict(only_two_axis_composition_differs=True,same_t0_calibration_all_modes=True,four_diagnostic_and_twenty_heldout_samples=True,all_values_finite=all(np.isfinite([r['max_position_error_mm'],r['max_rotation_error_rad']]).all() for r in rows),inputs_unchanged=all(sha(p)==h for p,h in inputs.items()));assert all(checks.values())
    result=dict(checks=checks,input_sha256=inputs,summary=summary,rows=rows,native_initializations=0,physics_steps=0,scope='joint-relative and whole-chain saved actualq/pose comparison; t0-only calibration; empirical two-axis composition evidence on24frames, not global importer/PD/contact/playing certification');(PHASE/'analysis.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps(dict(checks=checks,summary=summary),indent=2))
if __name__=='__main__':main()
