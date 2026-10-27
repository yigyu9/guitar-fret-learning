"""Native GPU hand target/reversal probe; no policy, state injection, or PD edits."""
import argparse
import hashlib
import json
from pathlib import Path
import time

FINGERS = ('index', 'middle', 'ring', 'pinky')


def protocol(time_s):
    """Fixed 16s protocol, measured independently of observed finger response."""
    if time_s <= 1:
        return 'initial_hold', 0., 0.
    if time_s <= 5:
        part = min(int(time_s-1-1e-9), 3)
        return ('initial_flex_plus', 'initial_flex_minus', 'initial_spread_plus',
                'initial_spread_minus')[part], (.04, -.04, 0., 0.)[part], (0., 0., .04, -.04)[part]
    if time_s <= 9:
        return 'move_B', 0., 0.
    if time_s <= 10:
        return 'B_hold', 0., 0.
    if time_s <= 14:
        part = min(int(time_s-10-1e-9), 3)
        return ('B_flex_plus', 'B_flex_minus', 'B_spread_plus',
                'B_spread_minus')[part], (.04, -.04, 0., 0.)[part], (0., 0., .04, -.04)[part]
    return 'final_hold', 0., 0.


def smooth_B(time_s):
    u = min(max((time_s-5.)/4., 0.), 1.)
    return u*u*(3-2*u)


