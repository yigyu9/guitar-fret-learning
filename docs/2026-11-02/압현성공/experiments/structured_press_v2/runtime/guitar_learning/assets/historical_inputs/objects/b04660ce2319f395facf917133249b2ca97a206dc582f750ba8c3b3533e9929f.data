"""Verify recorded command stages, unchanged settling, and rendered string markers."""
import argparse
from pathlib import Path
import numpy as np
from .initial_pose_noise_v1 import read, save, sha, pose
from .elbow_wrist_strike_source_v1 import string_segments


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--cases', type=Path, nargs='+', required=True)
    args = parser.parse_args()
    files = [Path(__file__).resolve()] + [f for n in args.cases for f in n.rglob('*') if f.is_file()]
    inputs = {str(f.resolve()): sha(f) for f in files}
    save(args.out.with_name(args.out.stem + '_before.json'), inputs)
    baseline = args.cases[0]
    b = read(baseline / 'initial_values.json')
    initial_state = b['native_initial_state']
    settling = read(baseline / 'media/physics_endpoint_contacts.json')['rows'][:480]
    trace0 = read(baseline / 'trace.json')[:121]
    results = {}
    for n in args.cases:
        initial = read(n / 'initial_values.json')
        assert initial['native_initial_state'] == initial_state
        assert initial['q_ref_rad'] == b['q_ref_rad'] and initial['PD_properties'] == b['PD_properties']
        names = initial['joint_names']
        distal = [names.index(prefix + '_' + axis) for prefix in ('R_Elbow', 'R_Wrist') for axis in 'xyz']
        mask = np.ones(81, dtype=bool); mask[distal] = False
        qref = np.array(initial['q_ref_rad'])
        caps = np.array(initial['PD_properties']['effort'])
        lower = np.array(initial['PD_properties']['lower']); upper = np.array(initial['PD_properties']['upper'])
        targets = read(n / 'media/six_joint_target_rows.json')['rows']
        previous = qref.copy(); max_rate = 0.; max_norm = 0.
        for row in targets:
            request = np.array(row['requested_target81_rad']); final = np.array(row['final_target81_rad'])
            assert np.array_equal(request[mask], qref[mask]) and np.array_equal(final[mask], qref[mask])
            assert np.isfinite(final).all() and np.isfinite(request).all()
            for value in (request, final):
                assert np.all(value >= lower - 1e-6) and np.all(value <= upper + 1e-6)
                assert np.max(abs(value[distal] - qref[distal])) <= 1 + 1e-6
                norm = np.linalg.norm(value[distal].reshape(2, 3), axis=1).max()
                assert norm < np.deg2rad(160); max_norm = max(max_norm, norm)
            rate = abs(final[distal] - previous[distal]) * 60
            assert rate.max() <= 3.0001
            max_rate = max(max_rate, rate.max()); previous = final
        endpoints = read(n / 'media/physics_endpoint_contacts.json')['rows']
        assert endpoints[:480] == settling and read(n / 'trace.json')[:121] == trace0
        velocity_path = n / 'media/six_velocity_effort_rows.json'
        feedback_path = n / 'media/pick_feedback_effort_rows.json'
        velocity_rows = read(velocity_path)['rows'] if velocity_path.exists() else []
        pick_rows = read(feedback_path)['rows'] if feedback_path.exists() else []
        max_force = 0.; max_jac_error = 0.; max_command = 0.
        if not velocity_rows:
            for row in read(n / 'media/body_effort_rows.json')['rows']:
                final = np.array(row['final_efforts_Nm'])
                assert np.isfinite(final).all() and np.all(abs(final) <= caps + 1e-6)
                max_command = max(max_command, abs(final).max())
        for row in velocity_rows:
            k = row['physics_step']; control_index = k // 4
            current = np.array(targets[control_index]['final_target81_rad'])
            prior = qref if control_index == 0 else np.array(targets[control_index-1]['final_target81_rad'])
            velocity = (current[distal] - prior[distal]) * 60
            assert np.max(abs(velocity - row['target_velocity6_rad_s'])) < 1e-10
            term = np.array(row['D_Nms_rad']) * velocity
            assert np.max(abs(term - row['velocity_term6_Nm'])) < 1e-10
            request = np.array(row['original_raw_request6_Nm']) + term
            before = np.array(row['before_velocity_efforts81_Nm']); final = np.array(row['actual_submitted_efforts81_Nm'])
            expected = np.clip(request, -caps[distal], caps[distal]).astype(np.float32).astype(float)
            assert np.array_equal(expected, final[distal]) and np.array_equal(before[mask], final[mask])
            assert np.all(abs(final) <= caps + 1e-6)
            if k < 480: assert np.array_equal(before, final)
            max_command = max(max_command, abs(final).max())
        for row in pick_rows:
            k = row['physics_step']; before = np.array(row['before_pick_efforts81_Nm'])
            assert row['before_pick_efforts81_Nm'] == velocity_rows[k]['actual_submitted_efforts81_Nm']
            final = np.array(row['actual_submitted_efforts81_Nm']); force = np.array(row['bounded_virtual_force_W_N'])
            raw = row['ramp'] * (4000 * (np.array(row['goal_W_m']) - row['point_W_m']) + 40 * (np.array(row['goal_velocity_W_m_s']) - row['point_velocity_W_m_s']))
            assert np.max(abs(raw - row['raw_virtual_force_W_N'])) < 1e-10
            expected_force = raw * min(1., 20 / max(np.linalg.norm(raw), 1e-12))
            assert np.max(abs(force - expected_force)) < 1e-10
            task = np.array(row['point_jacobian_all'])[:, distal].T @ force
            assert np.max(abs(task - row['task6_Nm'])) < 1e-10
            expected = np.clip(before[distal] + task, -caps[distal], caps[distal]).astype(np.float32).astype(float)
            assert np.array_equal(expected, final[distal]) and np.array_equal(before[mask], final[mask])
            assert np.all(abs(final) <= caps + 1e-6)
            selected_error = row['jacobian_velocity_errors_m_s'][row['selected_jacobian_frame']]
            assert selected_error <= .01 and np.isfinite(final).all()
            if k < 480: assert row['ramp'] == 0 and np.array_equal(before, final)
            max_force = max(max_force, np.linalg.norm(force)); max_jac_error = max(max_jac_error, selected_error)
            max_command = max(max_command, abs(final).max())
        capture = read(n / 'media/capture.json'); starts, ends = string_segments(initial)
        marker_error = 0.
        for frame in capture['frames']:
            assert frame['render_preserves_states'] and not capture['actual_strap_enabled']
            k = frame['physics_step']; state = initial_state['guitar_body_states'][0] if k == 0 else endpoints[k-1]['guitar_body_states']['guitar']
            gp, gr = pose(state)
            predicted = np.stack((gp + gr.apply(starts), gp + gr.apply(ends)), axis=1)
            error = np.linalg.norm(predicted - np.array(frame['string_endpoints_W_m']), axis=2).max()
            marker_error = max(marker_error, error)
            assert error < 3e-6
        assert len(targets) == 300 and len(endpoints) == 1200
        results[n.name] = {'initial_and_first_2s_exact': True, 'targets75_exact': True,
            'target_rate_max_rad_s': float(max_rate), 'requested_final_ball_norm_max_deg': float(np.rad2deg(max_norm)),
            'velocity_rows': len(velocity_rows), 'pick_rows': len(pick_rows), 'force_max_N': float(max_force),
            'selected_jacobian_velocity_error_max_m_s': float(max_jac_error), 'submitted_command_max_Nm': float(max_command),
            'render_frames': len(capture['frames']), 'rigid_marker_max_error_m_all_captures': float(marker_error)}
        print(n.name, results[n.name], flush=True)
    assert all(sha(f) == h for f, h in inputs.items())
    save(args.out, {'passed': True, 'input_sha256': inputs, 'cases': results,
        'scope': 'command math and read-only frame data; commands/virtual force are not measured contact forces; zero correction for first2s and exact measured settling across cases'})


if __name__ == '__main__': main()
