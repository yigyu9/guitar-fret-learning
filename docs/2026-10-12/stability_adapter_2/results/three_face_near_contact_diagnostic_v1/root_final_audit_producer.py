import ast,hashlib,json,shutil,subprocess
from pathlib import Path
R=Path('/home/ajou/yigyu/3');B=R/'docs/2026-10-12/stability_adapter_2/results';P=B/'three_face_near_contact_diagnostic_v1';phases=[B/'three_face_wider_hand_initial_v1',B/'three_face_support_plane_initial_v1',P];checks={};seen={}
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 p=Path(p)
 if str(p) not in seen:seen[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
 return seen[str(p)]
def check(n,v):assert v,n;checks[n]=True
def closure(d):return all(sha(p)==h for p,h in d.items())
for phase,source,count,nchecks in [(phases[0],'search_wider_hand_initial.py',12,61),(phases[1],'search_support_plane_initial.py',3,16)]:
 e=read(phase/'search_execution.json');d=read(phase/'proposal.json');pre=read(phase/'root_preflight.json');v=read(phase/'interval_data_verification.json');old=read(phase/'previous_source_preservation.json')
 check(phase.name+'_completed_source_exact_source_log_inputs',e['exit_code']==e['native_calls']==0 and e['input_sha256_before']==e['input_sha256_after'] and closure(e['input_sha256_before']) and sha(R/'stability_adapter_2'/source)==sha(phase/'search_source.py') and sha(phase/'search.log')==e['log_sha256'])
 check(phase.name+'_source_preflight_closure',all(d['checks'].values()) and all(pre['checks'].values()) and closure(d['input_sha256']) and closure(pre['input_sha256']))
 check(phase.name+'_source_counts_and_support_failures_not_native_grip',len(d['rejected'])==count and d['processed_source_candidates']==count and not d['rows'] and d['native_initializations']==d['physics_steps']==0 and not (phase/'native').exists() and all(r['accepted_for_fresh_native'] is False and r['reasons'] for r in d['rejected']))
 check(phase.name+'_all_geometry_and_witness_checks_recorded',len(v['checks'])==nchecks and all(v['checks'].values()) and len(v['measurements'])==count*2 and v['audit_source']==(R/'stability_adapter_2/verify_full_hand_initial_v2.py').read_text())
 check(phase.name+'_previous_source_exact',sha(old['original'])==sha(old['snapshot'])==old['sha256'])
a=read(P/'analysis_v2.json');f=read(P/'native_feature_analysis.json');proposal=read(P/'proposal.json');pre=read(P/'root_native_preflight.json');m=read(P/'artifacts/artifact_manifest.json')
check('native_proposal_preflight_analysis_feature_closures',all(proposal['checks'].values()) and all(pre['checks'].values()) and all(a['checks'].values()) and all(f['checks'].values()) and all(closure(x['input_sha256']) for x in (proposal,pre,a,f)))
check('source_failure_retained_under_native_diagnostic_policy',proposal['source_search_constraints_relaxed'] is False and len(proposal['rows'])==2 and all(r['source_support_search_passed'] is False and r['accepted_for_fresh_native'] is False and r['source_support_search_reasons'] and r['admitted_for_native_near_contact_diagnostic'] for r in proposal['rows']))
check('source_snapshot_provenance_exact_payload',read(P/'completed_source_row_snapshot.json')==read(phases[1]/'proposal.json')['rejected'][0])
old=read(P/'previous_runner_preservation.json');check('prior_consumed_native_runner_preserved',sha(old['original'])==sha(old['snapshot'])==old['sha256'])
for label in ('original_targets','initial_finger_targets'):
 e=read(P/f'{label}_native_execution.json');r=read(P/'native'/label/'report.json');audit=read(P/'native'/label/'initial_grip_audit.json')
 check(label+'_execution_closure_exit_zero',e['exit_code']==0 and e['input_sha256_before']==e['input_sha256_after'] and closure(e['input_sha256_before']) and sha(P/f'{label}_native.log')==e['log_sha256'])
 check(label+'_actual5s_1200steps_151frames_source_FK',r['completed'] and r['physics_steps']==1200 and r['simulation_elapsed_s']==5 and r['frame_count']==151 and all(r['checks'].values()) and all(audit['checks'].values()) and closure(r['input_sha256']))
 check(label+'_diagnostic_not_adopted_and_constraints_reported',r['diagnostic_only'] and not r['source_support_search_passed'] and not r['stability_success'] and r['palm_up_proxy_passed'] and not r['constraint_violations'])
 check(label+'_actual_two_video_hashes',len(r['videos'])==2 and all(sha(v['path'])==v['sha256'] and v['stream']['nb_read_frames']=='151' and v['stream']['avg_frame_rate']=='30/1' for v in r['videos'].values()))
for label,source in [('analysis_v2','analyze_near_contact_diagnostic_v2.py'),('native_feature','analyze_near_contact_features.py'),('artifact','make_near_contact_artifacts.py')]:
 e=read(P/f'{label}_execution.json');check(label+'_exact_success_source_log_no_physics',e['exit_code']==e['native_calls']==0 and e['source_sha256_before']==e['source_sha256_after']==sha(R/'stability_adapter_2'/source)==sha(P/f'{label}_source.py') and sha(P/f'{label}_execution.log')==e['log_sha256'])
check('failed_v1_analysis_preserved_not_reclassified',read(P/'analysis_execution.json')['exit_code']==1 and not (P/'analysis.json').exists() and all(sha(p)==row['sha256']==sha(row['snapshot']) for p,row in read(P/'analysis_failure_v1/preservation.json')['files'].items()))
check('artifact_all_input_sha_and_three_actual_opened_PNG',len(m['outputs_sha256'])==3 and m['input_sha256_before']==m['input_sha256_after'] and closure(m['input_sha256_before']) and closure(m['outputs_sha256']) and m['native_initializations_by_producer']==m['physics_steps_by_producer']==0)
# Actual reviewed old native observation and physics loop must stay identical.
def node(source,kind):
 tree=ast.parse(source)
 return next(n for n in ast.walk(tree) if (kind=='observe' and isinstance(n,ast.FunctionDef) and n.name=='observe') or (kind=='loop' and isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='step' and isinstance(n.iter,ast.Call) and isinstance(n.iter.func,ast.Name) and n.iter.func.id=='range' and ast.literal_eval(n.iter.args[0])==1200))
new=(R/'stability_adapter_2/run_near_contact_diagnostic.py').read_text();oldtext=Path(old['snapshot']).read_text()
check('native_observe_and_actual1200_loop_AST_unchanged',all(ast.dump(node(new,k),include_attributes=False)==ast.dump(node(oldtext,k),include_attributes=False) for k in ('observe','loop')))
check('requested_palm_patch_not_observed_and_success_not_claimed',all(row['by_body']['LH:palm']['positive_requested_patch_rows']==0 for row in f['summary']) and all(r['stability_success'] is False for r in a['summary']))
check('two_source_batches_15_and_native2_2400_counts',a['counts']=={'native_initializations':2,'physics_steps':2400} and len(f['rows'])==6715)
# Read the authoritative preceding list without executing previous audit producers.
tree=ast.parse(Path('/tmp/audit_near_rear_phase.py').read_text());prior=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='prior' for t in n.targets)))+['three_face_rear_facet_catalog_v1','three_face_near_rear_anchor_v1','three_face_front_finger_initial_v1','three_face_front_sliding_v1'];counts={}
for name in prior:
 inv=read(B/name/'artifact_inventory.json');check(name+'_frozen_inventory',all(Path(p).stat().st_size==row['size'] and sha(p)==row['sha256'] for p,row in inv.items()));counts[name]=len(inv)
