#!/usr/bin/env python3
"""Create the Korean V2 wording correction while preserving the consumed V1 artifacts."""
from pathlib import Path
import hashlib, json

A = Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_body_approach_v1/artifacts_v1')
V = Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_body_approach_v1')
source = A/'README_V1.md'
target = A/'README_V2.md'
inputs = [source, A/'build_artifacts_v1.py', A/'provenance_v1.json', A/'initial_six_whole_body.png', A/'initial_six_right_blocks_crop.png', A/'inset6_whole_body_timeline.png', A/'inset6_hands_timeline.png', V/'INDEX_V1.md', V/'manifest_v1.json']

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''): h.update(chunk)
    return h.hexdigest()

def pins(): return {str(p): {'sha256':sha(p),'bytes':p.stat().st_size} for p in inputs}

before=pins()
s=source.read_text()
replacements=[
 ('`inset`은 humanoid의 고정된 수평 전방축을 따른 이동량이며 world-Y 단독 이동이 아니다.', '`inset`은 humanoid의 고정된 수평 전방축 반대 방향, 즉 몸쪽으로 이동한 거리이며 world-Y 단독 이동이 아니다.'),
 ('## 선택 조건: inset 6 mm', '## 비교용 조건: inset 6 mm'),
 ('6 mm의 물리 실행은 5.0초(1200 physics steps) 완료됐다.', '6 mm는 비교를 위한 물리 실행이며 새 기본값으로 채택한 조건이 아니다. 물리 실행은 5.0초(1200 physics steps) 완료됐다.'),
 ('여섯 조건 전신·손 영상 10개의 원본–사본 해시와 ffprobe 메타데이터는', '새 실행 다섯 조건의 전신·손 영상 10개만 복사했다. 기준 조건은 초기 이미지 비교에만 사용했으며 영상 복사에는 포함하지 않았다. 원본–사본 해시와 ffprobe 메타데이터는'),
]
for old,new in replacements:
    if s.count(old)!=1: raise SystemExit(f'expected exactly one source phrase: {old!r}, found {s.count(old)}')
    s=s.replace(old,new)
# Keep the original link clauses after replacing the lead-in.
target.write_text(s)
after=pins()
if before!=after: raise SystemExit('an input changed during correction')
prov={
 'scope':'문서 문구 3건 정정만; native/물리 실행 0회, 영상 재복사 0회',
 'corrections':[
  'inset 방향을 고정 수평 전방축의 반대(몸쪽) 이동으로 명시',
  '6 mm를 비교용으로 표시하고 새 기본값으로 채택하지 않았음을 명시',
  '영상 10개가 새 다섯 실행의 전신·손이며 baseline은 초기 이미지 비교에만 사용했음을 명시'
 ],
 'input_before':before,
 'input_after':after,
 'outputs':[
  {'path':str(target),'sha256':sha(target),'bytes':target.stat().st_size},
  {'path':str(Path(__file__)),'sha256':sha(Path(__file__)),'bytes':Path(__file__).stat().st_size}
 ]
}
(A/'provenance_v2.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n')
