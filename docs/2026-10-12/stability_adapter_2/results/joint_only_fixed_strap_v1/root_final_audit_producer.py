from pathlib import Path
import ast,hashlib,json,re,shutil,subprocess
R=Path('/home/ajou/yigyu/3');A=R/'stability_adapter_2';D=R/'docs/2026-10-12/stability_adapter_2';B=D/'results';P=B/'joint_only_fixed_strap_v1';PREV=B/'playing_target_bridge_v1'
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
prep=read(P/'preparation.json');analysis=read(P/'analysis.json');report=read(P/'native/report.json');cap=read(P/'native/capture.json');admission=read(P/'native/initial_grip_audit.json')
for k,d in [('preparation',prep),('analysis',analysis),('native',report)]:
 check(k+'_allchecks_and_inputclosure',all(d['checks'].values()) and closure(d['input_sha256']))
 e=read(P/(k+'_execution.json'));check(k+'_execution0_inputs_log_exact',e['exit_code']==0 and e['input_sha256_before']==e['input_sha256_after'] and closure(e['input_sha256_before']) and e['log_sha256']==sha(P/(k+'.log')))
for stage in ['native','analysis']:
 m=read(P/(stage+'_source_manifest.json'));check(stage+'_preserved_source_paths_exact',all(sha(p)==sha(v['snapshot'])==v['sha256'] for p,v in m.items()))
e=read(P/'preparation_execution.json');check('first_wrapper_preparation_snapshot3_exact',len(e['input_sha256_before'])==3 and all(sha(p)==sha(P/'preparation_source'/Path(p).name)==h for p,h in e['input_sha256_before'].items()))
check('actual_one1200step_two151frames',report['completed'] and report['failure'] is None and report['native_initialization_attempts']==report['native_initializations']==1 and report['physics_steps']==1200 and report['frame_count']==len(cap['frames'])==151 and len(report['videos'])==2)
check('fresh14checks1188selfpairs_sourceclear',len(admission['checks'])==14 and all(admission['checks'].values()) and admission['complete_source_self_screen']['pair_count']==1188 and not admission['complete_source_self_screen']['intersections'])
check('both_original_LA_exact',all(r['strap']['rest_length_m']==1.1018469719600776 for r in analysis['summary']))
for frame in cap['frames']:
 for k in ['image_sha256','raw_image_sha256']:assert closure(frame[k])
check('all604PNG_SHA_exact',True)
video={}
for view,v in report['videos'].items():
 stream=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=duration,nb_read_frames','-of','json',v['path']],text=True))['streams'][0];video[view]=stream
 check(view+'_MP4_151frames_SHA',sha(v['path'])==v['sha256'] and int(stream['nb_read_frames'])==151 and abs(float(stream['duration'])-151/30)<.002)
(P/'video_verification.json').write_text(json.dumps(video,indent=2)+'\n')
update=read(D/'video_collection_update_v5.json');check('new2_video_copies_and_index',update['total_count']==130 and len(update['copies'])==2 and all(sha(v['source'])==sha(v['copy'])==v['sha256'] for v in update['copies']) and update['previous_index_sha256']==sha(D/'VIDEO_INDEX_v5.md') and update['new_index_sha256']==sha(D/'VIDEO_INDEX_v6.md') and (D/'VIDEO_INDEX_v6.md').read_text().endswith((D/'VIDEO_INDEX_v5.md').read_text()))
videos=list((D/'videos').glob('*.mp4'));check('all130_video_copies_exact',len(videos)==130 and all(sha(v)==sha(B/Path(v.name.replace('__','/'))) for v in videos))
counts=read(PREV/'final_verification.json')['counts']['previous_inventories'].copy();counts[PREV.name]=len(read(PREV/'artifact_inventory.json'))
for name,expected in counts.items():
 inv=read(B/name/'artifact_inventory.json');check('preserved_phase_'+name,len(inv)==expected and all(Path(p).stat().st_size==v['size'] and sha(p)==v['sha256'] for p,v in inv.items()))
