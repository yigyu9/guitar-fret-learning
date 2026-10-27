"""Offline bounded candidate grid; not a native reachability certificate."""
import json,gzip
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from scipy.optimize import least_squares
from guitar_learning.geometry_v1 import frame
from guitar_learning.control import ACTIVE_NAMES
from guitar_learning.recording import digest,write
from stability_adapter_2.lower_body_release_v1.controller_horizontal_v4 import full_fk
P=Path(__file__).resolve().parent
source=P/'right_servo_v4/trace.json.gz';reset=P/'right_servo_v4/reset.json';namesfile=Path('/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/native_free_strike_v14/initial_values.json')
paths=[source,reset,namesfile,Path(__file__)];pinned={str(p):digest(p) for p in paths}
r=json.loads(gzip.decompress(source.read_bytes()))[0]['samples240'][0];n=json.loads(namesfile.read_text());meta=json.loads(reset.read_text())['target_contract']
q=np.array([s['pos'] for s in r['native']['human_dof_states']]);scene=SimpleNamespace(names=n['joint_names'],human_bodies=n['human_body_names'],q_ref=q)
fk=full_fk(scene,r['native']);idx=[scene.names.index(x) for x in ACTIVE_NAMES[33:]];gp,gr=frame(r['native']['guitar_body_states'][0]);lo=np.array(meta['action_lower_rad'])[33:];hi=np.array(meta['action_upper_rad'])[33:]
rows=[]
for y in np.linspace(-.38,-.26,7):
 for depth in [.002,.004,.008,.012]:
  start,end=np.array(r['geometry']['starts_G_m'])[1],np.array(r['geometry']['ends_G_m'])[1];target=start+(end-start)*(y-start[1])/(end[1]-start[1]);target[2]-=depth
  endpoints=[]
  for across in [-.008,.008]:
   goal=target+np.array([across,0,0]);world=gp+gr.apply(goal)
   def residual(v):
    trial=q.copy();trial[idx]=v
    return np.r_[1000*(fk(trial)['RH:pick'][0]-world),.01*(v-q[idx])]
   fit=least_squares(residual,np.clip(q[idx],lo+1e-9,hi-1e-9),bounds=(lo,hi),max_nfev=30)
   trial=q.copy();trial[idx]=fit.x
   endpoints.append(dict(goal_G_m=goal.tolist(),target6=fit.x.tolist(),residual_m=float(np.linalg.norm(fk(trial)['RH:pick'][0]-world))))
  rows.append(dict(y_m=y,depth_m=depth,endpoints=endpoints,max_residual_m=max(x['residual_m'] for x in endpoints)))
rows.sort(key=lambda x:x['max_residual_m']);write(P/'right_grid_v2.json',dict(inputs=pinned,rows=rows,inputs_unchanged=all(digest(p)==s for p,s in pinned.items()),scope='offline pose-anchored FK hypothesis only; original codec and native contact/strike checks required'))
print(json.dumps(rows[:4]))
