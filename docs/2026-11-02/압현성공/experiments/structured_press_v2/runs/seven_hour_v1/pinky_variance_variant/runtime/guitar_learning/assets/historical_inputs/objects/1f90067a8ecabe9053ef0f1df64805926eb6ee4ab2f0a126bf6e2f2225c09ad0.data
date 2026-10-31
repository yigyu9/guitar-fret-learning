"""Record the complete left grip/release diagnostic on the accepted right-shift initial pose."""
import argparse
import traceback
from unittest.mock import patch
from .initial_pose_noise_v1 import read, save, sha


def main():
    from pathlib import Path
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True); parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(); out = args.out.resolve(); out.mkdir(parents=True, exist_ok=False)
    from . import dual_music_scene_v1 as dual
    from .left_near_scene_v3 import scene_class
    from . import right_block_body_effort_v5 as support
    from .environment import ROOT, np
    from .environment_contract_v1 import EnvironmentContract
    from .run_joint_hold import native_state
    from .initial_pose_noise_v1 import pose
    from .build_fixed_lower_asset import LOWER_BODIES
    from .realistic_guitar_geometry_v1 import source_scene, source_audit
    from scipy.spatial.transform import Rotation
    import xml.etree.ElementTree as ET
    cfg = args.config.resolve(); contract = EnvironmentContract(cfg)
    baseline = ROOT/'docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/native_elbow5_close'
    geometry = read(ROOT/'stability_adapter_2/assets/om_body_geometry_v3/manifest.json')
    paths = set((ROOT/'stability_adapter_2').rglob('*.py')) | set((ROOT/'stability_adapter_2').rglob('*.xml'))
    paths |= set((ROOT/'stability_adapter_2').glob('*PLAN*.md')) | set((ROOT/'tab2body').rglob('*.py'))
    paths |= {baseline/'initial_values.json',baseline/'native_properties.json',ROOT/'docs/2026-10-19/stability_adapter_2/results/left_thumb_natural_v1/native_v1/initial_values.json',ROOT/'docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3/search.json'}
    paths |= {ROOT/'stability_adapter_2/assets/om_body_geometry_v3/manifest.json',ROOT/'docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/native_off_v1/initial_values.json'}
    paths |= set(map(Path, contract.inputs)) | set(map(Path, geometry['input_sha256'])) | {Path(geometry['asset'])}
    paths |= {Path(m['path']) for m in geometry['meshes']}
    human_asset = ROOT/'stability_adapter_2/assets/humanoid_fixed_lower.xml'
    human_xml = ET.parse(human_asset).getroot(); meshdir = (human_asset.parent/human_xml.find('compiler').get('meshdir')).resolve()
    paths |= {(meshdir/m.get('file')).resolve() for m in human_xml.findall('./asset/mesh')}
    guitar_asset=Path(geometry['asset']); guitar_xml=ET.parse(guitar_asset).getroot()
    guitar_meshdir=(guitar_asset.parent/guitar_xml.find('compiler').get('meshdir')).resolve()
    paths |= {(guitar_meshdir/m.get('file')).resolve() for m in guitar_xml.findall('./asset/mesh')}
    paths |= {ROOT/'docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/native_realistic_v2/native_properties.json', ROOT/'stability_adapter_2/LEFT_GRIP_RELEASE_CYCLE_PLAN_V1.md', ROOT/'stability_adapter_2/LEFT_GRIP_RELEASE_CYCLE_PLAN_V2.md', ROOT/'stability_adapter_2/config.json', ROOT/'docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/native_right10_v1/initial_values.json'}
    paths = {p for p in paths if 'fresh_learning_v1' not in p.parts}
    hashes = {str(p): sha(p) for p in sorted(paths)}; save(out/'attempt.json', {'input_sha256': hashes})
    scene = recorder = None; failure = None; trace = []; controls = []; videos = {}; stop = None
    try:
        with patch.object(dual, 'EnvironmentContract', lambda: EnvironmentContract(cfg)): scene = scene_class()(16.)
        initial = native_state(scene)
        assert initial == read(ROOT/'docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/native_right10_v1/initial_values.json')['native_initial_state'], 'shifted actual initial state changed'
        reference = read(baseline/'initial_values.json'); old = reference['native_initial_state']
        fixed = [scene.human_bodies.index(n) for n in ('Pelvis',)+LOWER_BODIES]
        q = np.array([s['pos'] for s in initial['human_dof_states']]); fingers = [i for i,n in enumerate(scene.names) if n.startswith(('LH:', 'RH:')) and not n.startswith('LH:')]
        thumb = [i for i,n in enumerate(scene.names) if n.startswith('LH:thumb')]; assert len(fingers)==21 and len(thumb)==5
        if not scene.contract.candidate.get('left_neck_near',{}).get('accepted_for_native'):raise AssertionError('three-face source not accepted')
        current=read(ROOT/'docs/2026-10-19/stability_adapter_2/results/left_thumb_natural_v1/native_v1/initial_values.json')
        arms=[i for i,n in enumerate(scene.names) if n.startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist','R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))]
        frozen=[i for i in range(81) if i not in arms];assert len(arms)==24 and len(frozen)==57
        current=read(ROOT/'docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/native_off_v1/initial_values.json')
        assert all(initial['human_dof_states'][i]==current['native_initial_state']['human_dof_states'][i] for i in frozen)
        shift=np.array(scene.contract.candidate['right_shift_initial']['guitar_delta_W_m'])
        original_g=current['native_initial_state']['guitar_body_states']
        assert len(original_g)==len(initial['guitar_body_states'])
        assert all(a['pose']['r']==b['pose']['r'] and np.linalg.norm(pose(a)[0]-pose(b)[0]-shift)<3e-6 for a,b in zip(initial['guitar_body_states'],original_g))
        expected_PD = {k:list(v) for k,v in reference['PD_properties'].items()}
        body_factor = float(scene.contract.config.get('body_PD_factor', 1)); assert body_factor in (1.,4.)
        for i,n in enumerate(scene.names):
            if n.startswith(('Torso_','Spine_','Chest_')):
                expected_PD['stiffness'][i] *= body_factor; expected_PD['damping'][i] *= body_factor**.5
        if scene.contract.config.get('body9_effort'):
            for i in scene.contract.body:
                expected_PD['driveMode'][i] = 3; expected_PD['stiffness'][i] = 0; expected_PD['damping'][i] = 0
        actual_PD = {k:scene.pd_properties[k].tolist() for k in scene.pd_properties.dtype.names}
        expected_guitar = scene.contract.candidate['predicted_guitar_body_states']
        guitar_errors = []
        for actual, expected in zip(initial['guitar_body_states'], expected_guitar):
            p,r = pose(actual); ep,er = pose(expected)
            guitar_errors.append({'position_m':float(np.linalg.norm(p-ep)), 'rotation_rad':float((er.inv()*r).magnitude())})
        exact = {'guitar': len(initial['guitar_body_states']) == len(expected_guitar) and all(v['position_m'] < 3e-6 and v['rotation_rad'] < 1e-5 for v in guitar_errors),
                 'neck_direction': float(np.linalg.norm(pose(old['guitar_body_states'][0])[1].apply([0,1,0])-pose(initial['guitar_body_states'][0])[1].apply([0,1,0]))) < 1e-6,
                 'root_lower': all(initial['human_body_states'][i] == old['human_body_states'][i] for i in fixed),
                 'right_fingers21': all(initial['human_dof_states'][i] == old['human_dof_states'][i] for i in fingers),
                 'PD': actual_PD == expected_PD,
                 'mass': scene.mass_properties == read(baseline/'native_properties.json'),
                 'q_ref': np.array_equal(q, scene.contract.q_ref),
                 'thumb5': all(q[i]==scene.contract.q_ref[i] for i in thumb),
                 'limits': bool(np.all(q >= scene.contract.lower) and np.all(q <= scene.contract.upper))}
        prediction = scene.contract.candidate['predicted_human_poses']; errors = {}
        for n,s in zip(scene.human_bodies, initial['human_body_states']):
            p,r = pose(s); expected = prediction[n]
            errors[n] = {'position_m':float(np.linalg.norm(p-expected['p'])), 'rotation_rad':float((Rotation.from_quat(expected['q']).inv()*r).magnitude())}
        xml = ET.parse(ROOT/'stability_adapter_2/assets/humanoid_fixed_lower.xml').getroot()
        parents = {c.get('name'):p.get('name') for p in xml.iter('body') for c in p.findall('body')}
        audit = source_audit(source_scene(initial, scene.human_bodies, geometry['asset']), parents)
        fk_ok = max(v['position_m'] for v in errors.values()) < .001 and max(v['rotation_rad'] for v in errors.values()) < .001
        assert native_state(scene) == initial
        save(out/'initial_verification.json', {'invariants':exact, 'FK_ok':fk_ok, 'FK_errors':errors, 'source_audit':audit, 'expected_PD':expected_PD, 'body_PD_factor':body_factor, 'guitar_candidate_state_errors':guitar_errors, 'guitar_initial_delta_W_m':(pose(initial['guitar_body_states'][0])[0]-pose(old['guitar_body_states'][0])[0]).tolist()})
        save(out/'initial_values.json', {'native_initial_state':initial, 'human_body_names':scene.human_bodies,
             'guitar_body_names':scene.guitar_bodies, 'joint_names':scene.names, 'PD_properties':actual_PD, 'q_ref_rad':q.tolist()})
        save(out/'native_properties.json', scene.mass_properties)
        from .environment import gymapi
        gp,gr = pose(initial['guitar_body_states'][0]); target = gp+gr.apply([0,-.34,-.02]); eye = target+gr.apply([.24,0,1.05])
        props = gymapi.CameraProperties(); props.width,props.height = 1280,960
        camera = scene.gym.create_camera_sensor(scene.env, props)
        if camera < 0: raise RuntimeError('OM camera creation failed')
        scene.gym.set_camera_location(camera,scene.env,gymapi.Vec3(*eye),gymapi.Vec3(*target)); scene.cameras['OM_appearance'] = camera
        # Additional read-only camera shows the thumb from the neck's back/underside.
        thumb_state=initial['human_body_states'][scene.human_bodies.index('LH:thumb3')]
        palm_state=initial['human_body_states'][scene.human_bodies.index('LH:palm')]
        target=(pose(thumb_state)[0]+pose(palm_state)[0])/2; eye=target+gr.apply([.13,.07,-.28])
        props=gymapi.CameraProperties();props.width,props.height=1280,720
        thumb_camera=scene.gym.create_camera_sensor(scene.env,props)
        if thumb_camera<0:raise RuntimeError('thumb camera creation failed')
        scene.gym.set_camera_location(thumb_camera,scene.env,gymapi.Vec3(*eye),gymapi.Vec3(*target));scene.cameras['thumb_back']=thumb_camera
        scene.left_near_track_hold=True;recorder=support.EffortRecording(scene,out/'media')
        recorder.views=recorder.strap.views=tuple(recorder.views)+('thumb_back',)
        for recording in (recorder,recorder.strap):(recording.out/'frames/thumb_back').mkdir(parents=True,exist_ok=False)
        from .left_neck_near_geometry_v1 import FACETS
        from .left_neck_three_face_geometry_v1 import measurements,placement_pass
        facets=read(FACETS)['facets']
        def faces(owner,state):
            poses={name:pose(row) for name,row in zip(owner.human_bodies,state['human_body_states'])}
            gp,gr=pose(state['guitar_body_states'][0]);row=owner.contract.candidate['left_neck_near']
            return measurements(poses,gp,gr,row['station_G_m'],row['front_z_G_m'],facets)
        faces_pass=placement_pass
        initial_faces=faces(scene,initial)
        save(out/'initial_three_faces.json',{'measurements':initial_faces,'pass':faces_pass(initial_faces),'frozen57_initial_exact':True,'guitar_rotation39_exact':True,'guitar_delta_W_m':shift.tolist()})
        if not faces_pass(initial_faces):raise AssertionError('actual initial three-face positions rejected')
        previous_observe=scene.after_physics
        def observe_faces(owner):
            previous_observe(owner);state=native_state(owner);measured=faces(owner,state)
            row=recorder.endpoint_rows[-1];row['left_three_faces']=measured;row['left_three_faces_pass']=faces_pass(measured)
            row['human_body_states'].update({n:state['human_body_states'][owner.human_bodies.index(n)] for n in measured})
            assert native_state(owner)==state
        scene.after_physics=observe_faces
        recorder.capture()
        if not(all(exact.values()) and fk_ok and audit['source_clear'] and scene.contract.candidate['right_block_cradle']['accepted_for_native']):
            raise AssertionError('native initial verification rejected')
        def sample():
            s = native_state(scene)
            assert all(s['human_body_states'][i] == initial['human_body_states'][i] for i in fixed)
            q = np.array([v['pos'] for v in s['human_dof_states']]); velocity = np.array([v['vel'] for v in s['human_dof_states']])
            if not np.isfinite(np.r_[q,velocity]).all() or abs(velocity).max() > 50: raise RuntimeError('unsafe joint state')
            gp,gr = pose(s['guitar_body_states'][0]); g0,r0 = pose(initial['guitar_body_states'][0])
            trace.append({'physics_step':scene.steps, 'position_W_m':gp.tolist(), 'quaternion_xyzw':gr.as_quat().tolist(),
                          'q_rad':q.tolist(), 'qdot_rad_s':velocity.tolist()})
            if np.linalg.norm(gp-g0) > .20 or np.rad2deg((r0.inv()*gr).magnitude()) > 35: raise RuntimeError('guitar safety displacement')
        sample()
        action = np.clip((scene.contract.q_ref-scene.contract.mid)/scene.contract.half, -1., 1.)
        for tick in range(960):
            _, info = scene.step(action); controls.append(info); sample()
            if scene.steps % 8 == 0: recorder.capture()
            if scene.steps % 240 == 0: print('recorded', scene.steps/240, 'seconds', flush=True)
        stop = 'sixteen_second_left_cycle_observation'
    except BaseException as e:
        failure = {'type':type(e).__name__, 'message':str(e), 'traceback':traceback.format_exc()}; print(failure['traceback'], flush=True)
    finally:
        if scene and recorder and (not recorder.frames or recorder.frames[-1]['physics_step'] != scene.steps):
            try: recorder.capture()
            except BaseException as e:
                if failure is None: failure = {'type':type(e).__name__, 'message':str(e)}
        steps = scene.steps if scene else 0; forbidden = list(scene.forbidden_calls) if scene else []
        if scene: save(out/'final_state.json', native_state(scene)); scene.close()
        if recorder:
            try: videos = recorder.encode()
            except BaseException as e:
                if failure is None: failure = {'type':type(e).__name__, 'message':str(e)}
        unchanged = all(sha(p) == h for p,h in hashes.items())
        save(out/'controls.json', controls); save(out/'trace.json', trace)
        save(out/'report.json', {'completed':failure is None and unchanged and not forbidden, 'failure':failure,
             'stop_reason':stop, 'physics_steps':steps, 'control_steps':len(controls), 'physics_seconds':steps/240,
             'inputs_unchanged':unchanged, 'forbidden_calls':forbidden, 'videos':videos, 'strap_enabled':False, 'right_shift_initial':True,
             'checkpoints_connected':False, 'training_updates':0, 'left_cycle_diagnostic':True, 'right_strike_enabled':False, 'config':str(cfg)})
    if failure or not unchanged or forbidden: raise RuntimeError(failure or 'input/guard violation')


if __name__ == '__main__':
    from .left_grip_release_cycle_v2 import main as run_cycle
    run_cycle(main)
