"""Preserve consumed inputs and seal completed noisy-reset evidence."""
import ast,hashlib,json,shutil
from pathlib import Path
R=Path('/home/ajou/yigyu/3');P=R/'docs/2026-10-12/stability_adapter_2/results/initial_pose_noise_v1';OLD=P.parent/'parallel_collection_v1';V=R/'docs/2026-10-12/video'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def save(p,d):
    with p.open('x') as f:json.dump(d,f,ensure_ascii=False,indent=2)
checks={}
for name in ('analysis_v1.json','verification_v1.json'):
    d=read(P/name);checks[name]=d['passed'] and all(sha(p)==h for p,h in d['input_sha256'].items())
source_pin={**read(P/'source_before_native_v1.json'),**read(P/'source_addition_probe_v1.json')}
checks['new_sources_pinned']=all(sha(p)==h for p,h in source_pin.items())
main=read(P/'main_append_completion_v1.json');old_main=read(P/'main_append_v1.json')
checks['append_stage_chain']=all(old_main[p]['current_sha256']==v['old_prefix_sha256'] for p,v in main.items())
checks['main_current_exact']=all(sha(p)==v['current_sha256'] for p,v in main.items())
checks['two_append_prefixes_exact']=all(Path(p).read_bytes().startswith((P/folder/f'{i}_{Path(p).name}').read_bytes()) and sha(P/folder/f'{i}_{Path(p).name}')==record[p]['old_prefix_sha256'] for folder,record in [('main_before_v1',old_main),('main_before_completion_v1',main)] for i,p in enumerate(record))
# Main append occurred only after all consumed native runs finished; preserve each consumed old prefix.
closure_checks=[]
for name in ('smoke_v1','eval_noise_1_v1','eval_noise_4_v1'):
    changed=[]
    for p,h in read(P/name/'attempt.json')['input_sha256'].items():
        if sha(p)==h:continue
        if p in main and main[p]['old_prefix_sha256']==h:continue
        changed.append(p)
    closure_checks.append(not changed)
checks['all_native_inputs_preserved_or_documented_main_append']=all(closure_checks)
checks['previous_8103_artifacts_unchanged']=all(sha(r['path'])==r['sha256'] for r in read(OLD/'artifact_inventory_v1.json')['files'])
manifest=read(V/'initial_pose_noise_v1/manifest.json')
checks['four_archived_videos_exact']=len(manifest['videos'])==4 and all(sha(v['source'])==v['source_sha256_before']==v['source_sha256_after']==v['destination_sha256']==sha(v['destination']) for v in manifest['videos'])
for index in (1,4):
    capture=read(P/f'eval_noise_{index}_v1/native/episode_0001/media/capture.json')
    checks[f'noise_{index}_all_raw_and_overlay_frames_exact']=all(sha(p)==h for f in capture['frames'] for field in ('image_sha256','raw_image_sha256') for p,h in f[field].items())
checks['corrected_PD_PREP_doc']='PREP 동안에도 기존 PD와 안정화 policy가 계속 제어' in (P/'artifacts_v1/README_V2.md').read_text()
checks['latest_index_uses_correction']='artifacts_v1/README_V2.md' in (V/'README_ABSOLUTE_V10.md').read_text()
checks['review_exists']=(P/'review_final_v1.md').is_file()
assert all(checks.values()),checks
sources={Path(p) for p in source_pin};sources.update(P.glob('*.py'));sources.update(P.glob('*.md'));sources.update(P.glob('artifacts_v*/*.py'));sources.update(Path(p) for p in main)
snap=P/'source_final_v1';snap.mkdir();source_manifest={}
for p in sorted(sources):
    if p.suffix=='.py':ast.parse(p.read_text(),filename=str(p))
    dest=snap/p.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
    assert sha(p)==sha(dest);source_manifest[str(p)]={'sha256':sha(p),'snapshot':str(dest)}
save(snap/'manifest.json',source_manifest)
paths={p for p in P.rglob('*') if p.is_file()};paths.update(p for p in (V/'initial_pose_noise_v1').rglob('*') if p.is_file());paths.update([V/'README_ABSOLUTE_V9.md',V/'README_ABSOLUTE_V10.md'])
records=[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size,'line':1 if p.suffix in ('.py','.md','.json','.jsonl','.log') else None} for p in sorted(paths)]
save(P/'artifact_inventory_v1.json',{'files':records,'scope':'completed native initial-noise phase and four archived videos; original/corrected documents both preserved'})
checks['source_snapshots_exact']=all(sha(p)==v['sha256']==sha(v['snapshot']) for p,v in source_manifest.items())
checks['inventory_exact']=all(sha(v['path'])==v['sha256'] for v in records)
save(P/'final_verification_v1.json',{'passed':all(checks.values()),'checks':checks,'artifact_inventory_sha256':sha(P/'artifact_inventory_v1.json'),'source_manifest_sha256':sha(snap/'manifest.json'),'review_sha256':sha(P/'review_final_v1.md'),'files_sealed':len(records),'sources_snapshotted':len(source_manifest),'bank_entries':5,'noisy_entries':4,'training':{'environments':4,'steps_per_worker':64,'new_updates':1,'transitions':256,'source_CP320':'model/RMS only; fresh Adam/counters'},'scope':'coupled random initial pose from validated discrete bank; full representative recordings and real optimizer/collector verified, music0/42 and large late drift remain; eval indices fixed and v1 general-sampling metadata limitation disclosed'})
print(json.dumps({'passed':all(checks.values()),'files':len(records),'sources':len(source_manifest)}))
