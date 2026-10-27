"""Read saved native samples and predict final R9 target FK; no new physics."""
from pathlib import Path
import hashlib
import json
import numpy as np
from scipy.spatial.transform import Rotation as R
phase=Path(__file__).resolve().parent
root=phase.parents[4]
native=phase/'native_retry_v1/data'
out=phase/'authority_analysis_v2';out.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=[Path(__file__).resolve(),root/'stability_adapter_2/underneck_initial_search.py',root/'stability_adapter_2/assets/humanoid_fixed_lower.xml']+[native/n for n in ('initial_values.json','trace.json','controls.json')]
hashes={str(p):sha(p) for p in paths}
(out/'inputs_before.json').write_text(json.dumps({'sha256':hashes},indent=2)+'\n')
from stability_adapter_2.underneck_initial_search import calibrated_fk,pose
read=lambda p:json.loads(p.read_text())
i=read(native/'initial_values.json');traces=read(native/'trace.json');controls=read(native/'controls.json')
states={r['physics_step']:r['native_state'] for r in traces}
fk,_=calibrated_fk(i['joint_names'],i['human_body_names'],i['native_initial_state'],np.array(i['initial_angles_rad']))
rows=[]
for row in controls:
    r=row.get('phase_target_residual',{})
    if r.get('source_motor_phase')!=1 or r['adapter_approach_open'] or row['before_physics_step'] not in states:continue
    assert r['target_geometry_index']==3
    state=states[row['before_physics_step']];gp,gr=pose(state['guitar_body_states'][0]);actual=np.array(r['actual_dofs_rad']);final=np.array(row['final_targets_rad']);idx=r['joint_indices']
    q=actual.copy();q[idx]=final[idx]
    fp,_=fk(q)['RH:pick'];base,_=fk(actual)['RH:pick'];predicted=np.array(r['actual_pick_W_m'])+R.from_quat(r['current_chest_delta_xyzw']).apply(fp-base);goal_G=gr.inv().apply(predicted-gp)
    rows.append({'time_s':row['time_s'],'physics_step':row['before_physics_step'],'waypoint_G_z_mm':r['target_G_m'][2]*1000,'actual_pick_G_z_mm':row['readiness']['pick_G_m'][2]*1000,'predicted_final_R9_goal_pick_G_z_mm':float(goal_G[2]*1000),'maximum_R9_goal_minus_actual_rad':float(abs(final[idx]-actual[idx]).max())})
assert len(rows)==8 and np.isfinite([[v for v in row.values()] for row in rows]).all()
summary={'sample_count':len(rows),'predicted_R9_goal_G_z_minmax_mm':[min(r['predicted_final_R9_goal_pick_G_z_mm'] for r in rows),max(r['predicted_final_R9_goal_pick_G_z_mm'] for r in rows)],'R9_goal_actual_max_error_minmax_rad':[min(r['maximum_R9_goal_minus_actual_rad'] for r in rows),max(r['maximum_R9_goal_minus_actual_rad'] for r in rows)],'scope':'native measured marker depth and actualq; finalR9 target FK prediction holds fingers at current actual angles and uses actualanchor/ChestDelta. Prediction is not measured futurepose or unobservedderivativecertificate; no newphysics/controlchange.'}
(out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,ax=plt.subplots(figsize=(8,4.5));time=[r['time_s'] for r in rows]
for key,label in (('actual_pick_G_z_mm','Measured native pick'),('waypoint_G_z_mm','Requested READY waypoint'),('predicted_final_R9_goal_pick_G_z_mm','Final R9 goal FK prediction (fingers held actual)')):ax.plot(time,[r[key] for r in rows],marker='o',label=label)
ax.set(xlabel='Native time (s)',ylabel='Guitar-local z (mm)',title='Closed source approach window: waypoint versus final arm goal');ax.grid(alpha=.3);ax.legend(fontsize=8);fig.tight_layout();fig.savefig(out/'goal_authority.png',dpi=160);plt.close(fig)
changed=[p for p,h in hashes.items() if sha(Path(p))!=h]
(out/'inputs_after.json').write_text(json.dumps({'unchanged':not changed,'changed':changed},indent=2)+'\n');assert not changed
print(summary)
