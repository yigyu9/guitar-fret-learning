"""Recolor the original final body poses and inspect source geometry; no physics."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

os.environ['MUJOCO_GL'] = 'osmesa'
os.environ['PYOPENGL_PLATFORM'] = 'osmesa'
PHASE = Path(__file__).resolve().parents[1]
ROOT = PHASE.parents[3]
sys.path.insert(0, str(ROOT))
import mujoco
import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial.transform import Rotation
from guitar_learning.native.initial_pose_video60_v1.static_visual_v7 import build_model, set_body_poses, add_strings
from guitar_learning.gpu.geometry import finger_mesh_surface_samples
from guitar_learning.gpu.episode_diagnostics import load_thumb_rear_surface, thumb_rear_distance

SOURCE = ROOT/'docs/2026-10-25/guitar_learning_v20_A500'
OLD_ANALYSIS = ROOT/'docs/2026-10-25/guitar_learning_v20_standby_diagnosis/frame_analysis.json'
VISUAL_HELPER = ROOT/'docs/2026-10-26/시각화/생성자료/render_finger_preparation_candidates_v1.py'
COLORS = dict(thumb=(.94, .24, .27, 1), index=(.18, .52, .87, 1),
              middle=(.10, .67, .49, 1), ring=(.94, .57, .18, 1), pinky=(.63, .38, .82, 1))
LABELS = dict(thumb='엄지', index='검지', middle='중지', ring='약지', pinky='소지')
FONT = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    paths = [SOURCE/'evaluation_repeat1'/name for name in
             ('poses_env0000.npz', 'capture_metadata.json', 'visual_initial.json')]
    paths += [OLD_ANALYSIS, VISUAL_HELPER, Path(__file__).resolve(),
              ROOT/'guitar_learning/gpu/environment.py',
              SOURCE/'source_training/guitar_learning/gpu/environment.py']
    pins = {str(p): sha(p) for p in paths}
    assert paths[-2].read_bytes() == paths[-1].read_bytes()
    pose = np.load(paths[0])
    meta, initial = [json.loads(p.read_text()) for p in paths[1:3]]
    frame, names = pose['body_state'][-1], meta['body_names']
    state = {actor+'_body_states': [] for actor in ('human', 'guitar', 'chair')}
    for name, row in zip(names, frame):
        state[name.split('/')[0]+'_body_states'].append(dict(pose=dict(
            p=dict(zip('xyz', row[:3].tolist())), r=dict(zip('xyzw', row[3:7].tolist())))))
    model, data, mapping, xml = build_model(initial)
    audit = set_body_poses(model, data, mapping, state)
    for i in range(model.ngeom):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, int(model.geom_bodyid[i])) or ''
        if name.startswith('human/LH:'):
            model.geom_rgba[i] = [.65, .68, .72, 1]
        for finger, color in COLORS.items():
            if name.startswith('human/LH:'+finger):
                model.geom_rgba[i] = color
    spec = importlib.util.spec_from_file_location('source_B_static_geometry', VISUAL_HELPER)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    intersections = helper.separation_check(model, data)
    pairs = [row for row in intersections if
        any('LH:'+f in n for n in row['bodies'] for f in ('thumb', 'index')) and
        any('LH:middle' in n for n in row['bodies'])]
    local, valid = finger_mesh_surface_samples(['LH:thumb2', 'LH:thumb3'])
    body_ids = [names.index('human/LH:thumb'+str(j)) for j in (2, 3)]
    points_W = np.stack([frame[j, :3]+Rotation.from_quat(frame[j, 3:7]).apply(s)
                         for j, s in zip(body_ids, local)]).reshape(-1, 3)
    g = names.index('guitar/guitar')
    points_G = Rotation.from_quat(frame[g, 3:7]).inv().apply(points_W-frame[g, :3])
    triangles, plane = load_thumb_rear_surface()
    distance, compatible = thumb_rear_distance(torch.tensor(points_G[None]),
        torch.tensor(valid.flatten()), torch.tensor(triangles), torch.tensor(plane))
    renderer = mujoco.Renderer(model, height=700, width=1000)
    board = Image.new('RGB', (2000, 870), '#f1f5fa')
    draw = ImageDraw.Draw(board)
    draw.text((24, 15), '원영상 마지막 자세 · 손가락 색상 구분', font=ImageFont.truetype(FONT, 36), fill='#1b3045')
    draw.text((24, 66), '물리 시계 32.816667초 · 원영상과 동일한 저장 몸체 자세 · 추가 물리 0회',
              font=ImageFont.truetype(FONT, 25), fill='#4a6078')
    for k, (finger, color) in enumerate(COLORS.items()):
        draw.text((24+k*260, 109), '● '+LABELS[finger], font=ImageFont.truetype(FONT, 26),
                  fill=tuple(int(v*255) for v in color[:3]))
    camera = json.loads((SOURCE/'video_hand/presentation.json').read_text())['camera']
    model.cam_pos[0], model.cam_quat[0], model.cam_fovy[0] = (
        camera['position'], camera['quaternion_wxyz'], camera['fovy_degrees'])
    for k in range(2):
        if k:
            helper.camera(model, [-.27, -.09, .66], [-.38, .31, .18], [0, 0, 1], .48, 40.)
        mujoco.mj_camlight(model, data)
        renderer.update_scene(data, camera='front')
        endpoints = [[frame[names.index('guitar/G:string%d%s' % (j, suffix)), :3]
                      for suffix in ('', '_end')] for j in range(1, 7)]
        add_strings(renderer.scene, np.asarray(endpoints))
        board.paste(Image.fromarray(renderer.render()), (1000*k, 160))
    renderer.close()
    board.save(PHASE/'final_colored.png')
    analysis = json.loads(OLD_ANALYSIS.read_text())['selected']['trace']
    result = dict(physical_clock_s=float(pose['clock'][-1]/240), video_pts_s=32.8,
        source_pose_sha256=sha(paths[0]), pose_readback=audit,
        actual_geometric_flexion_degrees={f['finger']: f['final_angles'] for f in analysis['fingers']},
        final_native={f: {key: (pose[key][-1, [i for i, n in enumerate(meta['joint_names'])
            if n.startswith('LH:'+f)]]*180/np.pi).tolist() for key in ('q', 'target')}
            for f in COLORS},
        thumb_finite_source_rear_distance_m=float(distance[0]),
        thumb_rear_compatible_distance_m=float(compatible[0]),
        selected_source_convex_pairs=pairs,
        limitations=['Source convex intersection inradius is not PhysX cooked penetration or contact-pair evidence.',
            'Thumb rear distance uses the existing finite thumb2/3 support samples and finite source rear facets; not calibrated contact or exact mesh minimum.',
            'Two views replay the same original saved world poses without physics; hand colors and camera presentation change. Display strings use the original saved logical endpoints.'],
        fingerprints=pins)
    assert all(sha(p) == h for p, h in pins.items())
    (PHASE/'analysis.json').write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False)+'\n')
    print(json.dumps(dict(thumb_rear_mm=float(distance[0])*1000,
        overlapping_source_pairs=[row for row in pairs if row['overlap_over_1um']]), ensure_ascii=False))


if __name__ == '__main__':
    main()
