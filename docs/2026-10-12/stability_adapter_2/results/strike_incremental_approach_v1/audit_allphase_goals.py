"""Read-only velocity feedback, goal ownership and sampled native prefix audit."""
import hashlib,json
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parent
inputs={str(Path(__file__).resolve()):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
def load(p):
 inputs[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
 return json.loads(p.read_text())
c=load(P/'native/data/controls.json');t=load(P/'native/data/trace.json');v=load(P/'native/data/initial_values.json')
b=load(P.parent/'strike_waypoint_velocity_v1/native/data/controls.json');bt=load(P.parent/'strike_waypoint_velocity_v1/native/data/trace.json')
first=next(x for x in c if x['actor_used']);bf=next(x for x in b if x['actor_used']);start=first['time_s']
fields=('time_s','phase','actor_used','requested_targets_rad','final_targets_rad','source_history','song_time_s','readiness')
prefix=[x for x in c if x['time_s']<start]
assert all({k:x.get(k) for k in fields}=={k:b[i].get(k) for k in fields} for i,x in enumerate(prefix))
tp=[x for x in t if x['time_s']<=start]
assert all(x['native_state']==bt[i]['native_state'] for i,x in enumerate(tp))
assert first['observation']==bf['observation'] and first['action']==bf['action']
first_open=next((x for x in c if x['actor_used'] and x['phase_target_residual']['source_motor_phase']==1 and x['phase_target_residual']['adapter_approach_open']),None)
exact_until_open=None
if first_open is not None:
 boundary=first_open['time_s']
 extended=[x for x in c if x['time_s']<boundary]
 selected=fields+('observation','action','info','done')
 assert all({k:x.get(k) for k in selected}=={k:b[i].get(k) for k in selected} for i,x in enumerate(extended))
 pre_native=[x for x in t if x['time_s']<=boundary]
 assert all(x['native_state']==bt[i]['native_state'] for i,x in enumerate(pre_native))
 base_open=next(x for x in b if x['time_s']==boundary)
 assert first_open['observation']==base_open['observation'] and first_open['action']==base_open['action']
 exact_until_open={'first_open_time_s':boundary,'controls_before_open':len(extended),'sampled_native_states_through_open':len(pre_native),'first_open_actor_observation_action_exact':True}
lo=np.asarray(v['native_lower_rad'],dtype=np.float32);hi=np.asarray(v['native_upper_rad'],dtype=np.float32)
previous_pick=None;previous_time=None;velocity_count=0;velocity_error=0.;feedback_error=0.;native_anchor_count=0
prev=np.asarray(v['initial_angles_rad'],dtype=np.float32);I=np.zeros(9);counts={'ready':0,'closed_approach':0,'open_approach':0,'recovery':0};err=0.
names=v['joint_names'];source=[i for i,n in enumerate(names) if n.startswith(('R_Shoulder','R_Elbow','R_Wrist','RH:'))]
for r in c:
 final=np.asarray(r['final_targets_rad'],dtype=np.float32)
 if r['actor_used']:
  a=r['phase_target_residual'];idx=a['joint_indices'];phase=a['source_motor_phase'];ready=phase==0 or (phase==1 and not a['adapter_approach_open'])
  pick=np.asarray(a['measured_pick_G_m']);time=a['measured_pick_time_s'];assert time==r['time_s']
  velocity=np.zeros(3) if previous_pick is None else (pick-previous_pick)/(time-previous_time)
  velocity_error=max(velocity_error,float(np.max(abs(velocity-np.asarray(a['measured_pick_velocity_G_m_s'])))))
  assert np.allclose(velocity,a['measured_pick_velocity_G_m_s'],atol=1e-12,rtol=0)
  active=phase in (0,2) or (phase==1 and not a['adapter_approach_open']);assert active==a['velocity_feedback_active']
  feedback=-.1*velocity if active else np.zeros(3)
  length=float(np.linalg.norm(feedback))
  if length>.005:feedback*=.005/length
  feedback_error=max(feedback_error,float(np.max(abs(feedback-np.asarray(a['velocity_feedback_G_m'])))))
  assert np.allclose(feedback,a['velocity_feedback_G_m'],atol=1e-12,rtol=0)
  assert np.linalg.norm(feedback)<=.005+1e-12
  assert np.allclose(np.asarray(a['source_waypoint_G_m'])+feedback,a['target_G_m'],atol=1e-12,rtol=0)
  if not active:assert np.all(feedback==0)
  previous_pick=pick;previous_time=time;velocity_count+=1
  matched=[x for x in t if x['physics_step']==r['before_physics_step']]
  if matched:
   from scipy.spatial.transform import Rotation
   state=matched[0]['native_state'];g=state['guitar_body_states'][0]['pose'];h=state['human_body_states'][v['human_body_names'].index('RH:pick')]['pose']
   point=np.array([h['p'][k]-g['p'][k] for k in ('x','y','z')]);rot=Rotation.from_quat([g['r'][k] for k in ('x','y','z','w')])
   assert np.allclose(rot.inv().apply(point),pick,atol=1e-7,rtol=0);native_anchor_count+=1
  assert a['ready_priority_active']==ready
  correction=np.asarray(a['correction_rad']);integral=np.asarray(a['integral_rad']);applied=np.asarray(a['applied_correction_rad']);policy=np.asarray(a['policy_targets_rad'],dtype=np.float32)
  assert np.array_equal(np.asarray(a['previous_actuator_targets_rad'],dtype=np.float32),prev[idx])
  assert a['geometry_arm_priority_active']
  assert np.array_equal(integral,I) and np.all(integral==0)
  assert np.array_equal(applied,2*correction)
  goal=np.clip(prev[idx]+applied,lo[idx],hi[idx])
  label='recovery' if phase==2 else ('ready' if phase==0 else ('closed_approach' if not a['adapter_approach_open'] else 'open_approach'))
  requested=np.asarray(r['requested_targets_rad']);err=max(err,float(np.max(abs(goal-requested[idx]))));assert np.allclose(goal,requested[idx],atol=2e-7,rtol=0)
  rate=np.full(81,.8,dtype=np.float32);rate[source]=3.2
  expected=np.clip(np.clip(requested,prev-rate/60,prev+rate/60),lo,hi).astype(np.float32)
  assert np.array_equal(final,expected)
  I=integral;counts[label]+=1
 prev=final
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in inputs.items())
result={'input_sha256':inputs,'inputs_unchanged':True,'exact_prepare_controls':len(prefix),'exact_sampled_native_prefix':len(tp),'first_actor_observation_action_exact':True,'exact_until_first_open_approach':exact_until_open,'goal_owner_counts':counts,'goal_formula_max_error_rad':err,'velocity_records_verified':velocity_count,'sampled_native_pick_anchors_verified':native_anchor_count,'velocity_formula_max_error_m_s':velocity_error,'feedback_formula_max_error_m':feedback_error,'feedback_max_m':.005,'allphase_integral_held_zero':True,'policy_arm_goals_logged_only':True,'native_rate_clip_final_goal_exact':True,'scope':'finite-difference and bounded servo feedback, requested/final goal and sampled native prefix audit; no contact causality, source drive equivalence or fullsong success certification'}
(P/'allphase_goal_audit.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k!='input_sha256'})
