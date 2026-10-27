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
B = P.parent/'dual_checkpoint_shoulder_v1'
V = D/'video/left_neck_near_initial_v1'


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
    for file in P.glob('native_analysis_v*.json'):
        for path, digest in read(file)['input_sha256'].items(): verify(path, digest)
    def provenance(node):
        if isinstance(node, list):
            for child in node: provenance(child)
        elif isinstance(node, dict):
            if isinstance(node.get('path'), str) and 'sha256' in node: verify(node['path'], node['sha256'])
            for key, child in node.items():
                if key.startswith('/') and isinstance(child, dict):
                    for value in (child, child.get('before', {}), child.get('after', {})):
                        if 'sha256' in value: verify(key, value['sha256'])
                provenance(child)
    for file in (P/'artifacts_v1').glob('provenance_v*.json'): provenance(read(file))
    videos = read(V/'manifest_v1.json')['videos']
    expected = {'hold_v1': ('151', 5.033333), 'hold_v2': ('56', 1.866667),
                'hold_v3': ('151', 5.033333), 'hold_v4': ('151', 5.033333), 'pair_v1': ('74', 2.466667)}
    assert len(videos) == 10 and len({r['destination'] for r in videos}) == 10
    for case in expected:
        assert sum(r['case'] == case for r in videos) == 2
        assert {r['view'] for r in videos if r['case'] == case} == {'whole_body', 'hands'}
    for row in videos:
        verify(row['source'], row['source_sha256']); verify(row['destination'], row['copy_sha256'])
        assert row['source_sha256'] == row['copy_sha256']
        frames, duration = expected[row['case']]
        assert row['ffprobe']['nb_read_frames'] == frames and row['ffprobe']['avg_frame_rate'] == '30/1'
        assert abs(float(row['ffprobe']['duration'])-duration) < 1e-6
    result = read(P/'native_analysis_v3.json'); cases = result['cases']
    assert len(cases) == 5 and sum(c['completed'] for c in cases.values()) == 4
    assert cases['native_hold_v2']['failure']['type'] == 'ValueError' and cases['native_hold_v2']['physics_steps'] == 440
    assert cases['native_pair_v1']['paired_inference_ticks'] == 26
    assert cases['native_pair_v1']['Fret_done'] == [False] and cases['native_pair_v1']['Strike_done'] == [True]
    rows = read(P/'search_v5/search.json')['rows']; assert sum(r['accepted_for_native'] for r in rows) == 1
    docs = [P/'README.md', P/'CHANGED_FILES_v1.md', A/'LEFT_NECK_NEAR_INITIAL_COMPLETION_V1.md']
    docs += list((P/'artifacts_v1').glob('*.md'))+list(V.glob('*.md'))
    links = 0
    for file in docs:
        for target in re.findall(r'\]\((/[^)]+)\)', file.read_text()):
            line = re.search(r':(\d+)$', target); path = re.sub(r':\d+$', '', target)
            assert Path(path).exists(), (str(file), path)
            if line: assert 1 <= int(line[1]) <= len(Path(path).read_text().splitlines())
            links += 1
    for pattern in ('*left_neck_near_v*.py', 'left_near*.py'):
        for file in A.glob(pattern): ast.parse(file.read_text())
    ast.parse(Path(__file__).read_text())
    save(P/'source_final_v1.json', {'preserved': preserved, 'append_prefixes': updates,
         'scope': 'current source/native/analysis/artifact input hashes and previous complete saved-source closure+353-file inventory; authorized main append snapshots'})
    files = sorted(f for f in P.rglob('*') if f.is_file())+sorted(f for f in V.rglob('*') if f.is_file())
    save(P/'artifact_inventory_v1.json', {'files': [{'path': str(f), 'sha256': sha(f), 'bytes': f.stat().st_size} for f in files]})
    save(P/'final_verification_v1.json', {'passed': True, 'preserved_input_versions': len(preserved), 'inventory_files': len(files),
         'links_checked': links, 'native_attempts': 5, 'native_execution_completed': 4, 'native_safety_aborted': 1,
         'native_total_physics_steps': sum(c['physics_steps'] for c in cases.values()),
         'native_total_control_ticks': sum(c['control_ticks'] for c in cases.values()), 'training_updates': 0,
         'source_CPU_interrupted': 2, 'source_final_candidates': 6, 'source_rejected': 5, 'source_accepted': 1,
         'video_copies': 10, 'authorized_navigation_appends': 3, 'review_path': str(review), 'review_sha256': sha(review),
         'scope': 'initial-near layout and one5s finite preparation improvement; pair original Strike failure, no song completion/continuous cooked certification'})
    print('passed', len(preserved), 'preserved input versions;', len(files), 'inventory files;', links, 'links')


if __name__ == '__main__': main()
