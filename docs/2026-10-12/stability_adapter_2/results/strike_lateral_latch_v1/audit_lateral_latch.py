"""Offline audit of completed lateral latch; never imports a native environment."""
import ast
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

P = Path(__file__).resolve().parent
N = P/'native'
B = P.parent/'strike_lateral_staging_v1/native'
required = [N/'inputs_after.json', N/'data/report.json']
if not all(p.exists() for p in required):
    raise SystemExit('Native completion records unavailable; no raw analysis performed.')
paths = [Path(__file__).resolve()]
for base in (N, B):
    paths += [base/name for name in ('inputs_before.json', 'inputs_after.json')]
    paths += [base/'data'/name for name in
              ('controls.json', 'trace.json', 'initial_values.json', 'PD_phase_properties.json', 'report.json', 'checkpoint_connection.json')]
paths += [N/'source_before/stability_adapter_2/run_strike_lateral_latch.py',
          B/'source_before/stability_adapter_2/run_strike_lateral_staging.py',
          N/'source_before/stability_adapter_2/strike_native_view.py',
          P.parent/'strike_lateral_staging_v1/audit_lateral_staging.py']
# SHA collection precedes all decoding, JSON/AST parsing, and numeric reads.
before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
cache = {str(p): p.read_bytes() for p in paths}
assert all(hashlib.sha256(cache[str(p)]).hexdigest()==before[str(p)] for p in paths)
load = lambda p: json.loads(cache[str(p)])
report = load(N/'data/report.json')
assert report['failure'] is None and report['completed_5s'] and all(report['checks'].values())
manifest_before, manifest_after = [load(N/name) for name in ('inputs_before.json', 'inputs_after.json')]
assert manifest_after['inputs_unchanged'] and manifest_after['changed']==[] and manifest_after['task_error'] is None
assert manifest_after['input_count']==len(manifest_before['sha256'])
producer = N/'source_before/stability_adapter_2/run_strike_lateral_latch.py'
producer_key = next(k for k in manifest_before['sha256'] if k.endswith('/stability_adapter_2/run_strike_lateral_latch.py'))
assert before[str(producer)] == manifest_before['sha256'][producer_key]
trees = [ast.parse(cache[str(p)].decode()) for p in (producer, B/'source_before/stability_adapter_2/run_strike_lateral_staging.py')]
def function(tree, name):
    return next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name==name)
def hold_body(tree):
    return next(n.orelse for n in ast.walk(tree) if isinstance(n, ast.If) and n.orelse and
                any(isinstance(z,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='song'
                                                    for t in z.targets) for z in n.orelse))
assert ast.dump(function(trees[0],'submit'),include_attributes=False)==ast.dump(function(trees[1],'submit'),include_attributes=False)
assert ast.dump(ast.Module(body=hold_body(trees[0]),type_ignores=[]),include_attributes=False)==ast.dump(ast.Module(body=hold_body(trees[1]),type_ignores=[]),include_attributes=False)
c,t,v,pd = [load(N/'data'/name) for name in ('controls.json','trace.json','initial_values.json','PD_phase_properties.json')]
bc,bt,bv,bpd = [load(B/'data'/name) for name in ('controls.json','trace.json','initial_values.json','PD_phase_properties.json')]
assert v==bv
lo,hi = [np.asarray(v[key],dtype=np.float32) for key in ('native_lower_rad','native_upper_rad')]
previous = np.asarray(v['initial_angles_rad'],dtype=np.float32)
source_right = [i for i,n in enumerate(v['joint_names']) if n.startswith(('R_Shoulder','R_Elbow','R_Wrist','RH:'))]
assert len(source_right)==30
first_stage = next((r for r in c if r.get('phase_target_residual',{}).get('entry_staging_active')),None)
assert first_stage is not None
def common(row):
    result=dict(row)
    if 'phase_target_residual' in result:
        a=dict(result['phase_target_residual'])
        for key in ('scope','adapter_lateral_ready_latched'):
            a.pop(key,None)
        result['phase_target_residual']=a
    return result
