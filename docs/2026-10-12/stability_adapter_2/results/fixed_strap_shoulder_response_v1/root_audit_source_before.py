from pathlib import Path
import ast,hashlib,json,re,shutil,subprocess
R=Path('/home/ajou/yigyu/3');A=R/'stability_adapter_2';D=R/'docs/2026-10-12/stability_adapter_2';B=D/'results';P=B/'fixed_strap_shoulder_response_v1';PREV=B/'joint_only_fixed_strap_v1'
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
analysis=read(P/'analysis.json');prep=read(P/'preparation.json')
for label,data in [('preparation',prep),('analysis',analysis)]:check(label+'_allchecks_inputSHA',all(data['checks'].values()) and closure(data['input_sha256']))
for stage in ['preparation','minus008','plus008','analysis']:
 e=read(P/(stage+'_execution.json'));check(stage+'_execution0_inputSHA_log',e['exit_code']==0 and e['input_sha256_before']==e['input_sha256_after'] and closure(e['input_sha256_before']) and sha(P/(stage+'.log'))==e['log_sha256'])
 m=read(P/(stage+'_source_manifest.json'));check(stage+'_sourcecopies_exact',all(sha(p)==sha(v['snapshot'])==v['sha256'] for p,v in m.items()))
video={}
for label in ['minus008','plus008']:
 report=read(P/label/'report.json');cap=read(P/label/'capture.json');ad=read(P/label/'initial_grip_audit.json')
 check(label+'_actual_one1200step',report['completed'] and report['failure'] is None and report['native_initializations']==report['native_initialization_attempts']==1 and report['physics_steps']==1200 and report['frame_count']==len(cap['frames'])==151 and all(report['checks'].values()))
 check(label+'_fresh14checks_1188clear',len(ad['checks'])==14 and all(ad['checks'].values()) and ad['complete_source_self_screen']['pair_count']==1188 and not ad['complete_source_self_screen']['intersections'])
 check(label+'_604PNG_SHA',all(closure(frame[k]) for frame in cap['frames'] for k in ['image_sha256','raw_image_sha256']))
 for view,v in report['videos'].items():
  s=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=duration,nb_read_frames','-of','json',v['path']],text=True))['streams'][0];video[label+'_'+view]=s
  check(label+'_'+view+'_151frames_SHA',sha(v['path'])==v['sha256'] and int(s['nb_read_frames'])==151 and abs(float(s['duration'])-151/30)<.002)
(P/'video_verification.json').write_text(json.dumps(video,indent=2)+'\n')
check('three_exact_LA',all(r['strap']['rest_length_m']==1.1018469719600776 for r in analysis['summary']))
update=read(D/'video_collection_update_v6.json');check('collection4_index134',len(update['copies'])==4 and update['total_count']==134 and all(sha(v['source'])==sha(v['copy'])==v['sha256'] for v in update['copies']) and update['previous_index_sha256']==sha(D/'VIDEO_INDEX_v6.md') and update['new_index_sha256']==sha(D/'VIDEO_INDEX_v7.md') and (D/'VIDEO_INDEX_v7.md').read_text().endswith((D/'VIDEO_INDEX_v6.md').read_text()))
videos=list((D/'videos').glob('*.mp4'));check('all134_video_copies_exact',len(videos)==134 and all(sha(v)==sha(B/Path(v.name.replace('__','/'))) for v in videos))
e=read(P/'collection_execution.json');check('collection_execution_input_source_log_exact',e['exit_code']==0 and e['input_sha256_before']==e['input_sha256_after'] and closure(e['input_sha256_before']) and e['source_sha256_before']==e['source_sha256_after']==sha(A/'collect_fixed_strap_shoulder_videos.py')==sha(P/'collection_source.py') and sha(P/'collection.log')==e['log_sha256'])
counts=read(PREV/'final_verification.json')['counts']['previous_inventories'].copy();counts[PREV.name]=len(read(PREV/'artifact_inventory.json'))
for name,n in counts.items():
 inv=read(B/name/'artifact_inventory.json');check('protected_'+name,len(inv)==n and all(Path(p).stat().st_size==v['size'] and sha(p)==v['sha256'] for p,v in inv.items()))
