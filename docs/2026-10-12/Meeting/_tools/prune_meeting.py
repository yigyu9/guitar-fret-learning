"""Keep representative meeting copies; originals are never removed."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import re
import sys

M = Path(__file__).resolve().parents[1]
p = M / 'MATERIAL_MANIFEST.json'
manifest = json.loads(p.read_text())
shortlist = json.loads((M / 'SHORTLIST_MANIFEST.json').read_text())
records = manifest['records']
by_id = {r['id']: r for r in records}
keep = {r['id'] for key in ('videos', 'images') for r in shortlist[key]}
extra = {
 'V0373': '기존 Fret 35,000 전체곡 배경 비교',
 'V0032': '자유 기타 기본 환경 전신',
 'V0075': '기타 기준 양손 준비 자세',
 'V0100': '엄지와 여러 손가락의 넥 지지 시험',
 'V0353': '팀원 범위 검사: 현재 환경 조건',
 'V0355': '팀원 범위 검사: 보고된 중심 조건',
 'V0357': '팀원 범위 검사: 보고된 기준 조건',
 'I0015': '초기 겹침 형상 진단',
 'I0210': '회전 허용 범위 전체 비교: 정면',
 'I0212': '회전 허용 범위 전체 비교: 측면',
 'I0213': '이동 허용 범위 전체 비교: 정면',
 'I0215': '이동 허용 범위 전체 비교: 측면',
 'I0506': '병렬 학습 CP315와 CP316 장면 비교',
 'I0536': '보상 설계 점검 시각화',
 'I0701': '팀원이 제공한 기타 자세 판정표',
 'I0748': '과거 부위별 보상 설계 제안',
}
keep.update(extra)
# Preserve every source directly cited by the six reports and media shortlist.
for doc in M.glob('*.md'):
 if doc.name.endswith('_INDEX.md'):
  continue
 for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', doc.read_text()):
  filename = Path(target.strip('<>')).name
  rid = filename.split('__')[0]
  if rid in by_id:
   keep.add(rid)
keep.update('D0091 D0168 D0326 D0333 D0418 D0461 D0602 D0684 D1025 D1101 D1105'.split())
keep.update('D1194 D1195 D1210 D1211 D1216 D1222 D1269 D1272'.split())
# The whole-project plans provide background for parts discussed at the meeting.
for r in records:
 if r['kind'] == 'document' and '/master_plan/' in r['source']:
  keep.add(r['id'])
assert keep <= by_id.keys(), sorted(keep - by_id.keys())
retained = [r for r in records if r['id'] in keep]
removed = [r for r in records if r['id'] not in keep]
counts = dict(Counter(r['kind'] for r in retained))
print(json.dumps({'before': manifest['counts'], 'after': counts,
                  'remove': len(removed), 'retained_MiB': round(sum(r['bytes'] for r in retained)/1048576, 1)}, ensure_ascii=False, indent=2))
if '--apply' not in sys.argv:
 raise SystemExit(0)
# Validate all deletion targets before deleting any file.
for r in removed:
 target = Path(r['destination'])
 assert target.resolve().is_relative_to(M)
 assert target.is_file() and not target.is_symlink()
 assert hashlib.sha256(target.read_bytes()).hexdigest() == r['sha256'], r['id']
audit = {
 'created_utc': datetime.now(timezone.utc).isoformat(),
 'scope': 'Meeting copies only; research originals unchanged',
 'before_counts': manifest['counts'], 'after_counts': counts,
 'removed': [{'id': r['id'], 'source': r['source'], 'removed_copy': r['destination'],
              'sha256': r['sha256'], 'reason': '중간 시행·반복 프레임·이전 버전·미팅 설명에 쓰지 않는 진단 사본'} for r in removed]
}
(M / 'REMOVAL_MANIFEST.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2)+'\n')
for r in removed:
 Path(r['destination']).unlink()
for root in ('video', 'image', 'document'):
 for folder in sorted((M/root).rglob('*'), key=lambda x: len(x.parts), reverse=True):
  if folder.is_dir() and not any(folder.iterdir()):
   folder.rmdir()
manifest['records'] = retained
manifest['counts'] = counts
manifest['total_bytes'] = sum(r['bytes'] for r in retained)
manifest['selection_updated_utc'] = audit['created_utc']
manifest['scope'] = '대표 사례로 축약한 미팅 자료; 원본 연구 자료는 보존'
p.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
for kind, name in [('video', 'VIDEO_INDEX.md'), ('image', 'IMAGE_INDEX.md'), ('document', 'DOCUMENT_INDEX.md')]:
 title = {'video':'남겨 둔 동영상', 'image':'남겨 둔 이미지', 'document':'남겨 둔 근거 문서'}[kind]
 lines = [f'# {title}', '', '중간 반복 자료를 제외하고 대표 사례를 남겼습니다. V·I·D 번호는 기존 번호를 유지합니다.', '']
 for category, label in manifest['categories'].items():
  selected = [r for r in retained if r['kind']==kind and r['category']==category]
  if not selected: continue
  lines.extend([f'## {label}', ''])
  for r in selected:
   text = extra.get(r['id'], r.get('title') or r['label'])
   lines.append(f"- [{r['id']} — {text}]({r['destination']})")
   lines.append(f"  - 원본: `{r['source']}`")
  lines.append('')
 (M/name).write_text('\n'.join(lines)+'\n')
readme = (M/'README.md').read_text()
for kind, old, new in [('video',397,counts['video']),('image',1377,counts['image']),('document',1947,counts['document'])]:
 readme = readme.replace(f'|{old}|', f'|{new}|')
readme = readme.replace('총 약493.7MB입니다.', f"총 약{manifest['total_bytes']/1048576:.1f}MiB입니다.")
readme = re.sub(r'## 자료 검증\n.*', '', readme, flags=re.S)
readme = readme.replace('이미지에는 요약 그림과 시작 및 중간 및 끝 프레임을 넣었습니다.', '이미지에는 주요 비교 그림과 대표 장면을 남겼습니다.')
readme += '''## 반복 자료 정리\n\n반복 초기각 탐색, 비슷한 중간 체크포인트, 영상마다 추출한 반복 프레임, 이전 캡션·시각화 버전, 세부 진단 JSON과 실행 도구 사본을 줄였습니다. 기존 추천 영상 19개와 이미지 11개는 모두 유지하고, Fret 원본 기준선과 초기 환경 및 자세 범위 비교 자료도 남겼습니다. 각 연구 단계의 실패 사례와 보고 수치의 근거는 보존했습니다.\n\n원본 연구 폴더의 파일은 삭제하지 않았습니다. [제거한 사본의 원본 경로](/home/ajou/yigyu/3/docs/2026-10-12/Meeting/REMOVAL_MANIFEST.json)로 다시 찾을 수 있습니다. [최종 검증 기록](/home/ajou/yigyu/3/docs/2026-10-12/Meeting/COLLECTION_VERIFICATION.json)도 포함했습니다.\n'''
(M/'README.md').write_text(readme)
(M/'WORK_PLAN.md').write_text('''# 미팅 자료 반복본 정리\n\n- [x] 기존 추천 자료와 요약 문서에서 인용한 근거를 확인한다.\n- [x] 단계별 대표 영상, 범위 비교 이미지, 핵심 근거 문서를 남긴다.\n- [x] Meeting 안의 불필요한 사본만 제거하고 원본 경로를 기록한다.\n- [x] 목록과 파일 수를 갱신한다.\n- [ ] 남은 파일의 해시와 문서 링크를 검증한다.\n''')
# Initial broad collector would recreate removed copies; omit obsolete preparation tools.
for name in ('collect_materials.py', 'write_meeting_documents.py', 'collection.log'):
 target=M/'_tools'/name
 if target.is_file(): target.unlink()
