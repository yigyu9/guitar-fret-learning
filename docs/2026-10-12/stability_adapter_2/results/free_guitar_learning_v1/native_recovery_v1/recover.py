"""Audit preserved physical outputs after the original reporting-only failure."""
import gzip,hashlib,json
from pathlib import Path
phase=Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/free_guitar_learning_v1')
run=phase/'native_smoke_v1';out=Path(__file__).parent
names=['inputs_before.json','attempt.json','comparison.json','initial_baseline.json','initial_handoff.json','prepared_baseline.json','prepared_handoff.json','baseline240.json.gz','zero_handoff240.json.gz','nonzero_handoff240.json.gz','original_source_model_parity.json','media_baseline/capture.json','media_handoff/capture.json','media_baseline/videos.json','media_handoff/videos.json']
paths=[Path(__file__),phase/'native_smoke_v1.log']+[run/n for n in names]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def read(p):return json.load(gzip.open(p,'rt')) if p.suffix=='.gz' else json.loads(p.read_text())
pins={str(p):sha(p) for p in paths};(out/'inputs_before.json').write_text(json.dumps(pins,indent=2)+'\n')
oldpins=read(run/'inputs_before.json');changed=[p for p,h in oldpins.items() if sha(Path(p))!=h];assert not changed
comparison=read(run/'comparison.json');assert comparison['policy_forbidden_calls']==[]
checks={}
for name,start,end in [('baseline240.json.gz',5281,5520),('zero_handoff240.json.gz',5281,5520),('nonzero_handoff240.json.gz',5521,5760)]:
 rows=read(run/name)['rows'];steps=[s['native']['physics_step'] for row in rows for s in row['physics_samples240']]
 assert len(rows)==60 and steps==list(range(start,end+1))
 checks[name]={'control_ticks':len(rows),'physics_samples':len(steps),'first_step':start,'last_step':end}
for name in ['initial_baseline.json','initial_handoff.json']:
 x=read(run/name);assert x['physics_step']==0 and x['human_root_fixed'] and not x['guitar_root_fixed'] and not x['guitar_gravity_disabled']
 assert len(x['joint_names'])==105 and len(x['zero_range_indices'])==8
for name in ['prepared_baseline.json','prepared_handoff.json']:assert read(run/name)['native']['physics_step']==5280
for name,count,step in [('media_baseline',116,5520),('media_handoff',121,5760)]:
 capture=read(run/name/'capture.json');assert len(capture['frames'])==count and capture['frames'][-1]['physics_step']==step
 assert all(row['render_preserves_states'] for row in capture['frames'])
 for row in capture['frames']:
  for p,h in row['image_sha256'].items():assert sha(Path(p))==h
 for video in read(run/name/'videos.json').values():assert sha(Path(video['path']))==video['sha256']
assert not (run/'report.json').exists()
trace=(phase/'native_smoke_v1.log').read_text();assert "'NoneType' object has no attribute 'endswith'" in trace
assert all(sha(Path(p))==h for p,h in pins.items())
result={'physical_segments_completed':True,'recovery_audit_passed':True,'original_process_exit_code':1,
 'original_failure':'Post-import summary collection called endswith on namespace module __file__=None after all physics/data/video work',
 'original_report_present':False,'original_run_modified':False,'raw_segment_checks':checks,
 'total_new_physics_steps':11280,'total_physical_seconds':47.,'new_training_updates':0,
 'original_before_pinned_inputs':len(oldpins),'changed_original_inputs':changed,
 'original_source_model_parity_record':str(run/'original_source_model_parity.json'),
 'actual_post_import_list_available':False,'actual_post_import_closure_certified':False,
 'scope':'Read-only physical-output recovery audit. Original runner failed at final reporting; no additional physics. Does not recreate the lost original post-import module list or certify musical/V3 success.'}
(out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
