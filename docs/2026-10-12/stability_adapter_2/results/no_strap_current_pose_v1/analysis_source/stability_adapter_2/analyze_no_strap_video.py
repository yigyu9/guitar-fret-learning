"""Compare saved strap-on/off trials; never invoke the simulator."""
from pathlib import Path
import hashlib
import json
import numpy as np
from .analyze_natural_envelope import angles_deg
from .build_fixed_lower_asset import LOWER_BODIES

R = Path(__file__).resolve().parents[1]
B = R / 'docs/2026-10-12/stability_adapter_2/results'
P = B / 'no_strap_current_pose_v1'
OLD = B / 'initial_middle3_alignment_v1/native'


def read(p): return json.loads(Path(p).read_text())
def rows(p): return [json.loads(s) for s in Path(p).read_text().splitlines()]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    assert not (P / 'analysis.json').exists()
    folders = dict(strap_on=OLD, strap_off=P / 'native')
    data = {label: dict(initial=read(f / 'initial_values.json'), states=rows(f / 'states.jsonl'),
                       trace=rows(f / 'trace.jsonl'), controls=rows(f / 'controls.jsonl'),
                       report=read(f / 'report.json'), capture=read(f / 'capture.json'),
                       audit=read(f / 'initial_grip_audit.json')) for label, f in folders.items()}
    base, new = data['strap_on'], data['strap_off']
    common = ['motion_command', 'input_trial', 'effective_initial_settings', 'human_joint_names',
              'human_body_names', 'main_control_joint_names', 'actual_initial_angles_rad',
              'initial_PD_target_rad', 'native_initial_state', 'guitar_goal_position_W_m',
              'guitar_goal_quaternion_xyzw', 'PD_properties', 'physics_parameters',
              'absolute_strap_rest_length_m', 'initial_route_length_m', 'body9_gain_change',
              'strap_law_parameters', 'warmstart_alpha', 'preserved_absolute_targets_rad', 'left33_names']
    checks = dict(all21_initial_fields_exact=all(new['initial'][k] == base['initial'][k] for k in common))
    command_keys = ['final_target_rad', 'physics_step', 'updated_before_step', 'command_time_s', 'wrist_motion_delta_rad']
    checks['all81_1200_commands_exact'] = len(new['controls']) == len(base['controls']) == 1200 and all(
        all(a[k] == b[k] for k in command_keys) for a, b in zip(new['controls'], base['controls']))
    summaries = {}
    for label, d in data.items():
        states, trace, report, initial = d['states'], d['trace'], d['report'], d['initial']
        checks[label + '_completed_1200_steps'] = report['completed'] and report['failure'] is None and report['physics_steps'] == 1200 and report['simulation_elapsed_s'] == 5 and all(report['checks'].values())
        checks[label + '_ordered_1201_samples'] = len(states) == len(trace) == 1201 and [s['physics_step'] for s in states] == list(range(1201)) and all(t['time_s'] == i / 240 for i, t in enumerate(trace))
        fixed = [initial['human_body_names'].index(n) for n in ('Pelvis',) + LOWER_BODIES]
        checks[label + '_root_lower_fixed'] = all(all(s['human_body_states'][i] == states[0]['human_body_states'][i] for i in fixed) for s in states)
        audit = d['audit']
        checks[label + '_fresh14_source1188'] = len(audit['checks']) == 14 and all(audit['checks'].values()) and audit['complete_source_self_screen']['pair_count'] == 1188 and not audit['complete_source_self_screen']['intersections']
        pos = np.array([t['guitar_position_m'] for t in trace])
        quat = np.array([t['guitar_quaternion_xyzw'] for t in trace])
        raw_pos = np.array([[s['guitar_body_states'][0]['pose']['p'][k] for k in 'xyz'] for s in states])
        raw_quat = np.array([[s['guitar_body_states'][0]['pose']['r'][k] for k in 'xyzw'] for s in states])
        raw_quat /= np.linalg.norm(raw_quat, axis=1, keepdims=True)
        checks[label + '_finite_raw_pose_matches_trace'] = bool(np.isfinite(pos).all() and np.isfinite(quat).all() and np.array_equal(pos, raw_pos) and np.max(np.minimum(np.linalg.norm(quat - raw_quat, axis=1), np.linalg.norm(quat + raw_quat, axis=1))) < 1e-12)
        dp = np.linalg.norm(pos - initial['guitar_goal_position_W_m'], axis=1) * 1000
        dr = angles_deg(quat, np.array(initial['guitar_goal_quaternion_xyzw']))
        checks[label + '_pose_errors_match_trace'] = bool(np.max(abs(dp - np.array([t['position_error_m'] for t in trace]) * 1000)) < 1e-9 and np.max(abs(dr - np.array([t['rotation_error_deg'] for t in trace]))) < 1e-4)
        windows = [(float(np.linalg.norm(pos[i:i+241] - pos[i], axis=1).max() * 1000),
                    float(angles_deg(quat[i:i+241], quat[i]).max())) for i in range(480, 961, 4)]
        summaries[label] = dict(max_initial_position_error_mm=float(dp.max()), max_initial_rotation_error_deg=float(dr.max()),
            end_position_error_mm=float(dp[-1]), end_rotation_error_deg=float(dr[-1]),
            max_late_1s_position_change_mm=max(w[0] for w in windows), max_late_1s_rotation_change_deg=max(w[1] for w in windows),
            provisional_initial_envelope_outside_samples=int(((dp > 30) | (dr > 5)).sum()),
            provisional_late_windows_within_limits=sum(w[0] <= 5 and w[1] <= 1 for w in windows),
            late_window_count=len(windows), guitar_end_position_W_m=pos[-1].tolist(),
            guitar_end_quaternion_xyzw=quat[-1].tolist(), palm_up_proxy_passed=report['palm_up_proxy_passed'],
            constraint_violations=report['constraint_violations'])
    mode = read(P / 'native/no_strap_mode.json')
    checks['no_strap_mode_force_api_calls_zero'] = mode['strap_enabled'] is False and mode['strap_rendered'] is False and mode['explicit_body_force_API_attempts'] == 0 and mode['completed_physics_steps'] == 1200
    checks['all1201_applied_tension_zero'] = all(t['last_applied_tension_n'] == 0 for t in new['trace'])
    checks['metadata_no_strap'] = all(read(P / 'native' / n)['strap_enabled'] is False for n in ['attempt.json', 'initial_values.json', 'report.json'])
    frames = new['capture']['frames']
    checks['151_readonly_raw_native_frames'] = len(frames) == 151 and all(f['physics_step'] == i * 8 and f['time_s'] == i / 30 and f['render_preserves_states'] for i, f in enumerate(frames)) and 'strap_visualization' not in new['capture']
    checks['302_native_PNG_sha_exact'] = sum(len(f['image_sha256']) for f in frames) == 302 and all(sha(p) == h for f in frames for p, h in f['image_sha256'].items())
    videos = read(P / 'native/videos.json')
    checks['two151frame30fps_videos'] = set(videos) == {'whole_body', 'hands'} and all(v['ffmpeg_exit_code'] == v['ffprobe_exit_code'] == 0 and v['stream']['nb_read_frames'] == '151' and v['stream']['avg_frame_rate'] == '30/1' and abs(float(v['stream']['duration']) - 151 / 30) < 1e-6 and sha(v['path']) == v['sha256'] for v in videos.values())
    assert all(checks.values()), checks
    result = dict(checks=checks, summary=summaries, compared_initial_fields=common,
        physical_initializations=1, physical_steps=1200, actor_inference_calls=0, training_updates=0,
        scope='Saved same-initial-state/commands physical strap-force OFF comparison; nominal route/rest length inactive; source geometry not cooked contact certification; provisional 30mm/5deg and late1s5mm/1deg not playing-success certification')
    (P / 'analysis.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__': main()
