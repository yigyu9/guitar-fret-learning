from pathlib import Path
import datetime,hashlib,importlib.util,json
base=Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_sufficient_training_v1');out=base/'analysis_v1';folder=base/'baseline_fresh6_v1'
spec=importlib.util.spec_from_file_location('analysis',out/'analyze.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as stream:
  for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def leafdiff(a,b,path=''):
 if isinstance(a,dict) and isinstance(b,dict):
  for k in sorted(set(a)|set(b)):
   if k not in a or k not in b:yield {'path':path+'.'+k,'baseline':a.get(k),'fresh':b.get(k)}
   else:yield from leafdiff(a[k],b[k],path+'.'+k)
 elif isinstance(a,list) and isinstance(b,list):
  if len(a)!=len(b):yield {'path':path+'.length','baseline':len(a),'fresh':len(b)}
  for i,(x,y) in enumerate(zip(a,b)):yield from leafdiff(x,y,path+'[%d]'%i)
 elif type(a)!=type(b) or a!=b:yield {'path':path,'baseline':a,'fresh':b}
parent=json.loads((folder/'result.json').read_text());validation=json.loads((base/'baseline_fresh6_v1_validation.json').read_text());protocol=json.loads((folder/'protocol.json').read_text());seeds=[x['seed'] for x in protocol['cases']]
assert parent['completed'] is True and parent['mode']=='evaluate' and parent['process_mode']=='fresh_process' and validation['passed'] is True
assert len(parent['children'])==len(validation['cases'])==len(seeds)==6
pins={str(p):sha(p) for p in [folder/'result.json',folder/'protocol.json',base/'baseline_fresh6_v1_validation.json']};rows=[];initials=[];persistent=[];comparisons=[]
artifact_names={'trace_sha256':'trace.jsonl.gz','demonstration_sha256':'demonstration.npz','contract_sha256':'contract.json','settings_sha256':'settings.json','inputs_before_sha256':'inputs_before.json','context_sha256':'context.json','initial_sha256':'initial.json','initial_state_sha256':'initial_state.json','case_spec_sha256':'case_spec.json','evaluation_seed_sha256':'evaluation_seed.json'}
kinematic_keys=['human_position105','human_velocity105','guitar_bodies','target105','last_target105','codec_target81','previous_action39','controller_history']
for i,seed in enumerate(seeds):
 process=folder/('process_%03d'%i);case=process/'case_000';child=parent['children'][i];vr=validation['cases'][i]
 assert child['case_index']==i and child['returncode']==0 and vr['seed']==seed
 e=m.evaluation_summary(process);assert e['finalized_recorded_pass'];result=json.loads((case/'result.json').read_text());seedmeta=json.loads((case/'evaluation_seed.json').read_text());casespec=json.loads((case/'case_spec.json').read_text())
 assert e['parent']['process_mode']=='fresh_process' and e['parent']['evaluation_mode']=='stochastic'
 assert result['action_source']=='policy' and result['teacher_intervention'] is False and result['perturbation'] is None
 assert seedmeta['seed']==seed and seedmeta['case_index']==0 and seedmeta['protocol_case_index']==i and seedmeta['seed_applied_after_checkpoint_load'] is True and seedmeta['evaluation_mode']=='stochastic' and seedmeta['process_mode']=='fresh_process'
 assert casespec['seed']==seed and casespec['protocol_case_index']==i and casespec['process_mode']=='fresh_process' and casespec['evaluation_mode']=='stochastic'
 assert sha(process/'result.json')==child['result_sha256'] and sha(process.with_name(process.name+'_runtime_json_audit.json'))==child['runtime_audit_sha256']
 assert sha(case/'result.json')==e['parent']['case_manifests'][str(case)]
 for key,filename in artifact_names.items():assert sha(case/filename)==result[key];pins[str(case/filename)]=result[key]
 for path in [case/'result.json',process/'result.json',process.with_name(process.name+'_runtime_json_audit.json')]:pins[str(path)]=sha(path)
 row=m.episode_row(result['episode']);assert row['success']==result['success']==vr['successful'];row.update(seed=seed,protocol_case_index=i,local_case_index=0,pid=vr['pid'],process=str(process),initial_state_sha256=result['initial_state_sha256'],physical_flags_ok=result['physical_flags_ok']);rows.append(row)
 initial=json.loads((case/'initial_state.json').read_text());initials.append(initial)
 pp=base/'baseline_stochastic_v2'/('case_%03d'%i);pr=json.loads((pp/'result.json').read_text());ps=json.loads((pp/'case_spec.json').read_text());pi=json.loads((pp/'initial_state.json').read_text());assert ps['seed']==seed
 for path in [pp/'result.json',pp/'initial_state.json',pp/'case_spec.json']:pins[str(path)]=sha(path)
 prow=m.episode_row(pr['episode']);prow.update(seed=seed,case_index=i);persistent.append(prow)
 diffs=list(leafdiff(pi,initial));comparisons.append({'seed':seed,'persistent':prow,'fresh':row,'full_initial_leaf_exact_equal':not diffs,'initial_top_level_key_sets_equal':set(pi)==set(initial),'different_initial_top_level_values':[k for k in pi if pi[k]!=initial[k]],'kinematic_target_controller_blocks_exact_equal':all(pi[k]==initial[k] for k in kinematic_keys),'initial_leaf_or_length_difference_count':len(diffs),'initial_examples':diffs[:8],'transition':('success_to_' if prow['success'] else 'failure_to_')+('success' if row['success'] else 'failure')})
assert len(set(r['pid'] for r in rows))==6 and sum(r['success'] for r in rows)==validation['successful_cases']==3
result={'schema':'guitar_learning.baseline_fresh6_analysis.v1','captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Completed baseline only. Six separately created processes are not six independent training runs; no final-model/improvement/generalization conclusion.','source_pins':pins,'root_validation_passed':True,'local_metadata_and_hash_checks_passed':True,'protocol_seeds':seeds,'fresh_summary':m.summarize(rows),'fresh_cases':rows,'unique_pids':len(set(r['pid'] for r in rows)),'initial_states':{'all_six_full_sha_exact_equal':len(set(r['initial_state_sha256'] for r in rows))==1,'all_six_full_leaf_exact_equal':all(x==initials[0] for x in initials),'reference_sha256':rows[0]['initial_state_sha256'],'leaf_differences_vs_first':[len(list(leafdiff(initials[0],x))) for x in initials],'scope':'Observable saved JSON only; does not reveal hidden PhysX solver state.'},'persistent_first6_summary':m.summarize(persistent),'comparison_with_persistent_same_first6':comparisons,'helper_sha256':sha(Path(__file__))}
assert all(sha(Path(path))==digest for path,digest in pins.items());result['sources_unchanged_after_analysis']=True
(out/'baseline_fresh6.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:v for k,v in result.items() if k in ['fresh_summary','fresh_cases','initial_states','persistent_first6_summary']},indent=2))
