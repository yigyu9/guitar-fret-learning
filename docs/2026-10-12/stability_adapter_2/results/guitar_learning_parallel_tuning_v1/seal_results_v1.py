"""Root final preservation seal after completed independent review; no new training."""
from pathlib import Path
import json,hashlib,shutil,re,datetime
base=Path(__file__).resolve().parent;root=base.parents[4]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,value):
 with Path(p).open('x') as stream:json.dump(value,stream,indent=2,ensure_ascii=False)
audit=read(base/'input_audit.json');assert audit['passed'] and not audit['errors']
review=base/'review.md';assert review.exists() and 'Critical: 없음' in review.read_text()
config=root/'guitar_learning/configs/long_B_16env_v1.json';settings=read(config);baseline=read(base/'pilot_baseline_v1/settings.json')
assert {k for k in settings if settings[k]!=baseline[k]}=={'updates','checkpoint_every','max_wall_seconds'}
source_checks={}
for before in sorted(base.glob('*source_before.json')):
 for p,h in read(before).items():source_checks[p]=sha(p)==h
assert all(source_checks.values())
# Read-only confirm of runtime and record maps since the preceding root audit.
for p,hashes in audit['input_versions'].items():
 if p==str(root/'guitar_learning/train_parallel.py'):
  assert sha(p) in hashes
 else:assert sha(p)==hashes[0]
for p,h in audit['report_sha256'].items():assert sha(p)==h
plan=root/'docs/plans/guitar_learning_parallel_tuning_20261018.md';s=plan.read_text();s=s.replace('- [ ]','- [x]');s+='\n최종 완료: 독립 change-reviewer 문제없음, root 입력 감사1580경로/실제XML+mesh106파일/보관 및snapshot151SHA 통과. 총10native/31616전이/295완료episode/실패0, 준비398회, 측정126464물리표본과준비191040step은환경합산1322.9333초다. fullraw저장은398ticks/1592표본이며나머지는60Hzcompact다. 현행소스·설정·문서와입력변종(runner v1/v2)·출력inventory를최종보존했다. 음악수렴과8h자원거동은미검증이며장기run은실행하지않았다.\n';plan.write_text(s)
paths={p for p in (root/'guitar_learning').rglob('*') if p.is_file() and p.suffix in ('.py','.md','.json') and 'archive' not in p.relative_to(root/'guitar_learning').parts and '__pycache__' not in p.parts}
paths.update([plan,root/'stability_adapter_2/PLAN.md',root/'stability_adapter_2/README.md'])
paths.update(base.glob('*.py'))
destination=base/'source_final';destination.mkdir();rows=[]
for f in sorted(paths):
 d=destination/f.relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d);assert sha(f)==sha(d)
 rows.append(dict(path=str(f),preserved=str(d),sha256=sha(f)))
write(base/'source_final_manifest.json',rows)
# Check published local links; the last two seal outputs are created below.
documents=[base/'README.md',root/'guitar_learning/README.md',root/'guitar_learning/TRAINING.md',root/'guitar_learning/PARALLEL_TRAINING.md',root/'guitar_learning/archive/README.md']
links=set()
for doc in documents:
 for link in re.findall(r'\]\((/[^)]+)\)',doc.read_text()):
  link=link.split('#',1)[0]
  if re.search(r':\d+$',link):link=link.rsplit(':',1)[0]
  links.add(link)
reserved={str(base/'artifact_inventory.json'),str(base/'final_verification.json')}
assert all(Path(p).exists() or p in reserved for p in links)
entries=[]
for f in sorted(base.rglob('*')):
 if f.is_file() and f.name not in ('artifact_inventory.json','final_verification.json'):
  entries.append(dict(path=str(f.resolve()),bytes=f.stat().st_size,sha256=sha(f)))
write(base/'artifact_inventory.json',dict(scope='All phase files existing before final seal; excludes inventory itself and final_verification.json to avoid circular digests',files=entries))
result=dict(completed=True,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Measured environment-count and bounded hyperparameter selection complete; no overnight training or musical convergence claim',cpu_tests=104,native_runs=audit['native_runs'],transitions=audit['transitions'],completed_episodes=audit['completed_episodes'],failure_episodes=audit['failure_episodes'],prepared_resets=audit['prepared_resets'],learning_physics_samples=audit['learning_physics_samples'],total_physics_seconds=audit['total_physics_seconds'],physics_scope='sum across independent environments, includes2s preparation perreset; not elapsed walltime; only1592 fullraw physics samples stored, remaindercompact60Hz',project_input_paths=audit['project_input_paths'],declared_asset_files=audit['declared_mesh_and_xml_count'],all_reset_recorded_properties_equal=audit['all_reset_native_static_properties_equal'],archived_files=audit['archive_files_checked'],source_final_files=len(rows),source_checks=source_checks,selected_settings=settings,selection='stable startingpoint from baseline; all pilots hadzero50/100ms matches',long_training_launched=False,review=dict(path=str(review),sha256=sha(review),critical_findings=0),input_audit=dict(path=str(base/'input_audit.json'),sha256=sha(base/'input_audit.json')),artifact_inventory=dict(path=str(base/'artifact_inventory.json'),sha256=sha(base/'artifact_inventory.json'),file_count=len(entries)),source_final_manifest_sha256=sha(base/'source_final_manifest.json'),published_config_sha256=sha(config),local_links_checked=len(links),source_final_exact=True)
write(base/'final_verification.json',result)
assert all(Path(p).exists() for p in links)
assert all(sha(e['path'])==e['sha256'] for e in entries)
print(json.dumps(dict(completed=True,inventory_files=len(entries),source_final_files=len(rows),local_links_checked=len(links),native_runs=audit['native_runs'],transitions=audit['transitions'],long_training_launched=False)))
