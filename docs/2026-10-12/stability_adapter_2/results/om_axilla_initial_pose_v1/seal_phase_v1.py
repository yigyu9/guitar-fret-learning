"""Verify immutable inputs and prior phase, then inventory this completed unit."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[4];A=R/'stability_adapter_2';V=R/'docs/2026-10-12/video/om_axilla_initial_pose_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def save(name,data):
 p=P/name
 if p.exists():raise FileExistsError(p)
 p.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
def verify(mapping):
 for p,value in mapping.items():
  h=value['sha256'] if isinstance(value,dict) else value
  assert sha(p)==h,p
# Every started producer and native input closure still matches its recorded input.
verify(read(P/'analysis_inputs_before_v1.json'));verify(read(P/'source_before_native_v1.json'))
for f in P.glob('search_v*/search.json'):verify(read(f)['input_sha256'])
for f in [*P.glob('native_v1/*/attempt.json'),*P.glob('native_v2/*/attempt.json')]:verify(read(f)['input_sha256'])
for f in [P/'artifacts_v1/provenance_v1.json',P/'artifacts_v1/docs_provenance_v1.json',P/'artifacts_v2/provenance_v2.json']:
 x=read(f);assert x['inputs_before']==x['inputs_after'];verify(x['inputs_before']);verify(x['outputs'])
for item in read(V/'manifest_v1.json')['videos']:
 assert sha(item['source'])==item['source_sha256']==sha(item['destination'])==item['copy_sha256']
# Main four are append-only. Original bytes are preserved as before snapshots.
start=read(P/'main_append_v1.json');end=read(P/'main_completion_append_v1.json');snapshots={}
for first,last in zip(start,end):
 p=Path(first['path']);b0=Path(first['snapshot']).read_bytes();b1=Path(last['snapshot']).read_bytes();b2=p.read_bytes()
 assert b1.startswith(b0) and b2.startswith(b1)
 assert sha(first['snapshot'])==first['before_sha256'];assert sha(last['snapshot'])==first['after_sha256']==last['before_sha256'];assert sha(p)==last['after_sha256']
 snapshots[str(p)]=first['snapshot']
previous=R/'docs/2026-10-12/stability_adapter_2/results/guitar_focused_view_v1';prior=read(previous/'artifact_inventory_v1.json')
for row in prior['files']:
 assert sha(snapshots.get(row['path'],row['path']))==row['sha256'],row['path']
assert read(previous/'final_verification_v1.json')['inventory_sha256']==sha(previous/'artifact_inventory_v1.json')
review=P/'review_final_v1.md';assert review.exists()
# Preserve and inventory all current outputs plus exact controller/source closure.
files={p.resolve() for p in P.rglob('*') if p.is_file()}|{p.resolve() for p in V.rglob('*') if p.is_file()}|{Path(row['path']) for row in start}
files|=set(A.glob('*om_axilla*v*.py'))|set(A.glob('OM_AXILLA_*V*.md'))
source={str(p):sha(p) for p in sorted(files) if p.parent==A or p.name in ['analyze_native_v1.py','seal_phase_v1.py']}
save('source_final_v1.json',source);files.add(P/'source_final_v1.json')
inventory={'files':[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(files)]}
save('artifact_inventory_v1.json',inventory)
save('final_verification_v1.json',{'passed':True,'native_runs':3,'physics_steps_total':3600,'prior_preserved_files':len(prior['files']),'prior_inventory_sha256':sha(previous/'artifact_inventory_v1.json'),'review_sha256':sha(review),'inventory_sha256':sha(P/'artifact_inventory_v1.json'),'all_recorded_input_pins_unchanged':True,'main_four_append_only':True,'six_video_copies_exact':True,'stable_pose_adopted':False,'hold_leaf_pre_execution_sha_available':False,'latest_panels':'artifacts_v2','preserved_v1_caption_error':'rearward30deg -> corrected rearward30mm in v2'})
for row in inventory['files']:assert sha(row['path'])==row['sha256']
print(json.dumps({'passed':True,'inventoried_files':len(files),'prior_preserved_files':len(prior['files'])}))
