"""Read-only analysis of three completed native trials; no simulation calls."""
import hashlib,json,subprocess
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parent
A=P.parents[4]/'stability_adapter_2'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,data):
 p=P/name
 if p.exists():raise FileExistsError(p)
 p.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
cases={'clear_reference':P/'native_v1/clear_reference','lean18_back30':P/'native_v1/lean18_back30','lean18_back30_hold_pi':P/'native_v2/lean18_back30_hold_pi'}
inputs={str(p):sha(p) for folder in cases.values() for p in folder.rglob('*') if p.is_file()}
inputs[str(Path(__file__).resolve())]=sha(__file__)
for p in [P/'source_before_native_v1.json',P/'hold_correction_config_v1.json',P/'search_v4/search.json']:
 inputs[str(p)]=sha(p)
save('analysis_inputs_before_v1.json',inputs)
checks={}; summaries={}
for label,folder in cases.items():
 attempt,report,trace,contacts,initial=[read(folder/f) for f in ['attempt.json','report.json','trace.json','contacts.json','initial_values.json']]
 pins=attempt['input_sha256'];bad=[p for p,h in pins.items() if sha(p)!=h]
 assert not bad,bad
 assert report['completed'] and report['physics_steps']==1200 and report['controls']==300
 assert not report['forbidden_calls'] and report['policy_calls']==report['checkpoint_loads']==0
 assert len(trace)==301 and len(contacts)==300
 assert all(np.isfinite(row['q_rad']).all() and np.isfinite(row['qdot_rad_s']).all() for row in trace)
 shapes=read(folder/'native_shapes.json');mass=read(folder/'native_properties.json')
 assert shapes['shape_count']==91 and len(shapes['body_names'])==39
 assert mass['setter_calls_before_initialization']==1 and mass['property_setter_rejections']==0
 gbody=shapes['shape_ranges'][shapes['body_names'].index('G:body')];assert gbody[1]==63
 capture=read(folder/'media/capture.json');assert len(capture['frames'])==151
 for frame in capture['frames']:
  assert frame['render_preserves_states']
  assert all(sha(p)==h for p,h in frame['image_sha256'].items())
 videos={}
 for name in ['whole_body','hands']:
  v=folder/'media'/f'{name}.mp4'
  probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames,r_frame_rate,duration','-of','json',str(v)]))['streams'][0]
  assert int(probe['nb_read_frames'])==151 and probe['r_frame_rate']=='30/1'
  videos[name]=probe
 counts={}
 for body in ['Chest','Spine','Torso','R_Shoulder','R_Thorax','R_Elbow','LH:palm','LH:thumb1','LH:thumb2','LH:thumb3']:
  presence=positive=0
  for row in contacts:
   matched=[c for c in row['contacts'] if 'guitar/G:body' in [c['body0_name'],c['body1_name']] and 'human/'+body in [c['body0_name'],c['body1_name']]]
   presence+=bool(matched);positive+=any(c['lambda']>0 for c in matched)
  counts[body]={'presence_samples':presence,'positive_raw_lambda_samples':positive,'total_samples':300}
 qgoal=np.array(initial['q_ref_rad']);qfinal=np.array(trace[-1]['q_rad']);qtarget=np.array(trace[-1]['submitted_target_rad'])
 late=[r for r in trace if r['time_s']>=2];p2=np.array(late[0]['position_W_m']);pf=np.array(trace[-1]['position_W_m'])
 from scipy.spatial.transform import Rotation
 rotation2final=(Rotation.from_quat(trace[-1]['quaternion_xyzw'])*Rotation.from_quat(late[0]['quaternion_xyzw']).inv()).magnitude()*180/np.pi
 summaries[label]={'final_position_change_mm':trace[-1]['position_change_m']*1000,'final_rotation_change_deg':trace[-1]['rotation_change_deg'],'max_position_change_mm':max(r['position_change_m'] for r in trace)*1000,'max_rotation_change_deg':max(r['rotation_change_deg'] for r in trace),'position_2s_to_5s_mm':float(np.linalg.norm(pf-p2)*1000),'rotation_2s_to_5s_deg':float(rotation2final),'native_contact_sample_counts':counts,'final_actual_minus_initial_goal_deg':dict(zip(initial['joint_names'],np.rad2deg(qfinal-qgoal).tolist())),'final_actual_minus_submitted_target_deg':dict(zip(initial['joint_names'],np.rad2deg(qfinal-qtarget).tolist())),'total_guitar_mass_kg':mass['total_mass_kg'],'videos':videos}
 checks[label]={'input_pins_unchanged':len(pins),'native_completed':True,'native_body_count':39,'shape_count':91,'body_convex_pieces':63,'render_state_invariance_samples':151,'forbidden_calls':[]}
