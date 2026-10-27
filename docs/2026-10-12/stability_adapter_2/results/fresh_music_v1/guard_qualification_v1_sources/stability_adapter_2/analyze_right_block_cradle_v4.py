"""Audit finite human commands and two-block native contacts, then compare elbow trial."""
import json
import subprocess
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from .initial_pose_noise_v1 import read, save, sha, pose
from .om_axilla_source_geometry_v3 import CapsuleBodyDistance
from .upper_arm_static_geometry_v1 import ROOT, ASSET

P = ROOT/'docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1'


def main():
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--cases', type=Path, nargs='+', required=True); args = parser.parse_args()
    geometry = read(ROOT/'stability_adapter_2/assets/om_body_geometry_v3/manifest.json')
    shapes = CapsuleBodyDistance(geometry['asset'], ASSET)
    vertices = np.vstack([p[0] for p in shapes.pieces]); centre = (vertices.min(0)+vertices.max(0))/2
    inputs = {str(Path(__file__).resolve()):sha(__file__), str(ASSET):sha(ASSET)}
    inputs.update({str(p):sha(p) for folder in args.cases for p in folder.rglob('*') if p.is_file()})
    inputs.update({str(p):sha(p) for p in (ROOT/'stability_adapter_2').glob('*.py')})
    inputs.update({str(p):sha(p) for p in [Path(geometry['asset'])]+[Path(m['path']) for m in geometry['meshes']]})
    cases = {}; data = {}
    for folder in args.cases:
        folder = folder.resolve(); report = read(folder/'report.json'); attempt = read(folder/'attempt.json')
        for path,h in attempt['input_sha256'].items():
            assert sha(path) == h; inputs[path] = h
        initial = read(folder/'initial_values.json'); verification = read(folder/'initial_verification.json')
        assert report['completed'] and report['physics_steps'] == 1200 and report['control_steps'] == 300
        assert not report['forbidden_calls'] and not report['strap_enabled'] and not report['checkpoints_connected']
        assert all(verification['invariants'].values()) and verification['FK_ok'] and verification['source_audit']['source_clear']
        trace = read(folder/'trace.json'); endpoints = read(folder/'media/physics_endpoint_contacts.json')['rows']
        right = read(folder/'media/effort_control_rows.json'); tracking = read(folder/'media/left_wrist_tracking_rows.json')['rows']
        body_mode = (folder/'media/body_effort_rows.json').exists()
        body_rows = read(folder/'media/body_effort_rows.json')['rows'] if body_mode else None
        body_config = read(folder/'media/body_effort_configuration.json') if body_mode else None
        dynamic = (folder/'media/two_block_rows.json').exists()
        thorax = read(folder/'media'/('two_block_rows.json' if dynamic else 'thorax_point_rows.json'))['rows']
        config = read(folder/'media'/('two_block_configuration.json' if dynamic else 'thorax_point_configuration.json'))
        if dynamic: config['indices'] = [i for i,n in enumerate(initial['joint_names']) if n.startswith(('R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))]
        config['cap_N'] = config['cap_each_N'] if dynamic else config['cap_N']
        actuator = read(folder/'media/effort_configuration.json'); caps = np.array(actuator['joint_effort_caps_Nm'])
        positions = read(folder/'media/position_command_rows.json')['rows']; indices = config['indices']; q0 = np.array(initial['q_ref_rad'])
        motion = read(folder/'media/elbow_motion_configuration.json'); selected = np.array(actuator['right_indices'])
        assert len(trace) == 301 and len(endpoints) == len(thorax) == len(tracking) == len(right['rows']) == 1200
        assert right['right_effort_calls'] == 1200 and right['right_effort_window_closed']
        assert all((row['position48_exact'] if body_mode else row['position57_exact']) and row['state_preserved'] for row in positions) and len(positions) == 300
        own = [i for i,n in enumerate(initial['joint_names']) if n.startswith(('R_Thorax','R_Shoulder','R_Elbow','R_Wrist','L_Thorax','L_Shoulder','L_Elbow','L_Wrist'))]
        if body_mode: own += body_config['indices']
        outside = np.array([i for i in range(81) if i not in own]); force_norms = []
        for k,(row,tr,rr) in enumerate(zip(thorax,tracking,right['rows'])):
            assert row['physics_step'] == tr['physics_step'] == rr['physics_step'] == k
            assert endpoints[k]['physics_step'] == k+1
            if dynamic:
                from .strap import point_kinematics
                task81 = np.zeros(81)
                gs = initial['native_initial_state']['guitar_body_states'][0] if k == 0 else endpoints[k-1]['guitar_body_states']['guitar']
                gp,gr = pose(gs); vec = lambda body,field: np.array([body['vel'][field][c] for c in 'xyz'])
                for point,reference in zip(row['points'],config['references']):
                    assert point['body'] == reference['body']
                    goal,gv = point_kinematics(gp,gr.as_quat(),vec(gs,'linear'),vec(gs,'angular'),np.array(reference['goal_G_m']),np.array(actuator['guitar_root_COM_local_m']))
                    assert np.allclose(goal,point['goal_W_m'],atol=1e-12,rtol=0) and np.allclose(gv,point['goal_velocity_W_m_s'],atol=1e-12,rtol=0)
                    hs = initial['native_initial_state']['human_body_states'][reference['index']] if k == 0 else endpoints[k-1]['human_body_states'][reference['body']]
                    hp,hr = pose(hs); measured,velocity = point_kinematics(hp,hr.as_quat(),vec(hs,'linear'),vec(hs,'angular'),np.array(reference['local_m']),np.array(reference['COM_local_m']))
                    assert np.allclose(measured,point['point_W_m'],atol=1e-12,rtol=0) and np.allclose(velocity,point['velocity_W_m_s'],atol=1e-12,rtol=0)
                    force = config['K_N_m']*(goal-measured)+config['D_Ns_m']*(gv-velocity)
                    force *= min(1.,config['cap_N']/max(float(np.linalg.norm(force)),1e-12))
                    assert np.allclose(force,point['virtual_force_request_W_N'],atol=1e-10,rtol=0)
                    jac = np.array(point['jacobian_all']); child = [i for i,n in enumerate(initial['joint_names']) if n.startswith(('R_Elbow','R_Wrist'))]
                    error = float(np.linalg.norm(jac@np.array(rr['qdot_all_rad_s'])-velocity))
                    assert abs(jac[:,child]).max() < 1e-10 and error <= .01 and abs(error-point['jacobian_velocity_error_m_s']) < 1e-12
                    contribution = np.zeros(81); contribution[reference['indices']] = (jac.T@force)[reference['indices']]
                    assert np.allclose(contribution,point['task81_Nm'],atol=1e-10,rtol=0); task81 += contribution
                    force_norms.append(float(np.linalg.norm(force)))
                requested = np.array(rr['requested_efforts_Nm'])[selected]-np.array(rr['axilla_point_task_right_Nm'])+task81[selected]
                assert np.allclose(requested,row['requested_right_Nm'],atol=1e-10,rtol=0)
                final = np.array(row['before_efforts_Nm']).astype(np.float32); final[selected] = np.clip(requested,-caps[selected],caps[selected]).astype(np.float32)
            else:
                force = config['K_N_m']*(np.array(config['desired_point_W_m'])-row['point_W_m'])-config['D_Ns_m']*np.array(row['velocity_W_m_s'])
                force *= min(1.,config['cap_N']/max(float(np.linalg.norm(force)),1e-12))
                assert np.allclose(force,row['virtual_force_request_W_N'],atol=1e-10,rtol=0)
                task = np.array(row['jacobian_all']).T@force
                requested = np.array(rr['requested_efforts_Nm'])[indices]+task[indices]
                assert np.allclose(requested,row['requested_Thorax3_Nm'],atol=1e-10,rtol=0)
                final = np.array(row['before_efforts_Nm']).astype(np.float32)
                final[indices] = np.clip(requested,-caps[indices],caps[indices]).astype(np.float32)
                assert row['child_jacobian_max_abs'] < 1e-10 and row['jacobian_velocity_error_m_s'] <= .01
                force_norms.append(float(np.linalg.norm(force)))
            assert np.array_equal(final,row['final_efforts_Nm'])
            assert np.array_equal(row['before_efforts_Nm'],tr['before_two_block_efforts_Nm'] if dynamic else tr['before_thorax_efforts_Nm'])
            if body_mode:
                br = body_rows[k]; bi = np.array(body_config['indices']); assert br['physics_step'] == k
                assert np.array_equal(final,br['before_efforts_Nm']) and np.array_equal(final,tr['before_body9_efforts_Nm'])
                gravity = (np.array(body_config['mass_kg'])[1:,None]*9.81*np.array(br['gravity_COM_z_J_body9'])).sum(axis=0)
                task = sum((np.array(point['jacobian_all'])[:,bi].T@np.array(point['virtual_force_request_W_N']) for point in row['points']),np.zeros(9))
                posture = body_config['K_Nm_rad']*(np.array(br['target_body_rad'])-br['q_body_rad'])-body_config['D_Nms_rad']*np.array(br['qdot_body_rad_s'])
                assert np.allclose(gravity,br['gravity_body_Nm'],atol=1e-10,rtol=0) and np.allclose(task,br['task_body_Nm'],atol=1e-10,rtol=0)
                assert np.allclose(posture,br['posture_body_Nm'],atol=1e-10,rtol=0) and np.array_equal(br['target_body_rad'],q0[bi])
                assert np.array_equal(br['qdot_body_rad_s'],np.array(rr['qdot_all_rad_s'])[bi])
                request = gravity+task+posture; assert np.allclose(request,br['requested_body_Nm'],atol=1e-10,rtol=0)
                final[bi] = np.clip(request,-caps[bi],caps[bi]).astype(np.float32)
                assert np.array_equal(final,br['final_efforts_Nm'])
            assert np.array_equal(final,tr['actual_combined_submitted_efforts_Nm'])
            assert np.all(abs(final) <= caps+1e-6) and np.all(final[outside] == 0)
            target = q0.copy(); velocity = np.zeros(81); t = k/240
            if 2.5 <= t < 4.5:
                target[motion['index']] += motion['amplitude_rad']*np.sin(np.pi*(t-2.5))
                velocity[motion['index']] = motion['amplitude_rad']*np.pi*np.cos(np.pi*(t-2.5))
            assert np.array_equal(target,rr['posture_target_rad']) and np.array_equal(velocity,rr['posture_target_velocity_rad_s'])
        assert all(np.array_equal(r['logical_final_target_rad'],q0) for r in positions)
        # Raw local contact coordinates are queried at physics endpoints; no conversion of lambda to Newtons.
        a,b = shapes.capsules['R_Shoulder'][0]; axis = b-a; regions = []; statistics = {}
        for field in ('right_thorax_body_contacts','right_upper_arm_body_contacts','right_forearm_body_contacts',
                      'right_distal_guitar_contacts','left_arm_hand_guitar_contacts','head_guitar_contacts','right_hip_body_contacts'):
            statistics[field] = {'presence_steps':sum(bool(e[field]) for e in endpoints),
                                 'positive_raw_lambda_steps':sum(any(c['lambda'] > 0 for c in e[field]) for e in endpoints)}
        for ep in endpoints:
            fractions = []
            for c in ep['right_upper_arm_body_contacts']:
                i = 0 if c['body0_name'] == 'human/R_Shoulder' else 1
                point = np.array([c['localPos'+str(i)][k] for k in 'xyz'])
                fractions.append((float((point-a)@axis/(axis@axis)),c['lambda']))
            thorax_positive = any(c['lambda'] > 0 for c in ep['right_thorax_body_contacts'])
            regions.append({'physics_step':ep['physics_step'], 'proximal30_presence':any(0 <= f <= .3 for f,_ in fractions),
                'proximal35_presence':any(0 <= f <= .35 for f,_ in fractions),
                'proximal30_positive':any(0 <= f <= .3 and lam > 0 for f,lam in fractions),
                'Thorax_presence':bool(ep['right_thorax_body_contacts']), 'Thorax_positive':thorax_positive,
                'proximal30_endpoint_clamped_presence':any(np.clip(f,0,1) <= .3 for f,_ in fractions),
                'proximal30_endpoint_clamped_positive':any(np.clip(f,0,1) <= .3 and lam > 0 for f,lam in fractions),
                'upper_segment_fractions': [f for f,_ in fractions]})
        statistics['both_Thorax_proximal30_presence_steps'] = sum(r['Thorax_presence'] and r['proximal30_presence'] for r in regions)
        statistics['both_Thorax_proximal30_positive_steps'] = sum(r['Thorax_positive'] and r['proximal30_positive'] for r in regions)
        statistics['both_Thorax_proximal30_endpoint_clamped_presence_steps'] = sum(r['Thorax_presence'] and r['proximal30_endpoint_clamped_presence'] for r in regions)
        statistics['both_Thorax_proximal30_endpoint_clamped_positive_steps'] = sum(r['Thorax_positive'] and r['proximal30_endpoint_clamped_positive'] for r in regions)
        gp = np.array([t['position_W_m'] for t in trace]); rot = Rotation.from_quat([t['quaternion_xyzw'] for t in trace])
        body = gp+rot.apply(np.tile(centre,(len(trace),1))); motion_deg = np.rad2deg((rot[0].inv()*rot).magnitude())
        q = np.array([t['q_rad'] for t in trace])
        body_peak = None
        if body_mode:
            final_state = read(folder/'final_state.json'); bi = np.array(body_config['indices'])
            sampled = np.array([row['q_body_rad'] for row in body_rows]+[[final_state['human_dof_states'][i]['pos'] for i in bi]])
            body_peak = float(np.rad2deg(abs(sampled-q0[bi]).max()))
        chest0 = pose(initial['native_initial_state']['human_body_states'][initial['human_body_names'].index('Chest')])[1]
        chest_peak = float(max(np.rad2deg((chest0.inv()*pose(ep['human_body_states']['Chest'])[1]).magnitude()) for ep in endpoints))
        capture = read(folder/'media/capture.json')
        assert len(capture['frames']) == 151 and all(f['render_preserves_states'] for f in capture['frames'])
        videos = {}
        for view in ('whole_body','hands'):
            f = folder/'media'/(view+'.mp4')
            stream = json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0',
                '-show_entries','stream=nb_read_frames,r_frame_rate,duration','-of','json',str(f)]))['streams'][0]
            assert stream['nb_read_frames'] == '151' and stream['r_frame_rate'] == '30/1'
            videos[view] = {'path':str(f),'sha256':sha(f),'stream':stream}
        cases[folder.name] = {'physics_steps':1200,'control_steps':300,'Thorax_cap_N':config['cap_N'],'current_G_point_tracking':dynamic,'body9_effort':body_mode,
            'final_body_centre_change_mm':float(np.linalg.norm(body[-1]-body[0])*1000),
            'max_body_centre_change_mm':float(np.linalg.norm(body-body[0],axis=1).max()*1000),
            'final_rotation_change_deg':float(motion_deg[-1]),'max_rotation_change_deg':float(motion_deg.max()),
            'body_centre_2_to_5s_mm':float(np.linalg.norm(body[-1]-body[120])*1000),
            'rotation_2_to_5s_deg':float(np.rad2deg((rot[120].inv()*rot[-1]).magnitude())),
            'max_body9_scalar_deviation_240Hz_deg':body_peak,'body9_actual_small_motion_gate_passed':body_peak <= np.rad2deg(.08) if body_mode else None,
            'max_Chest_world_rotation_delta_240Hz_deg':chest_peak,
            'max_body9_scalar_deviation_60Hz_deg':float(np.rad2deg(abs(q[:,:9]-q0[:9]).max())),
            'elbow_target_amplitude_deg':float(np.rad2deg(motion['amplitude_rad'])),
            'elbow_actual_2p5_to_5s_range_deg':float(np.rad2deg(np.ptp(q[150:,motion['index']]))),
            'max_proximal_point_virtual_force_request_N':max(force_norms),'contacts':statistics,'videos':videos,
            'both_contacts_last_half_second_steps':sum(r['Thorax_presence'] and r['proximal30_presence'] for r in regions[1080:]),
            'both_contacts_elbow_wave_steps':sum(r['Thorax_presence'] and r['proximal30_presence'] for r in regions[600:1080])}
        data[folder.name] = (initial,body,rot,trace,regions)
    comparisons = {}
    for label,(initial,body,rot,trace,regions) in data.items():
        if cases[label]['elbow_target_amplitude_deg'] == 0: continue
        match = next((n for n in data if cases[n]['elbow_target_amplitude_deg'] == 0 and cases[n]['Thorax_cap_N'] == cases[label]['Thorax_cap_N'] and cases[n]['current_G_point_tracking'] == cases[label]['current_G_point_tracking'] and cases[n]['body9_effort'] == cases[label]['body9_effort']), None)
        assert match is not None
        other,b0,r0,trace0,_ = data[match]; assert initial == other and trace[:151] == trace0[:151]
        comparisons[label] = {'static_case':match,'initial_full_state_and_first2p5s_trace_exact':True,
            'max_same_time_body_centre_difference_mm':float(np.linalg.norm(body-b0,axis=1).max()*1000),
            'max_same_time_rotation_difference_deg':float(np.rad2deg((r0.inv()*rot).magnitude()).max())}
    assert all(sha(p) == h for p,h in inputs.items())
    save(args.out, {'passed':True,'input_sha256':inputs,'cases':cases,'comparisons':comparisons,
         'body_centre_G_m':centre.tolist(),'scope':'native five-second support and one scalar elbow cycle; command audit, not contact-force, all-motion, music or repeatability certification'})
    print(json.dumps({'cases':cases,'comparisons':comparisons},ensure_ascii=False,indent=2))


if __name__ == '__main__': main()
