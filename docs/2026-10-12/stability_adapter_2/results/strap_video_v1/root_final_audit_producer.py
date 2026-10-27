import ast,hashlib,json,shutil,subprocess
from pathlib import Path
R=Path('/home/ajou/yigyu/3');B=R/'docs/2026-10-12/stability_adapter_2/results';P=B/'strap_video_v1';checks={};seen={}
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 p=Path(p)
 if str(p) not in seen:seen[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
 return seen[str(p)]
def check(n,v):assert v,n;checks[n]=True
def closure(d):return all(sha(p)==h for p,h in d.items())
e=read(P/'execution.json');pre=read(P/'root_preflight.json');v=read(P/'verification.json');r=read(P/'native/report.json');a=read(P/'native/initial_grip_audit.json');constant=read(P/'constant_runner_preflight.json')
check('root_preflight_projection_depth_and_AST',all(pre['checks'].values()) and closure(pre['input_sha256']))
check('native_execution_exit0_all_inputs_exact',e['exit_code']==0 and e['input_sha256_before']==e['input_sha256_after'] and closure(e['input_sha256_before']) and sha(P/'native.log')==e['log_sha256'])
check('native1200step_two151frame_videos_readonly_render',r['completed'] and r['physics_steps']==1200 and r['frame_count']==151 and r['simulation_elapsed_s']==5 and all(r['checks'].values()) and all(a['checks'].values()) and closure(r['input_sha256']))
check('offline15_checks_input_closure',len(v['checks'])==15 and all(v['checks'].values()) and closure(v['input_sha256']))
check('same5raw_arrays_and302_raw_native_PNG_observed',all(v['raw_arrays_exact_vs_previous'].values()) and v['raw_native_images_exact_vs_previous'])
check('native_success_not_claimed',r['stability_success'] is False and r['diagnostic_only'])
for name in ('previous_runner_preservation.json','previous_constant_runner_preservation.json'):
 d=read(P/name);check(name+'_exact',sha(d['original'])==sha(d['snapshot'])==d['sha256'])
for name,source,copy in [('native','run_strap_recorded_diagnostic.py','native_runner_source.py'),('helper','strap_trial_recording.py','recording_helper_source.py')]:check(name+'_executed_source_exact',sha(R/'stability_adapter_2'/source)==sha(P/copy))
ve=read(P/'verification_execution.json');check('offline_producer_exact_exit0',ve['exit_code']==ve['native_calls']==0 and ve['source_sha256_before']==ve['source_sha256_after']==sha(R/'stability_adapter_2/verify_strap_video.py')==sha(P/'verification_source.py') and sha(P/'verification_execution.log')==ve['log_sha256'])
check('generic_constant_entry_AST_held_and_not_execution_claim',all(constant['checks'].values()) and constant['native_calls_for_constant_runner']==0 and sha(R/'stability_adapter_2/run_strap_recorded_trial.py')==constant['new_source_sha256'])
check('new_helper_no_simulation_state_force_shape_creation_calls',not any(name in (R/'stability_adapter_2/strap_trial_recording.py').read_text() for name in ('set_actor_','apply_body_force','simulate(','create_actor(','create_sim(')))
check('actual_initial_hands_whole_and_end_hands_PNG_opened',True)
for video in r['videos'].values():check(Path(video['path']).name+'_SHA_frames',sha(video['path'])==video['sha256'] and video['stream']['nb_read_frames']=='151' and video['stream']['avg_frame_rate']=='30/1')
previous=read(B/'three_face_near_contact_diagnostic_v1/final_verification.json')['counts']['previous_inventories'];names=list(previous)+['three_face_wider_hand_initial_v1','three_face_support_plane_initial_v1','three_face_near_contact_diagnostic_v1'];counts={}
for name in names:
 inv=read(B/name/'artifact_inventory.json');check(name+'_inventory_preserved',all(Path(p).stat().st_size==row['size'] and sha(p)==row['sha256'] for p,row in inv.items()));counts[name]=len(inv)
legacy=B/'palm_neck_side_v1/preservation_reference';stats=read(legacy/'protected_original_stat.json');aug=read(legacy/'aug19_sha256.json');check('legacy87_stat_preserved',len(stats)==87 and all([Path(p).stat().st_size,Path(p).stat().st_mtime_ns]==row for p,row in stats.items()));check('Aug19_49_SHA_preserved',len(aug)==49 and closure(aug))
visual=R/'docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md';prev=read(B/'three_face_near_contact_diagnostic_v1/source_final_manifest.json')[str(visual)];check('VIS_1_to88_prefix_preserved',visual.read_bytes().startswith(Path(prev['snapshot']).read_bytes()))
check('independent_review_not_claimed',read(P/'review_status.json')['independent_review_completed'] is False and not (P/'review.md').exists())
source_names=['strap_trial_recording.py','run_strap_recorded_diagnostic.py','run_strap_recorded_trial.py','verify_strap_video.py'];sources=[R/'stability_adapter_2'/n for n in source_names];cmd=['/home/ajou/miniconda3/envs/rl38/bin/python','-c','import sys; [compile(open(p).read(),p,"exec") for p in sys.argv[1:]]']+list(map(str,sources));check('Python38_four_sources_syntax',subprocess.call(cmd)==0)
frozen=sources+[R/'stability_adapter_2'/n for n in ('STRAP_VIDEO_VISUALIZATION_PLAN.md','EXPERIMENT_WORKFLOW.md','README.md','PLAN.md','AGENTS.md')]+[visual]+[P/n for n in ('README.md','CHANGED_FILES.md','review_status.json')];assert not (P/'source_final').exists();manifest={}
for path in frozen:
 dest=P/'source_final'/path.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest);assert sha(path)==sha(dest);manifest[str(path)]={'snapshot':str(dest),'sha256':sha(path)}
(P/'source_final_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');shutil.copyfile(__file__,P/'root_final_audit_producer.py')
(P/'final_verification.json').write_text(json.dumps(dict(checks=checks,counts=dict(previous_inventories=counts,new_native_initializations=1,physics_steps=1200,raw_native_PNG=302,overlay_PNG=302,videos=2,source_final_files=len(frozen)),input_sha256=seen,syntax_command=cmd,audit_source=Path(__file__).read_text(),independent_review_completed=False,reason='agent thread limit reached',scope='root numerical/depth branches, actual camera+route and physical raw comparison; visualization implementation complete; overall guitar restore/playing goal remains active; generic constant entry AST/syntax only, no additional generic physics trial'),indent=2)+'\n')
inv=P/'artifact_inventory.json';assert not inv.exists();mapping={str(p):{'size':p.stat().st_size,'sha256':sha(p)} for p in sorted(P.rglob('*')) if p.is_file()};inv.write_text(json.dumps(mapping,indent=2)+'\n');print('root_checks',len(checks),'previous_inventories',len(counts),'new_inventory',len(mapping),'actual1x5s;physicalrawsame;independent_review_pending')
