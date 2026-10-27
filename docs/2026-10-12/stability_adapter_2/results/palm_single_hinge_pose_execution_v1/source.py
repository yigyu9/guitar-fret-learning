"""Conditional native-parent + scalarq to child pose on saved frames; no new physics."""
import hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'docs/2026-10-12/stability_adapter_2/results';OLD=BASE/'torso_hold_native_collision_v1';PHASE=BASE/'palm_single_hinge_pose_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def main():
    PHASE.mkdir(exist_ok=False);previous=read(BASE/'palm_measured_geometry_v1/analysis.json');inputs=dict(previous['input_sha256'])
    for p in [Path(__file__).resolve(),ROOT/'stability_adapter_2/PALM_SINGLE_HINGE_CHECK_PLAN.md',BASE/'palm_measured_geometry_v1/analysis.json']:inputs[str(p)]=sha(p)
    assert all(sha(p)==h for p,h in inputs.items());(PHASE/'attempt.json').write_text(json.dumps(dict(input_sha256=inputs,native_initializations=0,physics_steps=0),indent=2)+'\n')
    from .environment import np
    from .build_fixed_lower_asset import pose
    from scipy.spatial.transform import Rotation
    init=read(OLD/'native/initial_values.json');states=[json.loads(v) for v in (OLD/'native/states.jsonl').read_text().splitlines()];names=init['human_joint_names'];bodies=init['human_body_names'];xml=ET.parse(ROOT/'tab2body/assets/smpl_mpl_hands_body.xml').getroot();parents={c:p for p in xml.iter('body') for c in p.findall('body')};rows=[]
    steps=[0,24,120,1200,1,4,8,12,36,48,60,96,144,180,240,300,360,480,600,720,840,960,1080,1192]
    for name in ('LH:thumb2','LH:thumb3','LH:index2','LH:index3','LH:middle2','LH:middle3'):
        body=next(b for b in xml.iter('body') if b.get('name')==name);joints=body.findall('joint');assert len(joints)==1;axis=np.fromstring(joints[0].get('axis'),sep=' ');joint=joints[0].get('name');parent=parents[body].get('name');p0,q0=pose(states[0]['human_body_states'][bodies.index(parent)]);c0,r0=pose(states[0]['human_body_states'][bodies.index(name)]);R0=Rotation.from_quat(q0);relativep=R0.inv().apply(c0-p0);relativer=R0.inv()*Rotation.from_quat(r0);j=names.index(joint);a0=states[0]['human_dof_states'][j]['pos']
        for step in steps:
            s=states[step];p,q=pose(s['human_body_states'][bodies.index(parent)]);c,r=pose(s['human_body_states'][bodies.index(name)]);R=Rotation.from_quat(q);a=s['human_dof_states'][j]['pos'];predp=p+R.apply(relativep);predr=R*Rotation.from_rotvec(axis*a)*Rotation.from_rotvec(axis*a0).inv()*relativer;pe=float(np.linalg.norm(predp-c)*1000);re=float((predr*Rotation.from_quat(r).inv()).magnitude());rows.append(dict(body=name,joint=joint,parent=parent,physics_step=step,heldout=step not in (0,24,120,1200),actual_scalar_q_rad=a,position_error_mm=pe,rotation_error_rad=re,gate_passed=pe<=.1 and re<=.001))
    summary=[dict(body=name,max_position_error_mm=max(r['position_error_mm'] for r in rows if r['body']==name),max_rotation_error_rad=max(r['rotation_error_rad'] for r in rows if r['body']==name),all24_gates_passed=all(r['gate_passed'] for r in rows if r['body']==name)) for name in ('LH:thumb2','LH:thumb3','LH:index2','LH:index3','LH:middle2','LH:middle3')];checks=dict(six_single_axis_MJCF_bodies=True,t0_only_relative_calibration_and_actual_parent=True,one_hundred_forty_four_saved_observations=len(rows)==144,inputs_unchanged=all(sha(p)==h for p,h in inputs.items()));assert all(checks.values());result=dict(checks=checks,input_sha256=inputs,rows=rows,summary=summary,all_conditional_single_hinge_gates_passed=all(r['gate_passed'] for r in rows),native_initializations=0,physics_steps=0,scope='actual native parent pose supplied; scalar joint relation and unchanged t0 relative rest predict child pose; no whole-hand trajectory/PD/contact/global importer or physical grip certification');(PHASE/'analysis.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps(dict(checks=checks,summary=summary),indent=2))
if __name__=='__main__':main()
