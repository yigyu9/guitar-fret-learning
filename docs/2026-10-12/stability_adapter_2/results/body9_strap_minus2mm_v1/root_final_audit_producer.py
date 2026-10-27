from pathlib import Path
import json,hashlib,shutil,subprocess
R=Path('/home/ajou/yigyu/3');A=R/'stability_adapter_2';D=R/'docs/2026-10-12/stability_adapter_2';B=D/'results';P=B/'body9_strap_minus2mm_v1';PREV=B/'small_wrist_motion_v1';checks={};cache={}
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 p=Path(p)
 if str(p) not in cache:cache[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
 return cache[str(p)]
def closure(d):return all(sha(p)==h for p,h in d.items())
def check(n,v):assert v,n;checks[n]=True
prep=read(P/'preparation.json');analysis=read(P/'analysis.json');report=read(P/'native/report.json');exe=read(P/'native_execution.json');baseline,candidate=analysis['summary']
check('prepare_four_checks_inputs_exact_no_native',len(prep['checks'])==4 and all(prep['checks'].values()) and closure(prep['input_sha256']) and prep['native_initializations']==prep['physics_steps']==0 and sha(A/'prepare_body9_strap_fine_trial.py')==sha(P/'preparation_source.py'))
check('actual_one_native1200step_two151frames_complete',report['completed'] and report['failure'] is None and report['native_initializations']==1 and report['physics_steps']==1200 and report['frame_count']==151 and len(report['videos'])==2)
check('native_checks_and_ten_analysis_checks_closure',all(report['checks'].values()) and len(analysis['checks'])==10 and all(analysis['checks'].values()) and closure(report['input_sha256']) and closure(analysis['input_sha256']))
check('native_execution_source_inputs_log_exact',exe['exit_code']==0 and exe['input_sha256_before']==exe['input_sha256_after'] and closure(exe['input_sha256_before']) and exe['log_sha256']==sha(P/'native_execution.log') and sha(A/'run_small_wrist_recorded_diagnostic.py')==sha(P/'native_source.py')==sha(PREV/'native_source.py'))
check('same11_initial_fields_and_declared2mm_only_difference',len(analysis['common_initial_exact_fields'])==11 and all(analysis['common_initial_exact_fields'].values()) and candidate['strap']['rest_length_m']==baseline['strap']['rest_length_m']-.002)
check('both_G_max_and_late_pose_range_reduced',all(candidate['guitar'][key]<baseline['guitar'][key] for key in ('max_initial_position_error_mm','max_initial_rotation_error_deg','max_position_change_from_2s_mm','max_rotation_change_from_2s_deg')))
check('actual_motion_retained_and_both_cable_laws_reconstructed',candidate['wrist']['amplitude_deg']>.14 and baseline['wrist']['amplitude_deg']>.14 and all(r['strap']['law_reconstruction_max_error_n']==0 for r in analysis['summary']))
check('peak_T_increase_and_palm_no_contact_not_hidden',candidate['strap']['max_law_tension_n']>baseline['strap']['max_law_tension_n'] and all(r['palm_guitar_positive_raw_lambda_steps']==0 for r in analysis['summary']))
for tag,code in [('analysis','analyze_body9_strap_fine.py'),('artifact','make_body9_strap_fine_artifacts.py')]:
 e=read(P/(tag+'_execution.json'));check(tag+'_exit0_source_log_no_physics',e['exit_code']==e['native_calls']==0 and e['source_sha256_before']==e['source_sha256_after']==sha(A/code)==sha(P/(tag+'_source.py')) and e['log_sha256']==sha(P/(tag+'.log')))
m=read(P/'artifacts/manifest.json');check('artifact_input_output_SHA_exact_and_actual_QA',m['input_sha256_before']==m['input_sha256_after'] and closure(m['input_sha256_before']) and closure(m['outputs_sha256']) and len(m['outputs_sha256'])==1 and m['native_calls']==0)
for view,v in report['videos'].items():check(view+'_video_SHA151_frames5s',sha(v['path'])==v['sha256'] and int(v['stream']['nb_read_frames'])==151 and abs(float(v['stream']['duration'])-151/30)<.002)
oldcap=read(PREV/'native/capture.json');newcap=read(P/'native/capture.json');check('raw_t0_both_camera_RGB_exact_to_original_length',sorted(oldcap['frames'][0]['raw_image_sha256'].values())==sorted(newcap['frames'][0]['raw_image_sha256'].values()))
update=read(D/'video_collection_update_v2.json');check('new_video124_two_exact_copies_old_index_preserved',len(list((D/'videos').iterdir()))==124 and len(update['copies'])==2 and all(sha(r['source'])==sha(r['copy'])==r['sha256'] for r in update['copies']) and sha(D/'VIDEO_INDEX_v2.md')==update['previous_index_sha256'] and sha(D/'VIDEO_INDEX_v3.md')==update['new_index_sha256'])
old=read(D/'video_collection_manifest.json');priorupdate=read(D/'video_collection_update_v1.json');check('previous122_video_copies_preserved',all(sha(r['source'])==sha(r['copy'])==r['sha256'] for r in old['rows']+priorupdate['copies']))
previous=read(PREV/'final_verification.json')['counts']['previous_inventories'];counts={}
for name in list(previous)+[PREV.name]:
 inv=read(B/name/'artifact_inventory.json');check(name+'_inventory_preserved',all(Path(p).stat().st_size==v['size'] and sha(p)==v['sha256'] for p,v in inv.items()));counts[name]=len(inv)
check('48_previous_phase_inventories_preserved',len(counts)==48)
legacy=B/'palm_neck_side_v1/preservation_reference';stat=read(legacy/'protected_original_stat.json');aug=read(legacy/'aug19_sha256.json');check('legacy87_stat_preserved',len(stat)==87 and all([Path(p).stat().st_size,Path(p).stat().st_mtime_ns]==v for p,v in stat.items()));check('Aug19_49SHA_preserved',len(aug)==49 and closure(aug))
visual=D/'VISUAL_REPORT.md';old=read(PREV/'source_final_manifest.json')[str(visual)];check('VIS1_to94_prefix_preserved',visual.read_bytes().startswith(Path(old['snapshot']).read_bytes()))
check('independent_review_not_fabricated',read(P/'review_status.json')['independent_review_completed'] is False and not (P/'review.md').exists())
code=['prepare_body9_strap_fine_trial.py','analyze_body9_strap_fine.py','make_body9_strap_fine_artifacts.py'];cmd=['/home/ajou/miniconda3/envs/rl38/bin/python','-c','import sys; [compile(open(p).read(),p,"exec") for p in sys.argv[1:]]']+[str(A/n) for n in code];check('three_new_sources_Python38_syntax',subprocess.call(cmd)==0)
files=[A/n for n in code+['run_small_wrist_recorded_diagnostic.py','BODY9_STRAP_FINE_COMPARISON_PLAN.md','BODY9_STRAP_MINUS4MM_PLAN.md','README.md','PLAN.md','AGENTS.md','EXPERIMENT_WORKFLOW.md','trials/body9_strap_fine_v1/la_minus2mm.json']]+[P/n for n in ('README.md','CHANGED_FILES.md','review_status.json')]+[visual,D/'VIDEO_INDEX_v3.md',D/'video_collection_update_v2.json'];check('new_source_final_destination',not (P/'source_final').exists());manifest={}
for f in files:
 dest=P/'source_final'/f.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest);assert sha(dest)==sha(f);manifest[str(f)]=dict(snapshot=str(dest),sha256=sha(f))
(P/'source_final_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');shutil.copyfile(__file__,P/'root_final_audit_producer.py');(P/'final_verification.json').write_text(json.dumps(dict(checks=checks,counts=dict(previous_inventories=counts,native_initializations=1,physics_steps=1200,actual_physical_trials=1,source_final_files=len(files),video_collection_count=124),input_sha256=cache,independent_review_completed=False,syntax_command=cmd,scope='one LA-only comparison under same wrist motion; small improvement observed, no full66 playing/threeface palm grip/initialG restoration controller completion; full goal active'),indent=2)+'\n');inv=P/'artifact_inventory.json';assert not inv.exists();mapping={str(f):dict(size=f.stat().st_size,sha256=sha(f)) for f in sorted(P.rglob('*')) if f.is_file()};inv.write_text(json.dumps(mapping,indent=2)+'\n');print('root checks',len(checks),'inventory',len(mapping),'previous48 preserved; actual1x5s; goal active')
