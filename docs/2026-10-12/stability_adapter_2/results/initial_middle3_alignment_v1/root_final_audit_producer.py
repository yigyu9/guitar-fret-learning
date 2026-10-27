from pathlib import Path
import ast
import hashlib
import json
import re
import shutil

R = Path('/home/ajou/yigyu/3')
A = R / 'stability_adapter_2'
D = R / 'docs/2026-10-12/stability_adapter_2'
B = D / 'results'
P = B / 'initial_middle3_alignment_v1'
AR = P / 'artifacts'
checks, cache = {}, {}


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    path = Path(path)
    if str(path) not in cache:
        h = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1048576), b''):
                h.update(block)
        cache[str(path)] = h.hexdigest()
    return cache[str(path)]


def check(name, value):
    assert value, name
    checks[name] = True


def closure(mapping):
    return all(sha(path) == digest for path, digest in mapping.items())


assert not (P / 'final_verification.json').exists()
assert not (P / 'artifact_inventory.json').exists()
check('audit_producer_prearchived_exact', sha(__file__) == sha(P / 'root_final_audit_producer.py'))
for stage, inputs, copies in [('preparation', 14016, 116), ('native', 14019, 117), ('analysis', 31, 10), ('collection', 145, 5)]:
    execution = read(P / (stage + '_execution.json'))
    snapshot = read(P / (stage + '_source_manifest.json'))
    check(stage + '_exit0_input_before_after_current', execution['exit_code'] == 0 and len(execution['input_sha256_before']) == inputs and execution['input_sha256_before'] == execution['input_sha256_after'] and closure(execution['input_sha256_before']))
    check(stage + '_source_copies_and_log_exact', len(snapshot) == copies and all(sha(path) == sha(record['snapshot']) == record['sha256'] for path, record in snapshot.items()) and sha(P / (stage + '.log')) == execution['log_sha256'])

preparation = read(P / 'preparation.json')
proposal = read(P / 'proposal.json')
check('preparation14_proposal14015_closure_exact', len(preparation['checks']) == 14 and all(preparation['checks'].values()) and preparation['checks'] == proposal['checks'] and len(preparation['input_sha256']) == 14015 and preparation['input_sha256'] == proposal['input_sha256'] and closure(preparation['input_sha256']))
check('source_admitted1188_clear_zero_physics', preparation['admitted_for_native'] and preparation['source_self_pair_count'] == 1188 and not preparation['source_self_intersections'] and not preparation['source_human_guitar_intersections'] and not preparation['source_cross_hand_intersections'] and preparation['native_initializations'] == preparation['physics_steps'] == 0)
check('only_middle3_initial_at_goal_trial_preserved', preparation['changed_source_bodies'] == ['LH:middle3', 'LH:middle_top'] and preparation['new_initial_rad'] == 0.9091416597366333 and preparation['initial_delta_rad'] == -0.14060187339782715 and sha(preparation['trial_path']) == preparation['trial_sha256'])

analysis = read(P / 'analysis.json')
report = read(P / 'native/report.json')
fresh = read(P / 'native/initial_grip_audit.json')
check('analysis23_29input_closure_exact', len(analysis['checks']) == 23 and all(analysis['checks'].values()) and len(analysis['input_sha256_before']) == 29 and analysis['input_sha256_before'] == analysis['input_sha256_after'] and closure(analysis['input_sha256_before']))
check('actual_one1200_5s151frames', report['completed'] is True and report['failure'] is None and report['native_initializations'] == analysis['new_native_initializations'] == 1 and report['physics_steps'] == analysis['new_physics_steps'] == 1200 and report['simulation_elapsed_s'] == 5.0 and report['frame_count'] == 151)
check('native11_fresh14_source1188_clear', len(report['checks']) == 11 and all(report['checks'].values()) and len(fresh['checks']) == 14 and all(fresh['checks'].values()) and fresh['complete_source_self_screen']['pair_count'] == 1188 and not fresh['complete_source_self_screen']['intersections'])
check('not_naturalness_playing_certification_no_actor_training', analysis['naturalness_or_playing_success_certified'] is False and analysis['actor_inference_calls'] == analysis['training_updates'] == 0 and report['stability_success'] is None)
check('two_runs_full_series_windows', len(analysis['summary']) == 2 and len((P / 'joint_series.jsonl').read_text().splitlines()) == 2402 and len((P / 'guitar_series.jsonl').read_text().splitlines()) == 2402 and len((P / 'windows.jsonl').read_text().splitlines()) == 242)
old, new = analysis['summary']
check('fixed_LA_both_conditions', all(row['strap']['rest_length_m'] == 1.1018469719600776 for row in analysis['summary']))
check('observed_initial_error_zero_with_more_G_movement', old['initial_middle3_goal_error_deg'] > 8 and new['initial_middle3_goal_error_deg'] == 0 and new['guitar']['max_initial_position_error_mm'] > old['guitar']['max_initial_position_error_mm'] and new['max_1s_position_change_mm'] > old['max_1s_position_change_mm'] and new['max_1s_rotation_change_deg'] > old['max_1s_rotation_change_deg'])
check('observed_early_speed_tradeoff', new['early_0_to_05s']['max_linear_speed_mps'] > old['early_0_to_05s']['max_linear_speed_mps'] and new['early_0_to_05s']['max_angular_speed_rad_s'] > old['early_0_to_05s']['max_angular_speed_rad_s'])
check('observed_provisional_envelope_counts', all(row['windows_within_provisional_limits'] == 121 and row['outside_initial_envelope_samples'] == 0 for row in analysis['summary']))
check('same81_commands_and_only_initial_middle3_contract', all(analysis['checks'][name] for name in ['all81_1200_final_commands_and_clock_exact', 'only_middle3_initial_and_offset_changed', 'other80_initial_q_exact_middle3_aligned', 'G_and_other64_body_initial_states_exact', 'all11_common_initial_fields_exact', 'all604_new_PNG_exact']))

