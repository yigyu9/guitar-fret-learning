from pathlib import Path
import hashlib,json
import numpy as np
from stability_adapter_2.free_guitar_learning_v1.geometry_v1 import geometry_snapshot,fret_target,relative_sweep_inputs
from stability_adapter_2.initial_pose_contacts_v1.analyze_v1 import selected
root=Path('/home/ajou/yigyu/3');out=Path(__file__).parent
run=root/'paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/native_free_strike_v14'
paths=[Path(__file__),run/'states240.json',run/'initial_values.json',root/'stability_adapter_2/free_guitar_learning_v1/geometry_v1.py',root/'stability_adapter_2/initial_pose_contacts_v1/analyze_v1.py',root/'stability_adapter_2/initial_pose_video60_v1/replay_v6.py']
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
pins={str(p):sha(p) for p in paths};(out/'inputs_before.json').write_text(json.dumps(pins,indent=2))
initial=json.loads((run/'initial_values.json').read_text());data=selected(run/'states240.json',[6960,6961])
samples=[geometry_snapshot(data[n]['state'],initial['human_body_names'],initial['guitar_body_names']) for n in [6960,6961]]
sweep=relative_sweep_inputs(*samples)
for snapshot in samples:
 for string in range(1,7):
  for fret in range(1,23):assert np.isfinite(fret_target(snapshot,string,fret)).all()
assert all(sha(Path(p))==h for p,h in pins.items())
result={'status':'pass','sample_steps':[6960,6961],'fret_targets_checked':264,'max_local_string_endpoint_change_m':max(float(np.abs(samples[0][k]-samples[1][k]).max()) for k in ['starts_G_m','ends_G_m']),'relative_pick_displacement_m':(sweep['current_tip_g']-sweep['previous_tip_g']).tolist(),'dt_s':sweep['dt'],'inputs_unchanged':True,'new_physics_steps':0,'scope':'Read-only real recorded marker geometry; not a music/contact success test'}
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