# The control action is sampled before integration; its actual submitted target is in trace[k+1].
off=read(cases['lean18_back30']/'initial_values.json');on=read(cases['lean18_back30_hold_pi']/'initial_values.json')
assert off==on
checks['off_on_initial_exact']=True
controller=read(cases['lean18_back30_hold_pi']/'media/joint_hold_correction.json');trace=read(cases['lean18_back30_hold_pi']/'trace.json')
config=read(P/'hold_correction_config_v1.json');oldconfig=read(P/'search_v4/lean18_back30/config.json')
diff={k:[oldconfig.get(k),v] for k,v in config.items() if oldconfig.get(k)!=v};assert list(diff)==['target_rates_rad_s']
checks['off_on_config_difference']=diff
names=controller['joint_names'];goal=np.array(controller['initial_goal_rad']);cap=np.array(controller['residual_cap_rad']);dt=1/60
props=on['PD_properties'];lo=np.array(props['lower']);hi=np.array(props['upper']);lo[:9]=np.maximum(lo[:9],goal[:9]-np.deg2rad(5));hi[:9]=np.minimum(hi[:9],goal[:9]+np.deg2rad(5))
mid=(lo+hi)/2;half=(hi-lo)/2;integral=np.zeros(81)
groups=['body' if n.startswith(('Torso_','Spine_','Chest_')) else 'head' if n.startswith(('Neck_','Head_')) else 'finger' if n.startswith(('LH:','RH:')) else 'arm' for n in names]
rates=np.array([config['target_rates_rad_s'][g] for g in groups]);assert np.array_equal(cap,np.array([.05 if g=='body' else .3 if g=='arm' else 0 for g in groups]))
for k,row in enumerate(controller['rows']):
 actual=np.array(row['actual_q_rad']);assert np.array_equal(actual,np.array(trace[k]['q_rad']))
 error=goal-actual;integral=np.clip(integral+dt*error,-cap,cap);residual=np.clip(error+integral,-cap,cap);requested=np.clip(goal+residual,lo,hi);action=np.clip((requested-mid)/half,-1,1)
 for key,value in [('error_rad',error),('integral_rad',integral),('residual_rad',residual),('requested_target_rad',requested),('requested_action',action)]:assert np.allclose(row[key],value,atol=1e-12,rtol=0),key
 prev=np.array(trace[k]['submitted_target_rad']);target=np.clip(np.clip(mid+half*action,prev-rates*dt,prev+rates*dt),lo,hi).astype(np.float32)
 assert np.array_equal(target,np.array(trace[k+1]['submitted_target_rad']).astype(np.float32))
assert len(controller['rows'])==300
checks['controller_formula_and_actual_submission_exact_samples']=300
strap=read(cases['lean18_back30_hold_pi']/'media/strap_state_samples.json')['rows'];assert len(strap)==151
summaries['lean18_back30_hold_pi']['strap_saved_current_command_max_N']=max(r['current_enabled_calculated_tension_n'] for r in strap)
summaries['lean18_back30_hold_pi']['strap_saved_previous_step_command_max_N']=max(r['last_applied_tension_n'] or 0 for r in strap)
for r in strap:assert r['last_applied_at_physics_step']==(r['physics_step']-1 if r['physics_step'] else None)
for p,h in read(P/'source_before_native_v1.json').items():assert sha(p)==h
checks['pre_native_source_pins_unchanged']=True
checks['analysis_inputs_unchanged']=all(sha(p)==h for p,h in inputs.items());assert checks['analysis_inputs_unchanged']
save('verification_v1.json',{'passed':True,'native_runs':3,'physics_steps_total':3600,'checks':checks,'cases':summaries,'adopted_stable_pose':False,'limits':['Contacts report raw lambda, not calibrated newtons.','PI and arm target rate changed together.','HOLD leaf Markdown was path-recorded but not SHA-pinned before native; executed code/config pinned in attempt.','Source geometry distance is not cooked PhysX clearance certification.'],'hold_leaf_current_post_run_sha256':sha(A/'OM_AXILLA_HOLD_CORRECTION_PLAN_V1.md')})
print(json.dumps({k:{n:v for n,v in x.items() if n.startswith(('final_position','final_rotation','max_position','max_rotation','position_2s','rotation_2s'))} for k,x in summaries.items()},indent=2))
