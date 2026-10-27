from pathlib import Path
import datetime, hashlib, importlib.util, json
base=Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_sufficient_training_v1')
out=base/'analysis_v1';source=base/'training_long_v1';snapshot=out/'mid32_input_snapshot';snapshot.mkdir(exist_ok=False)
manifest={'captured_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(source),'highest_included_completed_update':31,'completed_updates':list(range(32)),'scope':'Provisional prefix of active run; no final report/runtime evidence. No old C/smoke episode pooling.','files':{}}
def save(name,payload):
 (snapshot/name).write_bytes(payload)
 manifest['files'][name]={'original_path':str(source/name),'snapshot_sha256':hashlib.sha256(payload).hexdigest(),'snapshot_bytes':len(payload)}
for i in range(32):
 name='update_%06d.json'%i;payload=(source/name).read_bytes();assert json.loads(payload)['update_index']==i;save(name,payload)
for name in ['episodes.jsonl','resources.jsonl']:
 rows=[]
 with (source/name).open('rb') as stream:
  for line in stream:
   if not line.endswith(b'\n'):break
   item=json.loads(line);update=item.get('update_index')
   if update is not None and update>31:break
   rows.append(line)
 save(name,b''.join(rows))
manifest['episode_rows']=len((snapshot/'episodes.jsonl').read_text().splitlines());assert manifest['episode_rows']==256
(out/'mid32_snapshot_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
spec=importlib.util.spec_from_file_location('analysis',out/'analyze.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
s=m.training_summary(snapshot);s['original_training_folder']=str(source);s['snapshot_manifest']=str(out/'mid32_snapshot_manifest.json');s['highest_included_completed_update']=31;s['scope']='Provisional completed-update prefix only; active run has no finalized report/runtime evidence yet.'
keys=['actor_lr','analytic_kl','kl_retries','std_mean','bc_mse','reward_value_loss','cost_value_loss','reward_explained_variance','cost_explained_variance','cost_reward_advantage_std_ratio','collection_s','update_s']
s['diagnostic_nonoverlap_windows']={name:{key:m.bounds([u.get(key) for u in updates]) for key in keys} for name,updates in [('first16',s['updates'][:16]),('last16',s['updates'][16:32])]}
fail=[];success=[]
for item in m.lines(snapshot/'episodes.jsonl'):
 row=m.episode_row(item['episode'],item['metrics']);(success if row['success'] else fail).append(row)
s['failure_diagnostics']={'count':len(fail),'ready_zero_count':sum(r['ready_s']==0 for r in fail),'hold_zero_count':sum(r['hold_fraction']==0 for r in fail),'failure_summary':m.summarize(fail),'successful_summary':m.summarize(success)}
(out/'mid32_summary.json').write_text(json.dumps(s,indent=2,allow_nan=False)+'\n');m.plot_training(s,out/'mid32_learning_curve.png')
print(json.dumps({k:v for k,v in s.items() if k in ['accounting','all_episodes','per_worker','nonoverlap_windows','diagnostic_nonoverlap_windows','resource_stream_extrema','failure_diagnostics']},indent=2))
