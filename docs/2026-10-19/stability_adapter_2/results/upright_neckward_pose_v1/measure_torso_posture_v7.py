"""Measure native chest facing and anatomical chest-to-neck inclination, including baseline."""
from pathlib import Path
import json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
P=Path(__file__).resolve().parent;R=P.parents[4];OLD=P.parent/'neckward_torso_turn_v1/native_v1/static_neckyaw12';BASE=P.parent/'natural_right_arm_v1/native_v2/front160mm/initial_values.json'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def vec(v):return np.array([v[k]for k in 'xyz'])
def pose(s):return vec(s['pose']['p']),Rotation.from_quat([s['pose']['r'][k]for k in 'xyzw'])
def save(p,x):
 with p.open('x')as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False)
def main():
 original=read(BASE);ps={n:pose(s)for n,s in zip(original['human_body_names'],original['native_initial_state']['human_body_states'])};up=ps['Neck'][0]-ps['Chest'][0];up/=np.linalg.norm(up);right=ps['R_Thorax'][0]-ps['L_Thorax'][0];right/=np.linalg.norm(right);front=np.cross(up,right);front/=np.linalg.norm(front);local_up=ps['Chest'][1].inv().apply(up);local_front=ps['Chest'][1].inv().apply(front);inputs={str(Path(__file__).resolve()):sha(Path(__file__).resolve()),str(BASE):sha(BASE)};cases={}
 for folder in [OLD]+[f.parent for f in sorted(P.glob('native_v*/*/report.json'))]:
  ip=folder/'initial_values.json';ep=folder/'media/physics_endpoint_contacts.json';inputs[str(ip)]=sha(ip);inputs[str(ep)]=sha(ep);initial=read(ip);chest=initial['native_initial_state']['human_body_states'][initial['human_body_names'].index('Chest')];rows=[]
  for step,body in [(0,chest)]+[(e['physics_step'],e['human_body_states']['Chest'])for e in read(ep)['rows']]:
   _,rot=pose(body);u=rot.apply(local_up);f=rot.apply(local_front);heading=float(np.rad2deg(np.arctan2(-f[0],f[1])));forward=float(np.rad2deg(np.arctan2(u[1],u[2])));side=float(np.rad2deg(np.arctan2(u[0],u[2])));inclination=float(np.rad2deg(np.arctan2(np.linalg.norm(u[:2]),u[2])));rows.append({'time_s':step/240,'chest_facing_yaw_from_guitar_front_deg':heading,'chest_to_neck_forward_inclination_deg':forward,'chest_to_neck_right_inclination_deg':side,'chest_to_neck_total_inclination_deg':inclination})
  cases[folder.name]={'folder':str(folder),'initial':rows[0],'final':rows[-1],'trace':rows,'interpretation':'native Chest rigid-body rotation transporting original anatomical chest-to-neck vector and perpendicular frontal vector; heading from+Y toward-X is positive, inclination positive+Y/right+X; not scalar q or additional source bend'}
 baseline=cases['static_neckyaw12'];
 for n,c in cases.items():
  if n!='static_neckyaw12':c['final_minus_previous_stable_deg']={k:c['final'][k]-baseline['final'][k]for k in c['final']if k!='time_s'}
 assert all(sha(Path(p))==h for p,h in inputs.items());save(P/'torso_posture_v7.json',{'input_sha256':inputs,'original_chest_to_neck_unit_local':local_up.tolist(),'original_chest_front_unit_local':local_front.tolist(),'cases':cases,'scope':'native orientation evidence for visual torso changes, not muscle realism or naturalness certification'});print(json.dumps({n:{'initial':c['initial'],'final':c['final'],'final_minus_previous_stable_deg':c.get('final_minus_previous_stable_deg')}for n,c in cases.items()},indent=2))
if __name__=='__main__':main()
