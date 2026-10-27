"""Offline audit of completed postclearance prestage; never imports a native environment."""
import ast
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import torch
from scipy.spatial.transform import Rotation

P = Path(__file__).resolve().parent
N = P/'native'
B = P.parent/'strike_lateral_staging_v1/native'
ROOT = P.parents[4]
TASK = ROOT/'tab2body/env/tasks/task_strike.py'
EVENTS = ROOT/'tab2body/env/strike_events.py'
CHECKPOINT = ROOT/'strike/training/runs/20260920_Jazz1_sync_baseline/checkpoints/strike_010000.pt'
BASE_AUDIT = B.parent/'audit_lateral_staging.py'
required = [N/'inputs_after.json', N/'data/report.json']
if not all(p.exists() for p in required):
    raise SystemExit('Native completion records unavailable; no raw analysis performed.')
paths = [Path(__file__).resolve()]
for base in (N, B):
    paths += [base/name for name in ('inputs_before.json', 'inputs_after.json')]
    paths += [base/'data'/name for name in
              ('controls.json', 'trace.json', 'initial_values.json', 'PD_phase_properties.json', 'report.json', 'checkpoint_connection.json')]
paths += [N/'source_before/stability_adapter_2/run_strike_postclearance_prestage.py',
          B/'source_before/stability_adapter_2/run_strike_lateral_staging.py',
          N/'source_before/stability_adapter_2/strike_native_view.py']
paths += [BASE_AUDIT, TASK, EVENTS, CHECKPOINT]
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
producer = N/'source_before/stability_adapter_2/run_strike_postclearance_prestage.py'
baseline_producer = B/'source_before/stability_adapter_2/run_strike_lateral_staging.py'
producer_key = next(k for k in manifest_before['sha256'] if k.endswith('/stability_adapter_2/run_strike_postclearance_prestage.py'))
assert before[str(producer)] == manifest_before['sha256'][producer_key]
trees = [ast.parse(cache[str(p)].decode()) for p in (producer, baseline_producer)]
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
first_stage = next((r for r,br in zip(c,bc) if r['final_targets_rad']!=br['final_targets_rad']),None)
assert first_stage is not None
stage_time=first_stage['time_s']
def common(row):
    result=dict(row)
    if 'phase_target_residual' in result:
        a=dict(result['phase_target_residual'])
        for key in ('scope','adapter_waypoint_G_m','postclearance_prestage'):
            a.pop(key,None)
        result['phase_target_residual']=a
    return result
prefix=[r for r in c if r['time_s']<stage_time]
assert [common(r) for r in prefix]==[common(r) for r in bc[:len(prefix)]]
nt=[r for r in t if r['time_s']<=stage_time]
assert nt==[r for r in bt if r['time_s']<=stage_time]
assert [r for r in pd if r['time_s']<=stage_time]==[r for r in bpd if r['time_s']<=stage_time]
# Execute only two pure tensor geometry functions extracted from sealed original AST.
def pure_function(path, name):
    tree=ast.parse(cache[str(path)].decode())
    node=function(tree,name)
    namespace={'torch':torch}
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),namespace)
    return namespace[name]
