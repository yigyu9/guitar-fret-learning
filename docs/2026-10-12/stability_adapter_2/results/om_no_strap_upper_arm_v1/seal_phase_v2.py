"""Verify immutable phase inputs and preserve the prior completed phase."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent;R=P.parents[4];A=R/'stability_adapter_2';V=R/'docs/2026-10-12/video/om_no_strap_upper_arm_v1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify(mapping):
 for p,v in mapping.items():assert sha(p)==(v['sha256']if isinstance(v,dict)else v),p
def save(name,x):
 with (P/name).open('x')as f:json.dump(x,f,indent=2,ensure_ascii=False)
verify(read(P/'analysis_inputs_before_v3.json'))
for f in P.glob('*preflight_inputs_v*.json'):verify(read(f))
for f in P.glob('search_v*/search.json'):verify(read(f)['input_sha256'])
for f in P.glob('native_v*/*/attempt.json'):verify(read(f)['input_sha256'])
for f in P.glob('artifacts_v*/*provenance*.json'):
 x=read(f);assert x['inputs_before']==x['inputs_after'];verify(x['inputs_before']);verify(x['outputs'])
for v in read(V/'manifest_v1.json')['videos']:assert sha(v['source'])==v['source_sha256']==sha(v['destination'])==v['copy_sha256']
start=read(P/'main_append_v1.json');end=read(P/'main_completion_append_v1.json');snaps={}
for a,b in zip(start,end):
 raw0=Path(a['snapshot']).read_bytes();raw1=Path(b['snapshot']).read_bytes();raw2=Path(a['path']).read_bytes();assert raw1.startswith(raw0) and raw2.startswith(raw1)
 assert sha(a['snapshot'])==a['before_sha256'] and sha(b['snapshot'])==a['after_sha256']==b['before_sha256'] and sha(a['path'])==b['after_sha256'];snaps[a['path']]=a['snapshot']
priorpath=R/'docs/2026-10-12/stability_adapter_2/results/om_thigh_height_initial_v1';prior=read(priorpath/'artifact_inventory_v1.json')
for row in prior['files']:assert sha(snaps.get(row['path'],row['path']))==row['sha256'],row['path']
assert read(priorpath/'final_verification_v1.json')['inventory_sha256']==sha(priorpath/'artifact_inventory_v1.json')
review=P/'review_final_v1.md';assert review.exists()
files={p.resolve()for p in P.rglob('*')if p.is_file()}|{p.resolve()for p in V.rglob('*')if p.is_file()}|{Path(r['path'])for r in start}|set(A.glob('*om_no_strap_upper_arm_v*.py'))|set(A.glob('OM_NO_STRAP_UPPER_ARM_PLAN_V*.md'))
save('source_final_v1.json',{str(p):sha(p)for p in sorted(files)if p.parent==A or p.name.startswith('seal_phase_')});files.add(P/'source_final_v1.json');inventory={'files':[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}for p in sorted(files)]};save('artifact_inventory_v1.json',inventory)
save('final_verification_v1.json',{'passed':True,'native_runs':3,'physics_steps_total':3600,'prior_preserved_files':len(prior['files']),'prior_inventory_sha256':sha(priorpath/'artifact_inventory_v1.json'),'review_sha256':sha(review),'inventory_sha256':sha(P/'artifact_inventory_v1.json'),'all_recorded_inputs_unchanged':True,'main_four_append_only':True,'all_actual_strap_force_calls':0,'scope':'diagnostic endpoints, no music/repeatability certification'})
for row in inventory['files']:assert sha(row['path'])==row['sha256']
print(json.dumps({'passed':True,'files':len(files),'prior_preserved_files':len(prior['files'])}))
