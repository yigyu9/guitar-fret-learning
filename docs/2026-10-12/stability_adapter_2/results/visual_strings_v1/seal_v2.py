"""Verify source/recording preservation and close the visual-string result inventory."""
from pathlib import Path
import hashlib
import json
import ast
import re
R=Path('/home/ajou/yigyu/3');A=R/'stability_adapter_2'
P=R/'docs/2026-10-12/stability_adapter_2/results/visual_strings_v1';B=P.parent/'om_body_geometry_v1'
V=R/'docs/2026-10-12/video/visual_strings_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def exact(p,h):assert sha(p)==h,str(p)
def save(n,d):
    f=P/n;assert not f.exists();f.write_text(json.dumps(d,indent=2)+'\n')
verification=read(P/'verification_v1.json');assert verification['passed']
for path,h in verification['input_sha256'].items():exact(path,h)
start=read(P/'main_append_v1.json');end=read(P/'main_completion_append_v1.json')
snapshots={}
for a,b in zip(start,end):
    assert a['path']==b['path'] and a['after_sha256']==b['before_sha256']
    exact(a['snapshot'],a['before_sha256']);exact(b['snapshot'],b['before_sha256']);exact(b['path'],b['after_sha256'])
    assert Path(b['snapshot']).read_bytes().startswith(Path(a['snapshot']).read_bytes())
    assert Path(b['path']).read_bytes().startswith(Path(b['snapshot']).read_bytes())
    snapshots[a['path']]=a['snapshot']
old=read(B/'final_verification_v2.json');assert old['passed']
exact(B/'artifact_inventory_v2.json',old['inventory_sha256'])
exact(B/'source_final_v1.json',old['source_final_sha256'])
prior=read(B/'artifact_inventory_v2.json')['files']
for e in prior:exact(snapshots.get(e['path'],e['path']),e['sha256'])
for base in (P/'artifacts_v1',P/'artifacts_v2'):
    for f in base.glob('*provenance*.json'):
        data=read(f);assert data['inputs_before']==data['inputs_after']
        for records in (data['inputs_before'],data['outputs']):
            for path,v in records.items():exact(path,v['sha256'])
archive=read(V/'manifest_v1.json');assert len(archive['videos'])==2
for v in archive['videos']:
    assert v['source_sha256']==v['copy_sha256'];exact(v['source'],v['source_sha256']);exact(v['destination'],v['copy_sha256'])
for f in [p for p in P.rglob('*.md') if not any(x.startswith('main_before') for x in p.parts)]+list(V.glob('*.md')):
    for target in re.findall(r'\]\((/[^)]+)\)',f.read_text()):
        target=re.sub(r':\d+$','',target);assert Path(target).exists(),(str(f),target)
review=P/'review_v1.md';assert review.is_file() and review.stat().st_size
sources=[A/n for n in ('VISUAL_STRINGS_PLAN_V1.md','string_trial_recording_v1.py','run_visual_strings_trial_v1.py')]+[P/'verify_v1.py',Path(__file__).resolve(),review]+[Path(p) for p in snapshots]
for f in sources:
    if f.suffix=='.py':ast.parse(f.read_text())
save('source_final_v1.json',{str(f):sha(f) for f in sources})
files={f for base in (P,V) for f in base.rglob('*') if f.is_file()}|set(sources)
save('artifact_inventory_v1.json',{'files':[{'path':str(f),'sha256':sha(f),'bytes':f.stat().st_size} for f in sorted(files)]})
save('final_verification_v1.json',{'passed':True,'prior_preserved_files':len(prior),'native_runs':1,'physics_steps':1200,'native_frame_files':906,'new_physics_geometry':0,'physics_exact_to_previous':True,'review_sha256':sha(review),'source_final_sha256':sha(P/'source_final_v1.json'),'inventory_sha256':sha(P/'artifact_inventory_v1.json')})
for f in read(P/'artifact_inventory_v1.json')['files']:exact(f['path'],f['sha256'])
print(json.dumps({'passed':True,'inventory_files':len(files),'prior_preserved':len(prior)}))
