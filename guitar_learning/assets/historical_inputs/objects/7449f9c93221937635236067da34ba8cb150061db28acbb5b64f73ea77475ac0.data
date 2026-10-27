"""Read completed strap-free trials and direct native support observations."""
from pathlib import Path
import hashlib,json,subprocess
import numpy as np
from scipy.spatial.transform import Rotation
from .om_axilla_source_geometry_v3 import CapsuleBodyDistance
from .upper_arm_static_geometry_v1 import ASSET
from .initial_pose_noise_v1 import pose
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,x):
 with (P/name).open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False)
def main():
 folders={('pilot_left_away' if p.parent.name=='native_v1' else 'pilot_left_high' if p.parent.name=='native_v2' else ('upper_arm_preload_pi' if p.parent.name=='native_v4' else p.name)):p for p in sorted(P.glob('native_v*/*')) if (p/'report.json').exists()};assert set(folders)=={'pilot_left_away','pilot_left_high','upper_arm_close','upper_arm_preload_pi','upper_arm_right_hold','upper_arm_relative_feedback','three_support_lean12'}
 files=[Path(__file__).resolve(),ASSET,P/'search_v4/search.json',P/'preflight_inputs_v1.json',P/'parked_left_preflight_inputs_v1.json',ROOT/'stability_adapter_2/om_axilla_source_geometry_v3.py']+[p for f in folders.values() for p in f.rglob('*') if p.is_file()]
 geometry=read(ROOT/'stability_adapter_2/assets/om_body_geometry_v3/manifest.json');files.append(Path(geometry['asset']));files.extend(Path(m['path'])for m in geometry['meshes']);inputs={str(p):sha(p)for p in files};save('analysis_inputs_before_v8.json',inputs)
 distance=CapsuleBodyDistance(geometry['asset'],ASSET);cases={};initials={}
 for label,folder in folders.items():
  report=read(folder/'report.json');attempt=read(folder/'attempt.json');trace=read(folder/'trace.json');contacts=read(folder/'contacts.json');initial=read(folder/'initial_values.json');initials[label]=initial
  assert all(sha(p)==h for p,h in attempt['input_sha256'].items())
  assert report['completed'] and report['physics_steps']==1200 and len(trace)==301 and len(contacts)==300
  assert report['actual_strap_enabled'] is False and initial['strap_initial']['enabled'] is False and report['strap_force_calls']==0 and not report['forbidden_calls']
  assert report['policy_calls']==report['checkpoint_loads']==0 and report['property_setter_calls']==1 and report['property_setter_rejections']==0 and all(report['property_cache_checks'].values())
  goal=np.array(initial['q_ref_rad']);assert all(np.isfinite(np.r_[t['q_rad'],t['qdot_rad_s'],t['position_W_m'],t['quaternion_xyzw']]).all()for t in trace)
  if label not in ('upper_arm_preload_pi','upper_arm_right_hold','upper_arm_relative_feedback','three_support_lean12'):assert all(np.array_equal(t['submitted_target_rad'],goal)for t in trace)
  capture=read(folder/'media/capture.json');assert capture['actual_strap_enabled'] is False and len(capture['frames'])==151
  for frame in capture['frames']:assert frame['render_preserves_states'] and all(sha(p)==h for p,h in frame['image_sha256'].items())
  strap=read(folder/'media/strap_state_samples.json')['rows'];assert len(strap)==151 and all(r['current_enabled_calculated_tension_n']==r['last_applied_tension_n']==0 for r in strap)
  support=read(folder/'media/support_state_samples.json')['rows'];assert len(support)==300 and all(r['physics_step']==4*k for k,r in enumerate(support))
  left_counts={};right_counts={}
  for key,prefix in [('left','human/L'),('right','human/R')]:
   counts={}
   for row in contacts:
    names=set()
    for c in row['contacts']:
     a,b=c['body0_name'],c['body1_name']
     if c['lambda']>0:
      if a.startswith(prefix) and b.startswith('guitar/'):names.add(a)
      if b.startswith(prefix) and a.startswith('guitar/'):names.add(b)
    for name in names:counts[name]=counts.get(name,0)+1
   if key=='left':left_counts=counts
   else:right_counts=counts
  left_arm_hand_samples=sum(any(c['lambda']>0 and ((c['body0_name'].startswith(('human/L_Thorax','human/L_Shoulder','human/L_Elbow','human/L_Wrist','human/LH:')) and c['body1_name'].startswith('guitar/')) or(c['body1_name'].startswith(('human/L_Thorax','human/L_Shoulder','human/L_Elbow','human/L_Wrist','human/LH:')) and c['body0_name'].startswith('guitar/'))) for c in r['contacts'])for r in contacts)
  bodycounts={}
  for n in ['L_Hip','R_Hip','Torso','Spine','Chest','R_Thorax','R_Shoulder','R_Elbow','R_Wrist','RH:palm']:
   bodycounts[n]=sum(any(c['lambda']>0 and 'guitar/G:body' in [c['body0_name'],c['body1_name']] and 'human/'+n in [c['body0_name'],c['body1_name']]for c in r['contacts'])for r in contacts)
  diagnostics=[]
  for k in [0,60,120,180,299]:
   r=support[k];ps={n:pose(s)for n,s in r['human_body_states'].items()};gp,gr=pose(r['guitar_body_states']['guitar']);m=distance.measure(ps,'R_Shoulder',gp,gr,.65);diagnostics.append({'time_s':r['time_s'],'proximal_source_gap_from_actual_native_poses':m,'left_palm_position_W_m':ps['LH:palm'][0].tolist()})
  video={}
  for view in ['whole_body','hands']:
   v=folder/'media'/f'{view}.mp4';stream=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames,r_frame_rate,duration','-of','json',str(v)]))['streams'][0];assert stream['nb_read_frames']=='151' and stream['r_frame_rate']=='30/1';video[view]={'path':str(v),'sha256':sha(v),'stream':stream}
  at2=trace[120];last=trace[-1]
  cases[label]={'final_position_change_mm':last['position_change_m']*1000,'final_rotation_change_deg':last['rotation_change_deg'],'max_position_change_mm':max(r['position_change_m']for r in trace)*1000,'max_rotation_change_deg':max(r['rotation_change_deg']for r in trace),'position_2_to_5s_mm':float(np.linalg.norm(np.array(last['position_W_m'])-at2['position_W_m'])*1000),'rotation_2_to_5s_deg':float(np.rad2deg((Rotation.from_quat(at2['quaternion_xyzw']).inv()*Rotation.from_quat(last['quaternion_xyzw'])).magnitude())),'body_positive_raw_lambda_samples_of_300':bodycounts,'left_arm_hand_any_guitar_positive_samples_of_300':left_arm_hand_samples,'all_left_positive_any_guitar_counts':left_counts,'all_right_positive_any_guitar_counts':right_counts,'direct_native_pose_source_diagnostics':diagnostics,'final_actual_minus_goal_deg':dict(zip(initial['joint_names'],np.rad2deg(np.array(last['q_rad'])-goal).tolist())),'videos':video,'strap_force_calls':0}
  endpoints_path=folder/'media/physics_endpoint_contacts.json'
  if endpoints_path.exists():
   endpoints=read(endpoints_path)['rows'];assert len(endpoints)==1200 and [r['physics_step']for r in endpoints]==list(range(1,1201))
   cases[label]['physics_endpoint_observations']={'total':1200,'left_arm_hand_contact_presence':sum(bool(r['left_arm_hand_guitar_contacts'])for r in endpoints),'left_arm_hand_positive_raw_lambda':sum(any(c['lambda']>0 for c in r['left_arm_hand_guitar_contacts'])for r in endpoints),'right_upper_arm_body_contact_presence':sum(bool(r['right_upper_arm_body_contacts'])for r in endpoints),'right_upper_arm_body_positive_raw_lambda':sum(any(c['lambda']>0 for c in r['right_upper_arm_body_contacts'])for r in endpoints)}
  if label in ('upper_arm_preload_pi','upper_arm_right_hold','upper_arm_relative_feedback','three_support_lean12'):
   ctrl=read(folder/'media/preload_control_rows.json')['rows'];setup=read(folder/'media/preload_configuration.json');config=read(P/'search_v5/three_support_lean12/config.json') if label=='three_support_lean12' else read(P/('right_hold_config_v1.json' if label in ('upper_arm_right_hold','upper_arm_relative_feedback') else 'preload_config_v1.json'));targetgoal=np.array(setup['goal_rad']);cap=np.array(setup['residual_cap_rad']);integral=np.zeros(81);lo=np.array(initial['PD_properties']['lower']);hi=np.array(initial['PD_properties']['upper']);lo[:9]=np.maximum(lo[:9],goal[:9]-np.deg2rad(5));hi[:9]=np.minimum(hi[:9],goal[:9]+np.deg2rad(5));mid=(lo+hi)/2;half=(hi-lo)/2;rates=np.array([config['target_rates_rad_s']['body' if n.startswith(('Torso_','Spine_','Chest_'))else 'head' if n.startswith(('Head_','Neck_'))else 'finger' if n.startswith(('LH:','RH:'))else 'arm']for n in initial['joint_names']]);assert len(ctrl)==300
   targetlo,targethi=lo.copy(),hi.copy();relative=None
   if label=='upper_arm_relative_feedback':
    relative=read(folder/'media/relative_goal_rows.json')['rows'];assert len(relative)==300;right=[i for i,n in enumerate(initial['joint_names'])if n.startswith(('R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))];targetlo[right]=np.maximum(lo[right],goal[right]-.8);targethi[right]=np.minimum(hi[right],goal[right]+.8);stopped=False;candidate=read(config['initial_candidate']);surface=np.array(candidate['no_strap_upper_arm_proposal']['proximal_support']['guitar_surface_G_m']);normal=np.array(setup['source_normal_G']);initialp=np.array(trace[0]['position_W_m']);initialr=Rotation.from_quat(trace[0]['quaternion_xyzw'])
   for k,r in enumerate(ctrl):
    if relative is not None:
     rr=relative[k];targetgoal=np.array(rr['goal_rad']);assert np.array_equal(rr['current_guitar_p_W_m'],trace[k]['position_W_m']) and np.array_equal(rr['current_guitar_q_xyzw'],trace[k]['quaternion_xyzw']);gr=Rotation.from_quat(rr['current_guitar_q_xyzw']);gp=np.array(rr['current_guitar_p_W_m']);assert np.allclose(rr['desired_motor_point_W_m'],gp+gr.apply(surface-.008*normal),atol=1e-12,rtol=0);stopped=stopped or np.linalg.norm(gp-initialp)>.15 or np.rad2deg((initialr.inv()*gr).magnitude())>25;assert rr['safety_stopped']==stopped;assert np.max(abs(targetgoal[right]-goal[right]))<=.400000001
     if rr['fit_status']=='accepted':assert rr['point_fit_error_m']<.005 and not stopped
     if k and rr['fit_status']!='accepted':assert np.array_equal(targetgoal,relative[k-1]['goal_rad'])
     other=[j for j in range(81)if j not in right];assert np.array_equal(targetgoal[other],goal[other])
    actual=np.array(trace[k]['q_rad']);assert np.array_equal(actual,np.array(r['actual_q_rad']));err=targetgoal-actual;integral=np.clip(integral+err/60,-cap,cap);residual=np.clip(err+integral,-cap,cap);requested=np.clip(targetgoal+residual,targetlo,targethi);action=np.clip((requested-mid)/half,-1,1)
    for key,value in [('error_rad',err),('integral_rad',integral),('residual_rad',residual),('requested_target_rad',requested),('requested_action',action)]:assert np.allclose(r[key],value,atol=1e-12,rtol=0)
    prev=np.array(trace[k]['submitted_target_rad']);target=np.clip(np.clip(mid+half*action,prev-rates/60,prev+rates/60),lo,hi).astype(np.float32);assert np.array_equal(target,np.array(trace[k+1]['submitted_target_rad']).astype(np.float32))
   if relative is not None:cases[label]['relative_goal_observations']={'accepted':sum(r['fit_status']=='accepted'for r in relative),'safety_stopped':sum(r['safety_stopped']for r in relative),'max_point_fit_error_m':max(r['point_fit_error_m']for r in relative if r['point_fit_error_m']is not None)}
   cases[label]['controller_formula_and_submission_exact_samples']=300;cases[label]['preload_point_fit_error_m']=setup['point_fit_error_m'];cases[label]['shape_filters']=setup['actual_shape_filters']
 a,b=initials['pilot_left_away'],initials['upper_arm_close'];assert a['PD_properties']==b['PD_properties'] and a['mass_properties']==b['mass_properties']
 idx=[i for i,n in enumerate(a['joint_names'])if not n.startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist','R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))]
 assert np.array_equal(np.array(a['q_ref_rad'])[idx],np.array(b['q_ref_rad'])[idx])
 assert initials['upper_arm_close']==initials['upper_arm_preload_pi'];assert initials['upper_arm_right_hold']==initials['upper_arm_relative_feedback']
 old,new=initials['upper_arm_preload_pi'],initials['upper_arm_right_hold'];assert old['native_initial_state']==new['native_initial_state'] and old['q_ref_rad']==new['q_ref_rad'] and old['mass_properties']==new['mass_properties'];right=[i for i,n in enumerate(old['joint_names'])if n.startswith(('R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))]
 for field,values in old['PD_properties'].items():
  expected=np.array(values)
  if field in ('stiffness','damping'):expected[right]*=(4 if field=='stiffness' else 2)
  assert np.array_equal(expected,new['PD_properties'][field]),field
 setup=read(folders['upper_arm_right_hold']/'media/right_hold_properties.json');assert setup['construction_override_calls']==1 and setup['applied']==new['PD_properties']
 cases['upper_arm_right_hold']['right_PD_change_verified']=True
 new=initials['three_support_lean12'];assert new['PD_properties']==initials['upper_arm_right_hold']['PD_properties'] and new['mass_properties']==initials['upper_arm_right_hold']['mass_properties'];finger=[i for i,n in enumerate(new['joint_names'])if n.startswith(('LH:','RH:'))];assert np.array_equal(np.array(new['q_ref_rad'])[finger],np.array(initials['upper_arm_right_hold']['q_ref_rad'])[finger]);cases['three_support_lean12']['same_PD_mass_finger_as_held_reference']=True
 assert all(sha(p)==h for p,h in inputs.items());save('verification_v8.json',{'passed':True,'new_native_runs':7,'physics_steps_total':8400,'first_six_body_head_finger_initial_q_PD_mass_same':True,'three_support_changes_body_head_arms_guitar_start':True,'right_gain_changed_since_fifth_trial':True,'left_pose_differs_across_pilots_and_final':True,'cases':cases,'scope':'diagnostic observation; left arm/hand independence evaluated from saved 240Hz after-physics endpoints where available; not continuous solver-internal certification; raw lambda not N; analytic source gaps from measured poses are not cooked penetration depth'})
 print(json.dumps({k:{n:v for n,v in d.items()if n in ['final_position_change_mm','final_rotation_change_deg','max_position_change_mm','max_rotation_change_deg','position_2_to_5s_mm','rotation_2_to_5s_deg','body_positive_raw_lambda_samples_of_300','left_arm_hand_any_guitar_positive_samples_of_300']}for k,d in cases.items()},indent=2))
if __name__=='__main__':main()
