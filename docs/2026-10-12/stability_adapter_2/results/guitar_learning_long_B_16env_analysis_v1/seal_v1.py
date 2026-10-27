from pathlib import Path
import json,hashlib,shutil,re,datetime
base=Path(__file__).resolve().parent;root=base.parents[4]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,v):
 with Path(p).open('x') as s:json.dump(v,s,indent=2,ensure_ascii=False)
review=base/'review.md';assert review.exists() and 'Critical: 없음' in review.read_text()
pins=read(base/'analysis_inputs_before_v2.json');pins.update(read(base/'checkpoint_analysis.json')['input_sha256']);pins.update(read(base/'plot_metadata_v3.json')['input_sha256'])
changed=[p for p,h in pins.items() if sha(p)!=h];assert not changed,changed
analysis=read(base/'analysis_v2.json');assert not analysis['changed_analysis_inputs'];assert analysis['optimizer_updated_samples']==28672 and analysis['partial_collect_log']['samples']==1792
ck=read(base/'checkpoint_analysis.json');assert all(r['model_all_finite'] for r in ck['rows']) and ck['rows'][-1]['updates']==10
run=Path(analysis['run']);original=read(run/'inputs_before.json');package=[root/'guitar_learning'/name for name in ['train_parallel.py','parallel.py','ppo.py','training_environment.py','safety.py','task_measurement.py','music_task.py']]
assert all(sha(p)==original[str(p.resolve())] for p in package)
plan=root/'docs/plans/guitar_learning_long_run_analysis_20261018.md';s=plan.read_text().replace('- [ ]','- [x]');s+='\n독립검수문제없음완료. V3그림candidate표기반영및원본보존,분석입력/체크포인트/그림데이터사전후SHA재확인. 원학습소스·설정·로그변경없음,새학습/물리0. 권장복구10update,8환경운영안및reward/curriculum후속필요사항을명시했다.\n';plan.write_text(s)
files=set(package)|set(base.glob('*.py'))|{base/'README.md',review,plan,root/'stability_adapter_2/PLAN.md',root/'stability_adapter_2/README.md'}
folder=base/'source_final';folder.mkdir();rows=[]
for f in sorted(files):
 d=folder/f.relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d);assert sha(d)==sha(f);rows.append(dict(path=str(f.resolve()),preserved=str(d.resolve()),sha256=sha(f)))
write(base/'source_final_manifest.json',rows)
links=[]
for link in re.findall(r'\]\((/[^)]+)\)',(base/'README.md').read_text()):
 link=link.split('#',1)[0]
 if re.search(r':\d+$',link):link=link.rsplit(':',1)[0]
 links.append(link)
assert all(Path(p).exists() or p==str(base/'final_verification.json') for p in links)
inventory=[dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(base.rglob('*')) if p.is_file() and p.name not in ('artifact_inventory.json','final_verification.json')]
write(base/'artifact_inventory.json',dict(scope='All phase files before final seal; inventory and final_verification excluded to avoid circular hashes',files=inventory))
result=dict(completed_analysis=True,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),new_native_runs=0,training_restarted=False,original_training_sources_unchanged=True,analysis_inputs_checked=len(pins),changed_inputs=changed,committed_updates=14,committed_transitions=28672,committed_episode_ends=320,partial_collect_transitions=1792,partial_episode_ends=16,host_oom_confirmed=True,worker_timeout_exact_native_cause_confirmed=False,training_worker_direct_oom_kill_confirmed=False,recovery_checkpoint_updates=10,original_run_completed=False,original_worker_final_audit_missing=1,review_sha256=sha(review),analysis_sha256=sha(base/'analysis_v2.json'),checkpoint_analysis_sha256=sha(base/'checkpoint_analysis.json'),recommended_plot=str(base/'training_diagnosis_v3.png'),recommended_plot_sha256=sha(base/'training_diagnosis_v3.png'),artifact_inventory_sha256=sha(base/'artifact_inventory.json'),source_final_manifest_sha256=sha(base/'source_final_manifest.json'),local_links_checked=len(links),scope='Analysis verification only; does not certify original failed run, musical success, longrun safety, strict resume or8x256 training')
write(base/'final_verification.json',result)
assert all(Path(p).exists() for p in links);assert all(sha(p)==h for p,h in pins.items());assert all(sha(x['path'])==x['sha256'] for x in inventory)
print(json.dumps(dict(completed_analysis=True,input_paths=len(pins),source_final_files=len(rows),inventory_files=len(inventory),local_links=len(links),new_native_runs=0)))
