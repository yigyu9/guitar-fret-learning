import hashlib,json,shutil,subprocess
from pathlib import Path
import numpy as np
R=Path('/home/ajou/yigyu/3');A=R/'stability_adapter_2';D=R/'docs/2026-10-12/stability_adapter_2';B=D/'results';P=B/'palm_support_two_axis_fk_v2';OLD=B/'torso_hold_native_collision_v1';checks={};seen={}
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 p=Path(p)
 if str(p) not in seen:seen[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
 return seen[str(p)]
def check(n,v):assert v,n;checks[n]=True
def closure(d):return all(sha(p)==h for p,h in d.items())
def true(d):return bool(d) and all(v is True for v in d.values())
stages=[('palm_support_runtime_fk_v1','palm_support_runtime_fk_execution_v1','audit_palm_support_runtime_fk.py',4,4),('palm_support_two_axis_fk_v1','palm_support_two_axis_fk_execution_v1','compare_palm_two_axis_fk.py',5,72),('palm_support_two_axis_fk_v2','palm_support_two_axis_fk_execution_v2','compare_palm_two_axis_fk_v2.py',5,96)]
for result,exe,code,count,rows in stages:
 e=read(B/exe/'execution.json');d=read(B/result/'analysis.json');check(result+'_exit0_source_log_exact',e['exit_code']==e['native_calls']==0 and e['source_sha256_before']==e['source_sha256_after']==sha(A/code)==sha(B/exe/'source.py') and e['log_sha256']==sha(B/exe/'execution.log'));check(result+'_checks_input_closure_and_no_physics',len(d['checks'])==count and true(d['checks']) and closure(d['input_sha256']) and d['native_initializations']==d['physics_steps']==0 and len(d['samples'] if result=='palm_support_runtime_fk_v1' else d['rows'])==rows)
runtime=read(B/'palm_support_runtime_fk_v1/analysis.json');v1=read(B/'palm_support_two_axis_fk_v1/analysis.json');d=read(P/'analysis.json');check('whole_hand_failure_all_four_hypotheses_retained',runtime['all_saved_prediction_gates_passed'] is False and not any(s['prediction_gate_passed'] for s in v1['summary']+d['summary']) and len(d['summary'])==8)
check('old_three_hypothesis_numeric_rows_exact_in_v2',v1['rows']==[r for r in d['rows'] if r['mode']!='tangent_half'])
check('expected_SHA_previous_two_sources_preserved',all(sha(p)==sha(v['snapshot'])==v['sha256'] for p,v in read(P/'previous_sources_preservation.json').items()))
for tag,code in [('scope','assess_palm_runtime_fk_scope.py'),('artifact','make_palm_runtime_fk_artifacts.py')]:
 e=read(P/(tag+'_execution.json'));check(tag+'_offline_exit0_source_log',e['exit_code']==e['native_calls']==0 and e['source_sha256_before']==e['source_sha256_after']==sha(A/code)==sha(P/(tag+'_source.py')) and e['log_sha256']==sha(P/(tag+'.log')))
s=read(P/'palm_scope_assessment.json');check('24_palm_scope_pass_distinct_from_whole_hand_failure',len(s['checks'])==4 and true(s['checks']) and closure(s['input_sha256']) and s['palm_samples']==24 and s['whole_hand_gate_passed'] is False and s['max_palm_origin_error_mm']==0.00031203302648127494)
i=read(OLD/'native/initial_values.json');q0=np.array([q['pos'] for q in i['native_initial_state']['human_dof_states']]);main=[i['human_joint_names'].index(n) for n in i['main_control_joint_names']];lo=np.array(i['PD_properties']['lower']);hi=np.array(i['PD_properties']['upper'])
check('all_four_unexecuted_float32_PD_targets_inside_model_and_offset0p3',all(np.all(np.array(r['base_plus_dq_float32_target_rad'])>=lo) and np.all(np.array(r['base_plus_dq_float32_target_rad'])<=hi) and np.all(abs((np.array(r['base_plus_dq_float32_target_rad'])-q0)[main])<=.3) for r in runtime['samples']))
check('geometric_dq_max0p05_not_actual_PD_motion',all(max(abs(v) for v in r['geometric_dq_rad'].values())<=.05 for r in runtime['samples']))
rawpath=OLD/'native/states.jsonl';states=[json.loads(v) for v in rawpath.read_text().splitlines()];q=np.array([[e['pos'] for e in s['human_dof_states']] for s in states]);outside=np.maximum(lo-q,q-hi);ids=np.flatnonzero((outside>0).any(axis=0));bounds=[dict(joint=i['human_joint_names'][k],steps=int((outside[:,k]>0).sum()),max_rad=float(outside[:,k].max())) for k in ids];check('full_saved_actual_bounds_three_tiny_RThorax_steps_retained',len(bounds)==1 and bounds[0]['joint']=='R_Thorax_x' and bounds[0]['steps']==3 and bounds[0]['max_rad']==9.99346375465393e-05)
m=read(P/'artifacts/manifest.json');check('two_actual_PNG_opened_inputs_output_exact_no_native',m['input_sha256_before']==m['input_sha256_after'] and closure(m['input_sha256_before']) and len(m['outputs_sha256'])==2 and closure(m['outputs_sha256']) and m['native_calls']==0)
previous=read(OLD/'final_verification.json')['counts']['previous_inventories'];counts={}
for name in list(previous)+['torso_hold_native_collision_v1']:
 inv=read(B/name/'artifact_inventory.json');check(name+'_inventory_preserved',all(Path(p).stat().st_size==v['size'] and sha(p)==v['sha256'] for p,v in inv.items()));counts[name]=len(inv)
check('previous34_phase_inventories_verified',len(counts)==34)
legacy=B/'palm_neck_side_v1/preservation_reference';stat=read(legacy/'protected_original_stat.json');aug=read(legacy/'aug19_sha256.json');check('legacy87_stat_preserved',len(stat)==87 and all([Path(p).stat().st_size,Path(p).stat().st_mtime_ns]==v for p,v in stat.items()));check('Aug19_49_SHA_preserved',len(aug)==49 and closure(aug))
visual=D/'VISUAL_REPORT.md';prev=read(OLD/'source_final_manifest.json')[str(visual)];check('VIS_sections1_to91_prefix_preserved',visual.read_bytes().startswith(Path(prev['snapshot']).read_bytes()))
phases=['palm_support_runtime_fk_v1','palm_support_runtime_fk_execution_v1','palm_support_two_axis_fk_v1','palm_support_two_axis_fk_execution_v1','palm_support_two_axis_fk_execution_v2','palm_support_two_axis_fk_v2'];check('independent_review_pending_not_fabricated',all(read(B/name/'review_status.json')['independent_review_completed'] is False and not (B/name/'review.md').exists() for name in phases))
code=['audit_palm_support_runtime_fk.py','palm_two_axis_fk.py','compare_palm_two_axis_fk.py','palm_two_axis_fk_v2.py','compare_palm_two_axis_fk_v2.py','assess_palm_runtime_fk_scope.py','make_palm_runtime_fk_artifacts.py'];cmd=['/home/ajou/miniconda3/envs/rl38/bin/python','-c','import sys; [compile(open(p).read(),p,"exec") for p in sys.argv[1:]]']+[str(A/n) for n in code];check('Python38_seven_sources_syntax',subprocess.call(cmd)==0)
check('no_new_native_constructor_or_state_force_physics_submission',all(not any(token in (A/n).read_text() for token in ('CameraEnvironment(','SelfCollisionEnvironment(','set_actor_','apply_body_force','step_physics(','acquire_gym(')) for n in code))
files=[A/n for n in code+['PALM_RUNTIME_FK_EXECUTION.md','PALM_SUPPORT_RESIDUAL_AT_BODY9_PLAN.md','PALM_FK_TWO_AXIS_DIAGNOSTIC.md','PALM_FK_TWO_AXIS_QUATERNION_PLAN.md','PALM_MEASURED_POSE_RESIDUAL_PLAN.md','README.md','PLAN.md','AGENTS.md','EXPERIMENT_WORKFLOW.md']]+[P/n for n in ('README.md','CHANGED_FILES.md','review_status.json')]+[B/name/'README.md' for name in phases[:-1]]+[visual];assert not (P/'source_final').exists();manifest={}
for f in files:
 dest=P/'source_final'/f.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest);assert sha(dest)==sha(f);manifest[str(f)]=dict(snapshot=str(dest),sha256=sha(f))
