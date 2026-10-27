#!/usr/bin/env python3
"""Create a text-only corrected README revision; preserve all consumed V1 outputs."""
from pathlib import Path
import hashlib, json

ART = Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/artifacts_v1')
BASE = ART.parent
VIDEO = Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_block_cradle_v1')
INPUTS = [
    ART / 'README_V1.md',
    ART / 'provenance_v1.json',
    ART / 'build_archive_v1.py',
    BASE / 'artifact_brief_v1.json',
    BASE / 'native_analysis_final_v1.json',
    BASE / 'failure_audit_v2.json',
    VIDEO / 'manifest_v1.json',
    VIDEO / 'INDEX_V1.md',
    Path(__file__),
]
README = ART / 'README_V2.md'
PROVENANCE = ART / 'provenance_v2.json'


def record(path):
    data = path.read_bytes()
    st = path.stat()
    return {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data), 'mtime_ns': st.st_mtime_ns}

before = {str(p): record(p) for p in INPUTS}
text = (ART / 'README_V1.md').read_text(encoding='utf-8')
old_a = 'source face-wrap 4·5는 실패해 실행하지 않았습니다.'
new_a = 'source 4·5의 6개 후보는 CPU 검사에서 거절되어 native로 실행하지 않았습니다.'
old_b = '**보관 산출물:** 위 세 이미지, byte-exact 24개 MP4, 한국어 README/색인, manifest 및'
new_b = '**보관 산출물:** 위 네 이미지(전신 패널·손 패널·초기 옆면·trace 그래프), byte-exact 24개 MP4, 한국어 README/색인, manifest 및'
if text.count(old_a) != 1 or text.count(old_b) != 1:
    raise RuntimeError('V1 문구가 예상과 다릅니다. 원문을 임의 변경하지 않습니다.')
text = text.replace(old_a, new_a).replace(old_b, new_b)
text += '\n\n> V2 정정: source 4·5 후보는 CPU 검사에서 거절되어 native 실행 대상이 아니었습니다. 이미지 목록은 본문에 포함된 네 이미지로 바로잡았습니다. V1 및 영상·이미지·manifest는 보존했습니다.\n'
README.write_text(text, encoding='utf-8')
after = {str(p): record(p) for p in INPUTS}
unchanged = all(before[k] == after[k] for k in before)
if not unchanged:
    raise RuntimeError('입력 파일이 작업 중 변경되었습니다.')
producer_rec = record(Path(__file__))
prov = {
    'purpose': '기존 README_V1의 이미지 개수 및 source 4·5 검사 설명만 바로잡은 문서 전용 정정',
    'native_runs': 0,
    'video_copies': 0,
    'image_regeneration': 0,
    'inputs_before_after': {
        k: {'before': before[k], 'after': after[k], 'unchanged': before[k] == after[k]}
        for k in before
    },
    'producer': {'path': str(Path(__file__)), **producer_rec},
    'output': {'path': str(README), **record(README)},
}
PROVENANCE.write_text(json.dumps(prov, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'readme': str(README), 'readme_sha256': record(README)['sha256'],
                  'provenance': str(PROVENANCE), 'inputs_unchanged': unchanged,
                  'input_count': len(INPUTS)}, ensure_ascii=False))
