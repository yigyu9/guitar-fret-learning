"""Actual GPU thumb-only rear approach/hold/release diagnostic, no policy.

Only five thumb targets are adjusted through the unchanged production action
codec. Native Jacobians provide small diagnostic requests, never state writes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time


def incremental_request(current, desired):
    return ((desired-current)*(60./4.)).clamp(-1., 1.)


def bounded_point_adjustment(jacobian, error, current, reference, lower, upper):
    """Small damped update; diagnostic excursion limits do not edit native limits."""
    import torch
    identity = torch.eye(3, device=jacobian.device, dtype=jacobian.dtype)
    delta = jacobian.transpose(-1, -2)@torch.linalg.solve(
        jacobian@jacobian.transpose(-1, -2)+1e-5*identity, error[..., None])
    delta = delta.squeeze(-1).clamp(-.00872664626, .00872664626)
    return torch.maximum(torch.minimum(current+delta,
        torch.minimum(upper, reference+.261799388)),
        torch.maximum(lower, reference-.261799388))


def point_jacobian(native, world_offset_from_com):
    """Native linear/angular Jacobian to a body-fixed point, SI units."""
    import torch
    return native[:, :3]+torch.cross(native[:, 3:].transpose(-1, -2),
        world_offset_from_com[:, None], dim=-1).transpose(-1, -2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--mode', choices=('hold', 'contact'), default='contact')
    parser.add_argument('--controls', type=int, default=900)
    parser.add_argument('--video', action='store_true')
    args = parser.parse_args()
    if not 60 <= args.controls <= 1800:
        raise ValueError('60..1800 diagnostic controls required')
    import isaacgym  # Native extension must precede NumPy and Torch.
    from isaacgym import gymapi
    import numpy as np
    import torch
    from guitar_learning.core.control import ACTIVE_NAMES
    from guitar_learning.gpu.scene import GpuScene
    from guitar_learning.gpu.control import BatchedController
    from guitar_learning.gpu.geometry import apply, conjugate, multiply, rotvec
    from guitar_learning.gpu.thumb_support import load_thumb_support, thumb_support_geometry
    from guitar_learning.gpu.wrist_region import load_wrist_region_track
    from guitar_learning.gpu.press_surface import load_press_surface
    from guitar_learning.runtime.prepared_reset_v1 import prepared_input_paths
    from guitar_learning.tool.validation.hand_contact_probe import GraphicsGym, physics_source_paths, finish_video

    root = Path('/home/ajou/yigyu/3')
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    paths = physics_source_paths(root) | set(prepared_input_paths())
    paths.update((Path(__file__).resolve(), root/'guitar_learning/gpu/thumb_support.py',
        root/'guitar_learning/gpu/wrist_region.py', root/'guitar_learning/gpu/press_surface.py'))
    patch = load_thumb_support()
    paths.update(Path(p) for p in patch['contract']['source_sha256'])
    bundle = root/'data/song_bundles/05_BN2-131-B_solo'
    track = load_wrist_region_track(bundle, load_press_surface([0], [1]))
    paths.update(Path(p) for p in track['contract']['source_sha256'])
    pins = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
    (out/'inputs_before.json').write_text(json.dumps(pins, indent=2))
    center = .5*(track['lower_G_m'][0][1]+track['upper_G_m'][0][1])
    torch.set_num_threads(1)
    torch.manual_seed(7)
    original_acquire = gymapi.acquire_gym
    scene, video, rows, joints = None, None, [], []
    failure, stage, stage_start, contact_ticks = None, 'initial_hold', 0., 0
    transitions, frames, max_codec = [], 0, 0.
    started = time.monotonic()
    try:
        if args.video:
            gymapi.acquire_gym = lambda: GraphicsGym(original_acquire())
        try:
            scene = GpuScene(1, 'left', out=out/'scene')
        finally:
            gymapi.acquire_gym = original_acquire
        controller = BatchedController(scene)
        snapshot = scene.snapshot()
        controller.reset([0], snapshot)
        joints = [scene.names.index('LH:'+name) for name in
            ('thumb1_x', 'thumb1_y', 'thumb1_z', 'thumb2', 'thumb3')]
        actions = [ACTIVE_NAMES.index(scene.names[j]) for j in joints]
        thumb = scene.body_names.index('human/LH:thumb3')
        guitar = len(scene.human_bodies)
        initial_guitar = snapshot['body_state'][:, guitar, :7].clone()
        reference = controller.target[:, joints].clone()
        desired = reference.clone()
        device = scene.device
        local = torch.as_tensor(patch['points_local'], dtype=scene.q.dtype, device=device)
        normals = torch.as_tensor(patch['normals_local'], dtype=scene.q.dtype, device=device)
        valid = torch.as_tensor(patch['valid'], device=device)
        rear = torch.as_tensor(patch['rear_vertices'], dtype=scene.q.dtype, device=device)
        plane = torch.as_tensor(patch['plane'], dtype=scene.q.dtype, device=device)
        center_t = torch.tensor([center], device=device)
        joint_ids = torch.tensor(joints, device=device)
        camera = None
        if args.video:
            props = gymapi.CameraProperties()
            props.width, props.height, props.horizontal_fov = 1280, 720, 55.
            camera = scene.gym.create_camera_sensor(scene.envs[0], props)
            if camera < 0:
                raise RuntimeError('Native camera unavailable')
            scene.gym.set_camera_location(camera, scene.envs[0], gymapi.Vec3(-.65, .22, .84),
                                          gymapi.Vec3(-.27, -.09, .66))
            for i, name in enumerate(scene.human_bodies):
                if name.startswith('LH:thumb'):
                    scene.gym.set_rigid_body_color(scene.envs[0], scene.actors[0][0], i,
                        gymapi.MESH_VISUAL, gymapi.Vec3(.94, .24, .27))
            video = subprocess.Popen(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n',
                '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1280x720', '-r', '30', '-i', '-',
                '-an', '-c:v', 'libx264', '-threads', '2', '-preset', 'fast', '-crf', '18',
                '-pix_fmt', 'yuv420p', str(out/'native_thumb_oblique.mp4')], stdin=subprocess.PIPE)

        def measure(sample):
            body = sample['body_state']
            t, g = body[:, thumb], body[:, guitar]
            world = t[:, None, :3]+apply(t[:, None, 3:7], local[None])
            points = apply(conjugate(g[:, None, 3:7]), world-g[:, None, :3])
            facing = apply(conjugate(g[:, None, 3:7]), apply(t[:, None, 3:7], normals[None]))
            force_g = apply(conjugate(g[:, 3:7]), sample['contact_force'][:, thumb])
            measured = thumb_support_geometry(points, facing, valid, center_t, rear, plane,
                                               net_force_guitar=force_g)
            return measured, force_g

        for tick in range(args.controls):
            now = tick/60.
            measurement, force_g = measure(snapshot)
            next_stage = None
            if args.mode == 'contact':
                if stage == 'initial_hold' and now >= 1.:
                    next_stage = 'approach'
                elif stage in ('approach', 'reapproach') and contact_ticks >= 24:
                    next_stage = 'contact_hold' if stage == 'approach' else 'final_hold'
                elif stage == 'contact_hold' and now-stage_start >= 1.5:
                    next_stage = 'release'
                elif stage == 'release' and now-stage_start >= 1.5:
                    next_stage = 'reapproach'
                elif stage == 'final_hold' and now-stage_start >= 1.5:
                    next_stage = 'completed_hold'
            if next_stage:
                transitions.append(dict(time_s=now, previous=stage, next=next_stage,
                    thumb_target_rad=desired[0].tolist()))
                stage, stage_start, contact_ticks = next_stage, now, 0
            if stage in ('approach', 'reapproach', 'release') and tick % 6 == 0:
                t = snapshot['body_state'][:, thumb]
                g = snapshot['body_state'][:, guitar]
                p_local = local[measurement['sample_index'].clamp_min(0)]
                # Native jacobian linear rows are at the human body COM.
                native = snapshot['jacobian'][:, thumb-1]
                offset = apply(t[:, 3:7], p_local-scene.com[thumb])
                point_j = point_jacobian(native, offset)
                goal_gap = .003 if stage == 'release' else .0001
                normal = plane[:3]/torch.linalg.vector_norm(plane[:3])
                delta_g = measurement['delta']+goal_gap*normal
                error_world = apply(g[:, 3:7], delta_g)
                if float(torch.linalg.vector_norm(force_g)) < 2. or stage == 'release':
                    desired = bounded_point_adjustment(point_j[:, :, joints], error_world,
                        controller.target[:, joints], reference, scene.lower[joints], scene.upper[joints])
            action = torch.zeros(1, 39, device=device)
            action[:, actions] = incremental_request(controller.target[:, joints], desired)
            before = controller.target[:, joints].clone()
            target = controller.targets(action, snapshot)
            expected = (before+action[:, actions]*(4./60.)).clamp(scene.lower[joints], scene.upper[joints])
            max_codec = max(max_codec, float((target[:, joints]-expected).abs().max()))
            if max_codec > 2e-6:
                raise AssertionError('Diagnostic bypassed production incremental codec')
            for _ in range(4):
                effort = controller.efforts(snapshot)
                if not bool(controller.diagnostics['valid'].all()):
                    raise RuntimeError('Existing finite support invalid')
                snapshot = scene.step(target, effort)
                if not all(bool(torch.isfinite(snapshot[k]).all()) for k in
                           ('q', 'qd', 'body_state', 'contact_force')):
                    raise FloatingPointError('Nonfinite native response')
                measurement, force_g = measure(snapshot)
                contact_ticks = contact_ticks+1 if bool(measurement['contact_candidate'][0]) else 0
                t = snapshot['body_state'][:, thumb]
                selected_local = local[measurement['sample_index'].clamp_min(0)]
                com_offset = apply(t[:, 3:7], selected_local-scene.com[thumb])
                point_j = point_jacobian(snapshot['jacobian'][:, thumb-1], com_offset)
                velocity_predicted = (point_j@snapshot['qd'][..., None]).squeeze(-1)
                velocity_measured = t[:, 7:10]+torch.cross(t[:, 10:13], com_offset, dim=-1)
                g = snapshot['body_state'][:, guitar]
                drift = torch.linalg.vector_norm(g[:, :3]-initial_guitar[:, :3], dim=-1)
                rotation = torch.linalg.vector_norm(rotvec(multiply(
                    conjugate(initial_guitar[:, 3:]), g[:, 3:7])), dim=-1)
                row = dict(time_s=snapshot['physics_step'][0].double()/240.,
                    q=snapshot['q'][0], qd=snapshot['qd'][0], target=snapshot['target'][0],
                    body_state=snapshot['body_state'][0], contact_force=snapshot['contact_force'][0],
                    action=action[0], thumb_force_G=force_g[0],
                    thumb_point_jacobian=point_j[0, :, joints],
                    thumb_point_velocity_predicted=velocity_predicted[0],
                    thumb_point_velocity_measured=velocity_measured[0],
                    guitar_translation=drift[0], guitar_rotation=rotation[0])
                row.update({'thumb_'+k:v[0] for k,v in measurement.items()})
                row = {k:v.detach().cpu().numpy().copy() for k,v in row.items()}
                row['stage'] = stage
                rows.append(row)
                if float(drift.max()) > .08 or float(rotation.max()) > .35 or float(snapshot['qd'].abs().max()) > 50:
                    raise RuntimeError('Existing physical excursion threshold exceeded')
            if args.video and (tick+1) % 2 == 0:
                scene.gym.step_graphics(scene.sim)
                scene.gym.render_all_camera_sensors(scene.sim)
                rgba = scene.gym.get_camera_image(scene.sim, scene.envs[0], camera, gymapi.IMAGE_COLOR)
                video.stdin.write(np.asarray(rgba).reshape(720, 1280, 4)[..., :3].copy().tobytes())
                frames += 1
            if (tick+1) % 60 == 0:
                print('tick', tick+1, stage, 'gap', float(measurement['signed_gap'][0]),
                    'force_G', force_g[0].tolist(), 'candidate', bool(measurement['contact_candidate'][0]), flush=True)
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error))
        raise
    finally:
        gymapi.acquire_gym = original_acquire
        code, cleanup = finish_video(video)
        if rows:
            try:
                np.savez_compressed(out/'physics_env0000.npz', **{k:np.stack([r[k] for r in rows]) for k in rows[0]})
            except Exception as error:
                cleanup.append('raw_save: '+repr(error))
        if scene:
            try:
                scene.close()
            except Exception as error:
                cleanup.append('scene_close: '+repr(error))
        changed = [p for p,h in pins.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest() != h]
        stages = {}
        for name in sorted({r['stage'] for r in rows}):
            selected_rows = [r for r in rows if r['stage'] == name]
            load = np.array([r['thumb_normal_load'] for r in selected_rows])
            gap = np.array([r['thumb_signed_gap'] for r in selected_rows])
            stages[name] = dict(seconds=len(selected_rows)/240.,
                candidate_fraction=float(np.mean([r['thumb_contact_candidate'] for r in selected_rows])),
                normal_load_mean_N=float(load.mean()), normal_load_max_N=float(load.max()),
                gap_min_m=float(gap.min()), gap_max_m=float(gap.max()),
                gap_final_m=float(gap[-1]))
        passed = dict(first_contact='contact_hold' in stages,
            first_hold=stages.get('contact_hold', {}).get('seconds', 0) >= 1.49 and
                stages.get('contact_hold', {}).get('candidate_fraction', 0) >= .9,
            release=stages.get('release', {}).get('seconds', 0) >= 1.49 and
                stages.get('release', {}).get('candidate_fraction', 1) < .1 and
                stages.get('release', {}).get('gap_final_m', 0) >= .002,
            recontact='final_hold' in stages,
            final_hold=stages.get('final_hold', {}).get('seconds', 0) >= 1.49 and
                stages.get('final_hold', {}).get('candidate_fraction', 0) >= .9)
        velocity_residual = np.array([r['thumb_point_velocity_predicted']-
            r['thumb_point_velocity_measured'] for r in rows])
        (out/'report.json').write_text(json.dumps(dict(completed=failure is None and not changed and not cleanup
                and code in (None, 0), failure=failure, changed_inputs=changed, cleanup_errors=cleanup,
            mode=args.mode, measured_hz=240, frames=frames, video_encoder_exit=code,
            physical_endpoints=len(rows), transitions=transitions, final_stage=stage,
            measured_stages=stages, protocol_passed=passed,
            all_contact_protocol_conditions_passed=all(passed.values()) if args.mode == 'contact' else None,
            point_jacobian_velocity_rms_m_s=float(np.sqrt(np.mean(velocity_residual**2))) if rows else None,
            contact_confirmation='24 consecutive240Hz candidate endpoints before hold; candidate is source samepoint geometry plus native normal resultant, not a body-pair certificate',
            wall_s=time.monotonic()-started, codec_max_error_rad=max_codec,
            native_joint_names=scene.names if scene else [], body_names=scene.body_names if scene else [],
            thumb_joint_indices=joints if scene else [], fixed_work_center_y_m=center,
            scope='Thumb5 target requests only; every other policy channel0, production finite lower/right/chest support; free gravity guitar. Native 240Hz forces are body resultants, not contact-pair pressure. Jacobian request is a diagnostic, not learned policy or production controller.',
            state_setters='Prepared episode boundary reset only',
            diagnostic_request_limits='Per update0.5degree; initial thumb target+/-15degree, unchanged full native limits and4rad/s production codec',
            scene=scene.diagnostics if scene else None), indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