next_string=pure_function(EVENTS,'strike_next_traversal_string')
lane_geometry=pure_function(TASK,'_string_lane_geometry')
checkpoint=torch.load(io.BytesIO(cache[str(CHECKPOINT)]),map_location='cpu',weights_only=True)
config=checkpoint['checkpoint_contract']['payload']['config']['strike']
trajectory=config['trajectory'];zone=config['zone']
assert checkpoint['training_context']['curriculum_stage']=='S3_SONG_INTEGRATION'
assert checkpoint['environment_state']['zone_gate_active']
ready_across=trajectory['ready_across_offset_m'];ready_height=trajectory['ready_height_m'];clearance_height=trajectory['clearance_height_m']
scheduled_completed=False; completion_transitions=[];prestage_rows=[];native_current_ready_count=0;max_current_ready_error=0.
previous_pick=None; previous_pick_time=None; latch=False; previous_key=None
actor_count=hold_count=anchor_count=rate_count=stage_count=0
max_geometry_error=max_native_anchor_error=0.
stage_rows=[];hold_anchor=None;frozen_goals=None;frozen_history=None;frozen_clock=None
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
        if key!=previous_key or source_phase!=1:latch=False
        if source_phase==1 and entry_distance<=.006:latch=True
        previous_key=key
        opened=a['source_song_time_at_command_s']>=a['source_effective_target_time_s']+a['source_first_offset_s']-a['source_approach_lead_s']
        staged=source_phase==1 and opened and not latch and xy>.004
        exit_active=source_phase==1 and latch and opened
        waypoint=3 if source_phase==0 or (source_phase==1 and (not opened or staged)) else (5 if source_phase==2 or exit_active else 4)
        assert latch==a['adapter_entry_reached'] and opened==a['adapter_approach_open']
        assert staged==a['entry_staging_active'] and exit_active==a['adapter_exit_active']
        assert waypoint==a['target_geometry_index']
        assert a['entry_staging_xy_max_m']==.004 and a['source_entry_distance_m']==.006
        assert abs(xy-a['native_pick_to_ready_xy_m'])<2e-6
        assert abs(entry_distance-a['native_pick_to_entry_m'])<2e-6
        assert a['source_song_time_at_command_s']==r['song_time_s']
        error=max(float(np.linalg.norm(source_pick-pick)),float(np.linalg.norm(geometry[waypoint]-a['source_waypoint_G_m'])))
        max_geometry_error=max(max_geometry_error,error);assert error<2e-6
        p=a['postclearance_prestage'];ctx=bool(obs[253]);assert ctx==p['recovery_context_valid']
        assert source_phase==p['source_motor_phase']
        assert scheduled_completed==p['scheduled_recovery_completed']
        if ctx:
            assert bool(obs[260])==p['clearance_required'] and bool(obs[262])==p['clearance_reached']
        mismatch=False
        if source_phase==2:
            mask=torch.tensor([obs[119:125]>.5],dtype=torch.bool)
            completed=torch.tensor([obs[229:235]>.5],dtype=torch.bool)
            direction=1 if obs[137]>.5 else -1
            assert (obs[137]>.5)!=(obs[138]>.5)
            fallback=torch.zeros(1,dtype=torch.long);d=torch.tensor([direction])
            assert mask.any() and (mask & ~completed).any()
            musical_exit=next_string(mask,torch.zeros_like(mask),-d,fallback)
            entry=int(next_string(mask,completed,d,musical_exit)[0])
            assert entry==p['current_entry_string'] and direction==p['current_direction']
            mismatch=entry!=p['cached_next_entry_string'] or direction!=p['cached_next_direction'] or p['current_lane_y_m']!=p['cached_next_lane_y_m']
            assert p['current_event_ready_G_m'] is not None
        else:
            assert p['current_event_ready_G_m'] is None and p['current_entry_string'] is None and p['current_direction'] is None
        assert mismatch==p['target_mismatch']
        active=source_phase==2 and ctx and scheduled_completed and (not p['clearance_required'] or p['clearance_reached']) and mismatch
        assert active==p['active']
        adapter=np.asarray(a['adapter_waypoint_G_m'])
        if active:
            expected_adapter=np.asarray(p['current_event_ready_G_m']).copy()
            expected_adapter[2]+=max(ready_height,clearance_height)-ready_height
            assert np.allclose(adapter,expected_adapter,atol=2e-7,rtol=0)
            prestage_rows.append({'control_index':ci,'time_s':r['time_s'],'event_key':key,'source_waypoint_G_m':a['source_waypoint_G_m'],
                'adapter_waypoint_G_m':a['adapter_waypoint_G_m'],'current_event_ready_G_m':p['current_event_ready_G_m'],
                'current_entry_string':entry,'current_direction':direction,'cached_next_entry_string':p['cached_next_entry_string'],
                'cached_next_direction':p['cached_next_direction'],'scheduled_completed':scheduled_completed,
                'context_valid':ctx,'clearance_required':p['clearance_required'],'clearance_reached':p['clearance_reached']})
        else:
            assert np.array_equal(adapter,np.asarray(a['source_waypoint_G_m']))
        flag_before=scheduled_completed
        if r['info']['physical_target_hit'][0]:scheduled_completed=False
        if r['info']['scheduled_recovery_complete_pulse'][0]:scheduled_completed=True
        if flag_before!=scheduled_completed:
            completion_transitions.append({'command_time_s':r['time_s'],'feedback_time_s':r['after_physics_step']/240,
                'physical_target_hit':r['info']['physical_target_hit'][0],'scheduled_recovery_complete_pulse':r['info']['scheduled_recovery_complete_pulse'][0],
                'before':flag_before,'after':scheduled_completed})
        velocity=np.zeros(3) if previous_pick is None else (pick-previous_pick)/(r['time_s']-previous_pick_time)
        assert np.allclose(velocity,a['measured_pick_velocity_G_m_s'],atol=1e-12,rtol=0)
        feedback_active=source_phase in (0,2) or (source_phase==1 and (not opened or staged))
        feedback=-.1*velocity if feedback_active else np.zeros(3)
        length=float(np.linalg.norm(feedback))
        if length>.005:feedback*=.005/length
        assert feedback_active==a['velocity_feedback_active']
        assert np.allclose(feedback,a['velocity_feedback_G_m'],atol=1e-12,rtol=0)
        assert np.allclose(np.asarray(a['adapter_waypoint_G_m'])+feedback,a['target_G_m'],atol=1e-12,rtol=0)
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
        if r.get('actor_used') and source_phase==2:
            def string_point(name):
                pose=st['guitar_body_states'][v['guitar_body_names'].index(name)]['pose']
                world=np.array([pose['p'][k] for k in 'xyz'])
                return gr.inv().apply(world-gp)
            start=torch.tensor([[string_point('G:string'+str(j)) for j in range(1,7)]],dtype=torch.float64)
            end=torch.tensor([[string_point('G:string'+str(j)+'_end') for j in range(1,7)]],dtype=torch.float64)
            lane,across=lane_geometry(None,torch.tensor([p['current_lane_y_m']],dtype=torch.float64),segments=(start,end))
            ready=(lane[0,entry]-ready_across*direction*across[0,entry]).numpy();ready[2]+=ready_height
            error=float(np.linalg.norm(ready-np.asarray(p['current_event_ready_G_m'])))
            assert error<2e-6
            max_current_ready_error=max(max_current_ready_error,error);native_current_ready_count+=1
            if active:
                staged_ready=ready.copy();staged_ready[2]=float(lane[0,entry,2])+max(ready_height,clearance_height)
                assert np.allclose(staged_ready,adapter,atol=2e-6,rtol=0)
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
# Resolved info lane_allowed aliases the event buffer, which source resets before
# info return. Reconstruct the accepted crossing gate, rather than treating the
# reset alias as evidence of the just-resolved event's lane acceptance.
physical=[];wrong=[]
for r in c:
    if not r.get('actor_used'):continue
    info=r['info'];a=r['phase_target_residual'];meta=a['postclearance_prestage']
    if info['wrong_crossing_count'][0]>0:
        wrong.append({'command_time_s':r['time_s'],'feedback_time_s':r['after_physics_step']/240,'event_before':info['target_event_index_before_step'][0],
            'release_mask':info['release_mask'][0],'release_direction':info['release_direction'][0],'wrong_count':info['wrong_crossing_count'][0],
            'unplanned_crossing_count':info['strum_unplanned_crossing_count'][0],'wrong_direction_count':info['strum_wrong_direction_count'][0]})
    if not info['physical_target_hit'][0]:continue
    accepted=np.asarray(info['accepted_release_mask'][0],dtype=bool)
    crossings=np.asarray(info['release_crossing_y'][0]);offset=crossings-meta['current_lane_y_m']
    detector=np.asarray(info['release_zone_allowed'][0],dtype=bool)
    lane_at_release=bool(np.all((~accepted)|(detector&(np.abs(offset)<=zone['lane_allowed_half_width_m']))))
    timing=info['timing_error_ms'][0]
    timing_ok=-info['timing_left_tolerance_ms'][0]<=timing<=info['timing_right_tolerance_ms'][0]
    assert bool(info['target_hit'][0])==(timing_ok and lane_at_release)
    physical.append({'command_time_s':r['time_s'],'feedback_time_s':r['after_physics_step']/240,'event_before':info['target_event_index_before_step'][0],
        'event_after':info['event_index_after_step'][0],'physical_string_raw0':info['physical_release_string'][0],
        'physical_direction':info['physical_release_direction'][0],'timing_error_ms':timing,'timing_pass':timing_ok,
        'accepted_release_mask':accepted.tolist(),'accepted_crossing_y_m':crossings[accepted].tolist(),
        'current_lane_y_m':meta['current_lane_y_m'],'accepted_lane_offset_m':offset[accepted].tolist(),
        'lane_allowed_half_width_m':zone['lane_allowed_half_width_m'],'accepted_detector_zone_allowed':detector[accepted].tolist(),
        'lane_at_release_reconstructed':lane_at_release,'raw_zone_lane_allowed_alias':info['zone_lane_allowed'][0],
        'target_hit':info['target_hit'][0],'prepared_target_hit':info['prepared_target_hit'][0],
        'unprepared_target_hit':info['unprepared_target_hit'][0],'release_phase_violation':info['release_phase_violation'][0],
        'entry_ready_label':info['entry_ready'][0],'miss':info['miss'][0],
        'command_pick_G_m':a['measured_pick_G_m'],'feedback_pick_G_m':info['tip_position_g'][0],
        'command_source_waypoint_G_m':a['source_waypoint_G_m'],'command_adapter_waypoint_G_m':a['adapter_waypoint_G_m'],
        'command_servo_G_m':a['target_G_m']})