legacy=B/'palm_neck_side_v1/preservation_reference';s=read(legacy/'protected_original_stat.json');aug=read(legacy/'aug19_sha256.json');check('legacy87_stat_preserved',len(s)==87 and all([Path(p).stat().st_size,Path(p).stat().st_mtime_ns]==row for p,row in s.items()));check('Aug19_49_SHA_preserved',len(aug)==49 and closure(aug))
report=R/'docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md';oldvisual=read(B/'three_face_front_sliding_v1/source_final_manifest.json')[str(report)];check('VIS_1_to_87_prefix_preserved',report.read_bytes().startswith(Path(oldvisual['snapshot']).read_bytes()))
for phase in phases:
 status=read(phase/'review_status.json');check(phase.name+'_independent_review_not_claimed',status['independent_source_and_final_review_completed'] is False and not (phase/'review.md').exists())
source_names=['search_wider_hand_initial.py','search_support_plane_initial.py','verify_full_hand_initial.py','diagnose_full_hand_intervals.py','verify_full_hand_initial_v2.py','run_near_contact_diagnostic.py','near_contact_initial_audit.py','source_patch_interval.py','prepare_near_contact_diagnostic.py','analyze_near_contact_diagnostic.py','analyze_near_contact_diagnostic_v2.py','analyze_near_contact_features.py','make_near_contact_artifacts.py'];sources=[R/'stability_adapter_2'/n for n in source_names]
cmd=['/home/ajou/miniconda3/envs/rl38/bin/python','-c','import sys; [compile(open(p).read(),p,"exec") for p in sys.argv[1:]]']+list(map(str,sources));check('Python38_13_sources_syntax',subprocess.call(cmd)==0)
# Review documentation links/line numbers are real; binaries have no synthetic line number.
for phase in phases:
 for filename in ('README.md','CHANGED_FILES.md','review_status.json'):check(phase.name+'_'+filename+'_exists',bool((phase/filename).read_text()))
