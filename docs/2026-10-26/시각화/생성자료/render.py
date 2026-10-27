"""Fixed035/v14 source visual with live song annotations; no policy or physics."""
import argparse
import base64
import hashlib
import os
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
os.environ['MUJOCO_GL'] = 'osmesa'
os.environ['PYOPENGL_PLATFORM'] = 'osmesa'
os.environ.setdefault('LIBGL_ALWAYS_SOFTWARE', '1')

import numpy as np
from scipy.spatial.transform import Rotation
import torch
from PIL import Image, ImageDraw, ImageFont

from guitar_learning.core.geometry_v1 import frame, geometry_snapshot
from guitar_learning.gpu.environment import TensorSongEnvironment
from guitar_learning.gpu.finger_reward import finger_target_indices
from guitar_learning.gpu.press_surface import load_press_surface
from guitar_learning.native.initial_pose_video60_v1.static_visual_v7 import (
    asset_paths, build_model, set_body_poses, add_strings)
from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract
from guitar_learning.song.task import make_task
from guitar_learning.song.wrist_guide import load_anchor_track
from guitar_learning.training import json_io
from guitar_learning.tool._rendering import FONT, encoder, probe

HERE = Path(__file__).resolve().parent
W, H = 1280, 720
FINGERS = {1: '검지', 2: '중지', 3: '약지', 4: '소지'}
# Camera right=+Gy, up=-Gx, backward=+Gz: upright at agreed035/v14.
NECK_CAMERA_AXES_G = np.array([[0,-1,0],[1,0,0],[0,0,1]])


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json_io.dumps(value, ensure_ascii=False, indent=2)+'\n')