class GraphicsGym:
    """Change only the diagnostic graphics device; delegate all native calls."""
    def __init__(self, native):
        self.native = native

    def __getattr__(self, name):
        return getattr(self.native, name)

    def create_sim(self, compute, graphics, engine, params):
        if graphics != -1:
            raise ValueError('Expected production headless graphics choice')
        return self.native.create_sim(compute, compute, engine, params)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--num-envs', type=int, default=1)
    parser.add_argument('--controls', type=int, default=960)
    parser.add_argument('--video', action='store_true', help='Native oblique camera, first environment only')
    args = parser.parse_args()
    if not 1 <= args.num_envs <= 1024 or not 1 <= args.controls <= 960:
        raise ValueError('1..1024 environments, 1..960 controls required')
    import isaacgym  # Native extension must load before Torch/NumPy.
    from isaacgym import gymapi
    import numpy as np
    import torch
    from guitar_learning.core.control import ACTIVE_NAMES, LEFT_HAND_NAMES
    from guitar_learning.gpu.control import BatchedController
    from guitar_learning.gpu.scene import GpuScene
    from guitar_learning.gpu.geometry import conjugate, multiply, rotvec
    from guitar_learning.gpu.finger_reward import B_PREPARATION_INPUT_DEGREES, B_PREPARATION_SPREAD_DEGREES
    from guitar_learning.runtime.prepared_reset_v1 import prepared_input_paths
    import subprocess

    root = Path(__file__).resolve().parents[3]
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    paths = set(prepared_input_paths()) | {p for p in root.rglob('*.py') if 'archive' not in p.parts}
    pins = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
    (out/'inputs_before.json').write_text(json.dumps(pins, indent=2))
    torch.set_num_threads(1)
    torch.manual_seed(7)
    np.random.seed(7)
    scene, video, samples, controls = None, None, [], []
    started, failure, reset_check, max_codec_error = time.monotonic(), None, None, 0.
    original_acquire = gymapi.acquire_gym
    try:
        if args.video:
            gymapi.acquire_gym = lambda: GraphicsGym(original_acquire())
        try:
            scene = GpuScene(args.num_envs, 'left', out=out/'scene')
        finally:
            gymapi.acquire_gym = original_acquire
        controller = BatchedController(scene)
        sample = scene.snapshot()
        controller.reset(range(args.num_envs), sample)
        joints = [scene.names.index('LH:'+f+s) for f in FINGERS for s in ('1_x', '1_z', '2', '3')]
        hand_joints = [scene.names.index(n) for n in LEFT_HAND_NAMES]
        hand_actions = [ACTIVE_NAMES.index(n) for n in LEFT_HAND_NAMES]
        actions = [ACTIVE_NAMES.index(scene.names[j]) for j in joints]
        segments = torch.tensor([[scene.body_names.index('human/LH:'+f+str(j)) for j in (1, 2, 3)]
                                 for f in FINGERS], device=scene.device)
        palm = scene.body_names.index('human/LH:palm')
        thumb = [scene.body_names.index('human/LH:thumb'+str(j)) for j in (1, 2, 3)]
        goal = torch.tensor([[x, z, pip, dip] for (x, pip, dip), z in
            zip(B_PREPARATION_INPUT_DEGREES, B_PREPARATION_SPREAD_DEGREES)], device=scene.device).flatten()*np.pi/180.
        move_start = None
        camera = None
        if args.video:
            props = gymapi.CameraProperties()
            props.width, props.height, props.horizontal_fov = 1280, 720, 55.
            camera = scene.gym.create_camera_sensor(scene.envs[0], props)
            if camera < 0:
                raise RuntimeError('Native camera creation failed')
            scene.gym.set_camera_location(camera, scene.envs[0], gymapi.Vec3(-.65, .22, .84),
                                          gymapi.Vec3(-.27, -.09, .66))
            video = subprocess.Popen(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n',
                '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1280x720', '-r', '30', '-i', '-',
                '-an', '-c:v', 'libx264', '-threads', '2', '-preset', 'fast', '-crf', '18',
                '-pix_fmt', 'yuv420p', str(out/'native_oblique.mp4')], stdin=subprocess.PIPE)
        for tick in range(args.controls):
            t = (tick+1)/60.
            stage, flex, spread = protocol(t)
            action = torch.zeros(args.num_envs, 39, device=scene.device)
            action[:, actions[0::4]] = flex
            action[:, actions[1::4]] = spread
            if stage == 'move_B':
                if move_start is None:
                    move_start = controller.target[:, joints].clone()
                desired = move_start+(goal[None]-move_start)*smooth_B(t)
                action[:, actions] = ((desired-controller.target[:, joints])*(60./4.)).clamp(-1, 1)
            before = controller.target[:, hand_joints].clone()
            expected = torch.maximum(torch.minimum(before+action[:, hand_actions]*(4./60.),
                                                   scene.upper[hand_joints]), scene.lower[hand_joints])
            target = controller.targets(action, sample)
            error = float((target[:, hand_joints]-expected).abs().max())
            max_codec_error = max(max_codec_error, error)
            if error > 2e-6:
                raise AssertionError('Incremental target codec disagrees with bounded integration')
            controls.append(dict(tick=tick+1, stage=stage, action=action[0].cpu().numpy().copy(),
                                 target=target[0].cpu().numpy().copy(), codec_error=error,
                                 physics_step_before=int(sample['physics_step'][0])))
            for _ in range(4):
                effort = controller.efforts(sample)
                if not bool(controller.diagnostics['valid'].all()):
                    raise RuntimeError('Finite support controller invalid')
                sample = scene.step(target, effort)
                if not all(bool(torch.isfinite(sample[k]).all()) for k in ('q', 'qd', 'body_state', 'contact_force')):
                    raise FloatingPointError('Nonfinite native response')
                body = sample['body_state']
                relative = multiply(conjugate(body[:, palm, None, 3:7]).expand(-1, 4, -1),
                                    body[:, segments[:, 0], 3:7])
                row = dict(time_s=sample['physics_step'][0].to(torch.float64)/240.,
                    body_state=body[0], q=sample['q'][0], qd=sample['qd'][0], target=sample['target'][0],
                    action=action[0], base_relative_quaternion=relative[0], base_relative_rotvec=rotvec(relative)[0],
                    segment_net_force=sample['contact_force'][0, segments],
                    thumb_net_force=sample['contact_force'][0, thumb],
                    palm_net_force=sample['contact_force'][0, palm])
                samples.append({k: v.detach().cpu().numpy().copy() for k, v in row.items()})
            if args.video and (tick+1) % 2 == 0:
                scene.gym.step_graphics(scene.sim)
                scene.gym.render_all_camera_sensors(scene.sim)
                rgba = scene.gym.get_camera_image(scene.sim, scene.envs[0], camera, gymapi.IMAGE_COLOR)
                rgb = np.asarray(rgba).reshape(720, 1280, 4)[..., :3].copy()
                video.stdin.write(rgb.tobytes())
            if (tick+1) % 60 == 0:
                print('control_tick', tick+1, stage, 'codec_max', max_codec_error, flush=True)
        scene.reset(range(args.num_envs))
        controller.reset(range(args.num_envs), scene.snapshot())
        reset_check = dict(all_physics_clocks_zero=bool((scene.episode_steps == 0).all()),
            target_reference_max_error=float((controller.target-scene.reference105).abs().max()),
            prepared_q_max_error=float((scene.q-scene.reference105).abs().max()), reset_calls=scene.reset_calls)
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error))
        raise
    finally:
        gymapi.acquire_gym = original_acquire
        video_code = None
        if video is not None:
            video.stdin.close()
            video_code = video.wait()
        if samples:
            np.savez_compressed(out/'physics_env0000.npz', **{k: np.stack([x[k] for x in samples]) for k in samples[0]})
        if controls:
            np.savez_compressed(out/'controls_env0000.npz', **{k: np.stack([x[k] for x in controls]) for k in controls[0]})
        if scene is not None:
            scene.close()
        changed = [p for p, v in pins.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest() != v]
        report = dict(completed=failure is None and not changed and video_code in (None, 0), failure=failure,
            num_envs=args.num_envs, controls=len(controls), physics_endpoints_per_environment=len(samples),
            recorded_environment=0, measured_hz=240, control_hz=60, max_codec_error_rad=max_codec_error,
            reset_check=reset_check, changed_inputs=changed, wall_s=time.monotonic()-started,
            video_encoder_exit_code=video_code, scene=scene.diagnostics if scene else None,
            scope='No training. Fixed small-action reversal and B target diagnostic. Forces are native body net forces, not body-pair pressures.',
            H32='No operation/reset at 32-control boundaries; every target transition checked against previous bounded target',
            joint_names=scene.names if scene else [], body_names=scene.body_names if scene else [],
            stage_labels='Initial/B describe commanded configurations; measured force must determine loading',
            state_writes='One initial prepared reset and one explicit end-of-protocol reset check',
            video_time_mapping='frame n maps to physical time (n+1)/30s; no initial camera frame')
        (out/'report.json').write_text(json.dumps(report, indent=2, allow_nan=False))
        if failure is None and not report['completed']:
            raise RuntimeError('Input immutability or video encoder audit failed')


if __name__ == '__main__':
    main()
