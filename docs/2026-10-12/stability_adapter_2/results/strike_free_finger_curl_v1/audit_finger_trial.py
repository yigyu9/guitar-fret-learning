"""Read-only native prefix and requested/final finger goal audit."""
import hashlib,json
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parent
R=P.parent
inputs={str(Path(__file__).resolve()):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
def load(p):
 inputs[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
 return json.loads(p.read_text())
c=load(P/'native/data/controls.json');t=load(P/'native/data/trace.json');v=load(P/'native/data/initial_values.json')
b=load(R/'strike_timed_wait_rebase_v1/native/data/controls.json');bt=load(R/'strike_timed_wait_rebase_v1/native/data/trace.json')
n=v['joint_names'];curl=[n.index(k) for k in ('RH:middle2','RH:middle3','RH:ring2','RH:ring3')];fingers=[i for i,k in enumerate(n) if k.startswith('RH:')];other=[i for i in fingers if i not in curl]
first=next(x for x in c if x['actor_used']);bf=next(x for x in b if x['actor_used']);start=first['time_s']
fields=('time_s','phase','actor_used','requested_targets_rad','final_targets_rad','source_history','song_time_s','readiness')
prefix=[x for x in c if x['time_s']<start]
assert all({k:x.get(k) for k in fields}=={k:b[i].get(k) for k in fields} for i,x in enumerate(prefix))
tp=[x for x in t if x['time_s']<=start]
assert all(x['native_state']==bt[i]['native_state'] for i,x in enumerate(tp))
assert first['observation']==bf['observation'] and first['action']==bf['action']
lo=np.asarray(v['native_lower_rad'],dtype=np.float32);hi=np.asarray(v['native_upper_rad'],dtype=np.float32)
prev=np.asarray(v['initial_angles_rad'],dtype=np.float32);err=0.;count=0;maxrate=0.
for x in c:
 final=np.asarray(x['final_targets_rad'],dtype=np.float32)
 if x['actor_used']:
  a=x['free_finger_curl'];ids=a['source_finger_joint_indices'];src=np.asarray(a['source_finger_targets_rad'],dtype=np.float32);req=np.asarray(x['requested_targets_rad'],dtype=np.float32)
  assert ids==fingers
  expected=src.copy()
  for i in curl:expected[ids.index(i)]+=np.float32(.2)
  assert np.array_equal(req[fingers],expected)
  assert np.array_equal(req[other],src[[ids.index(i) for i in other]])
  err=max(err,float(np.max(abs(req[curl]-src[[ids.index(i) for i in curl]]-.2))))
  rate=np.full(81,.8,dtype=np.float32)
  rate[[i for i,k in enumerate(n) if k.startswith(('R_Shoulder','R_Elbow','R_Wrist','RH:'))]]=3.2
  computed=np.clip(np.clip(req,prev-rate/60,prev+rate/60),lo,hi).astype(np.float32)
  assert np.array_equal(computed,final)
  maxrate=max(maxrate,float(np.max(abs(final-prev))))
  count+=1
 assert np.all(final>=lo) and np.all(final<=hi)
 prev=final
assert count==155
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in inputs.items())
result={'input_sha256':inputs,'inputs_unchanged':True,'exact_prepare_controls':len(prefix),'exact_sampled_native_prefix':len(tp),'first_actor_observation_action_exact':True,'PLAY_requested_finger_goals_verified':count,'curl_indices':curl,'other17_requested_policy_exact':True,'native_rate_clip_final_goal_exact':True,'maximum_curl_delta_float_error_rad':err,'max_PLAY_final_step_rad':maxrate,'scope':'sampled prefix and requested/final joint goals; source finger4 adapter residual, not full30 policy equivalence; no contact causality or fullsong success proof'}
(P/'finger_audit.json').write_text(json.dumps(result,indent=2)+'\n')
print({k:v for k,v in result.items() if k!='input_sha256'})
