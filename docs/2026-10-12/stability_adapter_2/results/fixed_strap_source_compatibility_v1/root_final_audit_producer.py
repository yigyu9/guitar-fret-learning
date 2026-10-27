from pathlib import Path
import ast
import hashlib
import json
import math
import re
import shutil

R = Path('/home/ajou/yigyu/3')
A = R / 'stability_adapter_2'
D = R / 'docs/2026-10-12/stability_adapter_2'
B = D / 'results'
P = B / 'fixed_strap_source_compatibility_v1'
AR = P / 'artifacts'
checks, cache = {}, {}


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    path = Path(path)
    if str(path) not in cache:
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1048576), b''):
                digest.update(block)
        cache[str(path)] = digest.hexdigest()
    return cache[str(path)]


def check(name, value):
    assert value, name
    checks[name] = True


def closure(mapping):
    return all(sha(path) == digest for path, digest in mapping.items())


assert not (P / 'final_verification.json').exists()
assert not (P / 'artifact_inventory.json').exists()
check('audit_prearchived_exact', sha(__file__) == sha(P / 'root_final_audit_producer.py'))
result, execution = read(P / 'compatibility.json'), read(P / 'execution.json')
snapshot = read(P / 'source_snapshot.json')
check('cpu34_checks_and48_input_closure_exact', len(result['checks']) == 34 and all(result['checks'].values()) and len(result['input_sha256_before']) == 48 and result['input_sha256_before'] == result['input_sha256_after'] == execution['input_sha256_before'] == execution['input_sha256_after'] and closure(result['input_sha256_before']))
check('cpu48_snapshot_copies_exact', len(snapshot) == 48 and all(sha(path) == sha(record['snapshot']) == record['sha256'] for path, record in snapshot.items()))
check('cpu_exit0_handoff_and_log_exact', execution['exit_code'] == 0 and sha(P / 'analysis.log') == execution['log_sha256'] and sha(P / 'input_sha256_before.json') == execution['input_manifest_sha256_before'] == execution['input_manifest_sha256_after'] and read(P / 'input_sha256_before.json') == result['input_sha256_before'])
check('cpu_no_native_physics_actor_training', all(result[key] == 0 for key in ['native_initializations', 'physics_steps', 'actor_inference_calls', 'training_updates']))
rows = [json.loads(line) for line in (P / 'joint_ranges.jsonl').read_text().splitlines()]
check('810_finite_range_rows_native_within', len(rows) == result['joint_row_count'] == 810 and all(math.isfinite(row['current_rad']) and row['native_lower_rad'] <= row['current_rad'] <= row['native_upper_rad'] for row in rows))
check('signed_minimum_change_reference_only_consistent', all(row['signed_minimum_change_rad'] == row['nearest_reference_rad'] - row['current_rad'] and row['nearest_reference_rad'] == min(row['effective_upper_rad'], max(row['effective_lower_rad'], row['current_rad'])) and row['outside_effective_range'] == (row['signed_minimum_change_rad'] != 0) and row['minimum_change_deg'] == math.degrees(abs(row['signed_minimum_change_rad'])) for row in rows))
for summary in result['summary']:
    label = summary['label']
    for kind, metrics in summary['ranges'].items():
        local = [row for row in rows if row['label'] == label and row['kind'] == kind]
        check(label + '_' + kind + '_summary_exact', len(local) == 81 and metrics['outside_names'] == [row['name'] for row in local if row['outside_effective_range']] and metrics['outside_count'] == sum(row['outside_effective_range'] for row in local) and metrics['max_minimum_change_rad'] == max(abs(row['signed_minimum_change_rad']) for row in local))
    check(label + '_observed_warmstart_rejected', summary['warmstart_rejected'] and summary['ranges']['held']['outside_count'] == 5)
check('current_initial6_vs5', result['summary'][0]['ranges']['actual_initial']['outside_count'] == 6 and result['summary'][1]['ranges']['actual_initial']['outside_count'] == 5)
check('qualification_preserved_false_no_loader_bypass', all(source['strict_G0_qualification']['qualified_for_g0'] is False for source in result['sources'].values()))

