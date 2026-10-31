"""Saved native comparisons: initial placement, bounded actuator math and videos."""
from pathlib import Path
import hashlib
import json
import subprocess
import isaacgym  # Native module must precede torch imported for actor replay.
import numpy as np
from scipy.spatial.transform import Rotation
from .initial_pose_noise_v1 import read, pose
from .om_axilla_source_geometry_v3 import CapsuleBodyDistance
from .left_neck_near_geometry_v1 import FACETS, left_indices, native_faces
from .environment_contract_v1 import EnvironmentContract

R = Path(__file__).resolve().parents[1]
A = R/'stability_adapter_2'
P = R/'docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1'


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    folders = sorted(p.parent for p in P.glob('native_*/report.json'))
    paths = [Path(__file__).resolve(), FACETS, A/'assets/om_body_geometry_v3/manifest.json',
             A/'assets/humanoid_fixed_lower.xml', A/'om_axilla_source_geometry_v3.py',
             A/'left_neck_near_geometry_v1.py', A/'environment_contract_v1.py']
    geometry = read(paths[2]); paths += [Path(geometry['asset'])]+[Path(m['path']) for m in geometry['meshes']]
    paths += list(A.glob('*.py'))
    paths += [R/'tab2body/learning/fret_v2_model.py', R/'tab2body/learning/strike_v2_model.py']
    for folder in folders:
        paths += [f for f in folder.rglob('*') if f.is_file()]
        paths += [Path(p) for p in EnvironmentContract(Path(read(folder/'report.json')['actual_initial_candidate'])).inputs]
    for folder in folders:
        if (folder/'source_contract.json').exists():
            meta = read(folder/'source_contract.json')
            paths += [Path(meta[k+'_checkpoint']) for k in ('Fret', 'Strike')]
    paths += [A/'left_near_arm_effort_v1.py', A/'left_near_arm_effort_v2.py', A/'left_near_arm_effort_v3.py']
    inputs = {str(f): sha(f) for f in paths}
    pieces = CapsuleBodyDistance(geometry['asset'], A/'assets/humanoid_fixed_lower.xml').pieces
    vertices = np.vstack([piece[0] for piece in pieces]); centre = (vertices.min(0)+vertices.max(0))/2
    reference_state = read(P/'native_hold_v1/initial_values.json')['native_initial_state']
    cases = {}
    for folder in folders:
        report = read(folder/'report.json'); initial = read(folder/'initial_values.json')
        gate = read(folder/'initial_verification.json'); trace = read(folder/'trace.json')
        rows = read(folder/'controls.json'); contract = EnvironmentContract(Path(report['actual_initial_candidate']))
        assert initial['native_initial_state'] == reference_state
        assert gate['source_audit_at_native_initial']['source_clear'] and gate['native_FK_ok'] and gate['faces_ok']
        assert gate['other48_angles_exact'] and gate['guitar_initial_full_state_exact'] and gate['mass_properties_exact']
        assert gate.get('PD_only_declared_left_mode_change', gate['PD_properties_exact'])
        assert report['inputs_unchanged'] and not report['forbidden_calls']
        assert report['right_effort_calls'] == report['physics_steps']
        qprev = contract.q_ref.copy()
        for row in rows:
            request, final = contract.targets(np.array(row['action81']), qprev)
            assert np.array_equal(final, np.array(row['final_rad']))
            assert np.allclose(request, row['requested_rad'], atol=1e-14, rtol=0)
            qprev = final.astype(float)
        final_state = read(folder/'final_state.json')
        if trace[-1]['physics_step'] != report['physics_steps']:
            gp, gr = pose(final_state['guitar_body_states'][0])
            from types import SimpleNamespace
            trace = trace+[{'physics_step': report['physics_steps'], 'position_W_m': gp.tolist(),
                            'quaternion_xyzw': gr.as_quat().tolist(),
                            'q_rad': [r['pos'] for r in final_state['human_dof_states']],
                            'left_faces': native_faces(SimpleNamespace(human_bodies=initial['human_body_names']), final_state, contract.candidate)}]
        rotations = [Rotation.from_quat(t['quaternion_xyzw']) for t in trace]
        body = np.array([np.array(t['position_W_m'])+q.apply(centre) for t, q in zip(trace, rotations)])
        displacement = np.linalg.norm(body-body[0], axis=1)*1000
        angle = np.array([np.rad2deg((rotations[0].inv()*q).magnitude()) for q in rotations])
        endpoints = read(folder/'media/physics_endpoint_contacts.json')['rows']
        assert len(endpoints) == report['physics_steps']
        right_rows = read(folder/'media/effort_control_rows.json')['rows']
        assert len(right_rows) == report['physics_steps']
        left_path = folder/'media/left_arm_effort_rows.json'
        tracking_path = folder/'media/left_wrist_tracking_rows.json'
        checks = {'left_effort_formula_max_error_Nm': None, 'combined_vector_clip_exact': None}
        if left_path.exists():
            left_rows = read(left_path)['rows']; config = read(folder/'media/left_arm_effort_configuration.json')
            left = np.array(config['left_indices']); cap = np.array(config['joint_effort_caps_Nm'])
            kp, kd = np.array(config['K_posture_Nm_rad']), np.array(config['D_posture_Nms_rad'])
            tracking = read(tracking_path)['rows'] if tracking_path.exists() else None
            if tracking is not None:
                tracking_config = read(folder/'media/left_wrist_tracking_configuration.json')
                old_right_config = read(folder/'media/effort_configuration.json')
            max_error = 0.; assert len(left_rows) == report['physics_steps']
            for j, row in enumerate(left_rows):
                assert row['physics_step'] == j
                final_target = np.array(rows[j//4]['final_rad'])[left]
                assert np.array_equal(row['target_left_rad'], final_target)
                pd = kp*(final_target-np.array(row['q_left_rad']))-kd*np.array(row['qdot_left_rad_s'])
                max_error = max(max_error, float(np.max(abs(pd-np.array(row['posture_left_Nm'])))))
                request = np.array(row['gravity_left_Nm'])+pd
                assert np.allclose(request, row['requested_left_Nm'], atol=1e-10, rtol=0)
                combined = np.array(right_rows[j]['submitted_efforts_Nm'])
                if tracking is not None:
                    tr = tracking[j]; force = np.array(tr['virtual_force_request_W_N'])
                    assert np.linalg.norm(force) <= 30+1e-10 and tr['jacobian_velocity_error_m_s'] <= .01
                    enabled = tracking_config['hold_for_entire_static_trial'] or j < 480
                    assert tr['enabled'] == enabled
                    desired = np.array(tr['desired_wrist_W_m']); point = np.array(tr['wrist_point_W_m'])
                    expected_force = 1000*(desired-point)+30*(np.array(tr['desired_velocity_W_m_s'])-tr['wrist_velocity_W_m_s']) if enabled else np.zeros(3)
                    expected_force *= min(1., 30/max(float(np.linalg.norm(expected_force)), 1e-12))
                    assert np.allclose(expected_force, force, atol=1e-10, rtol=0)
                    right_row = right_rows[j]; gp = np.array(right_row['current_guitar_p_W_m'])
                    gr = Rotation.from_quat(right_row['current_guitar_q_xyzw']); goal = np.array(tracking_config['goal_wrist_G_m'])
                    expected_goal = gp+gr.apply(goal)
                    expected_velocity = np.array(right_row['guitar_root_linear_COM_W_m_s'])+np.cross(np.array(right_row['guitar_root_angular_W_rad_s']), gr.apply(goal-np.array(old_right_config['guitar_root_COM_local_m'])))
                    assert np.allclose(expected_goal, desired, atol=1e-10, rtol=0)
                    assert np.allclose(expected_velocity, tr['desired_velocity_W_m_s'], atol=1e-10, rtol=0)
                    task = np.array(tr['point_jacobian_all']).T@force
                    assert np.allclose(task[left], tr['task_left_Nm'], atol=1e-10, rtol=0)
                    request += task[left]
                    if report['dual_checkpoints_connected'] and j >= 480:
                        assert not tr['enabled'] and np.all(force == 0)
                    actual = np.array(tr['actual_combined_submitted_efforts_Nm'])
                else: actual = np.array(row['combined_submitted_efforts_Nm'])
                combined[left] = np.clip(request, -cap, cap).astype(np.float32).astype(float)
                assert np.array_equal(combined, actual)
            assert max_error < 1e-10
            checks.update(left_effort_formula_max_error_Nm=max_error, combined_vector_clip_exact=True)
        case = {'completed': report['completed'], 'failure': report['failure'], 'stop_reason': report['stop_reason'],
                'physics_steps': report['physics_steps'], 'control_ticks': report['control_steps'],
                'physics_seconds': report['physics_seconds'], 'initial_full_native_exact_all_cases': True,
                'initial_faces': gate['face_measurements'], 'final_faces': trace[-1]['left_faces'],
                'guitar_final_body_bbox_change_mm': float(displacement[-1]), 'guitar_max_body_bbox_change_mm': float(displacement.max()),
                'guitar_final_SO3_deg': float(angle[-1]), 'guitar_max_SO3_deg': float(angle.max()),
                'contact_endpoint_presence_counts': {k: sum(bool(e[k]) for e in endpoints) for k in
                    ('left_arm_hand_guitar_contacts', 'right_upper_arm_body_contacts', 'head_guitar_contacts', 'right_distal_guitar_contacts')},
                'contact_scope': 'endpoint presence counts, not measured forces or face support certification',
                'actuator_checks': checks, 'videos': {}, 'paired_inference_ticks': sum(bool(r['actor_used']) for r in rows)}
        if tracking_path.exists():
            tr = read(tracking_path)['rows']; case['tracking_wrist_error_final_mm'] = tr[-1]['point_error_m']*1000
            case['tracking_wrist_error_max_mm'] = max(r['point_error_m'] for r in tr)*1000
        at2 = next((t for t in trace if t['physics_step'] == 480), None)
        if at2: case['faces_at_2s'] = at2['left_faces']
        if case['paired_inference_ticks']:
            meta = read(folder/'source_contract.json'); replay = {}
            import torch
            from tab2body.learning.fret_v2_model import FretV2ActorCritic
            from tab2body.learning.strike_v2_model import StrikeV2ActorCritic
            for label, cls, dimension, values in [('Fret', FretV2ActorCritic, 420, 6), ('Strike', StrikeV2ActorCritic, 303, 1)]:
                cp = torch.load(meta[label+'_checkpoint'], map_location='cpu', weights_only=True)
                model = cls(dimension, 30, value_dim=values, init_std=cp['checkpoint_contract']['payload']['model']['policy_init_std'])
                model.load_state_dict(cp['model'], strict=True); model.eval(); errors = []
                for row in rows:
                    if row['actor_used']:
                        with torch.no_grad(): action = model.act(torch.tensor([row[label+'_observation']], dtype=torch.float32), deterministic=True)[0][0].tolist()
                        errors.append(max(abs(x-y) for x, y in zip(action, row[label+'_action'])))
                assert max(errors) < 1e-7; replay[label] = {'max_action_replay_error': max(errors), 'inferences': len(errors)}
            case['actor_replay'] = replay
            case['terminal_Fret'] = rows[-1]['Fret_info']; case['terminal_Strike'] = rows[-1]['Strike_info']
            case['Fret_done'] = rows[-1]['Fret_done']; case['Strike_done'] = rows[-1]['Strike_done']
            case['joint_resolved_events'] = len(read(folder/'joint_events.json'))
            case['joint_string_crossings'] = len(read(folder/'joint_crossings.json'))
        for label, video in report['videos'].items():
            stream = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0',
                '-show_entries', 'stream=nb_read_frames,avg_frame_rate,duration', '-of', 'json', video['path']]))['streams'][0]
            assert stream['avg_frame_rate'] == '30/1' and sha(video['path']) == video['sha256']
            case['videos'][label] = {'path': video['path'], 'sha256': video['sha256'], 'stream': stream}
        cases[folder.name] = case
    assert all(sha(p) == h for p, h in inputs.items())
    with (P/'native_analysis_v2.json').open('x') as f:
        json.dump({'input_sha256': inputs, 'cases': cases, 'guitar_collision_body_bbox_centre_G_m': centre.tolist(),
            'measurement_scope': 'selected source facet signed gaps/finite target error at actual native poses; not whole hand cooked clearance',
            'training_updates': 0}, f, ensure_ascii=False, indent=2, allow_nan=False)
    print(json.dumps({k: {x: v[x] for x in ('completed', 'physics_seconds', 'guitar_final_body_bbox_change_mm',
                       'guitar_final_SO3_deg', 'paired_inference_ticks')} for k, v in cases.items()}, indent=2))


if __name__ == '__main__': main()
