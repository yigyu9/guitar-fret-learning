"""Read-only goal ownership and preparation-prefix audit."""
import hashlib,json
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parent
inputs={str(Path(__file__).resolve()):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
def load(p):
 inputs[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
 return json.loads(p.read_text())
c=load(P/'native/data/controls.json');t=load(P/'native/data/trace.json');v=load(P/'native/data/initial_values.json')
b=load(P.parent/'strike_free_finger_curl_v1/native/data/controls.json');bt=load(P.parent/'strike_free_finger_curl_v1/native/data/trace.json')
first=next(x for x in c if x['actor_used']);bf=next(x for x in b if x['actor_used']);start=first['time_s']
fields=('time_s','phase','actor_used','requested_targets_rad','final_targets_rad','source_history','song_time_s','readiness')
prefix=[x for x in c if x['time_s']<start]
assert all({k:x.get(k) for k in fields}=={k:b[i].get(k) for k in fields} for i,x in enumerate(prefix))
tp=[x for x in t if x['time_s']<=start]
assert all(x['native_state']==bt[i]['native_state'] for i,x in enumerate(tp))
assert first['observation']==bf['observation'] and first['action']==bf['action']
lo=np.asarray(v['native_lower_rad'],dtype=np.float32);hi=np.asarray(v['native_upper_rad'],dtype=np.float32)
prev=np.asarray(v['initial_angles_rad'],dtype=np.float32);I=np.zeros(9);counts={'ready':0,'closed_approach':0,'open_approach':0,'recovery':0};err=0.
names=v['joint_names'];source=[i for i,n in enumerate(names) if n.startswith(('R_Shoulder','R_Elbow','R_Wrist','RH:'))]
for r in c:
 final=np.asarray(r['final_targets_rad'],dtype=np.float32)
 if r['actor_used']:
  a=r['phase_target_residual'];idx=a['joint_indices'];phase=a['source_motor_phase'];ready=phase==0 or (phase==1 and not a['adapter_approach_open'])
  assert a['ready_priority_active']==ready
  correction=np.asarray(a['correction_rad']);integral=np.asarray(a['integral_rad']);applied=np.asarray(a['applied_correction_rad']);policy=np.asarray(a['policy_targets_rad'],dtype=np.float32)
  assert np.array_equal(np.asarray(a['previous_actuator_targets_rad'],dtype=np.float32),prev[idx])
  if phase==2 or ready:
   assert np.array_equal(integral,I)
   assert np.array_equal(applied,2*correction)
   goal=np.clip(prev[idx]+applied,lo[idx],hi[idx])
   label='recovery' if phase==2 else ('ready' if phase==0 else 'closed_approach')
  else:
   assert phase==1 and a['adapter_approach_open']
   goal=np.clip(policy+np.clip(correction+integral,-.3,.3),lo[idx],hi[idx]);label='open_approach'
  requested=np.asarray(r['requested_targets_rad']);err=max(err,float(np.max(abs(goal-requested[idx]))));assert np.allclose(goal,requested[idx],atol=2e-7,rtol=0)
  rate=np.full(81,.8,dtype=np.float32);rate[source]=3.2
  expected=np.clip(np.clip(requested,prev-rate/60,prev+rate/60),lo,hi).astype(np.float32)
  assert np.array_equal(final,expected)
  I=integral;counts[label]+=1
 prev=final
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in inputs.items())
result={'input_sha256':inputs,'inputs_unchanged':True,'exact_prepare_controls':len(prefix),'exact_sampled_native_prefix':len(tp),'first_actor_observation_action_exact':True,'goal_owner_counts':counts,'goal_formula_max_error_rad':err,'ready_closed_recovery_integral_held':True,'native_rate_clip_final_goal_exact':True,'scope':'requested/final goal and sampled native prefix audit; no contact causality, source drive equivalence or fullsong success certification'}
(P/'goal_audit.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k!='input_sha256'})