manifest = read(AR / 'artifact_manifest.json')
artifact_execution = read(AR / 'producer_execution.json')
artifact_snapshot = read(AR / 'source_snapshot.json')
artifact_inputs = len(manifest['inputs_sha256_before'])
check('artifact_inputs_current_before_after_exact', manifest['inputs_sha256_before'] == manifest['inputs_sha256_after'] == artifact_execution['inputs_sha256_before'] == artifact_execution['inputs_sha256_after'] and closure(manifest['inputs_sha256_before']))
check('artifact_source_copies_exact', len(artifact_snapshot['files']) == artifact_inputs and all(sha(record['original_path']) == sha(record['copy_path']) == record['sha256'] for record in artifact_snapshot['files']))
check('artifact_producer_wrapper_log_exact', manifest['producer_sha256_before'] == manifest['producer_sha256_after'] == artifact_execution['producer_sha256_before'] == artifact_execution['producer_sha256_after'] == sha(A / 'make_fixed_strap_source_compatibility_artifacts.py') and sha(AR / 'run_producer.sh') == sha(AR / 'run_producer.sh.archived') == artifact_execution['wrapper_sha256'] and sha(AR / 'producer.log') == artifact_execution['log_sha256'])
check('artifact_exit0_outputs_exact', artifact_execution['exit_code'] == 0 and manifest['outputs_sha256'] == artifact_execution['outputs_sha256'] and all(sha(AR / path) == digest for path, digest in manifest['outputs_sha256'].items()))
check('artifact_no_native_physics_actor_training', all(manifest[key] == artifact_execution[key] == 0 for key in ['native_initializations', 'physics_steps', 'actor_inference_calls', 'training_updates']))

protected = 0
for phase, count in [('initial_middle3_alignment_v1', 964), ('playing_target_bridge_v1', 41)]:
    inventory = read(B / phase / 'artifact_inventory.json')
    check('preserved_' + phase, len(inventory) == count and all(Path(path).stat().st_size == record['size'] and sha(path) == record['sha256'] for path, record in inventory.items()))
    protected += count
collection = read(D / 'video_collection_update_v9.json')
check('video_collection140_unchanged', len(list((D / 'videos').glob('*.mp4'))) == collection['total_count'] == 140 and closure(collection['previous_video_sha256']) and all(sha(record['copy']) == sha(record['source']) == record['sha256'] for record in collection['copies']) and sha(D / 'VIDEO_INDEX_v10.md') == collection['new_index_sha256'])
for path, record in read(P / 'journal_before.json').items():
    check('append_only_' + Path(path).name, hashlib.sha256(Path(path).read_bytes()[:record['size']]).hexdigest() == record['sha256'])
modules = ['audit_fixed_strap_source_compatibility.py', 'run_fixed_strap_source_compatibility.py', 'make_fixed_strap_source_compatibility_artifacts.py']
for name in modules:
    ast.parse((A / name).read_text(), feature_version=(3, 8))
    check('syntax38_' + name, True)
for path in P.glob('*.md'):
    for target, line in re.findall(r'\]\(<?(/[^)>]+?)(?::(\d+))?>?\)', path.read_text()):
        linked = Path(target)
        check('link_' + str(len(checks)), linked.exists() and (not line or len(linked.read_text().splitlines()) >= int(line)))
check('review_present', (P / 'review.md').is_file())
paths = [A / name for name in modules + ['FIXED_STRAP_SOURCE_COMPATIBILITY_PLAN.md', 'FIXED_STRAP_SOURCE_COMPATIBILITY_DECISION.md', 'FIXED_STRAP_SOURCE_HAND_INITIAL_PLAN.md', 'README.md', 'PLAN.md']]
paths += [D / 'VISUAL_REPORT.md'] + list(P.glob('*.md'))
final_sources = {}
for path in paths:
    copied = P / 'source_final' / path.relative_to(R)
    copied.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, copied)
    check('final_copy_' + str(len(final_sources)), sha(copied) == sha(path))
    final_sources[str(path)] = dict(snapshot=str(copied), sha256=sha(path))
(P / 'source_final_manifest.json').write_text(json.dumps(final_sources, indent=2) + '\n')
(P / 'final_verification.json').write_text(json.dumps(dict(checks=checks, counts=dict(checks=len(checks), protected_previous_files=protected, native_initializations=0, physics_steps=0, actor_inference_calls=0, training_updates=0, cpu_inputs=48, joint_rows=810, artifact_inputs=artifact_inputs, video_collection_total=140), command=['python', '/tmp/audit_fixed_strap_source_compatibility.py'], root_audit_producer_sha256=sha(__file__), source_final_manifest_sha256=sha(P / 'source_final_manifest.json'), scope='Saved two-candidate necessary source/native/normalized ranges; five remaining LH mismatches; next hand5 native trial not executed; no geometry, naturalness or playing certification'), indent=2) + '\n')
inventory = {str(path): dict(size=path.stat().st_size, sha256=sha(path)) for path in sorted(P.rglob('*')) if path.is_file() and path != P / 'artifact_inventory.json'}
(P / 'artifact_inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
print(json.dumps(dict(checks=len(checks), inventory=len(inventory), protected_previous_files=protected, native_initializations=0, physics_steps=0, cpu_inputs=48, artifact_inputs=artifact_inputs)))