def build_geometry(song):
    prepared = load_prepared_reset_contract()
    initial, state = prepared['initial'], prepared['state']
    geometry = geometry_snapshot(state, initial['human_body_names'], initial['guitar_body_names'])
    bundle = ROOT/'data/song_bundles'/song
    task = make_task(bundle, pre_roll_s=3., tail_s=.5)
    track = load_anchor_track(bundle)
    body_names = (['human/'+n for n in initial['human_body_names']] +
                  ['guitar/'+n for n in initial['guitar_body_names']] + ['chair/box'])
    records = state['human_body_states']+state['guitar_body_states']+state['chair_body_states']
    positions = np.array([frame(r)[0] for r in records])
    rotations = np.array([frame(r)[1].as_quat() for r in records])
    guitar = body_names.index('guitar/guitar')
    gp, gr = frame(records[guitar])
    local = gr.inv().apply(positions-gp)
    wrist = body_names.index('human/L_Wrist')
    ref_q = (gr.inv()*Rotation.from_quat(rotations[wrist])).as_quat()
    ticks = task.provenance['song']['control_ticks']
    times = torch.arange(ticks+1, dtype=torch.float64)/60.
    # Execute the production GPU method on CPU with an immutable repeated scene.
    count = ticks+1
    tensor = lambda value: torch.tensor(value, dtype=torch.float32)
    bodies = torch.cat((tensor(positions), tensor(rotations)), -1)[None].expand(count, -1, -1)
    state_view = SimpleNamespace(device=torch.device('cpu'), clock=torch.arange(count)*4, song={'pre_roll_s': 3.},
        anchor_times=torch.tensor(track['times_s'], dtype=torch.float64),
        anchor_values=tensor(track['anchors']), N=count,
        frets=tensor(geometry['fret_markers_G_m'])[None].expand(count, -1, -1),
        local_bodies=tensor(local)[None].expand(count, -1, -1), wrist_index=wrist,
        reference_wrist=tensor(local[wrist])[None].expand(count, -1),
        reference_wrist_q=tensor(ref_q)[None].expand(count, -1),
        guitar_q=tensor(gr.as_quat())[None].expand(count, -1), body=bodies)
    guide = TensorSongEnvironment._wrist_guide(state_view)
    wrist_targets = (state_view.reference_wrist+guide['delta']).numpy()
    # Independent interpolation identity checks the production y-offset formula.
    anchor = np.interp(times.numpy()-3., track['times_s'], track['anchors'])
    frets = geometry['fret_markers_G_m']
    expected = np.repeat(local[wrist][None], count, axis=0)
    expected[:, 1] += np.interp(anchor, np.arange(1, 23), frets[1:, 1])-frets[5, 1]
    error = float(np.max(np.abs(wrist_targets-expected)))
    if error > 2e-6:
        raise ValueError('Production wrist guide differs from independent interpolation')
    onset = torch.tensor([t.onset_s for t in task.targets], dtype=torch.float64)
    end = torch.tensor([t.end_s for t in task.targets], dtype=torch.float64)
    press = torch.tensor([t.press_s for t in task.targets], dtype=torch.float64)
    finger = torch.tensor([t.finger for t in task.targets], dtype=torch.long)
    selection = finger_target_indices(times, onset, end, press, finger)
    plane = load_press_surface([t.string for t in task.targets], [t.fret for t in task.targets])
    def z_at(x, y):
        p = plane['plane_G']
        return -(p[0]*x+p[1]*y+p[3])/p[2]
    starts, ends = geometry['starts_G_m'], geometry['ends_G_m']
    def string_point(string, y):
        p = starts[string]+((y-starts[string, 1])/(ends[string, 1]-starts[string, 1]))*(ends[string]-starts[string])
        p[2] = z_at(p[0], p[1])
        return p
    cells = []
    for f in range(1, 23):
        ys = [frets[f-1, 1], frets[f, 1]]
        # Full six-string footprint, not an invented change to collision width.
        quad = [string_point(s, y).tolist() for s, y in [(5,ys[0]),(0,ys[0]),(0,ys[1]),(5,ys[1])]]
        cells.append(dict(fret=f, quad_G_m=quad, label_G_m=[.029, sum(ys)/2, z_at(.029,sum(ys)/2)]))
    targets = []
    for index, t in enumerate(task.targets):
        lo, hi = sorted([frets[t.fret-1, 1], frets[t.fret, 1]])
        a, b = string_point(t.string, lo+.002), string_point(t.string, hi-.002)
        targets.append(dict(index=index, target_id=t.target_id, string=t.string+1,
            fret=t.fret, finger=t.finger, onset_s=t.onset_s, end_s=t.end_s, press_s=t.press_s,
            segment_G_m=[a.tolist(),b.tolist()], center_G_m=((a+b)/2).tolist()))
    # Recover fractional anchor from target y for display; endpoints clamped as runtime.
    actual_anchor = np.interp(wrist_targets[:,1]-local[wrist,1]+frets[5,1],
                              frets[1:,1][::-1], np.arange(1,23)[::-1])
    result = dict(schema='guitar_learning.fixed_song_guides.v1', song=song, target_count=len(targets),
        pre_roll_s=3., fps=60, control_ticks=ticks, duration_s=task.duration_s,
        cells=cells, targets=targets, wrist_G_m=local[wrist].tolist(),
        wrist_target_G_m=wrist_targets.tolist(), anchor_fret=actual_anchor.tolist(),
        tracking=selection['indices'][...,0].tolist(), tracking_valid=selection['valid'][...,0].tolist(),
        press_plane=plane, guide_formula_max_error_m=error,
        source_pose='agreed035/v14 prepared reset; source historical physics_step5280, visualization clock0',
        frozen_state_sha256=hashlib.sha256(json_io.dumps(state,sort_keys=True).encode()).hexdigest(),
        scope='Static source body geometry; only score clock and overlays change. No contact or achievement simulation.')
    pins = dict(prepared['source_sha256'])
    pins.update(plane['source_sha256'])
    pins.update({row['path']:row['sha256'] for row in task.provenance['provenance']})
    pins[str(bundle/'manifest.json')] = sha(bundle/'manifest.json')
    pins[str(bundle/'training/hand_position_targets.json')] = sha(bundle/'training/hand_position_targets.json')
    return prepared, geometry, result, pins


def camera(model, data, gp, gr, center_G, distance, local_rotation):
    import mujoco
    q = (gr*local_rotation).as_quat()
    eye = gp+gr.apply(np.asarray(center_G)+local_rotation.apply([0,0,distance]))
    model.cam_pos[0] = eye
    model.cam_quat[0] = q[[3,0,1,2]]
    mujoco.mj_camlight(model,data)
    rotation = Rotation.from_quat(q)
    focal = H/2/np.tan(np.deg2rad(model.cam_fovy[0])/2)
    def project(points_G):
        p = rotation.inv().apply(gp+gr.apply(np.asarray(points_G))-eye)
        if np.any(p[...,2] >= 0): raise ValueError('Overlay behind camera')
        return np.stack((W/2+focal*p[...,0]/(-p[...,2]), H/2-focal*p[...,1]/(-p[...,2])), -1)
    return project, dict(eye_W_m=eye.tolist(), quaternion_xyzw=q.tolist(), focal_px=float(focal))


