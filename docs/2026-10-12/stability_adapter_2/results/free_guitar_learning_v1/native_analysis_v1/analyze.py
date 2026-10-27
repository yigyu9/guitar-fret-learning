"""Read-only connection diagnostics; no music or V3 success certificate."""
from pathlib import Path
import gzip,hashlib,json
import numpy as np
from scipy.spatial.transform import Rotation
root=Path('/home/ajou/yigyu/3')
phase=root/'docs/2026-10-12/stability_adapter_2/results/free_guitar_learning_v1'
run=phase/'native_smoke_v1';out=Path(__file__).parent
files=[Path(__file__)]+[run/name for name in ['report.json','comparison.json','initial_baseline.json','initial_handoff.json','prepared_baseline.json','prepared_handoff.json','baseline240.json.gz','zero_handoff240.json.gz','nonzero_handoff240.json.gz']]
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def read(path):
 return json.load(gzip.open(path,'rt')) if path.suffix=='.gz' else json.loads(path.read_text())
def pose(state):
 p=state['guitar_body_states'][0]['pose']
 return np.array([p['p'][a] for a in 'xyz']),Rotation.from_quat([p['r'][a] for a in 'xyzw'])
def metrics(rows, reference):
 p,r=pose(reference);samples=[entry['native'] for row in rows for entry in row['physics_samples240']]
 return {'samples':len(samples),'first_physics_step':samples[0]['physics_step'],'last_physics_step':samples[-1]['physics_step'],
 'max_root_displacement_from_prepared_mm':max(float(np.linalg.norm(pose(s)[0]-p))*1000 for s in samples),
 'max_rotation_from_prepared_deg':max(float((r.inv()*pose(s)[1]).magnitude())*180/np.pi for s in samples)}
pins={str(p):sha(p) for p in files};(out/'inputs_before.json').write_text(json.dumps(pins,indent=2)+'\n')
report=read(run/'report.json');assert report['completed'],report
b=read(run/'baseline240.json.gz')['rows'];z=read(run/'zero_handoff240.json.gz')['rows'];n=read(run/'nonzero_handoff240.json.gz')['rows']
pb=read(run/'prepared_baseline.json')['native'];ph=read(run/'prepared_handoff.json')['native']
assert pb['physics_step']==ph['physics_step']==5280
comparison=read(run/'comparison.json');contract=comparison['handoff_initial']['target_contract'];names=read(run/'initial_handoff.json')['joint_names'];held=[names.index(x) for x in contract['held_names']];active=[names.index(x) for x in contract['action_order']]
reference=np.array(comparison['handoff_initial']['prepared_target105_rad']);commands=z+n
held_error=max(float(np.abs(np.array(row['native_final_target105_rad'])[held]-reference[held]).max()) for row in commands)
assert held_error==0
assert all(len(row['physics_samples240'])==4 and row['physics_steps_advanced']==4 for row in commands)
assert all(np.array_equal(row['normalized_action39'],np.zeros(39)) for row in z)
assert all(np.array_equal(row['normalized_action39'],np.full(39,.25)) for row in n)
initial_b=read(run/'initial_baseline.json');initial_h=read(run/'initial_handoff.json');assert initial_b['native_PD_properties']==initial_h['native_PD_properties']
result={'scope':'Short native connection test; not music learning, full V3 stability or general controller validation',
 'original_baseline':metrics(b,pb),'zero_policy_handoff':metrics(z,ph),'small_nonzero_handoff':metrics(n,ph),
 'prepared_native_state_exact_between_fresh_resets':pb==ph,'original_native_properties_exact_between_trials':True,
 'upper42_held_target_max_error_rad':held_error,'action_half_range_rad':.002,'nonzero_normalized_action':.25,
 'max_active_target_offset_rad':max(float(np.abs(np.array(row['native_final_target105_rad'])[active]-reference[active]).max()) for row in n),
 'zero_vs_original_max_target_difference_rad':comparison['zero_policy_vs_original_baseline_max_target_difference_rad'],
 'zero_and_nonzero_control_ticks':[len(z),len(n)],'new_training_updates':report['new_training_updates'],'inputs_unchanged':all(sha(Path(p))==h for p,h in pins.items())}
assert result['inputs_unchanged']
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
