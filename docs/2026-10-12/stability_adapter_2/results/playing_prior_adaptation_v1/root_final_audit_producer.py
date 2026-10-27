from pathlib import Path
import ast, hashlib, json, re, shutil
R=Path('/home/ajou/yigyu/3'); A=R/'stability_adapter_2'; D=R/'docs/2026-10-12/stability_adapter_2'; B=D/'results'; P=B/'playing_prior_adaptation_v1'; PREV=B/'body9_strap_minus2mm_v1'
checks={}; cache={}
def read(p): return json.loads(p.read_text())
def sha(p):
 p=Path(p)
 if str(p) not in cache:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for block in iter(lambda:f.read(1048576),b''):h.update(block)
  cache[str(p)]=h.hexdigest()
 return cache[str(p)]
def check(k,v):
 if not v:raise AssertionError(k)
 checks[k]=True
report=read(P/'contract_audit.json')
check('metadata_only_four_checks_pass',all(report['checks'].values()) and len(report['checks'])==4 and all(report[k]==0 for k in ['native_initializations','physics_steps','training_updates','model_inference_calls']))
check('inputs_SHA_before_after_unchanged',report['input_sha256_before']==report['input_sha256_after'] and all(sha(p)==h for p,h in report['input_sha256_before'].items()))
check('examples_not_selected_and_stages_explicit',all(not row['selected_for_playing'] for row in report['examples']) and [row['training_stage'] for row in report['examples']]==['goal_pair','S3_SONG_INTEGRATION'])
check('extra_six_Thorax_names',len(report['extra_main_control_names'])==6 and all('Thorax' in n for n in report['extra_main_control_names']))
ast.parse((A/'audit_playing_prior_contracts.py').read_text(),feature_version=(3,8))
check('new_producer_python38_syntax',True)
counts=read(PREV/'final_verification.json')['counts']['previous_inventories'].copy();counts[PREV.name]=len(read(PREV/'artifact_inventory.json'))
for name,expected in counts.items():
 inventory=read(B/name/'artifact_inventory.json')
 check('preserved_inventory_'+name,len(inventory)==expected and all(Path(p).is_file() and Path(p).stat().st_size==v['size'] and sha(p)==v['sha256'] for p,v in inventory.items()))
protected=read(B/'palm_neck_side_v1/preservation_reference/protected_original_stat.json')
check('legacy87_stat_preserved',len(protected)==87 and all([Path(p).stat().st_size,Path(p).stat().st_mtime_ns]==v for p,v in protected.items()))
aug=read(B/'palm_neck_side_v1/preservation_reference/aug19_sha256.json')
check('aug19_49_SHA_preserved',len(aug)==49 and all(sha(p)==h for p,h in aug.items()))
oldmanifest=read(PREV/'source_final_manifest.json')
for p in [A/'README.md',A/'PLAN.md',D/'VISUAL_REPORT.md']:
 old=Path(oldmanifest[str(p)]['snapshot']).read_bytes()
 check('old_prefix_'+p.name,p.read_bytes().startswith(old) and sha(oldmanifest[str(p)]['snapshot'])==oldmanifest[str(p)]['sha256'])
check('video_collection_124_unchanged',len(list((D/'videos').glob('*.mp4')))==124)
changed=read(P/'contract_audit.json')['input_sha256_before']
for p in [A/'PLAYING_PRIOR_ADAPTATION_PLAN.md',P/'README.md',P/'review.md',P/'CHANGED_FILES.md']:
 for path,lineno in re.findall(r'\]\((/[^)]+?)(?::(\d+))?\)',p.read_text()):
  link=Path(path)
  if link.name=='final_verification.json' and link.parent==P:continue
  check('link_'+str(p.name)+'_'+str(len(checks)),link.exists() and (not lineno or len(link.read_text().splitlines())>=int(lineno)))
check('index_actual_heading_lines',all(text in path.read_text().splitlines()[line-1] for path,line,text in [(A/'README.md',959,'## 자유 기타에서'),(A/'PLAN.md',1735,'## 자유 기타에서'),(D/'VISUAL_REPORT.md',1801,'## 96.'),(A/'PLAYING_PRIOR_ADAPTATION_PLAN.md',60,'## 제어권'),(A/'PLAYING_PRIOR_ADAPTATION_PLAN.md',102,'## 학습 구조'),(A/'audit_playing_prior_contracts.py',37,'def main')]))
shutil.copy2(__file__,P/'root_final_audit_producer.py')
files=[A/'PLAYING_PRIOR_ADAPTATION_PLAN.md',A/'audit_playing_prior_contracts.py',A/'README.md',A/'PLAN.md',D/'VISUAL_REPORT.md',P/'README.md',P/'CHANGED_FILES.md',P/'review.md']
manifest={}
for p in files:
 dest=P/'source_final'/p.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
 manifest[str(p)]={'snapshot':str(dest),'sha256':sha(p)}
(P/'source_final_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(P/'final_verification.json').write_text(json.dumps({'checks':checks,'counts':{'checks':len(checks),'previous_inventories':counts,'native_initializations':0,'physics_steps':0,'training_updates':0},'review':'root self-review only; independent reviewer thread limit','source_snapshot_manifest_sha256':sha(P/'source_final_manifest.json')},ensure_ascii=False,indent=2)+'\n')
inventory={str(p):{'size':p.stat().st_size,'sha256':sha(p)} for p in sorted(P.rglob('*')) if p.is_file() and p.name!='artifact_inventory.json'}
(P/'artifact_inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'protected_previous_phases':len(counts),'inventory':len(inventory),'native':0,'training':0}))
