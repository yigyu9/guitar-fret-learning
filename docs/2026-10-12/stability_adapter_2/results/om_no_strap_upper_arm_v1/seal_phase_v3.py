"""Seal preserved diagnostics, candidate repeat, source and prior phase."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent;R=P.parents[4];A=R/'stability_adapter_2';V=R/'docs/2026-10-12/video/om_no_strap_upper_arm_v1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify(mapping):
 for p,v in mapping.items():assert sha(p)==(v['sha256']if isinstance(v,dict)else v),p
def save(name,x):
 with(P/name).open('x')as f:json.dump(x,f,indent=2,ensure_ascii=False)
for f in list(P.glob('*analysis_inputs_before_*.json'))+list(P.glob('*preflight_inputs_v*.json'))+[P/'support_repeat_inputs_before_v1.json',P/'material_inspection_v1/inputs_before.json']:verify(read(f))
for f in list(P.glob('search_v*/search.json'))+list(P.glob('native_v*/*/attempt.json')):verify(read(f)['input_sha256'])
provenance=list(P.glob('artifacts_*/*provenance*.json'))+list(V.glob('diagnostics_v*/*provenance*.json'))
for f in provenance:
 x=read(f);producer=x['producer'];assert sha(producer['path'])==producer['sha256']
 if 'inputs_before_sha256'in x:
  assert x['inputs_before_sha256']==x['inputs_after_sha256'];verify(x['inputs_before_sha256'])
 else:
  ref=x['source_verification'];assert sha(ref['path'])==ref['sha256_before']==ref['sha256_after']
  for p,h in x['source_videos_before_after_sha256'].items():assert sha(p)==h['before']==h['after']
 verify(x['outputs_sha256'])
for f in V.glob('manifest_v*.json'):
 for v in read(f)['videos']:assert sha(v['source'])==v['source_sha256']==sha(v['destination'])==v['copy_sha256']
start=read(P/'main_append_v1.json');end=read(P/'main_completion_append_v1.json');snaps={}
for a,b in zip(start,end):
 raw0=Path(a['snapshot']).read_bytes();raw1=Path(b['snapshot']).read_bytes();raw2=Path(a['path']).read_bytes();assert raw1.startswith(raw0)and raw2.startswith(raw1)
 assert sha(a['snapshot'])==a['before_sha256']and sha(b['snapshot'])==a['after_sha256']==b['before_sha256']and sha(a['path'])==b['after_sha256'];snaps[a['path']]=a['snapshot']
priorpath=R/'docs/2026-10-12/stability_adapter_2/results/om_thigh_height_initial_v1';prior=read(priorpath/'artifact_inventory_v1.json')
for row in prior['files']:assert sha(snaps.get(row['path'],row['path']))==row['sha256'],row['path']
assert read(priorpath/'final_verification_v1.json')['inventory_sha256']==sha(priorpath/'artifact_inventory_v1.json')
reports=[read(f)for f in P.glob('native_v*/*/report.json')];assert len(reports)==11 and all(r['completed']and r['physics_steps']==1200 and r['actual_strap_enabled']is False and r['strap_force_calls']==r['policy_calls']==r['checkpoint_loads']==0 and not r['forbidden_calls']for r in reports)
assert read(P/'support_candidate_comparison_v1.json')['trace_exact_equal']and read(P/'effort_verification_v10_cases4.json')['passed']
failed=P/'native_v8/three_support_right_effort';assert(failed/'failure.json').exists()and not(failed/'report.json').exists();assert len(read(failed/'trace.json'))==1 and len(read(failed/'media/effort_control_rows.json')['rows'])==0
review=P/'review_final_v1.md';assert review.exists()
files={p.resolve()for p in P.rglob('*')if p.is_file()}|{p.resolve()for p in V.rglob('*')if p.is_file()}|{Path(r['path'])for r in start}|set(A.glob('*om_no_strap_upper_arm_v*.py'))|set(A.glob('OM_NO_STRAP_UPPER_ARM_PLAN_V*.md'))|{A/'inspect_om_surface_materials_v1.py'}
assert not any((P/name).exists()for name in ['source_final_v1.json','artifact_inventory_v1.json','final_verification_v1.json'])
save('source_final_v1.json',{str(p):sha(p)for p in sorted(files)if p.parent==A or p.name.startswith('seal_phase_')});files.add(P/'source_final_v1.json');inventory={'files':[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}for p in sorted(files)]};save('artifact_inventory_v1.json',inventory)
save('final_verification_v1.json',{'passed':True,'completed_native_runs':len(reports),'physics_steps_total':sum(r['physics_steps']for r in reports),'failed_first_step_runs':1,'failed_first_step_physics_steps':0,'material_read_only_runs':1,'material_read_only_physics_steps':0,'source_rejected_front_clamp_and_unseeded_neck_side_native_runs':0,'prior_preserved_files':len(prior['files']),'prior_inventory_sha256':sha(priorpath/'artifact_inventory_v1.json'),'review_sha256':sha(review),'inventory_sha256':sha(P/'artifact_inventory_v1.json'),'all_recorded_inputs_unchanged':True,'main_four_append_only':True,'all_actual_strap_force_calls':0,'candidate_identical_condition_repeat':True,'scope':'five-second hold candidate; no music, perturbation robustness, force distribution or cooked penetration certification'})
for row in inventory['files']:assert sha(row['path'])==row['sha256']
print(json.dumps({'passed':True,'files':len(files),'prior_preserved_files':len(prior['files']),'completed_native_runs':len(reports)},ensure_ascii=False))
