"""Render saved native body transforms, without integration or pose interpolation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

os.environ.setdefault('MUJOCO_GL', 'osmesa')
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from guitar_learning.native.initial_pose_video60_v1.static_visual_v7 import (
    asset_paths, build_model, set_body_poses, add_strings)

FONT = Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
WHITE, MUTED, RED = (239, 244, 249), (180, 195, 210), (255, 115, 106)
REASONS = {'guitar_displacement': '기타 이동 > 8cm', 'guitar_rotation': '기타 회전 > 0.35rad',
           'foot_displacement': '발 이동 > 4cm', 'support_lost': '기타 지지 접촉 소실',
           'ground_contact_lost': '발 지면 접촉 소실', 'joint_speed': '관절 속도 > 50rad/s',
           'support_control_invalid': '지지 제어 판정 실패'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def pose(row):
    return {'pose': {'p': dict(zip('xyz', row[:3].tolist())),
                     'r': dict(zip('xyzw', row[3:7].tolist()))}}


class Recording:
    def __init__(self, directory, env_id):
        self.directory = directory
        self.meta = json.loads((directory / 'metadata.json').read_text())
        report = json.loads((directory / 'report.json').read_text())
        if report['completed'] is not True or report['failure'] is not None:
            raise ValueError('Incomplete native capture cannot enter the comparison: ' + str(directory))
        self.arrays = np.load(str(directory / 'recording.npz'))
        self.row = self.meta['env_ids'].index(env_id)
        self.env_id = env_id
        self.body = self.arrays['body'][:, self.row]
        self.step = self.arrays['global_step']
        self.speed = np.max(np.abs(self.arrays['qd'][:, self.row]), axis=-1)
        self.nhuman = len(self.meta['human_body_names'])
        self.nguitar = len(self.meta['guitar_body_names'])
        guitar = self.body[:, self.nhuman]
        self.displacement = np.linalg.norm(guitar[:, :3] - guitar[0, :3], axis=-1)
        quat = guitar[:, 3:7].astype(np.float64)
        quat /= np.linalg.norm(quat, axis=-1, keepdims=True)
        self.angle = 2 * np.arccos(np.minimum(1., np.abs(quat @ quat[0])))
        bad = (self.displacement > .08) | (self.angle > .35) | (self.speed > 50.)
        indices = np.flatnonzero(bad)
        self.failure = None if len(indices) == 0 else int(indices[0])
        self.reason = []
        if self.failure is not None:
            i = self.failure
            if self.displacement[i] > .08:
                self.reason.append('기타 이동 > 8cm')
            if self.angle[i] > .35:
                self.reason.append('기타 회전 > 0.35rad')
            if self.speed[i] > 50.:
                self.reason.append('관절 속도 > 50rad/s')
        events_path = directory / 'events.jsonl'
        for line in events_path.read_text().splitlines() if events_path.exists() else []:
            event = json.loads(line)
            if event.get('env_id') != env_id:
                continue
            # Capturer records the actual physics step of terminal evaluation.
            event_step = event.get('physics_step', event.get('global_step'))
            if event_step is None:
                event_step = (event['control_tick'] + 1) * 4
            i = int(np.searchsorted(self.step, event_step))
            if i < len(self.step) and (self.failure is None or i < self.failure):
                self.failure = i
                self.reason = list(event.get('failure_reasons', ['물리 종료']))
            break
        self.model, self.data, self.mapping, xml = build_model(self.meta)
        (directory.parent / 'render' / (self.meta['case'] + '_env%d_source_visual.xml' % env_id)).write_text(xml)
        import mujoco
        # Leave room for the overlays while keeping both head and feet in view.
        self.model.cam_pos[0] = [0., 3.9, .8]
        dy, dz = 3.9, .15
        norm = np.hypot(dy, dz)
        axes = np.asarray([[-1., 0., 0.], [0., -dz / norm, dy / norm],
                           [0., dy / norm, dz / norm]])
        mujoco.mju_mat2Quat(self.model.cam_quat[0], axes.reshape(-1))
        self.renderer = mujoco.Renderer(self.model, width=800, height=450)
        self.detail_renderer = mujoco.Renderer(self.model, width=800, height=600)
        self.strings = [(self.meta['guitar_body_names'].index('G:string%d' % i),
                         self.meta['guitar_body_names'].index('G:string%d_end' % i))
                        for i in range(1, 7)]
        self.worst_position = self.worst_rotation = 0.

    def render(self, source_index, detail=False, side=False):
        import mujoco
        i = min(source_index, len(self.body) - 1)
        frozen = self.failure is not None and i >= self.failure
        if frozen:
            i = self.failure
        rows = self.body[i]
        state = {'human_body_states': [pose(row) for row in rows[:self.nhuman]],
                 'guitar_body_states': [pose(row) for row in rows[self.nhuman:self.nhuman + self.nguitar]],
                 'chair_body_states': [pose(rows[-1])]}
        errors = set_body_poses(self.model, self.data, self.mapping, state)
        self.worst_position = max(self.worst_position, errors['max_position_error_m'])
        self.worst_rotation = max(self.worst_rotation, errors['max_rotation_error_rad'])
        before = (self.data.xpos.copy(), self.data.xquat.copy())
        renderer = self.detail_renderer if detail else self.renderer
        if detail:
            camera = mujoco.MjvCamera()
            camera.type = mujoco.mjtCamera.mjCAMERA_FREE
            camera.lookat[:] = [0., 0., .93]
            camera.distance = 1.8
            camera.azimuth = 0 if side else -90
            camera.elevation = -3.
        else:
            camera = 'front'
        renderer.update_scene(self.data, camera=camera)
        endpoints = np.asarray([[rows[self.nhuman + a, :3], rows[self.nhuman + b, :3]]
                                for a, b in self.strings])
        add_strings(renderer.scene, endpoints)
        image = Image.fromarray(renderer.render())
        assert np.array_equal(before[0], self.data.xpos)
        assert np.array_equal(before[1], self.data.xquat) and self.data.time == 0.
        return image, i, frozen

    def summary(self):
        return {'case': self.meta['case'], 'env_id': self.env_id,
                'first_failure_source_index': self.failure,
                'first_failure_physics_step': None if self.failure is None else int(self.step[self.failure]),
                'first_failure_time_s': None if self.failure is None else float(self.step[self.failure] / 240.),
                'failure_reasons': self.reason,
                'guitar_reference': 'first recorded frame (physics_step 0 required)',
                'max_position_error_m': self.worst_position,
                'max_rotation_error_rad': self.worst_rotation,
                'renderer_clock_s': float(self.data.time)}

    def close(self):
        self.renderer.close()
        self.detail_renderer.close()


def text(draw, xy, value, size=23, fill=WHITE):
    draw.text(xy, value, font=ImageFont.truetype(str(FONT), size), fill=fill)


def annotate(image, recording, index, frozen, title, side_label=None):
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, image.width, 72), fill=(20, 28, 39))
    text(draw, (18, 7), title, 25)
    status = 'FAIL / FROZEN' if frozen else '재생 중'
    text(draw, (18, 42), '실제 시각 %.3fs · step %d · %s' %
         (recording.step[index] / 240., recording.step[index], status), 19, RED if frozen else MUTED)
    bottom = image.height - 68
    draw.rectangle((0, bottom, image.width, image.height), fill=(20, 28, 39))
    text(draw, (18, bottom + 4), '기타 이동 %.1fcm   회전 %.3frad   관절 최고속도 %.1frad/s' %
         (recording.displacement[index] * 100, recording.angle[index], recording.speed[index]), 19)
    reason = ' / '.join(REASONS.get(value, value) for value in recording.reason) if frozen else '표시 기준: 이동 8cm · 회전 0.35rad · 관절속도 50rad/s'
    text(draw, (18, bottom + 34), reason[:64], 18, RED if frozen else MUTED)
    if side_label:
        text(draw, (18, 83), side_label, 22, WHITE)
    return image


def encoder(path, width, height):
    return subprocess.Popen(['ffmpeg', '-nostdin', '-n', '-loglevel', 'error', '-f', 'rawvideo',
                             '-pix_fmt', 'rgb24', '-s', '%dx%d' % (width, height), '-r', '30',
                             '-i', '-', '-an', '-c:v', 'libx264', '-crf', '18', '-pix_fmt',
                             'yuv420p', '-movflags', '+faststart', str(path)], stdin=subprocess.PIPE)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    out = args.input / 'render'
    out.mkdir(exist_ok=True)
    choices = [('cpu_zero', 0, 'CPU 물리 · 무행동 · env 0'),
               ('gpu2_zero', 0, 'GPU 2환경 · 무행동 · env 0'),
               ('gpu1024_zero', 0, 'GPU 1024환경 · 무행동 · env 0'),
               ('gpu1024_zero', 64, 'GPU 1024환경 · 무행동 · env 64')]
    recordings = [Recording(args.input / case, env) for case, env, _ in choices]
    paths = {Path(__file__).resolve(), FONT}
    for recording in recordings:
        paths.update(recording.directory / name for name in ('recording.npz', 'metadata.json', 'events.jsonl', 'report.json'))
        for asset in recording.meta['loaded_assets']:
            paths.update(asset_paths(asset['path']))
    paths.add(ROOT / 'guitar_learning/native/initial_pose_video60_v1/static_visual_v7.py')
    paths.add(ROOT / 'guitar_learning/native/initial_pose_video60_v1/replay_v6.py')
    paths.add(ROOT / 'guitar_learning/native/paths.py')
    pins = {str(path): sha(path) for path in sorted(paths) if path.exists()}
    save(out / 'inputs_before.json', pins)
    # Every fourth source frame is 60Hz; repeat twice at 30fps gives 0.25x speed.
    common_step = min(int(r.step[-1]) for r in recordings)
    source_steps = list(range(0, common_step + 1, 4))
    frames = []
    comparison = encoder(out / 'comparison.mp4', 1600, 1020)
    detail = encoder(out / 'detail.mp4', 1600, 720)
    try:
        for frame_number, physics_step in enumerate(source_steps):
            canvas = Image.new('RGB', (1600, 1020), (11, 18, 28))
            draw = ImageDraw.Draw(canvas)
            text(draw, (24, 10), 'GPU 물리 실패 재현 | 같은 초기 자세 · 모두 무행동', 30)
            text(draw, (24, 55), '새 재현 기록 · 0.25배속 · CPU / GPU 2환경 / GPU 1024환경의 두 환경 · 실패 최초 프레임에서 정지', 21, MUTED)
            indices = []
            for panel, (recording, choice) in enumerate(zip(recordings, choices)):
                index = min(int(np.searchsorted(recording.step, physics_step)), len(recording.step) - 1)
                image, actual, frozen = recording.render(index)
                indices.append({'case': choice[0], 'source_index': actual, 'physics_step': int(recording.step[actual]), 'frozen': frozen})
                annotate(image, recording, actual, frozen, choice[2])
                canvas.paste(image, ((panel % 2) * 800, 110 + (panel // 2) * 450))
            for _ in range(2):
                comparison.stdin.write(canvas.tobytes())
            if frame_number in (0, len(source_steps) // 2, len(source_steps) - 1):
                canvas.save(out / ('comparison_frame_%03d.png' % frame_number))
            frames.append({'output_frame_start': frame_number * 2, 'requested_physics_step': physics_step, 'panels': indices})
            if frame_number % 30 == 0:
                print('Rendered %d/%d source times' % (frame_number + 1, len(source_steps)), flush=True)
        detail_frames = []
        recording = recordings[3]
        detail_indices = np.flatnonzero(recording.step <= min(common_step, 120))
        for frame_number, index in enumerate(detail_indices):
            closeup = Image.new('RGB', (1600, 720), (11, 18, 28))
            draw = ImageDraw.Draw(closeup)
            text(draw, (24, 10), 'GPU 1024환경 · 무행동 · env 64 | 기타와 몸통 확대', 30)
            text(draw, (24, 55), '0.125배속 · 최초 0.5초의 240Hz 원본 · 실패 최초 프레임에서 정지 · 마지막 2초 유지', 21, MUTED)
            for side in (False, True):
                image, actual, frozen = recording.render(int(index), detail=True, side=side)
                annotate(image, recording, actual, frozen, 'GPU 1024환경 · 무행동 · env 64', '측면' if side else '정면')
                closeup.paste(image, (800 if side else 0, 110))
            detail.stdin.write(closeup.tobytes())
            detail_frames.append({'output_frame': frame_number, 'requested_source_index': int(index),
                                  'actual_source_index': actual, 'physics_step': int(recording.step[actual]), 'frozen': frozen})
            if frame_number in (0, 8, 16, 32, len(detail_indices) - 1):
                closeup.save(out / ('detail_frame_%03d.png' % frame_number))
        for _ in range(60):
            detail.stdin.write(closeup.tobytes())
        for process in (comparison, detail):
            process.stdin.close()
            if process.wait() != 0:
                raise RuntimeError('Video encoding failed')
        assert all(sha(path) == digest for path, digest in pins.items())
        probes = {}
        for filename in ('comparison.mp4', 'detail.mp4'):
            probes[filename] = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-count_frames', '-show_streams', '-show_format', '-of', 'json', str(out / filename)]))
        save(out / 'render_report.json', {'scope': 'New reproduction; recorded native body poses rendered using original source visual geometry; not Isaac Gym cooked rendering.',
             'new_physics_steps': 0, 'interpolation': False, 'source_hz': 240, 'stride': 4,
             'output_fps': 30, 'frame_repeat': 2, 'playback_speed': .25, 'frame_count': len(frames) * 2,
             'detail_playback_speed': .125, 'detail_source_stride': 1, 'detail_final_hold_frames': 60,
             'detail_frame_count': len(detail_frames) + 60, 'detail_frames': detail_frames,
             'inputs_unchanged': True, 'cases': [r.summary() for r in recordings], 'ffprobe': probes, 'frames': frames,
             'output_sha256': {name: sha(out / name) for name in probes}})
    finally:
        for process in (comparison, detail):
            if process.poll() is None:
                process.kill()
                process.wait()
        for recording in recordings:
            recording.close()


if __name__ == '__main__':
    main()
