from pathlib import Path
import ast,hashlib,json,re,shutil
R=Path('/home/ajou/yigyu/3');A=R/'stability_adapter_2';D=R/'docs/2026-10-12/stability_adapter_2';B=D/'results';P=B/'natural_envelope_assessment_v1';AR=P/'artifacts';checks={};cache={}
def read(f):return json.loads(Path(f).read_text())
def sha(f):
 f=Path(f)
 if str(f) not in cache:
  h=hashlib.sha256()
  with f.open('rb') as s:
   for block in iter(lambda:s.read(1048576),b''):h.update(block)
  cache[str(f)]=h.hexdigest()
 return cache[str(f)]
def check(k,v):
 assert v,k
 checks[k]=True
def closure(m):return all(sha(f)==h for f,h in m.items())
assert not (P/'final_verification.json').exists() and not (P/'artifact_inventory.json').exists()
a=read(P/'analysis.json');e=read(P/'analysis_execution.json');s=read(P/'source_before_manifest.json')
check('analysis26_and19inputs',len(a['checks'])==26 and all(a['checks'].values()) and len(a['input_sha256_before'])==19 and a['input_sha256_before']==a['input_sha256_after'] and closure(a['input_sha256_before']))
check('analysis_execution0_source4_log_outputs_exact',e['exit_code']==0 and len(s)==4 and e['source_sha256_before']==e['source_sha256_after'] and closure(e['source_sha256_before']) and sha(P/'analysis.log')==e['log_sha256'] and closure(e['outputs_sha256']) and all(sha(f)==sha(v['snapshot'])==v['sha256'] for f,v in s.items()))
check('four_runs_and_full_records',len(a['runs'])==4 and len((P/'windows.jsonl').read_text().splitlines())==484 and len((P/'timeline.jsonl').read_text().splitlines())==4804 and all(x['observed_samples']==1201 and x['window_count']==121 for x in a['runs']))
check('provisional_not_certified_no_physics',a['naturalness_or_playing_success_certified'] is False and all(a[k]==0 for k in ['native_initializations','physics_steps','actor_inference_calls','training_updates']))
am=read(AR/'artifact_manifest.json');ae=read(AR/'producer_execution.json');ss=read(AR/'source_snapshot.json')
check('artifact26inputs_preserved',len(am['inputs_sha256_before'])==26 and am['inputs_sha256_before']==am['inputs_sha256_after'] and closure(am['inputs_sha256_before']))
check('artifact26_copies_producer_wrapper_exact',len(ss['files'])==26 and all(sha(v['original_path'])==sha(v['copy_path'])==v['sha256'] for v in ss['files']) and am['producer_sha256_before']==am['producer_sha256_after']==sha(A/'make_natural_envelope_artifacts.py') and sha(AR/'run_producer.sh')==sha(AR/'run_producer.sh.archived'))
check('artifact_execution0_output_exact',ae['exit_code']==0 and all(sha(AR/f)==h for f,h in am['outputs_sha256'].items()) and all(am[k]==0 for k in ['native_initializations','physics_steps','actor_inference_calls','training_updates']))
for name in ['analyze_natural_envelope.py','make_natural_envelope_artifacts.py']:
 ast.parse((A/name).read_text(),feature_version=(3,8));check('syntax38_'+name,True)
for name,count in [('natural_pose_criteria_v1',15),('finger_contact_map_v1',72)]:
 inv=read(B/name/'artifact_inventory.json');check('preserved_'+name,len(inv)==count and all(Path(f).stat().st_size==v['size'] and sha(f)==v['sha256'] for f,v in inv.items()))
before=read(P/'journal_before.json')
for f,v in before.items():check('append_only_'+Path(f).name,hashlib.sha256(Path(f).read_bytes()[:v['size']]).hexdigest()==v['sha256'])
for f in P.glob('*.md'):
 for target,line in re.findall(r'\]\(<?(/[^)>]+?)(?::(\d+))?>?\)',f.read_text()):
  q=Path(target);check('link_'+str(len(checks)),q.exists() and (not line or len(q.read_text().splitlines())>=int(line)))
check('review_present',(P/'review.md').is_file())
manifest={}
paths=[A/n for n in ['analyze_natural_envelope.py','make_natural_envelope_artifacts.py','NATURAL_ENVELOPE_ASSESSMENT_PLAN.md','NATURAL_ENVELOPE_ASSESSMENT_DECISION.md','NATURAL_PLAYING_ENVELOPE.md','README.md','PLAN.md']]+[D/'VISUAL_REPORT.md']+list(P.glob('*.md'))
for f in paths:
 dst=P/'source_final'/f.relative_to(R);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dst);manifest[str(f)]={'snapshot':str(dst),'sha256':sha(f)}
(P/'source_final_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(P/'final_verification.json').write_text(json.dumps(dict(checks=checks,counts=dict(checks=len(checks),protected_previous_files=87,physics_steps=0,native_initializations=0),artifact_log_sha256=sha(AR/'producer.log'),source_final_manifest_sha256=sha(P/'source_final_manifest.json'),scope='saved four-run pose evaluation; provisional initial envelope and121 complete1s windows/run; no new native/control/reward/actor/training or naturalness/playing certification'),indent=2)+'\n')
inv={str(f):dict(size=f.stat().st_size,sha256=sha(f)) for f in sorted(P.rglob('*')) if f.is_file() and f.name!='artifact_inventory.json'}
(P/'artifact_inventory.json').write_text(json.dumps(inv,indent=2)+'\n');print(json.dumps(dict(checks=len(checks),inventory=len(inv),protected_previous_files=87,native_initializations=0)))
