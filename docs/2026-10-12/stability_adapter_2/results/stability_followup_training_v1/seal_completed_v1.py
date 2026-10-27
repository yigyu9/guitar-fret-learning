"""Seal the completed CP86 analysis; do not seal the running learner's future."""
import hashlib,json,shutil
from pathlib import Path
P=Path(__file__).resolve().parent;checks={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
for name in ['analysis_v1.json','reward_analysis_v1.json','action_scale_diagnosis_v1.json','analyzer_function_verification_v3.json']:
 data=read(P/name)
 checks[name+'_verified']=data.get('checks_passed',data.get('inputs_unchanged',False))
 checks[name+'_inputs_exact']=all(sha(path)==h for path,h in data['input_sha256'].items())
for name in ['followup_comparison_provenance_v1.json','followup_action_scale_addendum_v1.json','followup_action_scale_addendum_v2.json']:
 data=read(P/'artifacts_v1'/name)
 for key in ['inputs_before','inputs_after','outputs','document_outputs','reused_final_images']:
  values=data.get(key,[])
  if isinstance(values,dict):values=list(values.values())
  for value in values:checks['artifact:'+value['path']]=sha(value['path'])==value['sha256']
for directory in ['source_before_analysis_v1','source_before_reward_v1']:
 for r in read(P/directory/'manifest.json')['records']:
  checks['source:'+r['source']]=sha(r['source'])==sha(r['copy'])==r['sha256']
review=P/'review_runtime_v1.md'
if not review.exists():raise RuntimeError('runtime review not yet saved')
checks['review_present']=True
archive=P.parents[2]/'video/archive_v3';records=read(archive/'manifest.json')
checks['archive_source_inputs_exact']=all(sha(p)==h for p,h in records['input_sha256'].items())
checks['archive_copies_exact']=all(sha(r['source'])==sha(r['copy'])==r['sha256'] for r in records['records'])
with (archive/'final_verification_v1.json').open('x') as f:json.dump({'checks_passed':checks['archive_source_inputs_exact'] and checks['archive_copies_exact'],
 'count':len(records['records']),'manifest_sha256':sha(archive/'manifest.json'),'scope':'two completed CP86 videos only; future checkpoint videos excluded'},f,indent=2)
S=P/'source_final_v1';S.mkdir(exist_ok=False);manifest=[]
for source in sorted([*P.glob('*.py'),*list((P/'artifacts_v1').glob('*.py'))]):
 target=S/source.name;shutil.copy2(source,target);manifest.append({'source':str(source),'copy':str(target),'sha256':sha(source)})
 checks['final-source:'+str(source)]=sha(source)==sha(target)
with (S/'manifest.json').open('x') as f:json.dump({'records':manifest},f,indent=2)
files={str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in P.rglob('*') if p.is_file()}
with (P/'artifact_inventory_v1.json').open('x') as f:json.dump({'scope':'completed selected-checkpoint analysis, fixed training prefix and artifacts; live parent run not included','files':files},f,indent=2)
with (P/'final_verification_v1.json').open('x') as f:json.dump({'checks_passed':all(checks.values()),'checks':checks,
 'review_sha256':sha(review),'inventory_sha256':sha(P/'artifact_inventory_v1.json'),
 'scope':'one saved CP86 evaluation vs CP1, verified diagnostics/artifacts/archive; no repeatability, body-center naturalness, production reward or future learning certification'},f,indent=2)
print('seal pass',all(checks.values()),'files',len(files),'source copies',len(manifest))
if not all(checks.values()):raise SystemExit([k for k,v in checks.items() if not v])