protected=read(B/'palm_neck_side_v1/preservation_reference/protected_original_stat.json');check('legacy87_stat_exact',len(protected)==87 and all([Path(p).stat().st_size,Path(p).stat().st_mtime_ns]==v for p,v in protected.items()))
aug=read(B/'palm_neck_side_v1/preservation_reference/aug19_sha256.json');check('aug19_49SHA_exact',len(aug)==49 and closure(aug))
before=read(P/'journal_before.json')
for p in [A/'README.md',A/'PLAN.md',D/'VISUAL_REPORT.md']:check('append_only_'+p.name,hashlib.sha256(p.read_bytes()[:before[str(p)]['size']]).hexdigest()==before[str(p)]['sha256'])
AR=P/'artifacts/v2';artifact=read(AR/'artifact_manifest.json');ae=read(AR/'producer_execution.json')
check('artifact_sources_inputs_outputs_exact',artifact['inputs_sha256_before']==artifact['inputs_sha256_after'] and closure(artifact['inputs_sha256_before']) and all(sha(AR/p)==h for p,h in artifact['outputs_sha256'].items()) and artifact['producer_sha256']==sha(A/'make_joint_only_fixed_strap_artifacts_v2.py'))
check('artifact_execution0_no_native',ae['exit_code']==0 and ae['producer_sha256_before']==ae['producer_sha256_after']==artifact['producer_sha256'] and ae['log_sha256']==sha(AR/'producer.log') and all(ae[k]==0 for k in ['native_initializations','physics_steps','actor_inference_calls','training_updates']))
ss=read(AR/'source_snapshot.json');check('artifact_pre_run_snapshots_exact',all(sha(r['original_path'])==sha(AR/r['copy_path'])==r['sha256'] for r in ss['files']))
check('failed_v1_source_preserved_exact',sha(A/'make_joint_only_fixed_strap_artifacts.py')==sha(P/'artifacts/source_snapshot/producer.py')=='a70d4fdab599c2255cd2f53d4d61bbee95b27858fd6180e6625b0db210d66ba5')
failed=P/'artifacts/v1_failed_attempt';fe=read(failed/'producer_execution.json')
check('failed_artifact_attempt_retained_and_limit_disclosed',fe['exit_code']==1 and not fe['artifact_created'] and sha(failed/'producer_source.py')==fe['producer_sha256'] and sha(failed/'producer.log')==fe['log_sha256'] and 'input전후SHA맵' in (P/'ROOT_VERIFICATION_NOTES.md').read_text())
e=read(P/'collection_execution.json');check('collection_execution0_source_log',e['exit_code']==0 and e['source_sha256_before']==e['source_sha256_after']==sha(A/'collect_joint_only_fixed_strap_videos.py')==sha(P/'collection_source.py') and e['log_sha256']==sha(P/'collection.log'))
sources=['prepare_joint_only_fixed_strap.py','run_joint_only_fixed_strap_phase.py','run_joint_only_fixed_strap_phase_v2.py','analyze_joint_only_fixed_strap.py','collect_joint_only_fixed_strap_videos.py','make_joint_only_fixed_strap_artifacts.py','make_joint_only_fixed_strap_artifacts_v2.py']
for s in sources:ast.parse((A/s).read_text(),feature_version=(3,8));check(s+'_python38_syntax',True)
check('independent_review_recorded',(P/'review.md').is_file());check('root_actual_graphic_QA_recorded','QA' in (P/'ROOT_VERIFICATION_NOTES.md').read_text())
for p in list(P.glob('*.md'))+[A/'JOINT_ONLY_FIXED_STRAP_DECISION.md']:
 for target,line in re.findall(r'\]\(<?(/[^)>]+?)(?::(\d+))?>?\)',p.read_text()):
  q=Path(target)
  if q.name=='final_verification.json' and q.parent==P:continue
  check('link_'+str(len(checks)),q.exists() and (not line or len(q.read_text().splitlines())>=int(line)))
shutil.copy2(__file__,P/'root_final_audit_producer.py')
files=[A/s for s in sources]+[A/s for s in ['JOINT_ONLY_FIXED_STRAP_PLAN.md','JOINT_ONLY_FIXED_STRAP_DECISION.md','README.md','PLAN.md','trials/joint_only_fixed_strap_v1/palm_witness_original_LA.json']]+[D/'VISUAL_REPORT.md',D/'VIDEO_INDEX_v6.md',D/'video_collection_update_v5.json']+list(P.glob('*.md'))
manifest={}
for p in files:
 dest=P/'source_final'/p.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);manifest[str(p)]={'snapshot':str(dest),'sha256':sha(p)}
(P/'source_final_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(P/'final_verification.json').write_text(json.dumps({'checks':checks,'counts':{'checks':len(checks),'previous_inventories':counts,'native_initializations':1,'physics_steps':1200,'actor_inference_calls':0,'training_updates':0},'source_snapshot_manifest_sha256':sha(P/'source_final_manifest.json')},ensure_ascii=False,indent=2)+'\n')
inventory={str(p):{'size':p.stat().st_size,'sha256':sha(p)} for p in sorted(P.rglob('*')) if p.is_file() and p.name!='artifact_inventory.json'}
(P/'artifact_inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'protected_previous_phases':len(counts),'inventory':len(inventory),'native_initializations':1,'physics_steps':1200}))
