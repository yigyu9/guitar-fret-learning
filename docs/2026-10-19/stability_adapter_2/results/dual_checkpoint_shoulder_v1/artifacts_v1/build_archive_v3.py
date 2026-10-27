#!/usr/bin/env python3
"""Create text-only V3 corrections and a corrected video index; never copies media."""
from pathlib import Path
import hashlib, json

P = Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/artifacts_v1')
V = Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/dual_checkpoint_shoulder_v1')
README_IN = P / 'README_V2.md'
README_OUT = P / 'README_V3.md'
INDEX_OUT = V / 'INDEX_V2.md'
PROV_OUT = P / 'provenance_v3.json'
SCRIPT = P / 'build_archive_v3.py'
MANIFEST = V / 'manifest_v1.json'
INDEX_OLD = V / 'INDEX_V1.md'
PROV_OLD = P / 'provenance_v2.json'

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def record(path):
    st = path.stat()
    return {'sha256': sha(path), 'bytes': st.st_size, 'mtime_ns': st.st_mtime_ns}

inputs = [README_IN, MANIFEST, INDEX_OLD, PROV_OLD]
before = {str(p): record(p) for p in inputs}
source = README_IN.read_text(encoding='utf-8')
old_phrase = '실제 누름, 해결된 관절 event, 관절 crossing은 관측되지 않았습니다.'
new_phrase = '실제 누름은 관측되지 않았고, 양손 공동 음악 평가에서 정산된 이벤트는 0건이며 현 crossing도 0건입니다.'
assert source.count(old_phrase) == 1
text = source.replace(old_phrase, new_phrase)
old_count = '원본 전신·손 영상 2개는 [영상 색인]'
new_count = '보관된 원본 영상은 총 4개(새 전체 연결 실행 2개와 이전 5초 정지 기준 2개)입니다. 물리 실행 집계에는 이전 기준 영상 2개를 포함하지 않습니다. 사례별 재생 시간과 파일은 [최신 영상 색인]'
assert text.count(old_count) == 1
text = text.replace(old_count, new_count)
text = text.replace('INDEX_V1.md)', 'INDEX_V2.md)')
text += '\n\n이 V3 문서는 V2 보존본의 공동 음악 이벤트 용어와 영상 사본 수 설명을 바로잡은 최신 설명입니다. V1/V2, 원본 영상 및 manifest는 변경하지 않았습니다.\n'
README_OUT.write_text(text, encoding='utf-8')

manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
rows = manifest['videos']
assert len(rows) == 4
assert sum(r['case'] == 'checkpoint_connection' for r in rows) == 2
assert sum(r['case'] == 'baseline_shoulder10mm' for r in rows) == 2
lines = [
    '# 두 체크포인트 연결 · 영상 색인 V2', '',
    'manifest에 기록된 byte-exact 원본 복사본은 총 4개입니다: 새 checkpoint 연결 실행의 전신·손 영상 2개와 연결 직전 shoulder-forward-10-mm 정지 기준의 전신·손 영상 2개입니다. 이 가운데 이번 연결 물리 실행의 영상은 2개이며, 이전 기준 영상은 별도 사례입니다.', '',
    '연결 실행은 물리 2.05초에 source terminal로 종료했고 영상은 63프레임 ÷ 30fps = 2.1초입니다. 이전 기준 사례는 물리 5.0초, 영상은 151프레임 ÷ 30fps = 5.033333초입니다. 영상은 재인코딩하지 않았습니다. SHA와 ffprobe는 [manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/dual_checkpoint_shoulder_v1/manifest_v1.json)에 있습니다.', '',
    '## 새 연결 실행 · checkpoint_connection', ''
]
for r in rows:
    if r['case'] != 'checkpoint_connection':
        continue
    view = '전신' if r['view'] == 'whole_body' else '손·기타 넥 방향'
    dest = r['destination']
    probe = r['ffprobe']
    lines.append(f"- [{view} 영상]({dest}) — {probe['nb_read_frames']}프레임, {probe['avg_frame_rate']}fps, 재생 {probe['duration']}초; 물리 실행은 2.05초에서 종료")
lines += ['', '## 이전 5초 정지 기준 · baseline_shoulder10mm', '']
for r in rows:
    if r['case'] != 'baseline_shoulder10mm':
        continue
    view = '전신' if r['view'] == 'whole_body' else '손·기타 넥 방향'
    dest = r['destination']
    probe = r['ffprobe']
    lines.append(f"- [{view} 영상]({dest}) — {probe['nb_read_frames']}프레임, {probe['avg_frame_rate']}fps, 재생 {probe['duration']}초; 이전 별도 기준 실행")
lines += ['', '사본 수는 파일 수이며 독립된 실험 조건 수를 뜻하지 않습니다. [SHA-256 manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/dual_checkpoint_shoulder_v1/manifest_v1.json)']
INDEX_OUT.write_text('\n'.join(lines) + '\n', encoding='utf-8')

# Ensure all declared source inputs stayed unchanged while producing docs.
after = {str(p): record(p) for p in inputs}
assert before == after
outs = [README_OUT, INDEX_OUT]
prov = {
    'task': 'V3 문구 정정 및 영상 색인 분류만; 원본/영상/manifest 불변',
    'physics_or_training_runs': 0,
    'video_copies_or_reencodes': 0,
    'corrections': [
        'JointMusicClock 결과를 양손 공동 음악 평가의 정산 이벤트 0건 및 현 crossing 0건으로 표현.',
        '4개 영상 사본을 연결 실행 2개와 이전 5초 정지 기준 2개로 구분하고 사례별 재생 시간을 명시.'
    ],
    'inputs_before_after': {p: {'before': before[p], 'after': after[p], 'unchanged': before[p] == after[p]} for p in before},
    'producer': {'path': str(SCRIPT), 'sha256': sha(SCRIPT), 'bytes': SCRIPT.stat().st_size},
    'outputs': {str(p): {'sha256': sha(p), 'bytes': p.stat().st_size} for p in outs},
    'manifest_video_rows': len(rows),
    'video_copy_count_by_case': {'checkpoint_connection': 2, 'baseline_shoulder10mm': 2}
}
PROV_OUT.write_text(json.dumps(prov, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'README': record(README_OUT), 'INDEX': record(INDEX_OUT), 'PROVENANCE': record(PROV_OUT), 'producer_sha256': sha(SCRIPT)}, ensure_ascii=False))
