from pathlib import Path
import datetime, hashlib, importlib.util, json, shutil
base=Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results')
root=base/'guitar_learning_sufficient_training_v1'
out=root/'analysis_v1'
source=root/'training_long_v1'
snapshot=out/'mid16_input_snapshot'
snapshot.mkdir(exist_ok=False)
manifest={'captured_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(source),'highest_included_completed_update':15,'completed_updates':list(range(16)),'scope':'Provisional prefix of active run, no final report/runtime evidence. No old C/smoke episode pooling.','files':{}}
def save(name,payload):
 (snapshot/name).write_bytes(payload)
 manifest['files'][name]={'original_path':str(source/name),'snapshot_sha256':hashlib.sha256(payload).hexdigest(),'snapshot_bytes':len(payload)}
for i in range(16):
 name='update_%06d.json'%i
 payload=(source/name).read_bytes(); assert json.loads(payload)['update_index']==i
 save(name,payload)
for name in ['episodes.jsonl','resources.jsonl']:
 rows=[]
 with (source/name).open('rb') as stream:
  for line in stream:
   if not line.endswith(b'\n'):break
   item=json.loads(line)
   update=item.get('update_index')
   if update is not None and update>15:break
   rows.append(line)
 save(name,b''.join(rows))
manifest['episode_rows']=len((snapshot/'episodes.jsonl').read_text().splitlines())
assert manifest['episode_rows']==128
(out/'mid16_snapshot_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
spec=importlib.util.spec_from_file_location('analysis',out/'analyze.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
summary=module.training_summary(snapshot)
summary['original_training_folder']=str(source)
summary['snapshot_manifest']=str(out/'mid16_snapshot_manifest.json')
summary['highest_included_completed_update']=15
summary['scope']='Provisional completed-update prefix only; active run has no finalized report or runtime evidence yet.'
(out/'mid16_summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
module.plot_training(summary,out/'mid16_learning_curve.png')
old=base/'guitar_learning_transition_refinement_long_v1/isolated_resume_training_v1'
keys=['actor_loss','reward_value_loss','cost_value_loss','actor_grad_norm','analytic_kl','max_attempted_kl','kl_retries','actor_lr','std_lr','bc_mse','cost_weight','transitions']
comparison=[]
for i in range(14):
 name='update_%06d.json'%i
 a=json.loads((source/name).read_text());b=json.loads((old/name).read_text())
 differences={key:{'new':a.get(key),'old':b.get(key)} for key in keys if a.get(key)!=b.get(key)}
 a_counts={k:a['learning_window'][k] for k in ['completed_episodes','quality_successful_episodes','physical_failure_episodes']}
 b_counts={k:b['learning_window'][k] for k in a_counts}
 comparison.append({'additional_update_index':i,'performance_counts_equal':a_counts==b_counts,'counts':a_counts,'key_float_metrics_exact_equal':not differences,'differences':differences,'diagnostics_exact_equal':a.get('diagnostics')==b.get('diagnostics'),'reward_terms_exact_equal':a['learning_window']['reward_terms']==b['learning_window']['reward_terms']})
comparison={'scope':'Exact comparison of saved non-timer scalar/diagnostic values; no statistical independence or old/new episode pooling.','updates':comparison,'all_key_scalar_metrics_exact_equal':all(c['key_float_metrics_exact_equal'] for c in comparison),'all_diagnostics_exact_equal':all(c['diagnostics_exact_equal'] for c in comparison),'all_counts_equal':all(c['performance_counts_equal'] for c in comparison)}
(out/'mid16_old_C_comparison.json').write_text(json.dumps(comparison,indent=2)+'\n')
print(json.dumps({'updates':summary['recorded_updates'],'accounting':summary['accounting'],'episodes':summary['all_episodes'],'diagnostics':summary['diagnostic_ranges'],'resources':summary['resource_stream_extrema'],'comparison':{k:v for k,v in comparison.items() if k!='updates'}},indent=2))
