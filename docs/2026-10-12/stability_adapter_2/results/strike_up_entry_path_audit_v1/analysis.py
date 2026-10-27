"""Read-only offline analysis of saved source observations and native records."""
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

ROOT = Path('/home/ajou/yigyu/3')
D = ROOT / 'docs/2026-10-12/stability_adapter_2/results'
NATIVE = D / 'strike_incremental_approach_v1/native'
OUT = Path(__file__).resolve().parent
paths = [NATIVE/'data'/n for n in ('controls.json', 'trace.json', 'initial_values.json', 'checkpoint_connection.json')]
paths += [NATIVE/'source_before/stability_adapter_2'/n for n in
          ('run_strike_incremental_approach.py', 'strike_native_view.py')]
paths += [ROOT/n for n in ('tab2body/env/tasks/task_strike.py', 'tab2body/strike_v2_contract.py', 'tab2body/env/strike_events.py')]
before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
cache = {str(p): p.read_bytes() for p in paths}
assert all(hashlib.sha256(cache[str(p)]).hexdigest() == before[str(p)] for p in paths)
data = lambda name: json.loads(cache[str(NATIVE/'data'/name)])
controls, trace, initial = [data(n) for n in ('controls.json', 'trace.json', 'initial_values.json')]
norm = lambda v: float(np.linalg.norm(v))
single = lambda v: v[0] if isinstance(v, list) and len(v)==1 else v
rows, verification, event_pulses = [], [], []
for ci, c in enumerate(controls):
    if not c.get('actor_used'):
        continue
    a, info, obs = c['phase_target_residual'], c['info'], c['observation'][0]
    assert len(obs)==303
    # ABI: proprio60+anchor18+hand30+grip7+event32 = target block147.
    pick = np.array(obs[93:96])
    ready, entry, exit_point, active = [pick+np.array(obs[start:start+3]) for start in (147,150,153,156)]
    next_entry_lift = pick+np.array(obs[266:269]) if obs[253] else None
    measured = np.array(a['measured_pick_G_m'])
    nominal = np.array(a['source_waypoint_G_m'])
    nominal_from_obs = {3:ready, 4:entry, 5:exit_point}[a['target_geometry_index']]
    checks = {'pick_error_m': norm(pick-measured),
              'ready_error_m': norm(ready-np.array(c['readiness']['ready_G_m'])),
              'selected_geometry_error_m': norm(nominal_from_obs-nominal)}
    assert max(checks.values()) < 2e-6
    match = [t for t in trace if t['physics_step']==c['before_physics_step']]
    if match:
        t=match[0]
        assert abs(t['time_s']-c['time_s'])<1e-12
        state=t['native_state'];gb=state['guitar_body_states'][initial['guitar_body_names'].index('guitar')]['pose']
        hb=state['human_body_states'][initial['human_body_names'].index('RH:pick')]['pose']
        gp=np.array([gb['p'][k] for k in 'xyz']);hp=np.array([hb['p'][k] for k in 'xyz'])
        gr=Rotation.from_quat([gb['r'][k] for k in 'xyzw'])
        native_pick=gr.inv().apply(hp-gp)
        checks['exact_trace_pick_error_m']=norm(native_pick-measured)
        assert checks['exact_trace_pick_error_m']<1e-10
    verification.append(checks)
    idx=a['joint_indices'];actual=np.array(a['actual_dofs_rad'])[idx]
    final=np.array(c['final_targets_rad'])[idx]
    err=final-actual
    releases = [{'raw_string_index': i, 'native_body_name': f'G:string{i+1}',
                 'direction': info['release_direction'][0][i],
                 'subframe_t': info['release_subframe_t'][0][i],
                 'depth_m': info['release_depth_m'][0][i],
                 'across_speed_m_s': info['release_across_speed_m_s'][0][i],
                 'crossing_y_m': info['release_crossing_y'][0][i]}
                for i, flag in enumerate(info['release_mask'][0]) if flag]
    fields = ['target_event_index_before_step','event_index_after_step','action_motor_phase','motor_phase',
              'target_string','motion_target_string','target_direction_down','target_effective_time_s',
              'physical_release','physical_release_string','physical_release_direction','physical_target_hit',
              'target_hit','prepared_target_hit','unprepared_target_hit','entry_ready','entry_distance_m',
              'miss','timing_sample','timing_error_ms','premature_release','release_phase_violation',
              'wrong_crossing_count','strum_wrong_direction_count','strum_unplanned_crossing_count',
              'scheduled_recovery_complete_pulse','recovery_complete_pulse','recovery_clearance_required',
              'recovery_clearance_lifted','recovery_clearance_reached','done']
    row={'control_index':ci,'command_time_s':c['time_s'],'feedback_time_s':c['after_physics_step']/240,
         'command_song_time_s':c['song_time_s'],'feedback_song_time_s':c['source_song_time_after_s'],
         'command_event_key_raw0based':a['adapter_event_key'], 'source_motor_phase_at_command':a['source_motor_phase'],
         'approach_open_at_command':a['adapter_approach_open'],'entry_latch_at_command':a['adapter_entry_reached'],
         'exit_active_at_command':a['adapter_exit_active'],'selected_geometry_index':a['target_geometry_index'],
         'time_to_target_s':obs[142],'window_open_delta_s':obs[143],'window_close_delta_s':obs[144],
         'pick_G_m':measured.tolist(),'pick_velocity_G_m_s':a['measured_pick_velocity_G_m_s'],
         'ready_G_m':ready.tolist(),'entry_G_m':entry.tolist(),'geometry5_G_m':exit_point.tolist(),
         'active_source_geometry_G_m':active.tolist(),
         'recovery_next_entry_lift_G_m':None if next_entry_lift is None else next_entry_lift.tolist(),
         'recovery_flags_at_command':dict(zip(('valid','clearance_required','clearance_lifted','clearance_reached'),
                                            [bool(obs[i]) for i in (253,260,261,262)])),
         'ready_xy_error_m':norm((ready-measured)[:2]), 'ready_z_error_m':float(ready[2]-measured[2]),
         'entry_xy_error_m':norm((entry-measured)[:2]),'entry_distance_m':norm(entry-measured),
         'ready_distance_m':norm(ready-measured),'geometry5_distance_m':norm(exit_point-measured),
         'final_minus_actual_R9_rad':err.tolist(),'final_minus_actual_R9_RMS_rad':math.sqrt(float(np.mean(err**2))),
         'final_minus_actual_R9_max_abs_rad':float(np.max(abs(err))),
         'command_goal_previous_R9_delta_rad':(final-np.array(a['previous_actuator_targets_rad'])).tolist(),
         'final_targets_R9_rad':final.tolist(),'actual_R9_rad':actual.tolist(),
         'adapter_servo_target_G_m':a['target_G_m'],'release_records':releases,
         'feedback':{k:single(info[k]) for k in fields if k in info}, 'done':c['done']}
    rows.append(row)
    if any(single(info[k]) for k in ('physical_target_hit','miss','scheduled_recovery_complete_pulse','wrong_crossing_count')):
        event_pulses.append(row)
