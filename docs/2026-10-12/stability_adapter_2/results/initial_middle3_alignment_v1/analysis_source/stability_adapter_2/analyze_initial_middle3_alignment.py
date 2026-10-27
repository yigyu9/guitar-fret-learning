"""Compare changed initial middle3 at identical absolute PD commands, from saved data."""
from pathlib import Path
import hashlib
import json
import numpy as np
from .analyze_natural_envelope import angles_deg
from .analyze_small_wrist_motion import metrics
from .analyze_body9_strap_minus4mm import strap_metrics
from .build_fixed_lower_asset import LOWER_BODIES
from .warmstart_targets import compose

R = Path(__file__).resolve().parents[1]; A = R / 'stability_adapter_2'
B = R / 'docs/2026-10-12/stability_adapter_2/results'; P = B / 'initial_middle3_alignment_v1'
FOLDERS = {'held_only': B / 'fixed_strap_middle_relax_v2/native', 'initial_aligned': P / 'native'}


def read(p): return json.loads(Path(p).read_text())
def rows(p): return [json.loads(s) for s in Path(p).read_text().splitlines()]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    assert not (P / 'analysis.json').exists()
    helpers = ['analyze_natural_envelope.py', 'analyze_small_wrist_motion.py', 'analyze_body9_strap_minus4mm.py', 'strap.py', 'warmstart_targets.py', 'build_fixed_lower_asset.py']
    paths = [Path(__file__).resolve(), A / 'INITIAL_MIDDLE3_ALIGNMENT_PLAN.md', P / 'preparation.json', P / 'proposal.json', P / 'native_execution.json'] + [A / n for n in helpers]
    paths += [f / n for f in FOLDERS.values() for n in ['initial_values.json', 'states.jsonl', 'trace.jsonl', 'controls.jsonl', 'contacts.jsonl', 'capture.json', 'report.json', 'videos.json', 'initial_grip_audit.json']]
    before = {str(f): sha(f) for f in paths}
    data = {label: dict(initial=read(f / 'initial_values.json'), states=rows(f / 'states.jsonl'), trace=rows(f / 'trace.jsonl'), controls=rows(f / 'controls.jsonl'), contacts=rows(f / 'contacts.jsonl'), capture=read(f / 'capture.json'), report=read(f / 'report.json'), videos=read(f / 'videos.json'), audit=read(f / 'initial_grip_audit.json')) for label, f in FOLDERS.items()}
    base = data['held_only']; names = base['initial']['human_joint_names']; axis = names.index('LH:middle3')
    other = [j for j in range(81) if j != axis]; changed_bodies = read(P / 'preparation.json')['changed_source_bodies']
    common = ['PD_properties', 'physics_parameters', 'guitar_goal_position_W_m', 'guitar_goal_quaternion_xyzw', 'human_joint_names', 'human_body_names', 'main_control_joint_names', 'absolute_strap_rest_length_m', 'initial_route_length_m', 'motion_command', 'strap_law_parameters']
    checks = {}; summary = []; windows = []; joint_series = []; guitar_series = []
    for label, d in data.items():
        initial, states, trace, controls = d['initial'], d['states'], d['trace'], d['controls']
        report, capture = d['report'], d['capture']; main_indices = [names.index(n) for n in initial['main_control_joint_names']]
        checks[label + '_complete_ordered_clock'] = report['completed'] and report['failure'] is None and report['native_initializations'] == 1 and report['physics_steps'] == 1200 and len(states) == len(trace) == 1201 and len(controls) == len(d['contacts']) == 1200 and [s['physics_step'] for s in states] == list(range(1201)) and [c['physics_step'] for c in controls] == [c['physics_step'] for c in d['contacts']] == list(range(1, 1201)) and all(t['time_s'] == j / 240 for j, t in enumerate(trace))
        checks[label + '_native_checks_fixed_LA'] = all(report['checks'].values()) and initial['absolute_strap_rest_length_m'] == 1.1018469719600776 and all(t['strap_rest_length_m'] == initial['absolute_strap_rest_length_m'] for t in trace)
        checks[label + '_fresh14_source1188_clear'] = len(d['audit']['checks']) == 14 and all(d['audit']['checks'].values()) and d['audit']['complete_source_self_screen']['pair_count'] == 1188 and not d['audit']['complete_source_self_screen']['intersections']
        checks[label + '_fixed_root_lower_allstates'] = all(all(s['human_body_states'][initial['human_body_names'].index(n)] == states[0]['human_body_states'][initial['human_body_names'].index(n)] for n in ('Pelvis',) + LOWER_BODIES) for s in states)
        checks[label + '_151frames_two_videos_readonly'] = len(capture['frames']) == 151 and len(d['videos']) == 2 and all(f['physics_step'] == j * 8 and f['time_s'] == j / 30 and f['render_preserves_states'] for j, f in enumerate(capture['frames'])) and all(v['ffmpeg_exit_code'] == v['ffprobe_exit_code'] == 0 and v['stream']['nb_read_frames'] == '151' and v['stream']['avg_frame_rate'] == '30/1' and abs(float(v['stream']['duration']) - 151 / 30) < 1e-6 and sha(v['path']) == v['sha256'] for v in d['videos'].values())
        offsets = np.array([initial['input_trial']['main_target_offsets_rad'].get(names[j], 0.) for j in main_indices])
        q0 = np.array(initial['initial_PD_target_rad'], dtype=np.float32)
        for c in controls:
            moving = offsets.copy(); moving[main_indices.index(names.index('L_Wrist_x'))] += c['wrist_motion_delta_rad']
            expected = q0.copy(); expected[main_indices] = (expected[main_indices].astype(float) + moving).astype(np.float32)
            command = np.array(c['final_target_rad'], dtype=np.float32)
            assert np.array_equal(expected, command) and np.array_equal(compose(q0, main_indices, moving, initial['PD_properties']['lower'], initial['PD_properties']['upper']), command)
            assert np.all(command >= initial['PD_properties']['lower']) and np.all(command <= initial['PD_properties']['upper']) and np.all(abs(moving) <= .3)
        checks[label + '_all1200_targets_reconstructed_unclipped'] = True
        if label == 'initial_aligned':
            checks['all11_common_initial_fields_exact'] = all(initial[k] == base['initial'][k] for k in common)
            restored = json.loads(json.dumps(initial['input_trial']))
            restored['initial_settings']['joint_angles_rad']['LH:middle3'] = base['initial']['input_trial']['initial_settings']['joint_angles_rad']['LH:middle3']
            restored['main_target_offsets_rad']['LH:middle3'] = base['initial']['input_trial']['main_target_offsets_rad']['LH:middle3']
            checks['only_middle3_initial_and_offset_changed'] = restored == base['initial']['input_trial']
            checks['other80_initial_q_exact_middle3_aligned'] = all(q0[j] == base['initial']['initial_PD_target_rad'][j] for j in other) and float(q0[axis]) == base['initial']['preserved_absolute_targets_rad'][axis] and initial['input_trial']['main_target_offsets_rad']['LH:middle3'] == 0.
            checks['all81_1200_final_commands_and_clock_exact'] = initial['preserved_absolute_targets_rad'] == base['initial']['preserved_absolute_targets_rad'] and all(c['final_target_rad'] == b['final_target_rad'] and all(c[k] == b[k] for k in ['physics_step', 'updated_before_step', 'command_time_s', 'wrist_motion_delta_rad']) for c, b in zip(controls, base['controls']))
            checks['G_and_other64_body_initial_states_exact'] = states[0]['guitar_body_states'] == base['states'][0]['guitar_body_states'] and all(states[0]['human_body_states'][j] == base['states'][0]['human_body_states'][j] for j, n in enumerate(initial['human_body_names']) if n not in changed_bodies)
            checks['all604_new_PNG_exact'] = all(sha(f) == h for frame in capture['frames'] for key in ['image_sha256', 'raw_image_sha256'] for f, h in frame[key].items())
        pos = np.array([t['guitar_position_m'] for t in trace]); quat = np.array([t['guitar_quaternion_xyzw'] for t in trace])
        raw_pos = np.array([[s['guitar_body_states'][0]['pose']['p'][k] for k in 'xyz'] for s in states])
        raw_quat = np.array([[s['guitar_body_states'][0]['pose']['r'][k] for k in 'xyzw'] for s in states]); raw_quat /= np.linalg.norm(raw_quat, axis=1, keepdims=True)
        checks[label + '_trace_matches_raw_G_pose'] = bool(np.array_equal(pos, raw_pos) and np.max(np.minimum(np.linalg.norm(quat - raw_quat, axis=1), np.linalg.norm(quat + raw_quat, axis=1))) < 1e-12)
        raw_pe = np.linalg.norm(raw_pos - np.array(initial['guitar_goal_position_W_m']), axis=1)
        raw_re = angles_deg(raw_quat, np.array(initial['guitar_goal_quaternion_xyzw']))
        raw_linear = np.linalg.norm(np.array([[s['guitar_body_states'][0]['vel']['linear'][k] for k in 'xyz'] for s in states]), axis=1)
        raw_angular = np.linalg.norm(np.array([[s['guitar_body_states'][0]['vel']['angular'][k] for k in 'xyz'] for s in states]), axis=1)
        checks[label + '_trace_errors_and_speeds_match_raw'] = bool(np.max(abs(raw_pe - np.array([t['position_error_m'] for t in trace]))) < 1e-9 and np.max(abs(raw_re - np.array([t['rotation_error_deg'] for t in trace]))) < 1e-4 and np.max(abs(raw_linear - np.array([t['linear_speed_mps'] for t in trace]))) < 1e-12 and np.max(abs(raw_angular - np.array([t['angular_speed_rad_s'] for t in trace]))) < 1e-12)
        for step, rec in enumerate(trace): guitar_series.append(dict(label=label, physics_step=step, time_s=step / 240, position_error_mm=rec['position_error_m'] * 1000, rotation_error_deg=rec['rotation_error_deg'], linear_speed_mps=rec['linear_speed_mps'], angular_speed_rad_s=rec['angular_speed_rad_s']))

        local_windows = []
        for start in range(480, 961, 4):
            wp = np.linalg.norm(pos[start:start + 241] - pos[start], axis=1) * 1000; wr = angles_deg(quat[start:start + 241], quat[start])
            local_windows.append(dict(label=label, start_step=start, end_step=start + 240, max_position_change_mm=float(wp.max()), max_rotation_change_deg=float(wr.max()), within_provisional_limits=bool(wp.max() <= 5 and wr.max() <= 1)))
        windows.extend(local_windows)
        actual = np.array([[x['pos'] for x in s['human_dof_states']] for s in states]); held = initial['preserved_absolute_targets_rad'][axis]
        for step in range(1201): joint_series.append(dict(label=label, physics_step=step, time_s=step / 240, middle3_actual_deg=float(np.degrees(actual[step, axis])), middle3_held_goal_deg=float(np.degrees(held)), middle2_actual_deg=float(np.degrees(actual[step, names.index('LH:middle2')]))))
        contacts = {}; self_steps = set()
        for rec in d['contacts']:
            for c in rec['contacts']:
                pair = [c['body0_name'], c['body1_name']]
                if all(n.startswith('human/') for n in pair): self_steps.add(rec['physics_step'])
                if c['lambda'] > 0 and any(n.startswith('human/') for n in pair) and any(n.startswith('guitar/') for n in pair): contacts.setdefault(next(n for n in pair if n.startswith('human/')), set()).add(rec['physics_step'])
        excess = np.maximum(np.array(initial['PD_properties']['lower']) - actual, actual - np.array(initial['PD_properties']['upper']))
        early = trace[:121]
        summary.append(dict(label=label, guitar=metrics(trace), strap=strap_metrics(trace, initial),
            early_0_to_05s=dict(max_initial_position_error_mm=max(t['position_error_m'] for t in early) * 1000, max_initial_rotation_error_deg=max(t['rotation_error_deg'] for t in early), max_linear_speed_mps=max(t['linear_speed_mps'] for t in early), max_angular_speed_rad_s=max(t['angular_speed_rad_s'] for t in early)),
            max_1s_position_change_mm=max(w['max_position_change_mm'] for w in local_windows), max_1s_rotation_change_deg=max(w['max_rotation_change_deg'] for w in local_windows), windows_within_provisional_limits=sum(w['within_provisional_limits'] for w in local_windows), outside_initial_envelope_samples=sum(t['position_error_m'] > .03 or t['rotation_error_deg'] > 5 for t in trace),
            middle3_goal_deg=float(np.degrees(held)), middle3_actual_samples_deg={str(step / 240):float(np.degrees(actual[step, axis])) for step in [0, 120, 480, 1200]}, initial_middle3_goal_error_deg=float(np.degrees(abs(actual[0, axis] - held))), max_middle3_goal_error_after2s_deg=float(np.degrees(abs(actual[480:, axis] - held).max())),
            human_guitar_positive_raw_lambda_steps={n:len(v) for n,v in sorted(contacts.items())}, human_self_contact_steps=len(self_steps), palm_up_proxy_passed=report['palm_up_proxy_passed'], constraint_violations=report['constraint_violations'], max_actual_native_bound_excess_rad=float(max(0, excess.max()))))
    after = {str(f):sha(f) for f in paths}; checks['inputs_preserved'] = before == after
    assert all(checks.values()), checks
    for name, records in [('windows.jsonl', windows), ('joint_series.jsonl', joint_series), ('guitar_series.jsonl', guitar_series)]: (P / name).write_text(''.join(json.dumps(r, allow_nan=False) + '\n' for r in records))
    result = dict(checks=checks, input_sha256_before=before, input_sha256_after=after, summary=summary, new_native_initializations=1, new_physics_steps=1200, actor_inference_calls=0, training_updates=0, naturalness_or_playing_success_certified=False, scope='one initial middle3 aligned at unchanged absolute81 commands; saved comparison, initial source/fresh gates, not cooked/force/playing certification')
    (P / 'analysis.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n'); print(json.dumps(dict(checks=checks, summary=summary), indent=2, allow_nan=False))


if __name__ == '__main__': main()
