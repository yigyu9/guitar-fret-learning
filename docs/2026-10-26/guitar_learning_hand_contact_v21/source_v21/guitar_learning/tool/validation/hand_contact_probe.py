"""Native GPU hand target/reversal probe; no policy, state injection, or PD edits."""
import argparse
import hashlib
import json
from pathlib import Path
import time

FINGERS = ('index', 'middle', 'ring', 'pinky')
# Fixed diagnostic command, matching the user-selected B; never updates state.
B_NATIVE_DEGREES = ((25., -14., 35., 12.), (28., -3., 38., 14.),
                    (31., 3., 41., 16.), (34., 10., 44., 18.))


def physics_source_paths(root):
    """Pin physical execution inputs, independent of concurrent reward edits."""
    paths = [root/'guitar_learning'/p for p in (
        'gpu/scene.py', 'gpu/control.py', 'gpu/geometry.py', 'gpu/rigid_guitar.py',
        'gpu/hand_collision.py', 'core/control.py', 'core/finger_control.py',
        'core/geometry_v1.py', 'runtime/prepared_reset_v1.py', 'runtime/native_session.py',
        'native/paths.py', 'tool/validation/hand_contact_probe.py')]
    return {p for p in paths if p.exists()} | set((root/'guitar_learning/assets/gpu_rigid_guitar_v1').glob('*'))


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


