"""Read saved native evaluations only; quantify research progress, not crash risk."""
import hashlib,json
from pathlib import Path
import numpy as np
G=Path(__file__).resolve().parent
inputs={str(Path(__file__).resolve()):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
def read(path):
    inputs[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
    return json.loads(path.read_text())
roots={
 'CP86':G.parent/'stability_support_nominal_v1/long_on_v1/evaluations/update_000086/native/episode_0001',
 'CP241':G.parent/'stability_support_nominal_v1/long_on_v2/evaluations/update_000241/native/episode_0001',
 'CP242':G/'smoke_on_v1/evaluations/update_000242/native/episode_0001'}
results={}
for label,base in roots.items():
    evaluation=read(base.parents[1]/'evaluation.json')
    assert evaluation['updates']==int(label[2:])
    rows=read(base/'controls.json');trace=read(base/'trace.json');report=read(base/'report.json')
    outside=np.linalg.norm([r['position_outside_m'] for r in rows],axis=1)
    q=np.array([r['quaternion_xyzw'] for r in trace]);q/=np.linalg.norm(q,axis=1)[:,None]
    angle=2*np.arccos(np.clip(np.abs(q@q[0]),0,1))
    results[label]={'native_episode':str(base),'outside_percent':100*float(np.mean(outside>0)),
        'max_position_outside_norm_m':float(outside.max()),'mean_position_outside_norm_m':float(outside.mean()),
        'max_SO3_from_initial_deg':float(np.degrees(angle.max())),
        'full_horizon_completed':report['full_horizon_completed'],'safety_violation':report['safety_violation'],
        'joint_success_events':report['joint_success_events'],'settled_events':report['settled_events'],
        'accepted_crossings':report['accepted_crossings'],'return':report['return']}
result={'evaluations':results,'input_sha256':inputs,
    'inputs_unchanged':all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in inputs.items()),
    'scope':'three single deterministic native episodes; outside uses current actor-root position box, rotation uses initial-orientation SO3 distance; not body-center naturalness or learning-success certification'}
with (G/'progress_analysis_v1.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False)
print(json.dumps(results,ensure_ascii=False,indent=2))
assert result['inputs_unchanged']