after={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
assert before==after
result={'input_SHA256_before_parsing':before,'input_SHA256_end':after,'inputs_unchanged':True,
        'native_manifest_after_reports_unchanged':True,'native_manifest_input_count':manifest_after['input_count'],
        'frozen_producer_matches_execution_manifest':True,
        'completed_5s_report_checks_all_pass':True,'initial_values_baseline_exact':True,
        'first_stage_time_s':stage_time,'first_stage_control_index':first_stage['before_physics_step']//4,
        'commonfield_control_prefix_exact_count':len(prefix),'native_trace_prefix_exact_count':len(nt),
        'native_trace_prefix_includes_stage_precommand_state':True,
        'prefix_ignored_metadata':['phase_target_residual.scope','phase_target_residual.adapter_waypoint_G_m','phase_target_residual.postclearance_prestage'],
        'PLAY_phase_open_latch_staging_waypoint_formula_count':actor_count,'PLAY_stage_count':stage_count,
        'all_target_rate_and_bounds_formula_count':rate_count,'source_observation_geometry_max_error_m':max_geometry_error,
        'exact_native_pick_anchor_count':anchor_count,'native_pick_anchor_max_error_m':max_native_anchor_error,
        'PLAY_integral_zero_R9_prevgoal_plus_2delta_fingers4curl_verified':True,
        'native_goal_scope':'stored final targets, unchanged submit AST and report submission checks; no separate native position-target getter measurement',
        'terminal_HOLD_count':hold_count,'terminal_HOLD_source_clock_history_other72_goals_frozen':True if hold is not None else None,
        'terminal_HOLD_and_submit_AST_baseline_exact':True,
        'terminal_PD_restore_native_readback_baseline_exact':True if hold is not None else None,
        'terminal_PD_restore_status':'검증 완료' if hold is not None else '해당 없음: terminal/HOLD 없이 5초 종료',
        'terminal_time_s':hold['time_s'] if hold is not None else None,'stage_rows':stage_rows,
        'first_divergent_control_precommand_obs_action_contacts_clock_baseline_exact':all(first_stage[k]==bc[c.index(first_stage)][k] for k in ('observation','action','contacts','song_time_s','source_history')),
        'prestage_count':len(prestage_rows),'prestage_rows':prestage_rows,
        'current_musical_entry_direction_from_source_observation_reconstructed':True,
        'current_lane_scope':'logged task target_lane_y; phase2 source geometry3 reflects cached motion and is not used as current musical READY',
        'current_event_READY_exact_native_string_geometry_count':native_current_ready_count,
        'current_event_READY_native_max_error_m':max_current_ready_error,
        'source_scheduled_completion_flag_transitions':completion_transitions,
        'completion_flag_scope':'initial false plus original physical_hit reset / scheduled completion pulse from each prior info step; required/reached independently compared to source observation only while context valid',
        'first_four_physical_records_baseline_exact':[{k:r['info'][k] for k in ('target_hit','physical_target_hit','timing_error_ms','target_event_index_before_step')} for r in c if r.get('actor_used') and r['info']['physical_target_hit'][0]][:4]==[{k:r['info'][k] for k in ('target_hit','physical_target_hit','timing_error_ms','target_event_index_before_step')} for r in bc if r.get('actor_used') and r['info']['physical_target_hit'][0]][:4],
        'physical_records':physical,'wrong_records':wrong,
        'source_target_hit_lines':'task_strike.py:3867-3873 accepted crossing detector-zone AND abs(crossing_y-currentlane)<=12.5mm; :3951-3957 timing candidate; :3977-3981 timingcandidate AND persistent event_zone_valid',
        'source_raw_zone_alias_lines':'task_strike.py:3982 alias; :4209 advance song; :2035 reset continuing event_zone_valid true; :4660 return alias',
        'clean_event_scope':'task_strike.py:4040 clean_event is used by reward call :4305; not directly by target_hit; entry_ready/phase_violation at :3939-3943 are labels and do not directly gate target_hit',
        'source_no_override_scope':'frozen producer inspected plus wrapper-reported unchanged source closure; differing resulting source flags follow differing saved physics, not equality of entire trajectories',
        'scope':'offline saved native/source controls; original phases/clock/detector unchanged; no new physics or contact causality/music success certification'}
(P/'postclearance_prestage_audit.json').write_text(json.dumps(result,indent=2)+'\n')
print({k:v for k,v in result.items() if k not in ('input_SHA256_before_parsing','input_SHA256_end','stage_rows','prestage_rows','physical_records','wrong_records','source_scheduled_completion_flag_transitions')})
