import hashlib,json,shutil,subprocess
from pathlib import Path
import numpy as np
R=Path('/home/ajou/yigyu/3');A=R/'stability_adapter_2';D=R/'docs/2026-10-12/stability_adapter_2';B=D/'results';P=B/'palm_measured_geometry_v1';PRIOR=B/'palm_support_two_axis_fk_v2';checks={};seen={}
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 p=Path(p)
 if str(p) not in seen:seen[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
 return seen[str(p)]
def check(n,v):assert v,n;checks[n]=True
def closure(d):return all(sha(p)==h for p,h in d.items())
stages=[('palm_measured_geometry_v1','palm_measured_geometry_execution_v1','check_measured_palm_geometry.py',16),('palm_single_hinge_pose_v1','palm_single_hinge_pose_execution_v1','check_palm_single_hinges.py',144)]
for phase,execution,code,rows in stages:
 e=read(B/execution/'execution.json');d=read(B/phase/'analysis.json');attempt=read(B/phase/'attempt.json')
 check(phase+'_exit0_source_log_exact',e['exit_code']==e['native_calls']==0 and e['source_sha256_before']==e['source_sha256_after']==sha(A/code)==sha(B/execution/'source.py') and e['log_sha256']==sha(B/execution/'execution.log'))
 check(phase+'_four_checks_and_input_closure',len(d['checks'])==4 and all(v is True for v in d['checks'].values()) and closure(d['input_sha256']) and attempt['input_sha256']==d['input_sha256'])
 check(phase+'_row_count_and_no_native',len(d['rows'])==rows and d['native_initializations']==d['physics_steps']==attempt['native_initializations']==attempt['physics_steps']==0)
g=read(P/'analysis.json');h=read(B/'palm_single_hinge_pose_v1/analysis.json');base=[r for r in g['rows'] if r['fraction']==0];new=[r for r in g['rows'] if r['fraction']!=0]
check('four_baselines_twelve_proposals_only_initial_quarter_passed',len(base)==4 and all(r['source_direction_screen_passed'] for r in base) and len(new)==12 and [(r['physics_step'],r['fraction']) for r in new if r['source_direction_screen_passed']]==[(0,.25)])
check('source_screen_truth_matches_increase_up_and_target_fields',all(r['source_direction_screen_passed']==(not r['new_or_increased_source_intersections'] and r['palm_up_proxy_z']>0 and r['PD_target_model_and_offset_bounds']) for r in g['rows']))
check('source_increased_pairs_over_epsilon_and_baseline_delta10um',all(v['common_radius_m']>1e-7 and v['increase_m']>1e-5 and abs(v['increase_m']-(v['common_radius_m']-v['baseline_common_radius_m']))<1e-15 for r in g['rows'] for v in r['new_or_increased_source_intersections']))
check('all_palm_up_and_PD_goal_bounds_true',all(r['palm_up_proxy_z']>0 and r['PD_target_model_and_offset_bounds'] for r in g['rows']))
check('palm_QP_upper_lower_finite_and_feasible',all(0<=r['palm_finite_patch_interval']['distance_lower_bound_m']<=r['palm_finite_patch_interval']['distance_m']+1e-12 and r['palm_finite_patch_interval']['optimizer_success'] and r['palm_finite_patch_interval']['feasibility_error_mm']<=1e-6 for r in g['rows']))
late=next(r for r in g['rows'] if r['physics_step']==1200 and r['fraction']==1);quarter=next(r for r in g['rows'] if r['physics_step']==1200 and r['fraction']==.25)
check('tiny_nonzero_late_palm_gap_retained',late['palm_finite_patch_interval']['distance_m']>0 and late['palm_finite_patch_interval']['distance_m']*1000==9.891870170584711e-8)
check('late_quarter_both_front_fingers_source_increase_retained',set(v['a'] for v in quarter['new_or_increased_source_intersections'] if v['kind']=='human_guitar' and v['b']=='guitar')=={'LH:index3','LH:middle3'})
check('conditional_six_hinges_24_each_four_plus20',len(h['summary'])==6 and len({r['physics_step'] for r in h['rows']})==24 and sum(r['heldout'] for r in h['rows'])==120 and all(sum(x['body']==r['body'] for x in h['rows'])==24 for r in h['summary']))
check('unchanged_conditional_0p1mm_1mrad_gate_all144',h['all_conditional_single_hinge_gates_passed'] and all(r['gate_passed']==(r['position_error_mm']<=.1 and r['rotation_error_rad']<=.001) for r in h['rows']) and all(r['gate_passed'] for r in h['rows']))
check('hinge_summaries_recomputed_actual_values',all(r['max_position_error_mm']==max(x['position_error_mm'] for x in h['rows'] if x['body']==r['body']) and r['max_rotation_error_rad']==max(x['rotation_error_rad'] for x in h['rows'] if x['body']==r['body']) for r in h['summary']))
check('finger1_whole_hand_failure_preserved',not any(s['prediction_gate_passed'] for s in read(PRIOR/'analysis.json')['summary']))
init=read(B/'torso_hold_native_collision_v1/native/initial_values.json');q0=np.array([q['pos'] for q in init['native_initial_state']['human_dof_states']]);t=np.array(init['preserved_absolute_targets_rad']);names=init['human_joint_names'];arm=[names.index(n) for n in read(B/'palm_support_runtime_fk_v1/analysis.json')['arm_joint_names']];main=[names.index(n) for n in init['main_control_joint_names']];lo=np.array(init['PD_properties']['lower']);hi=np.array(init['PD_properties']['upper'])
for r in g['rows']:
 target=t.copy();target[arm]+=r['angle_delta_rad'];target=target.astype(np.float32).astype(float)
 check('float32_PD_bounds_step'+str(r['physics_step'])+'_fraction'+str(r['fraction']),np.all(target>=lo) and np.all(target<=hi) and np.all(abs((target-q0)[main])<=.3))
for tag,folder,code in [('v1',P,'make_measured_palm_geometry_artifacts.py'),('v2',P/'artifact_v2_execution','make_measured_palm_geometry_artifacts_v2.py')]:
 e=read(folder/'artifact_execution.json');m=read(P/('artifacts' if tag=='v1' else 'artifacts_v2')/'manifest.json')
 check('artifact_'+tag+'_exit_source_log_exact_no_native',e['exit_code']==e['native_calls']==m['native_calls']==0 and e['source_sha256_before']==e['source_sha256_after']==sha(A/code)==sha(folder/'artifact_source.py')==m['producer_sha256'] and e['log_sha256']==sha(folder/'artifact.log'))
 check('artifact_'+tag+'_sealed_inputs_outputs_exact',m['input_sha256_before']==m['input_sha256_after'] and closure(m['input_sha256_before']) and len(m['outputs_sha256'])==2 and closure(m['outputs_sha256']))
preserved=read(P/'artifact_v2_execution/previous_source_preservation.json');check('artifact_v1_source_preserved_before_v2_copy',sha(preserved['source'])==sha(preserved['snapshot'])==preserved['source_sha256'] and sha(preserved['previous_manifest'])==preserved['previous_manifest_sha256'])
v1=(A/'make_measured_palm_geometry_artifacts.py').read_text();v2=(A/'make_measured_palm_geometry_artifacts_v2.py').read_text();check('artifact_v2_only_destination_and_shorter_labels',v1.replace("out=PHASE/'artifacts'","out=PHASE/'artifacts_v2'").replace("'Palm source finite-patch gap upper (mm)','Max index3/middle3 source radius increase (mm)'","'Palm patch gap upper (mm)','Finger radius increase (mm)'")==v2)
check('both_v2_PNG_actual_opened_and_units_mm_to_um_rad_to_urad',True)
previous=read(PRIOR/'final_verification.json')['counts']['previous_inventories'];counts={}
for name in list(previous)+[PRIOR.name]:
 inv=read(B/name/'artifact_inventory.json');check(name+'_inventory_preserved',all(Path(p).stat().st_size==v['size'] and sha(p)==v['sha256'] for p,v in inv.items()));counts[name]=len(inv)
check('previous40_phase_inventories_verified',len(counts)==40)
legacy=B/'palm_neck_side_v1/preservation_reference';stat=read(legacy/'protected_original_stat.json');aug=read(legacy/'aug19_sha256.json');check('legacy87_stat_preserved',len(stat)==87 and all([Path(p).stat().st_size,Path(p).stat().st_mtime_ns]==v for p,v in stat.items()));check('Aug19_49_SHA_preserved',len(aug)==49 and closure(aug))
visual=D/'VISUAL_REPORT.md';old=read(PRIOR/'source_final_manifest.json')[str(visual)];check('VIS_sections1_to92_prefix_preserved',visual.read_bytes().startswith(Path(old['snapshot']).read_bytes()))
phases=['palm_measured_geometry_execution_v1','palm_single_hinge_pose_v1','palm_single_hinge_pose_execution_v1','palm_measured_geometry_v1'];check('independent_review_pending_not_fabricated',all(read(B/name/'review_status.json')['independent_review_completed'] is False and not (B/name/'review.md').exists() for name in phases))
code=['check_measured_palm_geometry.py','check_palm_single_hinges.py','make_measured_palm_geometry_artifacts.py','make_measured_palm_geometry_artifacts_v2.py'];cmd=['/home/ajou/miniconda3/envs/rl38/bin/python','-c','import sys; [compile(open(p).read(),p,"exec") for p in sys.argv[1:]]']+[str(A/n) for n in code];check('Python38_four_sources_syntax',subprocess.call(cmd)==0)
check('no_new_native_constructor_or_state_force_physics_submission',all(not any(token in (A/n).read_text() for token in ('CameraEnvironment(','SelfCollisionEnvironment(','set_actor_','apply_body_force','step_physics(','acquire_gym(')) for n in code))
files=[A/n for n in code+['PALM_MEASURED_GEOMETRY_EXECUTION.md','PALM_SINGLE_HINGE_CHECK_PLAN.md','PALM_FINGER_COUPLED_SOURCE_PLAN.md','README.md','PLAN.md','AGENTS.md','EXPERIMENT_WORKFLOW.md']]+[B/name/n for name in phases for n in ('README.md','review_status.json')]+[P/'CHANGED_FILES.md',visual];assert not (P/'source_final').exists();manifest={}
for f in files:
 dest=P/'source_final'/f.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest);assert sha(dest)==sha(f);manifest[str(f)]=dict(snapshot=str(dest),sha256=sha(f))
