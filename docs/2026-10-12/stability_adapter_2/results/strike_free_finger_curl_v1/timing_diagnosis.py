"""Saved-state timing diagnosis only; no simulator imports or execution."""
import ast
import hashlib
import json
import math
from pathlib import Path

ROOT = Path('/home/ajou/yigyu/3')
RESULTS = ROOT / 'docs/2026-10-12/stability_adapter_2/results'
OUT = Path(__file__).resolve().parent
TRIALS = ('strike_free_finger_curl_v1', 'strike_timed_wait_rebase_v1')
SOURCE = ROOT / 'tab2body/env/tasks/task_strike.py'
EVENTS = ROOT / 'tab2body/env/strike_events.py'
CONTRACT = ROOT / 'tab2body/strike_v2_contract.py'
FROZEN = RESULTS / TRIALS[0] / 'native/source_before/stability_adapter_2'
INFO_KEYS = (
    'action_motor_phase', 'motor_phase', 'target_event_index_before_step', 'event_index_after_step',
    'target_string', 'motion_target_string', 'target_direction_down', 'physical_release',
    'physical_release_string', 'physical_release_direction', 'physical_target_hit', 'target_hit',
    'timing_sample', 'timing_error_ms', 'premature_release', 'miss', 'release_phase_violation',
    'wrong_crossing_count', 'strum_wrong_direction_count', 'strum_unplanned_crossing_count',
    'strum_order_violation_count', 'strum_duplicate_crossing_count', 'blocked_release_count',
    'recovery_complete_pulse', 'scheduled_recovery_complete_pulse', 'recovery_clearance_required',
    'recovery_clearance_lifted', 'recovery_clearance_reached', 'recovery_required_frames',
    'recovery_available_frames', 'recovery_reset_count', 'approach_open', 'entry_ready',
    'entry_distance_m', 'tip_position_g', 'tip_velocity_g', 'tip_speed_m_s',
    'target_original_time_s', 'target_effective_time_s', 'timing_left_tolerance_ms',
    'timing_right_tolerance_ms', 'target_traversal_mask', 'accepted_release_mask',
    'strike_true_positive_count', 'strike_false_positive_count', 'strike_false_negative_count',
    'wrong_crossing_count_termination', 'guitar_penetration_depth', 'guitar_swept_penetration_depth',
    'guitar_penetration', 'guitar_penetration_termination', 'failure_termination',
)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def one(value):
    return value[0] if isinstance(value, list) and len(value) == 1 else value


def norm(values):
    return math.sqrt(sum(x * x for x in values))


def source_excerpt(text, start, end):
    return [{'line': i + 1, 'text': line} for i, line in enumerate(text.splitlines()) if start <= i + 1 <= end]