def finish_video(video):
    """A broken encoder pipe must not prevent raw capture/scene cleanup."""
    errors, code = [], None
    if video is not None:
        try:
            video.stdin.close()
        except OSError as error:
            errors.append('encoder_stdin: '+repr(error))
        try:
            code = video.wait()
        except Exception as error:
            errors.append('encoder_wait: '+repr(error))
    return code, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--num-envs', type=int, default=1)
    parser.add_argument('--controls', type=int, default=960)
    parser.add_argument('--video', action='store_true', help='Native oblique camera, first environment only')
    parser.add_argument('--source-filters-diagnostic', action='store_true',
                        help='Diagnostic-only original filters comparison; never a training option')
    parser.add_argument('--tape', type=Path,
                        help='Immutable pose capture with action[t0+controls,39], clock, target; replay actions only')
    args = parser.parse_args()
    if not 1 <= args.num_envs <= 1024 or not 1 <= args.controls <= (1969 if args.tape else 960):
        raise ValueError('1..1024 environments; <=960 diagnostic or <=1969 tape controls required')
    import isaacgym  # Native extension must load before Torch/NumPy.
    from isaacgym import gymapi
    import numpy as np
    import torch
    from guitar_learning.core.control import ACTIVE_NAMES, LEFT_HAND_NAMES
    from guitar_learning.gpu.control import BatchedController
    from guitar_learning.gpu.scene import GpuScene
    from guitar_learning.gpu.geometry import conjugate, multiply, rotvec
    from guitar_learning.runtime.prepared_reset_v1 import prepared_input_paths
    import subprocess

    root = Path(__file__).resolve().parents[3]
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    paths = set(prepared_input_paths()) | physics_source_paths(root)
    tape = None
    if args.tape:
        paths.add(args.tape.resolve())
        with np.load(args.tape) as capture:
            tape = {k: capture[k].copy() for k in ('action', 'clock', 'target')}
        if (tape['action'].ndim != 2 or tape['action'].shape[1] != 39 or
                len(tape['action']) < args.controls+1 or not np.isfinite(tape['action']).all() or
                np.max(np.abs(tape['action'])) > 1 or tape['clock'][0] != 0 or
                not np.all(np.diff(tape['clock']) == 4) or not np.all(tape['action'][0] == 0)):
            raise ValueError('Finite bounded 39-action tape with explicit t0 and 4-step clock spacing required')
    pins = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
    (out/'inputs_before.json').write_text(json.dumps(pins, indent=2))
    torch.set_num_threads(1)
    torch.manual_seed(7)
    np.random.seed(7)
    scene, video, samples, controls = None, None, [], []
    started, failure, reset_check, max_codec_error = time.monotonic(), None, None, 0.
    tape_target_error, stopped_by_safety = 0., None
    original_acquire = gymapi.acquire_gym
    from guitar_learning.gpu import hand_collision
    original_filters = hand_collision.left_hand_collision_properties
    try:
        if args.video:
            gymapi.acquire_gym = lambda: GraphicsGym(original_acquire())
        if args.source_filters_diagnostic:
            import copy
            hand_collision.left_hand_collision_properties = lambda shapes: (
                copy.deepcopy(shapes), dict(schema='diagnostic.original_source_filters.v1',
                    enabled_distinct_finger_pairs=0, diagnostic_only=True))
        try:
            scene = GpuScene(args.num_envs, 'left', out=out/'scene')
        finally:
            gymapi.acquire_gym = original_acquire
            hand_collision.left_hand_collision_properties = original_filters
        controller = BatchedController(scene)
        sample = scene.snapshot()
        controller.reset(range(args.num_envs), sample)
        initial_q = sample['q'].clone()
        initial_guitar = sample['body_state'][:, len(scene.human_bodies), :7].clone()
        per_env = {key: torch.zeros(args.num_envs, device=scene.device) for key in
                   ('max_net_force_N', 'max_guitar_translation_m', 'max_guitar_rotation_rad',
                    'max_q_bound_excess_rad', 'max_abs_qd_rad_s')}
        force_peak_body = torch.zeros(args.num_envs, device=scene.device, dtype=torch.long)
        force_peak_step = torch.zeros_like(force_peak_body)
        joints = [scene.names.index('LH:'+f+s) for f in FINGERS for s in ('1_x', '1_z', '2', '3')]
        hand_joints = [scene.names.index(n) for n in LEFT_HAND_NAMES]
        hand_actions = [ACTIVE_NAMES.index(n) for n in LEFT_HAND_NAMES]
        actions = [ACTIVE_NAMES.index(scene.names[j]) for j in joints]
        segments = torch.tensor([[scene.body_names.index('human/LH:'+f+str(j)) for j in (1, 2, 3)]
                                 for f in FINGERS], device=scene.device)
        palm = scene.body_names.index('human/LH:palm')
        thumb = [scene.body_names.index('human/LH:thumb'+str(j)) for j in (1, 2, 3)]
        goal = torch.tensor(B_NATIVE_DEGREES, device=scene.device).flatten()*np.pi/180.
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
            if tape is not None:
                stage = 'captured_action_replay'
                action[:] = torch.as_tensor(tape['action'][tick+1], device=scene.device)
            before = controller.target[:, hand_joints].clone()
            expected = torch.maximum(torch.minimum(before+action[:, hand_actions]*(4./60.),
                                                   scene.upper[hand_joints]), scene.lower[hand_joints])
            target = controller.targets(action, sample)
            error = float((target[:, hand_joints]-expected).abs().max())
            max_codec_error = max(max_codec_error, error)
            if tape is not None:
                captured = torch.as_tensor(tape['target'][tick+1, hand_joints], device=scene.device)
                tape_target_error = max(tape_target_error, float((target[:, hand_joints]-captured).abs().max()))
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
                guitar = body[:, len(scene.human_bodies), :7]
                drift = torch.linalg.vector_norm(guitar[:, :3]-initial_guitar[:, :3], dim=-1)
                rotation = torch.linalg.vector_norm(rotvec(multiply(conjugate(initial_guitar[:, 3:]), guitar[:, 3:])), dim=-1)
                bound_excess = torch.maximum((sample['q']-scene.upper).clamp_min(0),
                                             (scene.lower-sample['q']).clamp_min(0))
                force, force_body = torch.linalg.vector_norm(sample['contact_force'], dim=-1).max(-1)
                higher = force > per_env['max_net_force_N']
                force_peak_body = torch.where(higher, force_body, force_peak_body)
                force_peak_step = torch.where(higher, sample['physics_step'], force_peak_step)
                for key, value in (('max_net_force_N', force), ('max_guitar_translation_m', drift),
                        ('max_guitar_rotation_rad', rotation), ('max_q_bound_excess_rad', bound_excess.max(-1).values),
                        ('max_abs_qd_rad_s', sample['qd'].abs().max(-1).values)):
                    per_env[key] = torch.maximum(per_env[key], value)
                row = dict(time_s=sample['physics_step'][0].to(torch.float64)/240.,
                    body_state=body[0], q=sample['q'][0], qd=sample['qd'][0], target=sample['target'][0],
                    action=action[0], base_relative_quaternion=relative[0], base_relative_rotvec=rotvec(relative)[0],
                    segment_net_force=sample['contact_force'][0, segments],
                    thumb_net_force=sample['contact_force'][0, thumb],
                    palm_net_force=sample['contact_force'][0, palm],
                    all_env_max_q_bound_excess_rad=bound_excess.max(),
                    all_env_max_abs_qd_rad_s=sample['qd'].abs().max(),
                    all_env_max_net_force_N=torch.linalg.vector_norm(sample['contact_force'], dim=-1).max(),
                    all_env_max_guitar_translation_m=drift.max(),
                    all_env_max_guitar_rotation_rad=rotation.max())
                samples.append({k: v.detach().cpu().numpy().copy() for k, v in row.items()})
            if args.video and (tick+1) % 2 == 0:
                scene.gym.step_graphics(scene.sim)
                scene.gym.render_all_camera_sensors(scene.sim)
                rgba = scene.gym.get_camera_image(scene.sim, scene.envs[0], camera, gymapi.IMAGE_COLOR)
                rgb = np.asarray(rgba).reshape(720, 1280, 4)[..., :3].copy()
                video.stdin.write(rgb.tobytes())
            if (tick+1) % 60 == 0:
                print('control_tick', tick+1, stage, 'codec_max', max_codec_error, flush=True)
            if tape is not None:
                thresholds = dict(guitar_displacement=bool((drift > .08).any()),
                    guitar_rotation=bool((rotation > .35).any()), joint_speed=bool((sample['qd'].abs() > 50).any()))
                if any(thresholds.values()):
                    stopped_by_safety = dict(control_tick=tick+1, physical_step=int(sample['physics_step'][0]),
                        reasons=[key for key, value in thresholds.items() if value])
                    break
        scene.reset(range(args.num_envs))
        controller.reset(range(args.num_envs), scene.snapshot())
        reset_check = dict(all_physics_clocks_zero=bool((scene.episode_steps == 0).all()),
            target_reference_max_error=float((controller.target-scene.reference105).abs().max()),
            prepared_q_restore_max_error=float((scene.q-initial_q).abs().max()),
            prepared_q_reference_difference=float((scene.q-scene.reference105).abs().max()), reset_calls=scene.reset_calls)
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error))
        raise
    finally:
        gymapi.acquire_gym = original_acquire
        hand_collision.left_hand_collision_properties = original_filters
        video_code, cleanup_errors = finish_video(video)
        for filename, rows in (('physics_env0000.npz', samples), ('controls_env0000.npz', controls)):
            if rows:
                try:
                    np.savez_compressed(out/filename, **{k: np.stack([x[k] for x in rows]) for k in rows[0]})
                except Exception as error:
                    cleanup_errors.append(filename+': '+repr(error))
        if samples:
            try:
                np.savez_compressed(out/'all_environment_extrema.npz',
                    **{k: v.cpu().numpy() for k, v in per_env.items()},
                    force_peak_body=force_peak_body.cpu().numpy(), force_peak_step=force_peak_step.cpu().numpy())
            except Exception as error:
                cleanup_errors.append('all_environment_extrema.npz: '+repr(error))
        if scene is not None:
            try:
                scene.close()
            except Exception as error:
                cleanup_errors.append('scene_close: '+repr(error))
        changed = [p for p, v in pins.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest() != v]
        report = dict(completed=failure is None and not changed and not cleanup_errors and video_code in (None, 0), failure=failure,
            num_envs=args.num_envs, controls=len(controls), physics_endpoints_per_environment=len(samples),
            recorded_environment=0, measured_hz=240, control_hz=60, max_codec_error_rad=max_codec_error,
            reset_check=reset_check, changed_inputs=changed, wall_s=time.monotonic()-started,
            video_encoder_exit_code=video_code, cleanup_errors=cleanup_errors, scene=scene.diagnostics if scene else None,
            scope=('No policy inference or training. Immutable A500 action-tape replay; q/body/target capture rows never written.'
                   if tape is not None else 'No training. Fixed small-action reversal and B target diagnostic.')+
                  ' Forces are native body net forces, not body-pair pressures.',
            H32='No operation/reset at 32-control boundaries; every target transition checked against previous bounded target',
            joint_names=scene.names if scene else [], body_names=scene.body_names if scene else [],
            stage_labels='Initial/B describe commanded configurations; measured force must determine loading',
            source_pin_scope='Prepared model/snapshot inputs and explicit physical code/assets; reward/environment/policy edits are independent',
            source_filters_diagnostic=args.source_filters_diagnostic,
            tape_path=str(args.tape.resolve()) if args.tape else None,
            tape_row_mapping='Capture row0 is t0, replay control n uses action row n+1; captured q/body/target never written',
            tape_LH21_reference_target_max_error_rad=tape_target_error if tape is not None else None,
            requested_controls=args.controls, protocol_completed=len(controls) == args.controls,
            stopped_by_safety=stopped_by_safety,
            tape_safety_scope='End-of-control hard guitar displacement .08m/rotation .35rad/joint speed50 only; support validity checked each physics tick. Not full song-contact safety or musical success.',
            all_environment_extrema={k: float(max(row[k] for row in samples)) for k in samples[0] if k.startswith('all_env_')} if samples else {},
            state_writes='One initial prepared reset and one explicit end-of-protocol reset check',
            video_time_mapping='frame n maps to physical time (n+1)/30s; no initial camera frame')
        (out/'report.json').write_text(json.dumps(report, indent=2, allow_nan=False))
        if failure is None and not report['completed']:
            raise RuntimeError('Diagnostic cleanup, input immutability, or output audit failed')


if __name__ == '__main__':
    main()