first_difference=next(i for i,(x,y) in enumerate(zip(c,bc)) if x['final_targets_rad']!=y['final_targets_rad'])
branch=c[first_difference];stage_time=branch['time_s']
assert common(branch)!=common(bc[first_difference])
branch_a=branch['phase_target_residual'];base_a=bc[first_difference]['phase_target_residual']
assert branch_a['source_motor_phase']==1 and branch_a['adapter_approach_open']
assert branch_a['adapter_lateral_ready_latched'] and not branch_a['adapter_entry_reached']
assert branch_a['native_pick_to_ready_xy_m']>.004
assert not branch_a['entry_staging_active'] and base_a['entry_staging_active']
assert branch_a['target_geometry_index']==4 and base_a['target_geometry_index']==3
assert not branch_a['velocity_feedback_active'] and base_a['velocity_feedback_active']
for key in ('observation','action','readiness','contacts','song_time_s','before_physics_step'):
    assert branch[key]==bc[first_difference][key]
prefix=[r for r in c if r['time_s']<stage_time]
assert [common(r) for r in prefix]==[common(r) for r in bc[:len(prefix)]]
nt=[r for r in t if r['time_s']<=stage_time]
assert nt==[r for r in bt if r['time_s']<=stage_time]
assert [r for r in pd if r['time_s']<=stage_time]==[r for r in bpd if r['time_s']<=stage_time]
previous_pick=None; previous_pick_time=None; latch=False; lateral_ready=False; previous_key=None
actor_count=hold_count=anchor_count=rate_count=stage_count=0
max_geometry_error=max_native_anchor_error=0.
stage_rows=[];hold_anchor=None;frozen_goals=None;frozen_history=None;frozen_clock=None
lateral_acquisitions=[];lateral_resets=[];latched_redepartures=[]
for ci,r in enumerate(c):
    requested=np.asarray(r['requested_targets_rad'],dtype=np.float32)
    final=np.asarray(r['final_targets_rad'],dtype=np.float32)
    rate=np.full(81,.8,dtype=np.float32)
    if r['phase'] in ('PLAY','HOLD'):rate[source_right]=3.2
    expected_final=np.clip(np.clip(requested,previous-rate/60,previous+rate/60),lo,hi).astype(np.float32)
    assert np.array_equal(final,expected_final)
    assert ((final>=lo)&(final<=hi)).all();rate_count+=1
    if r.get('actor_used'):
        actor_count+=1;a=r['phase_target_residual'];obs=np.asarray(r['observation'][0]);assert len(obs)==303
        pick=np.asarray(a['measured_pick_G_m']);source_pick=obs[93:96]
        geometry={i:source_pick+obs[start:start+3] for i,start in ((3,147),(4,150),(5,153))}
        source_phase=int(np.argmax(obs[224:227]));assert source_phase==a['source_motor_phase']
        key=a['adapter_event_key'];entry_distance=float(np.linalg.norm(pick-geometry[4]))
        xy=float(np.linalg.norm(pick[:2]-geometry[3][:2]))
        if key!=previous_key or source_phase!=1:
            if lateral_ready:lateral_resets.append({'time_s':r['time_s'],'event_key':key,'source_phase':source_phase})
            latch=False; lateral_ready=False
        if source_phase==1 and entry_distance<=.006:latch=True
        previous_key=key
        opened=a['source_song_time_at_command_s']>=a['source_effective_target_time_s']+a['source_first_offset_s']-a['source_approach_lead_s']
        if source_phase==1 and opened and xy<=.004:
            if not lateral_ready:lateral_acquisitions.append({'time_s':r['time_s'],'event_key':key,'READY_xy_error_m':xy})
            lateral_ready=True
        staged=source_phase==1 and opened and not latch and not lateral_ready
        assert lateral_ready==a['adapter_lateral_ready_latched']
        exit_active=source_phase==1 and latch and opened
        waypoint=3 if source_phase==0 or (source_phase==1 and (not opened or staged)) else (5 if source_phase==2 or exit_active else 4)
        assert latch==a['adapter_entry_reached'] and opened==a['adapter_approach_open']
        assert staged==a['entry_staging_active'] and exit_active==a['adapter_exit_active']
        if source_phase==1 and opened and lateral_ready and not latch and xy>.004:
            latched_redepartures.append({'time_s':r['time_s'],'event_key':key,'READY_xy_error_m':xy,
                                        'entry_distance_m':entry_distance,'selected_geometry_index':waypoint})
        assert waypoint==a['target_geometry_index']
        assert a['entry_staging_xy_max_m']==.004 and a['source_entry_distance_m']==.006
        assert abs(xy-a['native_pick_to_ready_xy_m'])<2e-6
        assert abs(entry_distance-a['native_pick_to_entry_m'])<2e-6
        assert a['source_song_time_at_command_s']==r['song_time_s']
        error=max(float(np.linalg.norm(source_pick-pick)),float(np.linalg.norm(geometry[waypoint]-a['source_waypoint_G_m'])))
        max_geometry_error=max(max_geometry_error,error);assert error<2e-6
        velocity=np.zeros(3) if previous_pick is None else (pick-previous_pick)/(r['time_s']-previous_pick_time)
        assert np.allclose(velocity,a['measured_pick_velocity_G_m_s'],atol=1e-12,rtol=0)
        feedback_active=source_phase in (0,2) or (source_phase==1 and (not opened or staged))
        feedback=-.1*velocity if feedback_active else np.zeros(3)
        length=float(np.linalg.norm(feedback))
        if length>.005:feedback*=.005/length
        assert feedback_active==a['velocity_feedback_active']
        assert np.allclose(feedback,a['velocity_feedback_G_m'],atol=1e-12,rtol=0)
        assert np.allclose(np.asarray(a['source_waypoint_G_m'])+feedback,a['target_G_m'],atol=1e-12,rtol=0)
        assert np.array_equal(a['integral_rad'],np.zeros(9))
        idx=a['joint_indices'];correction=np.asarray(a['correction_rad'])
        assert np.array_equal(np.asarray(a['previous_actuator_targets_rad'],dtype=np.float32),previous[idx])
        assert max(abs(correction))<=.15+1e-12
        assert np.allclose(a['applied_correction_rad'],2*correction,atol=1e-12,rtol=0)
        assert np.array_equal(requested[idx],np.clip(previous[idx]+2*correction,lo[idx],hi[idx]).astype(np.float32))
        curl=r['free_finger_curl'];finger_idx=curl['source_finger_joint_indices'];finger=np.asarray(curl['source_finger_targets_rad'],dtype=np.float32).copy()
        for joint in curl['joint_indices']:finger[finger_idx.index(joint)]+=.2
        assert np.array_equal(requested[finger_idx],finger)
        assert curl['pinch_requested_policy_exact'] and curl['nominal_additive_residual_rad']==.2
        if staged:
            stage_count+=1;stage_rows.append({'control_index':ci,'time_s':r['time_s'],'event_key':key,
                'READY_xy_error_m':xy,'entry_distance_m':entry_distance,'pick_G_m':pick.tolist(),
                'READY_G_m':geometry[3].tolist(),'servo_G_m':a['target_G_m'],
                'velocity_G_m_s':velocity.tolist(),'feedback_G_m':feedback.tolist()})
        point_metadata=a
    elif r['phase']=='HOLD':
        hold_count+=1;a=r['terminal_retraction'];idx=a['joint_indices'];outside=np.setdiff1d(np.arange(81),idx)
        pick=np.asarray(a['measured_pick_G_m']);anchor=np.asarray(a['anchor_G_m'])
        if hold_anchor is None:
            hold_anchor=anchor.copy();frozen_goals=previous.copy();frozen_history=r['source_history'];frozen_clock=r['song_time_s']
            assert np.array_equal(anchor[:2],pick[:2]) and anchor[2]>=pick[2]+.03-1e-12
        assert np.array_equal(anchor,hold_anchor)
        velocity=(pick-previous_pick)/(r['time_s']-previous_pick_time)
        assert np.allclose(velocity,a['measured_pick_velocity_G_m_s'],atol=1e-12,rtol=0)
        feedback=-.1*velocity;length=float(np.linalg.norm(feedback))
        if length>.005:feedback*=.005/length
        assert np.allclose(feedback,a['feedback_G_m'],atol=1e-12,rtol=0)
        assert np.allclose(anchor+feedback,a['servo_G_m'],atol=1e-12,rtol=0)
        correction=np.asarray(a['correction_rad']);assert max(abs(correction))<=.15+1e-12
        assert np.array_equal(np.asarray(a['previous_actuator_targets_rad'],dtype=np.float32),previous[idx])
        assert np.array_equal(requested[idx],np.clip(previous[idx]+2*correction,lo[idx],hi[idx]).astype(np.float32))
        assert np.array_equal(requested[outside],frozen_goals[outside]) and np.array_equal(final[outside],frozen_goals[outside])
        assert r['source_history']==frozen_history and r['song_time_s']==frozen_clock and not r['actor_used']
        point_metadata=a
    else:
        previous=final
        continue
    matches=[z for z in t if z['physics_step']==r['before_physics_step']]
    if matches:
        st=matches[0]['native_state'];g=st['guitar_body_states'][0]['pose'];h=st['human_body_states'][v['human_body_names'].index('RH:pick')]['pose']
        gp=np.array([g['p'][k] for k in 'xyz']);hp=np.array([h['p'][k] for k in 'xyz']);gr=Rotation.from_quat([g['r'][k] for k in 'xyzw'])
        error=float(np.linalg.norm(gr.inv().apply(hp-gp)-pick));assert error<1e-7
        max_native_anchor_error=max(max_native_anchor_error,error);anchor_count+=1
        assert np.allclose(gp+gr.apply(point_metadata.get('target_G_m',point_metadata.get('servo_G_m'))),point_metadata['target_W_m'],atol=1e-7,rtol=0)
    previous_pick=pick;previous_pick_time=r['time_s'];previous=final
