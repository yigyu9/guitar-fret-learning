from pathlib import Path
import ast,hashlib,json,re,shutil
R=Path('/home/ajou/yigyu/3');A=R/'stability_adapter_2';D=R/'docs/2026-10-12/stability_adapter_2';B=D/'results';P=B/'fixed_strap_middle_relax_v1';AR=P/'artifacts';checks={};cache={}
def read(f):return json.loads(Path(f).read_text())
def sha(f):
 f=Path(f)
 if str(f) not in cache:
  h=hashlib.sha256()
  with f.open('rb') as stream:
   for block in iter(lambda:stream.read(1048576),b''):h.update(block)
  cache[str(f)]=h.hexdigest()
 return cache[str(f)]
def check(k,v):
 assert v,k
 checks[k]=True
def closure(m):return all(sha(f)==h for f,h in m.items())
assert not (P/'final_verification.json').exists() and not (P/'artifact_inventory.json').exists()
check('audit_producer_prearchived_exact',sha(__file__)==sha(P/'root_final_audit_producer.py'))
for stage,n,c in [('preparation',11466,127),('native',11469,128),('analysis',31,10),('collection',141,5)]:
 e=read(P/(stage+'_execution.json'));s=read(P/(stage+'_source_manifest.json'))
 check(stage+'_exit0_inputs_before_after_current',e['exit_code']==0 and len(e['input_sha256_before'])==n and e['input_sha256_before']==e['input_sha256_after'] and closure(e['input_sha256_before']))
 check(stage+'_log_source_copies_exact',sha(P/(stage+'.log'))==e['log_sha256'] and len(s)==c and all(sha(f)==sha(v['snapshot'])==v['sha256'] for f,v in s.items()))
p=read(P/'preparation.json');proposal=read(P/'proposal.json')
check('preparation7_proposal11465_closure_exact',len(p['checks'])==7 and all(p['checks'].values()) and p['checks']==proposal['checks'] and len(p['input_sha256'])==11465 and p['input_sha256']==proposal['input_sha256'] and closure(p['input_sha256']))
check('trial_exact_target_delta',sha(p['trial_path'])==p['trial_sha256'] and p['axis']=='LH:middle3' and p['actual_float32_target_delta_rad']==-0.04999995231628418)
a=read(P/'analysis.json');report=read(P/'native/report.json');fresh=read(P/'native/initial_grip_audit.json')
check('analysis19_29input_closure',len(a['checks'])==19 and all(a['checks'].values()) and len(a['input_sha256_before'])==29 and a['input_sha256_before']==a['input_sha256_after'] and closure(a['input_sha256_before']))
check('actual_one1200_5s_151frames',report['completed'] is True and report['failure'] is None and report['native_initializations']==a['new_native_initializations']==1 and report['physics_steps']==a['new_physics_steps']==1200 and report['simulation_elapsed_s']==5.0 and report['frame_count']==151)
check('native11_fresh14_source1188',len(report['checks'])==11 and all(report['checks'].values()) and len(fresh['checks'])==14 and all(fresh['checks'].values()) and fresh['complete_source_self_screen']['pair_count']==1188 and fresh['complete_source_self_screen']['intersections']==[])
check('not_naturalness_or_playing_certification_no_actor_training',a['naturalness_or_playing_success_certified'] is False and a['actor_inference_calls']==a['training_updates']==0 and report['stability_success'] is None)
check('two_runs_full_windows_and_jointseries',len(a['summary'])==2 and len((P/'windows.jsonl').read_text().splitlines())==242 and len((P/'joint_series.jsonl').read_text().splitlines())==2402)
check('same_fixed_LA',all(x['strap']['rest_length_m']==1.1018469719600776 for x in a['summary']))
base,new=a['summary']
check('mixed_reference_outcomes_preserved',new['max_1s_position_change_mm']<base['max_1s_position_change_mm'] and new['max_1s_rotation_change_deg']<base['max_1s_rotation_change_deg'] and new['guitar']['max_position_change_from_2s_mm']>base['guitar']['max_position_change_from_2s_mm'] and new['guitar']['max_rotation_change_from_2s_deg']>base['guitar']['max_rotation_change_from_2s_deg'])
check('observed_envelope_counts',all(x['windows_within_provisional_limits']==121 and x['outside_initial_envelope_samples']==0 for x in a['summary']))
videos=read(P/'native/videos.json')
check('native_two_video_sha_151_30fps_duration',len(videos)==2 and all(sha(v['path'])==v['sha256'] and v['ffmpeg_exit_code']==v['ffprobe_exit_code']==0 and v['stream']['nb_read_frames']=='151' and v['stream']['avg_frame_rate']=='30/1' and v['stream']['duration']=='5.033333' for v in videos.values()))
check('native_png604_preserved',len(list((P/'native/raw').rglob('*.png')))==302 and len(list((P/'native/frames').rglob('*.png')))==302)
for camera in ['hands','whole_body']:
 old=B/'joint_only_fixed_strap_v1/native/frames'/camera
 current=P/'native/frames'/camera
 check(camera+'_t0_exact_t5_changed',sha(old/'00000.png')==sha(current/'00000.png') and sha(old/'00150.png')!=sha(current/'00150.png'))
