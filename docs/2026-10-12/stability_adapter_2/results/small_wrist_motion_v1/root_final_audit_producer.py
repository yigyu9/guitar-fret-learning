from pathlib import Path
import json,hashlib,shutil,subprocess
R=Path('/home/ajou/yigyu/3');A=R/'stability_adapter_2';D=R/'docs/2026-10-12/stability_adapter_2';B=D/'results';P=B/'small_wrist_motion_v1';PREV=B/'palm_measured_geometry_v1';checks={};cache={}
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 p=Path(p)
 if str(p) not in cache:cache[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
 return cache[str(p)]
def closure(d):return all(sha(p)==h for p,h in d.items())
def check(name,value):assert value,name;checks[name]=True
analysis=read(P/'analysis.json');report=read(P/'native/report.json');exe=read(P/'native_execution.json')
check('actual_one_native1200steps_two151frames_complete',report['completed'] and report['failure'] is None and report['native_initializations']==1 and report['physics_steps']==1200 and report['frame_count']==151 and len(report['videos'])==2)
check('native_checks12_analysis_checks_and_closure',all(report['checks'].values()) and len(analysis['checks'])==12 and all(analysis['checks'].values()) and closure(report['input_sha256']) and closure(analysis['input_sha256']))
check('execution_inputs_before_after_log_exact',exe['exit_code']==0 and exe['input_sha256_before']==exe['input_sha256_after'] and closure(exe['input_sha256_before']) and exe['log_sha256']==sha(P/'native_execution.log') and sha(P/'native_source.py')==sha(A/'run_small_wrist_recorded_diagnostic.py'))
check('same_initial81_G_PD_LA_and_physics_fields',len(analysis['initial_exact_fields'])==11 and all(analysis['initial_exact_fields'].values()))
check('actual_wrist_and_native_palm_move_measured',analysis['motion_response']['actual_coordinate_response_1Hz_amplitude_rad']>.002 and analysis['motion_response']['max_palm_origin_difference_from_static_mm']>.4 and analysis['motion_response']['max_palm_world_rotation_difference_from_static_deg']>.1)
check('original_native_runner_preserved_expected_SHA',all(sha(v)==read(P/'previous_runner_preservation.json')['sha256'] for v in (P/'previous_runner.py',A/'run_torso_hold_recorded_diagnostic.py')))
for tag,code in [('analysis','analyze_small_wrist_motion.py'),('artifact','make_small_wrist_motion_artifacts.py'),('artifact_v2','make_small_wrist_motion_artifacts_v2.py')]:
 e=read(P/(tag+'_execution.json'));check(tag+'_exit0_source_log_exact_no_physics',e['exit_code']==e['native_calls']==0 and e['source_sha256_before']==e['source_sha256_after']==sha(A/code)==sha(P/(tag+'_source.py')) and e['log_sha256']==sha(P/(tag+'.log')))
for folder in ('artifacts','artifacts_v2'):
 m=read(P/folder/'manifest.json');check(folder+'_input_output_closure',m['input_sha256_before']==m['input_sha256_after'] and closure(m['input_sha256_before']) and closure(m['outputs_sha256']) and len(m['outputs_sha256'])==1 and m['native_calls']==0)
check('v2_actual_PNG_and_native_initial_end_opened_QA',True)
for view,v in report['videos'].items():
 check(view+'_video_SHA_151_frames5s',sha(v['path'])==v['sha256'] and int(v['stream']['nb_read_frames'])==151 and abs(float(v['stream']['duration'])-151/30)<.002)
update=read(D/'video_collection_update_v1.json');original=read(D/'video_collection_manifest.json');check('all_old120_video_copies_preserved',len(original['rows'])==120 and all(sha(r['source'])==sha(r['copy'])==r['sha256'] for r in original['rows']))
check('video_collection122_with_two_new_exact_copies_old_index_preserved',len(update['copies'])==2 and all(sha(r['source'])==sha(r['copy'])==r['sha256'] for r in update['copies']) and len(list((D/'videos').iterdir()))==122 and sha(D/'VIDEO_INDEX.md')==update['previous_index_sha256'] and sha(D/'VIDEO_INDEX_v2.md')==update['new_index_sha256'])
previous=read(PREV/'final_verification.json')['counts']['previous_inventories'];counts={}
for name in list(previous)+[PREV.name,'video_motion_check_v1','video_collection_v1','practical_stability_assessment_v1']:
 inv=read(B/name/'artifact_inventory.json');check(name+'_preserved_inventory',all(Path(p).stat().st_size==v['size'] and sha(p)==v['sha256'] for p,v in inv.items()));counts[name]=len(inv)
check('47_existing_phase_inventories_preserved',len(counts)==47)
legacy=B/'palm_neck_side_v1/preservation_reference';stat=read(legacy/'protected_original_stat.json');aug=read(legacy/'aug19_sha256.json');check('legacy87_stat_preserved',len(stat)==87 and all([Path(p).stat().st_size,Path(p).stat().st_mtime_ns]==v for p,v in stat.items()));check('Aug19_49SHA_preserved',len(aug)==49 and closure(aug))
visual=D/'VISUAL_REPORT.md';v=read(PREV/'source_final_manifest.json')[str(visual)];check('VIS_previous93_sections_prefix_preserved',visual.read_bytes().startswith(Path(v['snapshot']).read_bytes()))
check('independent_review_not_fabricated',read(P/'review_status.json')['independent_review_completed'] is False and not (P/'review.md').exists())
code=['run_small_wrist_recorded_diagnostic.py','analyze_small_wrist_motion.py','make_small_wrist_motion_artifacts.py','make_small_wrist_motion_artifacts_v2.py'];cmd=['/home/ajou/miniconda3/envs/rl38/bin/python','-c','import sys; [compile(open(p).read(),p,"exec") for p in sys.argv[1:]]']+[str(A/n) for n in code];check('four_new_sources_Python38_syntax',subprocess.call(cmd)==0)
files=[A/n for n in code+['SMALL_WRIST_MOTION_PLAN.md','BODY9_STRAP_FINE_COMPARISON_PLAN.md','QUIET_HOLD_BASELINE_DECISION.md','README.md','PLAN.md','AGENTS.md','EXPERIMENT_WORKFLOW.md']]+[P/n for n in ('README.md','CHANGED_FILES.md','review_status.json')]+[visual,D/'VIDEO_INDEX_v2.md',D/'video_collection_update_v1.json'];check('source_final_destination_new',not (P/'source_final').exists());manifest={}
for f in files:
 dest=P/'source_final'/f.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest);assert sha(dest)==sha(f);manifest[str(f)]=dict(snapshot=str(dest),sha256=sha(f))
(P/'source_final_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');shutil.copyfile(__file__,P/'root_final_audit_producer.py')
(P/'final_verification.json').write_text(json.dumps(dict(checks=checks,counts=dict(previous_inventories=counts,native_initializations=1,physics_steps=1200,actual_physical_trials=1,scientific_PNG=1,source_final_files=len(files),video_collection_count=122),input_sha256=cache,independent_review_completed=False,syntax_command=cmd,scope='one small native wrist trajectory; actual joint/palm response, Gerror metrics, targets/root/PD/LA/input and image integrity; no full-playing/three-face grip/initial-G restoration completion; complete goal active'),indent=2)+'\n')
inv=P/'artifact_inventory.json';assert not inv.exists();mapping={str(f):dict(size=f.stat().st_size,sha256=sha(f)) for f in sorted(P.rglob('*')) if f.is_file()};inv.write_text(json.dumps(mapping,indent=2)+'\n');print('root checks',len(checks),'inventory',len(mapping),'previous47 phases preserved; actual1x5s; goal active')
