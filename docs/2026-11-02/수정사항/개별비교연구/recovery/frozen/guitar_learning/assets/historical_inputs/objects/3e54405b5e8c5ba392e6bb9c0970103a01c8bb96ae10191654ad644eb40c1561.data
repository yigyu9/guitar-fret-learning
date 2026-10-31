"""Three static native views of the user-requested horizontal-neck orientation."""
import argparse
from pathlib import Path
from .guitar_pose_static import Editor
from .interactive_guitar_pose_static import read, save, sha, np, Rotation, gymapi, BASELINE
from .run_joint_hold import native_state
from .render_static_guitar_range import CAMERAS, metrics
from .horizontal_guitar_pose import BODY_CENTER_LOCAL, placement

REFERENCE = Path(__file__).resolve().parents[1]/'docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_000/pose.json'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    inputs = [Path(__file__).resolve(), REFERENCE, BASELINE]
    inputs += [Path(__file__).with_name(n) for n in ('HORIZONTAL_NECK_INITIAL_PLAN.md', 'horizontal_guitar_pose.py',
        'guitar_pose_static.py', 'interactive_guitar_pose_static.py', 'guitar_pose_edit.py',
        'capture_isaac_gym_initial.py', 'run_joint_hold.py', 'render_static_guitar_range.py')]
    hashes = {str(f): sha(f) for f in inputs}
    ref = read(REFERENCE)
    center = np.asarray(ref['position_W_m']) + Rotation.from_quat(ref['quaternion_xyzw']).apply(BODY_CENTER_LOCAL)
    angles = [-10., 0., 10.]
    save(args.out/'attempt.json', {'body_center_W_m': center.tolist(), 'neck_elevations_deg': angles,
        'front_normal_W': [0., 1., 0.], 'input_sha256': hashes, 'physics_steps_requested': 0})
    editor = Editor(args.out/'scene', strap=False, viewer=False)
    rows = []
    try:
        initial = native_state(editor.env)
        save(args.out/'initial_state.json', initial)
        cameras = {}
        for name, config in CAMERAS.items():
            props = gymapi.CameraProperties(); props.width, props.height = 1280, 720
            camera = editor.env.gym.create_camera_sensor(editor.env.env, props)
            if camera < 0: raise RuntimeError('native camera creation failed: '+name)
            editor.env.gym.set_camera_location(camera, editor.env.env,
                gymapi.Vec3(*config['position_W_m']), gymapi.Vec3(*config['target_W_m']))
            cameras[name] = camera
        for angle in angles:
            editor.position, editor.quaternion = placement(center, angle)
            editor.install_pose()
            folder = editor.save_candidate()
            before = native_state(editor.env)
            editor.env.gym.step_graphics(editor.env.sim)
            editor.env.gym.render_all_camera_sensors(editor.env.sim)
            images = {}
            for name, camera in cameras.items():
                path = folder/(name+'.png')
                editor.env.gym.write_camera_image_to_file(editor.env.sim, editor.env.env, camera, gymapi.IMAGE_COLOR, str(path))
                if not path.is_file() or not path.stat().st_size: raise RuntimeError('native image write failed')
                images[str(path)] = sha(path)
            after = native_state(editor.env)
            actual = metrics(editor)
            rotation = Rotation.from_quat(editor.quaternion)
            checks = {'zero_steps': editor.env.steps == 0,
                'human_exact': after['human_body_states'] == initial['human_body_states'] and after['human_dof_states'] == initial['human_dof_states'],
                'render_readonly': before == after, 'no_physics_calls': editor.env.gym.blocked_physics_calls == 0,
                'front_faces_world_Y': bool(np.linalg.norm(rotation.apply([0,0,1])-[0,1,0]) < 1e-6),
                'body_center_preserved': bool(np.linalg.norm(np.asarray(actual['body_center_W_m'])-center) < 1e-6),
                'neck_elevation_matches': abs(actual['neck_elevation_deg']-angle) < 1e-4}
            save(folder/'comparison.json', dict(actual, requested_elevation_deg=angle, checks=checks, extra_image_sha256=images))
            if not all(checks.values()): raise AssertionError(checks)
            rows.append(dict(actual, requested_elevation_deg=angle, path=str(folder)))
            print('rendered neck', angle, flush=True)
        checks = {'all_three_completed': len(rows) == 3, 'inputs_unchanged': all(sha(f) == h for f,h in hashes.items())}
        save(args.out/'comparison.json', {'rows': rows, 'checks': checks, 'physics_steps': 0, 'input_sha256': hashes})
        if not all(checks.values()): raise AssertionError(checks)
    finally:
        editor.close_scene()


if __name__ == '__main__': main()
