from pathlib import Path
import datetime, hashlib, importlib.util, json
base=Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_sufficient_training_v1');out=base/'analysis_v1'
spec=importlib.util.spec_from_file_location('analysis',out/'analyze.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for v in iter(lambda:f.read(1024*1024),b''):h.update(v)
 return h.hexdigest()
artifact_names={'trace_sha256':'trace.jsonl.gz','demonstration_sha256':'demonstration.npz','contract_sha256':'contract.json','settings_sha256':'settings.json','inputs_before_sha256':'inputs_before.json','context_sha256':'context.json','initial_sha256':'initial.json','initial_state_sha256':'initial_state.json','case_spec_sha256':'case_spec.json','evaluation_seed_sha256':'evaluation_seed.json'}
folders={'baseline_deterministic':'baseline_deterministic_v2','baseline_stochastic':'baseline_stochastic_v2','mid32_deterministic':'mid32_deterministic_v1','mid32_stochastic':'mid32_stochastic_v1'}
evals={};pins={};seeds=None;initial_pins={}
for label,name in folders.items():
 p=base/name;e=m.evaluation_summary(p);assert e['finalized_recorded_pass']
 parent=e['parent'];mode=label.split('_',1)[1];assert parent['mode']=='evaluate' and parent['process_mode']=='persistent_reset' and parent['evaluation_mode']==mode
 protocol=json.loads((p/'protocol.json').read_text());expected=[v['seed'] for v in protocol['cases']]
 assert len(expected)==20
 if seeds is None:seeds=expected
 assert seeds==expected
 pins[str(p/'result.json')]=sha(p/'result.json');pins[str(p/'protocol.json')]=sha(p/'protocol.json');pins[str(p.with_name(p.name+'_runtime_json_audit.json'))]=sha(p.with_name(p.name+'_runtime_json_audit.json'))
 records=[];initial_pins[label]=[]
 for i in range(20):
  case=p/('case_%03d'%i);result=json.loads((case/'result.json').read_text());case_spec=json.loads((case/'case_spec.json').read_text());seed=json.loads((case/'evaluation_seed.json').read_text())
  assert result['completed'] and result['mode']=='evaluate' and result['action_source']=='policy' and result['teacher_intervention'] is False and result['perturbation'] is None
  assert result['success']==result['episode']['transition']['successful']
  assert case_spec==dict(seed=seeds[i],perturbation=None,protocol_case_index=i,process_mode='persistent_reset',evaluation_mode=mode)
  assert seed['seed']==seeds[i] and seed['case_index']==i and seed['protocol_case_index']==i and seed['process_mode']=='persistent_reset' and seed['evaluation_mode']==mode and seed['seed_applied_after_checkpoint_load'] is True
  assert all(seed['seeded_backends'].values())
  assert seed['checkpoint_sha256']==result['initialization_checkpoint_sha256']==sha(Path(result['source_checkpoint']))
  digest=sha(case/'result.json');assert digest==parent['case_manifests'][str(case)];pins[str(case/'result.json')]=digest
  for key,filename in artifact_names.items():
   digest=sha(case/filename);assert digest==result[key];pins[str(case/filename)]=digest
  initial_pins[label].append(result['initial_state_sha256'])
  row=m.episode_row(result['episode']);row.update(case_index=i,seed=seeds[i],case=str(case));records.append(row)
 assert len(parent['successful_cases'])==sum(r['success'] for r in records)
 e['cases']=records;e['summary']=m.summarize(records);e['metadata_and_artifact_hash_checks_passed']=True;evals[label]=e
paired={}
for mode in ['deterministic','stochastic']:
 old=evals['baseline_'+mode]['cases'];new=evals['mid32_'+mode]['cases'];rows=[]
 for a,b in zip(old,new):
  assert a['seed']==b['seed'] and a['case_index']==b['case_index']
  change=('success_to_' if a['success'] else 'failure_to_')+('success' if b['success'] else 'failure')
  rows.append({'seed':a['seed'],'case_index':a['case_index'],'transition':change,'baseline':a,'mid32':b,'delta':{key:b[key]-a[key] for key in ['hold_fraction','ready_s','wrong_press_s','missing_press_s','reward','cost']}})
 paired[mode]={'counts':{name:sum(r['transition']==name for r in rows) for name in ['success_to_success','success_to_failure','failure_to_success','failure_to_failure']},'mean_delta':{key:m.mean([r['delta'][key] for r in rows]) for key in rows[0]['delta']},'observable_initial_state_hash_exact_equal_cases':sum(a==b for a,b in zip(initial_pins['baseline_'+mode],initial_pins['mid32_'+mode])),'rows':rows}
result={'schema':'guitar_learning.mid32_paired_evaluation.v1','captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Completed evaluation artifacts and SHA/metadata checks only; root native source/runtime replay audit remains separate. Intermediate model selection evaluation, same prepared pose persistent reset and single training lineage; not independent training seeds/generalization/statistical significance.','protocol_seeds_in_original_order':seeds,'all_metadata_and_artifact_hash_checks_passed':True,'file_hashes':pins,'evaluations':evals,'paired':paired,'helper_sha256':sha(Path(__file__))}
(out/'mid32_evaluation.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps({'summaries':{k:v['summary'] for k,v in evals.items()},'paired':{k:{i:j for i,j in v.items() if i!='rows'} for k,v in paired.items()}},indent=2))
