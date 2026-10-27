"""Static source-mesh preparation-pose candidates; never step or change training."""
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

os.environ.setdefault('MUJOCO_GL', 'osmesa')
os.environ.setdefault('PYOPENGL_PLATFORM', 'osmesa')
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
import mujoco
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.spatial import ConvexHull
from scipy.optimize import linprog
from PIL import Image, ImageDraw, ImageFont

from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract
from guitar_learning.native.initial_pose_video60_v1.static_visual_v7 import (
    asset_paths, build_model, set_body_poses)

HERE, OUT = Path(__file__).resolve().parent, Path(__file__).resolve().parent.parent
FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
FINGERS = ('index', 'middle', 'ring', 'pinky')
LABELS = ('검지', '중지', '약지', '소지')
COLORS = ((.18, .52, .87, 1), (.10, .67, .49, 1),
          (.94, .57, .18, 1), (.63, .38, .82, 1))
SPREAD = (-14., -3., 3., 10.)
CANDIDATES = dict(
    A=[[15, 25, 8], [18, 28, 10], [21, 31, 12], [24, 34, 14]],
    B=[[25, 35, 12], [28, 38, 14], [31, 41, 16], [34, 44, 18]],
    C=[[35, 45, 18], [38, 48, 20], [41, 51, 22], [44, 54, 24]])
INK, MUTED = '#23364c', '#5c7088'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pose(row):
    p, q = row['pose']['p'], row['pose']['r']
    return np.array([p[k] for k in 'xyz']), Rotation.from_quat([q[k] for k in 'xyzw'])


def changed_state(prepared, bodies, angles):
    state = copy.deepcopy(prepared['state'])
    names = prepared['initial']['human_body_names']
    rows = dict(zip(names, state['human_body_states']))
    palm_p, palm_r = pose(rows['LH:palm'])
    records, checks = {}, []
    for finger, flexion, spread in zip(FINGERS, angles, SPREAD):
        parent_p, parent_r = palm_p, palm_r
        for segment, angle in enumerate(flexion, start=1):
            name = 'LH:'+finger+str(segment)
            source = bodies[name]
            assert source.get('quat', '1 0 0 0') == '1 0 0 0'
            offset = np.fromstring(source.get('pos', '0 0 0'), sep=' ')
            p = parent_p+parent_r.apply(offset)
            local = Rotation.from_rotvec(np.deg2rad([angle, 0, spread if segment == 1 else 0]))
            r = parent_r*local
            requested = {name+'_x': angle, name+'_z': spread} if segment == 1 else {name: angle}
            for joint_name, value in requested.items():
                joint = source.find('joint[@name="'+joint_name+'"]')
                lower, upper = np.fromstring(joint.get('range'), sep=' ')
                assert lower <= value <= upper, (joint_name, value, lower, upper)
                index = prepared['initial']['joint_names'].index(joint_name)
                props = prepared['initial']['native_PD_properties']
                native_lower, native_upper = np.rad2deg([props['lower'][index], props['upper'][index]])
                assert native_lower <= value <= native_upper
                checks.append(dict(joint=joint_name, requested_degrees=value,
                    source_range_degrees=[lower, upper], native_range_degrees=[native_lower, native_upper]))
            rows[name]['pose'] = dict(p=dict(zip('xyz', p.tolist())),
                                     r=dict(zip('xyzw', r.as_quat().tolist())))
            records[name] = dict(position_W_m=p.tolist(), quaternion_xyzw=r.as_quat().tolist())
            # Retain source descendants such as the nonphysical tip marker.
            for child in source.findall('body'):
                if child.get('name') in rows and child.get('name').endswith('_top'):
                    cp = p+r.apply(np.fromstring(child.get('pos'), sep=' '))
                    rows[child.get('name')]['pose'] = dict(p=dict(zip('xyz', cp.tolist())),
                        r=dict(zip('xyzw', r.as_quat().tolist())))
            parent_p, parent_r = p, r
    changed = set(records) | {'LH:'+finger+'_top' for finger in FINGERS}
    for name, before, after in zip(names, prepared['state']['human_body_states'], state['human_body_states']):
        if name not in changed:
            assert before == after, name
    assert state['guitar_body_states'] == prepared['state']['guitar_body_states']
    assert state['chair_body_states'] == prepared['state']['chair_body_states']
    return state, records, checks


