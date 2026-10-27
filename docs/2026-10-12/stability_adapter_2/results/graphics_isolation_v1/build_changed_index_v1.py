"""Root path/line index from files that actually exist."""
import ast,hashlib,json
from pathlib import Path
R=Path('/home/ajou/yigyu/3');A=R/'stability_adapter_2';G=R/'docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1'
entries=[]
def add(path,description,symbol=None,heading=None):
    assert path.exists()
    text=path.read_text();line=1
    if symbol:
        line=next(n.lineno for n in ast.walk(ast.parse(text)) if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==symbol)
    if heading:line=next(i for i,s in enumerate(text.splitlines(),1) if heading in s)
    entries.append({'path':str(path),'line':line,'description':description,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
for name,description,symbol in (
 ('deadline_graphics_v1.py','학습−1/평가0 그래픽 장치 전달과 렌더 API 차단','graphics_wrapper'),
 ('deadline_native_v8.py','기존 native 제어를 유지한 그래픽 래퍼 연결','reset'),
 ('deadline_graphics_migration_v1.py','기존 물리·제어 ABI/소스 유지와 수치 불변 이행','migrate_payload'),
 ('run_deadline_training_v9.py','학습/영상 분리,5분 복구 저장,30분 공식 평가','main'),
 ('test_deadline_graphics_v1.py','CPU9검사·변경 거절 반례','GraphicsTests'),
 ('run_graphics_reset_probe_v1.py','원본 실패 진단 보존; 실제 비교는D 진단v2 사용','main')):add(A/name,description,symbol=symbol)
add(A/'GRAPHICS_ISOLATION_PLAN_V1.md','구현 계획과 단계별 검증')
for path in (A/'PLAN.md',A/'README.md',G.parents[1]/'README.md',G.parents[1]/'VISUAL_REPORT.md'):
    add(path,'기존 prefix 보존 후 검증 결과 추가',heading='그래픽 분리 실제 검증 완료')
for name,description,symbol in (
 ('run_graphics_reset_probe_v2.py','학습 ABI/감사 입력 분리;60회 초기화·전체 물리 비교','main'),
 ('verify_graphics_v1.py','checkpoint 수치·제어·영상 실제 검증','main'),
 ('launch_recorded_learning_v1.py','재개 supervisor와영상 자동 보관','archive_complete')):add(G/name,description,symbol=symbol)
for path,description in (
 (G/'README.md','결과 요약·현재 상태'),(G/'PROVENANCE_NOTE_V1.md','실패·그림정정·동일바이트재기록공개'),
 (G/'artifacts_v3/README.md','최신한글그림·영상설명'),(R/'docs/2026-10-12/video/README_ABSOLUTE_V4.md','영상10개·이전보관색인')):add(path,description)
with (G/'CHANGED_FILES_V1.md').open('x') as f:
    f.write('# 변경 파일과 실제 위치\n\n기존 소스는 보존하고 새버전으로 구현했다. main4는 기존 prefix를 유지한 append다. 결과물의 실행 시점 SHA와 최종값은 별도감사에 기록한다.\n\n')
    f.write('| 파일 | 내용 |\n|---|---|\n')
    for e in entries:f.write(f"| [{Path(e['path']).name}]({e['path']}:{e['line']}) | {e['description']} |\n")
with (G/'changed_index_v1.json').open('x') as f:json.dump(entries,f,ensure_ascii=False,indent=2)
