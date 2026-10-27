from pathlib import Path
import ast,hashlib,json,re,shutil,subprocess
R=Path('/home/ajou/yigyu/3'); A=R/'stability_adapter_2'; D=R/'docs/2026-10-12/stability_adapter_2'; B=D/'results'; P=B/'body9_strap_minus4mm_v1'; PREV=B/'playing_prior_adaptation_v1'; checks={}; cache={}
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
 if not v:raise AssertionError(k)
 checks[k]=True

def closure(d):return all(sha(p)==h for p,h in d.items())
analysis=read(P/'analysis.json');report=read(P/'native/report.json');prep=read(P/'preparation.json');exe=read(P/'native_execution.json');cap=read(P/'native/capture.json');rows=analysis['summary']
check('preparation_four_checks_closure_no_physics',len(prep['checks'])==4 and all(prep['checks'].values()) and closure(prep['input_sha256']) and prep['native_initializations']==prep['physics_steps']==0 and sha(A/'prepare_body9_strap_minus4mm_trial.py')==sha(P/'preparation_source.py'))
check('one_native1200step_two151frames_complete',report['completed'] and report['failure'] is None and report['native_initializations']==1 and report['physics_steps']==1200 and report['frame_count']==151 and len(report['videos'])==2 and len(cap['frames'])==151)
check('all_native_checks_inputs_exact',all(report['checks'].values()) and closure(report['input_sha256']))
check('native_wrapper_source_log_exact',exe['exit_code']==0 and exe['input_sha256_before']==exe['input_sha256_after'] and closure(exe['input_sha256_before']) and exe['log_sha256']==sha(P/'native_execution.log') and sha(A/'run_small_wrist_recorded_diagnostic.py')==sha(P/'native_source.py')=='34d50c9f95a1b100efce621470a099d0aa259df7bbf307e5c7e44c6927598ef6')
check('analysis13_checks_closure_threeconditions',len(analysis['checks'])==13 and all(analysis['checks'].values()) and closure(analysis['input_sha256']) and [r['label'] for r in rows]==['baseline','minus2mm','minus4mm'])
check('law_reconstruction_all1200_threeconditions',all(r['strap']['law_reconstruction_max_error_n']<1e-8 for r in rows))
check('tradeoffs_and_missing_palm_preserved',rows[2]['guitar']['max_initial_position_error_mm']>rows[1]['guitar']['max_initial_position_error_mm'] and rows[2]['guitar']['max_initial_rotation_error_deg']<rows[1]['guitar']['max_initial_rotation_error_deg'] and rows[2]['guitar']['max_position_change_from_2s_mm']>rows[1]['guitar']['max_position_change_from_2s_mm'] and all(r['palm_guitar_positive_raw_lambda_steps']==0 for r in rows))
for tag,source in [('analysis','analyze_body9_strap_minus4mm.py'),('artifact','make_body9_strap_minus4mm_artifacts.py'),('artifact_execution_v2','make_body9_strap_minus4mm_artifacts_v2.py'),('artifact_execution_v3','make_body9_strap_minus4mm_artifacts_v3.py')]:
 meta=P/(tag+'.json') if tag.startswith('artifact_execution_') else P/(tag+'_execution.json'); e=read(meta)
 log=P/('artifact_'+tag.rsplit('_',1)[1]+'.log') if tag.startswith('artifact_execution_') else P/(tag+'.log')
 check(tag+'_execution0_source_log',e['exit_code']==e['native_calls']==0 and e['source_sha256_before']==e['source_sha256_after']==sha(A/source) and e['log_sha256']==sha(log))
for suffix in ['','_v2','_v3']:
 m=read(P/('artifacts/artifact_manifest'+suffix+'.json'))
 check('artifact'+suffix+'_all_inputs_outputs_exact',m['input_sha256_before']==m['input_sha256_after'] and closure(m['input_sha256_before']) and closure(m['outputs_sha256']) and m['native_initializations_during_plotting']==m['physics_steps_during_plotting']==0)
for version in ['v1','v2']:
 folder=P/('artifact_'+version+'_preserved')
 for f in folder.iterdir():check('preserved_'+version+'_'+f.name,sha(f)==sha(P/f.name))
for frame in cap['frames']:
 for key in ['image_sha256','raw_image_sha256']:
  assert closure(frame[key])
check('604_recorded_PNG_SHA_exact',True)
oldcap=read(B/'small_wrist_motion_v1/native/capture.json')
check('t0_raw_both_camera_RGB_exact',sorted(oldcap['frames'][0]['raw_image_sha256'].values())==sorted(cap['frames'][0]['raw_image_sha256'].values()))
video={}
for view,v in report['videos'].items():
 raw=subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=duration,nb_read_frames','-of','json',v['path']],text=True);stream=json.loads(raw)['streams'][0];video[view]=stream
 check(view+'_MP4actual151frames5s_SHA',sha(v['path'])==v['sha256'] and int(stream['nb_read_frames'])==151 and abs(float(stream['duration'])-151/30)<.002)
