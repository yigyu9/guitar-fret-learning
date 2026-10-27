"""Audit finite human commands and two-block native contacts, then compare elbow trial."""
import json
import subprocess
import xml.etree.ElementTree as ET
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
        thorax = read(folder/'media/thorax_point_rows.json')['rows']; config = read(folder/'media/thorax_point_configuration.json')
        actuator = read(folder/'media/effort_configuration.json'); caps = np.array(actuator['joint_effort_caps_Nm'])
        positions = read(folder/'media/position_command_rows.json')['rows']; indices = config['indices']; q0 = np.array(initial['q_ref_rad'])
        motion = read(folder/'media/elbow_motion_configuration.json'); selected = np.array(actuator['right_indices'])
        assert len(trace) == 301 and len(endpoints) == len(thorax) == len(tracking) == len(right['rows']) == 1200
        assert right['right_effort_calls'] == 1200 and right['right_effort_window_closed']
        assert all(row['position57_exact'] and row['state_preserved'] for row in positions) and len(positions) == 300
        own = [i for i,n in enumerate(initial['joint_names']) if n.startswith(('R_Thorax','R_Shoulder','R_Elbow','R_Wrist','L_Thorax','L_Shoulder','L_Elbow','L_Wrist'))]
        outside = np.array([i for i in range(81) if i not in own]); force_norms = []
        for k,(row,tr,rr) in enumerate(zip(thorax,tracking,right['rows'])):
            assert row['physics_step'] == tr['physics_step'] == rr['physics_step'] == k
            assert endpoints[k]['physics_step'] == k+1
            force = config['K_N_m']*(np.array(config['desired_point_W_m'])-row['point_W_m'])-config['D_Ns_m']*np.array(row['velocity_W_m_s'])
            force *= min(1.,config['cap_N']/max(float(np.linalg.norm(force)),1e-12))
            assert np.allclose(force,row['virtual_force_request_W_N'],atol=1e-10,rtol=0)
            task = np.array(row['jacobian_all']).T@force
            requested = np.array(rr['requested_efforts_Nm'])[indices]+task[indices]
            assert np.allclose(requested,row['requested_Thorax3_Nm'],atol=1e-10,rtol=0)
            final = np.array(row['before_efforts_Nm']).astype(np.float32)
            final[indices] = np.clip(requested,-caps[indices],caps[indices]).astype(np.float32)
            assert np.array_equal(final,row['final_efforts_Nm']) and np.array_equal(final,tr['actual_combined_submitted_efforts_Nm'])
            assert np.array_equal(row['before_efforts_Nm'],tr['before_thorax_efforts_Nm'])
            assert np.all(abs(final) <= caps+1e-6) and np.all(final[outside] == 0)
            assert row['child_jacobian_max_abs'] < 1e-10 and row['jacobian_velocity_error_m_s'] <= .01
            target = q0.copy(); velocity = np.zeros(81); t = k/240
            if 2.5 <= t < 4.5:
                target[motion['index']] += motion['amplitude_rad']*np.sin(np.pi*(t-2.5))
                velocity[motion['index']] = motion['amplitude_rad']*np.pi*np.cos(np.pi*(t-2.5))
            assert np.array_equal(target,rr['posture_target_rad']) and np.array_equal(velocity,rr['posture_target_velocity_rad_s'])
            force_norms.append(float(np.linalg.norm(force)))
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
                'upper_segment_fractions': [f for f,_ in fractions]})
        statistics['both_Thorax_proximal30_presence_steps'] = sum(r['Thorax_presence'] and r['proximal30_presence'] for r in regions)
        statistics['both_Thorax_proximal30_positive_steps'] = sum(r['Thorax_positive'] and r['proximal30_positive'] for r in regions)
        gp = np.array([t['position_W_m'] for t in trace]); rot = Rotation.from_quat([t['quaternion_xyzw'] for t in trace])
        body = gp+rot.apply(np.tile(centre,(len(trace),1))); motion_deg = np.rad2deg((rot[0].inv()*rot).magnitude())
        q = np.array([t['q_rad'] for t in trace]); capture = read(folder/'media/capture.json')
        assert len(capture['frames']) == 151 and all(f['render_preserves_states'] for f in capture['frames'])
        videos = {}
        for view in ('whole_body','hands'):
            f = folder/'media'/(view+'.mp4')
            stream = json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0',
                '-show_entries','stream=nb_read_frames,r_frame_rate,duration','-of','json',str(f)]))['streams'][0]
            assert stream['nb_read_frames'] == '151' and stream['r_frame_rate'] == '30/1'
            videos[view] = {'path':str(f),'sha256':sha(f),'stream':stream}
        cases[folder.name] = {'physics_steps':1200,'control_steps':300,'Thorax_cap_N':config['cap_N'],
            'final_body_centre_change_mm':float(np.linalg.norm(body[-1]-body[0])*1000),
            'max_body_centre_change_mm':float(np.linalg.norm(body-body[0],axis=1).max()*1000),
            'final_rotation_change_deg':float(motion_deg[-1]),'max_rotation_change_deg':float(motion_deg.max()),
            'body_centre_2_to_5s_mm':float(np.linalg.norm(body[-1]-body[120])*1000),
            'rotation_2_to_5s_deg':float(np.rad2deg((rot[120].inv()*rot[-1]).magnitude())),
            'elbow_target_amplitude_deg':float(np.rad2deg(motion['amplitude_rad'])),
            'elbow_actual_2p5_to_5s_range_deg':float(np.rad2deg(np.ptp(q[150:,motion['index']]))),
            'max_Thorax_virtual_force_request_N':max(force_norms),'contacts':statistics,'videos':videos,
            'both_contacts_last_half_second_steps':sum(r['Thorax_presence'] and r['proximal30_presence'] for r in regions[1080:]),
            'both_contacts_elbow_wave_steps':sum(r['Thorax_presence'] and r['proximal30_presence'] for r in regions[600:1080])}
        data[folder.name] = (initial,body,rot,trace,regions)
    comparisons = {}
    for label,(initial,body,rot,trace,regions) in data.items():
        if cases[label]['elbow_target_amplitude_deg'] == 0: continue
        match = next((n for n in data if cases[n]['elbow_target_amplitude_deg'] == 0 and cases[n]['Thorax_cap_N'] == cases[label]['Thorax_cap_N']), None)
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