def main():
    raw_paths = [RESULTS / trial / 'native/data' / name for trial in TRIALS
                 for name in ('controls.json', 'trace.json', 'initial_values.json', 'report.json',
                              'checkpoint_connection.json', 'PD_phase_properties.json')]
    source_paths = [SOURCE, EVENTS, CONTRACT, FROZEN / 'run_strike_free_finger_curl.py',
                    FROZEN / 'run_strike_timed_wait_rebase.py', FROZEN / 'strike_native_view.py']
    paths = source_paths + raw_paths
    # Seal every analysis input before parsing or inspecting any source/helper/raw content.
    before = {str(path): digest(path.read_bytes()) for path in paths}
    cached = {str(path): path.read_bytes() for path in paths}
    assert all(digest(cached[str(path)]) == before[str(path)] for path in paths)
    tree = ast.parse(cached[str(CONTRACT)].decode())
    assignment = next(node for node in tree.body if isinstance(node, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == 'STRIKE_V2_BLOCK_SIZES' for t in node.targets))
    dims = ast.literal_eval(assignment.value.args[0])
    slices, start = {}, 0
    for name, width in dims:
        slices[name] = (start, start + width)
        start += width
    assert start == 303
    result = {'scope': 'Frozen saved control/native trace and original source semantics; read-only arithmetic, no causal or force certificate',
              'physics_steps': 0, 'native_initializations': 0,
              'time_semantics': 'command time is pre four physics steps; info is source feedback after those steps; source song time advances 1/60 afterward. String indices are raw zero-based.',
              'input_sha256_before_content_analysis': before, 'observation_slices': slices, 'trials': {},
              'analysis_script_sha256': digest(Path(__file__).read_bytes())}
    for trial in TRIALS:
        directory = RESULTS / trial / 'native/data'
        files = {p.name: json.loads(cached[str(p)]) for p in raw_paths if p.parent == directory}
        controls, trace, initial = [files[n] for n in ('controls.json', 'trace.json', 'initial_values.json')]
        names = initial['joint_names']
        controlled = [i for i, n in enumerate(names) if n.startswith(('R_Shoulder', 'R_Elbow', 'R_Wrist', 'RH:'))]
        assert len(controlled) == 30
        rows, pick_checks, proprio_checks = [], [], []
        for index, control in enumerate(controls):
            info, adapter = control.get('info'), control.get('phase_target_residual')
            if not info or not adapter:
                continue
            observation = one(control['observation'])
            assert len(observation) == 303
            block = lambda key: observation[slices[key][0]:slices[key][1]]
            tip = block('O_hand_geometry')[15:18]
            velocity = block('O_hand_geometry')[24:27]
            vectors = block('O_target_geometry')
            points = {name: [a + b for a, b in zip(tip, vectors[offset:offset + 3])]
                      for name, offset in (('READY', 0), ('ENTRY', 3), ('geometry5_EXIT_or_clearance', 6), ('source_phase_active', 9))}
            distances = {name: norm(vectors[offset:offset + 3]) * 1000
                         for name, offset in (('READY', 0), ('ENTRY', 3), ('geometry5_EXIT_or_clearance', 6), ('source_phase_active', 9))}
            target = adapter['target_G_m']
            actual = adapter['actual_angles_rad']
            joints = adapter['joint_indices']
            final = [control['final_targets_rad'][i] for i in joints]
            previous = adapter['previous_actuator_targets_rad']
            error = [a - b for a, b in zip(final, actual)]
            proprio = block('O_proprio')
            native_velocity = [proprio[30 + controlled.index(i)] for i in joints]
            recovery = block('O_recovery')
            row = {'control_index': index, 'command_native_time_s': control['time_s'],
                   'feedback_native_time_s': control['after_physics_step'] / 240,
                   'command_physics_step': control['before_physics_step'],
                   'song_before_s': control['song_time_s'], 'song_after_s': control['source_song_time_after_s'],
                   'command_source_phase': adapter['source_motor_phase'], 'command_event_key': adapter['adapter_event_key'],
                   'command_approach_open': adapter['adapter_approach_open'],
                   'command_entry_latch': adapter['adapter_entry_reached'], 'command_EXIT_active': adapter['adapter_exit_active'],
                   'command_geometry_index': adapter['target_geometry_index'], 'command_target_G_m': target,
                   'command_actual_pick_G_m': tip, 'command_pick_body_velocity_in_moving_G_m_s': velocity,
                   'command_pick_body_speed_in_moving_G_m_s': norm(velocity),
                   'command_source_geometry_G_m': points, 'command_source_geometry_distance_mm': distances,
                   'command_actual_pick_to_command_target_mm': norm([a - b for a, b in zip(tip, target)]) * 1000,
                   'command_recovery_flags': {'valid': bool(recovery[0]), 'clearance_required': bool(recovery[7]),
                                              'clearance_lifted': bool(recovery[8]), 'clearance_reached': bool(recovery[9])},
                   'command_next_entry_lift_G_m': [a + b for a, b in zip(tip, recovery[13:16])],
                   'native_R9_velocity_rad_s': native_velocity,
                   'R9_final_target_minus_actual_rad': error, 'R9_goal_actual_RMS_rad': norm(error) / 3,
                   'R9_goal_actual_max_abs_rad': max(map(abs, error)),
                   'R9_final_targets_rad': final, 'R9_actual_rad': actual,
                   'R9_target_step_from_previous_rad': [a - b for a, b in zip(final, previous)],
                   'R9_native_velocity_RMS_rad_s': norm(native_velocity) / 3,
                   'source_policy_R9_targets_rad': adapter['policy_targets_rad'],
                   'feedback': {k: one(info[k]) for k in INFO_KEYS if k in info}, 'detected_release_details': []}
            flags = row['command_recovery_flags']
            row['command_geometry5_kind'] = ('release_lift' if not flags['clearance_lifted'] else
                                            'next_ready' if flags['clearance_reached'] else 'next_entry_lift') if flags['valid'] and flags['clearance_required'] else 'original_exit_depth'
            row['current_target_time_to_command_s'] = one(info['target_effective_time_s']) - control['song_time_s']
            row['current_target_late_window_end_s'] = one(info['target_effective_time_s']) + one(info['timing_right_tolerance_ms']) / 1000
            mask = one(info['release_mask'])
            for string, released in enumerate(mask):
                if not released:
                    continue
                subframe = one(info['release_subframe_t'])[string]
                release_song = control['song_time_s'] + subframe / 60
                row['detected_release_details'].append({
                    'string_index': string, 'direction': one(info['release_direction'])[string],
                    'subframe_t': subframe, 'release_song_time_s': release_song,
                    'release_native_time_s': control['time_s'] + subframe / 60,
                    'signed_error_vs_current_event_ms': (release_song - one(info['target_effective_time_s'])) * 1000,
                    'accepted': one(info['accepted_release_mask'])[string],
                    'depth_m': one(info['release_depth_m'])[string],
                    'across_speed_m_s': one(info['release_across_speed_m_s'])[string],
                    'crossing_y_G_m': one(info['release_crossing_y'])[string],
                    'zone_allowed': one(info['release_zone_allowed'])[string]})
            previous_tip = one(controls[index - 1]['info']['tip_position_g']) if index and controls[index - 1].get('info') else None
            row['previous_detector_tip_G_m'] = previous_tip
            if previous_tip is not None:
                row['previous_detector_tip_to_current_ENTRY_mm'] = norm([a - b for a, b in zip(previous_tip, points['ENTRY'])]) * 1000
            pick_checks.append(norm([a - b for a, b in zip(tip, control['readiness']['pick_G_m'])]))
            proprio_checks.append(max(abs(proprio[k] - adapter['actual_dofs_rad'][i]) for k, i in enumerate(controlled)))
            rows.append(row)
        previous_phase = None
        transitions, physical, misses, pulses, terminal = [], [], [], [], []
        for row in rows:
            info = row['feedback']
            if info['motor_phase'] != previous_phase:
                transitions.append(row)
            if info['physical_release']:
                physical.append(row)
            if info['miss']:
                misses.append(row)
            if info['recovery_complete_pulse'] or info['scheduled_recovery_complete_pulse']:
                pulses.append(row)
            if info['failure_termination']:
                terminal.append(row)
            previous_phase = info['motor_phase']
        selected = []
        for requested in (1.2333333333, 1.25, 1.3333333333, 1.35, 1.3666666667, 1.3833333333,
                          1.55, 1.5666666667, 1.75, 2.3666666667, 2.4833333333, 2.8, 3.0166666667, 3.3833333333):
            selected.append({'requested_native_command_time_s': requested,
                             **min(rows, key=lambda row: abs(row['command_native_time_s'] - requested))})
        result['trials'][trial] = {'control_count': len(controls), 'saved_native_state_count': len(trace),
                                  'source_feedback_count': len(rows), 'play_start_native_time_s': files['report.json']['play_start_time_s'],
                                  'phase_transitions': transitions, 'physical_releases': physical, 'misses': misses,
                                  'recovery_pulses': pulses, 'terminal_rows': terminal, 'selected_rows': selected,
                                  'all_source_feedback_rows': rows, 'PD_switches': [{'time_s': p['time_s'], 'source_motor_phase': p['source_motor_phase'], 'damping_scale': p['damping_scale']} for p in files['PD_phase_properties.json']],
                                  'observation_pick_vs_readiness_max_difference_m': max(pick_checks),
                                  'observation_proprio_vs_native_actual_max_difference_rad': max(proprio_checks)}
    result['source_evidence'] = {
        str(SOURCE): {str(a): source_excerpt(cached[str(SOURCE)].decode(), a, b) for a, b in
                      ((1382, 1453), (1460, 1507), (2009, 2041), (3640, 3660), (3720, 3770),
                       (3830, 3839), (3939, 3957), (3985, 4015), (4168, 4253), (4256, 4270), (4351, 4359))},
        str(EVENTS): {str(a): source_excerpt(cached[str(EVENTS)].decode(), a, b) for a, b in
                     ((653, 695), (699, 733), (963, 972))},
        str(FROZEN / 'run_strike_free_finger_curl.py'): {'124': source_excerpt(cached[str(FROZEN / 'run_strike_free_finger_curl.py')].decode(), 124, 218)}}
    result['input_sha256_after_analysis'] = {str(path): digest(path.read_bytes()) for path in paths}
    result['checks'] = {'input_sources_helpers_raw_sealed_before_content_analysis': True,
                        'cached_content_matches_pre_analysis_seal': all(digest(cached[str(p)]) == before[str(p)] for p in paths),
                        'input_files_unchanged_to_end': before == result['input_sha256_after_analysis'],
                        'observation_geometry_from_original_303_contract': True, 'zero_native_physics': True,
                        'source_obs_native_proprio_match': all(t['observation_proprio_vs_native_actual_max_difference_rad'] < 1e-7 for t in result['trials'].values()),
                        'source_obs_actual_pick_match': all(t['observation_pick_vs_readiness_max_difference_m'] < 1e-6 for t in result['trials'].values())}
    assert all(result['checks'].values()), result['checks']
    (OUT / 'timing_diagnosis.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'checks': result['checks'], 'trials': {trial: {'releases': [(r['command_native_time_s'], r['feedback']['physical_release_string'], r['feedback']['physical_target_hit'], r['feedback']['target_hit'], r['feedback']['timing_error_ms']) for r in t['physical_releases']],
                               'pulse_times': [(r['command_native_time_s'], r['feedback']['recovery_complete_pulse'], r['feedback']['scheduled_recovery_complete_pulse']) for r in t['recovery_pulses']],
                               'terminal_feedback_times': [r['feedback_native_time_s'] for r in t['terminal_rows']]} for trial, t in result['trials'].items()}}, indent=2))


if __name__ == '__main__':
    main()
