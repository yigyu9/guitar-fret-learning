"""Single-environment B target test: real GPU PhysX and native Gym cameras."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

PHASE = Path(__file__).resolve().parents[1]
ROOT = PHASE.parents[3]
sys.path.insert(0, str(ROOT))
FINGERS = ('index', 'middle', 'ring', 'pinky')
COLORS = ((.18, .52, .87), (.10, .67, .49), (.94, .57, .18), (.63, .38, .82))
CAMERAS = dict(
    front=dict(position=[-.244, .508, .629], target=[-.244, -.10, .629], horizontal_fov=55.),
    oblique=dict(position=[-.65, .22, .84], target=[-.27, -.09, .66], horizontal_fov=55.),
    fullbody=dict(position=[-.10, 2.7, 1.1], target=[-.15, -.10, .65], horizontal_fov=55.))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)


def blend(t):
    u = min(max((t-1.)/4., 0.), 1.)
    return u*u*(3.-2.*u)


def target_action(current, desired):
    """Invert the production 4rad/s incremental target codec, without q writes."""
    return ((desired-current)*(60./4.)).clamp(-1., 1.)


class GraphicsGym:
    """Delegate every native call; enable graphics only for this new scene."""
    def __init__(self, native):
        self.native = native

    def __getattr__(self, name):
        return getattr(self.native, name)

    def create_sim(self, compute, graphics, engine, params):
        if graphics != -1:
            raise ValueError('Expected production headless graphics choice')
        return self.native.create_sim(compute, compute, engine, params)


def encoder(path):
    return subprocess.Popen(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n',
        '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1280x720', '-r', '30',
        '-i', '-', '-an', '-c:v', 'libx264', '-threads', '2', '-preset', 'fast',
        '-crf', '18', '-pix_fmt', 'yuv420p', str(path)], stdin=subprocess.PIPE)


def finish_encoders(videos):
    codes, errors = {}, {}
    for name, process in videos.items():
        try:
            process.stdin.close()
        except OSError as error:
            errors[name] = repr(error)
        codes[name] = process.wait()
    return codes, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=PHASE/'native_run')
    parser.add_argument('--controls', type=int, default=480, help='60Hz ticks; 480 gives the full8s test')
    args = parser.parse_args()
    if not 1 <= args.controls <= 480:
        raise ValueError('Controls must be1..480')
    import isaacgym  # Must precede NumPy/Torch.
    from isaacgym import gymapi
    import numpy as np
    import torch
    from guitar_learning.core.control import ACTIVE_NAMES
    from guitar_learning.gpu.scene import GpuScene
    from guitar_learning.gpu.control import BatchedController
    from guitar_learning.gpu.finger_reward import (
        B_PREPARATION_INPUT_DEGREES, B_PREPARATION_SPREAD_DEGREES,
        B_PREPARATION_ANGLES_DEGREES, finger_posture_reward)
    from guitar_learning.runtime.prepared_reset_v1 import prepared_input_paths

    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    paths = {p for p in (ROOT/'guitar_learning').rglob('*.py') if 'archive' not in p.parts}
    paths.update(prepared_input_paths())
    paths.add(Path(__file__).resolve())
    pins = {str(p): sha(p) for p in sorted(paths)}
    write(out/'inputs_before.json', pins)
    torch.set_num_threads(1)
    torch.manual_seed(7)
    np.random.seed(7)
    original_acquire = gymapi.acquire_gym
    scene, videos, samples = None, {}, []
    started, failure = time.monotonic(), None
    frame_count = 0
    try:
        gymapi.acquire_gym = lambda: GraphicsGym(original_acquire())
        try:
            scene = GpuScene(1, 'left', out=out/'scene')
        finally:
            gymapi.acquire_gym = original_acquire
        controller = BatchedController(scene)
        sample = scene.snapshot()
        controller.reset([0], sample)
        initial_body = sample['body_state'][0].cpu().numpy().copy()
        joints = [scene.names.index('LH:'+f+s) for f in FINGERS for s in ('1_x', '1_z', '2', '3')]
        actions = [ACTIVE_NAMES.index(scene.names[j]) for j in joints]
        segments = torch.tensor([[scene.body_names.index('human/LH:'+f+str(j)) for j in (1, 2, 3)]
            for f in FINGERS], device=scene.device)
        palm = scene.body_names.index('human/LH:palm')
        native_b = [[x, z, pip, dip] for (x, pip, dip), z in
            zip(B_PREPARATION_INPUT_DEGREES, B_PREPARATION_SPREAD_DEGREES)]
        goal = torch.tensor(native_b, device=scene.device).flatten()*np.pi/180.
        if not bool(((goal >= scene.lower[joints]) & (goal <= scene.upper[joints])).all()):
            raise ValueError('B requested joint values outside unchanged native limits')
        start_target = controller.target[:, joints].clone()
        reference = torch.tensor(B_PREPARATION_ANGLES_DEGREES, device=scene.device)*np.pi/180.
        for i, name in enumerate(scene.human_bodies):
            for finger, color in zip(FINGERS, COLORS):
                if name.startswith('LH:'+finger):
                    scene.gym.set_rigid_body_color(scene.envs[0], scene.actors[0][0], i,
                        gymapi.MESH_VISUAL, gymapi.Vec3(*color))
        scene.gym.set_light_parameters(scene.sim, 0, gymapi.Vec3(.9, .9, .9),
            gymapi.Vec3(.55, .55, .55), gymapi.Vec3(-.3, -1, -1))
        cameras = {}
        for name, config in CAMERAS.items():
            props = gymapi.CameraProperties()
            props.width, props.height, props.horizontal_fov = 1280, 720, config['horizontal_fov']
            handle = scene.gym.create_camera_sensor(scene.envs[0], props)
            if handle < 0:
                raise RuntimeError('Native camera creation failed: '+name)
            scene.gym.set_camera_location(handle, scene.envs[0],
                gymapi.Vec3(*config['position']), gymapi.Vec3(*config['target']))
            cameras[name] = handle
            videos[name] = encoder(out/('raw_'+name+'.mp4'))
        write(out/'metadata.json', dict(joint_names=scene.names, body_names=scene.body_names,
            finger_joint_names=[scene.names[j] for j in joints], B_native_degrees=native_b,
            B_geometric_degrees=B_PREPARATION_ANGLES_DEGREES, initial_body_state=initial_body.tolist(),
            cameras=CAMERAS, width=1280, height=720, fps=30, physics_hz=240, control_hz=60,
            schedule=dict(hold_initial_s=1., move_s=4., hold_final_s=3.),
            measurement='Actual relative-body forward-vector yz flexion, as the production B preference',
            video_time_mapping='frame n records physical time(n+1)/30s; no t0 camera frame',
            scope='Direct B target diagnostic, no learned policy or training; native GPU PhysX and native Gym camera pixels',
            unchanged='Other policy actions zero, thumb command held; finite support control, native PD/limits/collision, free gravity guitar; no physical-state overwrites after boundary reset',
            graphics_adapter='Only create_sim graphics device changes from−1 to compute GPU; physics params passed unchanged'))
        empty = torch.empty(0, device=scene.device)
        finger_ids = empty.to(torch.long)
        for tick in range(args.controls):
            t = (tick+1)/60.
            desired = start_target+(goal[None]-start_target)*blend(t)
            action = torch.zeros(1, 39, device=scene.device)
            action[:, actions] = target_action(controller.target[:, joints], desired)
            target = controller.targets(action, sample)
            if not torch.allclose(target[:, joints], desired, atol=2e-6, rtol=0):
                raise ValueError('Production codec did not follow the smooth bounded B schedule')
            for _ in range(4):
                effort = controller.efforts(sample)
                if not bool(controller.diagnostics['valid'].all()):
                    raise RuntimeError('Existing finite support controller is invalid')
                sample = scene.step(target, effort)
                if not all(bool(torch.isfinite(sample[k]).all()) for k in ('q', 'qd', 'body_state', 'contact_force')):
                    raise FloatingPointError('Nonfinite native response')
                body = sample['body_state']
                measured = finger_posture_reward(sample['physics_step']/240., empty, empty, empty,
                    finger_ids, body[:, palm, 3:7], body[:, segments, 3:7])
                angles, valid = measured['angles'], measured['valid'].all(-1)
                excess = (angles-reference).abs().sub(np.pi/12).clamp_min(0)
                quality = (1+(excess/(np.pi/6)).square().sum(-1)).reciprocal()*valid
                values = dict(time_s=sample['physics_step'][0].to(torch.float64)/240., body_state=body[0],
                    q=sample['q'][0], target=sample['target'][0], action=action[0],
                    angles=angles[0], band_inside=(valid & (excess == 0).all(-1))[0], quality=quality[0],
                    segment_net_force=sample['contact_force'][0, segments], palm_net_force=sample['contact_force'][0, palm])
                samples.append({k: v.detach().cpu().numpy().copy() for k, v in values.items()})
            if (tick+1) % 2 == 0:
                scene.gym.step_graphics(scene.sim)
                scene.gym.render_all_camera_sensors(scene.sim)
                for name, handle in cameras.items():
                    rgba = scene.gym.get_camera_image(scene.sim, scene.envs[0], handle, gymapi.IMAGE_COLOR)
                    rgb = np.asarray(rgba).reshape(720, 1280, 4)[..., :3].copy()
                    if frame_count == 0 and float(rgb.std()) < 1.:
                        raise RuntimeError('Native camera image is blank: '+name)
                    videos[name].stdin.write(rgb.tobytes())
                frame_count += 1
            if (tick+1) % 60 == 0:
                print('control_tick', tick+1, 'time_s', t, 'B_inside', samples[-1]['band_inside'].tolist(), flush=True)
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error))
        raise
    finally:
        gymapi.acquire_gym = original_acquire
        encoder_exit_codes, encoder_errors = finish_encoders(videos)
        close_error = None
        try:
            if samples:
                np.savez_compressed(out/'physics.npz', **{k: np.stack([row[k] for row in samples]) for k in samples[0]})
        finally:
            if scene is not None:
                try:
                    scene.close()
                except Exception as error:
                    close_error = repr(error)
        changed = [p for p, expected in pins.items() if sha(p) != expected]
        success = (failure is None and not changed and not encoder_errors and close_error is None
                   and all(v == 0 for v in encoder_exit_codes.values()))
        write(out/'report.json', dict(completed=success, failure=failure, requested_controls=args.controls,
            physics_endpoints=len(samples), frames_per_view=frame_count, fps=30,
            wall_s=time.monotonic()-started, input_count=len(pins), changed_inputs=changed,
            encoder_exit_codes=encoder_exit_codes, encoder_errors=encoder_errors, close_error=close_error,
            scene=scene.diagnostics if scene is not None else None,
            native_rendering=True, training=False, state_setters='Prepared boundary reset only',
            output_sha256={p.name: sha(p) for p in out.glob('*.mp4')}))
        if failure is None and not success:
            raise RuntimeError('Input immutability or native-video encoder audit failed')


if __name__ == '__main__':
    main()
