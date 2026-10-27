"""Seal completed physical responses, the preserved crash, and saved artifacts."""
from pathlib import Path
import hashlib
import json
import shutil

R=Path('/home/ajou/yigyu/3');A=R/'stability_adapter_2';D=R/'docs/2026-10-12/stability_adapter_2'
P=D/'results/quiet_index_support_authority_v1'


def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    assert not (P/'artifact_inventory.json').exists() and not (P/'final_verification.json').exists()
    checks={}
    for condition,count,code in [('plus',103,0),('minus',103,-11),('minus_retry_v2',107,0)]:
        e=read(P/(condition+'_execution.json'));m=read(P/(condition+'_source_manifest.json'))
        checks[condition+'_execution_and_current_inputs']=e['exit_code']==code and len(e['input_sha256_before'])==count and e['input_sha256_before']==e['input_sha256_after'] and all(sha(p)==h for p,h in e['input_sha256_before'].items()) and sha(P/(condition+'.log'))==e['log_sha256']
        checks[condition+'_source_copies_exact']=len(m)==count and all(sha(p)==sha(v['snapshot'])==v['sha256'] for p,v in m.items())
        if code==0:
            report=read(P/'native'/condition/'report.json');audit=read(P/'native'/condition/'initial_grip_audit.json')
            checks[condition+'_completed_one_native_1200_151']=report['completed'] and report['failure'] is None and report['native_initialization_attempts']==report['native_initializations']==1 and report['physics_steps']==1200 and report['frame_count']==151 and all(report['checks'].values())
            checks[condition+'_fresh15_direct_gate']=len(audit['checks'])==15 and all(audit['checks'].values()) and audit['complete_source_self_screen']['pair_count']==1188
    crash=read(P/'minus_native_crash.json')
    checks['original_minus86_files_preserved_and_partial_scope']=len(crash['output_inventory'])==86 and crash['physics_steps_observed']==152 and crash['frame_count']==19 and crash['simulation_elapsed_s_observed']<2 and all(crash['checks'].values()) and all(Path(p).stat().st_size==v['size'] and sha(p)==v['sha256'] for p,v in crash['output_inventory'].items()) and not (P/'native/minus/report.json').exists() and not (P/'native/minus/videos.json').exists()
    checks['retry_preserved_first_crash']=read(P/'minus_retry_v2_execution.json')['prior_partial_outputs_unchanged'] is True
    analysis=read(P/'analysis.json')
    checks['analysis47_3initializations_2400complete_152failed_observed']=len(analysis['checks'])==47 and all(analysis['checks'].values()) and analysis['physical_initializations']==3 and analysis['completed_trial_physics_steps']==2400 and analysis['failed_trial_steps_observed']==152 and analysis['total_physics_steps_observed']==2552 and analysis['actor_inference_calls']==analysis['training_updates']==0
    for stage in ['analysis','collection','artifact','artifact_v2']:
        e=read(P/(stage+'_execution.json'));m=read(P/(stage+'_source_manifest.json'))['files']
        checks[stage+'_exit0_current_inputs_closed_log']=e['exit_code']==0 and e['input_sha256_before']==e['input_sha256_after'] and all(sha(p)==h for p,h in e['input_sha256_before'].items()) and sha(P/(stage+'.log'))==e['log_sha256']
        checks[stage+'_declared_copies_exact']=all(sha(v['original_path'])==sha(v['copy_path'])==v['sha256']==v['copy_sha256'] for v in m)
    checks['analysis_direct_closure_preserved']=analysis['input_sha256_before']==analysis['input_sha256_after'] and all(sha(p)==h for p,h in analysis['input_sha256_before'].items()) and set(analysis['input_sha256_before'])<=set(read(P/'analysis_execution.json')['input_sha256_before'])
    drift=read(P/'source_drift/record.json')
    checks['unexecuted_canonical_edit_preserved_and_restored']=sha(A/'run_quiet_index_postprocess.py')==drift['consumed_sha256']==drift['canonical_restored_sha256'] and sha(drift['preserved_modified_source'])==drift['unexecuted_modified_sha256'] and not drift['collection_invocation_present'] and not drift['collection_execution_present'] and drift['physical_reruns']==drift['analysis_reruns']==0
    for folder in [P/'artifacts',P/'artifacts/v2']:
        artifact=read(folder/'manifest.json')
        checks['plot_exact_no_new_physics_'+str(folder.relative_to(P))]=artifact['native_calls']==artifact['physics_steps']==artifact['actor_inference_calls']==artifact['training_updates']==0 and artifact['inputs_sha256_before']==artifact['inputs_sha256_after'] and all(sha(p)==h for p,h in artifact['inputs_sha256_before'].items()) and all(sha(folder/p)==h for p,h in artifact['outputs_sha256'].items())
    update=read(D/'video_collection_update_v13.json')
    checks['158_videos_previous152_exact_sixcopies']=len(list((D/'videos').glob('*.mp4')))==update['total_count']==158 and len(update['previous_video_sha256'])==152 and all(sha(p)==h for p,h in update['previous_video_sha256'].items()) and len(update['copies'])==6 and sum(v['partial'] for v in update['copies'])==2 and all(sha(v['source'])==sha(v['copy'])==v['sha256']==v['copy_sha256'] for v in update['copies'])
    checks['video_indexes_preserved']=sha(D/'VIDEO_INDEX_v13.md')==update['previous_index_sha256'] and sha(D/'VIDEO_INDEX_v14.md')==update['new_index_sha256']
    for p,v in read(P/'journal_before.json').items():checks['append_only_'+Path(p).name]=hashlib.sha256(Path(p).read_bytes()[:v['size']]).hexdigest()==v['sha256']
    previous={}
    phases=['initial_middle3_alignment_v1','fixed_strap_source_compatibility_v1','no_strap_current_pose_v1','fixed_strap_source_hand_initial_v1','source_hand_thumb_base_native_v1','source_hand_wrist_clearance_v1','source_hand_arm_position_v1','source_hand_arm_continuous_v1']
    inventories=[D/'results'/n/'artifact_inventory.json' for n in phases]+[D/'results/source_hand_thumb2_clearance_v2/artifact_inventory_v2.json']
    for inventory in inventories:
        for p,v in read(inventory).items():
            assert p not in previous or previous[p]==v
            previous[p]=v
    checks['all_prior_declared_files_exact']=all(Path(p).stat().st_size==v['size'] and sha(p)==v['sha256'] for p,v in previous.items())
    checks['independent_final_review_PASS']='최종 판정: PASS' in (P/'review.md').read_text()
    assert all(checks.values()),checks
    sources=[A/n for n in ['QUIET_INDEX_SUPPORT_AUTHORITY_PLAN.md','QUIET_INDEX_SUPPORT_EXECUTION.md','QUIET_INDEX_NATIVE_RETRY_V2.md','QUIET_WRIST_SUPPORT_AUTHORITY_PLAN.md','run_quiet_index_support.py','run_quiet_index_support_phase.py','run_quiet_index_support_retry.py','analyze_quiet_index_support.py','analyze_quiet_index_support_v2.py','run_quiet_index_postprocess.py','collect_quiet_index_videos.py','make_quiet_index_artifacts.py','make_quiet_index_artifacts_v2.py','README.md','PLAN.md']]
    sources += [D/'VISUAL_REPORT.md',D/'VIDEO_INDEX_v14.md',D/'video_collection_update_v13.json',P/'README.md',P/'CHANGED_FILES.md',P/'review.md',P/'ROOT_VERIFICATION_NOTES.md',Path(__file__).resolve()]
    manifest={}
    for p in sources:
        dest=P/'source_final'/p.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);assert sha(dest)==sha(p)
        manifest[str(p)]=dict(snapshot=str(dest),sha256=sha(p))
    (P/'source_final_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (P/'final_verification.json').write_text(json.dumps(dict(checks=checks,prior_declared_files_preserved=len(previous),physical_initializations=3,completed_trial_physics_steps=2400,failed_trial_steps_observed=152,total_physics_steps_observed=2552,actor_inference_calls=0,training_updates=0,scope='Final saved-data audit only; no solver/native/analysis/plot rerun; quiet wrist next plan remains unexecuted'),indent=2)+'\n')
    files={p for p in P.rglob('*') if p.is_file() and p!=P/'artifact_inventory.json'}|set(sources)
    files-={A/'README.md',A/'PLAN.md',D/'VISUAL_REPORT.md'}
    inventory={str(p):dict(size=p.stat().st_size,sha256=sha(p)) for p in sorted(files,key=str)}
    (P/'artifact_inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
    assert all(Path(p).stat().st_size==v['size'] and sha(p)==v['sha256'] for p,v in inventory.items())
    print(json.dumps(dict(checks=len(checks),inventory_files=len(inventory),prior_declared_files_preserved=len(previous))))


if __name__=='__main__':main()
