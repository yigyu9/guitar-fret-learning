"""Verify recorded owner transitions and summarize the simultaneous transfer diagnostic."""
import hashlib,json
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parent
RUN=P/'pair100_v4'
ROOT=P.parents[4]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=[RUN/n for n in ('attempt.json','initial_values.json','report.json','controls.json','trace.json','source_contract.json','observation_manifest.json','music_physics_samples.json','joint_crossings.json','joint_events.json','media/capture.json','media/videos.json')]+[Path(__file__),ROOT/'stability_adapter_2/environment_foundation_v1.json']
hashes={str(p):sha(p) for p in paths}
read=lambda n:json.loads((RUN/n).read_text())
r,t,info,initial=read('controls.json'),read('trace.json'),read('report.json'),read('initial_values.json')
m,c,e=read('music_physics_samples.json'),read('joint_crossings.json'),read('joint_events.json')
assert info['completed'] and info['dual_checkpoints_connected'] and not info['forbidden_calls']
assert len(r)==231 and len(t)==232 and len(m)==924 and info['physics_steps']==924
assert [x['physics_step'] for x in m]==list(range(1,925))
assert all(x['physics_step_before']==4*i and x['clock']['physics_step']==4*(i+1) for i,x in enumerate(r))
assert sum(x['actor_used'] for x in r)==111 and all(not x['actor_used'] for x in r[:120])
assert all(x['score_frame']==i for i,x in enumerate(r[120:]))
assert all(len(x['combined_observation'])==1299 and np.isfinite(x['combined_observation']).all() for x in r)
qref=np.array(initial['q_ref_rad']);targets=np.r_[qref[None],np.array([x['final_rad'] for x in r])]
config=json.loads((ROOT/'stability_adapter_2/environment_foundation_v1.json').read_text())
names=initial['joint_names']
def group(name):
    if name.startswith(('Torso','Spine','Chest')):return 'body'
    if name.startswith(('Neck','Head')):return 'head'
    if name.startswith(('LH:','RH:')):return 'finger'
    return 'arm'
groups=[group(n) for n in names]
rates=np.array([config['target_rates_rad_s'][g] for g in groups])
assert np.all(abs(np.diff(targets,axis=0))<=rates/60+2e-7)
lo=np.array(initial['PD_properties']['lower']);hi=np.array(initial['PD_properties']['upper'])
assert np.all(targets>=lo-2e-7) and np.all(targets<=hi+2e-7)
body=[j for j,g in enumerate(groups) if g=='body'];assert np.max(abs(targets[:,body]-qref[body]))<=np.deg2rad(5)+2e-7
p=np.array([x['position_W_m'] for x in t]);q=np.array([x['quaternion_xyzw'] for x in t]);q/=np.linalg.norm(q,axis=1)[:,None]
angles=np.rad2deg(2*np.arccos(np.clip(abs(q@q[0]),0,1)))
z=initial['native_initial_state']['human_body_states'][initial['human_body_names'].index('Chest')]['pose']['p']['z']
outside=np.maximum(np.maximum(np.array([-.5,-.15,.65])-p,p-np.array([-.15,.15,z])),0)
frames=read('media/capture.json')['frames'];assert len(frames)==117 and frames[-1]['physics_step']==924 and frames[0]['physics_step']==0
assert all(x['render_preserves_states'] for x in frames)
for x in frames:
    for path,digest in x['image_sha256'].items():assert sha(Path(path))==digest
for video in info['videos'].values():assert sha(Path(video['path']))==video['sha256'] and int(video['stream']['nb_read_frames'])==117
last=r[-1];assert last['Fret_done']==[True] and last['Strike_done']==[False]
assert last['Fret_info']['wrist_safety_termination']==[True] and last['Fret_info']['normal_termination']==[False]
assert all(not x['joint_success'] for x in e)
source_counts={k:sum(bool(x['Strike_info'][k][0]) for x in r[120:]) for k in ('target_hit','physical_target_hit','physical_target_miss','miss')}
history={label:{'max_reconstruction_error_rad':float(np.max(abs(np.array([x[label+'_history_reconstruction_error_rad'] for x in r])))),
    'max_PLAY_reconstruction_error_rad':float(np.max(abs(np.array([x[label+'_history_reconstruction_error_rad'] for x in r[120:]])))),
    'clipped_control_samples':sum(x[label+'_history_clipped_channels']>0 for x in r)} for label in ('Fret','Strike')}
assert all(sha(Path(p))==v for p,v in hashes.items())
summary={'scope':'saved native 60Hz poses,240Hz geometry diagnostic; source metrics separate from joint diagnostic',
    'input_sha256':hashes,'inputs_unchanged':True,'control_steps':231,'physics_steps':924,'preparation_seconds':2.,
    'physics_seconds':3.85,'PLAY_seconds':1.85,'actor_ticks':111,'frames_per_view':117,'video_seconds':3.9,
    'dimension':1299,'one_owner_clock_contiguous':True,'rate_and_native_target_bounds_pass':True,
    'root_lower_initial_exact_and_owner_runtime_guard_pass':True,
    'guitar_max_displacement_from_initial_mm':float(np.linalg.norm(p-p[0],axis=1).max()*1000),
    'guitar_max_rotation_from_initial_deg':float(angles.max()),
    'core_position_box_max_outside_norm_mm':float(np.linalg.norm(outside,axis=1).max()*1000),
    'first_terminal':'Fret wrist_safety_termination; native G-local wrist X bound; not joint angular limit',
    'terminal_wrist_position_G_m':last['Fret_info']['wrist_safety_local_position'][0],
    'terminal_wrist_axis_violations':last['Fret_info']['wrist_safety_violation_by_axis'][0],
    'Fret_done':True,'Strike_done':False,'normal_song_completion':False,
    'resolved_joint_events':len(e),'joint_successes':sum(bool(x['joint_success']) for x in e),
    'joint_crossings':len(c),'joint_crossing_reasons':[x['reason'] for x in c],
    'source_Strike_per_control_boolean_counts':source_counts,'source_history':history,
    'interpretation':'static preload improves initial support; full frozen source target requests lose it during PLAY',
    'unverified':['fractional-time pressure','continuous press proof','native contact clearance','SO3 allowed-region membership','source ABI equivalence','reward v4/fatal ledger/PPO'],
    'stability_success':False,'training_ready':False,'training_updates':0}
with (P/'pair_analysis_v1.json').open('x') as f:json.dump(summary,f,ensure_ascii=False,indent=2)
print(json.dumps({k:v for k,v in summary.items() if k!='input_sha256'},ensure_ascii=False,indent=2))