(P/'source_final_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');shutil.copyfile('/tmp/document_palm_runtime_fk.py',P/'documentation_producer.py')
for name in phases:
 folder=B/name;shutil.copyfile(__file__,folder/'root_final_audit_producer.py')
 (folder/'final_verification.json').write_text(json.dumps(dict(checks=checks,counts=dict(previous_inventories=counts.copy(),native_initializations=0,physics_steps=0,new_physical_trials=0,source_final_files=len(files) if folder==P else 0,whole_hand_hypotheses=4,diagnostic_saved_frames=4,heldout_saved_frames=20,scientific_PNG=2 if folder==P else 0),input_sha256=seen,actual_saved_bound_violations=bounds,syntax_command=cmd,audit_source=Path(__file__).read_text(),independent_review_completed=False,scope='root source/actual saved/FK numeric/float32 bounds/SHA and actual PNG QA; whole-hand gate failed in four modes, palm scope passed on24 saved poses; no new physics/controller/initial-G restoration/playing success; full goal active'),indent=2)+'\n')
 inv=folder/'artifact_inventory.json';assert not inv.exists();mapping={str(f):dict(size=f.stat().st_size,sha256=sha(f)) for f in sorted(folder.rglob('*')) if f.is_file()};inv.write_text(json.dumps(mapping,indent=2)+'\n');counts[name]=len(mapping);print(name,'inventory',len(mapping),flush=True)
print('root_checks',len(checks),'previous34 preserved; offline3 stages; wholehandfailed/palm accurate; goalactive')