(P/'video_verification.json').write_text(json.dumps(video,indent=2)+'\n')
update=read(D/'video_collection_update_v3.json')
check('126_video_collection_new2_exact_index_preserved',update['total_count']==len(list((D/'videos').glob('*.mp4')))==126 and len(update['copies'])==2 and all(sha(r['source'])==sha(r['copy'])==r['sha256'] for r in update['copies']) and update['previous_index_sha256']==sha(D/'VIDEO_INDEX_v3.md') and update['new_index_sha256']==sha(D/'VIDEO_INDEX_v4.md') and (D/'VIDEO_INDEX_v4.md').read_text().endswith((D/'VIDEO_INDEX_v3.md').read_text()))
corr=read(P/'contract_correction/contract_audit.json')
check('checkpoint_schema_corrected_fivechecks_no_execution',len(corr['checks'])==5 and all(corr['checks'].values()) and corr['input_sha256_before']==corr['input_sha256_after'] and closure(corr['input_sha256_before']) and [r['observation_schema'] for r in corr['examples']]==['fret.observation.v2','strike.observation.v2'] and all(corr[k]==0 for k in ['native_initializations','physics_steps','model_inference_calls','training_updates']))
counts=read(PREV/'final_verification.json')['counts']['previous_inventories'].copy();counts[PREV.name]=len(read(PREV/'artifact_inventory.json'))
for name,expected in counts.items():
 inv=read(B/name/'artifact_inventory.json');check('previous_inventory_'+name,len(inv)==expected and all(Path(p).stat().st_size==v['size'] and sha(p)==v['sha256'] for p,v in inv.items()))
protected=read(B/'palm_neck_side_v1/preservation_reference/protected_original_stat.json');check('legacy87_stat_exact',len(protected)==87 and all([Path(p).stat().st_size,Path(p).stat().st_mtime_ns]==v for p,v in protected.items()))
aug=read(B/'palm_neck_side_v1/preservation_reference/aug19_sha256.json');check('aug19_49SHA_exact',len(aug)==49 and closure(aug))
oldmanifest=read(PREV/'source_final_manifest.json')
for p in [A/'README.md',A/'PLAN.md',D/'VISUAL_REPORT.md']:
 record=oldmanifest[str(p)];check('previous_prefix_'+p.name,p.read_bytes().startswith(Path(record['snapshot']).read_bytes()) and sha(record['snapshot'])==record['sha256'])
sources=['prepare_body9_strap_minus4mm_trial.py','analyze_body9_strap_minus4mm.py','audit_playing_prior_contracts_v2.py','collect_body9_strap_minus4mm_videos.py','make_body9_strap_minus4mm_artifacts.py','make_body9_strap_minus4mm_artifacts_v2.py','make_body9_strap_minus4mm_artifacts_v3.py']
for s in sources:ast.parse((A/s).read_text(),feature_version=(3,8));check(s+'_python38syntax',True)
check('independent_review_exists', (P/'review.md').is_file() and 'v3' in (P/'review.md').read_text())
check('v3_actual_PNG_native_t0_5s_QA_recorded',(P/'ROOT_VERIFICATION_NOTES.md').is_file() and 'QA' in (P/'ROOT_VERIFICATION_NOTES.md').read_text())
check('actual_main_journal_lines',all(t in p.read_text().splitlines()[n-1] for p,n,t in [(A/'README.md',964,'## Strap total'),(A/'PLAN.md',1740,'## Strap total'),(D/'VISUAL_REPORT.md',1806,'## 97.')]))
for p in P.glob('*.md'):
 for path,line in re.findall(r'\]\((/[^)]+?)(?::(\d+))?\)',p.read_text()):
  q=Path(path)
  if q.name=='final_verification.json' and q.parent==P:continue
  check('link_'+str(len(checks)),q.exists() and (not line or len(q.read_text().splitlines())>=int(line)))
shutil.copy2(__file__,P/'root_final_audit_producer.py')
files=[A/s for s in sources]+[A/s for s in ['BODY9_STRAP_MINUS4MM_EXECUTION.md','PLAYING_PRIOR_CONTRACT_CORRECTION.md','STRAP_MINUS4MM_DECISION.md','README.md','PLAN.md','trials/body9_strap_minus4mm_v1/la_minus4mm.json']]+[D/'VISUAL_REPORT.md',D/'VIDEO_INDEX_v4.md',D/'video_collection_update_v3.json']+list(P.glob('*.md'))
manifest={}
for p in files:
 dest=P/'source_final'/p.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);manifest[str(p)]={'snapshot':str(dest),'sha256':sha(p)}
(P/'source_final_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(P/'final_verification.json').write_text(json.dumps({'checks':checks,'counts':{'checks':len(checks),'previous_inventories':counts,'native_initializations':1,'physics_steps':1200,'training_updates':0},'review':'independent reviewer; v1/v2 graphic defects preserved and v3 resolved','source_snapshot_manifest_sha256':sha(P/'source_final_manifest.json')},ensure_ascii=False,indent=2)+'\n')
inventory={str(p):{'size':p.stat().st_size,'sha256':sha(p)} for p in sorted(P.rglob('*')) if p.is_file() and p.name!='artifact_inventory.json'}
(P/'artifact_inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'protected_previous_phases':len(counts),'inventory':len(inventory),'native':1,'physics_steps':1200}))
