"""Seal the four completed static native trials without altering consumed inputs."""
from pathlib import Path
import hashlib
import json
import re
import subprocess

R = Path('/home/ajou/yigyu/3')
P = R / 'docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1'
V = R / 'docs/2026-10-12/video/upper_arm_static_support_v1'
OLD = P.parent / 'initial_pose_noise_v1'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def exact(mapping):
    return all(Path(p).is_file() and sha(p) == h for p, h in mapping.items())


def main():
    checks = {}
    for name in ('verification_v2.json', 'same_conditions_verification_v1.json'):
        data = read(P / name)
        checks[name] = data['passed'] and exact(data['input_sha256'])
    pins = {**read(P / 'source_before_native_v2.json'), **read(P / 'source_addition_batch_v2.json')}
    checks['eight_new_implementation_sources_exact'] = exact(pins)
    revision = read(P / 'preflight_source_revision_v1.json')
    old_pins = read(P / 'source_before_search_v1.json')
    old_pins[revision['path']] = revision['native_final_sha256']
    checks['pre_search_sources_and_prepared_runner_preserved'] = (
        exact(old_pins) and sha(revision['prepared_snapshot']) == revision['prepared_old_sha256']
        and revision['never_executed_before_revision'])
    old_inventory = read(OLD / 'artifact_inventory_v1.json')['files']
    checks['previous_phase_4099_artifacts_unchanged'] = all(sha(e['path']) == e['sha256'] for e in old_inventory)
    first_append = read(P / 'main_append_v1.json')
    completion = read(P / 'main_completion_append_v2.json')
    prefixes = []
    for i, entry in enumerate(completion):
        p = Path(entry['path'])
        before = Path(entry['snapshot'])
        original = P / 'main_before_v1' / f'{i}_{p.name}'
        first = first_append[str(p)]
        prefixes.append(sha(original) == first['old_prefix_sha256']
                        and before.read_bytes().startswith(original.read_bytes())
                        and sha(before) == first['current_sha256'] == entry['before_sha256']
                        and p.read_bytes().startswith(before.read_bytes())
                        and sha(p) == entry['after_sha256'])
    checks['two_main_append_prefixes_preserved'] = all(prefixes)
    frame_count = 0
    for case in read(P / 'native_v2/batch_report.json')['records']:
        out = Path(case['output'])
        capture = read(out / 'media/capture.json')
        images = {}
        for frame in capture['frames']:
            images.update(frame['image_sha256'])
            images.update(frame['raw_image_sha256'])
        frame_count += len(images)
        checks[case['label'] + '_all_raw_and_overlay_images_exact'] = len(images) == 604 and exact(images)
        checks[case['label'] + '_native_input_closure_exact'] = exact(read(out / 'attempt.json')['input_sha256'])
    archives = read(V / 'manifest.json')['files']
    archive_ok = len(archives) == 8
    for item in archives:
        probe = json.loads(subprocess.check_output([
            'ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_frames',
            '-show_entries', 'stream=nb_read_frames,avg_frame_rate,duration',
            '-of', 'json', item['destination']], text=True))['streams'][0]
        archive_ok &= (sha(item['source']) == item['sha256_source'] == item['sha256_destination']
                       == sha(item['destination']) and probe['nb_read_frames'] == '151'
                       and probe['avg_frame_rate'] == '30/1'
                       and abs(float(probe['duration']) - 151 / 30) < .002)
    checks['eight_archive_videos_exact_and_full_duration'] = archive_ok
    provenance = read(P / 'artifacts_v1/provenance_v1.json')
    checks['artifact_provenance_exact'] = (exact(provenance['input_sha256_before'])
        and exact(provenance['input_sha256_after'])
        and all(sha(e['path']) == e['sha256'] for e in provenance['outputs']))
    review = P / 'review_final_v2.md'
    checks['independent_review_exists'] = review.is_file() and review.stat().st_size > 0
    docs = [P / 'README.md', P / 'CHANGED_FILES_V2.md', P / 'artifacts_v1/README.md',
            P / 'artifacts_v1/CHANGED_FILES.md', V / 'README.md', V.parent / 'README_ABSOLUTE_V11.md']
    checks['new_document_links_exist'] = all(
        Path(re.sub(r':\d+$', '', target)).exists()
        for p in docs for target in re.findall(r'\]\((/[^)]+)\)', p.read_text()))
    assert all(checks.values()), checks
    snapshot_dir = P / 'source_final_v2'
    snapshot_dir.mkdir(exist_ok=False)
    sources = [Path(p) for p in pins] + [Path(e['path']) for e in completion]
    sources += [P / 'analyze_static_v2.py', P / 'verify_same_conditions_v1.py',
                P / 'artifacts_v1/make_static_support_figures_v1.py', Path(__file__),
                P / 'README.md', P / 'CHANGED_FILES_V2.md', review]
    manifest = []
    for source in sources:
        dest = snapshot_dir / source.relative_to(R)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(source.read_bytes())
        manifest.append({'source': str(source), 'snapshot': str(dest), 'sha256': sha(source)})
    (snapshot_dir / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    files = [p for p in P.rglob('*') if p.is_file()] + [p for p in V.rglob('*') if p.is_file()]
    files += [V.parent / 'README_ABSOLUTE_V11.md'] + [Path(p) for p in pins] + [Path(e['path']) for e in completion]
    inventory = [{'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size}
                 for p in sorted(set(files))]
    inventory_path = P / 'artifact_inventory_v2.json'
    inventory_path.write_text(json.dumps({'files': inventory}, ensure_ascii=False, indent=2))
    result = {'passed': True, 'checks': checks, 'previous_files_preserved': len(old_inventory),
              'native_images_verified': frame_count, 'videos_verified': len(archives),
              'sources_snapshotted': len(manifest), 'files_sealed': len(inventory),
              'artifact_inventory_sha256': sha(inventory_path),
              'source_manifest_sha256': sha(snapshot_dir / 'manifest.json'),
              'review_sha256': sha(review),
              'scope': 'four five-second constant initial-q PD trials; no music/checkpoint/policy/training; initial retention and sustained upper-arm support not achieved'}
    (P / 'final_verification_v2.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
