"""Compare preserved native repeat records; no new physical simulation."""
from pathlib import Path
import json,hashlib
import numpy as np
P=Path(__file__).resolve().parent
folders=[P/'native_v11/upper_arm_neck_side',P/'native_v12/upper_arm_neck_side_repeat']
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,data):
 with(P/name).open('x')as f:json.dump(data,f,indent=2,ensure_ascii=False,allow_nan=False)
files=[Path(__file__).resolve(),P/'effort_verification_v10_cases4.json']+[p/name for p in folders for name in ['initial_values.json','trace.json','contacts.json','report.json']]
inputs={str(p):sha(p)for p in files};save('support_repeat_inputs_before_v1.json',inputs)
initial=[read(p/'initial_values.json')for p in folders];traces=[read(p/'trace.json')for p in folders];metrics=read(P/'effort_verification_v10_cases4.json')['cases'];same={k:initial[0][k]==initial[1][k]for k in ['joint_names','q_ref_rad','PD_properties','mass_properties','native_initial_state']};assert all(same.values());assert traces[0]==traces[1]
rows={}
for p,i,t in zip(folders,initial,traces):
 delta=np.rad2deg(np.array([r['q_rad']for r in t])-np.array(i['q_ref_rad']));groups={}
 for label,prefix in [('몸통',('Torso','Spine','Chest')),('목·머리',('Neck','Head')),('오른팔',('R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))]:
  indices=[k for k,n in enumerate(i['joint_names'])if n.startswith(prefix)];groups[label]={'maximum_scalar_angle_deviation_deg':float(abs(delta[:,indices]).max()),'final_maximum_scalar_angle_deviation_deg':float(abs(delta[-1,indices]).max()),'scope':'native DOF scalar change from initial q; not body relative/world Euler rotation'}
 queries=read(p/'contacts.json');sampled=[r for r in queries if r['physics_step']>0];presence={};positive={}
 for r in sampled:
  seen=set();pos=set()
  for c in r['contacts']:
   names=[c['body0_name'],c['body1_name']]
   if any(n.startswith('guitar/')for n in names)and any(n.startswith('human/')for n in names):
    name=next(n for n in names if n.startswith('human/'));seen.add(name)
    if c['lambda']>0:pos.add(name)
  for name in seen:presence[name]=presence.get(name,0)+1
  for name in pos:positive[name]=positive.get(name,0)+1
 rows[p.name]={'verified_motion_and_endpoints':metrics[p.name],'native_DOF_scalar_deviations':groups,'human_guitar_control_queries':{'query_count':len(sampled),'steps':[r['physics_step']for r in sampled],'presence_queries_by_body':presence,'positive_raw_lambda_queries_by_body':positive,'scope':'60Hz queries at physics steps4..1196, not all-step force distribution or RH-finger contact exclusion'}}
assert all(sha(Path(p))==h for p,h in inputs.items());save('support_candidate_comparison_v1.json',{'passed':True,'initial_equal':same,'trace_exact_equal':True,'video_hash_exact_equal':all(metrics[folders[0].name]['videos'][v]['sha256']==metrics[folders[1].name]['videos'][v]['sha256']for v in ['whole_body','hands']),'cases':rows,'scope':'identical-condition five-second candidate repeat; no music, perturbation robustness or cooked penetration certification'})
print(json.dumps({'passed':True,'initial_equal':same,'trace_exact_equal':True,'cases':list(rows)},ensure_ascii=False))
