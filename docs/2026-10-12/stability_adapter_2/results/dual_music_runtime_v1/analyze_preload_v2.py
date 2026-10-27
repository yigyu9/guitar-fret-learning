"""Saved native data analysis; no simulation or candidate generation."""
import hashlib,json
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parent
BASE=P.parent/'environment_foundation_v1/native_neutral_v2'
folders={'neutral0':BASE,'preload050':P/'preload050_v2','preload100':P/'preload100_v2'}
paths=[f/n for f in folders.values() for n in ('trace.json','report.json','initial_values.json')]+[Path(__file__)]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
hashes={str(p):sha(p) for p in paths}
result={};initials=[]
for name,f in folders.items():
    rows=json.loads((f/'trace.json').read_text());report=json.loads((f/'report.json').read_text());init=json.loads((f/'initial_values.json').read_text())
    assert report['completed'] and report['physics_steps']==1200 and len(rows)==301
    old=name=='neutral0'
    p=np.array([r['guitar_position_W_m' if old else 'position_W_m'] for r in rows])
    q=np.array([r['guitar_quaternion_xyzw' if old else 'quaternion_xyzw'] for r in rows]);q/=np.linalg.norm(q,axis=1)[:,None]
    angles=np.rad2deg(2*np.arccos(np.clip(abs(q@q[0]),0,1)))
    state=init['native_initial_state'];initials.append(state)
    z=init['z_chest_frozen_m'] if old else state['human_body_states'][init['human_body_names'].index('Chest')]['pose']['p']['z']
    outside=np.maximum(np.maximum(np.array([-.5,-.15,.65])-p,p-np.array([-.15,.15,z])),0)
    result[name]={'guitar_max_displacement_from_initial_mm':float(np.linalg.norm(p-p[0],axis=1).max()*1000),
        'guitar_final_displacement_from_initial_mm':float(np.linalg.norm(p[-1]-p[0])*1000),
        'guitar_max_rotation_from_initial_deg':float(angles.max()),'guitar_final_rotation_from_initial_deg':float(angles[-1]),
        'position_box_max_outside_norm_mm':float(np.linalg.norm(outside,axis=1).max()*1000),
        'position_box_outside_samples':int(np.any(outside>0,axis=1).sum()),'samples':len(rows),
        'guitar_final_position_W_m':p[-1].tolist(),'physics_steps':report['physics_steps']}
assert all(s==initials[0] for s in initials)
selected=min(result,key=lambda k:(result[k]['position_box_max_outside_norm_mm'],result[k]['guitar_max_displacement_from_initial_mm']))
assert all(sha(Path(p))==v for p,v in hashes.items())
with (P/'preload_analysis_v2.json').open('x') as f:json.dump({'scope':'saved60Hznativeactor-root pose samples; core positionbox only, no SO3 allowed-region/contact certification',
    'input_sha256':hashes,'inputs_unchanged':True,'same_initial_native_state':True,'conditions':result,
    'selected_condition':selected,'selected_factor':{'neutral0':0.,'preload050':.5,'preload100':1.}[selected],
    'selection_rule':'minimum maximum core position-box violation, then maximum initial displacement; diagnostic choice only',
    'stability_success':False,'training_ready':False},f,indent=2)
print(json.dumps(result,indent=2));print('selected',selected)
