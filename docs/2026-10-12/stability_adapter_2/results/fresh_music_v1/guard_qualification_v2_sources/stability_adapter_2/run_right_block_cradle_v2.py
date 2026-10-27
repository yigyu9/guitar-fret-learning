"""Five seconds of free-guitar two-block support and scalar elbow motion."""
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
    from . import right_block_effort_v2 as support
    from .environment import ROOT, np
    from .environment_contract_v1 import EnvironmentContract
    from .run_joint_hold import native_state
    from .initial_pose_noise_v1 import pose
    from .build_fixed_lower_asset import LOWER_BODIES
    from .realistic_guitar_geometry_v1 import source_scene, source_audit
    from scipy.spatial.transform import Rotation
    import xml.etree.ElementTree as ET
    cfg = args.config.resolve(); contract = EnvironmentContract(cfg)
    baseline = ROOT/'docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/native_hold_v4'
    geometry = read(ROOT/'stability_adapter_2/assets/om_body_geometry_v3/manifest.json')
    paths = set((ROOT/'stability_adapter_2').rglob('*.py')) | set((ROOT/'stability_adapter_2').rglob('*.xml'))
    paths |= set((ROOT/'stability_adapter_2').glob('*PLAN*.md')) | set((ROOT/'tab2body').rglob('*.py'))
    paths |= {baseline/'initial_values.json', baseline/'native_properties.json'}
    paths |= {ROOT/'stability_adapter_2/assets/om_body_geometry_v3/manifest.json'}
    paths |= set(map(Path, contract.inputs)) | set(map(Path, geometry['input_sha256'])) | {Path(geometry['asset'])}
    paths |= {Path(m['path']) for m in geometry['meshes']}
    hashes = {str(p): sha(p) for p in sorted(paths)}; save(out/'attempt.json', {'input_sha256': hashes})
    scene = recorder = None; failure = None; trace = []; controls = []; videos = {}; stop = None
    try:
        with patch.object(dual, 'EnvironmentContract', lambda: EnvironmentContract(cfg)): scene = scene_class()(5.)
        initial = native_state(scene); reference = read(baseline/'initial_values.json'); old = reference['native_initial_state']
        fixed = [scene.human_bodies.index(n) for n in ('Pelvis',)+LOWER_BODIES]
        q = np.array([s['pos'] for s in initial['human_dof_states']]); fingers = [i for i,n in enumerate(scene.names) if n.startswith(('LH:', 'RH:'))]
        exact = {'guitar': initial['guitar_body_states'] == old['guitar_body_states'],
                 'root_lower': all(initial['human_body_states'][i] == old['human_body_states'][i] for i in fixed),
                 'fingers42': all(initial['human_dof_states'][i] == old['human_dof_states'][i] for i in fingers),
                 'PD': {k:scene.pd_properties[k].tolist() for k in scene.pd_properties.dtype.names} == reference['PD_properties'],
                 'mass': scene.mass_properties == read(baseline/'native_properties.json'),
                 'q_ref': np.array_equal(q, scene.contract.q_ref),
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
        save(out/'initial_verification.json', {'invariants':exact, 'FK_ok':fk_ok, 'FK_errors':errors, 'source_audit':audit})
        save(out/'initial_values.json', {'native_initial_state':initial, 'human_body_names':scene.human_bodies,
             'guitar_body_names':scene.guitar_bodies, 'joint_names':scene.names, 'PD_properties':reference['PD_properties'], 'q_ref_rad':q.tolist()})
        save(out/'native_properties.json', scene.mass_properties)
        from .environment import gymapi
        gp,gr = pose(initial['guitar_body_states'][0]); target = gp+gr.apply([0,-.34,-.02]); eye = target+gr.apply([.24,0,1.05])
        props = gymapi.CameraProperties(); props.width,props.height = 1280,960
        camera = scene.gym.create_camera_sensor(scene.env, props)
        if camera < 0: raise RuntimeError('OM camera creation failed')
        scene.gym.set_camera_location(camera,scene.env,gymapi.Vec3(*eye),gymapi.Vec3(*target)); scene.cameras['OM_appearance'] = camera
        scene.left_near_track_hold = True; recorder = support.EffortRecording(scene, out/'media'); recorder.capture()
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
        for tick in range(300):
            _, info = scene.step(action); controls.append(info); sample()
            if scene.steps % 8 == 0: recorder.capture()
            if scene.steps % 240 == 0: print('recorded', scene.steps/240, 'seconds', flush=True)
        stop = 'five_second_observation'
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
             'inputs_unchanged':unchanged, 'forbidden_calls':forbidden, 'videos':videos, 'strap_enabled':False,
             'checkpoints_connected':False, 'training_updates':0, 'config':str(cfg)})
    if failure or not unchanged or forbidden: raise RuntimeError(failure or 'input/guard violation')


if __name__ == '__main__':
    from . import right_block_effort_v2 as support
    with patch.object(support.LearningScene, '_create_scene', support.create_effort), \
         patch.object(support.base.string_trial_recording_v1, 'StrapTrialRecording', support.base.GymTrialRecording):
        main()
