"""Verify saved native evidence and append-only navigation, then seal this phase."""
from pathlib import Path
import ast
import hashlib
import json
import re


P = Path(__file__).resolve().parent
R = P.parents[4]
A = R / 'stability_adapter_2'
D = R / 'docs/2026-10-19/stability_adapter_2'
B = P.parent / 'waist_upright_right_arm_v1'
V = D / 'video/waist_straighten_v1'


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def main():
    review = P / 'review_final_v1.md'
    assert review.exists() and 'Critical: 0' in review.read_text()
    updates = read(P / 'navigation_update_v1.json')
    assert len(updates) == 3
    current_prefixes = {}
    for row in updates:
        before = Path(row['before_snapshot']).read_bytes()
        current = Path(row['path']).read_bytes()
        assert sha(row['before_snapshot']) == row['before_sha256']
        assert sha(row['path']) == row['after_sha256']
        assert current.startswith(before)
        assert current.decode().splitlines()[row['append_heading_line'] - 1].startswith('## ')
        current_prefixes[row['path'], row['before_sha256']] = row['before_snapshot']
    previous = read(B / 'source_final_v1.json')['preserved']
    previous_prefixes = {(r['path'], r['expected_sha256']): r['snapshot']
                         for r in previous if r.get('snapshot')}
    seen = set()
    preserved = []

    def verify(path, expected):
        path = str(path)
        key = path, expected
        if key in seen:
            return
        seen.add(key)
        current = sha(path)
        if current == expected:
            preserved.append({'path': path, 'expected_sha256': expected,
                              'resolution': 'current exact'})
            return
        snapshot = current_prefixes.get(key) or previous_prefixes.get(key)
        assert snapshot, (path, 'unexpected modification')
        assert sha(snapshot) == expected
        assert Path(path).read_bytes().startswith(Path(snapshot).read_bytes())
        preserved.append({'path': path, 'expected_sha256': expected,
                          'resolution': 'exact prefix snapshot of authorized append',
                          'snapshot': snapshot})

    assert read(B / 'final_verification_v1.json')['passed']
    for row in previous:
        verify(row['path'], row['expected_sha256'])
    for row in read(B / 'artifact_inventory_v1.json')['files']:
        verify(row['path'], row['sha256'])
    for name in ('source_final_v1.json', 'artifact_inventory_v1.json',
                 'final_verification_v1.json'):
        file = B / name
        verify(file, sha(file))
    for folder in (P / 'search_v1',):
        for file in folder.glob('*.json'):
            obj = read(file)
            maps = [obj.get('input_sha256', {})] if isinstance(obj, dict) else []
            if file.name == 'inputs_before.json':
                maps.append(obj)
            for mapping in maps:
                if isinstance(mapping, dict):
                    for path, digest in mapping.items():
                        if path.startswith('/') and isinstance(digest, str) and re.fullmatch('[0-9a-f]{64}', digest):
                            verify(path, digest)
    for file in P.glob('native_*/attempt.json'):
        for path, digest in read(file)['input_sha256'].items():
            verify(path, digest)
    for file in list(P.glob('analysis_*/*.json')) + [P / 'posture_final_v1.json']:
        obj = read(file)
        for mapping in (obj.get('input_sha256', {}), obj.get('support', {}).get('input_sha256', {})):
            for path, digest in mapping.items():
                verify(path, digest)
    provenance = read(P / 'artifacts_v1/provenance_v1.json')
    for row in provenance['native_source_inputs'] + provenance['producers']:
        assert row['unchanged'] and row['sha256_before'] == row['sha256_after']
        verify(row['path'], row['sha256_before'])
    verify(provenance['manifest_path'], provenance['manifest_sha256'])
    manifest = read(V / 'manifest_v1.json')
    assert len(manifest['video_copies']) == 4 and len(manifest['derived_images']) == 6
    for row in manifest['video_copies']:
        assert row['byte_exact'] and row['copy_sha256'] == row['source_sha256']
        verify(row['source'], row['source_sha256'])
        verify(row['path'], row['copy_sha256'])
        assert Path(row['path']).stat().st_size == row['bytes']
        info = row['ffprobe']
        assert (info['width'], info['height'], info['avg_frame_rate'],
                info['nb_read_frames']) == (1280, 720, '30/1', '151')
        assert abs(float(info['duration']) - 5.033333) < 1e-6
    for row in manifest['derived_images']:
        verify(row['path'], row['sha256'])
    assert manifest['camera_comparison']['whole_body']['view_matrix_exact']
    assert manifest['camera_comparison']['whole_body']['projection_matrix_exact']
    frames = 0
    for case in ('native_add4_static', 'native_add8_static'):
        report = read(P / case / 'report.json')
        assert report['completed'] and report['inputs_unchanged'] and not report['forbidden_calls']
        assert not report['strap_enabled'] and report['physics_steps'] == 1200
        assert report['control_steps'] == 300 and report['training_updates'] == 0
        capture = read(P / case / 'media/capture.json')
        assert len(capture['frames']) == 151 and capture['actual_strap_enabled'] is False
        for row in capture['frames']:
            for path, digest in row['image_sha256'].items():
                verify(path, digest)
                frames += 1
    assert frames == 604
    analysis = read(P / 'analysis_final_v1/analysis.json')
    assert analysis['passed'] and analysis['support']['passed']
    cases = analysis['support']['cases']
    assert set(cases) == {'native_add4_static', 'native_add8_static'}
    for case, row in cases.items():
        assert row['Thorax_last_half_second_presence_steps'] == 0
        assert row['upper_last_half_second_presence_steps'] == 120
        assert row['contacts']['right_distal_guitar_contacts']['presence_steps'] == 0
        waist = analysis['waist_regions'][case]
        assert waist['waist_presence_steps'] == 1198
        assert waist['waist_positive_steps'] == (1197 if case == 'native_add4_static' else 1198)
        assert waist['waist_last_half_second_presence_steps'] == 120
        assert waist['waist_last_half_second_positive_steps'] == 120
    assert analysis['support']['comparisons'] == {}
    posture = read(P / 'posture_final_v1.json')['cases']['native_add8_static']
    difference = posture['comparisons']['previous_relief4']['initial_tilt_reduction_deg']
    assert abs(difference['Torso'] - 3.2) < 1e-4
    assert abs(difference['Spine'] - 6.0) < 1e-4
    assert abs(difference['Chest'] - 8.0) < 1e-4
    rows = read(P / 'search_v1/search.json')['rows']
    assert len(rows) == 2 and all(r['accepted_for_native'] for r in rows)
    docs = [P / 'README.md', P / 'CHANGED_FILES_v1.md',
            A / 'WAIST_STRAIGHTEN_COMPLETION_V1.md',
            P / 'artifacts_v1/README.md', V / 'INDEX.md']
    links = 0
    for file in docs:
        for target in re.findall(r'\]\((/[^)]+)\)', file.read_text()):
            line = re.search(r':(\d+)$', target)
            path = Path(re.sub(r':\d+$', '', target))
            assert path.exists(), (file, path)
            if line:
                assert 1 <= int(line[1]) <= len(path.read_text().splitlines())
            links += 1
    for file in (A / 'search_waist_straighten_v1.py', A / 'analyze_waist_straighten_v1.py',
                 P / 'artifacts_v1/build_artifacts_v1.py', Path(__file__)):
        ast.parse(file.read_text())
    save(P / 'source_final_v1.json', {'preserved': preserved, 'append_prefixes': updates,
         'scope': 'prior waist_upright_right_arm closure/inventory including original temporary dependency restoration; current source/native/analysis/artifact before/after hashes; all 604 native PNG; 4 exact MP4 copies; prior historical before-pin limitations retained'})
    files = sorted(f for f in P.rglob('*') if f.is_file()) + sorted(f for f in V.rglob('*') if f.is_file())
    save(P / 'artifact_inventory_v1.json',
         {'files': [{'path': str(f), 'sha256': sha(f), 'bytes': f.stat().st_size} for f in files]})
    save(P / 'final_verification_v1.json',
         {'passed': True, 'preserved_input_versions': len(preserved), 'inventory_files': len(files),
          'links_checked': links, 'raw_native_png_verified': frames, 'source_proposals': 2,
          'source_accepted': 2, 'source_rejected': 0, 'native_attempts': 2,
          'native_execution_completed': 2, 'native_total_physics_steps': 2400,
          'native_total_control_ticks': 600, 'video_copies': 4, 'training_updates': 0,
          'authorized_navigation_appends': 3, 'restored_temporary_dependency_files': 0,
          'review_path': str(review), 'review_sha256': sha(review),
          'scope': 'previous 4 degree waist posture preserved; additional 8 degree upright visual candidate with 2 completed static comparisons; no new elbow wave, sustained two-block wedge, passive no-left-hand stability, music, learning default replacement or repeatability certification'})
    print('passed', len(preserved), 'input versions;', len(files), 'inventory files;', links, 'links')


if __name__ == '__main__':
    main()
