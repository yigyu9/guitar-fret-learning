"""Seal the completed wrist response batch; no simulation or analysis rerun."""
from pathlib import Path
import hashlib
import json
import shutil

R=Path('/home/ajou/yigyu/3');A=R/'stability_adapter_2';D=R/'docs/2026-10-12/stability_adapter_2'
P=D/'results/quiet_wrist_support_authority_v1'


def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):Path(path).write_text(json.dumps(value,indent=2)+'\n')


def main():
    assert not (P/'final_verification.json').exists() and not (P/'artifact_inventory.json').exists()
    checks={}
    for condition in ['plus','minus']:
        e=read(P/(condition+'_execution.json'));m=read(P/(condition+'_source_manifest.json'))
        checks[condition+'_native_inputs_and_closed_log']=e['exit_code']==0 and e['terminal_state']=='completed' and len(e['input_sha256_before'])==103 and e['input_sha256_before']==e['input_sha256_after'] and all(sha(p)==h for p,h in e['input_sha256_before'].items()) and sha(P/(condition+'.log'))==e['log_sha256']
        checks[condition+'_103_source_copies_exact']=len(m)==103 and all(sha(p)==sha(v['snapshot'])==v['sha256'] for p,v in m.items())
        report=read(P/'native'/condition/'report.json');gate=read(P/'native'/condition/'initial_grip_audit.json')
        checks[condition+'_one_init_1200steps_151frames']=report['completed'] and report['failure'] is None and report['native_initialization_attempts']==report['native_initializations']==1 and report['physics_steps']==1200 and report['frame_count']==151 and all(report['checks'].values()) and not report['constraint_violations']
        checks[condition+'_15_fresh_gate_self1188']=len(gate['checks'])==15 and all(gate['checks'].values()) and gate['complete_source_self_screen']['pair_count']==1188
    analysis=read(P/'analysis.json')
    checks['saved_analysis_pass_2init_2400steps_no_actor_training']=bool(analysis['checks']) and all(analysis['checks'].values()) and analysis['physical_initializations']==2 and analysis['physical_steps']==2400 and analysis['actor_inference_calls']==analysis['training_updates']==0
    checks['analysis_direct_input_closure_exact']=analysis['input_sha256_before']==analysis['input_sha256_after'] and all(sha(p)==h for p,h in analysis['input_sha256_before'].items()) and set(analysis['input_sha256_before'])<=set(read(P/'analysis_execution.json')['input_sha256_before'])
    body=read(P/'body_motion.json')
    checks['body_motion7_saved_checks_and_source_exact']=len(body['checks'])==7 and all(body['checks'].values()) and body['input_sha256_before']==body['input_sha256_after'] and all(sha(p)==h for p,h in body['input_sha256_before'].items()) and sha(body['source_snapshot'])==sha(A/'analyze_quiet_wrist_body_motion.py') and body['native_calls']==body['physics_steps']==0
    for stage in ['analysis','collection','artifact']:
        e=read(P/(stage+'_execution.json'));m=read(P/(stage+'_source_manifest.json'))['files']
        checks[stage+'_exit0_current_inputs_closed_log']=e['exit_code']==0 and e['input_sha256_before']==e['input_sha256_after'] and all(sha(p)==h for p,h in e['input_sha256_before'].items()) and sha(P/(stage+'.log'))==e['log_sha256']
        checks[stage+'_selected_copies_exact']=all(sha(v['original_path'])==sha(v['copy_path'])==v['sha256']==v['copy_sha256'] for v in m)
    artifact=read(P/'artifacts/manifest.json')
    checks['plot_outputs_exact_no_new_physics']=artifact['native_calls']==artifact['physics_steps']==artifact['actor_inference_calls']==artifact['training_updates']==0 and artifact['inputs_sha256_before']==artifact['inputs_sha256_after'] and all(sha(p)==h for p,h in artifact['inputs_sha256_before'].items()) and all(sha(P/'artifacts'/p)==h for p,h in artifact['outputs_sha256'].items())
    update=read(D/'video_collection_update_v14.json')
    checks['162_videos_158_old_and_four_new_exact']=len(list((D/'videos').glob('*.mp4')))==update['total_count']==162 and len(update['previous_video_sha256'])==158 and all(sha(p)==h for p,h in update['previous_video_sha256'].items()) and len(update['copies'])==4 and all(not v['partial'] and sha(v['source'])==sha(v['copy'])==v['sha256']==v['copy_sha256'] for v in update['copies'])
    checks['old_and_new_indexes_exact']=sha(D/'VIDEO_INDEX_v14.md')==update['previous_index_sha256'] and sha(D/'VIDEO_INDEX_v15.md')==update['new_index_sha256']
    for p,v in read(P/'journal_before.json').items():
        checks['append_only_'+Path(p).name]=hashlib.sha256(Path(p).read_bytes()[:v['size']]).hexdigest()==v['sha256']
    previous={}
    names=['initial_middle3_alignment_v1','fixed_strap_source_compatibility_v1','no_strap_current_pose_v1','fixed_strap_source_hand_initial_v1','source_hand_thumb_base_native_v1','source_hand_wrist_clearance_v1','source_hand_arm_position_v1','source_hand_arm_continuous_v1','quiet_index_support_authority_v1']
    inventories=[D/'results'/n/'artifact_inventory.json' for n in names]+[D/'results/source_hand_thumb2_clearance_v2/artifact_inventory_v2.json']
    for inventory in inventories:
        for p,v in read(inventory).items():
            assert p not in previous or previous[p]==v
            previous[p]=v
    checks['previous_declared_files_exact']=all(Path(p).stat().st_size==v['size'] and sha(p)==v['sha256'] for p,v in previous.items())
    checks['independent_final_review_PASS']='최종 판정: PASS' in (P/'review.md').read_text()
    assert all(checks.values()),checks
    sources=[A/n for n in ['QUIET_WRIST_SUPPORT_AUTHORITY_PLAN.md','QUIET_WRIST_SUPPORT_EXECUTION.md','QUIET_WRIST_Z_SUPPORT_AUTHORITY_PLAN.md','analyze_quiet_wrist_body_motion.py','run_quiet_wrist_support.py','run_quiet_wrist_support_phase.py','analyze_quiet_wrist_support.py','run_quiet_wrist_postprocess.py','collect_quiet_wrist_videos.py','make_quiet_wrist_artifacts.py','README.md','PLAN.md']]
    sources += [D/'VISUAL_REPORT.md',D/'VIDEO_INDEX_v15.md',D/'video_collection_update_v14.json',P/'README.md',P/'CHANGED_FILES.md',P/'review.md',P/'ROOT_VERIFICATION_NOTES.md',Path(__file__).resolve()]
    manifest={}
    for path in sources:
        dest=P/'source_final'/path.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest);assert sha(dest)==sha(path)
        manifest[str(path)]=dict(snapshot=str(dest),sha256=sha(path))
    save(P/'source_final_manifest.json',manifest)
    save(P/'final_verification.json',dict(checks=checks,previous_declared_files_preserved=len(previous),physical_initializations=2,physics_steps=2400,actor_inference_calls=0,training_updates=0,scope='Saved-data audit only; no native, analysis, or plot rerun'))
    files={p for p in P.rglob('*') if p.is_file() and p!=P/'artifact_inventory.json'}|set(sources)
    files-={A/'README.md',A/'PLAN.md',D/'VISUAL_REPORT.md'}
    inventory={str(p):dict(size=p.stat().st_size,sha256=sha(p)) for p in sorted(files,key=str)}
    save(P/'artifact_inventory.json',inventory)
    assert all(Path(p).stat().st_size==v['size'] and sha(p)==v['sha256'] for p,v in inventory.items())
    print(json.dumps(dict(checks=len(checks),inventory_files=len(inventory),previous_declared_files_preserved=len(previous))))


if __name__=='__main__':main()
