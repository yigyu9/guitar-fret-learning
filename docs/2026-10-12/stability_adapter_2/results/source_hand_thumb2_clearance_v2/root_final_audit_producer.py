"""Seal the source-only sweep and preserve the preceding failed attempt."""
from pathlib import Path
import hashlib
import json
import shutil

R = Path('/home/ajou/yigyu/3')
A = R / 'stability_adapter_2'
D = R / 'docs/2026-10-12/stability_adapter_2'
P = D / 'results/source_hand_thumb2_clearance_v2'
V1 = D / 'results/source_hand_thumb2_clearance_v1'


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text())


def main():
    assert not (P/'final_verification.json').exists()
    assert not (P/'artifact_inventory.json').exists()
    checks = {}
    for phase, expected in [(V1, 1), (P, 0)]:
        tag = phase.name
        record = read(phase/'search_execution.json')
        checks[tag+'_search_exit_inputs_current'] = record['exit_code'] == expected and record['input_sha256_before'] == record['input_sha256_after'] and all(sha(p) == h for p,h in record['input_sha256_before'].items())
        checks[tag+'_search_log_exact'] = sha(phase/'search.log') == record['log_sha256']
        copies = read(phase/'search_source_manifest.json')
        checks[tag+'_source_copies_exact'] = all(sha(p) == sha(v['snapshot']) == v['sha256'] for p,v in copies.items())
        checks[tag+'_no_native_or_candidate'] = all(not (phase/n).exists() for n in ['proposal.json','native','native_execution.json'])
        for p,info in read(phase/'journal_before.json').items():
            checks[tag+'_append_only_'+Path(p).name] = hashlib.sha256(Path(p).read_bytes()[:info['size']]).hexdigest() == info['sha256']
    checks['v1_failed_v2_completed'] = read(V1/'search_execution.json')['terminal_state'] == 'error' and not (V1/'search.json').exists() and read(P/'search_execution.json')['terminal_state'] == 'completed'
    data = read(P/'search.json')
    rows = data['rows']
    checks['eight_source_checks_seven_rows'] = len(data['checks']) == 8 and all(data['checks'].values()) and len(rows) == 7
    checks['all_seven_HG_overlap_only_no_selection'] = data['selected'] is None and all(v['source_clear'] is False and len(v['source_human_guitar_intersections']) == 1 and v['source_human_guitar_intersections'][0]['a'] == 'LH:thumb2' and v['source_human_guitar_intersections'][0]['b'] == 'guitar' and v['source_human_guitar_intersections'][0]['common_radius_m'] > 1e-7 for v in rows)
    checks['all_self1188_cross_clear_pose_range_up'] = all(v['self_pair_count'] == 1188 and not v['source_self_intersections'] and not v['source_cross_hand_intersections'] and v['other_pose_identity'] and v['within_effective_range'] and v['palm_up_proxy_z'] > 0 for v in rows)
    checks['source_only_no_physics'] = data['native_initializations'] == data['physics_steps'] == 0
    record = read(P/'artifact_execution.json')
    checks['artifact_completed_input_preserved'] = record['exit_code'] == 0 and record['terminal_state'] == 'completed' and record['input_sha256_before'] == record['input_sha256_after'] and all(sha(p) == h for p,h in record['input_sha256_before'].items())
    checks['artifact_log_exact'] = sha(P/'artifact.log') == record['log_sha256']
    copies = read(P/'artifact_source_manifest.json')['files']
    checks['artifact_source_copies_exact'] = all(sha(v['original_path']) == sha(v['copy_path']) == v['sha256'] == v['copy_sha256'] for v in copies)
    manifest = read(P/'artifacts/manifest.json')
    checks['artifact_seven_rows_zero_physics_png_exact'] = manifest['rows_plotted'] == 7 and manifest['native_calls'] == manifest['physics_steps'] == manifest['actor_inference_calls'] == manifest['training_updates'] == 0 and all(sha(P/'artifacts'/p) == h for p,h in manifest['outputs_sha256'].items())
    previous = {}
    for phase in ['initial_middle3_alignment_v1','fixed_strap_source_compatibility_v1','no_strap_current_pose_v1','fixed_strap_source_hand_initial_v1']:
        for p,v in read(D/'results'/phase/'artifact_inventory.json').items():
            assert p not in previous or previous[p] == v
            previous[p] = v
    checks['all_prior_declared_files_preserved'] = all(Path(p).stat().st_size == v['size'] and sha(p) == v['sha256'] for p,v in previous.items())
    update = read(D/'video_collection_update_v11.json')
    checks['all144_videos_preserved'] = len(list((D/'videos').glob('*.mp4'))) == update['total_count'] == 144 and len(update['previous_video_sha256']) == 142 and all(sha(p) == h for p,h in update['previous_video_sha256'].items()) and len(update['copies']) == 2 and all(sha(v['source']) == sha(v['copy']) == v['sha256'] for v in update['copies'])
    checks['video_indexes_preserved'] = sha(D/'VIDEO_INDEX_v11.md') == update['previous_index_sha256'] and sha(D/'VIDEO_INDEX_v12.md') == update['new_index_sha256']
    checks['independent_review_PASS'] = 'PASS' in (P/'review.md').read_text() and 'PASS' in (V1/'review.md').read_text()
    assert all(checks.values()), checks
    sources = [A/n for n in ['search_thumb2_clearance.py','run_thumb2_clearance_phase.py','search_thumb2_clearance_v2.py','run_thumb2_clearance_phase_v2.py','make_thumb2_clearance_artifacts.py','SOURCE_HAND_THUMB2_CLEARANCE_PLAN.md','THUMB2_CLEARANCE_V2_EXECUTION.md','SOURCE_HAND_THUMB_BASE_NATIVE_PLAN.md','README.md','PLAN.md']]
    sources += [D/'VISUAL_REPORT.md', P/'README.md', P/'CHANGED_FILES.md', P/'ROOT_VERIFICATION_NOTES.md', P/'review.md', Path(__file__).resolve()]
    saved = {}
    for p in sources:
        dest = P/'source_final'/p.relative_to(R)
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,dest)
        assert sha(dest) == sha(p)
        saved[str(p)] = dict(snapshot=str(dest),sha256=sha(p))
    (P/'source_final_manifest.json').write_text(json.dumps(saved,indent=2)+'\n')
    result = dict(checks=checks, prior_declared_files_preserved=len(previous), native_initializations=0, physical_steps=0, actor_inference_calls=0, training_updates=0, five_second_stability_measured=False, scope='Saved static source results only; v1 failure preserved; no new simulation or solver execution in this audit')
    (P/'final_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    files = [p for phase in [P,V1] for p in phase.rglob('*') if p.is_file() and p != P/'artifact_inventory.json']
    journals = {A/'README.md', A/'PLAN.md', D/'VISUAL_REPORT.md'}
    inventory = {str(p):dict(size=p.stat().st_size,sha256=sha(p)) for p in sorted((set(files)|set(sources))-journals,key=str)}
    (P/'artifact_inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
    print(json.dumps(dict(checks=len(checks),inventory_files=len(inventory),prior_declared_files_preserved=len(previous))))


if __name__ == '__main__': main()
