"""Compare two completed native neutral-policy evaluations; no rerun."""
import hashlib,json,math
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parent
inputs={}
def load(p):
 inputs[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest();return json.loads(p.read_text())
inputs[str(Path(__file__).resolve())]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
results={};initial=[]
for label,root in [('before',P.parent/'stability_update_correction_v1/smoke_on_v1'),('support_guard',P/'smoke_on_v2'),('after_one_update',P/'smoke_on_v2')]:
 base=root/('evaluations/update_000001/native/episode_0001' if label=='after_one_update' else 'evaluations/initial_000000/native/episode_0001')
 rows=load(base/'controls.json');trace=load(base/'trace.json');nr=load(base/'report.json');iv=load(base/'initial_values.json');initial.append(iv['native_initial_state'])
 d=np.linalg.norm([r['position_outside_m'] for r in rows],axis=1)
 p=np.array([r['position_W_m'] for r in trace]);q=np.array([r['quaternion_xyzw'] for r in trace]);q/=np.linalg.norm(q,axis=1)[:,None]
 rotation=2*np.arccos(np.clip(np.abs(q@q[0]),0,1))
 results[label]={'outside_percent':100*float(np.mean(d>0)),'max_position_outside_norm_m':float(max(d)),
 'max_displacement_from_initial_root_m':float(max(np.linalg.norm(p-p[0],axis=1))),
 'max_SO3_rotation_from_initial_deg':float(np.degrees(max(rotation))),
 'full_horizon_completed':nr['full_horizon_completed'],'physics_seconds':nr['physics_seconds'],
 'joint_success_events':nr['joint_success_events'],'accepted_crossings':nr['accepted_crossings'],
 'safety_violation':nr['safety_violation'],'videos':nr['videos']}
result={'inputs_unchanged':all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in inputs.items()),
 'native_initial_state_equal':all(i==initial[0] for i in initial),'evaluations':results,'input_sha256':inputs,
 'scope':'single deterministic neutral evaluations; guitar actor root position box and rotation-from-initial, not body-center naturalness certification; support_guard initial and after_one_update completed; long training excluded'}
with (P/'comparison_v2.json').open('x') as f:json.dump(result,f,indent=2,ensure_ascii=False)
print(json.dumps(result['evaluations'],ensure_ascii=False))
