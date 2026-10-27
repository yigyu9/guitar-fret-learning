"""Saved native observations only; never alter the active training process."""
from pathlib import Path
import hashlib
import json
import numpy as np
from scipy.spatial.transform import Rotation

ROOT=Path('/home/ajou/yigyu/3')
OUT=Path(__file__).resolve().parent
inputs=json.loads((OUT/'input_sha256.json').read_text())
inputs[str(Path(__file__).resolve())]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in inputs.items())
base=ROOT/'docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/long_run_v3/evaluations'
conditions=[]
for label in ('initial_000000','update_000001'):
    native=base/label/'native/episode_0001'
    rows=json.loads((native/'controls.json').read_text())
    trace=json.loads((native/'trace.json').read_text())
    outside=np.array([r['position_outside_m'] for r in rows])
    exited=(outside>1e-7).any(1)
    run=longest=0
    for value in exited:
        run=run+1 if value else 0
        longest=max(run,longest)
    p=np.array([r['position_W_m'] for r in trace])
    conditions.append({'condition':label,'control_samples':len(rows),
        'position_outside_fraction':float(exited.mean()),
        'rotation_outside_fraction':float(np.mean([not r['rotation']['inside'] for r in rows])),
        'max_position_excess_per_axis_m':outside.max(0).tolist(),
        'longest_contiguous_position_exit_s':longest/60,
        'max_initial_displacement_m':float(np.linalg.norm(p-p[0],axis=1).max())})
old=json.loads((ROOT/'docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/native/initial_values.json').read_text())
state=json.loads((base/'initial_000000/native/episode_0001/initial_values.json').read_text())['native_initial_state']
names=old['human_body_names']; bodies=state['human_body_states']
assert len(names)==len(bodies)
strap=json.loads((ROOT/'stability_adapter_2/config.json').read_text())['strap']
states=[state['guitar_body_states'][0]]+[bodies[names.index(n)] for n,_ in strap['guides']]+[state['guitar_body_states'][0]]
local=[strap['buttons_G_m'][0]]+[v for _,v in strap['guides']]+[strap['buttons_G_m'][1]]
points=[]
for body,point in zip(states,local):
    p,q=body['pose']['p'],body['pose']['r']
    points.append(np.array([p[k] for k in 'xyz'])+Rotation.from_quat([q[k] for k in 'xyzw']).apply(point))
length=float(np.linalg.norm(np.diff(points,axis=0),axis=1).sum())
rest=float(old['absolute_strap_rest_length_m'])
result={'scope':'saved native data assessment; no new physics or strap activation',
    'conditions':conditions,'fixed_original_rest_length_m':rest,
    'initial_route_reconstructed_m':length,'initial_slack_m':rest-length,
    'route_mapping_scope':'previous fixed-lower native body names; count matched, mapping must recheck in live strap scene',
    'fixed_law':{k:strap[k] for k in ('stiffness_n_per_m','damping_n_s_per_m','max_tension_n')},
    'strap_candidate_recommended':True,'inputs_unchanged':all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in inputs.items()),
    'input_sha256':inputs}
with (OUT/'assessment.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
assert result['inputs_unchanged']
print(json.dumps(result['conditions'],indent=2))
