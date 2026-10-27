"""Seal saved feedback results, including the preserved collection failure."""
from pathlib import Path
import hashlib
import json
import shutil

R=Path('/home/ajou/yigyu/3');A=R/'stability_adapter_2';D=R/'docs/2026-10-12/stability_adapter_2'
P=D/'results/quiet_wrist_yz_feedback_v1'


def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):Path(p).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def current(v):return v['input_sha256_before']==v['input_sha256_after'] and all(sha(p)==h for p,h in v['input_sha256_before'].items())


def main():
    assert not any((P/n).exists() for n in ['final_verification.json','artifact_inventory.json','source_final_manifest.json','source_final'])
    checks={}
    preflight=read(P/'preflight.json')
    checks['preflight12_current_and_snapshot_exact']=len(preflight['checks'])==12 and all(preflight['checks'].values()) and current(preflight) and sha(P/'preflight_source.py')==sha(A/'preflight_wrist_yz_feedback.py') and preflight['native_initializations']==preflight['physics_steps']==0
    for condition in ['off','on']:
        e=read(P/(condition+'_execution.json'));m=read(P/(condition+'_source_manifest.json'))
        checks[condition+'_native_inputs_and_closed_log']=e['exit_code']==0 and e['terminal_state']=='completed' and len(e['input_sha256_before'])==106 and current(e) and sha(P/(condition+'.log'))==e['log_sha256']
        checks[condition+'_106_source_copies_exact']=len(m)==106 and all(sha(p)==sha(v['snapshot'])==v['sha256'] for p,v in m.items())
        report=read(P/'native'/condition/'report.json');gate=read(P/'native'/condition/'initial_grip_audit.json')
        checks[condition+'_one_init_1200steps_151frames']=report['completed'] and report['failure'] is None and report['native_initialization_attempts']==report['native_initializations']==1 and report['physics_steps']==1200 and report['frame_count']==151 and all(report['checks'].values()) and not report['constraint_violations']
        checks[condition+'_15_fresh_gate_self1188']=len(gate['checks'])==15 and all(gate['checks'].values()) and gate['complete_source_self_screen']['pair_count']==1188
    analysis=read(P/'analysis.json')
    checks['saved_analysis56_pass_two_init_2400steps_no_actor']=len(analysis['checks'])==56 and all(analysis['checks'].values()) and current(analysis) and analysis['physical_initializations']==2 and analysis['physical_steps']==2400 and analysis['actor_inference_calls']==analysis['training_updates']==0
    checks['analysis_direct_inputs_within_wrapper']=set(analysis['input_sha256_before'])<=set(read(P/'analysis_execution.json')['input_sha256_before'])
    for stage in ['analysis','artifact']:
        e=read(P/(stage+'_execution.json'));m=read(P/(stage+'_source_manifest.json'))['files']
        checks[stage+'_exit0_current_inputs_closed_log']=e['exit_code']==0 and current(e) and sha(P/(stage+'.log'))==e['log_sha256']
        checks[stage+'_selected_copies_exact']=all(sha(v['original_path'])==sha(v['copy_path'])==v['sha256'] for v in m)
    recovery=read(P/'collection_recovery.json');failure=read(P/'collection_wrapper_failure.json')
    checks['collection_failure_preserved_recovery9_current_exact']=len(recovery['checks'])==9 and all(recovery['checks'].values()) and current(recovery) and recovery['wrapper_terminal_exit_code']==failure['wrapper_terminal_exit_code']==1 and recovery['collector_exit_code'] is failure['collector_exit_code'] is None and recovery['collector_wall_seconds'] is failure['collector_wall_seconds'] is None and recovery['collector_reruns']==recovery['native_calls']==recovery['physics_steps']==0 and not (P/'collection_execution.json').exists()
    checks['recovery_source_snapshot_exact']=sha(P/'collection_recovery_source.py')==sha(A/'audit_wrist_yz_collection_recovery.py')
    artifact=read(P/'artifacts/manifest.json')
    checks['plot_outputs_exact_no_new_physics']=artifact['native_calls']==artifact['physics_steps']==artifact['actor_inference_calls']==artifact['training_updates']==0 and artifact['inputs_sha256_before']==artifact['inputs_sha256_after'] and all(sha(p)==h for p,h in artifact['inputs_sha256_before'].items()) and all(sha(P/'artifacts'/p)==h for p,h in artifact['outputs_sha256'].items())
    update=read(D/'video_collection_update_v16.json')
    checks['170_videos_166_old_and_four_new_exact']=len(list((D/'videos').glob('*.mp4')))==update['total_count']==170 and len(update['previous_video_sha256'])==166 and all(sha(p)==h for p,h in update['previous_video_sha256'].items()) and len(update['copies'])==4 and all(not v['partial'] and sha(v['source'])==sha(v['copy'])==v['sha256']==v['copy_sha256'] for v in update['copies'])
    checks['old_and_new_indexes_exact']=sha(D/'VIDEO_INDEX_v16.md')==update['previous_index_sha256'] and sha(D/'VIDEO_INDEX_v17.md')==update['new_index_sha256']
    for p,v in read(P/'journal_before.json').items():
        checks['append_only_'+Path(p).name]=hashlib.sha256(Path(p).read_bytes()[:v['size']]).hexdigest()==v['sha256']
    previous={}
    names=['initial_middle3_alignment_v1','fixed_strap_source_compatibility_v1','no_strap_current_pose_v1','fixed_strap_source_hand_initial_v1','source_hand_thumb_base_native_v1','source_hand_wrist_clearance_v1','source_hand_arm_position_v1','source_hand_arm_continuous_v1','quiet_index_support_authority_v1','quiet_wrist_support_authority_v1','quiet_wrist_z_support_authority_v1']
    inventories=[D/'results'/n/'artifact_inventory.json' for n in names]+[D/'results/source_hand_thumb2_clearance_v2/artifact_inventory_v2.json']
    for inventory in inventories:
        for p,v in read(inventory).items():
            assert p not in previous or previous[p]==v
            previous[p]=v
    checks['previous_declared_files_exact']=all(Path(p).stat().st_size==v['size'] and sha(p)==v['sha256'] for p,v in previous.items())
    checks['independent_final_review_PASS']='최종 판정: PASS' in (P/'review.md').read_text()
    assert all(checks.values()),checks
    sources=[A/n for n in ['QUIET_WRIST_YZ_FEEDBACK_PLAN.md','QUIET_WRIST_YZ_FEEDBACK_EXECUTION.md','QUIET_WRIST_YZ_STARTUP_FEEDBACK_PLAN.md','wrist_yz_guitar_feedback.py','run_quiet_wrist_yz_feedback.py','run_quiet_wrist_yz_feedback_phase.py','preflight_wrist_yz_feedback.py','analyze_quiet_wrist_yz_feedback.py','run_wrist_yz_feedback_analysis.py','make_wrist_yz_feedback_artifacts.py','collect_wrist_yz_feedback_videos.py','audit_wrist_yz_collection_recovery.py','README.md','PLAN.md']]
    sources += [D/'VISUAL_REPORT.md',D/'VIDEO_INDEX_v17.md',D/'video_collection_update_v16.json',P/'README.md',P/'CHANGED_FILES.md',P/'review.md',P/'ROOT_VERIFICATION_NOTES.md',Path(__file__).resolve()]
    sources += [Path(v['copy']) for v in update['copies']]
    manifest={}
    for path in sources:
        dest=P/'source_final'/path.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest);assert sha(dest)==sha(path)
        manifest[str(path)]=dict(snapshot=str(dest),sha256=sha(path))
    save(P/'source_final_manifest.json',manifest)
    save(P/'final_verification.json',dict(checks=checks,previous_declared_files_preserved=len(previous),physical_initializations=2,physics_steps=2400,actor_inference_calls=0,training_updates=0,collection_wrapper_exit_code=1,collector_exit_code=None,collector_reruns=0,scope='Saved-data audit; collection failure and unknown original collector status remain preserved; no rerun'))
    files={p for p in P.rglob('*') if p.is_file() and p!=P/'artifact_inventory.json'}|set(sources)
    files-={A/'README.md',A/'PLAN.md',D/'VISUAL_REPORT.md'}
    inventory={str(p):dict(size=p.stat().st_size,sha256=sha(p)) for p in sorted(files,key=str)}
    save(P/'artifact_inventory.json',inventory)
    assert all(Path(p).stat().st_size==v['size'] and sha(p)==v['sha256'] for p,v in inventory.items())
    print(json.dumps(dict(checks=len(checks),inventory_files=len(inventory),previous_declared_files_preserved=len(previous))))


if __name__=='__main__':main()
