"""Strict finger-skill checkpoint capture with native env0 hand/body cameras."""
import argparse
import copy
import json
import math
from pathlib import Path
import subprocess
import time


CAMERAS = dict(hand=((-.65, .22, .84), (-.27, -.09, .66)),
               fullbody=((-.10, 2.7, 1.1), (-.15, -.10, .65)))
COLORS = dict(thumb=(.94, .24, .27), index=(.18, .52, .87), middle=(.10, .67, .49),
              ring=(.94, .57, .18), pinky=(.63, .38, .82))


def _create_cameras(scene, gymapi):
    cameras = {}
    for index, name in enumerate(scene.human_bodies):
        for finger, color in COLORS.items():
            if name.startswith('LH:'+finger):
                scene.gym.set_rigid_body_color(scene.envs[0], scene.actors[0][0], index,
                                               gymapi.MESH_VISUAL, gymapi.Vec3(*color))
    for name, (position, target) in CAMERAS.items():
        props = gymapi.CameraProperties()
        props.width, props.height, props.horizontal_fov = 1280, 720, 55.
        camera = scene.gym.create_camera_sensor(scene.envs[0], props)
        if camera < 0:
            raise RuntimeError('Native '+name+' camera unavailable')
        scene.gym.set_camera_location(camera, scene.envs[0], gymapi.Vec3(*position), gymapi.Vec3(*target))
        cameras[name] = camera
    return cameras


def _encoder(path):
    return subprocess.Popen(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n',
        '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1280x720', '-r', '30', '-i', '-',
        '-an', '-c:v', 'libx264', '-threads', '2', '-preset', 'fast', '-crf', '18',
        '-pix_fmt', 'yuv420p', str(path)], stdin=subprocess.PIPE)


class _EnvZeroCapture:
    """Record only env0's first episode, before the collector resets done rows."""
    def __init__(self, pool, gymapi, numpy, cameras, videos):
        self.pool, self.gymapi, self.np = pool, gymapi, numpy
        self.cameras, self.videos = cameras, videos
        self.samples, self.frame_times_s = [], []
        self.episode = None

    def record(self, tick, reward, cost, terminated, truncated, episodes):
        if self.episode is not None:
            return
        scene = self.pool.scene
        snapshot = scene.snapshot()
        row = {key: snapshot[key][0].detach().cpu().numpy().copy()
               for key in ('q', 'qd', 'target', 'body_state', 'contact_force', 'physics_step')}
        control_tick = len(self.samples)+1
        if int(row['physics_step']) != 4*control_tick:
            raise RuntimeError('env0 capture crossed a reset or skipped a native control endpoint')
        row.update(action=self.pool.environment.action[0].detach().cpu().numpy().copy(),
                   control_tick=self.np.asarray(control_tick), time_s=self.np.asarray(control_tick/60.))
        fields = getattr(self.pool, 'contract', {}).get('observation', {}).get('fields', [])
        timers = [i for i, name in enumerate(fields) if name.startswith('wrist_termination.')]
        if timers:
            row['wrist_termination_state'] = self.pool.observation['state'][0, timers].detach().cpu().numpy().copy()
        self.samples.append(row)
        if control_tick % 2 == 0:
            scene.gym.step_graphics(scene.sim)
            scene.gym.render_all_camera_sensors(scene.sim)
            for name, camera in self.cameras.items():
                pixels = scene.gym.get_camera_image(scene.sim, scene.envs[0], camera, self.gymapi.IMAGE_COLOR)
                rgb = self.np.asarray(pixels).reshape(720, 1280, 4)[..., :3].copy()
                self.videos[name].stdin.write(rgb.tobytes())
            self.frame_times_s.append(control_tick/60.)
        for episode in episodes:
            if episode['env_id'] == 0:
                self.episode = copy.deepcopy(episode)
                break
        if bool(terminated[0] or truncated[0]) and self.episode is None:
            raise RuntimeError('env0 terminated without a completed episode record')