window=[r for r in rows if 3.0-1e-10<=r['command_time_s']<=3.63334]
transitions=[]
for a,b in zip(window,window[1:]):
    if (a['command_event_key_raw0based']!=b['command_event_key_raw0based'] or
        a['source_motor_phase_at_command']!=b['source_motor_phase_at_command'] or
        a['approach_open_at_command']!=b['approach_open_at_command'] or
        norm(np.array(a['geometry5_G_m'])-np.array(b['geometry5_G_m']))>.005):
        transitions.append({'previous':a,'current':b})
after={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
assert before==after
summary={'scope':'offline original source observations/native snapshots; no FK/environment import/physics or source/raw changes',
         'analysis_SHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         'input_SHA256_before_parsing':before,'input_SHA256_end':after,'inputs_unchanged':True,
         'index_convention':'source target and release string indices are 0-based; native G:stringN uses index+1',
         'command_feedback_convention':'controls time_s is pre-native command; info follows next4 native steps (1/60s)',
         'verification':{'actor_samples':len(rows),'exact_trace_matched':sum('exact_trace_pick_error_m' in v for v in verification),
                         'max_errors_m':{k:max(v.get(k,0) for v in verification) for k in verification[0]}},
         'window_3_to_terminal':window,'event_and_wrong_pulses':event_pulses,'window_transitions':transitions}
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
print(summary['verification'])
for r in window:
    f=r['feedback']
    print('%.6f'%r['command_time_s'],r['command_event_key_raw0based'],r['source_motor_phase_at_command'],
          r['selected_geometry_index'],r['approach_open_at_command'],r['entry_latch_at_command'],
          'xy %.2f z %.2f entry %.2f mm'%(r['ready_xy_error_m']*1000,r['ready_z_error_m']*1000,r['entry_distance_m']*1000),
          'pick',np.round(r['pick_G_m'],4).tolist(),'v',np.round(r['pick_velocity_G_m_s'],3).tolist(),
          'RMS %.3f'%r['final_minus_actual_R9_RMS_rad'],
          'miss',f.get('miss'),'wrong',f.get('wrong_crossing_count'),'release',r['release_records'])
