from pathlib import Path
import ast,hashlib,json,re,shutil,subprocess
R=Path('/home/ajou/yigyu/3');A=R/'stability_adapter_2';D=R/'docs/2026-10-12/stability_adapter_2';B=D/'results';P=B/'coupled_palm_witness_v1';PREV=B/'coupled_support_source_v1'
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
search=read(P/'search.json');prep=read(P/'preparation.json');analysis=read(P/'analysis.json');report=read(P/'native/report.json');cap=read(P/'native/capture.json');audit=read(P/'native/initial_grip_audit.json')
for name,data in [('search',search),('preparation',prep),('analysis',analysis)]:
 check(name+'_all_checks_and_closure',all(data['checks'].values()) and closure(data['input_sha256']))
for name,source in [('search','search_coupled_palm_witness.py'),('preparation','prepare_palm_witness_initial_trial.py'),('analysis','analyze_palm_witness_initial.py')]:
 e=read(P/(name+'_execution.json'))
 check(name+'_execution0_source_log_exact',e['exit_code']==0 and e['source_sha256_before']==e['source_sha256_after']==sha(A/source)==sha(P/(name+'_source.py')) and e['log_sha256']==sha(P/(name+'.log')))
check('search16_placements6passes',len(search['rows'])==16 and sum(bool(r['source_direction_screen_passed']) for r in search['rows'])==6)
check('preparation11_checks_and_analysis16_checks',len(prep['checks'])==11 and len(analysis['checks'])==16)
check('native_one_complete1200step_two151frame',report['completed'] and report['failure'] is None and report['native_initializations']==1 and report['physics_steps']==1200 and report['frame_count']==151 and len(report['videos'])==2 and len(cap['frames'])==151)
check('native_checks_inputs_exact',report['native_initialization_attempts']==1 and all(report['checks'].values()) and closure(report['input_sha256']))
e=read(P/'native_execution.json')
check('native_execution0_sources_log_exact',e['exit_code']==0 and e['input_sha256_before']==e['input_sha256_after'] and closure(e['input_sha256_before']) and e['log_sha256']==sha(P/'native_execution.log') and sha(A/'run_palm_witness_initial_diagnostic.py')==sha(P/'native_entrypoint_source.py') and sha(A/'run_small_wrist_recorded_diagnostic.py')==sha(P/'native_source.py')=='34d50c9f95a1b100efce621470a099d0aa259df7bbf307e5c7e44c6927598ef6')
check('fresh_t0_14checks1188selfpairs_no_sourceintersection',len(audit['checks'])==14 and all(audit['checks'].values()) and audit['complete_source_self_screen']['pair_count']==1188 and not audit['complete_source_self_screen']['intersections'])
for frame in cap['frames']:
 for key in ['image_sha256','raw_image_sha256']:assert closure(frame[key])
check('604_recorded_PNG_SHA_exact',True)
video={}
for view,v in report['videos'].items():
 raw=subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=duration,nb_read_frames','-of','json',v['path']],text=True);stream=json.loads(raw)['streams'][0];video[view]=stream
 check(view+'_MP4actual151frames5s_SHA',sha(v['path'])==v['sha256'] and int(stream['nb_read_frames'])==151 and abs(float(stream['duration'])-151/30)<.002)
(P/'video_verification.json').write_text(json.dumps(video,indent=2)+'\n')
update=read(D/'video_collection_update_v4.json')
check('128_video_collection_new2_exact_index_preserved',update['total_count']==len(list((D/'videos').glob('*.mp4')))==128 and len(update['copies'])==2 and all(sha(r['source'])==sha(r['copy'])==r['sha256'] for r in update['copies']) and update['previous_index_sha256']==sha(D/'VIDEO_INDEX_v4.md') and update['new_index_sha256']==sha(D/'VIDEO_INDEX_v5.md') and (D/'VIDEO_INDEX_v5.md').read_text().endswith((D/'VIDEO_INDEX_v4.md').read_text()))
counts=read(PREV/'final_verification.json')['counts']['previous_inventories'].copy();counts[PREV.name]=len(read(PREV/'artifact_inventory.json'))
for name,expected in counts.items():
 inv=read(B/name/'artifact_inventory.json');check('preserved_phase_'+name,len(inv)==expected and all(Path(p).stat().st_size==v['size'] and sha(p)==v['sha256'] for p,v in inv.items()))
protected=read(B/'palm_neck_side_v1/preservation_reference/protected_original_stat.json');check('legacy87_stat_exact',len(protected)==87 and all([Path(p).stat().st_size,Path(p).stat().st_mtime_ns]==v for p,v in protected.items()))
aug=read(B/'palm_neck_side_v1/preservation_reference/aug19_sha256.json');check('aug19_49SHA_exact',len(aug)==49 and closure(aug))
before=read(P/'journal_before.json')
for p in [A/'README.md',A/'PLAN.md',D/'VISUAL_REPORT.md']:
 check('append_only_'+p.name,hashlib.sha256(p.read_bytes()[:before[str(p)]['size']]).hexdigest()==before[str(p)]['sha256'])
