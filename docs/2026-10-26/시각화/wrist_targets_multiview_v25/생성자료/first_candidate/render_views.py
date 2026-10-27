"""Frozen prepared native body poses, production wrist boxes, live song overlays."""
import os
os.environ['MUJOCO_GL'] = 'osmesa'
os.environ['PYOPENGL_PLATFORM'] = 'osmesa'
os.environ.setdefault('LIBGL_ALWAYS_SOFTWARE', '1')

import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('/home/ajou/yigyu/3')
sys.path.insert(0, str(ROOT))
import mujoco
import numpy as np
from scipy.spatial.transform import Rotation
from PIL import Image, ImageDraw, ImageFont
import torch

from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract
from guitar_learning.core.geometry_v1 import frame, geometry_snapshot
from guitar_learning.gpu.press_surface import load_press_surface
from guitar_learning.gpu.wrist_region import load_wrist_region_track, measure_wrist_region
from guitar_learning.song.task import make_task
from guitar_learning.native.initial_pose_video60_v1.static_visual_v7 import build_model, set_body_poses, add_strings
from guitar_learning.tool.experiments.active_press_v25.runtime import SPEC

OUT = Path(__file__).resolve().parents[1]
SUPPORT = Path(__file__).resolve().parent
FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
W, H, FPS = 1280, 720, 30
BASE_AXES = np.array([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]])
VIEWS = [('front', '정면', 0.), ('oblique', '비스듬한 시점', 40.), ('side', '측면', 75.)]
FINGERS = {1: '검지', 2: '중지', 3: '약지', 4: '소지'}


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def box(draw, project, low, high, color, fill=False):
    points = np.array(list(itertools.product(*zip(low, high))))
    pixels = project(points)
    if fill:
        for axis in range(3):
            for end in (0, 1):
                ids = [i for i in range(8) if ((i >> (2-axis)) & 1) == end]
                quad = pixels[ids]
                center = quad.mean(0)
                order = np.argsort(np.arctan2(quad[:, 1]-center[1], quad[:, 0]-center[0]))
                draw.polygon([tuple(x) for x in quad[order]], fill=color[:3]+(16,))
    for a in range(8):
        for bit in (1, 2, 4):
            b = a ^ bit
            if a < b:
                draw.line([tuple(pixels[a]), tuple(pixels[b])], fill=color, width=3)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    prepared = load_prepared_reset_contract()
    initial, state = prepared['initial'], prepared['state']
    geometry = geometry_snapshot(state, initial['human_body_names'], initial['guitar_body_names'])
    bundle = ROOT/'data/song_bundles/05_BN2-131-B_solo'
    task = make_task(bundle, pre_roll_s=3., tail_s=.5)
    surface = load_press_surface([t.string for t in task.targets], [t.fret for t in task.targets])
    track = load_wrist_region_track(bundle, surface)
    times = np.arange(0, task.provenance['song']['control_ticks'], 2)/60.
    wp, _ = frame(state['human_body_states'][initial['human_body_names'].index('L_Wrist')])
    gp, gr = frame(state['guitar_body_states'][initial['guitar_body_names'].index('guitar')])
    wrist_g = gr.inv().apply(wp-gp)
    measures = measure_wrist_region(torch.tensor(wrist_g[None].repeat(len(times), 0), dtype=torch.float64),
        torch.tensor(times-3., dtype=torch.float64), torch.tensor(track['times_s'], dtype=torch.float64),
        torch.tensor(track['lower_G_m'], dtype=torch.float64), torch.tensor(track['upper_G_m'], dtype=torch.float64))
    lows, highs = measures['lower_G_m'].numpy(), measures['upper_G_m'].numpy()
    source_frames = json.loads((bundle/'training/hand_position_targets.json').read_text())['frames']
    strings = np.stack((geometry['starts_G_m'], geometry['ends_G_m']), 1)
    frets = geometry['fret_markers_G_m']
    plane = np.array(surface['plane_G'])
    segments = []
    for target in task.targets:
        lo, hi = sorted([frets[target.fret-1, 1], frets[target.fret, 1]])
        ends = []
        for y in (lo+.002, hi-.002):
            a, b = strings[target.string]
            point = a+(y-a[1])/(b[1]-a[1])*(b-a)
            point[2] = -(plane[0]*point[0]+plane[1]*point[1]+plane[3])/plane[2]
            ends.append(point)
        segments.append(np.array(ends))
    model, data, mapping, _ = build_model(initial)
    pose_audit = set_body_poses(model, data, mapping, state)
    frozen = [x.copy() for x in (data.xpos, data.xquat, model.body_pos, model.body_quat)]
    renderer = mujoco.Renderer(model, height=H, width=W)
    title_font = ImageFont.truetype(FONT, 23)
    font = ImageFont.truetype(FONT, 19)
    small = ImageFont.truetype(FONT, 15)
    outputs, camera_records = [], []
    try:
        for key, label, degrees in VIEWS:
            rotation_g = Rotation.from_rotvec(np.array([0., np.deg2rad(degrees), 0.]))*Rotation.from_matrix(BASE_AXES)
            up = gr.apply(rotation_g.apply([0., 1., 0.]))
            if up[2] <= 0:
                raise ValueError('Camera is not upright')
            center_g, distance = np.array([.04, -.015, -.035]), .86
            eye = gp+gr.apply(center_g+rotation_g.apply([0., 0., distance]))
            world_rotation = gr*rotation_g
            q = world_rotation.as_quat()
            model.cam_pos[0], model.cam_quat[0] = eye, q[[3, 0, 1, 2]]
            mujoco.mj_camlight(model, data)
            renderer.update_scene(data, camera='front')
            endpoints = gp+gr.apply(strings.reshape(-1, 3))
            add_strings(renderer.scene, endpoints.reshape(6, 2, 3))
            background = Image.fromarray(renderer.render()).convert('RGBA')
            background.save(SUPPORT/(key+'_background.png'))
            focal = H/2/np.tan(np.deg2rad(model.cam_fovy[0])/2)

            def project(points):
                p = world_rotation.inv().apply(gp+gr.apply(np.asarray(points))-eye)
                if np.any(p[..., 2] >= 0):
                    raise ValueError('Overlay behind camera')
                return np.stack((W/2+focal*p[..., 0]/(-p[..., 2]), H/2-focal*p[..., 1]/(-p[..., 2])), -1)

            camera_records.append(dict(view=key, eye_W_m=eye.tolist(), quaternion_xyzw=q.tolist(),
                                       up_W=up.tolist(), world_up_dot=float(up[2])))
            video_path = OUT/(key+'.mp4')
            video = subprocess.Popen(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n',
                '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1280x720', '-r', str(FPS), '-i', '-',
                '-an', '-c:v', 'libx264', '-threads', '2', '-preset', 'fast', '-crf', '18',
                '-pix_fmt', 'yuv420p', str(video_path)], stdin=subprocess.PIPE)
            try:
                for index, now in enumerate(times):
                    image = background.copy()
                    overlay = Image.new('RGBA', image.size)
                    draw = ImageDraw.Draw(overlay)
                    lo, hi = lows[index], highs[index]
                    box(draw, project, lo-SPEC['wrist_margin_m'], hi+SPEC['wrist_margin_m'], (255, 103, 95, 210))
                    box(draw, project, lo, hi, (30, 225, 140, 235), True)
                    for fret in range(1, 23):
                        y = frets[fret, 1]
                        a, b = strings[0], strings[-1]
                        line = np.array([x[0]+(y-x[0, 1])/(x[1, 1]-x[0, 1])*(x[1]-x[0]) for x in (a, b)])
                        draw.line([tuple(p) for p in project(line)], fill=(128, 190, 245, 140), width=1)
                        p = project(np.array([[0., .5*(frets[fret-1, 1]+y), surface['plane_G'][3]*-1]]))[0]
                        draw.text(tuple(p), str(fret), font=small, anchor='mm', fill=(170, 215, 255, 255))
                    active = [i for i, t in enumerate(task.targets) if t.press_s <= now < t.end_s]
                    upcoming = [i for i, t in enumerate(task.targets) if now < t.press_s <= now+.5]
                    for ids, color, width in ((upcoming, (255, 224, 94, 240), 6), (active, (255, 129, 35, 255), 10)):
                        for i in ids:
                            points = project(segments[i])
                            draw.line([tuple(p) for p in points], fill=color, width=width)
                            center = points.mean(0)
                            draw.ellipse((center[0]-5, center[1]-5, center[0]+5, center[1]+5), fill=color)
                    wrist = project(wrist_g[None])[0]
                    draw.ellipse((wrist[0]-7, wrist[1]-7, wrist[0]+7, wrist[1]+7), fill=(255, 255, 255, 255), outline=(15, 25, 40, 255), width=2)
                    image = Image.alpha_composite(image, overlay).convert('RGB')
                    draw = ImageDraw.Draw(image)
                    draw.rectangle((0, 0, W, 91), fill=(20, 28, 39))
                    draw.rectangle((0, 615, W, H), fill=(20, 28, 39))
                    score_frame = source_frames[min(max(int((now-3)*60), 0), len(source_frames)-1)]
                    draw.text((18, 9), f'{label} | 곡 목표와 손목 영역 | t={now:.2f}s · 원오디오 {max(now-3, 0):.2f}s', font=title_font, fill='white')
                    draw.text((18, 47), '초록: 안내 영역  ·  빨강: 지속 이탈 종료 경계  ·  흰 점: 고정 초기 손목  ·  주황: 현재 압현  ·  노랑: 다음 목표', font=font, fill=(215, 230, 245))
                    description = ' / '.join(f'{FINGERS[task.targets[i].finger]} {task.targets[i].string+1}번줄 F{task.targets[i].fret}' for i in active) or ('초기 준비' if now < 3 else '압현 목표 없음')
                    draw.text((18, 626), '현재 목표: '+description, font=title_font, fill=(255, 199, 122))
                    span = score_frame['allowed_fret_range']
                    distance_mm = float(measures['distance_m'][index])*1000
                    draw.text((18, 663), f'작업 F{span[0]}~F{span[1]} · 안내 12×7×9cm · 종료 18×13×15cm · 초기 손목의 안내 영역 밖 거리 {distance_mm:.1f}mm', font=font, fill='white')
                    draw.text((18, 692), '035/v14 자세 고정 · 물리 진행/정책/IK 없음 · source 실측 자세 재구성 · 압현 성공/도달성 인증 영상 아님', font=small, fill=(185, 205, 225))
                    if index in (0, 110, 500):
                        image.save(SUPPORT/(key+'_frame_%04d.png'%index))
                    video.stdin.write(np.asarray(image).tobytes())
            finally:
                video.stdin.close()
                code = video.wait()
            if code:
                raise RuntimeError('ffmpeg encoding failed: '+key)
            probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height,nb_frames,avg_frame_rate,duration', '-of', 'json', str(video_path)]))['streams'][0]
            assert int(probe['nb_frames']) == len(times) and probe['avg_frame_rate'] == '30/1'
            outputs.append(dict(path=str(video_path), sha256=hashlib.sha256(video_path.read_bytes()).hexdigest(), stream=probe))
            print('DONE', key, len(times), flush=True)
    finally:
        renderer.close()
    assert data.time == 0 and model.nq == model.nv == 0
    assert all(np.array_equal(old, new) for old, new in zip(frozen, (data.xpos, data.xquat, model.body_pos, model.body_quat)))
    np.savez_compressed(SUPPORT/'region_track.npz', time_s=times, lower_G_m=lows, upper_G_m=highs,
        outer_lower_G_m=lows-.03, outer_upper_G_m=highs+.03, wrist_G_m=wrist_g,
        wrist_excess_G_m=measures['delta'].numpy())
    write(SUPPORT/'verification.json', dict(completed=True, original_target_count=len(task.targets),
        original_duration_s=task.duration_s, frames=len(times), fps=FPS, videos=outputs, cameras=camera_records,
        frozen_pose_audit=pose_audit, unchanged_body_transforms=True, physics_steps=0, policy_steps=0,
        source_renderer='MuJoCo static source meshes at measured Isaac prepared body poses; no physics simulation',
        wrist_region_runtime_contract=track['contract'], termination_spec=SPEC,
        video_end_rounding_s=len(times)/FPS-task.duration_s,
        source_sha256={**prepared['source_sha256'], **track['contract']['source_sha256'],
            str(Path(__file__).resolve()): hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
