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
B = P.parent/'right_block_cradle_v1'
V = D/'video/right_thigh_waist_v1'


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
    updates = read(P/'navigation_update_v1.json')+read(P/'workflow_update_v1.json')
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
    for file in P.glob('analysis_*/*.json'):
        value=read(file)
        for path,digest in value.get('input_sha256',{}).items():verify(path,digest)
        for path,digest in value.get('support',{}).get('input_sha256',{}).items():verify(path,digest)
    for path,digest in read(P/'partial_analysis_v1.json')['input_sha256'].items():verify(path,digest)
    for file in [P/'artifact_brief_v1.json']:
        for path,digest in read(file)['input_sha256'].items(): verify(path,digest)
    for pattern in ('*right_thigh_waist*.py','left_arm_clearance_source_v*.py','RIGHT_THIGH_WAIST*.md'):
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
    assert len(native) == 3 and sum(r['completed'] for r in native.values()) == 2
    assert len(videos) == 6 and len({r['destination'] for r in videos}) == 6
    for case in native:
        assert sum(r['case'] == case for r in videos) == 2
        assert {r['view'] for r in videos if r['case'] == case} == {'whole_body','hands'}
    for row in videos:
        verify(row['source'],row['source_sha256']); verify(row['destination'],row['copy_sha256'])
        assert row['source_sha256'] == row['copy_sha256']
        completed = native[row['case']]['completed']
        assert row['ffprobe']['nb_read_frames'] == ('151' if completed else '145')
        assert row['ffprobe']['avg_frame_rate'] == '30/1'
        assert abs(float(row['ffprobe']['duration'])-(5.033333 if completed else 4.833333)) < 1e-6
    result=read(P/'analysis_final_v1/analysis.json');cases=result['support']['cases']
    assert result['passed'] and result['support']['passed'] and len(cases)==2
    wave=cases['native_elbow5_v1'];comparison=result['support']['comparisons']['native_elbow5_v1']
    assert comparison['static_case']=='native_static_v2' and comparison['initial_full_state_and_first2p5s_trace_exact']
    assert comparison['max_same_time_body_centre_difference_mm']<.2 and comparison['max_same_time_rotation_difference_deg']<.2
    assert 10<wave['elbow_actual_2p5_to_5s_range_deg']<10.3 and wave['body9_actual_small_motion_gate_passed']
    assert wave['Thorax_last_half_second_presence_steps']==0
    assert wave['contacts']['right_distal_guitar_contacts']['presence_steps']==0
    for row in result['waist_regions'].values():
        assert row['waist_presence_steps']==row['waist_positive_steps']==1198
        assert row['waist_last_half_second_presence_steps']==row['waist_last_half_second_positive_steps']==120
    failed=native['native_static_v1'];assert not failed['completed'] and failed['physics_steps']==1148 and failed['control_steps']==287
    rows=[row for f in P.glob('search_v*/search.json') for row in read(f)['rows']]
    assert len(rows)==9 and sum(row['accepted_for_native'] for row in rows)==2
    docs=[P/'README.md',P/'CHANGED_FILES_v1.md',A/'RIGHT_THIGH_WAIST_COMPLETION_V1.md']
    docs+=list((P/'artifacts_v1').glob('*.md'))+list(V.glob('*.md'))+list(P.glob('CHANGED_FILES_v2.md'))
    links = 0
    for file in docs:
        for target in re.findall(r'\]\((/[^)]+)\)', file.read_text()):
            line = re.search(r':(\d+)$', target); path = re.sub(r':\d+$', '', target)
            assert Path(path).exists(), (str(file), path)
            if line: assert 1 <= int(line[1]) <= len(Path(path).read_text().splitlines())
            links += 1
    for pattern in ('*right_thigh_waist*.py','left_arm_clearance_source_v*.py'):
        for file in A.glob(pattern):ast.parse(file.read_text())
    ast.parse(Path(__file__).read_text())
    save(P/'source_final_v1.json', {'preserved': preserved, 'append_prefixes': updates,
         'scope': 'recorded source/native/analysis/partial/artifact inputs and previous41481-version closure+7222-file inventory; main3+manual append prefixes; source1 missing35 STL before pins explicitly limited, not retro-certified'})
    files = sorted(f for f in P.rglob('*') if f.is_file())+sorted(f for f in V.rglob('*') if f.is_file())
    save(P/'artifact_inventory_v1.json', {'files': [{'path': str(f), 'sha256': sha(f), 'bytes': f.stat().st_size} for f in files]})
    save(P/'final_verification_v1.json', {'passed': True, 'preserved_input_versions': len(preserved), 'inventory_files': len(files),
         'links_checked':links,'native_attempts':3,'native_execution_completed':2,'native_safety_aborted':1,
         'native_total_physics_steps':sum(r['physics_steps'] for r in native.values()),
         'native_total_control_ticks':sum(r['control_steps'] for r in native.values()),'training_updates':0,
         'source_final_candidates':9,'source_rejected':7,'source_accepted':2,'video_copies':6,
         'authorized_navigation_appends':3,'authorized_manual_appends':1,'review_path':str(review),'review_sha256':sha(review),
         'scope':'sampled240Hz waist flank contacts in two5s runs, one scalar elbow cycle; source1 before-STL limitation; Thorax final absent, left fingers/upper-arm remain; no passive/right-only/hip-only/all-motion/music/repeatability guarantee'})
    print('passed', len(preserved), 'preserved input versions;', len(files), 'inventory files;', links, 'links')


if __name__ == '__main__': main()
