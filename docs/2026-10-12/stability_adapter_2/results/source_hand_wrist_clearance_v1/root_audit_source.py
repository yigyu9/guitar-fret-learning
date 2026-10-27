"""Seal thirteen source hypotheses without claiming native or stability success."""
from pathlib import Path
import hashlib
import json
import shutil

R = Path('/home/ajou/yigyu/3')
A = R/'stability_adapter_2'
D = R/'docs/2026-10-12/stability_adapter_2'
P = D/'results/source_hand_wrist_clearance_v1'


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text())


def main():
    assert not (P/'artifact_inventory.json').exists() and not (P/'final_verification.json').exists()
    checks={}
    record=read(P/'search_execution.json')
    checks['search_exit0_69_current_inputs_preserved']=record['exit_code']==0 and record['terminal_state']=='completed' and len(record['input_sha256_before'])==69 and record['input_sha256_before']==record['input_sha256_after'] and all(sha(p)==h for p,h in record['input_sha256_before'].items())
    checks['search_log_exact']=sha(P/'search.log')==record['log_sha256']
    copies=read(P/'search_source_manifest.json')
    checks['all69_source_copies_exact']=len(copies)==69 and all(sha(p)==sha(v['snapshot'])==v['sha256'] for p,v in copies.items())
    data=read(P/'search.json'); rows=data['rows']
    checks['eight_checks_thirteen_rows']=len(data['checks'])==8 and all(data['checks'].values()) and len(rows)==13
    checks['all13_thumb2_intersections_no_selection']=data['selected'] is None and all(v['source_clear'] is False and any(x['a']=='LH:thumb2' and x['b']=='guitar' and x['common_radius_m']>1e-7 for x in v['source_human_guitar_intersections']) for v in rows)
    checks['all13_range_offset_identity_up_self1188_cross']=all(v['within_effective_ranges'] and v['other80_q_and_held_exact'] and v['upper_arm_identity'] and v['other_meshes_identity'] and v['hand_relative_identity'] and v['palm_up_proxy_z']>0 and v['self_pair_count']==1188 and not v['source_self_intersections'] and not v['source_cross_hand_intersections'] for v in rows)
    checks['wrist_subtree23_active17']=len(data['moving_body_names'])==23 and len(data['moving_collision_body_names'])==17
    checks['no_candidate_or_native_zero_physics']=data['native_initializations']==data['physics_steps']==0 and all(not (P/n).exists() for n in ['proposal.json','source_prediction.json','native','native_execution.json'])
    record=read(P/'artifact_execution.json')
    checks['artifact_exit0_inputs_current_log']=record['exit_code']==0 and record['input_sha256_before']==record['input_sha256_after'] and all(sha(p)==h for p,h in record['input_sha256_before'].items()) and sha(P/'artifact.log')==record['log_sha256']
    copies=read(P/'artifact_source_manifest.json')['files']
    checks['artifact_source_copies_exact']=all(sha(v['original_path'])==sha(v['copy_path'])==v['sha256']==v['copy_sha256'] for v in copies)
    artifact=read(P/'artifacts/manifest.json')
    checks['artifact_png_exact_zero_physics']=artifact['native_calls']==artifact['physics_steps']==artifact['actor_inference_calls']==artifact['training_updates']==0 and all(sha(P/'artifacts'/p)==h for p,h in artifact['outputs_sha256'].items())
    for p,v in read(P/'journal_before.json').items():
        checks['append_only_'+Path(p).name]=hashlib.sha256(Path(p).read_bytes()[:v['size']]).hexdigest()==v['sha256']
    previous={}
    inventories=[D/'results'/n/'artifact_inventory.json' for n in ['initial_middle3_alignment_v1','fixed_strap_source_compatibility_v1','no_strap_current_pose_v1','fixed_strap_source_hand_initial_v1','source_hand_thumb_base_native_v1']]
    inventories.append(D/'results/source_hand_thumb2_clearance_v2/artifact_inventory_v2.json')
    for inventory in inventories:
        for p,v in read(inventory).items():
            assert p not in previous or previous[p]==v
            previous[p]=v
    checks['all_previous_declared_files_exact']=all(Path(p).stat().st_size==v['size'] and sha(p)==v['sha256'] for p,v in previous.items())
    update=read(D/'video_collection_update_v12.json')
    checks['all152_videos_preserved']=len(list((D/'videos').glob('*.mp4')))==update['total_count']==152 and len(update['previous_video_sha256'])==144 and all(sha(p)==h for p,h in update['previous_video_sha256'].items()) and len(update['copies'])==8 and all(sha(v['source'])==sha(v['copy'])==v['sha256'] for v in update['copies'])
    checks['video_indexes_exact']=sha(D/'VIDEO_INDEX_v12.md')==update['previous_index_sha256'] and sha(D/'VIDEO_INDEX_v13.md')==update['new_index_sha256']
    checks['independent_review_PASS']='PASS' in (P/'review.md').read_text()
    assert all(checks.values()),checks
    sources=[A/n for n in ['SOURCE_HAND_WRIST_CLEARANCE_PLAN.md','SOURCE_HAND_ARM_POSITION_PLAN.md','search_wrist_clearance.py','run_wrist_clearance_phase.py','run_wrist_clearance_candidate.py','make_wrist_clearance_artifacts.py','README.md','PLAN.md']]
    sources += [D/'VISUAL_REPORT.md',P/'README.md',P/'CHANGED_FILES.md',P/'ROOT_VERIFICATION_NOTES.md',P/'review.md',Path(__file__).resolve()]
    manifest={}
    for p in sources:
        dest=P/'source_final'/p.relative_to(R)
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
        assert sha(dest)==sha(p)
        manifest[str(p)]=dict(snapshot=str(dest),sha256=sha(p))
    (P/'source_final_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    result=dict(checks=checks,prior_declared_files_preserved=len(previous),physical_initializations=0,physical_steps=0,actor_inference_calls=0,training_updates=0,five_second_stability_measured=False,scope='Thirteen conditional source wrist results sealed; no new native/solver/render/analysis execution in final audit')
    (P/'final_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    files={p for p in P.rglob('*') if p.is_file() and p!=P/'artifact_inventory.json'}|set(sources)
    files -= {A/'README.md',A/'PLAN.md',D/'VISUAL_REPORT.md'}
    inventory={str(p):dict(size=p.stat().st_size,sha256=sha(p)) for p in sorted(files,key=str)}
    (P/'artifact_inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
    assert all(Path(p).stat().st_size==v['size'] and sha(p)==v['sha256'] for p,v in inventory.items())
    print(json.dumps(dict(checks=len(checks),inventory_files=len(inventory),prior_declared_files_preserved=len(previous))))


if __name__ == '__main__':main()
