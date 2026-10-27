"""Finalize this no-strap comparison without rerunning physics or analysis."""
from pathlib import Path
import hashlib
import json
import shutil

R = Path('/home/ajou/yigyu/3')
A = R / 'stability_adapter_2'
D = R / 'docs/2026-10-12/stability_adapter_2'
P = D / 'results/no_strap_current_pose_v1'


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text())


def main():
    assert not (P / 'final_verification.json').exists() and not (P / 'artifact_inventory.json').exists()
    checks = {}
    for stage, filename in [('native', 'execution.json'), ('analysis', 'analysis_execution.json'), ('collection', 'collection_execution.json')]:
        execution = read(P / filename)
        checks[stage + '_exit0_inputs_preserved'] = execution['exit_code'] == 0 and execution['input_sha256_before'] == execution['input_sha256_after'] and all(sha(p) == h for p,h in execution['input_sha256_before'].items())
        log = 'native.log' if stage == 'native' else stage + '.log'
        checks[stage + '_log_preserved'] = sha(P / log) == execution['log_sha256']
        name = 'source_snapshot.json' if stage == 'native' else stage + '_source_manifest.json'
        checks[stage + '_source_copies_exact'] = all(sha(v['snapshot']) == sha(p) == v['sha256'] for p,v in read(P / name).items())
    analysis = read(P / 'analysis.json')
    checks['all20_analysis_checks_pass'] = len(analysis['checks']) == 20 and all(analysis['checks'].values())
    checks['compared_initial_fields_actual_count20'] = len(analysis['compared_initial_fields']) == 20
    strap = A / 'strap.py'
    checks['transitive_strap_helper_preserved'] = sha(strap) == read(P / 'execution.json')['input_sha256_before'][str(strap)]
    for p, info in read(P / 'journal_before.json').items():
        checks['append_only_' + Path(p).name] = hashlib.sha256(Path(p).read_bytes()[:info['size']]).hexdigest() == info['sha256']
    old_paths = {}
    for phase in ['initial_middle3_alignment_v1', 'fixed_strap_source_compatibility_v1']:
        for p, info in read(D / 'results' / phase / 'artifact_inventory.json').items():
            if p in old_paths: assert old_paths[p] == info
            old_paths[p] = info
    checks['prior_declared_inventories_preserved'] = all(Path(p).stat().st_size == v['size'] and sha(p) == v['sha256'] for p,v in old_paths.items())
    update = read(D / 'video_collection_update_v10.json')
    checks['previous140_videos_exact'] = len(update['previous_video_sha256']) == 140 and all(sha(p) == h for p,h in update['previous_video_sha256'].items())
    checks['142_videos_and_new_copies_exact'] = len(list((D / 'videos').glob('*.mp4'))) == update['total_count'] == 142 and len(update['copies']) == 2 and all(sha(v['source']) == sha(v['copy']) == v['sha256'] for v in update['copies'])
    checks['video_indexes_preserved'] = sha(D / 'VIDEO_INDEX_v10.md') == update['previous_index_sha256'] and sha(D / 'VIDEO_INDEX_v11.md') == update['new_index_sha256']
    mode = read(P / 'native/no_strap_mode.json')
    checks['no_body_force_calls_1200_steps'] = mode['explicit_body_force_API_attempts'] == 0 and mode['completed_physics_steps'] == 1200 and mode['strap_enabled'] is mode['strap_rendered'] is False
    trace = [json.loads(line) for line in (P / 'native/trace.jsonl').read_text().splitlines()]
    checks['1201_applied_tensions_zero'] = len(trace) == 1201 and all(t['last_applied_tension_n'] == 0 and t['finite'] for t in trace)
    report = read(P / 'native/report.json')
    checks['actual5s_no_constraint_violations'] = report['completed'] and report['physics_steps'] == 1200 and report['simulation_elapsed_s'] == 5 and report['frame_count'] == 151 and not report['constraint_violations']
    frames = read(P / 'native/capture.json')['frames']
    checks['all302_native_PNG_exact'] = len(frames) == 151 and sum(len(f['image_sha256']) for f in frames) == 302 and all(sha(p) == h for f in frames for p,h in f['image_sha256'].items())
    checks['independent_review_exists'] = (P / 'review.md').is_file() and 'PASS' in (P / 'review.md').read_text()
    assert all(checks.values()), checks
    final_inputs = [A / n for n in ['NO_STRAP_VIDEO_PLAN.md', 'run_no_strap_current_pose.py', 'run_no_strap_video_phase.py', 'analyze_no_strap_video.py', 'collect_no_strap_videos.py', 'run_no_strap_postprocess.py', 'strap.py', 'README.md', 'PLAN.md']]
    final_inputs += [D / 'VISUAL_REPORT.md', P / 'README.md', P / 'CHANGED_FILES.md', P / 'review.md', P / 'ROOT_VERIFICATION_NOTES.md', Path(__file__).resolve()]
    manifest = {}
    for p in final_inputs:
        dest = P / 'source_final' / p.relative_to(R)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)
        assert sha(dest) == sha(p)
        manifest[str(p)] = dict(snapshot=str(dest), sha256=sha(p))
    (P / 'source_final_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    result = dict(checks=checks, prior_declared_files_preserved=len(old_paths),
        input_counts={n:len(read(P / f)['input_sha256_before']) for n,f in [('native','execution.json'),('analysis','analysis_execution.json'),('collection','collection_execution.json')]},
        physical_initializations=1, physical_steps=1200, actor_inference_calls=0, training_updates=0,
        notes='all21_initial_fields_exact is a preserved legacy label; actual compared list contains20 fields. strap.py transitive import supplemented from immutable native input closure; no consumed source/output edited. No additional physics or analysis execution in final audit.')
    (P / 'final_verification.json').write_text(json.dumps(result, indent=2) + '\n')
    outputs = [p for p in P.rglob('*') if p.is_file() and p != P / 'artifact_inventory.json']
    outputs += final_inputs + [D / 'VIDEO_INDEX_v11.md', D / 'video_collection_update_v10.json'] + [Path(v['copy']) for v in update['copies']]
    journals = {A / 'README.md', A / 'PLAN.md', D / 'VISUAL_REPORT.md'}
    inventory = {str(p):dict(size=p.stat().st_size, sha256=sha(p)) for p in sorted(set(outputs) - journals, key=str)}
    (P / 'artifact_inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
    print(json.dumps(dict(checks=len(checks), inventory_files=len(inventory), prior_declared_files_preserved=len(old_paths))))


if __name__ == '__main__': main()