def render_background(prepared, geometry, out):
    import mujoco
    initial, state = prepared['initial'], prepared['state']
    model,data,mapping,_ = build_model(initial)
    audit = set_body_poses(model,data,mapping,state)
    before = (data.xpos.copy(),data.xquat.copy(),model.body_pos.copy(),model.body_quat.copy())
    gp,gr = frame(state['guitar_body_states'][initial['guitar_body_names'].index('guitar')])
    renderer = mujoco.Renderer(model,height=H,width=W)
    endpoints = gp+gr.apply(np.stack((geometry['starts_G_m'],geometry['ends_G_m']),1).reshape(-1,3))
    try:
        # Original full-body camera is context only; principal inspection looks down the neck.
        renderer.update_scene(data,camera='front');add_strings(renderer.scene,endpoints.reshape(6,2,3))
        Image.fromarray(renderer.render()).save(out/'fixed_fullbody.jpg',quality=88)
        r = Rotation.from_matrix(NECK_CAMERA_AXES_G)
        up_world = gr.apply(r.apply([0,1,0]))
        if up_world[2] <= 0:
            raise ValueError("Neck camera screen-up opposes world-up")
        project,presentation = camera(model,data,gp,gr,[.020,-.007,0],.64,r)
        presentation.update(screen_up_W=up_world.tolist(), world_up_dot_screen_up=float(up_world[2]))
        renderer.update_scene(data,camera='front');add_strings(renderer.scene,endpoints.reshape(6,2,3))
        Image.fromarray(renderer.render()).save(out/'fixed_neck.jpg',quality=92)
        if not all(np.array_equal(a,b) for a,b in zip(before,(data.xpos,data.xquat,model.body_pos,model.body_quat))):
            raise ValueError('Camera render changed frozen body transforms')
        if data.time != 0 or model.nq != 0 or model.nv != 0:
            raise ValueError('Static visual unexpectedly has physics DOFs/time')
        audit.update(new_physics_steps=0,visual_time_s=float(data.time),visual_nq=model.nq,visual_nv=model.nv,
                     poses_unchanged_after_render=True)
        write(out/'pose_audit.json',audit)
        mujoco.mj_saveLastXML(str(out/'source_visual.xml'),model)
        return project,presentation
    finally:
        renderer.close()


def overlay_data(scene, project):
    for cell in scene['cells']:
        cell['quad_px'] = project(cell['quad_G_m']).tolist()
        cell['label_px'] = project(cell['label_G_m']).tolist()
    for t in scene['targets']:
        t['segment_px'] = project(t['segment_G_m']).tolist()
        t['center_px'] = project(t['center_G_m']).tolist()
    scene['wrist_px'] = project(scene['wrist_G_m']).tolist()
    scene['wrist_target_px'] = project(scene['wrist_target_G_m']).tolist()


def active(scene, index):
    now = index/60.
    audible = [t['index'] for t in scene['targets'] if t['onset_s'] <= now < t['end_s']]
    preparation = [i for i,valid in zip(scene['tracking'][index],scene['tracking_valid'][index]) if valid and i not in audible]
    return audible,preparation