def camera(model, target, backward, up, distance, fovy):
    z = np.asarray(backward, float); z /= np.linalg.norm(z)
    y = np.asarray(up, float); y -= z*(y@z); y /= np.linalg.norm(y)
    x = np.cross(y, z)
    model.cam_pos[0] = np.asarray(target)+distance*z
    model.cam_quat[0] = Rotation.from_matrix(np.stack((x, y, z), 1)).as_quat()[[3, 0, 1, 2]]
    model.cam_fovy[0] = fovy


def render(model, data, renderer, option):
    mujoco.mj_kinematics(model, data)
    mujoco.mj_camlight(model, data)
    renderer.update_scene(data, camera='front', scene_option=option)
    assert data.time == 0 and model.nq == model.nv == 0
    return Image.fromarray(renderer.render())


def font(size):
    return ImageFont.truetype(FONT, size)


def separation_check(model, data):
    """Feasibility of source convex-hull intersection, not runtime collision."""
    items, necks, hulls = [], [], {}
    for i in range(model.ngeom):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, int(model.geom_bodyid[i])) or ''
        if model.geom_type[i] != mujoco.mjtGeom.mjGEOM_MESH:
            continue
        mesh = int(model.geom_dataid[i])
        mesh_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_MESH, mesh)
        is_hand = any(name.startswith('human/LH:'+finger) for finger in FINGERS+('thumb',))
        is_neck = mesh_name in ('guitar/guitar_neck1', 'guitar/guitar_neck2')
        if not is_hand and not is_neck:
            continue
        vertices = model.mesh_vert[model.mesh_vertadr[mesh]:model.mesh_vertadr[mesh]+model.mesh_vertnum[mesh]]
        local = ConvexHull(vertices).equations
        normals = local[:, :3]@data.geom_xmat[i].reshape(3, 3).T
        hulls[i] = np.c_[normals, local[:, 3]-normals@data.geom_xpos[i]]
        if is_neck:
            necks.append((i, 'neck', mesh_name))
        for finger in FINGERS+('thumb',):
            if name.startswith('human/LH:'+finger):
                items.append((i, finger, name))
    records = []
    for i, (a, finger, name) in enumerate(items):
        for b, other, other_name in items[i+1:]+necks:
            if finger != other:
                hull = np.r_[hulls[a], hulls[b]]
                result = linprog([0, 0, 0, -1], A_ub=np.c_[hull[:, :3], np.ones(len(hull))],
                    b_ub=-hull[:, 3], bounds=[(None, None)]*4, method='highs')
                assert result.success
                records.append(dict(bodies=[name, other_name], includes_neck=other == 'neck',
                    convex_intersection_inradius_m=float(result.x[3]),
                    overlap_over_1um=bool(result.x[3] > 1e-6)))
    return records