check('learning_plan_consumed_unchanged',sha(A/'PLAYING_RESIDUAL_EVALUATION.md')=='d3738dca9a7f701cf4e7221d2eb85ee01cfebfbba63fa48813eb68d615f2149b')
artifact=read(P/'artifacts/artifact_manifest.json');artifact_exe=read(P/'artifacts/producer_execution.json')
check('revised_artifact_inputs_outputs_source_exact',artifact['inputs_sha256_before']==artifact['inputs_sha256_after'] and closure(artifact['inputs_sha256_before']) and all(sha(P/'artifacts'/p)==h for p,h in artifact['outputs_sha256'].items()) and artifact['producer_sha256']==sha(A/'make_palm_witness_artifacts.py'))
check('revised_artifact_execution0_no_native',artifact_exe['exit_code']==0 and all(artifact[k]==0 for k in ['native_calls','physics_steps','inference_calls','training_steps']))
recovery=read(P/'artifact_revision_preservation.json')
check('original_source_and_PNG_recovered_exact',sha(recovery['recovered_source_path'])==sha(P/'artifacts/recovered_v1/producer_source.py')==recovery['original_source_sha256']=='61ea48b82aed0f27d3c005c17bedfc9b3edec157d55b7f6cdc712a18b95161fe' and sha(recovery['recovered_png_path'])==recovery['original_png_sha256']=='db6c6964dacc0c816272be17179b33813144b6692bd97dde1b4b3f412bfde68f')
check('revised_set_preserved5files_exact',len(recovery['revised'])==5 and all(sha(p)==sha(v['snapshot'])==v['sha256'] for p,v in recovery['revised'].items()))
check('original_execution_provenance_limitation_disclosed',not recovery['original_execution_manifest_log_metadata_byte_recovery_verified'] and 'byte' in (P/'ROOT_VERIFICATION_NOTES.md').read_text())
recovered_manifest=read(P/'artifacts/recovered_v1/artifact_manifest.json')
check('recovered_manifest_new_run_sealed_inputs',recovered_manifest['inputs_sha256_before']==recovered_manifest['inputs_sha256_after']==artifact['inputs_sha256_before'] and all(sha(P/'artifacts/recovered_v1'/p)==h for p,h in recovered_manifest['outputs_sha256'].items()))
e=read(P/'collection_execution.json')
check('collection_execution0_source_log_exact',e['exit_code']==0 and e['source_sha256_before']==e['source_sha256_after']==sha(A/'collect_palm_witness_videos.py')==sha(P/'collection_source.py') and e['log_sha256']==sha(P/'collection.log'))

sources=['search_coupled_palm_witness.py','prepare_palm_witness_initial_trial.py','run_palm_witness_initial_diagnostic.py','analyze_palm_witness_initial.py','collect_palm_witness_videos.py','make_palm_witness_artifacts.py','make_palm_witness_artifacts_v1_recovered.py']
for s in sources:ast.parse((A/s).read_text(),feature_version=(3,8));check(s+'_python38_syntax',True)
check('independent_review_recorded',(P/'review.md').is_file())
check('actual_graphic_QA_recorded',(P/'ROOT_VERIFICATION_NOTES.md').is_file() and 'QA' in (P/'ROOT_VERIFICATION_NOTES.md').read_text())
for p in list(P.glob('*.md'))+[A/'PALM_WITNESS_INITIAL_DECISION.md']:
 for target,line in re.findall(r'\]\(<?(/[^)>]+?)(?::(\d+))?>?\)',p.read_text()):
  q=Path(target)
  if q.name=='final_verification.json' and q.parent==P:continue
  check('link_'+str(len(checks)),q.exists() and (not line or len(q.read_text().splitlines())>=int(line)))
shutil.copy2(__file__,P/'root_final_audit_producer.py')
files=[A/s for s in sources]+[A/s for s in ['COUPLED_PALM_WITNESS_PLAN.md','PALM_WITNESS_INITIAL_TRIAL_PLAN.md','PALM_WITNESS_INITIAL_DECISION.md','README.md','PLAN.md','trials/coupled_palm_witness_v1/initial_witness.json']]+[D/'VISUAL_REPORT.md',D/'VIDEO_INDEX_v5.md',D/'video_collection_update_v4.json']+list(P.glob('*.md'))
manifest={}
for p in files:
 dest=P/'source_final'/p.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);manifest[str(p)]={'snapshot':str(dest),'sha256':sha(p)}
(P/'source_final_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(P/'final_verification.json').write_text(json.dumps({'checks':checks,'counts':{'checks':len(checks),'previous_inventories':counts,'native_initializations':1,'physics_steps':1200,'actor_inference_calls':0,'training_updates':0},'source_snapshot_manifest_sha256':sha(P/'source_final_manifest.json')},ensure_ascii=False,indent=2)+'\n')
inventory={str(p):{'size':p.stat().st_size,'sha256':sha(p)} for p in sorted(P.rglob('*')) if p.is_file() and p.name!='artifact_inventory.json'}
(P/'artifact_inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'protected_previous_phases':len(counts),'inventory':len(inventory),'native':1,'physics_steps':1200}))
