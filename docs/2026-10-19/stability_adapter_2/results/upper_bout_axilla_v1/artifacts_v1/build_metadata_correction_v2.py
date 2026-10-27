#!/usr/bin/env python3
"""Create a metadata-only correction without changing consumed V1 artifacts."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

BASE = Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1')
ART = BASE / 'artifacts_v1'
PRODUCER = ART / 'build_metadata_correction_v2.py'
README1 = ART / 'README_V1.md'
README2 = ART / 'README_V2.md'
PROV2 = ART / 'provenance_v2.json'
INPUTS = [
    README1, ART / 'provenance_v1.json', ART / 'build_archive_v1.py',
    ART / 'native_timeline_0_2_5s.png', ART / 'weakcase_motor_reference_vs_contact_v1.png',
    BASE / 'result_summary_v2.json', BASE / 'contact_region_v2.json',
    BASE / 'search_v3' / 'search.json', BASE / 'search_v4' / 'search.json',
    BASE / 'search_v5' / 'search.json', BASE / 'analysis_v1' / 'verification.json',
    BASE / 'analysis_v2' / 'verification.json', BASE / 'analysis_v3' / 'verification.json',
    Path('/home/ajou/yigyu/3/stability_adapter_2/assets/om_body_geometry_v3/manifest.json'),
]

def digest(path: Path) -> dict:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    st = path.stat()
    return {'sha256': h.hexdigest(), 'bytes': st.st_size, 'mtime_ns': st.st_mtime_ns}

before = {str(p): digest(p) for p in INPUTS}
text = README1.read_text(encoding='utf-8')
old = '세 조건 모두 실제 native 5초 완료이며 source v5 geometry 후보를 유지했습니다. root/lower body 고정, strap OFF, 기타 자유, left grip 없음, 기타에 직접 힘 없음입니다. Native1/2는 source right-bout geometry 조건에서 기존 forearm control과 upper-arm motor-point reference를 사용했고, native3은 upper-point effort를 gentle press로 변경했습니다. 여러 controller·기하·몸통 조건이 함께 달라졌으므로 차이를 한 설정의 단독 효과로 귀속하지 않습니다. Full native initial states는 native2/native3 exact match이고 세 조건 guitar initial pose는 같았습니다.'
new = ('세 조건 모두 실제 native 5초 완료입니다. Native1/2/3에는 search_v3에서 선택된 right4_upper35/right6_upper35 후보만 사용했고, OM asset v3은 동일하게 유지했습니다. Search_v4와 search_v5 후보는 native로 실행하지 않았습니다. 특히 search_v5의 right4_forward6_shift_upper35는 shoulder 전체 캡슐 source gap이 −0.0225 mm이고 지정 proximal 35% source gap이 8.902 mm여서 native 후보에서 제외됐습니다. root/lower body 고정, strap OFF, 기타 자유, left grip 없음, 기타 직접 힘 없음입니다. Native1/2는 기존 forearm control과 upper-arm motor-point reference를 사용했고, native3은 upper-point effort를 gentle press로 변경했습니다. 여러 controller·기하·몸통 조건이 함께 달라졌으므로 차이를 한 설정의 단독 효과로 귀속하지 않습니다. Full native initial states는 native2/native3 exact match이고 세 조건 guitar initial pose는 같았습니다.')
if text.count(old) != 1:
    raise RuntimeError('README V1 opening paragraph was not uniquely found')
text = text.replace(old, new)
text = text.replace('source-qualified proximal contact는 0/1200이었습니다.', 'native 공간 분류에서 지정된 proximal contact는 0/1200이었습니다.')
text = text.replace('Contact-region 검사에서는 shoulder-side 35%와 upper-bulge 규정 영역의 접촉이 세 조건 모두 0/1200으로 분류됐습니다.', 'Native 공간 분류에서는 shoulder-side 35%와 upper-bulge 지정 영역 접촉을 세 조건 모두 0/1200으로 기록했습니다.')
image_path = '/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/artifacts_v1/weakcase_motor_reference_vs_contact_v1.png)'
lines = text.splitlines()
seen_image = False
kept = []
for line in lines:
    if image_path in line:
        if seen_image:
            continue
        seen_image = True
    kept.append(line)
if not seen_image:
    raise RuntimeError('Weak-case image reference not found')
text = '\n'.join(kept) + '\n'
text = '# 정정본 안내\n\n이 문서는 README_V1의 native 후보 출처 문구를 바로잡은 새 판입니다. README_V1과 기존 이미지·영상은 보존했습니다.\n\n' + text
README2.write_text(text, encoding='utf-8')
after = {str(p): digest(p) for p in INPUTS}
if before != after:
    raise RuntimeError('A pinned input changed while producing the correction')
producer_hash = digest(PRODUCER)
prov = {
    'purpose': 'README metadata correction only; no native simulation, training, image regeneration, or video copy.',
    'inputs_before': before,
    'inputs_after': after,
    'outputs': {str(README2): digest(README2)},
    'producer': {str(PRODUCER): producer_hash},
    'corrections': [
        'Native trials used search_v3 right4_upper35/right6_upper35 and the same OM asset v3.',
        'search_v4/search_v5 candidates were not native-run; search_v5 candidate is explicitly recorded as rejected.',
        'Changed source-qualified wording to native spatial classification wording.',
        'Removed duplicate embed of the weak-case annotated image.'
    ],
}
PROV2.write_text(json.dumps(prov, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'readme': str(README2), 'readme_sha256': digest(README2)['sha256'], 'provenance': str(PROV2), 'provenance_sha256': digest(PROV2)['sha256'], 'inputs_unchanged': True}, ensure_ascii=False))