def main():
    prepared = load_prepared_reset_contract()
    initial = prepared['initial']
    source = Path(initial['loaded_assets'][0]['path'])
    bodies = {b.get('name'): b for b in ET.parse(source).findall('.//body')}
    _, _, _, xml = build_model(initial)
    root = ET.fromstring(xml)
    # The existing static helper prioritizes group-1 visual meshes, omitting
    # the guitar body's six display strings. Restore their exact source geoms.
    guitar_source = ET.parse(initial['loaded_assets'][1]['path'])
    guitar_node = root.find('./worldbody/body[@name="guitar/guitar"]')
    for source_geom in guitar_source.findall('./worldbody/body/geom'):
        if source_geom.get('type') == 'capsule':
            attributes = {key: value for key, value in source_geom.attrib.items()
                if key in ('type', 'pos', 'quat', 'size', 'fromto')}
            ET.SubElement(guitar_node, 'geom', attributes, rgba='.30 .38 .46 1', contype='0', conaffinity='0')
    ET.SubElement(root.find('asset'), 'texture', name='sky', type='skybox',
        builtin='gradient', rgb1='.96 .98 1', rgb2='.82 .87 .92', width='512', height='512')
    model = mujoco.MjModel.from_xml_string(ET.tostring(root, encoding='unicode'))
    data = mujoco.MjData(model)
    names = initial['human_body_names']
    mapping = [(actor, i, mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, actor+'/'+name), actor+'/'+name)
        for actor, ns in (('human', names), ('guitar', initial['guitar_body_names'])) for i, name in enumerate(ns)]
    mapping.append(('chair', 0, mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, 'chair'), 'chair'))
    hand_geoms = []
    for i in range(model.ngeom):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, int(model.geom_bodyid[i])) or ''
        if name.startswith('human/LH:'):
            model.geom_group[i] = 1; hand_geoms.append(i)
            model.geom_rgba[i] = [.60, .66, .72, 1]
            for finger, color in zip(FINGERS, COLORS):
                if name.startswith('human/LH:'+finger): model.geom_rgba[i] = color
        else:
            model.geom_group[i] = 0
    option = mujoco.MjvOption(); option.geomgroup[:] = 0; option.geomgroup[1] = 1
    palm_p, palm_r = pose(prepared['state']['human_body_states'][names.index('LH:palm')])
    center = palm_p+palm_r.apply([.015, -.09, -.02])
    renderer = mujoco.Renderer(model, height=520, width=700)
    board = Image.new('RGB', (2160, 1420), '#f3f6fa'); draw = ImageDraw.Draw(board)
    draw.text((30, 20), '손가락 준비 자세 후보 · 현재 손 모델', font=font(38), fill=INK)
    draw.text((30, 78), 'A 얕게  /  B 중간 굽힘(우선 추천)  /  C 조금 깊게  ·  엄지·손바닥 자세는 기존 상태 유지', font=font(24), fill=MUTED)
    for j, (label, color) in enumerate(zip(LABELS, COLORS)):
        x = 32+j*130; rgb=tuple(int(c*255) for c in color[:3])
        draw.rounded_rectangle((x, 125, x+20, 145), radius=5, fill=rgb)
        draw.text((x+30, 119), label, font=font(23), fill=INK)
    metadata = dict(scope='source-mesh static body-transform candidates; no physics steps, native joint integration, learning, reward or reset changes',
        recommended='B', angle_order=['MCP_x', 'PIP_x', 'DIP_x'], spread_z_degrees=list(SPREAD),
        first_joint_rotation='Exp([MCP_x,0,spread_z]) source-body-local command reference; not native physical integration',
        thumb_palm_arm_guitar='unchanged035/v14 recorded body poses', candidates={})
    for col, (key, angles) in enumerate(CANDIDATES.items()):
        state, records, limits = changed_state(prepared, bodies, angles)
        check = set_body_poses(model, data, mapping, state)
        draw.text((30+col*710, 165), key+'  '+('중간 굽힘 · 추천' if key == 'B' else '얕은 굽힘' if key == 'A' else '조금 깊은 굽힘'), font=font(28), fill=INK)
        views = []
        for row, (title, backward) in enumerate((('손바닥 쪽 사선', [-.35, -.25, -1]), ('옆에서 본 곡률', [-1, -.15, -.25]))):
            camera(model, center, palm_r.apply(backward), palm_r.apply([0, -1, 0]), .29, 40)
            im = render(model, data, renderer, option)
            board.paste(im, (20+col*710, 210+row*560))
            draw.text((35+col*710, 220+row*560), title, font=font(23), fill=INK)
            views.append(dict(title=title, camera_position_W_m=model.cam_pos[0].tolist(), camera_quaternion_wxyz=model.cam_quat[0].tolist()))
        draw.text((32+col*710, 1336), '설계각 '+str(angles[0])+'° · 검지', font=font(22), fill=INK)
        metadata['candidates'][key] = dict(finger_angles_degrees=dict(zip(FINGERS, angles)),
            body_poses_W=records, source_joint_limit_checks=limits, static_readback=check, cameras=views,
            source_convex_intersection_diagnostic=separation_check(model, data))
    draw.text((30, 1380), '정적 자세 후보입니다. 충돌·압현 안정성을 검증한 자세나 학습 결과는 아닙니다. 팔·손목과 학습 설정은 변경하지 않았습니다.', font=font(22), fill=MUTED)
    board.save(OUT/'finger_preparation_candidates_v1.png')
    renderer.close()

    state, _, _ = changed_state(prepared, bodies, CANDIDATES['B'])
    set_body_poses(model, data, mapping, state)
    option.geomgroup[:] = 1
    renderer = mujoco.Renderer(model, height=700, width=1100)
    board = Image.new('RGB', (2240, 860), '#f3f6fa'); draw = ImageDraw.Draw(board)
    draw.text((30, 18), '추천 B · 기존 기타와 손목 위치에서 본 모습', font=font(36), fill=INK)
    draw.text((30, 71), '기타·팔·손목·엄지 고정  /  검지~소지 굽힘과 소폭 벌림만 후보 각도로 표시', font=font(25), fill=MUTED)
    stored = json.loads((HERE/'camera.json').read_text())
    model.cam_pos[0] = stored['eye_W_m']; model.cam_quat[0] = np.array(stored['quaternion_xyzw'])[[3, 0, 1, 2]]
    model.cam_fovy[0] = np.rad2deg(2*np.arctan(360/stored['focal_px']))
    board.paste(render(model, data, renderer, option), (15, 120))
    gp, gr = pose(prepared['state']['guitar_body_states'][initial['guitar_body_names'].index('guitar')])
    camera(model, center, gr.apply([0, 0, 1]), [0, 0, 1], .32, 40)
    board.paste(render(model, data, renderer, option), (1125, 120))
    for x, title in ((32, '기존 정적 장면의 넥 시점'), (1142, '손과 넥 가까이 보기')):
        draw.rounded_rectangle((x-6, 125, x+350, 165), radius=6, fill='#f3f6fa')
        draw.text((x, 130), title, font=font(24), fill=INK)
    draw.text((30, 824), '주의: 현재 손목 위치에 그대로 넣으면 검지와 넥이 겹칩니다. 손 모양 선택 후 위치 조정이 필요하며 학습에는 적용하지 않았습니다.', font=font(22), fill='#aa3b36')
    board.save(OUT/'finger_preparation_B_context_v1.png'); renderer.close()

    pins = {str(p):sha(p) for asset in initial['loaded_assets'] for p in asset_paths(asset['path'])}
    for p in (Path(__file__), HERE/'camera.json', ROOT/'guitar_learning/native/initial_pose_video60_v1/static_visual_v7.py'):
        pins[str(p.resolve())] = sha(p)
    metadata['source_sha256'] = pins
    metadata['context_warning'] = 'At unchanged035/v14 wrist, proposed index meshes overlap source neck convex hulls. This preview is not an applied collision-free robot posture.'
    metadata['renderer'] = dict(engine='MuJoCo static source visual', backend='OSMesa CPU', joints=int(model.nq), clock_s=float(data.time), physics_steps=0)
    (HERE/'finger_preparation_candidates_v1.json').write_text(json.dumps(metadata, indent=2, ensure_ascii=False)+'\n')
    print('Created preparation candidate and context images; static time=', data.time)


if __name__ == '__main__':
    main()