def render(checkpoint, out, *, scope='full_song', num_envs=None):
    # Isaac's native extension must load before Torch or NumPy.
    import isaacgym
    from isaacgym import gymapi
    import numpy as np
    import torch
    from guitar_learning.training.gpu_pool import GpuPool
    from guitar_learning.training.decision_ppo import DecisionPPOTrainer
    from guitar_learning.training.finger_decisions import DecisionCollector
    from guitar_learning.training.finger_skill_runner import (
        resume_schema, _policy, _validate_pins, _pins, _DeterministicPolicy)
    from guitar_learning.training.ppo import PPOConfig
    from guitar_learning.training.recording import digest, write
    from guitar_learning.tool.validation.hand_contact_probe import GraphicsGym, finish_video

    checkpoint, out = Path(checkpoint), Path(out).resolve()
    if not checkpoint.is_absolute() or not checkpoint.is_file():
        raise ValueError('existing absolute checkpoint path required')
    checkpoint = checkpoint.resolve()
    if scope not in ('full_song', 'phrases'):
        raise ValueError('full_song/phrases scope required')
    payload = torch.load(checkpoint, map_location='cpu', weights_only=False)
    metadata = payload.get('metadata') if isinstance(payload, dict) else None
    if (not isinstance(metadata, dict) or
            metadata.get('schema') != resume_schema(metadata.get('settings', {}))):
        raise ValueError('own finger-skill checkpoint metadata required')
    _validate_pins(metadata)
    settings = copy.deepcopy(metadata['settings'])
    if num_envs is not None:
        if type(num_envs) is not int or not 1 <= num_envs <= 1024:
            raise ValueError('num_envs must be 1..1024')
        settings['num_envs'] = num_envs
    out.mkdir(parents=True, exist_ok=False)
    write(out/'settings.json', settings)
    pins = _pins(settings, out, [checkpoint])
    write(out/'inputs_before.json', pins)
    torch.set_num_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    original = gymapi.acquire_gym
    pool, capture, policy = None, None, None
    videos, codes, cleanup_errors = {}, {}, []
    failure, unchanged = None, False
    started = time.monotonic()
    try:
        gymapi.acquire_gym = lambda: GraphicsGym(original())
        try:
            pool = GpuPool(settings, out/'scene')
        finally:
            gymapi.acquire_gym = original
        write(out/'training_contract.json', pool.contract)
        policy = _policy(settings, pool)
        trainer = DecisionPPOTrainer(policy, PPOConfig(**settings['ppo']))
        trainer.load(checkpoint)  # Strict actual native pool identity, including control.
        model_before = {key: value.detach().clone() for key, value in policy.state_dict().items()}
        pool.environment.set_evaluation(enabled=True, full_song=scope == 'full_song')
        pool.observation = pool.reset()[0]
        cameras = _create_cameras(pool.scene, gymapi)
        for name in cameras:
            videos[name] = _encoder(out/(name+'.mp4'))
        capture = _EnvZeroCapture(pool, gymapi, np, cameras, videos)
        collector = DecisionCollector(_DeterministicPolicy(policy), pool,
            gamma=trainer.config.gamma, cost_gamma=trainer.config.cost_gamma)
        elapsed = 0
        maximum = math.ceil(pool.environment.task.duration_s*60)+settings['horizon']
        with torch.no_grad():
            while capture.episode is None and elapsed < maximum:
                collector.collect(settings['horizon'], transition_callback=capture.record,
                                  policy_version=trainer.updates)
                elapsed += settings['horizon']
        if capture.episode is None:
            raise RuntimeError('env0 did not finish within the original score duration')
        unchanged = all(torch.equal(value, model_before[key]) for key, value in policy.state_dict().items())
        if not unchanged:
            raise AssertionError('Evaluation changed policy weights or buffers')
        with (out/'episode_env0000.json').open('x') as stream:
            json.dump(capture.episode, stream, indent=2, allow_nan=False)
        write(out/'capture_metadata.json', dict(schema='guitar_learning.finger_skill_video.v1',
            checkpoint=str(checkpoint), checkpoint_sha256=digest(checkpoint), phase=policy.phase, scope=scope,
            environment=0, selection='predeclared env0 first episode; not selected by performance',
            actual_achieved_notes=capture.episode['song']['left_success_count'],
            actual_target_count=capture.episode['song']['target_count'],
            joint_names=pool.scene.names, body_names=pool.scene.body_names,
            native_pixels=True, width=1280, height=720, video_fps=30, capture_hz=60, source_physics_hz=240,
            frames=len(capture.frame_times_s), frame_times_s=capture.frame_times_s,
            video_duration_s=len(capture.frame_times_s)/30., captured_control_duration_s=len(capture.samples)/60.,
            first_physics_step=int(capture.samples[0]['physics_step']),
            last_physics_step=int(capture.samples[-1]['physics_step']),
            held_finger_phase=policy.phase == 'F', maximum_finger_decision_ticks=settings['finger_skill']['hold_ticks'],
            frame_mapping='frame n maps to control endpoint 2*(n+1); no t0 frame; odd final endpoint has no frame',
            control='checkpoint DecisionCollector contract; deterministic means; frozen support recomputed each60Hz',
            no_reset_frames=True, training_updates=0,
            termination_observation=dict(
                fields=[name for name in pool.contract['observation']['fields'] if name.startswith('wrist_termination.')],
                scales=[scale for name, scale in zip(pool.contract['observation']['fields'],
                    pool.contract['observation']['scales']) if name.startswith('wrist_termination.')],
                values='normalized policy observation at the same actual control endpoint')))
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error))
        raise
    finally:
        gymapi.acquire_gym = original
        for name, process in videos.items():
            code, errors = finish_video(process)
            codes[name] = code
            cleanup_errors.extend(dict(component=name, message=error) for error in errors)
        if capture and capture.samples:
            try:
                filename = 'poses_env0000.npz' if failure is None else 'partial_poses_env0000.npz'
                np.savez_compressed(out/filename, **{key: np.stack([row[key] for row in capture.samples])
                                                       for key in capture.samples[0]})
            except BaseException as error:
                cleanup_errors.append(dict(component='raw_capture', message=str(error)))
        if pool:
            try:
                pool.close()
            except BaseException as error:
                cleanup_errors.append(dict(component='scene_close', message=str(error)))
        changed = [path for path, value in pins.items() if not Path(path).is_file() or digest(path) != value]
        audit = pool.scene.diagnostics if pool and pool.scene else None
        closed = bool(audit and audit.get('closed'))
        lifecycle = bool(closed and audit.get('physx_use_gpu') and audit.get('use_gpu_pipeline') and
                         audit.get('simulator_count') == 1 and audit.get('environment_count') == settings['num_envs'])
        complete = (failure is None and unchanged and lifecycle and not changed and not cleanup_errors and
                    len(codes) == 2 and all(code == 0 for code in codes.values()))
        report = dict(schema='guitar_learning.finger_skill_render.v1', completed=complete, failure=failure,
            checkpoint=str(checkpoint), checkpoint_sha256=digest(checkpoint), phase=policy.phase if policy else None,
            scope=scope, recorded_environment=0, first_episode_only=True, policy_unchanged=unchanged,
            native_pixels=True, frames=len(capture.frame_times_s) if capture else 0,
            encoding_exit_codes=codes, cleanup_errors=cleanup_errors, source_pins_unchanged=not changed,
            changed_inputs=changed, source_checkpoint_pins_validated=True, scene_closed=closed,
            lifecycle_verified=lifecycle, gpu_scene=audit,
            training_updates=0, wall_s=time.monotonic()-started,
            episode=capture.episode if capture else None)
        write(out/'report.json', report)
        if failure is None and not complete:
            raise RuntimeError('Render encoding, source, policy or scene audit failed; see report.json')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--scope', choices=('full_song', 'phrases'), default='full_song')
    parser.add_argument('--num-envs', type=int)
    args = parser.parse_args()
    render(args.checkpoint, args.out, scope=args.scope, num_envs=args.num_envs)


if __name__ == '__main__':
    main()
