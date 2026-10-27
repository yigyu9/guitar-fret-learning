"""Seal this phase after independent review, without rewriting consumed outputs."""
from pathlib import Path
import hashlib
import json
import re
import ast

R=Path('/home/ajou/yigyu/3');A=R/'stability_adapter_2'
P=R/'docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1'
V=R/'docs/2026-10-12/video/om_body_geometry_v1'
B=P.parent/'om_body_outline_v1'

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,d):
    p=P/n;assert not p.exists();p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def exact(p,h):assert sha(p)==h,str(p)

checks=read(P/'verification_v1.json');assert checks['passed']
for path,h in checks['input_sha256'].items():exact(path,h)
for path,h in read(P/'source_before_native_v1.json').items():exact(path,h)
for path,h in read(P/'settled_window_v1.json')['input_sha256'].items():exact(path,h)
for i in (1,2):
    assert read(P/f'native_exit_v{i}.json')['exit_code']==0
    assert read(P/f'native_v{i}/report.json')['completed']

start=read(P/'main_append_v1.json');end=read(P/'main_completion_append_v1.json')
main={e['path'] for e in start};snapshots={}
for phase in (B,P):
    for e in read(phase/'main_append_v1.json'):
        exact(e['snapshot'],e['before_sha256']);snapshots[(e['path'],e['before_sha256'])]=e['snapshot']
        assert Path(e['path']).read_bytes().startswith(Path(e['snapshot']).read_bytes())
for a,b in zip(start,end):
    assert a['path']==b['path'] and a['after_sha256']==b['before_sha256']
    exact(b['snapshot'],b['before_sha256']);exact(b['path'],b['after_sha256'])
    assert Path(b['path']).read_bytes().startswith(Path(b['snapshot']).read_bytes())

preserved=0
for phase in (B.parent/'acoustic_guitar_appearance_v1',B):
    old=read(phase/'final_verification_v1.json');assert old['passed']
    exact(phase/'source_final_v1.json',old['source_final_sha256'])
    exact(phase/'artifact_inventory_v1.json',old['inventory_sha256'])
    for e in read(phase/'artifact_inventory_v1.json')['files']:
        path=snapshots.get((e['path'],e['sha256']),e['path']) if e['path'] in main else e['path']
        exact(path,e['sha256']);preserved+=1

src=read(P/'artifacts_v1/source_provenance_v1.json')
for path,v in src['input_sha256_before_after'].items():
    assert v['before']==v['after'];exact(path,v['before'])
for path,h in src['outputs_sha256'].items():exact(path,h)
for name in ('native_media_provenance_v1.json','native_docs_provenance_v1.json'):
    d=read(P/'artifacts_v1'/name);assert d['inputs_before']==d['inputs_after']
    for records in (d['inputs_before'],d['outputs']):
        for path,v in records.items():exact(path,v['sha256'])

# Syntax checks without importing native libraries or writing bytecode.
new_sources=list(A.glob('*om*geometry*v*.py'))+[A/'extract_om_depth_v1.py',A/'search_om_right_clearance_v1.py',A/'search_om_right_clearance_v2.py']
for path in new_sources+[P/'analyze_native_v1.py',Path(__file__).resolve()]:ast.parse(path.read_text(),filename=str(path))
for path in list(P.rglob('*.md'))+list(V.glob('*.md')):
    for link in re.findall(r'\]\((/[^)]+)\)',path.read_text()):
        target=link.rsplit(':',1)[0] if re.search(r':\d+$',link) else link
        assert Path(target).exists(),(str(path),target)
review=P/'review_final_v1.md';assert review.exists() and review.stat().st_size>0
sources=set(new_sources+[A/'OM_BODY_GEOMETRY_PLAN_V1.md',Path(__file__).resolve(),P/'analyze_native_v1.py',review])|{Path(p) for p in main}
for i in (1,2,3):sources.update(f for f in (A/f'assets/om_body_geometry_v{i}').rglob('*') if f.is_file())
save('source_final_v1.json',{str(f):sha(f) for f in sorted(sources)})
files={f for base in (P,V) for f in base.rglob('*') if f.is_file()}|sources
save('artifact_inventory_v1.json',{'files':[{'path':str(f),'sha256':sha(f),'bytes':f.stat().st_size} for f in sorted(files)]})
save('final_verification_v1.json',{'passed':True,'source_and_native_inputs_exact':True,'native_runs':2,'physics_steps_total':2400,'native_frame_files_verified':1208,'prior_inventory_entries_preserved':preserved,'originals_preserved':True,'main4_append_only':True,'independent_review_sha256':sha(review),'source_final_sha256':sha(P/'source_final_v1.json'),'inventory_sha256':sha(P/'artifact_inventory_v1.json'),'stabilization_success_claim':False})
print(json.dumps({'passed':True,'prior_preserved':preserved,'inventory_files':len(files)}))