am=read(AR/'artifact_manifest.json');ae=read(AR/'producer_execution.json');ss=read(AR/'source_snapshot.json')
check('artifact43_input_closure_exact',len(am['inputs_sha256_before'])==43 and am['inputs_sha256_before']==am['inputs_sha256_after']==ae['inputs_sha256_before']==ae['inputs_sha256_after'] and closure(am['inputs_sha256_before']))
check('artifact43_source_copies_exact',len(ss['files'])==43 and all(sha(v['original_path'])==sha(v['copy_path'])==v['sha256'] for v in ss['files']))
check('artifact_producer_wrapper_log_exact',am['producer_sha256_before']==am['producer_sha256_after']==ae['producer_sha256_before']==ae['producer_sha256_after']==sha(A/'make_middle_relax_artifacts.py') and sha(AR/'run_producer.sh')==sha(AR/'run_producer.sh.archived') and sha(AR/'producer.log')==ae['producer_log_sha256'])
check('artifact_execution0_outputs_exact',ae['exit_code']==0 and am['outputs_sha256']==ae['outputs_sha256'] and all(sha(AR/f)==h for f,h in am['outputs_sha256'].items()))
check('artifact_no_new_physics_actor_training',all(am[k]==ae[k]==0 for k in ['native_initializations_during_artifact','physics_steps_during_artifact','actor_inference_calls_during_artifact','training_updates_during_artifact']))
collection=read(D/'video_collection_update_v7.json')
check('collection_old134_exact_newtwo_exact_total136',len(collection['previous_video_sha256'])==134 and closure(collection['previous_video_sha256']) and len(collection['copies'])==2 and all(sha(v['source'])==sha(v['copy'])==v['sha256'] and Path(v['copy']).stat().st_size==v['size'] for v in collection['copies']) and collection['total_count']==136 and len(list((D/'videos').glob('*.mp4')))==136)
check('collection_old_new_indexes_exact',sha(D/'VIDEO_INDEX_v7.md')==collection['previous_index_sha256'] and sha(D/'VIDEO_INDEX_v8.md')==collection['new_index_sha256'] and sha(A/'collect_middle_relax_videos.py')==collection['producer_sha256'])
for name in ['prepare_fixed_strap_middle_relax.py','run_fixed_strap_middle_relax_phase.py','analyze_fixed_strap_middle_relax.py','collect_middle_relax_videos.py','make_middle_relax_artifacts.py']:
 ast.parse((A/name).read_text(),feature_version=(3,8));check('syntax38_'+name,True)
for name,count in [('natural_envelope_assessment_v1',63),('natural_pose_criteria_v1',15),('finger_contact_map_v1',72)]:
 inv=read(B/name/'artifact_inventory.json');check('preserved_'+name,len(inv)==count and all(Path(f).stat().st_size==v['size'] and sha(f)==v['sha256'] for f,v in inv.items()))
for f,v in read(P/'journal_before.json').items():check('append_only_'+Path(f).name,hashlib.sha256(Path(f).read_bytes()[:v['size']]).hexdigest()==v['sha256'])
for f in P.glob('*.md'):
 for target,line in re.findall(r'\]\(<?(/[^)>]+?)(?::(\d+))?>?\)',f.read_text()):
  q=Path(target);check('link_'+str(len(checks)),q.exists() and (not line or len(q.read_text().splitlines())>=int(line)))
check('review_present',(P/'review.md').is_file())
manifest={}
paths=[A/n for n in ['prepare_fixed_strap_middle_relax.py','run_fixed_strap_middle_relax_phase.py','analyze_fixed_strap_middle_relax.py','collect_middle_relax_videos.py','make_middle_relax_artifacts.py','FIXED_STRAP_MIDDLE_RELAX_PLAN.md','FIXED_STRAP_MIDDLE_RELAX_DECISION.md','trials/fixed_strap_middle_relax_v1/middle3_minus005.json','README.md','PLAN.md']]+[D/'VISUAL_REPORT.md',D/'VIDEO_INDEX_v8.md',D/'video_collection_update_v7.json']+list(P.glob('*.md'))
for f in paths:
 dst=P/'source_final'/f.relative_to(R);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dst);manifest[str(f)]={'snapshot':str(dst),'sha256':sha(f)}
(P/'source_final_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(P/'final_verification.json').write_text(json.dumps(dict(checks=checks,counts=dict(checks=len(checks),protected_previous_files=150,physics_steps=1200,native_initializations=1,actor_inference_calls=0,training_updates=0,artifact_inputs=43,video_collection_total=136),command=['python','/tmp/audit_fixed_strap_middle_relax.py'],root_audit_producer_sha256=sha(__file__),source_final_manifest_sha256=sha(P/'source_final_manifest.json'),scope='One actual middle3 PD-goal-only trial and saved-data comparison; fixed strap; source admission, mixed reference outcomes and artifacts preserved; provisional envelope, not naturalness/playing or cooked penetration certification'),indent=2)+'\n')
inv={str(f):dict(size=f.stat().st_size,sha256=sha(f)) for f in sorted(P.rglob('*')) if f.is_file() and f.name!='artifact_inventory.json'}
(P/'artifact_inventory.json').write_text(json.dumps(inv,indent=2)+'\n');print(json.dumps(dict(checks=len(checks),inventory=len(inv),protected_previous_files=150,native_initializations=1,physics_steps=1200)))
