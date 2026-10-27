"""Cross-trial native initial invariants and posture change checks."""
import json,hashlib
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
P=Path(__file__).resolve().parent;inputs={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):inputs[str(p)]=sha(p);return json.loads(p.read_text())
inputs[str(Path(__file__))]=sha(__file__);v=read(P/'verification_v2.json');batch=read(P/'native_v2/batch_report.json');data=[read(Path(r['output'])/'initial_values.json') for r in batch['records']];base=data[0];q0=np.array(base['q_ref_rad']);unchanged=np.array([i for i,n in enumerate(base['joint_names']) if n.startswith(('Neck_','Head_','LH:','RH:'))]);body=np.array([i for i,n in enumerate(base['joint_names']) if n.startswith(('Torso_','Spine_','Chest_'))]);arm=np.array([i for i,n in enumerate(base['joint_names']) if n.startswith(('L_','R_'))]);checks={'native_audit_passed':v['passed'],'same_initial_guitar_state':all(d['native_initial_state']['guitar_body_states']==base['native_initial_state']['guitar_body_states'] for d in data),'same_PD_properties':all(d['PD_properties']==base['PD_properties'] for d in data),'finger_head_initial_q_exact':all(np.array_equal(np.array(d['q_ref_rad'])[unchanged],q0[unchanged]) for d in data),'initial_torso_delta_bounded5deg':all(abs(np.array(d['q_ref_rad'])[body]-q0[body]).max()<=np.deg2rad(5)+1e-7 for d in data),'initial_arm_delta_bounded_point3rad':all(abs(np.array(d['q_ref_rad'])[arm]-q0[arm]).max()<=.3+1e-7 for d in data),'same_original_strap_rest_law':all(all(d['strap_initial'][k]==base['strap_initial'][k] for k in ('rest_length_m','k_n_m','c_n_s_m','cap_n','enabled')) for d in data)}
angles=[];ib=base['human_body_names'].index('Chest');rb=Rotation.from_quat([base['native_initial_state']['human_body_states'][ib]['pose']['r'][k] for k in 'xyzw'])
for record,d in zip(batch['records'],data):
 r=Rotation.from_quat([d['native_initial_state']['human_body_states'][ib]['pose']['r'][k] for k in 'xyzw']);delta=(r*rb.inv()).as_rotvec();angles.append({'label':record['label'],'native_Chest_delta_SO3_deg':float(np.rad2deg(np.linalg.norm(delta))),'native_forward_Chest_delta_deg':float(np.rad2deg(delta@np.array([-1,0,0])))})
checks['initial_Chest_0_0_3_5deg']=all(abs(row['native_forward_Chest_delta_deg']-want)<.01 for row,want in zip(angles,(0,0,3,5)))
with (P/'same_conditions_verification_v1.json').open('x') as f:json.dump({'passed':all(checks.values()),'checks':checks,'input_sha256':inputs,'initial_Chest_angles':angles,'scope':'native initial p/q/PD/finger-head/strap invariants; same static q_ref rule, no CP/music/policy'},f,ensure_ascii=False,indent=2)
print({'passed':all(checks.values()),'checks':len(checks),'angles':angles});assert all(checks.values()),checks
