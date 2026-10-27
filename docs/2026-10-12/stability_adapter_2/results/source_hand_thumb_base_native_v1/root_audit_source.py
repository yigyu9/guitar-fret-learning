"""Seal four actual native zero-step rejections without opening an audit log."""
from pathlib import Path
import hashlib
import json
import shutil

R = Path('/home/ajou/yigyu/3')
A = R/'stability_adapter_2'
D = R/'docs/2026-10-12/stability_adapter_2'
P = D/'results/source_hand_thumb_base_native_v1'


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text())


def main():
    assert not (P/'artifact_inventory.json').exists() and not (P/'final_verification.json').exists()
    checks = {}
    labels = [v['label'] for v in read(P/'proposal.json')['candidates']]
    assert labels == ['thumb1_x_minus005','thumb1_y_plus005','thumb1_x_minus010','thumb1_y_plus010']
    for stage in ['preparation','finish']+labels:
        record = read(P/(stage+'_execution.json'))
        expected = 1 if stage in labels else 0
        checks[stage+'_exit_input_current_SHA'] = record['exit_code'] == expected and record['input_sha256_before'] == record['input_sha256_after'] and all(sha(p) == h for p,h in record['input_sha256_before'].items())
        checks[stage+'_source_copies_exact'] = all(sha(p) == sha(v['snapshot']) == v['sha256'] for p,v in read(P/(stage+'_source_manifest.json')).items())
        checks[stage+'_log_exact'] = sha(P/(stage+'.log')) == record['log_sha256']
    batch = read(P/'native_batch.json')
    checks['four_initializations_zero_steps_no_selection'] = len(batch['attempts']) == 4 and batch['physical_initializations'] == 4 and batch['physical_steps'] == 0 and batch['selected'] is None
    checks['four_expected_geometry_terminals'] = all(v['terminal_state'] == 'initial_geometry_rejected_zero_steps' and v['exit_code'] == 1 and v['native_initializations'] == 1 and v['physics_steps'] == 0 and v['frame_count'] == 1 for v in batch['attempts'])
    analysis = read(P/'analysis.json')
    checks['saved35_checks_pass_no_stability_claim'] = len(analysis['checks']) == 35 and all(analysis['checks'].values()) and analysis['physical_initializations'] == 4 and analysis['physical_steps'] == 0 and analysis['five_second_stability_measured'] is False
    checks['all_native15_only_HG_fails'] = all(len(read(P/'native'/label/'initial_grip_audit.json')['checks']) == 15 and [n for n,v in read(P/'native'/label/'initial_grip_audit.json')['checks'].items() if not v] == ['source_human_guitar_clear'] for label in labels)
    checks['all_native_reports0step_and_png_exact'] = True
    for label in labels:
        native = P/'native'/label
        report = read(native/'report.json')
        capture = read(native/'capture.json')
        checks['all_native_reports0step_and_png_exact'] &= report['completed'] is False and report['physics_steps'] == 0 and report['native_initializations'] == 1 and len(capture['frames']) == 1 and capture['frames'][0]['render_preserves_states'] and all(sha(p) == h for key in ['image_sha256','raw_image_sha256'] for p,h in capture['frames'][0][key].items())
    record = read(P/'artifact_execution.json')
    checks['artifact_exit0_input_SHA_log'] = record['exit_code'] == 0 and record['input_sha256_before'] == record['input_sha256_after'] and all(sha(p) == h for p,h in record['input_sha256_before'].items()) and sha(P/'artifact.log') == record['log_sha256']
    copies = read(P/'artifact_source_manifest.json')['files']
    checks['artifact_source_copies_exact'] = all(sha(v['original_path']) == sha(v['copy_path']) == v['sha256'] == v['copy_sha256'] for v in copies)
    artifact = read(P/'artifacts/manifest.json')
    checks['artifact_png_exact_zero_physics'] = artifact['native_calls'] == artifact['physics_steps'] == artifact['actor_inference_calls'] == artifact['training_updates'] == 0 and all(sha(P/'artifacts'/p) == h for p,h in artifact['outputs_sha256'].items())
    for p,v in read(P/'journal_before.json').items():
        checks['append_only_'+Path(p).name] = hashlib.sha256(Path(p).read_bytes()[:v['size']]).hexdigest() == v['sha256']
    previous = {}
    inventories = [D/'results'/phase/'artifact_inventory.json' for phase in ['initial_middle3_alignment_v1','fixed_strap_source_compatibility_v1','no_strap_current_pose_v1','fixed_strap_source_hand_initial_v1']]
    inventories.append(D/'results/source_hand_thumb2_clearance_v2/artifact_inventory_v2.json')
    for inventory in inventories:
        for p,v in read(inventory).items():
            assert p not in previous or previous[p] == v
            previous[p] = v
    checks['all_prior_declared_files_preserved'] = all(Path(p).stat().st_size == v['size'] and sha(p) == v['sha256'] for p,v in previous.items())
    update = read(D/'video_collection_update_v12.json')
    checks['previous144_video_SHA_exact'] = len(update['previous_video_sha256']) == 144 and all(sha(p) == h for p,h in update['previous_video_sha256'].items())
    checks['all152_videos_eight_explicit_partials'] = len(list((D/'videos').glob('*.mp4'))) == update['total_count'] == 152 and len(update['copies']) == 8 and all(v['frames'] == 1 and v['physics_steps'] == 0 and 'ZERO_STEP_PARTIAL' in v['copy'] and sha(v['source']) == sha(v['copy']) == v['sha256'] for v in update['copies'])
    checks['indexes_exact'] = sha(D/'VIDEO_INDEX_v12.md') == update['previous_index_sha256'] and sha(D/'VIDEO_INDEX_v13.md') == update['new_index_sha256']
    checks['independent_review_PASS_exists'] = 'PASS' in (P/'review.md').read_text()
    assert all(checks.values()), checks
    sources = [A/n for n in ['SOURCE_HAND_THUMB_BASE_NATIVE_PLAN.md','SOURCE_HAND_WRIST_CLEARANCE_PLAN.md','run_thumb_base_candidate.py','run_thumb_base_native_phase.py','finish_thumb_base_native.py','make_thumb_base_native_artifacts.py','README.md','PLAN.md']]
    sources += [D/'VISUAL_REPORT.md',P/'README.md',P/'CHANGED_FILES.md',P/'ROOT_VERIFICATION_NOTES.md',P/'review.md',Path(__file__).resolve()]
    manifest = {}
    for p in sources:
        dest = P/'source_final'/p.relative_to(R)
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,dest)
        assert sha(dest) == sha(p)
        manifest[str(p)] = dict(snapshot=str(dest),sha256=sha(p))
    (P/'source_final_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    result = dict(checks=checks,prior_declared_files_preserved=len(previous),physical_initializations=4,physical_steps=0,actor_inference_calls=0,training_updates=0,five_second_stability_measured=False,scope='Four fresh native initial source-geometry rejections sealed; no repeated physics/solver/analysis/render in this audit')
    (P/'final_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    paths = {p for p in P.rglob('*') if p.is_file() and p != P/'artifact_inventory.json'}
    paths.update(sources)
    paths.update([D/'VIDEO_INDEX_v13.md',D/'video_collection_update_v12.json'])
    paths.update(Path(v['copy']) for v in update['copies'])
    paths.update(Path(v['trial_path']) for v in read(P/'proposal.json')['candidates'])
    paths -= {A/'README.md', A/'PLAN.md', D/'VISUAL_REPORT.md'}
    inventory = {str(p):dict(size=p.stat().st_size,sha256=sha(p)) for p in sorted(paths,key=str)}
    (P/'artifact_inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
    assert all(Path(p).stat().st_size == v['size'] and sha(p) == v['sha256'] for p,v in inventory.items())
    print(json.dumps(dict(checks=len(checks),inventory_files=len(inventory),prior_declared_files_preserved=len(previous))))


if __name__ == '__main__': main()
