"""Audit unchanged music prefix and human-only terminal retraction goals."""
import hashlib,json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
P=Path(__file__).resolve().parent
inputs={str(Path(__file__).resolve()):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
def load(p):
 inputs[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
 return json.loads(p.read_text())
c=load(P/'native/data/controls.json');t=load(P/'native/data/trace.json');v=load(P/'native/data/initial_values.json');pd=load(P/'native/data/PD_phase_properties.json')
b=load(P.parent/'strike_incremental_approach_v1/native/data/controls.json');bt=load(P.parent/'strike_incremental_approach_v1/native/data/trace.json');bpd=load(P.parent/'strike_incremental_approach_v1/native/data/PD_phase_properties.json')
hold=next(x for x in c if x['phase']=='HOLD');boundary=hold['time_s'];prefix=[x for x in c if x['time_s']<boundary]
assert prefix==b[:len(prefix)]
nt=[x for x in t if x['time_s']<=boundary];bn=[x for x in bt if x['time_s']<=boundary];assert nt==bn
assert pd[:-1]==bpd and pd[-1]['trigger']=='terminal_retraction'
assert pd[-1]['physics_step']==hold['before_physics_step']
assert pd[-1]['native_readback_properties']==v['PD_properties']
last=prefix[-1];held=np.asarray(last['final_targets_rad'],dtype=np.float32)
idx=hold['terminal_retraction']['joint_indices'];outside=np.setdiff1d(np.arange(81),idx)
lo=np.asarray(v['native_lower_rad'],dtype=np.float32);hi=np.asarray(v['native_upper_rad'],dtype=np.float32)
prev=held.copy();base_history=next(x for x in b if x['phase']=='HOLD')['source_history'];base_clock=hold['song_time_s'];anchor=np.asarray(hold['terminal_retraction']['anchor_G_m'])
previous_pick=np.asarray(last['phase_target_residual']['measured_pick_G_m']);previous_time=last['time_s'];error=0.;count=0;anchors=0
for r in c:
 if r['phase']!='HOLD':continue
 a=r['terminal_retraction'];pick=np.asarray(a['measured_pick_G_m']);time=a['measured_pick_time_s'];assert time==r['time_s']
 assert np.array_equal(anchor,a['anchor_G_m'])
 assert np.array_equal(pick[:2],anchor[:2]) if count==0 else True
 assert anchor[2]>=pick[2]+.03-1e-12 if count==0 else True
 velocity=(pick-previous_pick)/(time-previous_time);assert np.allclose(velocity,a['measured_pick_velocity_G_m_s'],atol=1e-12,rtol=0)
 feedback=-.1*velocity;length=float(np.linalg.norm(feedback))
 if length>.005:feedback*=.005/length
 assert np.allclose(feedback,a['feedback_G_m'],atol=1e-12,rtol=0) and np.linalg.norm(feedback)<=.005+1e-12
 assert np.allclose(anchor+feedback,a['servo_G_m'],atol=1e-12,rtol=0)
 assert np.array_equal(np.asarray(a['previous_actuator_targets_rad'],dtype=np.float32),prev[idx])
 correction=np.asarray(a['correction_rad']);assert np.max(abs(correction))<=.15+1e-12
 requested=np.asarray(r['requested_targets_rad'],dtype=np.float32);expected_goal=np.clip(prev[idx]+2*correction,lo[idx],hi[idx]).astype(np.float32)
 error=max(error,float(np.max(abs(requested[idx]-expected_goal))));assert np.array_equal(requested[idx],expected_goal)
 assert np.array_equal(requested[outside],held[outside])
 rate=np.full(81,.8,dtype=np.float32);rate[[i for i,n in enumerate(v['joint_names']) if n.startswith(('R_Shoulder','R_Elbow','R_Wrist','RH:'))]]=3.2
 final=np.asarray(r['final_targets_rad'],dtype=np.float32);assert np.array_equal(np.clip(np.clip(requested,prev-rate/60,prev+rate/60),lo,hi).astype(np.float32),final)
 assert np.array_equal(final[outside],held[outside])
 assert r['source_history']==base_history and r['song_time_s']==base_clock and not r['actor_used']
 matched=[x for x in t if x['physics_step']==r['before_physics_step']]
 if matched:
  st=matched[0]['native_state'];g=st['guitar_body_states'][0]['pose'];h=st['human_body_states'][v['human_body_names'].index('RH:pick')]['pose'];point=np.array([h['p'][k]-g['p'][k] for k in ('x','y','z')]);rot=Rotation.from_quat([g['r'][k] for k in ('x','y','z','w')]);assert np.allclose(rot.inv().apply(point),pick,atol=1e-7,rtol=0);anchors+=1
 previous_pick=pick;previous_time=time;prev=final;count+=1
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in inputs.items())
result={'input_sha256':inputs,'inputs_unchanged':True,'exact_PREP_PLAY_controls':len(prefix),'exact_native_trace_through_terminal':len(nt),'terminal_time_s':boundary,'PLAY_actor_steps':sum(x['actor_used'] for x in prefix),'baseline_PD_restore_exact':True,'HOLD_control_goal_formulas_verified':count,'HOLD_native_pick_anchors_verified':anchors,'HOLD_other72_goals_exact':True,'HOLD_source_clock_history_actor_frozen':True,'HOLD_goal_formula_max_error_rad':error,'scope':'stored human-joint goals and native sampled prefix/PD restoration; source timing/success criteria unchanged, no contact causality or guitar stabilization/fullsong certification'}
(P/'terminal_retraction_audit.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k!='input_sha256'})
