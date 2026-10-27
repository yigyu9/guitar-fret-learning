"""Validate arm/conditional hinges on saved native frames, then check the 18D map."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from .coupled_support_source import (ARM_BODIES, HINGES, CoupledSnapshot,
                                     anchor_catalog, features, np, Rotation, pose)

ROOT=Path(__file__).resolve().parents[1]
B=ROOT/'docs/2026-10-12/stability_adapter_2/results'
OLD=B/'body9_strap_minus2mm_v1'; P=B/'coupled_support_source_v1'
STEPS=(0,24,120,1200,1,4,8,12,36,48,60,96,144,180,240,300,360,480,600,720,840,960,1080,1192)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def main():
    P.mkdir(exist_ok=False)
    inputs=dict(read(OLD/'analysis.json')['input_sha256'])
    for relative in ['check_coupled_support_model.py','coupled_support_source.py','COUPLED_SUPPORT_SOURCE_EXECUTION.md','PALM_FINGER_COUPLED_SOURCE_PLAN.md','STRAP_MINUS4MM_DECISION.md','search_multi_face_grip.py','build_fixed_lower_asset.py','environment.py']:
        p=ROOT/'stability_adapter_2'/relative;inputs[str(p)]=sha(p)
    for p in [OLD/'analysis.json',OLD/'proposal.json',ROOT/'tab2body/assets/smpl_mpl_hands_body.xml',B/'palm_single_hinge_pose_v1/analysis.json']:
        inputs[str(p)]=sha(p)
    assert all(sha(p)==h for p,h in inputs.items())
    (P/'attempt.json').write_text(json.dumps(dict(input_sha256=inputs,native_initializations=0,physics_steps=0),indent=2)+'\n')
    init=read(OLD/'native/initial_values.json'); states=[json.loads(v) for v in (OLD/'native/states.jsonl').read_text().splitlines()]
    anchors=anchor_catalog(read(OLD/'proposal.json')); names=init['human_joint_names']; bodies=init['human_body_names']
    xml=ET.parse(ROOT/'tab2body/assets/smpl_mpl_hands_body.xml').getroot()
    parents={c:p for p in xml.iter('body') for c in p.findall('body')}
    calibration={}
    base=CoupledSnapshot(names,bodies,states[0],states[0])
    for name in HINGES:
        node=next(b for b in xml.iter('body') if b.get('name')==name);parent=parents[node].get('name')
        pp,pr=base.actual[parent];cp,cr=base.actual[name]
        calibration[name]=(parent,pr.inv().apply(cp-pp),pr.inv()*cr,np.fromstring(node.find('joint').get('axis'),sep=' '),base.q[names.index(name)])
    validation=[];samples=[]
    for step in STEPS:
        snap=CoupledSnapshot(names,bodies,states[0],states[step])
        predicted=snap.arm_at(snap.q)
        for name in ARM_BODIES+HINGES:
            if name in HINGES:
                parent,rp,rr,axis,a0=calibration[name];pp,pr=snap.actual[parent]
                predp=pp+pr.apply(rp);predr=pr*Rotation.from_rotvec(axis*(snap.q[names.index(name)]-a0))*rr
            else:predp,predr=predicted[name]
            actualp,actualr=snap.actual[name]
            pe=float(np.linalg.norm(predp-actualp)*1000);re=float((predr*actualr.inv()).magnitude())
            validation.append(dict(step=step,body=name,position_error_mm=pe,rotation_error_rad=re,passed=pe<=.1 and re<=.001,scope='actual parent supplied for hinge; t0 arm calibration with measured Chest'))
        if step not in (0,24,120,1200):continue
        zero=snap.poses(np.zeros(18));identity_p=max(np.linalg.norm(p-snap.actual[n][0]) for n,(p,r) in zero.items());identity_r=max((r*snap.actual[n][1].inv()).magnitude() for n,(p,r) in zero.items())
        jac=[]
        for h in (.0001,.00005):
            columns=[]
            for j in range(18):
                d=np.zeros(18);d[j]=h
                columns.append((features(snap,d,anchors)-features(snap,-d,anchors))/(2*h))
            jac.append(np.column_stack(columns))
        error=float(np.max(abs(jac[0]-jac[1])))
        samples.append(dict(step=step,selected_names=snap.selected,identity_position_error_m=float(identity_p),identity_rotation_error_rad=float(identity_r),features_W=features(snap,np.zeros(18),anchors).tolist(),feature_J_W_per_rad=jac[0].tolist(),central_half_step_max_difference=error,column_norms=np.linalg.norm(jac[0],axis=0).tolist()))
    checks=dict(saved24x11_predictions_pass=len(validation)==264 and all(r['passed'] for r in validation),four_identity_poses=all(r['identity_position_error_m']<1e-12 and r['identity_rotation_error_rad']<1e-12 for r in samples),eighteen_nonzero_finite_columns=all(np.isfinite(r['feature_J_W_per_rad']).all() and min(r['column_norms'])>1e-8 for r in samples),central_half_step_agreement=all(r['central_half_step_max_difference']<1e-6 for r in samples),inputs_unchanged=all(sha(p)==h for p,h in inputs.items()))
    result=dict(checks=checks,input_sha256=inputs,validation=validation,samples=samples,selected_names=base.selected,native_initializations=0,physics_steps=0,scope='conditional current measured finger1 relations; not global finger FK, future PD/contact response or native grip certification')
    (P/'model.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(checks=checks,max_position_error_mm=max(r['position_error_mm'] for r in validation),max_rotation_error_rad=max(r['rotation_error_rad'] for r in validation)),indent=2))
    assert all(checks.values()),checks
if __name__=='__main__':main()