def draw_frame(scene, bg, inset, index):
    image = bg.copy().convert('RGBA')
    layer = Image.new('RGBA',image.size);draw = ImageDraw.Draw(layer)
    font=ImageFont.truetype(str(FONT),22);small=ImageFont.truetype(str(FONT),17)
    audible,preparing = active(scene,index)
    for cell in scene['cells']:
        fill=(50,130,205,28 if cell['fret']%2 else 48)
        if any(scene['targets'][i]['fret']==cell['fret'] for i in audible):fill=(255,151,25,90)
        quad=[tuple(p) for p in cell['quad_px']]
        draw.polygon(quad,fill=fill);draw.line(quad+[quad[0]],fill=(200,220,235,150),width=1)
        p=cell['label_px'];label_y=p[1]+(20 if cell['fret']>=15 and cell['fret']%2 else 0)
        draw.text((p[0],label_y),str(cell['fret']),font=small,anchor='mm',fill=(245,245,245,255),stroke_width=2,stroke_fill=(22,27,34,255))
    for ids,color in [(preparing,(25,210,220,255)),(audible,(255,156,30,255))]:
        for i in ids:
            t=scene['targets'][i];a,b=t['segment_px'];draw.line((tuple(a),tuple(b)),fill=color,width=7)
            x,y=t['center_px'];draw.ellipse((x-7,y-7,x+7,y+7),fill=color)
    x,y=scene['wrist_target_px'][index];a,b=scene['wrist_px']
    draw.line((a,b,x,y),fill=(232,99,211,170),width=2)
    draw.ellipse((a-5,b-5,a+5,b+5),outline=(230,235,240,255),width=2)
    draw.ellipse((x-12,y-12,x+12,y+12),outline=(243,91,214,255),width=3)
    draw.line((x-18,y,x+18,y),fill=(243,91,214,255),width=3);draw.line((x,y-18,x,y+18),fill=(243,91,214,255),width=3)
    draw.text((x,y-28),'손목 안내',anchor='mm',font=small,fill=(255,170,238,255),stroke_width=2,stroke_fill=(22,27,34,255))
    image=Image.alpha_composite(image,layer).convert('RGB');image.paste(inset,(20,440))
    draw=ImageDraw.Draw(image);draw.rectangle((0,0,W,96),fill=(22,27,34));draw.rectangle((0,636,W,H),fill=(22,27,34))
    draw.text((20,7),f"초기 자세 고정 | 정책 시각 {index/60:.3f}초 · 원곡 {index/60-3:+.3f}초",font=font,fill='white')
    draw.text((20,43),'주황: 현재 발음 목표 · 청록: 손가락별 준비 목표 · 자홍: 손목 안내 · 숫자: 담당 프렛',font=small,fill=(225,235,245))
    desc=' / '.join(f"{scene['targets'][i]['string']}현 F{scene['targets'][i]['fret']} {FINGERS[scene['targets'][i]['finger']]}" for i in audible) or '현재 발음 목표 없음'
    draw.text((20,646),f"{desc} | 손목 anchor F{scene['anchor_fret'][index]:.2f}",font=font,fill='white')
    draw.text((20,684),'휴머노이드·기타·실제 손목은 고정 · 시간과 안내 표시만 변경 · 물리 적분 0회',font=small,fill=(225,235,245))
    return image


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--song',default='05_BN2-131-B_solo')
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if Path(args.song).name!=args.song or args.song in ('.','..'):raise ValueError('Safe song ID required')
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    prepared,geometry,scene,pins=build_geometry(args.song)
    project,presentation=render_background(prepared,geometry,out)
    overlay_data(scene,project)
    write(out/'scene.json',scene);write(out/'camera.json',presentation)
    assets=set().union(*(asset_paths(a['path']) for a in prepared['initial']['loaded_assets']))
    sources=assets|{Path(__file__).resolve(),FONT,HERE/'viewer.html'}
    sources.update(ROOT/p for p in ['guitar_learning/gpu/environment.py','guitar_learning/gpu/finger_reward.py',
        'guitar_learning/gpu/press_surface.py','guitar_learning/song/task.py','guitar_learning/song/wrist_guide.py',
        'guitar_learning/native/initial_pose_video60_v1/static_visual_v7.py',
        'guitar_learning/native/initial_pose_video60_v1/replay_v6.py','guitar_learning/core/geometry_v1.py',
        'guitar_learning/gpu/geometry.py','guitar_learning/tool/_rendering.py',
        'guitar_learning/runtime/prepared_reset_v1.py','guitar_learning/native/paths.py',
        'guitar_learning/training/json_io.py'])
    pins.update({str(p):sha(p) for p in sources});write(out/'inputs_before.json',pins)
    bg=Image.open(out/'fixed_neck.jpg').convert('RGB');inset=Image.open(out/'fixed_fullbody.jpg').resize((300,169))
    frames=scene['control_ticks'];video=out/'fixed_song_guides_60fps.mp4';process=encoder(video)
    chosen={0,round(scene['targets'][0]['onset_s']*60)+1,round(10*60),round(20*60),frames-1}
    try:
        for index in range(frames):
            image=draw_frame(scene,bg,inset,index);process.stdin.write(image.tobytes())
            if index in chosen:image.save(out/f'preview_{index:04d}.png')
        process.stdin.close()
        if process.wait()!=0:raise RuntimeError('Video encoder failed')
    finally:
        if process.poll() is None:process.kill();process.wait()
    media=probe(video,frames)
    inline=dict(scene)
    # High precision physical geometry stays in scene.json; inline presentation can be rounded.
    for key in ['wrist_target_G_m','wrist_target_px','anchor_fret']:
        inline[key]=np.round(np.asarray(scene[key]),5).tolist()
    def uri(p):return 'data:image/jpeg;base64,'+base64.b64encode(p.read_bytes()).decode()
    html=(HERE/'viewer.html').read_text().replace('__SCENE_JSON__',json_io.dumps(inline)).replace('__NECK_IMAGE__',uri(out/'fixed_neck.jpg')).replace('__BODY_IMAGE__',uri(out/'fixed_fullbody.jpg'))
    (out/'fixed-song-guides.html').write_text(html)
    if len(html.encode())>=1_000_000:raise ValueError('Inline visualization exceeds1MB')
    if any(sha(p)!=h for p,h in pins.items()):raise ValueError('Inputs changed during render')
    write(out/'report.json',dict(completed=True,song=args.song,target_count=len(scene['targets']),
        physical_pose='fixed035/v14',new_physics_steps=0,policy_executed=False,
        frozen_pose_audit='pose_audit.json',guide_formula_max_error_m=scene['guide_formula_max_error_m'],
        inputs_unchanged=True,inline_bytes=len(html.encode()),media=media))
    print(json_io.dumps(dict(completed=True,out=str(out),video=str(video))))


if __name__=='__main__':main()
