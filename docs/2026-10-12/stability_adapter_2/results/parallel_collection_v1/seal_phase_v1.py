"""Seal completed parallel collection evidence without rewriting consumed files."""
import ast
import hashlib
import json
import shutil
from pathlib import Path
R=Path('/home/ajou/yigyu/3');P=R/'docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1';V=R/'docs/2026-10-12/video'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def save(p,d):
    with p.open('x') as f:json.dump(d,f,ensure_ascii=False,indent=2)
checks={}
for name in ('verification_v1.json','completion_verification_v1.json','production_analysis_v1.json'):
    d=read(P/name);checks[name]=d['passed'] and all(sha(p)==h for p,h in d['input_sha256'].items())
checks['native_sources_pinned']=all(sha(p)==h for p,h in read(P/'source_before_native_v1.json').items())
for n in ('main_append_v1.json','main_append_resume_v1.json','main_append_completion_v1.json'):
    d=read(P/n);checks[n]=all(v['prefix_preserved'] for v in d.values())
# Latest append records certify each current main and the immediately preceding prefix.
d=read(P/'main_append_completion_v1.json')
checks['main_current_exact']=all(sha(p)==v['current_sha256'] for p,v in d.items())
checks['main_prefix_exact']=all(Path(p).read_bytes().startswith((P/'main_before_completion_v1'/f'{i}_{Path(p).name}').read_bytes()) for i,p in enumerate(d))
cp=read(P/'previous_stop_snapshot_v1.json')['checkpoint_record'];checks['old_CP315_preserved']=sha(cp['checkpoint'])==cp['sha256']
checks['review_complete']=(P/'review_final_v1.md').is_file()
checks['corrected_strap_caption']='physics strap 호출은 0회' not in (P/'artifacts_v2/README_V3.md').read_text()
assert all(checks.values()),checks
sources={Path(p) for p in read(P/'source_before_native_v1.json')}
sources.update(P.glob('*.py'));sources.update(P.glob('*.md'));sources.update(P.glob('artifacts_v*/*.py'));sources.update(Path(p) for p in d)
snap=P/'source_final_v1';snap.mkdir();manifest={}
for p in sorted(sources):
    if p.suffix=='.py':ast.parse(p.read_text(),filename=str(p))
    dest=snap/p.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
    assert sha(p)==sha(dest)
    manifest[str(p)]={'sha256':sha(p),'snapshot':str(dest)}
save(snap/'manifest.json',manifest)
paths={p for p in P.rglob('*') if p.is_file()}
for n in ('parallel_validation_v1','parallel_long_v1'):paths.update(p for p in (V/n).rglob('*') if p.is_file())
paths.update([V/'README_ABSOLUTE_V7.md',V/'README_ABSOLUTE_V8.md'])
records=[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size,'line':1 if p.suffix in ('.py','.md','.json','.jsonl','.log') else None} for p in sorted(paths)]
save(P/'artifact_inventory_v1.json',{'files':records,'scope':'completed parallel phase, source snapshots, eight archived videos and latest video index'})
checks['source_snapshots_exact']=all(sha(p)==v['sha256']==sha(v['snapshot']) for p,v in manifest.items())
checks['inventory_exact']=all(sha(v['path'])==v['sha256'] for v in records)
save(P/'final_verification_v1.json',{'passed':all(checks.values()),'checks':checks,'inventory_sha256':sha(P/'artifact_inventory_v1.json'),'source_manifest_sha256':sha(snap/'manifest.json'),'review_sha256':sha(P/'review_final_v1.md'),'files_sealed':len(records),'sources_snapshotted':len(manifest),'configuration':{'environments':4,'policy_batch':4,'rollout_steps_per_environment':256,'transitions_per_update':1024,'minibatch':128,'epochs':4,'physical_initial_noise':False},'completed_production_updates':4,'completed_production_transitions':4096,'checkpoint_update':320,'checkpoint_transitions':84992,'scope':'noon deadline run completed; batched CUDA policy and independent CPU physics validated; music 0/42 and mixed pose metrics, no stability or music success claim'})
print(json.dumps({'passed':all(checks.values()),'files':len(records),'sources':len(manifest)}))