plans=['THREE_FACE_WIDER_HAND_INITIAL_PLAN.md','THREE_FACE_WIDER_HAND_EXECUTION.md','THREE_FACE_SUPPORT_PLANE_INITIAL_PLAN.md','NEAR_CONTACT_NATIVE_DIAGNOSTIC_PLAN.md','NEAR_CONTACT_RESULT_ANALYSIS_PLAN.md','NEAR_CONTACT_ANALYSIS_RETRY_PLAN.md','PALM_PATCH_PRIORITY_INITIAL_PLAN.md','PLAN.md','README.md','AGENTS.md','EXPERIMENT_WORKFLOW.md']
frozen=sources+[R/'stability_adapter_2'/n for n in plans]+[report]+[phase/n for phase in phases for n in ('README.md','CHANGED_FILES.md','review_status.json')];assert not (P/'source_final').exists();manifest={}
for path in frozen:
 dest=P/'source_final'/path.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest);assert sha(path)==sha(dest);manifest[str(path)]={'snapshot':str(dest),'sha256':sha(path)}
(P/'source_final_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');shutil.copyfile(__file__,P/'root_final_audit_producer.py')
result=dict(checks=checks,counts=dict(previous_inventories=counts,new_source_candidates=15,source_support_accepted=0,new_native_initializations=2,new_physics_steps=2400,source_distance_witnesses=30,native_feature_rows=6715,PNG=3,videos=4,source_final_files=len(frozen)),input_sha256=seen,syntax_command=cmd,audit_source=Path(__file__).read_text(),independent_source_and_final_review_completed=False,independent_review_reason='agent thread limit reached',scope='root source/raw5s/control/camera/feature/preservation audit and actual PNG QA; source support still unmet; no successful grip, initial restore, playing, anatomical pad or cooked penetration certification; goal remains active')
(P/'final_verification.json').write_text(json.dumps(result,indent=2)+'\n')
for phase in phases:
 inventory=phase/'artifact_inventory.json';assert not inventory.exists();mapping={str(p):{'size':p.stat().st_size,'sha256':sha(p)} for p in sorted(phase.rglob('*')) if p.is_file()};inventory.write_text(json.dumps(mapping,indent=2)+'\n');print(phase.name,'inventory',len(mapping))
print('root_checks',len(checks),'previous27preserved;source15rejected;native2x5s;independentreviewpending;goalactive')