contact_steps = {}
for line in (P / 'native/contacts.jsonl').read_text().splitlines():
    record = json.loads(line)
    for contact in record['contacts']:
        pair = [contact['body0_name'], contact['body1_name']]
        if contact['lambda'] > 0 and any(name.startswith('guitar/') for name in pair):
            for name in pair:
                if name.startswith('human/LH:'):
                    contact_steps.setdefault(name, set()).add(record['physics_step'])
for name, count, first, last in [('human/LH:middle3', 91, 32, 122), ('human/LH:ring3', 38, 36, 73), ('human/LH:index3', 1156, 42, 1200)]:
    steps = contact_steps[name]
    check('raw_contact_steps_' + name, len(steps) == count and min(steps) == first and max(steps) == last and new['human_guitar_positive_raw_lambda_steps'][name] == count)
check('middle_ring_no_contact_after2s', all(step < 480 for name in ['human/LH:middle3', 'human/LH:ring3'] for step in contact_steps[name]))
check('thumb_contact587_after2s251', len(contact_steps['human/LH:thumb3']) == 587 and sum(step >= 480 for step in contact_steps['human/LH:thumb3']) == 251)

videos = read(P / 'native/videos.json')
check('native_two_videos_sha151_30fps_duration', len(videos) == 2 and all(sha(video['path']) == video['sha256'] and video['ffmpeg_exit_code'] == video['ffprobe_exit_code'] == 0 and video['stream']['nb_read_frames'] == '151' and video['stream']['avg_frame_rate'] == '30/1' and video['stream']['duration'] == '5.033333' for video in videos.values()))
check('native_png604_preserved', len(list((P / 'native/raw').rglob('*.png'))) == 302 and len(list((P / 'native/frames').rglob('*.png'))) == 302)
for camera in ['hands', 'whole_body']:
    previous = B / 'fixed_strap_middle_relax_v2/native/frames' / camera
    current = P / 'native/frames' / camera
    check(camera + '_t0_t5_changed', all(sha(previous / name) != sha(current / name) for name in ['00000.png', '00150.png']))

manifest = read(AR / 'artifact_manifest.json')
execution = read(AR / 'producer_execution.json')
snapshot = read(AR / 'source_snapshot.json')
artifact_inputs = len(manifest['inputs_sha256_before'])
check('artifact_all_input_closure_exact', manifest['inputs_sha256_before'] == manifest['inputs_sha256_after'] == execution['inputs_sha256_before'] == execution['inputs_sha256_after'] and closure(manifest['inputs_sha256_before']))
check('artifact_all_source_copies_exact', len(snapshot['files']) == artifact_inputs and all(sha(record['original_path']) == sha(record['copy_path']) == record['sha256'] for record in snapshot['files']))
check('artifact_producer_wrapper_log_exact', manifest['producer_sha256_before'] == manifest['producer_sha256_after'] == execution['producer_sha256_before'] == execution['producer_sha256_after'] == sha(A / 'make_initial_middle3_alignment_artifacts.py') and sha(AR / 'run_producer.sh') == sha(AR / 'run_producer.sh.archived') and sha(AR / 'producer.log') == execution['producer_log_sha256'])
check('artifact_execution0_outputs_exact', execution['exit_code'] == 0 and manifest['outputs_sha256'] == execution['outputs_sha256'] and all(sha(AR / path) == digest for path, digest in manifest['outputs_sha256'].items()))
check('artifact_no_physics_actor_training', all(manifest[key] == execution[key] == 0 for key in ['native_initializations_during_artifact', 'physics_steps_during_artifact', 'actor_inference_calls_during_artifact', 'training_updates_during_artifact']))