hold=next((r for r in c if r['phase']=='HOLD'),None)
if hold is not None:
    assert pd[-1]['trigger']=='terminal_retraction' and pd[-1]['physics_step']==hold['before_physics_step']
    assert pd[-1]['native_readback_properties']==v['PD_properties']
for switch in pd[:-1] if hold is not None else pd:
    assert switch['state_preserved'] and switch['native_PD_properties']==switch['requested_PD_properties']
    expected=[dict(item) for item in v['PD_properties']]
    if switch['source_motor_phase']==1:
        for idx in switch['joint_indices']:expected[idx]['damping']*=.25
    assert switch['native_PD_properties']==expected
after={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
assert before==after
result={'input_SHA256_before_parsing':before,'input_SHA256_end':after,'inputs_unchanged':True,
        'native_manifest_after_reports_unchanged':True,'native_manifest_input_count':manifest_after['input_count'],
        'frozen_producer_matches_execution_manifest':True,
        'completed_5s_report_checks_all_pass':True,'initial_values_baseline_exact':True,
        'first_stage_time_s':first_stage['time_s'],'first_stage_control_index':first_stage['before_physics_step']//4,
        'first_latch_goal_divergence_time_s':stage_time,'first_latch_goal_divergence_control_index':first_difference,
        'first_divergence_precommand_observation_action_contacts_clock_exact':True,
        'first_divergence_condition':'open phase1·ENTRY 미도달·READY xy 재이탈>4mm이나 lateral latch가 이미 true라 ENTRY4 유지; baseline은 READY3+velocity feedback',
        'first_divergence_READY_xy_error_m':branch_a['native_pick_to_ready_xy_m'],
        'commonfield_control_prefix_exact_count':len(prefix),'native_trace_prefix_exact_count':len(nt),
        'native_trace_prefix_includes_first_divergence_precommand_state':True,
        'prefix_ignored_metadata':['phase_target_residual.scope','phase_target_residual.adapter_lateral_ready_latched'],
        'PLAY_phase_open_latch_staging_waypoint_formula_count':actor_count,'PLAY_stage_count':stage_count,
        'lateral_latch_acquisitions':lateral_acquisitions,'lateral_latch_resets':lateral_resets,
        'latched_READY_xy_redepartures_ENTRY_preserved':latched_redepartures,
        'all_target_rate_and_bounds_formula_count':rate_count,'source_observation_geometry_max_error_m':max_geometry_error,
        'exact_native_pick_anchor_count':anchor_count,'native_pick_anchor_max_error_m':max_native_anchor_error,
        'PLAY_integral_zero_R9_prevgoal_plus_2delta_fingers4curl_verified':True,
        'native_goal_scope':'저장 final target·동일 submit AST·report 제출 검사를 확인; 별도 native position-target getter 측정은 없음',
        'terminal_HOLD_count':hold_count,'terminal_HOLD_source_clock_history_other72_goals_frozen':True if hold_count else None,
        'terminal_HOLD_and_submit_AST_baseline_exact':True,
        'terminal_PD_restore_native_readback_baseline_exact':True if hold is not None else None,
        'terminal_PD_restore_status':'검증 완료' if hold is not None else '해당 없음: terminal/HOLD 없이 5초 종료',
        'terminal_time_s':hold['time_s'] if hold is not None else None,'stage_rows':stage_rows,
        'scope':'저장 native/source control의 offline 감사. 원본 phase/clock/detector 조건 유지; 새 물리·접촉 인과·완주 성공 인증 없음'}
(P/'lateral_latch_audit.json').write_text(json.dumps(result,indent=2)+'\n')
print({k:v for k,v in result.items() if k not in ('input_SHA256_before_parsing','input_SHA256_end','stage_rows')})
