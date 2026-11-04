"""고정/자유 pelvis에서 같은 팔 동작을 실행하는 영상 진단. 학습 소스는 수정하지 않는다."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]


def write(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def run(out):
    import isaacgym
    from isaacgym import gymapi
    import numpy as np
    import torch
    from PIL import Image, ImageDraw, ImageFont
    from guitar_learning.gpu.scene import GpuScene
    from guitar_learning.gpu.control import BatchedController, apply, conjugate, multiply
    from guitar_learning.runtime.prepared_reset_v1 import prepared_input_paths, BASELINE_CONFIG
    from guitar_learning.native.paths import pin
    from guitar_learning.training.training_log_io import active_source_paths, digest

    torch.set_num_threads(1)
    out = Path(out).resolve()
    records = out/'기록'
    videos = out/'video'
    records.mkdir(exist_ok=True)
    videos.mkdir(exist_ok=True)
    sources = active_source_paths(ROOT/'guitar_learning') | prepared_input_paths() | {Path(__file__)}
    sources.update((ROOT/'guitar_learning/assets').rglob('*.json'))
    sources.update((ROOT/'guitar_learning/assets/gpu_rigid_guitar_v1').glob('*'))
    pins = pin(BASELINE_CONFIG, extra={p for p in sources if p.is_file()})
    write(records/'입력봉인.json', pins)

    class NativeProxy:
        def __init__(self, native, free):
            self.native, self.free = native, free
            self.loads = []

        def __getattr__(self, name):
            return getattr(self.native, name)

        def create_sim(self, compute, graphics, engine, params):
            return self.native.create_sim(compute, compute, engine, params)

        def load_asset(self, sim, folder, filename, options):
            # GpuScene의 첫 번째 자산만 인체다. 기타/의자는 동일하다.
            human = len(self.loads) == 0
            original = bool(options.fix_base_link)
            if human:
                options.fix_base_link = not self.free
            self.loads.append(dict(path=str(Path(folder)/filename), human=human,
                original_fixed=original, requested_fixed=bool(options.fix_base_link)))
            return self.native.load_asset(sim, folder, filename, options)

    class MovingPelvisController(BatchedController):
        def _lower_fk(self, q):
            positions, rotations = super()._lower_fk(q)
            # 원래 FK의 고정 pelvis 출력을 현재 pelvis 좌표계로 옮긴다. 가상 root 힘은 없다.
            initial = self.initial_bodies[self.bodies.index('Pelvis')]
            actual = self.scene.snapshot()['body_state'][:, self.bodies.index('Pelvis')]
            delta = multiply(actual[:, 3:7], conjugate(initial[3:7]).expand(q.shape[0], -1))
            positions = actual[:, None, :3]+apply(delta[:, None], positions-initial[:3])
            rotations = multiply(delta[:, None], rotations)
            return positions, rotations

    font_path = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
    font = ImageFont.truetype(font_path, 22)
    summaries = []
    for free in (False, True):
        for movement in ('hold', 'right', 'left'):
            tag = ('free' if free else 'fixed')+'_'+movement
            report_path = records/(tag+'.json')
            if report_path.exists():
                raise FileExistsError(str(report_path))
            scene = encoder = None
            proxy = None
            rows = []
            report = dict(condition=tag, completed=False, failure=None,
                human_root_fixed=not free, guitar_root_fixed=False,
                state_writes='one initial prepared boundary; no mid-episode reset',
                root_external_force=False, duration_s=12., physics_hz=240, control_hz=60,
                perturbation=dict(elbow_y_deg=12, wrist_x_deg=20, wrist_z_deg=15,
                                  frequency_hz=1., active_interval_s=[2., 10.]))
            native_acquire = gymapi.acquire_gym
            try:
                proxy = NativeProxy(native_acquire(), free)
                gymapi.acquire_gym = lambda: proxy
                try:
                    scene = GpuScene(1, 'left', out=None)
                finally:
                    gymapi.acquire_gym = native_acquire
                raw_shape = list(scene.jacobian.shape)
                expected = (1, len(scene.human_bodies) if free else len(scene.human_bodies)-1,
                            6, 111 if free else 105)
                if tuple(raw_shape) != expected:
                    raise ValueError('Unexpected native Jacobian layout: '+str(raw_shape))
                if free:
                    # native열은root6+joint105. 부모 제어기가 pelvis0행을 다시 붙인다.
                    scene.jacobian = scene.jacobian[:, 1:, :, 6:]
                controller = MovingPelvisController(scene)
                sample = scene.snapshot()
                controller.reset(torch.tensor([0], device=scene.device), sample)
                names = scene.names
                pelvis = scene.human_bodies.index('Pelvis')
                head = scene.human_bodies.index('Head')
                wrist = scene.human_bodies.index(('R_' if movement == 'right' else 'L_')+'Wrist')
                cameras = []
                views = (((0., 3.6, 1.35), (-.1, 0., .65)),
                         ((2.8, 2.3, 1.45), (-.1, 0., .65)))
                for position, target in views:
                    props = gymapi.CameraProperties()
                    props.width, props.height, props.horizontal_fov = 640, 720, 45.
                    camera = scene.gym.create_camera_sensor(scene.envs[0], props)
                    if camera < 0:
                        raise RuntimeError('Camera creation failed')
                    scene.gym.set_camera_location(camera, scene.envs[0], gymapi.Vec3(*position),
                                                  gymapi.Vec3(*target))
                    cameras.append(camera)
                encoder = subprocess.Popen(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n',
                    '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1280x720', '-r', '30', '-i', '-',
                    '-an', '-c:v', 'libx264', '-threads', '2', '-preset', 'fast', '-crf', '20',
                    '-pix_fmt', 'yuv420p', str(videos/(tag+'.mp4'))], stdin=subprocess.PIPE)
                initial_body = sample['body_state'][0].clone()
                initial_up = apply(initial_body[pelvis, 3:7],
                                   torch.tensor([0., 0., 1.], device=scene.device))
                initial_guitar = initial_body[len(scene.human_bodies), :3].clone()
                initial_root = scene._roots[0, 0].clone()
                target_positions, body_samples = [], []
                for tick in range(720):
                    t = tick/60.
                    wave = 0.
                    if 2. < t < 10. and movement != 'hold':
                        envelope = min(1., t-2., 10.-t)
                        envelope = .5-.5*math.cos(math.pi*max(envelope, 0.))
                        wave = envelope*math.sin(2*math.pi*(t-2.))
                    action = torch.zeros(1, 39, device=scene.device)
                    previous_targets = controller.target.clone()
                    target = controller.targets(action, sample).clone()
                    if movement != 'hold':
                        prefix = 'R_' if movement == 'right' else 'L_'
                        for suffix, amplitude in (('Elbow_y', 12.), ('Wrist_x', 20.), ('Wrist_z', 15.)):
                            j = names.index(prefix+suffix)
                            request = controller.reference[j]+math.radians(amplitude)*wave
                            previous = previous_targets[0, j]
                            target[0, j] = torch.clamp(torch.as_tensor(request, device=scene.device),
                                min=previous-controller.rate[j]/60., max=previous+controller.rate[j]/60.)
                    target = torch.maximum(torch.minimum(target, scene.upper), scene.lower)
                    controller.target.copy_(target)
                    for _ in range(4):
                        efforts = controller.efforts(sample)
                        if not torch.isfinite(efforts).all():
                            raise FloatingPointError('Nonfinite joint effort')
                        sample = scene.step(target, efforts)
                    body = sample['body_state'][0]
                    up = apply(body[pelvis, 3:7], torch.tensor([0., 0., 1.], device=scene.device))
                    tilt = torch.acos((up*initial_up).sum().clamp(-1, 1))*180/math.pi
                    root = scene._roots[0, 0]
                    row = dict(t_s=(tick+1)/60., root_delta_m=float(torch.linalg.vector_norm(root[:3]-initial_root[:3])),
                        root_delta_xy_m=float(torch.linalg.vector_norm(root[:2]-initial_root[:2])),
                        pelvis_z_m=float(body[pelvis, 2]), head_z_m=float(body[head, 2]),
                        pelvis_tilt_deg=float(tilt), root_speed_m_s=float(torch.linalg.vector_norm(root[7:10])),
                        guitar_delta_m=float(torch.linalg.vector_norm(body[len(scene.human_bodies), :3]-initial_guitar)),
                        wrist_delta_m=float(torch.linalg.vector_norm(body[wrist, :3]-initial_body[wrist, :3])),
                        max_joint_speed_rad_s=float(sample['qd'].abs().max()),
                        controller_valid=bool(controller.diagnostics['valid'].all()),
                        shake_wave=wave)
                    rows.append(row)
                    if tick % 2 == 1:
                        scene.gym.step_graphics(scene.sim)
                        scene.gym.render_all_camera_sensors(scene.sim)
                        frames = [np.asarray(scene.gym.get_camera_image(scene.sim, scene.envs[0], cam,
                            gymapi.IMAGE_COLOR)).reshape(720, 640, 4)[..., :3] for cam in cameras]
                        frame = Image.fromarray(np.concatenate(frames, axis=1))
                        draw = ImageDraw.Draw(frame)
                        draw.rectangle((0, 0, 1280, 95), fill=(18, 22, 27))
                        label = {'hold':'정지', 'right':'오른팔 흔들기', 'left':'왼팔 흔들기'}[movement]
                        draw.text((15, 8), ('ROOT 해제' if free else 'ROOT 고정')+' / '+label+
                                  ' / {:.2f}s'.format(row['t_s']), font=font, fill='white')
                        draw.text((15, 44), 'root 이동 {:.1f}cm / pelvis 기울기 {:.1f}° / 높이 {:.2f}m'.format(
                            row['root_delta_m']*100, row['pelvis_tilt_deg'], row['pelvis_z_m']),
                            font=font, fill=(255, 210, 100))
                        encoder.stdin.write(np.asarray(frame).tobytes())
                        body_samples.append(body.detach().cpu().numpy().copy())
                        target_positions.append(target.detach().cpu().numpy().copy())
                report.update(completed=True, native_jacobian_shape=raw_shape, asset_requests=proxy.loads,
                    native_steps=scene.physics_steps, reset_calls=scene.reset_calls,
                    max_root_delta_m=max(r['root_delta_m'] for r in rows),
                    max_root_delta_xy_m=max(r['root_delta_xy_m'] for r in rows),
                    max_pelvis_tilt_deg=max(r['pelvis_tilt_deg'] for r in rows),
                    min_pelvis_z_m=min(r['pelvis_z_m'] for r in rows),
                    min_head_z_m=min(r['head_z_m'] for r in rows),
                    max_guitar_delta_m=max(r['guitar_delta_m'] for r in rows),
                    max_wrist_delta_m=max(r['wrist_delta_m'] for r in rows),
                    controller_invalid_ticks=sum(not r['controller_valid'] for r in rows),
                    initial_pelvis_z_m=float(initial_body[pelvis, 2]),
                    final=rows[-1])
                np.savez_compressed(records/(tag+'_native.npz'),
                    body_state=np.asarray(body_samples), targets105=np.asarray(target_positions))
            except BaseException as exc:
                report['failure'] = repr(exc)
                raise
            finally:
                gymapi.acquire_gym = native_acquire
                if encoder is not None:
                    encoder.stdin.close()
                    code = encoder.wait(timeout=60)
                    report['encoder_exit_code'] = code
                    report['completed'] = report['completed'] and code == 0
                if scene is not None:
                    scene.close()
                write(report_path, report)
                with (records/(tag+'.jsonl')).open('w') as stream:
                    for row in rows:
                        stream.write(json.dumps(row, allow_nan=False)+'\n')
            summaries.append(report)
            print(json.dumps(dict(condition=tag, completed=report['completed'],
                root_m=report['max_root_delta_m'], tilt_deg=report['max_pelvis_tilt_deg']), ensure_ascii=False), flush=True)
    changed = [name for name, sha in pins.items() if digest(name) != sha]
    write(records/'총괄.json', dict(completed=not changed and all(r['completed'] for r in summaries),
        changed_inputs=changed, conditions=summaries,
        limitations=['각조건1회12초의진단이며학습된균형정책을사용하지않음',
                     '실제자유root와native joint105Jacobian어댑터·현재pelvis발FK사용',
                     '의자·지면접촉유지, 기타외력·root강제복원·중간reset없음']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    run(parser.parse_args().out)
