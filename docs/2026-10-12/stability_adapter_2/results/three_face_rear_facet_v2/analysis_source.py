import json,hashlib
from pathlib import Path
R=Path('/home/ajou/yigyu/3');B=R/'docs/2026-10-12/stability_adapter_2/results';V=B/'three_face_rear_facet_v2';U=B/'three_face_rear_facet_v1'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not (V/'analysis.json').exists()
d=read(V/'proposal.json');partial=read(U/'partial_selection.json'); inputs={str(p):sha(p) for p in [V/'proposal.json',V/'search_execution.json',V/'search.log',V/'facet_selection.json',V/'sensitivity.json',V/'recovery_review.md',U/'partial_selection.json',U/'search_execution.json',U/'previous_postprocessing_review.md',Path(__file__)]};inputs.update(d['input_sha256']);assert all(sha(p)==h for p,h in inputs.items())
rows=d['rejected']+d['rows'];first=next(r for r in rows if r['label']==partial['rejected'][0]['label']); old=partial['rejected'][0]
checks={'search_checks':all(d['checks'].values()),'4_completed_0_accepted_0_native':len(rows)==4 and not d['rows'] and d['native_initializations']==d['physics_steps']==0,'first_partial_actual_q_anchor_and_intersections_exact':all(first[k]==old[k] for k in ['expected_initial_angles_rad','expected_absolute_targets_rad','anchor_G_m','anchor_goal_G_m','source_intersections','reasons']),'same_absolute81_targets_other64_coordinates':True,'distance_intervals_valid':True}
sensitivity=read(V/'sensitivity.json');initial=read(B/'three_face_support_loss_v1/native/saved_finger_targets/initial_values.json');indices=[initial['human_joint_names'].index(n) for n in sensitivity['coordinate_names']]
for r in rows:
 checks['same_absolute81_targets_other64_coordinates'] &= r['expected_absolute_targets_rad']==d['saved_absolute_targets_rad'] and all(q==q0 for i,(q,q0) in enumerate(zip(r['expected_initial_angles_rad'],d['old_initial_angles_rad'])) if i not in indices) and all(lo<=r['expected_initial_angles_rad'][i]<=hi for i,lo,hi in zip(indices,r['search_lower_rad'],r['search_upper_rad']))
 for gap in r['source_hull_to_finite_patch'].values():
  checks['distance_intervals_valid'] &= 0<=gap['distance_lower_bound_m']<=gap['distance_m']+1e-12 and gap['feasibility_error_mm']<=1e-10 and gap['weight_sum_error']<=1e-10
assert all(checks.values()),checks
summary=[{k:r[k] for k in ['label','thumb_radius_rad','target_clearance_m','reasons','anchor_G_m','anchor_goal_G_m','anchor_goal_error_mm','source_intersections','palm_up_proxy_z','thumb_witness_toward_patch_GZ_dot','thumb_witness_rear_signed_mm','source_footprint','source_hull_to_finite_patch']} for r in rows]
checks['sealed_inputs_unchanged']=all(sha(p)==h for p,h in inputs.items());assert checks['sealed_inputs_unchanged']
result={'checks':checks,'input_sha256':inputs,'summary':summary,'facet_selection':read(V/'facet_selection.json'),'initial_anchors_G_m':sensitivity['initial_anchor_G_m'],'regions_G_m':d['regions_G_m'],'counts':{'unique_completed_source_candidates':4,'original_partial_completed_candidates':1,'original_numerically_interrupted_candidate':1,'original_partial_candidate_repeated_in_v2':1,'accepted_candidates':0,'native_initializations':0,'physics_steps':0},'scope':'source geometry candidate exclusion; first partial source attempt failed at second QP; successful recovery repeats source only; no new actual Gym frames/physics/stability/grip certification'}
(V/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');(V/'analysis_source.py').write_text(Path(__file__).read_text());print(json.dumps({'checks':checks,'counts':result['counts'],'input_count':len(inputs),'analysis_sha256':sha(V/'analysis.json')},indent=2))
