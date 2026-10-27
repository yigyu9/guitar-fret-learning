"""Read-only native q-limit deviations and submitted-effort diagnostics."""
from pathlib import Path
import json,gzip
import numpy as np
BASE=Path(__file__).resolve().parent
props=json.loads((BASE/'train_default_v1/initial_values.json').read_text())
names=props['joint_names'];lower=np.array(props['native_PD_properties']['lower']);upper=np.array(props['native_PD_properties']['upper']);caps=np.array(props['native_PD_properties']['effort']);zero=lower==upper
right=[i for i,n in enumerate(names) if n.startswith(('R_Elbow_','R_Wrist_'))]
rows=[]
for folder in sorted(BASE.iterdir()):
 if not folder.is_dir() or not (folder/'report.json').exists():continue
 files=sorted(folder.glob('transition_*.json.gz')) or sorted(folder.glob('episode_*/transition_*.json.gz'))
 if not files:continue
 deviation=np.zeros(105);zero_motion=np.zeros(105);vmax=np.zeros(105);maxratio=np.zeros(105);count=np.zeros(105);total=0
 for path in files:
  with gzip.open(path,'rt') as stream:r=json.load(stream)
  native=r['info']['native_control']
  for sample,effort in zip(native['physics_samples240'],native['original_effort_diagnostics']):
   q=np.array([x['pos'] for x in sample['native']['human_dof_states']]);v=np.array([x['vel'] for x in sample['native']['human_dof_states']]);total+=1
   deviation=np.maximum(deviation,np.maximum(np.maximum(lower-q,q-upper),0));zero_motion=np.maximum(zero_motion,np.abs(q-lower));vmax=np.maximum(vmax,np.abs(v))
   submitted=np.array(effort['submitted105_Nm']);ratio=np.divide(np.abs(submitted),caps,out=np.zeros(105),where=caps>0)
   maxratio=np.maximum(maxratio,ratio);count+=ratio>=1-1e-6
 rows.append(dict(run=folder.name,physics_samples=total,
  max_nonzero_range_limit_excess_rad=float(deviation[~zero].max()),
  nonzero_range_axis_at_max=names[np.where(~zero)[0][deviation[~zero].argmax()]],
  max_nominal_zero8_absolute_q_from_bound_rad=float(zero_motion[zero].max()),
  max_native_reported_joint_speed_rad_s=float(vmax.max()),
  max_submitted_effort_cap_ratio=float(maxratio.max()),right6_submitted_effort_cap_ratio=float(maxratio[right].max()),
  right6_saturation_sample_fraction=float(count[right].sum()/(total*6)),
  scope='Native scalar q and submitted commands, not parent-child rotation or measured actuator torque. POSITION finger torques are not observed here; zero submitted effort is not zero actuator effort.',
  axis_limit_excess_rad=dict(zip(names,deviation.tolist()))))
with (BASE/'joint_effort_audit.json').open('x') as stream:json.dump(rows,stream,indent=2,allow_nan=False);stream.write('\n')
print(json.dumps([{k:v for k,v in r.items() if k!='axis_limit_excess_rad'} for r in rows],indent=2))
