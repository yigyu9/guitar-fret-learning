"""Final source/document index; large raw outputs are in the sealed inventory."""
import ast,hashlib,json
from pathlib import Path
R=Path('/home/ajou/yigyu/3');G=R/'docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1'
entries=json.loads((G/'changed_index_v1.json').read_text());known={e['path'] for e in entries}
paths=list(G.glob('*.py'))+list(G.glob('*.md'))
paths.extend([R/'docs/2026-10-12/video/README_ABSOLUTE_V5.md',R/'docs/2026-10-12/video/README_ABSOLUTE_V6.md'])
paths.extend(G.glob('artifacts_v3/*.py'));paths.extend(G.glob('artifacts_v3/*.md'))
for p in sorted(set(paths)):
    if str(p) in known:continue
    line=1
    if p.suffix=='.py':
        functions=[n for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,(ast.FunctionDef,ast.ClassDef))]
        if functions:line=min(n.lineno for n in functions)
    entries.append({'path':str(p),'line':line,'description':'새 구현·검증·운영/산출물 정리 파일'})
for e in entries:e['sha256_at_index_creation']=hashlib.sha256(Path(e['path']).read_bytes()).hexdigest();e.pop('sha256',None)
with (G/'CHANGED_FILES_V2.md').open('x') as f:
    f.write('# 최종 변경 파일과 실제 위치\n\n새구현·검증·계획·설명문서의절대경로와실제줄번호다. 원시로그/JSON/이미지/영상 전체의절대경로와최종SHA는 `artifact_inventory_v1.json`에서확인한다(봉인단계생성). 이전소스·산출물은보존했다.\n\n| 파일 | 내용 |\n|---|---|\n')
    for e in entries:f.write(f"| [{Path(e['path']).name}]({e['path']}:{e['line']}) | {e['description']} |\n")
with (G/'changed_index_v2.json').open('x') as f:json.dump(entries,f,ensure_ascii=False,indent=2)
print('indexed source/document files',len(entries))
