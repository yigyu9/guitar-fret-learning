from pathlib import Path
import json,hashlib
import numpy as np
from stability_adapter_2.initial_pose_contacts_v1.analyze_v1 import selected,transform
from stability_adapter_2.free_guitar_learning_v1.geometry_v1 import geometry_snapshot,world_to_guitar
root=Path('/home/ajou/yigyu/3');run=root/'paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/native_free_strike_v14';out=Path(__file__).parent
files=[Path(__file__),run/'states240.json',run/'contacts240.json',run/'initial_values.json',root/'stability_adapter_2/initial_pose_contacts_v1/analyze_v1.py',root/'stability_adapter_2/free_guitar_learning_v1/geometry_v1.py']
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
pins={str(p):sha(p) for p in files};(out/'inputs_before.json').write_text(json.dumps(pins,indent=2))
initial=json.loads((run/'initial_values.json').read_text());states=selected(run/'states240.json',[5280,6960]);contacts=selected(run/'contacts240.json',[5280,6960]);results=[]
for step in [5280,6960]:
 state=states[step]['state'];g=geometry_snapshot(state,initial['human_body_names'],initial['guitar_body_names']);found=[]
 lookup={**{'human/'+n:row for n,row in zip(initial['human_body_names'],state['human_body_states'])},**{'guitar/'+n:row for n,row in zip(initial['guitar_body_names'],state['guitar_body_states'])}}
 for c in contacts[step]['contacts']:
  if c['lambda']<=0:continue
  if not any(c['body%d_name'%i].startswith('human/LH:index') for i in [0,1]):continue
  if not any(c['body%d_name'%i].startswith('guitar/') for i in [0,1]):continue
  gi=next(i for i in [0,1] if c['body%d_name'%i].startswith('guitar/'))
  name=c['body%d_name'%gi];p=transform(lookup[name]['pose'],[c['localPos%d'%gi][a] for a in 'xyz']);pg=world_to_guitar(p,state['guitar_body_states'][0]);strings=g['starts_G_m']+(pg[1]-g['starts_G_m'][:,1])[:,None]/(g['ends_G_m'][:,1]-g['starts_G_m'][:,1])[:,None]*(g['ends_G_m']-g['starts_G_m']);dist=np.abs(strings[:,0]-pg[0]);near=int(dist.argmin())
  found.append({'pair':[c['body0_name'],c['body1_name']],'point_G_m':pg.tolist(),'nearest_physical_string':near+1,'lateral_m':float(dist[near]),'height_m':float(pg[2]-strings[near,2]),'raw_lambda':c['lambda']})
 results.append({'step':step,'index_native_contacts':found,'index3_origin_G_m':g['finger_distal_origins_G_m']['index'].tolist(),'fret4_5_y_m':g['fret_markers_G_m'][[4,5],1].tolist()})
assert all(sha(Path(p))==v for p,v in pins.items());(out/'result.json').write_text(json.dumps({'frames':results,'inputs_unchanged':True,'new_physics_steps':0},indent=2));print(json.dumps(results,indent=2))
