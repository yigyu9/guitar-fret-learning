"""Compare the recorded middle3 goal change with its unchanged fixed-LA baseline."""
from pathlib import Path
import hashlib
import json
import numpy as np
from .analyze_natural_envelope import angles_deg
from .analyze_small_wrist_motion import metrics
from .analyze_body9_strap_minus4mm import strap_metrics
from .build_fixed_lower_asset import LOWER_BODIES
from .warmstart_targets import compose

R = Path(__file__).resolve().parents[1]
A = R / 'stability_adapter_2'
B = R / 'docs/2026-10-12/stability_adapter_2/results'
P = B / 'fixed_strap_middle_relax_v1'
FOLDERS = {'baseline': B / 'joint_only_fixed_strap_v1/native', 'middle3_minus005': P / 'native'}


def read(p):
    return json.loads(Path(p).read_text())


def rows(p):
    return [json.loads(s) for s in Path(p).read_text().splitlines()]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    assert not (P / 'analysis.json').exists()
    helpers = ['analyze_natural_envelope.py', 'analyze_small_wrist_motion.py', 'analyze_body9_strap_minus4mm.py', 'strap.py', 'warmstart_targets.py', 'build_fixed_lower_asset.py']
    paths = [Path(__file__).resolve(), A / 'FIXED_STRAP_MIDDLE_RELAX_PLAN.md', P / 'preparation.json', P / 'proposal.json', P / 'native_execution.json'] + [A / n for n in helpers]
    paths += [folder / n for folder in FOLDERS.values() for n in ['initial_values.json', 'states.jsonl', 'trace.jsonl', 'controls.jsonl', 'contacts.jsonl', 'capture.json', 'report.json', 'videos.json', 'initial_grip_audit.json']]
    before = {str(p): sha(p) for p in paths}
    data = {label: dict(initial=read(folder / 'initial_values.json'), states=rows(folder / 'states.jsonl'), trace=rows(folder / 'trace.jsonl'), controls=rows(folder / 'controls.jsonl'), contacts=rows(folder / 'contacts.jsonl'), capture=read(folder / 'capture.json'), report=read(folder / 'report.json'), audit=read(folder / 'initial_grip_audit.json'), videos=read(folder / 'videos.json')) for label, folder in FOLDERS.items()}
    base = data['baseline']
    names = base['initial']['human_joint_names']
    axis = names.index('LH:middle3')
    other = [j for j in range(81) if j != axis]
    main_indices = [names.index(n) for n in base['initial']['main_control_joint_names']]
    wrist = main_indices.index(names.index('L_Wrist_x'))
    checks, summary, windows, joint_series = {}, [], [], []
    delta = read(P / 'preparation.json')['actual_float32_target_delta_rad']
    common = ['native_initial_state', 'initial_PD_target_rad', 'PD_properties', 'physics_parameters', 'guitar_goal_position_W_m', 'guitar_goal_quaternion_xyzw', 'human_joint_names', 'human_body_names', 'main_control_joint_names', 'absolute_strap_rest_length_m', 'initial_route_length_m', 'motion_command', 'strap_law_parameters']
    for label, d in data.items():
        initial, states, trace, controls = d['initial'], d['states'], d['trace'], d['controls']
        report, capture = d['report'], d['capture']
        checks[label + '_complete_ordered_clock'] = report['completed'] and report['failure'] is None and report['native_initializations'] == 1 and report['physics_steps'] == 1200 and len(states) == len(trace) == 1201 and len(controls) == len(d['contacts']) == 1200 and [s['physics_step'] for s in states] == list(range(1201)) and [c['physics_step'] for c in controls] == [c['physics_step'] for c in d['contacts']] == list(range(1, 1201)) and all(t['time_s'] == j / 240 for j, t in enumerate(trace))
        checks[label + '_native_checks_fixed_LA'] = all(report['checks'].values()) and initial['absolute_strap_rest_length_m'] == 1.1018469719600776 and all(t['strap_rest_length_m'] == initial['absolute_strap_rest_length_m'] for t in trace)
        checks[label + '_fresh14_source1188_clear'] = len(d['audit']['checks']) == 14 and all(d['audit']['checks'].values()) and d['audit']['complete_source_self_screen']['pair_count'] == 1188 and not d['audit']['complete_source_self_screen']['intersections']
        checks[label + '_fixed_root_lower_allstates'] = all(all(s['human_body_states'][initial['human_body_names'].index(n)] == states[0]['human_body_states'][initial['human_body_names'].index(n)] for n in ('Pelvis',) + LOWER_BODIES) for s in states)
        checks[label + '_151frames_readonly_two_videos'] = len(capture['frames']) == 151 and len(d['videos']) == 2 and all(f['physics_step'] == j * 8 and f['time_s'] == j / 30 and f['render_preserves_states'] for j, f in enumerate(capture['frames'])) and all(v['ffmpeg_exit_code'] == v['ffprobe_exit_code'] == 0 and v['stream']['nb_read_frames'] == '151' and v['stream']['avg_frame_rate'] == '30/1' and abs(float(v['stream']['duration']) - 151 / 30) < 1e-6 and sha(v['path']) == v['sha256'] for v in d['videos'].values())
        if label != 'baseline':
            checks['all_common_initial_fields_exact'] = all(initial[k] == base['initial'][k] for k in common)
            restored = json.loads(json.dumps(initial['input_trial']))
            restored['main_target_offsets_rad']['LH:middle3'] = base['initial']['input_trial']['main_target_offsets_rad']['LH:middle3']
            checks['only_middle3_trial_offset_changed'] = restored == base['initial']['input_trial']
            checks['other80_all1200targets_clock_exact'] = all(all(c['final_target_rad'][j] == b['final_target_rad'][j] for j in other) and all(c[k] == b[k] for k in ['physics_step', 'updated_before_step', 'command_time_s', 'wrist_motion_delta_rad']) for c, b in zip(controls, base['controls']))
            checks['middle3_constant_actual_target_delta'] = all(c['final_target_rad'][axis] - b['final_target_rad'][axis] == delta for c, b in zip(controls, base['controls']))
            offsets = np.array([initial['input_trial']['main_target_offsets_rad'].get(names[j], 0.) for j in main_indices])
            for c in controls:
                moving = offsets.copy()
                moving[wrist] += c['wrist_motion_delta_rad']
                assert np.array_equal(compose(np.array(initial['initial_PD_target_rad'], dtype=np.float32), main_indices, moving, initial['PD_properties']['lower'], initial['PD_properties']['upper']), np.array(c['final_target_rad'], dtype=np.float32))
            checks['all1200_targets_reconstructed_unclipped'] = True
            checks['all604_new_PNG_exact'] = all(sha(p) == h for f in capture['frames'] for k in ['image_sha256', 'raw_image_sha256'] for p, h in f[k].items())
        p = np.array([t['guitar_position_m'] for t in trace])
        q = np.array([t['guitar_quaternion_xyzw'] for t in trace])
        raw_p = np.array([[s['guitar_body_states'][0]['pose']['p'][k] for k in 'xyz'] for s in states])
        raw_q = np.array([[s['guitar_body_states'][0]['pose']['r'][k] for k in 'xyzw'] for s in states])
        raw_q /= np.linalg.norm(raw_q, axis=1, keepdims=True)
        checks[label + '_trace_matches_raw_G_pose'] = bool(np.array_equal(p, raw_p) and np.max(np.minimum(np.linalg.norm(q - raw_q, axis=1), np.linalg.norm(q + raw_q, axis=1))) < 1e-12)
        local_windows = []
        for start in range(480, 961, 4):
            wp = np.linalg.norm(p[start:start + 241] - p[start], axis=1) * 1000
            wr = angles_deg(q[start:start + 241], q[start])
            local_windows.append(dict(label=label, start_step=start, end_step=start + 240, max_position_change_mm=float(wp.max()), max_rotation_change_deg=float(wr.max()), within_provisional_limits=bool(wp.max() <= 5 and wr.max() <= 1)))
        windows.extend(local_windows)
        qactual = np.array([[x['pos'] for x in s['human_dof_states']] for s in states])
        bound_excess = np.maximum(np.array(initial['PD_properties']['lower']) - qactual, qactual - np.array(initial['PD_properties']['upper']))
        contacts, self_steps = {}, set()
        for record in d['contacts']:
            for c in record['contacts']:
                pair = [c['body0_name'], c['body1_name']]
                if all(n.startswith('human/') for n in pair):
                    self_steps.add(record['physics_step'])
                if c['lambda'] > 0 and any(n.startswith('human/') for n in pair) and any(n.startswith('guitar/') for n in pair):
                    contacts.setdefault(next(n for n in pair if n.startswith('human/')), set()).add(record['physics_step'])
        held = initial['preserved_absolute_targets_rad'][axis]
        for step in range(1201):
            joint_series.append(dict(label=label, physics_step=step, time_s=step / 240, middle3_actual_deg=float(np.degrees(qactual[step, axis])), middle3_held_goal_deg=float(np.degrees(held)), middle2_actual_deg=float(np.degrees(qactual[step, names.index('LH:middle2')]))))
        summary.append(dict(label=label, guitar=metrics(trace), strap=strap_metrics(trace, initial), max_1s_position_change_mm=max(w['max_position_change_mm'] for w in local_windows), max_1s_rotation_change_deg=max(w['max_rotation_change_deg'] for w in local_windows), windows_within_provisional_limits=sum(w['within_provisional_limits'] for w in local_windows), outside_initial_envelope_samples=sum(t['position_error_m'] > .03 or t['rotation_error_deg'] > 5 for t in trace), middle3_goal_deg=float(np.degrees(held)), middle3_actual_samples_deg={str(step / 240):float(np.degrees(qactual[step, axis])) for step in [0, 120, 480, 1200]}, max_middle3_goal_error_after2s_deg=float(np.degrees(abs(qactual[480:, axis] - held).max())), human_guitar_positive_raw_lambda_steps={n:len(v) for n,v in sorted(contacts.items())}, human_self_contact_steps=len(self_steps), palm_up_proxy_passed=report['palm_up_proxy_passed'], constraint_violations=report['constraint_violations'], max_actual_native_bound_excess_rad=float(max(0, bound_excess.max()))))
    after = {str(p):sha(p) for p in paths}
    checks['inputs_preserved'] = before == after
    assert all(checks.values()), checks
    result = dict(checks=checks, input_sha256_before=before, input_sha256_after=after, summary=summary, actual_target_delta_rad=delta, new_native_initializations=1, new_physics_steps=1200, actor_inference_calls=0, training_updates=0, naturalness_or_playing_success_certified=False, scope='one actual middle3 PD-goal-only probe; initial81/G/LA and other80 commands unchanged; 121 complete1s windows per run; scalar joint coordinates and rawlambda, not pad/force/cooked certification')
    for name, records in [('windows.jsonl', windows), ('joint_series.jsonl', joint_series)]:
        (P / name).write_text(''.join(json.dumps(r, allow_nan=False) + '\n' for r in records))
    (P / 'analysis.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(dict(checks=checks, summary=summary), indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