collection = read(D / 'video_collection_update_v9.json')
check('collection_old138_exact_newtwo_total140', len(collection['previous_video_sha256']) == 138 and closure(collection['previous_video_sha256']) and len(collection['copies']) == 2 and all(sha(record['source']) == sha(record['copy']) == record['sha256'] and Path(record['copy']).stat().st_size == record['size'] for record in collection['copies']) and collection['total_count'] == 140 and len(list((D / 'videos').glob('*.mp4'))) == 140)
check('collection_old_new_indexes_exact', sha(D / 'VIDEO_INDEX_v9.md') == collection['previous_index_sha256'] and sha(D / 'VIDEO_INDEX_v10.md') == collection['new_index_sha256'] and sha(A / 'collect_initial_middle3_alignment_videos.py') == collection['producer_sha256'])

modules = ['prepare_initial_middle3_alignment.py', 'run_initial_middle3_alignment_phase.py', 'analyze_initial_middle3_alignment.py', 'collect_initial_middle3_alignment_videos.py', 'make_initial_middle3_alignment_artifacts.py']
for name in modules:
    ast.parse((A / name).read_text(), feature_version=(3, 8))
    check('syntax38_' + name, True)
protected = 0
for phase, count in [('fixed_strap_middle_relax_v2', 1561), ('fixed_strap_middle_relax_v1', 982), ('natural_envelope_assessment_v1', 63), ('natural_pose_criteria_v1', 15), ('finger_contact_map_v1', 72)]:
    inventory = read(B / phase / 'artifact_inventory.json')
    check('preserved_' + phase, len(inventory) == count and all(Path(path).stat().st_size == record['size'] and sha(path) == record['sha256'] for path, record in inventory.items()))
    protected += count
check('five_previous_inventories2693', protected == 2693)
for path, record in read(P / 'journal_before.json').items():
    check('append_only_' + Path(path).name, hashlib.sha256(Path(path).read_bytes()[:record['size']]).hexdigest() == record['sha256'])
for path in P.glob('*.md'):
    for target, line in re.findall(r'\]\(<?(/[^)>]+?)(?::(\d+))?>?\)', path.read_text()):
        linked = Path(target)
        check('link_' + str(len(checks)), linked.exists() and (not line or len(linked.read_text().splitlines()) >= int(line)))
check('review_present', (P / 'review.md').is_file())

final_sources = {}
paths = [A / name for name in modules + ['INITIAL_MIDDLE3_ALIGNMENT_PLAN.md', 'INITIAL_MIDDLE3_ALIGNMENT_DECISION.md', 'trials/initial_middle3_alignment_v1/middle3_initial_at_goal.json', 'README.md', 'PLAN.md']]
paths += [D / 'VISUAL_REPORT.md', D / 'VIDEO_INDEX_v10.md', D / 'video_collection_update_v9.json'] + list(P.glob('*.md'))
for path in paths:
    copied = P / 'source_final' / path.relative_to(R)
    copied.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, copied)
    check('final_copy_' + str(len(final_sources)), sha(copied) == sha(path))
    final_sources[str(path)] = dict(snapshot=str(copied), sha256=sha(path))
(P / 'source_final_manifest.json').write_text(json.dumps(final_sources, indent=2) + '\n')
(P / 'final_verification.json').write_text(json.dumps(dict(checks=checks, counts=dict(checks=len(checks), protected_previous_files=protected, native_initializations=1, physics_steps=1200, actor_inference_calls=0, training_updates=0, artifact_inputs=artifact_inputs, video_collection_total=140), command=['python', '/tmp/audit_initial_middle3_alignment.py'], root_audit_producer_sha256=sha(__file__), source_final_manifest_sha256=sha(P / 'source_final_manifest.json'), scope='One initial middle3 alignment trial at identical final81 commands; observed greater G motion, both provisional envelopes satisfied; not naturalness, playing or cooked penetration certification'), indent=2) + '\n')
inventory = {str(path): dict(size=path.stat().st_size, sha256=sha(path)) for path in sorted(P.rglob('*')) if path.is_file() and path.name != 'artifact_inventory.json'}
(P / 'artifact_inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
print(json.dumps(dict(checks=len(checks), inventory=len(inventory), protected_previous_files=protected, native_initializations=1, physics_steps=1200, artifact_inputs=artifact_inputs)))
