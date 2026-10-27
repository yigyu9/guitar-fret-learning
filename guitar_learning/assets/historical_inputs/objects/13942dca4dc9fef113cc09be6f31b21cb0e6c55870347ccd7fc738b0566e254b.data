"""Analyze completed height trials without rerunning physics or changing inputs."""
from pathlib import Path
import json,hashlib,subprocess
import numpy as np
from scipy.spatial.transform import Rotation
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'docs/2026-10-12/stability_adapter_2/results/om_thigh_height_initial_v1'
OLD=ROOT/'docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1/native_v1/lean18_back30'

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False)

def main():
 folders={'previous_high':OLD,'thigh_gap8mm':P/'native_v1/thigh_gap8mm','thigh_gap3mm':P/'native_v1/thigh_gap3mm'}
 direct=[Path(__file__).resolve(),P/'search_v1/search.json',P/'search_v2/search.json',P/'preflight_inputs_v1.json']
 direct += [p for folder in folders.values() for p in folder.rglob('*') if p.is_file()]
 inputs={str(p):sha(p) for p in direct};save(P/'analysis_inputs_before_v1.json',inputs)
 original=read(OLD/'initial_values.json');oldtrace=read(OLD/'trace.json');out={};checks={}
 for label,folder in folders.items():
  attempt=read(folder/'attempt.json');report=read(folder/'report.json');initial=read(folder/'initial_values.json');trace=read(folder/'trace.json');contacts=read(folder/'contacts.json');capture=read(folder/'media/capture.json')
  assert all(sha(p)==h for p,h in attempt['input_sha256'].items())
  assert report['completed'] and report['physics_steps']==1200 and len(trace)==301 and len(contacts)==300 and len(capture['frames'])==151
  assert report['policy_calls']==report['checkpoint_loads']==0 and not report['forbidden_calls']
  assert report['initial_state_write_calls']==['set_actor_rigid_body_states','set_actor_dof_states']
  assert report['property_setter_calls']==1 and not report['property_setter_rejections'] and all(report['property_cache_checks'].values())
  assert initial['PD_properties']==original['PD_properties'] and initial['mass_properties']==original['mass_properties']
  q=np.array(initial['q_ref_rad']);names=initial['joint_names'];lower=initial['PD_properties']['lower'];upper=initial['PD_properties']['upper']
  assert np.all(q>=lower) and np.all(q<=upper)
  for row in trace:
   assert np.isfinite(np.r_[row['q_rad'],row['qdot_rad_s'],row['position_W_m'],row['quaternion_xyzw']]).all()
   assert np.array_equal(row['submitted_target_rad'],q)
  for frame in capture['frames']:
   assert frame['render_preserves_states'] and all(sha(p)==h for p,h in frame['image_sha256'].items())
  video={}
  for name in ['whole_body','hands']:
   path=folder/'media'/f'{name}.mp4';v=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames,r_frame_rate,duration','-of','json',str(path)]))['streams'][0]
   assert v['nb_read_frames']=='151' and v['r_frame_rate']=='30/1';video[name]={'path':str(path),'sha256':sha(path),'stream':v}
  if label!='previous_high':
   row=next(r for r in read(P/'search_v2/search.json')['rows'] if r['label']==label);assert row['accepted_for_native']
   unchanged=[i for i,n in enumerate(names) if not n.startswith(tuple(s+'_'+b for s in ['L','R'] for b in ['Thorax','Shoulder','Elbow','Wrist']))]
   assert np.array_equal(q[unchanged],np.array(original['q_ref_rad'])[unchanged])
   assert all(initial['native_initial_state']['human_body_states'][i]==original['native_initial_state']['human_body_states'][i] for i in range(9))
   assert np.array_equal(trace[0]['quaternion_xyzw'],oldtrace[0]['quaternion_xyzw'])
   assert np.allclose(np.array(trace[0]['position_W_m'])-oldtrace[0]['position_W_m'],row['guitar_delta_W_m'],atol=1e-6,rtol=0)
   assert report['source_audit']['source_clear'] and all(sha(p)==h for p,h in read(P/'preflight_inputs_v1.json').items())
  counts={}
  for body in ['L_Hip','R_Hip','Chest','Spine','R_Shoulder','R_Elbow','LH:palm']:
   match=lambda c: 'guitar/G:body' in [c['body0_name'],c['body1_name']] and 'human/'+body in [c['body0_name'],c['body1_name']]
   counts[body]={'contact_presence_samples':sum(any(match(c) for c in r['contacts']) for r in contacts),'positive_raw_lambda_samples':sum(any(match(c) and c['lambda']>0 for c in r['contacts']) for r in contacts),'of':300}
  leftcounts={}
  for body in ['LH:palm','LH:thumb1','LH:thumb2','LH:thumb3','LH:index3','LH:middle3']:
   def neckmatch(c):
    pair=[c['body0_name'],c['body1_name']]
    return 'human/'+body in pair and any(n.startswith('guitar/') and n not in ['guitar/G:body'] for n in pair)
   leftcounts[body]={'positive_raw_lambda_samples':sum(any(neckmatch(c) and c['lambda']>0 for c in r['contacts']) for r in contacts),'scope':'any non-G:body guitar body, not exclusive neck surface attribution','of':300}
  at2=trace[120];last=trace[-1];delta=np.array(last['position_W_m'])-trace[0]['position_W_m'];latep=np.linalg.norm(np.array(last['position_W_m'])-at2['position_W_m']);later=(Rotation.from_quat(at2['quaternion_xyzw']).inv()*Rotation.from_quat(last['quaternion_xyzw'])).magnitude()
  out[label]={'initial_actor_root_position_W_m':trace[0]['position_W_m'],'final_actor_root_position_W_m':last['position_W_m'],'final_actor_root_delta_W_mm':(delta*1000).tolist(),'final_position_change_mm':last['position_change_m']*1000,'final_rotation_change_deg':last['rotation_change_deg'],'max_position_change_mm':max(r['position_change_m'] for r in trace)*1000,'max_rotation_change_deg':max(r['rotation_change_deg'] for r in trace),'position_2_to_5s_mm':float(latep*1000),'rotation_2_to_5s_deg':float(np.rad2deg(later)),'body_contact_samples':counts,'left_nonbody_guitar_contact_samples':leftcounts,'final_actual_minus_initial_goal_deg':dict(zip(names,np.rad2deg(np.array(last['q_rad'])-q).tolist())),'videos':video}
  if label!='previous_high':
   strap=read(folder/'media/strap_state_samples.json')['rows'];assert len(strap)==151
   out[label]['strap_saved_current_command_max_N']=max(r['current_enabled_calculated_tension_n'] for r in strap);out[label]['strap_saved_previous_step_command_max_N']=max(r['last_applied_tension_n'] or 0 for r in strap)
  checks[label]={'completed':True,'inputs_unchanged':len(attempt['input_sha256']),'targets_constant_all_301':True,'PD_mass_same_as_previous':True,'render_state_invariance_151':True,'forbidden_calls':[]}
 assert all(sha(p)==h for p,h in inputs.items())
 save(P/'verification_v1.json',{'passed':True,'new_native_runs':2,'new_physics_steps_total':2400,'checks':checks,'cases':out,'interpretation':'initial height diagnostic; no repeatability or music success certification; raw lambda is not N; source distance is not cooked clearance; 3/8mm is min of both thighs, not vertical height'})
 print(json.dumps({k:{n:v for n,v in d.items() if n in ['final_position_change_mm','final_rotation_change_deg','max_position_change_mm','max_rotation_change_deg','position_2_to_5s_mm','rotation_2_to_5s_deg','final_actor_root_delta_W_mm']} for k,d in out.items()},indent=2))

if __name__=='__main__':main()
