"""Seal completed smoke/artifacts only; exclude the ongoing learner's live outputs."""
import hashlib,json,shutil
from pathlib import Path
P=Path(__file__).resolve().parent
checks={};sources=set()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
for version in (1,2):
 m=read(P/f'source_before_native_v{version}/manifest.json')
 records=m['records'] if 'records' in m else [dict(source=p,**v) for p,v in m.items()]
 for r in records:
  checks['source:'+r['source']]=sha(r['source'])==sha(r['copy'])==r['sha256'];sources.add(r['source'])
checks['runtime_all_pass']=read(P/'runtime_verification_v2.json')['checks_passed']
checks['runtime_inputs_still_exact']=all(sha(p)==h for p,h in read(P/'runtime_verification_v2.json')['input_sha256'].items())
checks['review_exists']=(P/'review_runtime_v1.md').exists()
for n in ['qp_final_comparison_provenance_v1.json','qp_final_comparison_provenance_addendum_v2.json','README_FINAL_v2_provenance.json']:
 r=read(P/'artifacts_v1'/n)
 for key in ['inputs_before','inputs_after','outputs','final_visual_outputs','final_document_outputs']:
  items=r.get(key,[])
  if isinstance(items,dict):items=list(items.values())
  for item in items:
   checks['artifact:'+item['path']]=sha(item['path'])==item['sha256']
for p,r in read(P/'main_prefix_before_v1/manifest.json').items():
 checks['main-prefix:'+p]=Path(p).read_bytes().startswith(Path(r['snapshot']).read_bytes()) and sha(r['snapshot'])==r['sha256']
historical={r['source']:r['copy'] for r in read(P/'historical_input_prefix_v1/manifest.json')['records']}
checks['failed_attempt_inputs_preserved']=all(sha(historical.get(p,p))==h for p,h in read(P/'smoke_on_v1/attempt.json')['input_sha256'].items())
checks['long_start_only']=read(P/'long_start_snapshot_v1.json')['checks_passed']
archive=P.parents[2]/'video/archive_v2/final_verification_v1.json'
checks['archive14_exact']=read(archive)['checks_passed'] and read(archive)['count']==14
sources.update(str(P/n) for n in ['verify_runtime_v2.py','analyze_initial_comparison_v1.py','analyze_comparison_v2.py','start_smoke_v2.py','start_long_v1.py','snapshot_long_start_v1.py','seal_completed_v1.py'])
sources.update(str(P/'artifacts_v1'/n) for n in ['build_qp_initial_comparison_draft_v1.py','build_qp_final_comparison_v1.py'])
final=P/'source_final_v1';final.mkdir(exist_ok=False);manifest=[]
for s in sorted(sources):
 source=Path(s);target=final/source.name
 if target.exists():raise FileExistsError(target)
 shutil.copy2(source,target);manifest.append({'source':s,'copy':str(target),'sha256':sha(source)})
 checks['final-source:'+s]=sha(source)==sha(target)
with (final/'manifest.json').open('x') as f:json.dump({'records':manifest},f,indent=2)
files={str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in P.rglob('*') if p.is_file()
       and 'long_on_v1' not in p.relative_to(P).parts and not p.name.startswith('long_on_v1.')
       and not p.name.startswith('supervisor_long_v1.')}
with (P/'artifact_inventory_v1.json').open('x') as f:json.dump({'scope':'fixed completed smoke, artifacts and startup evidence; live long_on_v1 excluded','files':files},f,indent=2)
with (P/'final_verification_v1.json').open('x') as f:json.dump({'checks_passed':all(checks.values()),'checks':checks,
 'review_sha256':sha(P/'review_runtime_v1.md'),'inventory_sha256':sha(P/'artifact_inventory_v1.json'),
 'scope':'completed 1-update native smoke and artifacts, failed-attempt preservation, startup snapshot and video archive; long learning outcome, repeatability, music and production reward not certified'},f,indent=2)
print('seal pass',all(checks.values()),'fixed files',len(files),'source copies',len(manifest))
if not all(checks.values()):raise SystemExit([k for k,v in checks.items() if not v])