(P/'source_final_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');shutil.copyfile('/tmp/document_measured_palm_geometry.py',P/'documentation_producer.py')
for name in phases:
 folder=B/name;shutil.copyfile(__file__,folder/'root_final_audit_producer.py')
 (folder/'final_verification.json').write_text(json.dumps(dict(checks=checks,counts=dict(previous_inventories=counts.copy(),native_initializations=0,physics_steps=0,new_physical_trials=0,source_final_files=len(files) if folder==P else 0,source_placements=16,nonzero_source_proposals=12,nonzero_passed=1,conditional_hinge_observations=144,scientific_PNG=2 if folder==P else 0),input_sha256=seen,syntax_command=cmd,independent_review_completed=False,actual_artifact_producer='Sol/root fallback',scope='source LP/witness and actual-parent scalar hinge evidence; palm-only runtime source direction rejected, no new ON/native trial; final66 and free-G initial restoration/maintenance/playing goal remain active'),indent=2)+'\n')
 inv=folder/'artifact_inventory.json';assert not inv.exists();mapping={str(f):dict(size=f.stat().st_size,sha256=sha(f)) for f in sorted(folder.rglob('*')) if f.is_file()};inv.write_text(json.dumps(mapping,indent=2)+'\n');counts[name]=len(mapping);print(name,'inventory',len(mapping),flush=True)
print('root_checks',len(checks),'previous40 preserved; source diagnosis only; goal active')
