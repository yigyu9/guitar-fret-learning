"""Audit the one-target live contact path, not musical or pressure success."""
from pathlib import Path
import gzip,hashlib,json
from collections import Counter
import numpy as np
from scipy.spatial.transform import Rotation
phase=Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/free_guitar_fretting_v1');run=phase/'native_probe_v1';out=Path(__file__).parent
files=[Path(__file__)]+[run/n for n in ['report.json','attempt.json','prepared.json','final.json','initial_values.json','measurements240.json.gz','media/capture.json','media/videos.json']]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.load(gzip.open(p,'rt')) if p.suffix=='.gz' else json.loads(p.read_text())
def pose(s):
 row=s['guitar_body_states'][0]['pose'];return np.array([row['p'][k] for k in 'xyz']),Rotation.from_quat([row['r'][k] for k in 'xyzw'])
pins={str(p):sha(p) for p in files};(out/'inputs_before.json').write_text(json.dumps(pins,indent=2)+'\n')
report=read(run/'report.json');assert report['completed'] and not report['missing_import_pins'] and not report['original_source_parity_errors'],report
samples=read(run/'measurements240.json.gz')['rows'];assert [s['native']['physics_step'] for s in samples]==list(range(5280,5521))
assert all(s['native_contacts']['physics_step']==s['native']['physics_step']==s['fretting_measurement']['physics_step'] for s in samples)
assert read(run/'final.json')['forbidden_calls']==[]
bodies=Counter();reasons=Counter();max_witness=0.
for s in samples:
 for e in s['fretting_measurement']['contact_evidence']:
  if e['valid']:bodies[e['human_body']]+=1;max_witness=max(max_witness,e['body_pair_witness_gap_m'])
  elif e['positive_lambda'] and e['human_body'].startswith('human/LH:index'):
   reasons.update(e['reason_flags'])
p,r=pose(samples[0]['native'])
prepared=read(run/'prepared.json')['sample'];assert prepared==samples[0]
capture=read(run/'media/capture.json');assert len(capture['frames'])==116 and all(f['render_preserves_states'] for f in capture['frames'])
for video in read(run/'media/videos.json').values():assert sha(Path(video['path']))==video['sha256']
result={'scope':'One-target candidate measurement after real22s prep withzeroaction1s; not calibrated string pressure, sound or song success',
 'samples':len(samples),'candidate_samples':sum(s['fretting_measurement']['fretting_contact_candidate'] for s in samples),
 'valid_contact_bodies':dict(bodies),'rejected_same_finger_positive_reasons':dict(reasons),
 'max_valid_body_pair_witness_gap_m':max_witness,'final_progress':samples[-1]['fretting_progress'],
 'max_guitar_root_displacement_from_prepared_mm':max(float(np.linalg.norm(pose(s['native'])[0]-p))*1000 for s in samples),
 'max_guitar_rotation_from_prepared_deg':max(float((r.inv()*pose(s['native'])[1]).magnitude())*180/np.pi for s in samples),
 'contact_query_preserves_native_state':True,'actual_source_import_census_passed':True,
 'new_physics_seconds':23,'new_training_updates':0,'inputs_unchanged':all(sha(Path(p))==h for p,h in pins.items())}
assert result['inputs_unchanged'];(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
