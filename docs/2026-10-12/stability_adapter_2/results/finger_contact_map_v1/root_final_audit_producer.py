from pathlib import Path
import ast,hashlib,json,re,shutil
R=Path('/home/ajou/yigyu/3');A=R/'stability_adapter_2';D=R/'docs/2026-10-12/stability_adapter_2';B=D/'results';P=B/'finger_contact_map_v1';PREV=B/'finger_curl_diagnosis_v1';checks={};cache={}
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
a=read(P/'analysis.json');config=read(P/'configuration_clarification.json')
check('analysis_contract_inputs_exact',all(v for k,v in a['checks'].items() if k!='single_substep') and len(a['input_sha256_before'])==17 and a['input_sha256_before']==a['input_sha256_after'] and closure(a['input_sha256_before']))
check('configuration_supersedes_default_claim',all(config['checks'].values()) and config['supersedes_analysis_check']=='single_substep' and config['configured_substeps_from_consumed_source']==1 and config['native_SimParams_readback_performed'] is False and config['saved_physics_parameters_contains_substeps'] is False and config['input_sha256_before']==config['input_sha256_after'] and closure(config['input_sha256_before']))
for stage,prefix,n in [('analysis','',6),('configuration','configuration_',11)]:
 e=read(P/(stage+'_execution.json'));m=read(P/(prefix+'source_before_manifest.json'))
 check(stage+'_execution0_source_log_exact',e['exit_code']==0 and e['input_sha256_before']==e['input_sha256_after'] and closure(e['input_sha256_before']) and e['log_sha256']==sha(P/(stage+'.log')))
 check(stage+'_sourcecopies_exact',len(m)==n and all(sha(p)==sha(v['snapshot'])==v['sha256'] for p,v in m.items()))
check('1198_features4snapshots',len((P/'features.jsonl').read_text().splitlines())==1198 and len(a['snapshots'])==4 and [len(s['current_positive_features']) for s in a['snapshots']]==[0,2,0,1])
check('decision_inputs_exact',closure(read(P/'decision_inputs.json')))
check('no_new_physics_actor_training',all(a[k]==0 for k in ['native_initializations','physics_steps','actor_inference_calls','training_updates']))
for name in ['analyze_finger_contact_map.py','verify_finger_map_configuration.py','make_finger_contact_map_artifacts.py']:
 ast.parse((A/name).read_text(),feature_version=(3,8));check(name+'_python38_syntax',True)
AR=P/'artifacts';am=read(AR/'artifact_manifest.json');ae=read(AR/'producer_execution.json')
check('artifact_inputs_outputs_exact',am['inputs_sha256_before']==am['inputs_sha256_after'] and closure(am['inputs_sha256_before']) and all(sha(AR/n)==h for n,h in am['outputs_sha256'].items()) and sha(A/'make_finger_contact_map_artifacts.py')==am['producer_sha256_before']==am['producer_sha256_after'])
check('artifact_execution0_closure',ae['exit_code']==0 and ae['producer_sha256_before']==ae['producer_sha256_after']==am['producer_sha256_before'] and sha(AR/'producer.log')==ae['log_sha256'] and all(ae[k]==0 for k in ['native_calls','physics_steps','actor_inference_calls','training_updates']))
check('artifact_wrapper_execution_hashes',ae['wrapper_sha256_before']==ae['wrapper_sha256_after']==am['wrapper_sha256_before']==am['wrapper_sha256_after']==sha(AR/'run_finger_contact_map_artifacts.sh') and ae['inputs_sha256_before']==ae['inputs_sha256_after']==am['inputs_sha256_before'] and ae['outputs_sha256']==am['outputs_sha256'])
ss=read(AR/'source_snapshot.json');check('artifact_pre_run_sources_exact',all(sha(r['original_path'])==sha(AR/r['copy_path'])==r['sha256'] for r in ss['files']))
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
for p in [A/n for n in ['analyze_finger_contact_map.py','verify_finger_map_configuration.py','make_finger_contact_map_artifacts.py','FINGER_CONTACT_MAP_PLAN.md','FINGER_CONTACT_MAP_DECISION.md','README.md','PLAN.md']]+[D/'VISUAL_REPORT.md']+list(P.glob('*.md')):
 dest=P/'source_final'/p.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);manifest[str(p)]={'snapshot':str(dest),'sha256':sha(p)}
(P/'source_final_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(P/'final_verification.json').write_text(json.dumps(dict(checks=checks,counts=dict(checks=len(checks),previous_inventories=counts,native_initializations=0,physics_steps=0,actor_inference_calls=0,training_updates=0),scope='saved native feature/body-origin map and separate scientificplot; source substeps setting distinguished from native readback; no new physical/control change',source_final_manifest_sha256=sha(P/'source_final_manifest.json')),indent=2)+'\n')
inventory={str(p):dict(size=p.stat().st_size,sha256=sha(p)) for p in sorted(P.rglob('*')) if p.is_file() and p.name!='artifact_inventory.json'}
(P/'artifact_inventory.json').write_text(json.dumps(inventory,indent=2)+'\n');print(json.dumps(dict(checks=len(checks),previous_phases=len(counts),inventory=len(inventory),native_initializations=0)))
