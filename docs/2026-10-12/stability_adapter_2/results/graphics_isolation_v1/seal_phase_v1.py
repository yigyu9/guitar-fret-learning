"""Seal only completed results and a finite live-training snapshot."""
import ast,hashlib,json,shutil
from pathlib import Path
R=Path('/home/ajou/yigyu/3');A=R/'stability_adapter_2';D=R/'docs/2026-10-12/stability_adapter_2';G=D/'results/graphics_isolation_v1';V=R/'docs/2026-10-12/video'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def save(p,value):
    with p.open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2)
checks={}
for name in ('verification_v1.json','resume_verification_v1.json'):
    item=read(G/name)
    checks[name]=item['passed'] and all(sha(p)==h for p,h in item['input_sha256'].items())
checks['old_1158_inputs_preserved']=read(G/'preservation_verification_v1.json')['passed']
checks['progress_analysis_inputs']=all(sha(p)==h for p,h in read(G/'progress_analysis_v1.json')['input_sha256'].items())
checks['A_source_seal']=all(sha(p)==h for p,h in read(G/'source_before_native_v1.json').items())
checks['V4_video_sha']=all(sha(v['source'])==sha(v['destination'])==v['sha256_source_before']==v['sha256_destination'] for v in read(V/'archive_v4/manifest.json')['videos'])
checks['font_fixed']=sha(G/'artifacts_v3/cp241_cp242_native_frames_v3.png')=='52d2875d89250a3927ed1fb1a40810e943247dc763bb36105ad28efccbd41dbd'
checks['latest_video_index']=sha(V/'README_ABSOLUTE_V6.md')=='470ca7177340d2c6e51e5f08bd27b3f999a7704f9d4c5909a33e5d722db4ba54'
checks['review_exists']=(G/'review_final_v1.md').exists()
assert all(checks.values()),checks
# Snapshot implementation and consumed root/artifact producers, without changing them.
source_final=G/'source_final_v1';source_final.mkdir()
source_paths=[Path(p) for p in read(G/'source_before_native_v1.json')]
source_paths.extend(G.glob('*.py'));source_paths.extend(G.glob('*.md'))
source_paths.extend(p for p in G.glob('artifacts_v*/*.py'))
source_paths.extend([A/'PLAN.md',A/'README.md',D/'README.md',D/'VISUAL_REPORT.md'])
source_manifest={}
for source in sorted(set(source_paths)):
    if source.suffix=='.py':ast.parse(source.read_text(),filename=str(source))
    destination=source_final/source.relative_to(R);destination.parent.mkdir(parents=True,exist_ok=True)
    assert not destination.exists();shutil.copyfile(source,destination)
    assert sha(source)==sha(destination)
    source_manifest[str(source)]={'sha256':sha(source),'snapshot':str(destination)}
save(source_final/'manifest.json',source_manifest)
# Files under long_on_v1 remain live; only immutable inputs in its snapshot audit are added.
live_logs={G/'long_on_v1.log',G/'supervisor_long_v1.log'}
paths={p for p in G.rglob('*') if p.is_file() and G/'long_on_v1' not in p.parents and p not in live_logs}
paths.update(p for p in (V/'archive_v4').rglob('*') if p.is_file())
paths.update([V/'README_ABSOLUTE_V5.md',V/'README_ABSOLUTE_V6.md'])
paths.update(Path(p) for p in read(G/'resume_verification_v1.json')['input_sha256'] if '/graphics_long_v1/' in p or '/graphics_isolation_v1/long_on_v1/' in p)
records=[]
for p in sorted(paths):
    line=1 if p.suffix in ('.py','.md','.json','.jsonl','.log') else None
    records.append({'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size,'line':line})
save(G/'artifact_inventory_v1.json',{'files':records,'scope':'immutable completed phase results, archived videos, source snapshots and finite live-run inputs; active training log/output excluded'})
checks['source_snapshots_exact']=all(sha(source)==record['sha256']==sha(record['snapshot']) for source,record in source_manifest.items())
checks['inventory_exact']=all(sha(record['path'])==record['sha256'] for record in records)
checks['live_prefix_preserved']=(G/'long_on_v1/training.jsonl').read_bytes().startswith((G/'training_prefix_at_recovery_v1.jsonl').read_bytes())
save(G/'final_verification_v1.json',{'passed':all(checks.values()),'checks':checks,
    'inventory_sha256':sha(G/'artifact_inventory_v1.json'),'source_manifest_sha256':sha(source_final/'manifest.json'),
    'final_review_sha256':sha(G/'review_final_v1.md'),'files_sealed':len(records),'sources_snapshotted':len(source_manifest),
    'live_run':str(G/'long_on_v1'),'cutoff':'2026-10-12T11:40:00+09:00',
    'scope':'graphics-prevention mitigation validated; finite first recovery/full initial evaluation/258-update snapshot only; long-run completion and musical success not certified'})
print(json.dumps({'passed':all(checks.values()),'files_sealed':len(records),'sources_snapshotted':len(source_manifest)},indent=2))
assert all(checks.values())
