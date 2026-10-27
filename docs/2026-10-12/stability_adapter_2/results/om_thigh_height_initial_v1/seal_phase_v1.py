"""Preserve prior phase and verify completed lower-height inputs/media."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent;R=P.parents[4];A=R/'stability_adapter_2';V=R/'docs/2026-10-12/video/om_thigh_height_initial_v1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify(mapping):
 for p,v in mapping.items():assert sha(p)==(v['sha256'] if isinstance(v,dict) else v),p
def save(name,x):
 with (P/name).open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False)
verify(read(P/'analysis_inputs_before_v1.json'));verify(read(P/'preflight_inputs_v1.json'))
for f in P.glob('search_v*/search.json'):verify(read(f)['input_sha256'])
for f in P.glob('native_v1/*/attempt.json'):verify(read(f)['input_sha256'])
for f in P.glob('artifacts_v1/*provenance*.json'):
 x=read(f);assert x['inputs_before']==x['inputs_after'];verify(x['inputs_before']);verify(x['outputs'])
for v in read(V/'manifest_v1.json')['videos']:
 assert sha(v['source'])==v['source_sha256']==sha(v['destination'])==v['copy_sha256']
start=read(P/'main_append_v1.json');end=read(P/'main_completion_append_v1.json');snapshots={}
for before,after in zip(start,end):
 b0=Path(before['snapshot']).read_bytes();b1=Path(after['snapshot']).read_bytes();b2=Path(before['path']).read_bytes()
 assert b1.startswith(b0) and b2.startswith(b1)
 assert sha(before['snapshot'])==before['before_sha256'] and sha(after['snapshot'])==before['after_sha256']==after['before_sha256'] and sha(before['path'])==after['after_sha256']
 snapshots[before['path']]=before['snapshot']
previous=R/'docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1';prior=read(previous/'artifact_inventory_v1.json')
for row in prior['files']:assert sha(snapshots.get(row['path'],row['path']))==row['sha256'],row['path']
assert read(previous/'final_verification_v1.json')['inventory_sha256']==sha(previous/'artifact_inventory_v1.json')
review=P/'review_final_v1.md';assert review.exists()
files={p.resolve() for p in P.rglob('*') if p.is_file()}|{p.resolve() for p in V.rglob('*') if p.is_file()}|{Path(x['path']) for x in start}|set(A.glob('*om_thigh_height_initial_v*.py'))|set(A.glob('OM_THIGH_HEIGHT_INITIAL_PLAN_V*.md'))
source={str(p):sha(p) for p in sorted(files) if p.parent==A or p.name=='seal_phase_v1.py'};save('source_final_v1.json',source);files.add(P/'source_final_v1.json')
inventory={'files':[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}for p in sorted(files)]};save('artifact_inventory_v1.json',inventory)
save('final_verification_v1.json',{'passed':True,'new_native_runs':2,'new_physics_steps_total':2400,'prior_preserved_files':len(prior['files']),'prior_inventory_sha256':sha(previous/'artifact_inventory_v1.json'),'review_sha256':sha(review),'inventory_sha256':sha(P/'artifact_inventory_v1.json'),'all_recorded_inputs_unchanged':True,'main_four_append_only':True,'six_videos_exact':True,'source_gap_scope':'min left/right Hip distance, not vertical height or cooked certification'})
for row in inventory['files']:assert sha(row['path'])==row['sha256']
print(json.dumps({'passed':True,'files':len(files),'prior_preserved_files':len(prior['files'])}))
