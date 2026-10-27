"""Summarize the two verified same-initial body-side support trials."""
from pathlib import Path
import json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
P=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
 with p.open('x')as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False)
def main():
 specs=[('forearm',P/'native_v1/right4_close_support',P/'analysis_v2/verification.json'),('forearm_upper_press',P/'native_v2/right4_close_support_upper_press',P/'analysis_v3/verification.json')]
 inputs={};cases={};initials=[]
 for label,folder,verification in specs:
  paths=[verification,folder/'initial_values.json',folder/'contacts.json',folder/'trace.json']
  for p in paths:inputs[str(p)]=sha(p)
  verified=read(verification);assert verified['passed'];metrics=verified['cases'][folder.name];initial=read(folder/'initial_values.json');initials.append(initial['native_initial_state']);contacts=read(folder/'contacts.json');assert len(contacts)==300 and [r['physics_step']for r in contacts]==list(range(0,1200,4))
  counts={}
  for name in ['R_Hip','L_Hip','Chest','R_Shoulder','R_Elbow']:
   rows=[[c for c in r['contacts']if 'human/'+name in(c['body0_name'],c['body1_name'])and'guitar/G:body'in(c['body0_name'],c['body1_name'])]for r in contacts]
   counts[name]={'presence_samples':sum(bool(r)for r in rows),'positive_raw_lambda_samples':sum(any(c['lambda']>0 for c in r)for r in rows),'total_samples':300,'sample_basis':'before control:0..1196 physics steps at60Hz; distinct from1200after-step endpoints'}
  trace=read(folder/'trace.json');angles=[]
  for t in trace:
   neck=Rotation.from_quat(t['quaternion_xyzw']).apply([0.,1.,0.]);angles.append(float(np.rad2deg(np.arcsin(np.clip(neck[2],-1,1)))))
  cases[label]={'folder':str(folder),'verification':str(verification),'metrics':metrics,'body_contacts_60Hz':counts,'neck_G_plus_Y_elevation_deg':{'initial':angles[0],'final':angles[-1],'minimum':min(angles),'maximum':max(angles),'definition':'G+Y from body toward neck, signed angle above world horizontal; not SO3 magnitude'},'decision':'initial guitar orientation not maintained; no stable final pose adopted'}
 assert initials[0]==initials[1]
 assert all(sha(Path(p))==h for p,h in inputs.items())
 save(P/'result_summary_v1.json',{'passed_record_checks':True,'same_full_native_initial_state_between_trials':True,'direction':'player right = frontal screen left = guitar body side; additional Chest4deg,Torso1deg,Spine2.5deg from accepted natural-arm base','cases':cases,'inputs_sha256':inputs,'scope':'contacts presence/rawlambda do not quantify support force; initial pose fit uses source geometry; no playing/checkpoints/training in this phase'})
 print(json.dumps({k:{'centre_mm':v['metrics']['final_body_bbox_centre_change_mm'],'rotation_deg':v['metrics']['final_rotation_change_deg'],'neck':v['neck_G_plus_Y_elevation_deg'],'hip':v['body_contacts_60Hz']['R_Hip']}for k,v in cases.items()},indent=2))
if __name__=='__main__':main()
