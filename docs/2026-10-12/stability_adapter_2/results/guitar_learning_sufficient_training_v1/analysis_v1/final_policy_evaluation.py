from pathlib import Path
import datetime,hashlib,importlib.util,json
base=Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_sufficient_training_v1');out=base/'analysis_v1'
spec=importlib.util.spec_from_file_location('analysis',out/'analyze.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
def leaves(a,b):
 if isinstance(a,dict) and isinstance(b,dict):return sum(leaves(a.get(k),b.get(k)) for k in set(a)|set(b))
 if isinstance(a,list) and isinstance(b,list):return abs(len(a)-len(b))+sum(leaves(x,y) for x,y in zip(a,b))
 return int(type(a)!=type(b) or a!=b)
models={'B32':(32,Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_contact_recovery_v1/reference_provenance_migration_v1/checkpoint_evaluation_only.pt'),'8bedd8d9affc16406b3fb82667429615b8f13ec5e894d1dc576e940549edfd67'),'M64':(64,base/'training_long_v1/checkpoint_000031.pt','e30516096cda7e31d184049ae0ee6c0349b6eb63fea52d1f27fdc5126996f86f'),'F160':(160,base/'training_long_v1/final.pt','ae9770470cdbd7141bf47c277a4a81757a753841beab18419c60de31f2e9a7e6')}
for counter,p,digest in models.values():assert sha(p)==digest
names={'B32':{'deterministic':'baseline_deterministic_v2','stochastic':'baseline_stochastic_v2'},'M64':{'deterministic':'mid32_deterministic_v1','stochastic':'mid32_stochastic_v1'},'F160':{'deterministic':'final_deterministic_v1','stochastic':'final_stochastic_v1'}}
artifacts={'trace_sha256':'trace.jsonl.gz','demonstration_sha256':'demonstration.npz','contract_sha256':'contract.json','settings_sha256':'settings.json','inputs_before_sha256':'inputs_before.json','context_sha256':'context.json','initial_sha256':'initial.json','initial_state_sha256':'initial_state.json','case_spec_sha256':'case_spec.json','evaluation_seed_sha256':'evaluation_seed.json'}
pins={};evaluations={};initials={};seeds=None
physical=['human_position105','human_velocity105','guitar_bodies','target105','last_target105','codec_target81','previous_action39','controller_history']
def pin(p):pins[str(p)]=sha(p)
def checked_case(case,model,mode,process_mode,local_index,protocol_index,expected_seed,parent):
 counter,checkpoint,digest=models[model];d=json.loads((case/'result.json').read_text());seed=json.loads((case/'evaluation_seed.json').read_text());sp=json.loads((case/'case_spec.json').read_text());init=json.loads((case/'initialization.json').read_text())
 assert d['completed'] and d['source_unchanged'] and d['physical_flags_ok'] and not any(d.get(k) for k in ['failure','cleanup_error','forbidden_calls','missing_import_pins'])
 assert d['mode']=='evaluate' and d['action_source']=='policy' and d['teacher_intervention'] is False and d['perturbation'] is None
 assert d['source_checkpoint']==str(checkpoint) and d['initialization_checkpoint_sha256']==seed['checkpoint_sha256']==digest
 assert init=={'mode':'strict_PPO','optimizer_updates':counter}
 assert seed['seed']==expected_seed and seed['evaluation_mode']==mode and seed['process_mode']==process_mode and seed['case_index']==local_index and seed['protocol_case_index']==protocol_index and seed['seed_applied_after_checkpoint_load'] is True and all(seed['seeded_backends'].values())
 assert sp==dict(seed=expected_seed,perturbation=None,protocol_case_index=protocol_index,process_mode=process_mode,evaluation_mode=mode)
 assert sha(case/'result.json')==parent['case_manifests'][str(case)]
 for key,name in artifacts.items():assert sha(case/name)==d[key];pins[str(case/name)]=d[key]
 pin(case/'result.json');pin(case/'initialization.json')
 row=m.episode_row(d['episode']);assert row['success']==d['success'];row.update(seed=expected_seed,case_index=protocol_index,local_case_index=local_index,case=str(case));return row,json.loads((case/'initial_state.json').read_text())
for model,modes in names.items():
 evaluations[model]={};initials[model]={}
 for mode,name in modes.items():
  folder=base/name;e=m.evaluation_summary(folder);assert e['finalized_recorded_pass'];parent=e['parent'];assert parent['mode']=='evaluate' and parent['process_mode']=='persistent_reset' and parent['evaluation_mode']==mode
  protocol=json.loads((folder/'protocol.json').read_text());ss=[c['seed'] for c in protocol['cases']]
  if seeds is None:seeds=ss
  assert ss==seeds and len(ss)==20
  rows=[];initials[model][mode]=[]
  for i,seed in enumerate(ss):
   row,initial=checked_case(folder/('case_%03d'%i),model,mode,'persistent_reset',i,i,seed,parent);rows.append(row);initials[model][mode].append(initial)
  for p in [folder/'result.json',folder/'protocol.json',folder.with_name(folder.name+'_runtime_json_audit.json')]:pin(p)
  evaluations[model][mode]={'folder':str(folder),'summary':m.summarize(rows),'cases':rows,'runtime_recorded_pass':e['runtime']['recorded_pass']}
def paired(a,b):
 rows=[]
 for old,new in zip(a,b):
  assert old['seed']==new['seed'];change=('success_to_' if old['success'] else 'failure_to_')+('success' if new['success'] else 'failure')
  rows.append({'seed':old['seed'],'transition':change,'baseline':old,'new':new,'delta':{k:new[k]-old[k] for k in ['hold_fraction','ready_s','wrong_press_s','missing_press_s','cost']}})
 return {'counts':{name:sum(r['transition']==name for r in rows) for name in ['success_to_success','success_to_failure','failure_to_success','failure_to_failure']},'mean_delta':{k:m.mean([r['delta'][k] for r in rows]) for k in rows[0]['delta']},'rows':rows}
comparisons={}
for a,b in [('B32','M64'),('M64','F160'),('B32','F160')]:
 comparisons[a+'_to_'+b]={}
 for mode in ['deterministic','stochastic']:
  pair=paired(evaluations[a][mode]['cases'],evaluations[b][mode]['cases']);aa=initials[a][mode];bb=initials[b][mode]
  pair['initial_state_comparison']={'full_leaf_equal_cases':sum(x==y for x,y in zip(aa,bb)),'physical_target_controller_blocks_exact_equal_cases':sum(all(x[k]==y[k] for k in physical) for x,y in zip(aa,bb)),'difference_top_level_fields':sorted(set(k for x,y in zip(aa,bb) for k in x if x[k]!=y[k]))};comparisons[a+'_to_'+b][mode]=pair
fresh={};fresh_initials=[];pids=[]
for model,name in [('B32','baseline_fresh6_v1'),('F160','final_fresh6_v1')]:
 folder=base/name;parent=json.loads((folder/'result.json').read_text());vpath=base/(name+'_validation_v2.json');validation=json.loads(vpath.read_text());assert parent['completed'] and validation['passed'] and validation['optimizer_updates']==models[model][0] and validation['expected_checkpoint_sha256']==models[model][2] and validation['expected_checkpoint']==str(models[model][1]);pin(vpath);pin(folder/'result.json');pin(folder/'protocol.json');rows=[];ii=[]
 for i,seed in enumerate(seeds[:6]):
  process=folder/('process_%03d'%i);e=m.evaluation_summary(process);assert e['finalized_recorded_pass'];child=parent['children'][i];assert child['returncode']==0 and child['case_index']==i and sha(process/'result.json')==child['result_sha256'] and sha(process.with_name(process.name+'_runtime_json_audit.json'))==child['runtime_audit_sha256']
  row,initial=checked_case(process/'case_000',model,'stochastic','fresh_process',0,i,seed,e['parent']);vr=validation['cases'][i];assert vr['seed']==seed and vr['successful']==row['success'];row['pid']=vr['pid'];pids.append(vr['pid']);rows.append(row);ii.append(initial);fresh_initials.append(initial)
  for p in [process/'result.json',process.with_name(process.name+'_runtime_json_audit.json')]:pin(p)
 fresh[model]={'summary':m.summarize(rows),'cases':rows,'all_six_initial_leaves_equal':all(v==ii[0] for v in ii),'initial_state_shas':[sha(Path(row['case'])/'initial_state.json') for row in rows],'root_validation_passed':True}
assert len(set(pids))==12
fresh_pair=paired(fresh['B32']['cases'],fresh['F160']['cases']);fresh_pair['all12_initial_json_leaves_exact_equal']=all(v==fresh_initials[0] for v in fresh_initials);fresh_pair['all12_contact_histories_exact_equal']=all(v['contact_history']==fresh_initials[0]['contact_history'] for v in fresh_initials);fresh_pair['leaf_difference_counts_vs_first']=[leaves(fresh_initials[0],v) for v in fresh_initials];fresh_pair['unique_native_pids']=len(set(pids))
validations={}
for name in ['baseline_validation_v1.json','mid32_validation_v1.json','final_deterministic_v1_validation_v2.json','final_stochastic_v1_validation_v2.json','final_fresh6_v1_validation_v2.json','baseline_fresh6_v1_validation_v2.json']:
 p=base/name;validations[name]=json.loads(p.read_text());pin(p)
result={'schema':'guitar_learning.final_policy_evaluation_analysis.v1','captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Completed policy evaluations only:132 separate cases, not training transitions. Same single training lineage, same prepared pose; policy RNG seeds are not independent training seeds.','models':{k:{'optimizer_updates':v[0],'checkpoint':str(v[1]),'sha256':v[2]} for k,v in models.items()},'protocol_seeds':seeds,'persistent':evaluations,'paired_persistent':comparisons,'fresh':fresh,'paired_fresh':fresh_pair,'root_validations':validations,'source_pins':pins,'all_metadata_and_artifact_checks_passed':True,'fresh_local_case_index_zero_all12':True,'helper_sha256':sha(Path(__file__))}
assert all(sha(Path(path))==digest for path,digest in pins.items());result['all_read_artifacts_unchanged_after_analysis']=True
(out/'final_policy_evaluation.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps({'persistent':{model:{mode:v['summary'] for mode,v in modes.items()} for model,modes in evaluations.items()},'paired':{name:{mode:{'counts':v['counts'],'initial':v['initial_state_comparison']} for mode,v in modes.items()} for name,modes in comparisons.items()},'fresh':{k:v['summary'] for k,v in fresh.items()},'fresh_pair':{k:v for k,v in fresh_pair.items() if k!='rows'}},indent=2))
