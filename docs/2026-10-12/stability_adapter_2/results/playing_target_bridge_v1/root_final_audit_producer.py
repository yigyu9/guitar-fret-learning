from pathlib import Path
import ast,hashlib,json,re,shutil
R=Path('/home/ajou/yigyu/3');A=R/'stability_adapter_2';D=R/'docs/2026-10-12/stability_adapter_2';B=D/'results';P=B/'playing_target_bridge_v1';PREV=B/'coupled_palm_witness_v1'
checks={};cache={}
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
c=read(P/'contract.json');e=read(P/'execution.json');ar=P/'artifacts';m=read(ar/'artifact_manifest.json');ae=read(ar/'producer_execution.json')
check('CPU10_checks_30inputs_SHA',len(c['checks'])==10 and all(c['checks'].values()) and len(c['input_sha256_before'])==30 and c['input_sha256_before']==c['input_sha256_after'] and closure(c['input_sha256_before']))
check('CPU_execution0_source_copies_log_SHA',e['exit_code']==0 and e['source_sha256_before']==e['source_sha256_after'] and all(sha(A/p)==sha(P/p)==h for p,h in e['source_sha256_before'].items()) and sha(P/'execution.log')==e['log_sha256'])
counters=['native_initializations','physics_steps','actor_inference_calls','training_updates']
check('CPU_native_physics_actor_training0',all(c[k]==e[k]==0 for k in counters))
check('rounding_difference_not_bitwise_equivalence',c['original_Base_AST_max_target_difference_rad']==2.384185791015625e-7 and c['final_history_decode_max_error_rad']==1.1920928955078125e-7)
check('source60_main66_held15_nine_rejections',len(c['native_names'])==81 and len(c['main_names'])==66 and len(c['held_native_indices'])==15 and sum(len(v['names']) for v in c['source_mapping'].values())==60 and len(c['rejected_cases'])==9)
check('all_four_strictG0_unqualified',len(c['sources'])==4 and all(not s['strict_G0_qualification']['qualified_for_g0'] for s in c['sources']))
qm=c['actual_initial_q_profile_mismatches'];tm=c['actual_baseline_profile_mismatches']
check('six_hand_q_and_PD_profile_mismatches',len(qm)==len(tm)==6 and {r['name'] for r in qm}=={r['name'] for r in tm} and max(r['required_min_target_change_rad'] for r in qm)==.6612687706947327 and max(r['required_min_target_change_rad'] for r in tm)==.6176479458808899)
check('artifact_inputs_outputs_exact',m['inputs_sha256_before']==m['inputs_sha256_after'] and closure(m['inputs_sha256_before']) and all(sha(ar/p)==h for p,h in m['outputs_sha256'].items()))
check('artifact_execution_source_SHA_log0',ae['exit_code']==0 and m['producer_sha256']==ae['source_sha256_before']==ae['source_sha256_after']==sha(A/'make_playing_bridge_artifacts.py') and ae['log_sha256']==sha(ar/'producer.log') and all(ae[k]==0 for k in counters) and all(m[k]==0 for k in ['native_calls','physics_steps','actor_inference_calls','training_updates']))
ss=read(ar/'source_snapshot.json')
check('pre_generation_source_copies_exact',len(ss['files'])==5 and all(sha(r['original_path'])==sha(ar/r['copy_path'])==r['sha256'] for r in ss['files']) and ae['source_snapshot_sha256']==sha(ar/'source_snapshot.json'))
counts=read(PREV/'final_verification.json')['counts']['previous_inventories'].copy();counts[PREV.name]=len(read(PREV/'artifact_inventory.json'))
for name,expected in counts.items():
 inv=read(B/name/'artifact_inventory.json');check('preserved_phase_'+name,len(inv)==expected and all(Path(p).stat().st_size==v['size'] and sha(p)==v['sha256'] for p,v in inv.items()))
protected=read(B/'palm_neck_side_v1/preservation_reference/protected_original_stat.json');check('legacy87_stat_exact',len(protected)==87 and all([Path(p).stat().st_size,Path(p).stat().st_mtime_ns]==v for p,v in protected.items()))
aug=read(B/'palm_neck_side_v1/preservation_reference/aug19_sha256.json');check('aug19_49SHA_exact',len(aug)==49 and closure(aug))
before=read(P/'journal_before.json')
for p in [A/'README.md',A/'PLAN.md',D/'VISUAL_REPORT.md']:
 check('append_only_'+p.name,hashlib.sha256(p.read_bytes()[:before[str(p)]['size']]).hexdigest()==before[str(p)]['sha256'])
check('learning_plan_consumed_unchanged',sha(A/'PLAYING_RESIDUAL_EVALUATION.md')=='d3738dca9a7f701cf4e7221d2eb85ee01cfebfbba63fa48813eb68d615f2149b')
videos=list((D/'videos').glob('*.mp4'))
check('128_video_copies_all_exact_no_new_videos',len(videos)==128 and all(sha(v)==sha(B/Path(v.name.replace('__','/'))) for v in videos))
pm=read(PREV/'source_final_manifest.json')
for p in [D/'VIDEO_INDEX_v5.md',D/'video_collection_update_v4.json']:check('unchanged_'+p.name,sha(p)==pm[str(p)]['sha256'])
sources=['playing_target_bridge.py','check_playing_target_bridge.py','make_playing_bridge_artifacts.py']
for s in sources:ast.parse((A/s).read_text(),feature_version=(3,8));check(s+'_python38_syntax',True)
check('independent_review_recorded',(P/'review.md').is_file())
check('actual_PNG_QA_recorded','이미지 QA' in (P/'ROOT_VERIFICATION_NOTES.md').read_text())
for p in list(P.glob('*.md'))+[A/'PLAYING_TARGET_BRIDGE_DECISION.md',A/'SOURCE_PROFILE_INITIAL_POSE_PLAN.md']:
 for target,line in re.findall(r'\]\(<?(/[^)>]+?)(?::(\d+))?>?\)',p.read_text()):
  q=Path(target)
  if q.name=='final_verification.json' and q.parent==P:continue
  check('link_'+str(len(checks)),q.exists() and (not line or len(q.read_text().splitlines())>=int(line)))
shutil.copy2(__file__,P/'root_final_audit_producer.py')
files=[A/s for s in sources]+[A/s for s in ['PLAYING_TARGET_BRIDGE_PLAN.md','PLAYING_TARGET_BRIDGE_DECISION.md','SOURCE_PROFILE_INITIAL_POSE_PLAN.md','README.md','PLAN.md']]+[D/'VISUAL_REPORT.md']+list(P.glob('*.md'))
manifest={}
for p in files:
 dest=P/'source_final'/p.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);manifest[str(p)]={'snapshot':str(dest),'sha256':sha(p)}
(P/'source_final_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(P/'final_verification.json').write_text(json.dumps({'checks':checks,'counts':{'checks':len(checks),'previous_inventories':counts,**{k:0 for k in counters}},'source_snapshot_manifest_sha256':sha(P/'source_final_manifest.json')},ensure_ascii=False,indent=2)+'\n')
inventory={str(p):{'size':p.stat().st_size,'sha256':sha(p)} for p in sorted(P.rglob('*')) if p.is_file() and p.name!='artifact_inventory.json'}
(P/'artifact_inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'protected_previous_phases':len(counts),'inventory':len(inventory),**{k:0 for k in counters}}))
