from pathlib import Path
import json,gzip,csv,math,collections
import numpy as np
L=Path(__file__).resolve().parents[1];D=L.parent
out=[]
for seed in (7,17):
 for u in (100,200,300):
  for mode in ('mean','sampled'):
   name=f'base_seed{seed}_u{u}_{mode}';v=collections.defaultdict(lambda:collections.defaultdict(list));first=None
   with gzip.open(D/f'진단/{name}/finger_control_trace.jsonl.gz','rt') as f:
    for line in f:
     x=json.loads(line)
     if first is None:first=x['episode_id']
     if x['episode_id']!=first:continue
     t=x['episode_time_s'];ph='B' if 5.25<=t<6.75 else 'other';z=x['natural_preparation']['transition']
     for j,n in enumerate(z['arm_joint_names']):
      for k,key in [('action','arm_action'),('request','arm_requested_rad'),('apply','arm_applied_rad'),('actual','arm_actual_rad')]:v[(ph,n)][k].append(z[key][j])
     for j,n in enumerate(x['joint_names']):
      if not n.startswith(('LH:index','LH:middle')):continue
      for k,key in [('action','action'),('request','requested_target_rad'),('apply','applied_target_rad'),('actual','actual_rad'),('velocity','velocity_rad_s')]:v[(ph,n)][k].append(x[key][j])
   for (ph,n),z in v.items():
    q=np.array(z['actual']);r=np.array(z['request']);a=np.array(z['action']);ap=np.array(z['apply']);out.append(dict(condition=name,phase=ph,axis=n,frames=len(a),action_mean=float(a.mean()),action_std=float(a.std()),action_saturation_abs_ge098=float((abs(a)>=.98).mean()),requested_mean_deg=float(r.mean()*180/math.pi),applied_mean_deg=float(ap.mean()*180/math.pi),actual_mean_deg=float(q.mean()*180/math.pi),actual_range_deg=float(np.ptp(q)*180/math.pi),request_actual_rms_deg=float(np.sqrt(np.mean((r-q)**2))*180/math.pi),request_apply_rms_deg=float(np.sqrt(np.mean((r-ap)**2))*180/math.pi),mean_abs_velocity_deg_s=float(np.mean(abs(np.array(z['velocity'])))*180/math.pi) if 'velocity' in z else 'not logged'))
with (L/'tables/active_axis_stats.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
print('20 active axes, mean/sampled, six models: env0 statistics written')
