from pathlib import Path
import ast,hashlib,json,re,shutil
R=Path('/home/ajou/yigyu/3');A=R/'stability_adapter_2';D=R/'docs/2026-10-12/stability_adapter_2';B=D/'results';P=B/'finger_curl_diagnosis_v1';PREV=B/'fixed_strap_shoulder_response_v1';checks={};cache={}
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 p=Path(p)
 if str(p) not in cache:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for block in iter(lambda:f.read(1048576),b''):h.update(block)
  cache[str(p)]=h.hexdigest()
 return cache[str(p)]
def check(k,v):
 assert v,k
 checks[k]=True
def closure(d):return all(sha(p)==h for p,h in d.items())
assert not (P/'final_verification.json').exists() and not (P/'artifact_inventory.json').exists()
a=read(P/'analysis.json');e=read(P/'analysis_execution.json');m=read(P/'source_before_manifest.json')
check('analysis4checks10inputs_exact',len(a['checks'])==4 and all(a['checks'].values()) and len(a['input_sha256_before'])==10 and a['input_sha256_before']==a['input_sha256_after'] and closure(a['input_sha256_before']))
check('analysis21joint5contactrows',len(a['joint_rows'])==21 and len(a['distal_body_contacts'])==5)
check('analysis_execution0_sources_log_exact',e['exit_code']==0 and e['input_sha256_before']==e['input_sha256_after'] and closure(e['input_sha256_before']) and e['log_sha256']==sha(P/'analysis.log'))
check('pre_execution_4sourcecopies_exact',len(m)==4 and all(sha(p)==sha(v['snapshot'])==v['sha256'] for p,v in m.items()))
check('no_new_physics_actor_training',all(a[k]==0 for k in ['native_initializations','physics_steps','actor_inference_calls','training_updates']))
ast.parse((A/'analyze_finger_curl.py').read_text(),feature_version=(3,8));check('python38_syntax',True)
counts=read(PREV/'final_verification.json')['counts']['previous_inventories'].copy();counts[PREV.name]=len(read(PREV/'artifact_inventory.json'))
for name,n in counts.items():
 inv=read(B/name/'artifact_inventory.json');check('preserved_'+name,len(inv)==n and all(Path(p).stat().st_size==v['size'] and sha(p)==v['sha256'] for p,v in inv.items()))
before=read(P/'journal_before.json')
for p in [A/'README.md',A/'PLAN.md',D/'VISUAL_REPORT.md']:check('append_only_'+p.name,hashlib.sha256(p.read_bytes()[:before[str(p)]['size']]).hexdigest()==before[str(p)]['sha256'])
for p in P.glob('*.md'):
 for target,line in re.findall(r'\]\(<?(/[^)>]+?)(?::(\d+))?>?\)',p.read_text()):
  q=Path(target);check('link_'+str(len(checks)),q.exists() and (not line or len(q.read_text().splitlines())>=int(line)))
check('independent_review',(P/'review.md').is_file())
manifest={}
for p in [A/'analyze_finger_curl.py',A/'FINGER_CONTACT_REGION_PLAN.md',A/'README.md',A/'PLAN.md',D/'VISUAL_REPORT.md']+list(P.glob('*.md')):
 dest=P/'source_final'/p.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);manifest[str(p)]={'snapshot':str(dest),'sha256':sha(p)}
(P/'source_final_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(P/'final_verification.json').write_text(json.dumps(dict(checks=checks,counts=dict(checks=len(checks),previous_inventories=counts,native_initializations=0,physics_steps=0,actor_inference_calls=0,training_updates=0),scope='saved-data diagnosis and future contact-region design; no new render/physics/control change',source_final_manifest_sha256=sha(P/'source_final_manifest.json')),indent=2)+'\n')
inventory={str(p):dict(size=p.stat().st_size,sha256=sha(p)) for p in sorted(P.rglob('*')) if p.is_file() and p.name!='artifact_inventory.json'}
(P/'artifact_inventory.json').write_text(json.dumps(inventory,indent=2)+'\n');print(json.dumps(dict(checks=len(checks),previous_phases=len(counts),inventory=len(inventory),native_initializations=0)))
