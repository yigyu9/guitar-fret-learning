"""Seal the actual zero-step rejection, never claiming a completed stability trial."""
from pathlib import Path
import hashlib
import json
import shutil

R = Path('/home/ajou/yigyu/3')
A = R / 'stability_adapter_2'
D = R / 'docs/2026-10-12/stability_adapter_2'
P = D / 'results/fixed_strap_source_hand_initial_v1'


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text())


def main():
    assert not (P/'final_verification.json').exists() and not (P/'artifact_inventory.json').exists()
    checks = {}
    for stage, expected in [('preparation',0),('native',1),('finish',0)]:
        record = read(P/(stage+'_execution.json'))
        checks[stage+'_expected_exit_and_input_preservation'] = record['exit_code'] == expected and record['input_sha256_before'] == record['input_sha256_after'] and all(sha(p) == h for p,h in record['input_sha256_before'].items())
        checks[stage+'_log_exact'] = sha(P/(stage+'.log')) == record['log_sha256']
        checks[stage+'_source_copies_exact'] = all(sha(p) == sha(v['snapshot']) == v['sha256'] for p,v in read(P/(stage+'_source_manifest.json')).items())
    for p,info in read(P/'journal_before.json').items():
        checks['append_only_'+Path(p).name] = hashlib.sha256(Path(p).read_bytes()[:info['size']]).hexdigest() == info['sha256']
    old_paths = {}
    for phase in ['initial_middle3_alignment_v1','fixed_strap_source_compatibility_v1','no_strap_current_pose_v1']:
        for p,info in read(D/'results'/phase/'artifact_inventory.json').items():
            if p in old_paths: assert old_paths[p] == info
            old_paths[p] = info
    checks['prior_declared_inventory_files_preserved'] = all(Path(p).stat().st_size == v['size'] and sha(p) == v['sha256'] for p,v in old_paths.items())
    report,audit = read(P/'native/report.json'),read(P/'native/initial_grip_audit.json')
    checks['one_init_zero_steps_one_frame_rejected'] = report['native_initializations'] == 1 and report['physics_steps'] == 0 and report['simulation_elapsed_s'] == 0 and report['frame_count'] == 1 and report['completed'] is False
    checks['only_HG_fails_15_fresh_checks'] = len(audit['checks']) == 15 and [n for n,v in audit['checks'].items() if not v] == ['source_human_guitar_clear']
    checks['thumb2_source_intersection_only'] = len(audit['source_intersections']) == 1 and audit['source_intersections'][0]['human'] == 'LH:thumb2' and audit['source_intersections'][0]['guitar'] == 'guitar' and audit['source_intersections'][0]['common_radius_m'] == 0.004288364821171085
    checks['self1188_cross_clear'] = audit['complete_source_self_screen']['pair_count'] == 1188 and not audit['complete_source_self_screen']['intersections'] and not audit['cross_hand_intersections']
    analysis = read(P/'analysis.json')
    checks['15_saved_checks_pass_no_stability_claim'] = len(analysis['checks']) == 15 and all(analysis['checks'].values()) and analysis['physical_steps'] == 0 and analysis['five_second_stability_measured'] is False
    frames = read(P/'native/capture.json')['frames']
    checks['four_raw_overlay_PNG_exact'] = len(frames) == 1 and frames[0]['render_preserves_states'] and sum(len(frames[0][k]) for k in ['image_sha256','raw_image_sha256']) == 4 and all(sha(p) == h for k in ['image_sha256','raw_image_sha256'] for p,h in frames[0][k].items())
    update = read(D/'video_collection_update_v11.json')
    checks['previous142_videos_exact'] = len(update['previous_video_sha256']) == 142 and all(sha(p) == h for p,h in update['previous_video_sha256'].items())
    checks['144_videos_two_explicit_partial_copies'] = len(list((D/'videos').glob('*.mp4'))) == update['total_count'] == 144 and len(update['copies']) == 2 and all(v['physics_steps'] == 0 and v['frames'] == 1 and 'ZERO_STEP_PARTIAL' in v['copy'] and sha(v['source']) == sha(v['copy']) == v['sha256'] for v in update['copies'])
    checks['old_new_indexes_exact'] = sha(D/'VIDEO_INDEX_v11.md') == update['previous_index_sha256'] and sha(D/'VIDEO_INDEX_v12.md') == update['new_index_sha256']
    checks['review_PASS_exists'] = (P/'review.md').is_file() and 'PASS' in (P/'review.md').read_text()
    assert all(checks.values()),checks
    sources = [A/n for n in ['FIXED_STRAP_SOURCE_HAND_INITIAL_PLAN.md','SOURCE_HAND_INITIAL_EXECUTION.md',
        'SOURCE_HAND_THUMB2_CLEARANCE_PLAN.md','prepare_source_hand_initial.py','run_source_hand_initial.py',
        'run_source_hand_initial_phase.py','finish_source_hand_initial.py','README.md','PLAN.md']]
    sources += [D/'VISUAL_REPORT.md',P/'README.md',P/'CHANGED_FILES.md',P/'ROOT_VERIFICATION_NOTES.md',P/'review.md',Path(__file__).resolve()]
    manifest = {}
    for p in sources:
        dest = P/'source_final'/p.relative_to(R)
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
        assert sha(dest) == sha(p)
        manifest[str(p)] = dict(snapshot=str(dest),sha256=sha(p))
    (P/'source_final_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    result = dict(checks=checks,prior_declared_files_preserved=len(old_paths),
        physical_initializations=1,physical_steps=0,actor_inference_calls=0,training_updates=0,
        five_second_stability_measured=False,scope='Expected initial source geometry rejection sealed; no trial or analysis rerun; LP common radius is not physical penetration depth')
    (P/'final_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    paths = [p for p in P.rglob('*') if p.is_file() and p != P/'artifact_inventory.json']
    paths += sources + [D/'VIDEO_INDEX_v12.md',D/'video_collection_update_v11.json'] + [Path(v['copy']) for v in update['copies']]
    journals = {A/'README.md',A/'PLAN.md',D/'VISUAL_REPORT.md'}
    inventory = {str(p):dict(size=p.stat().st_size,sha256=sha(p)) for p in sorted(set(paths)-journals,key=str)}
    (P/'artifact_inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
    print(json.dumps(dict(checks=len(checks),inventory_files=len(inventory),prior_declared_files_preserved=len(old_paths))))


if __name__ == '__main__': main()