protected=read(B/'palm_neck_side_v1/preservation_reference/protected_original_stat.json');check('legacy87_stat',len(protected)==87 and all([Path(p).stat().st_size,Path(p).stat().st_mtime_ns]==v for p,v in protected.items()))
aug=read(B/'palm_neck_side_v1/preservation_reference/aug19_sha256.json');check('aug19_49SHA',len(aug)==49 and closure(aug))
before=read(P/'journal_before.json')
for p in [A/'README.md',A/'PLAN.md',D/'VISUAL_REPORT.md']:check('append_only_'+p.name,hashlib.sha256(p.read_bytes()[:before[str(p)]['size']]).hexdigest()==before[str(p)]['sha256'])
AR=P/'artifacts';am=read(AR/'artifact_manifest.json');ae=read(AR/'producer_execution.json')
check('artifact_input_output_exact',am['inputs_sha256_before']==am['inputs_sha256_after'] and closure(am['inputs_sha256_before']) and all(sha(AR/n)==h for n,h in am['outputs_sha256'].items()) and sha(A/'make_fixed_strap_shoulder_artifacts.py')==am['producer_sha256_before']==am['producer_sha256_after'])
check('artifact_execution0_no_native',ae['exit_code']==0 and ae['producer_sha256_before']==ae['producer_sha256_after']==am['producer_sha256_before'] and sha(AR/'producer.log')==ae['log_sha256'] and all(ae[k]==0 for k in ['native_initializations','physics_steps','actor_inference_calls','training_updates']))
check('artifact_execution_maps_match',ae['inputs_sha256_before']==ae['inputs_sha256_after']==am['inputs_sha256_before'] and ae['outputs_sha256']==am['outputs_sha256'])
ss=read(AR/'source_snapshot.json');check('artifact_pre_run_snapshots',all(sha(row['original_path'])==sha(AR/row['copy_path'])==row['sha256'] for row in ss['files']))
sources=['prepare_fixed_strap_shoulder_response.py','run_fixed_strap_shoulder_phase.py','analyze_fixed_strap_shoulder_response.py','collect_fixed_strap_shoulder_videos.py','make_fixed_strap_shoulder_artifacts.py']
for source in sources:ast.parse((A/source).read_text(),feature_version=(3,8));check(source+'_python38_syntax',True)
check('root_QA_and_review',(P/'review.md').is_file() and 'QA' in (P/'ROOT_VERIFICATION_NOTES.md').read_text())
for p in list(P.glob('*.md'))+[A/'FIXED_STRAP_SHOULDER_RESPONSE_DECISION.md']:
 for target,line in re.findall(r'\]\(<?(/[^)>]+?)(?::(\d+))?>?\)',p.read_text()):
  q=Path(target)
  if q.name=='final_verification.json' and q.parent==P:continue
  check('link_'+str(len(checks)),q.exists() and (not line or len(q.read_text().splitlines())>=int(line)))
shutil.copy2(__file__,P/'root_final_audit_producer.py')
files=[A/s for s in sources]+[A/s for s in ['FIXED_STRAP_SHOULDER_RESPONSE_PLAN.md','FIXED_STRAP_SHOULDER_RESPONSE_DECISION.md','README.md','PLAN.md','trials/fixed_strap_shoulder_response_v1/minus008.json','trials/fixed_strap_shoulder_response_v1/plus008.json']]+[D/'VISUAL_REPORT.md',D/'VIDEO_INDEX_v7.md',D/'video_collection_update_v6.json']+list(P.glob('*.md'))
manifest={}
for p in files:
 dest=P/'source_final'/p.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);manifest[str(p)]={'snapshot':str(dest),'sha256':sha(p)}
(P/'source_final_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(P/'final_verification.json').write_text(json.dumps(dict(checks=checks,counts=dict(checks=len(checks),previous_inventories=counts,native_initializations=2,physics_steps=2400,actor_inference_calls=0,training_updates=0),source_snapshot_manifest_sha256=sha(P/'source_final_manifest.json')),ensure_ascii=False,indent=2)+'\n')
inventory={str(p):dict(size=p.stat().st_size,sha256=sha(p)) for p in sorted(P.rglob('*')) if p.is_file() and p.name!='artifact_inventory.json'}
(P/'artifact_inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(checks=len(checks),protected_previous_phases=len(counts),inventory=len(inventory),native_initializations=2,physics_steps=2400)))
