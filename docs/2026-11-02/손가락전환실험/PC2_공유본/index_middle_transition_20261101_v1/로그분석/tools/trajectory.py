from pathlib import Path
import gzip,json,csv,math,collections,hashlib
import numpy as np
L=Path(__file__).resolve().parents[1];D=L.parent

def rows(p):
 with gzip.open(p/'finger_control_trace.jsonl.gz','rt') as f:
  first=None
  for line in f:
   x=json.loads(line)
   if first is None:first=x['episode_id']
   if x['episode_id']==first:yield x

def compare(p,q):
 dif={k:{str(t):None for t in (1e-9,1e-6,1e-4)} for k in ('actual_rad','requested_target_rad','applied_target_rad','arm_actual_rad','arm_requested_rad','arm_applied_rad','all_env_distance_m','all_env_candidate','all_env_wrong')};initial={};count=0
 for a,b in zip(rows(p),rows(q)):
  if abs(a['episode_time_s']-b['episode_time_s'])>1e-7:break
  count+=1
  for k,levels in dif.items():
   aa=np.asarray(a.get(k,a['natural_preparation']['transition'].get(k)),dtype=float);bb=np.asarray(b.get(k,b['natural_preparation']['transition'].get(k)),dtype=float)
   if aa.shape!=bb.shape:
    if k.startswith('all_env'):aa=aa[:32];bb=bb[:32]
    else:raise ValueError(k)
   delta=abs(aa-bb);mx=float(delta.max());ix=np.unravel_index(int(delta.argmax()),delta.shape)
   if count==1:initial[k]=mx
   for threshold in levels:
    if levels[threshold] is None and mx>float(threshold):levels[threshold]=dict(t=a['episode_time_s'],max_abs=mx,index=[int(z) for z in ix],a=float(aa[ix]),b=float(bb[ix]))
 return dict(a=str(p),b=str(q),aligned_rows=count,first_record_max_abs=initial,first_threshold_exceedance=dif,scope='first240Hz endpoint logged; earliest unrecorded force/body state or observation is unknown; thresholds are not proof of causation')
comparisons={}
pairs=[('old128_repeat',D/'진단/final128_seed17_mean',D/'진단/context_repeat_seed17_mean_128'),('old32_vs_old128_front32',D/'진단/base_seed17_u200_mean',D/'진단/final128_seed17_mean')]
for n in (32,128):
 for k in (2,3):pairs.append((f'newN{n}_1_vs_{k}',L/f'runs/s17_u200_mean_N{n}_repeat1',L/f'runs/s17_u200_mean_N{n}_repeat{k}'))
for label,p,q in pairs:
 if (p/'report.json').exists() and (q/'report.json').exists():comparisons[label]=compare(p,q)
snapshots={};release={}
for seed in (7,17):
 for u in (100,200,300):
  for mode in ('mean','sampled'):
   name=f'base_seed{seed}_u{u}_{mode}';p=D/'진단'/name;rr=list(rows(p));ss={};r0=rr[0];middle=[i for i,n in enumerate(r0['joint_names']) if n.startswith('LH:middle')];joints=r0['joint_names'];b=[x for x in rr if 5.25<=x['episode_time_s']<6.75]
   for t in (3.25,4.49,4.75,5.0,5.25,5.8,6.7):
    x=min(rr,key=lambda x:abs(x['episode_time_s']-t));f=x['natural_preparation']['fingers'][1];tr=x['natural_preparation']['transition'];ss[str(t)]=dict(t=x['episode_time_s'],B_approach_selected_sample=f,B_position_any_sample=tr['all_env_position_geometry'][0][1],B_facing_any_sample=tr['all_env_facing_geometry'][0][1],B_raw=tr['all_env_raw_candidate'][0][1],B_effective=tr['all_env_candidate'][0][1],B_wrong=tr['all_env_wrong'][0][1],A_raw=tr['all_env_raw_candidate'][0][0],A_effective=tr['all_env_candidate'][0][0],wrist_guide_excess_mm=[1000*v for v in tr['wrist_error_m']],middle_native_axis_names=[joints[i] for i in middle],**{k:[x[k][i]*180/math.pi for i in middle] for k in ('requested_target_rad','applied_target_rad','actual_rad')})
   metrics={}
   for j,i in enumerate(middle):
    act=np.array([x['actual_rad'][i] for x in b]);req=np.array([x['requested_target_rad'][i] for x in b]);app=np.array([x['applied_target_rad'][i] for x in b]);metrics[joints[i]]=dict(request_actual_RMS_deg=float(np.sqrt(np.mean((req-act)**2))*180/math.pi),request_apply_RMS_deg=float(np.sqrt(np.mean((req-app)**2))*180/math.pi),actual_range_deg=float(np.ptp(act)*180/math.pi),requested_range_deg=float(np.ptp(req)*180/math.pi),actual_start_end_deg=[float(v*180/math.pi) for v in (act[0],act[-1])],mean_velocity_deg_s=float(np.mean([abs(x['velocity_rad_s'][i]) for x in b])*180/math.pi) if 'velocity_rad_s' in b[0] else None)
   a_raw_gap=[x['episode_time_s'] for x in rr if 4.5<=x['episode_time_s']<5.25 and x['natural_preparation']['transition']['all_env_raw_candidate'][0][0]]
   both={ph:sum(all(x['natural_preparation']['transition']['all_env_raw_candidate'][0]) for x in rr if lo<=x['episode_time_s']<hi)/240 for ph,(lo,hi) in {'A':(3,4.5),'gap':(4.5,5.25),'B':(5.25,6.75)}.items()}
   snapshots[name]=dict(samples=ss,B_joint_metrics=metrics,A_raw_gap_last_s=max(a_raw_gap) if a_raw_gap else None,A_raw_gap_endpoints_s=len(a_raw_gap)/240,raw_dual_env0_endpoint_seconds=both)
(L/'trajectory_comparison.json').write_text(json.dumps(comparisons,indent=2,ensure_ascii=False));(L/'snapshots.json').write_text(json.dumps(snapshots,indent=2,ensure_ascii=False));print('trajectory comparisons and snapshots written')
