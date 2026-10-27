"""Seal saved inputs, previous evidence, authorized append prefixes and media copies."""
from pathlib import Path
import ast
import hashlib
import json
import re

P = Path(__file__).resolve().parent
R = P.parents[4]
A = R/'stability_adapter_2'
D = R/'docs/2026-10-19/stability_adapter_2'
B = P.parent/'left_neck_near_initial_v1'
V = D/'video/right_block_cradle_v1'


def read(p): return json.loads(Path(p).read_text())
cache = {}


def sha(p):
    p = str(p)
    if p not in cache: cache[p] = hashlib.sha256(Path(p).read_bytes()).hexdigest()
    return cache[p]


def save(p, value):
    with p.open('x') as f: json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)


def main():
    review = P/'review_final_v1.md'; assert review.exists()
    updates = read(P/'navigation_update_v1.json')
    previous = read(B/'source_final_v1.json')['preserved']
    previous_prefixes = {(r['path'], r['expected_sha256']): r for r in previous if r.get('snapshot')}
    own_prefixes = {(r['path'], r['before_sha256']): r['before_snapshot'] for r in updates}
    for row in updates:
        snapshot = Path(row['before_snapshot']).read_bytes(); current = Path(row['path']).read_bytes()
        assert sha(row['before_snapshot']) == row['before_sha256'] and sha(row['path']) == row['after_sha256']
        assert current.startswith(snapshot) and current.decode().splitlines()[row['append_heading_line']-1].startswith('##')
    seen = set(); preserved = []
    def verify(path, expected):
        key = (path, expected)
        if key in seen: return
        seen.add(key)
        if sha(path) == expected:
            preserved.append({'path': path, 'expected_sha256': expected, 'resolution': 'current exact'}); return
        snapshot = own_prefixes.get(key) or previous_prefixes.get(key, {}).get('snapshot')
        assert snapshot and sha(snapshot) == expected, (path, 'unexpected modification')
        assert Path(path).read_bytes().startswith(Path(snapshot).read_bytes()), (path, 'original prefix changed')
        preserved.append({'path': path, 'expected_sha256': expected, 'resolution': 'exact original prefix snapshot of authorized append', 'snapshot': snapshot})
    for row in previous: verify(row['path'], row['expected_sha256'])
    for row in read(B/'artifact_inventory_v1.json')['files']: verify(row['path'], row['sha256'])
    for folder in P.glob('search_v*'):
        before = folder/'inputs_before.json'
        if before.exists():
            for path, digest in read(before).items(): verify(path, digest)
    for file in P.glob('native_*/attempt.json'):
        for path, digest in read(file)['input_sha256'].items(): verify(path, digest)
    for file in P.glob('native_analysis*.json'):
        if file.name == 'native_analysis_low_v1.json': continue
        for path, digest in read(file)['input_sha256'].items(): verify(path, digest)
    for path,digest in read(P/'failure_audit_v2.json')['input_sha256'].items(): verify(path,digest)
    for file in [P/'artifact_brief_v1.json']:
        for path,digest in read(file)['input_sha256'].items(): verify(path,digest)
    for pattern in ('*right_block*.py','RIGHT_BLOCK_CRADLE*.md'):
        for file in A.glob(pattern): verify(str(file),sha(file))
    def provenance(node):
        if isinstance(node, list):
            for child in node: provenance(child)
        elif isinstance(node, dict):
            if isinstance(node.get('path'), str) and 'sha256' in node: verify(node['path'], node['sha256'])
            for key, child in node.items():
                if key.startswith('/') and isinstance(child,str) and re.fullmatch('[0-9a-f]{64}',child): verify(key,child)
                if key.startswith('/') and isinstance(child, dict):
                    for value in (child, child.get('before', {}), child.get('after', {})):
                        if 'sha256' in value: verify(key, value['sha256'])
                provenance(child)
    for file in (P/'artifacts_v1').glob('provenance_v*.json'): provenance(read(file))
    videos = read(V/'manifest_v1.json')['videos']
    native = {f.parent.name: read(f) for f in P.glob('native_*/report.json')}
    assert len(native) == 12 and sum(r['completed'] for r in native.values()) == 11
    assert len(videos) == 24 and len({r['destination'] for r in videos}) == 24
    for case in native:
        assert sum(r['case'] == case for r in videos) == 2
        assert {r['view'] for r in videos if r['case'] == case} == {'whole_body','hands'}
    for row in videos:
        verify(row['source'],row['source_sha256']); verify(row['destination'],row['copy_sha256'])
        assert row['source_sha256'] == row['copy_sha256']
        completed = native[row['case']]['completed']
        assert row['ffprobe']['nb_read_frames'] == ('151' if completed else '2')
        assert row['ffprobe']['avg_frame_rate'] == '30/1'
        assert abs(float(row['ffprobe']['duration'])-(5.033333 if completed else .066667)) < 1e-6
    result = read(P/'native_analysis_final_v1.json'); cases = result['cases']
    assert result['passed'] and len(cases) == 11
    wave = cases['native_elbow5_close']; comparison = result['comparisons']['native_elbow5_close']
    assert comparison['static_case'] == 'native_static_close' and comparison['initial_full_state_and_first2p5s_trace_exact']
    assert comparison['max_same_time_body_centre_difference_mm'] < .1
    assert comparison['max_same_time_rotation_difference_deg'] < .05
    assert 10 < wave['elbow_actual_2p5_to_5s_range_deg'] < 10.3
    assert wave['body9_actual_small_motion_gate_passed'] and wave['both_contacts_elbow_wave_steps'] == 480
    assert wave['both_contacts_last_half_second_steps'] == 120 and wave['both_positive_last_half_second_steps'] == 56
    assert wave['contacts']['right_distal_guitar_contacts']['presence_steps'] == 0
    assert wave['contacts']['left_arm_hand_guitar_contacts']['presence_steps'] == 1072
    failed = native['native_static_body9_effort']
    assert not failed['completed'] and failed['physics_steps'] == 5 and failed['control_steps'] == 1
    rows = [row for f in P.glob('search_v*/search.json') for row in read(f)['rows']]
    assert len(rows) == 14 and sum(row['accepted_for_native'] for row in rows) == 2
    docs = [P/'README.md',P/'CHANGED_FILES_v1.md',A/'RIGHT_BLOCK_CRADLE_COMPLETION_V1.md']
    docs += list((P/'artifacts_v1').glob('*.md'))+list(V.glob('*.md'))
    docs += list(P.glob('CHANGED_FILES_v2.md'))
    links = 0
    for file in docs:
        for target in re.findall(r'\]\((/[^)]+)\)', file.read_text()):
            line = re.search(r':(\d+)$', target); path = re.sub(r':\d+$', '', target)
            assert Path(path).exists(), (str(file), path)
            if line: assert 1 <= int(line[1]) <= len(Path(path).read_text().splitlines())
            links += 1
    for file in A.glob('*right_block*.py'): ast.parse(file.read_text())
    ast.parse(Path(__file__).read_text())
    save(P/'source_final_v1.json', {'preserved': preserved, 'append_prefixes': updates,
         'scope': 'current source/native/analysis/failure/artifact inputs and previous complete saved-source closure+2570-file inventory; authorized main append snapshots; invalid low_v1 checksum preserved via canonical failure audit'})
    files = sorted(f for f in P.rglob('*') if f.is_file())+sorted(f for f in V.rglob('*') if f.is_file())
    save(P/'artifact_inventory_v1.json', {'files': [{'path': str(f), 'sha256': sha(f), 'bytes': f.stat().st_size} for f in files]})
    save(P/'final_verification_v1.json', {'passed': True, 'preserved_input_versions': len(preserved), 'inventory_files': len(files),
         'links_checked':links,'native_attempts':12,'native_execution_completed':11,'native_safety_aborted':1,
         'native_total_physics_steps':sum(r['physics_steps'] for r in native.values()),
         'native_total_control_ticks':sum(r['control_steps'] for r in native.values()),'training_updates':0,
         'source_final_candidates':14,'source_rejected':12,'source_accepted':2,'video_copies':24,
         'authorized_navigation_appends':3,'review_path':str(review),'review_sha256':sha(review),
         'scope':'one5s static and one scalar elbow cycle with sampled 240Hz endpoint two-region presence; left-thumb/thigh remain; no passive force closure/right-only/all-motion/music/repeatability certification'})
    print('passed', len(preserved), 'preserved input versions;', len(files), 'inventory files;', links, 'links')


if __name__ == '__main__': main()
