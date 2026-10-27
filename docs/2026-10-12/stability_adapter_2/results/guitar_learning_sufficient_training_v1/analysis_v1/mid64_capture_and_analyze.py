from pathlib import Path
import datetime,hashlib,importlib.util,json
base=Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_sufficient_training_v1');out=base/'analysis_v1';source=base/'training_long_v1';snapshot=out/'mid64_input_snapshot';snapshot.mkdir(exist_ok=False)
manifest={'captured_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(source),'highest_included_completed_update':63,'completed_updates':list(range(64)),'scope':'Provisional completed-update prefix of active run; no final report/runtime evidence. Never pool old C or smoke episodes.','files':{}}
def save(name,payload):
 (snapshot/name).write_bytes(payload);manifest['files'][name]={'original_path':str(source/name),'snapshot_sha256':hashlib.sha256(payload).hexdigest(),'snapshot_bytes':len(payload)}
# Establish the immutable completed-update input list before reading growing streams.
update_paths=[source/('update_%06d.json'%i) for i in range(64)]
manifest['update_file_list_before_stream_read']=[str(path) for path in update_paths]
for i,path in enumerate(update_paths):
 payload=path.read_bytes();assert json.loads(payload)['update_index']==i;save(path.name,payload)
for name in ['episodes.jsonl','resources.jsonl']:
 rows=[]
 with (source/name).open('rb') as stream:
  for line in stream:
   if not line.endswith(b'\n'):break
   item=json.loads(line);index=item.get('update_index')
   if index is not None and index>63:break
   rows.append(line)
 save(name,b''.join(rows))
manifest['episode_rows']=len((snapshot/'episodes.jsonl').read_text().splitlines());assert manifest['episode_rows']==512
(out/'mid64_snapshot_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
spec=importlib.util.spec_from_file_location('analysis',out/'analyze.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
s=m.training_summary(snapshot);s.update(original_training_folder=str(source),snapshot_manifest=str(out/'mid64_snapshot_manifest.json'),highest_included_completed_update=63,scope='Provisional completed-update prefix only; active run has no finalized report/runtime evidence yet.')
rows=[]
for item in m.lines(snapshot/'episodes.jsonl'):
 row=m.episode_row(item['episode'],item['metrics']);row.update(worker_id=item['worker_id'],update_index=item['update_index']);rows.append(row)
keys=['actor_lr','analytic_kl','kl_retries','std_mean','bc_mse','reward_value_loss','cost_value_loss','reward_explained_variance','cost_explained_variance','cost_reward_advantage_std_ratio','collection_s','update_s']
def group(first,last):
 subset=[r for r in rows if first<=r['update_index']<last];updates=s['updates'][first:last];fail=[r for r in subset if not r['success']]
 return {'update_indices':list(range(first,last)),**m.summarize(subset),'failure_diagnostics':{'failed_count':len(fail),'ready_zero_count':sum(r['ready_s']==0 for r in fail),'ready_positive_but_hold_failed_count':sum(r['ready_s']>0 and not r['hold_pass'] for r in fail),'hold_zero_count':sum(r['hold_fraction']==0 for r in fail),'first_clean_never_observed_count':sum(r['first_clean_s'] is None for r in fail)},'diagnostics':{key:m.bounds([u.get(key) for u in updates]) for key in keys}}
s['nonoverlap32']={'first32':group(0,32),'last32':group(32,64)};s['nonoverlap16']={name:group(start,start+16) for name,start in [('updates1_16',0),('updates17_32',16),('updates33_48',32),('updates49_64',48)]};s['failure_diagnostics']=group(0,64)['failure_diagnostics']
s['worker_nonoverlap32']={str(worker):{name:m.summarize([r for r in rows if r['worker_id']==worker and first<=r['update_index']<last]) for name,first,last in [('first32',0,32),('last32',32,64)]} for worker in range(8)}
s['ready_failure_definition']='ready_positive means positive accumulated clean contact in the preparation window; not the unimplemented R1/R2 50ms acquisition latch.'
(out/'mid64_summary.json').write_text(json.dumps(s,indent=2,allow_nan=False)+'\n');m.plot_training(s,out/'mid64_learning_curve.png')
print(json.dumps({k:v for k,v in s.items() if k in ['accounting','all_episodes','nonoverlap32','nonoverlap16','failure_diagnostics','resource_stream_extrema']},indent=2))
