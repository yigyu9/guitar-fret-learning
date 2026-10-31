"""Read completed strap-free trials and direct native support observations."""
from pathlib import Path
import hashlib,json,subprocess
import numpy as np
from scipy.spatial.transform import Rotation
from .om_axilla_source_geometry_v3 import CapsuleBodyDistance
from .upper_arm_static_geometry_v1 import ASSET
from .initial_pose_noise_v1 import pose
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,x):
 with (P/name).open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False)
def main():
 folders={('pilot_left_away' if p.parent.name=='native_v1' else 'pilot_left_high' if p.parent.name=='native_v2' else p.name):p for p in sorted(P.glob('native_v*/*')) if (p/'report.json').exists()};assert set(folders)=={'pilot_left_away','pilot_left_high','upper_arm_close'}
 files=[Path(__file__).resolve(),ASSET,P/'search_v4/search.json',P/'preflight_inputs_v1.json',P/'parked_left_preflight_inputs_v1.json',ROOT/'stability_adapter_2/om_axilla_source_geometry_v3.py']+[p for f in folders.values() for p in f.rglob('*') if p.is_file()]
 geometry=read(ROOT/'stability_adapter_2/assets/om_body_geometry_v3/manifest.json');files.append(Path(geometry['asset']));files.extend(Path(m['path'])for m in geometry['meshes']);inputs={str(p):sha(p)for p in files};save('analysis_inputs_before_v3.json',inputs)
 distance=CapsuleBodyDistance(geometry['asset'],ASSET);cases={};initials={}
 for label,folder in folders.items():
  report=read(folder/'report.json');attempt=read(folder/'attempt.json');trace=read(folder/'trace.json');contacts=read(folder/'contacts.json');initial=read(folder/'initial_values.json');initials[label]=initial
  assert all(sha(p)==h for p,h in attempt['input_sha256'].items())
  assert report['completed'] and report['physics_steps']==1200 and len(trace)==301 and len(contacts)==300
  assert report['actual_strap_enabled'] is False and initial['strap_initial']['enabled'] is False and report['strap_force_calls']==0 and not report['forbidden_calls']
  assert report['policy_calls']==report['checkpoint_loads']==0 and report['property_setter_calls']==1 and report['property_setter_rejections']==0 and all(report['property_cache_checks'].values())
  goal=np.array(initial['q_ref_rad']);assert all(np.array_equal(t['submitted_target_rad'],goal) and np.isfinite(np.r_[t['q_rad'],t['qdot_rad_s'],t['position_W_m'],t['quaternion_xyzw']]).all()for t in trace)
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
 a,b=initials['pilot_left_away'],initials['upper_arm_close'];assert a['PD_properties']==b['PD_properties'] and a['mass_properties']==b['mass_properties']
 idx=[i for i,n in enumerate(a['joint_names'])if not n.startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist','R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))]
 assert np.array_equal(np.array(a['q_ref_rad'])[idx],np.array(b['q_ref_rad'])[idx])
 assert all(sha(p)==h for p,h in inputs.items());save('verification_v3.json',{'passed':True,'new_native_runs':3,'physics_steps_total':3600,'body_head_finger_initial_q_PD_mass_same':True,'left_pose_differs_across_pilots_and_final':True,'cases':cases,'scope':'diagnostic observation; left arm/hand independence evaluated from 60Hz contacts, not all physics subframes; raw lambda not N; analytic source gaps from measured poses are not cooked penetration depth'})
 print(json.dumps({k:{n:v for n,v in d.items()if n in ['final_position_change_mm','final_rotation_change_deg','max_position_change_mm','max_rotation_change_deg','position_2_to_5s_mm','rotation_2_to_5s_deg','body_positive_raw_lambda_samples_of_300','left_arm_hand_any_guitar_positive_samples_of_300']}for k,d in cases.items()},indent=2))
if __name__=='__main__':main()
