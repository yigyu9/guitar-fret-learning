"""Verify immutable inputs, native media, prior artifacts and append-only records."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

R = Path('/home/ajou/yigyu/3')
P = R / 'docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1'
V = R / 'docs/2026-10-12/video/realistic_guitar_proportions_v1'


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def exact(mapping):
    for path, expected in mapping.items():
        path = Path(path)
        if not path.is_absolute():
            path = R / path
        assert sha(path) == expected, str(path)


def save(name, value):
    path = P / name
    assert not path.exists(), str(path)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


checks = {}
for name in ['verification_v3.json', 'body_center_audit_v2.json',
             'native_geometry_ABI_verification_v1.json', 'geometry_build_v1.json']:
    data = read(P / name)
    assert data.get('passed', all(data.get('checks', {}).values()))
    assert all(data.get('checks', {}).values())
    exact(data['input_sha256'])
checks['canonical_analysis_geometry_ABI_inputs'] = True
for path in sorted(P.glob('source_before_*.json')) + [P / 'assets_before_native_v1.json']:
    exact(read(path))
checks['source_and_asset_pins'] = True

frames = 0
for trial in ['native_baseline_v2', 'native_realistic_v2']:
    exact(read(P / trial / 'attempt.json')['input_sha256'])
    for capture in ['media/capture.json', 'media/raw/capture.json']:
        data = read(P / trial / capture)
        assert len(data['frames']) == 151
        for frame in data['frames']:
            assert frame['render_preserves_states']
            exact(frame['image_sha256'])
            frames += len(frame['image_sha256'])
checks['native_inputs_and_1208_frame_hashes'] = frames == 1208

for version in ['v1', 'v2']:
    folder = P / ('artifacts_' + version)
    data = read(folder / 'provenance.json')
    for path, pair in data['inputs_sha256_before_after'].items():
        assert pair['before'] == pair['after'] == sha(path), path
    exact(data['outputs_sha256'])
    assert sha(folder / ('make_artifacts_' + version + '.py')) == data['producer_sha256']
checks['both_artifact_versions_preserved'] = True
videos = read(V / 'manifest.json')['videos']
assert len(videos) == 4
for video in videos:
    assert sha(video['source']) == sha(video['destination']) == video['source_sha256'] == video['copy_sha256']
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams',
        'v:0', '-show_entries', 'stream=nb_frames,r_frame_rate', '-of', 'json', video['destination']]))
    assert probe['streams'][0]['nb_frames'] == '151'
    assert probe['streams'][0]['r_frame_rate'] == '30/1'
checks['four_exact_archived_videos'] = True

chains = [read(P / name) for name in ['main_append_v1.json', 'main_append_v2.json',
    'main_completion_append_v1.json', 'main_visual_correction_append_v1.json']]
main_paths = {entry['path'] for entry in chains[0]}
for index in range(4):
    for step, chain in enumerate(chains):
        entry = chain[index]
        before = Path(entry['snapshot']).read_bytes()
        assert sha(entry['snapshot']) == entry['before_sha256']
        after_path = chains[step + 1][index]['snapshot'] if step < 3 else entry['path']
        assert sha(after_path) == entry['after_sha256']
        assert Path(after_path).read_bytes().startswith(before)
checks['four_main_documents_append_only'] = True
old = read(P.parent / 'rounded_spine_no_left_v1/artifact_inventory_v1.json')['files']
for entry in old:
    if entry['path'] in main_paths:
        original = next(r['snapshot'] for r in chains[0] if r['path'] == entry['path'])
        assert sha(original) == entry['sha256']
    else:
        assert sha(entry['path']) == entry['sha256'], entry['path']
checks['previous_phase_all_files_preserved'] = True

review = P / 'review_final_v1.md'
assert review.is_file() and review.stat().st_size > 0
checks['independent_review_saved'] = True
for doc in [P / 'README.md', P / 'CHANGED_FILES_V2.md', P / 'artifacts_v2/README.md']:
    for target in re.findall(r'\]\((/[^)]+)\)', doc.read_text()):
        assert Path(re.sub(r':\d+$', '', target)).exists(), target
checks['canonical_document_links_exist'] = True
assert all(checks.values())
sources = set(read(P / 'source_before_native_v2.json')) | set(read(P / 'assets_before_native_v1.json')) | main_paths
sources |= {str(path) for path in P.glob('*.py')} | {str(review)}
save('source_final_v1.json', {path: sha(path) for path in sorted(sources)})
paths = set(path for path in P.rglob('*') if path.is_file()) | set(path for path in V.rglob('*') if path.is_file())
paths |= {Path(path) for path in sources}
paths.add(V.parent / 'README_ABSOLUTE_V13.md')
inventory = [{'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size} for path in sorted(paths)]
save('artifact_inventory_v1.json', {'files': inventory})
save('final_verification_v1.json', {'passed': True, 'checks': checks,
    'previous_phase_preserved_files': len(old), 'frame_hashes_checked': frames,
    'videos_checked': len(videos), 'inventory_files': len(inventory), 'review_sha256': sha(review),
    'source_final_sha256': sha(P / 'source_final_v1.json'),
    'inventory_sha256': sha(P / 'artifact_inventory_v1.json')})
print(json.dumps({'passed': True, 'checks': len(checks), 'files': len(inventory), 'frames': frames}))
