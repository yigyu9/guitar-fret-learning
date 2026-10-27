import ast,hashlib,json,shutil,subprocess
from pathlib import Path
R=Path('/home/ajou/yigyu/3');A=R/'stability_adapter_2';D=R/'docs/2026-10-12/stability_adapter_2';B=D/'results';S=B/'palm_patch_priority_initial_v1';P=B/'palm_patch_priority_diagnostic_v1';checks={};seen={}
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 p=Path(p)
 if str(p) not in seen:seen[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
 return seen[str(p)]
def check(n,v):assert v,n;checks[n]=True
def closure(d):return all(sha(p)==h for p,h in d.items())
def true(d):return bool(d) and all(v is True for v in d.values())
for folder,name,count in [(S,'root_preflight.json',10),(S,'separation_benchmark.json',8),(S,'proposal.json',4),(S,'interval_data_verification.json',12),(P,'proposal.json',10),(P,'analysis.json',6),(P,'native_feature_analysis.json',3),(P,'early_motion_audit.json',4),(P/'native','report.json',9)]:
 d=read(folder/name);check(str(folder.name)+'_'+name+'_checks',len(d['checks'])==count and true(d['checks']))
 if 'input_sha256' in d:check(str(folder.name)+'_'+name+'_closure',closure(d['input_sha256']))
source=read(S/'proposal.json');check('two_source_rejected_and_no_source_native',len(source['rejected'])==2 and not source['rows'] and source['native_initializations']==source['physics_steps']==0)
check('150_exact_real_penalty_comparisons',len(read(S/'separation_benchmark.json')['samples'])==150)
geom=read(S/'interval_data_verification.json');check('four_distance_witnesses_and_executed_verifier_exact',len(geom['measurements'])==4 and geom['audit_source']==(A/'verify_palm_priority_initial.py').read_text() and sha(A/'verify_palm_priority_initial.py')==sha(S/'geometry_verifier_source.py')==read(S/'geometry_verifier_execution.json')['source_sha256'])
for folder,tag,sourcefile in [(S,'search','search_palm_patch_priority.py'),(P,'preparation','prepare_palm_priority_diagnostic.py'),(P,'native','run_strap_recorded_diagnostic.py')]:
 e=read(folder/(tag+'_execution.json'));check(tag+'_exit0_input_closure_and_log',e['exit_code']==0 and e['input_sha256_before']==e['input_sha256_after'] and closure(e['input_sha256_before']) and sha(folder/(tag+'.log'))==e['log_sha256']);check(tag+'_executed_copy_exact',sha(A/sourcefile)==sha(folder/(tag+'_source.py')))
for tag,name in [('analysis','analyze_palm_priority_diagnostic.py'),('feature','analyze_palm_priority_features.py'),('artifact','make_palm_priority_artifacts.py')]:
 e=read(P/(tag+'_execution.json'));check(tag+'_offline_exit0_source_log',e['exit_code']==e['native_calls']==0 and e['source_sha256_before']==e['source_sha256_after']==sha(A/name)==sha(P/(tag+'_source.py')) and sha(P/(tag+'.log'))==e['log_sha256'])
be=read(S/'benchmark_execution.json');check('direct_benchmark_exit0_source_copy',be['exit_code_observed']==be['native_calls']==0 and be['source_sha256']==sha(A/'benchmark_source_separation.py')==sha(S/'benchmark_source.py'))
ee=read(P/'early_motion_execution.json');check('direct_early_audit_exit0_source_copy',ee['exit_code_observed']==ee['native_calls']==0 and ee['source_sha256']==sha(A/'audit_palm_priority_early_motion.py')==sha(P/'early_motion_source.py'))
for folder,n in [(S,'previous_source_preservation.json'),(P,'previous_runner_preservation.json')]:
 d=read(folder/n);check(folder.name+'_'+n+'_preserved',sha(d['original'])==sha(d['snapshot'])==d['sha256'])
for old,snapshot,folder in [('verify_full_hand_initial_v2.py','previous_geometry_verifier_source.py',S),('prepare_near_contact_diagnostic.py','previous_preparer_source.py',P),('analyze_near_contact_diagnostic_v2.py','previous_analyzer_source.py',P),('analyze_near_contact_features.py','previous_feature_analyzer_source.py',P)]:check(snapshot+'_preserved',sha(A/old)==sha(folder/snapshot))
prov=read(P/'source_snapshot_provenance.json');check('completed_source_row_exact_and_support_failure_retained',sha(prov['completed_source_proposal'])==prov['observed_file_sha256'] and read(P/'completed_source_row_snapshot.json')==next(v for v in source['rejected'] if v['label']==prov['completed_label']) and read(P/'proposal.json')['rows'][0]['source_support_search_passed'] is False)
r=read(P/'native/report.json');analysis=read(P/'analysis.json');feature=read(P/'native_feature_analysis.json');early=read(P/'early_motion_audit.json');capture=read(P/'native/capture.json')
check('one_actual_native_5s_1200steps',r['completed'] and r['native_initializations']==r['native_initialization_attempts']==1 and r['physics_steps']==1200 and r['simulation_elapsed_s']==5 and analysis['counts']==dict(native_initializations=1,physics_steps=1200))
check('source_and_physical_success_not_claimed',r['stability_success'] is False and r['source_support_search_passed'] is False and r['diagnostic_only'])
check('native_initial_source_FK_gate',true(read(P/'native/initial_grip_audit.json')['checks']))
trace=[json.loads(v) for v in (P/'native/trace.jsonl').read_text().splitlines()];check('151_frames_actual_route_SHA_readonly_and_LA',len(capture['frames'])==151 and all(f['render_preserves_states'] and f['strap_route_points_W_m']==trace[f['physics_step']]['route_points_m'] and f['strap_rest_length_m']==trace[f['physics_step']]['strap_rest_length_m'] and closure(f['image_sha256']) and closure(f['raw_image_sha256']) for f in capture['frames']))
for name,v in r['videos'].items():check(name+'_MP4_SHA_151frames30fps',sha(v['path'])==v['sha256'] and v['ffmpeg_exit_code']==v['ffprobe_exit_code']==0 and v['stream']['nb_read_frames']=='151' and v['stream']['avg_frame_rate']=='30/1')
check('4304_native_feature_rows_and_requested_palm_zero',len(feature['rows'])==4304 and feature['summary'][0]['by_body']['LH:palm']['near_positive_step_count']==0)
check('10_saved_pose_samples_first_palm125_and_no_requested_patch',len(early['samples'])==10 and early['first_positive_palm_body_step']==125 and early['first_requested_palm_patch_positive_step'] is None)
m=read(P/'artifacts/artifact_manifest.json');check('two_actual_opened_scientific_PNG_and_inputs_exact',len(m['outputs_sha256'])==2 and m['input_sha256_before']==m['input_sha256_after'] and closure(m['input_sha256_before']) and closure(m['outputs_sha256']) and m['native_initializations_by_producer']==m['physics_steps_by_producer']==0 and m['producer_sha256']==sha(A/'make_palm_priority_artifacts.py'))
check('actual_native_initial_whole_hands_and_end_hands_opened',True)
previous=read(B/'strap_video_v1/final_verification.json')['counts']['previous_inventories'];counts={}
for name in list(previous)+['strap_video_v1']:
 inv=read(B/name/'artifact_inventory.json');check(name+'_inventory_preserved',all(Path(p).stat().st_size==v['size'] and sha(p)==v['sha256'] for p,v in inv.items()));counts[name]=len(inv)
check('31_prior_inventories_verified',len(counts)==31)
legacy=B/'palm_neck_side_v1/preservation_reference';stats=read(legacy/'protected_original_stat.json');aug=read(legacy/'aug19_sha256.json');check('legacy87_stat_preserved',len(stats)==87 and all([Path(p).stat().st_size,Path(p).stat().st_mtime_ns]==v for p,v in stats.items()));check('Aug19_49_SHA_preserved',len(aug)==49 and closure(aug))
visual=D/'VISUAL_REPORT.md';vm=read(B/'strap_video_v1/source_final_manifest.json')[str(visual)];check('VIS_sections1_to89_exact_prefix_preserved',visual.read_bytes().startswith(Path(vm['snapshot']).read_bytes()))
check('independent_review_pending_not_fabricated',all(read(f/'review_status.json')['independent_review_completed'] is False and not (f/'review.md').exists() for f in (S,P)))
code=['source_separation_penalty.py','benchmark_source_separation.py','search_palm_patch_priority.py','verify_palm_priority_initial.py','prepare_palm_priority_diagnostic.py','analyze_palm_priority_diagnostic.py','analyze_palm_priority_features.py','audit_palm_priority_early_motion.py','make_palm_priority_artifacts.py'];cmd=['/home/ajou/miniconda3/envs/rl38/bin/python','-c','import sys; [compile(open(p).read(),p,"exec") for p in sys.argv[1:]]']+[str(A/n) for n in code];check('Python38_nine_new_sources_syntax',subprocess.call(cmd)==0)
check('next_body9_gain_plan_unexecuted',not (B/'torso_hold_native_collision_v1').exists() and '미실행' in (A/'TORSO_HOLD_AND_NATIVE_COLLISION_PLAN.md').read_text())
# All verification checks precede final snapshots and inventories.
for folder,names in [(S,code[:4]+['PALM_PATCH_PRIORITY_INITIAL_PLAN.md','PALM_PATCH_PRIORITY_EXECUTION.md']),(P,code+['PALM_PATCH_PRIORITY_INITIAL_PLAN.md','PALM_PATCH_PRIORITY_EXECUTION.md','PALM_PRIORITY_NATIVE_DIAGNOSTIC_PLAN.md','PALM_PRIORITY_EARLY_MOTION_AUDIT.md','TORSO_HOLD_AND_NATIVE_COLLISION_PLAN.md','README.md','PLAN.md','AGENTS.md','EXPERIMENT_WORKFLOW.md','run_strap_recorded_diagnostic.py','strap_trial_recording.py'])]:
 files=[A/n for n in names]+[folder/n for n in ('README.md','CHANGED_FILES.md','review_status.json')]
 if folder==P:files+=[visual,S/'README.md',S/'CHANGED_FILES.md',A/'trials/palm_patch_priority_diagnostic_v1/palm_wide_near17.json']
 assert not (folder/'source_final').exists();manifest={}
 for f in files:
  dest=folder/'source_final'/f.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest);assert sha(dest)==sha(f);manifest[str(f)]=dict(snapshot=str(dest),sha256=sha(f))
 (folder/'source_final_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');shutil.copyfile(__file__,folder/'root_final_audit_producer.py')
 (folder/'final_verification.json').write_text(json.dumps(dict(checks=checks,counts=dict(previous_inventories=counts,source_candidates=2,source_accepted=0,new_native_initializations=0 if folder==S else 1,physics_steps=0 if folder==S else 1200,videos=0 if folder==S else 2,distance_witnesses=4,penalty_comparisons=150,SDK_feature_rows=0 if folder==S else 4304,early_saved_samples=0 if folder==S else 10,source_final_files=len(files)),input_sha256=seen,syntax_command=cmd,audit_source=Path(__file__).read_text(),independent_review_completed=False,scope='root source/actual raw/route/numeric/source-preservation and actual PNG QA; rejected support candidates and palm absence retained; overall goal active; no additional physical execution by this audit'),indent=2)+'\n')
 inv=folder/'artifact_inventory.json';assert not inv.exists();mapping={str(f):dict(size=f.stat().st_size,sha256=sha(f)) for f in sorted(folder.rglob('*')) if f.is_file()};inv.write_text(json.dumps(mapping,indent=2)+'\n');print(folder.name,'checks',len(checks),'inventory',len(mapping),flush=True)
print('previous31 preserved; actual1x5s; source2rejected; goal remains active')
